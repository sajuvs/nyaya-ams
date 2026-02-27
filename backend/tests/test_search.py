"""Tests for search module."""

import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from src.search import RAGSearch


@pytest.fixture
def temp_store_dir():
    """Create temporary directory for vector store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@patch('src.search.ChatGroq')
@patch('src.search.FaissVectorStore')
def test_rag_search_initialization(mock_vectorstore, mock_llm, temp_store_dir):
    """Test RAGSearch initializes correctly."""
    mock_store_instance = Mock()
    mock_vectorstore.return_value = mock_store_instance
    
    rag = RAGSearch(persist_dir=temp_store_dir)
    
    assert rag.vectorstore is not None
    mock_vectorstore.assert_called_once()


@patch('src.search.ChatGroq')
@patch('src.search.FaissVectorStore')
def test_search_and_summarize_with_results(mock_vectorstore, mock_llm, temp_store_dir):
    """Test search and summarize with valid results."""
    mock_store_instance = Mock()
    mock_store_instance.query.return_value = [
        {"metadata": {"text": "IPC Section 420 deals with fraud"}},
        {"metadata": {"text": "Punishment includes imprisonment"}}
    ]
    mock_vectorstore.return_value = mock_store_instance
    
    mock_llm_instance = Mock()
    mock_response = Mock()
    mock_response.content = "Summary of fraud laws"
    mock_llm_instance.invoke.return_value = mock_response
    mock_llm.return_value = mock_llm_instance
    
    rag = RAGSearch(persist_dir=temp_store_dir)
    result = rag.search_and_summarize("fraud laws", top_k=2)
    
    assert result == "Summary of fraud laws"
    mock_store_instance.query.assert_called_once_with("fraud laws", top_k=2)


@patch('src.search.ChatGroq')
@patch('src.search.FaissVectorStore')
def test_search_and_summarize_no_results(mock_vectorstore, mock_llm, temp_store_dir):
    """Test search and summarize with no results."""
    mock_store_instance = Mock()
    mock_store_instance.query.return_value = []
    mock_vectorstore.return_value = mock_store_instance
    
    rag = RAGSearch(persist_dir=temp_store_dir)
    result = rag.search_and_summarize("nonexistent query")
    
    assert result == "No relevant documents found."
