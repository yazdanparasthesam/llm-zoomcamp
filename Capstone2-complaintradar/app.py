import json

import streamlit as st

from src.config import COMPANY_DISPLAY, COMPANY_KEYS, PRODUCTS, RESULTS_DIR, get_default_search_mode
from src.db import get_monitoring_stats, init_db, log_feedback
from src.rag import ComplaintRadarRAG

st.set_page_config(
    page_title="ComplaintRadar — CFPB Complaint Intelligence",
    page_icon="📡",
    layout="wide",
)

if "copilot" not in st.session_state:
    init_db()
    st.session_state.copilot = ComplaintRadarRAG()
if "last_conv_id" not in st.session_state:
    st.session_state.last_conv_id = None
if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False

default_mode = get_default_search_mode()

st.sidebar.title("⚙️ ComplaintRadar Settings")
st.sidebar.caption("Consumer-voice intelligence — not SEC filings, not legal advice.")

company_filter = st.sidebar.selectbox(
    "Filter by company",
    ["All companies"] + [f"{COMPANY_DISPLAY[k]} ({k})" for k in COMPANY_KEYS],
)
company_val = None if company_filter == "All companies" else company_filter.split("(")[-1].replace(")", "").strip()

product_filter = st.sidebar.selectbox("Filter by product", ["All products"] + PRODUCTS)
product_val = None if product_filter == "All products" else product_filter

mode_options = ["hybrid_rerank", "hybrid", "text", "vector"]
mode_labels = {
    "hybrid_rerank": "🌟 Hybrid + Re-ranking",
    "hybrid": "🔗 Hybrid Search (BM25 + Cosine RRF)",
    "text": "📝 Text Search (BM25)",
    "vector": "🧠 Vector Search (Dense Cosine)",
}
default_idx = mode_options.index(default_mode) if default_mode in mode_options else 0
search_mode = st.sidebar.selectbox(
    f"Retrieval method (default from eval: {default_mode})",
    mode_options,
    index=default_idx,
    format_func=lambda x: mode_labels[x] + ("  ← EVAL WINNER" if x == default_mode else ""),
)

prompt_style = st.sidebar.selectbox(
    "LLM prompt strategy",
    ["ops", "compliance", "hype"],
    format_func=lambda x: {
        "ops": "📡 Ops analyst (default, cited themes + quotes)",
        "compliance": "⚖️ Compliance officer (harm + review checklist)",
        "hype": "🚫 Hype / overclaim (negative control — expected weaker)",
    }[x],
)

