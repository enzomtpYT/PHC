import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def ask_llm(prompt, model="llama3.2:1b"):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )

    if response.status_code == 200:
        return response.json()["response"]
    else:
        return f"Erreur Ollama: {response.text}"