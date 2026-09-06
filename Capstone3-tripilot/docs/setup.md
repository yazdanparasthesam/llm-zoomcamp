# Setup Guide

TripPilot runs in four modes. **Peer reviewers need Option A or D only.**

## Option A — Docker Compose (recommended)

```bash
git clone https://github.com/yazdanparasthesam/llm-zoomcamp.git  # clone the existing course repository
cd llm-zoomcamp/Capstone3-tripilot          # enter the published project folder
cp .env.example .env          # optional: add GROQ_API_KEY
docker compose up --build -d

# URLs
#  Streamlit copilot : http://localhost:8501
#  Grafana (admin/admin): http://localhost:3000
#  Elasticsearch     : http://localhost:9200
#  Postgres          : localhost:5432 (tripilot_db/postgres/postgres)
```

The app container auto-initializes the Postgres telemetry schema on boot;
the Grafana dashboard (6 panels) is auto-provisioned from
`grafana/dashboards/tripilot_dashboard.json`.

## Option B — Kubernetes (local Kind)

See `k8s/README-k8s.md` for the full walkthrough (build → kind load →
`kubectl apply -f k8s/` → port-forward).

## Option C — Cloud deployment (deferred)

Step 11 is deferred for this submission; no public cloud URL or cloud-deployment bonus is claimed. Keep using the verified local Compose/Kind workflows. Optional future configurations are in `fly.toml`, [the Fly guide](deploy-fly.md), `terraform/README.md`, and `render.yaml`. Review provider costs before running any cloud provisioning commands.

## Publish this project to GitHub

Follow [the publication guide](publish-github.md) to import the current source into `Capstone3-tripilot` in `yazdanparasthesam/llm-zoomcamp`, keep the root CI workflow in the correct place, preserve earlier coursework, and verify the final merged `main` hash.

## Option D — Local standalone (zero Docker)

```bash
pip install -r requirements.txt
make dlt-ingest     # dlt -> DuckDB + normalized JSON (uses committed snapshot)
make ingest         # Module-07 chunking + embeddings
make eval           # retrieval (4 approaches) + RAG judge (3 prompts)
make test           # 13 pytest tests
make run            # streamlit on :8501
```

No keys needed: the app detects the missing `GROQ_API_KEY` and runs the
deterministic grounded **mock mode**; telemetry falls back to SQLite.

## Environment variables

See `.env.example`. Only optional keys (Groq / Amadeus / OpenAI) and infra
overrides. Defaults are fully self-contained.

## Common issues

| Symptom | Fix |
|---|---|
| `port 8501 already in use` | `docker compose down` or `pkill -f streamlit` |
| ES container OOM | it is capped `-Xms256m -Xmx256m`; app works without ES anyway (local index) |
| Grafana shows "no data" | ask a few questions in the UI first, panels refresh every 10s |
| `ModuleNotFoundError: openai` in offline runs | not required for mock mode — code guards the import; install requirements to silence |
| `ModuleNotFoundError: pkg_resources` (from `import dlt` in clean venvs) | `dlt 1.3.0` needs `pkg_resources`, **removed in setuptools 81+**; the lock pins `setuptools==80.9.0` — reinstall with `uv pip install -r requirements.txt`. The pipeline masks this import error as "dlt/duckdb not installed" and falls back to JSON-only mode by design |
| `make dlt-ingest` says "normalized extract exists" | reproducibility guard; force a real dlt run with `TRIPILOT_FORCE_REFRESH=true make dlt-ingest` (env flag must prefix the SAME command line — `make` does not carry env across lines) |
