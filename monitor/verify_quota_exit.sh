#!/usr/bin/env bash
# S1's green light: the circuit breaker has an exit, the exit is automatic, and
# the exit does not spend more than it is allowed to.
#
#     bash monitor/verify_quota_exit.sh
#
# Offline by construction. `claude` is never invoked: the one function that
# would call it is stubbed everywhere below, and the deadline exit is asserted
# to work with `subprocess.run` rigged to explode, so a regression that made it
# reach for the network fails loudly instead of quietly costing money.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$HERE")"
cd "$REPO"
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

step "the state-machine suite: hold -> reopen -> auto-exit, and the throttle" \
    python -m pytest monitor/tests -q

step "the negative controls (a suite whose failures nobody has seen is a comment)" \
    bash -c '
set -e
cp monitor/quota.py "$TMPDIR_Q/quota.bak" 2>/dev/null || cp monitor/quota.py /tmp/quota.bak
BAK=${TMPDIR_Q:-/tmp}/quota.bak
restore() { cp "$BAK" monitor/quota.py; }
trap restore EXIT

expect_fail() {
    if python -m pytest monitor/tests -q >/dev/null 2>&1; then
        echo "   NOT DETECTED: $1"
        restore; exit 1
    fi
    echo "   detected: $1"
    restore
}

python - <<PY
s = open("monitor/quota.py", encoding="utf-8").read()
open("monitor/quota.py", "w", encoding="utf-8", newline="\n").write(
    s.replace("MIN_PING_INTERVAL_MIN = 20", "MIN_PING_INTERVAL_MIN = 0"))
PY
expect_fail "throttle removed -> unbounded pings during an outage"

python - <<PY
s = open("monitor/quota.py", encoding="utf-8").read()
open("monitor/quota.py", "w", encoding="utf-8", newline="\n").write(
    s.replace("        if due and now >= due:", "        if False:"))
PY
expect_fail "deadline exit removed -> the one-way latch is back"

python - <<PY
s = open("monitor/quota.py", encoding="utf-8").read()
open("monitor/quota.py", "w", encoding="utf-8", newline="\n").write(
    s.replace(chr(32)*4 + "st[\"last_ping_at\"] = now_utc()",
              chr(32)*4 + "st[\"last_ping_at\"] = now_utc() if ok else st.get(\"last_ping_at\")"))
PY
expect_fail "only successes recorded -> no throttle while the window is shut"
'

step "the CLI contract reflex depends on: --if-due exits 3 and spends nothing" \
    python - <<'PY'
import os, sys, tempfile
sys.path.insert(0, "monitor")
import quota

with tempfile.TemporaryDirectory() as tmp:
    quota.STATE = os.path.join(tmp, "quota_state.json")
    quota.save_state({"mode": "hold", "requeue": [],
                      "last_ping_at": quota.now_utc(),
                      "last_ping_result": "CLOSED"})

    def explode(*a, **k):
        raise AssertionError("a throttled ping must not reach the provider")
    quota.subprocess.run = explode

    code = quota.ping(if_due=True)
    assert code == 3, code
    print("ping --if-due -> exit 3, no call made")
PY

step "reflex still parses and asks for the throttled spelling" \
    python - <<'PY'
import ast, io
src = open("monitor/reflex.py", encoding="utf-8").read()
ast.parse(src)
assert '"ping", "--if-due"' in src, "reflex must use the throttled ping"
assert '"ping"]' not in src, "an unthrottled ping is left in reflex"
assert "quota:RESUMED(auto)" in src and "quota:probe-throttled" in src, \
    "reflex must distinguish an automatic resume from a throttled probe in its log"
print("reflex: throttled probe, both outcomes logged")
PY

echo
if [ "$fail" -eq 0 ]; then
    echo "VERIFY OK -- the hold ends by itself, and pays at most one call per 20 min"
else
    echo "VERIFY FAILED"
fi
exit "$fail"
