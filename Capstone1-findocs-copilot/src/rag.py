import time
from src.search import FinancialSearchEngine
from src.llm import generate_rag_answer, evaluate_relevance
from src.db import log_conversation
from src.config import DEFAULT_MODEL

class FinDocsCopilotRAG:
    """
    End-to-end RAG Coordinator for FinDocs Copilot.
    Combines hybrid search + document re-ranking, query rewriting, LLM synthesis,
    LLM-as-a-Judge relevance scoring, and database logging.
    """
    def __init__(self):
        self.search_engine = FinancialSearchEngine()

    def answer_question(self, question, filter_ticker=None, search_mode="hybrid_rerank", 
                        prompt_style="analyst", top_k=3, log_db=True):
        start_time = time.time()
        
        # 1. Retrieve relevant SEC / Earnings Call chunks
        results = self.search_engine.search(
            query=question,
            top_k=top_k,
            mode=search_mode,
            filter_ticker=filter_ticker,
            rewrite=True
        )
        chunks = [r[0] for r in results]
        
        # 2. Generate cited RAG answer
        answer = generate_rag_answer(question, chunks, system_prompt_type=prompt_style)
        
        # 3. LLM-as-a-Judge Relevance Evaluation (Module 03/04 approach)
        relevance_label, relevance_score = evaluate_relevance(question, answer, chunks)
        
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        # 4. Log to PostgreSQL / SQLite database
        conv_id = None
        if log_db:
            conv_id = log_conversation(
                question=question,
                answer=answer,
                model=DEFAULT_MODEL,
                latency_ms=latency_ms,
                relevance_label=relevance_label,
                relevance_score=relevance_score,
                ticker=filter_ticker
            )
            
        return {
            "question": question,
            "answer": answer,
            "chunks": chunks,
            "relevance_label": relevance_label,
            "relevance_score": relevance_score,
            "latency_ms": latency_ms,
            "conversation_id": conv_id,
            "search_mode": search_mode,
            "prompt_style": prompt_style
        }

if __name__ == "__main__":
    copilot = FinDocsCopilotRAG()
    test_q = "What was NVIDIA's total revenue in fiscal year 2024 and how much did Data Center contribute?"
    print(f"Testing FinDocs Copilot RAG on: '{test_q}'")
    res = copilot.answer_question(test_q, filter_ticker="NVDA")
    print("\n--- Answer ---")
    print(res["answer"])
    print("\n--- Evaluation & Latency ---")
    print(f"Relevance: {res['relevance_label']} ({res['relevance_score']}) | Latency: {res['latency_ms']} ms | ConvID: {res['conversation_id']}")
