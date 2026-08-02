import json
import math
import re
import numpy as np
from src.config import INDEX_CACHE_PATH, ELASTICSEARCH_URL, ELASTICSEARCH_INDEX, USE_DOCKER

class BM25Searcher:
    """
    Okapi BM25 keyword retrieval implementation for hybrid search.
    """
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.doc_lengths = []
        self.avg_doc_len = 0
        self.doc_freqs = {}
        self.tf_list = []
        self._build_index()

    def _tokenize(self, text):
        return re.findall(r'\w+', text.lower())

    def _build_index(self):
        total_len = 0
        for chunk in self.chunks:
            tokens = self._tokenize(chunk["title"] + " " + chunk["text"])
            length = len(tokens)
            self.doc_lengths.append(length)
            total_len += length

            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.tf_list.append(tf)

            for t in set(tokens):
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_doc_len = total_len / max(1, len(self.chunks))
        self.N = len(self.chunks)

    def _idf(self, term):
        df = self.doc_freqs.get(term, 0)
        return math.log(1.0 + (self.N - df + 0.5) / (df + 0.5))

    def search(self, query, top_k=5, filter_ticker=None):
        q_tokens = self._tokenize(query)
        scores = []
        for idx, chunk in enumerate(self.chunks):
            if filter_ticker and chunk["ticker"].upper() != filter_ticker.upper():
                scores.append((0.0, idx))
                continue
            score = 0.0
            length = self.doc_lengths[idx]
            tf_dict = self.tf_list[idx]
            for term in q_tokens:
                if term in tf_dict:
                    tf = tf_dict[term]
                    idf_val = self._idf(term)
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (length / self.avg_doc_len))
                    score += idf_val * (numerator / denominator)
            scores.append((score, idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [(self.chunks[idx], score) for score, idx in scores[:top_k] if score > 0]

class VectorSearcher:
    """
    Dense vector cosine similarity retrieval using pre-computed embeddings.
    """
    def __init__(self, chunks):
        self.chunks = chunks
        self.embeddings = np.array([c["embedding"] for c in chunks], dtype=np.float32)
        # Vocabulary mapping for basic SVD query projection
        self._init_vocabulary()

    def _init_vocabulary(self):
        # Create a simple term-to-vector projection from doc embeddings
        self.vocab = {}
        for idx, chunk in enumerate(self.chunks):
            words = re.findall(r'\w+', (chunk["title"] + " " + chunk["text"]).lower())
            for w in set(words):
                if w not in self.vocab:
                    self.vocab[w] = []
                self.vocab[w].append(self.embeddings[idx])
        for w in self.vocab:
            self.vocab[w] = np.mean(self.vocab[w], axis=0)
            norm = np.linalg.norm(self.vocab[w])
            if norm > 0:
                self.vocab[w] /= norm

    def embed_query(self, query):
        words = re.findall(r'\w+', query.lower())
        vecs = [self.vocab[w] for w in words if w in self.vocab]
        if not vecs:
            # Default mean vector if out of vocabulary
            vec = np.mean(self.embeddings, axis=0)
        else:
            vec = np.mean(vecs, axis=0)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def search(self, query, top_k=5, filter_ticker=None):
        q_vec = self.embed_query(query)
        scores = []
        for idx, chunk in enumerate(self.chunks):
            if filter_ticker and chunk["ticker"].upper() != filter_ticker.upper():
                scores.append((-1.0, idx))
                continue
            sim = float(np.dot(q_vec, self.embeddings[idx]))
            scores.append((sim, idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [(self.chunks[idx], score) for score, idx in scores[:top_k]]

def rewrite_query(query):
    """
    Best Practice 3: User Query Rewriting / Expansion.
    Expands ticker symbols and financial acronyms to improve recall and hybrid search matching.
    """
    expanded = query
    ticker_expansions = {
        r'\bNVDA\b': 'NVIDIA NVDA',
        r'\bAAPL\b': 'Apple AAPL',
        r'\bMSFT\b': 'Microsoft MSFT',
        r'\bTSLA\b': 'Tesla TSLA',
        r'\bGOOGL\b': 'Alphabet Google GOOGL'
    }
    term_expansions = {
        r'\bCapEx\b': 'capital expenditures CapEx',
        r'\bMD&A\b': 'Management Discussion and Analysis MD&A',
        r'\bFSD\b': 'Full Self-Driving FSD autonomous',
        r'\bDMA\b': 'Digital Markets Act regulatory EU',
        r'\bAI\b': 'artificial intelligence AI'
    }
    for pat, rep in {**ticker_expansions, **term_expansions}.items():
        expanded = re.sub(pat, rep, expanded, flags=re.IGNORECASE)
    return expanded

def rerank_documents(query, candidates, top_k=5):
    """
    Best Practice 2: Document Re-ranking.
    Re-ranks candidate chunks by scoring exact ticker matches, title relevance,
    and term overlap density.
    """
    q_lower = query.lower()
    q_terms = set(re.findall(r'\w+', q_lower))
    
    reranked = []
    for chunk, orig_score in candidates:
        boost = 0.0
        # Check explicit ticker match
        if chunk["ticker"].lower() in q_lower or chunk["company"].lower() in q_lower:
            boost += 1.5
        
        # Check section prominence based on query intent
        if any(w in q_lower for w in ["risk", "export", "control", "rule", "law", "regulation", "court", "doj", "illegal"]):
            if "risk" in chunk["section"].lower():
                boost += 1.2
        elif any(w in q_lower for w in ["revenue", "margin", "billion", "growth", "income", "sales"]):
            if "md&a" in chunk["section"].lower():
                boost += 1.0
        if any(w in q_lower for w in ["say", "call", "comment", "state", "highlight", "announce", "timeline", "musk", "cook", "pichai", "nadella", "huang"]):
            if "earnings" in chunk["doc_type"].lower():
                boost += 1.0
                
        # Term overlap ratio
        doc_terms = set(re.findall(r'\w+', (chunk["title"] + " " + chunk["text"]).lower()))
        overlap = len(q_terms.intersection(doc_terms)) / max(1, len(q_terms))
        boost += overlap * 0.3
        
        final_score = orig_score + boost * 0.15
        reranked.append((chunk, final_score))
        
    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_k]

class FinancialSearchEngine:
    """
    Unified Financial Search Engine combining:
    1. Text Search (BM25)
    2. Vector Search (Cosine Similarity)
    3. Hybrid Search (Reciprocal Rank Fusion - RRF)
    4. Hybrid + Re-ranking (Best Practice 2)
    """
    def __init__(self, cache_path=INDEX_CACHE_PATH):
        with open(cache_path, 'r') as f:
            self.chunks = json.load(f)
        self.bm25 = BM25Searcher(self.chunks)
        self.vector_searcher = VectorSearcher(self.chunks)

    def search(self, query, top_k=5, mode="hybrid_rerank", filter_ticker=None, rewrite=True):
        search_query = rewrite_query(query) if rewrite else query

        if mode == "text":
            return self.bm25.search(search_query, top_k=top_k, filter_ticker=filter_ticker)
        elif mode == "vector":
            return self.vector_searcher.search(search_query, top_k=top_k, filter_ticker=filter_ticker)
        elif mode in ("hybrid", "hybrid_rerank"):
            # Reciprocal Rank Fusion (RRF)
            text_res = self.bm25.search(search_query, top_k=top_k * 2, filter_ticker=filter_ticker)
            vec_res = self.vector_searcher.search(search_query, top_k=top_k * 2, filter_ticker=filter_ticker)

            rrf_scores = {}
            chunk_map = {}
            k_rrf = 60.0

            for rank, (chunk, score) in enumerate(text_res):
                c_id = chunk["chunk_id"]
                rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (k_rrf + rank + 1))
                chunk_map[c_id] = chunk

            for rank, (chunk, score) in enumerate(vec_res):
                c_id = chunk["chunk_id"]
                rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (k_rrf + rank + 1))
                chunk_map[c_id] = chunk

            sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
            hybrid_candidates = [(chunk_map[c_id], score) for c_id, score in sorted_rrf[:top_k * 2]]

            if mode == "hybrid_rerank":
                return rerank_documents(search_query, hybrid_candidates, top_k=top_k)
            else:
                return hybrid_candidates[:top_k]
        else:
            raise ValueError(f"Unknown search mode: {mode}")

if __name__ == "__main__":
    engine = FinancialSearchEngine()
    test_q = "What are NVIDIA export controls to China?"
    print("Testing Hybrid + Rerank Search for:", test_q)
    results = engine.search(test_q, top_k=3, mode="hybrid_rerank")
    for r, s in results:
        print(f"[{s:.2f}] {r['chunk_id']} | {r['title']}")
