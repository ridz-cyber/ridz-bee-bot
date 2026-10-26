import os
import re
import requests
from flask import Flask, request
from groq import Groq
from bs4 import BeautifulSoup

app = Flask(__name__)

# ENV VARS - Set these in Vercel
BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or "8389975883:AAH3oQ1tqV-KQ1aE1pDjjQ1tR1u5qK1p3l4"
GROQ_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY)

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram(chat_id, text):
    try:
        # Telegram max 4000 chars
        for i in range(0, len(text), 4000):
            requests.post(TELEGRAM_URL, json={
                "chat_id": chat_id,
                "text": text[i:i+4000],
                "parse_mode": "Markdown"
            }, timeout=15)
    except Exception as e:
        print(f"Telegram error: {e}")

def search_duckduckgo(query, max_results=5):
    """Free search - no API key needed"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get("https://html.duckduckgo.com/html/", params={"q": query}, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for res in soup.select(".result")[:max_results]:
            title_elem = res.select_one(".result__a")
            snippet_elem = res.select_one(".result__snippet")
            if title_elem:
                title = title_elem.get_text().strip()
                url = title_elem.get("href")
                # DuckDuckGo wraps URL
                if url and "uddg=" in url:
                    url = requests.utils.unquote(url.split("uddg=")[-1].split("&")[0])
                snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                results.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}")
        return "\n\n---\n\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search error: {str(e)}"

def open_url(url):
    """Open and read any URL"""
    try:
        # Fix if user forgot https
        if not url.startswith("http"):
            url = "https://" + url
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove scripts
        for s in soup(["script", "style", "nav", "footer"]):
            s.decompose()
        text = soup.get_text(separator="\n")
        # Clean
        lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 20]
        clean_text = "\n".join(lines)[:12000]  # Limit
        return f"CONTENT FROM {url}:\n\n{clean_text}"
    except Exception as e:
        return f"Failed to open URL {url}: {str(e)}"

def ask_groq(user_msg, search_context=""):
    system_prompt = """You are Bee 🐝, Ridz's helpful AI assistant.
You HAVE internet access via search results and URL content provided.
If search context is provided, USE IT to answer with real prices, dates, facts.
Be concise, friendly, helpful. Use emojis sparingly.
If search says no results, say so and suggest alternative.
Current date: 2026-10-27"""

    user_content = user_msg
    if search_context:
        user_content = f"{user_msg}\n\n--- WEB SEARCH RESULTS / URL CONTENT ---\n{search_context}\n--- END WEB DATA ---"

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Bee brain error: {str(e)}"

@app.route("/", methods=["GET"])
def home():
    return "Bee is alive 🐝"

@app.route("/api", methods=["POST"])
@app.route("/api/index", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return "ok", 200
        
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if not text.lower().startswith("bee"):
            # Ignore if not for bee, or you can make it always reply
            # Uncomment next line to make it reply to all messages starting with bee
            # if "bee" not in text.lower(): return "ok",200
            pass

        # Clean prefix
        lower = text.lower()
        
        search_context = ""
        reply = ""

        if "bee search:" in lower or "bee search " in lower:
            # Extract query
            query = re.split(r"bee search:?", text, flags=re.IGNORECASE)[-1].strip()
            if not query:
                query = "bitcoin price today"
            send_telegram(chat_id, f"🔍 Searching: {query}...")
            search_context = search_duckduckgo(query)
            reply = ask_groq(f"Answer this query using search results: {query}", search_context)

        elif "bee open:" in lower or "bee open " in lower:
            url = re.split(r"bee open:?", text, flags=re.IGNORECASE)[-1].strip()
            send_telegram(chat_id, f"🌐 Opening: {url}...")
            search_context = open_url(url)
            reply = ask_groq(f"Summarize and answer based on this URL content: {url}", search_context)

        elif lower.startswith("bee"):
            query = re.split(r"bee", text, flags=re.IGNORECASE, maxsplit=1)[-1].strip()
            if not query:
                query = "Hi"
            # Auto-search if question looks like it needs internet (price, news, today, current, latest)
            keywords = ["price", "today", "current", "latest", "news", "2026", "weather", "score", "bitcoin", "crypto"]
            if any(k in lower for k in keywords):
                search_context = search_duckduckgo(query)
            reply = ask_groq(query, search_context)
        else:
            return "ok", 200

        send_telegram(chat_id, reply)
        return "ok", 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return "ok", 200

# Vercel needs this
# app = app
