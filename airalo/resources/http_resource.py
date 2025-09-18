"""
HTTP Resource Module

This module provides HTTP client functionality using urllib for making API requests.
"""

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlencode

from ..config import Config
from ..constants.sdk_constants import SdkConstants
from ..exceptions.airalo_exception import NetworkError


class HttpResource:
    """
    HTTP client for making API requests.

    Uses urllib for HTTP operations with support for GET, POST, and HEAD methods.
    """

    def __init__(self, config: Config, get_handler: bool = False):
        """
        Initialize HTTP resource.

        Args:
            config: SDK configuration
            get_handler: If True, return request object instead of executing

        Raises:
            NetworkError: If urllib is not available
        """
        self._config = config
        self._get_handler = get_handler
        self._ignore_ssl = False
        self._timeout = SdkConstants.DEFAULT_TIMEOUT
        self._rfc = 1  # Default to RFC1738 for query encoding

        # Response attributes
        self.header: str = ""
        self.code: int = 0
        self.response_headers: Dict[str, str] = {}

        # Request headers
        self._request_headers: Dict[str, str] = {}
        self._default_headers: Dict[str, str] = {
            "User-Agent": f"Airalo-Python-SDK/{SdkConstants.VERSION}",
            "airalo-python-sdk": f"{SdkConstants.VERSION}",
            "Accept": "application/json",
        }

        # Initialize headers
        self._init_headers()

    def get(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[str, urllib.request.Request]:
        """
        Perform GET request.

        Args:
            url: Request URL
            params: Query parameters

        Returns:
            Response body as string or request object if get_handler is True
        """
        if params:
            # Build query string
            query_string = self._build_query_string(params)
            url = f"{url.rstrip('?')}?{query_string}"

        return self._request(url, method="GET")

    def post(
        self, url: str, params: Optional[Union[Dict[str, Any], str]] = None
    ) -> Union[str, urllib.request.Request]:
        """
        Perform POST request.

        Args:
            url: Request URL
            params: Request body (dict or string)

        Returns:
            Response body as string or request object if get_handler is True
        """
        data = None

        if params:
            if isinstance(params, dict):
                # Check if we should send as JSON or form data
                if (
                    "Content-Type" in self._request_headers
                    and "json" in self._request_headers["Content-Type"]
                ):
                    data = json.dumps(params).encode("utf-8")
                else:
                    data = urlencode(params).encode("utf-8")
            else:
                # Assume it's already a string (could be JSON or form-encoded)
                data = params.encode("utf-8") if isinstance(params, str) else params

        return self._request(url, data=data, method="POST")

    def head(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[str, urllib.request.Request]:
        """
        Perform HEAD request.

        Args:
            url: Request URL
            params: Query parameters

        Returns:
            Response headers as string or request object if get_handler is True
        """
        if params:
            query_string = self._build_query_string(params)
            url = f"{url.rstrip('?')}?{query_string}"

        return self._request(url, method="HEAD")

    def set_headers(self, headers: Union[Dict[str, str], List[str]]) -> "HttpResource":
        """
        Set additional request headers.

        Args:
            headers: Dictionary or list of header strings

        Returns:
            Self for method chaining
        """
        if isinstance(headers, list):
            # Parse list of header strings
            for header in headers:
                if ":" in header:
                    key, value = header.split(":", 1)
                    self._request_headers[key.strip()] = value.strip()
        else:
            # Merge dictionary
            self._request_headers.update(headers)

        return self

    def set_timeout(self, timeout: int = 30) -> "HttpResource":
        """
        Set request timeout.

        Args:
            timeout: Timeout in seconds

        Returns:
            Self for method chaining
        """
        self._timeout = timeout
        return self

    def ignore_ssl(self) -> "HttpResource":
        """
        Ignore SSL certificate verification.

        Returns:
            Self for method chaining
        """
        self._ignore_ssl = True
        return self

    def use_rfc(self, rfc: int) -> "HttpResource":
        """
        Set RFC standard for URL encoding.

        Args:
            rfc: RFC standard (1 for RFC1738, 3 for RFC3986)

        Returns:
            Self for method chaining
        """
        self._rfc = rfc
        return self

    def set_basic_authentication(
        self, username: str, password: str = ""
    ) -> "HttpResource":
        """
        Set HTTP basic authentication.

        Args:
            username: Username
            password: Password

        Returns:
            Self for method chaining
        """
        import base64

        credentials = base64.b64encode(f"{username}:{password}".encode()).decode(
            "ascii"
        )
        self._request_headers["Authorization"] = f"Basic {credentials}"
        return self

    def _request(
        self, url: str, data: Optional[bytes] = None, method: str = "GET"
    ) -> Union[str, urllib.request.Request]:
        """
        Execute HTTP request.

        Args:
            url: Request URL
            data: Request body
            method: HTTP method

        Returns:
            Response body or request object

        Raises:
            NetworkError: If request fails
        """
        # Create request object
        request = urllib.request.Request(url, data=data, method=method)

        # Add headers
        for key, value in self._request_headers.items():
            request.add_header(key, value)

        # Return request object if handler mode
        if self._get_handler:
            return request

        # Configure SSL context
        context = None
        if self._ignore_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        try:
            # Execute request
            response = urllib.request.urlopen(
                request, timeout=self._timeout, context=context
            )

            # Read response
            response_body = response.read().decode("utf-8")

            # Store response details
            self.code = response.getcode()
            self.response_headers = dict(response.headers)
            self.header = str(response.headers)

            # Reset for next request
            self._reset()

            return response_body

        except urllib.error.HTTPError as e:
            # HTTP error (4xx, 5xx)
            self.code = e.code
            self.response_headers = dict(e.headers)
            self.header = str(e.headers)

            # Try to read error response
            try:
                error_body = e.read().decode("utf-8")
                self._reset()
                return error_body
            except:
                self._reset()
                raise NetworkError(f"HTTP {e.code}: {e.reason}", http_status=e.code)

        except urllib.error.URLError as e:
            # Network error
            self._reset()
            raise NetworkError(f"Network error: {e.reason}")

        except Exception as e:
            # Other errors
            self._reset()
            raise NetworkError(f"Request failed: {str(e)}")

    def _init_headers(self) -> None:
        """Initialize request headers with defaults and config headers."""
        self._request_headers = self._default_headers.copy()

        # Add custom headers from config
        config_headers = self._config.get_http_headers()
        if isinstance(config_headers, list):
            for header in config_headers:
                if ":" in header:
                    key, value = header.split(":", 1)
                    self._request_headers[key.strip()] = value.strip()
        elif isinstance(config_headers, dict):
            self._request_headers.update(config_headers)

    def _reset(self) -> None:
        """Reset headers and state for next request."""
        self._init_headers()
        self._ignore_ssl = False
        self._timeout = SdkConstants.DEFAULT_TIMEOUT

    def _build_query_string(self, params: Dict[str, Any]) -> str:
        """
        Build query string from parameters.

        Args:
            params: Query parameters

        Returns:
            URL-encoded query string
        """
        # Use appropriate encoding based on RFC setting
        if self._rfc == 3:
            # RFC3986 - uses %20 for spaces
            return urlencode(params, quote_via=urllib.parse.quote)
        else:
            # RFC1738 - uses + for spaces (default)
            return urlencode(params)
