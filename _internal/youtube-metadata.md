# PricePilot - SEO Title Research + YouTube Metadata (Week 2)

## SEO research (word-by-word intent)

### Seller-side search demand (high volume, high intent)
From live search results, the handmade-pricing space is dominated by:
- "how to price handmade items" / "Etsy pricing calculator" / "craft pricing formula"
- Pain phrasing that recurs: "undercharging", "what to charge", "pricing for profit"
- These are the terms a *buyer of this tool* searches. High commercial intent.

### Open/local AI search demand (strong, evergreen)
- "run AI locally", "no API costs", "no data leaving your machine", "offline AI", "for free",
  "Ollama", "open-weight". Every local-LLM article leans on these exact phrases.

### TabPFN space (niche, low competition = differentiation)
- TabPFN content is technical/research-heavy (arXiv, insurance pricing). Almost no
  consumer-facing "price prediction" product content. Our wedge: a *predicted price*, not a
  calculator or a document reader. In the Week 2 field, the invoice/receipt crowd is huge;
  TabPFN price-prediction is nearly empty.

### Title strategy
Blend ONE high-demand seller phrase (price / what to charge) + the open-local differentiator
(laptop / no API / private / free), keep it first-person + story (DEV winners are first-person
narratives), under ~70 chars for the article, punchy for YouTube.

---

## ARTICLE TITLE (dev.to) - chosen

**"My friend prices her Etsy candles by vibes. I built an open-weight model that prices them from data, on her laptop."**

Why: names a real persona (DEV winning pattern), "Etsy" + "prices" = search intent,
"open-weight model" + "on her laptop" = the differentiator, "by vibes" = the human hook.

Backup A/B options kept in the draft front matter:
- "I built a local AI that tells Etsy sellers what to charge, no account, no API bill"
- "Stop pricing your handmade shop by vibes: an open-weight price model that runs on your laptop"

Tags: devchallenge, hf26challenge, tabpfn, opensource

---

## YOUTUBE TITLE - chosen (front-loaded keyword + payoff + freshness, <70 chars)

**"I Built an Offline AI That Prices Your Etsy Shop (No API, 2026)"**  (60 chars)

A/B alternative (how-much hook):
"Local AI Tells Etsy Sellers What to Charge, No Cloud, No Bill (2026)"

Rationale: "Offline AI" + "Prices Your Etsy Shop" captures both the local-AI searcher and the
seller searcher; "No API" + "2026" add the evergreen + freshness signals that rank.

---

## YouTube Description

Most Etsy and eBay sellers price by gut, and get it wrong. Price a handmade item too high and
it sits; too low and you work for free. The tools that fix this charge a monthly fee and want
your whole sales history uploaded to their server. So I built PricePilot: it predicts what your
item will actually sell for, and writes the listing, entirely on your own laptop. No account,
no API bill, nothing uploaded.

Two open-weight models do the work. TabPFN-v2, an open tabular foundation model, predicts the
sell price in one CPU pass, with an honest range and a measured error (about $2.90 on this
data). Gemma 3, running locally through Ollama, turns that price into a ready-to-paste title,
description, and tags. It never invents a number, the price is always TabPFN's.

In this video I price three very different items, a silver pendant, a soy candle, and a leather
wallet, and the price genuinely changes with the inputs because the model is predicting, not
looking up a table. It also shows the what-if levers: exactly how much more photos, Q4 timing,
or personalization would add.

Built for the Hacktoberfest Open-Source AI Challenge 2026, Week 2: Side Hustle.

Live demo (fully interactive): https://simplynadaf.github.io/pricepilot/
Code (MIT, clone and run): https://github.com/simplynadaf/pricepilot

Chapters:
0:00  The money question: what do I charge?
0:12  PricePilot: price it right, then watch it sell
0:20  Item 1: a handmade silver pendant
0:45  Item 2: a soy candle (the levers matter most)
1:15  Item 3: a leather wallet (a very different price)
1:40  How it works and why open innovation matters

Tools used:
- TabPFN-v2 (open-weight tabular foundation model): https://github.com/PriorLabs/TabPFN
- Gemma 3 (open-weight LLM): https://ai.google.dev/gemma
- Ollama (local model runner): https://ollama.com

Follow me:
Portfolio: https://sarvarnadaf.com
LinkedIn: https://www.linkedin.com/in/sarvar04/
Dev.to: https://dev.to/sarvar_04
GitHub: https://github.com/simplynadaf
X: https://x.com/SarvarN_04

#OpenSourceAI #TabPFN #Gemma #OfflineAI #Hacktoberfest #Etsy

## Tags (YouTube, comma-separated)
offline AI, open weight model, TabPFN, Gemma 3, local LLM, Ollama, run AI offline, price
prediction, etsy pricing, how to price handmade, what to charge etsy, handmade pricing,
side hustle AI, hacktoberfest 2026, open source AI, no API AI, on-device AI, private AI,
tabular foundation model, local AI tutorial

## Thumbnail text (max 3 words, high contrast)
"PRICE IT RIGHT"  (or)  "WHAT TO CHARGE"
Pair with the emerald->gold cover; show the $ price result on the right.

## Pinned comment (first-hour seeding)
Code is MIT and runs fully offline: https://github.com/simplynadaf/pricepilot
Live interactive demo: https://simplynadaf.github.io/pricepilot/
The fun part was using TabPFN as a prediction AGENT, it re-queries itself to tell you which
levers (photos, Q4, personalization) raise the price and by how much. Ask me anything about
wiring an open tabular model to a local LLM.
