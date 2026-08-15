# Data

- `cfpb_complaints.json` — curated snapshot of public CFPB consumer complaint **narratives**.
  Source: https://www.consumerfinance.gov/data-research/consumer-complaints/
  U.S. government public data. Narratives appear only when the consumer consented.
  PII in the official feed is already masked by CFPB (`[REDACTED]`).
- `ground_truth_qa.json` — 100 evaluation questions with `ground_truth_doc_id` / `ground_truth_chunk_id`.
- `index_cache.json` — created by `make ingest` (chunk embeddings). Safe to regenerate.
- `audio/` — multimodal spoken briefings (`*.mp3`) plus `transcripts.txt`. Regenerate with `python3 data/generate_audio.py`.

Refresh from the live API with the dlt pipeline:

```bash
CFPB_FORCE_REFRESH=true make dlt-ingest
make ingest
```
