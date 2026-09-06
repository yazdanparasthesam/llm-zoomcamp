# Ingestion — dlt pipeline (special tool: 2/2 rubric)

TripPilot uses **[dlt](https://dlthub.com/)** (data load tool) as the
automated ingestion framework:

```bash
make dlt-ingest        # = python3 ingestion/hotel_reviews_pipeline.py
make ingest            # = python3 -m src.ingest  (chunking + embeddings)
```

## Two-stage design

| Stage | Tool | Output |
|---|---|---|
| 1. Extract + normalize | `ingestion/hotel_reviews_pipeline.py` (dlt → DuckDB warehouse + JSON extract) | `data/tripilot.duckdb`, `data/normalized/reviews_normalized.json` |
| 2. Chunk + embed + index | `src/ingest.py` (Module 07 hierarchical chunking, TF-IDF→SVD 64-d vectors, optional Elasticsearch mirror) | `data/index_cache.json` |

`TRIPILOT_FORCE_REFRESH=false` (default) keeps the committed snapshot so
reviewers do not re-run stage 1.

## Using the REAL Kaggle dataset (optional)

The pipeline natively reads the real *515K Hotel Reviews* CSV:

```bash
# after downloading Hotel_Reviews.csv from Kaggle with your own account:
export TRIPILOT_REAL_KAGGLE_CSV=data/Hotel_Reviews.csv
TRIPILOT_FORCE_REFRESH=true make dlt-ingest
make ingest
```

Column mapping is handled inside `_from_kaggle_csv()` (`Hotel_Address` →
`hotel_address`, `Tags` → list, `Reviewer_Score` → float, ...).

## Live flight data (optional, separate from reviews)

The `search_flights` agent tool (`src/tools.py`) upgrades from the
committed `data/routes_extract.csv` snapshot to live **Amadeus test-tier**
offers when `AMADEUS_API_KEY` / `AMADEUS_API_SECRET` are present.
Data flow: `city -> IATA (OpenFlights extract) -> route offers (Amadeus or
snapshot) -> price-ranked options`. Reviewers need no key: the tool then
answers from the snapshot and labels results `source: snapshot`.
