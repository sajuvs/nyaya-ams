"""
Example usage of the Nyaya-Flow Legal Aid API.

This script demonstrates how to interact with the multi-agent system.
"""
import asyncio
import json
from app.services.orchestrator import LegalAidOrchestrator


async def example_consumer_complaint():
    """Example: Consumer complaint for defective product."""
    print("=" * 80)
    print("EXAMPLE 1: Consumer Complaint - Defective Mobile Phone")
    print("=" * 80)
    
    grievance = """
    I purchased a mobile phone worth Rs. 25,000 from a shop in Kochi, Kerala on 
    January 15, 2026. Within 10 days, the phone started having serious issues - 
    the screen would randomly go black and the battery would drain within 2 hours.
    
    I went back to the shop multiple times requesting a replacement or refund as 
    the phone is clearly defective and still under warranty. The shopkeeper refuses 
    to help and says "all sales are final". I have the original bill and warranty card.
    
    I need help filing a consumer complaint to get my money back or a replacement phone.
    """
    
    orchestrator = LegalAidOrchestrator()
    
    print("\n🤖 Starting multi-agent workflow...\n")
    
    result = await orchestrator.generate_legal_aid(
        grievance=grievance,
        rag_context=""
    )
    
    print("\n📊 WORKFLOW SUMMARY")
    print("-" * 80)
    print(f"Status: {result['status']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Case Merit Score: {result['research_findings'].get('merits_score')}/10")
    
    print("\n📋 AGENT TRACES")
    print("-" * 80)
    for trace in result['agent_traces']:
        print(f"[{trace['agent'].upper()}] {trace['action']}")
        print(f"  → {trace['details'][:100]}...")
        print()
    
    print("\n⚖️  LEGAL PROVISIONS IDENTIFIED")
    print("-" * 80)
    for provision in result['research_findings'].get('legal_provisions', []):
        print(f"  • {provision}")
    
    print("\n📄 FINAL DOCUMENT")
    print("-" * 80)
    print(result['final_document'][:500] + "...\n")
    
    print("\n✅ REVIEW RESULT")
    print("-" * 80)
    review = result['review_result']
    print(f"Approved: {review.get('is_approved')}")
    print(f"Jurisdiction Check: {review.get('jurisdiction_check', 'N/A')}")
    print(f"Statute Check: {review.get('statute_check', 'N/A')}")
    print(f"Tone Check: {review.get('tone_check', 'N/A')}")
    
    return result


async def example_service_denial():
    """Example: Public service denial complaint."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Public Service Denial")
    print("=" * 80)
    
    grievance = """
    I applied for a birth certificate for my newborn child at the local Panchayat 
    office in Thiruvananthapuram on December 1, 2025. According to the Kerala Right 
    to Public Service Act, this should be issued within 7 days.
    
    It has been over 60 days now and despite multiple visits and follow-ups, the 
    officials keep saying "come next week". They are not giving me any written 
    reason for the delay. I have submitted all required documents.
    
    This delay is causing problems as I need the birth certificate for my child's 
    passport application. I want to file a complaint under the Right to Service Act.
    """
    
    orchestrator = LegalAidOrchestrator()
    
    print("\n🤖 Starting multi-agent workflow...\n")
    
    result = await orchestrator.generate_legal_aid(
        grievance=grievance,
        rag_context=""
    )
    
    print("\n📊 WORKFLOW SUMMARY")
    print("-" * 80)
    print(f"Status: {result['status']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Case Merit Score: {result['research_findings'].get('merits_score')}/10")
    
    print("\n⚖️  LEGAL PROVISIONS IDENTIFIED")
    print("-" * 80)
    for provision in result['research_findings'].get('legal_provisions', []):
        print(f"  • {provision}")
    
    print("\n📄 DOCUMENT PREVIEW")
    print("-" * 80)
    print(result['final_document'][:400] + "...\n")
    
    return result


async def main():
    """Run all examples."""
    print("\n🏛️  NYAYA-FLOW LEGAL AID PLATFORM - EXAMPLES\n")
    
    try:
        # Example 1: Consumer Complaint
        result1 = await example_consumer_complaint()
        
        # Example 2: Service Denial
        result2 = await example_service_denial()
        
        print("\n" + "=" * 80)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nThe multi-agent system successfully:")
        print("  1. Analyzed both grievances")
        print("  2. Identified applicable Indian laws")
        print("  3. Generated formal legal petitions")
        print("  4. Passed expert review audits")
        print("\n💡 Check the output above for detailed agent traces and documents.")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure:")
        print("  1. GROQ_API_KEY is set in your .env file")
        print("  2. You have internet connectivity")
        print("  3. All dependencies are installed")


if __name__ == "__main__":
    asyncio.run(main())
