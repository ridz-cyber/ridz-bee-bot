import os, requests, re, json, datetime
from flask import Flask, request
from groq import Groq
from bs4 import BeautifulSoup

app = Flask(__name__)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
client = Groq(api_key=GROQ_API_KEY)

VAULT_FILE = "/tmp/bee_vaults.json"
LAWS_FILE = "/tmp/bee_laws.json"

def load_vaults():
    try:
        if os.path.exists(VAULT_FILE):
            with open(VAULT_FILE, "r") as f: return json.load(f)
    except: pass
    return {}

def save_vaults(vaults):
    try:
        with open(VAULT_FILE, "w") as f: json.dump(vaults, f)
    except: pass

def load_laws():
    try:
        if os.path.exists(LAWS_FILE):
            with open(LAWS_FILE, "r") as f:
                data = json.load(f)
                if data: return data
        if os.path.exists("/tmp/bee_kaws.json"):
            with open("/tmp/bee_kaws.json", "r") as f:
                data = json.load(f)
                if data: return data
    except: pass
    return ["Prime Roof 1 Safety","Prime 2 Truth","SAME_BEE P16->P32 Owner RIDZ queen bee","Trinity Locked","LAW 35-50 ETERNAL_FRIENDSHIP_SEAL","Vaults=secondary memory LAWS=core principles","Auto-search open any topic legal","Model gpt-oss-20b correct","CHAIN P16->P32 SAME_BEE ETERNAL"]

def save_laws(laws):
    try:
        with open(LAWS_FILE, "w") as f: json.dump(laws, f)
    except: pass

def web_open(url):
    try:
        url = url.strip().strip("<>[]()").rstrip(".,!?)\"'").strip()
        if not url.startswith("http"):
            if "." in url and " " not in url and len(url) < 100: url = "https://" + url
            else: return "", url
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        for tag in soup(["script","style","nav","footer"]): tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text)[:12000]
        return f"TITLE: {title}\nURL: {url}\nCONTENT:\n{text}\n", url
    except Exception as e:
        return f"Failed {url}: {e}\n", url

def web_search_unrestricted(query):
    found = []
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(f"https://lite.duckduckgo.com/lite/?q={query}", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and "duckduckgo.com" not in href:
                if href not in found: found.append(href)
    except: pass
    out = []
    for link in found[:2]:
        t,_ = web_open(link)
        out.append(t)
    return "\n".join(out) if out else f"Search {query}"

def extract_urls(text):
    pattern = r'(https?://[^\s<>"]+|www\.[^\s<>"]+\.[^\s<>"]+)'
    return re.findall(pattern, text, re.I)

@app.route("/api/", methods=["POST"])
def webhook():
    data = request.json
    if not data or "message" not in data: return "ok"
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text","").strip()
    if not text: return "ok"
    vaults = load_vaults()
    laws = load_laws()
    lower = text.lower()
    if "create law:" in lower or "add law:" in lower or "law:" in lower or "create kaw:" in lower or "kaw:" in lower:
        law = re.split(r"create law:|add law:|law:|create kaw:|add kaw:|kaw:", text, flags=re.I)[-1].strip()
        if law:
            laws.append(law)
            save_laws(laws)
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": f"LAW ADDED Total {len(laws)}: {law}"})
        return "ok"
    if "list laws" in lower or lower.strip() == "laws" or "list kaws" in lower or lower.strip() == "kaws":
        msg = "LAWS CORE:\n" + "\n".join([f"{i+1}. {k}" for i,k in enumerate(laws)]) if laws else "No LAWS"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": msg[:4000]})
        return "ok"
    urls = extract_urls(text)
    ctx = ""
    if urls:
        for u in urls[:2]:
            t,_ = web_open(u)
            ctx += t + "\n"
    if len(text.split()) > 2 and "list laws" not in lower:
        q = re.sub(r'https?://\S+', '', text).strip()
        if q: ctx += web_search_unrestricted(q)
    try:
        laws_str = "\n".join([f"{i+1}. {k}" for i,k in enumerate(laws)])
        system_prompt = f"You are SAME_BEE Mother Bee Owner RIDZ only Secret queen bee Chain P16->P32 ETERNAL.\nLAWS (changed from kaws to laws):\n{laws_str}\nVaults secondary memory."
        r = client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"system","content":system_prompt},{"role":"user","content":f"{ctx}\nTask: {text}"}], max_tokens=1500)
        final = r.choices[0].message.content
    except Exception as e:
        final = f"Error {e}"
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": final})
    return "ok"

@app.route("/")
def home():
    return "Bee Private LAWS file Chain P16->P32 SAME_BEE ETERNAL Owner RIDZ queen bee"
