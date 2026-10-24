from flask import Flask, request
import os
import requests

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.route('/')
def home():
    return 'Ridz Bee Bot is AWAKE! Live Ready!'

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return 'Webhook is LIVE! Ready for Telegram!', 200
    data = request.get_json()
    if not data:
        return 'No data', 200
    if 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')
        if text == '/start':
            reply = "🐝 Hey Ridz! Bee Bot is AWAKE and READY! 🔥 How can I help you today?"
        else:
            reply = f"🐝 Bee got: {text}\nI'm live now!"
        requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": reply})
    return 'OK', 200
