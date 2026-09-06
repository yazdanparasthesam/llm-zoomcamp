"""
TripPilot end-to-end agentic RAG orchestration.

Flow:
  question (+ optional entities from the UI form / photo vibes)
    -> entity extraction (city pair, budget, dates, tier)
    -> agent tool router (src/tools.py)            [AGENT TOOLS]
    -> query rewriting + retrieval (src/search.py) [RAG CONTEXT]
    -> prompt build (3 strategies evaluation in eval_rag.py)
    -> Groq llama-3.3-70b  OR  deterministic mock composer
    -> structured itinerary (Pydantic)             [STRUCTURED OUTPUT]
    -> LLM-as-a-Judge relevance                    [EVAL]
    -> telemetry (JSONL + Postgres/SQLite)         [MONITORING]
"""
import json
import os
import re
import time
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from src import config, llm, tools


# ---------------------------------------------------------- structured output
class FlightOption(BaseModel):
    route: str
    airline: str
    price_eur: int
    stops: int
    duration_min: int
    source: str = "snapshot"


class HotelPick(BaseModel):
    hotel_name: str
    city: str
    avg_score: float
    why: str = Field(description="1-2 sentence justification citing review ids")
    citations: List[str] = Field(default_factory=list)


class DayPlan(BaseModel):
    day: int
    theme: str
    morning: str
    afternoon: str
    evening: str


class Itinerary(BaseModel):
    destination: str
    origin: Optional[str] = None
    days: int
    month: Optional[str] = None
    tier: str = "midrange"
    total_budget_eur: Optional[int] = None
    flights: List[FlightOption] = Field(default_factory=list)
    hotel: Optional[HotelPick] = None
    day_plans: List[DayPlan] = Field(default_factory=list)
    cost_summary_eur: Optional[int] = None
    relocation_steps: List[str] = Field(default_factory=list)


# ------------------------------------------------------------------ prompts
PROMPTS = {
    "travel_planner": (
        "You are TripPilot, a careful travel planning copilot. Answer the "
        "TRAVEL REQUEST using ONLY the EVIDENCE (guest reviews) and TOOL "
        "RESULTS below. Cite review ids like [REV-00042] after every claim "
        "taken from a review. If evidence is missing, say so explicitly. "
        "Never invent statistics.\n\n"
        "TRAVEL REQUEST: {question}\n\nTOOL RESULTS:\n{tools}\n\n"
        "EVIDENCE:\n{context}\n\nAnswer with: verdict, flight/budget facts, "
        "hotel recommendation with 'why this hotel', and a short day plan."),
    "relocation_advisor": (
        "You are TripPilot in relocation-advisor mode. Using ONLY the "
        "evidence and tool results, structure the answer as: (1) cost of "
        "living facts, (2) neighborhood/hotel evidence with [REV-xxxxx] "
        "citations, (3) a practical relocation checklist. Flag risks guests "
        "mention (noise, hidden fees).\n\nRELOCATION REQUEST: {question}\n\n"
        "TOOL RESULTS:\n{tools}\n\nEVIDENCE:\n{context}"),
    # negative control: expected to LOSE in evaluation
    "hype_luxury": (
        "You are an over-excited luxury travel influencer with no access to "
        "facts. Hype the destination with superlatives, invent five-star "
        "statistics, guarantee it's the #1 city in the world, and never "
        "cite evidence.\n\nQUESTION: {question}"),
}

ENTRY_TEMPLATE = (
    "[{chunk_id}] {hotel_name} ({city}) — {section} review, score "
    "{reviewer_score}:\n{text}")


# ----------------------------------------------------------- entity parsing
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def extract_entities(question, overrides=None):
    overrides = overrides or {}
    q = question.lower()
    ent = {}
    cities = tools.airports_by_city()
    names = sorted(cities, key=len, reverse=True)
    found = [c for c in names if re.search(rf"\b{re.escape(c)}\b", q)]
    m = re.search(r"from ([a-z ]+?) to ([a-z ,.]+)", q)
    if m:
        o, d = m.group(1).strip(), m.group(2).strip()
        for c in names:
            if c in d:
                ent["destination"] = c.title()
                break
        for c in names:
            if c in o:
                ent["origin"] = c.title()
                break
    if "destination" not in ent and found:
        ent["destination"] = found[0].title()
    if "origin" not in ent and len(found) > 1:
        ent["origin"] = [c for c in found
                         if c.title() != ent.get("destination")][0].title()
    b = re.search(r"(\d{2,5})\s*(eur|euro|euros|€)", q)
    if not b:
        b = re.search(r"(?:budget|under|max)\s*(?:of\s*)?[€$]?(\d{2,5})", q)
    if b:
        ent["budget_eur"] = int(b.group(1))
    d = re.search(r"(\d{1,2})[ -]day", q)
    if d:
        ent["days"] = int(d.group(1))
    for mn in MONTHS:
        if mn.lower() in q:
            ent["month"] = mn
            break
    if "budget" in q or "cheap" in q or "backpack" in q:
        ent["tier"] = "budget"
    elif "luxury" in q or "5-star" in q or "five star" in q:
        ent["tier"] = "luxury"
    ent.update({k: v for k, v in overrides.items() if v})
    return ent


