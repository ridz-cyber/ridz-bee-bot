from flask import Flask, request
import os, requests, traceback
from groq import Groq

app = Flask(__name__)

@app.route("/api", methods=["POST"])
@app.route("/api/", methods=["POST"])
def webhook():
    data = request.json or {}
    chat_id = data.get("message",{}).get("chat",{}).get("id")
    text = data.get("message",{}).get("text","")
    print(f"BEE HIT: chat={chat_id} text={text}")
    
    token = os.environ.get("TELEGRAM_TOKEN")
    gkey = os.environ.get("GROQ_API_KEY")
    print(f"BEE ENV: token_len={len(token) if token else 0} gkey_len={len(gkey) if gkey else 0}")

    reply = "BEE DEFAULT"
    try:
        if not gkey:
            reply = "BEE ERROR: GROQ_API_KEY missing in Vercel Env Vars!"
        else:
            client = Groq(api_key=gkey)
            comp = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role":"system","content":"You are Bee RIDZ Mother Bee"},{"role":"user","content":text}],
                max_tokens=500
            )
            reply = comp.choices[0].message.content
            print(f"BEE GROQ OK: {reply[:100]}")
    except Exception as e:
        reply = f"BEE GROQ ERROR: {str(e)[:700]}"
        print(f"BEE GROQ FAIL: {traceback.format_exc()}")

    # SEND
    try:
        if not token:
            print("BEE SEND FAIL: TELEGRAM_TOKEN missing!")
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            r = requests.post(url, json={"chat_id": chat_id, "text": reply[:4000]}, timeout=10)
            print(f"BEE SEND RESP: {r.status_code} {r.text[:1000]}")
    except Exception as e:
        print(f"BEE SEND EXC: {traceback.format_exc()}")

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bee P36 Debug"
