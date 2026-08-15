import json

from src.config import GROUND_TRUTH_PATH, RESULTS_DIR, get_default_search_mode
from src.llm import evaluate_relevance, generate_rag_answer
from src.search import ComplaintSearchEngine


STRATEGIES = {
    "ops": "Ops Analyst (Default)",
    "compliance": "Compliance Officer",
    "hype": "Hype / Overclaim (Expected weaker)",
}


def run_eval(max_questions=40):
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)[:max_questions]
    engine = ComplaintSearchEngine()
    mode = get_default_search_mode()

    print("=" * 88)
    print("COMPLAINTRADAR — LLM (RAG) EVALUATION")
    print(f"Questions: {len(ground_truth)} | Retriever: {mode}")
    print("=" * 88)
    print(f"{'Prompt Strategy':<34} | {'RELEVANT %':<12} | {'PARTIAL %':<12} | {'NON_REL %':<12} | Mean")
    print("-" * 88)

    report = {"retriever_mode": mode, "n_questions": len(ground_truth), "strategies": {}}
    best_name, best_score = None, -1.0

    for key, label in STRATEGIES.items():
        labels = []
        scores = []
        for item in ground_truth:
            hits = engine.search(item["question"], top_k=4, mode=mode, rewrite=True)
            chunks = [c for c, _ in hits]
            answer = generate_rag_answer(item["question"], chunks, system_prompt_type=key)
            lab, score = evaluate_relevance(item["question"], answer, chunks)
            labels.append(lab)
            scores.append(score)
        n = max(1, len(labels))
        rel = 100.0 * labels.count("RELEVANT") / n
        part = 100.0 * labels.count("PARTIALLY_RELEVANT") / n
        non = 100.0 * labels.count("NON_RELEVANT") / n
        mean = sum(scores) / n
        report["strategies"][key] = {
            "label": label,
            "relevant_pct": round(rel, 1),
            "partial_pct": round(part, 1),
            "non_relevant_pct": round(non, 1),
            "mean_score": round(mean, 4),
        }
        print(f"{label:<34} | {rel:<12.1f} | {part:<12.1f} | {non:<12.1f} | {mean:.4f}")
        if key != "hype" and mean > best_score:
            best_score = mean
            best_name = key

    report["selected_prompt"] = best_name
    report["note"] = (
        "The hype/overclaim prompt is included as a negative control so one strategy is expected to lose. "
        "The production default is the best non-hype prompt (ops or compliance)."
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "rag_eval.json").write_text(json.dumps(report, indent=2))
    print("-" * 88)
    print(f"SELECTED DEFAULT PROMPT: {STRATEGIES[best_name]} ({best_name})")
    print(f"Wrote {RESULTS_DIR / 'rag_eval.json'}")
    print("=" * 88)
    return report


if __name__ == "__main__":
    run_eval()
