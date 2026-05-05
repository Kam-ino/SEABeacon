# SEABeacon

> Cross-border disaster early-warning demo for ASEAN.

SEABeacon ingests storm tracks, predicts impact zones across national borders, and pushes localized alerts to citizens via Telegram in their language. The flagship demo replays **Typhoon Kammuri (Tisoy, December 2019)** end-to-end: a judge clicks "Run Kammuri 2019", watches the typhoon track animate from the western Pacific across the Philippines into the South China Sea, sees impact zones light up across PH and VN, scripted social-media signals corroborate the model, and real Telegram messages reach subscribed phones in **English / Filipino / Vietnamese / Thai**.

This is a hackathon demo, not a production system.

---

## What it isn't

These are **DEMO STUBS** — clearly labeled in code with `# DEMO STUB:` comments — and would be replaced before any real-world use:

| Stub                                              | Replaced in production by                                                  |
| ------------------------------------------------- | -------------------------------------------------------------------------- |
| `services/propagation.py` radius-and-bearing rule | XGBoost trajectory + IMERG rainfall propagation model trained on IBTrACS   |
| `fixtures/kammuri_signals.json` scripted signals  | Multilingual NLP fine-tune on live Twitter/X, Facebook, Zalo, Line streams |
| `fixtures/kammuri_track.json` static replay       | JTWC / JMA / PAGASA real-time best-track ingest                            |
| Telegram-only delivery                            | Multi-platform: Viber, Zalo, Line, SMS, push, and national CAP feeds       |
| In-process bot + API                              | Split services, Redis-backed queue, horizontal scale                       |

We do not import `xgboost`, `torch`, `transformers`, `sklearn`, `tweepy`, or any social-platform SDK. Greppable: `grep -r "twitter\|facebook\|jtwc\|jma\|hysplit\|imerg" backend/` returns only mentions in comments and this README.

---

## 30-second demo run

