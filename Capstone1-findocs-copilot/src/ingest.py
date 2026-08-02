import json
import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from src.config import DATASET_PATH, INDEX_CACHE_PATH, ELASTICSEARCH_URL, ELASTICSEARCH_INDEX, USE_DOCKER

def chunk_document(doc):
    """
    Module 07 Chunking for Longer Texts:
    Splits each document into smaller semantic chunks and assigns a unique chunk_id
    (e.g. doc_id_1, doc_id_2) while preserving parent doc_id and metadata.
    """
    text = doc["text"]
    # Split text into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    chunks = []
    current_chunk_sentences = []
    current_word_count = 0
    chunk_idx = 1
    
    for sentence in sentences:
        words = sentence.split()
        current_chunk_sentences.append(sentence)
        current_word_count += len(words)
        
        # Target ~60-100 words per chunk or end of sentences
        if current_word_count >= 50 or sentence == sentences[-1]:
            chunk_text = " ".join(current_chunk_sentences)
            chunk_id = f"{doc['doc_id']}_{chunk_idx}"
            chunks.append({
                "doc_id": doc["doc_id"],
                "chunk_id": chunk_id,
                "ticker": doc["ticker"],
                "company": doc["company"],
                "doc_type": doc["doc_type"],
                "fiscal_year": doc["fiscal_year"],
                "section": doc["section"],
                "title": doc["title"],
                "text": chunk_text
            })
            current_chunk_sentences = []
            current_word_count = 0
            chunk_idx += 1

    # If any remaining sentences, append to last chunk or create new
    if current_chunk_sentences:
        chunk_text = " ".join(current_chunk_sentences)
        chunk_id = f"{doc['doc_id']}_{chunk_idx}"
        chunks.append({
            "doc_id": doc["doc_id"],
            "chunk_id": chunk_id,
            "ticker": doc["ticker"],
            "company": doc["company"],
            "doc_type": doc["doc_type"],
            "fiscal_year": doc["fiscal_year"],
            "section": doc["section"],
            "title": doc["title"],
            "text": chunk_text
        })
        
    return chunks

def generate_embeddings(chunks):
    """
    Generates keyword representations and dense 64-dimensional embeddings
    using TfidfVectorizer + TruncatedSVD (or sentence-transformers if installed).
    This ensures local reproducible vector search without API keys.
    """
    texts = [c["title"] + ": " + c["text"] for c in chunks]
    
    # 1. TF-IDF vectorizer for keyword search & embedding basis
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    # 2. Dense 64-dimensional embeddings via SVD (LSA)
    n_components = min(64, len(chunks) - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    dense_matrix = svd.fit_transform(tfidf_matrix)
    
    # Normalize vectors for cosine similarity
    norms = np.linalg.norm(dense_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized_matrix = (dense_matrix / norms).tolist()
    
    for idx, chunk in enumerate(chunks):
        chunk["embedding"] = normalized_matrix[idx]
        
    return chunks, vectorizer, svd

def index_to_elasticsearch(chunks):
    """
    Indexes chunked documents into Elasticsearch when running in Docker or connected to ES.
    """
    try:
        import requests
        headers = {"Content-Type": "application/json"}
        # Check ES health
        resp = requests.get(ELASTICSEARCH_URL, timeout=2)
        if resp.status_code != 200:
            return False
            
        # Delete index if exists
        requests.delete(f"{ELASTICSEARCH_URL}/{ELASTICSEARCH_INDEX}", timeout=2)
        
        # Create index mapping with text and dense_vector
        mapping = {
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "chunk_id": {"type": "keyword"},
                    "ticker": {"type": "keyword"},
                    "company": {"type": "text"},
                    "doc_type": {"type": "keyword"},
                    "fiscal_year": {"type": "keyword"},
                    "section": {"type": "keyword"},
                    "title": {"type": "text"},
                    "text": {"type": "text"},
                    "embedding": {"type": "dense_vector", "dims": len(chunks[0]["embedding"]), "index": True, "similarity": "cosine"}
                }
            }
        }
        requests.put(f"{ELASTICSEARCH_URL}/{ELASTICSEARCH_INDEX}", json=mapping, headers=headers, timeout=2)
        
        # Bulk index
        bulk_data = []
        for chunk in chunks:
            bulk_data.append(json.dumps({"index": {"_index": ELASTICSEARCH_INDEX, "_id": chunk["chunk_id"]}}))
            bulk_data.append(json.dumps(chunk))
        
        bulk_payload = "\n".join(bulk_data) + "\n"
        requests.post(f"{ELASTICSEARCH_URL}/_bulk", data=bulk_payload, headers=headers, timeout=5)
        print(f"Successfully indexed {len(chunks)} chunks into Elasticsearch index '{ELASTICSEARCH_INDEX}'.")
        return True
    except Exception as e:
        print(f"Elasticsearch indexing skipped (not connected): {e}")
        return False

def run_ingest():
    print(f"Loading raw documents from {DATASET_PATH}...")
    with open(DATASET_PATH, 'r') as f:
        docs = json.load(f)
        
    print("Chunking documents (Module 07 doc_id + chunk_id strategy)...")
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
        
    print(f"Created {len(all_chunks)} chunks from {len(docs)} parent documents.")
    
    print("Generating dense vector embeddings...")
    chunks_with_embeds, vectorizer, svd = generate_embeddings(all_chunks)
    
    print(f"Saving local knowledge base and embeddings cache to {INDEX_CACHE_PATH}...")
    with open(INDEX_CACHE_PATH, 'w') as f:
        json.dump(chunks_with_embeds, f, indent=2)
        
    # Try indexing to Elasticsearch if available
    index_to_elasticsearch(chunks_with_embeds)
    print("Ingestion complete!")
    return chunks_with_embeds

if __name__ == '__main__':
    run_ingest()
