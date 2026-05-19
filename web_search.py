# web_search.py
import logging
from duckduckgo_search import DDGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_web(query: str, max_results: int = 3) -> str:
    """Cerca sul web e restituisce un riassunto ottimizzato per TTS."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region="it-it", safesearch="moderate", max_results=max_results))
        
        if not results:
            return "Non ho trovato risultati pertinenti online."

        # Estrae titoli e snippet, li unisce e li tronca per la sintesi vocale
        summary_parts = [f"{r['title']}: {r['body']}" for r in results[:2]]
        summary = " ".join(summary_parts)
        return (summary[:250] + "...") if len(summary) > 250 else summary
    except Exception as e:
        logger.error(f"❌ Errore ricerca web: {e}")
        return "Scusa, al momento non riesco a verificare online. Prova a riformulare."