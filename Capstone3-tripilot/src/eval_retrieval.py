#!/usr/bin/env python3
"""
TripPilot retrieval evaluation (rubric: multiple approaches, best used).

Evaluates 4+ retrieval approaches over data/ground_truth_qa.json at BOTH
Module-07 levels — parent document (doc_id) and chunk (chunk_id):
  Hit Rate@5 and MRR@5 for
    text (BM25), vector (cosine), hybrid (RRF), hybrid + re-ranking
  plus ablations: rerank delta, rewrite delta (hybrid vs hybrid_no_rewrite)

Writes:
  evaluation_results/retrieval_eval.json
  evaluation_results/selected_retriever.json   (winner -> app default)

Run:  python3 -m src.eval_retrieval
"""
import json
import os

from src import config
from src.search import SEARCH_MODES, get_index, rewrite_query


def _ranking(idx, question, mode, k=5, use_rewrite=None):
    """Return ordered chunk list for one ground-truth question."""
    q = question
    if use_rewrite is False:
        # bypass the built-in rewrite inside hybrid modes
        orig = rewrite_query
        import src.search as sm
        sm.rewrite_query = lambda x: (x, [])
        try:
            res = idx.search(q, mode=mode, k=k)
        finally:
            sm.rewrite_query = orig
    else:
        res = idx.search(question, mode=mode, k=k)
    return res["results"]


def evaluate(gt, idx, mode, k=5, use_rewrite=None):
    doc_hits, chunk_hits = 0, 0
    doc_rr, chunk_rr = 0.0, 0.0
    for item in gt:
        chunks = _ranking(idx, item["question"], mode, k, use_rewrite)
        doc_ids = [c["doc_id"] for c in chunks]
        chunk_ids = [c["chunk_id"] for c in chunks]
        if item["doc_id"] in doc_ids:
            doc_hits += 1
            doc_rr += 1.0 / (doc_ids.index(item["doc_id"]) + 1)
        target_chunks = {cid for c, cid in
                         [(c, c["chunk_id"]) for c in idx.chunks
                          if c["doc_id"] == item["doc_id"]]}
        rank = next((i for i, cid in enumerate(chunk_ids)
                     if cid in target_chunks), None)
        if rank is not None:
            chunk_hits += 1
            chunk_rr += 1.0 / (rank + 1)
    n = len(gt)
    return {
        "doc_hit_rate@5": round(doc_hits / n, 4),
        "doc_mrr@5": round(doc_rr / n, 4),
        "chunk_hit_rate@5": round(chunk_hits / n, 4),
        "chunk_mrr@5": round(chunk_rr / n, 4),
    }


def main():
    gt = json.load(open(config.GROUND_TRUTH_PATH))
    idx = get_index()
    results = {"n_questions": len(gt), "levels": ["doc_id", "chunk_id"],
               "approaches": {}}
    for mode in SEARCH_MODES:
        print(f"[eval] {mode} ...")
        results["approaches"][mode] = evaluate(gt, idx, mode)

    # ablation 1: rerank delta
    h = results["approaches"]["hybrid"]
    hr = results["approaches"]["hybrid_rerank"]
    results["rerank_ablation"] = {
        "doc_mrr@5_delta": round(hr["doc_mrr@5"] - h["doc_mrr@5"], 4),
        "chunk_mrr@5_delta": round(hr["chunk_mrr@5"] - h["chunk_mrr@5"], 4),
    }
    # ablation 2: rewrite delta (hybrid without query rewriting)
    hnr = evaluate(gt, idx, "hybrid", use_rewrite=False)
    results["rewrite_ablation"] = {
        "hybrid_no_rewrite": hnr,
        "doc_hit@5_delta": round(h["doc_hit_rate@5"] - hnr["doc_hit_rate@5"], 4),
        "doc_mrr@5_delta": round(h["doc_mrr@5"] - hnr["doc_mrr@5"], 4),
    }

    # winner: max chunk MRR, tiebreak doc MRR (production default)
    best = max(SEARCH_MODES,
               key=lambda m: (results["approaches"][m]["chunk_mrr@5"],
                              results["approaches"][m]["doc_mrr@5"]))
    results["selected_mode"] = best

    os.makedirs(config.EVAL_DIR, exist_ok=True)
    with open(os.path.join(config.EVAL_DIR, "retrieval_eval.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(config.EVAL_DIR, "selected_retriever.json"), "w") as f:
        json.dump({"selected_mode": best,
                   "reason": "max chunk MRR@5 (tiebreak doc MRR@5)",
                   "eval_file": "evaluation_results/retrieval_eval.json"},
                  f, indent=2)
    print(json.dumps(results, indent=2))
    print(f"\n[eval] selected production retriever: {best}")
    return results


if __name__ == "__main__":
    main()
