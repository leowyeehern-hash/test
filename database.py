import sqlite3
from contextlib import contextmanager

DB_NAME = "students.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
    finally:
        conn.close()

# 为了兼容你之前的 app.py，我们保留 connect 函数，但内部也调用 get_db
def connect():
    return sqlite3.connect(DB_NAME)

def create_table():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE, 
            subject_id TEXT, time_slots TEXT, 
            advantage TEXT, weakness TEXT,
            intent TEXT, fee_pref TEXT, role TEXT, privacy_mode BOOLEAN, rating REAL
        )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_name ON users(name)")
    create_matches_table()
    create_messages_table()

def save_user(name, subject_id, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating):
    with get_db() as conn:
        conn.execute("""
        INSERT INTO users (name, subject_id, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, subject_id, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating))
        conn.commit()

def get_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return [{
            "id": r[0], "name": r[1], "subject_id": r[2], "time_slots": r[3],
            "advantage": r[4], "weakness": r[5], "intent": r[6],
            "fee_pref": r[7], "role": r[8], "privacy_mode": r[9], "rating": r[10]
        } for r in rows]

def get_user_by_name(name):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0], "name": row[1], "subject_id": row[2], "time_slots": row[3],
                "advantage": row[4], "weakness": row[5], "intent": row[6],
                "fee_pref": row[7], "role": row[8], "privacy_mode": row[9], "rating": row[10]
            }
    return None

def update_user(name, subject_id, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating):
    with get_db() as conn:
        conn.execute("""
        UPDATE users SET subject_id = ?, time_slots = ?, advantage = ?, weakness = ?, 
        intent = ?, fee_pref = ?, role = ?, privacy_mode = ?, rating = ?
        WHERE name = ?
        """, (subject_id, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating, name))
        conn.commit()

def save_or_update_user(name, subject_id, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating):
    if get_user_by_name(name):
        update_user(name, subject_id, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating)
    else:
        save_user(name, subject_id, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating)

def create_matches_table():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_a TEXT, user_b TEXT, status TEXT DEFAULT 'pending'
            )
        ''')
        conn.commit()

def create_messages_table():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT, receiver TEXT, content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()