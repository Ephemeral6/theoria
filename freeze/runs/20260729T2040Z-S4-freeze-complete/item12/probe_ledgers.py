"""Scratch probe: survey every arm ledger dialect and its cost field.

Read-only. Written under freeze/ per the item-12 red lines; not part of the
deliverable, kept so the numbers in BUDGET_TABLE.md can be re-derived.
"""
import glob
import json
import os

for p in sorted(glob.glob("theoria-arm/runs/**/ledger.jsonl", recursive=True)):
    n = 0
    cost = 0.0
    kinds = {}
    for line in open(p, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        n += 1
        k = rec.get("kind") or rec.get("event") or rec.get("type") or "?"
        kinds[k] = kinds.get(k, 0) + 1
        for fld in ("total_cost_usd", "cost_usd", "usd"):
            v = rec.get(fld)
            if v is None and isinstance(rec.get("response"), dict):
                v = rec["response"].get(fld)
            if v is not None:
                try:
                    cost += float(v)
                except Exception:
                    pass
    print("%-70s n=%3d self_reported=$%.4f %s"
          % (p.replace(os.sep, "/"), n, cost, kinds))
