"""RAG Search Module for Nyaya-Flow Legal Aid Platform.

This module implements Retrieval-Augmented Generation (RAG) for legal document search
and summarization. It combines semantic search with LLM-powered summarization to provide
accurate, context-aware legal assistance.

Functionalities:
    - Semantic search over legal document corpus using FAISS
    - Context retrieval from vector store
    - LLM-powered summarization using Groq API
    - Automatic vector store initialization and loading

Groq Integration:
    Groq provides ultra-fast LLM inference through their API. This module uses ChatGroq
    to access models like Llama 3.3 for generating legal summaries. Groq's optimized
    infrastructure enables real-time responses for legal queries.
    
    Benefits:
        - Fast inference (10x faster than traditional APIs)
        - Cost-effective for high-volume queries
        - Support for large context windows (ideal for legal documents)
        - Multiple open-source models available

Typical Usage:
    from backend.src.search import RAGSearch
    
    rag = RAGSearch()
    summary = rag.search_and_summarize("IPC Section 420 fraud cases", top_k=5)
    print(summary)
"""

import os
from dotenv import load_dotenv
from src.vectorstore import FaissVectorStore
from langchain_groq import ChatGroq

load_dotenv()

class RAGSearch:
    """RAG-based search and summarization for legal documents.
    
    Combines FAISS vector search with Groq LLM to retrieve relevant legal content
    and generate contextual summaries. Automatically manages vector store lifecycle.
    
    Attributes:
        vectorstore (FaissVectorStore): FAISS vector store for semantic search.
        llm (ChatGroq): Groq LLM client for text generation.
    """
    
    def __init__(self, persist_dir: str = "data/faiss_store", embedding_model: str = "all-MiniLM-L6-v2", llm_model: str = "llama-3.3-70b-versatile"):
        """Initialize RAG search with vector store and LLM.
        
        Loads existing vector store if available, otherwise builds from documents.
        Initializes Groq LLM client for summarization.
        
        Args:
            persist_dir (str): Directory for FAISS index storage. Defaults to "data/faiss_store".
            embedding_model (str): Sentence-transformer model. Defaults to "all-MiniLM-L6-v2".
            llm_model (str): Groq model name. Defaults to "llama-3.3-70b-versatile".
        
        Note:
            Requires GROQ_API_KEY environment variable to be set.
        """
        self.vectorstore = FaissVectorStore(persist_dir, embedding_model)
        # Load or build vectorstore
        faiss_path = os.path.join(persist_dir, "faiss.index")
        meta_path = os.path.join(persist_dir, "metadata.pkl")
        if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
            from src.data_loader import load_all_documents
            docs = load_all_documents("../docustore/pdf")
            self.vectorstore.build_from_documents(docs)
        else:
            self.vectorstore.load()
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=llm_model)
        print(f"[INFO] Groq LLM initialized: {llm_model}")

    def search_and_summarize(self, query: str, top_k: int = 5) -> str:
        """Search legal documents and generate AI-powered summary.
        
        Performs semantic search to retrieve relevant document chunks, then uses
        Groq LLM to generate a coherent summary based on the retrieved context.
        
        Args:
            query (str): Natural language legal query (e.g., "Kerala land acquisition laws").
            top_k (int): Number of most relevant chunks to retrieve. Defaults to 5.
        
        Returns:
            str: AI-generated summary of relevant legal content, or error message if no results.
        
        Example:
            >>> rag = RAGSearch()
            >>> summary = rag.search_and_summarize("Motor Vehicle Act penalties", top_k=3)
            >>> print(summary)
        
        Note:
            Uses Groq's fast inference for real-time legal assistance.
        """
        results = self.vectorstore.query(query, top_k=top_k)
        texts = [r["metadata"].get("text", "") for r in results if r["metadata"]]
        context = "\n\n".join(texts)
        if not context:
            return "No relevant documents found."
        prompt = f"""Summarize the following context for the query: '{query}'\n\nContext:\n{context}\n\nSummary:"""
        response = self.llm.invoke([prompt])
        return response.content

# Example usage
if __name__ == "__main__":
    rag_search = RAGSearch()
    query = "Tamil Nadu Womens Harassment Act"
    summary = rag_search.search_and_summarize(query, top_k=3)
    print("Summary:", summary)