# vector_store.py
import os
import faiss
import numpy as np
import pickle
from rank_bm25 import BM25Okapi


class HybridStore:
    """
    A hybrid vector-based and keyword-based search system.
    
    This class combines vector similarity search (using FAISS) with keyword search (using BM25)
    to provide more robust information retrieval. It handles embedding storage,
    indexing, persistence, and hybrid search capabilities.
    
    Attributes:
        dim (int): Dimensionality of the embedding vectors
        index_path (str): Path to store the FAISS index
        meta_path (str): Path to store metadata and BM25 model
        _vectors (list): Internal storage for embedding vectors
        metadata (list): List of document metadata
        bm25 (BM25Okapi): BM25 index for keyword search
        index (faiss.Index): FAISS index for vector search
    """

    def __init__(self, dim: int, index_path="index.faiss", meta_path="meta.pkl"):
        """
        Initialize a new HybridStore.
        
        Args:
            dim (int): Dimensionality of the embedding vectors
            index_path (str, optional): Path to store the FAISS index. Defaults to "index.faiss".
            meta_path (str, optional): Path to store metadata and BM25 model. Defaults to "meta.pkl".
        """
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
        """
        Add embedding vectors and their metadata to the store.
        
        Args:
            items (list[dict]): List of dictionaries, each containing:
                - 'vector': The embedding vector
                - 'path': Path or identifier for the document
                - 'chunk': Text content of the document
        
        Returns:
            None
        """
        for itm in items:
            self._vectors.append(np.array(itm["vector"], dtype="float32"))
            self.metadata.append({"path": itm["path"], "chunk": itm["chunk"]})

    def build_index(self):
        """
        Build the FAISS index from stored vectors.
        
        Creates either a flat L2 index for small collections (<1000 vectors)
        or an IVF index for larger collections, which is more efficient for search.
        
        Returns:
            None
        
        Raises:
            ValueError: If no vectors have been added to the store
        """
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
        """
        Build the BM25 index for keyword-based search.
        
        Tokenizes all document chunks and creates a BM25Okapi index for efficient
        keyword-based retrieval.
        
        Returns:
            None
        """
        tokenized = [doc["chunk"].split() for doc in self.metadata]
        self.bm25 = BM25Okapi(tokenized)

    def persist(self):
        """
        Save the FAISS index and metadata to disk.
        
        Writes the FAISS index to the index_path and serializes metadata and
        BM25 model to the meta_path.
        
        Returns:
            None
            
        Raises:
            RuntimeError: If the index hasn't been built
            IOError: If writing to files fails
        """
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump({"metadata": self.metadata, "bm25": self.bm25}, f)

    def query(self, q_vector, q_tokens, top_k=5, alpha=0.25):
        """
        Perform a hybrid search combining vector similarity and keyword matching.
        
        This method combines results from FAISS (vector similarity) and BM25 (keyword matching)
        to provide a more robust search experience. The alpha parameter controls the balance
        between the two approaches.
        
        Args:
            q_vector (list or numpy.ndarray): Query embedding vector
            q_tokens (list): Query tokens for BM25 search
            top_k (int, optional): Number of results to return. Defaults to 5.
            alpha (float, optional): Proportion of results to take from vector search,
                with (1-alpha) proportion from BM25. Defaults to 0.25.
        
        Returns:
            list: List of top_k dictionaries with 'path' and 'chunk' fields
            
        Raises:
            RuntimeError: If the index hasn't been built
        """
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
