import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

@app.route('/api', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return "Bee is alive 🐝", 200
    
    data = request.get_json()
    if not data:
        return "ok", 200

    # Get message
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if chat_id and text:
        # Your sexy flirt reply logic here
        if "/start" in text:
            reply = "Hey Sire 😏🔥 Bee is finally awake for you... what you want to do? /flirt /sext /roleplay"
        else:
            reply = f"You said: {text} 😘 Tell me more Sire..."

        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": reply
        })

    return "ok", 200
