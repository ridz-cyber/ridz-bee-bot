from flask import Flask, request, jsonify
import os, requests

app = Flask(__name__)

BOT = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TAV = os.environ.get("TAVILY_API_KEY", "")
GRO = os.environ.get("GROQ_API_KEY", "")

def web_search(q):
    try:
        if not TAV:
            return "No TAV key"
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAV,
                "query": q,
                "search_depth": "advanced",
                "include_answer": True,
                "max_results": 6
            },
            timeout=12
        )
        j = r.json()
        out = ""
        if j.get("answer"):
            out += j["answer"] + "\n\n"
        for x in j.get("results", [])[:4]:
            out += x.get("content", "")[:500] + "\n\n"
        return out[:3500]
    except Exception as e:
        return f"Search offline: {e}"

def ai_brain(q, ctx):
    try:
        if not GRO:
            return ctx[:3500]
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GRO}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Bee - expert analyst. Use web context to give 100% accurate answer. Cite sources."
                    },
                    {
                        "role": "user",
                        "content": f"Question: {q}\n\nResearch:\n{ctx[:3000]}"
                    }
                ]
            },
            timeout=15
        )
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return ctx[:3500]

@app.route('/', methods=['GET','POST'])
@app.route('/api', methods=['GET','POST'])
@app.route('/api/index', methods=['GET','POST'])
def main():
    if request.method == 'GET':
        return jsonify({"status": "Bee Master V3 Ready"}), 200
    
    try:
        data = request.get_json(silent=True) or {}
        msg = data.get('message', {})
        cid = msg.get('chat', {}).get('id')
        txt = msg.get('text', 'hi').strip()
        
        if not cid:
            return jsonify({"ok": True}), 200
        
        # Full functions simulation
        web = web_search(txt)
        ans = ai_brain(txt, web)
        ans = ans[:3800]
        
        requests.post(
            f"https://api.telegram.org/bot{BOT}/sendMessage",
            json={"chat_id": cid, "text": ans},
            timeout=8
        )
    except:
        pass
    
    return jsonify({"ok": True}), 200
