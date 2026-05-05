"""Vercel FastAPI entrypoint.

Vercel's Python runtime auto-discovers `app` from a small set of well-known
paths at the service root (main.py, app.py, asgi.py, …). The real application
lives in seabeacon/main.py — this module re-exports it so the runtime can
locate it without any extra config.

The sys.path insert covers the case where Vercel imports this file via a
constructed module spec rather than running it with the service directory as
the cwd; either way `seabeacon` resolves.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parent
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))

from seabeacon.main import app  # noqa: E402,F401

__all__ = ["app"]
