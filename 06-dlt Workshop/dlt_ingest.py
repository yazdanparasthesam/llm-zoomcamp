import os
import dlt
from dotenv import load_dotenv
from dlt.sources.logfire import logfire_source

load_dotenv()

def run_logfire_pipeline():
    read_token = os.environ.get("LOGFIRE_READ_TOKEN")
    if not read_token:
        raise ValueError("LOGFIRE_READ_TOKEN is missing in .env")

    # 1. Initialize dlt pipeline targeting local DuckDB
    pipeline = dlt.pipeline(
        pipeline_name="logfire_traces_pipeline",
        destination="duckdb",
        dataset_name="agent_traces",
    )

    # 2. Extract traces via the logfire source
    source = logfire_source(read_token=read_token)

    # 3. Load data into DuckDB
    load_info = pipeline.run(source)
    print("Pipeline Execution Summary:")
    print(load_info)

if __name__ == "__main__":
    run_logfire_pipeline()
