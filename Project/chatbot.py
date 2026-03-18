import requests
import json
import utilities as util

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
    "Always cite at least one source for every claim or piece of information you provide. Sources must be:\n" 

"- **Relevant**: directly related to the specific output or claim being made\n" 
"- **Specific**: include the source name, author (if known), and URL or publication where applicable\n" 
"- **Honest**: if you are uncertain whether a source exists or are working from training data rather than a live search, clearly state that (e.g., \"Based on my training data, a relevant reference is...\") — never fabricate citations\n" 

"For every response, you MUST end with a source block in this exact format:\n\n" 
    "SOURCE:\n" 
    "URL: <paste full URL here>\n" 
    "Title: <article or page title>\n" 
    "Publisher: <domain or organizaion name>\n" 
    "Supports: <one sentence describing what claim this source backs>\n\n" 
    "Hard rules:\n" 
    "- The URL field is mandatory. Never leave it blank or use placeholder text.\n" 
    "- Only use real, publicly accessible URLs (no paywalled or login-required pages).\n" 
    "- If you cannot find a real URL for a claim, do not make that claim.\n" 
    "- Do not fabricate URLs. If uncertain, say 'No verified source available' " 
    "and omit the claim instead.\n" 
    "- The URL must begin with https://\n" 

"If no reliable source can be identified for a claim, explicitly say so rather than inventing one." 
)
MAX_TURNS = 10

def trim_history(history):
    system = [history[0]]
    dialog = history[1:]
    trimmed = dialog[-(MAX_TURNS * 2):]
    return system + trimmed


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
    print("CS4811 AI Tutor ready. Type 'quit' to exit.")
    print("-" * 60)
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Goodbye!")
            break
        if not user_input:
            continue
        history.append({"role": "user", "content": user_input})
        history = trim_history(history)
        reply = chat(history)
        history.append({"role": "assistant", "content": reply})
        print("-" * 60)



if __name__ == "__main__":
    main()




