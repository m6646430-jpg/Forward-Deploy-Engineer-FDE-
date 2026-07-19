"""Stage 4 — Report.

Takes the aggregated, risk-scored products and writes the weekly "Merch Intelligence"
digest. We use a stronger model here because this is judgment work: prioritizing,
writing crisp prose a busy merchandiser will actually read, and recommending action.

Note the division of labor — a recurring FDE pattern:
  - cheap model does the HIGH-VOLUME structured extraction (extract.py)
  - strong model does the LOW-VOLUME synthesis (here)
This keeps cost down while keeping the final artifact high quality.

Usage:  python -m src.report
"""

import os
from datetime import date
from pathlib import Path

from src.aggregate import compute
from src.llm import chat, text_of

# A stronger model for the low-volume synthesis. Any OpenRouter model id works.
MODEL = os.getenv("REPORT_MODEL", "anthropic/claude-sonnet-4.5")
OUT = Path(__file__).resolve().parent.parent / "docs" / "merch_digest.md"

SYSTEM = (
    "You are a retail merchandising analyst writing the Monday intelligence digest for "
    "a busy merch team. Be concise, specific, and action-oriented. Lead with what's on "
    "fire. Use the data given; never invent numbers. For each flagged product give: the "
    "pattern, the evidence, and a recommended action (e.g. 'audit zipper supplier', "
    "'update size chart', 'pull from featured'). Plain Markdown, scannable, no fluff."
)


def build_prompt(products: list[dict]) -> str:
    lines = [f"Weekly review data as of {date.today().isoformat()}:\n"]
    for p in products:
        lines.append(
            f"- {p['product_name']} (id {p['product_id']}): "
            f"{p['n_reviews']} reviews, avg {p['avg_rating']}, "
            f"{p['neg_share']:.0%} negative, risk {p['risk_score']:.2f}. "
            f"Top issue category: {p['top_issue_category']} ×{p['top_issue_count']}. "
            f"Top issues: {'; '.join(p['top_issues']) or 'none'}. "
            f"Quotes: {' | '.join(p['sample_quotes']) or 'none'}."
        )
    lines.append(
        "\nWrite the digest: a 2-sentence executive summary, then a '## Flagged products' "
        "section (risk >= 0.4) with pattern/evidence/action for each, then a one-line "
        "'## Watchlist' for the rest."
    )
    return "\n".join(lines)


def run() -> str:
    products = compute()
    resp = chat(
        model=MODEL,
        # Generous budget: reasoning-capable models spend tokens thinking before the
        # actual prose, so a small limit gets truncated to empty content.
        max_tokens=6000,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": build_prompt(products)},
        ],
    )
    body = text_of(resp).strip()
    if not body:
        raise SystemExit(
            "Report model returned empty content (likely truncated by reasoning tokens). "
            "Raise max_tokens or use a non-reasoning REPORT_MODEL."
        )
    report = f"# NovaGoods — Weekly Merch Intelligence\n_{date.today().isoformat()}_\n\n{body}\n"
    OUT.write_text(report, encoding="utf-8")
    return str(OUT)


if __name__ == "__main__":
    path = run()
    print(f"Wrote digest → {path}")
