import json
import pytest
from types import SimpleNamespace
from unittest.mock import Mock, call

from airalo.exceptions.airalo_exception import (
    AiraloException,
    ValidationError,
    APIError,
)
from airalo.services.order_service import OrderService
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
    m.set_headers.return_value = m
    m.code = 200
    return m


@pytest.fixture
def mock_multi_http():
    # multi_http.tag(id).set_headers(...).post(url, payload)
    # Accumulate calls per tag; exec() returns a dict mapping tag->response
    class MultiMock:
        def __init__(self):
            self.calls = {}

        def tag(self, key):
            self.calls.setdefault(key, [])

            # chain object
            def set_headers(h):
                self.calls[key].append(("headers", h))
                return chain

            def post(url, payload):
                self.calls[key].append(("post", url, payload))
                return chain

            chain = SimpleNamespace(set_headers=set_headers, post=post)
            return chain

        def exec(self):
            # default to simple OK json for every tag unless overridden in test
            return {k: json.dumps({"ok": True, "tag": k}) for k in self.calls}

    return MultiMock()


@pytest.fixture
def mock_signature():
    m = Mock()
    m.get_signature.return_value = "sig"
    return m


@pytest.fixture
def service(mock_config, mock_http, mock_multi_http, mock_signature, monkeypatch):
    # CloudSimShareValidator.validate no-op
    monkeypatch.setattr(
        "airalo.services.order_service.CloudSimShareValidator", Mock(validate=Mock())
    )
    return OrderService(
        config=mock_config,
        http_resource=mock_http,
        multi_http_resource=mock_multi_http,
        signature=mock_signature,
        access_token="tok",
    )


# ---------- helpers ----------


def expect_headers(payload):
    return {
        "Authorization": "Bearer tok",
        "Content-Type": "application/json",
        "airalo-signature": "sig",
    }


# ---------- tests: init / headers / validation ----------


def test_init_requires_token(mock_config, mock_http, mock_multi_http, mock_signature):
    with pytest.raises(AiraloException):
        OrderService(
            mock_config, mock_http, mock_multi_http, mock_signature, access_token=""
        )
    s = OrderService(
        mock_config, mock_http, mock_multi_http, mock_signature, access_token="tok"
    )
    assert s._base_url == "https://api.example.com"


def test__get_headers_uses_signature_and_token(service, mock_signature):
    payload = {"package_id": "p1", "quantity": 1}
    headers = service._get_headers(payload)
    assert headers == expect_headers(payload)
    mock_signature.get_signature.assert_called_once_with(payload)


def test_validate_order_rules(service):
    with pytest.raises(ValidationError):
        service._validate_order({"quantity": 1})
    with pytest.raises(ValidationError):
        service._validate_order({"package_id": "p", "quantity": 0})
    over = SdkConstants.ORDER_LIMIT + 1
    with pytest.raises(ValidationError):
        service._validate_order({"package_id": "p", "quantity": over})


def test_validate_bulk_order_limit(service):
    packages = {f"p{i}": 1 for i in range(SdkConstants.BULK_ORDER_LIMIT + 1)}
    with pytest.raises(ValidationError):
        service._validate_bulk_order(packages)


# ---------- tests: create_order ----------


def test_create_order_success_sets_default_type_and_parses(
    service, mock_http, mock_signature
):
    payload = {"package_id": "p1", "quantity": 2}
    mock_http.code = 200
    mock_http.post.return_value = json.dumps({"id": "o1"})

    out = service.create_order(payload)

    # default type set
    assert payload["type"] == "sim"
    assert out == {"id": "o1"}
    mock_http.set_headers.assert_called_once_with(expect_headers(payload))
    mock_http.post.assert_called_once_with(
        "https://api.example.com" + ApiConstants.ORDERS_SLUG, payload
    )


def test_create_order_non_200_raises(service, mock_http):
    mock_http.code = 422
    mock_http.post.return_value = '{"error":"bad"}'
    with pytest.raises(APIError) as e:
        service.create_order({"package_id": "p1", "quantity": 1})
    assert "status code: 422" in str(e.value)
    assert "bad" in str(e.value)


