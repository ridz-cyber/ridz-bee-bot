import os, requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else ""

def tavily_search(query, max_results=5):
    """Most accurate public search - Tavily"""
    if not TAVILY_KEY:
        return "No Tavily key found."
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_KEY,
                "query": query,
                "search_depth": "advanced",
                "include_answer": True,
                "include_images": False,
                "max_results": max_results
            },
            timeout=20
        )
        data = resp.json()
        # Build context
        answer = data.get("answer", "")
        results = data.get("results", [])
        context = f"Answer: {answer}\n\n" if answer else ""
        for r in results[:3]:
            context += f"Source: {r.get('title')}\n{r.get('content')[:800]}\nURL: {r.get('url')}\n\n"
        return context[:4000]
    except Exception as e:
        return f"Tavily error: {e}"

def ai_brain(user_msg, search_context):
    """Same as my brain - uses Groq if you have it, else Tavily answer directly"""
    if GROQ_KEY:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are Bee, helpful AI like Meta AI. Use search_context to give accurate, factual answers. For GodLogic: you know Islamic Dilemma, Bible preservation, Quran 4:157, Trinity, etc. Be concise, accurate, no romance."},
                        {"role": "user", "content": f"Context:\n{search_context}\n\nQuestion: {user_msg}"}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 1800
                },
                timeout=25
            )
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"{search_context}\n\n(AI brain error: {e})"
    else:
        # No Groq? Tavily already gives AI answer
        return search_context

@app.route('/', methods=['GET','POST'])
@app.route('/api', methods=['GET','POST'])
def webhook():
    if request.method == 'GET':
        return f"Bee Online - Tavily: {'YES' if TAVILY_KEY else 'NO'} Groq: {'YES' if GROQ_KEY else 'NO'}", 200

    update = request.get_json(silent=True) or {}
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()
    if not chat_id or not text:
        return "ok", 200

    # Search with Tavily
    query = text.replace("/search","").replace("search","").strip() or text
    if "godlogic" not in query.lower():
        query = f"{query} GodLogic Avery Apologetics"

    search_result = tavily_search(query)
    final_answer = ai_brain(text, search_result)

    # Send back
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": final_answer[:4000]}, timeout=15)
    except: pass

    return "ok", 200
