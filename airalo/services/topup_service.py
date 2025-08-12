"""
Topup Service Module

This module handles top-up related API operations including creating top-ups.
"""

import json
from typing import Any, Dict, Optional

from ..config import Config
from ..constants.api_constants import ApiConstants
from ..exceptions.airalo_exception import AiraloException, ValidationError, APIError
from ..helpers.signature import Signature
from ..resources.http_resource import HttpResource


class TopupService:
    """
    Service for managing top-up operations.
    """

    def __init__(
        self,
        config: Config,
        http_resource: HttpResource,
        signature: Signature,
        access_token: str,
    ):
        """
        Initialize top-up service.

        Args:
            config: SDK configuration
            http_resource: HTTP client for requests
            signature: Signature generator for request signing
            access_token: API access token

        Raises:
            AiraloException: If access token is invalid
        """
        if not access_token:
            raise AiraloException("Invalid access token, please check your credentials")

        self._config = config
        self._http = http_resource
        self._signature = signature
        self._access_token = access_token
        self._base_url = config.get_url()

    def create_topup(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new top-up.

        Args:
            payload: Top-up data including:
                - package_id: Package ID to top-up (required)
                - iccid: ICCID of the SIM to top-up (required)

        Returns:
            Top-up response data or None

        Raises:
            ValidationError: If payload is invalid
            APIError: If API request fails
        """
        self._validate_topup(payload)

        # Set headers with signature
        headers = self._get_headers(payload)
        self._http.set_headers(headers)

        # Make request
        url = self._base_url + ApiConstants.TOPUPS_SLUG
        response = self._http.post(url, payload)

        if self._http.code != 200:
            raise APIError(
                f"Topup creation failed, status code: {self._http.code}, response: {response}"
            )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise APIError("Failed to parse top-up response")

    def _get_headers(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Get headers for top-up request with signature.

        Args:
            payload: Request payload

        Returns:
            Headers dictionary
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}",
            "airalo-signature": self._signature.get_signature(payload),
        }

    def _validate_topup(self, payload: Dict[str, Any]) -> None:
        """
        Validate top-up payload.

        Args:
            payload: Top-up data

        Raises:
            ValidationError: If validation fails
        """
        if not payload.get("package_id"):
            raise ValidationError(
                f"The package_id is required, payload: {json.dumps(payload)}"
            )

        iccid = payload.get("iccid")

        if not iccid:
            raise ValidationError(
                f"The iccid is required, payload: {json.dumps(payload)}"
            )

        if len(iccid) < 16 or len(iccid) > 21:
            raise ValidationError(
                f"The iccid must be between 16 and 21 characters, received: {iccid}"
            )
