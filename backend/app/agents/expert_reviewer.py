"""
Expert Reviewer Agent: Senior Advocate & Quality Auditor.

Audits legal drafts for zero-error compliance with Indian legal standards.
"""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langsmith import traceable

logger = logging.getLogger(__name__)


class ExpertReviewerAgent:
    """
    Expert Reviewer Agent with dynamic domain-specific prompts.
    
    Can be configured for different domains (legal, product comparison, etc.)
    Requires a system_prompt to be provided - no default prompt.
    """
    
    def __init__(self, model_name: str = "gpt-4.1", temperature: float = 0.0, system_prompt: str = None):
        """
        Initialize the Expert Reviewer Agent.
        
        Args:
            model_name: The LLM model to use for review
            temperature: Controls consistency (0 for deterministic reviews)
            system_prompt: Domain-specific system prompt (REQUIRED)
            
        Raises:
            ValueError: If system_prompt is not provided
        """
        if not system_prompt:
            raise ValueError(
                "ExpertReviewerAgent requires a system_prompt. "
                "Load a domain configuration and pass the reviewer_prompt."
            )
        
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.parser = JsonOutputParser()
        self.system_prompt = system_prompt
        
        # Domain-agnostic human message template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """Research Findings:
{research_findings}

Draft to Review:
{draft}

Provide your audit results in JSON format.""")
        ])
        
        self.chain = self.prompt | self.llm | self.parser
    
    @traceable(name="expert_legal_review")
    async def review(self, draft: str, research_findings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a legal draft for compliance and accuracy.
        
        Args:
            draft: The legal petition to review
            research_findings: Original research to verify citations
            
        Returns:
            Dictionary containing review results with approval status and feedback
        """
        logger.info("Expert Reviewer Agent: Starting audit of legal draft")
        
        try:
            result = await self.chain.ainvoke({
                "draft": draft,
                "research_findings": self._format_research(research_findings)
            })
            
            approval_status = "APPROVED" if result.get("is_approved") else "REJECTED"
            logger.info(f"Expert Reviewer Agent: Audit complete - {approval_status}")
            
            if not result.get("is_approved"):
                logger.warning(f"Expert Reviewer Agent: Feedback - {result.get('feedback')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Expert Reviewer Agent: Error during review - {str(e)}")
            raise
    
    def _format_research(self, research: Dict[str, Any]) -> str:
        """Format research findings for the prompt."""
        return f"""
Legal Provisions Cited: {research.get('legal_provisions', [])}
Merits Score: {research.get('merits_score', 'N/A')}/10
Kerala-Specific Context: {research.get('kerala_specific', 'None')}
"""
