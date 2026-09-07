"""
Flask API backend for the Finance Agent.
Exposes a REST endpoint that the frontend uses to call the real Gemini-powered agent.
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from agent import run_agent_loop

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)  # Allow cross-origin requests during development

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def index():
    """Serve the main HTML frontend."""
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Run the finance agent on a user query.

    Request body (JSON):
        query (str): The user's investment question
        ticker (str, optional): Stock ticker symbol (already formatted, e.g. RELIANCE.NS)

    Returns:
        JSON with 'answer' field containing the agent's response.
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Field 'query' is required and cannot be empty"}), 400

        # Run the agent
        answer = run_agent_loop(query)

        return jsonify({"answer": answer, "query": query})

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    api_key_set = bool(os.getenv("GEMINI_API_KEY"))
    return jsonify({
        "status": "ok",
        "gemini_api_key_configured": api_key_set
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Finance Agent server on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    app.run(host="0.0.0.0", port=port, debug=False)
