"""
OAuth Service Module

This module handles OAuth authentication and access token management.
"""

import hashlib
import json
import time
from typing import Optional
from urllib.parse import urlencode

from ..config import Config
from ..constants.api_constants import ApiConstants
from ..constants.sdk_constants import SdkConstants
from ..exceptions.airalo_exception import AuthenticationError
from ..helpers.cached import Cached
from ..helpers.crypt import Crypt
from ..helpers.signature import Signature
from ..resources.http_resource import HttpResource


class OAuthService:
    """
    OAuth service for managing API authentication.

    Handles access token generation, caching, and refresh with automatic retry logic.
    """

    CACHE_NAME = "airalo_access_token"
    RETRY_LIMIT = SdkConstants.DEFAULT_RETRY_COUNT

    def __init__(
        self, config: Config, http_resource: HttpResource, signature: Signature
    ):
        """
        Initialize OAuth service.

        Args:
            config: SDK configuration
            http_resource: HTTP client for API requests
            signature: Signature generator for request signing
        """
        self._config = config
        self._http_resource = http_resource
        self._signature = signature

        # Prepare OAuth payload
        self._payload = {
            **self._config.get_credentials(),
            "grant_type": "client_credentials",
        }

    def get_access_token(self) -> Optional[str]:
        """
        Get access token with caching and retry logic.

        Returns:
            Access token string or None if failed

        Raises:
            AuthenticationError: If token generation fails after retries
        """
        retry_count = 0

        # Generate cache key based on credentials
        cache_name = f"{self.CACHE_NAME}_{self._generate_cache_key()}"

        while retry_count < self.RETRY_LIMIT:
            try:
                # Try to get cached token
                encrypted_token = Cached.get(
                    lambda: self._request_token(),
                    cache_name,
                    ttl=SdkConstants.TOKEN_CACHE_TTL,
                )

                # Decrypt and return token
                if encrypted_token:
                    return Crypt.decrypt(encrypted_token, self._get_encryption_key())

            except Exception as e:
                retry_count += 1

                if retry_count >= self.RETRY_LIMIT:
                    raise AuthenticationError(
                        f"Failed to get access token from API after {self.RETRY_LIMIT} attempts: {str(e)}"
                    )

                # Wait before retry (exponential backoff)
                time.sleep(0.5 * (2 ** (retry_count - 1)))

        return None

    def _request_token(self) -> str:
        """
        Request new access token from API.

        Returns:
            Encrypted access token

        Raises:
            AuthenticationError: If token request fails
        """
        # Prepare request
        url = self._config.get_url() + ApiConstants.TOKEN_SLUG

        # Generate signature
        signature_hash = self._signature.get_signature(self._payload)

        # Set headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "airalo-signature": signature_hash,
        }

        # Make request
        self._http_resource.set_headers(headers)
        response = self._http_resource.post(url, urlencode(self._payload))

        # Check response
        if not response or self._http_resource.code != 200:
            raise AuthenticationError(
                f"Access token generation failed, status code: {self._http_resource.code}, "
                f"response: {response}"
            )

        # Parse response
        try:
            response_data = json.loads(response)
        except json.JSONDecodeError as e:
            raise AuthenticationError(
                f"Failed to parse access token response: {str(e)}"
            )

        # Extract token
        if not isinstance(response_data, dict) or "data" not in response_data:
            raise AuthenticationError("Invalid response format: missing 'data' field")

        if "access_token" not in response_data["data"]:
            raise AuthenticationError("Access token not found in response")

        access_token = response_data["data"]["access_token"]

        # Encrypt token for caching
        return Crypt.encrypt(access_token, self._get_encryption_key())

    def _get_encryption_key(self) -> str:
        """
        Generate encryption key from credentials.

        Returns:
            Encryption key
        """
        credentials_string = self._config.get_credentials(as_string=True)
        return hashlib.md5(credentials_string.encode()).hexdigest()

    def _generate_cache_key(self) -> str:
        """
        Generate unique cache key for token storage.

        Returns:
            Cache key hash
        """
        credentials_string = self._config.get_credentials(as_string=True)
        return hashlib.sha256(credentials_string.encode()).hexdigest()

    def clear_token_cache(self) -> None:
        """Clear cached access token."""
        cache_name = f"{self.CACHE_NAME}_{self._generate_cache_key()}"
        # Clear specific token cache
        # Note: This would need enhancement in Cached class to clear specific cache
        Cached.clear_cache()

    def refresh_token(self) -> Optional[str]:
        """
        Force refresh of access token.

        Returns:
            New access token
        """
        # Clear existing cache
        self.clear_token_cache()

        # Get new token
        return self.get_access_token()
