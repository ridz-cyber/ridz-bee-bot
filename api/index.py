from flask import Flask, request, jsonify
import os, requests

app = Flask(__name__)

BOT = os.environ.get("TELEGRAM_BOT_TOKEN", "")

@app.route('/', methods=['GET','POST'])
@app.route('/api', methods=['GET','POST'])
@app.route('/api/index', methods=['GET','POST'])
def main():
    if request.method == 'GET':
        return jsonify({"status": "Bee Alive"}), 200
    
    try:
        data = request.get_json(silent=True) or {}
        cid = data.get('message', {}).get('chat', {}).get('id')
        txt = data.get('message', {}).get('text', 'hi')
        
        if cid:
            requests.post(
                f"https://api.telegram.org/bot{BOT}/sendMessage",
                json={"chat_id": cid, "text": f"Bee Alive Sire! You said: {txt}"},
                timeout=5
            )
    except:
        pass
    
    return jsonify({"ok": True}), 200
