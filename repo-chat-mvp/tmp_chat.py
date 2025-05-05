import os
import shutil
import pickle
import hashlib
import sys
from collections import defaultdict
import requests
import time

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
from git import Repo, GitCommandError
from urllib.parse import urlparse

from flask import Flask, request, jsonify, Response, abort
from flask_cors import CORS
from celery import Celery

from ingestion import parse_directory
from embedding import embed_texts
from vector_store import HybridStore
from ratelimit import limits, sleep_and_retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import RateLimitError

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
load_dotenv()
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_DOMAINS = ["github.com"]
CLONE_BASE_DIR = os.getenv("CLONE_BASE_DIR", "./repo")
INDEX_FILE = os.getenv("INDEX_FILE", "./index.faiss")
EMBEDS_CACHE = os.getenv("EMBEDS_CACHE", "embeds_cache.pkl")
STRUCTURE_CACHE = os.getenv("STRUCTURE_CACHE", "structure_cache.pkl")

# Global structure storage
repo_structures = {}


def list_all_files(root_dir: str) -> list[str]:
    """
    Walk `root_dir` and return a list of all file paths,
    relative to `root_dir`, using forward-slashes.
    """
    files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            # build the relative posix path
            rel = os.path.relpath(os.path.join(dirpath, fn), root_dir)
            files.append(rel.replace(os.sep, "/"))
    return files


def _find_docs_root():
    """
    Locate the first 'docs' directory under any cloned repo in CLONE_BASE_DIR.
    """
    print(f"Looking for docs directory in {CLONE_BASE_DIR}")

    if not os.path.isdir(CLONE_BASE_DIR):
        print(f"Clone base directory does not exist: {CLONE_BASE_DIR}")
        return None

    repos = sorted(os.listdir(CLONE_BASE_DIR))
    if not repos:
        print(f"No repositories found in {CLONE_BASE_DIR}")
        return None

    print(f"Found repositories: {repos}")

    for repo in repos:
        repo_dir = os.path.join(CLONE_BASE_DIR, repo)
        if not os.path.isdir(repo_dir):
            continue

        docs_dir = os.path.join(repo_dir, "docs")
        if os.path.isdir(docs_dir):
            print(f"Found docs directory at: {docs_dir}")
            return docs_dir

    print("No docs directory found in any repository")
    return None


def _build_tree(dir_path, rel_root):
    """
    Recursively build a JSON tree for directory at dir_path.
    Paths for files are made relative to rel_root, using forward-slashes.
    """
    tree = {"name": os.path.basename(dir_path), "type": "directory", "children": []}
    for entry in sorted(os.listdir(dir_path)):
        full = os.path.join(dir_path, entry)
        if os.path.isdir(full):
            tree["children"].append(_build_tree(full, rel_root))
        else:
            relpath = os.path.relpath(full, rel_root).replace(os.sep, "/")
            tree["children"].append({"name": entry, "type": "file", "path": relpath})
    return tree


# ----------------------------------------------------------------------------
# OpenAI client
# ----------------------------------------------------------------------------
client = OpenAI(api_key=OPENAI_API_KEY)

# allow 1 call per second
CALLS = 1
PERIOD = 2  # in seconds
MAX_RETRIES = 5


@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def generate_doc(
    prompt: str, model: str = "openai/gpt-4.1-nano", temperature: float = 0
) -> str:
    """
    Thin wrapper around OpenAI chat completion:
      - rate-limited to 1 req/sec
      - retries on HTTP 429 with exponential backoff
    """
    backoff = 1
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            chat = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": prompt}],
                temperature=temperature,
            )
            return chat.choices[0].message.content

        except RateLimitError as e:
            if attempt == MAX_RETRIES:
                # give up, re-raise
                raise
            # wait, then retry
            time.sleep(backoff)
            backoff *= 2  # exponential backoff

    # should never hit this
    raise RuntimeError("Failed to generate doc after retries")


