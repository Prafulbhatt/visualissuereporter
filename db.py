"""SQLite storage for logged issues.

Schema:
    issues(id, description, category, photo_path, timestamp, status)
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "issues.db"

CATEGORIES = [
    "Structural",
    "Electrical",
    "Plumbing",
    "Furniture & Fixtures",
    "Safety Hazard",
    "Cleanliness",
    "Equipment/Appliance",
    "IT/Electronics",
    "Other",
]


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the issues table if it doesn't exist yet. Safe to call every startup."""
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                photo_path TEXT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open'
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def insert_issue(description: str, category: str, photo_path: str, timestamp: str, status: str = "open") -> int:
    """Insert a new issue row. This is what the agent's log_issue tool calls."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO issues (description, category, photo_path, timestamp, status) VALUES (?, ?, ?, ?, ?)",
            (description, category, photo_path, timestamp, status),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_all_issues() -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM issues ORDER BY timestamp DESC", conn)
        return df
    finally:
        conn.close()


def update_status(issue_id: int, status: str) -> None:
    conn = get_connection()
    try:
        conn.execute("UPDATE issues SET status = ? WHERE id = ?", (status, issue_id))
        conn.commit()
    finally:
        conn.close()