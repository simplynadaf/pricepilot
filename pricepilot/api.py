"""PricePilot API: wires the open stack together and serves the UI.

  POST /api/price  { item, category_id, material_id, size_score, make_hours,
                     condition_score, seller_rating, photo_count, season_id,
                     is_personalized, shipping_cost }
    -> { pricing {price, low, high, whatifs[], mae}, listing {title, description, tags,
         source, model} }

  GET  /api/meta    -> categories, materials, seasons, held-out MAE, model status
  GET  /api/health  -> model + ollama status

Everything runs locally: TabPFN-v2 (CPU) + Gemma via Ollama. No external calls.
"""
from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pricepilot.pricing import (
    PriceAgent, FEATURES, CATEGORY_NAMES, MATERIAL_NAMES, SEASON_NAMES,
)
from pricepilot.listing import write_listing, MODEL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")

app = FastAPI(title="PricePilot", version="1.0.0")
_agent = PriceAgent()


@app.on_event("startup")
def _warm():
    """Warm TabPFN (fit the in-context model) and compute the held-out MAE once at
    startup, so the first real pricing request is fast instead of paying the ~30s
    one-time cost mid-demo."""
    try:
        _agent._ensure_model()
        _agent.held_out_mae()
    except Exception:
        pass


class PriceIn(BaseModel):
    item: str = "handmade item"
    category_id: int = 0
    material_id: int = 1
    size_score: float = 0.6
    make_hours: float = 3.0
    condition_score: float = 1.0
    seller_rating: float = 4.7
    photo_count: int = 3
    season_id: int = 1
    is_personalized: int = 0
    shipping_cost: float = 5.0


def _ollama_ok() -> bool:
    import urllib.request
    try:
        urllib.request.urlopen(
            os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/tags", timeout=3
        )
        return True
    except Exception:
        return False


@app.get("/api/health")
def health():
    return {"status": "ok", "model": MODEL, "ollama": _ollama_ok(),
            "predictor": "TabPFN-v2 (CPU)"}


@app.get("/api/meta")
def meta():
    return {
        "categories": [{"id": k, "name": v} for k, v in CATEGORY_NAMES.items()],
        "materials": [{"id": k, "name": v} for k, v in MATERIAL_NAMES.items()],
        "seasons": [{"id": k, "name": v} for k, v in SEASON_NAMES.items()],
        "mae": round(_agent.held_out_mae(), 2),
        "ollama": _ollama_ok(),
        "model": MODEL,
    }


@app.post("/api/price")
def price(inp: PriceIn):
    feats = {c: getattr(inp, c) for c in FEATURES}
    pr = _agent.price(feats)
    category = CATEGORY_NAMES.get(inp.category_id, "handmade item")
    listing = write_listing(inp.item, category, pr)
    return JSONResponse({
        "pricing": {
            "price": pr.price,
            "low": pr.low,
            "high": pr.high,
            "currency": pr.currency,
            "mae": round(_agent.held_out_mae(), 2),
            "model": pr.model,
            "whatifs": [{"label": w.label, "delta": w.delta, "new_price": w.new_price}
                        for w in pr.whatifs],
        },
        "listing": listing,
        "category": category,
    })


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))


app.mount("/assets", StaticFiles(directory=os.path.join(WEB, "assets")), name="assets")
