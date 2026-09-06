import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Initialize client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# List available models
print("Available models:")
for model in client.models.list():
    print(f"- {model.name}")

# Test a simple generation
print("\nTesting simple generation:")
try:
    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents="Say hello in one sentence."
    )
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

    # Try other common model names
    model_names = [
        "gemini-pro",
        "gemini-1.0-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro-latest"
    ]

    for model_name in model_names:
        try:
            print(f"\nTrying model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents="Say hello in one sentence."
            )
            print(f"Success! Response: {response.text}")
            break
        except Exception as e2:
            print(f"Failed: {e2}")