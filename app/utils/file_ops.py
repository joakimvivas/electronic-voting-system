# utils/file_ops.py

import json
import os
from typing import Any

from .encrypt import encrypt_data, decrypt_data

VOTACIONES_DIR = "votaciones"

def save_voting_file(voting_id: str, voting_data: dict, key: bytes):
    """
    Guarda (encripta) un diccionario JSON en un fichero .enc en la carpeta votaciones.
    """
    if not os.path.exists(VOTACIONES_DIR):
        os.makedirs(VOTACIONES_DIR)
    
    raw_json = json.dumps(voting_data).encode("utf-8")
    encrypted = encrypt_data(raw_json, key)

    # Ejemplo: votaciones/<voting_id>.enc
    file_path = os.path.join(VOTACIONES_DIR, f"{voting_id}.enc")
    with open(file_path, "wb") as f:
        f.write(encrypted)


def load_voting_file(voting_id: str, key: bytes) -> dict:
    """
    Carga y desencripta el fichero de votación correspondiente.
    Si no existe, lanza una excepción.
    """
    file_path = os.path.join(VOTACIONES_DIR, f"{voting_id}.enc")
    
    if not os.path.isfile(file_path):
        raise FileNotFoundError("No existe el fichero de votación")

    with open(file_path, "rb") as f:
        encrypted_content = f.read()

    decrypted_bytes = decrypt_data(encrypted_content, key)
    voting_data = json.loads(decrypted_bytes.decode("utf-8"))
    return voting_data
