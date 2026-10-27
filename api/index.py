import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else ""

@app.route('/', methods=['GET', 'POST'])
@app.route('/api', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return "Bee is alive 🐝 Send /start in Telegram", 200
    
    data = request.get_json(silent=True)
    if not data:
        return "ok", 200

    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "") or ""

    if chat_id and API_URL:
        if "/start" in text.lower():
            reply = "Hey Sire 😏🔥 Bee is awake now... I'm all yours. Try /flirt"
        else:
            reply = f"You said: {text} 😘 tell me more Sire..."

        try:
            requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": reply}, timeout=10)
        except Exception as e:
            print(f"Error: {e}")

    return "ok", 200
