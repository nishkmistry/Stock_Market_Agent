"""
Test script for the agent loop with both stock and news tools
"""

import sys
# Ensure stdout can handle UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from agent import run_agent_loop

def test_combined():
    # Test queries that might use both tools
    test_queries = [
        "What's RELIANCE.NS trading at and what's the latest news?",
        "Should I consider investing in TCS.BO based on recent developments?",
        "Give me a quick overview of INFY.NS"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print('='*60)
        result = run_agent_loop(query)
        print("Final Answer:")
        print(result)
        print('-'*60)

if __name__ == "__main__":
    test_combined()