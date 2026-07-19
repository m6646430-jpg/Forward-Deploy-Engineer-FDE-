"""Stage 2 — Extract (the LLM agent).

For each review, we ask the Anthropic API to return structured JSON matching ReviewInsight.
We force structure using a *tool definition* whose input_schema is our Pydantic
schema. This is the single most reliable way to get structured output from the Anthropic API:
the model must "call the tool" with args that match the schema, and the SDK/parse
step rejects anything malformed.

Key FDE lessons embedded here:
  - Cheap model for high-volume, low-judgment work (per-review extraction).
  - Idempotent: skip reviews already extracted, so re-runs are cheap and resumable.
  - Validate every response with Pydantic before trusting it.

Usage:  python -m src.extract
"""

from __future__ import annotations

import argparse
import json
import os

from src.db import connect, init_schema
from src.llm import chat, tool_args_of
from src.schema import ReviewInsight, REVIEW_INSIGHT_SCHEMA

# Any model on OpenRouter. Default is a cheap, fast model — perfect for per-review work.
MODEL = os.getenv("EXTRACT_MODEL", "anthropic/claude-haiku-4.5")

SYSTEM = (
    "You are a retail merchandising analyst. You read one customer product review "
    "and extract structured signal for the merch team. Be precise and literal: only "
    "record issues the review actually states. Do not invent problems. Keep phrases "
    "short and specific (e.g. 'zipper split after 2 weeks', not 'bad quality')."
)

# The tool is just a schema-carrier (OpenAI function-calling format). We never execute
# anything; we force the model to produce args matching our schema.
EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": "record_insight",
        "description": "Record the structured insight extracted from one review.",
        "parameters": REVIEW_INSIGHT_SCHEMA,
    },
}


def extract_one(review_text: str, product_name: str) -> ReviewInsight:
    resp = chat(
        model=MODEL,
        max_tokens=1024,
        tools=[EXTRACT_TOOL],
        # "required" = must call a tool, but we don't pin which by name. Pinning a
        # specific tool is rejected by some reasoning models (e.g. Kimi with thinking on);
        # since we define exactly one tool, "required" forces record_insight anyway.
        tool_choice="required",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Product: {product_name}\n\nReview:\n{review_text}"},
        ],
    )
    # With forced tool_choice, the first tool call holds our structured args.
    return ReviewInsight.model_validate(tool_args_of(resp))


def run(limit: int | None = None) -> int:
    init_schema()
    processed = 0
    with connect() as conn:
        # Only pull reviews we haven't extracted yet → idempotent + resumable.
        # `limit` lets you smoke-test on 1-2 reviews before paying for the full run.
        rows = conn.execute(
            """SELECT r.review_id, r.product_name, r.review_text
               FROM reviews r
               LEFT JOIN insights i ON i.review_id = r.review_id
               WHERE i.review_id IS NULL"""
            + (f" LIMIT {int(limit)}" if limit else "")
        ).fetchall()

        for row in rows:
            insight = extract_one(row["review_text"], row["product_name"])
            conn.execute(
                """INSERT OR REPLACE INTO insights
                   (review_id, sentiment, issues_json, categories_json,
                    praise_json, summary, evidence_quote)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["review_id"],
                    insight.sentiment.value,
                    json.dumps(insight.issues),
                    json.dumps([c.value for c in insight.issue_categories]),
                    json.dumps(insight.praise),
                    insight.summary,
                    insight.evidence_quote,
                ),
            )
            conn.commit()
            processed += 1
            print(f"  ✓ {row['review_id']}  [{insight.sentiment.value}]  {insight.summary}")

    return processed


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="only extract N reviews (use --limit 1 for a cheap smoke test)")
    args = ap.parse_args()
    n = run(limit=args.limit)
    print(f"\nExtracted insights for {n} new review(s).")
