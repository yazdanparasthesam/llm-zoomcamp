"""Module-07 ingestion & embedding tests."""
from src import ingest


def test_module07_hierarchical_chunking():
    reviews = ingest.load_reviews()
    assert len(reviews) == 354
    chunks = ingest.build_chunks(reviews)
    assert len(chunks) > len(reviews) * 1.1  # parents -> multiple children
    c = chunks[0]
    # every chunk inherits parent document identity + metadata
    assert c["chunk_id"].startswith(c["doc_id"] + "_")
    for field in ("hotel_name", "city", "reviewer_score", "section",
                  "tags", "review_date"):
        assert field in c
    assert c["section"] in ("positive", "negative", "neutral")


def test_chunk_word_budget():
    reviews = ingest.load_reviews()[:50]
    for r in reviews:
        for c in ingest.chunk_review(r):
            assert len(c["text"].split()) <= ingest.config.CHUNK_WORDS + 30


def test_generate_embeddings_dim_and_norm():
    import numpy as np
    reviews = ingest.load_reviews()[:40]
    chunks = ingest.build_chunks(reviews)
    V, vec, svd = ingest.embed_chunks(chunks)
    assert V.shape[0] == len(chunks)
    assert 2 <= V.shape[1] <= 64
    norms = np.linalg.norm(V, axis=1)
    assert abs(norms.mean() - 1.0) < 0.05  # L2-normalized rows
