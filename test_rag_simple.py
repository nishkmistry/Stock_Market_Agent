import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Test RAG with existing database if it exists, otherwise skip
from rag import FinancialRAG

def test_rag_simple():
    print("Testing RAG functionality...")

    # Check if we have existing data
    db_path = "./chroma_db"
    if os.path.exists(db_path):
        print("Found existing ChromaDB, testing with existing data...")
        try:
            rag = FinancialRAG(db_path)
            stats = rag.get_collection_stats()
            print(f"Collection stats: {stats}")

            # Test a simple query
            results = rag.query("What are the listing requirements for NSE?", n_results=2)
            print(f"Query returned {len(results.get('results', []))} results")

            if results.get('results'):
                print("First result preview:", results['results'][0].get('text', '')[:100] + "...")
            else:
                print("No results found - may need to ingest sample data first")

        except Exception as e:
            print(f"Error testing RAG: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No existing ChromaDB found. Skipping RAG test for now.")
        print("To test RAG, run: python ingest_sample_docs.py")

if __name__ == "__main__":
    test_rag_simple()