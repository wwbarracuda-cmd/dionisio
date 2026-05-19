"""
autocorrect.py - Autocorrezione intelligente per DIONISIO
Supporta: spellchecking, fuzzy matching, dizionario personalizzato, contesto
"""
import re
import logging
from typing import Optional, List, Dict
from difflib import get_close_matches

# ✅ Opzionale: pyspellchecker per correzione ortografica avanzata
try:
    from spellchecker import SpellChecker
    SPELLCHECKER_AVAILABLE = True
except ImportError:
    SPELLCHECKER_AVAILABLE = False
    logging.getLogger(__name__).debug("pyspellchecker non installato → fallback base attivo")

logger = logging.getLogger(__name__)

# 📚 Dizionario personalizzato (termini tecnici, nomi propri, comandi)
CUSTOM_DICT = {
    # Correzioni comuni italiano
    "ore": "ore", "ora": "ora", "dati": "data", "dat": "data",
    "googel": "google", "youtub": "youtube", "spotifay": "spotify",
    "dionisio": "dionisio", "dioniso": "dionisio", "jonisio": "dionisio",
    "apri": "apri", "aprire": "apri", "chiudi": "chiudi", "spegni": "spegni",
    "volume": "volume", "volome": "volume", "volune": "volume",
    "meteo": "meteo", "meto": "meteo", "che ore": "che ore",
    # Nomi propri / luoghi (es. per comandi meteo)
    "roma": "roma", "milano": "milano", "napoli": "napoli",
    "firenze": "firenze", "torino": "torino",
}

# 🎯 Keyword per intent recognition (usate per fuzzy matching)
INTENT_KEYWORDS = {
    "che_ora_e": ["ora", "ore", "orario", "che ore", "quante ore"],
    "che_data_e": ["data", "oggi", "giorno", "che giorno", "che data"],
    "cerca_google": ["google", "cerca", "cerca su google", "googla"],
    "apri_youtube": ["youtube", "yt", "video", "guarda youtube"],
    "apri_sito": ["apri", "sito", "vai su", "visita"],
    "richiedi_meteo": ["meteo", "tempo", "previsioni", "che tempo fa"],
    "spegni_pc": ["spegni", "shutdown", "arresta", "spegni pc"],
    "volume_su": ["volume su", "alza volume", "più alto", "volume +"],
    "volume_giu": ["volume giù", "abbassa volume", "più basso", "volume -"],
}

class AutoCorrector:
    """Motore di autocorrezione contestuale per DIONISIO."""
    
    def __init__(self, language: str = "it", max_distance: int = 2):
        self.language = language
        self.max_distance = max_distance  # Soglia per fuzzy matching
        self.spell = SpellChecker(language=language) if SPELLCHECKER_AVAILABLE else None
        
    def normalize(self, text: str) -> str:
        """Normalizzazione base: minuscolo, spazi, caratteri speciali."""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)  # Spazi multipli → singolo
        text = re.sub(r'[^\w\sàèéìòù]', '', text)  # Mantieni accentate italiane
        return text.strip()
    
    def apply_custom_dict(self, text: str) -> str:
        """Applica correzioni dal dizionario personalizzato."""
        words = text.split()
        corrected = []
        for word in words:
            # Priorità: dizionario custom > spellchecker > originale
            if word in CUSTOM_DICT:
                corrected.append(CUSTOM_DICT[word])
            elif self.spell and word not in self.spell.known([word]):
                # Correzione spellchecker (solo se parola sconosciuta)
                candidates = self.spell.candidates(word)
                if candidates:
                    best = self._rank_candidates(word, list(candidates))
                    corrected.append(best if best else word)
                else:
                    corrected.append(word)
            else:
                corrected.append(word)
        return ' '.join(corrected)
    
    def _rank_candidates(self, original: str, candidates: List[str]) -> Optional[str]:
        """Ranking intelligente: preferisce parole nel dizionario intenti."""
        # 1. Priorità a keyword di intent riconosciute
        all_intent_words = set(w for words in INTENT_KEYWORDS.values() for w in words)
        for cand in candidates:
            if cand in all_intent_words:
                return cand
        
        # 2. Fallback: più simile per edit distance
        return get_close_matches(original, candidates, n=1, cutoff=0.6)[0] if candidates else None
    
    def fuzzy_intent_match(self, text: str) -> Optional[str]:
        """Riconosce l'intent anche con input imperfetto (fuzzy matching)."""
        text_norm = self.normalize(text)
        
        for intent, keywords in INTENT_KEYWORDS.items():
            for kw in keywords:
                # Matching esatto
                if kw in text_norm:
                    return intent
                # Fuzzy matching per keyword corte (< 5 char)
                if len(kw) < 5:
                    matches = get_close_matches(kw, [text_norm], n=1, cutoff=0.7)
                    if matches:
                        return intent
        return None
    
    def correct(self, text: str, context: Optional[Dict] = None) -> Dict[str, any]:
        """
        Corregge il testo e restituisce metadati utili.
        
        Returns:
            {
                "original": str,      # Input originale
                "corrected": str,     # Testo corretto
                "intent_hint": str,   # Intent suggerito (o None)
                "was_corrected": bool # Se è stata applicata una correzione
            }
        """
        original = text
        normalized = self.normalize(original)
        
        # Applica dizionario custom + spellchecker
        corrected = self.apply_custom_dict(normalized)
        
        # Rileva intent anche da testo corretto
        intent_hint = self.fuzzy_intent_match(corrected)
        
        was_corrected = (normalized != corrected)
        
        if was_corrected:
            logger.debug(f"Autocorrezione: '{original}' → '{corrected}' [intent: {intent_hint}]")
        
        return {
            "original": original,
            "corrected": corrected,
            "intent_hint": intent_hint,
            "was_corrected": was_corrected
        }

# 🎯 Istanza globale pronta all'uso
autocorrector = AutoCorrector()

def autocorrect(text: str, context: Optional[Dict] = None) -> str:
    """Funzione wrapper semplice: restituisce solo il testo corretto."""
    return autocorrector.correct(text, context)["corrected"]

def get_intent_hint(text: str) -> Optional[str]:
    """Ottieni un suggerimento di intent senza correggere il testo."""
    return autocorrector.fuzzy_intent_match(text)