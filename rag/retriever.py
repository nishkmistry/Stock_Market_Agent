"""
Retriever module: orchestrates freshness checks, auto-fetch and semantic search.

Flow
----
1. query_filings_rag(query, ticker) in tools.py calls ensure_data(ticker).
2. ensure_data() checks ChromaDB: is there data for this ticker ingested
   within the last CACHE_TTL_HOURS?  If not -> fetch + ingest.
3. search(query, ticker) embeds the query and returns the top-k most
   semantically similar chunks, always mixing in RBI macro documents.
"""

from __future__ import annotations

#import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Shared singletons from ingest (avoids loading the model twice)
from rag.ingest import _get_collection, _get_model, collection_count #type: ignore
from rag.fetcher import fetch_all_filings
from rag.ingest import ingest_documents

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CACHE_TTL_HOURS = 24   # re-fetch after 24 h
DEFAULT_TOP_K   = 3    # kept low to stay within Groq token-per-minute limits


# ---------------------------------------------------------------------------
# Freshness check
# ---------------------------------------------------------------------------

def _normalize(ticker: str) -> str:
    return ticker.replace(".NS", "").replace(".BO", "").upper()


def is_data_fresh(ticker: str, ttl_hours: int = CACHE_TTL_HOURS) -> bool:
    """
    Return True if ChromaDB contains at least one chunk for *ticker*
    that was ingested within *ttl_hours*.
    """
    try:
        collection = _get_collection()
        if collection.count() == 0:
            return False

        clean = _normalize(ticker)
        results = collection.get(
            where={"ticker": clean},
            limit=1,
            include=["metadatas"],
        )
        metas:list[Any] = results.get("metadatas") or []
        if not metas:
            return False

        ingested_at_str : str= metas[0].get("ingested_at", "")
        if not ingested_at_str:
            return False

        ingested_at = datetime.fromisoformat(ingested_at_str)
        return datetime.now() - ingested_at < timedelta(hours=ttl_hours)

    except Exception as e:
        print(f"[retriever] freshness check failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Auto-fetch + ingest
# ---------------------------------------------------------------------------

import threading

_fetch_lock = threading.Lock()
_fetching: set[Any] = set()   # tickers currently being fetched in background


def _fetch_and_ingest(ticker: str) -> None:
    """Background worker: fetch + ingest for *ticker*, then clear the in-progress flag."""
    try:
        docs = fetch_all_filings(ticker)
        if docs:
            ingest_documents(docs)
    except Exception as e:
        print(f"[retriever] Background fetch failed for {ticker}: {e}")
    finally:
        with _fetch_lock:
            _fetching.discard(ticker)


def ensure_data(ticker: str) -> None:
    """
    Guarantee fresh data for *ticker* exists in ChromaDB.

    * Cache hit  → returns immediately (< 1 ms).
    * Cache miss → starts a background fetch thread and returns immediately.
                   The next call (after ~5-10 s) will find the data ready.
    """
    if is_data_fresh(ticker):
        clean = _normalize(ticker)
        print(f"[retriever] Cache hit for {clean}")
        return

    clean = _normalize(ticker)
    with _fetch_lock:
        if clean in _fetching:
            print(f"[retriever] Fetch already in progress for {clean}")
            return
        _fetching.add(clean)

    print(f"[retriever] Cache miss — fetching {ticker} in background...")
    t = threading.Thread(target=_fetch_and_ingest, args=(ticker,), daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------

def search(
    query: str,
    ticker: Optional[str] = None,
    top_k: int = DEFAULT_TOP_K,
) -> List[Dict[str, Any]]:
    """
    Embed *query* and return the top-k most similar chunks from ChromaDB.

    Args:
        query:  Natural-language search string.
        ticker: Optional ticker to focus results.  RBI documents are always
                included regardless of this filter.
        top_k:  Maximum number of results to return.

    Returns:
        List of dicts with keys: text, source, date, ticker, url, similarity_score.
    """
    collection = _get_collection()
    total      = collection.count()
    if total == 0:
        return []

    model:Any           = _get_model()
    query_embedding = model.encode([query]).tolist()[0]

    # Build where clause: ticker-specific docs + RBI macro docs
    where: Optional[Dict[Any, Any]] = None
    if ticker:
        clean = _normalize(ticker)
        where = {"ticker": {"$in": [clean, "RBI"]}}

    n = min(top_k, total)

    try:
        results : Any = collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as first_err:
        # Fallback: try without filter (ChromaDB raises if filter matches 0 docs)
        print(f"[retriever] Filtered query error ({first_err}), retrying without filter...")
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            print(f"[retriever] Search failed: {e}")
            return []

    formatted: List[Dict[str, Any]] = []
    docs      = results.get("documents", [[]])[0]
    metas : list[Any]    = results.get("metadatas",  [[]])[0]
    distances = results.get("distances",  [[]])[0]

    for i, doc_text in enumerate(docs):
        meta:Any  = metas[i]     if i < len(metas)     else {}
        dist  = distances[i] if i < len(distances)  else 1.0
        score = round(max(0.0, 1.0 - dist), 4)    # cosine dist -> similarity

        formatted.append({
            "text":             doc_text,
            "source":           meta.get("source", ""),
            "date":             meta.get("date",   ""),
            "ticker":           meta.get("ticker", ""),
            "url":              meta.get("url",    ""),
            "similarity_score": score,
        })

    return formatted


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    ticker = "RELIANCE.NS"
    ensure_data(ticker)
    results = search("quarterly revenue profits", ticker=ticker, top_k=3)
    print(json.dumps(results, indent=2, default=str))
