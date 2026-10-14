// PricePilot app logic: scroll reveals (GSAP), meta/preset loading, the price call,
// animated counting price, what-if levers, and the Gemma listing card.

gsap.registerPlugin(ScrollTrigger);
document.documentElement.classList.add('js-reveal');
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (reduced) {
  gsap.set('.reveal', { opacity: 1, y: 0 });
} else {
  const hero = gsap.utils.toArray('header .reveal');
  gsap.to(hero, { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out', stagger: 0.08 });
  gsap.utils.toArray('section .reveal, footer .reveal').forEach((el) => {
    gsap.to(el, { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out',
      scrollTrigger: { trigger: el, start: 'top 90%' } });
  });
  setTimeout(() => {
    document.querySelectorAll('.reveal').forEach((el) => {
      if (parseFloat(getComputedStyle(el).opacity) < 0.1) gsap.set(el, { opacity: 1, y: 0 });
    });
  }, 2500);
}

// ---- range value labels ----
function bindRange(id) {
  const el = document.getElementById(id);
  const out = document.getElementById(id + '_v');
  const upd = () => { if (out) out.textContent = el.value; };
  el.addEventListener('input', upd); upd();
}
bindRange('size_score');
bindRange('condition_score');

// ---- live vs static mode ----
// Live: a FastAPI backend is running (python run.py) → real TabPFN + Gemma on each request.
// Static: GitHub Pages has no backend → an in-browser model (model.js) mirrors TabPFN so
//         every field stays fully interactive and the price updates instantly.
let MODE = 'live';
let META = null; // {categories, materials, seasons, mae} for static mode

async function detectMode() {
  try {
    const r = await fetch('/api/health', { method: 'GET' });
    if (r.ok) return 'live';
  } catch (e) { /* no backend */ }
  return 'static';
}

// ---- meta (categories / materials / seasons) ----
async function loadMeta() {
  MODE = await detectMode();
  if (MODE === 'static') {
    // Static meta: match the Python CATEGORY/MATERIAL/SEASON names exactly.
    META = {
      categories: [
        { id: 0, name: 'handmade jewelry' }, { id: 1, name: 'hand-poured candle' },
        { id: 2, name: 'ceramic mug / pottery' }, { id: 3, name: 'knitted / crochet item' },
        { id: 4, name: 'digital print (download)' }, { id: 5, name: 'vintage clothing' },
        { id: 6, name: 'leather goods' }, { id: 7, name: 'wooden home decor' },
        { id: 8, name: 'sticker / enamel pin' }, { id: 9, name: 'soap / bath product' },
      ],
      materials: [
        { id: 0, name: 'basic / recycled' }, { id: 1, name: 'standard' },
        { id: 2, name: 'premium' }, { id: 3, name: 'precious' },
      ],
      seasons: [
        { id: 0, name: 'off-season' }, { id: 1, name: 'spring' },
        { id: 2, name: 'summer' }, { id: 3, name: 'holiday / Q4' },
      ],
      mae: 2.96,
    };
    fill('category_id', META.categories);
    fill('material_id', META.materials, 1);
    fill('season_id', META.seasons, 1);
    addMaeBadge(META.mae);
    showStaticNote();
    return;
  }
  try {
    const d = await (await fetch('/api/meta')).json();
    fill('category_id', d.categories);
    fill('material_id', d.materials, 1);
    fill('season_id', d.seasons, 1);
    addMaeBadge(d.mae);
  } catch (e) {
    fill('category_id', [{ id: 0, name: 'handmade jewelry' }]);
    fill('material_id', [{ id: 1, name: 'standard' }]);
    fill('season_id', [{ id: 1, name: 'spring' }]);
  }
}
function addMaeBadge(mae) {
  const badge = document.querySelector('.badges');
  if (badge && mae != null) {
    const note = document.createElement('span');
    note.innerHTML = `<b>±$${mae}</b> typical error (measured)`;
    badge.appendChild(note);
  }
}
function showStaticNote() {
  const note = document.createElement('div');
  note.style.cssText = 'margin-bottom:18px;font-size:12.5px;color:var(--muted);border:1px dashed var(--line);border-radius:10px;padding:10px 14px;background:rgba(74,222,138,.04)';
  note.innerHTML = 'Live interactive demo: this hosted page runs an <b style="color:#86efac">in-browser estimate</b> that mirrors the real model, so every field below is editable and the price updates instantly. For the actual <b>TabPFN-v2</b> prediction (with Gemma writing the listing), clone the repo and run <code>python run.py</code>, fully offline.';
  const panel = document.querySelector('#price .panel');
  if (panel) panel.insertBefore(note, panel.firstChild);
}
function fill(id, items, def) {
  const sel = document.getElementById(id);
  sel.innerHTML = items.map((i) => `<option value="${i.id}">${i.name}</option>`).join('');
  if (def != null) sel.value = def;
}
function fill(id, items, def) {
  const sel = document.getElementById(id);
  sel.innerHTML = items.map((i) => `<option value="${i.id}">${i.name}</option>`).join('');
  if (def != null) sel.value = def;
}

// ---- price call ----
const go = document.getElementById('go');
const result = document.getElementById('result');
const FIELDS = ['category_id', 'material_id', 'size_score', 'make_hours', 'condition_score',
  'seller_rating', 'photo_count', 'season_id', 'is_personalized', 'shipping_cost'];

go.addEventListener('click', async () => {
  const payload = { item: (document.getElementById('item').value || 'handmade item').trim() };
  for (const f of FIELDS) payload[f] = parseFloat(document.getElementById(f).value);

  // Static (GitHub Pages): compute instantly with the in-browser model, fully interactive.
  if (MODE === 'static' && window.PricePilotModel) {
    go.disabled = true; go.innerHTML = '<span class="spinner"></span> Pricing…';
    await new Promise((r) => setTimeout(r, 450)); // brief beat so the result feels computed
    const feats = {};
    for (const f of FIELDS) feats[f] = payload[f];
    const pricing = window.PricePilotModel.predict(feats);
    pricing.mae = META ? META.mae : 2.96;
    const listing = window.PricePilotModel.writeListing(payload.item, feats, pricing);
    const catName = (META.categories.find((c) => c.id === feats.category_id) || {}).name || 'handmade item';
    renderResult({ pricing, listing, category: catName });
    go.disabled = false; go.textContent = 'Price my item';
    return;
  }

  go.disabled = true; go.innerHTML = '<span class="spinner"></span> Pricing locally…';
  result.innerHTML = '<div class="empty"><span class="spinner"></span><br>Running TabPFN-v2, then Gemma… (a few seconds on CPU)</div>';

  try {
    const r = await fetch('/api/price', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
    const d = await r.json();
    renderResult(d);
  } catch (e) {
    result.innerHTML = `<div class="empty">Something went wrong: ${e.message}</div>`;
  } finally {
    go.disabled = false; go.textContent = 'Price my item';
  }
});

function renderResult(d) {
  const p = d.pricing, l = d.listing;
  const levers = (p.whatifs || []).slice(0, 4).map((w) => {
    const sign = w.delta >= 0 ? '+' : '';
    return `<div class="lever"><span class="ll">${w.label}</span><span class="ld">${sign}$${w.delta.toFixed(2)}</span></div>`;
  }).join('');
  const srcLabel = l.source === 'gemma'
    ? `Listing written locally by ${l.model} (open-weight)`
    : l.source === 'browser-estimate'
    ? `Browser estimate · the full app writes this with a local Gemma 3 model`
    : `Offline fallback (no model reachable) · rule-based`;
  const tags = (l.tags || []).map((t) => `<span class="tag">${t}</span>`).join('');

  result.innerHTML = `
    <div>
      <div style="font-size:13px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase">${d.category} · suggested price</div>
      <div class="price" id="pz">$${p.price.toFixed(2)}</div>
      <div class="pricemeta">likely between <b>$${p.low.toFixed(2)}</b> and <b>$${p.high.toFixed(2)}</b></div>
      <span class="count">Predicted by ${p.model} · ±$${p.mae} typical error</span>
      ${levers ? `<div class="levers"><div class="lh">What raises the price</div>${levers}</div>` : ''}
      <div class="listing">
        <div class="who">✍️ Draft listing</div>
        <div class="lt">${escapeHtml(l.title || '')}</div>
        <div class="ld">${escapeHtml(l.description || '')}</div>
        <div class="tags">${tags}</div>
        <div class="src">${srcLabel}</div>
      </div>
    </div>`;

  countUp(document.getElementById('pz'), p.price);
  gsap.from('.levers .lever', { opacity: 0, y: 10, duration: 0.5, stagger: 0.06, ease: 'power3.out' });
  gsap.from('.listing', { opacity: 0, y: 16, duration: 0.6, delay: 0.1, ease: 'power3.out' });
}

function countUp(el, target) {
  if (reduced) { el.textContent = `$${target.toFixed(2)}`; return; }
  let cur = 0; const start = performance.now(); const dur = 700;
  const step = (now) => {
    const t = Math.min(1, (now - start) / dur);
    cur = target * (1 - Math.pow(1 - t, 3));
    el.textContent = `$${cur.toFixed(2)}`;
    if (t < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

loadMeta();

document.getElementById('price-btn')?.addEventListener('click', () => {
  document.getElementById('price').scrollIntoView({ behavior: 'smooth' });
});
document.getElementById('how-btn')?.addEventListener('click', (e) => {
  e.preventDefault();
  document.getElementById('how').scrollIntoView({ behavior: 'smooth' });
});
