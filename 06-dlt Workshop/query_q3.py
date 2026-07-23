import duckdb

conn = duckdb.connect(".dlt/data/dev/logfire_traces_pipeline.duckdb")

# Query total input tokens per trace using the exact column name created by dlt
query = """
SELECT 
    trace_id,
    SUM(TRY_CAST(attributes__gen_ai_usage_input_tokens AS INT)) AS total_input_tokens
FROM agent_traces.records
WHERE attributes__gen_ai_usage_input_tokens IS NOT NULL
GROUP BY trace_id;
"""

df = conn.execute(query).df()
print("=== Input Tokens per Trace ===")
print(df)
