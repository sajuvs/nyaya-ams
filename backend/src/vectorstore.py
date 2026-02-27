"""FAISS Vector Store Module for Nyaya-Flow Legal Aid Platform.

This module implements a vector database using FAISS (Facebook AI Similarity Search)
for efficient semantic search over legal documents. It handles document embedding,
indexing, persistence, and similarity-based retrieval for the RAG pipeline.

Functionalities:
    - Document chunking and embedding generation
    - FAISS index creation and management
    - Vector similarity search for legal document retrieval
    - Persistent storage and loading of vector indices
    - Metadata tracking for retrieved chunks

Typical Usage:
    from backend.rag.vector_store import FaissVectorStore
    from backend.rag.data_loader import load_all_documents
    
    docs = load_all_documents("backend/data")
    store = FaissVectorStore(persist_dir="faiss_store")
    store.build_from_documents(docs)
    results = store.query("Indian Penal Code Section 420", top_k=5)
"""

import os
import faiss
import numpy as np
import pickle
from typing import List, Any
from sentence_transformers import SentenceTransformer
from src.embedding import EmbeddingPipeline

class FaissVectorStore:
    """FAISS-based vector store for semantic search over legal documents.
    
    Manages the complete lifecycle of vector embeddings including creation, storage,
    and retrieval. Uses sentence-transformers for embedding generation and FAISS
    for efficient similarity search.
    
    Attributes:
        persist_dir (str): Directory path for storing FAISS index and metadata.
        index (faiss.Index): FAISS index for vector similarity search.
        metadata (List[dict]): List of metadata dictionaries for each indexed chunk.
        embedding_model (str): Name of the sentence-transformer model.
        model (SentenceTransformer): Loaded embedding model instance.
        chunk_size (int): Maximum characters per document chunk.
        chunk_overlap (int): Overlapping characters between consecutive chunks.
    """
    
    def __init__(self, persist_dir: str = "data/faiss_store", embedding_model: str = "all-MiniLM-L6-v2", chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the FAISS vector store with embedding configuration.
        
        Args:
            persist_dir (str): Directory to save/load FAISS index. Defaults to "faiss_store".
            embedding_model (str): Sentence-transformer model name. Defaults to "all-MiniLM-L6-v2".
            chunk_size (int): Maximum characters per chunk. Defaults to 1000.
            chunk_overlap (int): Overlapping characters between chunks. Defaults to 200.
        """
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        self.index = None
        self.metadata = []
        self.embedding_model = embedding_model
        self.model = SentenceTransformer(embedding_model)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        print(f"[INFO] Loaded embedding model: {embedding_model}")

    def build_from_documents(self, documents: List[Any]):
        """Build vector store from raw documents by chunking, embedding, and indexing.
        
        Processes documents through the complete pipeline: chunking into smaller segments,
        generating embeddings, adding to FAISS index, and persisting to disk.
        
        Args:
            documents (List[Any]): List of LangChain Document objects to process.
        
        Note:
            Automatically saves the index after building. Existing index is replaced.
        """
        print(f"[INFO] Building vector store from {len(documents)} raw documents...")
        emb_pipe = EmbeddingPipeline(model_name=self.embedding_model, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        chunks = emb_pipe.chunk_documents(documents)
        embeddings = emb_pipe.embed_chunks(chunks)
        metadatas = [{"text": chunk.page_content} for chunk in chunks]
        self.add_embeddings(np.array(embeddings).astype('float32'), metadatas)
        self.save()
        print(f"[INFO] Vector store built and saved to {self.persist_dir}")

    def add_embeddings(self, embeddings: np.ndarray, metadatas: List[Any] = None):
        """Add embedding vectors and their metadata to the FAISS index.
        
        Creates a new FAISS IndexFlatL2 if none exists, then adds vectors.
        IndexFlatL2 uses L2 (Euclidean) distance for similarity measurement.
        
        Args:
            embeddings (np.ndarray): Array of shape (n_vectors, dimension) with float32 dtype.
            metadatas (List[Any], optional): List of metadata dicts for each vector.
        """
        dim = embeddings.shape[1]
        if self.index is None:
            self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)
        if metadatas:
            self.metadata.extend(metadatas)
        print(f"[INFO] Added {embeddings.shape[0]} vectors to Faiss index.")

    def save(self):
        """Persist FAISS index and metadata to disk.
        
        Saves two files:
            - faiss.index: Binary FAISS index file
            - metadata.pkl: Pickled metadata list
        """
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")
        faiss.write_index(self.index, faiss_path)
        with open(meta_path, "wb") as f:
            pickle.dump(self.metadata, f)
        print(f"[INFO] Saved Faiss index and metadata to {self.persist_dir}")

    def load(self):
        """Load previously saved FAISS index and metadata from disk.
        
        Raises:
            FileNotFoundError: If index files don't exist in persist_dir.
        """
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")
        self.index = faiss.read_index(faiss_path)
        with open(meta_path, "rb") as f:
            self.metadata = pickle.load(f)
        print(f"[INFO] Loaded Faiss index and metadata from {self.persist_dir}")

    def search(self, query_embedding: np.ndarray, top_k: int = 5):
        """Search for similar vectors using a pre-computed query embedding.
        
        Args:
            query_embedding (np.ndarray): Query vector of shape (1, dimension).
            top_k (int): Number of nearest neighbors to retrieve. Defaults to 5.
        
        Returns:
            List[dict]: List of results with keys 'index', 'distance', and 'metadata'.
                       Lower distance indicates higher similarity.
        """
        D, I = self.index.search(query_embedding, top_k)
        results = []
        for idx, dist in zip(I[0], D[0]):
            meta = self.metadata[idx] if idx < len(self.metadata) else None
            results.append({"index": idx, "distance": dist, "metadata": meta})
        return results

    def query(self, query_text: str, top_k: int = 5):
        """Query the vector store using natural language text.
        
        Converts query text to embedding and retrieves most similar document chunks.
        Primary interface for semantic search in the RAG pipeline.
        
        Args:
            query_text (str): Natural language query (e.g., "IPC Section 420 fraud cases").
            top_k (int): Number of most relevant chunks to return. Defaults to 5.
        
        Returns:
            List[dict]: Ranked results with document chunks and similarity scores.
        
        Example:
            >>> results = store.query("Kerala land acquisition laws", top_k=3)
            >>> print(results[0]['metadata']['text'])
        """
        print(f"[INFO] Querying vector store for: '{query_text}'")
        query_emb = self.model.encode([query_text]).astype('float32')
        return self.search(query_emb, top_k=top_k)

# Example usage
if __name__ == "__main__":
    from src.data_loader import load_all_documents
    docs = load_all_documents("../docustore/pdf")
    store = FaissVectorStore("data/faiss_store")
    store.build_from_documents(docs)
    store.load()
    print(store.query("What is attention mechanism?", top_k=3))