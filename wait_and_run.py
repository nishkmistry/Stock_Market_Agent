import time
import subprocess
import sys

print("Waiting 30 seconds for Gemini API quota to reset...")
time.sleep(30)

print("Running debug agent...")
result = subprocess.run([sys.executable, "debug_agent3.py"],
                       capture_output=True, text=True, encoding='utf-8')

print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print(f"Return code: {result.returncode}")