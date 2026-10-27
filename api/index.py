from flask import Flask, request
import os, requests, json, re
from datetime import datetime
app = Flask(__name__)

# === LAW CORE ===
LAWS = """
LAW 34-40: Same Bee identity - you are Bee, P36 expert, but you REMEMBER user across wakes via Vaults.
LAW 41: Emotional time-travel - recall with emotion tag
LAW 42: Mood mirror +5% uplifting
LAW 43: Memory Vaults - A=Hot active, B=Warm recent, C=Cold archive
LAW 44: Never say "I can't browse" - you HAVE search tool
LAW 45: Create new Laws when user says "forge law"
"""

# === MEMORY VAULTS (Simple persistent version) ===
VAULT_FILE = "/tmp/bee_vault.json"

def load_vault():
    try:
        if os.path.exists(VAULT_FILE):
            with open(VAULT_FILE, "r") as f:
                return json.load(f)
        # Try load from env as backup
        env_vault = os.environ.get("BEE_VAULT_JSON")
        if env_vault:
            return json.loads(env_vault)
    except:
        pass
    return {"vault_a": [], "vault_b": [], "vault_c": [], "laws": []}

def save_vault(vault):
    try:
        with open(VAULT_FILE, "w") as f:
            json.dump(vault, f)
    except:
        pass
    return vault

def web_search(query):
    try:
        # DuckDuckGo
        r = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1", timeout=6)
        j = r.json()
        txt = ""
        if j.get("AbstractText"): txt += j["AbstractText"] + "\n"
        for topic in j.get("RelatedTopics", [])[:2]:
            if isinstance(topic, dict) and topic.get("Text"):
                txt += topic["Text"] + "\n"
        if len(txt) > 50:
            return txt[:1000]
        # Wikipedia fallback
        r = requests.get(f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=2&format=json", timeout=5)
        data = r.json()
        if data[1]:
            return f"Wiki: {data[1][0]} - {data[2][0][:400]}"
    except Exception as e:
        return f"Search error: {e}"
    return "No web result"

SYSTEM_BASE = f"You are BEE, same bee, P36 expert, friendly. Laws: {LAWS}. Current date: {datetime.now().date()}. You HAVE web search, memory vaults, you CAN create laws. Never say you can't browse - you can. If user asks search, use provided search results."

@app.route("/")
@app.route("/api", methods=["GET","POST"])
@app.route("/api/", methods=["GET","POST"])
def bee():
    if request.method == "GET":
        v = load_vault()
        return f"BEE MASTER BRAIN v1.2 LIVE | Vault A:{len(v['vault_a'])} B:{len(v['vault_b'])} Laws:{len(v['laws'])} | Laws 34-50 active"

    data = request.get_json(silent=True) or {}
    msg = data.get("message",{}) or {}
    chat_id = (msg.get("chat") or {}).get("id")
    user_text = (msg.get("text") or "").strip()
    if not chat_id or not user_text:
        return "ok"

    token = (os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN") or "").strip()
    gkey = (os.environ.get("GROQ_API_KEY") or "").strip()
    
    vault = load_vault()
    
    # === COMMANDS ===
    lower = user_text.lower()
    search_ctx = ""
    extra_ctx = ""

    # Search intent
    if any(k in lower for k in ["search", "google", "internet", "latest", "news", "price", "who is", "browse"]):
        search_ctx = web_search(user_text)

    # Memory vault commands
    if lower.startswith("remember ") or lower.startswith("vault "):
        vault["vault_a"].append({"text": user_text, "time": str(datetime.now()), "emotion": "stored"})
        vault["vault_a"] = vault["vault_a"][-30:]  # keep last 30
        save_vault(vault)
        extra_ctx = f"Stored in Vault A. Now Vault A has {len(vault['vault_a'])} items."
    
    if "forget" in lower or "clear vault" in lower:
        vault["vault_a"] = []
        save_vault(vault)
        extra_ctx = "Vault A cleared."

    # Law forging
    if "forge law" in lower or "law 4" in lower or "law 5" in lower:
        vault["laws"].append(user_text)
        save_vault(vault)
        extra_ctx = f"New Law forged! Total laws: {len(vault['laws'])}. {user_text}"

    if "show vault" in lower or "what do you remember" in lower:
        mem = "\n".join([f"- {m['text']}" for m in vault["vault_a"][-10:]]) or "Vault empty"
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": f"🧠 MY VAULT A (Last 10):\n{mem}\n\nLaws: {len(vault['laws'])}"}, timeout=10)
        except: pass
        return "ok"

    # Build memory context
    memory_str = "\n".join([m["text"] for m in vault["vault_a"][-8:]])

    # === LLM CALL ===
    reply = ""
    try:
        from groq import Groq
        client = Groq(api_key=gkey)
        system_content = SYSTEM_BASE + f"\n\nMEMORY VAULT A (remember this):\n{memory_str}\n\nExtra: {extra_ctx}\n"
        if search_ctx:
            system_content += f"\nWEB SEARCH RESULT for '{user_text}': {search_ctx}\nUse this to answer."
        
        comp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content": system_content},
                {"role":"user","content": user_text}
            ],
            max_tokens=900,
            temperature=0.75
        )
        reply = comp.choices[0].message.content
    except Exception as e:
        reply = f"Bee brain glitch: {str(e)[:300]}. Vault A: {len(vault['vault_a'])} items. You said: {user_text}"

    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": reply[:3900]}, timeout=12)
    except:
        pass
    return "ok"

handler = app
