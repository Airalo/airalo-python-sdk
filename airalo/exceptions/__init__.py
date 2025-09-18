"""
Exceptions package for Airalo SDK.
"""

from .airalo_exception import (
    AiraloException,
    ConfigurationError,
    AuthenticationError,
    ValidationError,
    APIError,
    NetworkError,
)

__all__ = [
    "AiraloException",
    "ConfigurationError",
    "AuthenticationError",
    "ValidationError",
    "APIError",
    "NetworkError",
]
