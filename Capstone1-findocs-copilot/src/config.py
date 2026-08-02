import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "evaluation_results"

DATASET_PATH = DATA_DIR / "sec_10k_earnings_dataset.json"
GROUND_TRUTH_PATH = DATA_DIR / "ground_truth_qa.json"
INDEX_CACHE_PATH = DATA_DIR / "index_cache.json"
SQLITE_DB_PATH = DATA_DIR / "findocs_monitoring.db"

# Elastic / Docker configuration
USE_DOCKER = os.getenv("USE_DOCKER", "false").lower() == "true"
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX = "findocs_sec_index"

# Database configuration (PostgreSQL in Docker, SQLite locally)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "findocs_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Groq LLM configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEFAULT_MODEL = "llama-3.3-70b-versatile"
FAST_MODEL = "llama-3.1-8b-instant"
