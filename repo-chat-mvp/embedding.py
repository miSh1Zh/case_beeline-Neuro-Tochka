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
    Batch-embed a list of text chunks using the OpenAI embedding API.
    
    This function sends texts to the OpenAI API to generate vector embeddings for each chunk.
    The embeddings can be used for semantic search and similarity comparisons.
    
    Args:
        texts (list[dict]): List of dictionaries, each containing 'path' and 'chunk' keys.
            path: The file path or identifier for the text.
            chunk: The actual text content to be embedded.
        model (str, optional): The embedding model to use. 
            Defaults to "emb-openai/text-embedding-3-small".
    
    Returns:
        list[dict]: The same list of dictionaries with 'vector' field added to each item.
            path: Original path/identifier.
            chunk: Original text chunk.
            vector: The embedding vector from the API.
    
    Raises:
        Exception: If the OpenAI API request fails.
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
