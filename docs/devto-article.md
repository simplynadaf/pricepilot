---
title: "My friend prices her Etsy candles by vibes. I built an open-weight model that prices them from data, on her laptop."
published: false
tags: devchallenge, hf26challenge, tabpfn, opensource
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

![PricePilot: price it right, then watch it sell](docs/banner.png)

My friend runs a tiny candle shop on Etsy. Forty-odd listings, a day job, and a pricing
strategy she described to me, without a trace of irony, as **"vibes."**

She is not wrong to struggle. There is no sticker price for a hand-poured soy candle. The
right number depends on the scent, the size, the wax, how long it took, the season, how many
photos she shot, how her shop is rated, a dozen little things that interact. Price it $4 too
high and it sits until the wax degrades. Price it $4 too low and she is paying Etsy fees to
work for free. She has lost real money both ways.

The tools that promise to fix this are closed SaaS products: a monthly fee, and an upload of
her entire sales history to someone else's server so they can rent her a number back. For a
shop that clears maybe $300 a month, that is a bad trade twice over, the cost, and handing
the one thing that is actually hers (what sells, at what margin) to a stranger's cloud.

So I built her **PricePilot**: a pricing copilot that runs entirely on her laptop, predicts
what an item will sell for from sold-listings data, and writes the listing, with no account,
no API bill, and nothing uploaded anywhere.

## What I Built

**PricePilot turns one short form into three things a seller can act on immediately:**

1. **A price with an honest range.** Not a single false-precise number, a predicted sell
   price *and* the 10–90% band around it, plus a measured error so you know how much to trust
   it.
2. **The levers that raise it.** It doesn't just score the listing; it tells her *what to
   change and by how much*: "add photos **+$2**", "offer personalization **+$5**", "list in
   the Q4 season **+$8**", "use premium wax **+$12**", ranked by dollar impact.
3. **A ready-to-paste listing.** Title, description, and eight search tags, written to match
   the predicted price.

**Who would pay for it:** independent Etsy / eBay / marketplace sellers, the exact "side
hustle" person this week is about. The thing it fixes (what do I charge?) is the thing that
most directly decides whether the hustle makes money.

## Demo

