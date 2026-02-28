"""
Pydantic models for API request/response validation.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LegalAidRequest(BaseModel):
    """Request model for legal aid generation."""
    
    grievance: str = Field(
        ..., 
        description="User's plain-text description of their legal issue",
        min_length=10
    )
    domain: str = Field(
        default="legal_ai",
        description="Domain to use (legal_ai, product_comparison, etc.)"
    )
    rag_context: Optional[str] = Field(
        default="",
        description="Additional legal context from vector store (optional)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "grievance": "I purchased a defective mobile phone from a shop in Kochi. The seller refuses to provide a refund or replacement despite the phone not working within the warranty period.",
                "domain": "legal_ai",
                "rag_context": ""
            }
        }


class AgentTraceItem(BaseModel):
    """Individual trace entry from an agent."""
    
    agent: str = Field(..., description="Name of the agent")
    action: str = Field(..., description="Action being performed")
    details: str = Field(..., description="Detailed description")
    timestamp: str = Field(..., description="ISO timestamp")


class ReviewResult(BaseModel):
    """Expert reviewer audit results."""
    
    is_approved: bool = Field(..., description="Whether the draft is approved")
    feedback: str = Field(..., description="Correction notes if rejected")
    reasoning: str = Field(..., description="Internal thought process")
    jurisdiction_check: Optional[str] = Field(None, description="Jurisdiction audit result")
    statute_check: Optional[str] = Field(None, description="Statute verification result")
    tone_check: Optional[str] = Field(None, description="Tone assessment result")


class ResearchFindings(BaseModel):
    """Research agent output."""
    
    summary_of_facts: List[str] = Field(..., description="Key facts from grievance")
    legal_provisions: List[str] = Field(..., description="Applicable laws and sections")
    merits_score: int = Field(..., ge=1, le=10, description="Case strength score")
    reasoning: str = Field(..., description="Why these laws apply")
    kerala_specific: Optional[str] = Field(None, description="Kerala-specific provisions")


class LegalAidResponse(BaseModel):
    """Response model for legal aid generation."""
    
    final_document: str = Field(..., description="The approved legal petition")
    research_findings: Dict[str, Any] = Field(..., description="Legal analysis and citations")
    review_result: Dict[str, Any] = Field(..., description="Final audit results")
    agent_traces: List[AgentTraceItem] = Field(..., description="Complete reasoning trace")
    iterations: int = Field(..., description="Number of refinement cycles")
    status: str = Field(..., description="approved or max_iterations_reached")
    timestamp: str = Field(..., description="ISO timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "final_document": "To: The District Consumer Forum...",
                "research_findings": {
                    "summary_of_facts": ["Purchased defective phone", "Seller refused refund"],
                    "legal_provisions": ["Consumer Protection Act 2019, Section 35"],
                    "merits_score": 8,
                    "reasoning": "Clear case of defective goods..."
                },
                "review_result": {
                    "is_approved": True,
                    "feedback": "",
                    "reasoning": "All checks passed"
                },
                "agent_traces": [],
                "iterations": 1,
                "status": "approved",
                "timestamp": "2026-02-27T10:00:00"
            }
        }


class ResearchApprovalRequest(BaseModel):
    """Request to approve/edit research findings."""
    
    session_id: str = Field(..., description="Workflow session ID")
    approved_research: Dict[str, Any] = Field(..., description="Human-approved research findings")


class DraftReviewRequest(BaseModel):
    """Request to provide feedback on draft."""
    
    session_id: str = Field(..., description="Workflow session ID")
    feedback: str = Field(..., description="Human feedback for refinement")


class FinalizeRequest(BaseModel):
    """Request to finalize and approve workflow."""
    
    session_id: str = Field(..., description="Workflow session ID")


class WorkflowStatusResponse(BaseModel):
    """Response for workflow status check."""
    
    session_id: str
    stage: str
    message: str
    data: Optional[Dict[str, Any]] = None
