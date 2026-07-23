import logfire
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Configure and instrument Logfire with Pydantic AI
logfire.configure()
logfire.instrument_pydantic_ai()

from agent import SearchDeps, faq_agent
from ingest import build_index, load_faq_data


def main():
    # Build search index
    documents = load_faq_data()
    index = build_index(documents)

    deps = SearchDeps(index=index)

    # Ask the homework target question
    question = "How do I run Ollama locally?"
    result = faq_agent.run_sync(question, deps=deps)

    print(result.output)


if __name__ == "__main__":
    main()
