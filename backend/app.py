from src.data_loader import load_all_documents
from src.vectorstore import FaissVectorStore
from src.search import RAGSearch


if __name__ == "__main__":
    
    docs = load_all_documents("docustore/pdf")
    store = FaissVectorStore("data/faiss_store")
    #store.build_from_documents(docs)
    store.load()
    print(store.query("Order to pay compensation.", top_k=3))
    rag_search = RAGSearch()
    query = "Duty of crew in public service vehicle."
    summary = rag_search.search_and_summarize(query, top_k=3)
    print("Summary:", summary)
