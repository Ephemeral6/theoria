#!/usr/bin/env bash
# E3 -- the whole deliverable, checked offline.
#
# No key, no network, no model call, no quota, no billed action. Everything the
# live second game depends on is exercised here first, because a property
# discovered during a paid run has already cost the money it was supposed to
# protect.
#
#   cd theoria-arm && bash verify_e3.sh                  # the offline deliverable
#   cd theoria-arm && bash verify_e3.sh <live-run-slug>  # and the live run too
#
# The optional argument re-runs the artefact checks and the credential scan
# against a real run directory. The credential scan in particular is worth
# almost nothing against the mock -- the mock has its own key -- and is worth a
# great deal against a run that actually held the ARC key.
#
set -uo pipefail

cd "$(dirname "$0")"
REPO="$(cd .. && pwd)"
LIVE_SLUG="${1:-}"

fail=0
step() { printf '\n=== %s\n' "$1"; }
ok()   { printf '  ok   %s\n' "$1"; }
bad()  { printf '  FAIL %s\n' "$1"; fail=1; }

step "1/6  the offline suite"
if python -m pytest -q; then ok "pytest"; else bad "pytest"; fi

step "2/6  a carried run, end to end, against the mock"
SLUG="verify-e3-carried"
rm -rf "runs/$SLUG"
if python -m harness.run --mock --budget 8 --slug "$SLUG" \
      --carry-books runs/20260728T015354Z-g50t-first-contact/books \
      --carry-source-game g50t-5849a774 \
      --prompt-id E3-engines-online >/dev/null 2>&1; then
  ok "the run completed"
else
  bad "the run did not complete"
fi

step "3/6  the artefacts E3 promised"
for f in transfer.json CARRIED.json engines_online.jsonl engines_online.json \
         bill_shape.json candidates.jsonl ledger.jsonl; do
  if [ -s "runs/$SLUG/$f" ]; then ok "$f"; else bad "$f is missing or empty"; fi
done

step "4/6  the properties those artefacts have to have"
python - "$SLUG" <<'PY'
import json, os, sys
slug = sys.argv[1]
d = os.path.join("runs", slug)
bad = []

def check(cond, why):
    if not cond:
        bad.append(why)

t = json.load(open(os.path.join(d, "transfer.json"), encoding="utf-8"))
check(t["stage"] == "cold", "transfer.json is not the cold report")
check(t["model_calls_so_far"] == 0,
      "the cold report was written after a model call")
check("problem.json" in t["provenance"]["not_carried"],
      "problem.json is not declared as un-carried")
check(t["prediction_scored"]["verdict"] in
      ("held", "refuted", "withheld", "unscorable"),
      "the carried formula was not scored")
check("retention" in t, "no retention record")

# Whether this game can test the carried theory at all decides how every other
# number in the report may be read, so it must be present and it must be
# stated, not inferred. INC-TA-007's neighbour: the first carry had no such
# field and its replay result was read as evidence it could not be.
check(isinstance(t.get("carried_theory_is_testable_on_this_game"), bool),
      "the cold report does not say whether the carried theory is testable here")
check(isinstance((t.get("actions") or {}).get("shared"), list),
      "no action-vocabulary overlap was computed")
check("evidence" in (t.get("replay_means") or ""),
      "the report does not say what its replay result means")

carried = json.load(open(os.path.join(d, "CARRIED.json"), encoding="utf-8"))
check(carried["carried"]["theory.dsl"]["sha256"], "the carried manual is unhashed")
check(not os.path.exists(os.path.join(d, "books", "problem.json")) or
      json.load(open(os.path.join(d, "books", "problem.json"),
                     encoding="utf-8")).get("name") is not None,
      "problem.json is malformed")

rows = [json.loads(x) for x in open(os.path.join(d, "engines_online.jsonl"),
                                    encoding="utf-8") if x.strip()]
check(rows, "no engine dispatch recorded")
check(all("run_id" in r for r in rows), "an engine row has no run_id")
check(rows[0]["label"] == "cold",
      "the first dispatch is not the zero-model-call one")
