"""TensorFold's native server as a Hermes model provider: its own /v1/models, a loopback endpoint unless asked."""

import json
import urllib.request

from providers import register_provider
from providers.base import ProviderProfile

# `tensorfold serve`'s own bind: the engine stays on loopback with its API key.
DEFAULT_BASE_URL = "http://127.0.0.1:8080/v1"


def _models(base_url: str, api_key: str, timeout: float = 8.0) -> list[dict]:
    """The server's model entries (id, context_length, reasoning), or none when it does not answer."""
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    req = urllib.request.Request(base_url.rstrip("/") + "/models", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r).get("data", [])
    except (OSError, ValueError, AttributeError):
        return []
    return [m for m in data if isinstance(m, dict)]


class TensorFoldProfile(ProviderProfile):
    """A served model's context window comes from the server, which knows the window it was started with."""

    def live_context_length(self, model: str, *, api_key: str = "", base_url: str = "") -> int | None:
        for m in _models(base_url or self.base_url, api_key):
            if m.get("id") == model and isinstance(m.get("context_length"), int):
                return m["context_length"]
        return None


register_provider(
    TensorFoldProfile(
        name="tensorfold",
        aliases=("tf",),
        display_name="TensorFold",
        description="TensorFold native server (OpenAI-compatible, on this machine by default)",
        signup_url="https://github.com/ashhart/TensorFold",
        env_vars=("TENSORFOLD_API_KEY", "TENSORFOLD_BASE_URL"),
        base_url=DEFAULT_BASE_URL,
        auth_type="api_key",
    )
)
