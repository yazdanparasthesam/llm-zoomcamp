import json
from pathlib import Path
from src.rag import FinDocsCopilotRAG
from src.config import GROUND_TRUTH_PATH, RESULTS_DIR

def evaluate_rag():
    print(f"Loading ground-truth Q&A dataset from {GROUND_TRUTH_PATH}...")
    with open(GROUND_TRUTH_PATH, 'r') as f:
        qa_pairs = json.load(f)
        
    copilot = FinDocsCopilotRAG()
    
    prompt_styles = [
        ("Analyst Prompt (Default)", "analyst"),
        ("Concise Auditor Prompt", "concise"),
        ("Strategic Advisor Prompt", "advisor")
    ]
    
    results_summary = {}
    
    print("\n===================================================================================")
    print("                      FINDOCS COPILOT — LLM (RAG) EVALUATION                      ")
    print("===================================================================================")
    print(f"{'Prompt Strategy':<26} | {'RELEVANT (%)':<14} | {'PARTIAL (%)':<12} | {'NON_REL (%)':<12} | {'Mean Score':<10}")
    print("-" * 83)
    
    for name, p_style in prompt_styles:
        counts = {"RELEVANT": 0, "PARTIALLY_RELEVANT": 0, "NON_RELEVANT": 0}
        score_sum = 0.0
        
        for qa in qa_pairs:
            query = qa["question"]
            res = copilot.answer_question(
                question=query, 
                filter_ticker=qa["ticker"], 
                search_mode="hybrid_rerank",
                prompt_style=p_style, 
                log_db=False
            )
            label = res["relevance_label"]
            counts[label] = counts.get(label, 0) + 1
            score_sum += res["relevance_score"]
            
        n = len(qa_pairs)
        rel_pct = round((counts["RELEVANT"] / n) * 100, 1)
        part_pct = round((counts["PARTIALLY_RELEVANT"] / n) * 100, 1)
        non_pct = round((counts["NON_RELEVANT"] / n) * 100, 1)
        mean_score = round(score_sum / n, 4)
        
        results_summary[name] = {
            "relevant_percent": rel_pct,
            "partially_relevant_percent": part_pct,
            "non_relevant_percent": non_pct,
            "mean_relevance_score": mean_score,
            "counts": counts
        }
        
        print(f"{name:<26} | {rel_pct:<14.1f} | {part_pct:<12.1f} | {non_pct:<12.1f} | {mean_score:<10.4f}")
        
    print("===================================================================================\n")
    
    RESULTS_DIR.mkdir(exist_ok=True)
    output_path = RESULTS_DIR / "rag_eval.json"
    with open(output_path, 'w') as f:
        json.dump(results_summary, f, indent=2)
    print(f"RAG evaluation results saved to {output_path}")
    return results_summary

if __name__ == "__main__":
    evaluate_rag()
