"""
Example usage of Project AETHER
"""

import asyncio
from workflow.orchestrator import Orchestrator
from llm.llm_client import create_llm_client, LLMProvider
import os

async def main():
    # Initialize LLM client
    provider = LLMProvider(os.getenv("LLM_PROVIDER", "huggingface"))
    llm_client = create_llm_client(provider)
    
    # Create orchestrator
    orchestrator = Orchestrator(llm_client)
    
    # Example document
    sample_text = """
    Case Study: Company X Performance Analysis
    
    Company X has experienced a 30% decline in revenue over the past year. 
    The company operates in the technology sector and has been facing increased 
    competition from new market entrants. Key observations:
    
    1. Market share decreased from 25% to 18%
    2. Customer retention rate dropped to 65%
    3. Employee turnover increased to 20% annually
    4. Product innovation pipeline has slowed significantly
    5. Marketing budget was reduced by 40% last quarter
    
    The board is considering several strategic options:
    - Merging with a competitor
    - Pivoting to a new market segment
    - Restructuring operations
    - Seeking additional investment
    """
    
    print("Starting Project AETHER Analysis...")
    print("=" * 60)
    
    # Run analysis
    result = await orchestrator.analyze(sample_text, show_updates=True)
    
    if result.get("success"):
        print("\n" + "=" * 60)
        print("FINAL REPORT")
        print("=" * 60)
        print(result['final_report']['report'])
        print("\n" + "=" * 60)
        print(f"Analysis complete! Identified {len(result['factors'])} factors.")
    else:
        print(f"Analysis failed: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())

