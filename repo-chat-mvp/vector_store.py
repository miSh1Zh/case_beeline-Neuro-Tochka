# vector_store.py
import os
import faiss
import numpy as np
import pickle
from rank_bm25 import BM25Okapi


class HybridStore:
    def __init__(self, dim: int, index_path="faiss.index", meta_path="meta.pkl"):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path
        self._vectors = []
        self.metadata = []
        self.bm25 = None
        self.index = None

        # Load existing index and metadata if available
        if os.path.exists(index_path) and os.path.exists(meta_path):
            self.index = faiss.read_index(index_path)
            with open(meta_path, "rb") as f:
                saved = pickle.load(f)
                self.metadata = saved["metadata"]
                self.bm25 = saved["bm25"]

    def add_embeddings(self, items: list[dict]):
        for itm in items:
            self._vectors.append(np.array(itm["vector"], dtype="float32"))
            self.metadata.append({"path": itm["path"], "chunk": itm["chunk"]})

    def build_index(self):
        vecs = np.stack(self._vectors, axis=0)
        n = vecs.shape[0]
        if n < 1000:
            self.index = faiss.IndexFlatL2(self.dim)
        else:
            nlist = int(max(1, min(n, n // 39)))
            self.index = faiss.index_factory(
                self.dim, f"IVF{nlist},Flat", faiss.METRIC_L2
            )
            self.index.nprobe = min(10, nlist)
            self.index.train(vecs)
        self.index.add(vecs)

    def build_bm25(self):
        tokenized = [doc["chunk"].split() for doc in self.metadata]
        self.bm25 = BM25Okapi(tokenized)

    def persist(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump({"metadata": self.metadata, "bm25": self.bm25}, f)

    def query(self, q_vector, q_tokens, top_k=5, alpha=0.25):
        if self.index is None:
            raise RuntimeError("Index not built; call build_index() first")
        D, I = self.index.search(np.array([q_vector], dtype="float32"), top_k)
        faiss_hits = [self.metadata[i] for i in I[0]]
        bm25_scores = self.bm25.get_scores(q_tokens)
        top_bm25_idx = np.argsort(bm25_scores)[::-1][:top_k]
        bm25_hits = [self.metadata[i] for i in top_bm25_idx]
        n1 = int(top_k * alpha)
        merged = faiss_hits[:n1] + bm25_hits[: top_k - n1]
        seen, results = set(), []
        for doc in merged:
            key = (doc["path"], doc["chunk"][:30])
            if key not in seen:
                seen.add(key)
                results.append(doc)
        return results[:top_k]
