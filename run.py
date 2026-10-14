#!/usr/bin/env python3
"""PricePilot launcher. One command to run everything locally.

    python run.py            # serve at http://127.0.0.1:8088
    python run.py --port 9000

Pre-reqs (see README): install deps, an Ollama install with a Gemma model pulled
(`ollama pull gemma3:1b`), and the dataset built once
(`python scripts/build_dataset.py`, already included in the repo).
"""
import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser(description="Run the PricePilot local server.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8088)
    ap.add_argument("--model", default=os.environ.get("PRICEPILOT_MODEL", "gemma3:1b"),
                    help="Ollama model for the listing writer (any open-weight model).")
    args = ap.parse_args()

    os.environ["PRICEPILOT_MODEL"] = args.model
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    import uvicorn
    print(f"PricePilot -> http://{args.host}:{args.port}  (listing model: {args.model})")
    uvicorn.run("pricepilot.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
