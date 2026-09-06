#!/usr/bin/env python
# Simple script to ingest documents without background processes

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("Starting document ingestion...")
print("=" * 50)

try:
    from rag import ingest_sample_documents
    ingest_sample_documents()
    print("=" * 50)
    print("✅ Document ingestion completed successfully!")
except Exception as e:
    print("=" * 50)
    print(f"❌ Error during ingestion: {e}")
    import traceback
    traceback.print_exc()