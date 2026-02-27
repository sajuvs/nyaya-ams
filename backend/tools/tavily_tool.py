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
    "consumerhelpline.gov.in"
]


@tool("tavily_search")
def tavily_search_tool(query: str) -> str:
    """
    Search ONLY official Indian legal and Kerala government sources.
    """

    response = tavily_client.search(
        query=query,
        search_depth="advanced",
        include_answer=True,
        include_sources=True,
        include_domains=ALLOWED_DOMAINS  # 🔥 Restrict to trusted sites
    )

    formatted_results = []

    if response.get("answer"):
        formatted_results.append(f"Answer:\n{response['answer']}")

    for result in response.get("results", [])[:5]:
        formatted_results.append(
            f"\nSource: {result.get('url')}\nContent: {result.get('content')}"
        )

    return "\n".join(formatted_results)