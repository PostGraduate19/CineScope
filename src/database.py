import sqlite3
from pathlib import Path
import datetime

# Establish paths relative to this file's position inside the src directory
BASE = Path(__file__).resolve().parents[1]
DB_PATH = BASE / 'data' / 'user_interactions.db'

def init_db():
    """Creates the database folder and the interactions table if they do not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            tmdb_id INTEGER,
            movie_title TEXT,
            interaction_type TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_interaction(session_id, tmdb_id, movie_title, interaction_type):
    """Records a unique user behavior event to the persistent SQLite table."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute('''
            INSERT INTO interactions (session_id, tmdb_id, movie_title, interaction_type, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, tmdb_id, movie_title, interaction_type, now))
        conn.commit()
        conn.close()
    except Exception as e:
        # Prevent database failures from crashing the main user interface
        print(f"Database logging failure: {e}")

if __name__ == '__main__':
    init_db()
    print(f"Database initialized successfully at {DB_PATH}")