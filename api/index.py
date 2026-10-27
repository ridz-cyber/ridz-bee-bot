from flask import Flask, request
import os, requests
app = Flask(__name__)

@app.route("/")
@app.route("/api", methods=["GET","POST"])
@app.route("/api/", methods=["GET","POST"])
def bee():
    if request.method == "GET":
        return "Bee TEST LIVE - No Groq!"

    data = request.get_json(silent=True) or {}
    chat_id = (data.get("message",{}).get("chat") or {}).get("id")
    
    if not chat_id:
        return "ok"
    
    token = os.environ.get("TELEGRAM_TOKEN","").strip()
    
    # SIMPLE REPLY - NO GROQ
    text = f"Bee alive! Token ok? {bool(token)} Chat:{chat_id}"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})
    
    return "ok"

handler = app
