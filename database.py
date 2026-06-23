import sqlite3
from contextlib import contextmanager

import os
import shutil

# If running on Vercel, use /tmp/students.db to allow writes
if os.environ.get("VERCEL"):
    DB_NAME = "/tmp/students.db"
    bundled_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")
    if not os.path.exists(DB_NAME) and os.path.exists(bundled_db):
        try:
            shutil.copy2(bundled_db, DB_NAME)
        except Exception as e:
            print(f"Failed to copy DB: {e}")
else:
    DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# For backward compat with existing app.py
def connect():
    return sqlite3.connect(DB_NAME)

def create_table():
    with get_db() as conn:
        cursor = conn.cursor()
        # Core users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            subject_id TEXT, time_slots TEXT,
            advantage TEXT, weakness TEXT,
            intent TEXT, fee_pref TEXT, role TEXT, privacy_mode BOOLEAN, rating REAL,
            email TEXT,
            email_verified INTEGER DEFAULT 0,
            google_id TEXT,
            contact_info TEXT,
            language TEXT DEFAULT 'English',
            frequency TEXT,
            study_mode TEXT,
            group_size TEXT,
            grade_goal TEXT,
            study_style TEXT,
            resource_pref TEXT,
            bio TEXT,
            profile_pic TEXT
        )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_name ON users(name)")

        # Add new columns if upgrading from old schema (safe migration)
        new_columns = [
            ("email", "TEXT"),
            ("email_verified", "INTEGER DEFAULT 0"),
            ("google_id", "TEXT"),
            ("contact_info", "TEXT"),
            ("language", "TEXT DEFAULT 'English'"),
            ("frequency", "TEXT"),
            ("study_mode", "TEXT"),
            ("group_size", "TEXT"),
            ("grade_goal", "TEXT"),
            ("study_style", "TEXT"),
            ("resource_pref", "TEXT"),
            ("bio", "TEXT"),
            ("profile_pic", "TEXT"),
        ]
        for col_name, col_type in new_columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass  # Column already exists

        # Email confirmation tokens table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            token TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()

    create_matches_table()
    create_messages_table()


# ─────────────────────────────────────────
#  CORE USER CRUD
# ─────────────────────────────────────────

