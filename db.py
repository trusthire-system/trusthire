import sqlite3
import hashlib
from datetime import datetime
import secrets
import os

# ---------- DATABASE PATH ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "trusthire.db")

print("📂 USING DATABASE:", DB_NAME)

# ---------- CONNECTION ----------
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=10)
    conn.execute("PRAGMA foreign_keys=ON;")  # enforce foreign keys
    return conn

# ---------- PASSWORD ----------
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str):
    return hashlib.sha256(password.encode()).hexdigest() == hashed_password

# ---------- TOKEN ----------
def generate_token(length=32):
    return secrets.token_urlsafe(length)

# ---------- ADD COLUMN IF MISSING ----------
def _add_column_if_missing(cur, table, column_def):
    col_name = column_def.split()[0]
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    if col_name not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        print(f"➕ Added column {col_name} to {table}")

# ---------- CREATE TABLES ----------
def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    # ---------- COMPANIES ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            domain TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """)
    _add_column_if_missing(cur, "companies", "address TEXT")
    _add_column_if_missing(cur, "companies", "city TEXT")
    _add_column_if_missing(cur, "companies", "state TEXT")
    _add_column_if_missing(cur, "companies", "country TEXT")
    _add_column_if_missing(cur, "companies", "website TEXT")

    # ---------- USERS ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            company_id INTEGER,
            status TEXT DEFAULT 'pending_verification',
            verification_token TEXT UNIQUE,
            verified_at TEXT,
            resume_path TEXT,
            created_at TEXT,
            last_login TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    # ---------- ADMINS ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT
        )
    """)
    cur.execute("SELECT id FROM admins LIMIT 1")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO admins (email, password, created_at) VALUES (?, ?, ?)",
            ("admin@trusthire.com", hash_password("admin123"), datetime.now().isoformat())
        )

    # ---------- JOB POSTS ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            hr_id INTEGER,
            role TEXT NOT NULL,
            skills TEXT,
            experience TEXT,
            salary TEXT,
            location TEXT,
            description TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(id),
            FOREIGN KEY (hr_id) REFERENCES users(id)
        )
    """)

    # ---------- USER SKILLS ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            added_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ---------- CERTIFICATES ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            certificate_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ---------- CANDIDATE PROFILE (NEW) ----------
    # Base table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS candidate_profile (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            updated_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Add new columns (migration safe)
    _add_column_if_missing(cur, "candidate_profile", "headline TEXT")
    _add_column_if_missing(cur, "candidate_profile", "location TEXT")
    _add_column_if_missing(cur, "candidate_profile", "summary TEXT")
    _add_column_if_missing(cur, "candidate_profile", "education TEXT")
    _add_column_if_missing(cur, "candidate_profile", "experience TEXT")
    _add_column_if_missing(cur, "candidate_profile", "linkedin TEXT")
    _add_column_if_missing(cur, "candidate_profile", "github TEXT")

    conn.commit()
    conn.close()
