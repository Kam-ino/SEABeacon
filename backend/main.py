"""Vercel FastAPI entrypoint for SEABeacon.

Constructs the FastAPI `app` at module top level so Vercel's static parser
discovers the symbol without having to follow a `from seabeacon.main import
app` re-export through deps that aren't installed yet at parse time.

Mirror of seabeacon.main — keep in sync. Local dev (`python -m uvicorn
seabeacon.main:app`) continues to use the package-internal entrypoint.
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parent
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from seabeacon.bot.dispatcher import get_dispatcher
from seabeacon.bot.telegram_bot import lifespan_start, lifespan_stop
from seabeacon.db import init_db
from seabeacon.routes import alerts, events, scenarios, signals, subscriptions
from seabeacon.services.scenario_clock import get_runner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("seabeacon")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    try:
        from seabeacon.seed import seed_all
        seed_all()
    except Exception as exc:  # noqa: BLE001
        logger.warning("seed step skipped: %s", exc)

    try:
        await lifespan_start()
        dispatcher = get_dispatcher()
        runner = get_runner()
        runner.attach_sender(dispatcher.send)
    except Exception as exc:  # noqa: BLE001
        # Telegram polling can't survive serverless cold-starts; degrade
        # gracefully so the API and SSE stream still come up.
        logger.warning("bot startup skipped: %s", exc)

    yield

    runner = get_runner()
    for slug in list(runner.runs.keys()):
        await runner.stop(slug)
    try:
        await lifespan_stop()
    except Exception as exc:  # noqa: BLE001
        logger.warning("bot shutdown error: %s", exc)


app = FastAPI(
    title="SEABeacon API",
    version="0.1.0",
    description="Cross-border disaster early-warning demo for ASEAN.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scenarios.router)
app.include_router(alerts.router)
app.include_router(signals.router)
app.include_router(subscriptions.router)
app.include_router(events.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "seabeacon"}


__all__ = ["app"]
