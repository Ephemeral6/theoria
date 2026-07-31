#!/usr/bin/env sh
# P-24 rehearsal -- drive all four fleet skills end to end in a throwaway
# worktree, then prove each guard can actually go red.
#
#   sh .claude/skills/runs-p24/rehearse.sh            (from a checkout that has the skills)
#
# It creates worktree ../theoria-wt-p24r on branch agent/p24r-rehearsal, uses
# engine-rig as the rehearsal territory (a real suite, 150 tests), and removes
# both at the end. Nothing is pushed. A sealed game id is used as a negative
# control and is redacted out of this transcript before it is archived.
set -u

HOST=$(cd "$(dirname "$0")/../../.." && git rev-parse --show-toplevel)
cd "$HOST" || exit 2
PY=${PYTHON:-python}
SK=.claude/skills
RITUAL="$SK/fleet-branch-ritual/scripts/start_ritual.py"
ARCH="$SK/runs-archive/scripts/runs_archive.py"
GATE="$SK/verify-gate/scripts/verify_gate.py"
GUARD="$SK/verify-gate/scripts/guards.py"
CLOSE="$SK/handoff-close/scripts/handoff_close.py"

WT=$(cd .. && pwd)/theoria-wt-p24r
BRANCH=agent/p24r-rehearsal
BASE=$(git rev-parse HEAD)
PASS=0
FAIL=0

step() { printf '\n########## %s\n' "$*"; }
expect() {                       # expect <wanted-rc> <label> -- <cmd...>
  want=$1; label=$2; shift 3
  "$@"
  got=$?
  if [ "$got" -eq "$want" ]; then
    printf '\n[ok  ] %s (exit %s as expected)\n' "$label" "$got"
    PASS=$((PASS + 1))
  else
    printf '\n[BAD ] %s (exit %s, wanted %s)\n' "$label" "$got" "$want"
    FAIL=$((FAIL + 1))
  fi
}

printf '=== P-24 rehearsal ===\nhost checkout : %s\nbase          : %s\n' "$HOST" "$BASE"

# The rehearsal worktree is a fresh checkout of $BASE, so it runs the *committed*
# skills, not your working copy. Rehearsing uncommitted edits silently tests the
# previous version -- which is how the first run of this script reported green
# checks for code that no longer existed.
if ! git diff --quiet -- "$SK" || ! git diff --cached --quiet -- "$SK"; then
  printf '\nABORT: %s has uncommitted changes. Commit them first -- the rehearsal\n' "$SK"
  printf 'checks out %s and would otherwise exercise the previous version.\n' "$(echo "$BASE" | cut -c1-7)"
  exit 2
fi

# ------------------------------------------------------------------ cleanup
git worktree remove --force "$WT" 2>/dev/null
git branch -D "$BRANCH" 2>/dev/null
rm -rf "$WT"

# ------------------------------------------------------- 1. branch ritual
step "1. fleet-branch-ritual -- open the ticket"
expect 0 "start_ritual" -- "$PY" "$RITUAL" \
  --ticket P-24R --slug rehearsal --territory engine-rig \
  --worktree "$WT" --branch "$BRANCH" --base "$BASE" \
  --no-fetch --sections 1 --now 2026-07-28T12:00:00Z

cd "$WT" || exit 2
printf '\nticket context:\n'
cat "$(git rev-parse --absolute-git-dir)/fleet-ticket.json"

# ------------------------------------------------------- 2. runs archive
step "2. runs-archive -- open the archive, write as you go"
expect 0 "archive new" -- "$PY" "$ARCH" --now 2026-07-28T12:01:00Z new --slug engines-smoke
expect 0 "archive note" -- "$PY" "$ARCH" --now 2026-07-28T12:02:00Z note \
  --text "Rehearsal: ran the six engines end to end via tools.run_all."
expect 0 "archive record json" -- "$PY" "$ARCH" record \
  --key engines.count --json 6
expect 0 "archive record str" -- "$PY" "$ARCH" record \
  --key tests --value "150 passed, 1 skipped"

