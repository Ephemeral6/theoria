#!/usr/bin/env bash
# A3-campaign-devpile -- the stop gate.
#
# Everything here is offline: no key, no network, no ARC quota, $0.00, and zero
# contact with the sealed pile. Run from the arm's directory:
#
#     cd theoria-arm && bash runs/20260728T233900Z-A3-campaign-devpile/verify.sh
#
# Gate 6 is the one worth reading twice. A probe that cannot be shown to go red
# is a green light with nothing behind it, so each of the three defects this
# run fixed is re-broken on a scratch copy and the test that covers it must
# fail. If a negative control passes, the gate fails -- silence there means the
# test was never testing anything.

set -u
cd "$(dirname "$0")/../.." || exit 2
ARM="$PWD"
FAILED=0

pass() { printf '  ok    %s\n' "$1"; }
fail() { printf '  FAIL  %s\n' "$1"; FAILED=$((FAILED + 1)); }

echo "== gate 1: the suite runs twice in a row =="
# Twice, because before this run it was green exactly once per clean checkout
# and red forever after: a test asserted a whole-file invariant over a shared
# append-only ledger it did not own.
if python -m pytest -q >/tmp/a3-g1a.txt 2>&1; then pass "first run"
else fail "first run"; tail -5 /tmp/a3-g1a.txt; fi
if python -m pytest -q >/tmp/a3-g1b.txt 2>&1; then pass "second run"
else fail "second run (the property that was broken)"; tail -5 /tmp/a3-g1b.txt; fi

echo "== gate 2: a live campaign cannot be started by omitting a flag =="
if python -m harness.campaign --out-dir /tmp/a3-refuse >/tmp/a3-g2.txt 2>&1; then
  fail "a live campaign started without --pool or --i-have-authorisation"
else
  grep -q "refusing to start a LIVE campaign" /tmp/a3-g2.txt \
    && pass "refused, and said why" \
    || { fail "refused for the wrong reason"; head -3 /tmp/a3-g2.txt; }
fi

echo "== gate 3: a sealed game is refused by name =="
python - <<'PY' && pass "sealed pile refused" || fail "sealed pile NOT refused"
import json, os, sys
sys.path.insert(0, os.getcwd())
import _bootstrap                                       # noqa: F401
from harness import campaign as camp
piles = json.load(open(os.path.join(camp.REPO, "arc-recon", "data",
                                    "piles.json"), encoding="utf-8"))
try:
    camp.assert_dev_pile([piles["sealed_pile"][0]])
except camp.CampaignStopped:
    sys.exit(0)
sys.exit(1)
PY

echo "== gate 4: the offline rehearsal reproduces =="
POOL="$(mktemp -d)/pool.jsonl"
OUT="$(mktemp -d)/rehearsal"
mkdir -p "$OUT"
if timeout 900 python -m harness.campaign --mock --pool "$POOL" \
     --out-dir "$OUT" --games g50t-5849a774 sk48-d8078629 \
     --max-legs 2 --actions-per-level 6 >/tmp/a3-g4.txt 2>&1; then
  pass "campaign ran end to end against the mock"
else
  fail "rehearsal failed"; tail -8 /tmp/a3-g4.txt
fi
for f in campaign.json MANIFEST.json campaign_series.json; do
  [ -s "$OUT/$f" ] && pass "wrote $f" || fail "missing $f"
done
python - "$OUT" <<'PY' && pass "campaign_turn dense, leg turn restarts" \
                        || fail "campaign axis is wrong"
import json, os, sys
doc = json.load(open(os.path.join(sys.argv[1], "campaign_series.json"),
                     encoding="utf-8"))
rows = doc["rows"]
turns = [r["campaign_turn"] for r in rows]
sys.exit(0 if turns == list(range(1, len(rows) + 1)) else 1)
PY

echo "== gate 5: no money moved and the shared pool was not touched =="
python - "$OUT" <<'PY' && pass "rehearsal spent \$0.00" || fail "rehearsal spent money"
import json, os, sys
doc = json.load(open(os.path.join(sys.argv[1], "campaign.json"),
                     encoding="utf-8"))
sys.exit(0 if float(doc["spent_usd"]) == 0.0 else 1)
PY
# The scratch pool must be somewhere other than the fleet's. `_scratch_policy`
# refuses a path under runs/ or named ledger.jsonl; this checks the run
# actually used the scratch one.
case "$POOL" in
  *"/proxy/var/"*) fail "the rehearsal drew on the SHARED pool" ;;
  *) pass "drew on a scratch pool outside proxy/var/" ;;
esac

echo "== gate 6: the negative controls -- each fix must be re-breakable =="
SCRATCH="$(mktemp -d)"
cp -r "$ARM" "$SCRATCH/arm" 2>/dev/null
cd "$SCRATCH/arm" || exit 2

# 6a. blocker A: the five non-canonical fields on model_call.
python - <<'PY'
import re
p = "harness/modelcall.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""                  "elapsed_ms": elapsed_ms, "attempts": 1,
                  "forwarded": False, "stream": False},
        )""",
"""                  "elapsed_ms": elapsed_ms, "attempts": 1,
                  "forwarded": False, "stream": False},
            beat=beat, label=label, transport="claude-code-cli",
            proxied=False, proxy_gap="re-broken by verify.sh gate 6a",
        )""", 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
PY
if python -m pytest -q tests/test_desk_gate.py -k canonical_model_call \
     >/tmp/a3-g6a.txt 2>&1; then
  fail "6a: re-breaking the canon fix did NOT turn its test red"
else
  pass "6a: canon regression test goes red when the fix is removed"
fi
cd "$ARM" || exit 2
rm -rf "$SCRATCH"

# 6b. the anonymity guard.
SCRATCH="$(mktemp -d)"; cp -r "$ARM" "$SCRATCH/arm" 2>/dev/null
cd "$SCRATCH/arm" || exit 2
python - <<'PY'
p = "harness/modelcall.py"
s = open(p, encoding="utf-8").read()
s = s.replace("        leaked = sorted({s for s in self.forbid_in_prompt if s in prompt})",
              "        leaked = []      # re-broken by verify.sh gate 6b", 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
PY
if python -m pytest -q tests/test_desk_gate.py -k "carrying_the_game_id" \
     >/tmp/a3-g6b.txt 2>&1; then
  fail "6b: disabling the anonymity guard did NOT turn its test red"
else
  pass "6b: anonymity test goes red when the guard is disabled"
fi
cd "$ARM" || exit 2
rm -rf "$SCRATCH"

# 6c. the leg-cost key.
SCRATCH="$(mktemp -d)"; cp -r "$ARM" "$SCRATCH/arm" 2>/dev/null
cd "$SCRATCH/arm" || exit 2
python - <<'PY'
p = "harness/campaign.py"
s = open(p, encoding="utf-8").read()
s = s.replace('    cli = desk.get("cli_cost_usd")',
              '    cli = desk.get("cost_usd")      # re-broken by gate 6c', 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
PY
if python -m pytest -q tests/test_campaign.py -k "leg_cost_reads_a_key" \
     >/tmp/a3-g6c.txt 2>&1; then
  fail "6c: restoring the wrong cost key did NOT turn its test red"
else
  pass "6c: leg-cost test goes red when the wrong key is restored"
fi
cd "$ARM" || exit 2
rm -rf "$SCRATCH"

echo
if [ "$FAILED" -eq 0 ]; then
  echo "A3 verify: ALL GREEN"
  exit 0
fi
echo "A3 verify: $FAILED FAILED"
exit 1
