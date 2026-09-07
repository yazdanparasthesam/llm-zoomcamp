# TripPilot — Live demo user guide

[**Open TripPilot**](https://tripilot-chatbot.streamlit.app/) · [**Watch the demo**](https://github.com/user-attachments/assets/4670016d-9b90-420c-920c-f12700e65f1a)

TripPilot helps explore hotel recommendations, flight and city-cost information, itineraries, and relocation checklists. It combines hotel-review retrieval with planning tools and shows the evidence supporting its suggestions.

The public demo runs in a browser. **Visitors do not need an Azure subscription, an API key, Docker, or a local installation.** The interface is in English.

## 1. Set the trip parameters

Open the live demo and use the sidebar:

| Setting | What to choose |
|---|---|
| **Origin city** | The city the trip starts from |
| **Destination city** | The city to explore or relocate to |
| **Month** | The intended travel month for seasonal guidance |
| **Trip length (days)** | The requested duration |
| **Budget for flights (EUR)** | The flight-price limit, **not the total trip budget** |
| **Travel style** | Budget, midrange, or luxury |

Keep **Enable agent tools** checked to include supported flight, cost, seasonal, and relocation information. The recommended retrieval setting is `hybrid_rerank`; it combines text and vector retrieval with re-ranking.

Use `travel_planner` for a trip or `relocation_advisor` for relocation questions. `hype_luxury` is an evaluation-only negative control, not a recommended planning mode.

## 2. Ask a question

Review the request text so it agrees with the sidebar settings, then click **Ask TripPilot**.

For example, select Amsterdam → Barcelona, June, 3 days, a EUR 400 flight budget, and midrange travel style. Then ask:

> Plan a 3-day trip from Amsterdam to Barcelona in June. My flight budget is EUR 400 and I prefer a midrange stay. Which hotel would you recommend, and what review evidence supports it?

For relocation, select a destination and the `relocation_advisor` prompt strategy, then ask about living costs, a temporary hotel stay, and practical relocation considerations.

## 3. Read the answer and its evidence

The response contains several useful sections:

- **Answer:** the recommendation and available planning facts.
- **Structured itinerary:** the hotel pick, flight options when available, day-plan entries, estimated costs, and applicable relocation steps.
- **Citations:** expand the review-chunk panel to inspect the retrieved text. Identifiers such as `REV-00037_1` refer to evidence in the committed review dataset; they are not booking links.
- **Agent tool trace:** expand it to see which tools were called and what they returned.
- **Model and Judge:** show the response mode and its relevance assessment.

Check that the cited hotel and destination match the request. A relevance label is not a guarantee that every travel fact is correct or current.

### Understand the model mode

When the app displays **`offline-mock`** or **offline mock mode**, the answer is produced by a deterministic, evidence-based composer using committed data—not by a live LLM call. Its relevance judgment uses a heuristic.

If a live model is configured by the service operator, the displayed model identifies that provider/model. Visitors do not need to enter their own API credentials to use the hosted interface.

### Understand the estimates

- A result marked **`snapshot`** is example data from the committed dataset, not a current bookable flight offer.
- The flight budget is separate from the displayed overall trip-cost estimate.
- Seasonal guidance is not a live weather forecast.
- The current structured itinerary displays **up to five day-plan entries**, even when a longer trip is selected. Verify the displayed coverage rather than assuming every requested day has a detailed plan.
- Review snippets and cost tables have limited coverage. If evidence is missing or does not match the intended city, try a destination covered by the dataset or make the question more specific.

TripPilot does not make bookings or purchases. Check current prices, availability, and official visa/entry requirements before making travel or relocation decisions.

## 4. Explore photo-inspired planning and audio

### Photo-inspired destination suggestions

Open the photo-planning section, choose a JPG or PNG, and inspect the available suggestions.

If live vision is unavailable, select the photo's vibe tags manually—for example **beach**, **food**, **historic**, or **museums**. In offline mode, adding a photo alone does not perform AI image analysis. Select one of the suggested cities in the destination sidebar before requesting a plan.

### Audio briefings

Open **Multimodal: destination audio briefings**, select an available briefing, and use its playback controls. The project includes prerecorded destination briefings and [text transcripts](../data/transcripts.txt) as a reading alternative.

## 5. Leave feedback

After reviewing a response, use its **thumbs-up or thumbs-down** control. The confirmation applies to the displayed conversation. Rate the answer based on its usefulness and evidence; do not treat the Judge label as a substitute for that review.

## 6. Use the Monitoring and Evaluation tabs

**Monitoring** summarizes recorded activity, including query count, average latency, feedback totals, relevance labels, destinations, and a token-cost estimate. Aggregates can include activity from other demo visitors. The estimate is not a charge to the visitor or an Azure credit balance.

The hosted demo uses a lightweight telemetry backend; local files and sessions should be treated as temporary. Counts can reset when the service restarts or is redeployed. The separate six-panel Grafana dashboard belongs to the project's PostgreSQL deployment, not an automatically created service on Streamlit Community Cloud.

**Evaluation** displays the project's saved retrieval and prompt-strategy evaluation results. These are offline benchmark artifacts, not a new live evaluation of the current visitor's session.

## 7. Availability and privacy

- If the hosting platform displays a sleeping or starting notice, use its wake/open option if offered and allow the app to start before submitting another request.
- If a request fails, wait briefly and try again. Avoid repeated rapid submissions, which can hit service limits.
- The application records questions, answers, and feedback for monitoring. **Do not enter passwords, API keys, payment-card details, passport numbers, or other confidential information.**
- If a live model provider is configured, the request and retrieved context may be sent to that provider for processing.

For a local installation or deployment details, see the [main project README](../README.md) and [setup guide](setup.md).
