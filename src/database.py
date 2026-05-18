import sqlite3
import os
from passlib.hash import argon2

DB_PATH = "data/health_data.db"


# -----------------------
# INIT DB
# -----------------------
def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        type TEXT,
        duration REAL,
        calories REAL,
        distance REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        type TEXT,
        value REAL,
        unit TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT
    )
    """)

    # -----------------------
    # ADMIN DEFAULT USER
    # -----------------------
    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        ("admin",)
    )
    row = cursor.fetchone()

    # Si admin n'existe pas → création
    if not row:
        password_hash = argon2.hash("admin")

        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", password_hash)
        )
        print("✅ Compte admin créé (admin/admin)")

    else:
        stored_hash = row[0]

        # 🔥 Si ancien hash (ex: bcrypt), on force migration vers argon2
        if not stored_hash.startswith("$argon2"):
            password_hash = argon2.hash("admin")

            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (password_hash, "admin")
            )
            print("♻️ Hash admin migré vers argon2 (admin/admin)")

    conn.commit()
    conn.close()


# -----------------------
# CREATE USER
# -----------------------
def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    password_hash = argon2.hash(password)

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# -----------------------
# VERIFY USER
# -----------------------
def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    try:
        return argon2.verify(password, row[0])
    except Exception:
        return False