"""Vercel FastAPI entrypoint.

Vercel's Python runtime auto-discovers `app` from a small set of well-known
paths at the service root (main.py, app.py, asgi.py, …). The real application
lives in seabeacon/main.py — this module re-exports it so the runtime can
locate it without any extra config.
"""
from seabeacon.main import app  # noqa: F401

__all__ = ["app"]
