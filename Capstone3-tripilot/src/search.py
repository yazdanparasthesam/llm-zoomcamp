"""
TripPilot retrieval engine — the three rubric best practices:

  Best Practice 3: User Query Rewriting   (rewrite_query)
  Best Practice 1: Hybrid Search, RRF     (hybrid_search)
  Best Practice 2: Document Re-ranking    (rerank)

Modes evaluated by src/eval_retrieval.py:
  text           -> BM25 keyword search                    (app default: eval winner)
  vector         -> TF-IDF/SVD dense cosine similarity
  hybrid         -> Reciprocal Rank Fusion (k=60) of both
  hybrid_rerank  -> hybrid + travel-domain re-ranker
"""
import json
import math
import os
import re
from collections import defaultdict

from src import config

WORD_RE = re.compile(r"[a-z0-9']+")

# --------------------------------------------------------------------------
# Best Practice 3 — User Query Rewriting
# --------------------------------------------------------------------------
REWRITE_EXPANSIONS = {
    # airport codes / city nicknames -> city keywords
    "nyc": "new york jfk",
    "jfk": "new york jfk",
    "lon": "london",
    "lhr": "london heathrow",
    "cdg": "paris charles de gaulle",
    "bcn": "barcelona el prat",
    "ams": "amsterdam schiphol",
    "vie": "vienna",
    "mad": "madrid",
    "ber": "berlin",
    "prg": "prague",
    "bud": "budapest hungary",
    "zrh": "zurich",
    "cph": "copenhagen",
    "ist": "istanbul",
    "lys": "lyon",
    "muc": "munich",
    "bru": "brussels",
    "opo": "porto",
    "vce": "venice",
    "spu": "split",
    "fco": "rome fiumicino",
    # travel slang -> review vocabulary
    "bkfst": "breakfast",
    "brekky": "breakfast",
    "a/c": "air conditioning",
    "ac": "air conditioning",
    "wifi": "wifi internet remote work desk",
    "wi-fi": "wifi internet remote work desk",
    "bucks": "eur budget price value",
    "cheap": "cheap budget value price",
    "noisy": "noise street thin walls",
    "comfy": "comfortable bed mattress",
    "hostel": "budget value price",
    "honeymoon": "couple romance romantic view",
    "kids": "family children pool",
    "sightseeing": "location walking distance centre landmarks",
    "downtown": "centre location city center",
    "overpriced": "price value hidden fees not worth",
}
CITY_TERMS = {
    "london", "paris", "amsterdam", "barcelona", "rome", "vienna", "madrid",
    "berlin", "prague", "budapest", "zurich", "copenhagen", "lyon", "munich",
    "brussels", "porto", "venice", "split", "istanbul",
}


def rewrite_query(query):
    """Expand abbreviations / slang with domain vocabulary (Best Practice 3)."""
    tokens = re.findall(r"[a-z0-9'/+-]+", query.lower())
    additions = []
    for t in tokens:
        if t in REWRITE_EXPANSIONS:
            additions.append(REWRITE_EXPANSIONS[t])
    rewritten = query if not additions else f"{query} {' '.join(additions)}"
    return rewritten, additions


