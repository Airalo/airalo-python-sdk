"""
Caching Helper Module

This module provides file-based caching functionality for the SDK.
"""

import hashlib
import os
import pickle
import tempfile
import time
from ..constants.sdk_constants import SdkConstants
from pathlib import Path
from typing import Any, Callable, Optional, Union


class Cached:
    """
    File-based caching utility.

    Provides simple file-based caching with TTL support using
    project root cache directory.
    """

    CACHE_KEY_PREFIX = "airalo_"

    _cache_path: Optional[Path] = None
    _cache_name: str = ""

    @classmethod
    def get(
        cls, work: Union[Callable[[], Any], Any], cache_name: str, ttl: int = 0
    ) -> Any:
        """
        Get cached value or compute and cache it.

        Args:
            work: Callable that produces the value, or the value itself
            cache_name: Unique name for this cache entry
            ttl: Time-to-live in seconds (0 uses default)

        Returns:
            Cached or computed value
        """
        cls._init(cache_name)

        cache_id = cls._get_id(cache_name)

        # Try to get from cache
        cached_result = cls._cache_get(cache_id, ttl)
        if cached_result is not None:
            return cached_result

        # Compute result
        if callable(work):
            result = work()
        else:
            result = work

        # Cache and return
        return cls._cache_this(cache_id, result)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cache files."""
        cls._init()

        # Find and remove all cache files
        cache_pattern = cls._cache_path / f"{cls.CACHE_KEY_PREFIX}*"
        for cache_file in cls._cache_path.glob(f"{cls.CACHE_KEY_PREFIX}*"):
            try:
                cache_file.unlink()
            except OSError:
                pass  # Ignore errors when deleting cache files

    @classmethod
    def _init(cls, cache_name: str = "") -> None:
        """
        Initialize cache directory and name.

        Args:
            cache_name: Optional cache name to set
        """
        if cls._cache_path is None:
            # Use project root cache directory
            cls._cache_path = Path(__file__).resolve().parent.parent.parent / ".cache"
            cls._cache_path.mkdir(parents=True, exist_ok=True)

        if cache_name:
            cls._cache_name = cache_name

    @classmethod
    def _get_id(cls, key: str) -> str:
        """
        Generate cache file ID from key.

        Args:
            key: Cache key

        Returns:
            Cache file ID
        """
        return cls.CACHE_KEY_PREFIX + hashlib.md5(key.encode()).hexdigest()

    @classmethod
    def _cache_get(cls, cache_id: str, custom_ttl: int = 0) -> Optional[Any]:
        """
        Retrieve value from cache if valid.

        Args:
            cache_id: Cache file ID
            custom_ttl: Custom TTL in seconds

        Returns:
            Cached value or None if not found/expired
        """
        cache_file = cls._cache_path / cache_id

        if not cache_file.exists():
            return None

        # Check TTL
        now = time.time()
        file_mtime = cache_file.stat().st_mtime
        ttl = custom_ttl if custom_ttl > 0 else SdkConstants.DEFAULT_CACHE_TTL

        if now - file_mtime > ttl:
            # Cache expired, remove file
            try:
                cache_file.unlink()
            except OSError:
                return None

        # Read cached data
        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except (OSError, pickle.PickleError):
            # Corrupted cache file, remove it
            try:
                cache_file.unlink()
            except OSError:
                return None

    @classmethod
    def _cache_this(cls, cache_id: str, result: Any) -> Any:
        """
        Store value in cache.

        Args:
            cache_id: Cache file ID
            result: Value to cache

        Returns:
            The cached value
        """
        if result is None:
            return None

        cache_file = cls._cache_path / cache_id

        try:
            # Write cache file
            with open(cache_file, "wb") as f:
                pickle.dump(result, f)

            # Try to set permissions (may fail on some systems)
            try:
                cache_file.chmod(0o666)
            except OSError:
                pass  # Ignore permission errors

        except (OSError, pickle.PickleError) as e:
            # Failed to cache, but return the result anyway
            pass

        return result
