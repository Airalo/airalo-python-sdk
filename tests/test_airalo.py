# tests/test_airalo.py

import types
import sys
import pytest
from unittest.mock import Mock

from airalo.exceptions.airalo_exception import AiraloException
from airalo.airalo import Airalo


# ---------- tiny fakes with correct __init__ signatures ----------


class FakeConfig:
    def __init__(self, src=None):
        self.src = src

    def get(self, key, default=None):
        return "secret-123" if key == "client_secret" else default

    def get_url(self):
        return "https://api.example.com"


class FakeHttp:
    def __init__(self, config):
        self.config = config


class FakeMultiHttp:
    def __init__(self, config):
        self.config = config


class FakeSignature:
    def __init__(self, secret):
        self.secret = secret


class FakeOAuth:
    def __init__(self, config, http, signature):
        self.config, self.http, self.signature = config, http, signature

    def get_access_token(self):
        return "AT"

    def refresh_token(self):
        return "AT2"


# generic service stub that records calls and returns a marker
class SRV:
    def __init__(self, *a, **k):
        self.calls = []

    def __getattr__(self, name):
        def _(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return {"called": name, "args": args, "kwargs": kwargs}

        return _


# ---------- fixtures ----------


@pytest.fixture(autouse=True)
def reset_pool():
    Airalo._pool = {}
    yield
    Airalo._pool = {}


@pytest.fixture
def wire_minimal_monkeypatch(monkeypatch):
    # Patch constructors where the client looks them up
    monkeypatch.setattr("airalo.airalo.Config", FakeConfig)
    monkeypatch.setattr("airalo.airalo.HttpResource", FakeHttp)
    monkeypatch.setattr("airalo.airalo.MultiHttpResource", FakeMultiHttp)
    monkeypatch.setattr("airalo.airalo.Signature", FakeSignature)
    monkeypatch.setattr("airalo.airalo.OAuthService", FakeOAuth)
    # Services
    monkeypatch.setattr("airalo.airalo.PackagesService", SRV)
    monkeypatch.setattr("airalo.airalo.OrderService", SRV)
    monkeypatch.setattr("airalo.airalo.TopupService", SRV)
    monkeypatch.setattr("airalo.airalo.InstallationInstructionsService", SRV)
    monkeypatch.setattr("airalo.airalo.FutureOrderService", SRV)
    monkeypatch.setattr("airalo.airalo.CompatibilityDevicesService", SRV)
    monkeypatch.setattr("airalo.airalo.SimService", SRV)
    monkeypatch.setattr("airalo.airalo.ExchangeRatesService", SRV)
    monkeypatch.setattr("airalo.airalo.VoucherService", SRV)
    return monkeypatch


def test_init_raises_when_token_missing(monkeypatch):
    monkeypatch.setattr("airalo.airalo.Config", FakeConfig)
    monkeypatch.setattr("airalo.airalo.HttpResource", FakeHttp)
    monkeypatch.setattr("airalo.airalo.MultiHttpResource", FakeMultiHttp)
    monkeypatch.setattr("airalo.airalo.Signature", FakeSignature)

    class NoTokOAuth(FakeOAuth):
        def get_access_token(self):
            return None

    monkeypatch.setattr("airalo.airalo.OAuthService", NoTokOAuth)
    with pytest.raises(AiraloException) as e:
        Airalo(config={})
    assert "Failed to obtain access token" in str(e.value)


def test_refresh_token_updates_value(wire_minimal_monkeypatch):
    c = Airalo(config={})
    assert c.get_access_token() == "AT"
    assert c.refresh_token() == "AT2"
    assert c.get_access_token() == "AT2"


# ---------- clear_cache patches the imported module, not the class on airalo.airalo ----------


def test_clear_cache_calls_cached_clear(monkeypatch, wire_minimal_monkeypatch):
    called = {"ok": False}
    fake_cached_mod = types.ModuleType("airalo.helpers.cached")

    class _Cached:
        @staticmethod
        def clear_cache():
            called["ok"] = True

    fake_cached_mod.Cached = _Cached
    sys.modules["airalo.helpers.cached"] = fake_cached_mod

    c = Airalo(config={})
    c.clear_cache()
    assert called["ok"] is True


# ---------- package method delegation ----------


def test_package_methods_delegate_and_return(wire_minimal_monkeypatch):
    c = Airalo(config={})
    out1 = c.get_all_packages(flat=True, limit=5, page=2)
    out2 = c.get_sim_packages(flat=False, limit=None, page=3)
    out3 = c.get_local_packages(flat=True, limit=7, page=None)
    out4 = c.get_global_packages(flat=False, limit=None, page=None)
    out5 = c.get_country_packages("us", flat=True, limit=9)
    assert out1["called"] == "get_all_packages"
    assert out2["called"] == "get_sim_packages"
    assert out3["called"] == "get_local_packages"
    assert out4["called"] == "get_global_packages"
    assert out5["called"] == "get_country_packages"


# ---------- order methods delegation ----------


def test_order_methods_delegate(wire_minimal_monkeypatch):
    c = Airalo(config={})
    o1 = c.order("p1", 2, description="d")
    o2 = c.order_with_email_sim_share(
        "p1", 1, {"to_email": "a@b.com", "sharing_option": ["link"]}
    )
    o3 = c.order_async("p1", 1, webhook_url="https://hook", description=None)
    b1 = c.order_bulk({"p1": 1}, description="D")
    b2 = c.order_bulk_with_email_sim_share(
        {"p1": 1}, {"to_email": "a@b.com", "sharing_option": ["link"]}, description=None
    )
    b3 = c.order_async_bulk({"p1": 1}, webhook_url=None, description=None)

    assert o1["called"] == "create_order"
    assert o2["called"] == "create_order_with_email_sim_share"
    assert o3["called"] == "create_order_async"
    assert b1["called"] == "create_order_bulk"
    assert b2["called"] == "create_order_bulk_with_email_sim_share"
    assert b3["called"] == "create_order_async_bulk"


def test_order_bulk_none_when_empty(wire_minimal_monkeypatch):
    c = Airalo(config={})
    assert c.order_bulk({}) is None
    assert (
        c.order_bulk_with_email_sim_share(
            {}, {"to_email": "x", "sharing_option": ["link"]}
        )
        is None
    )
    assert c.order_async_bulk({}, webhook_url=None) is None


# ---------- topup delegation ----------


def test_topup_delegates(wire_minimal_monkeypatch):
    c = Airalo(config={})
    t = c.topup("pkg", "iccid", description="hi")
    assert t["called"] == "create_topup"


# ---------- other delegations ----------


def test_misc_delegations(wire_minimal_monkeypatch):
    c = Airalo(config={})
    ii = c.get_installation_instructions({"iccid": "x"})
    f1 = c.create_future_order({"x": 1})
    f2 = c.cancel_future_order({"y": 2})
    cd = c.get_compatible_devices()
    su = c.sim_usage("iccid")
    sb = c.sim_usage_bulk(["a", "b"])
    st = c.get_sim_topups("iccid")
    sp = c.get_sim_package_history("iccid")
    fx = c.get_exchange_rates({"to": "USD"})
    v1 = c.create_voucher({"amount": 1, "quantity": 1})
    v2 = c.create_esim_voucher({"vouchers": [{"package_id": "p", "quantity": 1}]})

    assert ii["called"] == "get_instructions"
    assert f1["called"] == "create_future_order"
    assert f2["called"] == "cancel_future_order"
    assert cd["called"] == "get_compatible_devices"
    assert su["called"] == "get_usage"
    assert sb["called"] == "get_usage_bulk"
    assert st["called"] == "get_topups"
    assert sp["called"] == "get_package_history"
    assert fx["called"] == "exchange_rates"
    assert v1["called"] == "create_voucher"
    assert v2["called"] == "create_esim_voucher"
