"""
Individual tool functions for the Finance Agent
Each tool follows a clean interface with docstrings and schemas for LLM function calling
"""

import yfinance as yf
import json
import requests
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv




def _format_dividend_yield(raw_yield) -> str:
    """
    yfinance returns dividendYield inconsistently:
    - Some tickers: decimal fraction  (e.g. 0.0046  → 0.46%)
    - Some Indian tickers: already %  (e.g. 1.83    → 1.83%)
    Heuristic: if the raw value > 0.5 it is already a percentage.
    A genuine dividend yield above 50% is essentially impossible.
    """
    if not raw_yield:
        return "0.00%"
    val = float(raw_yield)
    if val > 0.5:          # already in percentage form
        pct = round(val, 2)
    else:                  # decimal form – multiply by 100
        pct = round(val * 100, 2)
    return f"{pct}%"


def get_stock_overview(ticker: str) -> Dict[str, Any]:
    """
    Get comprehensive stock overview data for a given ticker symbol.

    Args:
        ticker (str): Stock ticker symbol (e.g., 'RELIANCE.NS' for NSE, 'RELIANCE.BO' for BSE, 'AAPL' for US)

    Returns:
        Dict[str, Any]: Dictionary containing stock information including:
            - symbol: ticker symbol
            - short_name: company name
            - current_price: latest price
            - market_cap: market capitalization
            - pe_ratio: price-to-earnings ratio
            - dividend_yield: dividend yield percentage
            - 52_week_high: 52 week high price
            - 52_week_low: 52 week low price
            - volume: trading volume
            - avg_volume: average trading volume
            - currency: currency of the stock
            - exchange: exchange where stock is traded
            - last_updated: timestamp of data retrieval

    Example:
        >>> get_stock_overview("RELIANCE.NS")
        {
            "symbol": "RELIANCE.NS",
            "short_name": "Reliance Industries Ltd",
            "current_price": 2450.75,
            ...
        }
    """
    try:
        # Create yfinance ticker object
        stock = yf.Ticker(ticker)

        # Get basic info
        info = stock.info

        # Get historical data for current price and volume
        hist = stock.history(period="1d")
        if hist.empty:
            raise ValueError(f"No historical data found for ticker {ticker}")

        latest_data = hist.iloc[-1]

        # Extract key information
        overview = {
            "symbol": ticker.upper(),
            "short_name": info.get("shortName", "N/A"),
            "current_price": round(float(latest_data["Close"]), 2),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "dividend_yield": _format_dividend_yield(info.get("dividendYield")),
            "52_week_high": info.get("fiftyTwoWeekHigh", None),
            "52_week_low": info.get("fiftyTwoWeekLow", None),
            "volume": int(latest_data["Volume"]),
            "avg_volume": info.get("averageVolume", 0),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", "N/A"),
            "last_updated": datetime.now().isoformat()
        }

        # Handle None values for JSON serialization
        for key, value in overview.items():
            if value is None:
                overview[key] = "N/A"

        return overview

    except Exception as e:
        return {
            "error": f"Failed to retrieve stock data for {ticker}: {str(e)}",
            "symbol": ticker.upper(),
            "last_updated": datetime.now().isoformat()
        }

