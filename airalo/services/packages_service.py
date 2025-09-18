"""
Packages Service Module

This module handles all package-related API operations.
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from ..config import Config
from ..constants.api_constants import ApiConstants
from ..exceptions.airalo_exception import AiraloException, APIError
from ..helpers.cached import Cached
from ..resources.http_resource import HttpResource


class PackagesService:
    """
    Service for managing package operations.

    Handles fetching packages with various filters, pagination, and caching.
    """

    def __init__(self, config: Config, http_resource: HttpResource, access_token: str):
        """
        Initialize packages service.

        Args:
            config: SDK configuration
            http_resource: HTTP client
            access_token: API access token

        Raises:
            AiraloException: If access token is invalid
        """
        if not access_token:
            raise AiraloException("Invalid access token, please check your credentials")

        self._config = config
        self._http = http_resource
        self._access_token = access_token
        self._base_url = config.get_url()

    def get_packages(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get packages with optional filters.

        Args:
            params: Query parameters including:
                - flat: If True, return flattened response
                - limit: Number of results per page
                - page: Page number
                - type: 'local' or 'global'
                - country: Country code filter
                - simOnly: If True, exclude topup packages

        Returns:
            Packages data or None if no results
        """
        params = params or {}
        url = self._build_url(params)

        # Generate cache key
        cache_key = self._get_cache_key(url, params)

        # Try to get from cache
        result = Cached.get(
            lambda: self._fetch_packages(url, params),
            cache_key,
            ttl=3600,  # Cache for 1 hour
        )

        # Return None if no data
        if not result or not result.get("data"):
            return None

        return result

    def _fetch_packages(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch packages from API with pagination support.

        Args:
            url: API URL
            params: Query parameters

        Returns:
            Combined packages data
        """
        current_page = params.get("page") or 1
        limit = params.get("limit")
        result = {"data": []}

        while True:
            # Build page URL
            page_url = f"{url}&page={current_page}" if current_page else url

            # Make request
            self._http.set_headers({"Authorization": f"Bearer {self._access_token}"})

            response = self._http.get(page_url)

            if not response:
                return result

            # Parse response
            try:
                response_data = json.loads(response)
            except json.JSONDecodeError:
                return result

            # Check for data
            if not response_data.get("data"):
                break

            # Append data
            result["data"].extend(response_data["data"])

            # Check if we've reached the limit
            if limit and len(result["data"]) >= limit:
                result["data"] = result["data"][:limit]
                break

            # Check for more pages
            meta = response_data.get("meta", {})
            last_page = meta.get("last_page", current_page)

            if current_page >= last_page:
                break

            current_page += 1

        # Flatten if requested
        if params.get("flat"):
            result = self._flatten(result)

        return result

    def _build_url(self, params: Dict[str, Any]) -> str:
        """
        Build API URL with query parameters.

        Args:
            params: Query parameters

        Returns:
            Complete URL
        """
        url = self._base_url + ApiConstants.PACKAGES_SLUG + "?"

        query_params = {}

        # Include topup packages by default (unless simOnly is True)
        if not params.get("simOnly"):
            query_params["include"] = "topup"

        # Add filters
        if params.get("type") == "local":
            query_params["filter[type]"] = "local"
        elif params.get("type") == "global":
            query_params["filter[type]"] = "global"

        if params.get("country"):
            query_params["filter[country]"] = params["country"].upper()

        if params.get("limit") and params["limit"] > 0:
            query_params["limit"] = params["limit"]

        # Build query string
        if query_params:
            url += urlencode(query_params)

        return url

    def _flatten(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten nested package structure.

        Args:
            data: Nested package data

        Returns:
            Flattened package data
        """
        flattened = {"data": []}

        for item in data.get("data", []):
            # Each item represents a country/region
            for operator in item.get("operators", []):
                # Extract country codes
                countries = [
                    country.get("country_code")
                    for country in operator.get("countries", [])
                ]

                # Process each package
                for package in operator.get("packages", []):
                    image = operator.get("image", {})

                    flattened_package = {
                        "package_id": package.get("id"),
                        "slug": item.get("slug"),
                        "type": package.get("type"),
                        "price": package.get("price"),
                        "net_price": package.get("net_price"),
                        "amount": package.get("amount"),
                        "day": package.get("day"),
                        "is_unlimited": package.get("is_unlimited"),
                        "title": package.get("title"),
                        "data": package.get("data"),
                        "short_info": package.get("short_info"),
                        "voice": package.get("voice"),
                        "text": package.get("text"),
                        "plan_type": operator.get("plan_type"),
                        "activation_policy": operator.get("activation_policy"),
                        "operator": {
                            "title": operator.get("title"),
                            "is_roaming": operator.get("is_roaming"),
                            "info": operator.get("info"),
                        },
                        "countries": countries,
                        "image": image.get("url") if image else None,
                        "other_info": operator.get("other_info"),
                    }
                    flattened["data"].append(flattened_package)

        return flattened

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
            "token": self._access_token[:20],  # Use partial token for key
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"packages_{hashlib.md5(key_string.encode()).hexdigest()}"

    # Convenience methods for common queries

    def get_all_packages(
        self,
        flat: bool = False,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get all available packages.

        Args:
            flat: If True, return flattened response
            limit: Number of results
            page: Page number

        Returns:
            Packages data or None
        """
        return self.get_packages({"flat": flat, "limit": limit, "page": page})

    def get_sim_packages(
        self,
        flat: bool = False,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get SIM-only packages (excludes topups).

        Args:
            flat: If True, return flattened response
            limit: Number of results
            page: Page number

        Returns:
            Packages data or None
        """
        return self.get_packages(
            {"flat": flat, "limit": limit, "page": page, "simOnly": True}
        )

    def get_local_packages(
        self,
        flat: bool = False,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get local packages only.

        Args:
            flat: If True, return flattened response
            limit: Number of results
            page: Page number

        Returns:
            Packages data or None
        """
        return self.get_packages(
            {"flat": flat, "limit": limit, "page": page, "type": "local"}
        )

    def get_global_packages(
        self,
        flat: bool = False,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get global packages only.

        Args:
            flat: If True, return flattened response
            limit: Number of results
            page: Page number

        Returns:
            Packages data or None
        """
        return self.get_packages(
            {"flat": flat, "limit": limit, "page": page, "type": "global"}
        )

    def get_country_packages(
        self, country_code: str, flat: bool = False, limit: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get packages for a specific country.

        Args:
            country_code: ISO country code (e.g., 'US', 'GB')
            flat: If True, return flattened response
            limit: Number of results

        Returns:
            Packages data or None
        """
        return self.get_packages(
            {"flat": flat, "limit": limit, "country": country_code.upper()}
        )
