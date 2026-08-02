import json
from pathlib import Path
from src.search import FinancialSearchEngine
from src.config import GROUND_TRUTH_PATH, RESULTS_DIR

def evaluate_retrieval():
    print(f"Loading ground-truth Q&A dataset from {GROUND_TRUTH_PATH}...")
    with open(GROUND_TRUTH_PATH, 'r') as f:
        qa_pairs = json.load(f)
        
    engine = FinancialSearchEngine()
    
    # 4 Retrieval approaches to compare (satisfies multiple retrieval approaches requirement)
    methods = [
        ("Text Search (BM25)", "text"),
        ("Vector Search (Cosine)", "vector"),
        ("Hybrid Search (RRF)", "hybrid"),
        ("Hybrid + Re-ranking (Best Practice)", "hybrid_rerank")
    ]
    
    results_summary = {}
    
    print("\n=========================================================================================")
    print("                      FINDOCS COPILOT — RETRIEVAL EVALUATION                             ")
    print("=========================================================================================")
    print(f"{'Method':<32} | {'Doc Hit@5':<10} | {'Doc MRR@5':<10} | {'Chunk Hit@5':<12} | {'Chunk MRR@5':<11}")
    print("-" * 89)
    
    for name, mode in methods:
        doc_hits = 0
        doc_mrr_sum = 0.0
        chunk_hits = 0
        chunk_mrr_sum = 0.0
        
        for qa in qa_pairs:
            query = qa["question"]
            gt_doc_id = qa["ground_truth_doc_id"]
            gt_chunk_id = qa["ground_truth_chunk_id"]
            
            # Retrieve top-5 candidates
            candidates = engine.search(query, top_k=5, mode=mode, rewrite=True)
            retrieved_doc_ids = [c[0]["doc_id"] for c in candidates]
            retrieved_chunk_ids = [c[0]["chunk_id"] for c in candidates]
            
            # 1. Document-level Hit Rate and MRR (Module 07 requirement)
            if gt_doc_id in retrieved_doc_ids:
                doc_hits += 1
                rank = retrieved_doc_ids.index(gt_doc_id) + 1
                doc_mrr_sum += 1.0 / rank
                
            # 2. Chunk-level Hit Rate and MRR (Module 07 requirement)
            if gt_chunk_id in retrieved_chunk_ids:
                chunk_hits += 1
                rank = retrieved_chunk_ids.index(gt_chunk_id) + 1
                chunk_mrr_sum += 1.0 / rank
                
        n = len(qa_pairs)
        doc_hit_rate = round(doc_hits / n, 4)
        doc_mrr = round(doc_mrr_sum / n, 4)
        chunk_hit_rate = round(chunk_hits / n, 4)
        chunk_mrr = round(chunk_mrr_sum / n, 4)
        
        results_summary[name] = {
            "doc_hit_rate@5": doc_hit_rate,
            "doc_mrr@5": doc_mrr,
            "chunk_hit_rate@5": chunk_hit_rate,
            "chunk_mrr@5": chunk_mrr
        }
        
        print(f"{name:<32} | {doc_hit_rate:<10.4f} | {doc_mrr:<10.4f} | {chunk_hit_rate:<12.4f} | {chunk_mrr:<11.4f}")
        
    print("=========================================================================================\n")
    
    # Save evaluation results to file
    RESULTS_DIR.mkdir(exist_ok=True)
    output_path = RESULTS_DIR / "retrieval_eval.json"
    with open(output_path, 'w') as f:
        json.dump(results_summary, f, indent=2)
    print(f"Retrieval evaluation results saved to {output_path}")
    return results_summary

if __name__ == "__main__":
    evaluate_retrieval()
