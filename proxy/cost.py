"""Cost is a conversion, not a record.

The ledger holds the provider's `usage` block verbatim and a `pricing_ref`
naming the price table that was in force. Dollars appear only here, computed on
demand. The reason is in LEDGER_FORMAT.md §5: an append-only file that recorded
a price would be wrong the day the price changed, and could not be corrected.

    python -m proxy.cost --ledger proxy/var/ledger.jsonl
"""

import argparse
import glob
import json
import os
import sys
from typing import Any, Dict, List, Optional

from .ledger import read_ledger, sha256
from .paths import LEDGER_PATH, PRICING_DIR

DEFAULT_TABLE = "pricing_v1"


class PriceTable:
    def __init__(self, spec: Dict[str, Any], source: Optional[str] = None):
        self.spec = spec
        self.source = source
        self.name = spec["table"]
        self.sha256 = sha256(spec)
        self.models: Dict[str, Any] = spec["models"]
        self.cache = spec.get("cache_multipliers", {})

    @classmethod
    def load(cls, name: str = DEFAULT_TABLE, directory: str = PRICING_DIR) -> "PriceTable":
        path = os.path.join(directory, name + ".json")
        if not os.path.exists(path):
            available = [os.path.basename(p)[:-5]
                         for p in sorted(glob.glob(os.path.join(directory, "*.json")))]
            raise KeyError("no price table %r in %s (have: %s)"
                           % (name, directory, ", ".join(available) or "none"))
        with open(path, encoding="utf-8") as fh:
            return cls(json.load(fh), source=path)

    def reference(self) -> Dict[str, Any]:
        """Goes into every `model_call` record."""
        return {"table": self.name, "sha256": self.sha256}

    def cost(self, model: str, usage: Dict[str, Any]) -> Dict[str, Any]:
        prices = self.models.get(model)
        if prices is None:
            return {"usd": None, "model": model,
                    "unpriced": "model %r is not in %s" % (model, self.name)}

        per_token_in = prices["input"] / 1_000_000.0
        per_token_out = prices["output"] / 1_000_000.0

        lines: Dict[str, float] = {}
        lines["input_tokens"] = int(usage.get("input_tokens") or 0) * per_token_in
        lines["output_tokens"] = int(usage.get("output_tokens") or 0) * per_token_out
        for field, multiplier in self.cache.items():
            count = int(usage.get(field) or 0)
            if count:
                lines[field] = count * per_token_in * multiplier

        # Any usage key we do not know how to price is reported, not ignored:
        # a silently dropped token is a silently wrong bill.
        known = {"input_tokens", "output_tokens"} | set(self.cache)
        unknown = sorted(k for k, v in usage.items()
                         if k not in known and isinstance(v, int) and v)

        return {"usd": round(sum(lines.values()), 6), "model": model,
                "lines": {k: round(v, 6) for k, v in lines.items()},
                "unpriced_usage_keys": unknown or None}


def price_run(records: List[Dict[str, Any]], table: PriceTable) -> Dict[str, Any]:
    total = 0.0
    per_model: Dict[str, Dict[str, Any]] = {}
    unpriced: List[str] = []

    for record in records:
        if record.get("event") != "model_call":
            continue
        result = table.cost(record.get("model", "?"), record.get("usage") or {})
        if result["usd"] is None:
            if result["model"] not in unpriced:
                unpriced.append(result["model"])
            continue
        total += result["usd"]
        bucket = per_model.setdefault(result["model"], {"usd": 0.0, "calls": 0})
        bucket["usd"] = round(bucket["usd"] + result["usd"], 6)
        bucket["calls"] += 1

    return {"pricing": table.reference(), "usd_total": round(total, 6),
            "per_model": per_model, "unpriced_models": unpriced or None,
            "model_calls": sum(b["calls"] for b in per_model.values())}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ledger", default=LEDGER_PATH)
    ap.add_argument("--table", default=DEFAULT_TABLE)
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args(argv)

    records = read_ledger(args.ledger)
    if args.run_id:
        records = [r for r in records if r.get("run_id") == args.run_id]
    report = price_run(records, PriceTable.load(args.table))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
