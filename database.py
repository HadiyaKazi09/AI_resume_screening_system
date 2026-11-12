import sqlite3
from datetime import datetime

import pandas as pd

DB_NAME = "screening.db"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screened_at TEXT,
                job_title TEXT,
                name TEXT,
                email TEXT,
                phone TEXT,
                match_pct REAL,
                similarity REAL,
                matched TEXT,
                missing TEXT
            )"""
        )
        cols = [row[1] for row in conn.execute("PRAGMA table_info(results)")]
        if "weighted_pct" not in cols:
            conn.execute("ALTER TABLE results ADD COLUMN weighted_pct REAL")


def save_result(job_title, r):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """INSERT INTO results
               (screened_at, job_title, name, email, phone, match_pct, weighted_pct,
                similarity, matched, missing)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                job_title,
                r["name"],
                r["email"],
                r["phone"],
                r["match_pct"],
                r["weighted_pct"],
                r["similarity"],
                ", ".join(r["matched"]),
                ", ".join(r["missing"]),
            ),
        )


def load_results():
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql("SELECT * FROM results ORDER BY id DESC", conn)