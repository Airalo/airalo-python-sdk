import json
import hashlib
import pytest
from unittest.mock import Mock
from types import SimpleNamespace

from airalo.exceptions import AiraloException

from airalo.services.exchange_rates_service import ExchangeRatesService
from airalo.constants.api_constants import ApiConstants


@pytest.fixture
def mock_config():
    m = Mock()
    m.get_url.return_value = "https://api.example.com/"
    m.get_http_headers.return_value = {"X-App": "sdk", "X-Env": "test"}
    return m


@pytest.fixture
def mock_curl():
    m = Mock()
    # allow chaining: curl.set_headers(...).get(url)
    m.set_headers.return_value = m
    return m


@pytest.fixture
def service(mock_config, mock_curl):
    return ExchangeRatesService(mock_config, mock_curl, access_token="tok")


def test_init_requires_token(mock_config, mock_curl):
    with pytest.raises(AiraloException):
        ExchangeRatesService(mock_config, mock_curl, access_token="")
    s = ExchangeRatesService(mock_config, mock_curl, access_token="x")
    assert s.base_url == "https://api.example.com/"


def test_validate_exchange_rates_request_date_ok(service, monkeypatch):
    # Force DateHelper.validate_date to return True
    from airalo.helpers import date_helper as dh

    monkeypatch.setattr(dh, "DateHelper", Mock(validate_date=Mock(return_value=True)))
    # Should not raise
    service.validate_exchange_rates_request({"date": "2025-09-01"})


def test_validate_exchange_rates_request_bad_date_raises(service, monkeypatch):
    from airalo.helpers import date_helper as dh

    monkeypatch.setattr(dh, "DateHelper", Mock(validate_date=Mock(return_value=False)))
    with pytest.raises(AiraloException):
        service.validate_exchange_rates_request({"date": "2025-99-99"})


@pytest.mark.parametrize(
    "to_value", ["USD,EURO", "US,EUR", "USDEUR,", ",USD", "usd,EU"]
)  # invalid shapes
def test_validate_exchange_rates_request_bad_to_raises(service, to_value):
    with pytest.raises(AiraloException):
        service.validate_exchange_rates_request({"to": to_value})


@pytest.mark.parametrize(
    "to_value", ["USD", "USD,EUR", "usd,eur,GBP"]
)  # regex allows letters, case-insensitive
def test_validate_exchange_rates_request_to_ok(service, to_value):
    # Should not raise
    service.validate_exchange_rates_request({"to": to_value})


def test_build_url_with_params_order_and_encoding(service):
    url = service.build_url({"date": "2025-09-01", "to": "USD,EUR"})
    assert (
        url
        == f"https://api.example.com/{ApiConstants.EXCHANGE_RATES_SLUG}?date=2025-09-01&to=USD%2CEUR"
    )


def test_build_url_no_params_trailing_question_mark(service):
    url = service.build_url({})
    assert url == f"https://api.example.com/{ApiConstants.EXCHANGE_RATES_SLUG}?"


def test_get_key_is_md5_of_expected_concat(service, mock_config):
    url = "https://api.example.com/x?date=2025-09-01"
    params = {"date": "2025-09-01"}
    # Expected raw string per implementation
    raw_key = f"{url}{json.dumps(params, sort_keys=True)}{json.dumps(mock_config.get_http_headers())}tok"
    expected = hashlib.md5(raw_key.encode()).hexdigest()
    assert service.get_key(url, params) == expected


def test_exchange_rates_happy_path_uses_cache_and_headers(
    service, mock_curl, monkeypatch
):
    # Patch the DateHelper used by the *service module*
    monkeypatch.setattr(
        "airalo.services.exchange_rates_service.DateHelper",
        Mock(validate_date=Mock(return_value=True)),
    )

    # Make Cached.get call the provided fetcher so we exercise headers and URL
    def fake_cached_get(fetcher, key, ttl):
        return fetcher()

    monkeypatch.setattr(
        "airalo.services.exchange_rates_service.Cached",
        SimpleNamespace(get=fake_cached_get),
    )

    # HTTP layer returns valid JSON
    mock_curl.set_headers.return_value = mock_curl  # ensure chaining
    mock_curl.get.return_value = json.dumps({"data": {"rates": {"USD": 1.0}}})

    result = service.exchange_rates({"date": "2025-09-01", "to": "USD,EUR"})
    assert result == {"data": {"rates": {"USD": 1.0}}}

    mock_curl.set_headers.assert_called_once_with(
        {
            "Accept": "application/json",
            "Authorization": "Bearer tok",
        }
    )
    mock_curl.get.assert_called_once_with(
        f"https://api.example.com/{ApiConstants.EXCHANGE_RATES_SLUG}?date=2025-09-01&to=USD%2CEUR"
    )


def test_exchange_rates_returns_none_when_no_data(service, mock_curl, monkeypatch):
    from airalo.helpers import date_helper as dh

    monkeypatch.setattr(dh, "DateHelper", Mock(validate_date=Mock(return_value=True)))

    def fake_cached_get(fetcher, key, ttl):
        # simulate cache returning value without "data"
        return {"meta": {"ok": True}}

    from airalo.helpers import cached as cached_mod

    monkeypatch.setattr(cached_mod, "Cached", Mock(get=fake_cached_get))

    mock_curl.get.return_value = json.dumps({"meta": {"ok": True}})

    assert service.exchange_rates({"to": "USD"}) is None


def test_exchange_rates_bubbles_invalid_json(service, mock_curl, monkeypatch):
    monkeypatch.setattr(
        "airalo.services.exchange_rates_service.DateHelper",
        Mock(validate_date=Mock(return_value=True)),
    )

    # Cached.get invokes fetcher so JSON parsing happens inside service
    def fake_cached_get(fetcher, key, ttl):
        return fetcher()

    monkeypatch.setattr(
        "airalo.services.exchange_rates_service.Cached",
        SimpleNamespace(get=fake_cached_get),
    )

    mock_curl.set_headers.return_value = mock_curl
    mock_curl.get.return_value = "not-json"

    with pytest.raises(json.JSONDecodeError):
        service.exchange_rates({"to": "USD"})
