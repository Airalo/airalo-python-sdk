---
name: add-endpoint
description: Add a new Partner API endpoint or public SDK method to the Airalo Python SDK end to end, covering the constant, service, client method, exports, README and tests. Use when asked to add, wrap or expose a new endpoint or API method, or to extend an existing one with new parameters.
---

# Add an endpoint to the SDK

This workflow follows the "Adding or changing an endpoint" checklist in `AGENTS.md`. Work through the steps in order, and don't skip any: missing the README entry or the tests is the most common review failure.

## 1. Gather the spec

Confirm these with the developer before writing code, and ask for anything you can't infer:

- Endpoint path and HTTP method (`GET` / `POST` / `DELETE`).
- Request parameters: required vs optional, types, validation rules.
- Whether it needs request signing. Order, top-up, voucher and future-order calls are signed (`Signature`); read-only calls are not.
- Whether responses should be cached, and for how long.
- The public method name and signature. Match the naming of neighbouring methods (`get_x`, `x_bulk`, …).
- Which ticket it belongs to (needed for the commit title).

## 2. Pick a template

Find the closest existing method and copy its shape instead of inventing a new one:

| Kind of call | Template |
|---|---|
| Simple GET, no params | `CompatibilityDevicesService.get_compatible_devices()` |
| GET with params + caching | `SimService.sim_usage()` |
| Signed POST | `TopupService`, `OrderService` |
| Bulk / parallel requests | `SimService.sim_usage_bulk()` (uses the multi-HTTP resource) |

Read the template service and its `Airalo` method before continuing.

## 3. Implement

1. **Constant:** add the path slug to `airalo/constants/api_constants.py` next to related slugs.
2. **Service:** add the method to the relevant `airalo/services/*_service.py`, or create a new service that follows the template's constructor. Validate every input first and raise `AiraloException` (or a subclass) with a clear message **before** any HTTP call. Return an `Optional[dict]`/`Optional[list]`.
3. **Wiring (new service only):** construct it in `Airalo._init_services()`, add the matching `self._<name>` attribute, and register it in the `_pool` dict in `Airalo.__init__()`, respecting the existing `self._pool.get(...) or Service(...)` pattern.
4. **Client method:** add the public method to `airalo/airalo.py` with type hints and an `Args:`/`Returns:`/`Raises:` docstring matching neighbouring methods.
5. **Exports:** if the change introduces a new public class, add it to `__all__` in `airalo/__init__.py`.
6. **README:** add an entry under "Methods Interface" in the same format as its neighbours: signature, a short description, and a usage example. Use placeholder credentials (`<YOUR_API_CLIENT_ID>`) only.
7. **Tests:** add or extend a test under `tests/services/`, mocking the HTTP layer with `unittest.mock` as `tests/services/test_sim_service.py` does. Cover the happy path and each validation failure. Never call the real API.

Constraints: stay **Python 3.10 compatible**, add no new runtime dependencies, and don't break existing signatures.

## 4. Verify

Run the quality gates in `AGENTS.md`, fixing and rerunning each until it passes:

1. `black airalo tests`
2. `pylint --fail-under=8 airalo`
3. `pytest -q --cov=airalo --cov-report=term tests`

Then run the `sdk-reviewer` agent on the diff and address any blockers.

## 5. Hand off

Summarise the files you changed and propose a commit title such as `feat: <what the method does> (<TICKET>)`. Don't commit or push unless the developer asks.
