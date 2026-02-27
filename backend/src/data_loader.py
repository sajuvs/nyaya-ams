"""Data Loader Module for Nyaya-Flow Legal Aid Platform.

This module provides functionality to load and process various document formats
for the RAG (Retrieval-Augmented Generation) pipeline. It supports multiple file
types including PDF, TXT, CSV, Excel, Word, and JSON documents.

Functionalities:
    - Multi-format document loading (PDF, TXT, CSV, XLSX, DOCX, JSON)
    - Recursive directory traversal for document discovery
    - Automatic conversion to LangChain document structure
    - Comprehensive error handling and debug logging
    - Support for Indian legal documents and statutes

Typical Usage:
    from backend.rag.data_loader import load_all_documents
    
    documents = load_all_documents("backend/data")
    print(f"Loaded {len(documents)} documents for processing")
"""

from pathlib import Path
from typing import List, Any
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from langchain_community.document_loaders import JSONLoader

def load_all_documents(data_dir: str) -> List[Any]:
    """Load all supported document files from the specified directory.
    
    Recursively scans the data directory for supported file formats and converts
    them into LangChain document objects for downstream RAG processing. Each document
    is loaded with its metadata preserved for citation and traceability.
    
    Args:
        data_dir (str): Path to the directory containing documents to load.
                       Can be relative or absolute path.
    
    Returns:
        List[Any]: List of LangChain Document objects containing page_content and metadata.
                   Returns empty list if no documents found or directory doesn't exist.
    
    Supported Formats:
        - PDF (.pdf): Legal statutes, case laws, petitions
        - Text (.txt): Plain text legal documents
        - CSV (.csv): Structured legal data, case records
        - Excel (.xlsx): Tabular legal information
        - Word (.docx): Draft petitions, legal briefs
        - JSON (.json): Structured legal metadata
    
    Example:
        >>> docs = load_all_documents("backend/data")
        >>> print(f"Loaded {len(docs)} documents")
        >>> print(docs[0].page_content[:100])
    
    Note:
        - Errors during individual file loading are caught and logged
        - Processing continues even if some files fail to load
        - Debug logs track the loading progress for each file type
    """
    data_path = Path(data_dir).resolve()
    
    if not data_path.exists():
        print(f"[ERROR] Data directory does not exist: {data_path}")
        return []
    
    print(f"[DEBUG] Data path: {data_path}")
    documents = []

    # PDF files
    pdf_files = list(data_path.glob('**/*.pdf'))
    print(f"[DEBUG] Found {len(pdf_files)} PDF files: {[str(f) for f in pdf_files]}")
    for pdf_file in pdf_files:
        print(f"[DEBUG] Loading PDF: {pdf_file}")
        try:
            loader = PyPDFLoader(str(pdf_file))
            loaded = loader.load()
            print(f"[DEBUG] Loaded {len(loaded)} PDF docs from {pdf_file}")
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Failed to load PDF {pdf_file}: {e}")

    # TXT files
    txt_files = list(data_path.glob('**/*.txt'))
    print(f"[DEBUG] Found {len(txt_files)} TXT files: {[str(f) for f in txt_files]}")
    for txt_file in txt_files:
        print(f"[DEBUG] Loading TXT: {txt_file}")
        try:
            loader = TextLoader(str(txt_file), encoding='utf-8')
            loaded = loader.load()
            print(f"[DEBUG] Loaded {len(loaded)} TXT docs from {txt_file}")
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Failed to load TXT {txt_file}: {e}")

    # CSV files
    csv_files = list(data_path.glob('**/*.csv'))
    print(f"[DEBUG] Found {len(csv_files)} CSV files: {[str(f) for f in csv_files]}")
    for csv_file in csv_files:
        print(f"[DEBUG] Loading CSV: {csv_file}")
        try:
            loader = CSVLoader(str(csv_file))
            loaded = loader.load()
            print(f"[DEBUG] Loaded {len(loaded)} CSV docs from {csv_file}")
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Failed to load CSV {csv_file}: {e}")

    # Excel files
    xlsx_files = list(data_path.glob('**/*.xlsx'))
    print(f"[DEBUG] Found {len(xlsx_files)} Excel files: {[str(f) for f in xlsx_files]}")
    for xlsx_file in xlsx_files:
        print(f"[DEBUG] Loading Excel: {xlsx_file}")
        try:
            loader = UnstructuredExcelLoader(str(xlsx_file))
            loaded = loader.load()
            print(f"[DEBUG] Loaded {len(loaded)} Excel docs from {xlsx_file}")
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Failed to load Excel {xlsx_file}: {e}")

    # Word files
    docx_files = list(data_path.glob('**/*.docx'))
    print(f"[DEBUG] Found {len(docx_files)} Word files: {[str(f) for f in docx_files]}")
    for docx_file in docx_files:
        print(f"[DEBUG] Loading Word: {docx_file}")
        try:
            loader = Docx2txtLoader(str(docx_file))
            loaded = loader.load()
            print(f"[DEBUG] Loaded {len(loaded)} Word docs from {docx_file}")
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Failed to load Word {docx_file}: {e}")

    # JSON files
    json_files = list(data_path.glob('**/*.json'))
    print(f"[DEBUG] Found {len(json_files)} JSON files: {[str(f) for f in json_files]}")
    for json_file in json_files:
        print(f"[DEBUG] Loading JSON: {json_file}")
        try:
            loader = JSONLoader(str(json_file), jq_schema='.', text_content=False)
            loaded = loader.load()
            print(f"[DEBUG] Loaded {len(loaded)} JSON docs from {json_file}")
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Failed to load JSON {json_file}: {e}")

    print(f"[DEBUG] Total loaded documents: {len(documents)}")
    return documents

# Example usage
if __name__ == "__main__":
    docs = load_all_documents("../docustore/pdf")
    print(f"Loaded {len(docs)} documents.")
    print("Example document:", docs[0] if docs else None)