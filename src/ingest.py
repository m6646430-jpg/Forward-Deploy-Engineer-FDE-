"""Stage 1 — Ingest.

CSV → SQLite. The least glamorous stage and often the most important: real customer
data is messy (missing fields, weird encodings, duplicate ids). Getting a clean,
queryable table is 80% of a real engagement. We keep it simple here because our
sample is clean, but note where you'd add validation for real data.

Usage:  python -m src.ingest data/sample_reviews.csv
"""

import csv
import sys
from src.db import connect, init_schema


def ingest(csv_path: str) -> int:
    init_schema()
    rows = 0
    with open(csv_path, newline="", encoding="utf-8") as f, connect() as conn:
        reader = csv.DictReader(f)
        for row in reader:
            # In real data you'd validate/normalize here: skip blank reviews,
            # coerce ratings, dedupe by review_id, normalize product names, etc.
            if not row.get("review_text", "").strip():
                continue
            conn.execute(
                """INSERT OR REPLACE INTO reviews
                   (review_id, product_id, product_name, rating, date, review_text)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    row["review_id"],
                    row["product_id"],
                    row["product_name"],
                    int(row["rating"]) if row.get("rating") else None,
                    row.get("date"),
                    row["review_text"],
                ),
            )
            rows += 1
    return rows


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/sample_reviews.csv"
    n = ingest(path)
    print(f"Ingested {n} reviews from {path} into data/reviews.db")
