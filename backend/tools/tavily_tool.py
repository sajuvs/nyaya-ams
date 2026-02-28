import re
import os
from typing import Optional, List
from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# Default boilerplate phrases to remove (domain-agnostic)
DEFAULT_BOILERPLATE = [
    "Click here to view",
    "Skip to main content",
    "JavaScript is disabled",
    "All rights reserved",
    "Copyright",
    "Powered by",
    "Terms and Conditions",
    "Privacy Policy",
    "Disclaimer",
    "Last Updated",
]

MAX_CONTENT_LENGTH = 500


class TavilySearchConfig:
    """Configuration for domain-specific Tavily searches."""
    
    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        search_depth: str = "advanced",
        max_results: int = 5,
        boilerplate_phrases: Optional[List[str]] = None,
        description: str = "Search for relevant information online"
    ):
        """
        Initialize Tavily search configuration.
        
        Args:
            allowed_domains: List of domains to restrict search to (None = no restriction)
            search_depth: "basic" or "advanced"
            max_results: Maximum number of results to return
            boilerplate_phrases: Additional boilerplate phrases to remove
            description: Tool description for the domain
        """
        self.allowed_domains = allowed_domains
        self.search_depth = search_depth
        self.max_results = max_results
        self.boilerplate_phrases = (boilerplate_phrases or []) + DEFAULT_BOILERPLATE
        self.description = description


def _clean_text(text: str, boilerplate_phrases: List[str]) -> str:
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
    for phrase in boilerplate_phrases:
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


def create_tavily_search_tool(config: TavilySearchConfig):
    """
    Create a domain-specific Tavily search tool.
    
    Args:
        config: TavilySearchConfig with domain-specific settings
        
    Returns:
        Configured search function
    """
    
    def tavily_search(query: str) -> dict:
        """Search for relevant information using Tavily."""
        
        # Build search parameters
        search_params = {
            "query": query,
            "search_depth": config.search_depth,
            "include_answer": False,
            "include_sources": True,
        }
        
        # Add domain restriction if specified
        if config.allowed_domains:
            search_params["include_domains"] = config.allowed_domains
        
        response = tavily_client.search(**search_params)
        
        sources = []
        for r in response.get("results", [])[:config.max_results]:
            url = r.get("url", "")
            
            # If domains specified, verify result is from allowed domain
            if config.allowed_domains:
                if not any(domain in url for domain in config.allowed_domains):
                    continue
            
            content = _clean_text(r.get("content", ""), config.boilerplate_phrases)
            title = _clean_text(r.get("title", ""), config.boilerplate_phrases)
            
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
    
    # Set function metadata
    tavily_search.__name__ = "tavily_search"
    tavily_search.__doc__ = config.description
    
    return tavily_search


# Legacy global tool for backward compatibility (will be deprecated)
@tool("tavily_search")
def tavily_search_tool(query: str) -> dict:
    """
    DEPRECATED: Use create_tavily_search_tool() with domain config instead.
    
    Legacy search tool with hardcoded legal domain restrictions.
    This exists only for backward compatibility and will be removed.
    """
    # Hardcoded legal AI config for backward compatibility
    legacy_config = TavilySearchConfig(
        allowed_domains=[
            "indiacode.nic.in",
            "legislative.gov.in",
            "kerala.gov.in",
            "hckreform.gov.in",
            "main.sci.gov.in",
            "consumerhelpline.gov.in",
            "prsindia.org",
            "lawreformscommission.kerala.gov.in",
            "niyamasabha.org",
        ],
        boilerplate_phrases=[
            "Authenticity may be verified through",
            "Site designed and developed by",
            "National Informatics Centre",
            "Content Provided by the State Government",
            "Working Hours",
            "as accessed on",
        ],
        description="Search legal information from trusted Indian government domains only."
    )
    
    search_func = create_tavily_search_tool(legacy_config)
    return search_func(query)