def get_news(ticker: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get recent news articles for a given stock ticker from GNews and Marketaux APIs.

    Args:
        ticker (str): Stock ticker symbol (e.g., 'RELIANCE.NS' for NSE)
        limit (int): Maximum number of news articles to return per source

    Returns:
        Dict[str, Any]: News articles data from both sources combined
    """
    try:
        # Extract clean ticker symbol (remove .NS/.BO suffix for API queries)
        clean_ticker = ticker.replace('.NS', '').replace('.BO', '')

        # Get company name from yfinance for better news search
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            company_name = info.get('shortName', clean_ticker)
        except:
            company_name = clean_ticker

        all_articles = []

        # Fetch from GNews API
        gnews_articles = _fetch_gnews(company_name, limit)
        if gnews_articles:
            all_articles.extend(gnews_articles)

        # Fetch from Marketaux API
        marketaaux_articles = _fetch_marketaaux(clean_ticker, limit)
        if marketaaux_articles:
            all_articles.extend(marketaaux_articles)

        # Remove duplicates based on title similarity
        unique_articles = _remove_duplicate_articles(all_articles)

        # Sort by publication date (newest first) and limit results
        unique_articles.sort(key=lambda x: x.get('publishedAt', ''), reverse=True)
        final_articles = unique_articles[:limit]

        return {
            "ticker": ticker,
            "company_name": company_name,
            "articles_found": len(final_articles),
            "articles": final_articles,
            "sources": ["GNews", "Marketaux"],
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "error": f"Failed to retrieve news for {ticker}: {str(e)}",
            "ticker": ticker,
            "last_updated": datetime.now().isoformat()
        }


def _fetch_gnews(company_name: str, limit: int) -> List[Dict[str, Any]]:
    """Fetch news from GNews API."""
    try:
        api_key = os.getenv("GNEWS_API_KEY")
        if not api_key:
            return []

        url = "https://gnews.io/api/v4/search"
        params = {
            "q": company_name,
            "lang": "en",
            "country": "in",  # Focus on Indian news
            "max": min(limit, 10),  # GNews max is 10 per request
            "apikey": api_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "url": article.get("url", ""),
                "source": article.get("source", {}).get("name", "GNews"),
                "publishedAt": article.get("publishedAt", ""),
                "image": article.get("image", ""),
                "source_api": "GNews"
            })

        return articles

    except Exception as e:
        print(f"GNews API error: {e}")
        return []


def _fetch_marketaaux(ticker: str, limit: int) -> List[Dict[str, Any]]:
    """Fetch news from Marketaux API."""
    try:
        api_key = os.getenv("MARKETAUX_API_KEY")
        if not api_key:
            return []

        url = "https://api.marketaux.com/v1/news/all"
        params = {
            "symbols": ticker,
            "filter_entities": "true",
            "limit": min(limit, 50),  # Marketaux allows up to 50
            "api_token": api_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = []
        for article in data.get("data", []):
            entities = article.get("entities", [])
            # Find the matching ticker entity
            ticker_entity = None
            for entity in entities:
                if entity.get("symbol") == ticker:
                    ticker_entity = entity
                    break

            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("snippet", ""),
                "url": article.get("url", ""),
                "source": article.get("source", ""),
                "publishedAt": article.get("published_at", ""),
                "image": article.get("image_url", ""),
                "source_api": "Marketaux",
                "entities": entities,
                "relevance_score": ticker_entity.get("score", 0) if ticker_entity else 0
            })

        return articles

    except Exception as e:
        print(f"Marketaux API error: {e}")
        return []


def _remove_duplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate articles based on title similarity."""
    if not articles:
        return []

    unique_articles = []
    seen_titles = set()

    for article in articles:
        title = article.get("title", "").lower().strip()
        # Simple deduplication: if title is very similar, skip
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_articles.append(article)

    return unique_articles


def query_filings_rag(query: str, ticker: str = None) -> Dict[str, Any]:
    """
    Query the RAG pipeline for NSE/BSE/RBI regulatory filings and documents.

    Automatically fetches live filings from BSE, NSE and RBI for the given
    ticker (or refreshes the 24-hour cache) before performing a semantic search.

    Args:
        query (str): Natural-language search query
        ticker (str, optional): Stock ticker (e.g. 'RELIANCE.NS') to focus results.
                                RBI macro documents are always included.

    Returns:
        Dict[str, Any]: {
            query:          original query string,
            ticker:         ticker filter used (if any),
            results_count:  number of chunks returned,
            results:        list of { text, source, date, ticker, url, similarity_score },
            note:           informational message
        }
    """
    try:
        from rag.retriever import is_data_fresh, search
        from rag.fetcher import fetch_all_filings
        from rag.ingest import ingest_documents

        note_parts = []

        # SYNCHRONOUS fetch+ingest when cache is stale or missing.
        # Previously this used a background thread (ensure_data) and returned
        # immediately, causing search() to always run on empty/stale data.
        if ticker:
            if not is_data_fresh(ticker):
                print(f"[query_filings_rag] Cache miss for {ticker} — fetching synchronously...")
                try:
                    docs = fetch_all_filings(ticker)
                    if docs:
                        ingest_documents(docs)
                        note_parts.append(f"Fetched {len(docs)} fresh filings for {ticker}.")
                    else:
                        note_parts.append(f"No filings found for {ticker} on BSE/RBI.")
                except Exception as fetch_err:
                    print(f"[query_filings_rag] Fetch failed for {ticker}: {fetch_err}")
                    note_parts.append(f"Live fetch failed ({fetch_err}); searching cached data.")
            else:
                note_parts.append(f"Using cached filings for {ticker} (refreshed within 24h).")

        results = search(query, ticker=ticker)

        if not results:
            return {
                "query":         query,
                "ticker":        ticker,
                "results_count": 0,
                "results":       [],
                "note": (
                    "No relevant documents found. "
                    "Try a broader query or check that the ticker is listed on NSE/BSE."
                ),
            }

        note_parts.append("Results from BSE/NSE corporate filings and RBI documents. Data cached for 24h.")
        return {
            "query":         query,
            "ticker":        ticker,
            "results_count": len(results),
            "results":       results,
            "note":          " ".join(note_parts),
        }

    except Exception as e:
        return {
            "error":  f"RAG pipeline error: {str(e)}",
            "query":  query,
            "ticker": ticker,
        }


if __name__ == "__main__":
    # Test the stock overview function
    print("Testing get_stock_overview with RELIANCE.NS:")
    result = get_stock_overview("RELIANCE.NS")
    print(json.dumps(result, indent=2))