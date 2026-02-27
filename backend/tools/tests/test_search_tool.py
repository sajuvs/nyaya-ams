"""All tavily_search_tool edge cases with mocked Tavily API."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch
from tavily_tool import tavily_search_tool

# Access underlying function
search_func = tavily_search_tool.func


def _make_result(url, content, title="Test"):
    return {"url": url, "content": content, "title": title}


class TestDomainFiltering:
    @patch("tavily_tool.tavily_client")
    def test_filters_non_allowed_domains(self, mock_client):
        mock_client.search.return_value = {
            "results": [
                _make_result("https://randomsite.com/page", "Some legal content about the act and its provisions in detail here"),
                _make_result("https://prsindia.org/act/123", "The Kerala Act 2023 provides for public health regulation and governance in the state"),
            ]
        }
        result = search_func("test")
        assert result["total_results"] == 1
        assert "prsindia.org" in result["sources"][0]["url"]


class TestContentFiltering:
    @patch("tavily_tool.tavily_client")
    def test_skips_short_content(self, mock_client):
        mock_client.search.return_value = {
            "results": [
                _make_result("https://kerala.gov.in/x", "Too short"),
                _make_result("https://kerala.gov.in/y", "This is a proper legal document with enough content about the Kerala Public Health Act provisions"),
            ]
        }
        result = search_func("test")
        assert result["total_results"] == 1

    @patch("tavily_tool.tavily_client")
    def test_skips_non_english_content(self, mock_client):
        mock_client.search.return_value = {
            "results": [
                _make_result("https://kerala.gov.in/ml", "കേരള പൊതുജനാരോഗ്യ ആക്റ്റ് 2023 നിയമം"),
                _make_result("https://kerala.gov.in/en", "The Kerala Public Health Act 2023 was enacted to regulate communicable diseases and public health"),
            ]
        }
        result = search_func("test")
        assert result["total_results"] == 1
        assert "Public Health Act" in result["sources"][0]["content"]


class TestEdgeCases:
    @patch("tavily_tool.tavily_client")
    def test_empty_results(self, mock_client):
        mock_client.search.return_value = {"results": []}
        result = search_func("nonexistent law xyz")
        assert result["total_results"] == 0
        assert result["sources"] == []

    @patch("tavily_tool.tavily_client")
    def test_max_5_results(self, mock_client):
        mock_client.search.return_value = {
            "results": [
                _make_result(f"https://kerala.gov.in/page{i}", f"Legal content number {i} about the Kerala Act and its various provisions for governance")
                for i in range(10)
            ]
        }
        result = search_func("test")
        assert result["total_results"] <= 5

    @patch("tavily_tool.tavily_client")
    def test_missing_fields_in_result(self, mock_client):
        mock_client.search.return_value = {
            "results": [
                {"url": "https://kerala.gov.in/page1"},
                {"content": "Some content about the act", "title": "Test"},
            ]
        }
        result = search_func("test")
        assert result["total_results"] == 0

    @patch("tavily_tool.tavily_client")
    def test_query_preserved_in_output(self, mock_client):
        mock_client.search.return_value = {"results": []}
        result = search_func("Kerala Act 2023")
        assert result["query"] == "Kerala Act 2023"
