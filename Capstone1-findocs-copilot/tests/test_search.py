import pytest
from src.search import FinancialSearchEngine, rewrite_query

def test_query_rewriting():
    """
    Tests Best Practice 3: User query rewriting and expansion.
    """
    q1 = "What is NVDA CapEx in 2024?"
    rewritten = rewrite_query(q1)
    assert "NVIDIA" in rewritten
    assert "capital expenditures" in rewritten

def test_hybrid_rerank_search():
    """
    Tests Best Practices 1 & 2: Hybrid RRF search and document re-ranking.
    """
    engine = FinancialSearchEngine()
    results = engine.search("What are NVIDIA export controls?", top_k=3, mode="hybrid_rerank")
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "NVDA" in top_chunk["ticker"] or "NVIDIA" in top_chunk["company"]
