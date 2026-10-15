"""End-to-end validation of the PricePilot API via FastAPI TestClient (in-process).

Exercises the real endpoints and the real TabPFN + Gemma code paths, with no need for a
long-running server. Run: python3.11 scripts/validate.py
"""
from __future__ import annotations
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from pricepilot.api import app

client = TestClient(app)
fails = 0


def check(name, cond, detail=""):
    global fails
    mark = "PASS" if cond else "FAIL"
    if not cond:
        fails += 1
    print(f"[{mark}] {name}{(' - ' + detail) if detail else ''}")


# 1) health
r = client.get("/api/health")
check("GET /api/health 200", r.status_code == 200, str(r.status_code))
h = r.json()
check("health reports TabPFN predictor", "TabPFN" in h.get("predictor", ""), h.get("predictor"))
print(f"      ollama reachable: {h.get('ollama')}, model: {h.get('model')}")

# 2) meta
r = client.get("/api/meta")
check("GET /api/meta 200", r.status_code == 200, str(r.status_code))
m = r.json()
check("meta has 10 categories", len(m.get("categories", [])) == 10, str(len(m.get("categories", []))))
check("meta MAE is a sane dollar value", 0 < m.get("mae", 0) < 20, f"${m.get('mae')}")

# 3) a real price call (TabPFN + Gemma)
payload = {
    "item": "silver moon pendant", "category_id": 0, "material_id": 1,
    "size_score": 0.6, "make_hours": 3.0, "condition_score": 1.0,
    "seller_rating": 4.7, "photo_count": 3, "season_id": 1,
    "is_personalized": 0, "shipping_cost": 5.0,
}
t0 = time.time()
r = client.post("/api/price", json=payload)
dt = time.time() - t0
check("POST /api/price 200", r.status_code == 200, str(r.status_code))
d = r.json()
p = d.get("pricing", {})
check("price is positive", p.get("price", 0) > 0, f"${p.get('price')}")
check("range brackets the price", p.get("low", 0) <= p.get("price", 0) <= p.get("high", 1e9),
      f"${p.get('low')} <= ${p.get('price')} <= ${p.get('high')}")
check("what-if levers returned", len(p.get("whatifs", [])) >= 1, f"{len(p.get('whatifs', []))} levers")
l = d.get("listing", {})
check("listing has title", bool(l.get("title")), (l.get("title") or "")[:50])
check("listing has tags", len(l.get("tags", [])) >= 1, f"{len(l.get('tags', []))} tags")
check("listing source is gemma or fallback", l.get("source") in ("gemma", "offline-fallback"), l.get("source"))
print(f"      /api/price latency: {dt:.1f}s, source={l.get('source')}, price=${p.get('price')}")
print(f"      title: {l.get('title')}")
print(f"      top lever: {p.get('whatifs', [{}])[0] if p.get('whatifs') else 'none'}")

# 4) index + assets served
check("GET / serves HTML", client.get("/").status_code == 200)
check("GET /assets/app.js served", client.get("/assets/app.js").status_code == 200)
check("GET /assets/scene.js served", client.get("/assets/scene.js").status_code == 200)

# 5) offline fallback path (point Ollama at a dead host, listing must still return)
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:1"  # unreachable
import importlib
import pricepilot.listing as L
importlib.reload(L)
from types import SimpleNamespace
pr = SimpleNamespace(price=40.0, low=36.0, high=44.0, whatifs=[])
fb = L.write_listing("test item", "handmade jewelry", pr, timeout=3)
check("offline fallback returns a listing", bool(fb.get("title")) and fb.get("source") == "offline-fallback", fb.get("source"))

print()
print(f"RESULT: {'ALL PASSED' if fails == 0 else str(fails) + ' FAILED'}")
sys.exit(1 if fails else 0)