def save_user(name, subject_id, time_slots, advantage, weakness, intent, fee_pref, role, privacy_mode, rating,
              email=None, google_id=None, contact_info=None, bio=None):
    with get_db() as conn:
        conn.execute("""
        INSERT INTO users (name, subject_id, time_slots, advantage, weakness, intent, fee_pref,
                           role, privacy_mode, rating, email, google_id, contact_info, bio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, subject_id, time_slots, advantage, weakness, intent, fee_pref,
              role, privacy_mode, rating, email, google_id, contact_info, bio))
        conn.commit()


def get_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_user_by_name(name):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_google_id(google_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user(name, subject_id, time_slots, advantage, weakness, intent, fee_pref, role,
                privacy_mode, rating, email=None, contact_info=None, bio=None):
    with get_db() as conn:
        conn.execute("""
        UPDATE users SET subject_id=?, time_slots=?, advantage=?, weakness=?,
        intent=?, fee_pref=?, role=?, privacy_mode=?, rating=?,
        email=COALESCE(?, email), contact_info=COALESCE(?, contact_info), bio=COALESCE(?, bio)
        WHERE name=?
        """, (subject_id, time_slots, advantage, weakness, intent, fee_pref, role,
              privacy_mode, rating, email, contact_info, bio, name))
        conn.commit()


def save_or_update_user(name, subject_id, time_slots, advantage, weakness, intent, fee_pref,
                        role, privacy_mode, rating, email=None, contact_info=None, bio=None):
    if get_user_by_name(name):
        update_user(name, subject_id, time_slots, advantage, weakness, intent, fee_pref,
                    role, privacy_mode, rating, email, contact_info, bio)
    else:
        save_user(name, subject_id, time_slots, advantage, weakness, intent, fee_pref,
                  role, privacy_mode, rating, email=email, contact_info=contact_info, bio=bio)


def create_google_user(name, email, google_id, profile_pic=None):
    """Create or fetch a user authenticated via Google Sign-In."""
    existing = get_user_by_google_id(google_id)
    if existing:
        return existing

    existing_email = get_user_by_email(email)
    if existing_email:
        # Link Google ID to existing email account
        with get_db() as conn:
            conn.execute("UPDATE users SET google_id=?, profile_pic=COALESCE(?, profile_pic) WHERE email=?",
                         (google_id, profile_pic, email))
            conn.commit()
        return get_user_by_email(email)

    # Create brand new user
    with get_db() as conn:
        conn.execute("""
        INSERT INTO users (name, email, google_id, profile_pic, email_verified, rating, intent, role,
                           fee_pref, privacy_mode)
        VALUES (?, ?, ?, ?, 0, 3.0, 'Receiver', 'Student (Peer)', 'Free Only', 0)
        """, (name, email, google_id, profile_pic))
        conn.commit()
    return get_user_by_email(email)


def verify_user_email(email):
    with get_db() as conn:
        conn.execute("UPDATE users SET email_verified=1 WHERE email=?", (email,))
        conn.commit()


# ─────────────────────────────────────────
#  EMAIL TOKEN STORE
# ─────────────────────────────────────────

def save_email_token(email, token):
    with get_db() as conn:
        conn.execute("""
        INSERT INTO email_tokens (email, token) VALUES (?, ?)
        ON CONFLICT(email) DO UPDATE SET token=excluded.token, created_at=CURRENT_TIMESTAMP
        """, (email, token))
        conn.commit()


def get_email_by_token(token):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM email_tokens WHERE token=?", (token,))
        row = cursor.fetchone()
        return row["email"] if row else None


# ─────────────────────────────────────────
#  FIND TUTOR / FIND PEER
# ─────────────────────────────────────────

def get_tutors(subject=None, limit=50):
    """Return users who are Providers (tutors)."""
    with get_db() as conn:
        cursor = conn.cursor()
        if subject and subject.strip():
            cursor.execute("""
            SELECT * FROM users
            WHERE intent='Provider'
              AND (subject_id LIKE ? OR subject_id LIKE ? OR subject_id LIKE ?)
            ORDER BY rating DESC LIMIT ?
            """, (f"%{subject}%", f"{subject}%", f"%{subject}"), limit)
        else:
            cursor.execute("""
            SELECT * FROM users WHERE intent='Provider'
            ORDER BY rating DESC LIMIT ?
            """, (limit,))
        return [dict(r) for r in cursor.fetchall()]


def get_peers(subject=None, limit=50):
    """Return users who are free-study-buddy Receivers (peers)."""
    with get_db() as conn:
        cursor = conn.cursor()
        if subject and subject.strip():
            cursor.execute("""
            SELECT * FROM users
            WHERE intent='Receiver' AND fee_pref='Free Only'
              AND (subject_id LIKE ? OR subject_id LIKE ? OR subject_id LIKE ?)
            ORDER BY rating DESC LIMIT ?
            """, (f"%{subject}%", f"{subject}%", f"%{subject}"), limit)
        else:
            cursor.execute("""
            SELECT * FROM users
            WHERE intent='Receiver' AND fee_pref='Free Only'
            ORDER BY rating DESC LIMIT ?
            """, (limit,))
        return [dict(r) for r in cursor.fetchall()]


# ─────────────────────────────────────────
#  MATCHES & MESSAGES (existing)
# ─────────────────────────────────────────

def create_matches_table():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_a TEXT, user_b TEXT, status TEXT DEFAULT 'pending'
        )
        """)
        conn.commit()


def create_messages_table():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT, receiver TEXT, content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()