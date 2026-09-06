"""
Orchestration loop for the Finance Agent using Gemini API function calling.
Implements a ReAct-style loop where the LLM decides which tools to call and processes results.
"""

import os
import json
import sys
import time
from typing import Dict, List, Any, Optional
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
# Try gemini-2.5-flash which might have better quota availability
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
        return result
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}

def run_agent_loop(user_query: str, max_iterations: int = 10) -> str:
    """
    Run the agent loop where the LLM decides which tools to call.

    Args:
        user_query (str): The user's question or request
        max_iterations (int): Maximum number of tool call iterations to prevent infinite loops

    Returns:
        str: Final response from the agent
    """
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
    # Try different models in order of preference
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-3.6-flash",
        "gemini-flash-latest"
    ]

    chat = None
    last_error = None

    for model_name in models_to_try:
        try:
            chat = client.chats.create(
                model=model_name,
                config=generate_content_config
            )
            # Test the connection with a simple message
            chat.send_message("test")
            break  # Success, exit the loop
        except Exception as e:
            last_error = e
            continue  # Try next model

    if chat is None:
        # If all models failed, return error message
        if last_error and "RESOURCE_EXHAUSTED" in str(last_error):
            return "Agent temporarily unavailable due to API quota limits. Please try again in a few minutes."
        else:
            return f"Failed to initialize agent: {str(last_error)}"

    # Add system prompt as initial context
    try:
        chat.send_message(system_prompt)
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            return "Agent temporarily unavailable due to API quota limits. Please try again in a few minutes."
        else:
            return f"Error in agent loop: {str(e)}"

    # Add user query
    try:
        response = chat.send_message(user_query)
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            return "Agent temporarily unavailable due to API quota limits. Please try again in a few minutes."
        else:
            return f"Error in agent loop: {str(e)}"

    # Track tool calls for transparency
    tool_call_history = []

    for iteration in range(max_iterations):
        try:
            # Check if the response contains a function call
            # Handle the case where function_calls might be None
            function_calls = getattr(response, 'function_calls', None) or []

            if function_calls:
                # Process tool calls
                function_responses = []

                for fc in function_calls:
                    tool_name = fc.name
                    tool_input = dict(fc.args)  # Convert to dict

                    # Record tool call
                    tool_call_record = {
                        "iteration": iteration + 1,
                        "tool": tool_name,
                        "input": tool_input
                    }
                    tool_call_history.append(tool_call_record)

                    # Execute the tool
                    tool_result = execute_tool(tool_name, tool_input)

                    # Record tool result
                    tool_result_record = {
                        "iteration": iteration + 1,
                        "tool": tool_name,
                        "result": tool_result
                    }

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
                try:
                    response = chat.send_message(function_responses)
                except Exception as e:
                    if "RESOURCE_EXHAUSTED" in str(e):
                        return "Agent temporarily unavailable due to API quota limits. Please try again in a few minutes."
                    else:
                        return f"Error in agent loop: {str(e)}"
                continue

            # If we get here, there are no function calls, so we have a final answer
            final_answer = response.text
            return final_answer

        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                return "Agent temporarily unavailable due to API quota limits. Please try again in a few minutes."
            else:
                return f"Error in agent loop: {str(e)}"

    # If we've exceeded max iterations
    return f"Agent reached maximum iterations ({max_iterations}) without completing. Consider simplifying your query."

# For testing the agent loop directly
if __name__ == "__main__":
    # Test the agent with a simple query
    test_query = "What's RELIANCE.NS trading at right now?"
    print("Testing agent loop with query:", test_query)
    print("=" * 50)
    result = run_agent_loop(test_query)
    print("Final Answer:")
    # Handle potential Unicode encoding issues on Windows
    try:
        print(result)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        sys.stdout.buffer.write(result.encode('utf-8') + b'\n')
    print("=" * 50)