# TripPilot Data Layer

TripPilot ships a **committed, reproducible snapshot** so peer reviewers
need **zero accounts and zero API keys**.

## Files

| File | Generated? | Description |
|---|---|---|
| `generate_snapshot.py` | – | Deterministic generator (seed 42) of the hotel & review snapshot |
| `hotels_snapshot.json` | ✅ | 24 hotels across 19 European cities (name, address, lat/lng, avg score) |
| `reviews_snapshot.json` | ✅ | 340 guest reviews (Kaggle 515K-Hotel-Reviews schema: positive/negative text, score, tags) |
| `kaggle_hotel_reviews_extract.csv` | ✅ | Same data in the exact Kaggle CSV column layout (`Hotel_Address`, `Tags`, `Reviewer_Score` ...) demonstrating source compatibility |
| `generate_ground_truth.py` | – | Deterministic generator (seed 123) of evaluation pairs |
| `ground_truth_qa.json` | ✅ | 51 question → `review_id` pairs used by retrieval & RAG evaluation |
| `openflights_extract.csv` | ❌ static | Hand-curated extract in the OpenFlights `airports.dat` layout showing that the tool layer can join real airport data |
| `routes_extract.csv` | ❌ static | Route rows (origin, dest, airline, stops, km, avg_price_eur) — an OpenFlights *routes* join with a public fare table |
| `city_costs.json` | ❌ static | Daily budget table per city (budget/midrange/luxury EUR/day, meals, transit, safety, best months, vibe tags) |
| `transcripts.txt` | ❌ static | Transcripts of the multimodal destination audio briefings |
| `audio/listen_notes.txt` | ❌ static | Expected audio briefing files & how to regenerate them |
| `index_cache.json` | ✅ (after `make ingest`) | Pre-computed chunk vectors + index (git-ignored by default) |

## Data provenance & method

- **Schema** is cloned from the public Kaggle dataset
  *“515K Hotel Reviews Data in Europe”* (columns `Hotel_Address`, `Review_Date`,
  `Average_Score`, `Negative_Review`, `Positive_Review`,
  `Review_Total_Negative_Word_Counts`, `Reviewer_Score`, `Tags` …).
  Because the real 350 MB dataset requires a Kaggle login — which would break
  the 2/2 reproducibility criterion — TripPilot generates a **350-row,
  schema-compatible snapshot** with a seeded RNG. The same dlt pipeline and
  chunking code runs unchanged on the real CSV (see `ingestion/README.md`).
- **OpenFlights** airports/routes layouts are mirrored in
  `openflights_extract.csv` / `routes_extract.csv`; the tool layer joins
  `city -> IATA -> route -> price`. With an `AMADEUS_API_KEY` the
  `search_flights` tool upgrades to **live Amadeus test-tier offers**.
- **Review short URLs**: reviewers with a Kaggle account can swap in the real
  dataset: download `Hotel_Reviews.csv`, drop it into `data/`, set
  `TRIPILOT_REAL_KAGGLE_CSV=data/Hotel_Reviews.csv`, then `make dlt-ingest && make ingest`.

## Regenerating

```bash
python3 data/generate_snapshot.py      # hotels + reviews (+ Kaggle CSV)
python3 data/generate_ground_truth.py  # 51 Q&A pairs
python3 data/generate_audio.py         # multimodal audio briefings (gTTS)
python3 ingestion/hotel_reviews_pipeline.py   # dlt extract -> DuckDB + normalized JSON
```

The committed JSON/CSV files are the canonical snapshot — regenerating with
the same seeds produces byte-identical content.
