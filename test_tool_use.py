"""
Test to see if Gemini can actually use tools when explicitly prompted
"""

import os
import json
from google import genai
from dotenv import load_dotenv
from tools import get_stock_overview

# Load environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def test_tool_use():
    # Define the tool for get_stock_overview
    stock_tool = {
        "name": "get_stock_overview",
        "description": "Get comprehensive stock overview data for a given ticker symbol including price, market cap, P/E ratio, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., 'RELIANCE.NS' for NSE, 'RELIANCE.BO' for BSE, 'AAPL' for US)"
                }
            },
            "required": ["ticker"]
        }
    }

    # Start a chat with the model
    chat = client.chats.create(model="gemini-3.6-flash")

    # System prompt that encourages tool use
    system_prompt = """You are a specialized financial research agent.
    When users ask about stock prices or financial data, you MUST use the available tools to get real-time data.
    Do not make up or guess financial data - always use the tools."""

    chat.send_message(system_prompt)

    # User query that should trigger tool use
    user_query = "What's the current price of RELIANCE.NS stock? Use the get_stock_overview tool to get this information."
    print(f"Sending query: {user_query}")

    response = chat.send_message(user_query)

    print(f"Response text: '{response.text}'")
    print(f"Has function_calls: {hasattr(response, 'function_calls')}")
    if hasattr(response, 'function_calls'):
        print(f"function_calls value: {response.function_calls}")
        if response.function_calls:
            print(f"Number of function calls: {len(response.function_calls)}")
            for i, fc in enumerate(response.function_calls):
                print(f"  Function call {i}: {fc.name} with args {fc.args}")
        else:
            print("function_calls is None or empty")

    # Check candidates for function calls in parts
    if hasattr(response, 'candidates'):
        for i, candidate in enumerate(response.candidates or []):
            print(f"\nCandidate {i}:")
            print(f"  Content: {candidate.content}")
            if hasattr(candidate.content, 'parts'):
                for j, part in enumerate(candidate.content.parts):
                    print(f"    Part {j}: {part}")
                    if hasattr(part, 'function_call') and part.function_call:
                        print(f"      FUNCTION CALL: {part.function_call}")
                    if hasattr(part, 'text') and part.text:
                        print(f"      TEXT: '{part.text[:100]}...'")

if __name__ == "__main__":
    test_tool_use()