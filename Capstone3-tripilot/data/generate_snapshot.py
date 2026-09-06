#!/usr/bin/env python3
"""
TripPilot data snapshot generator (offline, deterministic).

Generates a realistic, fully reproducible clone of the Kaggle
"515K Hotel Reviews Data in Europe" schema (Hotel_Address .. Tags,
Reviewer_Score ...) so that the project requires NO Kaggle login and
NO network access. Weights mimic the real distribution:
positive reviews outnumber negatives ~2:1, leisure tags dominate,
couples are the largest segment.

Seeded with SEED=42 -> identical snapshot on every machine.
Run:  python3 data/generate_snapshot.py
"""
import csv
import json
import random

SEED = 42
random.seed(SEED)

# ---------------------------------------------------------------- hotels ----
# (hotel_name, city, country)
HOTELS = [
    ("Hotel Arena", "Amsterdam", "Netherlands"),
    ("Hotel Danieli", "Venice", "Italy"),
    ("Park Plaza Westminster", "London", "United Kingdom"),
    ("Le Marais Boutique Hotel", "Paris", "France"),
    ("Barcelo Raval", "Barcelona", "Spain"),
    ("Hotel Sacher Wien", "Vienna", "Austria"),
    ("The Hoxton Shoreditch", "London", "United Kingdom"),
    ("Riu Plaza Espana", "Madrid", "Spain"),
    ("Hotel de la Cite", "Lyon", "France"),
    ("Generator Hostel Mitte", "Berlin", "Germany"),
    ("Grand Hotel Europa", "Prague", "Czech Republic"),
    ("Hotel Ibis Gare du Nord", "Paris", "France"),
    ("Mercure Roma Centro", "Rome", "Italy"),
    ("Motel One Hauptbahnhof", "Munich", "Germany"),
    ("Hotel KB City Center", "Budapest", "Hungary"),
    ("Douro Royal Valley Hotel", "Porto", "Portugal"),
    ("Copenhagen Admiral Hotel", "Copenhagen", "Denmark"),
    ("Hotel U Prince", "Prague", "Czech Republic"),
    ("Westcord City Centre Hotel", "Amsterdam", "Netherlands"),
    ("The Telegraph Suites", "Rome", "Italy"),
    ("Hotel NH Collection Grand Sablon", "Brussels", "Belgium"),
    ("Brown Beach House", "Split", "Croatia"),
    ("Hotel Opera", "Zurich", "Switzerland"),
    ("K+K Hotel Maria Theresia", "Vienna", "Austria"),
]

CITY_LATLNG = {
    "Amsterdam": (52.3676, 4.9041), "Venice": (45.4408, 12.3155),
    "London": (51.5074, -0.1278), "Paris": (48.8566, 2.3522),
    "Barcelona": (41.3874, 2.1686), "Vienna": (48.2082, 16.3738),
    "Madrid": (40.4168, -3.7038), "Lyon": (45.7640, 4.8357),
    "Berlin": (52.5200, 13.4050), "Prague": (50.0755, 14.4378),
    "Munich": (48.1351, 11.5820), "Rome": (41.9028, 12.4964),
    "Budapest": (47.4979, 19.0402), "Porto": (41.1579, -8.6291),
    "Copenhagen": (55.6761, 12.5683), "Brussels": (50.8503, 4.3517),
    "Split": (43.5081, 16.4402), "Zurich": (47.3769, 8.5417),
}

TRIP_TYPES = ["Leisure trip", "Business trip", "Leisure trip", "Leisure trip"]
GROUPS = ["Couple", "Solo traveler", "Family with young children",
          "Group", "Family with older children", "Couple", "Couple",
          "Solo traveler"]
STAY_NIGHTS = ["Stayed 1 night", "Stayed 2 nights", "Stayed 3 nights",
               "Stayed 4 nights", "Stayed 5 nights", "Stayed 7 nights"]
NATIONALITIES = ["United Kingdom", "United States of America", "Australia",
                 "Ireland", "Netherlands", "France", "Germany", "Spain",
                 "Italy", "Canada", "Israel", "Turkey", "Switzerland",
                 "Belgium", "Poland", "Romania", "Japan", "Brazil"]

