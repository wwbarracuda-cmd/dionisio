# voice.py
import os
import logging
import subprocess
import shutil
import platform
import threading
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from config import VOICE_FILE
except ImportError:
    VOICE_FILE = "output.mp3"

# Cache modello TTS e stato riproduzione
_tts_model = None
_playback_process = None
_speak_lock = threading.Lock()

def _analyze_text(text: str):
    """Modula speed/pitch in base a struttura ed enfasi del testo."""
    speed, pitch = 1.0, 0
    if text.strip().endswith('?'):
        pitch = 3  # Inflessione interrogativa
    if re.search(r'!\s*$', text) or re.search(r'[A-Z]{3,}', text):
        speed, pitch = 1.15, 2  # Enfasi/esclamazione
    if '...' in text or any(w in text.lower() for w in ['lentamente', 'pausa', 'con calma']):
        speed, pitch = 0.85, -1
    return speed, pitch

def stop_speaking():
    """Interrompe immediatamente la riproduzione audio in corso."""
    global _playback_process
    with _speak_lock:
        if _playback_process and _playback_process.poll() is None:
            logger.info("⏹️ Interruzione vocale attivata")
            try:
                _playback_process.terminate()
                _playback_process.wait(timeout=2)
            except Exception:
                pass
            finally:
                _playback_process = None

def _get_tts_model():
    global _tts_model
    if _tts_model is None:
        from TTS.api import TTS
        logger.info("🔄 Caricamento modello Coqui TTS in memoria...")
        _tts_model = TTS(model_name="tts_models/it/mai_female/vits", progress_bar=False)
    return _tts_model

def speak(text: str, speed: float = None, pitch: int = None, use_cuda: bool = False, async_play: bool = True):
    """Funzione principale con controllo dinamico e modalità async."""
    if not text or not text.strip():
        return

    # Calcola parametri dinamici se non forniti esplicitamente
    if speed is None or pitch is None:
        dyn_speed, dyn_pitch = _analyze_text(text)
        speed = speed if speed is not None else dyn_speed
        pitch = pitch if pitch is not None else dyn_pitch

    if async_play:
        # Esecuzione in background (non bloccante)
        target = threading.Thread(target=_generate_and_play, args=(text, speed, pitch, use_cuda), daemon=True)
        target.start()
    else:
        # ✅ FIX: Esecuzione sincrona diretta (senza thread)
        _generate_and_play(text, speed, pitch, use_cuda)

def _generate_and_play(text: str, speed: float, pitch: int, use_cuda: bool):
    global _playback_process
    output_path = VOICE_FILE.replace(".mp3", "_coqui.wav")
    try:
        tts = _get_tts_model()
        device = "cuda" if (use_cuda and _is_gpu_available()) else "cpu"
        tts.to(device)

        try:
            tts.tts_to_file(text=text, file_path=output_path, speed=speed, pitch=pitch)
        except TypeError:
            tts.tts_to_file(text=text, file_path=output_path)

        logger.info(f"✅ Audio pronto: {output_path} (s={speed}, p={pitch})")
        _playback_audio(output_path)
    except Exception as e:
        logger.error(f"❌ Errore generazione voce: {e}")
        _fallback_speak(text)
    finally:
        # Pulizia file temporaneo
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception as e:
            logger.debug(f"Cleanup temporaneo fallito: {e}")

def _is_gpu_available():
    try:
        import torch
        return torch.cuda.is_available()
    except: 
        return False

def _playback_audio(filepath: str):
    global _playback_process
    system = platform.system()
    cmd = []
    
    if system == "Darwin":
        cmd = ["afplay", filepath]
    elif system == "Windows":
        # Player killabili per stop_speaking() funzionante
        for player in ["mpv", "ffplay", "vlc"]:
            if shutil.which(player):
                cmd = [player, filepath, "--no-video"]
                break
        if not cmd:
            cmd = ["cmd", "/c", "start", "", filepath]  # Fallback (non killabile)
    else:
        for player in ["mpv", "ffplay", "mpg123", "vlc"]:
            if shutil.which(player):
                cmd = [player, filepath]
                break

    if not cmd:
        logger.warning("⚠️ Nessun player audio trovato. Installa `mpv` o `ffplay`.")
        return

    try:
        with _speak_lock:
            _playback_process = subprocess.Popen(cmd, shell=(system == "Windows" and not any(p in cmd[0] for p in ["mpv", "ffplay", "vlc"])))
            _playback_process.wait()
            _playback_process = None
    except Exception as e:
        logger.error(f"❌ Errore riproduzione: {e}")

def _fallback_speak(text: str):
    try:
        from gtts import gTTS
        out = VOICE_FILE.replace(".mp3", "_fallback.wav")
        gTTS(text=text, lang="it").save(out)
        _playback_audio(out)
    except: pass