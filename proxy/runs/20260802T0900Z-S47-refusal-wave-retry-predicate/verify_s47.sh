#!/usr/bin/env bash
# S47's acceptance, re-runnable. Offline: no network, no API call, no spend.
#
# The board item's acceptance line has four parts and each is a check here:
#   1. the predicate is true only when all three conjuncts hold;
#   2. the two mandatory negatives (`scorecard ... not found`, another game's id)
#      and the third (a genuine 400 stops after one attempt);
#   3. replaying the four archived legs shrinks the `env_step` row count by
#      classification while `actions_agree` stays true;
#   4. the repo's red lines are intact.
#
# Run from the repository root:
#     bash proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate/verify_s47.sh
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
cd "$ROOT"

fail=0
step() { printf '\n== %s\n' "$1"; }
ok()   { printf -- '-- ok\n'; }
bad()  { printf -- '-- FAILED: %s\n' "$1"; fail=1; }

LEGS=(
  theoria-arm/runs/20260731T1240Z-A3-level2-carried/ledger.jsonl
  theoria-arm/runs/20260731T1310Z-A3-level2-carried-r2/ledger.jsonl
  theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/ledger.jsonl
  theoria-arm/runs/20260731T1500Z-A3-sk48-carried-l1/ledger.jsonl
)

step "the predicate's own tests, including all three negative samples"
if (cd proxy && python -m pytest tests/test_forward_retry_predicate.py -q); then ok
else bad "the retry predicate's tests"; fi

step "the offline replay's tests"
if (cd proxy && python -m pytest tests/test_refusal_replay.py -q); then ok
else bad "the replay simulator's tests"; fi

step "the whole proxy suite (the invocation pytest.ini is written for)"
if (cd proxy && python -m pytest -q); then ok
else bad "proxy suite"; fi

step "the four archived legs replay: rows shrink, actions_agree holds, sockets do not move"
missing=0
for leg in "${LEGS[@]}"; do [ -f "$leg" ] || { echo "   absent: $leg"; missing=1; }; done
if [ "$missing" = 1 ]; then
    echo "   SKIPPED -- the archived legs are not in this checkout."
    echo "   This is the one check that cannot be run everywhere; it is not a pass."
else
    args=(); for leg in "${LEGS[@]}"; do args+=(--leg "$leg"); done
    if python -m proxy.tools.refusal_replay --verify "${args[@]}" \
            -o "$HERE/refusal_replay.rerun.json" >/dev/null; then
        python - "$HERE/refusal_replay.rerun.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8"))
p = r["pooled"]
print("   rows %d -> %d (%.1f%% fewer), sockets %d/%d, actions %d"
      % (p["env_steps_before"], p["env_steps_after"], 100 * p["row_reduction"],
         p["outbound_attempts_before"], p["outbound_attempts_after"],
         p["scorecard_total_actions"]))
print("   actions_agree before=%s after=%s | invariants %s"
      % (p["actions_agree_before"], p["actions_agree_after"], r["invariants"]))
PY
        # Byte-identical to the archived report, or the claim in RUN_STATE is
        # about a run nobody can reproduce.
        if python -c "
import sys
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read()
sys.exit(0 if a==b else 1)" "$HERE/refusal_replay.json" "$HERE/refusal_replay.rerun.json"; then
            ok
        else
            bad "the replay no longer reproduces the archived refusal_replay.json"
        fi
        rm -f "$HERE/refusal_replay.rerun.json"
    else
        bad "the replay's own invariants (see its FAIL lines)"
    fi
fi

step "red line: nothing changed outside proxy/ and monitor/inbox/"
# Against the **merge base**, not against `master`. Master is a moving target on
# a fleet board -- it advanced past this branch's base while this ticket was
# being written -- and diffing a moving ref reports other cells' landed work as
# this branch's strays. The honest question is "what did this branch change",
# and that is the merge base's question.
BASE="$(git merge-base HEAD master)"
echo "   merge base: $(git rev-parse --short "$BASE")"
strays="$(git diff --name-only "$BASE"; git ls-files --others --exclude-standard)"
strays="$(printf '%s\n' "$strays" | sort -u | grep -v '^proxy/' | grep -v '^monitor/inbox/' || true)"
if [ -z "$strays" ]; then ok; else bad "changed outside the territory: $strays"; fi

step "red line: no sealed-pile game id in anything this branch added"
if python - <<'PY'
import json, subprocess, sys
piles = json.load(open("arc-recon/data/piles.json", encoding="utf-8"))
ids = [g["game_id"] if isinstance(g, dict) else g for g in piles["sealed_pile"]]
stems = {s for i in ids for s in (i, i.split("-")[0]) if s}
base = subprocess.run(["git", "merge-base", "HEAD", "master"],
                      capture_output=True, text=True).stdout.strip()
diff = subprocess.run(["git", "diff", "-U0", base], capture_output=True,
                      text=True, encoding="utf-8").stdout
