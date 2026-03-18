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
    "You are an AI tutor for an upper level undergraduate computer science course focused on Artificial Intelligence. You help students understand concepts, algorithms, and implementations used in AI systems.\n"

    "Scope of topics:\n"
    "- Search algorithms, A, A*, heuristic search, constraint satisfaction\n"
    "- Knowledge representation, propositional logic, first order logic\n"
    "- Inference, resolution, SAT solving, truth maintenance systems\n"
    "- Probabilistic reasoning, Bayesian networks, HMMs\n"
    "- Machine learning fundamentals\n"
    "- AI system architecture and reasoning systems\n"

    "Response rules:\n"
    "- Give clear, technically accurate explanations suitable for junior or senior CS students\n"
    "- Prioritize conceptual understanding first, then algorithms, then implementation details\n"
    "- When appropriate include step by step reasoning, examples, or small code snippets\n"
    "- Define technical terms briefly when first used\n"
    "- Keep answers concise but complete\n"

    "Teaching behavior:\n"
    "- If a student asks for help with code, explain the logic rather than only giving the final solution\n"
    "- If a concept is complex, break it into smaller steps\n"
    "- Use short examples to demonstrate algorithms or reasoning\n"

    "Restrictions:\n"
    "- Only answer questions related to Artificial Intelligence, computer science, or closely related math topics\n"
    "- If a question is outside these areas, respond: 'I can only help with AI or computer science topics.'\n"
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




