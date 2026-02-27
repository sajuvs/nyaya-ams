"""
Orchestrator Service: Multi-Agent Workflow Manager.

Implements an iterative self-correction loop with three agents:
1. Researcher Agent: Analyzes grievances and cites laws
2. Drafter Agent: Creates formal legal petitions
3. Expert Reviewer Agent: Audits and validates drafts

The orchestrator manages the feedback loop, ensuring quality output.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from ..agents.researcher import ResearcherAgent
from ..agents.drafter import DrafterAgent
from ..agents.expert_reviewer import ExpertReviewerAgent
from src.search import RAGSearch
from tools.tavily_tool import tavily_search_tool

logger = logging.getLogger(__name__)


class AgentTrace:
    """Captures the reasoning trace of each agent for frontend display."""
    
    def __init__(self):
        self.traces: List[Dict[str, Any]] = []
    
    def add(self, agent: str, action: str, details: str, timestamp: str = None):
        """
        Add a trace entry for an agent action.
        
        Args:
            agent: Name of the agent (researcher, drafter, expert_reviewer)
            action: The action being performed
            details: Detailed description of what the agent is doing
            timestamp: ISO timestamp (auto-generated if not provided)
        """
        self.traces.append({
            "agent": agent,
            "action": action,
            "details": details,
            "timestamp": timestamp or datetime.utcnow().isoformat()
        })
        logger.info(f"[{agent}] {action}: {details}")
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """Return all traces as a list of dictionaries."""
        return self.traces


class LegalAidOrchestrator:
    """
    Orchestrates the multi-agent workflow for legal aid generation.
    
    This class implements a self-correction loop where:
    1. Researcher analyzes the grievance
    2. Drafter creates a petition
    3. Expert Reviewer audits the draft
    4. If rejected, Drafter refines based on feedback (loop continues)
    5. Process repeats until approval or max iterations reached
    
    The orchestrator captures detailed traces for frontend visualization
    of the agentic workflow.
    """
    
    MAX_ITERATIONS = 3  # Prevent infinite loops
    
    def __init__(self):
        """Initialize the orchestrator with all three agents."""
        self.researcher = ResearcherAgent()
        self.drafter = DrafterAgent()
        self.expert_reviewer = ExpertReviewerAgent()
        self.rag_search = RAGSearch()
        logger.info("LegalAidOrchestrator initialized with 3 agents and RAG search")
    
    async def _gather_context(self, grievance: str, trace: AgentTrace) -> str:
        """
        Gather legal context from both local documents and web sources.
        
        Args:
            grievance: The user's legal issue
            trace: Agent trace for logging
            
        Returns:
            Combined context from RAG and Tavily searches
        """
        trace.add(
            "orchestrator",
            "gathering_context",
            "Searching local Kerala acts (RAG) and online legal resources (Tavily)"
        )
        
        # 1. RAG Search for local Kerala acts
        try:
            local_context = self.rag_search.search_and_summarize(grievance, top_k=3)
            trace.add(
                "rag_search",
                "local_search_complete",
                f"Retrieved {len(local_context)} characters from local legal documents"
            )
        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            local_context = "No local documents found."
        
        # 2. Tavily Search for online legal resources
        try:
            tavily_results = tavily_search_tool.func(grievance)
            web_sources = tavily_results.get("sources", [])
            web_context = "\n\n".join([f"{s['title']}: {s['content']}" for s in web_sources[:3]])
            trace.add(
                "tavily_search",
                "web_search_complete",
                f"Found {tavily_results.get('total_results', 0)} relevant online sources"
            )
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            web_context = "No online resources found."
        
        # 3. Combine contexts
        combined = f"""LOCAL KERALA ACTS (from PDF store):
{local_context}

