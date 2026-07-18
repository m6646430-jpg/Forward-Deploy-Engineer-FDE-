# LinkedIn Post Drafts

Two versions. Post ONE. Swap in your real demo link and repo URL. Post with the dashboard
screenshot or a 20-second clip of the demo — posts with visuals get far more reach.

---

## Version A — the story (recommended)

I've been teaching myself the Forward Deployed Engineer skillset, so I did what an FDE
actually does: took a messy, real-world dataset and a fake customer, and shipped something
that finds a problem worth money.

The "customer": a retailer drowning in product reviews. They have star averages — but a
3.8-star product can be quietly bleeding returns, and nobody has time to read every review.

So I built a pipeline: stream real Amazon reviews → an LLM reads each one and extracts
structured signal (defects, fit, quality) → a transparent risk score ranks the products →
a weekly digest lands on the merch team's desk every Monday.

What it found on the Appliances data:

A reusable coffee filter sitting at an unremarkable 3.8 stars. But 9 of its 40 reviews were
negative — and 4 of those, from unrelated customers, said the exact same thing: the coffee
comes out weak and watery. "Brown water." "Too weak." A star average completely buries
that. Structured extraction makes it the headline — and turns it into an action: fix the
listing's expectations, or reconsider stocking the old model.

Three things I learned that feel like the actual job:
→ Don't download a 929MB file to prototype. Stream it and stop early.
→ Cheap model for high-volume extraction, strong model for the synthesis. Cost stayed
  around $2.
→ Make the risk score transparent Python, not a black box — the customer has to trust
  *why* something got flagged.

Code + write-up: [REPO URL]
3-min demo: [DEMO URL]

Open to Forward Deployed / AI Engineer conversations — if your team turns messy customer
data into working software, I'd love to talk.

#ForwardDeployedEngineer #AI #LLM #Python #BuildingInPublic

---

## Version B — short + punchy

A reusable coffee filter had a perfectly fine 3.8-star rating. It was also quietly failing:
4 of its 9 negative reviews, from unrelated customers, said the same thing — the coffee
comes out weak and watery. Star averages hide that. Structured data surfaces it.

I built a small pipeline to teach myself the Forward Deployed Engineer skillset: stream
real Amazon reviews → LLM extracts structured signal from each one → a transparent risk
score → a weekly report the merch team reads on Monday. ~$2 to run, real dataset, real
finding.

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
