import json
import hashlib
import pytest
from types import SimpleNamespace
from unittest.mock import Mock

from airalo.exceptions.airalo_exception import AiraloException
from airalo.services.sim_service import SimService
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
def mock_multi_http():
    # multi.tag(key).set_headers(...).get(url); exec() returns {key: response}
    class MultiMock:
        def __init__(self):
            self.calls = {}

        def tag(self, key):
            self.calls.setdefault(key, [])

            def set_headers(h):
                self.calls[key].append(("headers", h))
                return chain

            def get(url):
                self.calls[key].append(("get", url))
                return chain

            chain = SimpleNamespace(set_headers=set_headers, get=get)
            return chain

        def exec(self):
            return {k: json.dumps({"data": {"iccid": k}}) for k in self.calls}

    return MultiMock()


@pytest.fixture
def service(mock_config, mock_http, mock_multi_http):
    return SimService(
        mock_config, mock_http, mock_multi_http, access_token="toktoktoktoktoktoktok"
    )  # >20 chars


# ---------- init / validation ----------


def test_init_requires_token(mock_config, mock_http, mock_multi_http):
    with pytest.raises(AiraloException):
        SimService(mock_config, mock_http, mock_multi_http, access_token="")
    s = SimService(mock_config, mock_http, mock_multi_http, access_token="tok")
    assert s._base_url == "https://api.example.com"


@pytest.mark.parametrize(
    "val,ok",
    [
        ("89014103211118510720", True),  # 20 digits
        ("123456789012345678", True),  # 18
        ("1" * 22, True),  # 22
        ("", False),
        (None, False),
        ("12345678901234567", False),  # 17
        ("1" * 23, False),  # 23
        ("89014103211118510x20", False),  # non-digit
    ],
)
def test_is_valid_iccid(service, val, ok):
    assert service._is_valid_iccid(val) is ok


def test_build_url_requires_valid_iccid(service):
    with pytest.raises(AiraloException):
        service._build_url({"iccid": "bad"})
    url = service._build_url({"iccid": "89014103211118510720"}, ApiConstants.SIMS_USAGE)
    assert (
        url
        == f"https://api.example.com{ApiConstants.SIMS_SLUG}/89014103211118510720/{ApiConstants.SIMS_USAGE}"
    )


# ---------- _fetch_sim_data ----------


def test_fetch_sim_data_sets_headers_and_parses(service, mock_http):
    url = f"https://api.example.com{ApiConstants.SIMS_SLUG}/89014103211118510720/{ApiConstants.SIMS_USAGE}"
    mock_http.get.return_value = json.dumps({"data": {"ok": True}})
    out = service._fetch_sim_data(url)
    assert out == {"data": {"ok": True}}
    mock_http.set_headers.assert_called_once_with(
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer toktoktoktoktoktoktok",
        }
    )
    mock_http.get.assert_called_once_with(url)


def test_fetch_sim_data_empty_or_invalid_json_returns_data_none(service, mock_http):
    mock_http.get.return_value = ""
    assert service._fetch_sim_data("u") == {"data": None}
    mock_http.get.return_value = "not-json"
    assert service._fetch_sim_data("u") == {"data": None}


# ---------- sim_usage / sim_topups / sim_package_history with cache ----------


def test_sim_usage_uses_cache_ttl_300_and_returns_result(
    service, mock_http, monkeypatch
):
    captured = {}

    def cached_get(fetcher, key, ttl):
        captured["key"] = key
        captured["ttl"] = ttl
        mock_http.get.return_value = json.dumps({"data": {"usage": 1}})
        return fetcher()

    monkeypatch.setattr(
        "airalo.services.sim_service.Cached",
        SimpleNamespace(get=cached_get),
    )
    iccid = "89014103211118510720"
    out = service.sim_usage({"iccid": iccid})
    assert out == {"data": {"usage": 1}}
    assert captured["ttl"] == 300
    assert isinstance(captured["key"], str) and captured["key"].startswith("sim_")


