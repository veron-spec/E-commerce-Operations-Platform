"""Encrypt / decrypt third-party API keys using Fernet (AES-128-CBC + HMAC-SHA256).

Security properties:
  - Master key derived ONCE at startup via PBKDF2 from settings.encryption_key
  - Fernet singleton cached for all operations (no per-call PBKDF2 overhead)
  - Version-prefixed ciphertext format for algorithm migration
  - Legacy format backward compatible

Ciphertext format (base64-encoded):
  V<1-byte-version><fernet_token>   (new format, v1)
  <raw_fernet_token>                (legacy format, no prefix)
"""

import base64
import hashlib
import logging
from functools import cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

logger = logging.getLogger(__name__)


# ── Version header ──────────────────────────────────────────────────────────

_CURRENT_VERSION = 1
_HEADER = b"V"  # first byte of new-format ciphertext


# ══════════════════════════════════════════════════════════════════════════════
# Initialization-time validation
# ══════════════════════════════════════════════════════════════════════════════

def _validate_settings() -> None:
    """Warn loudly if the encryption key is still the default."""
    if settings.encryption_key in ("change-me", "", "default"):
        logger.warning(
            "⚠️  ⚠️  ⚠️  settings.encryption_key is still the default value! "
            "Set a strong, unique key in your .env file. "
            "Any encrypted API keys will be unrecoverable if this key changes."
        )


def _derive_key() -> bytes:
    """Derive a Fernet-compatible 32-byte key from settings.encryption_key."""
    raw = settings.encryption_key.encode("utf-8")
    salt = b"ecommerce-ops-crypto-v2"
    key = hashlib.pbkdf2_hmac("sha256", raw, salt, 100_000, dklen=32)
    return base64.urlsafe_b64encode(key)


# ── Singleton Fernet (derived once at import time) ─────────────────────────

@cache
def _get_fernet() -> Fernet:
    """Return the cached Fernet singleton.

    ``functools.cache`` guarantees this runs exactly once per process.
    """
    _validate_settings()
    return Fernet(_derive_key())


# ── Public API ─────────────────────────────────────────────────────────────

def encrypt_api_key(plaintext: str) -> str:
    """Encrypt an API key.

    Returns a version-prefixed, base64-encoded ciphertext string.
    """
    token = _get_fernet().encrypt(plaintext.encode("utf-8"))
    header = _HEADER + bytes([_CURRENT_VERSION])
    return base64.urlsafe_b64encode(header + token).decode()


def decrypt_api_key(ciphertext: str) -> str:
    """Decrypt an API key.

    Handles both version-prefixed (new) and raw (legacy) ciphertext formats.
    """
    raw = base64.urlsafe_b64decode(ciphertext.encode("utf-8"))

    # Strip version header if present
    if raw[:1] == _HEADER:
        version = raw[1]
        if version == 1:
            token = raw[2:]
        else:
            raise ValueError(f"Unsupported encryption version: {version}")
    else:
        # Legacy format — whole payload is a raw Fernet token
        token = raw

    try:
        return _get_fernet().decrypt(token).decode("utf-8")
    except InvalidToken:
        raise ValueError(
            "Decryption failed — the encryption_key in .env may have "
            "changed since this key was saved."
        )


def reencrypt_api_key(ciphertext: str, *, verify_prefix: str | None = None) -> str:
    """Re-encrypt an existing key under the current encryption key.

    Useful after rotating settings.encryption_key.
    If *verify_prefix* is given, the decrypted key is sanity-checked to
    start with that prefix before re-encrypting.
    """
    plaintext = decrypt_api_key(ciphertext)
    if verify_prefix and not plaintext.startswith(verify_prefix):
        raise ValueError(
            f"Decrypted key does not start with expected prefix "
            f"{verify_prefix!r} — refusing to re-encrypt"
        )
    return encrypt_api_key(plaintext)
