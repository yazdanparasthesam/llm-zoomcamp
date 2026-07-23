import duckdb

conn = duckdb.connect(".dlt/data/dev/logfire_traces_pipeline.duckdb")

# Group spans by trace_id to see how many spans each single agent run produced
query = """
SELECT 
    trace_id, 
    COUNT(*) AS span_count
FROM agent_traces.records
GROUP BY trace_id;
"""

print(conn.execute(query).df())
