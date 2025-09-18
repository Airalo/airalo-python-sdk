"""
Order Service Module

This module handles all order-related API operations including single orders,
bulk orders, and asynchronous orders.
"""

import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

from ..config import Config
from ..constants.api_constants import ApiConstants
from ..constants.sdk_constants import SdkConstants
from ..exceptions.airalo_exception import AiraloException, ValidationError, APIError
from ..helpers.signature import Signature
from ..helpers.cloud_sim_share_validator import CloudSimShareValidator
from ..resources.http_resource import HttpResource
from ..resources.multi_http_resource import MultiHttpResource


class OrderService:
    """
    Service for managing order operations.

    Handles single orders, bulk orders, async orders, and email SIM sharing.
    """

    def __init__(
        self,
        config: Config,
        http_resource: HttpResource,
        multi_http_resource: MultiHttpResource,
        signature: Signature,
        access_token: str,
    ):
        """
        Initialize order service.

        Args:
            config: SDK configuration
            http_resource: HTTP client for single requests
            multi_http_resource: HTTP client for concurrent requests
            signature: Signature generator for request signing
            access_token: API access token

        Raises:
            AiraloException: If access token is invalid
        """
        if not access_token:
            raise AiraloException("Invalid access token, please check your credentials")

        self._config = config
        self._http = http_resource
        self._multi_http = multi_http_resource
        self._signature = signature
        self._access_token = access_token
        self._base_url = config.get_url()

    def create_order(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a single order.

        Args:
            payload: Order data including:
                - package_id: Package ID to order
                - quantity: Number of SIMs (1-50)
                - type: Order type (default: 'sim')
                - description: Order description

        Returns:
            Order response data or None

        Raises:
            ValidationError: If payload is invalid
            APIError: If API request fails
        """
        self._validate_order(payload)

        # Set default type if not provided
        if "type" not in payload:
            payload["type"] = "sim"

        # Set headers with signature
        headers = self._get_headers(payload)
        self._http.set_headers(headers)

        # Make request
        url = self._base_url + ApiConstants.ORDERS_SLUG
        response = self._http.post(url, payload)

        # Check response
        if self._http.code != 200:
            raise APIError(
                f"Order creation failed, status code: {self._http.code}, response: {response}"
            )

        # Parse and return response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise APIError("Failed to parse order response")

    def create_order_with_email_sim_share(
        self, payload: Dict[str, Any], esim_cloud: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create an order with email SIM sharing.

        Args:
            payload: Order data
            esim_cloud: Email sharing configuration:
                - to_email: Recipient email (required)
                - sharing_option: List of options ['link', 'pdf'] (required)
                - copy_address: List of CC emails (optional)

        Returns:
            Order response data or None
        """
        self._validate_order(payload)
        self._validate_cloud_sim_share(esim_cloud)

        # Add email sharing to payload
        payload["to_email"] = esim_cloud["to_email"]
        payload["sharing_option"] = esim_cloud["sharing_option"]

        if esim_cloud.get("copy_address"):
            payload["copy_address"] = esim_cloud["copy_address"]

        # Set default type
        if "type" not in payload:
            payload["type"] = "sim"

        # Make request
        headers = self._get_headers(payload)
        self._http.set_headers(headers)

        url = self._base_url + ApiConstants.ORDERS_SLUG
        response = self._http.post(url, payload)

        if self._http.code != 200:
            raise APIError(
                f"Order creation failed, status code: {self._http.code}, response: {response}"
            )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise APIError("Failed to parse order response")

    def create_order_async(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create an asynchronous order.

        Args:
            payload: Order data including:
                - package_id: Package ID to order
                - quantity: Number of SIMs
                - webhook_url: URL for order completion notification
                - description: Order description

        Returns:
            Order response data or None
        """
        self._validate_order(payload)

        # Set default type
        if "type" not in payload:
            payload["type"] = "sim"

        # Make request
        headers = self._get_headers(payload)
        self._http.set_headers(headers)

        url = self._base_url + ApiConstants.ASYNC_ORDERS_SLUG
        response = self._http.post(url, payload)

        # Async orders return 202 Accepted
        if self._http.code != 202:
            raise APIError(
                f"Async order creation failed, status code: {self._http.code}, response: {response}"
            )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise APIError("Failed to parse order response")

    def create_order_bulk(
        self,
        packages: Union[Dict[str, int], List[Dict]],
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create multiple orders in bulk.

        Args:
            packages: Either:
                - Dict mapping package_id to quantity
                - List of dicts with 'package_id' and 'quantity' keys
            description: Order description for all orders

        Returns:
            Dict mapping package IDs to order responses
        """
        # Convert list format to dict format
        if isinstance(packages, list):
            packages_dict = {}
            for item in packages:
                packages_dict[item["package_id"]] = item["quantity"]
            packages = packages_dict

        self._validate_bulk_order(packages)

        if not packages:
            return None

        # Prepare concurrent requests
        for package_id, quantity in packages.items():
            payload = {
                "package_id": package_id,
                "quantity": quantity,
                "type": "sim",
                "description": description or "Bulk order placed via Airalo Python SDK",
            }

            self._validate_order(payload)

            # Add request to multi-http queue
            headers = self._get_headers(payload)
            self._multi_http.tag(package_id).set_headers(headers).post(
                self._base_url + ApiConstants.ORDERS_SLUG, payload
            )

        # Execute all requests
        responses = self._multi_http.exec()

        if not responses:
            return None

        # Parse responses
        result = {}
        for package_id, response in responses.items():
            try:
                result[package_id] = json.loads(response)
            except json.JSONDecodeError:
                result[package_id] = {
                    "error": "Failed to parse response",
                    "raw": response,
                }

        return result

    def create_order_bulk_with_email_sim_share(
        self,
        packages: Union[Dict[str, int], List[Dict]],
        esim_cloud: Dict[str, Any],
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create bulk orders with email SIM sharing.

        Args:
            packages: Package IDs and quantities
            esim_cloud: Email sharing configuration
            description: Order description

        Returns:
            Dict mapping package IDs to order responses
        """
        # Convert list format to dict format
        if isinstance(packages, list):
            packages_dict = {}
            for item in packages:
                packages_dict[item["package_id"]] = item["quantity"]
            packages = packages_dict

        self._validate_bulk_order(packages)
        self._validate_cloud_sim_share(esim_cloud)

        if not packages:
            return None

        # Prepare concurrent requests
        for package_id, quantity in packages.items():
            payload = {
                "package_id": package_id,
                "quantity": quantity,
                "type": "sim",
                "description": description or "Bulk order placed via Airalo Python SDK",
                "to_email": esim_cloud["to_email"],
                "sharing_option": esim_cloud["sharing_option"],
            }

            if esim_cloud.get("copy_address"):
                payload["copy_address"] = esim_cloud["copy_address"]

            self._validate_order(payload)

            # Add request to queue
            headers = self._get_headers(payload)
            self._multi_http.tag(package_id).set_headers(headers).post(
                self._base_url + ApiConstants.ORDERS_SLUG, payload
            )

        # Execute all requests
        responses = self._multi_http.exec()

        if not responses:
            return None

        # Parse responses
        result = {}
        for package_id, response in responses.items():
            try:
                result[package_id] = json.loads(response)
            except json.JSONDecodeError:
                result[package_id] = {
                    "error": "Failed to parse response",
                    "raw": response,
                }

        return result

    def create_order_async_bulk(
        self,
        packages: Union[Dict[str, int], List[Dict]],
        webhook_url: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create multiple asynchronous orders in bulk.

        Args:
            packages: Package IDs and quantities
            webhook_url: Webhook URL for notifications
            description: Order description

        Returns:
            Dict mapping package IDs to order responses
        """
        # Convert list format to dict format
        if isinstance(packages, list):
            packages_dict = {}
            for item in packages:
                packages_dict[item["package_id"]] = item["quantity"]
            packages = packages_dict

        self._validate_bulk_order(packages)

        if not packages:
            return None

        # Prepare concurrent requests
        for package_id, quantity in packages.items():
            payload = {
                "package_id": package_id,
                "quantity": quantity,
                "type": "sim",
                "description": description
                or "Bulk async order placed via Airalo Python SDK",
                "webhook_url": webhook_url,
            }

            self._validate_order(payload)

            # Add request to queue
            headers = self._get_headers(payload)
            self._multi_http.tag(package_id).set_headers(headers).post(
                self._base_url + ApiConstants.ASYNC_ORDERS_SLUG, payload
            )

        # Execute all requests
        responses = self._multi_http.exec()

        if not responses:
            return None

        # Parse responses
        result = {}
        for package_id, response in responses.items():
            try:
                result[package_id] = json.loads(response)
            except json.JSONDecodeError:
                result[package_id] = {
                    "error": "Failed to parse response",
                    "raw": response,
                }

        return result

    def _get_headers(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Get headers for order request with signature.

        Args:
            payload: Request payload

        Returns:
            Headers dictionary
        """
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "airalo-signature": self._signature.get_signature(payload),
        }

    def _validate_order(self, payload: Dict[str, Any]) -> None:
        """
        Validate order payload.

        Args:
            payload: Order data

        Raises:
            ValidationError: If validation fails
        """
        if not payload.get("package_id"):
            raise ValidationError(
                f"The package_id is required, payload: {json.dumps(payload)}"
            )

        quantity = payload.get("quantity", 0)
        if quantity < 1:
            raise ValidationError(
                f"The quantity must be at least 1, payload: {json.dumps(payload)}"
            )

        if quantity > SdkConstants.ORDER_LIMIT:
            raise ValidationError(
                f"The quantity may not be greater than {SdkConstants.ORDER_LIMIT}, "
                f"payload: {json.dumps(payload)}"
            )

    def _validate_bulk_order(self, packages: Dict[str, int]) -> None:
        """
        Validate bulk order payload.

        Args:
            packages: Package IDs and quantities

        Raises:
            ValidationError: If validation fails
        """
        if len(packages) > SdkConstants.BULK_ORDER_LIMIT:
            raise ValidationError(
                f"The packages count may not be greater than {SdkConstants.BULK_ORDER_LIMIT}"
            )

    def _validate_cloud_sim_share(self, sim_cloud_share: Dict[str, Any]) -> None:
        """
        Validate email SIM sharing configuration using CloudSimShareValidator.

        Args:
            sim_cloud_share: Email sharing configuration

        Raises:
            ValidationError: If validation fails
        """
        # Use CloudSimShareValidator with required fields for order service
        CloudSimShareValidator.validate(
            sim_cloud_share, required_fields=["to_email", "sharing_option"]
        )
