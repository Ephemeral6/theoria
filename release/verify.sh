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

# `--mode verify` rather than the strict default: this script must be runnable by
# someone checking a release they were handed, who has no `.env` because the
# credential was never theirs and never shipped. The strict `generate` path is
# exercised by `enumerate.py` below, which always runs the check in generate mode
# and refuses to write a manifest if it cannot run.
step "red lines clear, and every tracked file was actually read" \
    python check_redlines.py --mode verify

# Non-zero if any tracked file lands in class `?`/needs_human, because the
# manifest asserts a licence class for every tracked file and cannot assert one
# for a file it could not read.
step "every tracked file is classified" python enumerate.py --dry-run --mode verify

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
