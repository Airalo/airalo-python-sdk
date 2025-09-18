"""
Airalo Exception Module

This module defines custom exceptions for the Airalo SDK.
"""


class AiraloException(Exception):
    """
    Base exception class for Airalo SDK.

    This exception is raised when SDK-specific errors occur,
    such as configuration errors, API errors, or validation errors.
    """

    def __init__(self, message: str, error_code: str = None, http_status: int = None):
        """
        Initialize AiraloException.

        Args:
            message: Error message describing the exception
            error_code: Optional error code from API
            http_status: Optional HTTP status code
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.http_status = http_status

    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(AiraloException):
    """Exception raised for configuration-related errors."""

    pass


class AuthenticationError(AiraloException):
    """Exception raised for authentication failures."""

    pass


class ValidationError(AiraloException):
    """Exception raised for validation errors."""

    pass


class APIError(AiraloException):
    """Exception raised for API-related errors."""

    pass


class NetworkError(AiraloException):
    """Exception raised for network-related errors."""

    pass
