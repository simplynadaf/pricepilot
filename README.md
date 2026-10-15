# PricePilot

A local pricing copilot for independent marketplace sellers. An open-weight tabular model
(**TabPFN-v2**) predicts what a handmade or resale item will sell for from your own
sold-listings data, and a local language model (**Gemma 3** via Ollama) writes the listing.
Everything runs on your own machine: no account, no API bill, and your sales data never
leaves your laptop.

- **Live demo:** https://simplynadaf.github.io/pricepilot/
- Built for the Hacktoberfest Open-Source AI Challenge 2026, Week 2: Side Hustle.

## How it works

| Layer | Model | What it does |
|-------|-------|--------------|
| Price | TabPFN-v2 (open weights) | Predicts the sell price from past sold listings in one CPU pass, with a calibrated 10–90% range. Used as a prediction agent: re-queried under single-feature changes to rank the "what-if" levers that move the price. |
| Listing | Gemma 3 (local, via Ollama) | Turns the item plus the predicted price into a title, description, and tags. Told the price; never invents one. |
| Fallback | Deterministic rule | Writes a correct listing from the same price if Ollama is unreachable. |

On the sample dataset, TabPFN predicts held-out sold prices with a mean absolute error of
about $2.90 on items averaging ~$54 (roughly 5% error), with zero training time.

## Getting started

```bash
git clone https://github.com/simplynadaf/pricepilot.git
cd pricepilot

# CPU-only PyTorch (skip if you have a GPU build you prefer)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# the local language model (open-weight) via Ollama
# install Ollama from https://ollama.com, then:
ollama pull gemma3:1b

python run.py        # -> http://127.0.0.1:8088
```

Describe an item, hit **Price my item**. The first run downloads the TabPFN-v2 weights once
and caches them; after that it runs fully offline.

```bash
python -m pricepilot.pricing   # price agent on its own: price, range, MAE, what-if levers
python scripts/build_dataset.py  # regenerate data/sold_listings.csv
python scripts/validate.py       # end-to-end: API + TabPFN + Gemma + offline fallback
```

## Project structure

```
pricepilot/
├── pricepilot/              # the open-weight AI core
│   ├── api.py               # FastAPI: wires price + listing, serves the UI
│   ├── pricing.py           # TabPFN-v2 prediction agent (price, range, what-ifs, MAE)
│   └── listing.py           # Gemma 3 listing writer + offline fallback
├── web/                     # static front end (also the GitHub Pages demo)
│   ├── index.html
│   └── assets/{app.js, model.js, scene.js}
├── data/sold_listings.csv   # 900 grounded sold listings (swap in your own)
├── scripts/                 # build_dataset.py, bake_static.py, validate.py
├── run.py                   # one command to run everything
├── requirements.txt
└── LICENSE                  # MIT
```

## License

MIT. See [LICENSE](LICENSE).

Model weights are licensed by their authors: TabPFN-v2 under the Prior Labs License, and
Gemma under the Gemma Terms of Use.
