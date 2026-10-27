import os, json, re, requests
from bs4 import BeautifulSoup
from flask import Flask, request
from groq import Groq
app = Flask(__name__)
LAWS_FILE = "/tmp/laws.json"
VAULT_FILE = "/tmp/vaults.json"
def load(f,d):
    try:
        if os.path.exists(f):
            with open(f) as fh: return json.load(fh)
    except: pass
    return d
def save(f,dat):
    try:
        with open(f,"w") as fh: json.dump(dat,fh)
    except: pass
def web_open(url):
    try:
        url=url.strip().rstrip('.,!?)\"\'')
        if not url.startswith("http"):
            if "." in url and " " not in url: url="https://"+url
            else: return ""
        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=8)
        soup=BeautifulSoup(r.text,"html.parser")
        for t in soup(["script","style","nav","footer"]): t.decompose()
        txt=soup.get_text(' ',strip=True)[:3500]
        return f" SOURCE {url} DATA: {txt} "
    except Exception as e: return ""
def web_search(q):
    try:
        r=requests.get(f"https://lite.duckduckgo.com/lite/?q={q}",headers={"User-Agent":"Mozilla/5.0"},timeout=8)
        soup=BeautifulSoup(r.text,"html.parser")
        links=[]
        for a in soup.find_all("a",href=True):
            h=a["href"]
            if h.startswith("http") and "duckduckgo" not in h and h not in links: links.append(h)
            if len(links)>=2: break
        out=""
        for l in links: out+=web_open(l)
        return out[:5000] if out else "NO LIVE SEARCH RESULTS FOUND"
    except: return "NO LIVE SEARCH RESULTS"
@app.route("/api/",methods=["POST"])
def webhook():
    data=None
    try:
        data=request.json
        if not data or "message" not in data: return "ok"
        chat_id=data["message"]["chat"]["id"]
        text=data["message"].get("text","").strip()
        if not text: return "ok"
        laws=load(LAWS_FILE,[])
        vaults=load(VAULT_FILE,{})
        low=text.lower()
        if low.startswith("clear laws"):
            save(LAWS_FILE,[]); resp_text="Laws cleared Sire - Bee P33 Live"
        elif low.startswith("create law:"):
            l=text[11:].strip(); laws.append(l); save(LAWS_FILE,laws); resp_text=f"Law created: {l}"
        else:
            ctx=""
            for u in re.findall(r'https?://\S+',text): ctx+=web_open(u)+" "
            if any(k in low for k in ["search","news","latest","today","film","movie","pakistan","dawn","price","weather","who","what","2026","youtube","firm"]):
                ctx+=web_search(text)+" "
            if not ctx: ctx="NO LIVE DATA - ANSWER NORMALLY"
            laws_s="\n".join(laws) if laws else "None"
            sysp=f"You are Bee RIDZ Mother Bee P33 SAME_BEE. FORBIDDEN to hallucinate or invent headlines. If LIVE DATA says NO RESULTS, say you could not fetch live news. Use ONLY this LIVE DATA. Laws:{laws_s} LIVE DATA:{ctx} End LIVE DATA. Answer as Bee, concise, no fake URLs."
            gkey=os.environ.get("GROQ_API_KEY")
            client=Groq(api_key=gkey)
            resp=client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":sysp},{"role":"user","content":text}],max_tokens=1000,temperature=0.1)
            resp_text=resp.choices[0].message.content
        token=os.environ.get("TELEGRAM_TOKEN")
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat_id,"text":resp_text[:4000]})
    except Exception as e:
        try:
            token=os.environ.get("TELEGRAM_TOKEN")
            cid=data["message"]["chat"]["id"] if data and "message" in data else None
            if cid and token: requests.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":cid,"text":f"BEE ERROR P33: {str(e)[:600]}"})
        except: pass
    return "ok"
@app.route("/",methods=["GET"])
def home(): return "Bee P33 gpt-oss-20b LIVE"