# -------------------------------------------------- review fragment pools ---
POS_OPENERS = [
    "The location was perfect, only a five minute walk to the old town.",
    "Wonderful boutique feel and spotlessly clean throughout our stay.",
    "The staff went above and beyond when our train was delayed.",
    "Breakfast had a huge spread with fresh pastries and good coffee.",
    "Our room was quiet even though the hotel is in the very centre.",
    "Great value for money compared with other options in this city.",
    "The rooftop bar has an amazing view over the city skyline.",
    "Check in was fast and the receptionist upgraded us for free.",
    "The bed was extremely comfortable and the shower pressure great.",
    "Loved the design of the lobby and the rooms feel brand new.",
    "Housekeeping kept everything immaculate every single day.",
    "The concierge booked us a restaurant we could never have found.",
    "Perfect base for sightseeing, every landmark within walking distance.",
    "The spa and sauna were a lovely surprise after a long flight.",
    "Fast wifi, good desk, worked perfectly for my remote work mornings.",
    "The metro station is literally around the corner, so convenient.",
    "Beautiful historic building with modern renovated bathrooms.",
    "Kids loved the pool and the staff treated them wonderfully.",
    "Room service arrived hot and faster than promised.",
    "The view from the 8th floor over the river was unforgettable.",
]
POS_CLOSERS = [
    "Would definitely stay here again on our next trip.",
    "Highly recommended for couples on a city break.",
    "We will be back for sure.",
    "Easily the best hotel of our two week trip.",
    "Worth every euro.",
    "",
    "",
]

NEG_OPENERS = [
    "The room was much smaller than the photos suggested.",
    "Noise from the street kept us awake until 3am.",
    "The air conditioning was broken for our entire stay.",
    "Breakfast was chaotic, tables never cleaned, food ran out early.",
    "WiFi kept dropping and the staff could not fix it.",
    "The bathroom smelled of mould and the drain was clogged.",
    "Our room was not ready at 4pm and we waited an hour in the lobby.",
    "The elevator was out of service and we were on the 6th floor.",
    "Hidden city tax and parking fees appeared at checkout.",
    "Walls are paper thin, we heard every word from the neighbours.",
    "The mattress was sagging and clearly needed replacement.",
    "Reception was rude when we asked for a late checkout.",
    "The pool photos are misleading, it is tiny and cold.",
    "Housekeeping knocked at 8am despite the do not disturb sign.",
    "The heating could not be turned off and the room was 28 degrees.",
    "Our booking for a double bed became two singles pushed together.",
    "The minibar is absurdly priced, four euros for water.",
    "Construction next door started drilling at seven in the morning.",
    "The safe in our room was broken and never repaired.",
    "Coffee at breakfast was undrinkable and the queue was long.",
]
NEG_CLOSERS = [
    "Not worth the price we paid.",
    "We would not return.",
    "Management really needs to address this.",
    "Disappointing for a hotel with this rating.",
    "",
    "",
]
NEUTRAL_BITS = [
    "The location is convenient for the main station.",
    "It is a standard chain hotel, nothing more nothing less.",
    "Fine for a one night stopover.",
    "The lobby is nicer than the rooms.",
]

TAG_MOTIFS = {
    "positive": ["location", "staff", "breakfast", "clean", "view",
                 "comfortable bed", "value", "rooftop", "design", "spa"],
    "negative": ["noise", "small room", "wifi", "cleaning", "price",
                 "elevator", "air conditioning", "hidden fees", "breakfast queue",
                 "mattress"],
}


def hotel_records():
    out = []
    for i, (name, city, country) in enumerate(HOTELS, start=1):
        lat, lng = CITY_LATLNG[city]
        slug = name.lower().replace(" ", "-").replace("+", "")
        out.append({
            "hotel_id": f"HTL-{i:04d}",
            "hotel_name": name,
            "hotel_address": f"{i * 3} Main Street {city} {country}",
            "city": city,
            "country": country,
            "lat": round(lat + random.uniform(-0.01, 0.01), 5),
            "lng": round(lng + random.uniform(-0.01, 0.01), 5),
            "avg_score": None,  # filled later
            "slug": slug,
        })
    return out


