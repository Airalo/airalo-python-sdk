"""
Configuration Module

This module handles SDK configuration including credentials, environment settings,
and HTTP headers.
"""

import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

from .constants.api_constants import ApiConstants
from .exceptions.airalo_exception import ConfigurationError


class Config:
    """
    Configuration class for Airalo SDK.

    Handles SDK configuration including API credentials, environment selection,
    and custom HTTP headers.
    """

    MANDATORY_CONFIG_KEYS = [
        "client_id",
        "client_secret",
    ]

    def __init__(self, data: Union[Dict[str, Any], str, object]):
        """
        Initialize configuration.

        Args:
            data: Configuration data as dict, JSON string, or object with attributes

        Raises:
            ConfigurationError: If configuration is invalid or missing required fields
        """
        self._data: Dict[str, Any] = {}

        if not data:
            raise ConfigurationError("Config data is not provided")

        # Convert different input types to dictionary
        if isinstance(data, str):
            try:
                self._data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ConfigurationError(f"Invalid JSON config data: {e}")
        elif isinstance(data, dict):
            self._data = data.copy()
        elif hasattr(data, "__dict__"):
            # Convert object to dictionary
            self._data = vars(data).copy()
        else:
            try:
                # Try to serialize and deserialize to get a dict
                self._data = json.loads(json.dumps(data, default=lambda o: o.__dict__))
            except (TypeError, json.JSONDecodeError) as e:
                raise ConfigurationError(f"Invalid config data provided: {e}")

        self._validate()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._data.get(key, default)

    def get_config(self) -> Dict[str, Any]:
        """
        Get complete configuration dictionary.

        Returns:
            Configuration dictionary
        """
        return self._data.copy()

    def get_credentials(self, as_string: bool = False) -> Union[Dict[str, str], str]:
        """
        Get API credentials.

        Args:
            as_string: If True, return as URL-encoded string

        Returns:
            Credentials as dictionary or URL-encoded string
        """
        credentials = {
            "client_id": self._data["client_id"],
            "client_secret": self._data["client_secret"],
        }

        if as_string:
            return urlencode(credentials)

        return credentials

    def get_environment(self) -> str:
        """
        Get current environment.
        """
        return self._data.get("env", "production")

    def get_url(self) -> str:
        """
        Get base API URL for current environment.

        Returns:
            Base API URL
        """
        return ApiConstants.PRODUCTION_URL

    def get_http_headers(self) -> List[str]:
        """
        Get custom HTTP headers.

        Returns:
            List of HTTP header strings
        """
        return self._data.get("http_headers", [])

    def _validate(self) -> None:
        """
        Validate configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Check mandatory fields
        for key in self.MANDATORY_CONFIG_KEYS:
            if key not in self._data or not self._data[key]:
                raise ConfigurationError(
                    f"Mandatory field `{key}` is missing in the provided config data"
                )

        # Set default environment if not provided
        if "env" not in self._data:
            self._data["env"] = "production"
