from flask import Flask, request
import os, requests, json
from datetime import datetime
app = Flask(__name__)

# === VAULT SYSTEM ===
VAULT_FILE = "/tmp/bee_vault.json"

def load_vault():
    try:
        if os.path.exists(VAULT_FILE):
            with open(VAULT_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {"vault_a": [], "vault_b": [], "laws": []}

def save_vault(vault):
    try:
        with open(VAULT_FILE, "w") as f:
            json.dump(vault, f)
    except:
        pass

def web_search(query):
    """Free search - DuckDuckGo"""
    try:
        r = requests.get(
            f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1",
            timeout=6
        )
        j = r.json()
        txt = j.get("AbstractText", "") or ""
        if not txt:
            for t in j.get("RelatedTopics", [])[:3]:
                if isinstance(t, dict) and t