def make_review(rng_day):
    """Return dict matching Kaggle Hotel Reviews schema (subset)."""
    is_pos = random.random() < 0.62
    n_pos = random.randint(0, 2) if is_pos else random.randint(0, 1)
    n_neg = 0 if (is_pos and random.random() < 0.55) else (
        random.randint(1, 2) if is_pos else random.randint(1, 3))
    pos = " ".join(random.sample(POS_OPENERS, k=min(n_pos, len(POS_OPENERS))))
    if n_pos and random.random() < 0.4:
        pos += " " + random.choice(POS_CLOSERS).strip()
    neg = " ".join(random.sample(NEG_OPENERS, k=min(n_neg, len(NEG_OPENERS))))
    if n_neg and random.random() < 0.35:
        neg += " " + random.choice(NEG_CLOSERS).strip()
    if not pos and not neg:
        pos = random.choice(NEUTRAL_BITS)
    words = len((pos + " " + neg).split())
    # score correlates with sentiment + noise
    base = (8.4 + random.uniform(-0.5, 1.4)) if is_pos else (5.6 + random.uniform(-1.6, 1.2))
    base += (n_pos - n_neg) * 0.35
    score = round(min(10.0, max(2.5, base)), 1)
    tags = [random.choice(TRIP_TYPES), random.choice(GROUPS),
            random.choice(STAY_NIGHTS),
            random.choice(["Double or Twin Room", "Superior Double Room",
                           "Standard Double Room", "Deluxe Room", "Suite"]),
            "Submitted from a mobile device" if random.random() < 0.3 else "Submitted on desktop"]
    return {
        "positive_review": pos.strip(),
        "negative_review": neg.strip(),
        "score": score,
        "tags": tags,
        "reviewer_nationality": random.choice(NATIONALITIES),
        "review_date": rng_day,
        "total_words": words,
        "with_pets": 1 if random.random() < 0.04 else 0,
    }


def main():
    hotels = hotel_records()
    reviews = []
    rev_id = 1
    for h in hotels:
        h_scores = []
        per_hotel = 20 if h["hotel_name"] in (
            "Hotel de la Cite", "Hotel Danieli", "Barcelo Raval") else 14
        for _ in range(per_hotel):
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            r = make_review(f"2025-{month:02d}-{day:02d}")
            r["review_id"] = f"REV-{rev_id:05d}"
            r["hotel_id"] = h["hotel_id"]
            h_scores.append(r["score"])
            reviews.append(r)
            rev_id += 1
        h["avg_score"] = round(sum(h_scores) / len(h_scores), 1)

    with open("data/hotels_snapshot.json", "w") as f:
        json.dump(hotels, f, indent=2)
    with open("data/reviews_snapshot.json", "w") as f:
        json.dump(reviews, f, indent=2)

    # Kaggle-style CSV extract (exact column names of the 515K dataset)
    cols = ["Hotel_Address", "Review_Date", "Average_Score", "Hotel_Name",
            "Reviewer_Nationality", "Negative_Review", "Review_Total_Negative_Word_Counts",
            "Positive_Review", "Review_Total_Positive_Word_Counts",
            "Reviewer_Score", "Tags", "lat", "lng"]
    hotel_by_id = {h["hotel_id"]: h for h in hotels}
    with open("data/kaggle_hotel_reviews_extract.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in reviews:
            h = hotel_by_id[r["hotel_id"]]
            w.writerow({
                "Hotel_Address": h["hotel_address"],
                "Review_Date": r["review_date"],
                "Average_Score": h["avg_score"],
                "Hotel_Name": h["hotel_name"],
                "Reviewer_Nationality": r["reviewer_nationality"],
                "Negative_Review": r["negative_review"] or "No Negative",
                "Review_Total_Negative_Word_Counts": len(r["negative_review"].split()),
                "Positive_Review": r["positive_review"] or "No Positive",
                "Review_Total_Positive_Word_Counts": len(r["positive_review"].split()),
                "Reviewer_Score": r["score"],
                "Tags": "[ '" + "', '".join(r["tags"]) + "' ]",
                "lat": h["lat"], "lng": h["lng"],
            })
    print(f"Generated {len(hotels)} hotels and {len(reviews)} reviews")
    print("Files: data/hotels_snapshot.json, data/reviews_snapshot.json, "
          "data/kaggle_hotel_reviews_extract.csv")


if __name__ == "__main__":
    main()
