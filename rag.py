"""
RAG (Retrieval-Augmented Generation) pipeline for financial documents.
Handles document ingestion, chunking, embedding, storage, and retrieval.
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FinancialRAG:
    def __init__(self,
                 collection_name: str = "financial_documents",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 persist_directory: str = "./chroma_db"):
        """
        Initialize the RAG pipeline.

        Args:
            collection_name: Name of the ChromaDB collection
            embedding_model: Sentence transformer model to use for embeddings
            persist_directory: Directory to persist ChromaDB data
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Financial documents for NSE/BSE/RBI"}
            )

    def _get_document_hash(self, content: str) -> str:
        """Generate a hash for document content to avoid duplicates."""
        return hashlib.md5(content.encode()).hexdigest()

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text to chunk
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings near the end
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > start + chunk_size // 2:  # Only break if we're past halfway
                    chunk = text[start:break_point + 1]
                    end = break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap  # Overlap with previous chunk

            if start >= len(text):
                break

        return chunks

    def add_document(self,
                    content: str,
                    metadata: Optional[Dict[str, Any]] = None,
                    document_id: Optional[str] = None) -> str:
        """
        Add a document to the RAG pipeline.

        Args:
            content: Document text content
            metadata: Optional metadata dictionary
            document_id: Optional custom document ID

        Returns:
            Document ID
        """
        if document_id is None:
            document_id = self._get_document_hash(content)

        # Check if document already exists
        try:
            existing = self.collection.get(ids=[document_id])
            if existing['ids']:
                return document_id  # Document already exists
        except:
            pass  # Document doesn't exist, continue

        # Prepare metadata
        if metadata is None:
            metadata = {}

        metadata['document_id'] = document_id
        metadata['content_length'] = len(content)

        # Chunk the document
        chunks = self._chunk_text(content)

        # Generate embeddings for chunks
        embeddings = self.embedding_model.encode(chunks).tolist()

        # Prepare chunk IDs and metadata
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        chunk_metadatas = [
            {**metadata, "chunk_index": i, "chunk_count": len(chunks)}
            for i in range(len(chunks))
        ]

        # Add to collection
        self.collection.add(
            ids=chunk_ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=chunk_metadatas
        )

        return document_id

    def add_documents_from_directory(self,
                                   directory_path: str,
                                   file_extensions: List[str] = None,
                                   metadata_template: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Add all documents from a directory to the RAG pipeline.

        Args:
            directory_path: Path to directory containing documents
            file_extensions: List of file extensions to process (e.g., ['.txt', '.pdf'])
            metadata_template: Template metadata to apply to all documents

        Returns:
            List of document IDs that were added
        """
        if file_extensions is None:
            file_extensions = ['.txt', '.md', '.pdf']

        if metadata_template is None:
            metadata_template = {}

        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory {directory_path} does not exist")

        document_ids = []

        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                try:
                    # Read file content
                    if file_path.suffix.lower() == '.pdf':
                        # For PDF files, we'd need a PDF reader - skipping for now
                        continue
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                    # Prepare metadata
                    metadata = {
                        **metadata_template,
                        "source_file": str(file_path),
                        "file_name": file_path.name,
                        "file_size": file_path.stat().st_size
                    }

                    # Add document
                    doc_id = self.add_document(content, metadata)
                    document_ids.append(doc_id)

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue

        return document_ids

    def query(self,
              query_text: str,
              n_results: int = 5,
              filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query the RAG pipeline for relevant documents.

        Args:
            query_text: Query text to search for
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of relevant documents with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query_text]).tolist()[0]

        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )

        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })

        return formatted_results

    def query_filings_rag(self, query: str, ticker: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the RAG pipeline for NSE/BSE/RBI regulatory filings and documents.
        This is the function that will be called by the agent.

        Args:
            query: Search query for relevant documents
            ticker: Optional: Filter results by specific ticker symbol

        Returns:
            Dictionary containing search results and summary
        """
        try:
            # Prepare filter metadata if ticker is provided
            filter_metadata = None
            if ticker:
                filter_metadata = {"ticker": ticker}

            # Query the RAG pipeline
            results = self.query(query, n_results=10, filter_metadata=filter_metadata)

            if not results:
                return {
                    "query": query,
                    "ticker": ticker,
                    "results": [],
                    "summary": "No relevant documents found in the financial filings database.",
                    "source": "RAG Pipeline"
                }

            # Format results for agent consumption
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result['content'][:500] + "..." if len(result['content']) > 500 else result['content'],
                    "source": result['metadata'].get('source_file', 'Unknown'),
                    "relevance_score": 1 - (result['distance'] or 0),  # Convert distance to similarity
                    "metadata": result['metadata']
                })

            # Generate a summary of the findings
            summary = self._generate_query_summary(query, formatted_results)

            return {
                "query": query,
                "ticker": ticker,
                "results": formatted_results,
                "summary": summary,
                "source": "RAG Pipeline",
                "total_results": len(formatted_results)
            }

        except Exception as e:
            return {
                "error": f"RAG query failed: {str(e)}",
                "query": query,
                "ticker": ticker
            }

    def _generate_query_summary(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate a human-readable summary of query results."""
        if not results:
            return "No relevant information found."

        # Count results by source
        sources = {}
        for result in results:
            source = result['source']
            sources[source] = sources.get(source, 0) + 1

        # Create summary
        summary_parts = [f"Found {len(results)} relevant document chunks"]

        if sources:
            source_list = [f"{count} from {source}" for source, count in sources.items()]
            summary_parts.append(f"({', '.join(source_list)})")

        # Add relevance information
        high_relevance = [r for r in results if r['relevance_score'] > 0.7]
        if high_relevance:
            summary_parts.append(f"{len(high_relevance)} highly relevant results")

        summary = ". ".join(summary_parts) + "."

        # Add key findings preview
        if results:
            preview = results[0]['content'][:200]
            summary += f" Key preview: {preview}..."

        return summary

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection."""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {"error": f"Failed to get stats: {str(e)}"}

# Global RAG instance for use by the agent
financial_rag = FinancialRAG()

def query_filings_rag(query: str, ticker: Optional[str] = None) -> Dict[str, Any]:
    """
    Query the RAG pipeline for NSE/BSE/RBI regulatory filings and documents.
    This function is designed to be called by the agent loop.

    Args:
        query: Search query for relevant documents
        ticker: Optional: Filter results by specific ticker symbol

    Returns:
        Dictionary containing search results
    """
    return financial_rag.query_filings_rag(query, ticker)

# For testing the RAG pipeline directly
if __name__ == "__main__":
    # Test the RAG pipeline
    print("Testing Financial RAG Pipeline")
    print("=" * 40)

    # Add some test documents
    test_docs = [
        {
            "content": "Reliance Industries Limited (RELIANCE.NS) reported Q3 FY2024 results with revenue of ₹2.1 lakh crore, up 12% YoY. The company's refining margins improved to $12.5 per barrel.",
            "metadata": {
                "ticker": "RELIANCE.NS",
                "document_type": "quarterly_results",
                "date": "2024-01-20",
                "source": "company_filing"
            }
        },
        {
            "content": "Securities and Exchange Board of India (SEBI) issued new guidelines for mutual fund disclosures requiring standardized risk metrics and performance reporting formats effective April 2024.",
            "metadata": {
                "ticker": "SEBI",
                "document_type": "regulatory_guideline",
                "date": "2024-03-15",
                "source": "regulatory_filing"
            }
        },
        {
            "content": "Reserve Bank of India (RBI) maintained repo rate at 6.5% in its February 2024 monetary policy meeting, citing inflation concerns and growth prospects.",
            "metadata": {
                "ticker": "RBI",
                "document_type": "monetary_policy",
                "date": "2024-02-08",
                "source": "central_bank"
            }
        }
    ]

    # Add documents to RAG
    for doc in test_docs:
        doc_id = financial_rag.add_document(doc["content"], doc["metadata"])
        print(f"Added document: {doc_id}")

    # Test queries
    test_queries = [
        "What were Reliance Industries' Q3 results?",
        "SEBI mutual fund disclosure guidelines",
        "RBI repo rate decision February 2024"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = financial_rag.query_filings_rag(query)
        print(f"Summary: {results.get('summary', 'No summary')}")
        print(f"Results found: {len(results.get('results', []))}")

    # Show collection stats
    stats = financial_rag.get_collection_stats()
    print(f"\nCollection Stats: {stats}")