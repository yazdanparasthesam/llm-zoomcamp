"""
TripPilot agent tool belt (light agent layer).

Tools the copilot router can call; every call is recorded into a tool
trace surfaced in the Streamlit UI:

  search_flights(origin_city, dest_city, max_budget_eur)
      city -> IATA (OpenFlights extract) -> route offers
      (live Amadeus test tier when AMADEUS_API_KEY is set,
      otherwise committed snapshot rows labelled source="snapshot")
  city_budget(city, days, tier)      -> total cost estimate breakdown
  weather_season(city, month)        -> go/crowded/avoid advice
  route_lookup(origin_iata, dest_iata) -> direct connections
  hotel_evidence(query, mode)        -> top review chunks ("why this hotel")
  relocation_checklist(city, tier)   -> structured relocation plan
"""
import csv
import json
import math
import os
import random

from src import config

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
PEAK = {"June", "July", "August", "December"}

_cache = {}


def _load_json(path_key, path):
    if path_key not in _cache:
        _cache[path_key] = json.load(open(path))
    return _cache[path_key]


def city_table():
    return _load_json("cities", config.CITY_COSTS_PATH)


def get_city(city):
    for c in city_table():
        if c["city"].lower() == (city or "").strip().lower():
            return c
    return None


def airports_by_city():
    if "airports" not in _cache:
        out = {}
        with open(config.AIRPORTS_PATH, newline="") as f:
            for row in csv.DictReader(f):
                out[row["city"].lower()] = row["iata"]
        _cache["airports"] = out
    return _cache["airports"]


def routes():
    if "routes" not in _cache:
        rows = []
        with open(config.ROUTES_PATH, newline="") as f:
            for row in csv.DictReader(f):
                row["distance_km"] = int(row["distance_km"])
                row["avg_price_eur"] = float(row["avg_price_eur"])
                rows.append(row)
        _cache["routes"] = rows
    return _cache["routes"]


def hotels():
    return _load_json("hotels", config.HOTELS_PATH)


# --------------------------------------------------------------------- tools
def search_flights(origin_city, dest_city, max_budget_eur=None, month=None):
    """Rank flight options cheapest-first; live Amadeus when key present."""
    ap = airports_by_city()
    o_iata = ap.get((origin_city or "").lower())
    d_iata = ap.get((dest_city or "").lower())
    if not o_iata or not d_iata:
        return {"error": f"unknown airport for {origin_city or dest_city}",
                "options": []}

    options = []
    if config.AMADEUS_API_KEY and config.AMADEUS_API_SECRET:
        try:
            options = _amadeus_offers(o_iata, d_iata, month)
        except Exception as e:  # never break the agent on API failure
            options = []
            amadeus_err = str(e)
        else:
            amadeus_err = None
    else:
        amadeus_err = None

    if not options:
        rng = random.Random(f"{o_iata}-{d_iata}-{month or 'any'}")
        for r in routes():
            if r["origin"] == o_iata and r["dest"] == d_iata:
                factor = 1.0 if (month or "") not in PEAK else 1.35
                price = round(r["avg_price_eur"] * factor * rng.uniform(0.9, 1.1))
                options.append({
                    "iata": f"{o_iata}-{d_iata}", "airline": r["airline"],
                    "stops": int(r["stops"]), "duration_min":
                        int(r["distance_km"] / 780 * 60) + 35,
                    "price_eur": price, "source": "snapshot",
                })
        options.sort(key=lambda x: x["price_eur"])
    if max_budget_eur is not None:
        within = [o for o in options if o["price_eur"] <= max_budget_eur]
        over = [o for o in options if o["price_eur"] > max_budget_eur]
        options = within + over[:1]  # keep one out-of-budget for contrast
    out = {"origin": origin_city, "destination": dest_city,
           "origin_iata": o_iata, "dest_iata": d_iata,
           "budget_eur": max_budget_eur, "options": options[:4],
           "source": options[0]["source"] if options else "none"}
    if amadeus_err:
        out["live_api_error"] = amadeus_err
    return out


def _amadeus_offers(o_iata, d_iata, month):
    import urllib.parse
    import urllib.request

    token_req = urllib.request.Request(
        f"{config.AMADEUS_BASE}/v1/security/oauth2/token",
        data=urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": config.AMADEUS_API_KEY,
            "client_secret": config.AMADEUS_API_SECRET}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    token = json.load(urllib.request.urlopen(token_req, timeout=10))["access_token"]
    month_num = (MONTHS.index(month) + 1) if month in MONTHS else 6
    url = (f"{config.AMADEUS_BASE}/v2/shopping/flight-offers?"
           f"originLocationCode={o_iata}&destinationLocationCode={d_iata}"
           f"&departureDate=2026-{month_num:02d}-15&adults=1&max=3")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    data = json.load(urllib.request.urlopen(req, timeout=15))
    out = []
    for offer in data.get("data", []):
        seg = offer["itineraries"][0]["segments"]
        out.append({
            "iata": f"{o_iata}-{d_iata}",
            "airline": seg[0]["carrierCode"], "stops": len(seg) - 1,
            "duration_min": sum(1 for _ in seg) * 0 or
            int(seg[-1].get("duration", "PT2H").replace("PT", "")
                .replace("H", "").replace("M", "")[:2] or 120),
            "price_eur": round(float(offer["price"]["grandTotal"])),
            "source": "amadeus-live",
        })
    out.sort(key=lambda x: x["price_eur"])
    return out


