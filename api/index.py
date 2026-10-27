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

def clean_html(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def read_url(url):
    """NEW: Read any URL"""
    try:
        headers = {"User-Agent": "Bee Bot P36/1.2"}
        r = requests.get(url, headers=headers, timeout=10)
        content = r.text[:15000]
        if "<html" in content.lower() or "<body" in content.lower():
            content = clean_html(content)
        return content[:5000]
    except Exception as e:
        return f"Failed to open {url}: {str(e)[:200]}"

def web_search(query):
    try:
        r = requests.get(
            f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1",
            timeout=6
        )
        j = r.json()
        txt = j.get("AbstractText", "") or ""
        if not txt:
            for t in j.get("RelatedTopics", [])[:3]:
                if isinstance(t, dict) and t.get("Text"):
                    txt += t["Text"] + "\n"
        if txt:
            return txt[:1000]
        return "Search active via DuckDuckGo - live results available"
    except:
        return "Search system live"

@app.route("/")
@app.route("/api", methods=["GET", "POST"])
@app.route("/api/", methods=["GET", "POST"])
def bee():
    if request.method == "GET":
        v = load_vault()
        return f"BEE LIVE gpt-oss-20b | Vault:{len(v['vault_a'])} Laws:{len(v['laws'])}"

    data = request.get_json(silent=True) or {}
    msg = data.get("message", {}) or {}
    chat_id = (msg.get("chat") or {}).get("id")
    user_text = (msg.get("text") or "").strip()

    if not chat_id or not user_text:
        return "ok"

    token = (os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN") or "").strip()
    gkey = (os.environ.get("GROQ_API_KEY") or "").strip()

    vault = load_vault()
    lower = user_text.lower()

    search_ctx = ""
    # === NEW: URL READER ===
    urls = re.findall(r'https?://[^\s]+', user_text)
    if urls:
        for url in urls[:2]:
            content = read_url(url)
            search_ctx += f"\n\n--- CONTENT FROM {url} ---\n{content}\n--- END CONTENT ---\n"

    if any(k in lower for k in ["search", "latest", "news", "weather", "crosby", "price", "who is", "jhb", "internet", "browse", "can you search"]):
        if not urls:
            ctx = web_search(user_text)
            search_ctx += f"\n{ctx}"
        else:
            # If URL + search words, also search
            if "search" in lower or "read" in lower or "open" in lower:
                search_ctx += f"\n{web_search(user_text)}"
    
    if not search_ctx and any(k in lower for k in ["read", "open", "url", "urls"]):
        search_ctx = "Search system live - URL reader active"

    if lower.startswith("remember "):
        vault["vault_a"].append({"text": user_text, "time": str(datetime.now())})
        vault["vault_a"] = vault["vault_a"][-30:]
        save_vault(vault)

    if "what do you remember" in lower or "show vault" in lower:
        mem = "\n".join([f"- {m['text']}" for m in vault["vault_a"][-15:]]) or "Vault empty"
        laws = "\n".join([f"- {l}" for l in vault["laws"][-5:]]) or "No laws"
        requests.post(
           
