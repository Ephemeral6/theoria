#!/usr/bin/env bash
# release's green light. Offline by construction: no API call, no network, no
# action spent, and nothing written -- every step here is a --dry-run or a read.
#
#     cd release && bash verify.sh
#
# Exit 0 means: the red-line negative controls pass, the two red lines are clear
# over every tracked file *and the check could read every one of them*, the
# enumerator classifies the whole tree without abstaining, the checklist has no
# undetermined item, and the S23 before/after archive still reproduces.
#
# It does NOT mean the release is licensed to ship. That is a human call over
# `LICENCE_POSTURE.md` and the WITHHELD items, and no script decides it.
#
# ## Why this file exists
#
# `monitor/gates.py` reported `UNGATED: release` -- `monitor/ci_merge.py` was
# merging branches that touch the release machinery with nothing checking them,
# and logging that fact to `monitor/ci/merge.log` where it read as a category
# rather than as a gap. The territory holding the credential and sealed-pile red
# lines was the one territory with no gate of its own.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
fail=0

step() {
    echo
    echo "== $1"
    shift
    if "$@"; then
        echo "-- ok"
    else
        echo "-- FAILED (exit $?)"
        fail=1
    fi
}

# The negative controls come first. Every other step in this file reports that
# nothing is wrong, and a check that has never been seen to fail cannot
# distinguish "nothing is wrong" from "nothing is being checked" -- which is the
# defect S23 was opened about, so it is the one this gate refuses to repeat.
step "red-line negative controls" python -m pytest -q

# The mode is chosen by whether a credential is actually reachable, not fixed.
#
# This step used to pass `--mode verify` unconditionally, and that is this work
# order's own sentence turned on its own gate: in `verify` mode a missing key is
# reported NOT APPLICABLE with no violation and no needs_human, so on any
# checkout without `.env` the release gate came back green having not run half of
# what it gates. Where the key IS reachable -- this repository -- the strict mode
# must be the one that runs, or the strict path is never exercised at all.
#
# Where it is genuinely absent, `verify` is still correct: a stranger checking a
# release they were handed has no key to search the tree for, and telling them
# their clean checkout is dirty would be a lie in the other direction. But it is
# announced rather than silent, because a gate is allowed to skip a check and is
# not allowed to skip it quietly.
# Asked of the reader, not of the filesystem. `[ -f ../.env ]` was the first
# form and it is wrong inside a worktree: `arc-recon/client.py` resolves the
# MAIN checkout's `.env`, so the file is absent right here and the key is
# reachable anyway. The only honest question is whether `load_api_key()` returns.
# The path is relative because this script has already cd'd to its own
# directory: interpolating "$HERE" produced a POSIX `/c/...` path that the
# Windows interpreter cannot resolve, so the probe failed on the one machine
# where the key is definitely present and silently chose the lenient mode --
# a check that skipped itself while reporting on the skip. Exactly the shape.
if python -c "
import sys, os
sys.path.insert(0, os.path.join(os.pardir, 'arc-recon'))
from client import load_api_key
load_api_key()
" >/dev/null 2>&1; then
    MODE=generate
else
    MODE=verify
    echo
    echo "!! No .env is reachable, so the credential red line CANNOT run."
    echo "!! Falling back to --mode verify. This gate is about to report on the"
    echo "!! sealed-pile red line only. That is the right answer when checking a"
    echo "!! release you were handed; it is NOT a check of a tree you are about"
    echo "!! to publish from."
fi
step "red lines clear, and every tracked file was actually read (--mode $MODE)" \
    python check_redlines.py --mode "$MODE"

# Non-zero if any tracked file lands in class `?`/needs_human, because the
# manifest asserts a licence class for every tracked file and cannot assert one
# for a file it could not read.
step "every tracked file is classified" python enumerate.py --dry-run --mode "$MODE"

step "no checklist item rests on an unclassified file" python checklist.py --dry-run

# The archived before/after is a claim about what the old code did, and a claim
# that is not re-checked decays into a story. This replays BOTH versions over the
# planted negative samples and asserts the before/after verdicts are still what
# the run report says they were.
step "the S23 before/after archive still reproduces" \
    python runs/20260728T234923Z-S23/replicate.py

echo
if [ "$fail" -eq 0 ]; then
    echo "VERIFY: green"
else
    echo "VERIFY: RED"
fi
exit "$fail"
