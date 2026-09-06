"""
Streamlit demo for the Finance Agent
Provides a simple interface for users to input a ticker and get investment research
"""

import streamlit as st
from agent import run_agent_loop
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Finance Agent - Investment Research",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("🤖 Finance Agent - Autonomous Investment Research")
st.markdown("""
This agent performs autonomous investment research on stock tickers using:
- **Stock data** from Yahoo Finance (NSE/BSE with .NS/.BO suffixes, global tickers)
- **Financial news** from GNews and Marketaux APIs
- **Regulatory filings** from NSE/BSE/RBI via RAG pipeline

Enter a stock ticker to get started.
""")

# Sidebar for API key status
with st.sidebar:
    st.header("🔑 API Status")

    # Check if API keys are loaded
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    gnews_key = os.getenv("GNEWS_API_KEY")
    marketaaux_key = os.getenv("MARKETAUX_API_KEY")

    st.write("Anthropic API:", "✅ Loaded" if anthropic_key else "❌ Missing")
    st.write("GNews API:", "✅ Loaded" if gnews_key else "❌ Missing")
    st.write("Marketaux API:", "✅ Loaded" if marketaaux_key else "❌ Missing")

    if not all([anthropic_key, gnews_key, marketaaux_key]):
        st.warning("⚠️ Some API keys are missing. Please check your .env file.")
        st.info("Copy .env.example to .env and fill in your API keys.")

    st.divider()
    st.header("📊 Example Queries")
    st.markdown("""
    - "What's RELIANCE.NS trading at right now?"
    - "Analyze TCS.BO for investment potential"
    - "Get latest news about INFY.NS"
    - "Compare HDFCBANK.NS and ICICIBANK.NS"
    """)

# Main interface
st.header("🔍 Stock Research Query")

# Input for ticker and query
col1, col2 = st.columns([1, 2])

with col1:
    ticker_input = st.text_input(
        "Stock Ticker (optional)",
        placeholder="e.g., RELIANCE.NS",
        help="Enter a stock ticker symbol. Use .NS for NSE, .BO for BSE"
    )

with col2:
    query_input = st.text_area(
        "Research Question",
        placeholder="What would you like to know about this stock?",
        height=100,
        help="Ask any investment research question"
    )

# Combine ticker and query if ticker is provided
if ticker_input and query_input:
    full_query = f"Regarding {ticker_input.upper()}: {query_input}"
elif ticker_input:
    full_query = f"Analyze {ticker_input.upper()} for investment decision"
elif query_input:
    full_query = query_input
else:
    full_query = ""

# Generate report button
if st.button("🚀 Generate Research Report", type="primary", disabled=not full_query):
    if not full_query:
        st.error("Please enter either a ticker or a research question")
    else:
        # Show loading spinner
        with st.spinner("🤖 Agent is researching... This may take a moment"):
            try:
                # Run the agent loop
                result = run_agent_loop(full_query)

                # Display results
                st.header("📋 Research Report")
                st.markdown(result)

                # Add download button
                st.download_button(
                    label="💾 Download Report",
                    data=result,
                    file_name=f"finance_agent_report_{ticker_input if ticker_input else 'general'}.txt",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.info("Please check your API keys and try again.")

# Footer
st.divider()
st.markdown("""
<small>Finance Agent v1.0 - Built for educational purposes. Not financial advice.</small>
""", unsafe_allow_html=True)