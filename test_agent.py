"""
Test script for the agent loop with stock overview tool only
"""

import sys
# Ensure stdout can handle UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from agent import run_agent_loop

def test_agent():
    # Test the agent with a simple query
    test_query = "What's RELIANCE.NS trading at right now?"
    print("Testing agent loop with query:", test_query)
    print("=" * 50)
    result = run_agent_loop(test_query)
    print("Final Answer:")
    # Print result, ensuring UTF-8 output
    print(result)
    print("=" * 50)

if __name__ == "__main__":
    test_agent()