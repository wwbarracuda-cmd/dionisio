# stt.py
import logging
import os
import platform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configura le dipendenze opzionali
SPEECH_RECOGNITION_AVAILABLE = False
PYAUDIO_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ speech_recognition non installato: pip install SpeechRecognition")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ pyaudio non installato: pip install pyaudio")


def listen_microphone(timeout=5, phrase_time_limit=10, language="it-IT"):
    """
    Ascolta dal microfono e restituisce il testo riconosciuto.
    
    Args:
        timeout: secondi di silenzio prima di timeout
        phrase_time_limit: durata massima della frase
        language: codice lingua (es. "it-IT", "en-US")
    
    Returns:
        str o None se non riconosciuto
    """
    if not SPEECH_RECOGNITION_AVAILABLE or not PYAUDIO_AVAILABLE:
        logger.error("❌ Dipendenze STT mancanti. Installa: pip install SpeechRecognition pyaudio")
        return None
    
    recognizer = sr.Recognizer()
    
    # Ottimizzazioni per italiano
    recognizer.energy_threshold = 300  # Sensibilità
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    
    try:
        with sr.Microphone() as source:
            logger.info("🎙️ Ascolto in corso... (parla ora)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            audio = recognizer.listen(
                source, 
                timeout=timeout, 
                phrase_time_limit=phrase_time_limit
            )
            
            # Riconoscimento con Google Web Speech API (gratis, offline fallback)
            text = recognizer.recognize_google(audio, language=language)
            logger.info(f"✅ Riconosciuto: '{text}'")
            return text
            
    except sr.WaitTimeoutError:
        logger.warning("⏱️ Timeout: nessun audio rilevato")
    except sr.UnknownValueError:
        logger.warning("❓ Audio non comprensibile")
    except sr.RequestError as e:
        logger.error(f"🌐 Errore servizio riconoscimento: {e}")
    except Exception as e:
        logger.error(f"❌ Errore STT: {e}")
    
    return None


def listen_keyboard_fallback():
    """Fallback: input da tastiera con prompt vocale."""
    from voice import speak
    speak("Ti ascolto. Parla o digita e premi Invio.")
    try:
        text = input("🧑 Tu (o parla): ").strip()
        return text if text else None
    except KeyboardInterrupt:
        return None


def get_user_input(use_mic=True):
    """
    Funzione unificata: prova microfono, fallback tastiera.
    
    Args:
        use_mic: se False, salta direttamente al fallback
    
    Returns:
        str o None
    """
    if use_mic and SPEECH_RECOGNITION_AVAILABLE and PYAUDIO_AVAILABLE:
        result = listen_microphone()
        if result:
            return result
        logger.info("🔄 Fallback a input da tastiera...")
    
    return listen_keyboard_fallback()