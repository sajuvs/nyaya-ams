"""
Drafting Agent: Senior Legal Draftsman.

Transforms research findings into formal legal petitions.
"""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class DrafterAgent:
    """
    Drafting Agent with dynamic domain-specific prompts.
    
    Can be configured for different domains (legal, product comparison, etc.)
    Requires a system_prompt to be provided - no default prompt.
    """
    
    def __init__(self, model_name: str = "gpt-4.1", temperature: float = 0.2, system_prompt: str = None):
        """
        Initialize the Drafter Agent.
        
        Args:
            model_name: The LLM model to use for drafting
            temperature: Controls creativity (slightly higher for natural language)
            system_prompt: Domain-specific system prompt (REQUIRED)
            
        Raises:
            ValueError: If system_prompt is not provided
        """
        if not system_prompt:
            raise ValueError(
                "DrafterAgent requires a system_prompt. "
                "Load a domain configuration and pass the drafter_prompt."
            )
        
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.system_prompt = system_prompt
        
        # Domain-agnostic human message template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """User Query:
{grievance}

Research Findings:
{research_findings}

{feedback_section}

Create your analysis/document based on the above information.""")
        ])
        
        self.chain = self.prompt | self.llm
        
    async def draft(self, grievance: str, research_findings: Dict[str, Any], feedback: str = "") -> str:
        """
        Draft a formal legal petition based on research findings.
        
        Args:
            grievance: The original user grievance
            research_findings: Output from the Researcher Agent
            feedback: Optional feedback from Expert Reviewer for refinement
            
        Returns:
            The complete drafted legal petition as a string
        """
        iteration_msg = "REVISION REQUIRED" if feedback else "INITIAL DRAFT"
        logger.info(f"Drafter Agent: Creating {iteration_msg}")
        
        feedback_section = ""
        if feedback:
            feedback_section = f"\n**EXPERT REVIEWER FEEDBACK (Address these issues):**\n{feedback}\n"
        
        try:
            result = await self.chain.ainvoke({
                "grievance": grievance,
                "research_findings": self._format_research(research_findings),
                "feedback_section": feedback_section
            })
            
            draft = result.content
            logger.info(f"Drafter Agent: Draft complete ({len(draft)} characters)")
            return draft
            
        except Exception as e:
            logger.error(f"Drafter Agent: Error during drafting - {str(e)}")
            raise
    
    def _format_research(self, research: Dict[str, Any]) -> str:
        """Format research findings for the prompt."""
        return f"""
Summary of Facts: {research.get('summary_of_facts', [])}
Legal Provisions: {research.get('legal_provisions', [])}
Merits Score: {research.get('merits_score', 'N/A')}/10
Reasoning: {research.get('reasoning', '')}
Kerala-Specific: {research.get('kerala_specific', 'None')}
"""
