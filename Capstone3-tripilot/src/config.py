"""
TripPilot central configuration.

Every setting is an environment variable with a sensible default so the
application runs with ZERO configuration (offline snapshot + mock LLM),
mirroring the evaluation-friendliness contract:

- No GROQ_API_KEY      -> deterministic mock planner + heuristic judge
- No Elasticsearch     -> local numpy BM25 / TF-IDF-SVD cosine search
- No PostgreSQL        -> SQLite telemetry at data/tripilot_monitoring.db
- No AMADEUS_API_KEY   -> flight tool answers from committed route snapshot
"""
import os

# ------------------------------------------------------------------ paths --
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

HOTELS_PATH = os.getenv("TRIPILOT_HOTELS", os.path.join(DATA_DIR, "hotels_snapshot.json"))
REVIEWS_PATH = os.getenv("TRIPILOT_REVIEWS", os.path.join(DATA_DIR, "reviews_snapshot.json"))
NORMALIZED_PATH = os.getenv("TRIPILOT_NORMALIZED",
                            os.path.join(DATA_DIR, "normalized", "reviews_normalized.json"))
GROUND_TRUTH_PATH = os.getenv("TRIPILOT_GROUND_TRUTH",
                              os.path.join(DATA_DIR, "ground_truth_qa.json"))
INDEX_CACHE_PATH = os.getenv("TRIPILOT_INDEX_CACHE",
                             os.path.join(DATA_DIR, "index_cache.json"))
ROUTES_PATH = os.getenv("TRIPILOT_ROUTES", os.path.join(DATA_DIR, "routes_extract.csv"))
AIRPORTS_PATH = os.getenv("TRIPILOT_AIRPORTS",
                          os.path.join(DATA_DIR, "openflights_extract.csv"))
CITY_COSTS_PATH = os.getenv("TRIPILOT_CITY_COSTS",
                            os.path.join(DATA_DIR, "city_costs.json"))
EVAL_DIR = os.path.join(BASE_DIR, "evaluation_results")

# dlt can optionally read the real Kaggle CSV (needs a Kaggle download)
REAL_KAGGLE_CSV = os.getenv("TRIPILOT_REAL_KAGGLE_CSV", "")
FORCE_REFRESH = os.getenv("TRIPILOT_FORCE_REFRESH", "false").lower() == "true"

# ------------------------------------------------------------------- LLM --
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")          # groq | openai
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_ANSWER = os.getenv("TRIPILOT_MODEL_ANSWER", "llama-3.3-70b-versatile")
MODEL_JUDGE = os.getenv("TRIPILOT_MODEL_JUDGE", "llama-3.1-8b-instant")
MODEL_VISION = os.getenv("TRIPILOT_MODEL_VISION",
                         "meta-llama/llama-4-scout-17b-16e-instruct")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("TRIPILOT_OPENAI_MODEL", "gpt-4o-mini")

# ------------------------------------------------------------- flights API --
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY", "")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET", "")
AMADEUS_BASE = os.getenv("AMADEUS_BASE", "https://test.api.amadeus.com")

# --------------------------------------------------------- search settings --
CHUNK_WORDS = int(os.getenv("TRIPILOT_CHUNK_WORDS", "90"))
EMBED_DIM = int(os.getenv("TRIPILOT_EMBED_DIM", "64"))
DEFAULT_SEARCH_MODE = os.getenv("TRIPILOT_SEARCH_MODE", "")  # '' -> eval winner
SEARCH_TOP_K = int(os.getenv("TRIPILOT_TOP_K", "5"))
RRF_K = int(os.getenv("TRIPILOT_RRF_K", "60"))

# ------------------------------------------------------------ Elasticsearch --
ES_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ES_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
ES_URL = f"http://{ES_HOST}:{ES_PORT}"
ES_INDEX = os.getenv("ELASTICSEARCH_INDEX", "tripilot_chunks")

# --------------------------------------------------------------- telemetry --
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "tripilot_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
SQLITE_PATH = os.getenv("TRIPILOT_SQLITE",
                        os.path.join(DATA_DIR, "tripilot_monitoring.db"))
QUERY_LOG_PATH = os.getenv("TRIPILOT_QUERY_LOG",
                           os.path.join(DATA_DIR, "query_log.jsonl"))

TZ = os.getenv("TZ", "Europe/Berlin")

# -------------------------------------------------------------- vision I/O --
# Offline fallback: user picks the vibe keywords shown in the photo.
VIBE_KEYWORDS = ["beach", "nightlife", "historic", "food", "mountains",
                 "romance", "museums", "budget", "luxury"]
