import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

def effective_search(query):
    q = re.sub(r'^search|for me|to analyse|analyze', '', query, flags=re.I).strip()
    if len(q) < 3: q = query
    all_results = []

    def tavily_search():
        k = os.environ.get("TAVILY_API_KEY", "").strip()
        if not k: return []
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": k, "query": q, "search_depth": "advanced",
                "include_answer": True, "max_results": 10,
                "include_raw_content": True,
                "include_domains": [],
                "exclude_domains": []
            }, timeout=15)
            j = r.json()
            res = []
            if j.get("answer"): res.append(f"ANSWER: {j.get('answer')}\n")
            for it in j.get("results", []):
                res.append(f"{it.get('title')}: {it.get('url')}\n{it.get('content','')[:1000]}")
            return res
        except Exception as e:
            print("tavily err", e)
            return []

    def duckduckgo_fallback():
        try:
            r = requests.get(f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1", timeout=10)
            j = r.json()
            res = []
            if j.get("AbstractText"):
                res.append(f"DDG: {j.get('AbstractText
