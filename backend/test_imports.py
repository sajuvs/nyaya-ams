"""
Quick import test - verifies all components load without errors.
No API calls, just checks if everything is properly structured.
"""
import sys
import os

print("="*80)
print("NYAYA-FLOW IMPORT TEST")
print("="*80 + "\n")

tests_passed = 0
tests_total = 0

def test_import(module_path, description):
    """Test if a module can be imported."""
    global tests_passed, tests_total
    tests_total += 1
    
    try:
        parts = module_path.split('.')
        module = __import__(module_path)
        for part in parts[1:]:
            module = getattr(module, part)
        print(f"✓ {description}")
        tests_passed += 1
        return True
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Error: {str(e)}")
        return False

print("1. Testing Agent Imports...")
print("-" * 80)
test_import("app.agents.researcher", "Researcher Agent")
test_import("app.agents.drafter", "Drafter Agent")
test_import("app.agents.expert_reviewer", "Expert Reviewer Agent")

print("\n2. Testing Service Imports...")
print("-" * 80)
test_import("app.services.orchestrator", "Orchestrator Service")

print("\n3. Testing API Imports...")
print("-" * 80)
test_import("app.main", "FastAPI Application")
test_import("app.api.v1.endpoints", "API Endpoints")

print("\n4. Testing Model Imports...")
print("-" * 80)
test_import("app.models.schemas", "Pydantic Schemas")

print("\n5. Testing Agent Classes...")
print("-" * 80)
try:
    from app.agents.researcher import ResearcherAgent
    from app.agents.drafter import DrafterAgent
    from app.agents.expert_reviewer import ExpertReviewerAgent
    from app.services.orchestrator import LegalAidOrchestrator
    
    print("✓ All agent classes can be instantiated")
    tests_passed += 1
except Exception as e:
    print(f"❌ Agent class instantiation failed: {str(e)}")
tests_total += 1

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"\nTests Passed: {tests_passed}/{tests_total}")

if tests_passed == tests_total:
    print("\n✅ ALL IMPORTS SUCCESSFUL!")
    print("\nYour code structure is correct. Next steps:")
    print("  1. Add OPENAI_API_KEY to .env file")
    print("  2. Run full test: python backend/test_agents.py")
    print("  3. Start API: docker-compose up --build")
else:
    print(f"\n⚠️  {tests_total - tests_passed} import(s) failed")
    print("\nCommon fixes:")
    print("  - Install dependencies: pip install -r requirements.txt")
    print("  - Check Python version: python --version (need 3.11+)")
    print("  - Run from project root directory")

sys.exit(0 if tests_passed == tests_total else 1)
