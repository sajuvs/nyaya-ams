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


@tool("tavily_search")
def tavily_search_tool(query: str) -> dict:
    """
    Search legal information from trusted Indian government domains only.
    Returns RAW structured data (no AI-generated summary).
    """

    response = tavily_client.search(
        query=query,
        search_depth="advanced",
        include_answer=False,
        include_sources=True,
        include_domains=ALLOWED_DOMAINS
    )

    # Extra safety filter (double validation)
    sources = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "content": r.get("content")
        }
        for r in response.get("results", [])[:5]
        if any(domain in r.get("url", "") for domain in ALLOWED_DOMAINS)
    ]

    return {
        "query": query,
        "allowed_domains": ALLOWED_DOMAINS,
        "sources": sources
    }
