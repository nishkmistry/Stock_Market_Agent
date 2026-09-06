#!/usr/bin/env python
# Direct test of RAG functionality without background processes

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("Testing RAG with minimal document set...")
print("=" * 50)

try:
    from rag import FinancialRAG

    # Create a test directory for our small test
    test_db_path = "./test_chroma_db_mini"

    # Remove if exists
    import shutil
    shutil.rmtree(test_db_path, ignore_errors=True)

    print("Initializing RAG...")
    rag = FinancialRAG(test_db_path)
    print("✅ RAG initialized")

    # Add a very small test document
    test_doc = """
    NATIONAL STOCK EXCHANGE OF INDIA LIMITED
    LISTING REQUIREMENTS

    Minimum paid-up equity capital: ₹10 crores
    Minimum market capitalization: ₹25 crores
    Minimum public shareholding: 25%
    """

    print("Adding test document...")
    success = rag.add_document(test_doc, "NSE_LISTING_REQUIREMENTS", {"type": "listing"})
    if success:
        print("✅ Document added successfully")
    else:
        print("❌ Failed to add document")

    # Test query
    print("Testing query...")
    results = rag.query("What are the listing requirements for NSE?", n_results=1)
    print(f"Query returned {len(results.get('results', []))} results")

    if results.get('results'):
        print("✅ Query successful!")
        print("Result preview:", results['results'][0].get('text', '')[:100])
    else:
        print("❌ No results returned")

    # Show stats
    stats = rag.get_collection_stats()
    print(f"Collection stats: {stats}")

    # Cleanup
    shutil.rmtree(test_db_path, ignore_errors=True)
    print("🧹 Cleaned up test database")
    print("=" * 50)
    print("🎉 RAG test completed successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()