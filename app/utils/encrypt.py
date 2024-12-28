# utils/encrypt.py

from cryptography.fernet import Fernet

def generate_key():
    """
    Genera una nueva clave (hash) para encriptar / desencriptar.
    """
    return Fernet.generate_key()

def encrypt_data(data: bytes, key: bytes) -> bytes:
    """
    Encripta datos en binario usando la key (bytes).
    """
    f = Fernet(key)
    encrypted = f.encrypt(data)
    return encrypted

def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Desencripta datos en binario usando la key.
    """
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_data)
    return decrypted
