import re
import time

from src.config import COMPANY_DISPLAY, DEFAULT_MODEL, get_default_search_mode
from src.db import log_conversation
from src.llm import evaluate_relevance, generate_rag_answer
from src.search import ComplaintSearchEngine
from src.tools import lookup_complaint, similar_cases, theme_breakdown


COMPANY_ALIASES = {
    "EQUIFAX": "EQUIFAX",
    "EXPERIAN": "EXPERIAN",
    "TRANSUNION": "TRANSUNION",
    "TRANS UNION": "TRANSUNION",
    "CAPITAL ONE": "CAPITAL_ONE",
    "WELLS FARGO": "WELLS_FARGO",
    "SYNCHRONY": "SYNCHRONY",
    "BANK OF AMERICA": "BANK_OF_AMERICA",
    "BOFA": "BANK_OF_AMERICA",
    "NAVY FEDERAL": "NAVY_FEDERAL",
    "NFCU": "NAVY_FEDERAL",
    "NAVIENT": "NAVIENT",
    "APPLE CARD": "GOLDMAN_SACHS",
    "GOLDMAN": "GOLDMAN_SACHS",
    "CHASE": "JPMORGAN_CHASE",
    "JPMORGAN": "JPMORGAN_CHASE",
    "CITI": "CITIBANK",
    "CITIBANK": "CITIBANK",
    "ZELLE": "EARLY_WARNING",
    "DISCOVER": "DISCOVER",
    "AFFIRM": "AFFIRM",
}


class ComplaintRadarRAG:
    def __init__(self):
        self.search_engine = ComplaintSearchEngine()

    def _detect_company(self, question, chunks, fallback=None):
        if fallback:
            return fallback
        q = question.upper()
        for alias, key in COMPANY_ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", q):
                return key
        if chunks:
            return chunks[0].get("company_key")
        return "GENERAL"

    def _detect_product(self, question, chunks, fallback=None):
        if fallback:
            return fallback
        q = question.lower()
        mapping = {
            "credit report": "Credit reporting",
            "credit reporting": "Credit reporting",
            "credit card": "Credit card",
            "checking": "Checking or savings",
            "savings": "Checking or savings",
            "overdraft": "Checking or savings",
            "mortgage": "Mortgage",
            "foreclosure": "Mortgage",
            "escrow": "Mortgage",
            "debt collection": "Debt collection",
            "student loan": "Student loan",
            "navient": "Student loan",
            "auto loan": "Auto loan",
            "repossession": "Auto loan",
            "zelle": "Money transfer",
            "wire": "Money transfer",
            "payday": "Payday / personal loan",
            "bnpl": "Payday / personal loan",
        }
        for needle, product in mapping.items():
            if needle in q:
                return product
        if chunks:
            return chunks[0].get("product")
        return None

    def run_agent(self, question, filter_company=None, filter_product=None):
        """Lightweight tool router (RAG + tools bonus)."""
        q = question.lower()
        id_match = re.search(r"\b(\d{6,8})\b", question)
        if id_match and any(w in q for w in ["complaint", "lookup", "id", "case"]):
            return {"tool": "lookup_complaint", "result": lookup_complaint(self.search_engine, id_match.group(1))}
        if any(w in q for w in ["how many", "breakdown", "theme", "top issues", "volume", "count"]):
            company = filter_company or self._detect_company(question, [], None)
            if company == "GENERAL":
                company = None
            product = filter_product or self._detect_product(question, [], None)
            return {
                "tool": "theme_breakdown",
                "result": theme_breakdown(self.search_engine, company_key=company, product=product),
            }
        return {
            "tool": "similar_cases",
            "result": similar_cases(
                self.search_engine,
                question,
                top_k=5,
                company_key=filter_company,
                product=filter_product,
            ),
        }

    def answer_question(
        self,
        question,
        filter_company=None,
        filter_product=None,
        search_mode=None,
        prompt_style="ops",
        top_k=4,
        log_db=True,
        use_agent=False,
    ):
        start = time.time()
        mode = search_mode or get_default_search_mode()

        agent_payload = None
        if use_agent:
            agent_payload = self.run_agent(question, filter_company, filter_product)

        results = self.search_engine.search(
            query=question,
            top_k=top_k,
            mode=mode,
            filter_company=filter_company,
            filter_product=filter_product,
            rewrite=True,
        )
        chunks = [r[0] for r in results]
        answer = generate_rag_answer(question, chunks, system_prompt_type=prompt_style)

        if agent_payload and agent_payload.get("tool") == "theme_breakdown":
            stats = agent_payload["result"]
            answer = (
                f"{answer}\n\n**Index theme tool** (`theme_breakdown`): "
                f"{stats['n_complaints']} complaints in filter {stats['filters']}. "
                f"Top issues: {stats['top_issues'][:5]}"
            )
        elif agent_payload and agent_payload.get("tool") == "lookup_complaint":
            looked = agent_payload["result"]
            if looked.get("found"):
                answer = (
                    f"{answer}\n\n**Lookup tool**: loaded {looked['doc_id']} "
                    f"({looked['company']} / {looked['product']} / {looked['issue']})."
                )

        relevance_label, relevance_score = evaluate_relevance(question, answer, chunks)
        latency_ms = round((time.time() - start) * 1000, 2)
        company = self._detect_company(question, chunks, fallback=filter_company)
        product = self._detect_product(question, chunks, fallback=filter_product)

        conv_id = None
        if log_db:
            conv_id = log_conversation(
                question=question,
                answer=answer,
                model=DEFAULT_MODEL,
                latency_ms=latency_ms,
                relevance_label=relevance_label,
                relevance_score=relevance_score,
                company=COMPANY_DISPLAY.get(company, company),
                product=product,
            )

        return {
            "question": question,
            "answer": answer,
            "chunks": chunks,
            "relevance_label": relevance_label,
            "relevance_score": relevance_score,
            "latency_ms": latency_ms,
            "conversation_id": conv_id,
            "search_mode": mode,
            "prompt_style": prompt_style,
            "company": company,
            "product": product,
            "agent": agent_payload,
        }


if __name__ == "__main__":
    rag = ComplaintRadarRAG()
    q = "What are Wells Fargo customers saying about overdraft or low-balance fees?"
    res = rag.answer_question(q, use_agent=True)
    print(res["answer"][:600])
    print(res["relevance_label"], res["latency_ms"], res["company"])
