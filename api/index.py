import os, requests, re, json, datetime
from flask import Flask, request
from groq import Groq
from bs4 import BeautifulSoup

app = Flask(__name__)

# === KEYS FROM VERCEL ENV ===
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
client = Groq(api_key=GROQ_API_KEY)

# === MEMORY VAULT SYSTEM - PARTITIONS WITH LAWS ===
VAULT_FILE = "/tmp/bee_vaults.json"

def load_vaults():
    try:
        if os.path.exists(VAULT_FILE):
            with open(VAULT_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    # Default vault with your primary laws
    return {
        "main": {
            "laws": [
                "Primary Law: Online access is mandatory - always search web",
                "Primary Law: Bot may auto-open URLs itself to complete task",
                "Primary Law: No command word needed - auto-search all queries"
            ],
            "data": [],
            "created": str(datetime.datetime.now())
        }
    }

def save_vaults(vaults):
    try:
        with open(VAULT_FILE, "w") as f:
            json.dump(vaults, f)
    except:
        pass

# === WEB OPEN - AUTO URL ===
def web_open(url):
    try:
        url = url.strip().strip("<>[]()").rstrip(".,!?)\"'").strip()
        if not url.startswith("http"):
            # Allow domains like example.com, coindesk.com
            if "." in url and " " not in url and len(url) < 100:
                url = "https://" + url
            else:
                return "", url
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        for tag in soup(["script","style","nav","footer","header","aside","iframe","noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text)[:8000]
        return f"--- AUTO-OPENED BY BOT ---\n
