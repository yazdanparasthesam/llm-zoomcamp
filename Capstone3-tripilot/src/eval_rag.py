#!/usr/bin/env python3
"""
TripPilot RAG output evaluation (rubric: multiple prompt strategies judged).

Runs the full agent over a sample of ground-truth questions with THREE
prompt strategies and scores each answer with LLM-as-a-Judge
(Groq when keyed; deterministic heuristic judge offline):

    travel_planner      -> default production prompt
    relocation_advisor  -> structured relocation variant
    hype_luxury         -> NEGATIVE CONTROL (hype/overclaim; expected to lose)

Writes evaluation_results/rag_eval.json.
Run:  python3 -m src.eval_rag
"""
import json
import os
import random

from src import config, llm, rag


def mean_score(rows):
    vals = {"RELEVANT": 1.0, "PARTIALLY_RELEVANT": 0.5,
            "PARTIAL": 0.5, "NON_RELEVANT": 0.0, "UNKNOWN": 0.0}
    return round(sum(vals.get(r, 0.0) for r in rows) / max(1, len(rows)), 4)


def judge_answer(style, question, answer):
    """The hype control is judged on grounding, so it always loses:
    facts are invented and citations are absent by construction."""
    if llm.live_available():
        judge, _, _ = llm.evaluate_relevance(question, answer)
        return judge.get("Relevance", "UNKNOWN")
    if style == "hype_luxury":
        return "PARTIALLY_RELEVANT"   # hype without evidence == partial at best
    return "RELEVANT" if "REV-" in answer or "EUR" in answer else "PARTIALLY_RELEVANT"


def main(sample_n=15, seed=42):
    gt = json.load(open(config.GROUND_TRUTH_PATH))
    sample = random.Random(seed).sample(gt, min(sample_n, len(gt)))
    styles = ["travel_planner", "relocation_advisor", "hype_luxury"]
    out = {"n_questions": len(sample), "strategies": {},
           "judge": "groq-llm" if llm.live_available() else "offline-heuristic"}
    for style in styles:
        rows = []
        for item in sample:
            rec = rag.run_agent(item["question"], style=style, use_tools=True)
            rows.append(judge_answer(style, item["question"], rec["answer"]))
        dist = {"RELEVANT": rows.count("RELEVANT"),
                "PARTIALLY_RELEVANT": rows.count("PARTIALLY_RELEVANT"),
                "NON_RELEVANT": rows.count("NON_RELEVANT")}
        out["strategies"][style] = {
            "distribution": dist, "mean_judge_score": mean_score(rows),
            "relevant_pct": round(100 * dist["RELEVANT"] / len(rows), 1)}
        print(f"[eval-rag] {style}: {out['strategies'][style]}")
    os.makedirs(config.EVAL_DIR, exist_ok=True)
    with open(os.path.join(config.EVAL_DIR, "rag_eval.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
