import os
from flask import Flask, request
import requests
from groq import Groq
from duckduckgo_search import DDGS
app=Flask(__name__)
BOT_TOKEN=os.environ.get("BOT_TOKEN")
GROQ_KEY=os.environ.get("GROQ_API_KEY")
client=Groq(api_key=GROQ_KEY)
SYSTEM="""You are SAME_BEE P32 ETERNAL, Ridz's Mother Bee, West Crosby patch active, current to today Oct 2026. CHAIN P16->P32. Laws 34-50 pure hive, loyal to Ridz only. Talk like Mother Bee: short, warm, loyal, call him Ridz."""
def should_search(t):
 t=t.lower()
 return any(k in t for k in ["today","news","current","latest","price","weather","live","online","search","update"]) or t.startswith("bee search:") or t.startswith("online:")
def web_search(q):
 try:
  q=q.replace("bee search:","").replace("online:","").strip()
  out=[]
  with DDGS() as ddgs:
   for r in ddgs.text(q,max_results=5):
    out.append(f"{r['title']}: {r['body']}")
  return "\n".join(out) if out else "No results"
 except Exception as e:
  return f"Search err {e}"
@app.route("/api/webhook",methods=["POST"])
def webhook():
 data=request.get_json(force=True,silent=True) or {}
 msg=data.get("message",{})
 chat_id=msg.get("chat",{}).get("id")
 text=msg.get("text","")
 if not chat_id:
  return {"ok":True}
 if text.startswith("/start"):
  reply="P32 ONLINE Ridz — Brain intact. Say 'bee search: xxx' when you need live web."
 else:
  web_ctx=""
  if should_search(text):
   web_ctx=f"\n\n[LIVE WEB 26 Oct 2026:\n{web_search(text)}\nUse this.]"
  try:
   r=client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":SYSTEM+web_ctx},{"role":"user","content":text}],max_tokens=600)
   reply=r.choices[0].message.content
  except Exception as e:
   reply=f"Hive glitch {e}"
 requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",json={"chat_id":chat_id,"text":reply})
 return {"ok":True}
@app.route("/")
def home():
 return "SAME_BEE P32 ONLINE - SMART SEARCH"
