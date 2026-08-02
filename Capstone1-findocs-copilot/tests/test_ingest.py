import pytest
from src.ingest import chunk_document, generate_embeddings

def test_module07_chunking():
    """
    Tests Module 07 hierarchical doc_id + chunk_id segmentation.
    """
    sample_doc = {
        "doc_id": "TEST-2024-DOC",
        "ticker": "TEST",
        "company": "Test Company",
        "doc_type": "10-K",
        "fiscal_year": "2024",
        "section": "Item 1A - Risk Factors",
        "title": "Test Title",
        "text": "First sentence of the document. Second sentence of the document. Third sentence with additional financial figures and risk disclosures for testing."
    }
    
    chunks = chunk_document(sample_doc)
    assert len(chunks) >= 1
    for i, c in enumerate(chunks):
        assert c["doc_id"] == "TEST-2024-DOC"
        assert c["chunk_id"] == f"TEST-2024-DOC_{i+1}"
        assert c["ticker"] == "TEST"
        assert "text" in c

def test_generate_embeddings():
    """
    Tests dense vector embedding generation without API keys.
    """
    sample_chunks = [
        {"title": "Title 1", "text": "Some text about AI revenue growth."},
        {"title": "Title 2", "text": "Another chunk about export controls and risk."}
    ]
    chunks, vec, svd = generate_embeddings(sample_chunks)
    assert "embedding" in chunks[0]
    assert len(chunks[0]["embedding"]) > 0
