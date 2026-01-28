"""
API Constants Module

This module contains all API endpoints and URLs used by the Airalo SDK.
"""


class ApiConstants:
    """API endpoints and URLs for Airalo SDK."""

    PRODUCTION_URL = "https://partners-api.airalo.com/v2/"

    # Authentication
    TOKEN_SLUG = "token"

    # Package endpoints
    PACKAGES_SLUG = "packages"

    # Order endpoints
    ORDERS_SLUG = "orders"
    ASYNC_ORDERS_SLUG = "orders-async"
    TOPUPS_SLUG = "orders/topups"

    # Voucher endpoints
    VOUCHERS_SLUG = "voucher/airmoney"
    VOUCHERS_ESIM_SLUG = "voucher/esim"

    # SIM endpoints
    SIMS_SLUG = "sims"
    SIMS_USAGE = "usage"
    SIMS_TOPUPS = "topups"
    SIMS_PACKAGES = "packages"

    # Instructions and compatibility
    INSTRUCTIONS_SLUG = "instructions"
    COMPATIBILITY_SLUG = "compatible-devices-lite"

    # Finance endpoints
    EXCHANGE_RATES_SLUG = "finance/exchange-rates"

    # Future orders
    FUTURE_ORDERS = "future-orders"
    CANCEL_FUTURE_ORDERS = "cancel-future-orders"

    # Catalog
    OVERRIDE_SLUG = "packages/overrides"

    # Notifications
    NOTIFICATIONS_SLUG = "notifications"