use_agent = st.sidebar.checkbox("Enable agent tools (lookup / themes / similar cases)", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### Try a sample question")
sample_queries = [
    "What are Wells Fargo customers furious about with overdraft or low-balance fees?",
    "What identity-theft or mixed-file problems are consumers reporting against Equifax and Experian?",
    "What went wrong with Apple Card / Goldman Sachs billing or account closures?",
    "What are Navy Federal members saying about auto loan repossession?",
    "How many mortgage complaints mention forbearance or escrow, and what are the top issues?",
    "Look up CFPB complaint details for a student-loan problem involving Navient.",
]
selected_sample = st.sidebar.selectbox("Example questions", ["-- Select a sample --"] + sample_queries)

st.title("📡 ComplaintRadar — CFPB Product & Bank Complaint Intelligence")
st.markdown(
    "Ask what **real consumers told the CFPB** about a bank or product this quarter. "
    "Answers are grounded in public complaint **narratives** with `doc_id` citations — "
    "not 10-K filings and not a generic LLM guess."
)

with st.expander("🎧 Listen to AI Audio Complaint Briefings (Multimodal RAG Bonus Feature)", expanded=False):
    st.markdown(
        "Spoken-word ops briefings synthesized from recurring **public CFPB narrative themes**. "
        "These are consumer-voice summaries, not legal findings and not nationwide statistics."
    )
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("#### 🏦 Wells Fargo")
        st.caption("Overdraft / low-balance fees & mortgage servicing")
        st.audio("data/audio/wells_fargo_briefing.mp3", format="audio/mp3")
    with a2:
        st.markdown("#### 📋 Credit bureaus")
        st.caption("Equifax, Experian, TransUnion — mixed files & ID theft")
        st.audio("data/audio/credit_bureau_briefing.mp3", format="audio/mp3")
    with a3:
        st.markdown("#### 🎓 Loans & cards")
        st.caption("Navient, Navy Federal auto, Apple Card / Goldman Sachs")
        st.audio("data/audio/student_loan_card_briefing.mp3", format="audio/mp3")
    st.caption("Regenerate with `python3 data/generate_audio.py` (requires gTTS). Transcripts: `data/audio/transcripts.txt`.")
    st.markdown("---")

tab1, tab2, tab3 = st.tabs(
    ["💬 Complaint intelligence", "📈 Monitoring & feedback", "🔬 Evaluation metrics"]
)

with tab1:
    user_query = st.text_input(
        "Ask about customer pain, a company, a product, or a complaint id:",
        value=selected_sample if selected_sample != "-- Select a sample --" else "",
    )
    if st.button("Run analysis", type="primary") and user_query:
        with st.spinner("Rewriting query, retrieving narratives, running tools, synthesizing brief..."):
            res = st.session_state.copilot.answer_question(
                question=user_query,
                filter_company=company_val,
                filter_product=product_val,
                search_mode=search_mode,
                prompt_style=prompt_style,
                log_db=True,
                use_agent=use_agent,
            )
            st.session_state.last_res = res
            st.session_state.last_conv_id = res["conversation_id"]
            st.session_state.feedback_submitted = False

    if "last_res" in st.session_state:
        res = st.session_state.last_res
        st.markdown("### 📝 Intelligence brief")
        st.info(res["answer"])

        c1, c2, c3 = st.columns(3)
        color = "🟢" if res["relevance_label"] == "RELEVANT" else (
            "🟡" if res["relevance_label"] == "PARTIALLY_RELEVANT" else "🔴"
        )
        c1.metric("LLM-as-a-Judge", f"{color} {res['relevance_label']}", f"Score: {res['relevance_score']}")
        c2.metric("Latency", f"{res['latency_ms']} ms", f"Mode: {res['search_mode']}")
        c3.metric("Conversation", f"#{res['conversation_id']}", f"{res.get('company')} / {res.get('product')}")

        if res.get("agent"):
            with st.expander("🛠️ Agent tool trace", expanded=False):
                st.json(res["agent"])

        with st.expander("📚 Cited CFPB narratives (doc_id + chunk_id)", expanded=False):
            for i, chunk in enumerate(res["chunks"]):
                st.markdown(
                    f"**[{i+1}] `{chunk['doc_id']}` | `{chunk['chunk_id']}` | "
                    f"{chunk.get('company')} — {chunk.get('product')} — {chunk.get('issue')}**"
                )
                st.caption(chunk.get("title", ""))
                st.markdown(f"> *{chunk.get('text','')}*")
                st.markdown("---")

        st.markdown("### Was this brief useful for ops / compliance?")
        fb1, fb2, _sp = st.columns([1, 1, 8])
        if not st.session_state.feedback_submitted:
            with fb1:
                if st.button("👍 Yes (+1)"):
                    if st.session_state.last_conv_id:
                        log_feedback(st.session_state.last_conv_id, 1, "thumbs up")
                        st.session_state.feedback_submitted = True
                        st.success("Feedback logged.")
            with fb2:
                if st.button("👎 No (-1)"):
                    if st.session_state.last_conv_id:
                        log_feedback(st.session_state.last_conv_id, -1, "thumbs down")
                        st.session_state.feedback_submitted = True
                        st.warning("Feedback logged.")
        else:
            st.write("✅ Feedback already submitted for this response.")

with tab2:
    st.subheader("Live monitoring")
    stats = get_monitoring_stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total logged queries", stats["total_queries"])
    m2.metric("Avg latency", f"{stats['avg_latency']} ms")
    m3.metric("Avg relevance", f"{stats['avg_relevance_percent']}%")
    m4.metric("Feedback +1 / -1", f"{stats['positive_feedback']} / {stats['negative_feedback']}")
    st.markdown("#### Relevance distribution")
    st.json(stats["relevance_distribution"])
    st.markdown("#### Queries by company")
    st.json(stats["company_counts"])
    st.markdown("#### Queries by product")
    st.json(stats["product_counts"])
    st.info("With Docker Compose, the 6-chart Grafana board is at http://localhost:3000 (admin / admin).")

with tab3:
    st.subheader("Pre-computed retrieval & RAG evaluation")
    ret_file = RESULTS_DIR / "retrieval_eval.json"
    rag_file = RESULTS_DIR / "rag_eval.json"
    sel_file = RESULTS_DIR / "selected_retriever.json"
    if sel_file.exists():
        st.markdown("#### Selected production retriever")
        st.json(json.loads(sel_file.read_text()))
    if ret_file.exists():
        st.markdown("#### Retrieval evaluation (100 questions, Hit@5 / MRR@5 + rerank ablation)")
        st.json(json.loads(ret_file.read_text()))
    else:
        st.warning("Run `make eval` to generate retrieval metrics.")
    if rag_file.exists():
        st.markdown("#### LLM evaluation (ops vs compliance vs hype negative control)")
        st.json(json.loads(rag_file.read_text()))
    else:
        st.warning("Run `make eval` to generate LLM metrics.")