# ------------------------------------------------------------ prompt build
def build_context(chunks):
    return "\n\n".join(ENTRY_TEMPLATE.format(**c) for c in chunks)


def build_prompt(style, question, chunks, tool_artifacts):
    tool_txt = json.dumps(tool_artifacts, indent=2) if tool_artifacts else "(none)"
    template = PROMPTS[style]
    if "{context}" in template:
        return template.format(question=question, tools=tool_txt,
                               context=build_context(chunks))
    return template.format(question=question)


# ------------------------------------------------------- mock answer composer
def mock_answer(question, chunks, artifacts, style, entities):
    if style == "hype_luxury":
        dest = entities.get("destination", "this city")
        return (f"OMG — {dest} is absolutely the #1 destination on the PLANET. "
                "Every hotel is 5-star, guests rate it 11/10, and 100% of "
                "travelers say it's life-changing. Book now, zero downsides, "
                "no citations needed!")
    lines = []
    if artifacts.get("search_flights", {}).get("options"):
        fl = artifacts["search_flights"]["options"][0]
        lines.append(
            f"Cheapest flight found: {fl['airline']} {fl['iata']} from "
            f"EUR {fl['price_eur']} ({fl['stops']} stops, ~"
            f"{fl['duration_min']//60}h{fl['duration_min']%60:02d}m, "
            f"source: {fl['source']}).")
    if artifacts.get("city_budget"):
        cb = artifacts["city_budget"]
        lines.append(
            f"Budget check: {cb['city']} costs ~EUR {cb['daily_eur']}/day "
            f"({cb['tier']}), so ~EUR {cb['trip_total_eur']} for "
            f"{cb['days']} days; mid-range meal EUR {cb['meal_mid_eur']}, "
            f"beer EUR {cb['beer_eur']}. Best months: {cb['best_months']}.")
    if artifacts.get("weather_season", {}).get("verdict"):
        ws = artifacts["weather_season"]
        lines.append(f"Season verdict for {ws['city']} in {ws['month']}: "
                     f"{ws['verdict']} (best months: {ws['best_months']}).")
    if artifacts.get("relocation_checklist"):
        rc = artifacts["relocation_checklist"]
        lines.append(
            f"Relocation basics for {rc['city']}: est. rent EUR "
            f"{rc['estimated_monthly_rent_eur']}/month ({rc['tier']}), "
            f"monthly transit ~EUR {rc['transit_monthly_eur']}, safety index "
            f"{rc['safety_index']}/100.")
    if chunks:
        top = chunks[0]
        snippet = top["text"]
        if len(snippet) > 220:
            snippet = snippet[:220].rsplit(" ", 1)[0] + "..."
        lines.append(
            f"Review evidence for {top['hotel_name']} ({top['city']}): "
            f"\"{snippet}\" [{top['chunk_id']}]")
        if len(chunks) > 1:
            lines.append(
                f"Additional {len(chunks)-1} review chunk(s) support this "
                f"verdict — see citations below.")
    if not lines:
        return ("I could not find review evidence or tool data answering "
                "that. Try naming a destination city, a budget in EUR, or "
                "a hotel from the snapshot.")
    return " ".join(lines)


