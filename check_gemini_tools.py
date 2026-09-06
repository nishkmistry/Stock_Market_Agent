"""
Check how to properly use tools with Gemini in google-genai
"""

import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Let's check what methods are available on the client
print("Client methods:")
methods = [method for method in dir(client) if not method.startswith('_')]
for method in sorted(methods):
    print(f"  {method}")

# Check the types module for function declarations
print("\nChecking types for function declarations:")
try:
    from google.genai import types
    print("Types module imported successfully")

    # Check what's in types
    types_attrs = [attr for attr in dir(types) if not attr.startswith('_')]
    print(f"Types attributes: {types_attrs[:20]}...")  # First 20

    # Look for function-related types
    function_related = [attr for attr in types_attrs if 'func' in attr.lower() or 'tool' in attr.lower()]
    print(f"Function/tool related: {function_related}")

except Exception as e:
    print(f"Error importing types: {e}")

# Let's also check the chat module
print("\nChecking chat capabilities:")
try:
    # Try to see what parameters chats.create accepts
    help(client.chats.create)
except Exception as e:
    print(f"Error getting help: {e}")