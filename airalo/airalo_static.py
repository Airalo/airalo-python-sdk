"""
Airalo Static Client Module

This module provides a static/singleton interface to the Airalo SDK.
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

class AiraloStatic:
    """
    Static/Singleton Airalo SDK client.

    Provides class-level methods for all Airalo API operations.
    Must be initialized once with init() before use.
    """

    # Class-level attributes
    _pool: Dict[str, Any] = {}
    _config: Optional[Config] = None
    _http: Optional[HttpResource] = None
    _multi_http: Optional[MultiHttpResource] = None
    _signature: Optional[Signature] = None
    _oauth: Optional[OAuthService] = None
    _access_token: Optional[str] = None
    _installation_instructions: Optional[InstallationInstructionsService] = None

    # Service instances
    _packages: Optional[PackagesService] = None
    _order: Optional[OrderService] = None
    _topup: Optional[TopupService] = None
    _future_orders: Optional[FutureOrderService] = None

    @classmethod
    def init(cls, config: Union[Dict[str, Any], Config, str]) -> None:
        """
        Initialize the static client.

        Args:
            config: Configuration data (dict, Config object, or JSON string)

        Raises:
            AiraloException: If initialization fails
        """
        try:
            cls._init_resources(config)
            cls._init_services()

            # Store all class attributes in pool for potential reuse
            if not cls._pool:
                import inspect
                for name, value in inspect.getmembers(cls):
                    if name.startswith('_') and not name.startswith('__') and value is not None:
                        cls._pool[name[1:]] = value  # Remove leading underscore

        except Exception as e:
            cls._pool = {}
            raise AiraloException(f'Airalo SDK initialization failed: {str(e)}')

    @classmethod
    def _init_resources(cls, config: Union[Dict[str, Any], Config, str]) -> None:
        """
        Initialize core resources.

        Args:
            config: Configuration data
        """
        # Initialize configuration
        if isinstance(config, Config):
            cls._config = config
        else:
            cls._config = cls._pool.get('config') or Config(config)

        # Initialize HTTP resources
        cls._http = cls._pool.get('http') or HttpResource(cls._config)
        cls._multi_http = cls._pool.get('multi_http') or MultiHttpResource(cls._config)

        # Initialize signature helper
        cls._signature = cls._pool.get('signature') or Signature(
            cls._config.get('client_secret')
        )

    @classmethod
    def _init_services(cls) -> None:
        """
        Initialize service classes.

        Raises:
            AiraloException: If authentication fails
        """
        # Initialize OAuth service
        cls._oauth = cls._pool.get('oauth') or OAuthService(
            cls._config,
            cls._http,
            cls._signature
        )

        # Get access token
        cls._access_token = cls._oauth.get_access_token()
        if not cls._access_token:
            raise AiraloException('Failed to obtain access token')

        # Initialize other services
        cls._packages = cls._pool.get('packages') or PackagesService(
            cls._config, cls._http, cls._access_token
        )
        cls._order = cls._pool.get('order') or OrderService(
            cls._config, cls._http, cls._multi_http, cls._signature, cls._access_token
        )
        cls._installation_instructions = cls._pool.get('installation_instructions') or InstallationInstructionsService(
            cls._config, cls._http, cls._access_token
        )
        cls._topup = cls._pool.get('topup') or TopupService(
            cls._config, cls._http, cls._signature, cls._access_token
        )
        cls._future_orders = cls._pool.get('future_orders') or FutureOrderService(
            cls._config, cls._http, cls._signature, cls._access_token
        )
        # Additional services will be initialized here as implemented

    @classmethod
    def _check_initialized(cls) -> None:
        """
        Check if client is initialized.

        Raises:
            AiraloException: If not initialized
        """
        if not cls._pool or cls._config is None:
            raise AiraloException(
                'Airalo SDK is not initialized, please call AiraloStatic.init() first'
            )

    # =====================================================
    # OAuth Methods
    # =====================================================

    @classmethod
    def get_access_token(cls) -> Optional[str]:
        """
        Get current access token.

        Returns:
            Access token or None
        """
        cls._check_initialized()
        return cls._access_token

    @classmethod
    def refresh_token(cls) -> Optional[str]:
        """
        Refresh access token.

        Returns:
            New access token or None
        """
        cls._check_initialized()
        cls._access_token = cls._oauth.refresh_token()
        return cls._access_token

    # =====================================================
    # Package Methods
    # =====================================================

    @classmethod
    def get_all_packages(cls, flat: bool = False, limit: Optional[int] = None,
                        page: Optional[int] = None) -> Optional[Dict]:
        """
        Get all available packages.

        Args:
            flat: If True, return flattened response
            limit: Number of results per page
            page: Page number

        Returns:
            Packages data or None
        """
        cls._check_initialized()
        return cls._packages.get_all_packages(flat, limit, page)

    @classmethod
    def get_sim_packages(cls, flat: bool = False, limit: Optional[int] = None,
                        page: Optional[int] = None) -> Optional[Dict]:
        """
        Get SIM-only packages.

        Args:
            flat: If True, return flattened response
            limit: Number of results per page
            page: Page number

        Returns:
            Packages data or None
        """
        cls._check_initialized()
        return cls._packages.get_sim_packages(flat, limit, page)

    @classmethod
    def get_local_packages(cls, flat: bool = False, limit: Optional[int] = None,
                          page: Optional[int] = None) -> Optional[Dict]:
        """
        Get local packages.

        Args:
            flat: If True, return flattened response
            limit: Number of results per page
            page: Page number

        Returns:
            Packages data or None
        """
        cls._check_initialized()
        return cls._packages.get_local_packages(flat, limit, page)

    @classmethod
    def get_global_packages(cls, flat: bool = False, limit: Optional[int] = None,
                           page: Optional[int] = None) -> Optional[Dict]:
        """
        Get global packages.

        Args:
            flat: If True, return flattened response
            limit: Number of results per page
            page: Page number

        Returns:
            Packages data or None
        """
        cls._check_initialized()
        return cls._packages.get_global_packages(flat, limit, page)

    @classmethod
    def get_country_packages(cls, country_code: str, flat: bool = False,
                            limit: Optional[int] = None) -> Optional[Dict]:
        """
        Get packages for a specific country.

        Args:
            country_code: ISO country code
            flat: If True, return flattened response
            limit: Number of results

        Returns:
            Packages data or None
        """
        cls._check_initialized()
        return cls._packages.get_country_packages(country_code, flat, limit)

    # =====================================================
    # Order Methods
    # =====================================================

    @classmethod
    def order(cls, package_id: str, quantity: int,
             description: Optional[str] = None) -> Optional[Dict]:
        """
        Create an order.

        Args:
            package_id: Package ID to order
            quantity: Number of SIMs
            description: Order description

        Returns:
            Order data or None
        """
        cls._check_initialized()
        return cls._order.create_order({
            'package_id': package_id,
            'quantity': quantity,
            'type': 'sim',
            'description': description or 'Order placed via Airalo Python SDK'
        })

    @classmethod
    def order_with_email_sim_share(cls, package_id: str, quantity: int,
                                   esim_cloud: Dict[str, Any],
                                   description: Optional[str] = None) -> Optional[Dict]:
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
        cls._check_initialized()
        return cls._order.create_order_with_email_sim_share(
            {
                'package_id': package_id,
                'quantity': quantity,
                'type': 'sim',
                'description': description or 'Order placed via Airalo Python SDK'
            },
            esim_cloud
        )

    @classmethod
    def order_async(cls, package_id: str, quantity: int,
                   webhook_url: Optional[str] = None,
                   description: Optional[str] = None) -> Optional[Dict]:
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
        cls._check_initialized()
        return cls._order.create_order_async({
            'package_id': package_id,
            'quantity': quantity,
            'type': 'sim',
            'webhook_url': webhook_url,
            'description': description or 'Order placed via Airalo Python SDK'
        })

    @classmethod
    def order_bulk(cls, packages: Union[Dict[str, int], List[Dict]],
                  description: Optional[str] = None) -> Optional[Dict]:
        """
        Create bulk orders.

        Args:
            packages: Package IDs and quantities
            description: Order description

        Returns:
            Order data or None
        """
        cls._check_initialized()
        if not packages:
            return None
        return cls._order.create_order_bulk(packages, description)

    @classmethod
    def order_bulk_with_email_sim_share(cls, packages: Union[Dict[str, int], List[Dict]],
                                        esim_cloud: Dict[str, Any],
                                        description: Optional[str] = None) -> Optional[Dict]:
        """
        Create bulk orders with email SIM sharing.

        Args:
            packages: Package IDs and quantities
            esim_cloud: Email sharing configuration
            description: Order description

        Returns:
            Order data or None
        """
        cls._check_initialized()
        if not packages:
            return None
        return cls._order.create_order_bulk_with_email_sim_share(packages, esim_cloud, description)

    @classmethod
    def order_async_bulk(cls, packages: Union[Dict[str, int], List[Dict]],
                        webhook_url: Optional[str] = None,
                        description: Optional[str] = None) -> Optional[Dict]:
        """
        Create bulk asynchronous orders.

        Args:
            packages: Package IDs and quantities
            webhook_url: Webhook URL for notifications
            description: Order description

        Returns:
            Order data or None
        """
        cls._check_initialized()
        if not packages:
            return None
        return cls._order.create_order_async_bulk(packages, webhook_url, description)

    @classmethod
    def topup(
        cls, package_id: str, iccid: str, description: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create a top-up for a SIM.

        Args:
            package_id: Package ID to top-up
            iccid: ICCID of the SIM to top-up
            description: Top-up description
        Returns:
            Top-up data or None
        """
        cls._check_initialized()

        return cls._topup.create_topup(
            {
                "package_id": package_id,
                "iccid": iccid,
                "description": description or "Topup placed via Airalo Python SDK",
            }
        )

    # =====================================================
    # Utility Methods
    # =====================================================

    @classmethod
    def get_config(cls) -> Config:
        """
        Get current configuration.

        Returns:
            Configuration object
        """
        cls._check_initialized()
        return cls._config

    @classmethod
    def get_environment(cls) -> str:
        """
        Get current environment.

        Returns:
            Environment name ('sandbox' or 'production')
        """
        cls._check_initialized()
        return cls._config.get_environment()

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached data."""
        from .helpers.cached import Cached
        Cached.clear_cache()

    @classmethod
    def reset(cls) -> None:
        """Reset the static client to uninitialized state."""
        cls._pool = {}
        cls._config = None
        cls._http = None
        cls._multi_http = None
        cls._signature = None
        cls._oauth = None
        cls._access_token = None
        cls._packages = None
        cls._order = None
        # Reset other services as they're added

    # =====================================================
    # Installation Instruction Methods
    # =====================================================

    @classmethod
    def get_installation_instructions(cls, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Get installation instructions for a given ICCID and language.

        Args:
            params: Dictionary with at least 'iccid' key, optionally 'language'.

        Returns:
            EasyAccess-wrapped data or None
        """
        cls._check_initialized()
        return cls._installation_instructions.get_instructions(params or {})

    # =====================================================
    # Future Order Methods
    # =====================================================

    @classmethod
    def create_future_order(cls, payload: Dict[str, Any]) -> Optional[Dict]:
        """
        Create a future order.

        Args:
            payload: Dictionary containing order details.

        Returns:
            Response data as dictionary or None.
        """
        cls._check_initialized()
        return cls._future_orders.create_future_order(payload)

    @classmethod
    def cancel_future_order(cls, payload: Dict[str, Any]) -> Optional[Dict]:
        """
        Cancel a future order.

        Args:
            payload: Dictionary containing cancellation details.

        Returns:
            Response data as dictionary or None.
        """
        cls._check_initialized()
        return cls._future_orders.cancel_future_order(payload)
