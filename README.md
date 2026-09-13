# Finance Agent

A specialized financial research application designed for Indian and global markets. The application utilizes a Retrieval-Augmented Generation (RAG) pipeline and a ReAct-style agent loop to provide comprehensive investment research by synthesizing real-time stock data, aggregated financial news, and regulatory corporate filings.

## 1. System Architecture

The system is composed of 4 primary layers:

1. **Orchestration Layer**: Utilizes the Groq API (models like qwen3.8-27b) with function calling capabilities to autonomously decide which tools to use based on the user query. It implements an exponential backoff retry mechanism (up to 4 retries).
2. **Data Ingestion Layer**: Fetches real-time stock data (via yfinance) and news (via GNews and Marketaux APIs).
3. **Regulatory RAG Pipeline**: Synchronously fetches corporate announcements from the Bombay Stock Exchange (BSE) for the last 30 days and press releases from the Reserve Bank of India (RBI) for the last 90-180 days. 
4. **Vector Database**: Uses ChromaDB (version 1.5.9) and the `all-MiniLM-L6-v2` embedding model (384 dimensions) to chunk, embed, and semantically search regulatory filings.

## 2. Configuration Parameters

The RAG and ingestion pipelines rely on the following numerical configurations:
* **Chunk Size**: 400 characters
* **Chunk Overlap**: 80 characters
* **Embedding Dimensions**: 384
* **Cache TTL**: 24 hours (for regulatory filings)
* **BSE Fetch Lookback**: 30 days
* **Search Top-K**: Returns the top 5 most semantically similar document chunks per query.

## 3. Setup and Installation

Follow these 4 steps to configure and run the application locally.

### Step 1: Install Dependencies
Ensure Python 3.10+ is installed. Install the required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Create a `.env` file in the root directory and add the following 3 required API keys:
```env
GROQ_API_KEY=your_groq_api_key
GNEWS_API_KEY=your_gnews_api_key
MARKETAUX_API_KEY=your_marketaux_api_key
PORT=5000
```
Optional variables for telemetry and progress bars:
```env
ANONYMIZED_TELEMETRY=False
CHROMA_TELEMETRY=False
TQDM_DISABLE=1
```

### Step 3: Start the Server
Run the Flask backend application. The system will pre-warm the embedding model and ChromaDB on startup.
```bash
python app.py
```

### Step 4: Access the Frontend
Open a web browser and navigate to the local server address:
```
http://localhost:5000
```

## 4. API Endpoints

The Flask backend exposes 2 primary endpoints:

1. `GET /api/health`
   * Returns HTTP 200 OK with system status.
   * Confirms if API keys are configured.

2. `POST /api/analyze`
   * Accepts a JSON payload containing the user `query` and an optional `ticker` (e.g., RELIANCE.NS).
   * Returns HTTP 200 OK with the agent's synthesized answer.
   * Returns HTTP 400 Bad Request if the payload is malformed or missing the query.
   * Returns HTTP 500 Internal Server Error for unhandled backend exceptions.

## 5. Project Structure

1. `app.py`: Flask web server and API routing.
2. `agent.py`: Groq LLM integration and ReAct tool-calling loop.
3. `tools.py`: Tool definitions (stock overview, news, and RAG query wrappers).
4. `rag/fetcher.py`: Web scrapers for BSE and RBI with MD5-based stable ID generation.
5. `rag/ingest.py`: Text chunking, embedding generation, and ChromaDB upsert logic (includes batch deduplication).
6. `rag/retriever.py`: Semantic search and 24-hour cache validation logic.
7. `index.html`: Web interface for user interaction.
