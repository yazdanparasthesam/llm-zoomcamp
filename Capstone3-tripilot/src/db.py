#!/usr/bin/env python3
"""
TripPilot telemetry store.

PostgreSQL 16 when reachable (docker-compose), automatic fallback to a
local SQLite file (zero-config reviewers / CI). Same schema both ways.

  conversations  — every agent run with latency, tokens, judge labels
  feedback       — thumbs up/down (+1 / -1) per conversation
"""
import json
import os
import sqlite3
from datetime import datetime, timezone

from src import config

PG_COLS = """
    (id TEXT PRIMARY KEY, question TEXT, answer TEXT, mode TEXT,
     prompt_style TEXT, tools_used TEXT, model TEXT, response_time_ms FLOAT,
     relevance TEXT, relevance_explanation TEXT, prompt_tokens INTEGER,
     completion_tokens INTEGER, eval_total_tokens INTEGER,
     groq_cost_usd FLOAT, city TEXT, photo_used BOOLEAN,
     timestamp TIMESTAMPTZ)
"""
SQLITE_COLS = """
    (id TEXT PRIMARY KEY, question TEXT, answer TEXT, mode TEXT,
     prompt_style TEXT, tools_used TEXT, model TEXT, response_time_ms REAL,
     relevance TEXT, relevance_explanation TEXT, prompt_tokens INTEGER,
     completion_tokens INTEGER, eval_total_tokens INTEGER,
     groq_cost_usd REAL, city TEXT, photo_used INTEGER, timestamp TEXT)
"""

_pg_ok_cache = None


def _postgres_available():
    global _pg_ok_cache
    if _pg_ok_cache is not None:
        return _pg_ok_cache
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=config.POSTGRES_HOST, port=config.POSTGRES_PORT,
            dbname=config.POSTGRES_DB, user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD, connect_timeout=1)
        conn.close()
        _pg_ok_cache = True
    except Exception:
        _pg_ok_cache = False
    return _pg_ok_cache


def _pg_conn():
    import psycopg2
    return psycopg2.connect(host=config.POSTGRES_HOST, port=config.POSTGRES_PORT,
                            dbname=config.POSTGRES_DB, user=config.POSTGRES_USER,
                            password=config.POSTGRES_PASSWORD)


def _sqlite_conn():
    os.makedirs(os.path.dirname(config.SQLITE_PATH), exist_ok=True)
    return sqlite3.connect(config.SQLITE_PATH)


def init_db():
    ts = datetime.now(timezone.utc).isoformat()
    if _postgres_available():
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS conversations {PG_COLS}")
        cur.execute("""CREATE TABLE IF NOT EXISTS feedback
                       (id SERIAL PRIMARY KEY, conversation_id TEXT,
                        feedback INTEGER, timestamp TIMESTAMPTZ)""")
        conn.commit()
        conn.close()
        init_flag = "postgres"
    else:
        conn = _sqlite_conn()
        conn.execute(f"CREATE TABLE IF NOT EXISTS conversations {SQLITE_COLS}")
        conn.execute("""CREATE TABLE IF NOT EXISTS feedback
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         conversation_id TEXT, feedback INTEGER, timestamp TEXT)""")
        conn.commit()
        conn.close()
        init_flag = "sqlite"
    print(f"[db] initialized ({init_flag}) at {ts}")
    return init_flag


def save_conversation(rec):
    if _postgres_available():
        _pg_exec(
            """INSERT INTO conversations (id, question, answer, mode,
               prompt_style, tools_used, model, response_time_ms, relevance,
               relevance_explanation, prompt_tokens, completion_tokens,
               eval_total_tokens, groq_cost_usd, city, photo_used, timestamp)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            _row(rec))
    else:
        conn = _sqlite_conn()
        conn.execute(
            """INSERT INTO conversations (id, question, answer, mode,
               prompt_style, tools_used, model, response_time_ms, relevance,
               relevance_explanation, prompt_tokens, completion_tokens,
               eval_total_tokens, groq_cost_usd, city, photo_used, timestamp)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            _row(rec, pg=False))
        conn.commit()
        conn.close()


