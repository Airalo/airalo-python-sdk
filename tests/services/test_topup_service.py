import json
import pytest
from unittest.mock import Mock

from airalo.exceptions.airalo_exception import (
    AiraloException,
    ValidationError,
    APIError,
)
from airalo.services.topup_service import TopupService
from airalo.constants.api_constants import ApiConstants


# ---------- fixtures ----------


@pytest.fixture
def mock_config():
    m = Mock()
    m.get_url.return_value = "https://api.example.com"
    return m


@pytest.fixture
def mock_http():
    m = Mock()
    m.set_headers.return_value = m  # chain
    m.code = 200
    return m


@pytest.fixture
def mock_signature():
    m = Mock()
    m.get_signature.return_value = "sig"
    return m


@pytest.fixture
def service(mock_config, mock_http, mock_signature):
    return TopupService(mock_config, mock_http, mock_signature, access_token="tok")


# ---------- init ----------


def test_init_requires_token(mock_config, mock_http, mock_signature):
    with pytest.raises(AiraloException):
        TopupService(mock_config, mock_http, mock_signature, access_token="")
    s = TopupService(mock_config, mock_http, mock_signature, access_token="tok")
    assert s._base_url == "https://api.example.com"


# ---------- headers ----------


def test_get_headers_uses_signature_and_token(service, mock_signature):
    payload = {"package_id": "p1", "iccid": "89014103211118510720"}
    headers = service._get_headers(payload)
    assert headers == {
        "Content-Type": "application/json",
        "Authorization": "Bearer tok",
        "airalo-signature": "sig",
    }
    mock_signature.get_signature.assert_called_once_with(payload)


# ---------- validation ----------


def test_validate_topup_requires_package_id(service):
    with pytest.raises(ValidationError) as e:
        service._validate_topup({"iccid": "89014103211118510720"})
    assert "package_id is required" in str(e.value)


def test_validate_topup_requires_iccid(service):
    with pytest.raises(ValidationError) as e:
        service._validate_topup({"package_id": "p1"})
    assert "iccid is required" in str(e.value)


@pytest.mark.parametrize("iccid", ["short", "1" * 22])  # <16 or >21
def test_validate_topup_iccid_length_bounds(service, iccid):
    with pytest.raises(ValidationError) as e:
        service._validate_topup({"package_id": "p1", "iccid": iccid})
    assert "between 16 and 21 characters" in str(e.value)


def test_validate_topup_ok(service):
    # should not raise
    service._validate_topup({"package_id": "p1", "iccid": "8" * 20})


# ---------- create_topup ----------


def test_create_topup_success_sets_headers_posts_and_parses(service, mock_http):
    payload = {"package_id": "p1", "iccid": "89014103211118510720"}
    mock_http.code = 200
    mock_http.post.return_value = json.dumps({"ok": True, "id": "t1"})

    out = service.create_topup(payload)

    assert out == {"ok": True, "id": "t1"}
    mock_http.set_headers.assert_called_once_with(
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer tok",
            "airalo-signature": "sig",
        }
    )
    mock_http.post.assert_called_once_with(
        "https://api.example.com" + ApiConstants.TOPUPS_SLUG, payload
    )


def test_create_topup_non_200_raises(service, mock_http):
    payload = {"package_id": "p1", "iccid": "8" * 20}
    mock_http.code = 422
    mock_http.post.return_value = '{"error":"bad"}'
    with pytest.raises(APIError) as e:
        service.create_topup(payload)
    msg = str(e.value)
    assert "status code: 422" in msg and "bad" in msg


def test_create_topup_bad_json_raises(service, mock_http):
    payload = {"package_id": "p1", "iccid": "8" * 20}
    mock_http.code = 200
    mock_http.post.return_value = "not-json"
    with pytest.raises(APIError) as e:
        service.create_topup(payload)
    assert "Failed to parse top-up response" in str(e.value)
