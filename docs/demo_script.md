# 3-Minute Demo Script — Review Intelligence

**Goal:** show an FDE loop — messy real data → working software → an insight the customer
can act on. Talk to the *business value*, let the code prove it. Practice once out loud;
it should feel like showing a colleague, not reading.

**Before you hit record**
- Run the pipeline so output exists: `extract` → `aggregate` → `report`.
- Have three things open in tabs: (1) the dashboard at `localhost:8000`, (2)
  `docs/merch_digest.md` rendered, (3) a terminal in the project.
- Record at 1280×800, cursor-highlight on. Speak ~15% slower than feels natural.

---

## [0:00–0:20] · Hook — the customer's problem

> "Imagine you're the merchandising team at a mid-size online retailer. You sell thousands
> of appliance accessories, and you get thousands of customer reviews a week. You have the
> star averages — but a 3.8-star product could be fine, or it could be quietly bleeding
> money. Nobody has time to read every review. That's the problem I built for."

**[ON SCREEN]** Terminal, project open. Nothing fancy — just you talking over it.

## [0:20–0:45] · What it is + the data

> "This is a pipeline that turns that review firehose into a weekly report the merch team
> actually reads. I ran it on real data — the Amazon Reviews 2023 dataset, the Appliances
> category. One detail I'm proud of: that category file is almost a gigabyte. I don't
> download it — I stream it and stop early once I've sampled enough."

**[ON SCREEN]** Run the ingest so they see it live:
```
python3 -m src.ingest_amazon --category Appliances --products 15 --per-product 40 --min-reviews 12 --scan 120000 --reset
```
> "Six hundred reviews across fifteen products, sampled from a 929-megabyte file, in about
> ten seconds."

## [0:45–1:15] · The engine — structured extraction

> "The core is an LLM agent that reads each review and pulls out structured signal:
> defects, fit issues, quality complaints, praise, and a short evidence quote. Not a star
> rating — the actual *reason* behind it."

**[ON SCREEN]** Run (or show a pre-run of) extract so a few lines stream:
```
python3 -m src.extract
```
> "One cheap-model call per review — the whole pass costs a dollar or two. Then a second,
> deterministic stage rolls those up into a risk score per product. That score is plain,
> transparent logic, not a black box — because a merch VP has to trust *why* something got
> flagged."

## [1:15–2:15] · The finding — this is the heart of the demo

**[ON SCREEN]** Switch to the dashboard. Point at the top row.

> "Here's the payoff. The dashboard sorts products by risk. Top of the list: the Keurig
> reusable coffee filter. Its star average is 3.8 — totally unremarkable, you'd walk right
> past it. But watch what happens when I click in."

**[ON SCREEN]** Click the Keurig product → drill-in page. Point at the issues + quotes.

> "Nine of its forty reviews are negative — and they're not complaining about random
> things. Four of them, independently, say the same thing: the coffee comes out weak and
> watery. 'Brown water.' 'Colored water, too weak.' That's not noise — that's one specific
> failure, from unrelated customers, about the product's whole job."

> "A star average completely buries this. Structured extraction makes it the headline."

## [2:15–2:40] · The deliverable + the recommendation

**[ON SCREEN]** Switch to the rendered `merch_digest.md`.

> "And this all lands as a weekly digest — the thing the merch team opens on Monday.
> Flagged products, the pattern, the evidence, and a recommended action. For the Keurig
> filter: this is a listing-expectations problem as much as a product one. Update the
> description to set brew-strength expectations, or reconsider stocking the old model —
> and measure the return rate."

## [2:40–3:00] · Close — thinking like an FDE

> "The point isn't the code — it's the loop: take an unfamiliar business and messy,
> real-world data, ship something that works fast, and hand the customer an insight they
> can act on. Next steps would be joining returns data to put a dollar figure on each flag,
> and week-over-week trend detection. Thanks for watching."

---

## Delivery tips
- **Lead with the business problem, not the tech.** The first 20 seconds decide whether
  they keep watching.
- **The Keurig drill-in is the money shot** — slow down there, let the quotes land.
- **Say the recommended action out loud.** "What should the customer do" is what separates
  an FDE from a data analyst.
- If a live command feels risky on camera, pre-run it and just scroll the output — nobody
  minds, and it keeps you under 3:00.
- End on the *loop*, not a feature list. That's the sentence they'll remember.
