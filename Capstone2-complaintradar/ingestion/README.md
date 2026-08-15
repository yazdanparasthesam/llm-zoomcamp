# dlt ingestion (rubric: special tool = 2 points)

`cfpb_pipeline.py` is a [dlt](https://dlthub.com/) pipeline:

1. Declares a `@dlt.resource` that pages the public CFPB search API.
2. Runs `dlt.pipeline(..., destination="duckdb")`.
3. Normalizes company/product fields and writes `data/cfpb_complaints.json`.

Why dlt and not only `src/ingest.py`? In the 2026 project rubric a plain Python script is **1 point**. A special tool (dlt, Kestra, Airflow, Prefect) is **2 points**.

The committed snapshot means reviewers do **not** need network access to CFPB.
