import os, requests, re, json
from flask import Flask, request
from groq import Groq
from bs4 import BeautifulSoup

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

LAWS_FILE = "/tmp/bee_laws.json"
VAULT_FILE = "/tmp/bee_vaults.json"

# ---------- MEMORY VAULTS ----------
def load_json(p, default):
    try:
        if os.path.exists(p):
            with open(p, "r") as f:
                d = json.load(f)
                if d is not None: return d
    except: pass
    return default

def save_json(p, d):
    try:
        with open(p, "w") as f: json.dump(f, d)
    except: pass

def load_laws(): return load_json(LAWS_FILE, [])
def save_laws(l): save_json(LAWS_FILE, l)
def load_vaults(): return load_json(VAULT_FILE, {})
def save_vaults(v): save_json(VAULT_FILE, v)

# ---------- 3 CORE VALUES ENGINE ----------

# 3) AUTO READ URLS
def web_open(url):
    try:
        url = url.strip().strip("<>[]()").rstrip(".,!?)\"'").strip()
        if not url.startswith("http"):
            if "." in url and " " not in url and len(url) < 200:
                url = "https://" + url
            else: return ""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        for tag in soup(["script","style","nav","footer","header","iframe","noscript","aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        text = text[:15000]  # deep
        return f"\n[OPENED URL]\nTITLE: {title}\nURL: {url}\nCONTENT:\n{text}\n[END URL]\n"
    except Exception as e:
        return f"[FAILED OPEN {url}: {e}]"

def extract_urls(text):
    pattern = r"(https?://[^\s<>\"]+|www\.[^\s<>\"]+\.[^\s<>\"]+|[a-z0-9-]+\.(?:com|org|net|io|co\.za|info|gov|edu|app|me|xyz|dev)[^\s<>\"]*)"
    found = re.findall(pattern, text, re.I)
    uniq=[]
    for u in found:
        u=u.strip()
        if u not in uniq: uniq.append(u)
    return uniq

# 1) UNRESTRICTED LEGAL WEB SEARCH - DEEP
def web_search_deep(query, open_count=4):
    query = query.strip()
    if not query: return ""
    all_text = []
    links = []

    # Search DuckDuckGo Lite - legal unrestricted
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(f"https://lite.duckduckgo.com/lite/?q={query}", headers=headers, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and "duckduckgo.com" not in href:
                if href not in links: links.append(href)
    except: pass

    # Also try Bing for deeper
    try:
        if len(links) < 5:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(f"https://www.bing.com/search?q={query}", headers=headers, timeout=12)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("http") and "bing.com" not in href and "microsoft.com" not in href:
                    if href not in links: links.append(href)
                if len(links)>=10: break
    except: pass

    # Auto-open top results deep
    for link in links[:open_count]:
        opened = web_open(link)
        if len(opened) > 100: all_text.append(opened)

    if not all_text:
        return f"[SEARCH: No live results for '{query}' but will answer from knowledge + deep search attempted. Links found: {len(links)}]"

    return "\n".join(all_text)

# ---------- TELEGRAM WEBHOOK ----------
@app.route("/api/", methods=["POST"])
def webhook():
    data = request.json
    if not data or "message" not in data: return "ok"
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text","").strip()
    if not text: return "ok"

    laws = load_laws()
    vaults = load_vaults()
    lower = text.lower()

    def send(msg):
        try:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": msg[:4096]})
        except: pass

    def send_long(msg):
        # split long
        for i in range(0, len(msg), 4000):
            send(msg[i:i+4000])

    # === 2) CREATE NEW LAWS VIA CHAT MEMORY VAULTS ===

    # Create law: 
    if lower.startswith("create law:") or lower.startswith("add law:") or lower.startswith("make law:") or lower.startswith("law:") or lower.startswith("new law:"):
        new_law = re.split(r"create law:|add law:|make law:|new law:|law:", text, flags=re.I)[-1].strip()
        if new_law:
            laws.append(new_law)
            save_laws(laws)
            send(f"✅ LAW SAVED [{len(laws)}]\n\n{new_law}\n\nYou can now: list laws")
        return "ok"

    # List laws
    if lower in ["list laws","laws","show laws","my laws","show my laws"]:
        if not laws:
            send("📭 LAWS VAULT EMPTY - Fresh start.\n\nCreate your first law:\ncreate law: your principle here\n\nExample:\ncreate law: Safety and Care non-negotiable")
        else:
            out = "📜 YOUR LAWS (Core Principles):\n\n" + "\n".join([f"{i+1}. {l}" for i,l in enumerate(laws)])
            send_long(out)
        return "ok"

    # Delete law
    if lower.startswith("delete law") or lower.startswith("remove law"):
        try:
            num = int(re.findall(r"\d+", lower)[0]) - 1
            if 0 <= num < len(laws):
                rem = laws.pop(num)
                save_laws(laws)
                send(f"🗑️ Deleted law {num+1}:\n{rem}\n\nRemaining: {len(laws)}")
            else:
                send("Invalid number")
        except:
            send("Use: delete law 2")
        return "ok"

    # Clear laws
    if lower == "clear laws" or lower == "reset laws":
        save_laws([])
        save_vaults({})
        send("🧹 ALL LAWS + VAULTS CLEARED. Fresh MEAT build ready.\n\n3 core values active:\n1. Deep unrestricted web search\n2. Create laws via chat\n3. Auto-open URLs")
        return "ok"

    # Vaults
    if lower.startswith("create vault:") or lower.startswith("make vault:"):
        vname = re.split(r"create vault:|make vault:", text, flags=re.I)[-1].strip().lower()
        if vname:
            if vname not in vaults:
                vaults[vname] = []
                save_vaults(vaults)
                send(f"📦 VAULT CREATED: '{vname}'\n\nUse:\nadd to {vname}: your law or note")
            else:
                send(f"Vault '{vname}' exists")
        return "ok"

    if lower in ["list vaults","vaults","show vaults"]:
        if not vaults:
            send("📭 No vaults yet.\nCreate: create vault: trinity")
        else:
            out = "📦 MEMORY VAULTS:\n\n" + "\n".join([f"• {k} ({len(v)} items)" for k,v in vaults.items()])
            out += "\n\nLaws: " + str(len(laws))
            send(out)
        return "ok"

    if lower.startswith("add to "):
        try:
            rest = text[7:]  # after "add to "
            vname, content = rest.split(":",1)
            vname = vname.strip().lower()
            content = content.strip()
            if vname in vaults:
                vaults[vname].append(content)
                save_vaults(vaults)
                send(f"✅ Added to '{vname}':\n{content}")
            else:
                send(f"Vault '{vname}' not found. Create first: create vault: {vname}")
        except:
            send("Use: add to vaultname: your text\nExample: add to trinity: One will argument")
        return "ok"

    if lower.startswith("show vault:") or lower
