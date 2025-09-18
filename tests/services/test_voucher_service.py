import json
import pytest
from unittest.mock import Mock

from airalo.exceptions.airalo_exception import AiraloException
from airalo.services.voucher_service import VoucherService
from airalo.constants.api_constants import ApiConstants
from airalo.constants.sdk_constants import SdkConstants


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
    return VoucherService(mock_config, mock_http, mock_signature, access_token="tok")


# ---------- init ----------


def test_init_requires_token(mock_config, mock_http, mock_signature):
    with pytest.raises(AiraloException):
        VoucherService(mock_config, mock_http, mock_signature, access_token="")
    s = VoucherService(mock_config, mock_http, mock_signature, access_token="tok")
    assert s.config.get_url() == "https://api.example.com"


# ---------- headers ----------


def test_get_headers_returns_string_list_and_signs(service, mock_signature):
    payload = {"amount": 10, "quantity": 1}
    headers = service._get_headers(payload)
    assert isinstance(headers, list)
    assert "Content-Type: application/json" in headers
    assert "Authorization: Bearer tok" in headers
    assert any(
        h.startswith("airalo-signature: ") and h.endswith("sig") for h in headers
    )
    mock_signature.get_signature.assert_called_once_with(payload)


# ---------- create_voucher ----------


def test_create_voucher_success_sets_headers_posts_and_parses(service, mock_http):
    payload = {"amount": 10, "quantity": 1}
    mock_http.code = 200
    mock_http.post.return_value = json.dumps({"ok": True, "id": "v1"})

    out = service.create_voucher(payload)

    assert out == {"ok": True, "id": "v1"}
    mock_http.set_headers.assert_called_once()
    mock_http.post.assert_called_once_with(
        "https://api.example.com" + ApiConstants.VOUCHERS_SLUG, payload
    )


def test_create_voucher_non_200_raises(service, mock_http):
    payload = {"amount": 10, "quantity": 1}
    mock_http.code = 422
    mock_http.post.return_value = '{"error":"nope"}'

    with pytest.raises(AiraloException) as e:
        service.create_voucher(payload)

    msg = str(e.value)
    assert "status code: 422" in msg and "nope" in msg


def test_create_voucher_bad_json_bubbles(service, mock_http):
    payload = {"amount": 10, "quantity": 1}
    mock_http.code = 200
    mock_http.post.return_value = "not-json"
    with pytest.raises(json.JSONDecodeError):
        service.create_voucher(payload)


# ---------- create_esim_voucher ----------


def test_create_esim_voucher_success(service, mock_http):
    payload = {"vouchers": [{"package_id": "p1", "quantity": 1}]}
    mock_http.code = 200
    mock_http.post.return_value = json.dumps({"ok": True})

    out = service.create_esim_voucher(payload)

    assert out == {"ok": True}
    mock_http.set_headers.assert_called_once()
    mock_http.post.assert_called_once_with(
        "https://api.example.com" + ApiConstants.VOUCHERS_ESIM_SLUG, payload
    )


def test_create_esim_voucher_non_200_raises(service, mock_http):
    payload = {"vouchers": [{"package_id": "p1", "quantity": 1}]}
    mock_http.code = 500
    mock_http.post.return_value = "oops"

    with pytest.raises(AiraloException) as e:
        service.create_esim_voucher(payload)
    assert "status code: 500" in str(e.value) and "oops" in str(e.value)


def test_create_esim_voucher_bad_json_bubbles(service, mock_http):
    payload = {"vouchers": [{"package_id": "p1", "quantity": 1}]}
    mock_http.code = 200
    mock_http.post.return_value = "not-json"
    with pytest.raises(json.JSONDecodeError):
        service.create_esim_voucher(payload)


# ---------- validation: _validate_voucher ----------


def test_validate_voucher_amount_required_and_bounds(service):
    with pytest.raises(AiraloException):
        service._validate_voucher({"quantity": 1})  # no amount
    with pytest.raises(AiraloException):
        service._validate_voucher({"amount": "", "quantity": 1})
    with pytest.raises(AiraloException):
        service._validate_voucher({"amount": 0, "quantity": 1})
    with pytest.raises(AiraloException):
        service._validate_voucher(
            {"amount": SdkConstants.VOUCHER_MAX_NUM + 1, "quantity": 1}
        )


def test_validate_voucher_code_length_and_quantity_rule(service):
    long_code = "x" * 256
    with pytest.raises(AiraloException):
        service._validate_voucher(
            {"amount": 1, "quantity": 1, "voucher_code": long_code}
        )

    with pytest.raises(AiraloException):
        service._validate_voucher({"amount": 1, "quantity": 2, "voucher_code": "PROMO"})


def test_validate_voucher_usage_limit_bounds(service):
    with pytest.raises(AiraloException):
        service._validate_voucher({"amount": 1, "quantity": 1, "usage_limit": 0})
    with pytest.raises(AiraloException):
        service._validate_voucher(
            {
                "amount": 1,
                "quantity": 1,
                "usage_limit": SdkConstants.VOUCHER_MAX_NUM + 1,
            }
        )


def test_validate_voucher_quantity_required_and_bounds(service):
    with pytest.raises(AiraloException):
        service._validate_voucher({"amount": 1})  # no quantity
    with pytest.raises(AiraloException):
        service._validate_voucher({"amount": 1, "quantity": ""})
    with pytest.raises(AiraloException):
        service._validate_voucher({"amount": 1, "quantity": 0})
    with pytest.raises(AiraloException):
        service._validate_voucher(
            {"amount": 1, "quantity": SdkConstants.VOUCHER_MAX_QUANTITY + 1}
        )


def test_validate_voucher_ok(service):
    # should not raise
    service._validate_voucher({"amount": 10, "quantity": 1})


# ---------- validation: _validate_esim_voucher ----------


def test_validate_esim_voucher_requires_array_and_items(service):
    with pytest.raises(AiraloException):
        service._validate_esim_voucher({})
    with pytest.raises(AiraloException):
        service._validate_esim_voucher({"vouchers": "not-a-list"})


def test_validate_esim_voucher_item_rules_and_quantity_cap_current_impl(service):
    # current code checks payload['quantity'] > max (buggy), so include a top-level quantity to trigger it
    payload = {
        "vouchers": [{"package_id": "p1", "quantity": 1}],
        "quantity": SdkConstants.VOUCHER_MAX_QUANTITY + 1,
    }
    with pytest.raises(AiraloException):
        service._validate_esim_voucher(payload)


def test_validate_esim_voucher_missing_fields_in_item(service):
    with pytest.raises(AiraloException):
        service._validate_esim_voucher({"vouchers": [{"quantity": 1}]})
    with pytest.raises(AiraloException):
        service._validate_esim_voucher({"vouchers": [{"package_id": "p1"}]})


def test_validate_esim_voucher_ok_minimal(service):
    # should not raise on valid shape
    service._validate_esim_voucher({"vouchers": [{"package_id": "p1", "quantity": 1}]})
