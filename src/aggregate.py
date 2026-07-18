"""Stage 3 — Aggregate + risk score.

Turns per-review insights into per-product intelligence. This stage is plain Python,
no LLM — cheaper, deterministic, and easy to explain to a customer ("here's exactly
why this product got flagged"). Explainability matters: a merch VP won't trust a
black-box score.

The risk score is intentionally simple and transparent:
    risk = negative_share * 0.5
         + defect_share   * 0.3
         + recurring_bonus (0.2 if any single issue-category repeats >= 3 times)

Tune these weights WITH the customer — the formula is a conversation starter, not a
law of physics.

Usage:  python -m src.aggregate
"""

import json
from collections import Counter
from src.db import connect


def _load(conn):
    return conn.execute(
        """SELECT r.product_id, r.product_name, r.rating,
                  i.sentiment, i.issues_json, i.categories_json, i.evidence_quote
           FROM reviews r JOIN insights i ON i.review_id = r.review_id"""
    ).fetchall()


def compute():
    with connect() as conn:
        rows = _load(conn)

    products = {}
    for row in rows:
        pid = row["product_id"]
        p = products.setdefault(
            pid,
            {
                "product_id": pid,
                "product_name": row["product_name"],
                "n_reviews": 0,
                "ratings": [],
                "sentiments": Counter(),
                "category_counts": Counter(),
                "issues": [],
                "quotes": [],
            },
        )
        p["n_reviews"] += 1
        if row["rating"] is not None:
            p["ratings"].append(row["rating"])
        p["sentiments"][row["sentiment"]] += 1
        for cat in json.loads(row["categories_json"] or "[]"):
            p["category_counts"][cat] += 1
        p["issues"].extend(json.loads(row["issues_json"] or "[]"))
        if row["evidence_quote"]:
            p["quotes"].append(row["evidence_quote"])

    results = []
    for p in products.values():
        n = p["n_reviews"]
        neg_share = p["sentiments"]["negative"] / n if n else 0
        defect_share = p["category_counts"].get("defect", 0) / n if n else 0
        # "recurring" = the same issue category shows up 3+ times = a pattern, not noise.
        top_cat, top_count = (p["category_counts"].most_common(1) or [("", 0)])[0]
        recurring_bonus = 0.2 if top_count >= 3 else 0.0

        risk = round(neg_share * 0.5 + defect_share * 0.3 + recurring_bonus, 3)

        results.append(
            {
                "product_id": p["product_id"],
                "product_name": p["product_name"],
                "n_reviews": n,
                "avg_rating": round(sum(p["ratings"]) / len(p["ratings"]), 2)
                if p["ratings"]
                else None,
                "neg_share": round(neg_share, 2),
                "risk_score": risk,
                "top_issue_category": top_cat,
                "top_issue_count": top_count,
                "top_issues": [i for i, _ in Counter(p["issues"]).most_common(5)],
                "sample_quotes": p["quotes"][:3],
            }
        )

    results.sort(key=lambda r: r["risk_score"], reverse=True)
    return results


if __name__ == "__main__":
    for r in compute():
        flag = "[FLAG]" if r["risk_score"] >= 0.4 else "      "
        print(
            f"{flag} risk={r['risk_score']:.2f}  {r['product_name']:32s} "
            f"neg={r['neg_share']:.0%}  top={r['top_issue_category']}×{r['top_issue_count']}"
        )
