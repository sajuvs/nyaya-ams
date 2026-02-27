"""Tests for vectorstore module."""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import Mock
from src.vectorstore import FaissVectorStore


@pytest.fixture
def temp_store_dir():
    """Create temporary directory for vector store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_vectorstore_initialization(temp_store_dir):
    """Test FaissVectorStore initializes correctly."""
    store = FaissVectorStore(persist_dir=temp_store_dir)
    assert store.persist_dir == temp_store_dir
    assert store.index is None
    assert store.metadata == []
    assert store.model is not None


def test_add_embeddings(temp_store_dir):
    """Test adding embeddings to FAISS index."""
    store = FaissVectorStore(persist_dir=temp_store_dir)
    embeddings = np.random.rand(5, 384).astype('float32')
    metadatas = [{"text": f"chunk {i}"} for i in range(5)]
    
    store.add_embeddings(embeddings, metadatas)
    
    assert store.index is not None
    assert len(store.metadata) == 5


def test_save_and_load(temp_store_dir):
    """Test saving and loading FAISS index."""
    store = FaissVectorStore(persist_dir=temp_store_dir)
    embeddings = np.random.rand(3, 384).astype('float32')
    metadatas = [{"text": f"doc {i}"} for i in range(3)]
    
    store.add_embeddings(embeddings, metadatas)
    store.save()
    
    assert Path(temp_store_dir, "faiss.index").exists()
    assert Path(temp_store_dir, "metadata.pkl").exists()
    
    new_store = FaissVectorStore(persist_dir=temp_store_dir)
    new_store.load()
    
    assert len(new_store.metadata) == 3


def test_query(temp_store_dir):
    """Test querying the vector store."""
    store = FaissVectorStore(persist_dir=temp_store_dir)
    embeddings = np.random.rand(10, 384).astype('float32')
    metadatas = [{"text": f"legal document {i}"} for i in range(10)]
    
    store.add_embeddings(embeddings, metadatas)
    
    results = store.query("test query", top_k=3)
    
    assert len(results) == 3
    assert all("metadata" in r for r in results)
    assert all("distance" in r for r in results)
