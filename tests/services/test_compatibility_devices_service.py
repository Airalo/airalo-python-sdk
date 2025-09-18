import pytest
import json
from unittest.mock import Mock

import airalo.exceptions as exceptions
from airalo.services.compatibility_devices_service import (
    CompatibilityDevicesService,
)
from airalo.constants.api_constants import ApiConstants


@pytest.fixture
def mock_config():
    mock = Mock()
    mock.get_url.return_value = "https://api.example.com/"
    return mock


@pytest.fixture
def mock_curl():
    return Mock()


@pytest.fixture
def service(mock_config, mock_curl):
    return CompatibilityDevicesService(
        config=mock_config, curl=mock_curl, access_token="valid_token"
    )


def test_init_with_valid_token(mock_config, mock_curl):
    service = CompatibilityDevicesService(
        config=mock_config, curl=mock_curl, access_token="token123"
    )
    assert service.config == mock_config
    assert service.curl == mock_curl
    assert service.access_token == "token123"
    assert service.base_url == "https://api.example.com/"


def test_init_with_missing_token_raises(mock_config, mock_curl):
    with pytest.raises(exceptions.AiraloException) as exc:
        CompatibilityDevicesService(config=mock_config, curl=mock_curl, access_token="")
    assert "Invalid access token" in str(exc.value)


def test_build_url(service):
    url = service._build_url()
    assert url == f"https://api.example.com/{ApiConstants.COMPATIBILITY_SLUG}"


def test_get_compatible_devices_returns_data(service, mock_curl):
    expected = {"data": {"device": "iPhone"}}
    mock_curl.set_headers.return_value = mock_curl
    mock_curl.get.return_value = json.dumps(expected)

    result = service.get_compatible_devices()

    assert result == expected
    mock_curl.set_headers.assert_called_once_with(
        {"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
    )
    mock_curl.get.assert_called_once_with(
        f"https://api.example.com/{ApiConstants.COMPATIBILITY_SLUG}"
    )


def test_get_compatible_devices_returns_none_if_no_data(service, mock_curl):
    expected = {"meta": {"status": "ok"}}
    mock_curl.set_headers.return_value = mock_curl
    mock_curl.get.return_value = json.dumps(expected)

    result = service.get_compatible_devices()

    assert result is None


def test_get_compatible_devices_invalid_json(service, mock_curl):
    mock_curl.set_headers.return_value = mock_curl
    mock_curl.get.return_value = "not-a-json"

    with pytest.raises(json.JSONDecodeError):
        service.get_compatible_devices()
