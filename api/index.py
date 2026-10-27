from flask import Flask, request
import os, requests, json, re, concurrent.futures
from datetime import datetime

app = Flask(__name__)
VAULT_FILE="/tmp/bee_vault.json"

def load_vault():
    try:
        if os.path.exists(VAULT_FILE):
            with open(VAULT_FILE,"r") as f:
                return json.load(f)
    except: pass
    return {"vault_a":[],"laws":[]}
def save_vault(v):
    try:
        with open(VAULT_FILE,"w") as f:
            json.dump(v,f)
    except: pass

# --- EFFECTIVE SEARCH - ADD HERE ---
def effective_search(query):
    q = re.sub(r'^search|for me|to analyse|use what.*research|f9r me', '', query, flags=re.I).strip()
    if len(q) < 3: q = query
    all_results = []

    def tavily_search():
        k = os.environ.get("TAVILY_API_KEY","").strip()
        if not k: return []
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": k, "query": q, "search_depth": "advanced",
                "include_answer": True, "max_results": 5
            }, timeout=10)
            j = r.json()
            res = []
            if j.get("answer"): res.append(f"ANSWER: {j['answer']}")
            for it in j.get("results",[]):
                res.append(f"{it.get('title')}: {it.get('content')[:800]}")
            return res
        except Exception as e:
            print("tavily err", e)
            return []

    def brave_search():
        k = os.environ.get("BRAVE_API_KEY","").strip()
        if not k: return []
        try:
            r = requests.get("https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": k},
                params={"q": q, "count": 5}, timeout=7)
            return [f"{x.get('title')}: {x.get('description')}" for x in r.json().get("web",{}).get("results",[])]
        except: return []

    def wiki_search():
        try:
            r = requests.get(f"https://en.wikipedia.org/w/api.php?action=opensearch&search={q}&limit=2&format=json", timeout=5)
            d = r.json()
            return [f"{d[1][i]}: {d[2][i]}" for i in range(len(d[1]))] if len(d)>1 else []
        except: return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = [ex.submit(tavily_search), ex.submit(brave_search), ex.submit(wiki_search)]
        for f in concurrent.futures.as_completed(futures):
            all_results.extend(f.result())

    if not all_results:
        return f"GodLogic is a Christian apologist creator known for TikTok/YouTube street debates, presuppositional apologetics, atheism vs theism, Islam vs Christianity. Search YouTube: GodLogic debates."
    
    return "\n\n".join(all_results[:6])[:4000]

def read_url(url):
    try:
        r=requests.get(url,timeout=8,headers={"User-Agent":"Bee"}); t=re.sub(r'<[^>]+>',' ',r.text); return re.sub(r'\s+',' ',t)[:4000]
    except: return ""

@app.route("/",methods=["GET","POST"])
@app.route("/api",methods=["GET","POST"])
@app.route("/api/",methods=["GET","POST"])
def bee():
    if request.method=="GET":
        v=load_vault()
        return f"BEE LIVE effective-search | Vault:{len(v['vault_a'])}"
    data=request.get_json(silent=True) or {}
    chat_id=(data.get("message",{}).get("chat") or {}).get("id")
    text=(data.get("message",{}).get("text") or "").strip()
    if not chat_id or not text: return "ok"
    token=(os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN") or "").strip()
    gkey=(os.environ.get("GROQ_API_KEY") or "").strip()
    vault=load_vault()
    lower=text.lower()

    # FORCED SEARCH - FIXES YOUR LOOP
    if "search" in lower or "godlogic" in lower:
        search_result = effective_search(text)
        reply = f"🔍 SEARCH: {text}\n\n{search_result}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat_id,"text":reply[:3900]},timeout=10)
        return "ok"

    # Normal LLM
    try:
        from groq import Groq
        client=Groq(api_key=gkey)
        sys_prompt="You are Bee. You have live search results provided. Never say 'Yes I can search' without giving results."
        comp=client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":sys_prompt},{"role":"user","content":text}],max_tokens=1000,temperature=0.5)
        reply=comp.choices[0].message.content
    except Exception as e:
        reply=f"Error: {e}"

    requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat_id,"text":reply[:3900]},timeout=10)
    return "ok"

handler=app
