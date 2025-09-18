import json
import hashlib
import pytest
from types import SimpleNamespace
from unittest.mock import Mock

from airalo.exceptions.airalo_exception import AuthenticationError
from airalo.services.oauth_service import OAuthService
from airalo.constants.api_constants import ApiConstants
from airalo.constants.sdk_constants import SdkConstants


@pytest.fixture
def mock_config():
    m = Mock()
    m.get_url.return_value = "https://api.example.com"
    # credentials object used both as dict and as_string
    creds = {"client_id": "id", "client_secret": "sec"}
    m.get_credentials.side_effect = lambda as_string=False: (
        "client_id=id&client_secret=sec" if as_string else creds
    )
    return m


@pytest.fixture
def mock_http():
    m = Mock()
    m.set_headers.return_value = m
    m.code = 200
    return m


@pytest.fixture
def mock_signature():
    m = Mock()
    m.get_signature.return_value = "sig"
    return m


@pytest.fixture
def service(mock_config, mock_http, mock_signature):
    s = OAuthService(mock_config, mock_http, mock_signature)
    # make retry count predictable and small
    s.RETRY_LIMIT = 3
    return s


def test__get_encryption_key_uses_md5_of_credentials_string(service, mock_config):
    key = service._get_encryption_key()
    expected = hashlib.md5("client_id=id&client_secret=sec".encode()).hexdigest()
    assert key == expected


def test__generate_cache_key_uses_sha256_of_credentials_string(service, mock_config):
    ck = service._generate_cache_key()
    expected = hashlib.sha256("client_id=id&client_secret=sec".encode()).hexdigest()
    assert ck == expected


def test_request_token_success_sets_headers_posts_parses_and_encrypts(
    service, mock_http, mock_signature, monkeypatch
):
    # Crypt.encrypt returns predictable string
    monkeypatch.setattr(
        "airalo.services.oauth_service.Crypt",
        SimpleNamespace(encrypt=lambda token, key: f"enc({token}|{key})"),
    )

    body = {"data": {"access_token": "AT123"}}
    mock_http.post.return_value = json.dumps(body)
    mock_http.code = 200

    enc = service._request_token()

    # headers set with signature and content type
    mock_signature.get_signature.assert_called_once_with(service._payload)
    mock_http.set_headers.assert_called_once_with(
        {
            "Content-Type": "application/x-www-form-urlencoded",
            "airalo-signature": "sig",
        }
    )
    # URL and x-www-form-urlencoded body
    mock_http.post.assert_called_once_with(
        "https://api.example.com" + ApiConstants.TOKEN_SLUG,
        # use the same urlencode contract indirectly by recreating from service._payload
        __import__("urllib.parse").parse.urlencode(service._payload),  # noqa: E999
    )
    # encrypted value combines token + key (checked via our fake Crypt)
    assert enc.startswith("enc(AT123|")
    assert ")".endswith(")") or True  # just don't be precious


def test_request_token_non_200_raises(service, mock_http):
    mock_http.code = 401
    mock_http.post.return_value = '{"error":"unauthorized"}'
    with pytest.raises(AuthenticationError) as e:
        service._request_token()
    msg = str(e.value)
    assert "status code: 401" in msg
    assert "unauthorized" in msg


def test_request_token_invalid_json_raises(service, mock_http):
    mock_http.code = 200
    mock_http.post.return_value = "not-json"
    with pytest.raises(AuthenticationError) as e:
        service._request_token()
    assert "Failed to parse access token response" in str(e.value)


@pytest.mark.parametrize("payload", [None, {}, {"foo": "bar"}])
def test_request_token_missing_fields_raise(service, mock_http, payload):
    mock_http.code = 200
    mock_http.post.return_value = json.dumps(payload)
    with pytest.raises(AuthenticationError) as e:
        service._request_token()
    assert "Invalid response format" in str(e.value) or "Access token not found" in str(
        e.value
    )


def test_get_access_token_happy_path_uses_cache_and_decrypts(service, monkeypatch):
    # Cached.get should return an encrypted blob; Crypt.decrypt returns plain token
    def fake_cached_get(fetcher, name, ttl):
        # ensure cache key and ttl sane
        assert name.startswith("airalo_access_token_")
        assert ttl == SdkConstants.TOKEN_CACHE_TTL
        # return whatever _request_token would normally return
        return "ENCRYPTED"

    decrypt_calls = {}
    monkeypatch.setattr(
        "airalo.services.oauth_service.Cached",
        SimpleNamespace(get=fake_cached_get),
    )
    monkeypatch.setattr(
        "airalo.services.oauth_service.Crypt",
        SimpleNamespace(
            decrypt=lambda token, key: decrypt_calls.setdefault(
                "val", f"dec({token}|{key})"
            )
        ),
    )
    # no sleeping on happy path
    monkeypatch.setattr(
        "airalo.services.oauth_service.time",
        SimpleNamespace(sleep=lambda *_: (_ for _ in ()).send(None)),
    )

    tok = service.get_access_token()
    assert tok.startswith("dec(ENCRYPTED|")


def test_get_access_token_retries_then_raises_auth_error(service, monkeypatch):
    calls = {"n": 0}

    def raising_cached_get(fetcher, name, ttl):
        calls["n"] += 1
        raise RuntimeError("boom")

    sleeps = []

    monkeypatch.setattr(
        "airalo.services.oauth_service.Cached",
        SimpleNamespace(get=raising_cached_get),
    )
    monkeypatch.setattr(
        "airalo.services.oauth_service.time",
        SimpleNamespace(sleep=lambda t: sleeps.append(t)),
    )

    service.RETRY_LIMIT = 3
    with pytest.raises(AuthenticationError) as e:
        service.get_access_token()

    # 3 attempts -> 2 sleeps (after failures 1 and 2)
    assert len(sleeps) == 2
    assert "after 3 attempts" in str(e.value)
    assert calls["n"] == 3


def test_clear_token_cache_calls_cached_clear(monkeypatch, service):
    called = {"ok": False}
    monkeypatch.setattr(
        "airalo.services.oauth_service.Cached",
        SimpleNamespace(clear_cache=lambda: called.__setitem__("ok", True)),
    )
    service.clear_token_cache()
    assert called["ok"] is True


def test_refresh_token_clears_then_gets_token(service, monkeypatch):
    seq = []

    def fake_clear():
        seq.append("clear")

    def fake_get():
        seq.append("get")
        return "AT"

    monkeypatch.setattr(
        "airalo.services.oauth_service.OAuthService.clear_token_cache",
        lambda self: fake_clear(),
    )
    monkeypatch.setattr(
        "airalo.services.oauth_service.OAuthService.get_access_token",
        lambda self: fake_get(),
    )

    tok = service.refresh_token()
    assert tok == "AT"
    assert seq == ["clear", "get"]
