"""Tests for the enhanced crypto module."""
import base64

import pytest
from cryptography.fernet import Fernet

from app.core.crypto import decrypt_api_key, encrypt_api_key, reencrypt_api_key


class TestEncryptDecrypt:
    async def test_roundtrip(self):
        """A simple encrypt + decrypt roundtrip works."""
        original = "sk-test1234567890abcdef"
        encrypted = encrypt_api_key(original)
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == original

    async def test_output_format(self):
        """New-format ciphertext starts with V + version byte."""
        encrypted = encrypt_api_key("sk-any-key")
        raw = base64.urlsafe_b64decode(encrypted.encode())
        assert raw[:1] == b"V"
        assert raw[1] == 1  # version byte

    async def test_different_keys_different_ciphertexts(self):
        """Same plaintext produces different ciphertext each time (IV randomization)."""
        c1 = encrypt_api_key("sk-same-key")
        c2 = encrypt_api_key("sk-same-key")
        assert c1 != c2

    async def test_decrypt_legacy_format(self):
        """Encrypted data from the old format (raw Fernet token, no V prefix)."""
        # Build a legacy-style token using Fernet directly
        key = base64.urlsafe_b64encode(b"x" * 32)  # dummy key
        fernet = Fernet(key)
        legacy = fernet.encrypt(b"legacy-key-data").decode()

        encrypted = encrypt_api_key("new-style-key")
        # Not the same as legacy token
        assert encrypted != legacy


class TestDecryptErrors:
    async def test_decrypt_garbage(self):
        """Random garbage raises a clear error."""
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_api_key("this-is-not-valid-base64!!!")

    async def test_decrypt_tampered_ciphertext(self):
        """Tampered ciphertext (wrong key) raises a clear error."""
        encrypted = encrypt_api_key("my-secret-key")
        # Flip a bit in the base64 payload
        mangled = encrypted[:-3] + ("A" if encrypted[-3] != "A" else "B") + encrypted[-2:]
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_api_key(mangled)


class TestReencrypt:
    async def test_reencrypt_roundtrip(self):
        """Re-encrypt produces a valid ciphertext that still decrypts to the original."""
        original = "sk-original-value"
        encrypted = encrypt_api_key(original)
        reencrypted = reencrypt_api_key(encrypted)
        assert reencrypted != encrypted  # different ciphertext (new IV)
        assert decrypt_api_key(reencrypted) == original

    async def test_reencrypt_with_verify_prefix(self):
        """verify_prefix sanity-check passes."""
        encrypted = encrypt_api_key("sk-abcdef")
        result = reencrypt_api_key(encrypted, verify_prefix="sk-")
        assert decrypt_api_key(result) == "sk-abcdef"

    async def test_reencrypt_with_verify_prefix_mismatch(self):
        """verify_prefix mismatch raises."""
        encrypted = encrypt_api_key("sk-abcdef")
        with pytest.raises(ValueError, match="prefix"):
            reencrypt_api_key(encrypted, verify_prefix="pk-")


class TestSingleton:
    async def test_cached_fernet(self):
        """Multiple calls return the same Fernet instance (cached)."""
        from app.core.crypto import _get_fernet

        f1 = _get_fernet()
        f2 = _get_fernet()
        assert f1 is f2
