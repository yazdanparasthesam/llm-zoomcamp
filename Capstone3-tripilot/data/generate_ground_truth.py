#!/usr/bin/env python3
"""
Generates data/ground_truth_qa.json from data/reviews_snapshot.json.

Hybrid method (mirrors the course: LLM-generated questions per document),
implemented deterministically per-id so the file is reproducible
without an LLM call:
  - for hotels with >= 15 reviews: 3 Q&A pairs (id lookup + 2 themes)
  - all other hotels:             2 Q&A pairs (id lookup + 1 theme)
Total: 24 hotels -> 60 ground-truth pairs.

Each pair: {"question_id", "question", "doc_id"} where doc_id == review_id
of the review that contains the evidence phrase.
Seeded (random.seed(123)) -> identical output everywhere.
"""
import json
import random
from collections import defaultdict

random.seed(123)

ID_TEMPLATES = [
    "What evidence do we have from review {rid} about {hotel} in {city}?",
    "Summarize review {rid} for {hotel} ({city}).",
    "Is review {rid} about {hotel} positive or negative, and why?",
]
THEME_TEMPLATES = {
    "breakfast": [
        "Is the breakfast at {hotel} ({city}) worth it according to guests?",
        "What do travelers complain or rave about regarding breakfast at {hotel} in {city}?",
    ],
    "noise": [
        "How bad is the noise at {hotel} in {city} according to reviews?",
        "Will I sleep well at {hotel} ({city}) or is street noise a problem?",
    ],
    "location": [
        "Is {hotel} in {city} well located for sightseeing?",
        "What do guests say about the location of {hotel}, {city}?",
    ],
    "staff": [
        "How is the staff and service at {hotel} in {city}?",
        "Are the reception staff at {hotel} ({city}) friendly or rude?",
    ],
    "wifi": [
        "Does the WiFi at {hotel} in {city} actually work for remote work?",
        "Any WiFi problems reported at {hotel} ({city})?",
    ],
    "room": [
        "Are the rooms at {hotel} ({city}) small, noisy or comfortable?",
        "What do reviews say about the rooms at {hotel} in {city}?",
    ],
    "value": [
        "Is {hotel} in {city} good value for money for a budget traveler?",
        "Any hidden fees or price complaints at {hotel} ({city})?",
    ],
}
THEME_KEYWORDS = {
    "breakfast": ["breakfast", "pastries", "coffee"],
    "noise": ["noise", "awake", "thin", "drilling", "heard"],
    "location": ["location", "walk", "centre", "center", "corner", "station"],
    "staff": ["staff", "reception", "concierge", "receptionist", "rude"],
    "wifi": ["wifi", "desk", "remote work"],
    "room": ["room", "mattress", "bed", "bathroom", "shower", "mould"],
    "value": ["value", "price", "fees", "euro", "worth"],
}


def text_of(r):
    return (r["positive_review"] + " " + r["negative_review"]).lower()


def pick_theme_review(candidates, theme):
    kws = THEME_KEYWORDS[theme]
    hits = [r for r in candidates if any(k in text_of(r) for k in kws)]
    return random.choice(hits) if hits else random.choice(candidates)


def main():
    hotels = {h["hotel_id"]: h for h in json.load(open("data/hotels_snapshot.json"))}
    reviews = json.load(open("data/reviews_snapshot.json"))
    by_hotel = defaultdict(list)
    for r in reviews:
        by_hotel[r["hotel_id"]].append(r)

    qa, qid = [], 1
    for hid, h in hotels.items():
        cand = by_hotel[hid]
        n_themes = 2 if len(cand) >= 15 else 1
        # 1) id-lookup pair
        r0 = random.choice(cand)
        q = random.choice(ID_TEMPLATES).format(
            rid=r0["review_id"], hotel=h["hotel_name"], city=h["city"])
        qa.append({"question_id": f"Q{qid:03d}", "question": q,
                   "doc_id": r0["review_id"]})
        qid += 1
        # 2..n) theme pairs
        themes = random.sample(list(THEME_TEMPLATES), k=n_themes + 1)
        for t in themes[:n_themes]:
            rt = pick_theme_review(cand, t)
            q = random.choice(THEME_TEMPLATES[t]).format(
                hotel=h["hotel_name"], city=h["city"])
            qa.append({"question_id": f"Q{qid:03d}", "question": q,
                       "doc_id": rt["review_id"]})
            qid += 1

    with open("data/ground_truth_qa.json", "w") as f:
        json.dump(qa, f, indent=2)
    print(f"Wrote {len(qa)} ground-truth Q&A pairs")
    print(f"3-per-hotel hotels: {[h['hotel_name'] for h in hotels.values() if len(by_hotel[h['hotel_id']]) >= 15]}")


if __name__ == "__main__":
    main()
