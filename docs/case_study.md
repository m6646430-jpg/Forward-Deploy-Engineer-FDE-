# Case study: Review Intelligence for a mid-size retailer

> Fill this in as you build. This document — not the code — is what you link from your
> resume and LinkedIn. Interviewers hire the narrative; the repo is the proof.

## 1. The problem (the customer's words)
_2–3 sentences. What hurt, who felt it, what it cost. Avoid jargon._

NovaGoods' merchandising team couldn't keep up with review volume, so recurring
defects and sizing problems surfaced only after they'd caused returns and refunds.

## 2. How I scoped it
_What you chose to build FIRST and what you deliberately left out. FDEs are judged on
ruthless scoping, not completeness._

- In scope: per-product issue extraction, a transparent risk score, a weekly digest,
  a drill-in dashboard.
- Explicitly out: real-time alerts, returns-data join, multi-language reviews. (Phase 2.)

## 3. What I built
_The architecture diagram (paste the one from the README) + one paragraph. Emphasize
the design decisions: cheap model for extraction, strong model for synthesis, an
explainable non-LLM risk score the customer can trust._

## 4. Results
_Concrete. Run the pipeline and quote real output._

- Surfaced the zipper-defect cluster on the TrailBlaze jacket from 4/7 reviews.
- Flagged 3 products above the risk threshold, ranked by severity.
- Weekly digest generated in <1 min for the full catalog; cost ≈ $X per run.
- (For a real dataset: "processed N,000 reviews in M minutes for $Z".)

## 5. What I'd do next
_Shows product thinking. The FDE feeds this back to the product team._

- Join returns/refund data to validate that flagged products actually cost money.
- Trend detection (rising sentiment week-over-week), not just snapshots.
- Let merchandisers thumbs-up/down flags to tune the risk weights.
- Package the extraction schema as a config the customer edits themselves.

## 6. Demo
_Link your 3-minute Loom/screen recording here._
