import json
import math
import re

import numpy as np

from src.config import INDEX_CACHE_PATH


class BM25Searcher:
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.doc_lengths = []
        self.doc_freqs = {}
        self.tf_list = []
        self._build_index()

    def _tokenize(self, text):
        return re.findall(r"\w+", (text or "").lower())

    def _build_index(self):
        total_len = 0
        for chunk in self.chunks:
            tokens = self._tokenize(
                f"{chunk.get('title','')} {chunk.get('company','')} {chunk.get('product','')} {chunk.get('issue','')} {chunk.get('text','')}"
            )
            self.doc_lengths.append(len(tokens))
            total_len += len(tokens)
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

    def search(self, query, top_k=5, filter_company=None, filter_product=None):
        q_tokens = self._tokenize(query)
        scores = []
        for idx, chunk in enumerate(self.chunks):
            if filter_company and chunk.get("company_key") != filter_company:
                scores.append((0.0, idx))
                continue
            if filter_product and chunk.get("product") != filter_product:
                scores.append((0.0, idx))
                continue
            score = 0.0
            length = self.doc_lengths[idx]
            tf_dict = self.tf_list[idx]
            for term in q_tokens:
                if term in tf_dict:
                    tf = tf_dict[term]
                    denom = tf + self.k1 * (1 - self.b + self.b * (length / self.avg_doc_len))
                    score += self._idf(term) * (tf * (self.k1 + 1) / denom)
            scores.append((score, idx))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [(self.chunks[idx], score) for score, idx in scores[:top_k] if score > 0]


class VectorSearcher:
    def __init__(self, chunks):
        self.chunks = chunks
        self.embeddings = np.array([c["embedding"] for c in chunks], dtype=np.float32)
        self._init_vocabulary()

    def _init_vocabulary(self):
        self.vocab = {}
        for idx, chunk in enumerate(self.chunks):
            words = re.findall(
                r"\w+",
                f"{chunk.get('title','')} {chunk.get('text','')}".lower(),
            )
            for w in set(words):
                self.vocab.setdefault(w, []).append(self.embeddings[idx])
        for w, vecs in self.vocab.items():
            mean = np.mean(vecs, axis=0)
            norm = np.linalg.norm(mean)
            self.vocab[w] = mean / norm if norm > 0 else mean

    def embed_query(self, query):
        words = re.findall(r"\w+", query.lower())
        vecs = [self.vocab[w] for w in words if w in self.vocab]
        vec = np.mean(vecs, axis=0) if vecs else np.mean(self.embeddings, axis=0)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def search(self, query, top_k=5, filter_company=None, filter_product=None):
        q_vec = self.embed_query(query)
        scores = []
        for idx, chunk in enumerate(self.chunks):
            if filter_company and chunk.get("company_key") != filter_company:
                scores.append((-1.0, idx))
                continue
            if filter_product and chunk.get("product") != filter_product:
                scores.append((-1.0, idx))
                continue
            scores.append((float(np.dot(q_vec, self.embeddings[idx])), idx))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [(self.chunks[idx], score) for score, idx in scores[:top_k]]


def rewrite_query(query):
    """Best practice 3: expand company nicknames, products, and complaint slang."""
    expanded = query
    expansions = {
        r"\bBofA\b": "Bank of America BofA",
        r"\bBOA\b": "Bank of America BOA",
        r"\bWF\b": "Wells Fargo WF",
        r"\bNFCU\b": "Navy Federal Credit Union NFCU",
        r"\bApple Card\b": "Apple Card Goldman Sachs",
        r"\bZelle\b": "Zelle Early Warning money transfer",
        r"\bBNPL\b": "buy now pay later BNPL Affirm",
        r"\boverdraft\b": "overdraft NSF insufficient funds fee",
        r"\bID theft\b": "identity theft ID theft fraudulent account",
        r"\bfraudulent account\b": "identity theft fraudulent account opened without knowledge",
        r"\bmixed file\b": "mixed credit file wrong person information",
        r"\bhard inquiry\b": "hard inquiry hard pull credit report unauthorized",
        r"\bforbearance\b": "mortgage forbearance COVID hardship",
        r"\brepossession\b": "auto loan repossession vehicle seized",
        r"\bdebt validation\b": "debt validation FDCPA collection not owed",
        r"\bFCRA\b": "Fair Credit Reporting Act FCRA credit reporting investigation",
        r"\bFDCPA\b": "Fair Debt Collection Practices Act FDCPA",
        r"\bescrow\b": "mortgage escrow taxes insurance",
        r"\bID\b": "identity ID",
    }
    for pat, rep in expansions.items():
        expanded = re.sub(pat, rep, expanded, flags=re.IGNORECASE)
    return expanded


