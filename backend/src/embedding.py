"""Embedding Pipeline Module for Nyaya-Flow Legal Aid Platform.

This module provides document chunking and embedding generation functionality
for the RAG pipeline. It processes legal documents into semantic vectors for
similarity search and retrieval.

Functionalities:
    - Document chunking with configurable size and overlap
    - Semantic embedding generation using sentence-transformers
    - Batch processing of document chunks
    - Support for legal document structure preservation

Typical Usage:
    from backend.src.embedding import EmbeddingPipeline
    
    pipeline = EmbeddingPipeline(chunk_size=1000, chunk_overlap=200)
    chunks = pipeline.chunk_documents(documents)
    embeddings = pipeline.embed_chunks(chunks)
"""

from typing import List, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
from src.data_loader import load_all_documents

class EmbeddingPipeline:
    """Pipeline for chunking documents and generating semantic embeddings.
    
    Handles the transformation of raw legal documents into vector representations
    suitable for semantic search in the RAG system.
    
    Attributes:
        chunk_size (int): Maximum characters per chunk.
        chunk_overlap (int): Overlapping characters between chunks.
        model (SentenceTransformer): Loaded embedding model.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the embedding pipeline.
        
        Args:
            model_name (str): Sentence-transformer model name. Defaults to "all-MiniLM-L6-v2".
            chunk_size (int): Maximum characters per chunk. Defaults to 1000.
            chunk_overlap (int): Overlapping characters between chunks. Defaults to 200.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model = SentenceTransformer(model_name)
        print(f"[INFO] Loaded embedding model: {model_name}")

    def chunk_documents(self, documents: List[Any]) -> List[Any]:
        """Split documents into smaller chunks for embedding.
        
        Uses recursive character splitting to preserve document structure while
        maintaining semantic coherence within chunks.
        
        Args:
            documents (List[Any]): List of LangChain Document objects.
        
        Returns:
            List[Any]: List of chunked Document objects with preserved metadata.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        print(f"[INFO] Split {len(documents)} documents into {len(chunks)} chunks.")
        return chunks

    def embed_chunks(self, chunks: List[Any]) -> np.ndarray:
        """Generate semantic embeddings for document chunks.
        
        Converts text chunks into dense vector representations using the
        sentence-transformer model.
        
        Args:
            chunks (List[Any]): List of chunked Document objects.
        
        Returns:
            np.ndarray: Array of embeddings with shape (n_chunks, embedding_dim).
        """
        texts = [chunk.page_content for chunk in chunks]
        print(f"[INFO] Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        print(f"[INFO] Embeddings shape: {embeddings.shape}")
        return embeddings

# Example usage
if __name__ == "__main__":
    
    docs = load_all_documents("../docustore/pdf")
    emb_pipe = EmbeddingPipeline()
    chunks = emb_pipe.chunk_documents(docs)
    embeddings = emb_pipe.embed_chunks(chunks)
    print("[INFO] Example embedding:", embeddings[0] if len(embeddings) > 0 else None)