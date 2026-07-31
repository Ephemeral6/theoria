"""Requirement 4, as a demonstration rather than a claim.

Plant a record whose amount does not reconcile, and show the verdict go red.
The control comes first, because a red that was red before the tamper proves
nothing.

The tamper is the smallest one available: **one token**, on one field, of one
call. `usage.output_tokens` is moved from 43066 to 43067 while the provider's
own `modelUsage` breakdown in the same envelope keeps saying 43066. Both sides
are integers, so C-3 is an equality with no tolerance -- a tolerance is exactly
what would make this green by construction.

    python evidence/amount_mismatch.py
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "proxy", "tests"))

from test_reconcile import RUN, forge                       # noqa: E402
from test_reconcile_amount import write_cli_run             # noqa: E402

from proxy.reconcile import reconcile_run                   # noqa: E402


def tamper(record):
    if record.get("event") == "model_call":
        record["usage"] = dict(record["usage"], output_tokens=43067)
    return record


def line(report, label):
    print("%-26s verdict=%-10s cost leg=%-12s incident written=%s"
          % (label, report["verdict"], report["legs"]["cost"]["verdict"],
             bool(report["problems"])))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        clean = write_cli_run(os.path.join(tmp, "clean.jsonl"))
        control = reconcile_run(RUN, clean, write_incident=False)
        line(control, "CONTROL, untampered")
        assert control["verdict"] == "PASS", control

        planted = forge(clean, os.path.join(tmp, "planted.jsonl"), tamper)
        red = reconcile_run(RUN, planted, write_incident=False)
        line(red, "PLANTED, +1 token")
        assert red["verdict"] == "FAIL", red

        print("")
        print("what disagreed:")
        print(json.dumps(red["legs"]["cost"]["usage_disputed"], indent=2,
                         sort_keys=True))
        print("")
        for problem in red["problems"]:
            print("  " + problem)
        print("")
        print("the other two legs are untouched, so a reader can tell which")
        print("quantity was wrong:")
        for leg in ("actions", "score_per_run"):
            print("  %-14s %s" % (leg, red["legs"][leg]["verdict"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
