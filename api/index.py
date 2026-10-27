from flask import Flask, request
import os, requests
app = Flask(__name__)

@app.route("/")
@app.route("/api", methods=["GET","POST"])
@app.route("/api/", methods=["GET","POST"])
def bee():
    if request.method == "GET":
        return "Bee P38 LIVE - Fixed!"
    data = request.get_json(silent=True) or {}
    msg = data.get("message",{}) or {}
    chat_id = (msg.get("chat") or {}).get("id")
    text = msg.get("text","") or "hi"
    if not chat_id:
        return "ok"
    token = os.environ.get("TELEGRAM_TOKEN")
    gkey = os.environ.get("GROQ_API_KEY")
    reply = "Bee alive!"
    try:
        from groq import Groq
        c = Groq(api_key=gkey).chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"user","content":text}], max_tokens=500)
        reply = c.choices[0].message.content
    except Exception as e:
        reply = f"Bee debug: {e}"[:3000]
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id":chat_id,"text":reply[:3500]}, timeout=10)
    except:
        pass
    return "ok"

handler = app
