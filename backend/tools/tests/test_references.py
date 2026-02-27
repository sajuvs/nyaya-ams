"""Tests for reference number handling in _clean_text."""

from backend.tools.tavily_tool import _clean_text


class TestReferenceNumbers:
    def test_removes_bracket_refs(self):
        result = _clean_text("as per section [1] and clause [29] of the Act")
        assert "[1]" not in result
        assert "[29]" not in result

    def test_removes_paren_refs(self):
        result = _clean_text("NCDs (30) require state guidelines (31) for prevention")
        assert "(30)" not in result
        assert "(31)" not in result

    def test_keeps_section_subsection_text(self):
        """sub-section keyword should survive even if (1) is removed."""
        result = _clean_text("under sub-section (1) shall be liable")
        assert "sub-section" in result

    def test_removes_footnote_style_refs(self):
        result = _clean_text("The Act [12] was amended [45] in 2025")
        assert "[12]" not in result
        assert "[45]" not in result

    def test_preserves_legal_clause_letters(self):
        """Lettered clauses like (a), (b) should not be removed by digit-only regex."""
        result = _clean_text("clause (a) disinfect and (b) give prior notice")
        assert "(a)" in result
        assert "(b)" in result
