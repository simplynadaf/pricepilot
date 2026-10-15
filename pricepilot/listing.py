"""PricePilot listing writer: Gemma 3 (open-weight) via local Ollama.

Supporting layer. TabPFN decides the PRICE; Gemma turns the item + that price into a
conversion-focused marketplace listing (title, description, tags). Gemma is told the
price and the what-if levers; it never invents a number.

Runs fully offline against local Ollama. The model is swappable via PRICEPILOT_MODEL
(any Ollama open-weight model). If Ollama is unreachable, a deterministic template writes
a correct listing so the app never hard-fails and the seller is never blocked.
"""
from __future__ import annotations
import json
import os
import re
import urllib.request

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = os.environ.get("PRICEPILOT_MODEL", "gemma3:1b")

SYSTEM = (
    "You are PricePilot, a copywriter for independent marketplace sellers (Etsy, eBay). "
    "You are given an item, its category, and a DATA-DRIVEN suggested price with a range. "
    "Write a listing that helps it sell. Return STRICT JSON with keys: title, description, "
    "tags. Rules: title <= 80 characters, benefit-led, no ALL CAPS. description: 2-3 warm, "
    "concrete sentences (not paragraphs), mention one reason it is worth the price. tags: 8 "
    "lowercase search tags as an array, no '#'. Use the price you are given; never invent a "
    "different number. Output JSON only, no preamble, no markdown fences."
)


def _rule_based(item: str, category: str, pricing) -> dict:
    """Deterministic fallback listing, correct and useful with no model."""
    # Avoid duplicating a word that's already in the item/category (e.g. "handmade").
    cat = category.title()
    title = f"{item.title()} · {cat}"
    if "handmade" not in title.lower() and "handmade" not in cat.lower():
        title = f"Handmade {title}"
    title = title[:80]
    desc = (
        f"A carefully made {item.lower()} from our {category.lower()} range. "
        f"Priced at ${pricing.price}, in line with what comparable pieces sell for "
        f"(typically ${pricing.low}-${pricing.high}).\n\n"
        f"Each one is checked by hand before it ships. Message us for personalization or "
        f"bundle options."
    )
    base = re.sub(r"[^a-z0-9 ]", "", f"{item} {category}".lower()).split()
    tags = list(dict.fromkeys(base + ["handmade", "gift", "small shop", "unique"]))[:8]
    return {"title": title, "description": desc, "tags": tags}


def _extract_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        if isinstance(obj, dict) and {"title", "description", "tags"} <= set(obj):
            if isinstance(obj["tags"], str):
                obj["tags"] = [t.strip() for t in re.split(r"[,\n]", obj["tags"]) if t.strip()]
            return obj
    except Exception:
        return None
    return None


def write_listing(item: str, category: str, pricing, timeout: float = 60.0) -> dict:
    """Return {title, description, tags, source, model}. source is 'gemma' or 'offline'.

    Keeps the generation short (num_predict) and the timeout tight so a slow local CPU
    degrades gracefully to the deterministic fallback instead of blocking the seller."""
    levers = ", ".join(f"{w.label} (+${w.delta})" for w in pricing.whatifs[:3]) or "none"
    user = (
        f"Item: {item}\nCategory: {category}\n"
        f"Suggested price: ${pricing.price} (likely ${pricing.low}-${pricing.high})\n"
        f"Top levers that raise the price: {levers}\n"
        f"Write the JSON listing."
    )
    payload = {
        "model": MODEL,
        "prompt": f"{SYSTEM}\n\n{user}\n\nJSON:",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.4, "num_predict": 220},
    }
    try:
        req = urllib.request.Request(
            f"{OLLAMA}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            out = json.loads(resp.read())
        parsed = _extract_json((out.get("response") or "").strip())
        if parsed:
            parsed["tags"] = [str(t).lstrip("#").strip().lower() for t in parsed.get("tags", [])][:8]
            parsed["title"] = str(parsed.get("title", ""))[:80]
            parsed["source"] = "gemma"
            parsed["model"] = MODEL
            return parsed
    except Exception:
        pass
    fb = _rule_based(item, category, pricing)
    fb["source"] = "offline-fallback"
    fb["model"] = "rule-based"
    return fb


if __name__ == "__main__":
    from types import SimpleNamespace
    pr = SimpleNamespace(price=43.56, low=39.44, high=47.68, whatifs=[
        SimpleNamespace(label="Use premium materials", delta=12.09),
        SimpleNamespace(label="List in the holiday / Q4 season", delta=8.18),
    ])
    print(json.dumps(write_listing("silver moon pendant", "handmade jewelry", pr), indent=2))
