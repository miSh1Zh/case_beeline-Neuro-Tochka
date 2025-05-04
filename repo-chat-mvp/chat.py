import os
import sys
import pickle
import hashlib
from collections import defaultdict

from dotenv import load_dotenv
from openai import OpenAI
from ingestion import parse_directory  # updated to support multiple languages
from embedding import embed_texts
from vector_store import HybridStore
from tqdm import tqdm
from flask import Flask, request, jsonify
from flask_cors import CORS
from git import Repo, GitCommandError

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
print("API_KEY", API_KEY)
client = OpenAI(
    api_key=os.getenv(
        "OPENAI_API_KEY",
    ),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.vsegpt.ru/v1"),
)

EMBEDS_CACHE = "embeds_cache.pkl"

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


def load_embed_cache():
    if os.path.exists(EMBEDS_CACHE):
        with open(EMBEDS_CACHE, "rb") as f:
            return pickle.load(f)
    return {}


def save_embed_cache(cache):
    with open(EMBEDS_CACHE, "wb") as f:
        pickle.dump(cache, f)


def chunk_id(item: dict) -> str:
    h = hashlib.sha256(item["chunk"].encode("utf-8")).hexdigest()
    return f"{item['path']}::{h}"


class ChatCore:
    def __init__(self, dim=1536):
        self.store = HybridStore(dim)

    def ingest(self, repo_path: str):
        # Parse all supported files in the repo
        all_defs = parse_directory(repo_path)

        cache = load_embed_cache()
        all_embeds = []
        new_items = []

        # Group definitions by file for progress reporting
        defs_by_file = defaultdict(list)
        for d in all_defs:
            defs_by_file[d["path"]].append(d)

        # Per-definition documentation
        for path, defs in tqdm(defs_by_file.items(), desc="Processing files"):
            rel_dir = os.path.relpath(os.path.dirname(path), repo_path)
            base = os.path.splitext(os.path.basename(path))[0]
            out_dir = os.path.join(repo_path, "docs", rel_dir, base)
            os.makedirs(out_dir, exist_ok=True)

            for d in defs:
                prompt = (
                    f"Пиши документацию на русском языке. Сгенерируйте подробную документацию для этого {d['type']} «{d['name']}»:\n"
                    f"```\n{d['code']}\n```"
                )

                chat = client.chat.completions.create(
                    model="openai/gpt-4.1-nano",
                    messages=[{"role": "system", "content": prompt}],
                    temperature=0,
                )
                doc_text = chat.choices[0].message.content

                # Save per-definition doc
                out_file = os.path.join(out_dir, f"{d['name']}.md")
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(doc_text)

                # Prepare embedding
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

            # Whole-file overview documentation
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
                file_prompt = (
                    "Пиши документацию на русском языке. Сгенерируйте документацию высокого уровня (назначение, основные API, примечания по использованию, ключевые решения в дизайне) "
                    f"для этого модуля «{base}»:\n```\\n{source}\\n```"
                )

            chat = client.chat.completions.create(
                model="openai/gpt-4.1-nano",
                messages=[{"role": "system", "content": file_prompt}],
                temperature=0,
            )
            file_doc = chat.choices[0].message.content

            # Save file-level doc
            out_file = os.path.join(out_dir, "__file__.md")
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(file_doc)

            # Prepare file-level embedding
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

        # Embed new items in batches
        batches = [new_items[i : i + 50] for i in range(0, len(new_items), 50)]
        for batch in tqdm(batches, desc="Embedding docs"):
            to_embed = [{"path": it["path"], "chunk": it["chunk"]} for it in batch]
            embeds = embed_texts(to_embed)
            for it, e in zip(batch, embeds):
                cache[it["cid"]] = {"vector": e["vector"], "chunk": e["chunk"]}
                all_embeds.append(e)

        # Persist embeddings
        save_embed_cache(cache)
        self.store.add_embeddings(all_embeds)
        self.store.build_index()
        self.store.build_bm25()
        self.store.persist()

    def answer(self, query: str) -> str:
        # Embed the user query
        resp = client.embeddings.create(input=query, model="text-embedding-3-small")
        qvec = resp.data[0].embedding
        q_tokens = query.split()
        # Retrieve relevant docs
        snips = self.store.query(qvec, q_tokens, top_k=5)

        # Build prompt with context
        prompt = "Вы являетесь многоязычным ассистентом по документации кода. Овечай на запоросы пользователя подробно и с примерами из документации. Используйте эти документы:\n\n"
        for s in snips:
            prompt += f"### {s['path']}\n{s['chunk']}\n\n"
        prompt += f"Вопрос пользователя: {query}\nОтвет:"

        chat = client.chat.completions.create(
            model="openai/gpt-4.1-nano",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.2,
        )
        return chat.choices[0].message.content


@app.route("/api/clone", methods=["POST"])
def clone_repo():
    data = request.get_json() or {}
    repo_url = data.get("repo_url")
    token = data.get("token")

    if not repo_url:
        return jsonify({"error": "Missing 'repo_url'"}), 400

    # If token provided, inject it into the URL for HTTP(S) auth
    auth_url = repo_url
    if token:
        parts = repo_url.split("://", 1)
        if len(parts) != 2:
            return jsonify({"error": "Invalid repo_url format"}), 400
        scheme, path = parts
        auth_url = f"{scheme}://{token}@{path}"

    # Derive local folder name
    repo_name = repo_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    target_path = os.path.join(os.getcwd(), repo_name)

    if os.path.exists(target_path):
        return jsonify({"error": f"Directory '{repo_name}' already exists"}), 400

    try:
        Repo.clone_from(auth_url, target_path)
    except GitCommandError as e:
        return jsonify({"error": "Git clone failed", "details": str(e)}), 500

    return jsonify({"status": "cloned", "path": repo_name}), 200


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    data = request.json or {}
    msg = data.get("message", "")
    core = ChatCore()
    resp = core.answer(msg)
    return jsonify({"response": resp})


def main():
    if len(sys.argv) < 2:
        print("Usage: python chat.py <repo_path> [query]")
        sys.exit(1)

    repo = sys.argv[1]
    core = ChatCore()

    if len(sys.argv) == 2:
        core.ingest(repo)
    else:
        query = " ".join(sys.argv[2:])
        print(core.answer(query))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        app.run(debug=True, port=5001)
    else:
        main()
