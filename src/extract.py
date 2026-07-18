"""Stage 2 — Extract (the LLM agent).

For each review, we ask Claude to return structured JSON matching ReviewInsight.
We force structure using a *tool definition* whose input_schema is our Pydantic
schema. This is the single most reliable way to get structured output from Claude:
the model must "call the tool" with args that match the schema, and the SDK/parse
step rejects anything malformed.

Key FDE lessons embedded here:
  - Cheap model for high-volume, low-judgment work (per-review extraction).
  - Idempotent: skip reviews already extracted, so re-runs are cheap and resumable.
  - Validate every response with Pydantic before trusting it.

Usage:  python -m src.extract
"""

import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv

from src.db import connect, init_schema
from src.schema import ReviewInsight, REVIEW_INSIGHT_SCHEMA

load_dotenv()

client = Anthropic()  # reads ANTHROPIC_API_KEY from env
MODEL = os.getenv("EXTRACT_MODEL", "claude-haiku-4-5-20251001")

SYSTEM = (
    "You are a retail merchandising analyst. You read one customer product review "
    "and extract structured signal for the merch team. Be precise and literal: only "
    "record issues the review actually states. Do not invent problems. Keep phrases "
    "short and specific (e.g. 'zipper split after 2 weeks', not 'bad quality')."
)

# The tool is just a schema-carrier. We never execute anything; we force the model
# to produce args matching our schema.
EXTRACT_TOOL = {
    "name": "record_insight",
    "description": "Record the structured insight extracted from one review.",
    "input_schema": REVIEW_INSIGHT_SCHEMA,
}


def extract_one(review_text: str, product_name: str) -> ReviewInsight:
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "record_insight"},
        messages=[
            {
                "role": "user",
                "content": f"Product: {product_name}\n\nReview:\n{review_text}",
            }
        ],
    )
    # With forced tool_choice, the first tool_use block holds our structured args.
    tool_use = next(b for b in msg.content if b.type == "tool_use")
    return ReviewInsight.model_validate(tool_use.input)


def run() -> int:
    init_schema()
    processed = 0
    with connect() as conn:
        # Only pull reviews we haven't extracted yet → idempotent + resumable.
        rows = conn.execute(
            """SELECT r.review_id, r.product_name, r.review_text
               FROM reviews r
               LEFT JOIN insights i ON i.review_id = r.review_id
               WHERE i.review_id IS NULL"""
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
    n = run()
    print(f"\nExtracted insights for {n} new review(s).")
