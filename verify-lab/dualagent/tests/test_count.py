"""The census, and the ways a census of this shape lies.

Three kinds of test, and the second and third are the acceptance:

1. **Shape** -- the counters agree with a synthetic ledger whose answer is
   known by construction.
2. **Negative control** -- each rule the census claims is planted as a
   violation and the census must move. A counter that reports the same number
   whether or not the thing it counts is present is measuring nothing, which
   is exactly the defect S32 was opened about: "65 401s" was true and
   uninformative until a denominator stood beside it.
3. **The red line** -- a synthetic ledger carrying a credential-shaped value in
   a header field, and the assertion that nothing the census returns contains
   it. S32 forbids a real credential entering any file; this pins that the
   code could not carry one there even if handed it.

The live figures are asserted against the repository too, but as *lower
bounds with a recorded snapshot*, not equalities: `theoria-arm/runs/` is
append-only history, and a test that fails when a new run lands would be a
test that trains its reader to delete it.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DUALAGENT = os.path.dirname(HERE)
sys.path.insert(0, DUALAGENT)

import count  # noqa: E402


# --------------------------------------------------------------------------
# Synthetic ledgers
# --------------------------------------------------------------------------

def _write(path, records):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True) + "\n")


def _leg(event, status=200, forwarded=True):
    return {"event": event, "http": {"status": status, "forwarded": forwarded}}


def _make_run(root, name, upstream, legs, extras=()):
    os.makedirs(os.path.join(root, name), exist_ok=True)
    records = [{"event": "run_start", "env_upstream": upstream}]
    records.extend(legs)
    records.extend(extras)
    _write(os.path.join(root, name, "ledger.jsonl"), records)


# --------------------------------------------------------------------------
# 1. Shape
# --------------------------------------------------------------------------

def test_counts_only_proxy_legs(tmp_path):
    """Records the arm's own process wrote are not requests the proxy carried.

    `run_start`, `run_end`, `model_call` and `incident` all live in the same
    file as `env_step`. Counting lines instead of legs would have made the
    environment proxy's denominator 3568 instead of 1009 -- and the inflated
    number is the one that flatters the claim.
    """
    root = str(tmp_path)
    _make_run(root, "live", "https://example.invalid",
              [_leg("env_meta"), _leg("env_step"), _leg("env_step")],
              extras=[{"event": "incident", "kind": "bypass_attempt"},
                      {"event": "model_call", "http": {"status": 200}},
                      {"event": "run_end"}])
    out = count.env_proxy_traffic(root)
    assert out["requests_total"] == 3
    assert out["runs"][0]["env_meta"] == 1
    assert out["runs"][0]["env_step"] == 2


def test_live_and_fixture_are_separated(tmp_path):
    """A fixture upstream exercises the code path; it does not validate it."""
    root = str(tmp_path)
    _make_run(root, "live", "https://example.invalid", [_leg("env_step")] * 5)
    _make_run(root, "fixture", "http://127.0.0.1:5000", [_leg("env_step")] * 7)
    out = count.env_proxy_traffic(root)
    assert out["requests_total"] == 12
    assert out["requests_live_upstream"] == 5
    assert out["requests_fixture_upstream"] == 7
    assert out["live_runs"] == 1 and out["fixture_runs"] == 1


def test_a_4xx_is_still_a_request_the_proxy_handled(tmp_path):
    """726 of the live legs came back 400, and they still count.

    The proxy forwarded them, the upstream answered them, and the credential
    was applied -- a rejected *game action* is not a rejected *request*.
    Dropping them would understate the environment proxy's denominator by
    three quarters and would be the mirror of the mistake in test 1.
    """
    root = str(tmp_path)
    _make_run(root, "live", "https://example.invalid",
              [_leg("env_step", 200), _leg("env_step", 400),
               _leg("env_step", 404)])
    out = count.env_proxy_traffic(root)
    assert out["requests_live_upstream"] == 3
    assert out["live_status_counts"] == {"200": 1, "400": 1, "404": 1}


def test_model_proxy_success_is_2xx_only(tmp_path):
    path = str(tmp_path / "m.jsonl")
    _write(path, [
        {"event": "incident", "kind": "bypass_attempt", "header": "authorization"},
        {"event": "model_call", "http": {"status": 401}},
        {"event": "model_call", "http": {"status": 401}},
        {"event": "model_call", "http": {"status": 200}},
    ])
    out = count.model_proxy_traffic(path)
    assert out["records_total"] == 4
    assert out["model_calls"] == 3
    assert out["refused_401"] == 2
    assert out["succeeded"] == 1
    assert out["bypass_attempts"] == 1
    assert out["bypass_headers"] == ["authorization"]


# --------------------------------------------------------------------------
# 2. Negative controls -- plant the violation, require the census to move
# --------------------------------------------------------------------------

def test_negative_control_a_succeeded_model_call_would_show(tmp_path):
    """The verdict rests on `succeeded == 0`. Prove that field can be non-zero.

    Without this the honest reading and the broken reading are
    indistinguishable: a counter hard-wired to zero would produce the same
    (b) verdict from a proxy that was working perfectly.
    """
    path = str(tmp_path / "m.jsonl")
    _write(path, [{"event": "model_call", "http": {"status": 401}}])
    assert count.model_proxy_traffic(path)["succeeded"] == 0
    _write(path, [{"event": "model_call", "http": {"status": 200}}])
    assert count.model_proxy_traffic(path)["succeeded"] == 1


def test_negative_control_zero_live_traffic_would_show(tmp_path):
    """The (a)-vs-(b) split for the environment proxy rests on 924 > 0.

    Plant a repository in which every run used a fixture and require
    `requests_live_upstream == 0`, so the field is known to be capable of the
    answer that would have refuted the verdict.
    """
    root = str(tmp_path)
    _make_run(root, "f1", "http://127.0.0.1:5000", [_leg("env_step")] * 9)
    out = count.env_proxy_traffic(root)
    assert out["requests_total"] == 9
    assert out["requests_live_upstream"] == 0


def test_negative_control_an_empty_tree_is_zero_not_an_exception(tmp_path):
    """A census that crashes on an empty tree gets deleted from the gate."""
    out = count.env_proxy_traffic(str(tmp_path / "nope"))
    assert out["requests_total"] == 0 and out["ledgers"] == 0
    assert count.model_proxy_traffic(str(tmp_path / "nope.jsonl"))["records_total"] == 0


def test_negative_control_fixture_ledger_absence_is_declared(tmp_path):
    """`present: false` must not read as `succeeded: 0` on the real proxy.

    `proxy/var/` is gitignored, so absence is the *normal* state of a fresh
    clone. The flag is what stops a later reader turning "not on this
    checkout" into "the model proxy never completed a request".
    """
    absent = count.model_proxy_fixture_traffic(str(tmp_path / "nope.jsonl"))
    assert absent["present"] is False and absent["model_calls"] == 0
    path = str(tmp_path / "v.jsonl")
    _write(path, [{"event": "model_call", "arm": "mock_arm",
                   "model": "mock-model-1", "http": {"status": 200}}])
    present = count.model_proxy_fixture_traffic(path)
    assert present["present"] is True and present["succeeded"] == 1


# --------------------------------------------------------------------------
# 3. The red line
# --------------------------------------------------------------------------

def test_no_header_value_can_reach_the_output(tmp_path):
    """Counts and header *names*; never a header value.

    The model-proxy evidence exists because a client presented a credential of
    its own, so this file is the one place in verify-lab where a careless field
    read would put a secret in a deliverable. Handed a record with a
    credential-shaped value in every plausible slot, nothing the census returns
    may contain it.
    """
    sentinel = "sk-ant-NOTAREALKEY-000000000000"
    path = str(tmp_path / "m.jsonl")
    _write(path, [{"event": "incident", "kind": "bypass_attempt",
                   "header": "authorization", "value": sentinel,
                   "detail": "client sent " + sentinel,
                   "request": {"headers": {"authorization": sentinel}}},
                  {"event": "model_call", "http": {"status": 401},
                   "request": {"headers": {"x-api-key": sentinel}}}])
    out = count.model_proxy_traffic(path)
    assert sentinel not in json.dumps(out)
    assert out["bypass_headers"] == ["authorization"]


# --------------------------------------------------------------------------
# The repository as it stands
# --------------------------------------------------------------------------

#: The 2026-07-31 census. Lower bounds, because `theoria-arm/runs/` is
#: append-only: a later run may raise these and must not turn this file red.
SNAPSHOT = {"env_live": 924, "env_total": 1009,
            "model_records": 131, "model_calls": 65, "model_bypass": 66}


def test_the_repository_still_supports_the_verdict():
    env = count.env_proxy_traffic()
    model = count.model_proxy_traffic()
    assert env["requests_live_upstream"] >= SNAPSHOT["env_live"]
    assert env["requests_total"] >= SNAPSHOT["env_total"]
    # The model-proxy evidence is a closed archive, not a growing log, so this
    # one is an equality: a change to it is a change to the finding.
    assert model["records_total"] == SNAPSHOT["model_records"]
    assert model["model_calls"] == SNAPSHOT["model_calls"]
    assert model["bypass_attempts"] == SNAPSHOT["model_bypass"]
    assert model["refused_401"] == model["model_calls"]
    assert model["succeeded"] == 0


def test_the_named_exclusions_really_carry_no_proxy_leg():
    """The exclusions are checkable, not asserted.

    `baseline-arms/ledger.jsonl` and `arc-recon`'s recon ledger are the two
    biggest request logs in the repository, and folding either into the
    environment proxy's denominator would inflate it past 2900. They are left
    out because no record in them has a proxy `http` leg -- which is a fact
    about the files, so it is measured here rather than trusted.
    """
    for row in count.excluded_ledgers():
        assert row["proxy_legs"] == 0, row["path"]
