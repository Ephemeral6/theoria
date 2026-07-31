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

    def ceiling_for(self, body: Any) -> Dict[str, Any]:
        """The most this request could cost, computed *before* it is sent.

        `cost()` prices a call after the fact, which is the only way to know
        what it really cost -- and is therefore useless as a gate. An
        adversarial pass put $600 through a $10 ceiling in one call for exactly
        this reason: the money was checked only after it had left. What makes a
        pre-flight possible is that the Anthropic Messages API requires
        `max_tokens`, so the expensive half of the bill has a stated bound
        before the socket opens.

        Returns `{"usd": float}` when a bound exists, or `{"usd": None,
        "why": ...}` when none can be computed. **A missing bound is a
        refusal, not a zero** -- the caller must not send what it cannot price,
        because an unpriceable call is unbounded and the pool has no way to
        notice it going by.

        The input side is estimated from the serialised request at a
        deliberately pessimistic 3 characters per token; the output side uses
        `max_tokens` in full. Both err upward: this is a ceiling, and a ceiling
        that is sometimes too low is not a ceiling.
        """
        if not isinstance(body, dict):
            return {"usd": None, "why": "the request body is not a JSON object, "
                                        "so no model and no max_tokens can be read"}
        model = body.get("model")
        prices = self.models.get(model) if isinstance(model, str) else None
        if prices is None:
            return {"usd": None, "model": model,
                    "why": "model %r is not in %s, so this call has no "
                           "computable ceiling" % (model, self.name)}
        max_tokens = body.get("max_tokens")
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            return {"usd": None, "model": model,
                    "why": "max_tokens is %r; without it the output side of the "
                           "bill is unbounded" % (max_tokens,)}

        per_token_in = prices["input"] / 1_000_000.0
        per_token_out = prices["output"] / 1_000_000.0
        # Pessimistic: 3 chars/token is below any real tokeniser's ratio for
        # English, and cache multipliers can only raise the input side, so the
        # largest of them is applied to all of it.
        chars = len(json.dumps(body, ensure_ascii=False))
        input_tokens = chars / 3.0
        multiplier = max([1.0] + [float(m) for m in self.cache.values()])
        usd = input_tokens * per_token_in * multiplier + max_tokens * per_token_out
        return {"usd": round(usd, 6), "model": model,
                "basis": {"max_tokens": max_tokens,
                          "estimated_input_tokens": int(input_tokens),
                          "cache_multiplier_applied": multiplier,
                          "chars_per_token_assumed": 3.0}}


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
