# tts_cache.py
import os
import hashlib
import logging
from functools import wraps
from config import VOICE_FILE, CACHE_DIR

logger = logging.getLogger(__name__)

os.makedirs(CACHE_DIR, exist_ok=True)

def _get_text_hash(text: str, engine: str, **kwargs) -> str:
    """Genera un hash univoco per testo + parametri."""
    params = f"{text}|{engine}|{sorted(kwargs.items())}"
    return hashlib.md5(params.encode("utf-8")).hexdigest()

def tts_cache(func):
    """Decoratore per caching dei file audio generati."""
    @wraps(func)
    def wrapper(text: str, engine: str = "gtts", **kwargs):
        cache_key = _get_text_hash(text, engine, **kwargs)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.{'wav' if engine == 'coqui' else 'mp3'}")
        
        # ✅ Se esiste in cache, restituisci subito
        if os.path.exists(cache_path):
            logger.info(f"📦 Cache hit: {cache_path}")
            return cache_path
        
        # ❌ Altrimenti genera e salva in cache
        logger.info(f"🎙️ Generazione audio ({engine}) per: '{text[:50]}...'")
        output_path = func(text, engine=engine, **kwargs)
        
        # Copia in cache con nome hash
        if output_path and os.path.exists(output_path):
            shutil.copy2(output_path, cache_path)
            logger.info(f"💾 Salvato in cache: {cache_path}")
        
        return output_path
    return wrapper