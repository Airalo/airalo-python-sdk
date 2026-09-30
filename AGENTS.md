# AGENTS.md: Airalo Python SDK

Instructions for AI coding agents working in this repository. Human contributors are welcome to read it too.

## Where changes happen

This public repository (`github.com/Airalo/airalo-python-sdk`) is the canonical source for the SDK.
All SDK changes originate here, as pull requests against `main`.

## What this is

`airalo-sdk` is the Python client for the Airalo Partner API (eSIM packages, orders, top-ups, SIM usage, vouchers, exchange rates, future orders, compatible devices).
It handles authentication, request signing, caching and rate-limit handling for the partner, and returns responses as standard Python dicts.

- Python `>=3.10` runtime support; CI runs on 3.10 (the floor) and 3.13.
- Two runtime dependencies: `requests` and `cryptography`. Keep it that way.
- Distributed on PyPI as `airalo-sdk`; public method signatures are a semver contract.

### Public surface

The stable API is exactly what `airalo/__init__.py` exports; everything else is internal.

- `airalo.Airalo` (`airalo/airalo.py`): the client. `Airalo(config)` where `config` is a dict, `Config`, or JSON string with `client_id` and `client_secret`.
- `airalo.Config` (`airalo/config.py`): config parsing and validation.
- Responses are `Optional[dict]` (or `Optional[list]`) — standard Python data, no wrapper type.
- Every error the SDK raises derives from `airalo.AiraloException` (`ConfigurationError`, `AuthenticationError`, `ValidationError`, `APIError`, `NetworkError`).
- `__version__` in `airalo/__init__.py` is the single source of truth for the version string.

## Layout

```
airalo/
├── __init__.py        # public exports + __version__
├── airalo.py          # Airalo — the client; _init_services() wires services via a shared _pool
├── config.py          # Config parsing + validation (client_id, client_secret mandatory)
├── constants/         # api_constants (endpoints), sdk_constants
├── services/          # one *_service.py per API area (packages, order, topup, sim, …)
├── resources/         # http_resource, multi_http_resource (HTTP layer)
├── helpers/           # crypt, signature, cached, date_helper, validators
└── exceptions/        # AiraloException hierarchy
tests/                 # mirrors airalo/ (test_airalo.py, test_config.py, services/)
README.md              # public method reference ("Methods Interface")
```

### Adding or changing an endpoint

1. Add the endpoint path to `airalo/constants/api_constants.py`, not as an inline string.
2. Implement the call in the relevant `airalo/services/*_service.py`, or add a new service that follows a neighbouring service's constructor. Validate every input and raise `AiraloException` (or a subclass) with a clear message **before** any HTTP call.
3. Wire any new service in `Airalo._init_services()`, add its matching `self._<name>` attribute, and register it in the `_pool` dict in `__init__`.
4. Add the public method to `airalo/airalo.py` with type hints and a docstring matching the surrounding methods.
5. If it introduces a new public export, add it to `__all__` in `airalo/__init__.py`.
6. Document the method in the `README.md` "Methods Interface" section, with a usage example that uses placeholder credentials.
7. Add or extend a test under `tests/services/` that mocks HTTP — never call the real API.

Signed vs read-only: order, top-up, voucher and future-order calls take a `Signature` (see how `OrderService`/`TopupService` are constructed in `_init_services()`); read-only calls do not.

## Code conventions

- PEP 8, as enforced by `black` (default line length 88; no repo override). Match the surrounding code; don't reformat files outside the task.
- Type hints on public parameters and return types (`Optional[...]`, `Dict[str, Any]`, `List[...]`), and a docstring with `Args:`/`Returns:`/`Raises:` like the existing methods.
- Raise only `AiraloException` and its subclasses from the SDK; don't leak `requests` or other library exceptions to callers.
- Keep `pylint` happy — the CI gate requires a score of at least 8 (`pylint --fail-under=8 airalo`).

## Testing

- `pytest`. Tests live under `tests/` and mirror `airalo/` — service tests in `tests/services/`, named `test_<service>_service.py`, functions `test_*`.
- Unit tests only. **Never call the real Partner API from tests.** Mock the HTTP layer (`unittest.mock`), as the existing service tests do.
- Every behaviour change needs a test that fails without it.

## Quality gates

Run these in order after `pip install -e ".[dev]"` (or `pip install -r requirements-dev.txt`).
CI runs the lint and test gates on every push and PR to `main` (`.github/workflows/pylint.yml`, `.github/workflows/test.yml`).

1. `black airalo tests`: format.
2. `pylint --fail-under=8 airalo`: lint; the score must stay at or above 8. This is the CI gate.
3. `pytest -q --cov=airalo --cov-report=term tests`: full test suite must pass.

If a gate fails, make the smallest fix that makes it pass, rerun the same gate, and don't move on until it passes.
`mypy` is available as a dev dependency for optional type checking; it is not a CI gate.

## Definition of done

- All three gates pass.
- The service, the `Airalo` method, the README and the tests are updated for any public-surface change.
- No breaking change to a public signature without explicit approval (this would need a major version bump).
- No credentials, tokens or customer data in code, tests, fixtures or docs.

## Branches, commits and PRs

- Branch from `main`, named `<type>/<TICKET>-short-description`, where `<type>` is `feature`, `fix` or `bugfix` (e.g. `feature/AP-1234-sim-usage-bulk`).
- Commits and PR titles use Conventional Commits with the ticket key in parentheses:
  `feat: Support SIM usage bulk (AP-1234)`, `fix: ...`, `chore: ...`.
- PRs target `main` and need green CI before merge.

## Off limits without explicit approval

- New runtime dependencies, or raising the minimum Python version.
- `.github/workflows/`.
- Breaking changes to public method signatures or response shapes.
- Weakening auth, request signing (`helpers/signature.py`), encryption (`helpers/crypt.py`) or TLS verification in `resources/`.

## AI tooling

Claude Code picks these up automatically. Other agents can read them as plain workflow docs.

- `.claude/skills/add-endpoint/`: step-by-step workflow for adding or changing an endpoint.
- `.claude/skills/release/`: release workflow (`/release`): version bump PR, tag, GitHub release, PyPI checklist.
- `.claude/agents/sdk-reviewer.md`: SDK-specific diff review; run it before opening a PR.
- `.claude/hooks/py-lint.sh`: syntax-checks every Python file Claude edits (wired in `.claude/settings.json`).

## Security

- This is a public repository. Never commit `client_id`, `client_secret`, access tokens or partner account identifiers, not even sandbox ones. Use placeholders like `<YOUR_API_CLIENT_ID>` in docs and examples.
- Never log or echo credentials, tokens, ICCIDs or other customer data.
- Keep local experiment scripts untracked (`test.py` is already git-ignored).
