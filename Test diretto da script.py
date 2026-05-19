# Test diretto da script
from voice import speak
from tts import TTS

if __name__ == "__main__":
    # Con caching + parametri Coqui
    speak("Benvenuto in DIONISIO! Come posso aiutarti oggi?", speed=1.1, pitch=2)
    
    # Fallback automatico in caso di errore
    speak("Ciao, questa è una prova di sintesi vocale.") # se fallisce → usa TTS