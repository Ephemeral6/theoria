#!/usr/bin/env bash
# S9's green light: the shared contract is additive-safe, pinned, and diffable.
# Offline: no network, no upstream, no money.
#
#     cd proxy && bash verify_contract.sh
#
# Exit 0 means a field the format does not list is kept rather than refused, the
# five P-8 fields are canonical, what the format *forbids* is still refused, and
# `canon.describe()` matches its pin so that a change which narrows the contract
# cannot arrive on an importing track unannounced.
#
# It does NOT mean an announcement was made. A test cannot read PARTNER_SYNC and
# judge a paragraph; see CONTRACT_CHANGES.md §4.
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

step "the canon guard: unknown fields kept and warned, banned spellings refused" \
    python -m pytest proxy/tests/test_canon.py -q

step "the contract pin and its direction classifier" \
    python -m pytest proxy/tests/test_contract_changes.py -q

step "canon.describe() still matches proxy/canon_contract.json" \
    python -m proxy.tools.contract

step "the fingerprint an importing track pins is printable" \
    python -m proxy.tools.contract --fingerprint

step "the record that was refused after the provider had been paid is accepted" \
    python - <<'PY'
# INC-TA-006 reduced to its one line. The field set is copied from
# theoria-arm/harness/modelcall.py's ledger write as it stands on master;
# written out here rather than imported, because proxy/ must not depend on an
# arm.
#
# Two honest caveats. (1) The arm has an in-flight fix that works *around* the
# closure by nesting the five fields inside `request`; C-001 makes that
# unnecessary, and until the arm un-nests them, `beat` has two depths in live
# ledgers and `armtools/archive.py` reads both -- which is a reader branch, the
# exact cost the closure was invented to avoid. The PARTNER_SYNC contract-notice
# says the top-level spelling is canonical again. (2) So this step asserts the
# writer accepts the record, not that any arm currently sends it.
import tempfile, os, warnings
from proxy.ledger import Ledger, RunLedger

with tempfile.TemporaryDirectory() as tmp:
    run = RunLedger(Ledger(os.path.join(tmp, "l.jsonl")), "r1", "theoria",
                    game_id="sk48-d8078629")
    with warnings.catch_warnings():
        warnings.simplefilter("error")     # a warning here means a field slipped
        record = run.model_call(
            "anthropic", "claude-opus-5",
            request={"transport": "claude-code-cli", "model": "claude-opus-5",
                     "max_turns": 2, "prompt": "...", "beat": "theorize",
                     "label": ""},
            response={"subtype": "success"},
            usage={"input_tokens": 20000},
            pricing_ref=None, step_idx=0,
            http={"method": "CLI", "path": "claude -p --output-format json",
                  "status": 200, "elapsed_ms": 1, "attempts": 1,
                  "forwarded": False, "stream": False},
            beat="theorize", label="", transport="claude-code-cli",
            proxied=False,
            proxy_gap="model_proxy strips Authorization and no ANTHROPIC_API_KEY exists",
        )
    assert record["beat"] == "theorize", record
    assert run.unknown_fields == {}, run.unknown_fields
    print("accepted: beat=%s proxied=%s" % (record["beat"], record["proxied"]))
PY

step "under -W error the warning still does not eat the record" \
    python -W error - <<'PY'
# The trap this whole change walks into if nobody looks: a warning is an
# exception whenever the ambient filter says `error`. Raised inside the writer
# that would be INC-TA-006 rebuilt out of the warning meant to replace it --
# same paid call, same lost record. Run in a real subprocess with a real
# `-W error`, because a `simplefilter` inside pytest is a weaker claim.
import tempfile, os
from proxy.ledger import Ledger, RunLedger

with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "l.jsonl")
    run = RunLedger(Ledger(path), "r1", "theoria", game_id="sk48-d8078629")
    record = run.model_call("anthropic", "claude-opus-5", usage={},
                            a_field_from_2027="hello")
    assert record["a_field_from_2027"] == "hello"
    with open(path, encoding="utf-8") as fh:
        assert len(fh.readlines()) == 1
    assert run.unknown_fields == {"model_call.a_field_from_2027": 1}, run.unknown_fields
    print("record survived -W error; tally: %s" % run.unknown_fields)
PY

step "the frozen scorer notices when its imports move, not just its source" \
    python - <<'PY'
# S-12 delegates to tools/validate_ledger.py, which consults canon.py. Freezing
# only arc_v1.py froze the file and not the rule.
import copy, json, os, shutil, tempfile
from proxy import scoring
from proxy.scoring import arc_v1

scoring.verify_frozen()
frozen = copy.deepcopy(scoring.load_frozen())
assert set(frozen["scorers"]["arc_v1"]["depends_on"]) == {
    "tools/validate_ledger.py", "canon.py"}
frozen["scorers"]["arc_v1"]["depends_on"]["canon.py"] = "sha256:" + "0" * 64
with tempfile.TemporaryDirectory() as tmp:
    p = os.path.join(tmp, "frozen.json")
    with open(p, "w", encoding="utf-8", newline="") as fh:
        json.dump(frozen, fh)
    shutil.copy(os.path.join(os.path.dirname(arc_v1.__file__), "arc_v1.py"),
                os.path.join(tmp, "arc_v1.py"))
    try:
        scoring.verify_frozen(frozen_path=p)
        raise SystemExit("FAIL: a moved dependency did not trip the freeze")
    except scoring.ScorerDriftError as exc:
        assert "source is unchanged" in str(exc), exc
        print("tripped: %s" % str(exc)[:70])
PY

step "a stream carrying a field this reader has never heard of still validates" \
    python - <<'PY'
from proxy.tools.validate_ledger import validate_records

record = {"v": "1.0", "event": "model_call", "seq": 1, "arm": "theoria",
          "ts": "2026-07-28T00:00:00.000Z", "run_id": "r", "call_idx": 0,
          "provider": "anthropic", "model": "m", "request": {}, "response": {},
          "usage": {}, "http": {"status": 200},
          "a_field_from_2027": "hello"}
notices = []
problems = validate_records([record], notices=notices)
assert problems == [], problems
assert notices and notices[0]["fields"] == ["a_field_from_2027"], notices
print("verdict unaffected; 1 notice: %s" % notices[0]["fields"])
PY

step "the whole proxy suite" \
    python -m pytest proxy -q

echo
if [ "$fail" -eq 0 ]; then
    echo "VERIFY OK -- contract additive-safe, pinned, and diffable"
else
    echo "VERIFY FAILED"
fi
exit "$fail"