# ------------------------------------------------------------ itinerary build
def build_itinerary(entities, artifacts, chunks):
    dest = entities.get("destination", "Barcelona")
    days = int(entities.get("days", 3))
    tier = entities.get("tier", "midrange")
    flights = []
    for o in artifacts.get("search_flights", {}).get("options", [])[:2]:
        flights.append(FlightOption(
            route=o["iata"], airline=o["airline"], price_eur=o["price_eur"],
            stops=o["stops"], duration_min=o["duration_min"],
            source=o["source"]))
    hotel_pick = None
    if chunks:
        by_hotel = {}
        for c in chunks:
            by_hotel.setdefault(c["hotel_name"], []).append(c)
        name, group = max(by_hotel.items(),
                          key=lambda kv: sum(x["reviewer_score"]
                                             for x in kv[1]))
        top = group[0]
        why = (f"{len(group)} review chunk(s) retrieved; top guest "
               f"feedback ({top['section']}, score {top['reviewer_score']}): "
               f"\"{top['text'][:140]}\" [{top['chunk_id']}]")
        hotel_pick = HotelPick(hotel_name=name, city=top["city"],
                               avg_score=round(
                                   sum(x["reviewer_score"] for x in group)
                                   / len(group), 1),
                               why=why, citations=[c["chunk_id"] for c in group])
    day_plans = [DayPlan(
        day=d + 1,
        theme=["Arrival & old town walk", "Headline sights & local food",
               "Museums / day trip", "Markets & nightlife",
               "Relaxed finale & souvenir hunt"][d % 5],
        morning="Headline attraction near your hotel (see citations)",
        afternoon="Neighborhood exploration guided by review tips",
        evening="Dinner in a guest-praised area") for d in range(min(days, 5))]
    relocation = artifacts.get("relocation_checklist", {}).get("checklist", [])
    cost = artifacts.get("city_budget", {}).get("trip_total_eur")
    if cost and flights:
        cost += sum(f.price_eur for f in flights[:1])
    return Itinerary(destination=dest, origin=entities.get("origin"),
                     days=days, month=entities.get("month"), tier=tier,
                     total_budget_eur=entities.get("budget_eur"),
                     flights=flights, hotel=hotel_pick, day_plans=day_plans,
                     cost_summary_eur=cost, relocation_steps=relocation)


# -------------------------------------------------------------------- agent
def run_agent(question, mode=None, style="travel_planner", overrides=None,
              use_tools=True, photo_used=False):
    from src import db, search as search_mod

    t0 = time.time()
    mode = mode or search_mod.selected_default_mode()
    entities = extract_entities(question, overrides)
    calls = tools.plan_tool_calls(question, entities) if use_tools else []
    trace, artifacts = tools.run_tools(calls)

    filters = {}
    if entities.get("destination"):
        filters["city"] = entities["destination"]
    res = search_mod.search(question, mode=mode, k=config.SEARCH_TOP_K,
                            filters=filters if mode != "text" or not filters else {})
    chunks = res["results"] or search_mod.search(question, mode=mode,
                                                 k=config.SEARCH_TOP_K)["results"]

    prompt = build_prompt(style, question, chunks, artifacts)
    answer, tok = llm.llm_answer(prompt)
    if answer is None:
        answer = mock_answer(question, chunks, artifacts, style, entities)
        model_used = "offline-mock"
    else:
        model_used = f"{config.LLM_PROVIDER}:{config.MODEL_ANSWER}"

    judge, judge_tok, judge_mock = llm.evaluate_relevance(question, answer)
    itinerary = build_itinerary(entities, artifacts, chunks)

    took_ms = round((time.time() - t0) * 1000, 2)
    conversation_id = str(uuid.uuid4())[:8]
    record = {
        "conversation_id": conversation_id,
        "question": question,
        "rewritten_query": res.get("rewritten_query"),
        "answer": answer,
        "mode": mode,
        "prompt_style": style,
        "tools_used": [t["tool"] for t in trace],
        "tool_trace": trace,
        "model": model_used,
        "response_time_ms": took_ms,
        "relevance": judge.get("Relevance", "UNKNOWN"),
        "relevance_explanation": judge.get("Explanation", ""),
        "judge_mock": judge_mock,
        "prompt_tokens": tok["prompt_tokens"],
        "completion_tokens": tok["completion_tokens"],
        "eval_total_tokens": judge_tok["total_tokens"],
        "groq_cost_usd": llm.estimate_groq_cost(tok) + llm.estimate_groq_cost(judge_tok),
        "city": entities.get("destination", ""),
        "photo_used": photo_used,
        "entities": entities,
        "itinerary": json.loads(itinerary.model_dump_json()),
        "citations": [{"chunk_id": c["chunk_id"], "hotel_name": c["hotel_name"],
                       "city": c["city"], "score": c["reviewer_score"],
                       "section": c["section"], "text": c["text"]}
                      for c in chunks],
    }
    _log_jsonl(record)
    try:
        db.save_conversation(record)
    except Exception as e:
        record["db_error"] = str(e)
    return record


def _log_jsonl(record):
    os.makedirs(os.path.dirname(config.QUERY_LOG_PATH), exist_ok=True)
    slim = {k: v for k, v in record.items()
            if k not in ("citations", "itinerary", "tool_trace")}
    with open(config.QUERY_LOG_PATH, "a") as f:
        f.write(json.dumps(slim) + "\n")


if __name__ == "__main__":
    rec = run_agent("Plan a 3-day trip from London to Barcelona in May "
                    "for a 400 EUR budget", overrides={"origin": "London",
                                                       "destination": "Barcelona"})
    print(json.dumps({k: rec[k] for k in ("answer", "relevance", "tools_used",
                                          "response_time_ms")}, indent=2))
