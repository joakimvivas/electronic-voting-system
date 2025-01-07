# app/utils/token_index.py
import json
import os
import logging

TOKEN_INDEX_FILE = "tokens_index.json"
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")

# Reutilizamos las funciones de file_ops, pero solo usaremos "supabase" o "local"
from .file_ops import (
    supabase,
    _upload_to_supabase,
    _download_from_supabase
)

######### Lógica local #########
def _load_tokens_index_local() -> dict:
    if not os.path.isfile(TOKEN_INDEX_FILE):
        return {}
    with open(TOKEN_INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_tokens_index_local(data: dict):
    with open(TOKEN_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

######### Lógica supabase #########
def _load_tokens_index_supabase() -> dict:
    # Descargamos "tokens_index.json" del bucket
    content = _download_from_supabase("tokens_index.json")
    if not content:
        return {}
    # Asumiendo que 'content' son bytes
    return json.loads(content.decode("utf-8"))

def _save_tokens_index_supabase(data: dict):
    content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    _upload_to_supabase("tokens_index.json", content)

######### Interfaz principal #########
def load_tokens_index() -> dict:
    """
    Carga el tokens_index (local o supabase).
    """
    if STORAGE_BACKEND == "local":
        return _load_tokens_index_local()
    elif STORAGE_BACKEND == "supabase":
        return _load_tokens_index_supabase()
    else:
        raise ValueError(f"STORAGE_BACKEND desconocido o no soportado: {STORAGE_BACKEND}")

def save_tokens_index(data: dict):
    """
    Guarda el tokens_index (local o supabase).
    """
    if STORAGE_BACKEND == "local":
        _save_tokens_index_local(data)
    elif STORAGE_BACKEND == "supabase":
        _save_tokens_index_supabase(data)
    else:
        raise ValueError(f"STORAGE_BACKEND desconocido o no soportado: {STORAGE_BACKEND}")
