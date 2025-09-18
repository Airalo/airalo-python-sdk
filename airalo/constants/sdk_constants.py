"""
SDK Constants Module

This module contains SDK-specific constants such as version, limits, and timeouts.
"""


class SdkConstants:
    """SDK-specific constants for Airalo SDK."""

    # SDK Version
    VERSION = "1.0.0"

    # Order limits
    BULK_ORDER_LIMIT = 50
    ORDER_LIMIT = 50
    FUTURE_ORDER_LIMIT = 50

    # Voucher limits
    VOUCHER_MAX_NUM = 100000
    VOUCHER_MAX_QUANTITY = 100

    # HTTP settings
    DEFAULT_TIMEOUT = 60  # seconds
    DEFAULT_RETRY_COUNT = 2

    # Cache settings
    DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds
    TOKEN_CACHE_TTL = 3600  # 1 hour in seconds

    # Concurrency settings
    MAX_CONCURRENT_REQUESTS = 5