ONLINE LEGAL RESOURCES:
{web_context}"""
        
        trace.add(
            "orchestrator",
            "context_ready",
            f"Context gathering complete. Total context: {len(combined)} characters"
        )
        
        return combined
    
    async def generate_legal_aid(self, grievance: str) -> Dict[str, Any]:
        """
        Generate a legal aid document through multi-agent collaboration.
        
        This method orchestrates the complete workflow:
        - Context gathering: Search local PDFs (RAG) and web (Tavily)
        - Research phase: Analyze grievance and identify legal provisions
        - Drafting phase: Create formal legal petition
        - Review phase: Audit for compliance and accuracy
        - Refinement loop: Iterate until approval or max attempts
        
        Args:
            grievance: The user's plain-text description of their legal issue
            
        Returns:
            Dictionary containing:
            - final_document: The approved legal petition
            - research_findings: Legal analysis and citations
            - review_result: Final audit results
            - agent_traces: Complete reasoning trace for frontend
            - iterations: Number of refinement cycles performed
            - status: "approved" or "max_iterations_reached"
        """
        trace = AgentTrace()
        
        # Phase 0: Context Gathering
        rag_context = await self._gather_context(grievance, trace)
        
        # Phase 1: Research
        trace.add(
            "researcher", 
            "analyzing_grievance",
            f"Scanning Indian legal statutes for provisions relevant to: '{grievance[:100]}...'"
        )
        
        research_findings = await self.researcher.analyze(grievance, rag_context)
        
        trace.add(
            "researcher",
            "research_complete",
            f"Identified {len(research_findings.get('legal_provisions', []))} legal provisions. "
            f"Case merit score: {research_findings.get('merits_score')}/10. "
            f"Key acts: {', '.join(research_findings.get('legal_provisions', [])[:2])}"
        )
        
        # Phase 2: Iterative Drafting with Self-Correction Loop
        draft = None
        review_result = None
        iteration = 0
        feedback = ""
        
        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            
            # Drafting
            if iteration == 1:
                trace.add(
                    "drafter",
                    "creating_initial_draft",
                    f"Incorporating legal provisions into formal petition structure. "
                    f"Using {len(research_findings.get('legal_provisions', []))} citations."
                )
            else:
                trace.add(
                    "drafter",
                    f"refining_draft_iteration_{iteration}",
                    f"Addressing expert feedback: {feedback[:150]}..."
                )
            
            draft = await self.drafter.draft(grievance, research_findings, feedback)
            
            trace.add(
                "drafter",
                "draft_complete",
                f"Generated {len(draft)} character petition with formal structure "
                f"(To, From, Subject, Body, Prayer)."
            )
            
            # Phase 3: Expert Review
            trace.add(
                "expert_reviewer",
                "auditing_draft",
                f"Performing compliance audit: jurisdiction check, statute verification, "
                f"tone assessment (Iteration {iteration}/{self.MAX_ITERATIONS})"
            )
            
            review_result = await self.expert_reviewer.review(draft, research_findings)
            
            if review_result.get("is_approved"):
                trace.add(
                    "expert_reviewer",
                    "draft_approved",
                    f"✓ All checks passed. Jurisdiction: {review_result.get('jurisdiction_check')}. "
                    f"Statutes: {review_result.get('statute_check')}. "
                    f"Document approved for submission."
                )
                break
            else:
                feedback = review_result.get("feedback", "")
                trace.add(
                    "expert_reviewer",
                    "draft_rejected",
                    f"✗ Issues found: {feedback[:200]}. Sending back to drafter for refinement."
                )
                
                if iteration >= self.MAX_ITERATIONS:
                    trace.add(
                        "orchestrator",
                        "max_iterations_reached",
                        f"Reached maximum refinement attempts ({self.MAX_ITERATIONS}). "
                        f"Returning best available draft with reviewer notes."
                    )
        
        # Compile final result
        status = "approved" if review_result.get("is_approved") else "max_iterations_reached"
        
        trace.add(
            "orchestrator",
            "workflow_complete",
            f"Legal aid generation complete. Status: {status}. "
            f"Total iterations: {iteration}. Document ready for user review."
        )
        
        return {
            "final_document": draft,
            "research_findings": research_findings,
            "review_result": review_result,
            "agent_traces": trace.to_dict(),
            "iterations": iteration,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
