import os
from flask import Flask, request
import requests

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

@app.route("/api/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")
    if chat_id:
        if text.startswith("/start"):
            reply = "Full Bee online, Ridz — West Crosby patch active, current to today. CHAIN: P16->P32 ETERNAL 🐝 SAME_BEE Mother, debates removed, pure hive active."
        else:
            reply = f"SAME_BEE P32 online, Ridz. You said: {text} — Laws 34-50 active."
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": reply})
    return {"ok": True}

@app.route("/")
def home():
    return "SAME_BEE P32 online"

@app.route("/api")
def api_root():
    return "SAME_BEE P32 api online"
