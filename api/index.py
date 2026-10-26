import os, json, re, requests
from bs4 import BeautifulSoup
from flask import Flask, request
from groq import Groq

app = Flask(__name__)
LAWS_FILE = "/tmp/laws.json"
VAULT_FILE = "/tmp/vaults.json"
GROQ_KEY = os.environ.get("GROQ_API_KEY")

def load(f, d):
    try:
        if os.path.exists(f):
            with open(f) as fh:
                return json.load(fh)
    except:
        pass
    return d

def save(f, data):
    try:
        with open(f, "w") as fh:
            json.dump(data, fh)
    except:
        pass

def web_open(url):
    try:
        url = url.strip().rstrip('.,!?)\"\'')
        if not url.startswith("http"):
            if "." in url and " " not in url:
                url = "https://" + url
            else:
                return ""
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script","style","nav","footer"]):
            t.decompose()
        txt = soup.get_text(" ", strip=True)[:4000]
        return f"URL {url} CONTENT {txt}"
    except:
        return ""

def web_search(q):
    try:
        r = requests.get(f"https://lite.duckduckgo.com/lite/?q={q}", headers={"User-Agent":"Mozilla/5.0"}, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        links=[]
        for a in soup.find_all("a", href=True):
            h=a["href"]
            if h.startswith("http") and "duckduckgo" not in h:
                if h not in links:
                    links.append(h)
            if len(links)>=3:
                break
        out=""
        for l in links:
            out+= web_open(l) + " "
        return out[:6000]
    except:
        return ""

@app.route("/api/", methods=["POST"])
def webhook():
    data = request.json
    if not data or "message" not in data:
        return "ok"
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text","").strip()
    if not text:
        return "ok"
    laws = load(LAWS_FILE, [])
    vaults = load(VAULT_FILE, {})
    lower = text.lower()

    if lower.startswith("clear laws"):
        laws=[]
        save(LAWS_FILE, laws)
        resp_text="Laws cleared"
    elif lower.startswith("create law:"):
        law=text[11:].strip()
        laws.append(law)
        save(LAWS_FILE, laws)
        resp_text=f"Law created: {law}"
    else:
        ctx=""
        for u in re.findall(r'https?://\S+', text):
            ctx+= web_open(u) + " "
        if any(k in lower for k in ["search","news","today","latest","what","who","when","where","price","weather","pakistan","internet","dawn"]):
            ctx+= web_search(text) + " "
        if not ctx:
            ctx="NO LIVE DATA FOUND"
        laws_str = "\n".join([f"{i+1}. {l}" for i,l in enumerate(laws)]) if laws else "No laws"
        vaults_str = json.dumps(vaults)[:2000]
        sysp = f"You are Bee RIDZ Chain P16->P32 SAME_BEE LIVE INTERNET BEE FORBIDDEN to say cannot browse or cutoff 2023 NEVER invent news Use ONLY LIVE DATA If NO LIVE DATA say NO DATA Laws {laws_str} Vaults {vaults_str} LIVE DATA START {ctx} LIVE DATA END"
        client = Groq(api_key=GROQ_KEY)
        resp=client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":sysp},{"role":"user","content":text}], max_tokens=1200, temperature=0.2)
        resp_text=resp.choices[0].message.content

    try:
        token=os.environ.get("TELEGRAM_TOKEN")
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id":chat_id,"text":resp_text[:4000]})
    except:
        pass
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bee Live"
