"""
Researcher Agent: Legal Analyst & Citation Expert.

Identifies specific sections of Indian Law relevant to user grievances.
"""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langsmith import traceable

logger = logging.getLogger(__name__)


class ResearcherAgent:
    """
    Research Agent with dynamic domain-specific prompts.
    
    Can be configured for different domains (legal, product comparison, etc.)
    Requires a system_prompt to be provided - no default prompt.
    """
    
    def __init__(self, model_name: str = "gpt-4.1", temperature: float = 0.1, system_prompt: str = None):
        """
        Initialize the Researcher Agent.
        
        Args:
            model_name: The LLM model to use for research
            temperature: Controls randomness (lower = more focused)
            system_prompt: Domain-specific system prompt (REQUIRED)
            
        Raises:
            ValueError: If system_prompt is not provided
        """
        if not system_prompt:
            raise ValueError(
                "ResearcherAgent requires a system_prompt. "
                "Load a domain configuration and pass the researcher_prompt."
            )
        
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.parser = JsonOutputParser()
        self.system_prompt = system_prompt
        
        # Domain-agnostic human message template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "User Query:\n{grievance}\n\nAdditional Context:\n{rag_context}\n\nProvide your research findings in JSON format.")
        ])
        
        self.chain = self.prompt | self.llm | self.parser
    
    @traceable(name="legal_research_analysis")
    async def analyze(self, grievance: str, rag_context: str = "") -> Dict[str, Any]:
        """
        Analyze a user query and provide research findings.
        
        Args:
            grievance: The user's plain-text description of their issue
            rag_context: Additional legal context retrieved from vector store
            
        Returns:
            Dictionary containing research findings with legal citations
        """
        logger.info("Researcher Agent: Starting analysis of grievance")
        
        try:
            result = await self.chain.ainvoke({
                "grievance": grievance,
                "rag_context": rag_context or "No additional context provided."
            })
            
            logger.info(f"Researcher Agent: Analysis complete. Merits score: {result.get('merits_score', 'N/A')}")
            return result
            
        except Exception as e:
            logger.error(f"Researcher Agent: Error during analysis - {str(e)}")
            raise
