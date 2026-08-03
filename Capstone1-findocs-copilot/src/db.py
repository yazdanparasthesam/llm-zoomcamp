import sqlite3
import datetime
import time
from src.config import SQLITE_DB_PATH, USE_DOCKER, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

def get_db_connection():
    """
    Returns a connection to either PostgreSQL (in Docker) or SQLite (local standalone).
    Includes automatic retry logic for container startup.
    """
    if USE_DOCKER:
        import psycopg2
        for attempt in range(5):
            try:
                conn = psycopg2.connect(
                    host=POSTGRES_HOST,
                    port=POSTGRES_PORT,
                    dbname=POSTGRES_DB,
                    user=POSTGRES_USER,
                    password=POSTGRES_PASSWORD
                )
                return conn, "postgres"
            except Exception as e:
                if attempt == 4:
                    print(f"Postgres connection failed after retries ({e}), falling back to SQLite.")
                else:
                    time.sleep(1)
            
    conn = sqlite3.connect(SQLITE_DB_PATH)
    return conn, "sqlite"

def init_db():
    """
    Initializes database tables for logging conversations, LLM-as-a-judge relevance,
    and user feedback (+1 / -1). Safe to call multiple times (uses IF NOT EXISTS).
    """
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == "sqlite":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    model TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    relevance_label TEXT NOT NULL,
                    relevance_score REAL NOT NULL,
                    ticker TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    feedback_value INTEGER NOT NULL,
                    comment TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    model TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    relevance_label TEXT NOT NULL,
                    relevance_score REAL NOT NULL,
                    ticker TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id),
                    feedback_value INTEGER NOT NULL,
                    comment TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB Warning] Could not initialize database tables: {e}")
        return False

def log_conversation(question, answer, model, latency_ms, relevance_label, relevance_score, ticker=None):
    init_db()  # Ensure tables exist before inserting
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    if db_type == "sqlite":
        cursor.execute("""
            INSERT INTO conversations 
            (question, answer, model, latency_ms, relevance_label, relevance_score, ticker)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (question, answer, model, latency_ms, relevance_label, relevance_score, ticker))
        conv_id = cursor.lastrowid
    else:
        cursor.execute("""
            INSERT INTO conversations 
            (question, answer, model, latency_ms, relevance_label, relevance_score, ticker)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (question, answer, model, latency_ms, relevance_label, relevance_score, ticker))
        conv_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return conv_id

def log_feedback(conversation_id, feedback_value, comment=""):
    init_db()  # Ensure tables exist before inserting
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    if db_type == "sqlite":
        cursor.execute("""
            INSERT INTO feedback (conversation_id, feedback_value, comment)
            VALUES (?, ?, ?)
        """, (conversation_id, feedback_value, comment))
    else:
        cursor.execute("""
            INSERT INTO feedback (conversation_id, feedback_value, comment)
            VALUES (%s, %s, %s)
        """, (conversation_id, feedback_value, comment))
    conn.commit()
    conn.close()

def get_monitoring_stats():
    """
    Returns analytics statistics for Streamlit dashboard and monitoring preview.
    Automatically initializes database tables if they do not exist.
    """
    init_db()  # Ensure tables exist before querying
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), AVG(latency_ms), AVG(relevance_score) FROM conversations")
        row = cursor.fetchone()
        total_queries = row[0] or 0
        avg_latency = round(row[1] or 0, 2)
        avg_relevance = round((row[2] or 0) * 100, 1)
        
        cursor.execute("SELECT relevance_label, COUNT(*) FROM conversations GROUP BY relevance_label")
        relevance_dist = dict(cursor.fetchall())
        
        cursor.execute("SELECT feedback_value, COUNT(*) FROM feedback GROUP BY feedback_value")
        fb_dict = dict(cursor.fetchall())
        pos_fb = fb_dict.get(1, 0)
        neg_fb = fb_dict.get(-1, 0)
        
        cursor.execute("SELECT ticker, COUNT(*) FROM conversations WHERE ticker IS NOT NULL GROUP BY ticker")
        ticker_counts = dict(cursor.fetchall())
        
        conn.close()
        return {
            "total_queries": total_queries,
            "avg_latency": avg_latency,
            "avg_relevance_percent": avg_relevance,
            "relevance_distribution": relevance_dist,
            "positive_feedback": pos_fb,
            "negative_feedback": neg_fb,
            "ticker_counts": ticker_counts
        }
    except Exception as e:
        # Fallback empty stats if db query fails for any reason
        print(f"[DB Stats Warning] {e}")
        return {
            "total_queries": 0,
            "avg_latency": 0.0,
            "avg_relevance_percent": 100.0,
            "relevance_distribution": {"RELEVANT": 0},
            "positive_feedback": 0,
            "negative_feedback": 0,
            "ticker_counts": {}
        }

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
