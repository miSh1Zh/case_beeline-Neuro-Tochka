# embedding.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPEN_AI_API_KEY = os.getenv("OPENAI_API_KEY")
print("OPEN_AI_API_KEY", OPEN_AI_API_KEY)
client = OpenAI(
    api_key=OPEN_AI_API_KEY,
    base_url="https://api.vsegpt.ru/v1/",
)


def embed_texts(
    texts: list[dict], model: str = "emb-openai/text-embedding-3-small"
) -> list[dict]:
    """
    Batch-embed a list of {'path','chunk'} dicts.
    Returns same list with 'vector' added.
    """
    chunks = [t["chunk"] for t in texts]
    resp = client.embeddings.create(input=chunks, model=model)
    out = []
    for item, data in zip(texts, resp.data):
        out.append(
            {
                "path": item["path"],
                "chunk": item["chunk"],
                "vector": data.embedding,
            }
        )
    return out
