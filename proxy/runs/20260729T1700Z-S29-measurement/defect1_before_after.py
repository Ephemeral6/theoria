"""Defect 1, measured directly rather than through the new test file.

`proxy/tests/test_cost.py` cannot serve as its own fail-before evidence: it
imports `REQUIRED_USAGE_KEYS`, which does not exist on master, so running it
against master code raises `ImportError` at collection. That is a failure
*caused by* the change and not one that reaches the claim the tests are about --
the same trap this run's `RUN_STATE.md` already records for the two crash tests.

So this script asks `PriceTable.cost` the four questions directly and prints
what it answers. Run it once with the branch's `proxy/cost.py` in place and once
with master's, and diff the two outputs:

    python proxy/runs/20260729T1700Z-S29-measurement/defect1_before_after.py

Offline, no API calls, no ledger writes.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from proxy.cost import PriceTable                          # noqa: E402
from proxy.paths import PRICING_DIR                        # noqa: E402

MODEL = "claude-opus-5"

CASES = [
    ("no usage block at all -- the call was never measured",
     {}),
    ("a truncated stream: input_tokens arrived, output_tokens never did",
     {"input_tokens": 1000}),
    ("the provider serialised an explicit null for the output side",
     {"input_tokens": 1000, "output_tokens": None}),
    ("a genuine measured zero -- both halves present, both zero",
     {"input_tokens": 0, "output_tokens": 0}),
    ("a complete, ordinary block (the regression control)",
     {"input_tokens": 1000, "output_tokens": 5000}),
]


def main():
    spec = json.load(open(os.path.join(PRICING_DIR, "pricing_v1.json"),
                         encoding="utf-8"))
    table = PriceTable(spec)
    for label, usage in CASES:
        out = table.cost(MODEL, usage)
        print("%-62s usage=%s" % (label, json.dumps(usage, sort_keys=True)))
        print("    usd=%r  missing_usage_keys=%r  unpriced=%r"
              % (out.get("usd"), out.get("missing_usage_keys"),
                 out.get("unpriced")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
