import json
import pytest
from unittest.mock import Mock

from airalo.exceptions.airalo_exception import AiraloException
from airalo.services.future_order_service import FutureOrderService
from airalo.constants.api_constants import ApiConstants
from airalo.constants.sdk_constants import SdkConstants


@pytest.fixture
def mock_config():
    m = Mock()
    m.get_url.return_value = "https://api.example.com"
    return m


@pytest.fixture
def mock_http():
    m = Mock()
    # allow chaining set_headers(...).post(...)
    m.set_headers.return_value = m
    m.code = 200
    return m


@pytest.fixture
def mock_signature():
    m = Mock()
    m.get_signature.return_value = "sig-123"
    return m


@pytest.fixture
def service(mock_config, mock_http, mock_signature, monkeypatch):
    # Patch CloudSimShareValidator.validate to no-op by default
    monkeypatch.setattr(
        "airalo.services.future_order_service.CloudSimShareValidator",
        Mock(validate=Mock()),
    )
    return FutureOrderService(
        config=mock_config,
        http_resource=mock_http,
        signature=mock_signature,
        access_token="tok",
    )


def test_init_requires_token(mock_config, mock_http, mock_signature):
    with pytest.raises(AiraloException):
        FutureOrderService(mock_config, mock_http, mock_signature, access_token="")
    s = FutureOrderService(mock_config, mock_http, mock_signature, access_token="tok")
    assert s.base_url == "https://api.example.com"


def test_create_future_order_success_filters_payload_signs_and_calls_http(
    service, mock_http, mock_signature, monkeypatch
):
    # ensure validator is called; already patched in fixture but keep a spy we can assert on
    csv_mock = Mock()
    csv_mock.validate = Mock()
    monkeypatch.setattr(
        "airalo.services.future_order_service.CloudSimShareValidator",
        csv_mock,
    )

    payload = {
        "package_id": "abc-123",
        "quantity": 2,
        "due_date": "2025-09-20 14:30",
        "note": "",  # falsy -> should be removed before signing
        "meta": None,  # falsy -> should be removed
    }
    expected_filtered = {
        "package_id": "abc-123",
        "quantity": 2,
        "due_date": "2025-09-20 14:30",
    }

    mock_http.code = 200
    mock_http.post.return_value = json.dumps({"ok": True, "id": "req_1"})

    result = service.create_future_order(payload)

    assert result == {"ok": True, "id": "req_1"}

    # signature uses filtered payload
    mock_signature.get_signature.assert_called_once_with(expected_filtered)

    # cloud share validator called with original payload (method takes dict and does its own checks)
    csv_mock.validate.assert_called_once()

    mock_http.set_headers.assert_called_once_with(
        {
            "Authorization": "Bearer tok",
            "Content-Type": "application/json",
            "airalo-signature": "sig-123",
        }
    )
    mock_http.post.assert_called_once_with(
        "https://api.example.com" + ApiConstants.FUTURE_ORDERS,
        expected_filtered,
    )


def test_create_future_order_non_200_raises(service, mock_http):
    mock_http.code = 422
    mock_http.post.return_value = '{"error":"invalid"}'
    payload = {
        "package_id": "p",
        "quantity": 1,
        "due_date": "2025-09-20 14:30",
    }
    with pytest.raises(AiraloException) as e:
        service.create_future_order(payload)
    assert "status code: 422" in str(e.value)
    assert "invalid" in str(e.value)


def test_cancel_future_order_success(service, mock_http, mock_signature):
    mock_http.code = 200
    mock_http.post.return_value = json.dumps({"canceled": 2})
    payload = {"request_ids": ["r1", "r2"]}

    out = service.cancel_future_order(payload)

    assert out == {"canceled": 2}
    mock_signature.get_signature.assert_called_once_with(payload)
    mock_http.set_headers.assert_called_once()
    mock_http.post.assert_called_once_with(
        "https://api.example.com" + ApiConstants.CANCEL_FUTURE_ORDERS,
        payload,
    )


def test_cancel_future_order_non_200_raises(service, mock_http):
    mock_http.code = 500
    mock_http.post.return_value = "oops"
    with pytest.raises(AiraloException) as e:
        service.cancel_future_order({"request_ids": ["x"]})
    assert "status code: 500" in str(e.value)
    assert "oops" in str(e.value)


# ---- validation unit tests ----


def test_validate_future_order_missing_package_id_raises(service):
    with pytest.raises(AiraloException) as e:
        service._validate_future_order({"quantity": 1, "due_date": "2025-09-20 14:30"})
    assert "package_id is required" in str(e.value)


def test_validate_future_order_quantity_less_than_one_raises(service):
    with pytest.raises(AiraloException) as e:
        service._validate_future_order(
            {"package_id": "p", "quantity": 0, "due_date": "2025-09-20 14:30"}
        )
    assert "quantity is required" in str(e.value)


def test_validate_future_order_quantity_over_limit_raises(service):
    over = SdkConstants.FUTURE_ORDER_LIMIT + 1
    with pytest.raises(AiraloException) as e:
        service._validate_future_order(
            {"package_id": "p", "quantity": over, "due_date": "2025-09-20 14:30"}
        )
    # implementation mentions BULK_ORDER_LIMIT in the message; assert it complains
    assert "may not be greater" in str(e.value)


def test_validate_future_order_due_date_required_raises(service):
    with pytest.raises(AiraloException) as e:
        service._validate_future_order({"package_id": "p", "quantity": 1})
    assert "due_date is required" in str(e.value)


@pytest.mark.parametrize(
    "bad_due",
    [
        "2025-09-20",  # missing time
        "2025/09/20 14:30",  # wrong separators
        "2025-13-01 00:00",  # invalid month
        "2025-09-20 14:3",  # wrong minutes format
        "2025-09-20 14:30:00",  # seconds not allowed by strict check
    ],
)
def test_validate_future_order_due_date_bad_format_raises(service, bad_due):
    with pytest.raises(AiraloException) as e:
        service._validate_future_order(
            {"package_id": "p", "quantity": 1, "due_date": bad_due}
        )
    assert "must be in the format Y-m-d H:i" in str(e.value)


def test_validate_cancel_future_order_requires_non_empty_list(service):
    with pytest.raises(AiraloException):
        service._validate_cancel_future_order({"request_ids": []})
    with pytest.raises(AiraloException):
        service._validate_cancel_future_order({"request_ids": None})
    with pytest.raises(AiraloException):
        service._validate_cancel_future_order({"request_ids": "r1"})
