import requests
import json
from bs4 import BeautifulSoup


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:0.8b"

OPTIONS = {
    "temperature": 1.0, # Qwen3.5 default; lower for more focused answers
    "top_p": 0.95,
    "top_k": 20, # Qwen3.5 default
    "num_ctx": 4096,
    "num_predict": 2512,
    "repeat_penalty": 1.5,
}

SYSTEM_PROMPT = (
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
MAX_TURNS = 10

def trim_history(history):
    system = [history[0]]
    dialog = history[1:]
    trimmed = dialog[-(MAX_TURNS * 2):]
    return system + trimmed

def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # Remove junk
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Try to get main content
    main = soup.find("main") or soup.find("article") or soup.body

    text = main.get_text(separator="\n", strip=True)

    return text

def chat(history):
    payload = {
        "model": MODEL,
        "messages": history,
        "options": OPTIONS,
        "stream": True,
        "think": False
    }
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    response.raise_for_status()

    full_reply = []
    print("Model: ", end="", flush=True)

    for line in response.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        token = chunk["message"]["content"]
        print(token, end="", flush=True)
        full_reply.append(token)
        if chunk.get("done"):
            break
    print()
    return "".join(full_reply)

def main():
    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    url = "https://en.wikipedia.org/wiki/Computer"
    html_content = fetch_html(url)

    html_content = html_content[:12000]

    prompt = f"Here is the full HTML of a webpage:\n\n{html_content}\n\nEvaluate its credibility."

    history.append({"role": "user", "content": prompt})

    reply = chat(history)
    history.append({"role": "assistant", "content": reply})



if __name__ == "__main__":
    main()




