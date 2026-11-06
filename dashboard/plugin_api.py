"""The TensorFold tab's one route: the server's /health, /stats and /v1/models read here, so its key stays server-side."""

import asyncio
import json
import os
import urllib.error
import urllib.request

from fastapi import APIRouter

router = APIRouter()

# The provider's endpoint: TENSORFOLD_BASE_URL when set, else `tensorfold serve`'s loopback default.
DEFAULT_BASE_URL = "http://127.0.0.1:8080/v1"


def _root() -> str:
    base = (os.environ.get("TENSORFOLD_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    return base[: -len("/v1")] if base.endswith("/v1") else base


def _get(path: str) -> dict:
    key = os.environ.get("TENSORFOLD_API_KEY", "")
    req = urllib.request.Request(_root() + path, headers={"Authorization": f"Bearer {key}"} if key else {})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return {"ok": True, "body": json.load(r)}
    except urllib.error.HTTPError as e:
        hint = " (start the server with --dashboard)" if path == "/stats" and e.code == 404 else ""
        return {"ok": False, "error": f"{path}: HTTP {e.code}{hint}"}
    except (OSError, ValueError) as e:
        return {"ok": False, "error": f"{path}: {e}"}


@router.get("/summary")
async def summary():
    health, stats, models = await asyncio.gather(*(asyncio.to_thread(_get, p) for p in ("/health", "/stats", "/v1/models")))
    return {"server": _root(), "health": health, "stats": stats, "models": models}
