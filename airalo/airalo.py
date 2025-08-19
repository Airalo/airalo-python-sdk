"""
Airalo Main Client Module

This module provides the main Airalo client class for SDK operations.
"""

from typing import Any, Dict, List, Optional, Union

from .config import Config
from .exceptions.airalo_exception import AiraloException
from .helpers.signature import Signature
from .resources.http_resource import HttpResource
from .resources.multi_http_resource import MultiHttpResource
from .services.oauth_service import OAuthService

from .services.packages_service import PackagesService
from .services.order_service import OrderService
from .services.topup_service import TopupService
from .services.future_order_service import FutureOrderService
from .services.installation_instructions_service import InstallationInstructionsService

class Airalo:
    """
    Main Airalo SDK client.

    Provides access to all Airalo API operations through a single interface.
    """

    # Class-level pool for resource sharing
    _pool: Dict[str, Any] = {}

    def __init__(self, config: Union[Dict[str, Any], Config, str]):
        """
        Initialize Airalo client.

        Args:
            config: Configuration data (dict, Config object, or JSON string)

        Raises:
            AiraloException: If initialization fails
        """
        try:
            self._init_resources(config)
            self._init_services()

            # Store resources in pool for reuse
            if not self._pool:
                self._pool = {
                    'config': self._config,
                    'curl': self._http,
                    'multi_curl': self._multi_http,
                    'signature': self._signature,
                    'oauth': self._oauth,
                    'installation_instructions': self._installation_instructions,
                    'topup': self._topup,
                    'future_order': self._future_order
                    # Services will be added as implemented
                }
        except Exception as e:
            self._pool = {}
            raise AiraloException(f"Airalo SDK initialization failed: {str(e)}")

    def _init_resources(self, config: Union[Dict[str, Any], Config, str]) -> None:
        """
        Initialize core resources.

        Args:
            config: Configuration data
        """
        # Initialize configuration
        if isinstance(config, Config):
            self._config = config
        else:
            self._config = self._pool.get("config") or Config(config)

        # Initialize HTTP resources
        self._http = self._pool.get("curl") or HttpResource(self._config)
        self._multi_http = self._pool.get("multi_curl") or MultiHttpResource(
            self._config
        )

        # Initialize signature helper
        self._signature = self._pool.get("signature") or Signature(
            self._config.get("client_secret")
        )

    def _init_services(self) -> None:
        """
        Initialize service classes.

        Raises:
            AiraloException: If authentication fails
        """
        # Initialize OAuth service
        self._oauth = self._pool.get("oauth") or OAuthService(
            self._config, self._http, self._signature
        )

        # Get access token
        self._access_token = self._oauth.get_access_token()
        if not self._access_token:
            raise AiraloException("Failed to obtain access token")

        # Initialize other services
        self._packages = self._pool.get("packages") or PackagesService(
            self._config, self._http, self._access_token
        )
        self._order = self._pool.get("order") or OrderService(
            self._config,
            self._http,
            self._multi_http,
            self._signature,
            self._access_token,
        )
        self._topup = self._pool.get("topup") or TopupService(
            self._config, self._http, self._signature, self._access_token
        )
        self._installation_instructions = self._pool.get('installation_instructions') or InstallationInstructionsService(
            self._config, self._http, self._access_token
        )
        self._future_order = self._pool.get("future_order") or FutureOrderService(
            self._config, self._http, self._signature, self._access_token
        )

    # =====================================================
    # OAuth Methods
    # =====================================================

    def get_access_token(self) -> Optional[str]:
        """
        Get current access token.

        Returns:
            Access token or None
        """
        return self._access_token

    def refresh_token(self) -> Optional[str]:
        """
        Refresh access token.

        Returns:
            New access token or None
        """
        self._access_token = self._oauth.refresh_token()
        return self._access_token

    # =====================================================
    # Package Methods
    # =====================================================

    def get_all_packages(
        self,
        flat: bool = False,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Get all available packages.

        Args:
            flat: If True, return flattened response
            limit: Number of results per page
            page: Page number

        Returns:
            Packages data or None
        """
        return self._packages.get_all_packages(flat, limit, page)

    def get_sim_packages(
        self,
        flat: bool = False,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Get SIM-only packages.

        Args:
            flat: If True, return flattened response
            limit: Number of results per page
            page: Page number

        Returns:
            Packages data or None
        """
        return self._packages.get_sim_packages(flat, limit, page)

    def get_local_packages(
        self,
        flat: bool = False,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Get local packages.

        Args:
            flat: If True, return flattened response
            limit: Number of results per page
            page: Page number

        Returns:
            Packages data or None
        """
        return self._packages.get_local_packages(flat, limit, page)

    def get_global_packages(
        self,
        flat: bool = False,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Get global packages.

        Args:
            flat: If True, return flattened response
            limit: Number of results per page
            page: Page number

        Returns:
            Packages data or None
        """
        return self._packages.get_global_packages(flat, limit, page)

    def get_country_packages(
        self, country_code: str, flat: bool = False, limit: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Get packages for a specific country.

        Args:
            country_code: ISO country code
            flat: If True, return flattened response
            limit: Number of results

        Returns:
            Packages data or None
        """
        return self._packages.get_country_packages(country_code, flat, limit)

    # =====================================================
    # Order Methods
    # =====================================================

    def order(
        self, package_id: str, quantity: int, description: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create an order.

        Args:
            package_id: Package ID to order
            quantity: Number of SIMs
            description: Order description

        Returns:
            Order data or None
        """
        return self._order.create_order(
            {
                "package_id": package_id,
                "quantity": quantity,
                "type": "sim",
                "description": description or "Order placed via Airalo Python SDK",
            }
        )

    def order_with_email_sim_share(
        self,
        package_id: str,
        quantity: int,
        esim_cloud: Dict[str, Any],
        description: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Create an order with email SIM sharing.

        Args:
            package_id: Package ID to order
            quantity: Number of SIMs
            esim_cloud: Email sharing configuration
            description: Order description

        Returns:
            Order data or None
        """
        return self._order.create_order_with_email_sim_share(
            {
                "package_id": package_id,
                "quantity": quantity,
                "type": "sim",
                "description": description or "Order placed via Airalo Python SDK",
            },
            esim_cloud,
        )

    def order_async(
        self,
        package_id: str,
        quantity: int,
        webhook_url: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Create an asynchronous order.

        Args:
            package_id: Package ID to order
            quantity: Number of SIMs
            webhook_url: Webhook URL for notifications
            description: Order description

        Returns:
            Order data or None
        """
        return self._order.create_order_async(
            {
                "package_id": package_id,
                "quantity": quantity,
                "type": "sim",
                "webhook_url": webhook_url,
                "description": description or "Order placed via Airalo Python SDK",
            }
        )

    def order_bulk(
        self,
        packages: Union[Dict[str, int], List[Dict]],
        description: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Create bulk orders.

        Args:
            packages: Either dict of package_id: quantity or list of dicts
            description: Order description

        Returns:
            Order data or None
        """
        if not packages:
            return None
        return self._order.create_order_bulk(packages, description)

    def order_bulk_with_email_sim_share(
        self,
        packages: Union[Dict[str, int], List[Dict]],
        esim_cloud: Dict[str, Any],
        description: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Create bulk orders with email SIM sharing.

        Args:
            packages: Package IDs and quantities
            esim_cloud: Email sharing configuration
            description: Order description

        Returns:
            Order data or None
        """
        if not packages:
            return None
        return self._order.create_order_bulk_with_email_sim_share(
            packages, esim_cloud, description
        )

    def order_async_bulk(
        self,
        packages: Union[Dict[str, int], List[Dict]],
        webhook_url: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Create bulk asynchronous orders.

        Args:
            packages: Package IDs and quantities
            webhook_url: Webhook URL for notifications
            description: Order description

        Returns:
            Order data or None
        """
        if not packages:
            return None
        return self._order.create_order_async_bulk(packages, webhook_url, description)

    def topup(
        self, package_id: str, iccid: str, description: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create a top-up.

        Args:
            package_id: Package ID to top-up
            iccid: ICCID of the SIM to top-up
            description: Optional description for the top-up
        Returns:
            Top-up data or None
        """
        return self._topup.create_topup(
            {
                "package_id": package_id,
                "iccid": iccid,
                "description": description or "Topup placed via Airalo Python SDK",
            }
        )

    # =====================================================
    # Utility Methods
    # =====================================================

    def get_config(self) -> Config:
        """
        Get current configuration.

        Returns:
            Configuration object
        """
        return self._config

    def get_environment(self) -> str:
        """
        Get current environment.

        Returns:
            Environment name ('sandbox' or 'production')
        """
        return self._config.get_environment()

    def clear_cache(self) -> None:
        """Clear all cached data."""
        from .helpers.cached import Cached

        Cached.clear_cache()

    def __repr__(self) -> str:
        """String representation of Airalo client."""
        return f"<Airalo(env='{self.get_environment()}')>"


    # =====================================================
    # Installation Instruction Methods
    # =====================================================

    def get_installation_instructions(self, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Get installation instructions for a given ICCID and language.

        Args:
            params: Dictionary with at least 'iccid' key, optionally 'language'.

        Returns:
            EasyAccess-wrapped data or None
        """
        return self._installation_instructions.get_instructions(params or {})

    # =====================================================
    # Future Order Methods
    # =====================================================

    def create_future_order(self, payload: Dict[str, Any]) -> Optional[Dict]:
        """
        Create a future order.

        Args:
            payload: Dictionary containing order details.

        Returns:
            Response data as dictionary or None.
        """
        return self._future_order.create_future_order(payload)

    def cancel_future_order(self, payload: Dict[str, Any]) -> Optional[Dict]:
        """
        Cancel a future order.

        Args:
            payload: Dictionary containing cancellation details.

        Returns:
            Response data as dictionary or None.
        """
        return self._future_order.cancel_future_order(payload)
