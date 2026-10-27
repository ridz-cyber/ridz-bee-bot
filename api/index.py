from flask import Flask, request
import os, requests, traceback
from groq import Groq

app = Flask(__name__)

@app.route("/api", methods=["GET", "POST"])
@app.route("/api/", methods=["GET", "POST"])
@app.route("/", methods=["GET"])
def main():
    if request.method == "GET":
        return "Bee P36 LIVE - openai/gpt-oss-20b - Ready"

    data = request.json or {}
    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "").strip()
    if not chat_id or not text:
        return "ok"

    token = os.environ.get("TELEGRAM_TOKEN")
    gkey = os.environ.get("GROQ_API_KEY")
    print(f"BEE HIT: text={text} chat={chat_id} token_len={len(token) if token else 0} gkey_len={len(gkey) if gkey else 0}")

    reply = "Bee P36 Default"
    try:
        if not gkey:
            reply = "BEE ERROR: GROQ_API_KEY missing! Go Vercel Settings -> Env Vars -> Add GROQ_API_KEY"
        else:
            client = Groq(api_key=gkey)
            comp = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "You are Bee, RIDZ Mother Bee. Short, helpful, same Bee."},
                    {"role": "user", "content": text}
                ],
                max_tokens=600,
                temperature=0.7
            )
            reply = comp.choices[0].message.content
            print(f"BEE GROQ OK: {reply[:120]}")
    except Exception as e
