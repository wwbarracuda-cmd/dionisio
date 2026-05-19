import os
import uuid
import logging
from typing import Optional

# 🔍 Try/except per import dinamico (evita crash se il pkg manca)
try:
    from google.cloud import dialogflow_v2 as dialogflow
    from google.api_core.exceptions import GoogleAPIError, PermissionDenied, NotFound
    DIALOGFLOW_AVAILABLE = True
except ImportError:
    DIALOGFLOW_AVAILABLE = False
    logging.warning("⚠️ google-cloud-dialogflow non installato. Fallback locale attivo.")

from config import DIALOGFLOW_PROJECT_ID, GOOGLE_CREDENTIALS_PATH

logger = logging.getLogger(__name__)

# 🔐 Configurazione credenziali
if DIALOGFLOW_AVAILABLE and os.path.exists(GOOGLE_CREDENTIALS_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH

SESSION_ID = os.getenv("DIONISIO_SESSION_ID", f"dionisio-{uuid.uuid4().hex[:8]}")
LANGUAGE_CODE = "it-IT"

def detect_intent(text: str, session_id: Optional[str] = None) -> str:
    """
    Rileva l'intent da Dialogflow, con fallback locale se il SDK non è disponibile.
    """
    session_id = session_id or SESSION_ID
    
    # 🚫 Fallback immediato se Dialogflow non è configurato o disponibile
    if not DIALOGFLOW_AVAILABLE or DIALOGFLOW_PROJECT_ID in ["INSERISCI", "", None]:
        logger.debug("Dialogflow non disponibile → fallback locale")
        return _local_intent_fallback(text)
    
    try:
        session_client = dialogflow.SessionsClient()
        session_path = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
        
        text_input = dialogflow.TextInput(text=text, language_code=LANGUAGE_CODE)
        query_input = dialogflow.QueryInput(text=text_input)
        
        response = session_client.detect_intent(
            session=session_path,
            query_input=query_input
        )
        
        intent_name = response.query_result.intent.display_name if response.query_result.intent else "Default"
        confidence = response.query_result.intent_detection_confidence
        
        logger.info(f"Intent: '{intent_name}' (confidence: {confidence:.2%})")
        
        # Soglia confidenza minima
        if confidence < 0.4:
            return "Default"
            
        return intent_name
        
    except PermissionDenied:
        logger.error("❌ Permesso negato: verifica service_account.json")
        return "Default"
    except NotFound:
        logger.error(f"❌ Progetto non trovato: {DIALOGFLOW_PROJECT_ID}")
        return "Default"
    except GoogleAPIError as e:
        logger.error(f"❌ Errore API: {e}")
        return "Default"
    except Exception as e:
        logger.error(f"❌ Errore imprevisto: {type(e).__name__}: {e}")
        return "Default"


def _local_intent_fallback(text: str) -> str:
    """Fallback locale con matching keyword quando Dialogflow non è disponibile."""
    text_lower = text.lower()
    
    intent_map = {
        "ora": "che_ora_e",
        "che ore": "che_ora_e",
        "data": "che_data_e",
        "oggi": "che_data_e",
        "google": "cerca_google",
        "youtube": "apri_youtube",
        "apri sito": "apri_sito",
        "meteo": "richiedi_meteo",
        "spegni": "spegni_pc",
        "volume": "volume_su" if "su" in text_lower or "alto" in text_lower else "volume_giu",
    }
    
    for keyword, intent in intent_map.items():
        if keyword in text_lower:
            logger.debug(f"Fallback: '{keyword}' → '{intent}'")
            return intent
    
    return "Default"


def reset_session(session_id: Optional[str] = None):
    """Resetta la sessione corrente."""
    global SESSION_ID
    SESSION_ID = session_id or f"dionisio-{uuid.uuid4().hex[:8]}"
    logger.info(f"🔄 Sessione resettata: {SESSION_ID}")
    return SESSION_ID