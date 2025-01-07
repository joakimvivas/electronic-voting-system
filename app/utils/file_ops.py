# app/utils/file_ops.py

import json
import os
from typing import Any
import logging

from .encrypt import encrypt_data, decrypt_data

# Supabase
from supabase import create_client, Client

######### Variables de entorno #########
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
SUPABASE_URL = os.getenv("SUPABASE_SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_SUPABASE_ANON_KEY", "")
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "votaciones-enc")

######### Cliente de Supabase (si las vars están definidas) #########
supabase: Client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    if STORAGE_BACKEND == "supabase":
        logging.warning("ATENCIÓN: STORAGE_BACKEND=supabase, pero SUPABASE_URL/KEY no están configuradas.")
        # supabase seguirá siendo None, lo que generará un error si se intenta usar

######### Lógica local #########
VOTACIONES_DIR = "votaciones"

def _save_voting_file_local(voting_id: str, encrypted_data: bytes):
    """
    Guarda el fichero encriptado localmente en votaciones/<voting_id>.enc
    """
    if not os.path.exists(VOTACIONES_DIR):
        os.makedirs(VOTACIONES_DIR)

    file_path = os.path.join(VOTACIONES_DIR, f"{voting_id}.enc")
    with open(file_path, "wb") as f:
        f.write(encrypted_data)

def _load_voting_file_local(voting_id: str) -> bytes:
    """
    Lee el fichero encriptado localmente.
    """
    file_path = os.path.join(VOTACIONES_DIR, f"{voting_id}.enc")
    if not os.path.isfile(file_path):
        raise FileNotFoundError("No existe el fichero de votación local")
    with open(file_path, "rb") as f:
        return f.read()

######### Lógica con Supabase #########
def _upload_to_supabase(filename: str, data: bytes) -> None:
    """
    Sube 'data' (bytes) al bucket de Supabase con la 'key' = filename.
    """
    if not supabase:
        raise RuntimeError("Supabase client no inicializado o variables de entorno no configuradas.")
    
    response = supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(filename, data)
    if "error" in response and response["error"]:
        raise RuntimeError(f"Error subiendo a Supabase: {response['error']}")

def _download_from_supabase(filename: str) -> bytes:
    """
    Descarga bytes desde el bucket de Supabase.
    Retorna b'' si no existe.
    """
    if not supabase:
        raise RuntimeError("Supabase client no inicializado o variables de entorno no configuradas.")
    
    try:
        content = supabase.storage.from_(SUPABASE_BUCKET_NAME).download(filename)
        # Según la versión de supabase-py, 'download' puede retornar directamente bytes o un objeto
        if not content:
            return b""
        # 'content' podría ser bytes o un objeto con .decode() 
        # Ajusta si tu versión maneja la respuesta diferente.
        return content
    except Exception as e:
        logging.warning(f"No se pudo descargar {filename} desde Supabase. Error: {e}")
        return b""

######### Funciones principales #########
def save_voting_file(voting_id: str, voting_data: dict, key: bytes):
    """
    Guarda (encripta) un dict JSON en:
    - modo local (carpeta votaciones/)
    - modo supabase (bucket)
    según STORAGE_BACKEND.
    """
    raw_json = json.dumps(voting_data).encode("utf-8")
    encrypted_data = encrypt_data(raw_json, key)

    if STORAGE_BACKEND == "local":
        _save_voting_file_local(voting_id, encrypted_data)
    elif STORAGE_BACKEND == "supabase":
        filename = f"{voting_id}.enc"
        _upload_to_supabase(filename, encrypted_data)
    else:
        raise ValueError(f"STORAGE_BACKEND desconocido o no soportado: {STORAGE_BACKEND}")

def load_voting_file(voting_id: str, key: bytes) -> dict:
    """
    Carga y desencripta el fichero de votación (local o supabase).
    Retorna un dict con el contenido JSON.
    """
    if STORAGE_BACKEND == "local":
        encrypted_content = _load_voting_file_local(voting_id)
    elif STORAGE_BACKEND == "supabase":
        filename = f"{voting_id}.enc"
        encrypted_content = _download_from_supabase(filename)
        if not encrypted_content:
            raise FileNotFoundError("No existe el fichero de votación en Supabase.")
    else:
        raise ValueError(f"STORAGE_BACKEND desconocido o no soportado: {STORAGE_BACKEND}")

    # Desencripta
    decrypted_bytes = decrypt_data(encrypted_content, key)
    voting_data = json.loads(decrypted_bytes.decode("utf-8"))
    return voting_data
