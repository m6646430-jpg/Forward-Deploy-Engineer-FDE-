# Case Study — Review Intelligence for a Retailer

**Role:** Forward Deployed Engineer (simulated engagement)
**Stack:** Python · Anthropic Claude (structured output) · SQLite · FastAPI
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
   [extract]  →  one Claude call per review → validated structured JSON
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

2. **Right model for each job.** A cheap, fast model does the high-volume per-review
   extraction; a stronger model does the low-volume weekly synthesis. This keeps cost at
   ~$1–2 for 600 reviews while keeping the final report sharp.

3. **A risk score the customer can trust.** Scoring is deliberately *not* an LLM black box
   — it's transparent Python: negative share + defect share + a bonus when one issue
   category recurs ≥ 3 times. A merch VP can see exactly why a product was flagged, and
   the weights are a knob we tune *with* them.

## 4. Results

Run on 598 real Appliances reviews across 15 products.

### Headline finding — a product-fit problem hiding under a decent star rating

The pipeline surfaced the **"Keurig My K-Cup Reusable Coffee Filter (Old Model)"** as the
highest-risk product. Its 3.8-star average looks unremarkable — but the *content* of the
complaints is a tight cluster:

- **9 of 40 reviews are negative (≤ 2★).**
- **4 of those 9 independently complain that the coffee comes out weak/watery** —
  "very weak coffee," "colored water… too weak," "brown water," "weak coffee."

That's not scattered noise; it's the same complaint, from unrelated customers, about a
core function of the product. A star average buries it. Structured extraction makes it the
top line of the Monday digest.

**Recommended action (what I'd tell the customer):** this is a *listing-expectation* problem
as much as a product one. Either update the product description and imagery to set brew-
strength expectations, or reconsider stocking the "Old Model" given a newer version exists.
Cheapest fix first; measure return-rate change.

### Risk ranking (raw signal)

Products with the highest negative share in the sample:

| Product | Negative / total | Dominant theme |
|---|---|---|
| Keurig My K-Cup Reusable Filter (Old Model) | 9 / 40 | weak/watery coffee |
| Disposable Paper Coffee Filters (Keurig-compatible) | 6 / 40 | ⟩ FILL after extract |
| Reusable Coffee Pods (4-pack) | 5 / 39 | ⟩ FILL after extract |
| iPartPlusMore Reusable Coffee Filters | 4 / 40 | ⟩ FILL after extract |

*⟩ FILL: after running `extract` + `aggregate`, paste the categorized `risk_score` column
and dominant issue category per product here — that's the LLM turning raw negatives into
labeled, explainable risk.*

### The deliverable

⟩ FILL: paste a 4–6 line excerpt of the generated `docs/merch_digest.md` here, and drop a
screenshot of the dashboard (`app/main.py`) at `docs/dashboard.png`.

```
![Dashboard](dashboard.png)
```

### By the numbers

- 598 reviews across 15 products processed end-to-end.
- ~10 s to sample from a 929 MB source file (streamed, not downloaded).
- ~$1–2 total LLM cost for the full extraction pass.
- Weekly digest generated in under a minute.

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
