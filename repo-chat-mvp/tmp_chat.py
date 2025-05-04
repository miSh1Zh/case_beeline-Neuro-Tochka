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
    if os.path.exists(EMBEDS_CACHE):
        with open(EMBEDS_CACHE, "rb") as f:
            return pickle.load(f)
    return {}


def save_embed_cache(cache):
    with open(EMBEDS_CACHE, "wb") as f:
        pickle.dump(cache, f)


# ----------------------------------------------------------------------------
# Chunk ID for caching
# ----------------------------------------------------------------------------
def chunk_id(item: dict) -> str:
    h = hashlib.sha256(item["chunk"].encode("utf-8")).hexdigest()
    return f"{item['path']}::{h}"


# ----------------------------------------------------------------------------
# Flask + Celery setup
# ----------------------------------------------------------------------------
def make_celery(app):
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
    def __init__(self, dim=1536, index_path=None):
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
    host = urlparse(repo_url).netloc.lower()
    return any(host.endswith(d) for d in ALLOWED_DOMAINS)


# ----------------------------------------------------------------------------
# Celery task
# ----------------------------------------------------------------------------
@celery.task(bind=True)
def clone_and_ingest(self, repo_url: str):
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
    data = request.get_json() or {}
    url = data.get("repo_url")
    if not url:
        return jsonify({"error": "Missing repo_url"}), 400
    if not is_allowed_repo(url):
        return jsonify({"error": "Unsupported domain"}), 400
    job = clone_and_ingest.delay(url)
    return jsonify({"job_id": job.id}), 202


@app.route("/api/status/<job_id>", methods=["GET"])
def job_status(job_id):
    job = celery.AsyncResult(job_id)
    if job is None:
        return jsonify({"error": "Unknown job"}), 404
    return jsonify(
        {
            "status": job.status,
            "result": job.result if job.successful() else None,
            "error": str(job.result) if job.failed() else None,
        }
    )


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json() or {}
    msg = data.get("message", "")
    if not msg:
        return jsonify({"error": "Missing message"}), 400
    return jsonify({"response": core.answer(msg)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
