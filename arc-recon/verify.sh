#!/usr/bin/env bash
# arc-recon's green light. Offline by construction: no API call, no network, no
# action spent. Anything here that needs the live API is a bug in this script.
#
#     cd arc-recon && bash verify.sh
#
# Exit 0 means: the offline suite passes, the shipped canary schedule is
# internally consistent with the shipped canary spec, the pile cut still hashes
# to its published value, and no sealed game appears in any request we have ever
# made. It does NOT mean the environment has not drifted -- only a replay can
# say that, and only `canary_schedule.py run` buys one.
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

# `redact_ledger.py` with no args scans for the INC-008 shape only -- one field,
# `set_cookie`, because that is the field the incident was about. Kept: it is the
# remediation's own before/after check and it should keep working.
step "no cookie value reached the ledger (the INC-008 field)" python redact_ledger.py

# The general form, and the one that does not depend on knowing which incident
# happened. Every ledger this repo can see, every credential shape, whoever wrote
# the line -- see tools/ledger_invariants.py on why this is a check on the file
# rather than a rule inside a writer.
step "ledger invariants hold on the artefacts themselves" \
    python tools/ledger_invariants.py --all

echo
if [ "$fail" -eq 0 ]; then
    echo "VERIFY: green"
else
    echo "VERIFY: RED"
fi
exit "$fail"
