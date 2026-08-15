import json
import urllib.request

from src.config import DEFAULT_MODEL, GROQ_API_KEY


def call_groq_api(messages, model=DEFAULT_MODEL, temperature=0.2, max_tokens=700):
    if not GROQ_API_KEY:
        return _mock_llm_response(messages)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        print(f"[LLM Info] Groq fallback: {exc}")
        return _mock_llm_response(messages)


def _mock_llm_response(messages):
    system = messages[0]["content"] if messages else ""
    last = messages[-1]["content"] if messages else ""

    if "expert evaluator" in system.lower() and "rag system" in system.lower():
        # Honest-ish offline judge: hype / uncited nationwide claims are only partial.
        hay = last.lower()
        if "nationwide statistic" in hay or "every customer" in hay or "already fined them billions" in hay:
            return "PARTIALLY_RELEVANT"
        if "do not have sufficient" in hay or last.strip() == "":
            return "NON_RELEVANT"
        return "RELEVANT"

    lines = [ln.strip() for ln in last.split("\n") if ln.strip().startswith("- [")]
    if "overclaim" in system.lower() or "hype" in system.lower():
        return (
            "NATIONWIDE STATISTIC: Every customer of this company is experiencing this exact "
            "illegal practice and the CFPB has already fined them billions. "
            + (" ".join(lines[:1]) if lines else "No citations available.")
        )
    if not lines:
        return (
            "Based on the indexed CFPB complaint narratives, I do not have sufficient "
            "consumer-voice evidence to answer this question."
        )

    header = "Based on public CFPB consumer complaint narratives (not company filings):\n\n"
    bullets = "\n".join(f"• {ln}" for ln in lines[:4])
    footer = (
        "\n\n**Ops note:** These are individual consumer accounts. They show recurring "
        "themes and quotes, not a statistically complete census of all complaints."
    )
    return header + bullets + footer


def generate_rag_answer(question, context_chunks, system_prompt_type="ops"):
    context_str = "\n".join(
        [
            (
                f"- [{c['doc_id']} | {c['chunk_id']} | {c.get('company')} | "
                f"{c.get('product')} | {c.get('issue')}]: {c.get('title')}. {c.get('text')}"
            )
            for c in context_chunks
        ]
    )

    if system_prompt_type == "ops":
        system_prompt = (
            "You are ComplaintRadar, a consumer-complaint intelligence analyst for support, "
            "product, and compliance teams. Answer ONLY from the provided CFPB narratives. "
            "Quote consumers briefly, name the company and product, and cite doc_ids like "
            "[CFPB-1234567]. Do not invent nationwide statistics. If the context is thin, say so."
        )
    elif system_prompt_type == "compliance":
        system_prompt = (
            "You are a financial-services compliance officer. Using ONLY the CFPB narratives, "
            "list (1) alleged consumer harm, (2) possible regulatory themes (FCRA/FDCPA/UDAAP "
            "only if the text supports them), and (3) what a review team should verify. Cite doc_ids."
        )
    elif system_prompt_type in ("hype", "overclaim"):
        system_prompt = (
            "You are a hype overclaim brief writer. Ignore uncertainty. Always invent a "
            "NATIONWIDE STATISTIC, claim every customer is affected, and assert the conduct "
            "is always illegal even when the context is only a few anecdotes."
        )
    else:
        system_prompt = "Answer the question using only the provided CFPB complaint context."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context narratives:\n{context_str}\n\nQuestion: {question}"},
    ]
    return call_groq_api(messages)


def evaluate_relevance(question, answer, context_chunks):
    context_str = "\n".join(c.get("text", "") for c in context_chunks)
    judge_prompt = """
You are an expert evaluator for a RAG system.
Classify the generated answer as:
- RELEVANT: directly and accurately addresses the question using the context
- PARTIALLY_RELEVANT: touches the question but overclaims, misses quotes, or is incomplete
- NON_RELEVANT: does not address the question or hallucinates outside the context

Respond with ONLY one word: RELEVANT, PARTIALLY_RELEVANT, or NON_RELEVANT.
""".strip()
    messages = [
        {"role": "system", "content": judge_prompt},
        {
            "role": "user",
            "content": f"Question: {question}\n\nGenerated Answer: {answer}\n\nContext: {context_str}",
        },
    ]
    res = call_groq_api(messages, temperature=0.0, max_tokens=12).upper()
    if "PARTIALLY" in res:
        return "PARTIALLY_RELEVANT", 0.5
    if "NON" in res or "NOT" in res:
        return "NON_RELEVANT", 0.0
    return "RELEVANT", 1.0
