import os, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TAV = os.environ.get("TAVILY_API_KEY", "")
GRO = os.environ.get("GROQ_API_KEY", "")

# --- FUNCTION 1: FULL INTERNET SEARCH (Simulates Meta AI Search) ---
def full_search(query):
    try:
        if not TAV:
            return "Error: Add TAVILY_API_KEY in Vercel"
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAV,
                "query": query,
                "search_depth": "advanced",
                "include_answer": True,
                "include_images": False,
                "max_results": 8
            },
            timeout=12
        )
        data = r.json()
        out = ""
        if data.get("answer"):
            out += f"DIRECT ANSWER: {data['answer']}\n\n"
        for item in data.get("results", [])[:5]:
            title = item.get("title", "")
            url = item.get("url", "")
            content = item.get("content", "")[:600]
            out += f"Source: {title}\n{url}\n{content}\n\n"
        return out[:4000] if out else "No results found"
    except Exception as e:
        return f"Search temp offline: {e}"

# --- FUNCTION 2: DEEP BRAIN / ANALYSIS (Simulates Meta AI Reasoning) ---
def deep_brain(user_q, web_context):
    try:
        if not GRO:
            # Fallback if no GROQ key
            return f"BEE SEARCH RESULT:\n\n{web_context[:3500]}"
        
        # This uses Llama 3.3 70B - Most accurate public model
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
                        "content": "You are Bee - Ultimate Research Analyst. You combine web sources into 100% accurate, structured answers. For debates: give claim, evidence, counter, sources. For general: give direct answer + 3 sources. Be sharp, cite URLs, never hallucinate. If web context says something, use it."
                    },
                    {
                        "role": "user",
                        "content": f"User Question: {user_q}\n\nWeb Research Data:\n{web_context[:3500]}\n\nTask: Give 100% accurate answer based on research. Cite sources."
                    }
                ]
            },
            timeout=18
        )
        j = r.json()
        return j["choices"][0]["message"]["content"]
    except Exception as e:
        return f"{web_context[:3000]}\n\n(Brain temp offline: {e})"

# --- MAIN WEBHOOK - ALWAYS ALIVE ---
@app.route('/', methods=['GET','POST'])
@app.route('/api', methods=['GET','POST'])
@app.route('/api/index', methods=['GET','POST'])
def main():
    if request.method == 'GET':
        return jsonify({
            "status": "Bee Ultimate V3 Online",
            "functions": [
                "full_web_search",
                "deep_brain_analysis",
                "youtube_ready",
               
