"""
TripPilot — Streamlit interface (Interface rubric: 2/2).

Tab 1  🧭 Trip Copilot      — agent form + free-text request, tool trace,
                              cited answers, structured itinerary, feedback
Tab 2  📈 Monitoring         — live telemetry from Postgres/SQLite
Tab 3  🔬 Evaluation         — retrieval + RAG judge results, selected retriever
Extras 🎧 audio briefings (multimodal), 📷 photo -> destination vibe (vision)
"""
import json
import os

import streamlit as st

from src import config, db, llm, rag, search as search_mod

st.set_page_config(page_title="TripPilot — Trip & Relocation Copilot",
                   page_icon="🧭", layout="wide")

AUDIO_DIR = os.path.join(config.DATA_DIR, "audio")
AUDIO_FILES = [
    ("Paris vs Lyon — food-focused city break", "paris_vs_lyon_briefing.mp3"),
    ("Barcelona — beach + city break", "barcelona_beach_city_break.mp3"),
    ("Eastern Europe value circuit", "eastern_europe_value_briefing.mp3"),
]


@st.cache_resource
def bootstrap():
    db.init_db()
    search_mod.get_index()
    return search_mod.selected_default_mode()


DEFAULT_MODE = bootstrap()

st.title("🧭 TripPilot — Trip & Relocation Copilot")
st.caption("Agentic RAG over hotel guest reviews + flight/cost tools · "
           "LLM Zoomcamp Capstone 3 · "
           f"LLM: {'🟢 Groq live' if llm.live_available() else '🟡 offline mock mode'}")

tab_copilot, tab_monitor, tab_eval = st.tabs(
    ["🧭 Trip Copilot", "📈 Monitoring", "🔬 Evaluation"])

