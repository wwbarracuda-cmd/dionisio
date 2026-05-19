import os
import logging
from pathlib import Path

# 📁 Directory base del progetto (funziona su Colab, Linux, Windows, macOS)
BASE_DIR = Path(__file__).parent.resolve()

# 🔑 API Keys & Project IDs (letti da env var, vuoti di default)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID", "")

# 🌐 Google Cloud Credentials
GOOGLE_CREDENTIALS_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(BASE_DIR / "service_account.json")
)

# 💾 File di progetto
MEMORY_FILE = str(BASE_DIR / "memory.json")
VOICE_FILE  = str(BASE_DIR / "voice.mp3")
COQUI_MODEL = "tts_models/en/ljspeech/tacotron2-DDC"
CACHE_DIR = "tts_cache"  # Cartella per i file audio cachati

# 🔇 Check configurazione silenzioso (usa DEBUG, non spammerà la console)
logger = logging.getLogger("Dionisio.config")

if not OPENAI_API_KEY:
    logger.debug("OpenAI: non configurato → disabilitato")
if not DIALOGFLOW_PROJECT_ID:
    logger.debug("Dialogflow: non configurato → fallback locale attivo")
if not Path(GOOGLE_CREDENTIALS_PATH).exists():
    logger.debug(f"Credenziali Google: file non trovato in {GOOGLE_CREDENTIALS_PATH}")