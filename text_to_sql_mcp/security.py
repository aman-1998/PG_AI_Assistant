"""AES decryption of the per-request DB connection token, plus a simple SQL
statement classifier (DQL/DDL/DML) used for logging.

The encryption scheme here MUST match text_to_sql_backend/services/encryption_util.py
exactly (AES-256-CBC, key = SHA-256(passphrase), payload = base64(iv || ciphertext)).
Duplicated intentionally so this app has no import-time dependency on the backend.
"""
from __future__ import annotations

import base64
import hashlib
import json

import sqlparse
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from config import settings


class InvalidConnectionTokenError(Exception):
    pass


def _derive_key(passphrase: str) -> bytes:
    return hashlib.sha256(passphrase.encode("utf-8")).digest()


def decrypt_text(token: str, passphrase: str) -> str:
    key = _derive_key(passphrase)
    raw = base64.b64decode(token)
    iv, ciphertext = raw[:16], raw[16:]
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext = unpadder.update(padded) + unpadder.finalize()
    return plaintext.decode("utf-8")


def decode_connection_token(token: str) -> dict:
    """Decrypt+parse the X-DB-Conn-Token header value into connection params."""
    try:
        raw_json = decrypt_text(token, settings.DB_CONNECTION_TOKEN_SECRET)
        return json.loads(raw_json)
    except Exception as exc:  # noqa: BLE001
        raise InvalidConnectionTokenError(f"Could not decode DB connection token: {exc}") from exc


_DDL_KEYWORDS = {"CREATE", "ALTER", "DROP", "TRUNCATE"}
_DML_KEYWORDS = {"INSERT", "UPDATE", "DELETE", "MERGE"}
_DQL_KEYWORDS = {"SELECT", "WITH", "EXPLAIN", "SHOW"}


def classify_statement(sql: str) -> str:
    """Return 'DDL', 'DML', 'DQL', or 'OTHER' based on the first SQL keyword."""
    parsed = sqlparse.parse(sql.strip())
    if not parsed:
        return "OTHER"
    first_token = parsed[0].token_first(skip_cm=True)
    if first_token is None:
        return "OTHER"
    keyword = first_token.value.upper()
    if keyword in _DDL_KEYWORDS:
        return "DDL"
    if keyword in _DML_KEYWORDS:
        return "DML"
    if keyword in _DQL_KEYWORDS:
        return "DQL"
    return "OTHER"
