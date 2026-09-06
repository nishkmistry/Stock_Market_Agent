"""
Agent logic without API calls - for testing the flow
"""

import os
import json
import sys
from typing import Dict, Any
from tools import get_stock_overview, get_news, query_filings_rag

def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool function with the given input.

    Args:
        tool_name (str): Name of the tool to execute
        tool_input (Dict[str, Any]): Input parameters for the tool

    Returns:
        Dict[str, Any]: Tool execution result
    """
    # Map tool names to actual functions
    TOOL_FUNCTIONS = {
        "get_stock_overview": get_stock_overview,
        "get_news": get_news,
        "query_filings_rag": query_filings_rag
    }

    if tool_name not in TOOL_FUNCTIONS:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        func = TOOL_FUNCTIONS[tool_name]
        result = func(**tool_input)
        # Convert result to JSON-serializable format if needed
        if hasattr(result, '__dict__'):
            result = result.__dict__
        return result
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}

def simulate_agent_response(user_query: str) -> str:
    """
    Simulate what the agent would do without actually calling the LLM.
    This is for testing the tool execution flow.
    """
    print(f"Simulating agent processing: {user_query}")

    # Simple keyword-based tool selection (simulating what LLM would decide)
    if "price" in user_query.lower() or "trading" in user_query.lower() or "stock" in user_query.lower():
        # Extract ticker - simple approach
        import re
        ticker_match = re.search(r'([A-Z]+\.[A-Z]{2})', user_query.upper())
        if ticker_match:
            ticker = ticker_match.group(1)
            print(f"Detected ticker: {ticker}, calling get_stock_overview")
            result = execute_tool("get_stock_overview", {"ticker": ticker})
            return f"Based on stock data: {json.dumps(result, indent=2)}"

    if "news" in user_query.lower():
        # Extract ticker
        import re
        ticker_match = re.search(r'([A-Z]+\.[A-Z]{2})', user_query.upper())
        if ticker_match:
            ticker = ticker_match.group(1)
            print(f"Detected ticker: {ticker}, calling get_news")
            result = execute_tool("get_news", {"ticker": ticker, "limit": 5})
            return f"Based on news data: {json.dumps(result, indent=2)}"

    # Default response
    return "I would use the available tools to answer your question about stock data, news, or regulatory filings. Please specify what you'd like to know."

if __name__ == "__main__":
    # Test the simulation
    test_queries = [
        "What's RELIANCE.NS trading at right now?",
        "Show me recent news for TCS.NS",
        "What are the latest regulatory filings for INFY.NS?"
    ]

    for query in test_queries:
        print("=" * 60)
        print(f"Query: {query}")
        print("=" * 60)
        response = simulate_agent_response(query)
        print(response)
        print()