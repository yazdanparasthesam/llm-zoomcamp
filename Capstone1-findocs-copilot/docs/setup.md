# 🛠️ FinDocs Copilot — Setup & Configuration Guide

This document provides detailed setup instructions for running **FinDocs Copilot** in different environments.

---

## 1. Prerequisites

- **Python 3.10+** (if running locally without Docker)
- **Docker & Docker Compose** (if running full containerized stack)
- **Git**

---

## 2. Environment Variables (`.env`)

Copy the example environment file:
```bash
cp .env.example .env
```

### Configuration Overview
| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | `""` | Optional Groq API key for Llama-3-70B inference. If empty, runs in mock mode. |
| `USE_DOCKER` | `true` | Set to `true` when running in Docker Compose to use Postgres and Elasticsearch. |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elasticsearch endpoint. |
| `POSTGRES_HOST` | `localhost` | Hostname for PostgreSQL logging database. |
| `POSTGRES_PORT` | `5432` | Port for PostgreSQL. |
| `POSTGRES_DB` | `findocs_db` | Name of logging database. |
| `POSTGRES_USER` | `postgres` | Database user. |
| `POSTGRES_PASSWORD` | `postgres` | Database password. |

---

## 3. Running with Docker Compose (Recommended)

1. Build and start the complete stack:
   ```bash
   docker compose up --build -d
   ```
2. Verify services are running:
   ```bash
   docker compose ps
   ```
3. Open services in your browser:
   - **Streamlit App**: `http://localhost:8501`
   - **Grafana Dashboard**: `http://localhost:3000` (`admin` / `admin`)
   - **Elasticsearch API**: `http://localhost:9200`

To stop containers:
```bash
docker compose down -v
```

---

## 4. Running Locally in a Python Virtual Environment

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the automated ingestion script:
   ```bash
   python -m src.ingest
   ```
4. Run evaluation scripts to verify retrieval and RAG accuracy:
   ```bash
   python -m src.eval_retrieval
   python -m src.eval_rag
   ```
5. Launch the Streamlit application:
   ```bash
   streamlit run app.py --server.port=8501
   ```
