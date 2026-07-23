import os
import dlt
import logfire.db_api
from dotenv import load_dotenv

load_dotenv()

read_token = os.getenv("LOGFIRE_READ_TOKEN")
if not read_token:
    raise ValueError("LOGFIRE_READ_TOKEN is missing in .env")


@dlt.resource(name="records", write_disposition="replace")
def get_logfire_records():
    # Connect directly via Logfire DB API
    conn = logfire.db_api.connect(read_token=read_token)
    cursor = conn.cursor()

    # Query all records from Logfire
    cursor.execute("SELECT * FROM records")

    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    records = [dict(zip(columns, row)) for row in rows]
    yield records


def run():
    # Create dlt pipeline targeting DuckDB dataset 'agent_traces'
    pipeline = dlt.pipeline(
        pipeline_name="logfire_traces_pipeline",
        destination="duckdb",
        dataset_name="agent_traces",
    )

    load_info = pipeline.run(get_logfire_records())
    print(load_info)


if __name__ == "__main__":
    run()
