"""
Test the proper way to configure tools with Gemini API
"""

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

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

# Create a tool containing these function declarations
stock_tool = types.Tool(
    function_declarations=[get_stock_overview_declaration, get_news_declaration]
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

def test_with_proper_config():
    # Start a chat with the model using proper config
    chat = client.chats.create(
        model="gemini-3.6-flash",
        config=generate_content_config
    )

    # System prompt
    system_prompt = """You are a specialized financial research agent.
    When users ask about stock prices or financial data, you MUST use the available tools to get real-time data.
    Do not make up or guess financial data - always use the tools."""

    chat.send_message(system_prompt)

    # User query
    user_query = "What's the current price of RELIANCE.NS stock?"
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
                        print(f"        Name: {part.function_call.name}")
                        print(f"        Args: {part.function_call.args}")
                    if hasattr(part, 'text') and part.text:
                        print(f"      TEXT: '{part.text[:100]}...'")

if __name__ == "__main__":
    test_with_proper_config()