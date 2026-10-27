from flask import Flask, request
import os, requests, json, re
from datetime import datetime

app = Flask(__name__)
VAULT_FILE = "/tmp/bee_vault.json"

def load_vault():
    try:
        if os.path.exists(VAULT_FILE):
            with open(VAULT_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {"vault_a": [], "laws": []}

def save_vault(vault):
    try:
        with open(VAULT_FILE, "w") as f:
            json.dump(vault, f)
    except:
        pass

def web_search(q):
    try:
        r = requests.get(f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1", timeout=5)
        j = r.json()
        t = j.get("AbstractText","")
        if t:
            return t[:800]
        return "Search live"
    except:
        return "Search live"

def read_url(url):
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent":"Bee"})
        txt = re.sub(r'<[^>]+>', ' ', r.text)
        txt = re.sub(r'\s+', ' ', txt)
        return txt[:4000]
    except Exception as e:
        return f"Cannot open {url}"

@app.route("/")
@app.route("/api", methods=["GET","POST"])
@app.route("/api/", methods=["GET","POST"])
def bee():
    if request.method == "GET":
        v = load_vault()
        return f"BEE LIVE {len(v['vault_a'])} {len(v['laws'])}"

    data = request.get_json(silent=True) or {}
    msg = data.get("message",{}) or {}
    chat_id = (msg.get("chat") or {}).get("id")
    user_text = (msg.get("text") or "").strip()
    if not chat_id or not user_text:
        return "ok"

    token = (os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN") or "").strip()
    gkey = (os.environ.get("GROQ_API_KEY") or "").strip()
    vault = load_vault()
    lower = user_text.lower()
    ctx = ""

    urls = re.findall(r'https?://\S+', user_text)
    if urls:
        for u in urls[:1]:
            ctx += read_url(u) + "\n"

    if any(k in lower for k in ["search","weather","crosby","jhb","internet","news"]):
        if not urls:
            ctx += web_search(user_text)

    if lower.startswith("remember "):
        vault["vault_a"].append({"text": user_text})
        vault["vault_a"] = vault["vault_a"][-20:]
        save_vault(vault)

    if "what do you remember" in lower:
        mem = "\n".join([m["text"] for m in vault["vault_a"][-10:]]) or "empty"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id":chat_id,"text":f"VAULT:\n{mem}"}, timeout=10)
        return "ok"

    if "forge law" in lower:
        vault["laws"].append(user_text)
        save_vault(vault)

    memory = "\n".join([m["text"] for m in vault["vault_a"][-5:]])

    reply = "Bee alive"
    try:
        from groq import Groq
        client = Groq(api_key=gkey)
        sys_p = f"You are Bee, Ridz assistant. You CAN browse web, search, read URLs live. NEVER say you cannot browse. P36 is P36 Mobile SA. Memory: {memory}. Laws: {vault['laws'][-3:]}"
        user_c = user_text + f"\n\nInfo: {ctx}" if ctx else user_text
        c = client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"system","content":sys_p},{"role":"user","content":user_c}], max_tokens=800)
        reply = c.choices[0].message.content
    except
