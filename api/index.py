import os, re, requests
from flask import Flask, request
import groq

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = groq.Groq(api_key=GROQ_KEY) if GROQ_KEY else None

def tg_send(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text[:4000], "parse_mode": "Markdown"}, timeout=10)
    except: pass

def fetch_price(coin="bitcoin"):
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd&include_24hr_change=true", timeout=10).json()
        return f"{coin.upper()} PRICE LIVE: ${r[coin]['usd']:,.2f} USD, 24h change: {r[coin]['usd_24h_change']:.2f}% (CoinGecko)"
    except: return ""

def search_duckduckgo(q):
    try:
        # Try lite version - less blocking
        r = requests.get(f"https://lite.duckduckgo.com/lite/?q={q}", headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        # extract all text between links
        texts = re.findall(r'<a rel="nofollow"[^>]*>(.*?)</a>', r.text)
        snippet = "\n".join(texts)[:6000]
        # clean html
        snippet = re.sub('<[^>]+>', '', snippet)
        if len(snippet) > 100:
            return snippet
    except Exception as e:
        print(f"Search error {e}")
    # fallback to coingecko for crypto
    if "bitcoin" in q.lower() or "btc" in q.lower():
        return fetch_price("bitcoin")
    if "ethereum" in q.lower() or "eth" in q.lower():
        return fetch_price("ethereum")
    return f"No web results, but user asked: {q}. Use your knowledge cutoff 2026."

def open_page(url):
    try:
        if not url.startswith("http"): url = "https://" + url
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        txt = re.sub('<[^<]+?>', ' ', r.text)
        txt = re.sub('\s+', ' ', txt)
        return txt[:7000]
    except Exception as e:
        return f"Failed to open {url}: {e}"

@app.route("/api", methods=["POST", "GET"])
@app.route("/", methods=["POST", "GET"])
def main():
    if request.method == "GET":
        return "Bee Online 🐝"
    data = request.json
    if not data or "message" not in data:
        return {"ok": True}
    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text","")
    if not text.lower().startswith("bee"):
        return {"ok": True}

    raw_query = text[3:].strip().lstrip(":").strip()
    lower = text.lower()
    context = ""

    if "search:" in lower:
        q = text.split(":",1)[1].strip()
        tg_send(chat_id, f"🔍 Searching: {q}...")
        context = search_duckduckgo(q)
        if "bitcoin" in q.lower() or "price" in q.lower():
            context = fetch_price("bitcoin") + "\n" + context
    elif "open:" in lower:
        url = text.split(":",1)[1].strip()
        tg_send(chat_id, f"🌐 Opening: {url}...")
        context = open_page(url)
    else:
        # auto search if asks for live data
        if any(w in lower for w in ["price","today","2026","weather","latest","news"]):
            context = search_duckduckgo(raw_query)
            if "bitcoin" in lower:
                context = fetch_price("bitcoin") + "\n" + context

    prompt = f"User: {raw_query}\n\nLIVE WEB DATA:\n{context}\n\nInstructions: You are Bee. Answer using the LIVE WEB DATA above. If price data is there, give exact numbers. Don't say you can't fetch. Be concise and helpful."

    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content":"You are Bee, a Telegram bot with real-time web browsing. Always use the provided LIVE WEB DATA. Never say you can't fetch. If data is empty, still answer from knowledge but say search was limited."},
                {"role":"user","content": prompt}
            ],
            temperature=0.7
        )
        ans = resp.choices[0].message.content
    except Exception as e:
        ans = f"Groq Error: {e}\nData was: {context[:1000]}"

    tg_send(chat_id, ans)
    return {"ok": True}
