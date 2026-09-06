#!/usr/bin/env python3
"""
TripPilot ingestion — Module 07 hierarchical chunking + embeddings.

Pipeline:
  reviews (parent documents, doc_id = review_id)
    -> child chunks (chunk_id = doc_id_N, ~90 words, positive/negative
       sections kept separate so sentiment-aware retrieval works)
    -> TF-IDF (1-2 grams, 512 features) -> TruncatedSVD 64-d dense vectors
    -> data/index_cache.json  (+ optional Elasticsearch mirror index)

Run:  python3 -m src.ingest
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config  # noqa: E402

WORD_RE = re.compile(r"[A-Za-z0-9']+")


# ----------------------------------------------------------------- loading --
def load_reviews():
    """Prefer the dlt normalized extract; fall back to the raw snapshot."""
    if os.path.exists(config.NORMALIZED_PATH):
        rows = json.load(open(config.NORMALIZED_PATH))
        # dlt JSON extract may nest tags as string
        for r in rows:
            if isinstance(r.get("tags"), str):
                r["tags"] = [t.strip() for t in r["tags"].split(",") if t.strip()]
        return rows
    reviews = json.load(open(config.REVIEWS_PATH))
    hotels = {h["hotel_id"]: h for h in json.load(open(config.HOTELS_PATH))}
    out = []
    for r in reviews:
        h = hotels[r["hotel_id"]]
        out.append({
            "doc_id": r["review_id"], "hotel_id": r["hotel_id"],
            "hotel_name": h["hotel_name"], "hotel_address": h["hotel_address"],
            "city": h["city"], "country": h["country"],
            "review_date": r["review_date"],
            "positive_review": r["positive_review"],
            "negative_review": r["negative_review"],
            "reviewer_score": float(r["score"]), "tags": list(r["tags"]),
            "reviewer_nationality": r.get("reviewer_nationality", ""),
            "total_words": r.get("total_words", 0),
        })
    return out


def load_hotels():
    return json.load(open(config.HOTELS_PATH))


# ---------------------------------------------------------------- chunking --
def _split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def chunk_review(review, max_words=None):
    """Module 07 hierarchical chunking: doc -> ~max_words semantic chunks.

    Positive and negative sections are chunked independently and every
    chunk inherits the parent's metadata (hotel, city, tags, score).
    """
    max_words = max_words or config.CHUNK_WORDS
    chunks = []
    seq = 1
    for section in ("positive", "negative"):
        text = review.get(f"{section}_review", "") or ""
        if not text:
            continue
        buf, buf_words = [], 0
        for sent in _split_sentences(text):
            w = len(WORD_RE.findall(sent))
            if buf and buf_words + w > max_words:
                chunks.append(_mk_chunk(review, section, seq, " ".join(buf)))
                seq += 1
                buf, buf_words = [], 0
            buf.append(sent)
            buf_words += w
        if buf:
            chunks.append(_mk_chunk(review, section, seq, " ".join(buf)))
            seq += 1
    if not chunks:  # empty review edge case
        chunks.append(_mk_chunk(review, "neutral", 1, "No review text provided."))
    return chunks


def _mk_chunk(review, section, seq, text):
    return {
        "doc_id": review["doc_id"],
        "chunk_id": f"{review['doc_id']}_{seq}",
        "section": section,
        "text": text,
        "hotel_id": review["hotel_id"],
        "hotel_name": review["hotel_name"],
        "city": review["city"],
        "country": review["country"],
        "reviewer_score": review["reviewer_score"],
        "tags": review["tags"][:3],
        "review_date": review["review_date"],
    }


def build_chunks(reviews):
    chunks = []
    for r in reviews:
        chunks.extend(chunk_review(r))
    return chunks


# --------------------------------------------------------------- embeddings --
def embed_chunks(chunks, dim=None):
    """TF-IDF -> TruncatedSVD dense vectors (deterministic, seed 42)."""
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    dim = dim or config.EMBED_DIM
    texts = [
        f"{c['hotel_name']} {c['city']} {c['section']} "
        f"{' '.join(c['tags'])} {c['text']}" for c in chunks
    ]
    vec = TfidfVectorizer(max_features=512, ngram_range=(1, 2),
                          stop_words="english")
    X = vec.fit_transform(texts)
    n_comp = min(dim, max(2, X.shape[1] - 1), max(2, len(chunks) - 1))
    svd = TruncatedSVD(n_components=n_comp, random_state=42)
    V = svd.fit_transform(X)
    norms = np.linalg.norm(V, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    V = V / norms
    return V, vec, svd


def embed_query(text, vec, svd):
    import numpy as np
    q = vec.transform([text])
    v = svd.transform(q)
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return (v / n)[0]


# ------------------------------------------- elasticsearch (optional mirror) --
def index_to_elasticsearch(chunks):
    import urllib.request

    try:
        urllib.request.urlopen(config.ES_URL, timeout=1.5)
    except Exception:
        print(f"[ingest] Elasticsearch not reachable at {config.ES_URL} "
              "-> skipping ES mirror (local index only)")
        return False
    try:
        from elasticsearch import Elasticsearch
    except ImportError:
        print("[ingest] elasticsearch python client not installed -> skipping")
        return False
    es = Elasticsearch(config.ES_URL)
    es.indices.delete(index=config.ES_INDEX, ignore_unavailable=True)
    es.indices.create(index=config.ES_INDEX, ignore=400)
    ok = 0
    for c in chunks:
        es.index(index=config.ES_INDEX, id=c["chunk_id"],
                 document=c, refresh=False)
        ok += 1
    es.indices.refresh(index=config.ES_INDEX)
    print(f"[ingest] mirrored {ok} chunks to Elasticsearch index '{config.ES_INDEX}'")
    return True


# -------------------------------------------------------------------- main --
def run_ingest():
    reviews = load_reviews()
    chunks = build_chunks(reviews)
    V, vec, svd = embed_chunks(chunks)
    cache = {
        "meta": {
            "n_reviews": len(reviews), "n_chunks": len(chunks),
            "embed_dim": config.EMBED_DIM, "chunk_words": config.CHUNK_WORDS,
            "vocab_size": len(vec.vocabulary_),
        },
        "chunks": chunks,
        "vectors": [[round(float(x), 6) for x in row] for row in V],
    }
    with open(config.INDEX_CACHE_PATH, "w") as f:
        json.dump(cache, f)
    size_kb = os.path.getsize(config.INDEX_CACHE_PATH) // 1024
    print(f"[ingest] {len(reviews)} reviews -> {len(chunks)} chunks "
          f"(module-07 hierarchy), {config.EMBED_DIM}-d vectors "
          f"-> {config.INDEX_CACHE_PATH} ({size_kb} KB)")
    index_to_elasticsearch(chunks)
    return len(reviews), len(chunks)


if __name__ == "__main__":
    run_ingest()
