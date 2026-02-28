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
from tools.tavily_tool import create_tavily_search_tool, TavilySearchConfig
from .workflow_state import WorkflowState
from ..utils.pii_redactor import pii_redactor

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
    
    def __init__(self, domain: str = "legal_ai"):
        """
        Initialize the orchestrator with domain-specific agents.
        
        Args:
            domain: Domain name (e.g., "legal_ai", "product_comparison")
        """
        # Load domain configuration
        self.domain_config = DomainLoader.load_domain(domain)
        self.domain = domain
        
        # Initialize agents with domain-specific prompts
        self.researcher = ResearcherAgent(system_prompt=self.domain_config.researcher_prompt)
        self.drafter = DrafterAgent(system_prompt=self.domain_config.drafter_prompt)
        self.expert_reviewer = ExpertReviewerAgent(system_prompt=self.domain_config.reviewer_prompt)
        
        # Initialize RAG search (only used if domain requires it)
        self.rag_search = RAGSearch() if self.domain_config.use_rag else None
        
        # Initialize domain-specific Tavily search tool
        if self.domain_config.use_web_search and self.domain_config.search_config:
            search_cfg = self.domain_config.search_config
            self.tavily_config = TavilySearchConfig(
                allowed_domains=search_cfg.get("allowed_domains"),
                search_depth=search_cfg.get("search_depth", "advanced"),
                max_results=search_cfg.get("max_results", 5),
                boilerplate_phrases=search_cfg.get("boilerplate_phrases", []),
                description=search_cfg.get("description", "Search for relevant information")
            )
            self.tavily_search = create_tavily_search_tool(self.tavily_config)
        else:
            self.tavily_search = None
        
        logger.info(f"LegalAidOrchestrator initialized for domain: {self.domain_config.display_name}")
        logger.info(f"RAG enabled: {self.domain_config.use_rag}, Web search enabled: {self.domain_config.use_web_search}")
    
    async def _gather_context(self, grievance: str, trace: AgentTrace) -> str:
        """
        Gather context from both local documents and web sources.
        
        Args:
            grievance: The user's query/issue
            trace: Agent trace for logging
            
        Returns:
            Combined context from RAG and Tavily searches
        """
        contexts = []
        
        # 1. RAG Search for local documents (if enabled for this domain)
        if self.domain_config.use_rag and self.rag_search:
            trace.add(
                "orchestrator",
                "gathering_rag_context",
                "Searching local document store (RAG)"
            )
            try:
                local_context = self.rag_search.search_and_summarize(grievance, top_k=3)
                contexts.append(f"LOCAL DOCUMENTS:\n{local_context}")
                trace.add(
                    "rag_search",
                    "local_search_complete",
                    f"Retrieved {len(local_context)} characters from local documents"
                )
            except Exception as e:
                logger.warning(f"RAG search failed: {e}")
                contexts.append("LOCAL DOCUMENTS: No local documents found.")
        
        # 2. Tavily Search for online resources (if enabled for this domain)
        if self.domain_config.use_web_search and self.tavily_search:
            trace.add(
                "orchestrator",
                "gathering_web_context",
                "Searching online resources (Tavily)"
            )
            try:
                tavily_results = self.tavily_search(grievance)
                web_sources = tavily_results.get("sources", [])
                web_context = "\n\n".join([f"{s['title']}: {s['content']}" for s in web_sources[:3]])
                contexts.append(f"ONLINE RESOURCES:\n{web_context}")
                trace.add(
                    "tavily_search",
                    "web_search_complete",
                    f"Found {tavily_results.get('total_results', 0)} relevant online sources"
                )
            except Exception as e:
                logger.warning(f"Tavily search failed: {e}")
                contexts.append("ONLINE RESOURCES: No online resources found.")
        
        # 3. Combine contexts
        combined = "\n\n".join(contexts) if contexts else "No additional context available."
        
        trace.add(
            "orchestrator",
            "context_ready",
            f"Context gathering complete. Total context: {len(combined)} characters"
        )
        
        return combined
    
    async def start_research(self, grievance: str) -> Dict[str, Any]:
        """Start workflow and return research findings for human review.
        
        Args:
            grievance: User's legal issue
            
        Returns:
            Dictionary with session_id, research findings, and traces
        """
        # Redact PII before processing
        redacted_grievance, redaction_map = pii_redactor.redact(grievance)
        
        session_id = WorkflowState.create_session(grievance)
        trace = AgentTrace()
        
        trace.add(
            "pii_redactor",
            "redaction_complete",
            f"Redacted {len(redaction_map)} PII items before sending to agents"
        )
        
        # Context Gathering
        rag_context = await self._gather_context(redacted_grievance, trace)
        
        # Research Phase
        trace.add(
            "researcher",
            "analyzing_grievance",
            f"Scanning Indian legal statutes for provisions relevant to: '{redacted_grievance[:100]}...'"
        )
        
        research_findings = await self.researcher.analyze(redacted_grievance, rag_context)
        
        trace.add(
            "researcher",
            "research_complete",
            f"Identified {len(research_findings.get('legal_provisions', []))} legal provisions. "
            f"Awaiting human review and approval."
        )
        
        # Save state with redaction map
        WorkflowState.update_session(session_id, {
            "stage": "awaiting_research_approval",
            "research_findings": research_findings,
            "rag_context": rag_context,
            "agent_traces": trace.to_dict(),
            "redaction_map": redaction_map,
            "redacted_grievance": redacted_grievance
        })
        
        return {
            "session_id": session_id,
            "stage": "awaiting_research_approval",
            "research_findings": research_findings,
            "agent_traces": trace.to_dict(),
            "pii_redacted": len(redaction_map) > 0,
            "message": "Please review and approve the research findings to continue."
        }
    
    async def continue_with_draft(self, session_id: str, approved_research: Dict[str, Any]) -> Dict[str, Any]:
        """Continue workflow with approved research and generate draft.
        
        Args:
            session_id: Workflow session ID
            approved_research: Human-approved/edited research findings
            
        Returns:
            Dictionary with draft and traces for human review
        """
        session = WorkflowState.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session["stage"] != "awaiting_research_approval":
            raise ValueError(f"Invalid stage: {session['stage']}")
        
        grievance = session["grievance"]
        redacted_grievance = session.get("redacted_grievance", grievance)
        trace = AgentTrace()
        trace.traces = session.get("agent_traces", [])
        
        trace.add(
            "human",
            "research_approved",
            f"Human reviewed and approved research findings. Proceeding to drafting."
        )
        
        # Generate initial draft
        trace.add(
            "drafter",
            "creating_initial_draft",
            f"Incorporating legal provisions into formal petition structure."
        )
        
        draft = await self.drafter.draft(redacted_grievance, approved_research, "")
        
        trace.add(
            "drafter",
            "draft_complete",
            f"Generated {len(draft)} character petition. Awaiting human review."
        )
        
        # Save state
        WorkflowState.update_session(session_id, {
            "stage": "awaiting_draft_review",
            "approved_research": approved_research,
            "current_draft": draft,
            "agent_traces": trace.to_dict(),
            "iteration": 1
        })
        
        return {
            "session_id": session_id,
            "stage": "awaiting_draft_review",
            "draft": draft,
            "research_findings": approved_research,
            "agent_traces": trace.to_dict(),
            "iteration": 1,
            "max_iterations": self.MAX_ITERATIONS,
            "remaining_iterations": self.MAX_ITERATIONS - 1,
            "is_approved": True,
            "message": f"Please review the draft (Iteration 1/{self.MAX_ITERATIONS}). "
                      f"Approve or provide feedback for refinement ({self.MAX_ITERATIONS - 1} refinements remaining)."
        }
    
    async def refine_draft(self, session_id: str, human_feedback: str) -> Dict[str, Any]:
        """Refine draft based on human feedback.
        
        Args:
            session_id: Workflow session ID
            human_feedback: Human's feedback for refinement
            
        Returns:
            Dictionary with refined draft for review
        """
        session = WorkflowState.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session["stage"] != "awaiting_draft_review":
            raise ValueError(f"Invalid stage: {session['stage']}")
        
        grievance = session["grievance"]
        redacted_grievance = session.get("redacted_grievance", grievance)
        approved_research = session["approved_research"]
        iteration = session.get("iteration", 1) + 1
        
        if iteration > self.MAX_ITERATIONS:
            trace = AgentTrace()
            trace.traces = session.get("agent_traces", [])
            trace.add(
                "orchestrator",
                "max_iterations_reached",
                f"Maximum refinement iterations ({self.MAX_ITERATIONS}) reached. "
                f"Please finalize the current draft or start a new workflow."
            )
            WorkflowState.update_session(session_id, {
                "agent_traces": trace.to_dict()
            })
            raise ValueError(
                f"Maximum iterations ({self.MAX_ITERATIONS}) reached. "
                f"Current draft is the best available. Please approve or start new workflow."
            )
        
        trace = AgentTrace()
        trace.traces = session.get("agent_traces", [])
        
        trace.add(
            "human",
            "feedback_provided",
            f"Human provided feedback for refinement (Iteration {iteration}): {human_feedback[:150]}..."
        )
        
        trace.add(
            "drafter",
            f"refining_draft_iteration_{iteration}",
            f"Addressing human feedback."
        )
        
        draft = await self.drafter.draft(redacted_grievance, approved_research, human_feedback)
        
        trace.add(
            "drafter",
            "draft_refined",
            f"Refined draft complete ({len(draft)} characters). Awaiting human review."
        )
        
        # Save state
        WorkflowState.update_session(session_id, {
            "current_draft": draft,
            "agent_traces": trace.to_dict(),
            "iteration": iteration
        })
        
        return {
            "session_id": session_id,
            "stage": "awaiting_draft_review",
            "draft": draft,
            "research_findings": approved_research,
            "agent_traces": trace.to_dict(),
            "iteration": iteration,
            "max_iterations": self.MAX_ITERATIONS,
            "remaining_iterations": self.MAX_ITERATIONS - iteration,
            "message": f"Please review the refined draft (Iteration {iteration}/{self.MAX_ITERATIONS}). "
                      f"Approve or provide additional feedback ({self.MAX_ITERATIONS - iteration} refinements remaining)."
        }
    
    async def finalize_workflow(self, session_id: str) -> Dict[str, Any]:
        """Finalize workflow with human approval.
        
        Args:
            session_id: Workflow session ID
            
        Returns:
            Final approved document with complete traces
        """
        session = WorkflowState.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session["stage"] != "awaiting_draft_review":
            raise ValueError(f"Invalid stage: {session['stage']}")
        
        trace = AgentTrace()
        trace.traces = session.get("agent_traces", [])
        
        trace.add(
            "human",
            "draft_approved",
            "Human approved the final draft. Workflow complete."
        )
        
        trace.add(
            "orchestrator",
            "workflow_complete",
            f"Legal aid generation complete with human approval. "
            f"Total iterations: {session.get('iteration', 1)}. Document ready for submission."
        )
        
        # Update state
        WorkflowState.update_session(session_id, {
            "stage": "complete",
            "agent_traces": trace.to_dict()
        })
        
        # Restore PII in final document
        final_draft = session["current_draft"]
        redaction_map = session.get("redaction_map", {})
        if redaction_map:
            final_draft = pii_redactor.restore(final_draft, redaction_map)
            trace.add(
                "pii_redactor",
                "restoration_complete",
                f"Restored {len(redaction_map)} PII items in final document"
            )
        
        result = {
            "final_document": final_draft,
            "research_findings": session["approved_research"],
            "review_result": {
                "is_approved": True,
                "feedback": "",
                "reasoning": "Human approved the final draft"
            },
            "agent_traces": trace.to_dict(),
            "iterations": session.get("iteration", 1),
            "status": "approved_by_human",
            "is_approved": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Clean up session
        WorkflowState.delete_session(session_id)
        
        return result
    
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