def test_sim_usage_returns_none_when_no_data(service, mock_http, monkeypatch):
    monkeypatch.setattr(
        "airalo.services.sim_service.Cached",
        SimpleNamespace(get=lambda fetcher, key, ttl: {"data": None}),
    )
    assert service.sim_usage({"iccid": "89014103211118510720"}) is None


def test_sim_topups_and_packages_ttls(service, mock_http, monkeypatch):
    ttls = []

    def cached_get(fetcher, key, ttl):
        ttls.append(ttl)
        mock_http.get.return_value = json.dumps({"data": [1]})
        return fetcher()

    monkeypatch.setattr(
        "airalo.services.sim_service.Cached", SimpleNamespace(get=cached_get)
    )
    service.sim_topups({"iccid": "89014103211118510720"})
    service.sim_package_history({"iccid": "89014103211118510720"})
    assert 300 in ttls  # topups
    assert 900 in ttls  # packages


# ---------- sim_usage_bulk ----------


def test_sim_usage_bulk_queues_requests_and_parses(service, mock_multi_http):
    # default exec returns {"iccid": {"data": {"iccid": iccid}}}
    out = service.sim_usage_bulk(["89014103211118510720", "89014103211118510721"])
    assert set(out.keys()) == {"89014103211118510720", "89014103211118510721"}
    # ensure queued with headers and GET to usage endpoint
    for iccid, entries in mock_multi_http.calls.items():
        assert entries[0][0] == "headers"
        assert entries[1][0] == "get"
        assert entries[1][1].endswith(f"/{iccid}/{ApiConstants.SIMS_USAGE}")


def test_sim_usage_bulk_empty_list_returns_none(service):
    assert service.sim_usage_bulk([]) is None


def test_sim_usage_bulk_no_responses_returns_none(service, mock_multi_http):
    mock_multi_http.exec = lambda: {}
    assert service.sim_usage_bulk(["89014103211118510720"]) is None


# ---------- _get_cache_key ----------


def test_get_cache_key_includes_url_params_headers_and_partial_token(
    service, mock_config
):
    url = f"https://api.example.com{ApiConstants.SIMS_SLUG}/89014103211118510720/{ApiConstants.SIMS_USAGE}"
    params = {"iccid": "89014103211118510720"}
    key_data = {
        "url": url,
        "params": params,
        "headers": mock_config.get_http_headers(),
        "token": service._access_token[:20],
    }
    key_string = json.dumps(key_data, sort_keys=True)
    expected = f"sim_{hashlib.md5(key_string.encode()).hexdigest()}"
    assert service._get_cache_key(url, params) == expected


# ---------- convenience methods delegate ----------


def test_convenience_methods_delegate(service, monkeypatch):
    calls = {"usage": 0, "usage_bulk": 0, "topups": 0, "packages": 0}

    monkeypatch.setattr(
        SimService,
        "sim_usage",
        lambda self, p: calls.__setitem__("usage", p) or {"data": 1},
    )
    monkeypatch.setattr(
        SimService,
        "sim_usage_bulk",
        lambda self, l: calls.__setitem__("usage_bulk", l) or {"d": 1},
    )
    monkeypatch.setattr(
        SimService,
        "sim_topups",
        lambda self, p: calls.__setitem__("topups", p) or {"data": 2},
    )
    monkeypatch.setattr(
        SimService,
        "sim_package_history",
        lambda self, p: calls.__setitem__("packages", p) or {"data": 3},
    )

    iccid = "89014103211118510720"
    service.get_usage(iccid)
    service.get_usage_bulk([iccid])
    service.get_topups(iccid)
    service.get_package_history(iccid)

    assert calls["usage"] == {"iccid": iccid}
    assert calls["usage_bulk"] == [iccid]
    assert calls["topups"] == {"iccid": iccid}
    assert calls["packages"] == {"iccid": iccid}
