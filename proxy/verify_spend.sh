#!/usr/bin/env bash
# The spend gate's green light. Offline: no network, no upstream, no money.
#
#     cd proxy && bash verify_spend.sh
#
# Exit 0 means the gate holds under real multi-process contention, refuses on
# every failure mode it claims to, is on the egress path rather than beside it,
# and has no switch that turns it off. It does NOT mean the pool is under its
# ceiling -- run `python -m proxy.spend_gate` for that.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$HERE")"
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

step "the gate's own suite (global sums, fail-closed, bypass attempts)" \
    python -m pytest tests/test_spend_gate.py -q

step "multi-process fuzz: real interpreters, one pool file" \
    python -m pytest tests/test_spend_gate_concurrency.py -q

step "the bypasses an adversarial pass demonstrated, kept as tests" \
    python -m pytest tests/test_spend_gate_egress.py -q

step "the whole proxy suite, with the gate on the egress path" \
    python -m pytest -q

# A grep is a weak check, so it is not the only one -- `test_spend_gate.py`
# asserts the same thing from inside. It is here because this is the file
# somebody reads when they want to know whether the gate can be turned off,
# and the answer should be visible without running anything.
echo
echo "== no switch that turns the gate off"
# Matches code, not prose: the module's own docstring says the words "no
# `enabled` flag", and a check that trips on its own documentation is a check
# nobody will keep.
if grep -nE "os\.environ|getenv\(|SPEND_GATE_DISABLE|enabled *=|if +not +enabled|disabled *=" spend_gate.py; then
    echo "-- FAILED: the gate has acquired an off switch"
    fail=1
else
    echo "-- ok (no environment variable, no enabled flag)"
fi

echo
echo "== every socket in the package goes through a permit"
# `import socket` alone is not egress -- spend_gate.py uses it for
# gethostname(). What matters is a module opening its own connection, and
# forward.py is the one place allowed to, because it is the one place that
# demands a permit first.
# Three exemptions, each for a stated reason rather than to make the check
# pass:
#   forward.py    the one place allowed to open an upstream socket, because it
#                 is the one place that demands a permit before it does.
#   mock/         the mock arm is a *client of the proxy*: its `_post` targets
#                 the proxy's own base_url on 127.0.0.1, so its traffic is
#                 gated downstream by env_proxy._forward like any arm's.
#   replay.py     same shape -- it stands up an EnvProxy and posts to it, so a
#                 replay costs pool actions exactly as the original run did.
if grep -nE "socket\.socket|socket\.create_connection|http\.client\.|requests\.(get|post|put|request)\(|urlopen" \
        --include=*.py -r . \
        | grep -v "/tests/" | grep -v "forward\.py" \
        | grep -v "/mock/" | grep -v "replay\.py"; then
    echo "-- FAILED: a module reaches the network without going through forward()"
    fail=1
else
    echo "-- ok (urllib, via forward(), which requires permit=)"
fi

echo
echo "== the shared pool policy is readable and has a ceiling"
if (cd "$REPO" && python -c "
from proxy.spend_gate import SpendPolicy
p = SpendPolicy.load()
print('  pool %s   %.2f USD / %d actions   undeclared run gets %.2f / %d'
      % (p.pool, p.usd_ceiling, p.action_ceiling,
         p.default_run_caps['usd'], p.default_run_caps['actions']))"); then
    echo "-- ok"
else
    echo "-- FAILED"
    fail=1
fi

echo
echo "== baseline-arms campaign attribution"
if python "$REPO/baseline-arms/harness/ledger.py"; then
    echo "-- ok (a report, not an assurance: undecidable lines stay undecidable)"
else
    echo "-- FAILED"
    fail=1
fi

echo
if [ "$fail" -eq 0 ]; then
    echo "VERIFY: green"
else
    echo "VERIFY: RED"
fi
exit "$fail"
