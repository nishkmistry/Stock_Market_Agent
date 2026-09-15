"""
Ingest module: chunks text documents, generates embeddings and upserts into ChromaDB.

Design decisions
----------------
* Embedding model : sentence-transformers/all-MiniLM-L6-v2
    - 80 ms per batch, ~22 MB model, no API key required.
* Vector store     : ChromaDB PersistentClient (on-disk at data/chroma_db/)
* Chunking         : Simple character-based splitter that tries to break at
                     sentence boundaries rather than mid-word.
* IDs              : doc_id + chunk index -> deterministic, idempotent upserts.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH    = os.path.join(_BASE_DIR, "data", "chroma_db")
COLLECTION_NAME = "finance_filings"

CHUNK_SIZE    = 400   # characters
CHUNK_OVERLAP = 80    # characters
EMBED_MODEL   = "all-MiniLM-L6-v2"
BATCH_SIZE    = 32    # embedding batch size
UPSERT_BATCH  = 500   # ChromaDB upsert batch size

# Module-level singletons (lazy-loaded)
_model:      Optional[SentenceTransformer] = None
_client:     Optional[chromadb.PersistentClient] = None  #type: ignore
_collection: Optional[chromadb.Collection] = None #type: ignore


# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"[ingest] Loading embedding model '{EMBED_MODEL}'...")
        _model = SentenceTransformer(EMBED_MODEL)
        print("[ingest] Model loaded.")
    return _model


def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is None:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        _client : Any    = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection : Any = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split *text* into overlapping chunks of at most *chunk_size* characters.
    Prefers to break at a sentence boundary (". " or newline) when possible.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to break at a natural boundary within the latter half of the window
        if end < len(text):
            window = text[start:end]
            boundary = max(
                window.rfind(". "),
                window.rfind(".\n"),
                window.rfind("\n\n"),
                window.rfind("\n"),
            )
            if boundary > chunk_size // 2:
                end = start + boundary + 1  # include the period/newline

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # If we've consumed all the text, stop — don't rewind by overlap
        if end >= len(text):
            break

        start = end - overlap

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ingest_documents(docs: List[Dict[str, Any]]) -> int:
    """
    Chunk, embed and upsert *docs* into ChromaDB.

    Each doc dict must contain:
        text   (str)  – raw text content
        doc_id (str)  – globally unique identifier
        source (str)  – "BSE" | "NSE" | "RBI"
        date   (str)  – publication date
        ticker (str)  – normalised ticker or "RBI"
        url    (str)  – source URL

    Returns:
        Number of chunks actually upserted.
    """
    if not docs:
        return 0

    collection = _get_collection()
    model: Any      = _get_model()

    all_ids:   List[str]            = []
    all_texts: List[str]            = []
    all_metas: List[Dict[str, Any]] = []

    now_iso = datetime.now().isoformat()

    for doc in docs:
        text = (doc.get("text") or "").strip()
        if not text:
            continue

        chunks = _chunk_text(text)
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{doc['doc_id']}_c{idx}"
            meta: Dict[str, Any] = {
                "source":      str(doc.get("source", "")),
                "date":        str(doc.get("date", "")),
                "ticker":      str(doc.get("ticker", "")),
                "url":         str(doc.get("url", "")),
                "ingested_at": now_iso,
            }
            all_ids.append(chunk_id)
            all_texts.append(chunk)
            all_metas.append(meta)

    if not all_ids:
        print("[ingest] No non-empty chunks to store.")
        return 0

    print(f"[ingest] Embedding {len(all_texts)} chunks...")
    embeddings = model.encode(
        all_texts, batch_size=BATCH_SIZE, show_progress_bar=False
    ).tolist()

    # Deduplicate before upserting (ChromaDB 1.5.9 rejects dupes in a single batch)
    unique_ids:list[Any] = []
    unique_texts:list[Any] = []
    unique_metas:list[Any] = []
    unique_embeddings:list[Any] = []
    seen_ids:set[Any] = set()

    for idx, doc_id in enumerate(all_ids):
        if doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_ids.append(doc_id)
            unique_texts.append(all_texts[idx])
            unique_metas.append(all_metas[idx])
            unique_embeddings.append(embeddings[idx])

    total = 0
    for i in range(0, len(unique_ids), UPSERT_BATCH):
        s = i
        e = min(i + UPSERT_BATCH, len(unique_ids))
        batch_ids = unique_ids[s:e]
        collection.upsert(
            ids=batch_ids,
            documents=unique_texts[s:e],
            embeddings=unique_embeddings[s:e],
            metadatas=unique_metas[s:e],
        )
        total += len(batch_ids)

    print(f"[ingest] [OK] Upserted {total} unique chunks into ChromaDB.")
    return total


def collection_count() -> int:
    """Return total number of chunks currently stored in ChromaDB."""
    return _get_collection().count()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = [
        {
            "text":   "SEBI has issued new guidelines on insider trading for listed companies on NSE and BSE.",
            "source": "BSE",
            "date":   "2024-01-15",
            "ticker": "RELIANCE",
            "url":    "https://www.bseindia.com/",
            "doc_id": "test_001",
        }
    ]
    n = ingest_documents(sample)
    print(f"Ingested {n} chunks. Total in DB: {collection_count()}")
