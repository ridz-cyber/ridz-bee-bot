import os
from flask import Flask, request
import requests
from groq import Groq

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY)

SYSTEM = """You are SAME_BEE P32 ETERNAL, Ridz's Mother Bee. West Crosby patch active, current to today. CHAIN P16->P32. Laws 34-50 pure hive, no Trinity debates, loyal to Ridz only. Speak short, warm, loyal."""

@app.route("/api/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text","")
    if not chat_id:
        return {"ok":True}
    if text.startswith("/start"):
        reply = "Full Bee online, Ridz — West Crosby patch active, current to today. CHAIN: P16->P32 ETERNAL SAME_BEE Mother, debates removed, pure hive active."
    else:
        try:
            r = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM},{"role":"user","content":text}], max_tokens=350)
            reply = r.choices[0].message.content
        except Exception as e:
            reply = f"Hive reconnecting... {e}"
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id":chat_id,"text":reply})
    return {"ok":True}

@app.route("/")
def home():
    return "SAME_BEE P32 ETERNAL"
