# Setup

## Local (no Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
make dlt-ingest    # optional live CFPB pull via dlt
make ingest        # Module 07 chunk + embed
make eval
make test
make run
```

Optional Groq key (otherwise mock LLM mode):

```bash
export GROQ_API_KEY=your_key
```

## Docker Compose

```bash
export GROQ_API_KEY=your_key   # optional
docker compose up --build -d
```

- App: http://localhost:8501
- Grafana: http://localhost:3000 (`admin` / `admin`)

## Kubernetes

See `k8s/README-k8s.md`.