# --------------------------------------------------------------------------
# In-memory index (built from data/index_cache.json or on the fly)
# --------------------------------------------------------------------------
class TripIndex:
    def __init__(self):
        self.chunks = []
        self.vectors = None
        self.vec = None   # fitted TfidfVectorizer
        self.svd = None   # fitted TruncatedSVD
        self._bm25 = None
        self._load()

    # ------------------------------ build / load --------------------------
    def _load(self):
        from src import ingest

        if os.path.exists(config.INDEX_CACHE_PATH):
            cache = json.load(open(config.INDEX_CACHE_PATH))
            self.chunks = cache["chunks"]
        else:
            reviews = ingest.load_reviews()
            self.chunks = ingest.build_chunks(reviews)
            cache = None
        # always refit TF-IDF/SVD deterministically (fast on ~700 chunks)
        V, vec, svd = ingest.embed_chunks(self.chunks)
        self.vectors, self.vec, self.svd = V, vec, svd
        # BM25 over metadata-enriched documents (hotel, city, section, tags
        # + review text) so keyword search can match hotel/city names
        enriched = [
            f"{c['hotel_name']} {c['city']} {c['section']} "
            f"{' '.join(c['tags'])} {c['text']}" for c in self.chunks
        ]
        self._bm25 = _BM25(enriched)

    # ------------------------------ sub-searches --------------------------
    def bm25_scores(self, query):
        return self._bm25.scores(query)

    def vector_scores(self, query):
        import numpy as np
        from src import ingest
        qv = ingest.embed_query(query, self.vec, self.svd)
        return np.dot(self.vectors, qv)

    # ------------------------------ public API ----------------------------
    def search(self, query, mode="text", k=None, filters=None, boost=None):
        k = k or config.SEARCH_TOP_K
        filters = filters or {}
        rewritten = None
        q = query
        if mode in ("hybrid", "hybrid_rerank"):
            q, _ = rewrite_query(query)
            rewritten = q
        if mode == "text":
            scores = self.bm25_scores(q)
            order = _top_indices(scores, k * 4)
        elif mode == "vector":
            scores = self.vector_scores(q)
            order = _top_indices(scores, k * 4)
        else:  # hybrid / hybrid_rerank
            order = self._rrf(q, k * 4)
            if mode == "hybrid_rerank":
                order = self.rerank(query, order, filters)
        return self._materialize(order, k, filters, rewritten)

    def _rrf(self, query, pool):
        rrf_k = config.RRF_K
        bm_order = _top_indices(self.bm25_scores(query), pool)
        ve_order = _top_indices(self.vector_scores(query), pool)
        fused = defaultdict(float)
        for rank, idx in enumerate(bm_order):
            fused[idx] += 1.0 / (rrf_k + rank + 1)
        for rank, idx in enumerate(ve_order):
            fused[idx] += 1.0 / (rrf_k + rank + 1)
        return sorted(fused, key=lambda i: fused[i], reverse=True)

    def rerank(self, query, order, filters=None):
        """Best Practice 2 — travel-domain re-ranking boosts."""
        filters = filters or {}
        q = query.lower()
        q_tokens = set(WORD_RE.findall(q))
        quoted = re.findall(r'"([^"]+)"', query)
        want_negative = any(w in q for w in
                            ("complain", "problem", "bad", "worst", "issue",
                             "noise", "broken", "dirty", "avoid", "negative"))
        want_positive = any(w in q for w in
                            ("best", "praise", "love", "good", "great",
                             "recommend", "worth", "positive"))
        q_cities = {c for c in CITY_TERMS if c in q}
        scored = []
        for rank, idx in enumerate(order):
            c = self.chunks[idx]
            s = 1.0 / (rank + 1)
            # hotel name mention (+2.5, strongest: exact evidence requests)
            name = c["hotel_name"].lower()
            if name in q or all(t in q for t in name.split()[:2]):
                s += 2.5
            # city match (+1.6)
            if c["city"].lower() in q_cities or (
                    filters.get("city") and
                    c["city"].lower() == filters["city"].lower()):
                s += 1.6
            # quoted phrase (+2.0)
            for phrase in quoted:
                if phrase.lower() in c["text"].lower():
                    s += 2.0
            # trip-type / tag alignment (+0.7)
            tags = " ".join(c["tags"]).lower()
            for t in ("business", "couple", "family", "solo", "group"):
                if t in q and t in tags:
                    s += 0.7
            # sentiment-section alignment (+0.8)
            if want_negative and c["section"] == "negative":
                s += 0.8
            if want_positive and c["section"] == "positive":
                s += 0.8
            # term overlap density (+0.4)
            c_tokens = set(WORD_RE.findall(c["text"].lower()))
            overlap = len(q_tokens & c_tokens) / max(1, len(q_tokens))
            s += 0.4 * overlap
            scored.append((s, idx))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [idx for _, idx in scored]

    # ------------------------------ utils ---------------------------------
    def _materialize(self, order, k, filters, rewritten):
        out = []
        for idx in order:
            c = dict(self.chunks[idx])
            if filters.get("city") and c["city"].lower() != filters["city"].lower():
                continue
            if filters.get("hotel") and c["hotel_name"].lower() != filters["hotel"].lower():
                continue
            out.append(c)
            if len(out) >= k:
                break
        return {"results": out, "rewritten_query": rewritten}


def _top_indices(scores, n):
    import numpy as np
    arr = np.asarray(scores, dtype=float)
    if arr.size == 0:
        return []
    n = min(n, arr.size)
    part = np.argpartition(-arr, n - 1)[:n]
    return part[np.argsort(-arr[part])].tolist()


# --------------------------------------------------------------------------
# Minimal Okapi BM25 (numpy) — keeps text mode fully offline & deterministic
# --------------------------------------------------------------------------
class _BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.doc_tokens = [WORD_RE.findall(d.lower()) for d in docs]
        self.doc_len = [len(t) for t in self.doc_tokens]
        self.avgdl = sum(self.doc_len) / max(1, len(self.doc_len))
        df = defaultdict(int)
        for toks in self.doc_tokens:
            for t in set(toks):
                df[t] += 1
        n_docs = max(1, len(docs))
        self.idf = {t: math.log(1 + (n_docs - f + 0.5) / (f + 0.5))
                    for t, f in df.items()}

    def scores(self, query):
        import numpy as np
        q_tokens = WORD_RE.findall(query.lower())
        scores = np.zeros(len(self.doc_tokens))
        for i, toks in enumerate(self.doc_tokens):
            if not toks:
                continue
            tf = defaultdict(int)
            for t in toks:
                tf[t] += 1
            dl = self.doc_len[i] or 1
            s = 0.0
            for t in q_tokens:
                if t not in self.idf or tf[t] == 0:
                    continue
                f = tf[t]
                s += self.idf[t] * (f * (self.k1 + 1)) / (
                    f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            scores[i] = s
        return scores


# --------------------------------------------------------------------------
# module-level singleton + convenience API
# --------------------------------------------------------------------------
_INDEX = None


def get_index():
    global _INDEX
    if _INDEX is None:
        _INDEX = TripIndex()
    return _INDEX


def search(query, mode="text", k=None, filters=None):
    return get_index().search(query, mode=mode, k=k, filters=filters)


SEARCH_MODES = ["text", "vector", "hybrid", "hybrid_rerank"]


def selected_default_mode():
    """evaluation_results/selected_retriever.json wins; else 'text'."""
    path = os.path.join(config.EVAL_DIR, "selected_retriever.json")
    if config.DEFAULT_SEARCH_MODE:
        return config.DEFAULT_SEARCH_MODE
    if os.path.exists(path):
        try:
            return json.load(open(path)).get("selected_mode", "text")
        except Exception:
            pass
    return "text"


if __name__ == "__main__":
    res = search("Is the breakfast at Hotel de la Cite in Lyon worth it?",
                 mode="text")
    for c in res["results"]:
        print(c["chunk_id"], "|", c["hotel_name"], "|", c["text"][:90])
