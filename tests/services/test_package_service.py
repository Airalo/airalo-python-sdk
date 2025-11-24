import json
import hashlib
import pytest
from types import SimpleNamespace
from unittest.mock import Mock

from airalo.exceptions.airalo_exception import AiraloException
from airalo.services.packages_service import PackagesService
from airalo.constants.api_constants import ApiConstants


# ---------- fixtures ----------


@pytest.fixture
def mock_config():
    m = Mock()
    m.get_url.return_value = "https://api.example.com"
    m.get_http_headers.return_value = {"X-App": "sdk", "X-Env": "test"}
    return m


@pytest.fixture
def mock_http():
    m = Mock()
    m.set_headers.return_value = m  # chain
    return m


@pytest.fixture
def service(mock_config, mock_http):
    return PackagesService(
        mock_config, mock_http, access_token="toktoktoktoktoktoktok"
    )  # >20 chars


# ---------- init ----------


def test_init_requires_token(mock_config, mock_http):
    with pytest.raises(AiraloException):
        PackagesService(mock_config, mock_http, access_token="")
    s = PackagesService(mock_config, mock_http, access_token="tok")
    assert s._base_url == "https://api.example.com"


# ---------- _build_url ----------


def test_build_url_defaults_include_topup(service):
    url = service._build_url({})
    assert url == f"https://api.example.com{ApiConstants.PACKAGES_SLUG}?include=topup"


def test_build_url_sim_only_excludes_topup(service):
    url = service._build_url({"simOnly": True})
    # code always appends "?" even if no query params
    assert url == f"https://api.example.com{ApiConstants.PACKAGES_SLUG}?"


def test_build_url_type_country_limit(service):
    url = service._build_url({"type": "local", "country": "bg", "limit": 25})
    # Order from urlencode of dict insertion order: include, filter[type], filter[country], limit
    assert url == (
        f"https://api.example.com{ApiConstants.PACKAGES_SLUG}"
        "?include=topup&filter%5Btype%5D=local&filter%5Bcountry%5D=BG&limit=25"
    )
    url2 = service._build_url({"type": "global"})
    assert "filter%5Btype%5D=global" in url2


# ---------- _get_cache_key ----------


def test_get_cache_key_includes_url_params_headers_and_partial_token(
    service, mock_config
):
    url = f"https://api.example.com{ApiConstants.PACKAGES_SLUG}?include=topup"
    params = {"limit": 10}
    key_data = {
        "url": url,
        "params": params,
        "headers": mock_config.get_http_headers(),
        "token": service._access_token[:20],
    }
    key_string = json.dumps(key_data, sort_keys=True)
    expected = f"packages_{hashlib.md5(key_string.encode()).hexdigest()}"
    assert service._get_cache_key(url, params) == expected


# ---------- get_packages / _fetch_packages: pagination, limit, flat ----------


def test_get_packages_paginates_applies_limit_and_sets_auth_header(
    service, mock_http, monkeypatch
):
    # Cached.get should call the fetcher
    monkeypatch.setattr(
        "airalo.services.packages_service.Cached",
        SimpleNamespace(get=lambda fetcher, key, ttl: fetcher()),
    )
    # page 1 -> has data, meta says last_page=2
    page1 = json.dumps(
        {"pricing": {"model": "net_pricing", "discount_percentage": 0}, "data": [1, 2], "meta": {"last_page": 2}})
    # page 2 -> has data, no more pages after
    page2 = json.dumps({"data": [3]})

    # emulate GET by inspecting page param
    def fake_get(url):
        if "page=1" in url:
            return page1
        if "page=2" in url:
            return page2
        # first loop builds url without page if params['page'] falsy; code sets current_page to 1 by default
        return page1

    mock_http.get.side_effect = fake_get

    out = service.get_packages({"limit": 3})  # limit trims to exactly 3 items

    assert out == {"pricing": {"model": "net_pricing", "discount_percentage": 0}, "data": [1, 2, 3]}
    mock_http.set_headers.assert_called_with(
        {"Authorization": "Bearer toktoktoktoktoktoktok"}
    )
    # made at least two GETs
    assert mock_http.get.call_count >= 2


def test_get_packages_returns_none_on_no_data_or_invalid_json(
    service, mock_http, monkeypatch
):
    # invalid JSON on first request yields result {'data': []} from _fetch, which get_packages turns to None
    def cached_get(fetcher, key, ttl):
        # have fetcher parse invalid json and gracefully return empty
        mock_http.get.return_value = "not-json"
        return fetcher()

    monkeypatch.setattr(
        "airalo.services.packages_service.Cached",
        SimpleNamespace(get=cached_get),
    )

    assert service.get_packages({}) is None

    # also test when HTTP returns empty response
    def cached_get_empty(fetcher, key, ttl):
        mock_http.get.return_value = ""
        return fetcher()

    monkeypatch.setattr(
        "airalo.services.packages_service.Cached",
        SimpleNamespace(get=cached_get_empty),
    )
    assert service.get_packages({}) is None


def test_get_packages_flattening(service, mock_http, monkeypatch):
    monkeypatch.setattr(
        "airalo.services.packages_service.Cached",
        SimpleNamespace(get=lambda fetcher, key, ttl: fetcher()),
    )

    nested = {
        "data": [
            {
                "slug": "bg",
                "operators": [
                    {
                        "title": "TelcoBG",
                        "plan_type": "prepaid",
                        "activation_policy": "auto",
                        "is_roaming": False,
                        "info": "info",
                        "image": {"url": "http://img"},
                        "countries": [{"country_code": "BG"}],
                        "packages": [
                            {
                                "id": "bg-1gb-7d",
                                "type": "data",
                                "price": 5.0,
                                "net_price": 4.0,
                                "amount": 1,
                                "day": 7,
                                "is_unlimited": False,
                                "title": "BG 1GB 7D",
                                "data": "1GB",
                                "short_info": "short",
                                "voice": None,
                                "text": None,
                            }
                        ],
                        "other_info": "x",
                    }
                ],
            }
        ]
    }

    mock_http.get.return_value = json.dumps(nested)

    out = service.get_packages({"flat": True})
    assert "data" in out and isinstance(out["data"], list)
    assert len(out["data"]) == 1
    flat0 = out["data"][0]
    assert flat0["package_id"] == "bg-1gb-7d"
    assert flat0["slug"] == "bg"
    assert flat0["countries"] == ["BG"]
    assert flat0["image"] == "http://img"


# ---------- convenience methods dispatch ----------


def test_convenience_methods_delegate_to_get_packages(service, monkeypatch):
    called = []

    def fake_get_packages(p):
        called.append(p)
        return {"data": []}

    monkeypatch.setattr(
        PackagesService, "get_packages", lambda self, p=None: fake_get_packages(p)
    )

    service.get_all_packages(flat=True, limit=10, page=2)
    service.get_sim_packages(flat=False, limit=None, page=3)
    service.get_local_packages(flat=True, limit=5, page=None)
    service.get_global_packages(flat=False, limit=None, page=None)
    service.get_country_packages("us", flat=True, limit=7)

    assert called[0] == {"flat": True, "limit": 10, "page": 2}
    assert called[1] == {"flat": False, "limit": None, "page": 3, "simOnly": True}
    assert called[2] == {"flat": True, "limit": 5, "page": None, "type": "local"}
    assert called[3] == {"flat": False, "limit": None, "page": None, "type": "global"}
    assert called[4] == {"flat": True, "limit": 7, "country": "US"}
