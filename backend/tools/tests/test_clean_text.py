"""All _clean_text edge cases: empty, unicode, URLs, markdown, boilerplate, dedup, truncation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tavily_tool import _clean_text, MAX_CONTENT_LENGTH


class TestEmptyInputs:
    def test_none(self):
        assert _clean_text(None) == ""

    def test_empty_string(self):
        assert _clean_text("") == ""

    def test_whitespace_only(self):
        assert _clean_text("   \n\t  ") == ""


class TestUnicode:
    def test_malayalam_only(self):
        assert _clean_text("കേരള പൊതുജനാരോഗ്യ ആക്റ്റ് 2023") == ""

    def test_mixed_english_unicode(self):
        result = _clean_text("The Kerala Act 2023 കേരള ആക്റ്റ് provides for public health")
        assert "Kerala Act 2023" in result
        assert "public health" in result

    def test_hindi_devanagari(self):
        result = _clean_text("अधिनियम संख्या 28 वर्ष 2023")
        assert result == "" or len(result) < 5


class TestURLRemoval:
    def test_http(self):
        result = _clean_text("See http://example.com/page and also here")
        assert "http://" not in result

    def test_https(self):
        result = _clean_text("Visit https://kerala.gov.in/act/2023 for more info")
        assert "https://" not in result
        assert "for more info" in result

    def test_multiple_urls(self):
        result = _clean_text("Link1 https://a.com Link2 http://b.com end")
        assert "https://" not in result
        assert "http://" not in result


class TestMarkdown:
    def test_removes_table_syntax(self):
        assert "|" not in _clean_text("| Title | Year | | Kerala Act | 2023 | some text")

    def test_removes_headers(self):
        result = _clean_text("## Section 1\n### Subsection A\nActual content here")
        assert "##" not in result
        assert "Actual content here" in result

    def test_removes_pdf_tags(self):
        result = _clean_text("[PDF] The Kerala Public Health Act 2023")
        assert "[PDF]" not in result
        assert "Kerala Public Health Act" in result


class TestBoilerplate:
    def test_removes_authenticity_notice(self):
        result = _clean_text("Authenticity may be verified through the official portal. ACT 28 OF 2023")
        assert "Authenticity" not in result
        assert "ACT 28 OF 2023" in result

    def test_removes_copyright(self):
        assert "Copyright" not in _clean_text("Important legal text. Copyright 2023 Government of Kerala. More text.")

    def test_removes_multiple_boilerplate(self):
        result = _clean_text("Skip to main content. The Act provides. Powered by NIC. Disclaimer applies.")
        assert "Skip to main content" not in result
        assert "Powered by" not in result


class TestDedup:
    def test_removes_repeated_sentences(self):
        result = _clean_text("The Kerala Act 2023. The Kerala Act 2023. The Kerala Act 2023. Something new here.")
        assert result.count("The Kerala Act 2023") == 1
        assert "Something new here" in result

    def test_keeps_unique_sentences(self):
        result = _clean_text("Section 1 defines terms. Section 2 covers scope. Section 3 lists penalties.")
        assert "Section 1" in result and "Section 2" in result and "Section 3" in result


class TestTruncation:
    def test_truncates_long_content(self):
        text = ". ".join(f"Section {i} defines provision number {i} of the act" for i in range(100))
        result = _clean_text(text)
        assert len(result) <= MAX_CONTENT_LENGTH + 3
        assert result.endswith("...")

    def test_short_content_not_truncated(self):
        assert not _clean_text("Short legal text about Section 41 of the Act.").endswith("...")
