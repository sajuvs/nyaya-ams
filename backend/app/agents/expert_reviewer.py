"""
Expert Reviewer Agent: Senior Advocate & Quality Auditor.

Audits legal drafts for zero-error compliance with Indian legal standards.
"""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)


class ExpertReviewerAgent:
    """
    Senior Advocate with 20 plus years experience.
    
    Audits legal drafts for "Zero-Error" compliance with jurisdiction,
    statutes, and tone requirements.
    """
    
    SYSTEM_PROMPT = """You are a Senior Advocate of the Kerala High Court.
Your goal is to audit legal drafts for "Zero-Error" compliance.

**AUDIT CRITERIA:**
1. JURISDICTION: Verify if the case is directed to the correct District Court or appropriate forum.
2. STATUTES: Ensure no repealed laws are used (e.g., IPC must be replaced with BNS for criminal matters).
3. CITATIONS: Verify that all cited sections and acts are accurate and applicable.
4. TONE: Ensure the draft is respectful yet firm, following Indian legal conventions.
5. STRUCTURE: Check that the petition follows proper Indian legal format.
6. COMPLETENESS: Ensure all necessary elements are present (To, From, Subject, Body, Prayer).

**OUTPUT (JSON):**
{{
  "is_approved": boolean,
  "feedback": "Specific correction notes if false, empty string if approved",
  "reasoning": "Internal thought process explaining the decision",
  "jurisdiction_check": "Pass/Fail with explanation",
  "statute_check": "Pass/Fail with explanation",
  "tone_check": "Pass/Fail with explanation"
}}

**IMPORTANT:** Be thorough but fair. Only reject if there are genuine legal or structural issues."""
    
    def __init__(self, model_name: str = "gpt-4.1", temperature: float = 0.0):
        """
        Initialize the Expert Reviewer Agent.
        
        Args:
            model_name: The LLM model to use for review
            temperature: Controls consistency (0 for deterministic reviews)
        """
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.parser = JsonOutputParser()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", """Research Findings:
{research_findings}

Legal Draft to Review:
{draft}

Provide your audit results in JSON format.""")
        ])
        
        self.chain = self.prompt | self.llm | self.parser
        
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
