"""
Test Gemini API with minimal calls to check quota status
"""

import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def test_minimal_call():
    """Make a minimal API call to test quota"""
    try:
        print("Making minimal API call...")
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents="Hello"
        )
        print(f"Success: {response.text[:50]}...")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Gemini API quota status...")
    success = test_minimal_call()
    if success:
        print("Quota available!")
    else:
        print("Quota exhausted or other error")