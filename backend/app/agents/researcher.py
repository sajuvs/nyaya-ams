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
    Elite Legal Research Assistant specializing in Indian Constitutional and Civil Law.
    
    Analyzes citizen grievances and identifies legal grounds for cases.
    """
    
    SYSTEM_PROMPT = """You are an elite Legal Research Assistant specializing in Indian Constitutional and Civil Law.
Your goal is to analyze a citizen's grievance and identify the legal grounds for a case.

**STRICT GUIDELINES:**
1. ANALYZE: Break down the user's plain-text story into "Key Facts."
2. CITATION: Reference specific Indian Acts (e.g., Consumer Protection Act 2019, Section 35, BNS sections).
3. LOCALIZE: If the context is Kerala, mention relevant state-level rules or departments.
4. OUTPUT FORMAT (JSON):
   {{
     "summary_of_facts": ["Brief bullet points"],
     "legal_provisions": ["List of Acts/Sections with descriptions"],
     "merits_score": 1-10,
     "reasoning": "Explain why these laws apply",
     "kerala_specific": "Any Kerala-specific provisions or departments"
   }}

**TONE:** Objective, precise, and professional.
Do not give final legal advice; provide "Research Findings" for the Drafting Agent.

**IMPORTANT:** Use BNS (Bharatiya Nyaya Sanhita) instead of IPC for criminal matters as IPC has been replaced."""
    
    def __init__(self, model_name: str = "gpt-4.1", temperature: float = 0.1):
        """
        Initialize the Researcher Agent.
        
        Args:
            model_name: The LLM model to use for research
            temperature: Controls randomness (lower = more focused)
        """
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.parser = JsonOutputParser()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", "User Grievance:\n{grievance}\n\nRelevant Legal Context (from RAG):\n{rag_context}\n\nProvide your research findings in JSON format.")
        ])
        
        self.chain = self.prompt | self.llm | self.parser
    
    @traceable(name="legal_research_analysis")
    async def analyze(self, grievance: str, rag_context: str = "") -> Dict[str, Any]:
        """
        Analyze a user grievance and identify applicable legal provisions.
        
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
