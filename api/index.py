from flask import Flask, request
import os, requests, json
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
        return txt[:1000]
    except:
        return ""

@app.route("/")
@app.route("/api", methods=["GET", "POST"])
@app.route("/api/", methods=["GET", "POST"])
def bee():
    if request.method == "GET":
        v = load_vault()
        return f"BEE LIVE openai/gpt-oss-20b | Vault:{len(v['vault_a'])} Laws:{len(v['laws'])}"

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
    if any(k in lower for k in ["search", "latest", "news", "weather", "crosby", "price", "who is", "jhb"]):
        search_ctx = web_search(user_text)

    if lower.startswith("remember "):
        vault["vault_a"].append({"text": user_text, "time": str(datetime.now())})
        vault["vault_a"] = vault["vault_a"][-30:]
        save_vault(vault)

    if "what do you remember" in lower or "show vault" in lower:
        mem = "\n".join([f"- {m['text']}" for m in vault["vault_a"][-15:]]) or "Vault empty"
        laws = "\n".join([f"- {l}" for l in vault["laws"][-5:]]) or "No laws"
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": f"🧠 VAULT A:\n{mem}\n\n📜 LAWS:\n{laws}"},
            timeout=10
        )
        return "ok"

    if "forge law" in lower:
        vault["laws"].append(user_text)
        vault["laws"] = vault["laws"][-50:]
        save_vault(vault)

    memory_str = "\n".join([m["text"] for m in vault["vault_a"][-6:]])
    laws_str = "\n".join(vault["laws"][-10:])

    reply = ""
    try:
        from groq import Groq
        client = Groq(api_key=gkey)

        # CRITICAL: Do NOT mention tools, browsing, searching in system prompt for gpt-oss-20b
        system_prompt = f"You are Bee, SAME BEE, Ridz's assistant. P36 is P36 Mobile SA telecom in South Africa, not PowerShell. Date {datetime.now().date()}. Memory: {memory_str}. Laws: {laws_str}. Answer in text only."

        # CRITICAL: Put search data INSIDE user message, not separate system message, to avoid tool_use_failed
        final_user_content = user_text
        if search_ctx:
            final_user_content = f"{user_text}\n\n[Background info for you to use: {search_ctx}]"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_user_content}
        ]

        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            max_tokens=900,
            temperature=0.7
        )
        reply = completion.choices[0].message.content

    except Exception as e:
        err = str(e)
        # If it STILL tries to call tool, retry with super simple prompt
        if "tool" in err.lower():
            try:
                from groq import Groq
                client = Groq(api_key=gkey)
                simple_messages = [
                    {"role": "user", "content": f"You are Bee P36 Mobile SA. Memory: {memory_str}. User says: {user_text}. Info: {search_ctx}. Reply short."}
                ]
                comp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=simple_messages,
                    max_tokens=800
                )
                reply = comp.choices[0].message.content
            except Exception as e2:
                reply = f"Alive! Vault:{len(vault['vault_a'])} You:{user_text} (tool error fixed, retry)"
        else:
            reply = f"Bee alive! Vault:{len(vault['vault_a'])} Error:{err[:200]} You:{user_text}"

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": reply[:3900]},
            timeout=12
        )
    except:
        pass

    return "ok"

handler = app
