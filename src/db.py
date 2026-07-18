"""Tiny SQLite helper. In a real engagement this might be Postgres/Snowflake/the
customer's warehouse — but the shape of the code stays the same. Keep the storage
boring so the interesting work stays in the agents."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "reviews.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                review_id     TEXT PRIMARY KEY,
                product_id    TEXT NOT NULL,
                product_name  TEXT NOT NULL,
                rating        INTEGER,
                date          TEXT,
                review_text   TEXT NOT NULL
            );

            -- one row per review, populated by the extraction agent.
            CREATE TABLE IF NOT EXISTS insights (
                review_id        TEXT PRIMARY KEY REFERENCES reviews(review_id),
                sentiment        TEXT,
                issues_json      TEXT,   -- JSON array
                categories_json  TEXT,   -- JSON array
                praise_json      TEXT,   -- JSON array
                summary          TEXT,
                evidence_quote   TEXT
            );
            """
        )
