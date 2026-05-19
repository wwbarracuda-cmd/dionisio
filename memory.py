# memory.py
import json
import sqlite3
import os
from datetime import datetime
from pathlib import Path

MEMORY_FILE = "dionisio_memory.json"
DB_FILE = "dionisio.db"
USE_SQLITE = False  # Imposta True per usare SQLite invece di JSON


def _get_memory_path():
    """Restituisce il percorso assoluto per i file di memoria."""
    return Path(__file__).parent / MEMORY_FILE


def _get_db_path():
    """Restituisce il percorso per il database SQLite."""
    return Path(__file__).parent / DB_FILE


def load_memory():
    """Carica la memoria da JSON o SQLite."""
    if USE_SQLITE:
        return _load_sqlite()
    
    path = _get_memory_path()
    if not path.exists():
        return {"log": [], "profile": {}, "settings": {}}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Errore caricamento memoria: {e}. Creo nuovo file.")
        return {"log": [], "profile": {}, "settings": {}}


def save_memory(data):
    """Salva la memoria su JSON o SQLite."""
    if USE_SQLITE:
        return _save_sqlite(data)
    
    path = _get_memory_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Errore salvataggio memoria: {e}")
        return False


# === Opzionale: Backend SQLite per grandi volumi ===
def _init_sqlite():
    """Inizializza il database SQLite."""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_input TEXT,
            bot_output TEXT,
            metadata TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()


def _load_sqlite():
    """Carica memoria da SQLite (formato compatibile con JSON)."""
    _init_sqlite()
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    # Carica log conversazioni
    cursor.execute("SELECT timestamp, user_input, bot_output, metadata FROM conversations ORDER BY id DESC LIMIT 500")
    log = [
        {"timestamp": row[0], "input": row[1], "output": row[2], "metadata": json.loads(row[3]) if row[3] else {}}
        for row in cursor.fetchall()
    ]
    log.reverse()
    
    # Carica profilo
    cursor.execute("SELECT key, value FROM profile")
    profile = {row[0]: json.loads(row[1]) for row in cursor.fetchall()}
    
    conn.close()
    return {"log": log, "profile": profile, "settings": {}}


def _save_sqlite(data):
    """Salva memoria su SQLite."""
    _init_sqlite()
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    # Salva conversazioni
    for entry in data.get("log", []):
        cursor.execute(
            "INSERT INTO conversations (timestamp, user_input, bot_output, metadata) VALUES (?, ?, ?, ?)",
            (
                entry.get("timestamp", datetime.now().isoformat()),
                entry.get("input", ""),
                entry.get("output", ""),
                json.dumps(entry.get("metadata", {}), ensure_ascii=False)
            )
        )
    
    # Salva profilo
    for key, value in data.get("profile", {}).items():
        cursor.execute(
            "INSERT OR REPLACE INTO profile (key, value) VALUES (?, ?)",
            (key, json.dumps(value, ensure_ascii=False))
        )
    
    conn.commit()
    conn.close()
    return True


# === Utility per il contesto conversazionale ===
def get_recent_context(memory, last_n=5):
    """Restituisce gli ultimi N scambi per il contesto LLM."""
    log = memory.get("log", [])
    recent = log[-last_n:] if len(log) >= last_n else log
    return "\n".join([f"U: {e['input']}\nD: {e['output']}" for e in recent])


def add_to_profile(memory, key, value):
    """Aggiunge/aggiorna un dato nel profilo utente."""
    memory.setdefault("profile", {})[key] = value
    return memory


def get_setting(memory, key, default=None):
    """Recupera un'impostazione con fallback."""
    return memory.get("settings", {}).get(key, default)


def set_setting(memory, key, value):
    """Imposta un'opzione configurabile."""
    memory.setdefault("settings", {})[key] = value
    return memory