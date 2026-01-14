"""
Test script for strict validation rules implementation.
Tests circular reasoning detection, rejected factor exclusion, and integrity checks.
"""

import asyncio
from workflow.orchestrator import Orchestrator
from llm.llm_client import create_llm_client, LLMProvider
from validation import OutputFormatter


async def test_circular_reasoning():
    """Test that circular reasoning is detected and rejected."""
    print("=== TEST 1: Circular Reasoning Detection ===\n")
    
    test_document = """
    The company's hybrid work trade-offs led to decreased productivity.
    The balance between remote and office work created challenges.
    These challenges resulted in lower employee satisfaction.
    """
    
    llm_client = create_llm_client(LLMProvider.HUGGINGFACE)
    orchestrator = Orchestrator(llm_client)
    
    result = await orchestrator.analyze(test_document, show_updates=False)
    
    # Check validation results
    validation = result.get('validation_results', {})
    print(f"Circular factors detected: {validation.get('circular_factors', 0)}")
    print(f"Valid factors: {validation.get('valid_factors', 0)}/{validation.get('total_factors', 0)}")
    
    # Check integrity
    integrity = result.get('integrity_check', {})
    print(f"\nIntegrity check passed: {integrity.get('synthesis_valid', False)}")
    
    print("\n" + "="*60 + "\n")
    return result


async def test_insufficient_evidence():
    """Test that factors without evidence are rejected."""
    print("=== TEST 2: Insufficient Evidence Rejection ===\n")
    
    test_document = """
    The project failed. Some people think it was due to poor management.
    """
    
    llm_client = create_llm_client(LLMProvider.HUGGINGFACE)
    orchestrator = Orchestrator(llm_client)
    
    result = await orchestrator.analyze(test_document, show_updates=False)
    
    # Check resolutions
    resolutions = result.get('resolutions', {})
    print(f"Accepted factors: {len(resolutions.get('accepted', []))}")
    print(f"Rejected factors: {len(resolutions.get('rejected', []))}")
    
    # Check if rejected factors excluded from synthesis
    synthesis = result.get('synthesis', {})
    rejected_factors = synthesis.get('rejected_factors', [])
    print(f"\nRejected factors excluded from synthesis: {len(rejected_factors)}")
    
    print("\n" + "="*60 + "\n")
    return result


async def test_full_analysis():
    """Test full analysis with valid document."""
    print("=== TEST 3: Full Analysis with Valid Document ===\n")
    
    test_document = """
    The company implemented a new remote work policy in 2020 due to the pandemic.
    This policy was influenced by several factors:
    
    1. Government health guidelines required social distancing
    2. Employee surveys showed 85% preferred remote work options
    3. Office lease costs were $500,000 per year
    4. Productivity data from pilot programs showed 15% increase
    
    The policy allowed employees to work remotely 3 days per week.
    Initial results showed improved employee satisfaction scores from 6.5 to 8.2 out of 10.
    However, collaboration challenges emerged in cross-functional teams.
    """
    
    llm_client = create_llm_client(LLMProvider.HUGGINGFACE)
    orchestrator = Orchestrator(llm_client)
    
    result = await orchestrator.analyze(test_document, show_updates=True)
    
    # Format output
    formatted_output = OutputFormatter.format_analysis_output(result)
    print("\n" + "="*60)
    print("FORMATTED OUTPUT:")
    print("="*60 + "\n")
    print(formatted_output)
    
    # Compact summary
    summary = OutputFormatter.format_compact_summary(result)
    print("\n" + "="*60)
    print("COMPACT SUMMARY:")
    print("="*60 + "\n")
    print(summary)
    
    return result


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("STRICT VALIDATION RULES - TEST SUITE")
    print("="*60 + "\n")
    
    try:
        # Test 1: Circular reasoning
        result1 = await test_circular_reasoning()
        
        # Test 2: Insufficient evidence
        result2 = await test_insufficient_evidence()
        
        # Test 3: Full analysis
        result3 = await test_full_analysis()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
