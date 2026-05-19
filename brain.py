# brain.py - Versione definitiva corretta
import logging
import os
import json
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURAZIONE LLM
# =============================================================================
LLM_BACKEND = os.getenv("DIONISIO_LLM", "ollama").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "local-model")

# ✅ SYSTEM PROMPT (ESSENZIALE - NON RIMUOVERE)
SYSTEM_PROMPT = """Sei DIONISIO, un assistente vocale intelligente, utile e amichevole.
- Rispondi in italiano, in modo naturale e conciso (max 2-3 frasi per risposta vocale).
- Se non sai qualcosa, ammettilo con gentilezza.
- Mantieni un tono cordiale ma professionale.
- Ricorda il contesto della conversazione.
- Non inventare fatti: se incerto, chiedi chiarimenti.
"""

# =============================================================================
# FUNZIONE PRINCIPALE
# =============================================================================
def brain(user_input: str, context: str = "", memory: dict = None) -> str:
    prompt = _build_prompt(user_input, context, memory)
    
    try:
        if LLM_BACKEND == "openai" and OPENAI_API_KEY:
            return _query_openai(prompt)
        elif LLM_BACKEND == "ollama":
            return _query_ollama(prompt)
        elif LLM_BACKEND == "lmstudio":
            return _query_lmstudio(prompt)
        else:
            logger.warning(f"⚠️ Backend '{LLM_BACKEND}' non configurato. Uso fallback.")
            return _fallback_response(user_input, context, memory)
    except Exception as e:
        logger.error(f"❌ Errore LLM ({LLM_BACKEND}): {e}")
        return _fallback_response(user_input, context, memory, error=True)

# =============================================================================
# BACKEND: OpenAI API
# =============================================================================
def _query_openai(prompt: str) -> str:
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    reply = response.choices[0].message.content.strip()
    logger.info(f"🤖 OpenAI → {reply[:80]}...")
    return reply

# =============================================================================
# BACKEND: Ollama
# =============================================================================
def _query_ollama(prompt: str) -> str:
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nUtente: {prompt}\nDionisio:",
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 150}
    }
    response = requests.post(url, json=payload, timeout=200)
    response.raise_for_status()
    result = response.json()
    reply = result.get("response", "").strip()
    logger.info(f"🤖 Ollama → {reply[:80]}...")
    return reply or "Scusa, non ho capito. Puoi ripetere?"

# =============================================================================
# BACKEND: LM Studio
# =============================================================================
def _query_lmstudio(prompt: str) -> str:
    url = f"{LMSTUDIO_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY or 'not-needed'}"}
    payload = {
        "model": LMSTUDIO_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    response = requests.post(url, json=payload, headers=headers, timeout=200)
    response.raise_for_status()
    result = response.json()
    reply = result["choices"][0]["message"]["content"].strip()
    logger.info(f"🤖 LM Studio → {reply[:80]}...")
    return reply

# =============================================================================
# FALLBACK
# =============================================================================
def _fallback_response(user_input: str, context: str = "", memory: dict = None, error: bool = False) -> str:
    text = user_input.lower()
    if any(k in text for k in ["ciao", "salve", "buongiorno"]):
        return "Ciao! Come posso aiutarti oggi?"
    elif any(k in text for k in ["come stai", "tutto bene"]):
        return "Tutto bene, grazie! E tu, come va?"
    elif any(k in text for k in ["nome", "chi sei", "ti chiami"]):
        return "Sono DIONISIO, il tuo assistente vocale intelligente."
    elif any(k in text for k in ["grazie", "grazie mille"]):
        return "Di nulla! Sono qui per aiutarti."
    elif any(k in text for k in ["addio", "arrivederci", "a dopo"]):
        return "Alla prossima! Fai buon uso della tecnologia."
    elif error:
        return "Scusa, ho avuto un problema tecnico. Riprova tra un momento."
    else:
        return f"Ho ricevuto: '{user_input}'. Sto imparando a rispondere meglio!"

# =============================================================================
# UTILITIES
# =============================================================================
def _build_prompt(user_input: str, context: str = "", memory: dict = None) -> str:
    prompt_parts = []
    if context:
        prompt_parts.append(f"Contesto recente:\n{context}\n")
    if memory and memory.get("profile"):
        profile = memory["profile"]
        if profile.get("name"):
            prompt_parts.append(f"L'utente si chiama {profile.get('name')}.")
        if profile.get("preferences"):
            prompt_parts.append(f"Preferenze utente: {profile.get('preferences')}")
        prompt_parts.append("")
    prompt_parts.append(f"Domanda: {user_input}")
    return "\n".join(prompt_parts).strip()

def extract_intent(text: str) -> str:
    text = text.lower().strip()
    intents = {
        "greeting": ["ciao", "salve", "buongiorno", "buonasera"],
        "farewell": ["addio", "arrivederci", "a dopo", "ci vediamo"],
        "thanks": ["grazie", "grazie mille", "ti ringrazio"],
        "help": ["aiuto", "help", "cosa puoi fare", "comandi"],
        "name": ["come ti chiami", "chi sei", "il tuo nome"],
        "weather": ["meteo", "che tempo fa", "previsioni"],
        "time": ["che ore sono", "ora", "orario"],
    }
    for intent, keywords in intents.items():
        if any(kw in text for kw in keywords):
            return intent
    return "unknown"