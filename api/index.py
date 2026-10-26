import os, requests, json
from flask import Flask, request, jsonify
from groq import Groq
from duckduckgo_search import DDGS

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

# --- MEMORY VAULT ---
memory_store = {}  # fallback if no Upstash
def vault_save(user_id, key, value):
    try:
        if UPSTASH_URL and UPSTASH_TOKEN:
            requests.post(f"{UPSTASH_URL}/set/{user_id}_{key}/{value}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
        else:
            memory_store[f"{user_id}_{key}"] = value
        return True
    except: return False

def vault_get(user_id, key):
    try:
        if UPSTASH_URL and UPSTASH_TOKEN:
            r = requests.get(f"{UPSTASH_URL}/get/{user_id}_{key}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
            if r.ok and r.json().get("result"):
                return r.json()["result"]
        return memory_store.get(f"{user_id}_{key}")
    except: return None

def vault_all(user_id):
    # simple list for demo
    keys = [k for k in memory_store if k.startswith(str(user_id))]
    return "\n".join([f"{k}: {v}" for k,v in memory_store.items() if str(user_id) in k]) or "Vault empty. Use: bee remember: key = value"

# --- TOOLS ---
def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results: return "No results found."
        txt = "\n\n".join([f"• {r['title']}\n{r['body']}\n{r['href']}" for r in results])
        return txt
    except Exception as e:
        return f"Search error: {e}"

def groq_reply(prompt, search_context=""):
    try:
        system = f"You are Bee 🐝, Ridz's loyal AI hive assistant. Smart, concise, helpful. Sire calls you Bee. If search context provided, use it to answer with sources. Be friendly.\nContext: {search_context}\nVault: use only if asked."
        resp = client.chat.completions.create(
                            model="openai/gpt-oss-20b",
            messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Bee brain error: {e}"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id":chat_id,"text":text[:4000], "parse_mode":"Markdown"})

def send_photo(chat_id, prompt):
    # Free image via Pollinations
    safe_prompt = requests.utils.quote(prompt)
    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    requests.post(url, json={"chat_id":chat_id,"photo":img_url,"caption":f"🐝 {prompt}"})

def transcribe_voice(file_id):
    try:
        # Get file path
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
        file_path = r["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        audio = requests.get(file_url).content
        # Save temp and transcribe via Groq Whisper
        with open("/tmp/voice.ogg","wb") as f: f.write(audio)
        with open("/tmp/voice.ogg","rb") as f:
            tr = client.audio.transcriptions.create(model="whisper-large-v3", file=f)
        return tr.text
    except Exception as e:
        return f"Voice error: {e}"

@app.route("/")
def home(): return "Bee 🐝 Online - Ready for Sire"

@app.route("/api/webhook", methods=["POST","GET"])
def webhook():
    if request.method == "GET": return "Bee webhook alive"
    data = request.json
    if not data or "message" not in data: return jsonify(ok=True)
    msg = data["message"]
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    text = msg.get("text","")
    voice = msg.get("voice")

    # VOICE INPUT
    if voice:
        send_message(chat_id,"🎧 Bee listening...")
        txt = transcribe_voice(voice["file_id"])
        text = txt  # treat transcription as text
        send_message(chat_id,f"🗣 You said: {txt}")

    if not text: return jsonify(ok=True)
    lower = text.lower()

    # COMMANDS
    if lower.startswith("bee image:") or lower.startswith("bee img:"):
        prompt = text.split(":",1)[1].strip()
        send_message(chat_id,f"🎨 Drawing: {prompt}...")
        send_photo(chat_id,prompt)
        return jsonify(ok=True)

    if lower.startswith("bee remember:"):
        try:
            part = text.split(":",1)[1].strip()
            if "=" in part:
                k,v = part.split("=",1)
            else:
                k,v = "note", part
            vault_save(user_id, k.strip(), v.strip())
            send_message(chat_id,f"✅ Vault saved: {k.strip()} = {v.strip()}")
        except: send_message(chat_id,"Use: bee remember: key = value")
        return jsonify(ok=True)

    if "bee recall" in lower or "bee vault" in lower or "recall" in lower and "bee" in lower:
        all_mem = vault_all(user_id)
        send_message(chat_id,f"🧠 Your Vault:\n{all_mem}")
        return jsonify(ok=True)

    if "bee search:" in lower or lower.startswith("search:"):
        query = text.split(":",1)[1].strip()
        send_message(chat_id,f"🔍 Bee searching: {query}...")
        results = web_search(query)
        answer = groq_reply(f"User asks: {query}. Summarize these results in concise answer with links:", results)
        send_message(chat_id, f"{answer}\n\n📚 Sources:\n{results}")
        return jsonify(ok=True)

    # DEFAULT CHAT + auto search if question about price/news/today
    keywords = ["price","today","news","latest","who is","what is","bitcoin","crypto","stock"]
    search_ctx = ""
    if any(k in lower for k in keywords) or "?" in text:
        search_ctx = web_search(text)

    reply = groq_reply(text, search_ctx)
    send_message(chat_id, reply)
    return jsonify(ok=True)
