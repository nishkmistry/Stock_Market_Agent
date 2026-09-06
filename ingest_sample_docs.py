"""
Script to ingest sample NSE/BSE/RBI documents into the RAG pipeline
"""

import sys
# Ensure stdout can handle UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from rag import ingest_sample_documents

def main():
    print("Ingesting sample NSE/BSE/RBI documents into RAG pipeline...")
    print("=" * 60)
    ingest_sample_documents()
    print("=" * 60)
    print("✅ Sample documents ingestion completed!")

if __name__ == "__main__":
    main()