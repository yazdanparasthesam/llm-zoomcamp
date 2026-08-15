import json
from collections import OrderedDict

from src.config import GROUND_TRUTH_PATH, RESULTS_DIR, SELECTED_RETRIEVER_PATH
from src.search import ComplaintSearchEngine


def hit_rate(flags):
    return sum(1 for row in flags if any(row)) / max(1, len(flags))


def mrr(flags):
    total = 0.0
    for row in flags:
        for rank, ok in enumerate(row):
            if ok:
                total += 1.0 / (rank + 1)
                break
    return total / max(1, len(flags))


def evaluate_method(engine, ground_truth, mode, rewrite=True):
    doc_flags, chunk_flags = [], []
    for item in ground_truth:
        results = engine.search(
            item["question"],
            top_k=5,
            mode=mode,
            rewrite=rewrite,
        )
        docs = [c["doc_id"] for c, _ in results]
        chunks = [c["chunk_id"] for c, _ in results]
        doc_flags.append([d == item["ground_truth_doc_id"] for d in docs])
        chunk_flags.append([c == item["ground_truth_chunk_id"] for c in chunks])
    return {
        "doc_hit@5": round(hit_rate(doc_flags), 4),
        "doc_mrr@5": round(mrr(doc_flags), 4),
        "chunk_hit@5": round(hit_rate(chunk_flags), 4),
        "chunk_mrr@5": round(mrr(chunk_flags), 4),
    }


def run_eval():
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)
    engine = ComplaintSearchEngine()

    methods = OrderedDict(
        [
            ("text", "Text Search (BM25)"),
            ("vector", "Vector Search (Cosine)"),
            ("hybrid", "Hybrid Search (RRF)"),
            ("hybrid_rerank", "Hybrid + Re-ranking"),
        ]
    )

    # Ablation: hybrid with vs without rerank is already in the table.
    # Extra ablation: hybrid_rerank without query rewrite.
    print("=" * 88)
    print("COMPLAINTRADAR — RETRIEVAL EVALUATION")
    print(f"Ground-truth questions: {len(ground_truth)}")
    print("=" * 88)
    print(f"{'Method':<32} | {'Doc Hit@5':<10} | {'Doc MRR@5':<10} | {'Chunk Hit@5':<12} | {'Chunk MRR@5'}")
    print("-" * 88)

    results = {}
    for mode, label in methods.items():
        metrics = evaluate_method(engine, ground_truth, mode, rewrite=True)
        results[mode] = {"label": label, **metrics}
        print(
            f"{label:<32} | {metrics['doc_hit@5']:<10.4f} | {metrics['doc_mrr@5']:<10.4f} | "
            f"{metrics['chunk_hit@5']:<12.4f} | {metrics['chunk_mrr@5']:.4f}"
        )

    no_rerank = results["hybrid"]
    with_rerank = results["hybrid_rerank"]
    delta_doc = round(with_rerank["doc_mrr@5"] - no_rerank["doc_mrr@5"], 4)
    delta_chunk = round(with_rerank["chunk_mrr@5"] - no_rerank["chunk_mrr@5"], 4)
    print("-" * 88)
    print(f"Rerank ablation Δ Doc MRR@5   = {delta_doc:+.4f}  (hybrid+rerank minus hybrid)")
    print(f"Rerank ablation Δ Chunk MRR@5 = {delta_chunk:+.4f}")

    rewrite_off = evaluate_method(engine, ground_truth, "hybrid_rerank", rewrite=False)
    results["hybrid_rerank_no_rewrite"] = {
        "label": "Hybrid + Re-ranking (no rewrite)",
        **rewrite_off,
    }
    print(
        f"{'Hybrid + Re-ranking (no rewrite)':<32} | {rewrite_off['doc_hit@5']:<10.4f} | "
        f"{rewrite_off['doc_mrr@5']:<10.4f} | {rewrite_off['chunk_hit@5']:<12.4f} | {rewrite_off['chunk_mrr@5']:.4f}"
    )

    # Select the best production retriever by chunk MRR, then doc MRR, then hit rate.
    scored = []
    for mode in ("text", "vector", "hybrid", "hybrid_rerank"):
        m = results[mode]
        scored.append((m["chunk_mrr@5"], m["doc_mrr@5"], m["chunk_hit@5"], mode))
    scored.sort(reverse=True)
    winner = scored[0][3]
    selection = {
        "selected_mode": winner,
        "selected_label": results[winner]["label"],
        "reason": "Highest chunk MRR@5, then doc MRR@5, then chunk Hit@5 on the 100-question ground-truth set.",
        "metrics": results,
        "rerank_delta_doc_mrr@5": delta_doc,
        "rerank_delta_chunk_mrr@5": delta_chunk,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "retrieval_eval.json").write_text(json.dumps(selection, indent=2))
    SELECTED_RETRIEVER_PATH.write_text(
        json.dumps(
            {
                "selected_mode": winner,
                "selected_label": results[winner]["label"],
                "chunk_mrr@5": results[winner]["chunk_mrr@5"],
                "doc_mrr@5": results[winner]["doc_mrr@5"],
            },
            indent=2,
        )
    )
    print("=" * 88)
    print(f"SELECTED DEFAULT RETRIEVER: {results[winner]['label']}  ({winner})")
    print(f"Wrote {RESULTS_DIR / 'retrieval_eval.json'}")
    print("=" * 88)
    return selection


if __name__ == "__main__":
    run_eval()
