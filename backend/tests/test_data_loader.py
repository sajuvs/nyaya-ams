"""Tests for data_loader module."""

import pytest
import tempfile
from pathlib import Path
from src.data_loader import load_all_documents


def test_load_all_documents_empty_dir():
    """Test loading from empty directory returns empty list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs = load_all_documents(tmpdir)
        assert docs == []


def test_load_all_documents_nonexistent_dir():
    """Test loading from nonexistent directory returns empty list."""
    docs = load_all_documents("/nonexistent/path")
    assert docs == []


def test_load_all_documents_txt_file():
    """Test loading a text file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text("Sample legal document content")
        
        docs = load_all_documents(tmpdir)
        assert len(docs) == 1
        assert "Sample legal document content" in docs[0].page_content


def test_load_all_documents_multiple_files():
    """Test loading multiple text files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "doc1.txt").write_text("Document 1")
        (Path(tmpdir) / "doc2.txt").write_text("Document 2")
        
        docs = load_all_documents(tmpdir)
        assert len(docs) == 2