RUN=$("$PY" - <<'EOF'
import json, pathlib, subprocess
gd = subprocess.run(["git","rev-parse","--absolute-git-dir"],capture_output=True,text=True).stdout.strip()
print(json.loads(pathlib.Path(gd,"fleet-ticket.json").read_text(encoding="utf-8"))["run_dir"])
EOF
)
printf 'run dir: %s\n' "$RUN"

step "2b. MANIFEST"
expect 0 "manifest" -- "$PY" "$ARCH" --now 2026-07-28T12:03:00Z manifest \
  --title "P-24 rehearsal: engine-rig smoke" --seed 1729 \
  --tests "150 passed, 1 skipped" \
  --include 'engine-rig/pytest.ini' --include-tracked engine-rig/tools
printf '\n-- MANIFEST head --\n'
head -n 24 "$RUN/MANIFEST.json"

expect 0 "manifest check (green)" -- "$PY" "$ARCH" check

step "2c. determinism -- same inputs + same --now must give the same bytes"
cp "$RUN/MANIFEST.json" /tmp/p24-manifest-a.json
"$PY" "$ARCH" --now 2026-07-28T12:03:00Z manifest \
  --title "P-24 rehearsal: engine-rig smoke" --seed 1729 \
  --tests "150 passed, 1 skipped" \
  --include 'engine-rig/pytest.ini' --include-tracked engine-rig/tools >/dev/null
expect 0 "MANIFEST is byte-reproducible" -- cmp /tmp/p24-manifest-a.json "$RUN/MANIFEST.json"

# ------------------------------------------------------- 3. verify gate
step "3. verify-gate -- generate and run"
expect 0 "gate gen" -- "$PY" "$GATE" --now 2026-07-28T12:04:00Z gen \
  --require "$RUN/MANIFEST.json" \
  --check "fixtures are byte-stable::cd engine-rig && $PY -m fixtures.generate_all >/dev/null && git diff --quiet -- fixtures"
printf '\n-- verify.sh --\n'
cat engine-rig/verify.sh
expect 0 "gate run (green)" -- "$PY" "$GATE" run

# ------------------------------------------------- 4. negative controls
step "4. negative controls -- every guard must be able to go red"

printf '\n--- 4a boundary: touch a file outside the territory\n'
printf 'stray\n' > battery/P24R_STRAY.txt
expect 1 "boundary goes red on a stray file" -- \
  "$PY" "$GUARD" boundary --base "$BASE" --territory engine-rig
rm -f battery/P24R_STRAY.txt
expect 0 "boundary green again once removed" -- \
  "$PY" "$GUARD" boundary --base "$BASE" --territory engine-rig

printf '\n--- 4b sealed pile: a sealed game id in a changed file (id redacted below)\n'
SEALED=$("$PY" - <<'EOF'
import json
d = json.load(open("arc-recon/data/piles.json", encoding="utf-8"))
dev = set(d["dev_pile"])
print(sorted(set(d["contamination_register"]) - dev)[0])
EOF
)
printf 'observed %s while reading upstream notes\n' "$SEALED" > "$RUN/leak.md"
out=$("$PY" "$GUARD" sealed --base "$BASE" 2>&1); rc=$?
printf '%s\n' "$out" | sed "s/$SEALED/<sealed-id-redacted>/g"
if [ "$rc" -eq 1 ]; then printf '[ok  ] sealed guard goes red (exit 1)\n'; PASS=$((PASS+1));
else printf '[BAD ] sealed guard exit %s, wanted 1\n' "$rc"; FAIL=$((FAIL+1)); fi
rm -f "$RUN/leak.md"
expect 0 "sealed green again once removed" -- "$PY" "$GUARD" sealed --base "$BASE"

printf '\n--- 4c credential: a .env value reaching a tracked file (fake key, never a real one)\n'
# The fake value is *composed at run time* and never appears as a literal in this
# file. First attempt hard-coded it, and the guard duly flagged rehearse.sh
# itself -- correct behaviour, useless fixture.
FAKEVAL="rehearsal-not-a-key-$(printf '%s' "$BASE" | cut -c1-16)"
printf 'FAKE_TOKEN=%s\n' "$FAKEVAL" > .env
printf 'token = "%s"\n' "$FAKEVAL" > engine-rig/p24r_leak.py
expect 1 "secret guard goes red on a leaked value" -- "$PY" "$GUARD" secret --base "$BASE"
rm -f engine-rig/p24r_leak.py
expect 0 "secret green again once removed" -- "$PY" "$GUARD" secret --base "$BASE"
rm -f .env

