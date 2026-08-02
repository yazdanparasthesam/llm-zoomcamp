import streamlit as st
import time
import json
from src.rag import FinDocsCopilotRAG
from src.db import get_monitoring_stats, log_feedback
from src.config import RESULTS_DIR

st.set_page_config(
    page_title="FinDocs Copilot — SEC & Earnings AI Analyst",
    page_icon="📊",
    layout="wide"
)

# Initialize RAG backend in session state
if "copilot" not in st.session_state:
    st.session_state.copilot = FinDocsCopilotRAG()
if "last_conv_id" not in st.session_state:
    st.session_state.last_conv_id = None
if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False

# Sidebar configuration
st.sidebar.title("⚙️ FinDocs Copilot Settings")
st.sidebar.markdown("Configure hybrid search, re-ranking, and financial prompt strategies.")

company_filter = st.sidebar.selectbox(
    "Filter by Company / Ticker",
    ["All Companies", "NVIDIA (NVDA)", "Apple (AAPL)", "Microsoft (MSFT)", "Tesla (TSLA)", "Alphabet (GOOGL)"]
)
ticker_val = None
if company_filter != "All Companies":
    ticker_val = company_filter.split("(")[-1].replace(")", "").strip()

search_mode = st.sidebar.selectbox(
    "Retrieval Method (Module 02 / Best Practices)",
    ["hybrid_rerank", "hybrid", "text", "vector"],
    format_func=lambda x: {
        "hybrid_rerank": "🌟 Hybrid + Re-ranking (Best Practice)",
        "hybrid": "🔗 Hybrid Search (BM25 + Cosine RRF)",
        "text": "📝 Text Search (BM25 Keyword)",
        "vector": "🧠 Vector Search (Dense Cosine)"
    }[x]
)