# ----------------------------------------------------------------------------
# Embed cache helpers
# ----------------------------------------------------------------------------
def fetch_structure(url: str, path: str, language: str):
    payload = {"path": path, "language": language}
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def format_node(node: dict, indent: int = 0) -> str:
    """
    Преобразует узел и его детей в человекочитаемый формат.
    """
    pad = "  " * indent
    lines = []
    ntype = node.get("type")
    name = node.get("name", "")
    if ntype == "directory":
        lines.append(f"{pad}📁 {name}/")
        for child in node.get("children", []):
            lines.append(format_node(child, indent + 1))
    elif ntype == "file":
        lines.append(f"{pad}📄 {name}")
        # функции
        for fn in node.get("functions", []):
            lines.append(f"{pad}  └─ fn: {fn}()")
        # классы и методы
        for cls in node.get("classes", []):
            lines.append(f"{pad}  └─ class: {cls.get('name')}")
            for m in cls.get("methods", []):
                lines.append(f"{pad}      └─ method: {m}()")
    else:
        # неизвестный тип
        lines.append(f"{pad}{name} ({ntype})")
    return "\n".join(lines)


def load_embed_cache():
    """
    Load the embedding cache from disk.

    Returns:
        dict: The embedding cache, or an empty dictionary if the cache file doesn't exist
    """
    if os.path.exists(EMBEDS_CACHE):
        with open(EMBEDS_CACHE, "rb") as f:
            return pickle.load(f)
    return {}


def save_embed_cache(cache):
    """
    Save the embedding cache to disk.

    Args:
        cache (dict): The embedding cache to save

    Returns:
        None
    """
    with open(EMBEDS_CACHE, "wb") as f:
        pickle.dump(cache, f)


# ----------------------------------------------------------------------------
# Chunk ID for caching
# ----------------------------------------------------------------------------
def chunk_id(item: dict) -> str:
    """
    Generate a unique identifier for a text chunk.

    Args:
        item (dict): Dictionary containing 'path' and 'chunk' keys

    Returns:
        str: A unique identifier string for the chunk
    """
    h = hashlib.sha256(item["chunk"].encode("utf-8")).hexdigest()
    return f"{item['path']}::{h}"


# ----------------------------------------------------------------------------
# Flask + Celery setup
# ----------------------------------------------------------------------------
def make_celery(app):
    """
    Create a Celery instance for the Flask application.

    This function configures Celery to work within the Flask application context.

    Args:
        app (Flask): The Flask application instance

    Returns:
        Celery: Configured Celery instance
    """
    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"],
        backend=app.config["CELERY_RESULT_BACKEND"],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


app = Flask(__name__)
CORS(app)
app.config.update(
    {
        "CELERY_BROKER_URL": BROKER_URL,
        "CELERY_RESULT_BACKEND": RESULT_BACKEND,
    }
)
celery = make_celery(app)