def test_create_order_bad_json_raises(service, mock_http):
    mock_http.code = 200
    mock_http.post.return_value = "not-json"
    with pytest.raises(APIError) as e:
        service.create_order({"package_id": "p1", "quantity": 1})
    assert "Failed to parse order response" in str(e.value)


# ---------- tests: create_order_with_email_sim_share ----------


def test_create_order_with_email_sim_share_success(
    service, mock_http, mock_signature, monkeypatch
):
    csv_mock = Mock()
    csv_mock.validate = Mock()
    monkeypatch.setattr(
        "airalo.services.order_service.CloudSimShareValidator", csv_mock
    )

    payload = {"package_id": "p1", "quantity": 1}
    cloud = {
        "to_email": "a@b.com",
        "sharing_option": ["link"],
        "copy_address": ["c@d.com"],
    }
    mock_http.code = 200
    mock_http.post.return_value = json.dumps({"ok": True})

    out = service.create_order_with_email_sim_share(payload, cloud)

    assert out == {"ok": True}
    # payload was augmented
    assert payload["to_email"] == "a@b.com"
    assert payload["sharing_option"] == ["link"]
    assert payload["copy_address"] == ["c@d.com"]
    assert payload["type"] == "sim"
    csv_mock.validate.assert_called_once_with(
        cloud, required_fields=["to_email", "sharing_option"]
    )
    mock_http.set_headers.assert_called_once_with(expect_headers(payload))
    mock_http.post.assert_called_once()


def test_create_order_with_email_sim_share_non_200_raises(service, mock_http):
    mock_http.code = 500
    mock_http.post.return_value = "oops"
    with pytest.raises(APIError):
        service.create_order_with_email_sim_share(
            {"package_id": "p1", "quantity": 1},
            {"to_email": "x@y.com", "sharing_option": ["link"]},
        )


# ---------- tests: create_order_async ----------


def test_create_order_async_success_202(service, mock_http):
    mock_http.code = 202
    mock_http.post.return_value = json.dumps({"queued": True})
    out = service.create_order_async({"package_id": "p1", "quantity": 1})
    assert out == {"queued": True}
    mock_http.set_headers.assert_called_once()
    mock_http.post.assert_called_once_with(
        "https://api.example.com" + ApiConstants.ASYNC_ORDERS_SLUG,
        {"package_id": "p1", "quantity": 1, "type": "sim"},
    )


def test_create_order_async_non_202_raises(service, mock_http):
    mock_http.code = 200
    mock_http.post.return_value = "{}"
    with pytest.raises(APIError):
        service.create_order_async({"package_id": "p1", "quantity": 1})


def test_create_order_async_bad_json_raises(service, mock_http):
    mock_http.code = 202
    mock_http.post.return_value = "broken"
    with pytest.raises(APIError):
        service.create_order_async({"package_id": "p1", "quantity": 1})


# ---------- tests: create_order_bulk (dict and list inputs) ----------


def test_create_order_bulk_from_dict_queues_and_exec_parses(service, mock_multi_http):
    packages = {"p1": 1, "p2": 2}

    # override exec output with one valid JSON and one broken to test per-item parsing
    def custom_exec():
        return {"p1": json.dumps({"ok": True, "id": 1}), "p2": "not-json"}

    mock_multi_http.exec = custom_exec

    out = service.create_order_bulk(packages, description="bulk desc")

    # verify queuing
    for pid, qty in packages.items():
        # expect two recorded entries per tag: headers then post
        entries = mock_multi_http.calls[pid]
        assert entries[0][0] == "headers"
        assert entries[1][0] == "post"
        _, url, payload = entries[1]
        assert url == "https://api.example.com" + ApiConstants.ORDERS_SLUG
        assert payload["package_id"] == pid
        assert payload["quantity"] == qty
        assert payload["type"] == "sim"
        assert payload["description"] == "bulk desc"

    # verify result parsing behavior
    assert out["p1"] == {"ok": True, "id": 1}
    assert out["p2"]["error"] == "Failed to parse response"
    assert out["p2"]["raw"] == "not-json"