printf '\n--- 4d MANIFEST drift: change an artefact after it was hashed\n'
printf '\ndrift\n' >> "$RUN/NOTES.md"
expect 1 "manifest check goes red on drift" -- "$PY" "$ARCH" check
"$PY" "$ARCH" --now 2026-07-28T12:05:00Z manifest \
  --title "P-24 rehearsal: engine-rig smoke" --seed 1729 \
  --tests "150 passed, 1 skipped" \
  --include 'engine-rig/pytest.ini' --include-tracked engine-rig/tools >/dev/null
expect 0 "manifest check green after regeneration" -- "$PY" "$ARCH" check

printf '\n--- 4e PARTNER_SYNC: an edit to somebody else s paragraph\n'
"$PY" - <<'EOF'
import pathlib
p = pathlib.Path("PARTNER_SYNC.md")
t = p.read_text(encoding="utf-8")
p.write_text(t.replace("状态", "狀態", 1), encoding="utf-8", newline="\n")
EOF
expect 2 "sync refuses a non-append board" -- "$PY" "$CLOSE" sync \
  --track engine-rig --tag p24r-rehearsal \
  --status s --tests t --blocked none --next n
git checkout -- PARTNER_SYNC.md

printf '\n--- 4f verify.sh as a whole must go red when any one check is red\n'
printf 'stray\n' > battery/P24R_STRAY.txt
expect 1 "verify.sh red, and still prints every line" -- "$PY" "$GATE" run
rm -f battery/P24R_STRAY.txt

# ------------------------------------------------------- 5. handoff close
step "5. handoff-close -- 收工"
expect 0 "run-state template" -- "$PY" "$CLOSE" --now 2026-07-28T12:06:00Z run-state \
  --delivered "Rehearsal only: nothing was delivered to engine-rig." \
  --gaps "none -- this branch is a rehearsal and is deleted at the end." \
  --verify "6/6 green" --tests "150 passed, 1 skipped" \
  --open-items "none"
expect 1 "close blocks while PARTNER_SYNC has no section" -- "$PY" "$CLOSE" close --track engine-rig
expect 0 "sync appends a well-formed section" -- "$PY" "$CLOSE" --now 2026-07-28T12:07:00Z sync \
  --track engine-rig --tag p24r-rehearsal \
  --status "P-24 技能库演练，engine-rig 作靶territory，未交付任何代码" \
  --tests "150 passed, 1 skipped;验收 6/6 green" \
  --blocked "无" \
  --next "删除演练分支"
printf '\n-- tail of PARTNER_SYNC.md --\n'
tail -n 6 PARTNER_SYNC.md

printf 'stray\n' > battery/P24R_STRAY.txt
git add -A                       # the mistake this guard exists to catch
expect 2 "commit refuses a stray staged by `git add -A`" -- "$PY" "$CLOSE" commit --dry-run
git reset -q; rm -f battery/P24R_STRAY.txt

expect 0 "commit stages the territory only" -- "$PY" "$CLOSE" commit \
  -m "P-24R rehearsal (throwaway)"
expect 0 "close checklist green" -- "$PY" "$CLOSE" close --track engine-rig
expect 0 "push --dry-run" -- "$PY" "$CLOSE" push --dry-run

printf '\n--- 5b push must refuse master\n'
git checkout -q master 2>/dev/null || git checkout -q -B p24r-tmp-master
expect 2 "push refuses the wrong branch" -- "$PY" "$CLOSE" push --dry-run
git checkout -q "$BRANCH"

# ------------------------------------------------------------------ report
step "rehearsal result"
printf '%s/%s expectations met\n' "$PASS" "$((PASS + FAIL))"

cd "$HOST" || exit 2
if [ "${KEEP:-0}" = "0" ]; then
  git worktree remove --force "$WT" 2>/dev/null
  git branch -D "$BRANCH" 2>/dev/null
  git branch -D p24r-tmp-master 2>/dev/null
  printf 'rehearsal worktree and branch removed.\n'
fi
[ "$FAIL" -eq 0 ] || exit 1