def rerank_documents(query, candidates, top_k=5):
    """
    Best practice 2: domain re-ranker for consumer-complaint ops.
    Boosts company/product/issue matches and distinctive quoted phrases.
    """
    q_lower = query.lower()
    q_terms = set(re.findall(r"\w+", q_lower))
    quoted = re.findall(r'"([^"]+)"', query)

    reranked = []
    for chunk, orig_score in candidates:
        boost = 0.0
        company = (chunk.get("company") or "").lower()
        company_key = (chunk.get("company_key") or "").lower().replace("_", " ")
        product = (chunk.get("product") or "").lower()
        issue = (chunk.get("issue") or "").lower()
        text = f"{chunk.get('title','')} {chunk.get('text','')}".lower()

        if company and company in q_lower:
            boost += 1.6
        if company_key and company_key in q_lower:
            boost += 0.8
        if product and product in q_lower:
            boost += 1.1
        if issue and any(tok in q_lower for tok in issue.split() if len(tok) > 4):
            boost += 0.7
        if chunk.get("complaint_id") and chunk["complaint_id"] in query:
            boost += 2.5
        for phrase in quoted:
            if phrase.lower() in text:
                boost += 2.0

        doc_terms = set(re.findall(r"\w+", text))
        overlap = len(q_terms.intersection(doc_terms)) / max(1, len(q_terms))
        boost += overlap * 0.4

        reranked.append((chunk, orig_score + boost * 0.18))
    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_k]


class ComplaintSearchEngine:
    def __init__(self, cache_path=INDEX_CACHE_PATH):
        with open(cache_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
        self.bm25 = BM25Searcher(self.chunks)
        self.vector_searcher = VectorSearcher(self.chunks)

    def search(
        self,
        query,
        top_k=5,
        mode="hybrid_rerank",
        filter_company=None,
        filter_product=None,
        rewrite=True,
    ):
        search_query = rewrite_query(query) if rewrite else query
        kwargs = {
            "top_k": top_k,
            "filter_company": filter_company,
            "filter_product": filter_product,
        }

        if mode == "text":
            return self.bm25.search(search_query, **kwargs)
        if mode == "vector":
            return self.vector_searcher.search(search_query, **kwargs)
        if mode in ("hybrid", "hybrid_rerank"):
            text_res = self.bm25.search(search_query, top_k=top_k * 3, filter_company=filter_company, filter_product=filter_product)
            vec_res = self.vector_searcher.search(search_query, top_k=top_k * 3, filter_company=filter_company, filter_product=filter_product)
            rrf_scores, chunk_map, k_rrf = {}, {}, 60.0
            for rank, (chunk, _score) in enumerate(text_res):
                cid = chunk["chunk_id"]
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k_rrf + rank + 1)
                chunk_map[cid] = chunk
            for rank, (chunk, _score) in enumerate(vec_res):
                cid = chunk["chunk_id"]
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k_rrf + rank + 1)
                chunk_map[cid] = chunk
            hybrid = [
                (chunk_map[cid], score)
                for cid, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[: top_k * 2]
            ]
            if mode == "hybrid_rerank":
                return rerank_documents(search_query, hybrid, top_k=top_k)
            return hybrid[:top_k]
        raise ValueError(f"Unknown search mode: {mode}")


if __name__ == "__main__":
    engine = ComplaintSearchEngine()
    q = "What are customers saying about Wells Fargo overdraft fees?"
    print("Query:", q)
    for chunk, score in engine.search(q, top_k=3):
        print(f"[{score:.3f}] {chunk['chunk_id']} | {chunk['company']} | {chunk['product']}")
