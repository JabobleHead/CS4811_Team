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

# --------------------- ----
# Helper: LLM credibility
# -------------------------
def ai_credibility(text):
    system = (
    "You are an AI system that evaluates the credibility of a webpage using ONLY the provided content.\n\n"


    "EVALUATION CRITERIA:\n"
    "1. Authorship: named author, credentials, or organization\n"
    "2. Evidence: citations, references, or links supporting claims\n"
    "3. Tone: neutral/objective vs emotional/sensational\n"
    "4. Clarity: logical structure and internal consistency\n"
    "5. Support: whether claims are explained or justified within the text\n\n"

    "LENIENCY RULE:\n"
    "- If evidence is limited, prefer 'uncertain' rather than 'not credible'.\n"
    "- Do not heavily penalize simple or informational pages.\n\n"

    "SCORING GUIDELINES:\n"
    "- 80–100: Strong credibility signals present\n"
    "- 50–79: Some positive signals, but incomplete\n"
    "- 30–49: Weak or unclear credibility\n"
    "- 0–29: Clear negative signals or misleading content\n\n"

    "OUTPUT FORMAT (strict JSON):\n"
    'do not include reasoning in the final credibility output, just score and verdict'
    '  "score": number,\n'
    '  "verdict": "credible" | "uncertain" | "not credible",\n'

    "Only include information that is directly supported by the provided text."
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Evaluate this webpage content:\n\n{text}"}
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
    except Exception:
        return {"score": 50, "verdict": "uncertain"}

# -------------------------
# Symbolic rule layer
# -------------------------
def symbolic_score(domain, ai_score):
    score = ai_score  # base: 0-100 from AI

    if domain.endswith(".gov"):
        score = max(score, 85)
    elif domain.endswith(".edu"):
        score = max(score, 80)
    elif domain.endswith(".org"):
        score = max(score, 65)

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
