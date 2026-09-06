"""
Final test of the agent architecture - focusing on the ReAct loop pattern
using the working tools we've built, with simulated LLM reasoning for educational purposes.
"""

import os
import json
import time
import sys
from typing import Dict, Any
from tools import get_stock_overview, get_news, query_filings_rag
from dotenv import load_dotenv

load_dotenv()

def safe_print(*args, **kwargs):
    """Safely print text handling Unicode encoding issues on Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        # Convert args to string and encode
        arg_strings = [str(arg) for arg in args]
        line = ' '.join(arg_strings)
        sys.stdout.buffer.write(line.encode('utf-8') + b'\n')

# Simulate what an LLM would do in a ReAct loop
class SimulatedFinanceAgent:
    def __init__(self):
        self.tools = {
            "get_stock_overview": get_stock_overview,
            "get_news": get_news,
            "query_filings_rag": query_filings_rag
        }

        # Tool descriptions for the LLM to understand what each does
        self.tool_descriptions = {
            "get_stock_overview": "Get comprehensive stock overview data for a given ticker symbol including price, market cap, P/E ratio, etc.",
            "get_news": "Get recent news articles for a given stock ticker from financial news sources",
            "query_filings_rag": "Query the RAG pipeline for NSE/BSE/RBI regulatory filings and documents"
        }

    def run_agent_loop(self, user_query: str, max_iterations: int = 5) -> str:
        """
        Simulate a ReAct (Reasoning and Acting) agent loop.

        In a real implementation, an LLM would:
        1. Reason about what information is needed
        2. Act by selecting and executing appropriate tools
        3. Observe the results
        4. Repeat until sufficient information is gathered
        5. Provide a final answer

        For educational purposes, we'll simulate this reasoning process.
        """
        safe_print("Finance Agent Starting...")
        safe_print(f"Query: {user_query}\n")

        # Initialize state
        iteration = 0
        observations = []
        thoughts = []

        # Simulate the ReAct loop
        while iteration < max_iterations:
            iteration += 1
            safe_print(f"Iteration {iteration}")

            # THOUGHT: Reason about what we know and what we need
            thought = self._reason_about_query(user_query, observations, thoughts)
            thoughts.append(thought)
            safe_print(f"Thought: {thought}")

            # If we have enough information, provide final answer
            if self._has_sufficient_information(thought, observations):
                safe_print("Sufficient information gathered")
                break

            # ACTION: Decide which tool to use based on our thought
            action = self._decide_action(thought, observations)
            if action is None:
                safe_print("No clear action needed")
                break

            safe_print(f"Action: {action['tool']} with input {action['input']}")

            # Execute the tool
            try:
                observation = self._execute_tool(action['tool'], action['input'])
                observations.append(observation)
                safe_print(f"Observation: {self._summarize_observation(observation)}")
            except Exception as e:
                error_obs = f"Tool execution failed: {str(e)}"
                observations.append(error_obs)
                safe_print(f"Observation: {error_obs}")

            safe_print()  # Empty line for readability

            # If we've done reasonable amount of work, break
            if iteration >= 3:  # Prevent infinite loops in simulation
                break

        # Provide final answer based on all observations
        final_answer = self._synthesize_final_answer(user_query, thoughts, observations)
        return final_answer

    def _reason_about_query(self, query: str, observations: list, thoughts: list) -> str:
        """Simulate LLM reasoning about what to do next."""
        query_lower = query.lower()

        # If this is the first iteration, understand the query
        if len(thoughts) == 0:
            if any(word in query_lower for word in ['price', 'trading', 'stock', 'share']):
                return "User wants stock price/trading information. I need to get current stock data."
            elif any(word in query_lower for word in ['news', 'latest', 'recent', 'headline']):
                return "User wants recent news. I need to fetch news articles."
            elif any(word in query_lower for word in ['filing', 'regulatory', 'sebi', 'rbi', 'document']):
                return "User wants regulatory/filing information. I need to search the document database."
            else:
                return "User asking general question. I should gather comprehensive information including stock data, news, and filings."

        # If we have observations, reason about what they tell us
        latest_obs = observations[-1] if observations else ""

        # Check if we got stock data but might need news
        if "'symbol':" in str(latest_obs) and "news" not in " ".join(thoughts).lower():
            if any(word in query_lower for word in ['news', 'latest', 'recent']) or len(observations) == 1:
                return "Got stock data. User might also want recent news for context."

        # Check if we got news but might need more details
        if "'articles_found':" in str(latest_obs) and int(str(latest_obs).split("'articles_found':")[1].split(",")[0]) > 0:
            if "price" in query_lower or "trading" in query_lower:
                return "Got news articles. User also asked about price/trading, so I should get stock data."

        # Default: we have enough to answer
        return "I have gathered sufficient information to answer the user's question."

    def _has_sufficient_information(self, thought: str, observations: list) -> bool:
        """Determine if we have enough information to answer."""
        thought_lower = thought.lower()
        return any(word in thought_lower for word in ['sufficient', 'enough', 'answer']) or len(observations) >= 2

    def _decide_action(self, thought: str, observations: list) -> Dict[str, Any]:
        """Decide which tool to use based on the thought and what we've observed."""
        thought_lower = thought.lower()

        # Check what we've already observed
        has_stock_data = any(isinstance(obs, dict) and "symbol" in obs for obs in observations)
        has_news = any(isinstance(obs, dict) and "articles_found" in obs for obs in observations)
        has_filings = any(isinstance(obs, dict) and "results" in obs for obs in observations)

        # If we don't have stock data yet and the thought suggests we need it, get stock data
        if not has_stock_data and any(phrase in thought_lower for phrase in [
            "need to get stock", "need stock data", "get stock data",
            "fetch stock", "obtain stock", "retrieve stock", "stock information",
            "need price", "get price", "fetch price", "need trading",
            "user wants stock", "user wants price", "i need to get"
        ]):
            return {"tool": "get_stock_overview", "input": {"ticker": "RELIANCE.NS"}}

        # If we don't have news yet and the thought suggests we need it, get news
        if not has_news and any(phrase in thought_lower for phrase in [
            "need to get news", "need news data", "get news data",
            "fetch news", "obtain news", "retrieve news", "news information",
            "user might also want", "user might need", "also want news"
        ]):
            return {"tool": "get_news", "input": {"ticker": "RELIANCE.NS", "limit": 3}}

        # If we don't have filings yet and the thought suggests we need them, get filings
        if not has_filings and any(phrase in thought_lower for phrase in [
            "need to get filing", "need filing data", "get filing data",
            "fetch filing", "obtain filing", "retrieve filing", "filing information",
            "regulatory information", "document information"
        ]):
            return {"tool": "query_filings_rag", "input": {"query": "recent developments", "ticker": "RELIANCE.NS"}}

        # Default actions based on what we're missing (fallback)
        if not has_stock_data:
            return {"tool": "get_stock_overview", "input": {"ticker": "RELIANCE.NS"}}
        elif not has_news:
            return {"tool": "get_news", "input": {"ticker": "RELIANCE.NS", "limit": 3}}
        elif not has_filings:
            return {"tool": "query_filings_rag", "input": {"query": "recent developments", "ticker": "RELIANCE.NS"}}
        else:
            # We have everything we likely need
            return None

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = self.tools[tool_name](**tool_input)
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    def _summarize_observation(self, observation: Dict[str, Any]) -> str:
        """Create a brief summary of an observation for display."""
        if "error" in observation:
            return f"Error: {observation['error']}"

        if "symbol" in observation:
            return f"Stock data for {observation.get('symbol', 'N/A')}: Price ₹{observation.get('current_price', 'N/A')}"
        elif "articles_found" in observation:
            return f"News: {observation.get('articles_found', 0)} articles found"
        elif "results" in observation:
            return f"Filings: {len(observation.get('results', []))} relevant documents found"
        else:
            return f"Observation: {str(observation)[:100]}..."

    def _synthesize_final_answer(self, query: str, thoughts: list, observations: list) -> str:
        """Synthesize a final answer from all thoughts and observations."""
        safe_print("Synthesizing final answer...")

        # Extract key information from observations
        stock_info = None
        news_info = None
        filing_info = None

        for obs in observations:
            if isinstance(obs, dict):
                if "symbol" in obs:
                    stock_info = obs
                elif "articles_found" in obs:
                    news_info = obs
                elif "results" in obs:
                    filing_info = obs

        # Build comprehensive answer
        answer_parts = []

        answer_parts.append("=" * 60)
        answer_parts.append("FINANCE AGENT ANALYSIS")
        answer_parts.append("=" * 60)
        answer_parts.append(f"Query: {query}")
        answer_parts.append("")

        if stock_info:
            answer_parts.append("STOCK INFORMATION:")
            answer_parts.append(f"  Symbol: {stock_info.get('symbol', 'N/A')}")
            answer_parts.append(f"  Company: {stock_info.get('short_name', 'N/A')}")
            answer_parts.append(f"  Current Price: ₹{stock_info.get('current_price', 'N/A'):,.2f}")
            answer_parts.append(f"  Market Cap: ₹{stock_info.get('market_cap', 0):,}")
            answer_parts.append(f"  P/E Ratio: {stock_info.get('pe_ratio', 'N/A'):.2f}")
            answer_parts.append(f"  Dividend Yield: {stock_info.get('dividend_yield', 'N/A'):.2f}%")
            answer_parts.append(f"  52-Week Range: ₹{stock_info.get('52_week_low', 'N/A'):,.2f} - ₹{stock_info.get('52_week_high', 'N/A'):,.2f}")
            answer_parts.append(f"  Volume: {stock_info.get('volume', 'N/A'):,}")
            answer_parts.append("")

        if news_info and news_info.get('articles_found', 0) > 0:
            answer_parts.append("RECENT NEWS:")
            answer_parts.append(f"  Found {news_info['articles_found']} recent articles")
            for i, article in enumerate(news_info.get('articles', [])[:2], 1):  # Show first 2
                answer_parts.append(f"  {i}. {article.get('title', 'No title')}")
                answer_parts.append(f"     Source: {article.get('source', 'Unknown')} | {article.get('publishedAt', 'Unknown')[:10]}")
            answer_parts.append("")

        if filing_info and len(filing_info.get('results', [])) > 0:
            answer_parts.append("REGULATORY FILINGS:")
            answer_parts.append(f"  Found {len(filing_info['results'])} relevant documents")
            for i, filing in enumerate(filing_info['results'][:2], 1):  # Show first 2
                answer_parts.append(f"  {i}. {filing.get('content', 'No content')[:100]}...")
                if filing.get('metadata'):
                    answer_parts.append(f"     Source: {filing['metadata'].get('source_file', 'Unknown')}")
            answer_parts.append("")

        # Add synthesis
        answer_parts.append("SYNTHESIS:")
        if stock_info:
            answer_parts.append(f"  {stock_info.get('short_name', 'The company')} is currently trading at ₹{stock_info.get('current_price', 'N/A'):,.2f}")
            answer_parts.append(f"  with a market capitalization of ₹{stock_info.get('market_cap', 0):,}.")

            pe_ratio = stock_info.get('pe_ratio')
            if pe_ratio and pe_ratio > 25:
                answer_parts.append(f"  The P/E ratio of {pe_ratio:.1f} suggests the stock may be relatively expensive.")
            elif pe_ratio and pe_ratio < 15:
                answer_parts.append(f"  The P/E ratio of {pe_ratio:.1f} suggests the stock may be relatively inexpensive.")
            else:
                answer_parts.append(f"  The P/E ratio of {pe_ratio:.1f} is in a moderate range.")

        if news_info and news_info.get('articles_found', 0) > 0:
            answer_parts.append(f"  Recent news shows {news_info['articles_found']} articles covering various developments.")

        if filing_info and len(filing_info.get('results', [])) > 0:
            answer_parts.append(f"  Regulatory filings show {len(filing_info['results'])} compliance documents have been recently submitted.")

        answer_parts.append("")
        answer_parts.append("SOURCES:")
        answer_parts.append("  • Stock data: Yahoo Finance (yfinance)")
        answer_parts.append("  • News: GNews and Marketaux APIs")
        answer_parts.append("  • Filings: Local RAG pipeline with ChromaDB")
        answer_parts.append("")
        answer_parts.append("DISCLAIMER: This is for educational purposes only. Not financial advice.")
        answer_parts.append("=" * 60)

        return "\n".join(answer_parts)

def main():
    agent = SimulatedFinanceAgent()

    # Test queries
    test_queries = [
        "What's RELIANCE.NS trading at right now?",
        "Show me recent news for TCS.NS",
        "What are the latest regulatory filings for INFY.NS?",
        "Give me a comprehensive analysis of HDFCBANK.NS"
    ]

    for i, query in enumerate(test_queries, 1):
        safe_print(f"\nTEST {i} TEST")
        result = agent.run_agent_loop(query)
        # Handle potential Unicode encoding issues on Windows
        try:
            print(result)
        except UnicodeEncodeError:
            # Fallback for Windows console encoding issues
            sys.stdout.buffer.write(result.encode('utf-8') + b'\n')

        if i < len(test_queries):
            safe_print("\nPress Enter to continue to next test...")
            input()

if __name__ == "__main__":
    main()