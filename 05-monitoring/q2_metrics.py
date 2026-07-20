# q2_metrics.py
import time
from dotenv import load_dotenv
from openai import OpenAI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

load_dotenv()
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("llm-zoomcamp")

from starter import rag as base_rag
from rag_helper import RAGBase
from gitsource import GithubRepositoryDataReader
from minsearch import Index

COMMIT = "8c1834d"
reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id=COMMIT,
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)
documents = [file.parse() for file in reader.read()]
index = Index(text_fields=["content"], keyword_fields=["filename"])
index.fit(documents)
client = OpenAI()

def calculate_cost(model, usage):
    # Pricing for gpt-5.4-mini (example, adjust if needed)
    if "gpt-5.4-mini" in model:
        return (usage.input_tokens * 0.15 + usage.output_tokens * 0.60) / 1_000_000
    return 0.0

class RAGTraced(RAGBase):
    def rag(self, query):
        with tracer.start_as_current_span("rag") as span:
            return super().rag(query)

    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search") as span:
            return super().search(query, num_results)

    def llm(self, prompt):
        with tracer.start_as_current_span("llm") as span:
            response = super().llm(prompt)  # this returns the full response
            # Extract usage
            usage = response.usage
            cost = calculate_cost(self.model, usage)
            # Set attributes
            span.set_attribute("input_tokens", usage.input_tokens)
            span.set_attribute("output_tokens", usage.output_tokens)
            span.set_attribute("cost", cost)
            # Also store in span (optional)
            return response

traced_rag = RAGTraced(index=index, llm_client=client)

if __name__ == "__main__":
    query = "How does the agentic loop keep calling the model until it stops?"
    answer = traced_rag.rag(query)
    print("Answer:", answer[:200])
