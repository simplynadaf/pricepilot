"""PricePilot: a local pricing + listing copilot for independent marketplace sellers.

Open stack, 100% local:
  - TabPFN-v2 (Prior Labs, open weights) predicts the sell price from a sold-listings CSV.
  - Gemma 3 (open weight, via Ollama) writes the listing from that price.
Nothing leaves the seller's machine.
"""
__version__ = "1.0.0"