def city_budget(city, days=3, tier="midrange"):
    c = get_city(city)
    if not c:
        return {"error": f"no cost table for {city}"}
    daily = c["daily_budget_eur"].get(tier, c["daily_budget_eur"]["midrange"])
    return {
        "city": c["city"], "country": c["country"], "tier": tier, "days": days,
        "daily_eur": daily, "trip_total_eur": daily * days,
        "meal_mid_eur": c["meal_mid_eur"], "beer_eur": c["beer_eur"],
        "transit_day_eur": c["transit_day_eur"],
        "best_months": c["best_months"], "safety_index": c["safety_index"],
    }


def weather_season(city, month=None):
    c = get_city(city)
    if not c:
        return {"error": f"no season table for {city}"}
    best = c["best_months"]
    short = {"Jan": "Jan", "Feb": "Feb", "Mar": "Mar", "Apr": "Apr",
             "May": "May", "Jun": "Jun", "Jul": "Jul", "Aug": "Aug",
             "Sep": "Sep", "Oct": "Oct", "Nov": "Nov", "Dec": "Dec"}
    advice = "good"
    if month:
        m3 = month[:3]
        if m3 in best:
            advice = "crowded-peak" if month in PEAK else "good"
        else:
            advice = "off-season"
    return {"city": c["city"], "month": month, "best_months": best,
            "verdict": advice}


def route_lookup(origin_city, dest_city):
    ap = airports_by_city()
    o, d = ap.get((origin_city or "").lower()), ap.get((dest_city or "").lower())
    for r in routes():
        if r["origin"] == o and r["dest"] == d:
            return {"connection": f"{o}-{d}", "airline": r["airline"],
                    "stops": int(r["stops"]), "distance_km": r["distance_km"],
                    "typical_price_eur": r["avg_price_eur"]}
    return {"connection": f"{o}-{d}", "error": "no direct route in snapshot"}


def hotel_evidence(query, mode="text", k=5, filters=None):
    from src import search as search_mod
    return search_mod.search(query, mode=mode, k=k, filters=filters)


def relocation_checklist(city, tier="midrange"):
    c = get_city(city)
    if not c:
        return {"error": f"no relocation data for {city}"}
    monthly_rent = round(c["daily_budget_eur"][tier] * 30 * 0.45)
    return {
        "city": c["city"], "tier": tier,
        "estimated_monthly_rent_eur": monthly_rent,
        "transit_monthly_eur": round(c["transit_day_eur"] * 30 * 0.55, 1),
        "safety_index": c["safety_index"],
        "checklist": [
            f"Secure housing in {c['city']} (budget ~EUR {monthly_rent}/month for {tier})",
            "Register local address / residence permit within 14 days",
            f"Buy a monthly transit pass (~EUR {round(c['transit_day_eur'] * 30 * 0.55, 1)})",
            "Open a local bank account + get a local SIM",
            "Register with national health insurance / find a GP",
            f"Scout neighborhoods near top-rated hotels (see review evidence)",
        ],
    }


# ------------------------------------------------------------- tool routing
def plan_tool_calls(question, entities):
    """Deterministic agent router -> ordered tool calls with arguments."""
    calls = []
    dest = entities.get("destination")
    origin = entities.get("origin")
    budget = entities.get("budget_eur")
    days = entities.get("days", 3)
    month = entities.get("month")
    tier = entities.get("tier", "midrange")
    q = question.lower()

    if origin and dest and any(w in q for w in
                               ("fly", "flight", "travel from", "get to",
                                "trip", "itinerary", "plan")):
        calls.append(("search_flights",
                      {"origin_city": origin, "dest_city": dest,
                       "max_budget_eur": budget, "month": month}))
    if dest and ("relocat" in q or "move to" in q):
        calls.append(("relocation_checklist", {"city": dest, "tier": tier}))
    if dest and any(w in q for w in ("budget", "cost", "how much", "cheap",
                                     "expensive", "afford")):
        calls.append(("city_budget",
                      {"city": dest, "days": days, "tier": tier}))
    if dest and month:
        calls.append(("weather_season", {"city": dest, "month": month}))
    if origin and dest and "route" in q:
        calls.append(("route_lookup",
                      {"origin_city": origin, "dest_city": dest}))
    return calls


def run_tools(calls):
    trace, artifacts = [], {}
    for name, args in calls:
        fn = globals()[name]
        result = fn(**args)
        trace.append({"tool": name, "arguments": args, "ok": "error" not in result})
        artifacts[name] = result
    return trace, artifacts
