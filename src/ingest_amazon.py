"""Stage 1 (real data) — ingest the Amazon Reviews 2023 dataset.

Source: McAuley-Lab/Amazon-Reviews-2023 (UC San Diego), hosted on Hugging Face,
no login required. https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023

The catch — and the FDE lesson: the category files are 300MB–9GB of plain JSONL.
You never download the whole thing to prototype. We STREAM the file line by line and
STOP EARLY once we've sampled enough. The 326MB file and the 9GB file cost us the same
because we only ever read the first few MB.

Two files, joined on `parent_asin`:
  - raw/review_categories/<Category>.jsonl        (the reviews; no product name!)
  - raw/meta_categories/meta_<Category>.jsonl     (product titles + catalog data)

Because reviews are scattered (not grouped by product), we scan a window of reviews,
tally by product, keep the top-N products that clear a minimum review count, and cap
per product. The sampled subset is cached to data/ so you only pay the scan once.

Usage:
  python -m src.ingest_amazon --category All_Beauty --products 15 --per-product 40 \
      --min-reviews 12 --scan 120000 --reset
  # re-run instantly from the cache:
  python -m src.ingest_amazon --local data/amazon_All_Beauty.jsonl --reset
"""

import argparse
import hashlib
import json
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src.db import connect, init_schema

BASE = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _stream_jsonl(url_or_path: str):
    """Yield parsed JSON objects from a JSONL source, streaming (never loads it all)."""
    if url_or_path.startswith("http"):
        req = urllib.request.Request(url_or_path, headers={"User-Agent": "fde-demo"})
        stream = urllib.request.urlopen(req)
        for raw in stream:  # iterates line by line over the network
            line = raw.decode("utf-8", "ignore").strip()
            if line:
                yield json.loads(line)
    else:
        with open(url_or_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


def _review_id(rec: dict) -> str:
    seed = f"{rec.get('parent_asin')}|{rec.get('user_id')}|{rec.get('timestamp')}"
    return "az_" + hashlib.md5(seed.encode()).hexdigest()[:16]


def _to_date(ts_ms) -> str:
    try:
        return datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc).date().isoformat()
    except Exception:
        return ""


def sample_reviews(source: str, scan: int, per_product: int, n_products: int,
                   min_reviews: int) -> list[dict]:
    """Scan up to `scan` reviews, return the pooled reviews of the top products."""
    counts: dict[str, int] = defaultdict(int)
    buffers: dict[str, list[dict]] = defaultdict(list)
    scanned = 0

    for rec in _stream_jsonl(source):
        asin = rec.get("parent_asin")
        text = (rec.get("text") or "").strip()
        if not asin or not text:
            continue
        counts[asin] += 1
        if len(buffers[asin]) < per_product:
            buffers[asin].append(rec)
        scanned += 1
        if scanned >= scan:
            break

    # rank products by how much review signal they have; keep the ones worth analyzing
    ranked = [a for a, c in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
              if c >= min_reviews][:n_products]
    print(f"  scanned {scanned:,} reviews across {len(counts):,} products; "
          f"selected {len(ranked)} products (>= {min_reviews} reviews each)")
    selected = []
    for asin in ranked:
        selected.extend(buffers[asin])
    return selected


def resolve_titles(source_meta: str, asins: set[str], scan: int = 400000) -> dict[str, str]:
    """Stream the meta file to grab product titles for just our selected asins."""
    titles: dict[str, str] = {}
    scanned = 0
    for rec in _stream_jsonl(source_meta):
        a = rec.get("parent_asin")
        if a in asins and a not in titles:
            titles[a] = (rec.get("title") or a).strip()[:120]
            if len(titles) == len(asins):
                break
        scanned += 1
        if scanned >= scan:
            break
    return titles


def ingest(reviews: list[dict], titles: dict[str, str], reset: bool) -> int:
    init_schema()
    with connect() as conn:
        if reset:
            conn.execute("DELETE FROM insights")
            conn.execute("DELETE FROM reviews")
        n = 0
        for rec in reviews:
            asin = rec["parent_asin"]
            title = (rec.get("title") or "").strip()
            body = (rec.get("text") or "").strip()
            review_text = f"{title}. {body}" if title else body
            conn.execute(
                """INSERT OR REPLACE INTO reviews
                   (review_id, product_id, product_name, rating, date, review_text)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    _review_id(rec),
                    asin,
                    titles.get(asin, asin),
                    int(round(rec["rating"])) if rec.get("rating") is not None else None,
                    _to_date(rec.get("timestamp")),
                    review_text,
                ),
            )
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="All_Beauty",
                    help="Amazon Reviews 2023 category, e.g. All_Beauty, Appliances")
    ap.add_argument("--local", help="path to a cached sampled .jsonl instead of streaming")
    ap.add_argument("--scan", type=int, default=120000,
                    help="max reviews to scan while sampling")
    ap.add_argument("--per-product", type=int, default=40)
    ap.add_argument("--products", type=int, default=15)
    ap.add_argument("--min-reviews", type=int, default=12)
    ap.add_argument("--reset", action="store_true",
                    help="clear existing reviews/insights before loading")
    args = ap.parse_args()

    if args.local:
        source = args.local
    else:
        source = f"{BASE}/raw/review_categories/{args.category}.jsonl"

    print(f"Sampling reviews from {source} ...")
    reviews = sample_reviews(source, args.scan, args.per_product,
                             args.products, args.min_reviews)
    asins = {r["parent_asin"] for r in reviews}

    if args.local:
        titles = {}  # local cache is expected to already carry usable text
    else:
        print("Resolving product titles from meta file ...")
        titles = resolve_titles(
            f"{BASE}/raw/meta_categories/meta_{args.category}.jsonl", asins)

    # cache the sampled raw subset so future runs are instant + offline
    if not args.local and reviews:
        cache = DATA_DIR / f"amazon_{args.category}.jsonl"
        with open(cache, "w", encoding="utf-8") as f:
            for r in reviews:
                r = dict(r)
                r["_resolved_title"] = titles.get(r["parent_asin"], r["parent_asin"])
                f.write(json.dumps(r) + "\n")
        print(f"  cached {len(reviews)} sampled reviews → {cache}")

    n = ingest(reviews, titles, args.reset)
    print(f"Ingested {n} Amazon reviews for {len(asins)} products into data/reviews.db")


if __name__ == "__main__":
    main()
