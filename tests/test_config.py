import json
import pytest

from airalo.config import Config
from airalo.constants.api_constants import ApiConstants
from airalo.exceptions.airalo_exception import ConfigurationError


class ObjWithAttrs:
    def __init__(
        self, client_id="id", client_secret="sec", env="sandbox", http_headers=None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.env = env
        self.http_headers = http_headers or ["X-Foo: bar"]


# -------- init / validation --------


def test_init_requires_data():
    with pytest.raises(ConfigurationError) as e:
        Config(None)
    assert "Config data is not provided" in str(e.value)


def test_init_from_dict_and_missing_keys():
    cfg = Config({"client_id": "id", "client_secret": "sec"})
    assert cfg.get("client_id") == "id"
    assert cfg.get_environment() == "production"

    with pytest.raises(ConfigurationError):
        Config({"client_secret": "sec"})  # missing client_id
    with pytest.raises(ConfigurationError):
        Config({"client_id": "id"})  # missing client_secret
    with pytest.raises(ConfigurationError):
        Config({"client_id": "", "client_secret": "sec"})  # empty value invalid


def test_init_from_json_string_and_bad_json():
    cfg = Config(
        json.dumps({"client_id": "id", "client_secret": "sec", "env": "sandbox"})
    )
    assert cfg.get_environment() == "sandbox"

    with pytest.raises(ConfigurationError):
        Config("{not json}")


def test_init_from_object_with_attrs():
    cfg = Config(ObjWithAttrs())
    assert cfg.get("client_id") == "id"
    assert cfg.get("client_secret") == "sec"
    assert cfg.get_environment() == "sandbox"
    assert cfg.get_http_headers() == ["X-Foo: bar"]


# -------- getters --------


def test_get_and_get_config_returns_copy():
    data = {"client_id": "id", "client_secret": "sec", "env": "sandbox"}
    cfg = Config(data)
    assert cfg.get("client_id") == "id"
    out = cfg.get_config()
    assert out == data
    out["client_id"] = "mutated"
    assert cfg.get("client_id") == "id"  # prove it's a copy


def test_get_credentials_dict_and_string():
    cfg = Config({"client_id": "id", "client_secret": "sec"})
    creds = cfg.get_credentials()
    assert creds == {"client_id": "id", "client_secret": "sec"}

    creds_str = cfg.get_credentials(as_string=True)
    # urlencoded order can vary, check both possibilities
    assert creds_str in (
        "client_id=id&client_secret=sec",
        "client_secret=sec&client_id=id",
    )


def test_get_environment_default_and_override():
    assert (
        Config({"client_id": "id", "client_secret": "sec"}).get_environment()
        == "production"
    )
    assert (
        Config(
            {"client_id": "id", "client_secret": "sec", "env": "sandbox"}
        ).get_environment()
        == "sandbox"
    )


def test_get_url_returns_production_constant():
    cfg = Config({"client_id": "id", "client_secret": "sec"})
    assert cfg.get_url() == ApiConstants.PRODUCTION_URL


def test_get_http_headers_default_and_custom():
    cfg_default = Config({"client_id": "id", "client_secret": "sec"})
    assert cfg_default.get_http_headers() == []

    cfg_custom = Config(
        {
            "client_id": "id",
            "client_secret": "sec",
            "http_headers": ["X-A: 1", "X-B: 2"],
        }
    )
    assert cfg_custom.get_http_headers() == ["X-A: 1", "X-B: 2"]
