# Usage Guide

## 1. The Trip Copilot tab

1. Set **origin**, **destination**, **month**, **days**, **flight budget** and
   **travel style** in the sidebar.
2. Ask in natural language, e.g.:
   - *"Plan a 3-day trip from London to Barcelona in May for a 400 EUR budget — which hotel and why?"*
   - *"Compare relocating to Prague vs Budapest on a budget tier"*
   - *"What do guests complain about at Hotel Danieli in Venice?"*
3. TripPilot shows: judge badge & latency, a **grounded answer with
   [REV-xxxxx] citations**, a **structured itinerary** (flights, "why this
   hotel", day plans, relocation checklist, cost summary), the **agent tool
   trace**, the **citation expander**, and 👍/👎 feedback buttons.

### Sidebar switches that map to the evaluation
- **Search mode**: `hybrid_rerank` (evaluation winner, default) / `text` /
  `hybrid` / `vector` — exactly the four rows in the retrieval evaluation.
- **Prompt strategy**: `travel_planner` (winner, default) /
  `relocation_advisor` / `hype_luxury` (**negative control** from RAG eval).
- **Agent tools** toggle: runs the deterministic router
  (`search_flights`, `city_budget`, `weather_season`, `route_lookup`,
  `relocation_checklist`).

## 2. Multimodal features

- 📷 **Photo → destination** (Copilot tab expander): upload a travel photo.
  With a Groq key the llama-4 vision model returns `vibe` keywords + 3
  matching cities; offline you pick the vibes manually and
  `cities_for_vibes()` maps them to destinations from the cost table.
- 🎧 **Audio destination briefings**: three pre-generated mp3 briefings
  (`data/audio/`) synthesized with gTTS from the same evidence base;
  transcripts in `data/transcripts.txt`. Regenerate with `make audio`.

## 3. Monitoring tab

Live telemetry from Postgres (compose) or SQLite (offline): total queries,
average latency, judge relevance distribution, feedback ratio, queries by
destination, accumulated LLM cost. The Grafana dashboard mirrors this with
6 provisioned panels at `:3000`.

## 4. Evaluation tab

The committed results of:
- `make eval-retrieval` → 4 approaches × doc_id/chunk_id Hit@5 & MRR@5,
  rerank and rewrite ablations, and the **selected production retriever**.
- `make eval-rag` → LLM-as-a-Judge relevance distributions for the three
  prompt strategies (incl. the hype negative control).

## CLI power-user commands

```bash
python3 -m src.search            # quick retrieval demo
python3 -m src.rag               # one full agent run (offline mock)
python3 -m src.db                # init telemetry + print summary
make generate-data               # reproducible snapshot regeneration
```
