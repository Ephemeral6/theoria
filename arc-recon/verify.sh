#!/usr/bin/env bash
# arc-recon's green light. Offline by construction: no API call, no network, no
# action spent. Anything here that needs the live API is a bug in this script.
#
#     cd arc-recon && bash verify.sh
#
# Exit 0 means: the offline suite passes, the shipped canary schedule is
# internally consistent with the shipped canary spec, the pile cut still hashes
# to its published value, no sealed game appears in any request we have ever
# made, and the planned campaign fits inside the documented rate limit. It does
# NOT mean the environment has not drifted -- only a replay can say that, and
# only `canary_schedule.py run` buys one.
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

step "offline test suite" python -m pytest -q

step "canary spec and schedule agree" python canary_schedule.py status

# `run --dry-run` plans and gates without spending: it exercises the freeze
# check, the profile planner and the sealed-pile guard on the real shipped
# files, which `status` alone does not.
step "daily sweep plans within its budget" \
    python canary_schedule.py run --dry-run --profile quick --force
step "weekly sweep plans within its budget" \
    python canary_schedule.py run --dry-run --profile full --force

# Not a hard failure: exit 1 here means campaigns are frozen, which is the
# instrument working. It is reported, loudly, and left to a human.
echo
echo "== campaign freeze gate"
if python canary.py check-freeze; then
    echo "-- ok"
else
    echo "-- CAMPAIGNS ARE FROZEN. This is not a verify failure; it is the"
    echo "   canary having found drift. Adjudicate before spending anything."
fi

step "pile cut, claim set and the sealed-contact audit" \
    python contamination.py --json

# Phase 1's rate obligation (Theoria.md:299), in the unit that exists. Runs
# with --measure so a declared input that has drifted from the data file it
# was taken from is a verify failure, not a stale number nobody rechecks.
step "campaign rate budget fits inside the documented limit" \
    python rate_budget.py --measure

step "no credential or cookie value reached the ledger" python redact_ledger.py

echo
if [ "$fail" -eq 0 ]; then
    echo "VERIFY: green"
else
    echo "VERIFY: RED"
fi
exit "$fail"
