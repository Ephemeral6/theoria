"""Where things are. One module so no other file guesses at the layout."""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

DOTENV = os.path.join(REPO, ".env")
PILES = os.path.join(REPO, "arc-recon", "data", "piles.json")

VAR_DIR = os.path.join(HERE, "var")                 # runtime output, gitignored
LEDGER_PATH = os.path.join(VAR_DIR, "ledger.jsonl")
RUNS_DIR = os.path.join(VAR_DIR, "runs")

PRICING_DIR = os.path.join(HERE, "pricing")
VARIANTS_DIR = os.path.join(HERE, "variants")

UPSTREAM_ARC = "https://three.arcprize.org"
UPSTREAM_MODEL = "https://api.anthropic.com"
