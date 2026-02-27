"""
Tests for the LegalAidOrchestrator.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.orchestrator import LegalAidOrchestrator, AgentTrace


@pytest.fixture
def mock_research_findings():
    """Mock research findings from Researcher Agent."""
    return {
        "summary_of_facts": [
            "Purchased defective mobile phone",
            "Seller refused refund within warranty period"
        ],
        "legal_provisions": [
            "Consumer Protection Act 2019, Section 35",
            "Consumer Protection Act 2019, Section 2(9)"
        ],
        "merits_score": 8,
        "reasoning": "Clear case of defective goods under Consumer Protection Act",
        "kerala_specific": "Kerala State Consumer Disputes Redressal Commission"
    }


@pytest.fixture
def mock_draft():
    """Mock legal draft from Drafter Agent."""
    return """
To: The District Consumer Forum, Ernakulam
From: [INSERT NAME], [INSERT ADDRESS]
Subject: Consumer Complaint under Consumer Protection Act 2019

Body:
The complainant purchased a mobile phone on [INSERT DATE] from [SELLER NAME].
The product was found to be defective within the warranty period.
Despite multiple requests, the seller has refused to provide a refund or replacement.

Prayer:
The complainant prays for:
1. Refund of the purchase amount
2. Compensation for mental harassment
3. Any other relief deemed fit

[INSERT SIGNATURE]
"""


@pytest.fixture
def mock_approved_review():
    """Mock approved review from Expert Reviewer."""
    return {
        "is_approved": True,
        "feedback": "",
        "reasoning": "All checks passed. Proper jurisdiction, valid statutes, appropriate tone.",
        "jurisdiction_check": "Pass - Correctly directed to District Consumer Forum",
        "statute_check": "Pass - Consumer Protection Act 2019 properly cited",
        "tone_check": "Pass - Respectful and formal"
    }


@pytest.fixture
def mock_rejected_review():
    """Mock rejected review from Expert Reviewer."""
    return {
        "is_approved": False,
        "feedback": "The petition should specify the exact date of purchase and seller details.",
        "reasoning": "Missing critical information for case filing.",
        "jurisdiction_check": "Pass",
        "statute_check": "Pass",
        "tone_check": "Pass"
    }


class TestAgentTrace:
    """Test the AgentTrace class."""
    
    def test_add_trace(self):
        """Test adding a trace entry."""
        trace = AgentTrace()
        trace.add("researcher", "analyzing", "Scanning legal provisions")
        
        assert len(trace.traces) == 1
        assert trace.traces[0]["agent"] == "researcher"
        assert trace.traces[0]["action"] == "analyzing"
        assert "timestamp" in trace.traces[0]
    
    def test_to_dict(self):
        """Test converting traces to dictionary."""
        trace = AgentTrace()
        trace.add("researcher", "analyzing", "Details")
        trace.add("drafter", "drafting", "Creating petition")
        
        result = trace.to_dict()
        assert isinstance(result, list)
        assert len(result) == 2


class TestLegalAidOrchestrator:
    """Test the LegalAidOrchestrator class."""
    
    @pytest.mark.asyncio
    async def test_successful_first_iteration(
        self, 
        mock_research_findings, 
        mock_draft, 
        mock_approved_review
    ):
        """Test successful generation on first iteration."""
        with patch('app.services.orchestrator.ResearcherAgent') as MockResearcher, \
             patch('app.services.orchestrator.DrafterAgent') as MockDrafter, \
             patch('app.services.orchestrator.ExpertReviewerAgent') as MockReviewer:
            
            # Setup mocks
            mock_researcher = MockResearcher.return_value
            mock_researcher.analyze = AsyncMock(return_value=mock_research_findings)
            
            mock_drafter = MockDrafter.return_value
            mock_drafter.draft = AsyncMock(return_value=mock_draft)
            
            mock_reviewer = MockReviewer.return_value
            mock_reviewer.review = AsyncMock(return_value=mock_approved_review)
            
            # Execute
            orchestrator = LegalAidOrchestrator()
            result = await orchestrator.generate_legal_aid(
                grievance="I bought a defective phone and seller won't refund",
                rag_context=""
            )
            
            # Assertions
            assert result["status"] == "approved"
            assert result["iterations"] == 1
            assert result["final_document"] == mock_draft
            assert len(result["agent_traces"]) > 0
            assert mock_researcher.analyze.call_count == 1
            assert mock_drafter.draft.call_count == 1
            assert mock_reviewer.review.call_count == 1
    
    @pytest.mark.asyncio
    async def test_refinement_loop(
        self, 
        mock_research_findings, 
        mock_draft, 
        mock_rejected_review,
        mock_approved_review
    ):
        """Test refinement loop with one rejection then approval."""
        with patch('app.services.orchestrator.ResearcherAgent') as MockResearcher, \
             patch('app.services.orchestrator.DrafterAgent') as MockDrafter, \
             patch('app.services.orchestrator.ExpertReviewerAgent') as MockReviewer:
            
            # Setup mocks
            mock_researcher = MockResearcher.return_value
            mock_researcher.analyze = AsyncMock(return_value=mock_research_findings)
            
            mock_drafter = MockDrafter.return_value
            mock_drafter.draft = AsyncMock(return_value=mock_draft)
            
            mock_reviewer = MockReviewer.return_value
            # First call rejects, second call approves
            mock_reviewer.review = AsyncMock(
                side_effect=[mock_rejected_review, mock_approved_review]
            )
            
            # Execute
            orchestrator = LegalAidOrchestrator()
            result = await orchestrator.generate_legal_aid(
                grievance="I bought a defective phone",
                rag_context=""
            )
            
            # Assertions
            assert result["status"] == "approved"
            assert result["iterations"] == 2
            assert mock_drafter.draft.call_count == 2
            assert mock_reviewer.review.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_iterations_reached(
        self, 
        mock_research_findings, 
        mock_draft, 
        mock_rejected_review
    ):
        """Test max iterations limit."""
        with patch('app.services.orchestrator.ResearcherAgent') as MockResearcher, \
             patch('app.services.orchestrator.DrafterAgent') as MockDrafter, \
             patch('app.services.orchestrator.ExpertReviewerAgent') as MockReviewer:
            
            # Setup mocks - always reject
            mock_researcher = MockResearcher.return_value
            mock_researcher.analyze = AsyncMock(return_value=mock_research_findings)
            
            mock_drafter = MockDrafter.return_value
            mock_drafter.draft = AsyncMock(return_value=mock_draft)
            
            mock_reviewer = MockReviewer.return_value
            mock_reviewer.review = AsyncMock(return_value=mock_rejected_review)
            
            # Execute
            orchestrator = LegalAidOrchestrator()
            result = await orchestrator.generate_legal_aid(
                grievance="Test grievance",
                rag_context=""
            )
            
            # Assertions
            assert result["status"] == "max_iterations_reached"
            assert result["iterations"] == orchestrator.MAX_ITERATIONS
            assert mock_drafter.draft.call_count == orchestrator.MAX_ITERATIONS
