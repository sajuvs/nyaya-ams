import re
from langchain.tools import tool
from tavily import TavilyClient
from app.core.config import settings


tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)


ALLOWED_DOMAINS = [
    "indiacode.nic.in",
    "legislative.gov.in",
    "kerala.gov.in",
    "hckreform.gov.in",
    "main.sci.gov.in",
    "consumerhelpline.gov.in",
    "prsindia.org",
    "lawreformscommission.kerala.gov.in",
    "niyamasabha.org",
]

BOILERPLATE = [
    "Authenticity may be verified through",
    "Click here to view",
    "Skip to main content",
    "JavaScript is disabled",
    "Site designed and developed by",
    "National Informatics Centre",
    "Content Provided by the State Government",
    "Working Hours",
    "All rights reserved",
    "Copyright",
    "Powered by",
    "Terms and Conditions",
    "Privacy Policy",
    "Disclaimer",
    "Last Updated",
    "as accessed on",
]

MAX_CONTENT_LENGTH = 500


def _clean_text(text: str) -> str:
    """Aggressively clean scraped content to reduce tokens."""
    if not text:
        return ""
    # Strip non-ascii
    text = text.encode("ascii", "ignore").decode("ascii")
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove markdown table syntax
    text = re.sub(r"\|[^|]*\|", " ", text)
    # Remove markdown headers/formatting
    text = re.sub(r"#{1,6}\s*", "", text)
    # Remove [PDF] tags
    text = re.sub(r"\[PDF\]", "", text, flags=re.IGNORECASE)
    # Remove reference numbers like [1], (29), etc.
    text = re.sub(r"[\[\(]\d+[\]\)]", "", text)
    # Remove boilerplate
    for phrase in BOILERPLATE:
        text = re.sub(re.escape(phrase) + r"[^.]*\.?", "", text, flags=re.IGNORECASE)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove repeated phrases (e.g. title repeated multiple times)
    sentences = text.split(". ")
    seen = set()
    unique = []
    for s in sentences:
        s_clean = s.strip().lower()
        if s_clean and s_clean not in seen and len(s_clean) > 10:
            seen.add(s_clean)
            unique.append(s.strip())
    text = ". ".join(unique)
    # Truncate to save tokens
    if len(text) > MAX_CONTENT_LENGTH:
        text = text[:MAX_CONTENT_LENGTH].rsplit(" ", 1)[0] + "..."
    return text


@tool("tavily_search")
def tavily_search_tool(query: str) -> dict:
    """
    Search legal information from trusted Indian government domains only.
    Returns clean structured data optimized for LLM consumption.
    """

    response = tavily_client.search(
        query=query,
        search_depth="advanced",
        include_answer=False,
        include_sources=True,
        include_domains=ALLOWED_DOMAINS
    )

    sources = []
    for r in response.get("results", [])[:5]:
        url = r.get("url", "")
        if not any(domain in url for domain in ALLOWED_DOMAINS):
            continue

        content = _clean_text(r.get("content", ""))
        title = _clean_text(r.get("title", ""))

        # Skip empty, too-short, or non-English results
        if not content or len(content) < 30:
            continue
        word_count = len(re.findall(r"[a-zA-Z]{2,}", content))
        if word_count < 10:
            continue

        sources.append({
            "title": title,
            "url": url,
            "content": content
        })

    return {
        "query": query,
        "total_results": len(sources),
        "sources": sources
    }
