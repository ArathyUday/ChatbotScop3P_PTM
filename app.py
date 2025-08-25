from flask import Flask, request, jsonify
from pipeline import handle_query, reset_conversation

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint with conversational support"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "JSON body required"}), 400
            
        query = data.get("query", "")
        if not query:
            return jsonify({"error": "Query is required"}), 400

        response = handle_query(query)
        return jsonify({
            "response": response,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route("/reset", methods=["POST"])
def reset():
    """Reset conversation state"""
    try:
        reset_conversation()
        return jsonify({
            "message": "Conversation reset successfully",
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Scop3P And Scop3PTM Chatbot"
    })

# Quick test endpoint for debugging
@app.route("/test", methods=["GET"])
def test():
    """Test endpoint"""
    try:
        response = handle_query("What is CSS?")
        return jsonify({
            "test_query": "What is CSS?",
            "response": response,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)