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
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def extract_one(review_text: str, product_name: str, attempts: int = 3) -> ReviewInsight:
    # Some models occasionally return truncated / malformed JSON in the tool call
    # (or no tool call at all). Retry a few times — a transient bad response almost
    # always succeeds on the next try. Raises the last error if all attempts fail.
    last_err: Exception | None = None
    for _ in range(attempts):
        try:
            resp = chat(
                model=MODEL,
                max_tokens=1500,
                tools=[EXTRACT_TOOL],
                # "required" = must call a tool, but we don't pin which by name. Pinning a
                # specific tool is rejected by some reasoning models (e.g. Kimi with
                # thinking on); since we define one tool, "required" forces it anyway.
                tool_choice="required",
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": f"Product: {product_name}\n\nReview:\n{review_text}"},
                ],
            )
            return ReviewInsight.model_validate(tool_args_of(resp))
        except Exception as e:  # malformed JSON, missing tool_call, validation error
            last_err = e
    raise last_err  # type: ignore[misc]


def _persist(conn, review_id: str, insight: ReviewInsight) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO insights
           (review_id, sentiment, issues_json, categories_json,
            praise_json, summary, evidence_quote)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            review_id,
            insight.sentiment.value,
            json.dumps(insight.issues),
            json.dumps([c.value for c in insight.issue_categories]),
            json.dumps(insight.praise),
            insight.summary,
            insight.evidence_quote,
        ),
    )
    conn.commit()


def run(limit: int | None = None, workers: int = 8) -> int:
    init_schema()
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

        total = len(rows)
        # The slow part is the network call, so run several concurrently (I/O-bound →
        # threads work well). DB writes happen here in the main thread as results land,
        # so SQLite is only ever touched from one thread.
        processed = failed = done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(extract_one, r["review_text"], r["product_name"]): r
                for r in rows
            }
            for fut in as_completed(futures):
                row = futures[fut]
                done += 1
                try:
                    insight = fut.result()
                except Exception as e:
                    # One bad review shouldn't kill the run. It stays un-extracted so a
                    # later re-run (idempotent) retries it.
                    failed += 1
                    print(f"  [{done}/{total}] ! {row['review_id']} skipped: {str(e)[:100]}")
                    continue
                _persist(conn, row["review_id"], insight)
                processed += 1
                print(f"  [{done}/{total}] ✓ {row['review_id']}  [{insight.sentiment.value}]  {insight.summary[:70]}")

    if failed:
        print(f"  ({failed} skipped — re-run to retry them)")
    return processed


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="only extract N reviews (use --limit 1 for a cheap smoke test)")
    ap.add_argument("--workers", type=int, default=8,
                    help="concurrent API calls (default 8; raise to go faster)")
    args = ap.parse_args()
    n = run(limit=args.limit, workers=args.workers)
    print(f"\nExtracted insights for {n} new review(s).")
