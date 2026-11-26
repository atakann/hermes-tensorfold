"""Provider and dashboard tests: Hermes' modules stubbed, a fake TensorFold server on loopback."""

import asyncio
import importlib.util
import json
import sys
import threading
import types
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTERED = []
SECRETS = {}


def _stub_hermes():
    providers = types.ModuleType("providers")
    providers.register_provider = REGISTERED.append
    base = types.ModuleType("providers.base")

    class ProviderProfile:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    base.ProviderProfile = ProviderProfile
    scope = types.ModuleType("agent.secret_scope")
    scope.get_secret = lambda name, default="": SECRETS.get(name, default)
    sys.modules.update(
        {
            "providers": providers,
            "providers.base": base,
            "agent": types.ModuleType("agent"),
            "agent.secret_scope": scope,
        }
    )


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_stub_hermes()
plugin = _load("tensorfold_plugin", ROOT / "__init__.py")
api = _load("tensorfold_api", ROOT / "dashboard" / "plugin_api.py")


class FakeTensorFold(BaseHTTPRequestHandler):
    """/v1/models and /health answer; /stats is 404, as on a server started without --dashboard."""

    seen = []
    bodies = {"/v1/models": {"data": [{"id": "local-model", "context_length": 65536}]}, "/health": {"status": "ok"}}

    def do_GET(self):
        FakeTensorFold.seen.append((self.path, self.headers.get("Authorization")))
        body = self.bodies.get(self.path)
        self.send_response(200 if body else 404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body or {}).encode())

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    srv = HTTPServer(("127.0.0.1", 0), FakeTensorFold)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    FakeTensorFold.seen.clear()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()
    srv.server_close()


def test_registers_one_provider_on_loopback():
    # pytest also imports the repo's __init__.py as the root package, so the profile can be registered twice
    assert {p.name for p in REGISTERED} == {"tensorfold"}
    p = REGISTERED[-1]
    assert p.name == "tensorfold" and p.base_url == "http://127.0.0.1:8080/v1"
    assert p.env_vars == ("TENSORFOLD_API_KEY", "TENSORFOLD_BASE_URL")


def test_context_length_from_the_server(server):
    p = REGISTERED[-1]
    assert p.live_context_length("local-model", api_key="k", base_url=server + "/v1") == 65536
    assert FakeTensorFold.seen == [("/v1/models", "Bearer k")]


def test_unknown_model_has_no_context_length(server):
    assert REGISTERED[-1].live_context_length("other", base_url=server + "/v1") is None


def test_server_down_gives_none():
    assert REGISTERED[-1].live_context_length("local-model", base_url="http://127.0.0.1:9/v1") is None


def test_dashboard_root_drops_v1():
    SECRETS.clear()
    SECRETS["TENSORFOLD_BASE_URL"] = "http://127.0.0.1:8080/v1/"
    assert api._root() == "http://127.0.0.1:8080"


def test_summary_reads_three_routes_with_the_key(server):
    SECRETS.clear()
    SECRETS.update(TENSORFOLD_BASE_URL=server + "/v1", TENSORFOLD_API_KEY="k")
    out = asyncio.run(api.summary())
    assert out["health"]["ok"] and out["models"]["ok"]
    assert out["stats"] == {"ok": False, "error": "/stats: HTTP 404 (start the server with --dashboard)"}
    assert {a for _, a in FakeTensorFold.seen} == {"Bearer k"}


def test_no_key_sends_no_header(server):
    SECRETS.clear()
    SECRETS["TENSORFOLD_BASE_URL"] = server
    asyncio.run(api.summary())
    assert {a for _, a in FakeTensorFold.seen} == {None}
