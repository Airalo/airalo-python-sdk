"""
Airalo Python SDK

A Python SDK for integrating with Airalo's Partner API.
"""

from .config import Config
from .airalo import Airalo
from .exceptions.airalo_exception import (
    AiraloException,
    ConfigurationError,
    AuthenticationError,
    ValidationError,
    APIError,
    NetworkError,
)

__version__ = "1.0.0"

__all__ = [
    "Airalo",
    "Config",
    "AiraloException",
    "ConfigurationError",
    "AuthenticationError",
    "ValidationError",
    "APIError",
    "NetworkError",
]