def test_create_order_bulk_from_list_converted_and_exec_parses(
    service, mock_multi_http
):
    packages_list = [
        {"package_id": "p1", "quantity": 1},
        {"package_id": "p2", "quantity": 2},
    ]
    mock_multi_http.exec = lambda: {
        "p1": json.dumps({"ok": 1}),
        "p2": json.dumps({"ok": 2}),
    }

    out = service.create_order_bulk(packages_list, description=None)

    assert out == {"p1": {"ok": 1}, "p2": {"ok": 2}}
    # ensure both tags present (conversion happened)
    assert set(mock_multi_http.calls.keys()) == {"p1", "p2"}


def test_create_order_bulk_empty_or_no_responses_returns_none(service, mock_multi_http):
    assert service.create_order_bulk({}, description="x") is None
    # simulate no responses
    mock_multi_http.exec = lambda: {}
    assert service.create_order_bulk({"p1": 1}, description="x") is None


# ---------- tests: create_order_bulk_with_email_sim_share ----------


def test_create_order_bulk_with_email_sim_share_queues_and_validates(
    service, mock_multi_http, monkeypatch
):
    csv_mock = Mock()
    csv_mock.validate = Mock()
    monkeypatch.setattr(
        "airalo.services.order_service.CloudSimShareValidator", csv_mock
    )

    packages = {"p1": 1, "p2": 1}
    cloud = {
        "to_email": "a@b.com",
        "sharing_option": ["link"],
        "copy_address": ["c@d.com"],
    }
    mock_multi_http.exec = lambda: {
        "p1": json.dumps({"ok": True}),
        "p2": json.dumps({"ok": True}),
    }

    out = service.create_order_bulk_with_email_sim_share(
        packages, cloud, description="D"
    )

    csv_mock.validate.assert_called_once_with(
        cloud, required_fields=["to_email", "sharing_option"]
    )
    # queued payloads contain email share fields
    for pid in packages:
        entries = mock_multi_http.calls[pid]
        _, _, payload = entries[1]
        assert payload["to_email"] == "a@b.com"
        assert payload["sharing_option"] == ["link"]
        assert payload["copy_address"] == ["c@d.com"]
    assert out == {"p1": {"ok": True}, "p2": {"ok": True}}


def test_create_order_bulk_with_email_sim_share_empty_or_no_responses(
    service, mock_multi_http, monkeypatch
):
    csv_mock = Mock(validate=Mock())
    monkeypatch.setattr(
        "airalo.services.order_service.CloudSimShareValidator", csv_mock
    )
    assert (
        service.create_order_bulk_with_email_sim_share(
            {}, {"to_email": "x", "sharing_option": ["link"]}
        )
        is None
    )
    mock_multi_http.exec = lambda: {}
    assert (
        service.create_order_bulk_with_email_sim_share(
            {"p1": 1}, {"to_email": "x", "sharing_option": ["link"]}
        )
        is None
    )


# ---------- tests: create_order_async_bulk ----------


def test_create_order_async_bulk_queues_and_parses(service, mock_multi_http):
    packages = {"p1": 1}
    mock_multi_http.exec = lambda: {"p1": json.dumps({"queued": True})}

    out = service.create_order_async_bulk(
        packages, webhook_url="https://hook", description="D"
    )

    entries = mock_multi_http.calls["p1"]
    _, url, payload = entries[1]
    assert url == "https://api.example.com" + ApiConstants.ASYNC_ORDERS_SLUG
    assert payload["webhook_url"] == "https://hook"
    assert payload["description"] == "D"
    assert out == {"p1": {"queued": True}}


def test_create_order_async_bulk_empty_or_no_responses(service, mock_multi_http):
    assert service.create_order_async_bulk({}, webhook_url=None) is None
    mock_multi_http.exec = lambda: {}
    assert service.create_order_async_bulk({"p1": 1}, webhook_url=None) is None
