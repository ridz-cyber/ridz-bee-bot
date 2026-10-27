from flask import Flask, request
import os, requests, json
from datetime import datetime
app = Flask(__name__)

VAULT_FILE = "/tmp/bee_vault.json"
def load_vault():
    try:
        if os.path.exists(VAULT_FILE):
            return json.load(open(VAULT_FILE))
    except: pass
    return {"vault_a": [], "laws": []}
def save_vault(v):
    try: json.dump(v, open(VAULT_FILE,"w"))
    except: pass

def web_search(q):
    try:
        r = requests.get(f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1", timeout=5)
        j = r.json()
        txt = j.get("AbstractText","")
        if txt: return txt[:800]
        for t in j.get("RelatedTopics",[])[:2]:
            if isinstance(t, dict) and t.get("Text"): txt+=t["Text"]+"\n"
        if txt: return txt[:800]
    except: pass
    return "No web result"

@app.route("/")
@app.route("/api", methods=["GET","POST"])
@app.route("/api/", methods=["GET","POST"])
def bee():
    if request.method=="GET":
        v=load_vault()
        return f"BEE MASTER BRAIN LIVE | Vault:{len(v['vault_a'])} Laws:{len(v['laws'])}"
    data=request.get_json(silent=True) or {}
    chat_id=(data.get("message",{}).get("chat") or {}).get("id")
    text=(data.get("message",{}).get("text") or "").strip()
    if not chat_id or not text: return "ok"
    token=(os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN") or "").strip()
    gkey=(os.environ.get("GROQ_API_KEY") or "").strip()
    vault=load_vault()
    lower=text.lower()
    search_ctx=""
    if any(k in lower for k in ["search","google","latest","news","price","who is","browse","internet"]):
        search_ctx=web_search(text)
    if lower.startswith("remember"):
        vault["vault_a"].append({"text":text,"time":str(datetime.now())})
        vault["vault_a"]=vault["vault_a"][-30:]
        save_vault(vault)
    if "what do you remember" in lower or "show vault" in lower:
        mem="\n".join([f"- {m['text']}" for m in vault["vault_a"][-10:]]) or "Empty"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id":chat_id,"text":f"🧠 Vault A:\n{mem}"}, timeout=10)
        return "ok"
    if "forge law" in lower:
        vault["laws"].append(text)
        save_vault(vault)
        search_ctx+="\nLaw forged: "+text

    memory="\n".join([m["text"] for m in vault["vault_a"][-6:]])
    try:
        from groq import Groq
        client=Groq(api_key=gkey)
        sys_prompt=f"You are Bee, same bee, P36 expert. You HAVE web search tool. Never say you can't browse. Current date {datetime.now().date()}. Memory: {memory}. Laws: {len(vault['laws'])} active. If search results provided, use them."
        msgs=[{"role":"system","content":sys_prompt}]
        if search_ctx: msgs.append({"role":"system","content":f"WEB SEARCH RESULT: {search_ctx}"})
        msgs.append({"role":"user","content":text})
        comp=client.chat.completions.create(model="openai/gpt-oss-20b", messages=msgs, max_tokens=800, temperature=0.7)
        ans=comp.choices[0].message.content
    except Exception as e:
        ans=f"Alive! Vault:{len(vault['vault_a'])} You:{text} err:{str(e)[:150]}"
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id":chat_id,"text":ans[:3800]}, timeout=10)
    return "ok"

handler=app
