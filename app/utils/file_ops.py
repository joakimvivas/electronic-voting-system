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
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "electronic-voting-system")

######### Inicializar Supabase si corresponde #########
supabase: Client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    if STORAGE_BACKEND == "supabase":
        logging.warning(
            "ATENCIÓN: STORAGE_BACKEND=supabase, pero SUPABASE_URL/KEY no están configuradas."
        )
        # supabase seguirá siendo None, lo que causará error si se intenta usar

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
    Utiliza upsert=True y un contentType genérico para binarios.
    """
    if not supabase:
        raise RuntimeError("Supabase client no inicializado o variables de entorno no configuradas.")

    try:
        logging.debug(f"Subiendo archivo '{filename}' al bucket '{SUPABASE_BUCKET_NAME}' con upsert y contentType.")
        response = supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
            filename,
            data,
            {
                "upsert": True,
                "contentType": "application/octet-stream"
            }
        )
        logging.debug(f"Supabase upload response: {response}")

        # Verificar si hay error en la respuesta
        if "error" in response and response["error"]:
            raise RuntimeError(f"Error subiendo a Supabase: {response['error']}")
    except Exception as e:
        # Log completo de la excepción
        logging.exception(f"Excepción subiendo '{filename}' a Supabase:")
        raise

def _download_from_supabase(filename: str) -> bytes:
    """
    Descarga bytes desde el bucket de Supabase.
    Retorna b'' si no existe o si ocurre algún error.
    """
    if not supabase:
        raise RuntimeError("Supabase client no inicializado o variables de entorno no configuradas.")

    try:
        logging.debug(f"Descargando archivo '{filename}' del bucket '{SUPABASE_BUCKET_NAME}'...")
        content = supabase.storage.from_(SUPABASE_BUCKET_NAME).download(filename)
        logging.debug(f"Descarga completada. Tipo de 'content': {type(content)}")

        # Supabase-py a veces retorna bytes directos, otras un objeto.
        # Ajusta según tu versión. Si no hay contenido, devolvemos b''.
        if not content:
            return b""
        if isinstance(content, bytes):
            return content
        # Si es un objeto tipo HTTPResponse, quizá debas usar content.read() o similar.
        # Haz pruebas con logs.
        return content

    except Exception as e:
        logging.exception(f"No se pudo descargar '{filename}' desde Supabase:")
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
