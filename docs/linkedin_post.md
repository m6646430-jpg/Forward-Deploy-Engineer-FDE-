# LinkedIn Post Drafts

Two versions. Post ONE. Swap in your real demo link and repo URL. Post with the dashboard
screenshot or a 20-second clip of the demo — posts with visuals get far more reach.

---

## Version A — the story (recommended)

I've been teaching myself the Forward Deployed Engineer skillset, so I did what an FDE
actually does: took a messy, real-world dataset and a fake customer, and shipped something
that finds a problem worth money.

The "customer": a retailer drowning in product reviews. They have star averages — but an
average-looking product can be quietly bleeding returns, and nobody has time to read every
review.

So I built a pipeline: stream real Amazon reviews → an LLM reads each one and extracts
structured signal (defects, fit, quality, usability) → a transparent risk score ranks the
products → a weekly digest lands on the merch team's desk every Monday. It ran on 585 real
Appliances reviews.

What it found:

A reusable coffee filter with a perfectly unremarkable sub-4-star rating — ranked #1 by
risk (0.37). 31% of its reviews were negative, and they clustered on one theme: the filter
leaks, it's a hassle to use, and the coffee comes out weak. One customer summed up the
brand risk in a sentence: "Using a My K-cup filter with your own coffee really defeats the
purpose of having a Keurig." A star average buries that. Structured extraction pulls it to
the top — with an action: audit the gasket supplier, or delist the old model.

Three things I learned that feel like the actual job:
→ Don't download a 929MB file to prototype — stream it and stop early.
→ It worked on my test data but under-extracted on the real reviews; the model was leaving
  issues blank because my prompt was too cautious. Diagnosing that and fixing it was the
  real work — not the happy path.
→ Keep the risk score transparent, not a black box — the customer has to trust *why*
  something got flagged.

Code + write-up: [REPO URL]
3-min demo: [DEMO URL]

Open to Forward Deployed / AI Engineer conversations — if your team turns messy customer
data into working software, I'd love to talk.

#ForwardDeployedEngineer #AI #LLM #Python #BuildingInPublic

---

## Version B — short + punchy

A reusable coffee filter had a perfectly fine sub-4-star rating. It was also my #1
risk-flagged product: 31% negative reviews clustering on leaks, hassle, and weak coffee —
one customer said it "defeats the purpose of having a Keurig." Star averages hide that.
Structured data surfaces it.

I built a small pipeline to teach myself the Forward Deployed Engineer skillset: stream
real Amazon reviews → LLM extracts structured signal from each one → a transparent risk
score → a weekly report the merch team reads on Monday. 585 real reviews, a few dollars to
run — and the interesting part was fixing it when the first run under-extracted on real data.

Full write-up + code: [REPO URL] · Demo: [DEMO URL]

Open to FDE / AI Engineer roles. #ForwardDeployedEngineer #AI #LLM #Python

---

## Posting tips
- **Attach a visual.** Dashboard screenshot or a short screen clip. Text-only posts get
  buried. Put the demo video link in the FIRST comment if LinkedIn throttles link posts.
- **First line is the hook.** LinkedIn truncates after ~2 lines — the coffee-filter opener
  is designed to survive the "…see more" cut. Don't bury it under a preamble.
- **Reply to every comment in the first hour** — it's the single biggest reach lever.
- **Tag thoughtfully:** if you know anyone at a company hiring FDEs (Palantir, Anthropic,
  OpenAI, Sierra, etc.), a genuine comment from them beats any hashtag.
- **Don't overclaim.** "Teaching myself / a fake customer" is a strength here — it reads as
  initiative, not fraud. Keep it.
