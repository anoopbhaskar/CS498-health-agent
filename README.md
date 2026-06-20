# FitAgent

FitAgent is a safety-aware health and fitness coaching app for meal planning, workout planning, multi-turn conversation memory, and progress tracking. The production runtime is a FastAPI backend with a lightweight browser UI and a local SQLite store.

## Current runtime setup

- **Production path:** FastAPI app in `src/api/app.py`, serving REST endpoints plus the static UI in `static/`.
- **Legacy path:** `main.py` is the original terminal CLI that uses the older Claude/tool-calling orchestrator.
- **Persistence:** SQLite via `src/memory/sqlite_store.py`.
- **Agent orchestration:** deterministic local routing and tools in `src/agent/` and `src/tools/`, designed to work without external API keys.
- **Benchmark artifacts:** `benchmark/` contains the original 20-task benchmark definitions/results plus `benchmark/local_eval.py`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run locally

```bash
PYTHONPATH=src uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000> for the web UI.

## Run tests

```bash
pytest
```

## REST endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/profiles` | Create/update a session profile with age, sex, height, weight, activity level, health conditions, dietary restrictions, and goals |
| `GET` | `/api/profiles/{session_id}` | Retrieve current profile |
| `POST` | `/api/chat` | Ask a free-text health or fitness question |
| `GET` | `/api/conversations/{session_id}` | Retrieve conversation history |
| `GET` | `/api/progress/{session_id}` | Retrieve progress snapshots, events, and summary |

## Safety and scope

FitAgent provides general wellness education. It refuses unsafe requests such as crash dieting, exercising through pain, or replacing professional medical diagnosis. For medical conditions, injuries, diabetes, hypertension, or other clinical concerns, responses include guidance to consult a qualified clinician, physical therapist, or registered dietitian.

## Project structure

```text
src/
  api/       FastAPI app and API schemas
  agent/     Production orchestration and request routing
  memory/    SQLite persistence
  tools/     Nutrition, workout, safety, profile, and progress tools
  core/      Legacy Claude CLI agent/orchestrator
static/      Browser UI
tests/       Unit and integration tests
benchmark/   Benchmark tasks, prior results, and local eval harness
```

## Notes for production scaling

- Move `DATABASE_URL` to a managed database and add migrations.
- Add authentication and per-user authorization before storing real public-user health data.
- Encrypt sensitive profile fields at rest and tighten log retention.
- Add hosted observability for request categories, latency, tool failures, and safety flags.
- Optionally add model-backed generation behind the same safety and deterministic tool layer.
