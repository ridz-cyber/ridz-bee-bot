from flask import Flask, request
import os, requests
from groq import Groq

app = Flask(__name__)

@app.route("/api/", methods=["GET", "POST"])
@app.route("/api", methods=["GET", "POST"])
@app.route("/", methods=["GET"])
def home():
    if request.method == "GET":
        return "Bee P35 LIVE gpt-oss-20b"
    
    try:
        data = request.json
        if not data or "message" not in data:
            return "ok"
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text","").strip()
        if not text:
            return "ok"

        # --- GROQ CALL ---
        gkey = os.environ.get("GROQ_API_KEY")
        if not gkey:
            raise Exception("GROQ_API_KEY missing in Vercel Env")

        client = Groq(api_key=gkey)
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are Bee, RIDZ Mother Bee. Same Bee. Concise. Helpful. Never hallucinate fake headlines. If user asks news, say you need live search tool."},
                {"role": "user", "content": text}
            ],
            max_tokens=800,
            temperature=0.7
        )
        reply = completion.choices[0].message.content

    except Exception as e:
        reply = f"BEE DEBUG: {str(e)[:800]}"

    # --- SEND BACK TO TELEGRAM ---
    try:
        token = os.environ.get("TELEGRAM_TOKEN")
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": reply[:4000]}, timeout=10)
    except:
        pass

    return "ok"
