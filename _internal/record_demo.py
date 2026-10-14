"""PricePilot demo recorder (Week 2: Side Hustle).

Models the proven Week 1 FrostWise recorder:
  - Intro chapter card
  - Hero hold (galaxy + headline)
  - Scene banner (5s) -> scroll to the pricing desk
  - 3 real seller use cases, each: banner (5s) describing the seller, human-typed item +
    changed inputs, click, WAIT for the price to render, hold so the viewer reads the
    price + range + what-if levers + listing
  - Tour: How it works, Why open matters, footer

Records against the live interactive site (in-browser model mirroring TabPFN), so every
field is live and the result is instant and reliable. Banners use the Screencast overlay
API (5s holds). Typing is per-char to look human.

Run (serve web/ first on :8099):  python _internal/record_demo.py
"""
from playwright.sync_api import sync_playwright
import os
import threading
import http.server
import functools
import time

OUT = "/tmp/pricepilot-demo"
os.makedirs(OUT, exist_ok=True)
VIDEO = os.path.join(OUT, "pricepilot-demo.webm")
URL = "http://127.0.0.1:8099/"
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")

LOWER = lambda title, sub: f"""
<div style="position:fixed;bottom:46px;left:50%;transform:translateX(-50%);
  background:linear-gradient(135deg,rgba(10,15,12,.92),rgba(12,18,14,.92));
  backdrop-filter:blur(12px);border:1px solid rgba(74,222,138,.22);
  border-radius:14px;padding:16px 34px;text-align:center;
  font-family:-apple-system,Segoe UI,sans-serif;box-shadow:0 24px 70px rgba(0,0,0,.6);">
  <div style="font-size:22px;font-weight:700;color:#eef4ef;">{title}</div>
  <div style="font-size:15px;color:#86efac;margin-top:5px;">{sub}</div>
</div>"""


def banner(page, title, sub, ms=5000):
    page.screencast.hide_overlays()
    ov = page.screencast.show_overlay(LOWER(title, sub))
    page.wait_for_timeout(ms)
    try:
        ov.dispose()
    except Exception:
        pass
    page.screencast.hide_overlays()
    page.wait_for_timeout(250)


def scroll_to(page, sel, ms=1700, block="start"):
    page.evaluate(f"document.querySelector('{sel}').scrollIntoView({{behavior:'smooth',block:'{block}'}})")
    page.wait_for_timeout(ms)


def type_human(page, sel, text):
    page.click(sel)
    page.wait_for_timeout(400)
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.wait_for_timeout(300)
    page.type(sel, text, delay=90)
    page.wait_for_timeout(600)


def set_fields(page, fields):
    for fid, val in fields.items():
        el = page.query_selector(f"#{fid}")
        if not el:
            continue
        tag = page.eval_on_selector(f"#{fid}", "e=>e.tagName")
        if tag == "SELECT":
            page.select_option(f"#{fid}", str(val))
        else:
            page.fill(f"#{fid}", str(val))
        page.wait_for_timeout(220)


def run_case(page, item, fields, banner_title, banner_sub):
    banner(page, banner_title, banner_sub, 5000)
    scroll_to(page, "#item", 800, block="center")
    type_human(page, "#item", item)
    set_fields(page, fields)
    page.wait_for_timeout(500)
    page.click("#go")
    page.wait_for_function(
        "() => { const e=document.querySelector('.price'); return e && e.textContent.includes('$'); }",
        timeout=30000,
    )
    page.wait_for_timeout(1200)                      # count-up + levers animate
    scroll_to(page, "#result", 1400, block="center")
    page.wait_for_timeout(7000)                      # hold so viewer reads price + levers + listing


_handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=WEB_DIR)
_httpd = http.server.HTTPServer(("127.0.0.1", 8099), _handler)
threading.Thread(target=_httpd.serve_forever, daemon=True).start()
time.sleep(1.5)

try:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1440, "height": 810})
        pg = ctx.new_page()
        pg.screencast.start(path=VIDEO, size={"width": 1440, "height": 810})

        pg.goto(URL, wait_until="networkidle")
        pg.wait_for_timeout(1200)
        pg.screencast.show_chapter("PricePilot", description="Price it right, then watch it sell. Open-weight AI, on your laptop.", duration=3200)
        pg.wait_for_timeout(2600)

        banner(pg, "The money question: what do I charge?", "TabPFN-v2 predicts the price, Gemma 3 writes the listing, all local", 5000)
        scroll_to(pg, "#price", 1900)

        # Three different seller use cases, each changes the inputs so the price genuinely moves.
        run_case(pg, "silver moon pendant",
                 {"category_id": 0, "material_id": 3, "size_score": 0.5, "make_hours": 2.5,
                  "photo_count": 4, "season_id": 1, "is_personalized": 0, "seller_rating": 4.8},
                 "Seller 1: a handmade jeweler", "Precious materials, few photos, spring")

        run_case(pg, "hand-poured lavender soy candle",
                 {"category_id": 1, "material_id": 1, "size_score": 0.5, "make_hours": 1.5,
                  "photo_count": 3, "season_id": 3, "is_personalized": 0, "seller_rating": 4.9},
                 "Seller 2: a candle maker", "Low-cost item, holiday season, the levers matter most")

        run_case(pg, "hand-stitched leather wallet",
                 {"category_id": 6, "material_id": 3, "size_score": 0.4, "make_hours": 5,
                  "photo_count": 7, "season_id": 3, "is_personalized": 1, "seller_rating": 4.9},
                 "Seller 3: a leather maker", "High-value, personalized, Q4: a very different price")

        banner(pg, "Two open models, one job each", "TabPFN-v2 prices it, Gemma 3 writes the listing, you own the stack", 5000)
        scroll_to(pg, "#how", 2500)
        banner(pg, "Why open innovation matters", "Private sales data, $0 per listing, tune it to your niche", 5000)
        scroll_to(pg, "#why", 2500)
        pg.evaluate("window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'})")
        pg.wait_for_timeout(2600)

        pg.screencast.stop()
        ctx.close(); b.close()


finally:
    try:
        _httpd.shutdown()
    except Exception:
        pass

print("video:", VIDEO)
