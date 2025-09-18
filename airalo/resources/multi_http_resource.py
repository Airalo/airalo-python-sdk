"""
Multi HTTP Resource Module

This module provides concurrent HTTP request functionality using ThreadPoolExecutor.
"""

import concurrent.futures
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple, Union

from ..config import Config
from ..constants.sdk_constants import SdkConstants
from ..exceptions.airalo_exception import NetworkError


class MultiHttpResource:
    """
    Concurrent HTTP client for making multiple API requests in parallel.

    Uses ThreadPoolExecutor for concurrent request execution.
    """

    def __init__(self, config: Config):
        """
        Initialize multi HTTP resource.

        Args:
            config: SDK configuration
        """
        self._config = config
        self._handlers: List[Dict[str, Any]] = []
        self._headers: Dict[str, str] = {}
        self._options: Dict[str, Any] = {}
        self._ignore_ssl = False
        self._timeout = SdkConstants.DEFAULT_TIMEOUT
        self._tag: Optional[str] = None
        self._max_workers = SdkConstants.MAX_CONCURRENT_REQUESTS

        # Default headers
        self._default_headers: Dict[str, str] = {
            "User-Agent": f"Airalo-Python-SDK/{SdkConstants.VERSION}",
            "airalo-python-sdk": f"{SdkConstants.VERSION}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def add(self, method_name: str, args: List[Any]) -> "MultiHttpResource":
        """
        Add a request to the queue.

        Args:
            method_name: HTTP method name ('get', 'post', 'head')
            args: Method arguments [url, params]

        Returns:
            Self for method chaining
        """
        from .http_resource import HttpResource

        # Create HTTP resource for this request
        http_resource = HttpResource(self._config, get_handler=True)

        if self._ignore_ssl:
            http_resource.ignore_ssl()

        if self._timeout != SdkConstants.DEFAULT_TIMEOUT:
            http_resource.set_timeout(self._timeout)

        if self._headers:
            http_resource.set_headers(self._headers)

        # Get the method and create request
        method = getattr(http_resource, method_name)
        request = method(*args)

        # Store request with metadata
        handler = {
            "request": request,
            "tag": self._tag if self._tag else len(self._handlers),
            "options": self._options.copy(),
            "ignore_ssl": self._ignore_ssl,
            "timeout": self._timeout,
            "headers": self._merge_headers(),
        }

        self._handlers.append(handler)
        self._tag = None

        return self

    def get(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> "MultiHttpResource":
        """
        Add GET request to queue.

        Args:
            url: Request URL
            params: Query parameters

        Returns:
            Self for method chaining
        """
        return self.add("get", [url, params])

    def post(
        self, url: str, params: Optional[Union[Dict[str, Any], str]] = None
    ) -> "MultiHttpResource":
        """
        Add POST request to queue.

        Args:
            url: Request URL
            params: Request body

        Returns:
            Self for method chaining
        """
        return self.add("post", [url, params])

    def tag(self, name: str = "") -> "MultiHttpResource":
        """
        Set tag for next request.

        Args:
            name: Tag name

        Returns:
            Self for method chaining
        """
        if name:
            self._tag = name
        return self

    def set_headers(
        self, headers: Union[Dict[str, str], List[str]]
    ) -> "MultiHttpResource":
        """
        Set headers for all requests.

        Args:
            headers: Request headers

        Returns:
            Self for method chaining
        """
        if isinstance(headers, list):
            # Parse list of header strings
            for header in headers:
                if ":" in header:
                    key, value = header.split(":", 1)
                    self._headers[key.strip()] = value.strip()
        else:
            self._headers.update(headers)

        return self

    def set_timeout(self, timeout: int = 30) -> "MultiHttpResource":
        """
        Set timeout for all requests.

        Args:
            timeout: Timeout in seconds

        Returns:
            Self for method chaining
        """
        self._timeout = timeout
        return self

    def ignore_ssl(self) -> "MultiHttpResource":
        """
        Ignore SSL verification for all requests.

        Returns:
            Self for method chaining
        """
        self._ignore_ssl = True
        return self

    def setopt(self, options: Dict[str, Any]) -> "MultiHttpResource":
        """
        Set additional options for requests.

        Args:
            options: Request options

        Returns:
            Self for method chaining
        """
        self._options = options
        return self

    def exec(self) -> Dict[Union[str, int], str]:
        """
        Execute all queued requests concurrently.

        Returns:
            Dictionary mapping tags to response bodies
        """
        if not self._handlers:
            return {}

        responses = {}

        # Use ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_workers
        ) as executor:
            # Submit all requests
            future_to_tag = {}
            for handler in self._handlers:
                future = executor.submit(self._execute_request, handler)
                future_to_tag[future] = handler["tag"]

            # Collect results
            for future in concurrent.futures.as_completed(future_to_tag):
                tag = future_to_tag[future]
                try:
                    response = future.result()
                    responses[tag] = response
                except Exception as e:
                    # Store error as response
                    responses[tag] = json.dumps(
                        {"error": str(e), "type": type(e).__name__}
                    )

        # Clear handlers after execution
        self._handlers = []
        self._headers = {}
        self._options = {}
        self._ignore_ssl = False
        self._timeout = SdkConstants.DEFAULT_TIMEOUT

        return responses

    def _execute_request(self, handler: Dict[str, Any]) -> str:
        """
        Execute a single request.

        Args:
            handler: Request handler dictionary

        Returns:
            Response body

        Raises:
            NetworkError: If request fails
        """
        request = handler["request"]

        # Apply headers
        if isinstance(request, urllib.request.Request):
            for key, value in handler["headers"].items():
                request.add_header(key, value)

        # Configure SSL context
        context = None
        if handler["ignore_ssl"]:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        try:
            # Execute request
            response = urllib.request.urlopen(
                request, timeout=handler["timeout"], context=context
            )

            # Read and return response
            return response.read().decode("utf-8")

        except urllib.error.HTTPError as e:
            # Try to read error response
            try:
                return e.read().decode("utf-8")
            except:
                raise NetworkError(f"HTTP {e.code}: {e.reason}", http_status=e.code)

        except urllib.error.URLError as e:
            raise NetworkError(f"Network error: {e.reason}")

        except Exception as e:
            raise NetworkError(f"Request failed: {str(e)}")

    def _merge_headers(self) -> Dict[str, str]:
        """
        Merge default, config, and request headers.

        Returns:
            Merged headers dictionary
        """
        headers = self._default_headers.copy()

        # Add config headers
        config_headers = self._config.get_http_headers()
        if isinstance(config_headers, list):
            for header in config_headers:
                if ":" in header:
                    key, value = header.split(":", 1)
                    headers[key.strip()] = value.strip()
        elif isinstance(config_headers, dict):
            headers.update(config_headers)

        # Add request-specific headers
        headers.update(self._headers)

        return headers
