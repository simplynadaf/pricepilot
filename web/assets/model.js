// PricePilot in-browser pricing model.
//
// The real app predicts with TabPFN-v2 (an open-weight tabular model) running locally in
// Python. GitHub Pages can't run Python, so this is a faithful JS APPROXIMATION of the
// same relationships the local model learns from the sold-listings dataset, tuned to the
// same price drivers (data/sold_listings.csv) so the website behaves like the real thing:
// every field is live, and the price, range, levers, and listing update instantly.
//
// It is clearly labeled in the UI as a browser estimate. For the real TabPFN prediction
// (with its calibrated quantiles and measured MAE), clone the repo and run `python run.py`.

const CATEGORY_BASE = {
  0: [34, 18], 1: [22, 10], 2: [28, 14], 3: [45, 22], 4: [8, 4],
  5: [38, 26], 6: [62, 30], 7: [48, 25], 8: [11, 5], 9: [16, 7],
};
const MATERIAL_MULT = { 0: 0.85, 1: 1.0, 2: 1.28, 3: 1.70 };
const SEASON_MULT = { 0: 0.92, 1: 1.0, 2: 1.03, 3: 1.22 };

// Core price model: mirrors scripts/build_dataset.py so the JS estimate tracks what the
// local TabPFN model learns. Deterministic (no noise) so the UI is stable.
function corePrice(f) {
  const [base] = CATEGORY_BASE[f.category_id] ?? [30, 15];
  let p = base;
  p *= MATERIAL_MULT[f.material_id] ?? 1.0;
  p *= SEASON_MULT[f.season_id] ?? 1.0;
  p *= (0.75 + 0.5 * f.size_score);
  p += f.make_hours * 2.1;
  p *= (0.6 + 0.4 * f.condition_score);
  p *= (0.9 + 0.06 * ((f.seller_rating - 3.6) / 1.4));
  p *= (1.0 + 0.015 * Math.min(f.photo_count, 8));
  p += 6.0 * f.is_personalized;
  p += 0.3 * f.shipping_cost;
  return Math.max(2.0, p);
}

function predict(f) {
  const price = corePrice(f);
  // Range mimics TabPFN's 10–90% band width on this data (~±9%).
  const low = Math.max(2, price * 0.91);
  const high = price * 1.09;

  // What-if levers: re-run the model under single-feature changes, like the Python agent.
  const levers = [];
  const consider = (label, changes) => {
    const trial = { ...f, ...changes };
    const np = corePrice(trial);
    const delta = np - price;
    if (delta > 0.05) levers.push({ label, delta: round2(delta), new_price: round2(np) });
  };
  if (f.photo_count < 8) consider('Add photos (up to 8)', { photo_count: 8 });
  if (f.is_personalized === 0) consider('Offer personalization', { is_personalized: 1 });
  if (f.season_id !== 3) consider('List in the holiday / Q4 season', { season_id: 3 });
  if (f.condition_score < 0.95) consider('Improve condition to near-mint', { condition_score: 1.0 });
  if (f.material_id < 2) consider('Use premium materials', { material_id: 2 });
  levers.sort((a, b) => b.delta - a.delta);

  return { price: round2(price), low: round2(low), high: round2(high), currency: 'USD',
           model: 'in-browser estimate (mirrors TabPFN-v2)', whatifs: levers };
}

function round2(x) { return Math.round(x * 100) / 100; }

// A lightweight local listing writer (the website has no Gemma; the real app uses it).
const CAT_NAME = {
  0: 'handmade jewelry', 1: 'hand-poured candle', 2: 'ceramic mug / pottery',
  3: 'knitted / crochet item', 4: 'digital print', 5: 'vintage clothing',
  6: 'leather goods', 7: 'wooden home decor', 8: 'sticker / enamel pin', 9: 'soap / bath product',
};
function writeListing(item, f, pricing) {
  const cat = CAT_NAME[f.category_id] ?? 'handmade item';
  const titleCase = (s) => s.replace(/\b\w/g, (c) => c.toUpperCase());
  let title = `${titleCase(item)} · ${titleCase(cat)}`;
  if (title.length > 80) title = title.slice(0, 79);
  const personal = f.is_personalized ? ' Personalization is available on request.' : '';
  const desc =
    `A carefully made ${item.toLowerCase()} from our ${cat} range. Priced at $${pricing.price}, ` +
    `in line with what comparable pieces sell for (typically $${pricing.low} to $${pricing.high}).` +
    ` Each one is checked by hand before it ships.${personal}`;
  const words = `${item} ${cat}`.toLowerCase().replace(/[^a-z0-9 ]/g, '').split(/\s+/).filter(Boolean);
  const tags = [...new Set([...words, 'handmade', 'gift', 'small shop', 'unique'])].slice(0, 8);
  return { title, description: desc, tags, source: 'browser-estimate', model: 'template (local Gemma writes this in the full app)' };
}

window.PricePilotModel = { predict, writeListing };
