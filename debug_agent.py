"""
Debug version of the agent to see what's happening
"""

import os
import json
from typing import Dict, List, Any, Optional
from google import genai
from dotenv import load_dotenv
from tools import get_stock_overview, get_news, query_filings_rag

# Load environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def run_agent_loop_debug(user_query: str, max_iterations: int = 10) -> str:
    """
    Debug version of the agent loop to see what's happening
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

    Think step by step and use tools as needed to answer the answer the user's question comprehensively."""

    # Start a chat with the model
    chat = client.chats.create(model="gemini-3.6-flash")

    # Add system prompt as initial context
    print("Sending system prompt...")
    system_response = chat.send_message(system_prompt)
    print(f"System response: {system_response.text[:100]}...")

    # Add user query
    print(f"Sending user query: {user_query}")
    response = chat.send_message(user_query)
    print(f"Initial response received. Has function_calls: {hasattr(response, 'function_calls')}")
    if hasattr(response, 'function_calls'):
        print(f"Number of function calls: {len(response.function_calls)}")
        if response.function_calls:
            for i, fc in enumerate(response.function_calls):
                print(f"  Function call {i}: {fc.name} with args {fc.args}")
    print(f"Response text: '{response.text}'")

    # Track tool calls for transparency
    tool_call_history = []

    for iteration in range(max_iterations):
        print(f"\n=== Iteration {iteration + 1} ===")
        try:
            # Check if the response contains a function call
            if hasattr(response, 'function_calls') and response.function_calls:
                print(f"Processing {len(response.function_calls)} function calls...")
                # Process tool calls
                function_responses = []

                for fc in response.function_calls:
                    tool_name = fc.name
                    tool_input = dict(fc.args)  # Convert to dict

                    print(f"  Executing tool: {tool_name} with input: {tool_input}")

                    # Record tool call
                    tool_call_record = {
                        "iteration": iteration + 1,
                        "tool": tool_name,
                        "input": tool_input
                    }
                    tool_call_history.append(tool_call_record)

                    # Execute the tool
                    tool_result = execute_tool(tool_name, tool_input)
                    print(f"  Tool result: {str(tool_result)[:100]}...")

                    # Record tool result
                    tool_result_record = {
                        "iteration": iteration + 1,
                        "tool": tool_name,
                        "result": tool_result
                    }

                    # Prepare tool result for Gemini
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={"result": json.dumps(tool_result)}
                            )
                        )
                    )

                # Send function responses back to the model
                print(f"Sending {len(function_responses)} function responses back to model...")
                response = chat.send_message(function_responses)
                print(f"Got response. Has function_calls: {hasattr(response, 'function_calls')}")
                if hasattr(response, 'function_calls'):
                    print(f"Number of function calls: {len(response.function_calls)}")
                print(f"Response text: '{response.text}'")
                continue

            # If we get here, there are no function calls, so we have a final answer
            print("No function calls found, returning final answer")
            final_answer = response.text
            return final_answer

        except Exception as e:
            print(f"Error in iteration {iteration}: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error in agent loop: {str(e)}"

    # If we've exceeded max iterations
    return f"Agent reached maximum iterations ({max_iterations}) without completing. Consider simplifying your query."

def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool function with the given input.

    Args:
        tool_name (str): Name of the tool to execute
        tool_input (Dict[str, Any]): Input parameters for the tool

    Returns:
        Dict[str, Any]: Tool execution result
    """
    print(f"    [EXECUTE_TOOL] {tool_name} with {tool_input}")
    if tool_name not in TOOL_FUNCTIONS:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        func = TOOL_FUNCTIONS[tool_name]
        result = func(**tool_input)
        print(f"    [EXECUTE_TOOL] Result: {str(result)[:100]}...")
        return result
    except Exception as e:
        error_msg = f"Tool execution failed: {str(e)}"
        print(f"    [EXECUTE_TOOL] Error: {error_msg}")
        return {"error": error_msg}

# Map tool names to actual functions
TOOL_FUNCTIONS = {
    "get_stock_overview": get_stock_overview,
    "get_news": get_news,
    "query_filings_rag": query_filings_rag
}

if __name__ == "__main__":
    # Test the agent with a simple query
    test_query = "What's RELIANCE.NS trading at right now?"
    print("Testing agent loop with query:", test_query)
    print("=" * 50)
    result = run_agent_loop_debug(test_query)
    print("=" * 50)
    print("Final Answer:")
    print(result)
    print("=" * 50)