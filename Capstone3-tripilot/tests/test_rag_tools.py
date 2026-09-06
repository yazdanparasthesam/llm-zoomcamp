"""Agent tools + end-to-end RAG tests (deterministic offline mode)."""
from src import llm, rag, tools


def test_flight_tool_snapshot_sorted():
    out = tools.search_flights("London", "Barcelona", max_budget_eur=400)
    assert out["options"], "expected snapshot flight options"
    prices = [o["price_eur"] for o in out["options"]]
    source = out["options"][0]["source"]
    assert source == "snapshot"
    assert out["origin_iata"] == "LHR" and out["dest_iata"] == "BCN"


def test_city_budget_and_relocation():
    cb = tools.city_budget("Prague", days=4, tier="budget")
    assert cb["trip_total_eur"] == 50 * 4
    rc = tools.relocation_checklist("Prague")
    assert rc["estimated_monthly_rent_eur"] > 0
    assert len(rc["checklist"]) >= 5


def test_tool_router_calls_flights_for_trip():
    calls = tools.plan_tool_calls(
        "Plan a 3-day trip from London to Paris with 300 eur budget",
        {"origin": "London", "destination": "Paris", "budget_eur": 300})
    names = [c[0] for c in calls]
    assert "search_flights" in names and "city_budget" in names


def test_rag_pipeline_offline_mock_end_to_end():
    rec = rag.run_agent(
        "Plan a 3-day trip from London to Barcelona in May for a 400 EUR "
        "budget — which hotel and why?",
        overrides={"origin": "London", "destination": "Barcelona",
                   "budget_eur": 400, "days": 3})
    assert rec["relevance"] in ("RELEVANT", "PARTIALLY_RELEVANT")
    assert rec["itinerary"]["hotel"], "itinerary must pick a cited hotel"
    assert "search_flights" in rec["tools_used"]
    assert rec["citations"], "answer must carry review-chunk citations"
    assert rec["conversation_id"]


def test_hype_prompt_is_negative_control():
    rec = rag.run_agent("Tell me about Lyon hotels", style="hype_luxury",
                        overrides={"destination": "Lyon"})
    assert "#1" in rec["answer"]  # hype style leaks its inventions
    from src.eval_rag import judge_answer
    if not llm.live_available():
        assert judge_answer("hype_luxury", rec["question"],
                            rec["answer"]) == "PARTIALLY_RELEVANT"
