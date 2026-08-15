from src.ingest import chunk_document, generate_embeddings


def test_module07_chunking():
    doc = {
        "doc_id": "CFPB-1111111",
        "complaint_id": "1111111",
        "company_key": "WELLS_FARGO",
        "company": "Wells Fargo",
        "product": "Checking or savings",
        "issue": "Problem caused by your funds being low",
        "sub_issue": "Overdrafts and returned items",
        "state": "CA",
        "date_received": "2024-06-01",
        "company_response": "Closed with explanation",
        "title": "Wells Fargo — Checking or savings: overdraft",
        "text": (
            "I have been a Wells Fargo checking customer for years. The bank charged multiple overdraft fees "
            "in one day after a pending deposit was held. I called and was told the fees would not be reversed. "
            "This happened again the following week when my paycheck posted after midnight. I want the fees refunded "
            "and the account coding corrected. I also reported the issue through the CFPB portal."
        ),
        "doc_type": "cfpb_complaint_narrative",
    }
    chunks = chunk_document(doc, target_words=40)
    assert len(chunks) >= 2
    assert chunks[0]["doc_id"] == "CFPB-1111111"
    assert chunks[0]["chunk_id"] == "CFPB-1111111_1"
    assert chunks[1]["chunk_id"] == "CFPB-1111111_2"
    assert all(c["company_key"] == "WELLS_FARGO" for c in chunks)


def test_generate_embeddings():
    chunks = [
        {"title": "A", "text": "overdraft fee charged twice on one paycheck"},
        {"title": "B", "text": "identity theft mixed credit file wrong address"},
        {"title": "C", "text": "student loan forbearance interest capitalized"},
    ]
    out, _, _ = generate_embeddings(chunks)
    assert len(out[0]["embedding"]) >= 2
    assert abs(sum(x * x for x in out[0]["embedding"]) - 1.0) < 1e-5
