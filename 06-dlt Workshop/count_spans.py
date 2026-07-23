import duckdb

# Connect to the EXACT path reported by dlt
db_path = ".dlt/data/dev/logfire_traces_pipeline.duckdb"
conn = duckdb.connect(db_path)

print("=== 1. Total Tables Created in 'agent_traces' Schema ===")
table_count = conn.execute("""
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'agent_traces';
""").fetchone()[0]
print(f"Count: {table_count}\n")

print("=== 2. List of All Generated Tables ===")
tables = conn.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'agent_traces';
""").fetchall()

for t in tables:
    print(f" - {t[0]}")

print("\n=== 3. Total Spans/Records Ingested ===")
record_count = conn.execute("SELECT COUNT(*) FROM agent_traces.records;").fetchone()[0]
print(f"Total Rows in records: {record_count}")
