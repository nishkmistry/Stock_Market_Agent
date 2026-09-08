"""
RAG (Retrieval-Augmented Generation) pipeline for the Finance Agent.

Modules:
    fetcher   - Auto-fetch filings from BSE, NSE and RBI
    ingest    - Chunk, embed and store documents in ChromaDB
    retriever - Semantic search over stored filings
"""
