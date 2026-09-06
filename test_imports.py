"""
Test if required packages for RAG are installed
"""

try:
    import chromadb
    print("[OK] chromadb imported successfully")
except ImportError as e:
    print(f"[ERROR] chromadb import failed: {e}")

try:
    from sentence_transformers import SentenceTransformer
    print("[OK] sentence-transformers imported successfully")
except ImportError as e:
    print(f"[ERROR] sentence-transformers import failed: {e}")

try:
    from dotenv import load_dotenv
    print("[OK] python-dotenv imported successfully")
except ImportError as e:
    print(f"[ERROR] python-dotenv import failed: {e}")

print("All import tests completed")