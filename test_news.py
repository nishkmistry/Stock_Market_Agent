"""
Test script for the news tool
"""

import sys
# Ensure stdout can handle UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from tools import get_news
import json

def test_news_tool():
    # Test the news tool with RELIANCE.NS
    test_ticker = "RELIANCE.NS"
    print(f"Testing get_news with {test_ticker}:")
    print("=" * 50)
    result = get_news(test_ticker, limit=5)
    print(json.dumps(result, indent=2))
    print("=" * 50)

if __name__ == "__main__":
    test_news_tool()