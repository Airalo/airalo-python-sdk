import json
import hashlib
import pytest
from types import SimpleNamespace
from unittest.mock import Mock

from airalo.exceptions.airalo_exception import AiraloException
from airalo.services.installation_instructions_service import (
    InstallationInstructionsService,
)
from airalo.constants.api_constants import ApiConstants
from airalo.constants.sdk_constants import SdkConstants


@pytest.fixture
def mock_config():
    m = Mock()
    m.get_url.return_value = "https://api.example.com"
    m.get_http_headers.return_value = {"X-App": "sdk", "X-Env": "test"}
    return m


@pytest.fixture
def mock_curl():
    m = Mock()
    m.set_headers.return_value = m  # enable chaining
    return m


@pytest.fixture
def service(mock_config, mock_curl):
    return InstallationInstructionsService(
        config=mock_config, curl=mock_curl, access_token="tok"
    )


def test_init_requires_token(mock_config, mock_curl):
    with pytest.raises(AiraloException):
        InstallationInstructionsService(mock_config, mock_curl, access_token="")
    s = InstallationInstructionsService(mock_config, mock_curl, access_token="tok")
    assert s.base_url == "https://api.example.com"


def test_build_url_ok(service):
    url = service._build_url({"iccid": "890123"})
    assert (
        url
        == f"https://api.example.com{ApiConstants.SIMS_SLUG}/890123/{ApiConstants.INSTRUCTIONS_SLUG}"
    )


def test_get_key_is_md5(service, mock_config):
    url = f"https://api.example.com{ApiConstants.SIMS_SLUG}/890/{ApiConstants.INSTRUCTIONS_SLUG}"
    params = {"iccid": "890", "language": "en"}
    raw = url + json.dumps(params) + json.dumps(mock_config.get_http_headers()) + "tok"
    expect = hashlib.md5(raw.encode("utf-8")).hexdigest()
    assert service._get_key(url, params) == expect


def test_get_instructions_happy_path_calls_http_and_uses_cache(
    service, mock_curl, monkeypatch
):
    # Make Cached.get inside the service call the fetcher and capture ttl/key
    captured = {}

    def fake_cached_get(fetcher, key, ttl):
        captured["key"] = key
        captured["ttl"] = ttl
        return fetcher()

    monkeypatch.setattr(
        "airalo.services.installation_instructions_service.Cached",
        SimpleNamespace(get=fake_cached_get),
    )

    params = {"iccid": "890", "language": "en"}
    url = service._build_url(params)

    mock_curl.get.return_value = json.dumps({"data": {"steps": ["do x", "do y"]}})

    result = service.get_instructions(params)

    assert result == {"data": {"steps": ["do x", "do y"]}}
    # headers were set correctly
    mock_curl.set_headers.assert_called_once_with(
        {"Authorization": "Bearer tok", "Accept-Language": "en"}
    )
    # GET called with built URL
    mock_curl.get.assert_called_once_with(url)
    # Cache TTL respected
    assert captured["ttl"] == SdkConstants.DEFAULT_CACHE_TTL
    # cache key looks like md5 hex
    assert isinstance(captured["key"], str) and len(captured["key"]) == 32


def test_get_instructions_returns_none_when_data_empty_dict(
    service, mock_curl, monkeypatch
):
    def fake_cached_get(fetcher, key, ttl):
        # simulate empty data payload
        return {"data": {}}

    monkeypatch.setattr(
        "airalo.services.installation_instructions_service.Cached",
        SimpleNamespace(get=fake_cached_get),
    )

    out = service.get_instructions({"iccid": "111"})
    assert out is None


def test_fetch_sets_headers_and_parses_json(service, mock_curl):
    params = {"iccid": "222", "language": "bg"}
    url = service._build_url(params)
    mock_curl.get.return_value = json.dumps({"data": {"ok": True}})

    out = service._fetch(url, params)

    assert out == {"data": {"ok": True}}
    mock_curl.set_headers.assert_called_once_with(
        {"Authorization": "Bearer tok", "Accept-Language": "bg"}
    )
    mock_curl.get.assert_called_once_with(url)


def test_fetch_uses_empty_accept_language_when_missing(service, mock_curl):
    params = {"iccid": "333"}
    url = service._build_url(params)
    mock_curl.get.return_value = json.dumps({"data": {"ok": True}})

    _ = service._fetch(url, params)

    mock_curl.set_headers.assert_called_once_with(
        {"Authorization": "Bearer tok", "Accept-Language": ""}
    )


def test_get_instructions_bubbles_invalid_json(service, mock_curl, monkeypatch):
    def fake_cached_get(fetcher, key, ttl):
        return fetcher()  # let _fetch run

    monkeypatch.setattr(
        "airalo.services.installation_instructions_service.Cached",
        SimpleNamespace(get=fake_cached_get),
    )

    mock_curl.get.return_value = "not-json"

    with pytest.raises(json.JSONDecodeError):
        service.get_instructions({"iccid": "444", "language": "en"})