**🔗 Live demo (fully interactive):** [simplynadaf.github.io/pricepilot](https://simplynadaf.github.io/pricepilot/)
**🎥 Video walkthrough:** [watch on YouTube](https://youtu.be/VIDEO_ID)

> The hosted demo is interactive end to end: every field is editable and the price updates
> instantly, powered by an in-browser estimate that mirrors the model. For the actual
> **TabPFN-v2** prediction with **Gemma 3** writing the listing, clone the repo and
> `python run.py`, fully offline. That is the whole point of PricePilot.

Describe an item the way you'd list it (category, materials, size, hours to make, condition,
photos, season) and PricePilot prices it and drafts the listing in one shot.

![PricePilot result: a predicted price with its 10–90% range, the ranked what-if levers, and a listing with title, description, and tags](docs/screenshots/result.png)

## Code

{% github https://github.com/simplynadaf/pricepilot %}

## How I Built It

PricePilot is **two open-weight models doing one honest job each, locally.**

![How it works: you describe the item, TabPFN-v2 predicts the price, Gemma writes the listing](docs/screenshots/how.png)

### The price: TabPFN-v2 as a prediction *agent*

Pricing is a textbook small-data tabular problem (a few hundred past sold listings, ten
features, one continuous target), which is exactly what
[**TabPFN-v2**](https://github.com/PriorLabs/TabPFN), Prior Labs' open-weight tabular
foundation model, is built for. It predicts in a single CPU forward pass with **no per-dataset
training**.

But Prior Labs explicitly favors TabPFN used *inside a wider prediction agent*, not as a
one-shot regressor, so that's what I built. PricePilot:

- predicts the sell price **with a calibrated 10–90% range** from TabPFN's output quantiles,
- then runs a small **what-if loop**: it re-queries TabPFN under single-feature changes a
  seller actually controls (more photos, personalization, Q4 timing, better condition,
  premium materials) and ranks them by the dollar delta, all in **one batched forward pass**
  so it stays fast on CPU,
- and reports a **held-out mean absolute error** so every number is measured, not asserted.

On the sample dataset, TabPFN predicts held-out sold prices with an **MAE of about $2.90** on
items averaging ~$54, roughly 5% error, with zero training time. That honesty number is the
whole point: she can see how much to trust it.

```python
# the prediction agent, in essence: predict, then re-query to explain the number
mean, low, high = self._predict_one(feats)          # price + 10-90% range
preds = self._predict_rows(whatif_rows)             # ONE batched pass for all levers
levers = sorted(zip(labels, preds - mean), key=..., reverse=True)
```

### The listing: Gemma 3, grounded on the number

A local [**Gemma 3**](https://ai.google.dev/gemma) model (open-weight, served by
[Ollama](https://ollama.com)) turns the item and that *exact* predicted price into a title,
description, and tags. It is **told** the price and told never to invent a different one, the
number is always TabPFN's, Gemma just writes the copy around it.

### The safety net

If Ollama isn't running, a deterministic template writes a correct listing from the same
price, so she is never staring at a spinner. The whole stack (FastAPI, a no-build premium
front end, both models) runs on `localhost`. I verified the offline path by pointing the
Ollama host at a dead port and confirming the listing still came back.

## Why Does Open Innovation Matter?

This is the part that made the project worth building, and every point is something a **closed
API would have taken away:**

- **Her sales data stays hers.** What sells, at what margin, is her entire edge. PricePilot
  never uploads it. A closed pricing tool would turn her shop's history into *its* training
  data.
- **$0 per listing.** Open weights mean no per-call fee. She can reprice her whole shop every
  week and the bill is nothing. A subscription would eat the margin the tool is supposed to
  protect.
- **It can learn *her* niche.** She can drop in her own exported Etsy sales CSV and the model
  fits her corner of the market (soy candles in her price band) where a general API trained
  on "everything" is mediocre. The open approach is what lets the long tail have a model that
  fits it.
- **No lock-in.** The listing writer points at any open-weight model Ollama runs; the
  predictor can be retrained. She owns the stack, not a line on someone's pricing page.

A frost date, a race time, a candle price: the pattern that keeps winning this Hacktoberfest
is the same. **A small, open model, running where your data already lives, beats a big closed
one you have to pay and trust.**

## Would Someone Pay For It?

I built PricePilot for a real person: a friend who runs a small candle shop on Etsy and
genuinely prices by "vibes." I have not sat her down with the finished build yet (that is my
next step, and I will update this post with what she says), so I will not invent a reaction
here. What I *can* say honestly is why I think she, and sellers like her, would pay:

- **The pain is the money.** Pricing is the single decision that most directly sets whether a
  handmade shop earns or loses on each sale. A tool that gives a defensible number, with a
  range and a measured error, targets the exact spot where a side hustle leaks money.
- **The alternative already costs money.** Sellers pay $10–30/month for closed pricing SaaS
  that also wants their sales history uploaded. PricePilot does the same job for $0 and keeps
  the data on their laptop. "Same outcome, free, private" is an easy yes.
- **It answers a question they ask constantly.** "What do I charge, and what do I write?" is a
  daily question for an active seller. PricePilot answers both in one shot.

My honest take: I would not charge for the current build, because the whole point is that it
runs free on the seller's own machine. The thing a seller would actually pay for is the time
and the second-guessing it removes, and that is what I will test with her next.

## Prize Categories

- **Best Use of TabPFN:** TabPFN-v2 is the core: it predicts the price, provides the
  calibrated range, and is wrapped in a what-if **prediction agent** that re-queries the model
  to explain which levers move the number. Accuracy is reported as a held-out MAE (~$2.90), so
  the claim is measured, not asserted.

---

*Built with open weights, on a laptop, for a friend who prices by vibes. Made with 🤍 by
[Sarvar](https://sarvarnadaf.com).*