You need [Docker](https://docs.docker.com/get-docker/) **or** Python 3.11+ and Node 20+, plus a Telegram bot token from [@BotFather](https://t.me/BotFather).

```bash
cp .env.example .env
# paste your TELEGRAM_BOT_TOKEN into .env

# Option A — Docker
docker compose up

# Option B — local dev
cd backend && pip install -e . && python -m uvicorn seabeacon.main:app --reload &
cd ../frontend && npm install --legacy-peer-deps && npm run dev
```

Then open <http://localhost:3000/dashboard> and click **Run Kammuri 2019**.

To receive Telegram alerts: open your bot in Telegram, send `/start`, then `/subscribe`, and pick PH+Filipino (you'll receive the most alerts during landfall) or VN+Vietnamese (you'll receive cross-border alerts roughly two scenario-days before historical).

---

## 90-second demo script

1. Open `/dashboard`. The ASEAN basemap is centered on the Philippines.
2. Click **Run Kammuri 2019** at default 60× speed (≈ 5 minutes wall time for the full 11-day scenario; bump to 120× or 300× to fit a shorter slot).
3. Within 30 seconds the storm icon appears east of the Philippines and a track line begins extending westward. Filipino-language scripted signals start appearing in the Signals feed.
4. As the storm approaches Sorsogon, urgent (red) and warning (amber) impact zones appear across Bicol. PH/Filipino subscribers receive Telegram alerts.
5. Roughly 48 scenario-hours before the storm reaches Vietnam's central coast, **VN/Vietnamese alerts begin** for Da Nang, Hue, and Quang Ngai. This is the cross-border headline — point at it.
6. As the system weakens over the South China Sea, Thai-language signals trickle in from the Gulf coast, and Vietnamese coastal observation signals corroborate the alerts already issued.

---

## Architecture

```
                            ┌──────────────────────────┐
   Telegram (BotFather) ◄──►│ python-telegram-bot v21  │
                            │  /start /subscribe …     │
                            └────────────┬─────────────┘
                                         │ same process
                            ┌────────────▼─────────────┐
                            │  FastAPI                 │
                            │  + asyncio scenario_clock│
                            │  + SQLAlchemy → SQLite   │
                            └────────────┬─────────────┘
                                         │ SSE /events/{slug}
                            ┌────────────▼─────────────┐
                            │  Next.js 14 dashboard    │
                            │  + MapLibre GL           │
                            └──────────────────────────┘

    Fixtures (in-repo): kammuri_track.json, kammuri_signals.json,
                        alert_templates.json, asean_admin.geojson
```

Why SSE instead of WebSocket: scenario events are one-way (server → client), tick-paced, and recoverable on reload. SSE is one HTTP connection, no framing, no client library.

Why one process: the demo runs a single asyncio loop with both the FastAPI app and the Telegram bot's `Application.start()` cooperating. In production you would split these.

---

## Roadmap to production

| Layer                    | Demo                                                              | Production                                                              |
| ------------------------ | ----------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Track ingest             | static `kammuri_track.json`                                       | JTWC / JMA / PAGASA REST + ECMWF ensemble                               |
| Trajectory model         | radius-and-bearing in `propagation.py`                            | XGBoost regressor on IBTrACS, hourly ensemble forecast tracks           |
| Rainfall propagation     | not modeled                                                       | IMERG-driven HYSPLIT / mGrid-LSTM hybrid                                |
| Citizen signal ingest    | `kammuri_signals.json`                                            | Twitter v2, Facebook CrowdTangle, Zalo, Line, regional NLP fine-tune    |
| Alert templating         | Jinja2 over `alert_templates.json`                                | Same, plus DRR-expert-reviewed pack per country, accessible plain-text  |
| Delivery                 | Telegram bot only                                                 | Telegram, Viber, Zalo, Line, SMS gateways, national CAP feeds, web push |
| Storage                  | SQLite                                                            | Postgres + PostGIS, S3 for archived events                              |
| Observability            | stdlib logging                                                    | OpenTelemetry, per-country delivery dashboards, audit trail             |

---

## Repository layout

```
seabeacon/
├── backend/                 # FastAPI + SQLite + python-telegram-bot
│   ├── seabeacon/
│   │   ├── main.py          # FastAPI app + lifespan
│   │   ├── models.py        # ORM
│   │   ├── routes/          # /scenarios /alerts /signals /subscriptions /events
│   │   ├── services/
│   │   │   ├── propagation.py        # DEMO STUB radius-and-bearing model
│   │   │   ├── alerting.py           # alert creation + dispatch
│   │   │   ├── localization.py       # Jinja2 over alert_templates.json
│   │   │   └── scenario_clock.py     # the demo heartbeat
│   │   ├── bot/             # /start /subscribe /language /country /status /stop
│   │   ├── fixtures/        # Kammuri track, signals, ASEAN admin, alert templates
│   │   └── seed.py          # idempotent loader
│   └── tests/               # propagation + localization + clock tests
└── frontend/                # Next.js 14 + Tailwind + MapLibre
    ├── app/dashboard/       # the live demo surface
    ├── components/
    │   ├── Map/AseanMap.tsx
    │   ├── AlertsPanel.tsx
    │   ├── SignalsFeed.tsx
    │   ├── Timeline/ScenarioTimeline.tsx
    │   └── ScenarioControls.tsx
    └── lib/{api,ws}.ts
```

---

## Running the tests

```bash
cd backend
pip install -e .[dev]
pytest tests/ -v
```

Three propagation tests, three localization tests, two clock tests.

---

## Data sources

- **Typhoon Kammuri / Tisoy track** — coordinates and intensity values are derived from publicly reported best-track summaries published by JTWC and JMA. This is a hackathon-grade approximation; the file (`fixtures/kammuri_track.json`) cites the source in its header. **Not for operational use.**
- **ASEAN administrative geography** — country roster and coastal municipality centroids derived from public sources (GADM, Natural Earth, OpenStreetMap). Cited in `fixtures/asean_admin.geojson`. Country borders are drawn by the MapLibre base style.
- **Alert templates (`fixtures/alert_templates.json`)** — Filipino, Vietnamese, and Thai translations are best-effort and require native-speaker DRR-expert review before any public deployment.

---

## Known issues

- The Telegram bot and the API share a single asyncio loop. If the bot's polling raises a startup error, the FastAPI app starts without the bot attached and alerts are not pushed (the dashboard still works). Production should split these.
- The demo scenario only covers PH / VN / TH. The other seven ASEAN states are seeded in the country table for schema completeness; their subscription buttons are greyed out in the bot.
- No authentication on the dashboard; the only identity is the Telegram chat ID a subscriber registers with.
