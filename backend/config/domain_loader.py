"""
Domain Configuration Loader.

Loads domain-specific prompts and settings from JSON configuration files.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class DomainConfig:
    """Represents a domain configuration with all prompts and settings."""
    
    def __init__(self, config_data: Dict[str, Any]):
        """Initialize domain config from dictionary."""
        self.domain_name = config_data["domain_name"]
        self.display_name = config_data["display_name"]
        self.description = config_data["description"]
        self.researcher_prompt = config_data["researcher_prompt"]
        self.drafter_prompt = config_data["drafter_prompt"]
        self.reviewer_prompt = config_data["reviewer_prompt"]
        self.use_rag = config_data.get("use_rag", False)
        self.use_web_search = config_data.get("use_web_search", True)
        self.search_config = config_data.get("search_config", {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "domain_name": self.domain_name,
            "display_name": self.display_name,
            "description": self.description,
            "use_rag": self.use_rag,
            "use_web_search": self.use_web_search,
            "search_config": self.search_config
        }


class DomainLoader:
    """Loads and manages domain configurations."""
    
    DOMAINS_DIR = Path(__file__).parent / "domains"
    
    @classmethod
    def load_domain(cls, domain_name: str) -> DomainConfig:
        """
        Load a domain configuration by name.
        
        Args:
            domain_name: Name of the domain (e.g., "legal_ai", "product_comparison")
            
        Returns:
            DomainConfig object with all prompts and settings
            
        Raises:
            FileNotFoundError: If domain config file doesn't exist
            ValueError: If config file is invalid
        """
        config_path = cls.DOMAINS_DIR / f"{domain_name}.json"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Domain configuration not found: {domain_name}. "
                f"Expected file: {config_path}"
            )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            logger.info(f"Loaded domain configuration: {domain_name}")
            return DomainConfig(config_data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in domain config {domain_name}: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in domain config {domain_name}: {e}")
    
    @classmethod
    def list_available_domains(cls) -> List[Dict[str, str]]:
        """
        List all available domain configurations.
        
        Returns:
            List of dictionaries with domain metadata
        """
        domains = []
        
        if not cls.DOMAINS_DIR.exists():
            logger.warning(f"Domains directory not found: {cls.DOMAINS_DIR}")
            return domains
        
        for config_file in cls.DOMAINS_DIR.glob("*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                domains.append({
                    "domain_name": config_data["domain_name"],
                    "display_name": config_data["display_name"],
                    "description": config_data["description"]
                })
            except Exception as e:
                logger.error(f"Error loading domain config {config_file}: {e}")
        
        logger.info(f"Found {len(domains)} available domains")
        return domains
