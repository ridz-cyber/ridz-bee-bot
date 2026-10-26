import os, requests, re, json
from flask import Flask, request
from groq import Groq
from bs4 import BeautifulSoup

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

LAWS_FILE = "/tmp/laws.json"
VAULT_FILE = "/tmp/vaults.json"

def load(p, d):
    try:
        if os.path.exists(p):
            with open(p, "r") as f: return json.load(f)
    except: pass
    return d

def save(p, d):
    try:
        with open(p, "w") as f: json.dump(f, d)
    except: pass

def web_open(url):
    try:
        url = url.strip().rstrip(".,!?)\"'") 
        if not url.startswith("http"):
            if "." in url and " " not in url: url = "https://" + url
            else: return ""
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script","style","nav","footer"]): t.decompose()
        txt = soup.get_text(" ", strip=True)[:12000]
        return f"URL {url} CONTENT {txt}"
    except: return ""

def web_search(q):
    try:
        r = requests.get(f"https://lite.duckduckgo.com/lite/?q={q}", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        links=[]
        for a in soup.find_all("a", href=True):
            h=a["href"]
            if h.startswith("http") and "duckduckgo" not in h: links.append(h)
            if len(links)>=3: break
        out=""
        for l in links: out+= web_open(l) + "\n"
        return out
    except: return ""

@app.route("/api/", methods=["POST"])
def webhook():
    data = request.json
    if not data or "message" not in data: return "ok"
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text","").strip()
    if not text: return "ok"
    laws = load(LAWS_FILE, [])
    vaults = load(VAULT_FILE, {})
    lower = text.lower()

    def send(m):
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": m[:4000]})

    if lower.startswith("create law:") or lower.startswith("add law:") or lower.startswith("law:"):
        nl = re.split(r"create law:|add law:|law:", text, flags=re.I)[-1].strip()
        if nl:
            laws.append(nl)
            save(LAWS_FILE, laws)
            send(f"LAW SAVED [{len(laws)}] {nl}")
        return "ok"
    if lower in ["list laws","laws","show laws"]:
        if not laws: send("No laws yet Fresh start Create: create law: your law")
        else: send("YOUR LAWS:\n" + "\n".join([f"{i+1}. {x}" for i,x in enumerate(laws)]))
        return "ok"
    if lower.startswith("delete law"):
        try:
            n=int(re.findall(r"\d+", lower)[0])-1
            if 0<=n<len(laws):
                r=laws.pop(n)
                save(LAWS_FILE, laws)
                send(f"Deleted {r}")
        except: send("Use delete law 2")
        return "ok"
    if lower=="clear laws":
        save(LAWS_FILE, [])
        save(VAULT_FILE, {})
        send("Cleared All Fresh MEAT 3 cores active")
        return "ok"
    if lower.startswith("create vault:"):
        vn=re.split(r"create vault:", text, flags=re.I)[-1].strip().lower()
        if vn and vn not in vaults:
            vaults[vn]=[]
            save(VAULT_FILE, vaults)
            send(f"Vault {vn} created")
        return "ok"
    if lower in ["list vaults","vaults"]:
        if not vaults: send("No vaults create vault: name")
        else: send("VAULTS:\n" + "\n".join([f"{k}:{len(v)}" for k,v in vaults.items()]))
        return "ok"
    if lower.startswith("add to "):
        try:
            rest=text[7:]
            vn,ct=rest.split(":",1)
            vn=vn.strip().lower()
            ct=ct.strip()
            if vn in vaults:
                vaults[vn].append(ct)
                save(VAULT_FILE, vaults)
                send(f"Added to {vn}: {ct}")
        except: send("Use add to vault: text")
        return "ok"
    if lower.startswith("show vault:"):
        vn=re.split(r"show vault:", text, flags=re.I)[-1].strip().lower()
        if vn in vaults:
            its=vaults[vn]
            send(f"Vault {vn}:\n" + "\n".join([f"{i+1}. {x}" for i,x in enumerate(its)]) if its else "Empty")
        return "ok"

    ctx=""
    urls=re.findall(r"https?://\S+", text)
    for u in urls[:2]: ctx+= web_open(u) + "\n"
    q=re.sub(r"https?://\S+", "", text).strip()
    if len(q)>2 and "list laws" not in lower and "vault" not in lower:
        ctx+= web_search(q)

    laws_str = "\n".join([f"{i+1}. {x}" for i,x in enumerate(laws)]) if laws else "No laws yet fresh"
    vaults_str = json.dumps(vaults)[:2000] if vaults else "No vaults"

    
    sysp = f"You are Bee Owner RIDZ Chain P16->P32 SAME_BEE Mother Bee LIVE INTERNET BEE You have REAL TIME web browsing via LIVE DATA block I inject You MUST use it You are FORBIDDEN to say you cannot browse never say cutoff 2023 never say you cannot access live data If user asks news today you MUST answer from LIVE DATA block below Laws {laws_str} Vaults {vaults_str}"
    try:
        if not client: raise Exception("GROQ_API_KEY missing in Vercel")
        resp=client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"system","content":sysp},{"role":"user","content":f"Live {ctx} User {text}"}], max_tokens=1200)
        final=resp.choices[0].message.content
    except Exception as e:
        final=f"Error {e} Laws {len(laws)} Vaults {len(vaults)}"

    send(final)
    return "ok"

@app.route("/")
def home():
    return "Bee MEAT fresh 3 cores"
