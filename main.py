# main.py
import logging
from brain import brain
from voice import speak, stop_speaking
from web_search import search_web
from stt import get_user_input
from utils import clean
from memory import load_memory, save_memory, get_recent_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("DIONISIO")

def main():
    memory = load_memory()
    memory.setdefault("log", [])
    memory.setdefault("profile", {})
    memory.setdefault("settings", {"use_mic": True})

    logger.info("🍇 DIONISIO AVVIATO (Async + Dinamico + Web)")
    speak("Dionisio attivo. Cosa posso fare per te?", async_play=False)

    try:
        while True:
            # 1️⃣ Input Utente
            user = get_user_input(use_mic=memory["settings"].get("use_mic", True))
            if not user:
                continue

            user = clean(user)
            logger.info(f"📥 Input: {user}")

            # 2️⃣ Comandi Rapidi
            cmd = user.lower()
            if cmd in ["stop", "esci", "quit", "spegni"]:
                stop_speaking()
                speak("Dionisio si spegne. Alla prossima.", async_play=False)
                break
            elif "microfono" in cmd:
                memory["settings"]["use_mic"] = "disattiva" not in cmd
                save_memory(memory)
                speak("Microfono " + ("attivato" if memory["settings"]["use_mic"] else "disattivato"))
                continue

            # 3️️ Interruzione Vocale (se DIONISIO sta parlando e l'utente interviene)
            stop_speaking()

            # 4️⃣ Routing: Web Search vs LLM
            web_keywords = ["meteo", "notizie", "news", "calendario", "oggi", "quanto costa", "chi ha vinto", "ultimo", "classifica"]
            is_web_query = any(kw in cmd for kw in web_keywords)

            if is_web_query:
                logger.info("🌐 Richiesta web rilevata...")
                speak("Un attimo, cerco sul web...")
                response = search_web(user)
            else:
                context = get_recent_context(memory, last_n=3)
                response = brain(user, context=context, memory=memory)

            logger.info(f"📤 Output: {response[:100]}...")
            
            # 5️️ Memoria
            memory["log"].append({"input": user, "output": response})
            if len(memory["log"]) > 1000:
                memory["log"] = memory["log"][-500:]
            save_memory(memory)

            # 6️️ Risposta Vocale (Async + Dinamica)
            speak(response, async_play=True)

    except KeyboardInterrupt:
        logger.warning("⏹️ Interruzione manuale (Ctrl+C)")
        stop_speaking()
        speak("Dionisio in standby.", async_play=False)
    except Exception as e:
        logger.error(f"❌ Errore critico: {e}", exc_info=True)
        stop_speaking()
        speak("Si è verificato un errore. Riavvia Dionisio.", async_play=False)

if __name__ == "__main__":
    main()