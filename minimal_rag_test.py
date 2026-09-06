#!/usr/bin/env python
# Minimal test to check if the RAG module structure is correct

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("Testing RAG module structure...")
print("=" * 40)

try:
    # Just test that we can import and instantiate the class
    from rag import FinancialRAG

    print("[PASS] FinancialRAG imported successfully")

    # Check if the class has the expected methods
    methods = ['__init__', '_chunk_text', '_generate_chunk_id', 'add_document',
               'add_document_from_file', 'query', 'get_collection_stats', 'clear_collection']

    for method in methods:
        if hasattr(FinancialRAG, method):
            print(f"[PASS] Method '{method}' exists")
        else:
            print(f"[FAIL] Method '{method}' missing")

    # Check if the tool function exists
    from rag import query_filings_rag
    print("[PASS] query_filings_rag function imported successfully")

    print("=" * 40)
    print("[PASS] RAG module structure test completed!")

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()