"""
TripPilot LLM layer.

- Groq API (llama-3.3-70b-versatile answers, llama-3.1-8b-instant judge,
  llama-4-scout vision) via the OpenAI-compatible client.
- ZERO-CONFIG OFFLINE MOCK: with no GROQ_API_KEY the module deterministically
  composes answers from the *retrieved evidence* (never hallucinated
  statistics) so reviewers can run every feature without a key.
- LLM-as-a-Judge relevance classification shared by app + evaluation.
"""
import base64
import json
import os

from src import config

_PLACEHOLDER_JUDGE = {"Relevance": "RELEVANT",
                      "Explanation": "Answer grounded in retrieved evidence."}

JUDGE_TEMPLATE = """You are an expert evaluator for a travel RAG system.
Your task is to analyze the relevance of the generated answer to the given question.
Classify it as 'NON_RELEVANT', 'PARTIALLY_RELEVANT', or 'RELEVANT'.

Question: {question}
Generated Answer: {answer}

Respond in parsable JSON without code blocks:
{{
  "Relevance": "NON_RELEVANT" | "PARTIALLY_RELEVANT" | "RELEVANT",
  "Explanation": "[brief explanation]"
}}"""


def _client():
    try:
        from openai import OpenAI
    except ImportError:  # zero-config offline mode: no SDK installed
        return None, None
    try:
        if config.LLM_PROVIDER == "openai" and config.OPENAI_API_KEY:
            return OpenAI(api_key=config.OPENAI_API_KEY), config.OPENAI_MODEL
        if config.GROQ_API_KEY:
            return OpenAI(api_key=config.GROQ_API_KEY,
                          base_url=config.GROQ_BASE_URL), config.MODEL_ANSWER
    except Exception:
        return None, None
    return None, None


def live_available():
    client, _ = _client()
    return client is not None


# ------------------------------------------------------------------ answers
def llm_answer(prompt, model=None, max_tokens=900):
    client, default_model = _client()
    if client is None:
        return None, {"prompt_tokens": 0, "completion_tokens": 0,
                      "total_tokens": 0, "mock": True}
    resp = client.chat.completions.create(
        model=model or default_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2, max_tokens=max_tokens)
    usage = resp.usage
    return resp.choices[0].message.content, {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens, "mock": False}


# -------------------------------------------------------------------- judge
def evaluate_relevance(question, answer):
    """LLM-as-a-Judge; falls back to heuristic grounding check offline."""
    prompt = JUDGE_TEMPLATE.format(question=question, answer=answer)
    text, tokens = llm_answer(prompt, model=config.MODEL_JUDGE, max_tokens=200)
    if text:
        try:
            clean = text.strip().strip("`").replace("```json", "").strip()
            return json.loads(clean), tokens, False
        except Exception:
            pass
    return heuristic_judge(question, answer), {
        "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
        "mock": True}, True


def heuristic_judge(question, answer):
    """Deterministic offline judge: grounded answers are RELEVANT; answers
    whose cited context mismatches the question's city are downgraded."""
    q_cities = {c for c in _cities() if c in question.lower()}
    a_cities = {c for c in _cities() if c in answer.lower()}
    if q_cities and a_cities and not (q_cities & a_cities):
        return {"Relevance": "NON_RELEVANT",
                "Explanation": f"Answer discusses {sorted(a_cities)} "
                               f"but the question is about {sorted(q_cities)}."}
    if "no evidence" in answer.lower():
        return {"Relevance": "PARTIALLY_RELEVANT",
                "Explanation": "System found no matching review evidence."}
    return dict(_PLACEHOLDER_JUDGE)


def _cities():
    import csv
    cities = set()
    try:
        with open(config.AIRPORTS_PATH, newline="") as f:
            for row in csv.DictReader(f):
                cities.add(row["city"].lower())
    except Exception:
        pass
    return cities


# ------------------------------------------------------------------- vision
def describe_photo(image_bytes, filename="photo.jpg"):
    """Multimodal entry point: photo -> vibe keywords + suggested cities.

    Groq llama-4 vision when a key exists; otherwise raises
    VisionUnavailable so the UI switches to manual vibe selection
    (fully offline path).
    """
    client, _ = _client()
    if client is None:
        raise VisionUnavailable("no API key configured")
    b64 = base64.b64encode(image_bytes).decode()
    prompt = (
        "You are part of a travel recommendation engine. Look at this photo "
        "and reply in bare JSON with keys: vibe (3-5 of: beach, nightlife, "
        "historic, food, mountains, romance, museums, budget, luxury), "
        "scene (short description), cities (up to 3 European cities with "
        "this vibe). Example: "
        '{"vibe": ["historic", "food"], "scene": "old town square at dusk", '
        '"cities": ["Prague", "Lyon"]}')
    resp = client.chat.completions.create(
        model=config.MODEL_VISION,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}],
        temperature=0.1, max_tokens=200)
    text = resp.choices[0].message.content.strip().strip("`")
    text = text.replace("```json", "").strip()
    return json.loads(text)


class VisionUnavailable(Exception):
    pass


def cities_for_vibes(vibes):
    """Map selected vibe keywords -> ranked cities from the cost table."""
    import json as _json
    table = _json.load(open(config.CITY_COSTS_PATH))
    scored = []
    for c in table:
        overlap = len(set(vibes) & set(c["vibe"]))
        if overlap:
            scored.append((overlap, c["city"]))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [city for _, city in scored[:3]]


def estimate_groq_cost(tokens):
    """Rough llama-3.3-70b on-demand pricing $0.59/$0.79 per 1M tok."""
    return round((tokens.get("prompt_tokens", 0) * 0.59
                  + tokens.get("completion_tokens", 0) * 0.79) / 1_000_000, 6)
