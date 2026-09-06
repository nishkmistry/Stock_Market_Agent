"""
Simple test of the RAG pipeline
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag import FinancialRAG

def test_rag():
    print("Initializing RAG pipeline...")
    rag = FinancialRAG()

    print("Adding test document...")
    test_content = "Reliance Industries Limited (RELIANCE.NS) reported Q3 FY2024 results with revenue of ₹2.1 lakh crore, up 12% YoY."
    test_metadata = {
        "ticker": "RELIANCE.NS",
        "document_type": "quarterly_results",
        "date": "2024-01-20"
    }

    doc_id = rag.add_document(test_content, test_metadata)
    print(f"Added document with ID: {doc_id}")

    print("Testing query...")
    results = rag.query_filings_rag("What were Reliance Industries' Q3 results?", ticker="RELIANCE.NS")
    print(f"Query results: {results}")

    print("Test completed successfully!")

if __name__ == "__main__":
    test_rag()