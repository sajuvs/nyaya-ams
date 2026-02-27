"""Tests for orchestrator service with all edge cases."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.services.orchestrator import LegalAidOrchestrator, AgentTrace


@pytest.fixture
def mock_rag_search():
    """Mock RAG search."""
    with patch("app.services.orchestrator.RAGSearch") as mock:
        instance = Mock()
        instance.search_and_summarize.return_value = "Kerala Public Health Act 2023 provisions"
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_tavily():
    """Mock Tavily search."""
    with patch("app.services.orchestrator.tavily_search_tool") as mock:
        mock.func.return_value = {
            "total_results": 2,
            "sources": [
                {"title": "Act 1", "content": "Legal content 1"},
                {"title": "Act 2", "content": "Legal content 2"}
            ]
        }
        yield mock


@pytest.fixture
def mock_agents():
    """Mock all three agents."""
    with patch("app.services.orchestrator.ResearcherAgent") as researcher, \
         patch("app.services.orchestrator.DrafterAgent") as drafter, \
         patch("app.services.orchestrator.ExpertReviewerAgent") as reviewer:
        
        researcher_instance = Mock()
        researcher_instance.analyze = AsyncMock(return_value={
            "summary_of_facts": ["Fact 1", "Fact 2"],
            "legal_provisions": ["BNS Section 420", "Consumer Protection Act 2019"],
            "merits_score": 8,
            "reasoning": "Strong case",
            "kerala_specific": "Kerala jurisdiction applies"
        })
        researcher.return_value = researcher_instance
        
        drafter_instance = Mock()
        drafter_instance.draft = AsyncMock(return_value="Formal legal petition draft")
        drafter.return_value = drafter_instance
        
        reviewer_instance = Mock()
        reviewer_instance.review = AsyncMock(return_value={
            "is_approved": True,
            "feedback": "",
            "reasoning": "All checks passed",
            "jurisdiction_check": "Pass",
            "statute_check": "Pass",
            "tone_check": "Pass"
        })
        reviewer.return_value = reviewer_instance
        
        yield researcher_instance, drafter_instance, reviewer_instance


class TestAgentTrace:
    """Test AgentTrace functionality."""
    
    def test_add_trace(self):
        trace = AgentTrace()
        trace.add("researcher", "analyzing", "Analyzing grievance")
        
        assert len(trace.traces) == 1
        assert trace.traces[0]["agent"] == "researcher"
        assert trace.traces[0]["action"] == "analyzing"
    
    def test_to_dict(self):
        trace = AgentTrace()
        trace.add("drafter", "drafting", "Creating petition")
        
        result = trace.to_dict()
        assert isinstance(result, list)
        assert len(result) == 1


class TestContextGathering:
    """Test context gathering phase."""
    
    @pytest.mark.asyncio
    async def test_gather_context_success(self, mock_rag_search, mock_tavily):
        orchestrator = LegalAidOrchestrator()
        trace = AgentTrace()
        
        context = await orchestrator._gather_context("test grievance", trace)
        
        assert "LOCAL KERALA ACTS" in context
        assert "ONLINE LEGAL RESOURCES" in context
        assert len(trace.traces) >= 3
    
    @pytest.mark.asyncio
    async def test_gather_context_rag_fails(self, mock_rag_search, mock_tavily):
        orchestrator = LegalAidOrchestrator()
        mock_rag_search.search_and_summarize.side_effect = Exception("RAG error")
        trace = AgentTrace()
        
        context = await orchestrator._gather_context("test grievance", trace)
        
        assert "No local documents found" in context
        assert "ONLINE LEGAL RESOURCES" in context
    
    @pytest.mark.asyncio
    async def test_gather_context_tavily_fails(self, mock_rag_search, mock_tavily):
        orchestrator = LegalAidOrchestrator()
        mock_tavily.func.side_effect = Exception("Tavily error")
        trace = AgentTrace()
        
        context = await orchestrator._gather_context("test grievance", trace)
        
        assert "LOCAL KERALA ACTS" in context
        assert "No online resources found" in context
    
    @pytest.mark.asyncio
    async def test_gather_context_both_fail(self, mock_rag_search, mock_tavily):
        orchestrator = LegalAidOrchestrator()
        mock_rag_search.search_and_summarize.side_effect = Exception("RAG error")
        mock_tavily.func.side_effect = Exception("Tavily error")
        trace = AgentTrace()
        
        context = await orchestrator._gather_context("test grievance", trace)
        
        assert "No local documents found" in context
        assert "No online resources found" in context


class TestOrchestrationFlow:
    """Test complete orchestration workflow."""
    
    @pytest.mark.asyncio
    async def test_successful_first_iteration(self, mock_rag_search, mock_tavily, mock_agents):
        orchestrator = LegalAidOrchestrator()
        
        result = await orchestrator.generate_legal_aid("Defective product complaint")
        
        assert result["status"] == "approved"
        assert result["iterations"] == 1
        assert "final_document" in result
        assert "research_findings" in result
        assert "agent_traces" in result
    
    @pytest.mark.asyncio
    async def test_rejection_then_approval(self, mock_rag_search, mock_tavily, mock_agents):
        _, drafter, reviewer = mock_agents
        
        # First review rejects, second approves
        reviewer.review = AsyncMock(side_effect=[
            {"is_approved": False, "feedback": "Fix jurisdiction", "reasoning": "Wrong court"},
            {"is_approved": True, "feedback": "", "reasoning": "All good"}
        ])
        
        orchestrator = LegalAidOrchestrator()
        result = await orchestrator.generate_legal_aid("Test grievance")
        
        assert result["status"] == "approved"
        assert result["iterations"] == 2
        assert drafter.draft.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_iterations_reached(self, mock_rag_search, mock_tavily, mock_agents):
        _, _, reviewer = mock_agents
        
        # Always reject
        reviewer.review = AsyncMock(return_value={
            "is_approved": False,
            "feedback": "Multiple issues",
            "reasoning": "Needs work"
        })
        
        orchestrator = LegalAidOrchestrator()
        result = await orchestrator.generate_legal_aid("Test grievance")
        
        assert result["status"] == "max_iterations_reached"
        assert result["iterations"] == 3
    
    @pytest.mark.asyncio
    async def test_researcher_failure(self, mock_rag_search, mock_tavily, mock_agents):
        researcher, _, _ = mock_agents
        researcher.analyze = AsyncMock(side_effect=Exception("Research failed"))
        
        orchestrator = LegalAidOrchestrator()
        
        with pytest.raises(Exception, match="Research failed"):
            await orchestrator.generate_legal_aid("Test grievance")
    
    @pytest.mark.asyncio
    async def test_drafter_failure(self, mock_rag_search, mock_tavily, mock_agents):
        _, drafter, _ = mock_agents
        drafter.draft = AsyncMock(side_effect=Exception("Drafting failed"))
        
        orchestrator = LegalAidOrchestrator()
        
        with pytest.raises(Exception, match="Drafting failed"):
            await orchestrator.generate_legal_aid("Test grievance")
    
    @pytest.mark.asyncio
    async def test_reviewer_failure(self, mock_rag_search, mock_tavily, mock_agents):
        _, _, reviewer = mock_agents
        reviewer.review = AsyncMock(side_effect=Exception("Review failed"))
        
        orchestrator = LegalAidOrchestrator()
        
        with pytest.raises(Exception, match="Review failed"):
            await orchestrator.generate_legal_aid("Test grievance")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_empty_grievance(self, mock_rag_search, mock_tavily, mock_agents):
        orchestrator = LegalAidOrchestrator()
        
        result = await orchestrator.generate_legal_aid("")
        
        assert "final_document" in result
        assert result["iterations"] >= 1
    
    @pytest.mark.asyncio
    async def test_very_long_grievance(self, mock_rag_search, mock_tavily, mock_agents):
        orchestrator = LegalAidOrchestrator()
        long_grievance = "A" * 10000
        
        result = await orchestrator.generate_legal_aid(long_grievance)
        
        assert result["status"] in ["approved", "max_iterations_reached"]
    
    @pytest.mark.asyncio
    async def test_special_characters_grievance(self, mock_rag_search, mock_tavily, mock_agents):
        orchestrator = LegalAidOrchestrator()
        special_grievance = "Test <script>alert('xss')</script> & symbols @#$%"
        
        result = await orchestrator.generate_legal_aid(special_grievance)
        
        assert "final_document" in result
    
    @pytest.mark.asyncio
    async def test_unicode_grievance(self, mock_rag_search, mock_tavily, mock_agents):
        orchestrator = LegalAidOrchestrator()
        unicode_grievance = "കേരള പൊതുജനാരോഗ്യ ആക്റ്റ് complaint"
        
        result = await orchestrator.generate_legal_aid(unicode_grievance)
        
        assert "final_document" in result
    
    @pytest.mark.asyncio
    async def test_trace_completeness(self, mock_rag_search, mock_tavily, mock_agents):
        orchestrator = LegalAidOrchestrator()
        
        result = await orchestrator.generate_legal_aid("Test grievance")
        
        traces = result["agent_traces"]
        agents_in_traces = {t["agent"] for t in traces}
        
        assert "orchestrator" in agents_in_traces
        assert "researcher" in agents_in_traces
        assert "drafter" in agents_in_traces
        assert "expert_reviewer" in agents_in_traces
    
    @pytest.mark.asyncio
    async def test_timestamp_present(self, mock_rag_search, mock_tavily, mock_agents):
        orchestrator = LegalAidOrchestrator()
        
        result = await orchestrator.generate_legal_aid("Test grievance")
        
        assert "timestamp" in result
        assert result["timestamp"]