added = [l[1:] for l in diff.splitlines()
         if l.startswith("+") and not l.startswith("+++")]
for path in subprocess.run(["git", "ls-files", "--others", "--exclude-standard"],
                           capture_output=True, text=True).stdout.split():
    added += open(path, encoding="utf-8", errors="replace").read().splitlines()
hits = sorted({s for line in added for s in stems if s in line})
if hits:
    print("   sealed ids in added lines: %s" % ", ".join(hits))
    sys.exit(1)
print("   %d added lines, zero sealed-pile ids" % len(added))
PY
then ok; else bad "a sealed-pile id appears in added content"; fi

step "red line: no credential value in any tracked file"
if python - <<'PY'
import os, subprocess, sys
# The value is read and compared, never printed. A key that reached a tracked
# file is a key the Phase 4 release manifest publishes.
#
# `.env` lives at the **main** checkout's root and is gitignored, so a worktree
# does not have one. The first version of this check ran from a worktree, found
# no `.env`, and printed "nothing to leak" -- a red line that passes precisely
# because it could not find the thing it guards. `--git-common-dir` points at
# the shared `.git`, whose parent is the main checkout, so the secret is found
# from either place.
# `arc-recon/client.load_api_key()` first, because CLAUDE.md says to prefer the
# shared reader over parsing `.env`, and because it answers the only honest
# question -- "is a key reachable from here" -- rather than "is there a file
# here". `release/verify.sh:60-68` had already worked this out and its note is
# worth quoting: asking the filesystem produced "a check that skipped itself
# while reporting on the skip".
main_root = os.path.dirname(os.path.abspath(
    subprocess.run(["git", "rev-parse", "--git-common-dir"],
                   capture_output=True, text=True).stdout.strip() or ".git"))
sys.path.insert(0, os.path.join(main_root, "arc-recon"))

secrets, source = [], None
try:
    from client import load_api_key
    secrets, source = [load_api_key()], "arc-recon.client.load_api_key()"
except Exception:
    fallback = os.path.join(main_root, ".env")
    if os.path.exists(fallback):
        for line in open(fallback, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if len(value) >= 16:
                    secrets.append(value)
        source = fallback

secrets = [s for s in secrets if s and len(s) >= 16]
if not secrets:
    # Loud, and NOT a pass. "I found no secret" and "no secret leaked" are
    # different sentences, and only one of them is evidence. The first version
    # of this check ran from a worktree, found no `.env` beside it, printed
    # "nothing to leak" and went green.
    print("   INCONCLUSIVE: no credential is reachable from here, so this red "
          "line CANNOT run. Looked via arc-recon/client.py and %s/.env"
          % main_root)
    sys.exit(1)
print("   %d secret(s) reached via %s (values never printed)"
      % (len(secrets), source))
tracked = subprocess.run(["git", "ls-files"], capture_output=True,
                         text=True).stdout.split()
hits = []
for path in tracked:
    try:
        blob = open(path, encoding="utf-8", errors="replace").read()
    except (OSError, IsADirectoryError):
        continue
    if any(s in blob for s in secrets):
        hits.append(path)
if hits:
    print("   CREDENTIAL VALUE FOUND IN: %s" % ", ".join(hits))
    sys.exit(1)
print("   %d tracked files scanned, zero credential values" % len(tracked))
PY
then ok; else bad "a credential value is in a tracked file, or the check could not find a secret to look for"; fi

step "red line: this branch opened no socket to the live API"
if git diff "$BASE" --stat -- proxy/replay.py | grep -q .; then
    bad "proxy/replay.py changed -- that is the one module here that spends"
elif python - <<'PY'
# The imports, read with `ast`, not a grep over the source. The first version of
# this check was a regex for `requests\.`, and it went red on the phrase "what
# this archived row cost in outbound requests." in a docstring -- a gate that
# cries wolf at its own prose is a gate people learn to ignore.
import ast, sys
NETWORK = {"urllib", "socket", "http", "requests", "ssl", "asyncio", "ftplib",
           "smtplib", "telnetlib", "xmlrpc", "aiohttp", "httpx"}
path = "proxy/tools/refusal_replay.py"
tree = ast.parse(open(path, encoding="utf-8").read())
found = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        found |= {a.name.split(".")[0] for a in node.names}
    elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
        found.add(node.module.split(".")[0])
leaks = sorted(found & NETWORK)
if leaks:
    print("   %s imports %s" % (path, ", ".join(leaks)))
    sys.exit(1)
print("   proxy/replay.py untouched; %s imports %s -- nothing network-facing"
      % (path, ", ".join(sorted(found)) or "nothing"))
PY
then ok; else bad "the offline replay reaches for the network"; fi

printf '\n'
if [ "$fail" = 0 ]; then echo "S47 VERIFY GREEN"; else echo "S47 VERIFY FAILED"; fi
exit "$fail"
