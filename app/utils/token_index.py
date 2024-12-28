# app/utils/token_index.py
import json
import os

TOKEN_INDEX_FILE = "tokens_index.json"

def load_tokens_index() -> dict:
    if not os.path.isfile(TOKEN_INDEX_FILE):
        # Si no existe, devolvemos un dict vacío
        return {}
    with open(TOKEN_INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data

def save_tokens_index(data: dict):
    with open(TOKEN_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