def _row(rec, pg=True):
    ts = datetime.now(timezone.utc) if pg else datetime.now(timezone.utc).isoformat()
    return (rec["conversation_id"], rec["question"], rec["answer"], rec["mode"],
            rec["prompt_style"], json.dumps(rec["tools_used"]), rec["model"],
            rec["response_time_ms"], rec["relevance"],
            rec["relevance_explanation"], rec["prompt_tokens"],
            rec["completion_tokens"], rec["eval_total_tokens"],
            rec["groq_cost_usd"], rec["city"],
            bool(rec["photo_used"]) if pg else int(bool(rec["photo_used"])), ts)


def save_feedback(conversation_id, feedback):
    ts = datetime.now(timezone.utc)
    if _postgres_available():
        _pg_exec("INSERT INTO feedback (conversation_id, feedback, timestamp)"
                 " VALUES (%s,%s,%s)", (conversation_id, int(feedback), ts))
    else:
        conn = _sqlite_conn()
        conn.execute("INSERT INTO feedback (conversation_id, feedback, timestamp)"
                     " VALUES (?,?,?)", (conversation_id, int(feedback),
                                          ts.isoformat()))
        conn.commit()
        conn.close()


def _pg_exec(sql, params):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()


def telemetry_summary():
    """Aggregates consumed by the Streamlit monitoring tab."""
    empty = {"total_queries": 0, "avg_latency_ms": 0.0, "relevance": {},
             "feedback_up": 0, "feedback_down": 0, "cities": {},
             "total_cost_usd": 0.0, "backend": "sqlite"}
    try:
        if _postgres_available():
            conn = _pg_conn()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*), COALESCE(AVG(response_time_ms),0),"
                        " COALESCE(SUM(groq_cost_usd),0) FROM conversations")
            n, avg_lat, cost = cur.fetchone()
            cur.execute("SELECT relevance, COUNT(*) FROM conversations GROUP BY 1")
            rel = dict(cur.fetchall())
            cur.execute("SELECT city, COUNT(*) FROM conversations WHERE city<>''"
                        " GROUP BY 1 ORDER BY 2 DESC LIMIT 8")
            cities = dict(cur.fetchall())
            cur.execute("SELECT COALESCE(SUM(CASE WHEN feedback=1 THEN 1 ELSE 0 END),0),"
                        " COALESCE(SUM(CASE WHEN feedback=-1 THEN 1 ELSE 0 END),0)"
                        " FROM feedback")
            up, down = cur.fetchone()
            conn.close()
            backend = "postgres"
        else:
            conn = _sqlite_conn()
            n, avg_lat, cost = conn.execute(
                "SELECT COUNT(*), COALESCE(AVG(response_time_ms),0),"
                " COALESCE(SUM(groq_cost_usd),0) FROM conversations").fetchone()
            rel = dict(conn.execute(
                "SELECT relevance, COUNT(*) FROM conversations GROUP BY 1").fetchall())
            cities = dict(conn.execute(
                "SELECT city, COUNT(*) FROM conversations WHERE city<>''"
                " GROUP BY 1 ORDER BY 2 DESC LIMIT 8").fetchall())
            up, down = conn.execute(
                "SELECT COALESCE(SUM(CASE WHEN feedback=1 THEN 1 ELSE 0 END),0),"
                " COALESCE(SUM(CASE WHEN feedback=-1 THEN 1 ELSE 0 END),0)"
                " FROM feedback").fetchone()
            conn.close()
            backend = "sqlite"
        return {"total_queries": int(n or 0), "avg_latency_ms": round(float(avg_lat or 0), 2),
                "relevance": rel, "feedback_up": int(up or 0),
                "feedback_down": int(down or 0), "cities": cities,
                "total_cost_usd": round(float(cost or 0), 6), "backend": backend}
    except Exception:
        return empty


if __name__ == "__main__":
    init_db()
    print(json.dumps(telemetry_summary(), indent=2))
