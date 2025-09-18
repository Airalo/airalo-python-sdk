"""
Signature Helper Module

This module handles HMAC signature generation for API authentication.
"""

import hashlib
import hmac
import json
from typing import Any, Optional, Union


class Signature:
    """
    Signature generator for API authentication.

    Generates HMAC-SHA512 signatures for request payload validation.
    """

    def __init__(self, secret: str):
        """
        Initialize signature generator.

        Args:
            secret: Secret key for HMAC generation
        """
        self._secret = secret

    def get_signature(self, payload: Any) -> Optional[str]:
        """
        Generate HMAC signature for payload.

        Args:
            payload: Request payload (dict, string, or any JSON-serializable object)

        Returns:
            HMAC-SHA512 signature as hex string, or None if payload is empty
        """
        prepared_payload = self._prepare_payload(payload)
        if not prepared_payload:
            return None

        return self._sign_data(prepared_payload)

    def check_signature(self, hash_value: Optional[str], payload: Any) -> bool:
        """
        Verify HMAC signature.

        Args:
            hash_value: Expected signature
            payload: Request payload

        Returns:
            True if signature matches, False otherwise
        """
        if not hash_value:
            return False

        prepared_payload = self._prepare_payload(payload)
        if not prepared_payload:
            return False

        expected_signature = self._sign_data(prepared_payload)
        return hmac.compare_digest(expected_signature, hash_value)

    def _prepare_payload(self, payload: Any) -> Optional[str]:
        """
        Prepare payload for signing.

        Args:
            payload: Raw payload

        Returns:
            JSON string representation of payload, or None if empty
        """
        if not payload:
            return None

        if isinstance(payload, str):
            # If it's already a string, ensure it's valid JSON by parsing and re-encoding
            try:
                payload = self._escape_forward_slashes(payload)

                # Remove whitespaces by parsing and re-encoding
                parsed = json.loads(payload)
                return json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)
            except json.JSONDecodeError:
                # If not valid JSON, return as is
                return payload

        # Convert to JSON string
        try:
            json_encoded = json.dumps(
                payload, separators=(",", ":"), ensure_ascii=False
            )
            return self._escape_forward_slashes(json_encoded)
        except (TypeError, ValueError):
            # If not JSON-serializable, convert to string
            return str(payload)

    def _escape_forward_slashes(self, payload: str) -> str:
        return payload.replace("/", "\\/")

    def _sign_data(self, payload: str, algo: str = "sha512") -> str:
        """
        Generate HMAC signature.

        Args:
            payload: Prepared payload string
            algo: Hash algorithm (default: sha512)

        Returns:
            HMAC signature as hex string
        """
        return hmac.new(
            self._secret.encode("utf-8"),
            payload.encode("utf-8"),
            getattr(hashlib, algo),
        ).hexdigest()
