import os, json, re, requests
from bs4 import BeautifulSoup
from flask import Flask, request
from groq import Groq

app = Flask(__name__)
LAWS_FILE = "/tmp/laws.json"
VAULT_FILE = "/tmp/vaults.json"

def load(f, d):
    try:
        if os.path.exists(f):
            with open(f) as fh: return json.load(fh)
    except: pass
    return d

def save(f, data):
    try:
        with open(f, "w") as fh: json.dump(data, fh)
    except: pass

def web_open(url):
    try:
        url = url.strip().rstrip('.,!?)\"\'')
        if not url.startswith("http"):
            if "." in url and " " not in url: url = "https://" + url
            else: return ""
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style", "nav", "footer"]): t.decompose()
        return f"URL {url} CONTENT {soup.get_text(' ', strip=True)[:4000]}"
    except Exception as e:
        return f"web_open error {e}"

def web_search(q):
    try:
        r = requests.get(f"https://lite.duckduckgo.com/lite/?q={q}", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            h = a["href"]
            if h.startswith("http") and "duckduckgo" not in h and h not in links: links.append(h)
            if len(links) >= 2: break
        out = ""
        for l in links: out += web_open(l) + " "
        return out[:5000]
    except Exception as e:
        return f"web_search error {e}"

@app.route("/api/", methods=["POST"])
def webhook():
    data = None
    try:
        data = request.json
        if not data or "message" not in data: return "ok"
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        if not text: return "ok"

        laws = load(LAWS_FILE, [])
        vaults = load(VAULT_FILE, {})
        lower = text.lower()

        if lower.startswith("clear laws"):
            laws = []; save(LAWS_FILE, laws)
            resp_text = "Laws cleared RIDZ - SAME BEE"
        elif lower.startswith("create
