#!/usr/bin/env python3
"""Quick test to verify domain prompts load correctly without template variable errors."""

import sys
sys.path.insert(0, 'backend')

from config.domain_loader import DomainLoader
from langchain_core.prompts import ChatPromptTemplate

def test_domain_prompts(domain_name):
    """Test that domain prompts can be loaded into ChatPromptTemplate without errors."""
    print(f"\n{'='*60}")
    print(f"Testing domain: {domain_name}")
    print('='*60)
    
    try:
        # Load domain config
        config = DomainLoader.load_domain(domain_name)
        print(f"✓ Domain config loaded: {config.display_name}")
        
        # Test researcher prompt
        researcher_prompt = ChatPromptTemplate.from_messages([
            ("system", config.researcher_prompt),
            ("human", "Test query: {grievance}\n\nContext: {rag_context}")
        ])
        print("✓ Researcher prompt template created successfully")
        
        # Test drafter prompt
        drafter_prompt = ChatPromptTemplate.from_messages([
            ("system", config.drafter_prompt),
            ("human", "Grievance: {grievance}\n\nResearch: {research_findings}\n\n{feedback_section}")
        ])
        print("✓ Drafter prompt template created successfully")
        
        # Test reviewer prompt
        reviewer_prompt = ChatPromptTemplate.from_messages([
            ("system", config.reviewer_prompt),
            ("human", "Research: {research_findings}\n\nDraft: {draft}")
        ])
        print("✓ Reviewer prompt template created successfully")
        
        print(f"\n✅ All prompts for '{domain_name}' are valid!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing '{domain_name}': {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Domain Prompt Validation Test")
    print("="*60)
    
    domains = ["legal_ai", "product_comparison"]
    results = {}
    
    for domain in domains:
        results[domain] = test_domain_prompts(domain)
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for domain, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{domain}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All domains passed validation!")
    else:
        print("⚠️  Some domains failed validation")
    print("="*60 + "\n")
    
    sys.exit(0 if all_passed else 1)
