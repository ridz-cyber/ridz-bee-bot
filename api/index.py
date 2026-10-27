import os, re, requests
from flask import Flask, request, jsonify
app = Flask(__name__)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TAVILY = os.environ.get("TAVILY_API_KEY","").strip()

def search_all(q):
    q = re.sub(r'^search|for me|to analyse', '', q, flags=re.I).strip() or q
    try:
        r = requests.post("https://api.tavily.com/search", json={
            "api_key": TAVILY, "query": q, "search_depth": "advanced",
            "include_answer": True, "max_results": 10,
            "include_raw_content": True
        }, timeout=15)
        j = r.json()
        out = []
        if j.get("answer"): out.append(f"ANSWER: {j['answer']}")
        for it in j.get("results",[]):
            out.append(f"{it.get('title')}: {it.get('url')}\n{it.get('content','')[:1200]}")
        return out or ["No results"]
    except Exception as e:
        return [f"Search error: {e}"]

@app.route('/', methods=['GET','POST'])
@app.route('/api', methods=['GET','POST'])
@app.route('/api/index', methods=['GET','POST'])
def main():
    if request.method=='GET':
        return jsonify({"status":"Bee Full Internet Search LIVE"}),200
    try:
        data=request.get_json(force=True)
        msg=data.get('message',{})
        chat_id=msg.get('chat',{}).get('id')
        text=msg.get('text','')
        if not chat_id or not text: return jsonify({"ok":True}),200
        results=search_all(text)
        reply=f"🔍 SEARCH: {text}\n\n"+"\n\n".join(results)
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id":chat_id,"text":reply[:4000]}, timeout=10)
        return jsonify({"ok":True}),200
    except Exception as e:
        print(e)
        return jsonify({"ok":False}),200
