"""Tests for embedding module."""

import pytest
import numpy as np
from unittest.mock import Mock
from src.embedding import EmbeddingPipeline


@pytest.fixture
def mock_documents():
    """Create mock LangChain documents."""
    doc1 = Mock()
    doc1.page_content = "This is a sample legal document about Indian Penal Code."
    doc1.metadata = {"source": "test.txt"}
    
    doc2 = Mock()
    doc2.page_content = "Another document discussing Kerala jurisdiction laws."
    doc2.metadata = {"source": "test2.txt"}
    
    return [doc1, doc2]


def test_embedding_pipeline_initialization():
    """Test EmbeddingPipeline initializes correctly."""
    pipeline = EmbeddingPipeline(chunk_size=500, chunk_overlap=100)
    assert pipeline.chunk_size == 500
    assert pipeline.chunk_overlap == 100
    assert pipeline.model is not None


def test_chunk_documents(mock_documents):
    """Test document chunking."""
    pipeline = EmbeddingPipeline(chunk_size=50, chunk_overlap=10)
    chunks = pipeline.chunk_documents(mock_documents)
    
    assert len(chunks) >= len(mock_documents)
    assert all(hasattr(chunk, 'page_content') for chunk in chunks)


def test_embed_chunks():
    """Test embedding generation."""
    pipeline = EmbeddingPipeline()
    
    mock_chunk = Mock()
    mock_chunk.page_content = "Sample text for embedding"
    
    embeddings = pipeline.embed_chunks([mock_chunk])
    
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape[0] == 1
    assert embeddings.shape[1] > 0