# ================================================================== COPILOT ==
with tab_copilot:
    with st.sidebar:
        st.header("Trip parameters")
        cities = sorted({h["city"] for h in
                         json.load(open(config.HOTELS_PATH))} |
                        {"New York"})
        origin = st.selectbox("Origin city", cities, index=0)
        destination = st.selectbox("Destination city",
                                   cities, index=cities.index("Barcelona"))
        month = st.selectbox("Month", ["(any)"] + llm_months
                             if (llm_months := ["January", "February", "March",
                                                 "April", "May", "June", "July",
                                                 "August", "September", "October",
                                                 "November", "December"]) else [])
        days = st.slider("Trip length (days)", 1, 10, 3)
        budget = st.number_input("Budget for flights (EUR)", 0, 5000, 400, 25)
        tier = st.selectbox("Travel style", ["budget", "midrange", "luxury"], 1)
        st.divider()
        mode = st.selectbox(
            "Search mode",
            ["text", "hybrid_rerank", "hybrid", "vector"],
            index=["text", "hybrid_rerank", "hybrid", "vector"].index(DEFAULT_MODE),
            help="Default = winner of evaluation_results/selected_retriever.json")
        style = st.selectbox(
            "Prompt strategy",
            ["travel_planner", "relocation_advisor", "hype_luxury"],
            help="hype_luxury is the negative control from RAG evaluation")
        use_tools = st.checkbox("Enable agent tools", True,
                                help="search_flights / city_budget / "
                                     "weather_season / relocation_checklist")

    # ------------------------------------------------------- photo -> vibes
    with st.expander("📷 Multimodal: plan a trip from a PHOTO (vision LLM)"):
        photo = st.file_uploader("Upload a destination photo",
                                 type=["jpg", "jpeg", "png"])
        manual_vibes = st.multiselect(
            "…or pick the vibes in your photo (offline mode)",
            config.VIBE_KEYWORDS)
        photo_vibes, photo_cities = [], []
        if photo is not None and llm.live_available():
            try:
                desc = llm.describe_photo(photo.getvalue(), photo.name)
                photo_vibes = desc.get("vibe", [])
                photo_cities = desc.get("cities", [])
                st.info(f"Vision read: {desc.get('scene', '')} — vibes: "
                        f"{', '.join(photo_vibes)}")
            except Exception as e:
                st.warning(f"Vision call failed ({e}); use manual vibes.")
        elif photo is not None:
            st.warning("Offline mode: vision LLM unavailable — pick vibes "
                       "manually above.")
        if manual_vibes:
            photo_vibes = manual_vibes
        if photo_vibes and not photo_cities:
            photo_cities = llm.cities_for_vibes(photo_vibes)
        if photo_cities:
            st.success(f"Suggested destinations: {', '.join(photo_cities)}")
            st.caption("Pick one as Destination in the sidebar, then ask below.")

    default_q = (f"Plan a {days}-day trip from {origin} to {destination} "
                 f"in {month if month != '(any)' else 'June'} for a {budget} EUR "
                 "budget — which hotel and why?")
    question = st.text_area("Your travel request", value=default_q, height=90)

    if st.button("🚀 Ask TripPilot", type="primary"):
        overrides = {"origin": origin, "destination": destination,
                     "budget_eur": int(budget), "days": days, "tier": tier}
        if month != "(any)":
            overrides["month"] = month
        with st.spinner("Agent at work…"):
            rec = rag.run_agent(question, mode=mode, style=style,
                                overrides=overrides, use_tools=use_tools,
                                photo_used=bool(photo_vibes))
        st.session_state["last"] = rec

    if "last" in st.session_state:
        rec = st.session_state["last"]
        badge = {"RELEVANT": "🟢", "PARTIALLY_RELEVANT": "🟡",
                 "NON_RELEVANT": "🔴"}.get(rec["relevance"], "⚪")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Judge", f"{badge} {rec['relevance']}")
        c2.metric("Latency", f"{rec['response_time_ms']} ms")
        c3.metric("Model", rec["model"].split(":")[-1])
        c4.metric("Conversation", f"#{rec['conversation_id']}")
        if rec.get("rewritten_query") and rec["rewritten_query"] != rec["question"]:
            st.caption(f"🔀 Rewritten query: {rec['rewritten_query']}")

        st.markdown("### 🗨️ Answer")
        st.markdown(rec["answer"])
        st.caption(f"Judge: {rec['relevance_explanation']}"
                   + (" (offline heuristic)" if rec.get("judge_mock") else ""))

        it = rec["itinerary"]
        st.markdown("### 🗺️ Structured itinerary")
        col_a, col_b = st.columns(2)
        with col_a:
            if it["flights"]:
                st.markdown("**Flights**")
                for f in it["flights"]:
                    st.write(f"✈️ {f['route']} · {f['airline']} · "
                             f"EUR {f['price_eur']} · {f['stops']} stops · "
                             f"{f['duration_min']//60}h{f['duration_min']%60:02d}m "
                             f"· *{f['source']}*")
            if it["hotel"]:
                h = it["hotel"]
                st.markdown(f"**Why this hotel — {h['hotel_name']} "
                            f"({h['city']}, ⭐ {h['avg_score']})**")
                st.write(h["why"])
        with col_b:
            if it["day_plans"]:
                st.markdown("**Day plan**")
                for d in it["day_plans"]:
                    st.write(f"**Day {d['day']} — {d['theme']}**: "
                             f"{d['morning']} / {d['afternoon']} / {d['evening']}")
        if it["cost_summary_eur"]:
            st.info(f"💶 Estimated trip cost: **EUR {it['cost_summary_eur']}** "
                    f"(style: {it['tier']}, budget limit: "
                    f"{it['total_budget_eur'] or '—'} EUR)")
        if it["relocation_steps"]:
            st.markdown("**📦 Relocation checklist**")
            for s in it["relocation_steps"]:
                st.write("•", s)

        with st.expander(f"🔧 Agent tool trace ({len(rec['tools_used'])} calls)"):
            st.json(rec["tool_trace"])
        with st.expander(f"📚 Citations ({len(rec['citations'])} review chunks)"):
            for c in rec["citations"]:
                st.markdown(f"**{c['chunk_id']}** · {c['hotel_name']} "
                            f"({c['city']}) · {c['section']} · score {c['score']}")
                st.caption(c["text"])

        fb1, fb2, _ = st.columns([1, 1, 6])
        key = f"fb_{rec['conversation_id']}"
        if fb1.button("👍", key=key + "_up"):
            db.save_feedback(rec["conversation_id"], 1)
            st.toast("Feedback logged: +1")
        if fb2.button("👎", key=key + "_down"):
            db.save_feedback(rec["conversation_id"], -1)
            st.toast("Feedback logged: -1")

    # ------------------------------------------------------- audio briefings
    st.divider()
    with st.expander("🎧 Multimodal: destination audio briefings"):
        st.caption("Generated with gTTS from the same evidence base "
                   "(transcripts: data/transcripts.txt).")
        found = False
        for title, fname in AUDIO_FILES:
            path = os.path.join(AUDIO_DIR, fname)
            if os.path.exists(path):
                found = True
                st.markdown(f"**{title}**")
                st.audio(path)
        if not found:
            st.info("Audio files not generated yet — run "
                    "`python3 data/generate_audio.py` (needs network + gtts). "
                    "Transcripts are committed in data/transcripts.txt.")

