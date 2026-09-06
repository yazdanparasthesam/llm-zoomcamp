"""Retrieval best-practice tests: rewriting, hybrid, re-ranking."""
import json

from src import config
from src import search as sm


def test_query_rewriting_expands_slang_and_codes():
    rewritten, adds = sm.rewrite_query("Weekend in NYC with fast wifi and bkfst")
    assert "new york jfk" in rewritten.lower()
    assert "internet remote work" in rewritten.lower()
    assert "breakfast" in rewritten.lower()
    assert len(adds) == 3


def test_hybrid_retrieves_known_evidence():
    idx = sm.get_index()
    gt = json.load(open(config.GROUND_TRUTH_PATH))
    q = next(x for x in gt if "Barcelo Raval" in x["question"])
    hits = idx.search(q["question"], mode="hybrid_rerank", k=5)["results"]
    assert q["doc_id"] in [c["doc_id"] for c in hits]


def test_rerank_boosts_hotel_name_mentions():
    idx = sm.get_index()
    hits = idx.search("Is the breakfast at Hotel Sacher Wien worth it?",
                      mode="hybrid_rerank", k=5)["results"]
    assert hits[0]["hotel_name"] == "Hotel Sacher Wien"


def test_rerank_sentiment_section_alignment():
    idx = sm.get_index()
    hits = idx.search("What problems and complaints do guests report at "
                      "Park Plaza Westminster London?", mode="hybrid_rerank",
                      k=3)["results"]
    assert any(c["section"] == "negative" for c in hits)
