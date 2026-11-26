# Changelog

## Unreleased

- Tests: the provider and the dashboard route against a fake TensorFold server on loopback, with Hermes' modules stubbed.
- CI on Python 3.12 and 3.13: ruff check, ruff format --check and pytest.

## 0.1.0 (2026-11-08)

- TensorFold as a Hermes model provider: the served models from its `/v1/models` and each model's context window from the same list.
- A TensorFold tab in Hermes' dashboard: model, speed, streams, token totals, MTP acceptance and memory from `/health`, `/stats` and `/v1/models`. The key stays on the dashboard's side.
- `tensorfold serve`'s own loopback default, `http://127.0.0.1:8080/v1`; a scoped key needs `inference,read`.
- The dashboard route reads the endpoint and the key with `get_secret`, so it follows the active profile.