for r in rows:
    for name in ("mdl_segmenter", "cegis_miner", "zero_space"):
        e = r["engines"][name]
        check(e.get("delivered") or e.get("error") or e.get("skipped"),
              "%s came back empty with no reason on dispatch %d"
              % (name, r["dispatch_idx"]))

bill = json.load(open(os.path.join(d, "bill_shape.json"), encoding="utf-8"))
run = json.load(open(os.path.join(d, "run.json"), encoding="utf-8"))
check(bill["totals"]["actions_billed"] ==
      run["summary"]["budget"]["actions_ok"],
      "the bill's action axis disagrees with the budget")
cum = [c["usd_cumulative"] for c in bill["calls"]]
check(cum == sorted(cum), "cumulative spend is not monotonic")

if bad:
    for b in bad:
        print("  FAIL %s" % b)
    sys.exit(1)
print("  ok   transfer / engines / bill all hold")
PY
[ $? -eq 0 ] || fail=1

step "5/6  the frozen candidate schema"
if (cd "$REPO/engine-rig" && \
    python -m tools.validate_candidates \
      "$REPO/theoria-arm/runs/$SLUG/candidates.jsonl" >/dev/null); then
  ok "candidates.jsonl satisfies CONTRACTS/candidates_schema.md"
else
  bad "candidates.jsonl violates the frozen schema"
fi

step "6/6  no credential in anything these runs wrote"
python - "$SLUG" "$LIVE_SLUG" <<'PY'
import os, sys

# A worktree has no `.env` of its own -- it lives at the main checkout's root --
# so looking only at `..` finds nothing and reports a pass that checked nothing.
# Every plausible root is tried and the search is reported as skipped if none
# of them holds a key, which is a different outcome from "no key was found in
# the artefacts" and must not be printed as though it were the same.
def find_key():
    here = os.path.abspath("..")
    roots = [here]
    for _ in range(3):
        here = os.path.dirname(here)
        roots.append(here)
    for root in roots:
        env = os.path.join(root, ".env")
        if not os.path.exists(env):
            continue
        for line in open(env, encoding="utf-8"):
            if line.strip().startswith("ARC_API_KEY"):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value, env
    return None, None

key, env = find_key()
slugs = [s for s in sys.argv[1:] if s]
if not key:
    print("  SKIP no ARC_API_KEY found in any .env above this directory, so "
          "this scan checked nothing")
    sys.exit(0)

hits = []
for slug in slugs:
    for root, _dirs, names in os.walk(os.path.join("runs", slug)):
        for name in names:
            path = os.path.join(root, name)
            try:
                if key in open(path, encoding="utf-8", errors="ignore").read():
                    hits.append(path)
            except OSError:
                pass
if hits:
    print("  FAIL the ARC key appears in: %s" % ", ".join(hits))
    sys.exit(1)
print("  ok   the ARC key (from %s) appears in nothing under %s"
      % (env, ", ".join("runs/" + s for s in slugs)))
PY
[ $? -eq 0 ] || fail=1

if [ -n "$LIVE_SLUG" ]; then
  step "7/7  the live run's artefacts"
  for f in transfer.json CARRIED.json engines_online.jsonl bill_shape.json \
           candidates.jsonl ledger.jsonl MANIFEST.json; do
    if [ -s "runs/$LIVE_SLUG/$f" ]; then ok "$f"; else bad "$f is missing or empty"; fi
  done
  if (cd "$REPO/engine-rig" && \
      python -m tools.validate_candidates \
        "$REPO/theoria-arm/runs/$LIVE_SLUG/candidates.jsonl" >/dev/null); then
    ok "the live candidate stream satisfies the frozen schema"
  else
    bad "the live candidate stream violates the frozen schema"
  fi
fi

printf '\n'
if [ "$fail" -eq 0 ]; then
  echo "VERIFY-E3 GREEN"
else
  echo "VERIFY-E3 RED"
fi
exit "$fail"