# ================================================================ MONITORING ==
with tab_monitor:
    st.subheader("Live telemetry")
    t = db.telemetry_summary()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total queries", t["total_queries"])
    m2.metric("Avg latency (ms)", t["avg_latency_ms"])
    m3.metric("Feedback 👍/👎", f"{t['feedback_up']} / {t['feedback_down']}")
    m4.metric("LLM cost (USD)", f"{t['total_cost_usd']:.5f}")
    st.caption(f"Telemetry backend: **{t['backend']}** "
               "(PostgreSQL in docker-compose, SQLite offline)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Judge relevance distribution**")
        if t["relevance"]:
            st.bar_chart(t["relevance"])
        else:
            st.info("No queries logged yet.")
    with c2:
        st.markdown("**Queries by destination city**")
        if t["cities"]:
            st.bar_chart(t["cities"])
        else:
            st.info("No city telemetry yet.")
    st.markdown("**Grafana** — 6-panel dashboard auto-provisioned in "
                "docker-compose at :3000 (admin/admin): total queries, avg "
                "latency gauge, relevance donut, feedback pie, query volume "
                "time series, queries by destination.")

# ================================================================= EVALUATION ==
with tab_eval:
    st.subheader("Retrieval evaluation (4 approaches, Module-07 dual level)")
    rp = os.path.join(config.EVAL_DIR, "retrieval_eval.json")
    if os.path.exists(rp):
        r = json.load(open(rp))
        rows = [{"approach": a, **{k: v for k, v in m.items()}}
                for a, m in r["approaches"].items()]
        st.dataframe(rows, use_container_width=True)
        sel = r.get("selected_mode")
        st.success(f"Selected production retriever: **{sel}** "
                   f"(n={r['n_questions']} ground-truth questions). "
                   "Rerank ablation: "
                   f"Δdoc MRR {r['rerank_ablation']['doc_mrr@5_delta']:+.4f}, "
                   f"Δchunk MRR {r['rerank_ablation']['chunk_mrr@5_delta']:+.4f}.")
    else:
        st.info("Run `make eval` (python3 -m src.eval_retrieval).")

    st.subheader("RAG output evaluation (LLM-as-a-Judge, 3 prompts)")
    ep = os.path.join(config.EVAL_DIR, "rag_eval.json")
    if os.path.exists(ep):
        e = json.load(open(ep))
        rows = [{"strategy": s, **m["distribution"],
                 "mean_judge_score": m["mean_judge_score"],
                 "relevant_pct": m["relevant_pct"]}
                for s, m in e["strategies"].items()]
        st.dataframe(rows, use_container_width=True)
        st.caption(f"Judge: {e['judge']} · n={e['n_questions']} questions. "
                   "hype_luxury is the intentional negative control.")
    else:
        st.info("Run `make eval` (python3 -m src.eval_rag).")
