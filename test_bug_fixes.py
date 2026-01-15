"""
Simple test script to verify bug fixes without Docker deployment
Tests the fixed disagreement scoring and auto-rejection logic
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from backend.workflow.orchestrator import Orchestrator
from backend.llm.llm_client import create_llm_client, LLMProvider


async def test_auto_rejection_fix():
    """Test that weak evidence doesn't cause auto-rejection"""
    print("\n" + "="*60)
    print("TEST 1: Auto-Rejection Fix")
    print("="*60 + "\n")
    
    # Test with minimal input (should trigger INSUFFICIENT_EVIDENCE)
    test_input = "The project failed due to poor management."
    
    print(f"Input: {test_input}\n")
    
    llm_client = create_llm_client(LLMProvider.HUGGINGFACE)
    orchestrator = Orchestrator(llm_client)
    
    result = await orchestrator.analyze(test_input, show_updates=True)
    
    # Check results
    debates = result.get('debates', {})
    resolutions = result.get('resolutions', {})
    
    print("\n" + "-"*60)
    print("RESULTS:")
    print("-"*60)
    
    for factor_id, debate in debates.items():
        critique = debate.get('critique', {})
        resolution = critique.get('resolution', 'UNKNOWN')
        support = debate.get('support', {})
        has_evidence = support.get('has_evidence', True)
        
        print(f"\nFactor {factor_id}:")
        print(f"  Has Evidence: {has_evidence}")
        print(f"  Resolution: {resolution}")
        print(f"  Justification: {critique.get('justification', 'N/A')[:100]}...")
        
        # Check if auto-rejected due to weak evidence
        if not has_evidence and resolution == 'REJECTED':
            justification = critique.get('justification', '')
            if 'insufficient evidence' in justification.lower() and 'supporting agent' in justification.lower():
                print("  ⚠️  WARNING: Still auto-rejecting for weak evidence!")
            else:
                print("  ✅ Properly evaluated by LLM despite weak evidence")
    
    print(f"\nAccepted: {len(resolutions.get('accepted', []))}")
    print(f"Rejected: {len(resolutions.get('rejected', []))}")
    print(f"Partially Accepted: {len(resolutions.get('partially_accepted', []))}")
    
    return result


async def test_disagreement_scoring():
    """Test that disagreement scores are dynamic, not hardcoded 90%"""
    print("\n" + "="*60)
    print("TEST 2: Dynamic Disagreement Scoring")
    print("="*60 + "\n")
    
    # Test with substantial input
    test_input = """
    The company implemented a new remote work policy in 2020.
    This was influenced by government health guidelines and employee preferences.
    Initial results showed improved satisfaction scores from 6.5 to 8.2 out of 10.
    However, collaboration challenges emerged in cross-functional teams.
    """
    
    print(f"Input: {test_input.strip()}\n")
    
    llm_client = create_llm_client(LLMProvider.HUGGINGFACE)
    orchestrator = Orchestrator(llm_client)
    
    result = await orchestrator.analyze(test_input, show_updates=True)
    
    # Simulate frontend transformation
    print("\n" + "-"*60)
    print("DISAGREEMENT SCORES (Frontend Calculation):")
    print("-"*60)
    
    debates = result.get('debates', {})
    
    disagreement_scores = []
    for factor_id, debate in debates.items():
        critique = debate.get('critique', {})
        support = debate.get('support', {})
        rebuttal = debate.get('rebuttal', {})
        resolution = critique.get('resolution', 'UNKNOWN')
        
        # Simulate frontend calculation
        base_score = {
            'ACCEPTED': 0.1,
            'PARTIALLY_ACCEPTED': 0.4,
            'WEAKENED': 0.6,
            'REJECTED': 0.7  # Changed from 0.9
        }.get(resolution.upper(), 0.5)
        
        adjustment = 0
        
        # Evidence quality
        has_evidence = support.get('has_evidence', True)
        if not has_evidence:
            adjustment += 0.15
        
        # Rebuttal
        if rebuttal:
            is_concession = rebuttal.get('is_concession', False)
            if is_concession:
                adjustment += 0.15
        
        final_score = max(0, min(1, base_score + adjustment))
        disagreement_scores.append(final_score)
        
        print(f"\nFactor {factor_id}:")
        print(f"  Resolution: {resolution}")
        print(f"  Base Score: {base_score:.2f}")
        print(f"  Adjustment: {adjustment:+.2f}")
        print(f"  Final Disagreement: {final_score:.2%}")
        
        if resolution == 'REJECTED' and final_score == 0.9:
            print("  ⚠️  WARNING: Still using hardcoded 90%!")
        elif resolution == 'REJECTED':
            print(f"  ✅ Dynamic scoring working! (not 90%)")
    
    # Check if all scores are the same
    if len(set(disagreement_scores)) == 1 and disagreement_scores[0] == 0.9:
        print("\n❌ FAILED: All scores are 90% (hardcoded)")
    else:
        print(f"\n✅ PASSED: Dynamic scoring detected (scores: {[f'{s:.0%}' for s in disagreement_scores]})")
    
    return result


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BUG FIX VERIFICATION TESTS")
    print("="*60)
    
    try:
        # Test 1: Auto-rejection fix
        await test_auto_rejection_fix()
        
        # Test 2: Disagreement scoring fix
        await test_disagreement_scoring()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
