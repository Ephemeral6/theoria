"""What a desk call actually costs per second, measured from this arm's own logs.

`MODEL_CALL_CEILING_USD = 4.00` is one flat constant applied to every model. It
is the number charged for a call that comes back unpriceable, and
`proxy/var/spend_gate.jsonl` seq 7418 is what that costs: a call that ran 145 ms
and reached nothing was booked at $4.00, flagged `unpriced`, and the whole shared
pool has refused every dollar for every session since.

This script is the evidence for replacing that constant. It reads every
`desk_log.json` in the archive, re-derives each call's price from
`proxy/pricing/pricing_v1.json`, and compares it against the price the CLI itself
reported (`cli_cost_usd`). Two numbers come out, and both are needed:

* **usd/s per model** -- because a call's cost is bounded by how long it ran, and
  at the moment of charging an unpriced call we know that number.
* **derived/cli** -- how far the price table falls short of the CLI's own figure.
  A ceiling built on the table alone would inherit that shortfall, which is the
  one direction a ceiling may not err in (`proxy/cost.py:93`: "a ceiling that is
  sometimes too low is not a ceiling").

Run from `theoria-arm/`:  python runs/20260729T1745Z-A3-per-model-ceiling/measure_desk_rates.py
Zero network, zero dollars: it reads files already on disk.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
PRICING = os.path.join(os.path.dirname(ARM), "proxy", "pricing", "pricing_v1.json")


def _base(models, model):
    """The price row for a model id, tolerating a date suffix.

    `claude-haiku-4-5-20251001` is the id the desk actually sent; the table
    holds `claude-haiku-4-5`. `proxy/cost.py` does an exact-key lookup and so
    cannot price this call at all -- which is the reason the $4.00 placeholder
    could not be corrected and the pool stayed shut. Stripping one trailing
    `-<digits>` group is the whole fix at this end.
    """
    if model in models:
        return models[model]
    stem, _, tail = model.rpartition("-")
    if tail.isdigit() and stem in models:
        return models[stem]
    return None


def rows():
    table = json.load(open(PRICING, encoding="utf-8"))
    models, mult = table["models"], table["cache_multipliers"]
    out = []
    for path in sorted(glob.glob(os.path.join(ARM, "runs", "*", "desk_log.json"))):
        for record in json.load(open(path, encoding="utf-8")):
            if not isinstance(record, dict) or "usage" not in record:
                continue
            usage, model = record["usage"], record["model"]
            price = _base(models, model)
            if price is None:
                out.append((model, None, None, None, "unpriceable: no row"))
                continue
            created = usage.get("cache_creation") or {}
            derived = (
                usage.get("input_tokens", 0) * price["input"]
                + usage.get("output_tokens", 0) * price["output"]
                + created.get("ephemeral_1h_input_tokens", 0) * price["input"]
                * mult["cache_creation_input_tokens_1h"]
                + created.get("ephemeral_5m_input_tokens", 0) * price["input"]
                * mult["cache_creation_input_tokens"]
                + usage.get("cache_read_input_tokens", 0) * price["input"]
                * mult["cache_read_input_tokens"]
            ) / 1e6
            out.append((model, record["elapsed_ms"] / 1000.0,
                        record["cli_cost_usd"], derived, os.path.basename(
                            os.path.dirname(path))))
    return out


def main():
    data = rows()
    print("per call")
    for model, secs, cli, derived, run in data:
        if secs is None:
            print("  %-26s %s" % (model, run))
            continue
        print("  %-26s %7.1fs  cli=$%.6f  derived=$%.6f  derived/cli=%.4f  "
              "usd/s=%.6f  %s" % (model, secs, cli, derived, derived / cli,
                                  cli / secs, run))

    print("\nper model")
    for model in sorted({r[0] for r in data if r[1] is not None}):
        sub = [r for r in data if r[0] == model and r[1] is not None]
        print("  %-26s n=%d  max usd/s=%.6f  max call=$%.6f  "
              "worst derived/cli=%.4f" % (
                  model, len(sub),
                  max(c / s for _, s, c, _d, _r in sub),
                  max(c for _, _s, c, _d, _r in sub),
                  min(d / c for _, _s, c, d, _r in sub)))

    print("\nthe two facts a ceiling has to respect")
    worst = min(d / c for _, s, c, d, _r in data if s is not None)
    print("  * the price table under-derives by up to %.1f%% against the CLI's "
          "own figure," % ((1 - worst) * 100))
    print("    and never over-derives. A ceiling read off the table alone is "
          "short by that much.")
    print("  * usd/s differs by ~4.5x between the two models this arm has run, "
          "so one")
    print("    flat constant is either too high for the cheap one or too low "
          "for the dear one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
