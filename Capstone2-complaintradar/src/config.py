import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "evaluation_results"
INGESTION_DIR = BASE_DIR / "ingestion"

DATASET_PATH = DATA_DIR / "cfpb_complaints.json"
GROUND_TRUTH_PATH = DATA_DIR / "ground_truth_qa.json"
INDEX_CACHE_PATH = DATA_DIR / "index_cache.json"
SQLITE_DB_PATH = DATA_DIR / "complaintradar_monitoring.db"
SELECTED_RETRIEVER_PATH = RESULTS_DIR / "selected_retriever.json"

USE_DOCKER = os.getenv("USE_DOCKER", "false").lower() == "true"
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX = "complaintradar_cfpb_index"

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "complaintradar_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEFAULT_MODEL = "llama-3.3-70b-versatile"
FAST_MODEL = "llama-3.1-8b-instant"

# Fallback default. After `make eval`, this is overridden by the winning row
# in evaluation_results/selected_retriever.json so the app uses the best method.
FALLBACK_SEARCH_MODE = "hybrid_rerank"

COMPANY_KEYS = [
    "EQUIFAX",
    "EXPERIAN",
    "TRANSUNION",
    "CAPITAL_ONE",
    "WELLS_FARGO",
    "SYNCHRONY",
    "BANK_OF_AMERICA",
    "NAVY_FEDERAL",
    "NAVIENT",
    "GOLDMAN_SACHS",
    "JPMORGAN_CHASE",
    "CITIBANK",
    "EARLY_WARNING",
    "DISCOVER",
    "AFFIRM",
]

COMPANY_DISPLAY = {
    "EQUIFAX": "Equifax",
    "EXPERIAN": "Experian",
    "TRANSUNION": "TransUnion",
    "CAPITAL_ONE": "Capital One",
    "WELLS_FARGO": "Wells Fargo",
    "SYNCHRONY": "Synchrony",
    "BANK_OF_AMERICA": "Bank of America",
    "NAVY_FEDERAL": "Navy Federal",
    "NAVIENT": "Navient",
    "GOLDMAN_SACHS": "Goldman Sachs / Apple Card",
    "JPMORGAN_CHASE": "JPMorgan Chase",
    "CITIBANK": "Citibank",
    "EARLY_WARNING": "Early Warning / Zelle",
    "DISCOVER": "Discover",
    "AFFIRM": "Affirm",
}

PRODUCTS = [
    "Credit reporting",
    "Credit card",
    "Checking or savings",
    "Mortgage",
    "Debt collection",
    "Student loan",
    "Auto loan",
    "Money transfer",
    "Payday / personal loan",
]


def get_default_search_mode():
    """Use the empirically best retriever when evaluation results exist."""
    if SELECTED_RETRIEVER_PATH.exists():
        try:
            data = json.loads(SELECTED_RETRIEVER_PATH.read_text())
            mode = data.get("selected_mode")
            if mode in {"text", "vector", "hybrid", "hybrid_rerank"}:
                return mode
        except Exception:
            pass
    return FALLBACK_SEARCH_MODE
