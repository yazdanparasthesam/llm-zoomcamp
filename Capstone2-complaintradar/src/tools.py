"""Agent tools for ComplaintRadar (bonus: RAG + tools)."""

from collections import Counter


def lookup_complaint(engine, complaint_id):
    """Return the parent complaint chunks for a CFPB complaint_id."""
    cid = str(complaint_id).replace("CFPB-", "").strip()
    hits = [c for c in engine.chunks if str(c.get("complaint_id")) == cid]
    if not hits:
        return {"found": False, "complaint_id": cid, "chunks": []}
    return {
        "found": True,
        "complaint_id": cid,
        "doc_id": hits[0]["doc_id"],
        "company": hits[0].get("company"),
        "product": hits[0].get("product"),
        "issue": hits[0].get("issue"),
        "chunks": hits,
    }


def theme_breakdown(engine, company_key=None, product=None, top_n=8):
    """Count issues in the local index, optionally filtered."""
    rows = engine.chunks
    if company_key:
        rows = [c for c in rows if c.get("company_key") == company_key]
    if product:
        rows = [c for c in rows if c.get("product") == product]
    # count unique parent docs per issue
    seen = set()
    issues = []
    companies = []
    products = []
    for c in rows:
        if c["doc_id"] in seen:
            continue
        seen.add(c["doc_id"])
        issues.append(c.get("issue") or "Unknown")
        companies.append(c.get("company") or "Unknown")
        products.append(c.get("product") or "Unknown")
    return {
        "n_complaints": len(seen),
        "top_issues": Counter(issues).most_common(top_n),
        "top_companies": Counter(companies).most_common(top_n),
        "top_products": Counter(products).most_common(top_n),
        "filters": {"company_key": company_key, "product": product},
    }


def similar_cases(engine, query, top_k=5, company_key=None, product=None):
    """Hybrid+rerank retrieval exposed as a tool."""
    results = engine.search(
        query,
        top_k=top_k,
        mode="hybrid_rerank",
        filter_company=company_key,
        filter_product=product,
        rewrite=True,
    )
    return [
        {
            "doc_id": c["doc_id"],
            "chunk_id": c["chunk_id"],
            "company": c.get("company"),
            "product": c.get("product"),
            "issue": c.get("issue"),
            "score": round(float(score), 4),
            "snippet": (c.get("text") or "")[:280],
        }
        for c, score in results
    ]


TOOL_SPEC = [
    {
        "name": "lookup_complaint",
        "description": "Fetch one CFPB complaint by numeric complaint_id.",
        "args": ["complaint_id"],
    },
    {
        "name": "theme_breakdown",
        "description": "Count issues / companies / products in the local CFPB index.",
        "args": ["company_key", "product"],
    },
    {
        "name": "similar_cases",
        "description": "Find similar consumer narratives for a free-text theme.",
        "args": ["query", "company_key", "product"],
    },
]
