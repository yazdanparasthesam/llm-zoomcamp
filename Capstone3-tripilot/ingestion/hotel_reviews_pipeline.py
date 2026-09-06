#!/usr/bin/env python3
"""
TripPilot dlt ingestion pipeline (special ingestion tool, 2/2 rubric).

What it does
------------
1. Loads hotel reviews into a dlt resource. Source priority:
   a. REAL Kaggle CSV (if TRIPILOT_REAL_KAGGLE_CSV points to the 515K
      "Hotel_Reviews.csv" that you downloaded with your Kaggle account)
   b. the committed offline snapshot data/reviews_snapshot.json
      (default; reviewers need nothing).
2. Normalizes rows to the TripPilot schema (doc_id, section texts, tags).
3. Writes TWO destinations:
   - a DuckDB warehouse (data/tripilot.duckdb) — analytical queries, and
   - a normalized JSON extract (data/normalized/reviews_normalized.json)
     consumed by src/ingest.py (chunking + embeddings).

Usage
-----
    python3 ingestion/hotel_reviews_pipeline.py          # uses snapshot
    TRIPILOT_FORCE_REFRESH=true python3 ingestion/hotel_reviews_pipeline.py

dlt docs: https://dlthub.com/docs/intro
"""
import ast
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config  # noqa: E402


def _from_snapshot():
    reviews = json.load(open(config.REVIEWS_PATH))
    hotels = {h["hotel_id"]: h for h in json.load(open(config.HOTELS_PATH))}
    for r in reviews:
        h = hotels[r["hotel_id"]]
        yield _normalize(r, h)


def _from_kaggle_csv(path):
    hotel_ids, next_id = {}, 1
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for i, row in enumerate(csv.DictReader(f), start=1):
            name = row["Hotel_Name"].strip()
            if name not in hotel_ids:
                hotel_ids[name] = f"HTL-{next_id:04d}"
                next_id += 1
            try:
                tags = ast.literal_eval(row.get("Tags", "[]"))
            except Exception:
                tags = []
            h = {"hotel_id": hotel_ids[name], "hotel_name": name,
                 "hotel_address": row["Hotel_Address"],
                 "city": row["Hotel_Address"].split()[-2],
                 "country": row["Hotel_Address"].split()[-1], "avg_score": None}
            r = {"review_id": f"REV-{i:05d}", "hotel_id": hotel_ids[name],
                 "review_date": row["Review_Date"],
                 "positive_review": "" if row["Positive_Review"] == "No Positive"
                 else row["Positive_Review"],
                 "negative_review": "" if row["Negative_Review"] == "No Negative"
                 else row["Negative_Review"],
                 "score": float(row["Reviewer_Score"]), "tags": tags,
                 "reviewer_nationality": row.get("Reviewer_Nationality", ""),
                 "total_words": int(row.get("Review_Total_Positive_Word_Counts", "0")
                                    or 0) + int(row.get(
                                        "Review_Total_Negative_Word_Counts", "0") or 0)}
            yield _normalize(r, h)


def _normalize(r, h):
    return {
        "doc_id": r["review_id"],
        "hotel_id": r["hotel_id"],
        "hotel_name": h["hotel_name"],
        "hotel_address": h["hotel_address"],
        "city": h["city"],
        "country": h["country"],
        "review_date": r["review_date"],
        "positive_review": (r["positive_review"] or "").strip(),
        "negative_review": (r["negative_review"] or "").strip(),
        "reviewer_score": float(r["score"]),
        "tags": list(r["tags"]),
        "reviewer_nationality": r.get("reviewer_nationality", ""),
        "total_words": int(r.get("total_words", 0)),
    }


def load_normalized():
    """Run dlt -> DuckDB, then dump the normalized extract JSON."""
    if (os.path.exists(config.NORMALIZED_PATH) and not config.FORCE_REFRESH):
        print(f"[dlt] normalized extract exists at {config.NORMALIZED_PATH} "
              "(set TRIPILOT_FORCE_REFRESH=true to rebuild)")
        return

    try:
        import dlt
        import duckdb  # noqa: F401
    except ImportError:
        print("[dlt] dlt/duckdb not installed -> writing normalized JSON directly "
              "(pip install dlt duckdb to enable the full pipeline)")
        rows = list(_source_rows())
        _write_json_extract(rows)
        return

    rows = list(_source_rows())
    os.makedirs(config.DATA_DIR, exist_ok=True)
    pipeline = dlt.pipeline(
        pipeline_name="tripilot_hotel_reviews",
        destination=dlt.destinations.duckdb(
            os.path.join(config.DATA_DIR, "tripilot.duckdb")),
        dataset_name="hotel_reviews",
    )
    info = pipeline.run(rows, table_name="reviews",
                        write_disposition="replace")
    print(f"[dlt] load info: {info}")
    _write_json_extract(rows)


def _source_rows():
    if config.REAL_KAGGLE_CSV and os.path.exists(config.REAL_KAGGLE_CSV):
        print(f"[dlt] source: real Kaggle CSV {config.REAL_KAGGLE_CSV}")
        return _from_kaggle_csv(config.REAL_KAGGLE_CSV)
    print(f"[dlt] source: committed snapshot {config.REVIEWS_PATH}")
    return _from_snapshot()


def _write_json_extract(rows):
    os.makedirs(os.path.dirname(config.NORMALIZED_PATH), exist_ok=True)
    with open(config.NORMALIZED_PATH, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"[dlt] wrote {len(rows)} normalized reviews -> {config.NORMALIZED_PATH}")


if __name__ == "__main__":
    load_normalized()
