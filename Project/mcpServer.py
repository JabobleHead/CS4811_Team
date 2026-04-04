from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:0.8b"

# -------------------------
# Helper: fetch + clean HTML
# -------------------------
def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(response.content, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body
    return main.get_text(separator="\n", strip=True)[:500]

# -------------------------
# Helper: LLM credibility
# -------------------------
def ai_credibility(text):
    prompt = f"Evaluate credibility:\n\n{text}"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Return JSON with score and verdict"},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "think": False
    }

    res = requests.post(OLLAMA_URL, json=payload, timeout=60)
    data = res.json()

    try:
        content = data["message"]["content"]
        parsed = json.loads(content)
        verdict = parsed.get("verdict", "uncertain").lower()
        if "highly credible" in verdict or verdict == "credible":
            parsed["score"] = max(parsed.get("score", 0), 80)
        elif "uncertain" in verdict:
            parsed["score"] = max(parsed.get("score", 0), 50)
        return parsed
    except:
        return {"score": 50, "verdict": "uncertain"}

# -------------------------
# Symbolic rule layer
# -------------------------
def symbolic_score(domain, ai_score):
    score = ai_score  # base: 0-100 from AI

    if domain.endswith(".gov"):
        score += 20
    elif domain.endswith(".edu"):
        score += 15
    elif domain.endswith(".org"):
        score += 5

    score = min(score, 100)

    return {
        "final_score": score,
        "credible": score >= 60
    }

# -------------------------
# MCP Tool
# -------------------------
@app.route("/tool/evaluate_source", methods=["POST"])
def evaluate_source():
    data = request.json
    url = data.get("url")

    try:
        text = fetch_html(url)

        ai_result = ai_credibility(text)

        domain = urlparse(url).netloc

        symbolic = symbolic_score(domain, ai_result["score"])

        return jsonify({
            "success": True,
            "data": {
                "url": url,
                "ai_score": ai_result["score"],
                "ai_verdict": ai_result["verdict"],
                "domain": domain,
                "final_score": symbolic["final_score"],
                "credible": symbolic["credible"]
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


if __name__ == "__main__":
    app.run(port=8080)
