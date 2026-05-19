import logging
import webbrowser
import subprocess
import platform
import re
from datetime import datetime
from typing import Optional, Callable, Dict

logger = logging.getLogger(__name__)

# 🗂️ Registry delle azioni: {intent: funzione}
_ACTIONS_REGISTRY: Dict[str, Callable[[str], Optional[str]]] = {}

def register_action(intent: str):
    """Decoratore per registrare automaticamente un'azione."""
    def decorator(func: Callable[[str], Optional[str]]):
        _ACTIONS_REGISTRY[intent] = func
        logger.debug(f"Azione registrata: '{intent}' → {func.__name__}")
        return func
    return decorator

# =============================================================================
# 🎯 AZIONI PREDEFINITE (decoratori = facile estensione)
# =============================================================================

@register_action("che_ora_e")
@register_action("ora")
def action_time(text: str) -> Optional[str]:
    """Restituisce l'orario corrente."""
    try:
        return f"Sono le {datetime.now().strftime('%H:%M')}."
    except Exception as e:
        logger.error(f"Errore in action_time: {e}")
        return None

@register_action("che_data_e")
@register_action("data")
def action_date(text: str) -> Optional[str]:
    """Restituisce la data corrente."""
    try:
        today = datetime.now()
        giorni = ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"]
        giorno_sett = giorni[today.weekday()]
        return f"Oggi è {giorno_sett}, {today.strftime('%d/%m/%Y')}."
    except Exception as e:
        logger.error(f"Errore in action_date: {e}")
        return None

@register_action("apri_google")
@register_action("cerca_google")
def action_google(text: str) -> Optional[str]:
    """Apre Google o esegue una ricerca."""
    try:
        # Estrai eventuale query di ricerca
        match = re.search(r"cerca\s+(.+)", text, re.I)
        url = f"https://google.com/search?q={match.group(1)}" if match else "https://google.com"
        webbrowser.open(url)
        return "Apro Google 🌐"
    except Exception as e:
        logger.error(f"Errore in action_google: {e}")
        return "Impossibile aprire Google."

@register_action("apri_youtube")
def action_youtube(text: str) -> Optional[str]:
    """Apre YouTube."""
    try:
        webbrowser.open("https://youtube.com")
        return "Apro YouTube ▶️"
    except Exception as e:
        logger.error(f"Errore in action_youtube: {e}")
        return "Impossibile aprire YouTube."

@register_action("apri_sito")
def action_open_site(text: str) -> Optional[str]:
    """Apre un sito web specifico (es. 'apri github')."""
    try:
        siti = {
            "github": "https://github.com",
            "spotify": "https://open.spotify.com",
            "gmail": "https://mail.google.com",
            "whatsapp": "https://web.whatsapp.com",
        }
        for nome, url in siti.items():
            if nome in text.lower():
                webbrowser.open(url)
                return f"Apro {nome.capitalize()} 🔗"
        return None  # Nessun sito riconosciuto → fallback
    except Exception as e:
        logger.error(f"Errore in action_open_site: {e}")
        return "Impossibile aprire il sito richiesto."

@register_action("spegni_pc")
def action_shutdown(text: str) -> Optional[str]:
    """Spegni il computer (conferma richiesta per sicurezza)."""
    if "conferma" not in text.lower() and "sì" not in text.lower():
        return "⚠️ Per spegnere il PC, di' 'spegni pc conferma'."
    try:
        system = platform.system()
        if system == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "10"], check=True)
        elif system == "Darwin":  # macOS
            subprocess.run(["osascript", "-e", 'tell application "Finder" to shut down'], check=True)
        else:  # Linux
            subprocess.run(["shutdown", "-h", "now"], check=True)
        return "Spegnimento in corso... 🌙"
    except Exception as e:
        logger.error(f"Errore in action_shutdown: {e}")
        return "Impossibile eseguire lo spegnimento."

@register_action("volume_su")
@register_action("volume_giu")
def action_volume(text: str) -> Optional[str]:
    """Regola il volume di sistema (richiede dipendenze OS-specific)."""
    try:
        system = platform.system()
        if "su" in text:
            step = "5%+" if system == "Windows" else "5%+"
        else:
            step = "5%-" if system == "Windows" else "5%-"
        
        if system == "Windows":
            # Richiede pycaw: pip install pycaw
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            current = volume.GetMasterVolumeLevelScalar()
            new_vol = max(0, min(1, current + (0.05 if "su" in text else -0.05)))
            volume.SetMasterVolumeLevelScalar(new_vol, None)
        else:
            # Fallback generico con pactl (Linux PulseAudio)
            cmd = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", step]
            subprocess.run(cmd, capture_output=True, check=True)
        
        return f"Volume {'aumentato' if 'su' in text else 'diminuito'} 🔊"
    except ImportError:
        return "Installa 'pycaw' per il controllo volume su Windows."
    except Exception as e:
        logger.error(f"Errore in action_volume: {e}")
        return "Impossibile regolare il volume."

# =============================================================================
# 🚀 FUNZIONE PRINCIPALE DI ROUTING
# =============================================================================

def run_actions(text: str, intent: str = "Default") -> Optional[str]:
    """
    Esegue l'azione associata all'intent rilevato.
    Fallback: cerca per keyword se l'intent non ha azioni registrate.
    """
    # 1. Prova routing diretto per intent
    if intent in _ACTIONS_REGISTRY:
        logger.info(f"Esecuzione azione per intent: '{intent}'")
        try:
            result = _ACTIONS_REGISTRY[intent](text)
            if result:
                return result
        except Exception as e:
            logger.error(f"Errore durante l'esecuzione di '{intent}': {e}")

    # 2. Fallback: matching per keyword (compatibilità con vecchi flussi)
    for registered_intent, func in _ACTIONS_REGISTRY.items():
        if registered_intent in text.lower():
            try:
                result = func(text)
                if result:
                    logger.info(f"Azione eseguita via keyword: '{registered_intent}'")
                    return result
            except Exception as e:
                logger.error(f"Errore fallback keyword '{registered_intent}': {e}")

    # 3. Nessuna azione trovata
    return None

# =============================================================================
# 🧪 UTILITÀ PER TESTING / ESTENSIONE
# =============================================================================

def list_available_actions() -> list:
    """Restituisce la lista degli intent supportati."""
    return list(_ACTIONS_REGISTRY.keys())

def add_custom_action(intent: str, func: Callable[[str], Optional[str]]):
    """Aggiunge un'azione personalizzata a runtime."""
    _ACTIONS_REGISTRY[intent] = func
    logger.info(f"Azione personalizzata aggiunta: '{intent}'")