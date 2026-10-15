#!/usr/bin/env python3
"""Build PricePilot's sold-listings dataset.

A grounded, synthetic dataset of *sold* marketplace listings for handmade / resale
sellers (the Etsy/eBay persona in the Week 2 brief). Each row is one item that actually
sold, with the features a seller knows before listing and the price it sold for.

This is a TEACHING dataset: prices are generated from documented, realistic drivers
(category base price, materials, size, make-time, condition, seller rating, photo count,
season) plus noise, so the feature->price relationships are real and learnable by a
tabular model, without scraping any marketplace. A seller swaps in their own exported
sales CSV to make it theirs, that is the whole point of the open approach.

Columns written to data/sold_listings.csv:
    category_id, material_id, size_score, make_hours, condition_score,
    seller_rating, photo_count, season_id, is_personalized, shipping_cost,
    sold_price   (target, USD)

Run: python scripts/build_dataset.py
"""
from __future__ import annotations
import csv
import os
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sold_listings.csv")

# Human-readable category catalogue. base = typical sold price anchor (USD).
# These anchors are deliberately in the real ballpark for handmade/resale on Etsy/eBay.
CATEGORIES = [
    # id, name, base_price, price_spread
    (0, "handmade jewelry",        34,  18),
    (1, "hand-poured candle",      22,  10),
    (2, "ceramic mug / pottery",   28,  14),
    (3, "knitted / crochet item",  45,  22),
    (4, "digital print (download)", 8,   4),
    (5, "vintage clothing",        38,  26),
    (6, "leather goods",           62,  30),
    (7, "wooden home decor",       48,  25),
    (8, "sticker / enamel pin",    11,   5),
    (9, "soap / bath product",     16,   7),
]

MATERIALS = [
    # id, name, cost_multiplier (how much the material pushes price up)
    (0, "basic / recycled", 0.85),
    (1, "standard",          1.00),
    (2, "premium",           1.28),
    (3, "precious (silver/gold-fill/hardwood)", 1.70),
]

SEASONS = [  # id, name, demand_multiplier
    (0, "off-season", 0.92),
    (1, "spring",     1.00),
    (2, "summer",     1.03),
    (3, "holiday / Q4", 1.22),
]


def build(n: int = 900, seed: int = 7) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        cat = CATEGORIES[rng.integers(0, len(CATEGORIES))]
        mat = MATERIALS[rng.integers(0, len(MATERIALS))]
        season = SEASONS[rng.integers(0, len(SEASONS))]

        cat_id, _, base, spread = cat
        mat_id, _, mat_mult = mat
        season_id, _, season_mult = season

        size_score = float(rng.uniform(0.2, 1.0))        # relative size/complexity 0-1
        make_hours = float(np.round(rng.uniform(0.2, 12.0), 1))
        condition_score = float(rng.uniform(0.5, 1.0))   # 1.0 = new/mint, lower = used
        seller_rating = float(np.round(rng.uniform(3.6, 5.0), 2))
        photo_count = int(rng.integers(1, 11))
        is_personalized = int(rng.random() < 0.35)
        shipping_cost = float(np.round(rng.uniform(0, 12), 2))

        # Price model: base category price, moved by the drivers a seller controls.
        price = base
        price *= mat_mult
        price *= season_mult
        price *= (0.75 + 0.5 * size_score)               # bigger/more complex -> more
        price += make_hours * 2.1                         # labor shows up in price
        price *= (0.6 + 0.4 * condition_score)            # condition matters for resale
        price *= (0.9 + 0.06 * (seller_rating - 3.6) / 1.4 * 10 / 10)  # rating premium
        price *= (1.0 + 0.015 * min(photo_count, 8))      # good photos lift sold price
        price += 6.0 * is_personalized                    # personalization commands more
        price += 0.3 * shipping_cost                      # partial pass-through of shipping
        # category-level noise + idiosyncratic noise
        price += rng.normal(0, spread * 0.18)
        price = float(max(2.0, round(price, 2)))

        rows.append(dict(
            category_id=cat_id,
            material_id=mat_id,
            size_score=round(size_score, 3),
            make_hours=make_hours,
            condition_score=round(condition_score, 3),
            seller_rating=seller_rating,
            photo_count=photo_count,
            season_id=season_id,
            is_personalized=is_personalized,
            shipping_cost=shipping_cost,
            sold_price=price,
        ))
    return rows


def main():
    rows = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    prices = [r["sold_price"] for r in rows]
    print(f"wrote {len(rows)} sold listings -> {OUT}")
    print(f"price range ${min(prices):.2f} - ${max(prices):.2f}, mean ${sum(prices)/len(prices):.2f}")


if __name__ == "__main__":
    main()
