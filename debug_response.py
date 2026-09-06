"""
Debug script to see what the Gemini response actually contains
"""

import os
import json
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def debug_gemini_response():
    # Start a chat with the model
    chat = client.chats.create(model="gemini-3.6-flash")

    # Simple test
    system_prompt = "You are a helpful assistant."
    chat.send_message(system_prompt)

    user_query = "What's RELIANCE.NS trading at right now?"
    print(f"Sending query: {user_query}")
    response = chat.send_message(user_query)

    print(f"Response type: {type(response)}")
    print(f"Response dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")
    print(f"Has function_calls attr: {hasattr(response, 'function_calls')}")
    if hasattr(response, 'function_calls'):
        print(f"function_calls value: {response.function_calls}")
        print(f"function_calls type: {type(response.function_calls)}")

    print(f"Has text attr: {hasattr(response, 'text')}")
    if hasattr(response, 'text'):
        print(f"text value: '{response.text}'")
        print(f"text type: {type(response.text)}")

    # Check candidates
    if hasattr(response, 'candidates'):
        print(f"Has candidates: {len(response.candidates) if response.candidates else 0}")
        for i, candidate in enumerate(response.candidates or []):
            print(f"  Candidate {i}: {candidate}")
            print(f"    Content: {candidate.content}")
            if hasattr(candidate.content, 'parts'):
                print(f"    Parts: {len(candidate.content.parts)}")
                for j, part in enumerate(candidate.content.parts):
                    print(f"      Part {j}: {part}")
                    print(f"        Part type: {type(part)}")
                    if hasattr(part, 'function_call'):
                        print(f"        Has function_call: {part.function_call}")
                    if hasattr(part, 'text'):
                        print(f"        Has text: '{part.text}'")

if __name__ == "__main__":
    debug_gemini_response()