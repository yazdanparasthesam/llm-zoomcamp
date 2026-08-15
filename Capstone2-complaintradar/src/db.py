import sqlite3
import time

from src.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    SQLITE_DB_PATH,
    USE_DOCKER,
)


def get_db_connection():
    if USE_DOCKER:
        import psycopg2

        for attempt in range(5):
            try:
                conn = psycopg2.connect(
                    host=POSTGRES_HOST,
                    port=POSTGRES_PORT,
                    dbname=POSTGRES_DB,
                    user=POSTGRES_USER,
                    password=POSTGRES_PASSWORD,
                )
                return conn, "postgres"
            except Exception as exc:
                if attempt == 4:
                    print(f"Postgres connection failed after retries ({exc}), falling back to SQLite.")
                else:
                    time.sleep(1)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    return conn, "sqlite"


def init_db():
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        if db_type == "sqlite":
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    model TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    relevance_label TEXT NOT NULL,
                    relevance_score REAL NOT NULL,
                    company TEXT,
                    product TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    feedback_value INTEGER NOT NULL,
                    comment TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
                """
            )
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    model TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    relevance_label TEXT NOT NULL,
                    relevance_score REAL NOT NULL,
                    company TEXT,
                    product TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id),
                    feedback_value INTEGER NOT NULL,
                    comment TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        print(f"[DB Warning] Could not initialize tables: {exc}")
        return False


def log_conversation(question, answer, model, latency_ms, relevance_label, relevance_score, company=None, product=None):
    init_db()
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    if db_type == "sqlite":
        cursor.execute(
            """
            INSERT INTO conversations
            (question, answer, model, latency_ms, relevance_label, relevance_score, company, product)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (question, answer, model, latency_ms, relevance_label, relevance_score, company, product),
        )
        conv_id = cursor.lastrowid
    else:
        cursor.execute(
            """
            INSERT INTO conversations
            (question, answer, model, latency_ms, relevance_label, relevance_score, company, product)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (question, answer, model, latency_ms, relevance_label, relevance_score, company, product),
        )
        conv_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return conv_id


def log_feedback(conversation_id, feedback_value, comment=""):
    init_db()
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = "?" if db_type == "sqlite" else "%s"
    cursor.execute(
        f"INSERT INTO feedback (conversation_id, feedback_value, comment) VALUES ({ph}, {ph}, {ph})",
        (conversation_id, feedback_value, comment),
    )
    conn.commit()
    conn.close()


def get_monitoring_stats():
    init_db()
    empty = {
        "total_queries": 0,
        "avg_latency": 0.0,
        "avg_relevance_percent": 0.0,
        "relevance_distribution": {},
        "positive_feedback": 0,
        "negative_feedback": 0,
        "company_counts": {},
        "product_counts": {},
    }
    try:
        conn, _db_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), AVG(latency_ms), AVG(relevance_score) FROM conversations")
        row = cursor.fetchone()
        cursor.execute("SELECT relevance_label, COUNT(*) FROM conversations GROUP BY relevance_label")
        relevance_dist = dict(cursor.fetchall())
        cursor.execute("SELECT feedback_value, COUNT(*) FROM feedback GROUP BY feedback_value")
        fb_dict = dict(cursor.fetchall())
        cursor.execute("SELECT company, COUNT(*) FROM conversations WHERE company IS NOT NULL GROUP BY company")
        company_counts = dict(cursor.fetchall())
        cursor.execute("SELECT product, COUNT(*) FROM conversations WHERE product IS NOT NULL GROUP BY product")
        product_counts = dict(cursor.fetchall())
        conn.close()
        return {
            "total_queries": row[0] or 0,
            "avg_latency": round(row[1] or 0, 2),
            "avg_relevance_percent": round((row[2] or 0) * 100, 1),
            "relevance_distribution": relevance_dist,
            "positive_feedback": fb_dict.get(1, 0),
            "negative_feedback": fb_dict.get(-1, 0),
            "company_counts": company_counts,
            "product_counts": product_counts,
        }
    except Exception as exc:
        print(f"[DB Stats Warning] {exc}")
        return empty


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
