import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

# Wake word da rimuovere automaticamente (case-insensitive)
WAKE_WORDS = ["dionisio", "hey dionisio", "ok dionisio", "ascolta dionisio"]

def clean(text: str, remove_punct: bool = True, strip_wake: bool = True) -> str:
    """
    Pulisce e normalizza l'input testuale per il motore di Dionisio.
    """
    if not text or not text.strip():
        return ""

    # 1. Normalizzazione Unicode (evita caratteri nascosti o doppioni)
    text = unicodedata.normalize("NFKD", text)

    # 2. Minuscolo e trim
    text = text.lower().strip()

    # 3. Rimozione wake word (se presente all'inizio)
    if strip_wake:
        for wake in WAKE_WORDS:
            if text.startswith(wake):
                text = text[len(wake):].strip()
                break

    # 4. Rimozione punteggiatura (utile per matching intenti/keyword)
    if remove_punct:
        # In Python 3 \w include già lettere accentate e Unicode
        text = re.sub(r'[^\w\s]', '', text)

    # 5. Pulizia spazi multipli e finali
    text = re.sub(r'\s+', ' ', text).strip()

    return text
# Aggiungi in fondo a utils.py
from autocorrect import autocorrect, get_intent_hint

def clean(text: str, autocorrect_enabled: bool = True, **kwargs) -> str:
    """
    Pulizia testo con autocorrezione opzionale.
    """
    # ... [tutto il codice esistente di clean()] ...
    
    result = text  # dopo tutte le trasformazioni precedenti
    
    # ✅ Autocorrezione finale (opzionale)
    if autocorrect_enabled:
        result = autocorrect(result)
    
    return result