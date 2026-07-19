# Case Study — Review Intelligence for a Retailer

**Role:** Forward Deployed Engineer (simulated engagement)
**Stack:** Python · OpenRouter (LLM API, structured output) · SQLite · FastAPI
**Data:** Amazon Reviews 2023 (UC San Diego / McAuley Lab), *Appliances* category
**Repo:** https://github.com/m6646430-jpg/Forward-Deploy-Engineer-FDE-

> Three green TODO markers below (⟩ FILL) are the only things left to complete after you
> run the paid LLM pipeline once. Everything else is real and already computed.

---

## 1. The problem

**NovaGoods** (a stand-in mid-size online retailer) sells thousands of appliance
accessories — water filters, coffee pods, replacement parts. Their merchandising team
reads customer reviews by hand and can't keep up. By the time a recurring defect or a
"this product doesn't do what the listing promises" pattern is obvious, they've already
absorbed returns, refunds, and bad-review drag on the listing.

**The ask, in their words:**
> "Turn our review firehose into something the merch team reads every Monday. We already
> have the star average. We need to know *what's going wrong, on which products, before
> it costs us money.*"

## 2. How I scoped it

An FDE is judged on ruthless scoping, not completeness. For the first cut I committed to:

- **In scope:** per-review structured extraction (defects, fit, quality, praise),
  a *transparent* per-product risk score, a weekly digest, and a drill-in dashboard.
- **Deliberately out (phase 2):** real-time alerting, joining returns/refund data,
  multi-language reviews, and trend-over-time. Shipping the Monday digest first proves
  the value; the rest is follow-on.

## 3. What I built

A four-stage pipeline. Each stage is small, independently runnable, and resumable.

```
Amazon Reviews (JSONL, 300MB–9GB)
        │  stream + sample (never download the whole file)
        ▼
   [ingest]  →  SQLite
        │
        ▼
   [extract]  →  one LLM call per review → validated structured JSON
        │        (defects, sizing/fit, quality, praise, sentiment, evidence quote)
        ▼
   [aggregate]  →  per-product rollups + a transparent risk score  (plain Python, no LLM)
        │
        ▼
   [report]  →  weekly "Merch Intelligence" digest  +  FastAPI dashboard
```

**Three engineering decisions worth calling out** (these are the interview talking points):

1. **Stream, don't download.** The category files are 300 MB–9 GB of JSONL. The ingester
   reads reviews line-by-line over the network and *stops early* once it has sampled
   enough. For the Appliances demo it scanned 120,000 reviews — a small fraction of the
   929 MB file — in ~10 seconds, then cached the sample so re-runs are instant.

2. **Provider-agnostic by design.** All LLM calls go through one OpenAI-compatible client
   (`src/llm.py`), so the model is a one-line `.env` change. That mattered in practice: I
   started on a reasoning model for the report, found it was too slow and burned its token
   budget on hidden reasoning (empty output), and swapped to a faster model in one edit —
   no code change. Structured extraction is forced via a tool schema and validated with
   Pydantic, with per-review retries for the occasional malformed response.

3. **A risk score the customer can trust.** Scoring is deliberately *not* an LLM black box
   — it's transparent Python: negative share + defect share + a bonus when one issue
   category recurs ≥ 3 times. A merch VP can see exactly why a product was flagged, and
   the weights are a knob we tune *with* them.

## 4. Results

Run end-to-end on **598 real Appliances reviews across 15 products** (585 successfully
structured, 98%). Extraction: Kimi K2.5 via OpenRouter; synthesis: same.

### Headline finding — a "defeats the purpose" product hiding under an average rating

The pipeline ranked the **"Keurig My K-Cup Reusable Coffee Filter (Old Model)"** as the
highest-risk product: **risk 0.37, 31% negative sentiment**, with a recurring **usability**
cluster (4+ reviews). The complaints aren't scattered — they converge on the product
failing at its core job:

