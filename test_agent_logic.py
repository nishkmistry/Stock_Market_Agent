"""
Test the agent logic without worrying about Unicode printing issues
"""

import os
import sys
import json
from typing import Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tools import get_stock_overview, get_news, query_filings_rag

# Load environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Define function declarations using the proper types
get_stock_overview_declaration = types.FunctionDeclaration(
    name="get_stock_overview",
    description="Get comprehensive stock overview data for a given ticker symbol including price, market cap, P/E ratio, etc.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "ticker": types.Schema(
                type=types.Type.STRING,
                description="Stock ticker symbol (e.g., 'RELIANCE.NS' for NSE, 'RELIANCE.BO' for BSE, 'AAPL' for US)"
            )
        },
        required=["ticker"]
    )
)

get_news_declaration = types.FunctionDeclaration(
    name="get_news",
    description="Get recent news articles for a given stock ticker from financial news sources",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "ticker": types.Schema(
                type=types.Type.STRING,
                description="Stock ticker symbol"
            ),
            "limit": types.Schema(
                type=types.Type.INTEGER,
                description="Maximum number of news articles to return (default: 10)",
                default=10
            )
        },
        required=["ticker"]
    )
)

query_filings_rag_declaration = types.FunctionDeclaration(
    name="query_filings_rag",
    description="Query the RAG pipeline for NSE/BSE/RBI regulatory filings and documents",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "query": types.Schema(
                type=types.Type.STRING,
                description="Search query for relevant documents"
            ),
            "ticker": types.Schema(
                type=types.Type.STRING,
                description="Optional: Filter results by specific ticker symbol"
            )
        },
        required=["query"]
    )
)

# Create a tool containing these function declarations
stock_tool = types.Tool(
    function_declarations=[get_stock_overview_declaration, get_news_declaration, query_filings_rag_declaration]
)

# Configure the tool usage
tool_config = types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(
        mode=types.FunctionCallingConfigMode.AUTO
    )
)

# Create generate content config
generate_content_config = types.GenerateContentConfig(
    tools=[stock_tool],
    tool_config=tool_config
)

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

def test_agent_logic():
    """Test the agent logic with proper error handling"""
    print("Testing agent logic...")

    # Initialize conversation with system prompt and user query
    system_prompt = """You are a specialized financial research agent for Indian and global markets.
    Your goal is to provide comprehensive investment research by using available tools to gather
    stock data, news, and regulatory filings.

    When answering:
    1. Start by understanding what information is needed
    2. Use tools strategically to gather relevant data
    3. Synthesize information from multiple sources
    4. Provide clear, well-sourced answers
    5. If you need more information, continue using tools
    6. Always cite your sources from the tool outputs

    Available tools:
    - get_stock_overview: Get current stock data and metrics
    - get_news: Get recent financial news
    - query_filings_rag: Search regulatory documents and filings

    Think step by step and use tools as needed to answer the user's question comprehensively."""

    # Start a chat with the model using proper config
    chat = client.chats.create(
        model="gemini-3.6-flash",
        config=generate_content_config
    )

    # Add system prompt as initial context
    chat.send_message(system_prompt)

    # Add user query
    user_query = "What's RELIANCE.NS trading at right now?"
    print(f"Sending query: {user_query}")
    response = chat.send_message(user_query)

    iteration = 0
    max_iterations = 5

    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")

        # Check if the response contains a function call
        function_calls = getattr(response, 'function_calls', None) or []
        print(f"Function calls: {len(function_calls)}")

        if function_calls:
            # Process tool calls
            function_responses = []

            for fc in function_calls:
                tool_name = fc.name
                tool_input = dict(fc.args)  # Convert to dict
                print(f"Calling tool: {tool_name} with input: {tool_input}")

                # Execute the tool
                tool_result = execute_tool(tool_name, tool_input)
                print(f"Tool result keys: {list(tool_result.keys()) if isinstance(tool_result, dict) else 'Not a dict'}")

                # Prepare tool result for Gemini
                function_responses.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=tool_name,
                            response={"result": json.dumps(tool_result)}
                        )
                    )
                )

            # Send function responses back to the model
            print(f"Sending {len(function_responses)} responses back to model")
            response = chat.send_message(function_responses)

            # Show a preview of the response text
            response_text = getattr(response, 'text', '') or ''
            preview = response_text[:100] + "..." if len(response_text) > 100 else response_text
            print(f"Response preview: '{preview}'")

        else:
            # No function calls, we have a final answer
            final_answer = getattr(response, 'text', '') or ''
            print(f"\nFinal answer received:")
            print(final_answer)
            return final_answer

    print("Max iterations reached")
    return getattr(response, 'text', '') or ''

if __name__ == "__main__":
    result = test_agent_logic()
    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)