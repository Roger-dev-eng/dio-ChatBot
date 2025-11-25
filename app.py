from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from chatbot_core.chatbot import Chatbot
import os

app = Flask(__name__)
CORS(app)

bot = Chatbot()

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

@app.route("/<path:path>")
def serve_static_files(path):
    return send_from_directory("frontend", path)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json
    message = data.get("message", "")
    response = bot.chat(message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
