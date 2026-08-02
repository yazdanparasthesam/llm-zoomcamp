import pytest
from src.rag import FinDocsCopilotRAG

def test_rag_pipeline_execution():
    """
    Tests end-to-end RAG answer synthesis, citations, and LLM-as-a-Judge relevance scoring.
    """
    copilot = FinDocsCopilotRAG()
    res = copilot.answer_question(
        question="What was NVIDIA's total revenue in fiscal year 2024?",
        filter_ticker="NVDA",
        search_mode="hybrid_rerank",
        log_db=False
    )
    assert "answer" in res
    assert len(res["chunks"]) > 0
    assert res["relevance_label"] in ["RELEVANT", "PARTIALLY_RELEVANT", "NON_RELEVANT"]
    assert isinstance(res["relevance_score"], float)
