from src.rag import ComplaintRadarRAG
from src.tools import theme_breakdown


def test_rag_pipeline_execution():
    rag = ComplaintRadarRAG()
    res = rag.answer_question(
        "What are customers saying about credit reporting errors?",
        search_mode="hybrid_rerank",
        prompt_style="ops",
        log_db=False,
        use_agent=False,
    )
    assert res["answer"]
    assert res["relevance_label"] in {"RELEVANT", "PARTIALLY_RELEVANT", "NON_RELEVANT"}
    assert res["latency_ms"] >= 0
    assert isinstance(res["chunks"], list)


def test_agent_theme_tool():
    rag = ComplaintRadarRAG()
    payload = theme_breakdown(rag.search_engine, company_key="WELLS_FARGO")
    assert payload["n_complaints"] >= 1
    assert payload["top_issues"]
