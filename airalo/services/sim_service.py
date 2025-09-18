"""
SIM Service Module

This module handles all SIM-related API operations including usage tracking,
topup history, and package history.
"""

import json
from typing import Any, Dict, List, Optional

from ..config import Config
from ..helpers.cached import Cached
from ..resources.http_resource import HttpResource
from ..constants.api_constants import ApiConstants
from ..resources.multi_http_resource import MultiHttpResource
from ..exceptions.airalo_exception import AiraloException, APIError


class SimService:
    """
    Service for managing SIM operations.

    Handles SIM usage tracking, bulk usage queries, topup history, and package history.
    """

    def __init__(
        self,
        config: Config,
        http_resource: HttpResource,
        multi_http_resource: MultiHttpResource,
        access_token: str,
    ):
        """
        Initialize SIM service.

        Args:
            config: SDK configuration
            http_resource: HTTP client for single requests
            multi_http_resource: HTTP client for concurrent requests
            access_token: API access token

        Raises:
            AiraloException: If access token is invalid
        """
        if not access_token:
            raise AiraloException("Invalid access token, please check your credentials")

        self._config = config
        self._http = http_resource
        self._multi_http = multi_http_resource
        self._access_token = access_token
        self._base_url = config.get_url()

    def sim_usage(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get SIM usage information.

        Args:
            params: Parameters including:
                - iccid: ICCID of the SIM (required)

        Returns:
            SIM usage data or None

        Raises:
            AiraloException: If ICCID is invalid
        """
        url = self._build_url(params, ApiConstants.SIMS_USAGE)

        # Generate cache key
        cache_key = self._get_cache_key(url, params)

        # Try to get from cache (5 minutes TTL for usage data)
        result = Cached.get(
            lambda: self._fetch_sim_data(url), cache_key, ttl=300  # 5 minutes
        )

        # Return None if no data
        if not result or not result.get("data"):
            return None

        return result

    def sim_usage_bulk(self, iccids: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get usage information for multiple SIMs.

        Args:
            iccids: List of ICCIDs to check

        Returns:
            Dict mapping ICCIDs to usage data or None
        """
        if not iccids:
            return None

        # Generate cache key for bulk request
        cache_key = self._get_cache_key("".join(iccids), {})

        # Try to get from cache
        result = Cached.get(
            lambda: self._fetch_bulk_sim_usage(iccids), cache_key, ttl=300  # 5 minutes
        )

        return result

    def _fetch_bulk_sim_usage(self, iccids: List[str]) -> Optional[Dict[str, Any]]:
        """
        Fetch usage data for multiple SIMs concurrently.

        Args:
            iccids: List of ICCIDs

        Returns:
            Dict mapping ICCIDs to usage data
        """
        # Queue requests for each ICCID
        for iccid in iccids:
            url = self._build_url({"iccid": iccid}, ApiConstants.SIMS_USAGE)

            self._multi_http.tag(iccid).set_headers(
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._access_token}",
                }
            ).get(url)

        # Execute all requests
        responses = self._multi_http.exec()

        if not responses:
            return None

        # Parse responses
        result = {}
        for iccid, response in responses.items():
            try:
                result[iccid] = json.loads(response)
            except json.JSONDecodeError:
                result[iccid] = {"error": "Failed to parse response", "raw": response}

        return result

    def sim_topups(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get SIM topup history.

        Args:
            params: Parameters including:
                - iccid: ICCID of the SIM (required)

        Returns:
            SIM topup history or None

        Raises:
            AiraloException: If ICCID is invalid
        """
        url = self._build_url(params, ApiConstants.SIMS_TOPUPS)

        # Generate cache key
        cache_key = self._get_cache_key(url, params)

        # Try to get from cache (5 minutes TTL)
        result = Cached.get(
            lambda: self._fetch_sim_data(url), cache_key, ttl=300  # 5 minutes
        )

        # Return None if no data
        if not result or not result.get("data"):
            return None

        return result

    def sim_package_history(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get SIM package history.

        Args:
            params: Parameters including:
                - iccid: ICCID of the SIM (required)

        Returns:
            SIM package history or None

        Raises:
            AiraloException: If ICCID is invalid
        """
        url = self._build_url(params, ApiConstants.SIMS_PACKAGES)

        # Generate cache key
        cache_key = self._get_cache_key(url, params)

        # Try to get from cache (15 minutes TTL for package history)
        result = Cached.get(
            lambda: self._fetch_sim_data(url), cache_key, ttl=900  # 15 minutes
        )

        # Return None if no data
        if not result or not result.get("data"):
            return None

        return result

    def _fetch_sim_data(self, url: str) -> Dict[str, Any]:
        """
        Fetch SIM data from API.

        Args:
            url: API URL

        Returns:
            SIM data
        """
        # Make request
        self._http.set_headers(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._access_token}",
            }
        )

        response = self._http.get(url)

        if not response:
            return {"data": None}

        # Parse response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"data": None}

    def _build_url(self, params: Dict[str, Any], endpoint: Optional[str] = None) -> str:
        """
        Build API URL for SIM operations.

        Args:
            params: Parameters including ICCID
            endpoint: Specific endpoint (usage, topups, packages)

        Returns:
            Complete URL

        Raises:
            AiraloException: If ICCID is invalid
        """
        if "iccid" not in params or not self._is_valid_iccid(params["iccid"]):
            raise AiraloException(f"Invalid or missing ICCID: {params.get('iccid')}")

        iccid = str(params["iccid"])

        # Build URL
        url = f"{self._base_url}{ApiConstants.SIMS_SLUG}/{iccid}"

        if endpoint:
            url = f"{url}/{endpoint}"

        return url

    def _is_valid_iccid(self, iccid: Any) -> bool:
        """
        Validate ICCID format.

        Args:
            iccid: ICCID to validate

        Returns:
            True if valid, False otherwise
        """
        if not iccid:
            return False

        # Convert to string and check
        iccid_str = str(iccid)

        # ICCID should be 18-22 digits
        return iccid_str.isdigit() and 18 <= len(iccid_str) <= 22

    def _get_cache_key(self, url: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key for request.

        Args:
            url: Request URL
            params: Request parameters

        Returns:
            Cache key
        """
        import hashlib

        key_data = {
            "url": url,
            "params": params,
            "headers": self._config.get_http_headers(),
            "token": self._access_token[:20] if self._access_token else "",
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"sim_{hashlib.md5(key_string.encode()).hexdigest()}"

    # Convenience methods for cleaner API

    def get_usage(self, iccid: str) -> Optional[Dict[str, Any]]:
        """
        Get SIM usage (convenience method).

        Args:
            iccid: ICCID of the SIM

        Returns:
            SIM usage data or None
        """
        return self.sim_usage({"iccid": iccid})

    def get_usage_bulk(self, iccids: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get usage for multiple SIMs (convenience method).

        Args:
            iccids: List of ICCIDs

        Returns:
            Usage data for all SIMs
        """
        return self.sim_usage_bulk(iccids)

    def get_topups(self, iccid: str) -> Optional[Dict[str, Any]]:
        """
        Get SIM topup history (convenience method).

        Args:
            iccid: ICCID of the SIM

        Returns:
            Topup history or None
        """
        return self.sim_topups({"iccid": iccid})

    def get_package_history(self, iccid: str) -> Optional[Dict[str, Any]]:
        """
        Get SIM package history (convenience method).

        Args:
            iccid: ICCID of the SIM

        Returns:
            Package history or None
        """
        return self.sim_package_history({"iccid": iccid})
