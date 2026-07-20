import os
import dlt
import logfire.db_api
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

read_token = os.getenv("LOGFIRE_READ_TOKEN")
if not read_token:
    raise ValueError("LOGFIRE_READ_TOKEN is missing from your .env file!")

# 2. Define a dlt resource using Logfire DB API
@dlt.resource(name="records", write_disposition="replace")
def get_logfire_records():
    # Connect to Logfire via DB-API
    conn = logfire.db_api.connect(read_token=read_token)
    cursor = conn.cursor()
    
    # Query all trace records from Logfire
    cursor.execute("SELECT * FROM records")
    
    # Fetch column names and row data
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # Convert list of rows into dictionary records for dlt
    records = [dict(zip(columns, row)) for row in rows]
    yield records

# 3. Define and run the dlt pipeline
def run():
    pipeline = dlt.pipeline(
        pipeline_name="logfire_traces_pipeline",
        destination="duckdb",
        dataset_name="agent_traces"
    )

    load_info = pipeline.run(get_logfire_records())
    print("dlt Load Execution Summary:")
    print(load_info)

if __name__ == "__main__":
    run()
