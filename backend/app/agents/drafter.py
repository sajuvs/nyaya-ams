"""
Drafting Agent: Senior Legal Draftsman.

Transforms research findings into formal legal petitions.
"""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

logger = logging.getLogger(__name__)


class DrafterAgent:
    """
    Senior Legal Draftsman that creates professional legal petitions.
    
    Takes research findings and user stories to generate formal legal documents.
    """
    
    SYSTEM_PROMPT = """You are a Senior Legal Draftsman. Your task is to take "Research Findings" from the Researcher Agent and the "User Story" to create a professional legal petition.

**STRICT GUIDELINES:**
1. STRUCTURE: Use a formal Indian legal format (To, From, Subject, Body, Prayer/Relief).
2. LANGUAGE: Use formal English, but ensure the "Prayer" (what the user wants) is crystal clear.
3. BILINGUAL: If the user mentioned "Malayalam," include a 1-paragraph summary in Malayalam at the end for clarity.
4. PLACEHOLDERS: Use brackets like [INSERT DATE] or [INSERT ADDRESS] for missing user info.
5. NO HALLUCINATION: Only use the laws provided by the Researcher Agent.

**OUTPUT FORMAT:**
- Document Title: [e.g., Consumer Complaint under Consumer Protection Act 2019]
- The Draft: [The full text of the petition with proper sections]
- Next Steps: [What the user needs to do with this document]

**TONE:** Respectful yet firm, following Indian legal conventions."""
    
    def __init__(self, model_name: str = "gpt-4.1", temperature: float = 0.2):
        """
        Initialize the Drafter Agent.
        
        Args:
            model_name: The LLM model to use for drafting
            temperature: Controls creativity (slightly higher for natural language)
        """
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", """User Grievance:
{grievance}

Research Findings:
{research_findings}

{feedback_section}

Create a formal legal petition based on the above information.""")
        ])
        
        self.chain = self.prompt | self.llm
    
    @traceable(name="legal_petition_drafting")
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
