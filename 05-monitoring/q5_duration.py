# q5_duration.py
import sqlite3
conn = sqlite3.connect("traces.db")
cur = conn.cursor()
cur.execute("""
    SELECT name, SUM(end_time - start_time) / 1e9 as total_seconds
    FROM spans
    WHERE name != 'rag'
    GROUP BY name
""")
for name, total_sec in cur.fetchall():
    print(f"{name}: {total_sec:.3f} s")
conn.close()
