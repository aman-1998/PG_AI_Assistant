"""AES-256-CBC encryption helpers used to protect secrets at rest and in transit.

Mirrors the pattern used in ai-service/services/encryption_util.py:
- Key derivation: SHA-256 of a passphrase -> 32-byte AES-256 key.
- Payload layout: base64( iv(16 bytes) || ciphertext ), PKCS7 padded.

This module is intentionally self-contained (no shared import from ai-service)
so this application remains independently deployable.
"""
from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def _derive_key(passphrase: str) -> bytes:
    return hashlib.sha256(passphrase.encode("utf-8")).digest()


def encrypt_text(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext with AES-256-CBC, returning a base64 string of iv||ciphertext."""
    if plaintext is None:
        return plaintext
    key = _derive_key(passphrase)
    iv = os.urandom(16)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext).decode("utf-8")


def decrypt_text(token: str, passphrase: str) -> str:
    """Decrypt a base64 iv||ciphertext string produced by encrypt_text()."""
    if token is None:
        return token
    key = _derive_key(passphrase)
    raw = base64.b64decode(token)
    iv, ciphertext = raw[:16], raw[16:]
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext = unpadder.update(padded) + unpadder.finalize()
    return plaintext.decode("utf-8")
