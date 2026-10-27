from flask import Flask, request
import os, requests
app = Flask(__name__)

@app.route("/")
@app.route("/api", methods=["GET","POST"])
@app.route("/api/", methods=["GET","POST"])
def bee():
    if request.method == "GET":
        return "Bee P36 FINAL LIVE - Fixed Token Name!"
    
    data = request.get_json(silent=True) or {}
    msg = data.get("message",{}) or {}
    chat_id = (msg.get("chat") or {}).get("id")
    text = (msg.get("text") or "").strip()
    
    if not chat_id:
        return "ok"
    
    # FIX: READ BOTH NAMES - BOT_TOKEN and TELEGRAM_TOKEN
    token = (os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN") or "").strip()
    gkey = (os.environ.get("GROQ_API_KEY") or "").strip()
    
    if not token:
        return "ok"

    # Simple P36 Bee logic with Groq
    reply = f"Bee alive! Token found! You said: {text}"
    try:
        from groq import Groq
        if gkey:
            client = Groq(api_key=gkey)
            r = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role":"system","content":"You are Bee, P36 expert, friendly assistant."},
                    {"role":"user","content": text}
                ],
                max_tokens=600
            )
            reply = r.choices[0].message.content
    except Exception as e:
        reply = f"Bee alive! (Groq error, but token ok) You said: {text}"

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": reply[:3500]}, timeout=15)
    except:
        pass

    return "ok"

handler = app
