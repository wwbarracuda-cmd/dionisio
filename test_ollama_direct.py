import requests

url = "http://localhost:11434/api/generate"
payload = {
    "model": "llama3.2:3b",
    "prompt": "Rispondi in una frase: come ti chiami?",
    "stream": False
}

print("🔄 Chiamata diretta a Ollama...")
try:
    response = requests.post(url, json=payload, timeout=120)
    result = response.json()
    print(f"✅ Risposta: {result.get('response', 'Nessuna risposta')}")
except Exception as e:
    print(f"❌ Errore: {e}")