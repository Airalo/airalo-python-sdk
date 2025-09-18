"""
Encryption Helper Module

This module handles encryption and decryption operations using the cryptography library.
Provides equivalent functionality to PHP's sodium library.
"""

import base64
import os
from typing import Any, Union

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from ..exceptions.airalo_exception import AiraloException


class Crypt:
    """
    Encryption/decryption utility class.

    Uses ChaCha20-Poly1305 for authenticated encryption, which is equivalent
    to sodium's crypto_secretbox functionality.
    """

    # Constants matching sodium's requirements
    KEY_BYTES = 32  # SODIUM_CRYPTO_SECRETBOX_KEYBYTES
    NONCE_BYTES = 12  # For ChaCha20-Poly1305

    @staticmethod
    def encrypt(data: str, key: str) -> str:
        """
        Encrypt data using ChaCha20-Poly1305.

        Args:
            data: Plain text data to encrypt
            key: Encryption key (will be truncated/padded to 32 bytes)

        Returns:
            Base64-encoded encrypted data with nonce prepended
        """
        if not data or not key:
            return data

        # Prepare key (ensure it's exactly 32 bytes)
        key_bytes = Crypt._prepare_key(key)

        # Check if data is already encrypted
        if Crypt.is_encrypted(data):
            return data

        # Generate random nonce
        nonce = os.urandom(Crypt.NONCE_BYTES)

        # Create cipher and encrypt
        cipher = ChaCha20Poly1305(key_bytes)
        encrypted = cipher.encrypt(nonce, data.encode("utf-8"), None)

        # Combine nonce and encrypted data, then base64 encode
        combined = nonce + encrypted
        return base64.b64encode(combined).decode("ascii")

    @staticmethod
    def decrypt(data: str, key: str) -> str:
        """
        Decrypt data encrypted with ChaCha20-Poly1305.

        Args:
            data: Base64-encoded encrypted data
            key: Decryption key

        Returns:
            Decrypted plain text

        Raises:
            AiraloException: If decryption fails
        """
        if not data or not key:
            return data

        # Prepare key
        key_bytes = Crypt._prepare_key(key)

        # Check if data is encrypted
        if not Crypt.is_encrypted(data):
            return data

        try:
            # Decode from base64
            encrypted = base64.b64decode(data)

            # Extract nonce and ciphertext
            nonce = encrypted[: Crypt.NONCE_BYTES]
            ciphertext = encrypted[Crypt.NONCE_BYTES :]

            # Decrypt
            cipher = ChaCha20Poly1305(key_bytes)
            decrypted = cipher.decrypt(nonce, ciphertext, None)

            return decrypted.decode("utf-8")
        except Exception as e:
            raise AiraloException(f"Decryption failed: {e}")

    @staticmethod
    def is_encrypted(data: Any) -> bool:
        """
        Check if data appears to be encrypted.

        Args:
            data: Data to check

        Returns:
            True if data appears to be encrypted, False otherwise
        """
        # Check for non-string types
        if not isinstance(data, str):
            return False

        # Check minimum length (nonce + some ciphertext + base64 overhead)
        if len(data) < 56:
            return False

        # Check if it's numeric (encrypted data shouldn't be purely numeric)
        if data.isdigit():
            return False

        # Check if it's valid base64
        try:
            decoded = base64.b64decode(data, validate=True)
            # Verify we can encode it back to the same string
            return base64.b64encode(decoded).decode("ascii") == data
        except Exception:
            return False

    @staticmethod
    def _prepare_key(key: str) -> bytes:
        """
        Prepare encryption key to be exactly 32 bytes.

        Args:
            key: Raw key string

        Returns:
            32-byte key
        """
        key_bytes = key.encode("utf-8")

        # Truncate or pad to exactly 32 bytes
        if len(key_bytes) > Crypt.KEY_BYTES:
            return key_bytes[: Crypt.KEY_BYTES]
        elif len(key_bytes) < Crypt.KEY_BYTES:
            # Pad with zeros
            return key_bytes.ljust(Crypt.KEY_BYTES, b"\0")

        return key_bytes
