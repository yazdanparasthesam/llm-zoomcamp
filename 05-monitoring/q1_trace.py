# q1_trace.py
import sys
from dotenv import load_dotenv
from openai import OpenAI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# Setup OTel (must be before importing starter)
load_dotenv()
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("llm-zoomcamp")

# Now import starter and the base classes
from starter import rag as base_rag  # original RAGBase instance
from rag_helper import RAGBase
from gitsource import GithubRepositoryDataReader
from minsearch import Index

# We'll recreate the index and RAG to ensure we can override
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

class RAGTraced(RAGBase):
    def rag(self, query):
        with tracer.start_as_current_span("rag") as span:
            return super().rag(query)

    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search") as span:
            return super().search(query, num_results)

    def llm(self, prompt):
        with tracer.start_as_current_span("llm") as span:
            return super().llm(prompt)

traced_rag = RAGTraced(index=index, llm_client=client)

if __name__ == "__main__":
    query = "How does the agentic loop keep calling the model until it stops?"
    answer = traced_rag.rag(query)
    print("Answer:", answer[:200])
