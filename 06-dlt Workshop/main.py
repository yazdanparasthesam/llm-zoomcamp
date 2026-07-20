# main.py 
from dotenv import load_dotenv
load_dotenv()

from agent import faq_agent, SearchDeps
from ingest import build_index, load_faq_data
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()

def main():
    documents = load_faq_data()
    index = build_index(documents)
    deps = SearchDeps(index=index)

    question = 'How do I run Ollama locally?'
    result = faq_agent.run_sync(question, deps=deps)
    print(result.output)

if __name__ == '__main__':
    main()