# ----------------------------------------------------------------------------
# ChatCore
# ----------------------------------------------------------------------------
class ChatCore:
    """
    Core class for repository ingestion, embedding, and QA.
    """

    def __init__(self, dim: int = 1536, index_path: str = None):
        index_file = index_path or INDEX_FILE
        parent = os.path.dirname(index_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.store = HybridStore(dim, index_path=index_file)
        try:
            self.store.load()
        except Exception:
            pass

    def ingest(self, repo_path: str) -> int:
        """
        Ingest a repository:
          1. Generate per-definition docs (parallel, rate-limited, with progress bar).
          2. Generate module-level docs (parallel, with progress bar).
          3. Embed ALL new chunks in one batch.
          4. Update vector store.
        """
        # Parse definitions and load cache
        all_defs = parse_directory(repo_path)
        cache = load_embed_cache()

        # Organize definitions by file
        defs_by_file = defaultdict(list)
        for d in all_defs:
            defs_by_file[d["path"]].append(d)

        # 1) Generate per-definition docs in parallel
        all_embeds = []
        new_items = []
        flat_defs = [(path, d) for path, defs in defs_by_file.items() for d in defs]

        with ThreadPoolExecutor(max_workers=5) as pool:

            def submit_def(path, d):
                rel_dir = os.path.relpath(os.path.dirname(path), repo_path)
                base = os.path.splitext(os.path.basename(path))[0]
                out_dir = os.path.join(repo_path, "docs", rel_dir, base)
                os.makedirs(out_dir, exist_ok=True)
                prompt = (
                    f"Пиши документацию на русском языке. "
                    f"Сгенерируйте подробную документацию для этого {d['type']} «{d['name']}»:\n"
                    f"```{d['code']}```"
                )
                return pool.submit(generate_doc, prompt), d, out_dir

            futures_defs = [submit_def(path, d) for path, d in flat_defs]
            for future, d, out_dir in tqdm(
                ((fut, d, out_dir) for fut, d, out_dir in futures_defs),
                total=len(futures_defs),
                desc="Generating per-definition docs",
            ):
                doc_text = future.result()
                out_file = os.path.join(out_dir, f"{d['name']}.md")
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(doc_text)

                item = {"path": f"{d['path']}::{d['name']}", "chunk": doc_text}
                cid = chunk_id(item)
                if cid in cache:
                    all_embeds.append(
                        {
                            "path": item["path"],
                            "chunk": cache[cid]["chunk"],
                            "vector": cache[cid]["vector"],
                        }
                    )
                else:
                    new_items.append({**item, "cid": cid})

        # 2) Generate module-level docs in parallel
        module_paths = list(defs_by_file.keys())
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures_mods = {}
            for path in module_paths:
                rel_dir = os.path.relpath(os.path.dirname(path), repo_path)
                base = os.path.splitext(os.path.basename(path))[0]
                out_dir = os.path.join(repo_path, "docs", rel_dir, base)
                os.makedirs(out_dir, exist_ok=True)
                with open(path, "r", encoding="utf-8") as f:
                    source = f.read()
                prompt = (
                    "Пиши документацию на русском языке. Сгенерируйте документацию "
                    f"высокого уровня для этого модуля «{base}»:\n```\n{source}\n```"
                )
                futures_mods[pool.submit(generate_doc, prompt)] = (path, out_dir)

            for future in tqdm(
                as_completed(futures_mods),
                total=len(futures_mods),
                desc="Generating module-level docs",
            ):
                path, out_dir = futures_mods[future]
                file_doc = future.result()
                out_file = os.path.join(out_dir, "__file__.md")
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(file_doc)

                item = {"path": f"{path}::file", "chunk": file_doc}
                cid = chunk_id(item)
                if cid in cache:
                    all_embeds.append(
                        {
                            "path": item["path"],
                            "chunk": cache[cid]["chunk"],
                            "vector": cache[cid]["vector"],
                        }
                    )
                else:
                    new_items.append({**item, "cid": cid})

        # 3) Embed all new chunks in one batch
        if new_items:
            to_embed = [{"path": it["path"], "chunk": it["chunk"]} for it in new_items]
            embeds = embed_texts(to_embed)
            for it, e in zip(new_items, embeds):
                cache[it["cid"]] = {"vector": e["vector"], "chunk": e["chunk"]}
                all_embeds.append(e)
            save_embed_cache(cache)

        # 4) Update vector store
        self.store.add_embeddings(all_embeds)
        self.store.build_index()
        self.store.build_bm25()
        self.store.persist()

        return len(all_defs)

    def answer(self, query: str) -> str:
        """
        Answer a user query about the repository.
        """
        resp = client.embeddings.create(input=query, model="text-embedding-3-small")
        qvec = resp.data[0].embedding
        q_tokens = query.split()
        snips = self.store.query(qvec, q_tokens, top_k=5)

        prompt = """Вы — многоязычный ассистент по документации кода. При ответе строго опирайтесь 
на приведённые ниже документы и примеры кода. Если информация в контекстах отсутствует, 
ответьте: «Извините, у меня нет достаточных данных для ответа на этот вопрос.»"""
        for s in snips:
            prompt += f"### {s['path']}\n{s['chunk']}\n\n"
        prompt += f"Вопрос пользователя: {query}\nОтвет:"

        chat = client.chat.completions.create(
            model="openai/gpt-4.1-nano",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.2,
        )
        return chat.choices[0].message.content


# initialize core
core = ChatCore()


def format_node(node: dict, indent: int = 0) -> str:
    """
    Преобразует узел и его детей в человекочитаемый формат.
    """
    pad = "  " * indent
    lines = []
    ntype = node.get("type")
    name = node.get("name", "")
    if ntype == "directory":
        lines.append(f"{pad}📁 {name}/")
        for child in node.get("children", []):
            lines.append(format_node(child, indent + 1))
    elif ntype == "file":
        lines.append(f"{pad}📄 {name}")
        # функции
        for fn in node.get("functions", []):
            lines.append(f"{pad}  └─ fn: {fn}()")
        # классы и методы
        for cls in node.get("classes", []):
            lines.append(f"{pad}  └─ class: {cls.get('name')}")
            for m in cls.get("methods", []):
                lines.append(f"{pad}      └─ method: {m}()")
    else:
        # неизвестный тип
        lines.append(f"{pad}{name} ({ntype})")
    return "\n".join(lines)


def save_readable(structure: dict):
    text = format_node(structure)
    return text


# ----------------------------------------------------------------------------
# Utility
# ----------------------------------------------------------------------------
def is_allowed_repo(repo_url: str) -> bool:
    """
    Check if the repository domain is allowed for cloning.

    Args:
        repo_url (str): The repository URL to check

    Returns:
        bool: True if the domain is allowed, False otherwise
    """
    host = urlparse(repo_url).netloc.lower()
    return any(host.endswith(d) for d in ALLOWED_DOMAINS)


# ----------------------------------------------------------------------------
# Celery task
# ----------------------------------------------------------------------------
@celery.task(bind=True)
def clone_and_ingest(
    self, repo_url: str, branchName: str = "main", github_token: str = None
):
    """
    Clone and ingest a repository as a background task.

    This task:
    1. Validates the repository URL
    2. Clones the repository directly to CLONE_BASE_DIR/{repo_name}
    3. Ingests the repository code

    Args:
        self: Celery task instance
        repo_url (str): URL of the Git repository to clone
        branchName (str): Branch to clone (default: main)
        github_token (str): Optional GitHub token for private repos

    Returns:
        dict: Information about the ingested repository

    Raises:
        ValueError: If the repository domain is not allowed
        RuntimeError: If the Git clone operation fails
    """

    if not is_allowed_repo(repo_url):
        raise ValueError(f"Domain not allowed: {repo_url}")
    try:
        # Ensure CLONE_BASE_DIR exists
        os.makedirs(CLONE_BASE_DIR, exist_ok=True)

        # Derive repo name and clone target path
        name = os.path.basename(repo_url.rstrip("/")).removesuffix(".git")
        target = os.path.join(CLONE_BASE_DIR, name)

        # Remove target if it already exists
        if os.path.exists(target):
            shutil.rmtree(target)

        print(f"Cloning {repo_url} to {target}")
        # Clone repository
        Repo.clone_from(
            repo_url,
            target,
            branch=branchName,
            single_branch=True,
        )
        print(f"Cloned {repo_url} branch {branchName} to {target}")

        graph_flask_url = "http://127.0.0.1:8001"
        payload = {"path": "../" + "repo-chat-mvp" + target[1:]}

        response = requests.post(f"{graph_flask_url}/structure", json=payload)

        all_paths = list_all_files(target)
        repo_structures[name] = all_paths

        # Extract owner and repo for GitHub API call
        parsed = urlparse(repo_url)
        owner_repo = parsed.path.strip("/").removesuffix(".git")  # e.g., "owner/repo"
        # Ingest repository contents
        count = core.ingest(target)

        return {"repo": name, "items": count}
    except GitCommandError as e:
        raise RuntimeError("Git clone failed: " + str(e))
    finally:
        pass


# ----------------------------------------------------------------------------
# Flask endpoints
# ----------------------------------------------------------------------------
@app.route("/api/clone", methods=["POST"])
def enqueue_clone():
    """
    Enqueue a repository cloning and ingestion task.

    ---
    tags:
      - Repository Management
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - repo_url
          properties:
            repo_url:
              type: string
              description: URL of the Git repository to clone
    responses:
      202:
        description: Task successfully enqueued
        schema:
          type: object
          properties:
            job_id:
              type: string
              description: ID of the asynchronous task
      400:
        description: Invalid request parameters or unsupported domain
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
    """
    data = request.get_json() or {}
    url = data.get("repo_url")
    branchName = data.get("branch")
    token = data.get("token")
    if not url:
        return jsonify({"error": "Missing repo_url"}), 400
    if not is_allowed_repo(url):
        return jsonify({"error": "Unsupported domain"}), 400
    job = clone_and_ingest.delay(url, branchName, token)
    return jsonify({"job_id": job.id}), 202


@app.route("/api/job/<job_id>", methods=["GET"])
def job_status(job_id):
    """
    Check the status of an asynchronous job.

    This endpoint queries the Celery backend for the status of a previously
    submitted task and returns details about its progress or results.

    ---
    tags:
      - Task Management
    parameters:
      - in: path
        name: job_id
        required: true
        type: string
        description: The ID of the job to check
    responses:
      200:
        description: Job status information
        schema:
          type: object
          properties:
            status:
              type: string
              description: Current status of the job (PENDING, STARTED, SUCCESS, FAILURE)
            result:
              type: object
              description: Result data if the job completed successfully
            error:
              type: string
              description: Error message if the job failed
      404:
        description: Job not found
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
    """
    task = clone_and_ingest.AsyncResult(job_id)
    if not task:
        return jsonify({"error": "Job not found"}), 404

    if task.state == "PENDING":
        response = {"status": "PENDING", "message": "Job is pending."}
    elif task.state == "FAILURE":
        response = {"status": "FAILURE", "error": str(task.info)}
    elif task.state == "SUCCESS":
        response = {"status": "SUCCESS", "result": task.get()}
    else:  # STARTED or other states
        response = {"status": task.state, "message": "Job is in progress."}

    return jsonify(response)


@app.route("/api/documentation/tree", methods=["GET"])
def documentation_tree():
    """
    Return the directory tree of the 'docs' folder in your cloned repo.
    """
    docs_root = _find_docs_root()

    if not docs_root:
        print("No docs directory found, returning mock tree for testing")

    # Make paths like "docs/..." relative to the parent of 'docs'
    docs_parent = os.path.dirname(docs_root)
    tree = _build_tree(docs_root, docs_parent)
    return jsonify(tree), 200


@app.route("/api/documentation/<path:filepath>", methods=["GET"])
def documentation_file(filepath):
    """
    Return raw contents of a file under the 'docs' folder.
    Example: GET /api/documentation/docs/API.md
    """
    print(f"Received request for file: {filepath}")

    docs_root = _find_docs_root()

    # If no docs directory exists or we can't find the file, return mock content for testing
    if not docs_root or filepath.startswith("docs/"):
        print(f"Using mock content for: {filepath}")

        # Generate mock content based on the filepath
        mock_content = generate_mock_content(filepath)
        if mock_content:
            return Response(mock_content, mimetype="text/plain; charset=utf-8"), 200

    if not docs_root:
        print("No docs directory found")
        return jsonify({"error": "No docs directory found"}), 404

    docs_parent = os.path.dirname(docs_root)

    # Strip 'docs/' prefix if present - we'll add it back properly
    if filepath.startswith("docs/"):
        filepath = filepath[5:]  # Remove 'docs/' prefix

    # Construct the full path properly
    safe_full = os.path.normpath(os.path.join(docs_root, filepath))

    print(f"Looking for file at: {safe_full}")

    # Security check - make sure we're not accessing files outside the docs directory
    if not safe_full.startswith(docs_root):
        print(f"Security error: Path {safe_full} is outside docs root {docs_root}")
        return jsonify({"error": "Security error: Invalid file path"}), 400

    if not os.path.isfile(safe_full):
        print(f"File not found: {safe_full}")
        return Response(mock_content, mimetype="text/plain; charset=utf-8"), 200

        return jsonify({"error": f"File not found: {filepath}"}), 404

    # Read and return as plain text (Markdown)
    try:
        with open(safe_full, "r", encoding="utf-8") as f:
            data = f.read()
        print(f"Successfully read file: {filepath}")
        return Response(data, mimetype="text/plain; charset=utf-8"), 200
    except Exception as e:
        print(f"Error reading file {safe_full}: {str(e)}")
        return jsonify({"error": f"Error reading file: {str(e)}"}), 500


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    """
    Answer a question about the repository's code.

    This endpoint accepts a user message, processes it through the ChatCore,
    and returns a response generated by the language model based on relevant
    documentation from the repository.

    ---
    tags:
      - Chat
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - message
          properties:
            message:
              type: string
              description: User's question about the repository
    responses:
      200:
        description: Successful response
        schema:
          type: object
          properties:
            response:
              type: string
              description: AI-generated answer to the user's question
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
    """
    data = request.json or {}
    msg = data.get("message", "")
    if not msg:
        return jsonify({"error": "Message is required"}), 400
    try:
        resp = core.answer(msg)
        return jsonify({"response": resp})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        # This won't actually execute; needs to be run via 'celery -A tmp_chat.celery worker'
        pass
    else:
        # Run the Flask app
        app.run(debug=True, port=5001)
