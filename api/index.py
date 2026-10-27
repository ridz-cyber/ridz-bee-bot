from flask import Flask, request
import os, requests, traceback
app = Flask(__name__)

@app.route("/")
@app.route("/api", methods=["GET","POST"])
@app.route("/api/", methods=["GET","POST"])
def bee():
    if request.method == "GET":
        return "Bee P38 LIVE - Ready!"
    
    print("--- NEW MESSAGE FROM TELEGRAM ---")
    data = request.get_json(silent=True) or {}
    print(f"Data: {data}")
    
    msg = data.get("message",{}) or {}
    chat_id = (msg.get("chat") or {}).get("id")
    text = msg.get("text","") or "hi"
    
    print(f"ChatID: {chat_id}, Text: {text}")
    
    if not chat_id:
        print("NO CHAT ID!")
        return "ok"

    token = os.environ.get("TELEGRAM_TOKEN")
    gkey = os.environ.get("GROQ_API_KEY")
    
    print(f"Token exists: {bool(token)}, Groq exists: {bool(gkey)}")
    
    if not token:
        print("ERROR: TELEGRAM_TOKEN IS EMPTY IN VERCEL!")
        return "no token"

    reply = "Bee is alive! How can I help?"
    try:
        from groq import Groq
        client = Groq(api_key=gkey)
        r = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role":"user","content": text}],
            max_tokens=500
        )
        reply = r.choices[0].message.content
        print(f"Groq reply: {reply[:100]}")
    except Exception as e:
        print(f"Groq Error: {e}")
        traceback.print_exc()
        reply = f"Bee debug error: {e}"[:3000]

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        print(f"Sending to: {url[:50]}...")
        resp = requests.post(url, json={"chat_id": chat_id, "text": reply[:3500]}, timeout=10)
        print(f"Telegram Response: {resp.status_code} - {resp.text[:500]}")
    except Exception as e:
        print(f"Send Error: {e}")
        traceback.print_exc()

    return "ok"

handler = app
