"""
Quick test script to verify all agents are working correctly.

Run this to test the multi-agent system before committing.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: OPENAI_API_KEY not found in environment")
    print("Please add it to your .env file:")
    print("  echo 'OPENAI_API_KEY=your_key_here' >> .env")
    exit(1)

print("✓ OPENAI_API_KEY found")
print("\n" + "="*80)
print("TESTING NYAYA-FLOW MULTI-AGENT SYSTEM")
print("="*80 + "\n")


async def test_researcher_agent():
    """Test the Researcher Agent."""
    print("1. Testing Researcher Agent...")
    print("-" * 80)
    
    try:
        from app.agents.researcher import ResearcherAgent
        
        agent = ResearcherAgent()
        print("✓ Researcher Agent initialized")
        
        # Simple test
        grievance = "I bought a defective phone. Seller refuses refund."
        result = await agent.analyze(grievance, "")
        
        print(f"✓ Analysis complete")
        print(f"  - Legal provisions found: {len(result.get('legal_provisions', []))}")
        print(f"  - Merit score: {result.get('merits_score')}/10")
        print(f"  - First provision: {result.get('legal_provisions', ['None'])[0]}")
        
        return True
    except Exception as e:
        print(f"❌ Researcher Agent failed: {str(e)}")
        return False


async def test_drafter_agent():
    """Test the Drafter Agent."""
    print("\n2. Testing Drafter Agent...")
    print("-" * 80)
    
    try:
        from app.agents.drafter import DrafterAgent
        
        agent = DrafterAgent()
        print("✓ Drafter Agent initialized")
        
        # Mock research findings
        research = {
            "summary_of_facts": ["Purchased defective phone", "Seller refused refund"],
            "legal_provisions": ["Consumer Protection Act 2019, Section 35"],
            "merits_score": 8,
            "reasoning": "Clear case of defective goods"
        }
        
        grievance = "I bought a defective phone. Seller refuses refund."
        draft = await agent.draft(grievance, research, "")
        
        print(f"✓ Draft created")
        print(f"  - Document length: {len(draft)} characters")
        print(f"  - Contains 'To:': {'To:' in draft}")
        print(f"  - Contains 'Prayer': {'Prayer' in draft or 'prayer' in draft}")
        
        return True
    except Exception as e:
        print(f"❌ Drafter Agent failed: {str(e)}")
        return False


async def test_expert_reviewer_agent():
    """Test the Expert Reviewer Agent."""
    print("\n3. Testing Expert Reviewer Agent...")
    print("-" * 80)
    
    try:
        from app.agents.expert_reviewer import ExpertReviewerAgent
        
        agent = ExpertReviewerAgent()
        print("✓ Expert Reviewer Agent initialized")
        
        # Mock draft and research
        draft = """
To: The District Consumer Forum, Ernakulam
From: Test User
Subject: Consumer Complaint

I purchased a defective phone. Seller refuses refund.

Prayer: Refund of purchase amount.
"""
        research = {
            "legal_provisions": ["Consumer Protection Act 2019, Section 35"],
            "merits_score": 8
        }
        
        result = await agent.review(draft, research)
        
        print(f"✓ Review complete")
        print(f"  - Approved: {result.get('is_approved')}")
        print(f"  - Feedback: {result.get('feedback', 'None')[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Expert Reviewer Agent failed: {str(e)}")
        return False


async def test_orchestrator():
    """Test the complete orchestrator workflow."""
    print("\n4. Testing Orchestrator (Full Workflow)...")
    print("-" * 80)
    
    try:
        from app.services.orchestrator import LegalAidOrchestrator
        
        orchestrator = LegalAidOrchestrator()
        print("✓ Orchestrator initialized")
        
        grievance = "I bought a defective mobile phone from a shop in Kochi. The seller refuses to give a refund even though it is under warranty."
        
        print("  Running complete workflow (this may take 30-60 seconds)...")
        result = await orchestrator.generate_legal_aid(grievance, "")
        
        print(f"✓ Workflow complete")
        print(f"  - Status: {result['status']}")
        print(f"  - Iterations: {result['iterations']}")
        print(f"  - Agent traces: {len(result['agent_traces'])}")
        print(f"  - Document length: {len(result['final_document'])} characters")
        
        # Show agent trace summary
        print("\n  Agent Trace Summary:")
        for trace in result['agent_traces'][:5]:  # Show first 5
            print(f"    [{trace['agent']}] {trace['action']}")
        
        return True
    except Exception as e:
        print(f"❌ Orchestrator failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_imports():
    """Test that API components import correctly."""
    print("\n5. Testing API Components...")
    print("-" * 80)
    
    try:
        from app.main import app
        print("✓ FastAPI app imports")
        
        from app.api.v1.endpoints import router
        print("✓ API endpoints import")
        
        from app.models.schemas import LegalAidRequest, LegalAidResponse
        print("✓ Pydantic models import")
        
        return True
    except Exception as e:
        print(f"❌ API imports failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    results = []
    
    # Test individual agents
    results.append(await test_researcher_agent())
    results.append(await test_drafter_agent())
    results.append(await test_expert_reviewer_agent())
    
    # Test orchestrator
    results.append(await test_orchestrator())
    
    # Test API
    results.append(await test_api_imports())
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED! System is ready to use.")
        print("\nNext steps:")
        print("  1. Start the API: docker-compose up --build")
        print("  2. Test API: curl http://localhost:8000/api/v1/health")
        print("  3. Try example: python backend/example_usage.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        print("\nCommon issues:")
        print("  - Missing OPENAI_API_KEY in .env file")
        print("  - Missing dependencies: pip install -r requirements.txt")
        print("  - Network connectivity issues")


if __name__ == "__main__":
    asyncio.run(main())
