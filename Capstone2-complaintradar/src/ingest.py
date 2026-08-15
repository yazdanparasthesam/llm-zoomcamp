import json
import re

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import (
    DATASET_PATH,
    ELASTICSEARCH_INDEX,
    ELASTICSEARCH_URL,
    INDEX_CACHE_PATH,
)


def chunk_document(doc, target_words=90):
    """
    Module 07 hierarchical chunking:
    parent complaint = doc_id (CFPB-{complaint_id})
    child passages   = chunk_id (CFPB-{complaint_id}_1, _2, ...)
    """
    text = doc["text"]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        sentences = [text]

    chunks = []
    buf, word_count, idx = [], 0, 1
    for sentence in sentences:
        buf.append(sentence)
        word_count += len(sentence.split())
        if word_count >= target_words or sentence is sentences[-1]:
            chunk_text = " ".join(buf).strip()
            if chunk_text:
                chunks.append(_make_chunk(doc, idx, chunk_text))
                idx += 1
            buf, word_count = [], 0

    if buf:
        chunks.append(_make_chunk(doc, idx, " ".join(buf).strip()))
    return chunks


def _make_chunk(doc, idx, chunk_text):
    return {
        "doc_id": doc["doc_id"],
        "chunk_id": f"{doc['doc_id']}_{idx}",
        "complaint_id": doc.get("complaint_id", ""),
        "company_key": doc.get("company_key", ""),
        "company": doc.get("company", ""),
        "product": doc.get("product", ""),
        "issue": doc.get("issue", ""),
        "sub_issue": doc.get("sub_issue", ""),
        "state": doc.get("state", ""),
        "date_received": doc.get("date_received", ""),
        "company_response": doc.get("company_response", ""),
        "doc_type": doc.get("doc_type", "cfpb_complaint_narrative"),
        "title": doc.get("title", ""),
        "text": chunk_text,
    }


def generate_embeddings(chunks):
    """Local, reproducible 64-d LSA embeddings (no GPU / no API)."""
    texts = [f"{c['title']}: {c['text']}" for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=4000, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(texts)
    n_components = min(64, max(2, len(chunks) - 1))
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    dense = svd.fit_transform(tfidf_matrix)
    norms = np.linalg.norm(dense, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized = (dense / norms).tolist()
    for idx, chunk in enumerate(chunks):
        chunk["embedding"] = normalized[idx]
    return chunks, vectorizer, svd


def index_to_elasticsearch(chunks):
    try:
        import requests

        headers = {"Content-Type": "application/json"}
        resp = requests.get(ELASTICSEARCH_URL, timeout=2)
        if resp.status_code != 200:
            return False
        requests.delete(f"{ELASTICSEARCH_URL}/{ELASTICSEARCH_INDEX}", timeout=2)
        mapping = {
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "chunk_id": {"type": "keyword"},
                    "complaint_id": {"type": "keyword"},
                    "company_key": {"type": "keyword"},
                    "company": {"type": "text"},
                    "product": {"type": "keyword"},
                    "issue": {"type": "text"},
                    "title": {"type": "text"},
                    "text": {"type": "text"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": len(chunks[0]["embedding"]),
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            }
        }
        requests.put(
            f"{ELASTICSEARCH_URL}/{ELASTICSEARCH_INDEX}",
            json=mapping,
            headers=headers,
            timeout=2,
        )
        bulk_data = []
        slim = [{k: v for k, v in c.items() if k != "embedding" or True} for c in chunks]
        for chunk in slim:
            bulk_data.append(json.dumps({"index": {"_index": ELASTICSEARCH_INDEX, "_id": chunk["chunk_id"]}}))
            bulk_data.append(json.dumps(chunk))
        payload = "\n".join(bulk_data) + "\n"
        requests.post(f"{ELASTICSEARCH_URL}/_bulk", data=payload, headers=headers, timeout=15)
        print(f"Indexed {len(chunks)} chunks into Elasticsearch '{ELASTICSEARCH_INDEX}'.")
        return True
    except Exception as exc:
        print(f"Elasticsearch indexing skipped (not connected): {exc}")
        return False


def run_ingest():
    print(f"Loading CFPB snapshot from {DATASET_PATH}...")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)

    print("Chunking narratives (Module 07 doc_id + chunk_id)...")
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    print(f"Created {len(all_chunks)} chunks from {len(docs)} parent complaints.")

    print("Generating dense LSA embeddings...")
    chunks_with_embeds, _, _ = generate_embeddings(all_chunks)

    INDEX_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks_with_embeds, f)
    print(f"Saved local index cache to {INDEX_CACHE_PATH}")

    index_to_elasticsearch(chunks_with_embeds)
    print("Ingestion complete.")
    return chunks_with_embeds


if __name__ == "__main__":
    run_ingest()
