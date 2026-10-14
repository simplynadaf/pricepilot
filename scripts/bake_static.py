#!/usr/bin/env python3
"""Bake real TabPFN + Gemma results for a handful of preset example items.

The GitHub Pages preview is a static host (no Python backend), so it cannot run the live
models. Instead it serves these PRE-COMPUTED, REAL results so visitors can click through
genuine TabPFN-v2 + Gemma output. The live models still run on the user's own machine via
`python run.py`.

Writes web/static-data.json. Run: python scripts/bake_static.py
"""
from __future__ import annotations
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pricepilot.pricing import PriceAgent, FEATURES, CATEGORY_NAMES, MATERIAL_NAMES, SEASON_NAMES
from pricepilot.listing import write_listing

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "static-data.json")

# Preset example items a visitor can click through on the static demo.
PRESETS = [
    dict(key="silver moon pendant", item="silver moon pendant", category_id=0, material_id=3,
         size_score=0.5, make_hours=2.5, condition_score=1.0, seller_rating=4.8,
         photo_count=4, season_id=1, is_personalized=0, shipping_cost=4.0),
    dict(key="hand-poured lavender soy candle", item="hand-poured lavender soy candle", category_id=1,
         material_id=1, size_score=0.5, make_hours=1.5, condition_score=1.0, seller_rating=4.9,
         photo_count=3, season_id=3, is_personalized=0, shipping_cost=5.5),
    dict(key="vintage 90s denim jacket", item="vintage 90s denim jacket", category_id=5,
         material_id=1, size_score=0.8, make_hours=0.5, condition_score=0.8, seller_rating=4.6,
         photo_count=6, season_id=0, is_personalized=0, shipping_cost=8.0),
    dict(key="hand-stitched leather wallet", item="hand-stitched leather wallet", category_id=6,
         material_id=3, size_score=0.4, make_hours=5.0, condition_score=1.0, seller_rating=4.9,
         photo_count=7, season_id=3, is_personalized=1, shipping_cost=4.5),
    dict(key="crochet baby blanket", item="crochet baby blanket", category_id=3,
         material_id=2, size_score=0.9, make_hours=10.0, condition_score=1.0, seller_rating=4.7,
         photo_count=5, season_id=1, is_personalized=1, shipping_cost=7.0),
]


def main():
    agent = PriceAgent()
    agent._ensure_model()
    mae = round(agent.held_out_mae(), 2)
    results = {}
    for preset in PRESETS:
        feats = {c: preset[c] for c in FEATURES}
        pr = agent.price(feats)
        category = CATEGORY_NAMES.get(preset["category_id"], "handmade item")
        listing = write_listing(preset["item"], category, pr)
        results[preset["key"]] = {
            "item": preset["item"],
            "category": category,
            "inputs": {**feats, "item": preset["item"]},
            "pricing": {
                "price": pr.price, "low": pr.low, "high": pr.high, "currency": pr.currency,
                "mae": mae, "model": pr.model,
                "whatifs": [{"label": w.label, "delta": w.delta, "new_price": w.new_price} for w in pr.whatifs],
            },
            "listing": listing,
        }
        print(f"baked: {preset['key']} -> ${pr.price} ({listing['source']})")

    payload = {
        "mae": mae,
        "categories": [{"id": k, "name": v} for k, v in CATEGORY_NAMES.items()],
        "materials": [{"id": k, "name": v} for k, v in MATERIAL_NAMES.items()],
        "seasons": [{"id": k, "name": v} for k, v in SEASON_NAMES.items()],
        "presets": [{"key": p["key"], "item": p["item"]} for p in PRESETS],
        "results": results,
    }
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nwrote {OUT} ({len(results)} presets, MAE ${mae})")


if __name__ == "__main__":
    main()
