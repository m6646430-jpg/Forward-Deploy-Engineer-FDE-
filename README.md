# Review Intelligence — an FDE engagement simulation

> A Forward Deployed Engineer portfolio project. This repo is written as if it were a real
> customer engagement, because that is exactly the artifact that gets you hired.

## The customer

**NovaGoods** is a mid-size online retailer: ~2,000 SKUs, tens of thousands of customer
reviews across their catalog. Their merchandising team reads reviews manually and can't
keep up. By the time they notice "the zipper on the TrailBlaze jacket keeps breaking,"
they've already shipped 500 defective units and eaten the returns.

## The ask (verbatim from the customer)

> "Can you turn our review firehose into something our merch team actually reads every
> Monday? We don't need a star average — we have that. We need to know *what's going
> wrong, on which products, before it costs us money.*"

## What we built

A four-stage LLM pipeline:

1. **Ingest** — load raw reviews into SQLite, normalized.
2. **Extract** — an LLM agent reads each review and emits *structured* insight
   (defects, sizing/fit issues, praise, feature requests, sentiment).
3. **Aggregate** — roll insights up per product; compute a **risk score** that flags
   recurring defect clusters and rising negative sentiment.
4. **Report** — generate the weekly "Merch Intelligence" digest (Markdown/HTML), plus a
   web dashboard for drill-in.

```
reviews.csv → [ingest] → SQLite → [extract agent] → insights
                                       │
                                       ▼
                              [aggregate + risk] → [report] → digest + dashboard
```

## Quick start

```bash
cd retail-review-intelligence
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then paste your OpenRouter API key into .env

# run the pipeline end to end on the sample data
python -m src.ingest    data/sample_reviews.csv
python -m src.extract               # calls an LLM via OpenRouter; costs a few cents on sample data
python -m src.aggregate
python -m src.report                # writes docs/merch_digest.md

# view the dashboard
uvicorn app.main:app --reload       # http://127.0.0.1:8000
```

## Using real Amazon data (the real engagement)

The sample CSV is for a first smoke test. To work like an FDE, run the pipeline on the
**Amazon Reviews 2023** dataset (UC San Diego, hosted on Hugging Face, no login):

```bash
# stream + sample real reviews (only reads a few MB, not the 326MB file), then extract
python -m src.ingest_amazon --category All_Beauty --products 15 --per-product 40 \
    --min-reviews 12 --scan 120000 --reset
python -m src.extract
python -m src.aggregate
python -m src.report
uvicorn app.main:app --reload
```

Swap `--category` for any category (`Appliances`, `Cell_Phones_and_Accessories`,
`Toys_and_Games`, …). Full list: https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023

Key idea: the category files are 300MB–9GB of JSONL. `ingest_amazon.py` **streams and
stops early** — it reads reviews line-by-line, samples the top products, and aborts.
File size is irrelevant because we never read the whole thing. The sampled subset is
cached to `data/amazon_<category>.jsonl`, so re-runs are instant:

```bash
python -m src.ingest_amazon --local data/amazon_All_Beauty.jsonl --reset
```

Cost note: extraction runs one cheap-model call per review. 600 reviews ≈ a dollar or two.
Tune `--products` × `--per-product` to control both cost and how much signal each product has.

## Repo layout

| Path | What it is |
|---|---|
| `data/sample_reviews.csv` | Synthetic reviews with *deliberately planted* defect patterns, so you can see the pipeline find them. |
| `src/schema.py` | Pydantic models = the contract for what the LLM extracts. **Start reading here.** |
| `src/ingest.py` | CSV → SQLite (the sample data). |
| `src/ingest_amazon.py` | Stream + sample the real Amazon Reviews 2023 dataset. |
| `src/extract.py` | The extraction agent (LLM via OpenRouter, structured output). |
| `src/llm.py` | Tiny OpenRouter client (stdlib, no extra deps). |
| `src/aggregate.py` | Rollups + risk scoring. |
| `src/report.py` | Weekly digest generator. |
| `app/main.py` | FastAPI dashboard. |
| `docs/case_study.md` | The hiring artifact — problem → build → results → next. |

## The real deliverable

The code is half of it. The other half is `docs/case_study.md` + a 3-minute demo video.
That's what you link on your resume/LinkedIn. Interviewers hire the *narrative* of "I took
an unfamiliar business problem and shipped working software," and the code is the proof.
