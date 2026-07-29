"""Scratch probe: does the known 1h-cache-write defect in proxy/cost.py explain
the gap between the CLI's self-reported total_cost_usd and a pricing_v1
re-pricing of the same seven theoria-arm desk calls?

Read-only.
"""
import glob
import json
import sys

sys.path.insert(0, ".")
from proxy.cost import PriceTable  # noqa: E402

pt = PriceTable.load()
tbl = json.load(open("proxy/pricing/pricing_v1.json", encoding="utf-8"))
mult = tbl["cache_multipliers"]

self_reported = 0.0
repriced = 0.0
repriced_1h = 0.0
rows = []
for p in sorted(glob.glob("theoria-arm/runs/**/ledger.jsonl", recursive=True)):
    for line in open(p, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        u = rec.get("usage")
        if not isinstance(u, dict):
            continue
        model = rec.get("model")
        sr = rec.get("total_cost_usd")
        if sr is None and isinstance(rec.get("response"), dict):
            sr = rec["response"].get("total_cost_usd")
        if sr is None:
            print("!! usage row with no total_cost_usd:", model, rec.get("kind"))
            continue
        c = pt.cost(model, u)
        prices = tbl["models"][model]
        cw = int(u.get("cache_creation_input_tokens") or 0)
        # what the same row costs if every cache write is billed at the 1h rate
        delta = cw / 1e6 * prices["input"] * (mult["cache_creation_input_tokens_1h"]
                                              - mult["cache_creation_input_tokens"])
        self_reported += float(sr)
        repriced += c["usd"]
        repriced_1h += c["usd"] + delta
        rows.append((model, sr, c["usd"], c["usd"] + delta, cw,
                     u.get("cache_creation")))

for r in rows:
    print("%-16s self=%.6f  v1=%.6f  v1+1h=%.6f  cw=%d  %s" % r)
print()
print("self-reported   $%.4f" % self_reported)
print("pricing_v1      $%.4f  (%.2f%% vs self-report)"
      % (repriced, 100 * (repriced / self_reported - 1)))
print("pricing_v1 @1h  $%.4f  (%.2f%% vs self-report)"
      % (repriced_1h, 100 * (repriced_1h / self_reported - 1)))
