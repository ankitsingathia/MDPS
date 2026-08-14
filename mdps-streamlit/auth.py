"""Authentication module: SQLite + bcrypt."""
import sqlite3
import bcrypt
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            disease TEXT NOT NULL,
            symptoms TEXT,
            prediction TEXT NOT NULL,
            confidence REAL,
            severity REAL,
            details TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def signup(username: str, email: str, password: str) -> tuple[bool, str]:
    if not username or not email or not password:
        return False, "All fields are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    conn = get_conn()
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (username, email, password, created_at) VALUES (?, ?, ?, ?)",
            (username, email.lower(), hashed, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True, "Account created. Please log in."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    finally:
        conn.close()


def login(email: str, password: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower(),)
    ).fetchone()
    conn.close()
    if not row:
        return None
    if bcrypt.checkpw(password.encode(), row["password"].encode()):
        return {"id": row["id"], "username": row["username"], "email": row["email"]}
    return None


def save_report(user_id, disease, symptoms, prediction, confidence=None, severity=None, details=None):
    conn = get_conn()
    conn.execute(
        """INSERT INTO reports (user_id, disease, symptoms, prediction, confidence, severity, details, date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, disease, symptoms, prediction, confidence, severity, details,
         datetime.utcnow().isoformat()),
    )
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    conn.close()
    return rid


def get_user_reports(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM reports WHERE user_id = ? ORDER BY date DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_report(report_id: int) -> bool:
    """Delete a single report by ID."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    con.commit()
    con.close()
    return True

def delete_all_reports(user_id: int) -> bool:
    """Delete all reports for a user."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM reports WHERE user_id = ?", (user_id,))
    con.commit()
    con.close()
    return True