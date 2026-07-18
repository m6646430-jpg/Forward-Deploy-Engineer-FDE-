"""The demo dashboard — the thing you screen-record for your case study.

A single FastAPI app. The landing page is a risk-sorted product table; clicking a
product drills into its issues, quotes, and reviews. Kept to one file with inline
HTML on purpose: an FDE ships a working demo, not a frontend framework.

Run:  uvicorn app.main:app --reload   → http://127.0.0.1:8000
"""

import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from src.db import connect
from src.aggregate import compute

app = FastAPI(title="Review Intelligence")

PAGE = """
<!doctype html><html><head><meta charset="utf-8"><title>Review Intelligence</title>
<style>
  body {{ font: 15px/1.5 -apple-system, system-ui, sans-serif; margin: 2rem auto; max-width: 900px; color: #1a1a1a; }}
  h1 {{ margin-bottom: .2rem; }} .sub {{ color: #666; margin-top: 0; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ text-align: left; padding: .5rem .6rem; border-bottom: 1px solid #eee; }}
  th {{ font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: #888; }}
  .risk {{ font-weight: 600; }} .hi {{ color: #c0392b; }} .mid {{ color: #d68910; }} .lo {{ color: #27ae60; }}
  a {{ color: #2563eb; text-decoration: none; }} a:hover {{ text-decoration: underline; }}
  .pill {{ background: #f3f4f6; border-radius: 999px; padding: .1rem .55rem; font-size: 12px; }}
  .q {{ color: #444; font-style: italic; }}
</style></head><body>{body}</body></html>
"""


def risk_class(r: float) -> str:
    return "hi" if r >= 0.4 else "mid" if r >= 0.2 else "lo"


@app.get("/", response_class=HTMLResponse)
def home():
    products = compute()
    rows = ""
    for p in products:
        cls = risk_class(p["risk_score"])
        rows += (
            f"<tr><td class='risk {cls}'>{p['risk_score']:.2f}</td>"
            f"<td><a href='/product/{p['product_id']}'>{p['product_name']}</a></td>"
            f"<td>{p['n_reviews']}</td><td>{p['avg_rating']}</td>"
            f"<td>{p['neg_share']:.0%}</td>"
            f"<td><span class='pill'>{p['top_issue_category']} ×{p['top_issue_count']}</span></td></tr>"
        )
    body = (
        "<h1>NovaGoods · Review Intelligence</h1>"
        "<p class='sub'>Products sorted by risk. Click one to drill in.</p>"
        "<table><tr><th>Risk</th><th>Product</th><th>Reviews</th><th>Avg</th>"
        "<th>Neg</th><th>Top issue</th></tr>" + rows + "</table>"
    )
    return PAGE.format(body=body)


@app.get("/product/{product_id}", response_class=HTMLResponse)
def product(product_id: str):
    prod = next((p for p in compute() if p["product_id"] == product_id), None)
    if not prod:
        return PAGE.format(body="<p>Not found. <a href='/'>Back</a></p>")

    with connect() as conn:
        reviews = conn.execute(
            """SELECT r.rating, r.date, r.review_text, i.sentiment, i.summary
               FROM reviews r JOIN insights i ON i.review_id = r.review_id
               WHERE r.product_id = ? ORDER BY r.date""",
            (product_id,),
        ).fetchall()

    issues = "".join(f"<li>{i}</li>" for i in prod["top_issues"]) or "<li>none</li>"
    quotes = "".join(f"<p class='q'>“{q}”</p>" for q in prod["sample_quotes"])
    rlist = ""
    for r in reviews:
        rlist += (
            f"<tr><td>{r['rating']}★</td><td>{r['date']}</td>"
            f"<td>{r['sentiment']}</td><td>{r['summary']}</td></tr>"
        )
    body = (
        f"<p><a href='/'>← all products</a></p>"
        f"<h1>{prod['product_name']}</h1>"
        f"<p class='sub'>Risk {prod['risk_score']:.2f} · {prod['n_reviews']} reviews · "
        f"avg {prod['avg_rating']}★ · {prod['neg_share']:.0%} negative</p>"
        f"<h3>Top issues</h3><ul>{issues}</ul>"
        f"<h3>Evidence</h3>{quotes}"
        f"<h3>Reviews</h3><table><tr><th>Rating</th><th>Date</th>"
        f"<th>Sentiment</th><th>Summary</th></tr>{rlist}</table>"
    )
    return PAGE.format(body=body)


@app.get("/api/products")
def api_products():
    """JSON endpoint — because a real customer will want to pull this into their tools."""
    return compute()