- Leaking: *"leaking water flows over basket rim,"* *"missing compliant gasket/seal,"*
  *"rubber gasket slides up post."*
- Effort/usability: *"extensive prep and cleaning required,"* *"tricky screw-on assembly."*
- Weak output: *"inconsistent coffee strength,"* *"when I brewed first cup it was brown water."*

One review sums up the risk to the brand in a sentence:
> "Using a My K-cup filter assembly with your own coffee really defeats the purpose of having a Keurig."

A star average buries this. Structured extraction makes it the top line of the Monday digest.

**Recommended action:** audit the gasket supplier's tolerances and mold specs; if the
current revision already fixes the seal, delist the legacy SKU. Measure return-rate change.

### Risk ranking (LLM-labeled, explainable)

| Product | Risk | Negative | Dominant cluster |
|---|---|---|---|
| Keurig My K-Cup Reusable Filter (Old Model) | **0.37** | 31% | usability — seal failure, leaks |
| Reusable Coffee Pods (4-pack) | 0.34 | 23% | usability — brew spray, fit |
| Disposable Paper Coffee Filters (Keurig) | 0.33 | 25% | usability — wet-handling, 2.0 incompatibility |
| Linda's Silicone Stove Gap Covers | 0.32 | 23% | sizing_fit — doesn't stay put, safety |

The risk score is transparent Python (negative share + defect share + a bonus when one
category recurs ≥ 3×), so every flag is explainable — no black box.

### The engineering story worth telling (this is the real FDE moment)

The first full run on real data produced **flat risk scores and empty issue clusters** —
the model was capturing sentiment correctly but leaving the structured `issues`/`categories`
empty, because the original prompt ("do not invent problems") made it too conservative.
I diagnosed it by inspecting one product's raw extractions, tested a hardened prompt on a
2-review sample until issues + categories populated reliably, then **re-extracted only the
135 reviews that mattered** (non-positive) rather than redoing all 598. The risk model then
surfaced the real patterns above.

*It worked on the synthetic demo data but behaved differently on the customer's real,
messy data — so I diagnosed, fixed, and re-ran.* That loop is the job.

### The deliverable

Excerpt of the auto-generated weekly digest (`docs/merch_digest.md`):

> **Keurig My K-Cup Reusable Coffee Filter - Old Model**
> **Pattern:** Seal failure and dimensional tolerance gaps causing leakage and grind contamination.
> **Evidence:** 39 reviews, 31% negative, risk 0.37; "leaking water flows over basket rim," "missing compliant gasket/seal," "rubber gasket slides up post."
> **Action:** Audit gasket supplier tolerances and injection mold specs; delist legacy model if current revision resolves failures.

_Dashboard screenshot: run `uvicorn app.main:app --reload`, then save it to `docs/dashboard.png`._

### By the numbers

- 598 reviews / 15 products processed; 585 structured (98% after retries).
- Sampled from a **929 MB** source file in ~10 s (streamed, never downloaded).
- Total LLM cost: a few dollars (Kimi K2.5 via OpenRouter).
- Weekly digest generated in one call.

## 5. What I'd do next

The FDE feeds the roadmap back to the product team:

- **Join returns/refund data** to prove flagged products actually cost money (turns a
  "signal" into a dollar figure — the thing that gets budget).
- **Trend detection:** rising negative share week-over-week, not just a snapshot.
- **Human-in-the-loop tuning:** let merchandisers thumbs-up/down a flag to auto-adjust the
  risk weights.
- **Customer-editable schema:** expose the extraction taxonomy as config so each customer
  defines the buckets they care about, without a code change.

## 6. Demo

⟩ FILL: link a 3-minute screen recording (Loom/YouTube-unlisted) walking through the
Keurig finding on the live dashboard.

---

*Built as a portfolio project to demonstrate the core FDE loop: take an unfamiliar
business problem and unfamiliar, messy real-world data → ship working software fast →
surface an insight the customer can act on.*
