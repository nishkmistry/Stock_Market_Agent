"""
Test script for the agent loop with news tool
"""

import sys
# Ensure stdout can handle UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from agent import run_agent_loop
import json

def test_agent_news():
    # Test the agent with a news query
    test_query = "Get latest news about RELIANCE.NS"
    print("Testing agent loop with query:", test_query)
    print("=" * 50)
    result = run_agent_loop(test_query)
    print("Final Answer:")
    print(result)
    print("=" * 50)

if __name__ == "__main__":
    test_agent_news()