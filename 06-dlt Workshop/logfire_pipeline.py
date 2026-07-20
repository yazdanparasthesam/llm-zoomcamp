# logfire_pipeline.py
import dlt
import os
from dotenv import load_dotenv
from dlt.sources.helpers import requests

load_dotenv()

# Replace with the full URL you found
PROJECT_ID = "123456"  # <-- change to your numeric project ID
BASE_URL = f"https://logfire-us.pydantic.dev/api/v1/projects/{PROJECT_ID}"
HEADERS = {"Authorization": f"Bearer {os.getenv('LOGFIRE_READ_TOKEN')}"}

@dlt.resource
def logfire_traces(limit=1000):
    url = f"{BASE_URL}/traces"
    params = {"limit": limit}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    # The response might have a 'data' key or be the list directly
    traces = data.get("data", data)
    for trace in traces:
        yield trace

def load_logfire_traces():
    pipeline = dlt.pipeline(
        pipeline_name="agent_traces",
        destination="duckdb",
        dataset_name="agent_traces",
        dev_mode=True,
    )
    load_info = pipeline.run(logfire_traces, write_disposition="replace")
    print(load_info)

if __name__ == "__main__":
    load_logfire_traces()
