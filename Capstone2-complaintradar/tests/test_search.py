from src.search import rewrite_query, rerank_documents
from src.rag import ComplaintRadarRAG


def test_query_rewriting():
    out = rewrite_query("WF overdraft and Apple Card BNPL late fee")
    assert "Wells Fargo" in out
    assert "Goldman Sachs" in out
    assert "buy now pay later" in out.lower() or "BNPL" in out


def test_hybrid_rerank_search():
    rag = ComplaintRadarRAG()
    results = rag.search_engine.search(
        "What are Wells Fargo customers saying about overdraft fees?",
        top_k=5,
        mode="hybrid_rerank",
    )
    assert len(results) > 0
    assert "chunk_id" in results[0][0]
    companies = {c.get("company_key") for c, _ in results}
    assert "WELLS_FARGO" in companies or any("wells" in (c.get("company") or "").lower() for c, _ in results)


def test_rerank_boosts_quoted_phrase():
    chunk_hit = {
        "chunk_id": "a_1",
        "company": "Equifax",
        "company_key": "EQUIFAX",
        "product": "Credit reporting",
        "issue": "Incorrect information on your report",
        "complaint_id": "1",
        "title": "Equifax identity theft",
        "text": "account was opened without my knowledge and I filed a police report",
    }
    chunk_miss = {
        "chunk_id": "b_1",
        "company": "Navient",
        "company_key": "NAVIENT",
        "product": "Student loan",
        "issue": "Dealing with my lender or servicer",
        "complaint_id": "2",
        "title": "Navient payment",
        "text": "I asked for a payment plan on my student loan",
    }
    ranked = rerank_documents(
        'Equifax complaint that mentions "opened without my knowledge"',
        [(chunk_miss, 0.5), (chunk_hit, 0.5)],
        top_k=2,
    )
    assert ranked[0][0]["chunk_id"] == "a_1"
