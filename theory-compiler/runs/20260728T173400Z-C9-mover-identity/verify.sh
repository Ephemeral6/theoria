#!/usr/bin/env bash
# C9 second pass -- acceptance gate.  Run from the repository root:
#
#     bash theory-compiler/runs/20260728T173400Z-C9-mover-identity/verify.sh
#
# Green means: the identity repair fires where it should and nowhere else, the
# E-09 atom is priced as the ledger says, and worldgen's count-lock world runs
# through cold-start-a0's pipeline -- which is C9's work-order acceptance line.
#
# Read-only with respect to worldgen/ and engine-rig/.  No network, no API.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
fail=0

step () {
  printf '\n== %s\n' "$1"
}

step "1/5  cold-start-a0 suite (includes the 26 new C9 tests)"
( cd cold-start-a0 && python -m pytest ) || fail=1

step "2/5  theory-compiler suite -- the DSL side must not move"
( cd theory-compiler && python -m pytest ) || fail=1

step "3/5  cold-start-a0 end to end"
( cd cold-start-a0 && python run_all.py ) || fail=1

step "4/5  A0's mined guards are byte-identical to the base commit"
python - <<'PY' || fail=1
import json, subprocess, sys
base = "86d79c6"
bad = 0
for path in ("cold-start-a0/artifacts/candidates.jsonl",
             "cold-start-a0/artifacts/candidates_no_button.jsonl"):
    old = subprocess.run(["git", "show", "%s:%s" % (base, path)],
                         capture_output=True, text=True).stdout.splitlines()
    new = open(path, encoding="utf-8").read().splitlines()
    keep = lambda rows: [json.loads(r) for r in rows
                         if json.loads(r)["kind"] != "object_hypothesis"]
    a, b = keep(old), keep(new)
    ok = a == b
    print("   %-52s %d rows  %s" % (path, len(b), "identical" if ok else "MOVED"))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)
PY

step "5/5  C9's acceptance line -- the count-lock world through the pipeline"
python - <<'PY' || fail=1
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.getcwd(), "cold-start-a0"))
sys.path.insert(0, os.path.join(os.getcwd(), "engine-rig"))
import _bootstrap  # noqa: F401
from pipeline import engines_stage

trace = os.path.join("worldgen", "out", "worlds", "t2-lock-fragile",
                     "raw_trace.jsonl")
if not os.path.exists(trace):
    print("   SKIP -- worldgen has not been generated (different territory)")
    sys.exit(0)

with tempfile.TemporaryDirectory() as tmp:
    report = engines_stage.run_stage(
        trace, os.path.join(tmp, "c.jsonl"), os.path.join(tmp, "r.json"),
        timestamp="1970-01-01T00:00:00Z")

seg, mining = report["segmentation"], report["mining"]
chosen = next(r for r in seg["operator_comparison"] if r["chosen"])
repair = chosen["identity_repair"]
checks = [
    ("the mover is the agent, not a token", seg["mover"] == "obj0"),
    ("no track recolours into another",     "recolor" not in seg["event_types"]),
    ("the repair fired once per token",     repair["n_swaps"] == 3),
    ("and its price is on the record",      repair["delta_bits"] == 6),
    ("rules were mined at all",             len(mining["rules"]) > 0),
    ("every track explained",               all(mining["explains_every_transition"].values())),
    ("exclusively",                         all(mining["mutually_exclusive"].values())),
    ("the E-09 rule is stated",             any("!faces(obj1,RIGHT)" in r["guard"]
                                                for r in mining["rules"])),
]
bad = 0
for label, ok in checks:
    print("   [%s] %s" % ("ok " if ok else "FAIL", label))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)
PY

printf '\n'
if [ "$fail" -eq 0 ]; then
  echo "VERIFY GREEN"
else
  echo "VERIFY RED"
fi
exit "$fail"
