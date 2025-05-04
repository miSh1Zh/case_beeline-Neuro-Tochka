import os
import shutil
import tempfile
import pickle
import hashlib
from collections import defaultdict

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
from git import Repo, GitCommandError
from urllib.parse import urlparse

from flask import Flask, request, jsonify
from flask_cors import CORS
from celery import Celery

from ingestion import parse_directory
from embedding import embed_texts
from vector_store import HybridStore

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
load_dotenv()
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_DOMAINS = ["github.com"]
CLONE_BASE_DIR = os.getenv("CLONE_BASE_DIR", "./tmp")
INDEX_FILE = os.getenv("INDEX_FILE", "./index.faiss")
EMBEDS_CACHE = os.getenv("EMBEDS_CACHE", "embeds_cache.pkl")

# ----------------------------------------------------------------------------
# OpenAI client
# ----------------------------------------------------------------------------
client = OpenAI(api_key=OPENAI_API_KEY)


# ----------------------------------------------------------------------------
# Embed cache helpers
# ----------------------------------------------------------------------------
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
    Core class for the repository chat functionality.
    
    This class handles repository ingestion, embedding generation, and answering
    user queries about the repository code.
    
    Attributes:
        store (HybridStore): Vector store for hybrid search functionality
    """
    
    def __init__(self, dim=1536, index_path=None):
        """
        Initialize a new ChatCore instance.
        
        Args:
            dim (int, optional): Dimensionality of the embedding vectors. Defaults to 1536.
            index_path (str, optional): Path to load/save the index. Defaults to None.
        """
        index_file = index_path or INDEX_FILE
        parent = os.path.dirname(index_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.store = HybridStore(dim, index_path=index_file)
        try:
            self.store.load()
        except Exception:
            pass

    def ingest(self, repo_path: str):
        """
        Ingest a repository for semantic search and documentation generation.
        
        Args:
            repo_path (str): Path to the local repository
            
        Returns:
            int: Number of code elements processed
        """
        all_defs = parse_directory(repo_path)
        cache = load_embed_cache()
        all_embeds = []
        new_items = []

        defs_by_file = defaultdict(list)
        for d in all_defs:
            defs_by_file[d["path"]].append(d)

        for path, defs in tqdm(defs_by_file.items(), desc="Processing files"):
            rel_dir = os.path.relpath(os.path.dirname(path), repo_path)
            base = os.path.splitext(os.path.basename(path))[0]
            out_dir = os.path.join(repo_path, "docs", rel_dir, base)
            os.makedirs(out_dir, exist_ok=True)
            for d in defs:
                prompt = f"Пиши документацию на русском языке. Сгенерируйте подробную документацию для этого {d['type']} «{d['name']}»:\n```{d['code']}```"
                chat = client.chat.completions.create(
                    model="openai/gpt-4.1-nano",
                    messages=[{"role": "system", "content": prompt}],
                    temperature=0,
                )
                doc_text = chat.choices[0].message.content
                out_file = os.path.join(out_dir, f"{d['name']}.md")
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(doc_text)
                item = {"path": path + f"::{d['name']}", "chunk": doc_text}
                cid = chunk_id(item)
                if cid in cache:
                    vec = cache[cid]["vector"]
                    chunk = cache[cid]["chunk"]
                    all_embeds.append(
                        {"path": item["path"], "chunk": chunk, "vector": vec}
                    )
                else:
                    new_items.append({**item, "cid": cid})

            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
            file_prompt = (
                "Пиши документацию на русском языке. Сгенерируйте документацию высокого уровня"
                f" для этого модуля «{base}»:\n```\n{source}\n```"
            )
            chat = client.chat.completions.create(
                model="openai/gpt-4.1-nano",
                messages=[{"role": "system", "content": file_prompt}],
                temperature=0,
            )
            file_doc = chat.choices[0].message.content
            out_file = os.path.join(out_dir, "__file__.md")
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(file_doc)
            file_item = {"path": path + "::file", "chunk": file_doc}
            file_cid = chunk_id(file_item)
            if file_cid in cache:
                vec = cache[file_cid]["vector"]
                chunk = cache[file_cid]["chunk"]
                all_embeds.append(
                    {"path": file_item["path"], "chunk": chunk, "vector": vec}
                )
            else:
                new_items.append({**file_item, "cid": file_cid})

        batches = [new_items[i : i + 50] for i in range(0, len(new_items), 50)]
        for batch in tqdm(batches, desc="Embedding docs"):
            to_embed = [{"path": it["path"], "chunk": it["chunk"]} for it in batch]
            embeds = embed_texts(to_embed)
            for it, e in zip(batch, embeds):
                cache[it["cid"]] = {"vector": e["vector"], "chunk": e["chunk"]}
                all_embeds.append(e)

        save_embed_cache(cache)
        self.store.add_embeddings(all_embeds)
        self.store.build_index()
        self.store.build_bm25()
        self.store.persist()
        return len(all_defs)

    def answer(self, query: str) -> str:
        """
        Answer a user query about the repository.
        
        Args:
            query (str): The user's question about the repository
            
        Returns:
            str: The generated answer from the LLM
        """
        resp = client.embeddings.create(input=query, model="text-embedding-3-small")
        qvec = resp.data[0].embedding
        q_tokens = query.split()
        snips = self.store.query(qvec, q_tokens, top_k=5)
        prompt = "Вы являетесь многоязычным ассистентом по документации кода. Используйте эти документы:\n\n"
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
def clone_and_ingest(self, repo_url: str):
    """
    Clone and ingest a repository as a background task.
    
    This task:
    1. Validates the repository URL
    2. Creates a temporary directory for cloning
    3. Clones the repository
    4. Ingests the repository code
    5. Cleans up temporary files
    
    Args:
        self: Celery task instance
        repo_url (str): URL of the Git repository to clone
        
    Returns:
        dict: Information about the ingested repository
        
    Raises:
        ValueError: If the repository domain is not allowed
        RuntimeError: If the Git clone operation fails
    """
    if not is_allowed_repo(repo_url):
        raise ValueError(f"Domain not allowed: {repo_url}")
    tmpdir = tempfile.mkdtemp(dir=CLONE_BASE_DIR)
    try:
        name = os.path.basename(repo_url.rstrip("/")).removesuffix(".git")
        target = os.path.join(tmpdir, name)
        Repo.clone_from(repo_url, target)
        count = core.ingest(target)
        return {"repo": name, "items": count}
    except GitCommandError as e:
        raise RuntimeError("Git clone failed: " + str(e))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


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
    if not url:
        return jsonify({"error": "Missing repo_url"}), 400
    if not is_allowed_repo(url):
        return jsonify({"error": "Unsupported domain"}), 400
    job = clone_and_ingest.delay(url)
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
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        # This won't actually execute; needs to be run via 'celery -A tmp_chat.celery worker'
        pass
    else:
        # Run the Flask app
        app.run(debug=True, port=5001)