prompt_style = st.sidebar.selectbox(
    "LLM Prompt Strategy",
    ["analyst", "concise", "advisor"],
    format_func=lambda x: {
        "analyst": "📈 Senior Financial Analyst (Detailed + Cited)",
        "concise": "⚡ Concise Auditor (Bullet Points)",
        "advisor": "💼 Strategic Investment Advisor"
    }[x]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Try Sample Financial Queries:")
sample_queries = [
    "What U.S. export control rules impacted NVIDIA's GPU sales to China?",
    "What was Apple's Services revenue in fiscal 2024 and how many paid subscriptions did they reach?",
    "What did Satya Nadella say about Microsoft's AI revenue run rate and Azure CapEx?",
    "What is Tesla's Cybercab robotaxi target production year and expected cost?",
    "What antitrust court ruling did Alphabet face regarding Search advertising in August 2024?"
]
selected_sample = st.sidebar.selectbox("Select an example question:", ["-- Select a sample --"] + sample_queries)

# Main Application Layout
st.title("📊 FinDocs Copilot — Public Company SEC 10-K & Earnings Assistant")
st.markdown(
    "End-to-End Financial RAG Application powered by **Hybrid Search**, **Document Re-ranking**, "
    "**Query Rewriting**, **LLM-as-a-Judge Output Evaluation**, and **Multimodal Audio Executive Briefings**."
)

# Multimodal Audio Feature (Bonus Points)
with st.expander("🎧 Listen to AI Audio Executive Briefings (Multimodal RAG Bonus Feature)", expanded=False):
    st.markdown(
        "Listen to AI-synthesized spoken executive summaries of key corporate SEC filings and earnings calls "
        "generated via neural speech synthesis."
    )
    audio_col1, audio_col2, audio_col3 = st.columns(3)
    with audio_col1:
        st.markdown("#### 🟢 NVIDIA Corp. (NVDA)")
        st.caption("Export Controls & Blackwell GPU Transition")
        st.audio("data/audio/nvda_briefing.mp3", format="audio/mp3")
    with audio_col2:
        st.markdown("#### 🍏 Apple Inc. (AAPL)")
        st.caption("Services Revenue Record & EU DMA Rules")
        st.audio("data/audio/aapl_briefing.mp3", format="audio/mp3")
    with audio_col3:
        st.markdown("#### ⚡ Tesla, Inc. (TSLA)")
        st.caption("Cybercab Robotaxi Target & Megapack Margins")
        st.audio("data/audio/tsla_briefing.mp3", format="audio/mp3")
    st.markdown("---")

tab1, tab2, tab3 = st.tabs(["💬 Financial Chat & Citations", "📈 Monitoring & User Feedback", "🔬 Module Evaluation Metrics"])

with tab1:
    user_query = st.text_input(
        "Ask a financial question about SEC 10-K filings or Earnings Calls:",
        value=selected_sample if selected_sample != "-- Select a sample --" else ""
    )

    if st.button("Submit Question", type="primary") and user_query:
        with st.spinner("Retrieving SEC filings, applying hybrid re-ranking, and synthesizing analyst answer..."):
            res = st.session_state.copilot.answer_question(
                question=user_query,
                filter_ticker=ticker_val,
                search_mode=search_mode,
                prompt_style=prompt_style,
                log_db=True
            )
            st.session_state.last_res = res
            st.session_state.last_conv_id = res["conversation_id"]
            st.session_state.feedback_submitted = False

    if "last_res" in st.session_state:
        res = st.session_state.last_res
        
        # Display Assistant Response
        st.markdown("### 📝 AI Analyst Assessment")
        st.info(res["answer"])

        # Display Real-time LLM-as-a-Judge Score & Latency
        col1, col2, col3 = st.columns(3)
        with col1:
            color = "🟢" if res["relevance_label"] == "RELEVANT" else ("🟡" if res["relevance_label"] == "PARTIALLY_RELEVANT" else "🔴")
            st.metric("LLM-as-a-Judge Relevance", f"{color} {res['relevance_label']}", f"Score: {res['relevance_score']}")
        with col2:
            st.metric("Response Latency", f"{res['latency_ms']} ms", f"Mode: {res['search_mode']}")
        with col3:
            st.metric("Conversation ID (Postgres/SQLite)", f"#{res['conversation_id']}")

        # Citations Accordion
        with st.expander("📚 View Cited SEC 10-K & Earnings Call Context Chunks", expanded=False):
            for i, chunk in enumerate(res["chunks"]):
                st.markdown(
                    f"**[{i+1}] {chunk['doc_id']} | Chunk `{chunk['chunk_id']}` | "
                    f"{chunk['company']} ({chunk['ticker']}) — {chunk['section']}**"
                )
                st.caption(f"Title: {chunk['title']}")
                st.markdown(f"> *\"{chunk['text']}\"*")
                st.markdown("---")

        # User Feedback Section (Module 05 Monitoring requirement)
        st.markdown("### 🎯 Was this financial assessment helpful?")
        fb_col1, fb_col2, fb_col3 = st.columns([1, 1, 8])
        
        if not st.session_state.feedback_submitted:
            with fb_col1:
                if st.button("👍 Yes (+1)"):
                    if st.session_state.last_conv_id:
                        log_feedback(st.session_state.last_conv_id, 1, "User thumbs up")
                        st.session_state.feedback_submitted = True
                        st.success("Thank you for your feedback! Logged to database.")
            with fb_col2:
                if st.button("👎 No (-1)"):
                    if st.session_state.last_conv_id:
                        log_feedback(st.session_state.last_conv_id, -1, "User thumbs down")
                        st.session_state.feedback_submitted = True
                        st.warning("Thank you for your feedback! Logged to database.")
        else:
            st.write("✅ *Feedback already submitted for this response.*")

with tab2:
    st.subheader("📈 Live Monitoring Dashboard & Database Statistics")
    st.markdown("Real-time telemetry from PostgreSQL / SQLite logging database (Module 05 Monitoring).")
    
    stats = get_monitoring_stats()
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Total Logged Queries", stats["total_queries"])
    m_col2.metric("Avg Response Latency", f"{stats['avg_latency']} ms")
    m_col3.metric("Avg Relevance Score", f"{stats['avg_relevance_percent']}%")
    m_col4.metric("User Feedback Ratio (+1 / -1)", f"{stats['positive_feedback']} / {stats['negative_feedback']}")
    
    st.markdown("---")
    st.markdown("#### 📊 Relevance Distribution (LLM-as-a-Judge)")
    st.json(stats["relevance_distribution"])
    
    st.markdown("#### 🏢 Queries by Company Ticker")
    st.json(stats["ticker_counts"])
    
    st.info(
        "💡 **Note for Reviewers:** When running via `docker-compose up`, these metrics are also displayed "
        "graphically in the pre-provisioned Grafana dashboard at `http://localhost:3000`!"
    )

with tab3:
    st.subheader("🔬 Module 02 & 03 Pre-Computed Evaluation Results")
    st.markdown("Evaluation metrics generated across 20 ground-truth financial Q&A pairs.")
    
    ret_file = RESULTS_DIR / "retrieval_eval.json"
    rag_file = RESULTS_DIR / "rag_eval.json"
    
    if ret_file.exists():
        st.markdown("#### 1. Retrieval Evaluation (Hit Rate@5 & MRR@5 across `doc_id` and `chunk_id`)")
        with open(ret_file, 'r') as f:
            ret_data = json.load(f)
        st.json(ret_data)
    else:
        st.warning("Run `python -m src.eval_retrieval` to generate retrieval evaluation metrics.")

    if rag_file.exists():
        st.markdown("#### 2. LLM RAG Output Evaluation (LLM-as-a-Judge Relevance Distribution)")
        with open(rag_file, 'r') as f:
            rag_data = json.load(f)
        st.json(rag_data)
    else:
        st.warning("Run `python -m src.eval_rag` to generate LLM evaluation metrics.")
