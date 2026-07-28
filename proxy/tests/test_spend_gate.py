"""The shared spend gate: does it actually hold?

Three properties, and each one is a section here. The tests that matter most are
the ones asserting the gate goes **red** -- a gate that has never been seen to
refuse is not evidence that anything was checked. INC-BA-003 is precisely the
case where two correct gates both said yes.

Every test runs on a temp pool, injected as a `SpendPolicy` object. There is
deliberately no environment variable that relocates the real ledger: a pool
everyone can point somewhere else is a pool of one.

    cd proxy && python -m pytest tests/test_spend_gate.py
"""

import json
import os
import time

import pytest

from proxy.spend_gate import (GATE_VERSION, NoReservation, Reservation,
                              SpendGate, SpendGateError, SpendGateTripped,
                              SpendGateUnavailable, SpendPermit, SpendPolicy)


# -- fixtures ---------------------------------------------------------------

def policy(tmp_path, *, usd=100.0, actions=1000, ttl=3600.0, **extra):
    spec = {"v": "1.0", "pool": "test-pool", "usd_ceiling": usd,
            "action_ceiling": actions,
            "ledger": str(tmp_path / "spend.jsonl"),
            "default_ttl_seconds": ttl, "lock_timeout_seconds": 5.0,
            "default_run_caps": {"usd": 1.0, "actions": 10}}
    spec.update(extra)
    return SpendPolicy(spec, source=None)


@pytest.fixture
def gate(tmp_path):
    return SpendGate(policy(tmp_path))


def lines(gate):
    with open(gate.ledger_path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


# -- 1. global: the sum is over the pool, not over this process -------------

def test_the_check_reads_another_campaigns_spend(tmp_path):
    """The one sentence the module exists for."""
    first = SpendGate(policy(tmp_path, usd=10.0))
    second = SpendGate(policy(tmp_path, usd=10.0))       # a different process's gate

    a = first.reserve("campaign-a", usd_cap=5.0, action_cap=10)
    first.record(a, usd=5.0, actions=1)

    b = second.reserve("campaign-b", usd_cap=5.0, action_cap=10)
    with pytest.raises(SpendGateTripped) as exc:
        second.check(b, usd=5.01)
    assert exc.value.rule == "POOL_USD_CEILING"
    # ...and the refusal names the other campaign, so the reader can see whose
    # money it was. This is the diagnostic INC-BA-003 could not produce.
    assert "campaign-a" in str(exc.value)


def test_a_second_campaign_cannot_reserve_headroom_the_first_is_holding(tmp_path):
    """The middle term: held, not spent. This is what INC-BA-003 lacked."""
    first = SpendGate(policy(tmp_path, usd=100.0))
    second = SpendGate(policy(tmp_path, usd=100.0))
    first.reserve("campaign-a", usd_cap=60.0, action_cap=10)

    with pytest.raises(SpendGateTripped) as exc:
        second.reserve("campaign-b", usd_cap=60.0, action_cap=10)
    assert exc.value.rule == "POOL_USD_CEILING"
    assert "held" in str(exc.value)


def test_both_campaigns_fit_when_they_actually_fit(tmp_path):
    """The negative control for the test above: it must not refuse everything."""
    first = SpendGate(policy(tmp_path, usd=100.0))
    second = SpendGate(policy(tmp_path, usd=100.0))
    first.reserve("campaign-a", usd_cap=50.0, action_cap=10)
    second.reserve("campaign-b", usd_cap=50.0, action_cap=10)     # no raise


def test_the_action_ceiling_is_global_too(tmp_path):
    first = SpendGate(policy(tmp_path, actions=10))
    second = SpendGate(policy(tmp_path, actions=10))
    a = first.reserve("a", usd_cap=1.0, action_cap=8)
    first.record(a, actions=8)
    b = second.reserve("b", usd_cap=1.0, action_cap=2)
    with pytest.raises(SpendGateTripped) as exc:
        second.check(b, actions=3)
    assert exc.value.rule == "POOL_ACTION_CEILING"


def test_releasing_gives_the_unspent_remainder_back(tmp_path):
    first = SpendGate(policy(tmp_path, usd=100.0))
    second = SpendGate(policy(tmp_path, usd=100.0))
    a = first.reserve("a", usd_cap=90.0, action_cap=10)
    with pytest.raises(SpendGateTripped):
        second.reserve("b", usd_cap=20.0, action_cap=10)
    first.release(a)
    second.reserve("b", usd_cap=20.0, action_cap=10)     # now it fits


def test_release_returns_the_hold_but_never_the_spend(tmp_path):
    g = SpendGate(policy(tmp_path, usd=10.0))
    a = g.reserve("a", usd_cap=9.0, action_cap=10)
    g.record(a, usd=9.0, actions=1)
    g.release(a)
    assert g.totals().usd == 9.0                          # the spend stays
    assert g.totals().held_usd == 0.0                     # the hold is gone
    b = g.reserve("b", usd_cap=1.0, action_cap=1)
    with pytest.raises(SpendGateTripped):
        g.check(b, usd=1.01)


# -- 2. fail-closed: every failure refuses, none of them shrug --------------

def test_a_missing_policy_refuses_rather_than_defaulting(tmp_path):
    with pytest.raises(SpendGateUnavailable) as exc:
        SpendPolicy.load(str(tmp_path / "nope.json"))
    assert "not" in str(exc.value).lower()


def test_an_unparseable_policy_refuses(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(SpendGateUnavailable):
        SpendPolicy.load(str(path))


def test_a_policy_without_a_ceiling_is_not_a_gate(tmp_path):
    with pytest.raises(SpendGateUnavailable):
        SpendPolicy({"pool": "p", "ledger": "x.jsonl",
                     "default_run_caps": {"usd": 1.0, "actions": 1}},
                    source=None)


def test_a_zero_ceiling_is_refused_rather_than_read_as_unlimited(tmp_path):
    with pytest.raises(SpendGateUnavailable):
        policy(tmp_path, usd=0.0)


def test_a_corrupt_ledger_line_fails_the_whole_pool(tmp_path):
    """Deliberately harsher than proxy/ledger.read_ledger, and for a reason:
    there a strict reader turns one bad append into a denial of service on an
    audit trail (RED-44). Here the file is money -- a line nobody can read is
    spend nobody can count."""
    g = SpendGate(policy(tmp_path))
    a = g.reserve("a", usd_cap=1.0, action_cap=1)
    with open(g.ledger_path, "a", encoding="utf-8") as fh:
        fh.write("this is not json\n")
    with pytest.raises(SpendGateUnavailable) as exc:
        g.check(a, usd=0.01)
    assert "cannot be read" in str(exc.value) or "not JSON" in str(exc.value)


def test_a_ledger_from_a_future_gate_version_refuses(tmp_path):
    g = SpendGate(policy(tmp_path))
    a = g.reserve("a", usd_cap=1.0, action_cap=1)
    with open(g.ledger_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"v": "9.9", "kind": "spend", "usd": 1.0}) + "\n")
    with pytest.raises(SpendGateUnavailable):
        g.check(a, usd=0.01)


def test_spending_without_a_reservation_is_refused(gate):
    with pytest.raises(NoReservation):
        gate.check(None, usd=0.01)


def test_a_handle_whose_claim_is_not_on_disk_is_not_a_claim(gate):
    forged = Reservation("res-deadbeef", "a", 100.0, 100, time.time() + 60, {})
    with pytest.raises(NoReservation):
        gate.check(forged, usd=0.01)


def test_a_released_reservation_cannot_spend_again(gate):
    a = gate.reserve("a", usd_cap=1.0, action_cap=1)
    gate.release(a)
    with pytest.raises(NoReservation):
        gate.check(a, usd=0.01)


def test_an_expired_lease_refuses_and_cannot_be_renewed(tmp_path):
    """An expired lease has already given its headroom back, and somebody else
    may already hold it. Renewing would leave two campaigns each believing they
    own the whole budget -- which is the decision INC-BA-003 actually was."""
    g = SpendGate(policy(tmp_path, ttl=0.05))
    a = g.reserve("a", usd_cap=1.0, action_cap=1)
    time.sleep(0.1)
    with pytest.raises(NoReservation) as exc:
        g.check(a, usd=0.01)
    assert "expired" in str(exc.value)
    with pytest.raises(NoReservation) as exc:
        g.renew(a, ttl_seconds=60)
    assert "re-let" in str(exc.value)
    g.reserve("a", usd_cap=1.0, action_cap=1)             # reserving again works


def test_a_live_lease_can_still_be_renewed(tmp_path):
    """The negative control: a long campaign heartbeats rather than
    re-reserving, and that must keep working."""
    g = SpendGate(policy(tmp_path, ttl=30.0))
    a = g.reserve("a", usd_cap=1.0, action_cap=1)
    g.renew(a, ttl_seconds=600)
    g.check(a, usd=0.01)


def test_an_expired_lease_that_was_renewed_cannot_double_the_pool(tmp_path):
    """The exploit the check above closes, stated as its outcome: A's lease
    lapses, B takes the freed headroom, and A renews. Both now hold the pool."""
    g = SpendGate(policy(tmp_path, usd=10.0, ttl=0.05))
    a = g.reserve("a", usd_cap=10.0, action_cap=10)
    time.sleep(0.1)
    b = SpendGate(policy(tmp_path, usd=10.0)).reserve("b", usd_cap=10.0,
                                                      action_cap=10)
    with pytest.raises(NoReservation):
        g.renew(a, ttl_seconds=600)
    assert g.totals().held_usd == 10.0                    # B's claim, once
    assert g.totals().free_usd == 0.0


def test_a_released_reservation_cannot_be_renewed(gate):
    """Resurrecting a released claim would take back headroom somebody else may
    already hold."""
    a = gate.reserve("a", usd_cap=1.0, action_cap=1)
    gate.release(a)
    with pytest.raises(NoReservation):
        gate.renew(a)


def test_an_expired_lease_stops_holding_headroom(tmp_path):
    """A session that died mid-campaign must not hold the pool until a human
    notices -- but its spend keeps counting forever."""
    g = SpendGate(policy(tmp_path, usd=10.0, ttl=0.05))
    a = g.reserve("a", usd_cap=9.0, action_cap=10)
    g.record(a, usd=1.0, actions=1)
    time.sleep(0.1)
    totals = g.totals()
    assert totals.held_usd == 0.0
    assert totals.usd == 1.0
    g2 = SpendGate(policy(tmp_path, usd=10.0))
    g2.reserve("b", usd_cap=9.0, action_cap=10)           # the hold is released


def test_an_unwritable_ledger_directory_refuses(tmp_path):
    spec = {"v": "1.0", "pool": "p", "usd_ceiling": 1.0, "action_ceiling": 1,
            "default_run_caps": {"usd": 1.0, "actions": 1},
            "ledger": str(tmp_path / "afile" / "nested" / "l.jsonl")}
    (tmp_path / "afile").write_text("I am a file, not a directory",
                                    encoding="utf-8")
    with pytest.raises(SpendGateUnavailable):
        SpendGate(SpendPolicy(spec, source=None))


def test_an_unpriced_call_stops_the_pool_rather_than_undercounting(gate):
    """A dollar total that is only a lower bound is a number the gate must not
    pretend to have."""
    a = gate.reserve("a", usd_cap=10.0, action_cap=10)
    gate.record(a, usd=0.0, actions=1, unpriced=True)
    with pytest.raises(SpendGateTripped) as exc:
        gate.check(a, usd=0.01)
    assert exc.value.rule == "UNPRICED_SPEND"


def test_an_unnamed_campaign_is_refused(gate):
    """`ledger.jsonl` mixed two campaigns in one append-only file and no line
    could say which was which. An unnamed spend is that again."""
    with pytest.raises(SpendGateError):
        gate.reserve("", usd_cap=1.0, action_cap=1)


def test_negative_spend_is_refused(gate):
    a = gate.reserve("a", usd_cap=1.0, action_cap=1)
    with pytest.raises(SpendGateError):
        gate.record(a, usd=-1.0)


# -- 3. accounting: the record is a fact, the cap is a judgment --------------

def test_an_over_cap_spend_is_written_down_before_it_raises(gate):
    """A gate that refused to record an over-budget spend would be a gate that
    makes the pool look under budget."""
    a = gate.reserve("a", usd_cap=1.0, action_cap=10)
    with pytest.raises(SpendGateTripped):
        gate.record(a, usd=2.0, actions=1)
    assert gate.totals().usd == 2.0                       # the fact survived
    kinds = [r["kind"] for r in lines(gate)]
    assert kinds.count("spend") == 1 and "trip" in kinds  # and the breach is evidence


def test_the_trip_record_is_evidence_and_not_arithmetic(gate):
    a = gate.reserve("a", usd_cap=1.0, action_cap=10)
    with pytest.raises(SpendGateTripped):
        gate.record(a, usd=2.0, actions=1)
    assert gate.totals().usd == 2.0        # the trip line did not add anything


def test_check_prevents_where_record_accounts(gate):
    """Both are needed and they run in opposite orders: check refuses before
    the money moves, record writes after it has."""
    a = gate.reserve("a", usd_cap=1.0, action_cap=10)
    with pytest.raises(SpendGateTripped):
        gate.check(a, usd=2.0)
    assert gate.totals().usd == 0.0                       # nothing was recorded


def test_every_spend_carries_its_campaign(gate):
    a = gate.reserve("phase3-envelope", usd_cap=1.0, action_cap=10)
    gate.record(a, usd=0.5, actions=2)
    spends = [r for r in lines(gate) if r["kind"] == "spend"]
    assert [r["campaign"] for r in spends] == ["phase3-envelope"]


def test_totals_partition_by_campaign(tmp_path):
    g = SpendGate(policy(tmp_path))
    a = g.reserve("a", usd_cap=10.0, action_cap=10)
    b = g.reserve("b", usd_cap=10.0, action_cap=10)
    g.record(a, usd=1.0, actions=1)
    g.record(b, usd=2.0, actions=3)
    by = g.totals().by_campaign
    assert by["a"]["usd"] == 1.0 and by["b"]["actions"] == 3


def test_the_ledger_is_append_only_and_densely_sequenced(gate):
    a = gate.reserve("a", usd_cap=10.0, action_cap=10)
    for _ in range(3):
        gate.record(a, usd=0.1, actions=1)
    gate.release(a)
    seqs = [r["seq"] for r in lines(gate)]
    assert seqs == list(range(1, len(seqs) + 1))
    assert all(r["v"] == GATE_VERSION for r in lines(gate))


def test_the_reservation_cap_binds_even_when_the_pool_is_empty(gate):
    a = gate.reserve("a", usd_cap=0.5, action_cap=1)
    with pytest.raises(SpendGateTripped) as exc:
        gate.check(a, usd=0.6)
    assert exc.value.rule == "RESERVATION_USD_CAP"


def test_the_reservation_action_cap_binds_too(gate):
    a = gate.reserve("a", usd_cap=10.0, action_cap=2)
    with pytest.raises(SpendGateTripped) as exc:
        gate.check(a, actions=3)
    assert exc.value.rule == "RESERVATION_ACTION_CAP"


def test_a_run_can_record_which_pool_it_drew_on(gate):
    fp = gate.fingerprint()
    assert fp["pool"] == "test-pool" and fp["gate_version"] == GATE_VERSION
    assert len(fp["policy_sha256"]) == 64


# -- 4. bypass attempts: routing around the gate ----------------------------

def test_a_permit_cannot_be_constructed_without_the_mint(gate):
    """Egress takes an argument that can only come from a live reservation, so
    'forgot to check the gate' is a TypeError at the call site rather than a
    discovery in the next incident report."""
    a = gate.reserve("a", usd_cap=1.0, action_cap=1)
    with pytest.raises(SpendGateError):
        SpendPermit(gate, a, usd=0.1, actions=1)


def test_a_permit_from_the_mint_checks_against_the_live_pool(gate):
    a = gate.reserve("a", usd_cap=1.0, action_cap=1)
    permit = gate.permit(a, usd=0.5, actions=1)
    permit.check()                                        # fine
    gate.record(a, usd=0.9, actions=0)
    with pytest.raises(SpendGateTripped):
        permit.check()                # the pool moved under it; it says so now


def test_a_permit_needs_a_reservation(gate):
    with pytest.raises(NoReservation):
        gate.permit(None, usd=0.1)


def test_a_reservation_object_cannot_lie_about_its_cap(gate):
    """The ledger is the source of truth, not the handle in this process."""
    a = gate.reserve("a", usd_cap=1.0, action_cap=1)
    a.usd_cap = 10_000.0                                  # tamper with the handle
    with pytest.raises(SpendGateTripped) as exc:
        gate.check(a, usd=5.0)
    assert exc.value.rule == "RESERVATION_USD_CAP"


def test_deleting_the_ledger_does_not_reset_the_pool_silently(gate):
    """It resets the *total*, which is why the recovery is a human act. What
    must not happen is a live reservation surviving the reset and being spent
    against as though nothing had changed."""
    a = gate.reserve("a", usd_cap=1.0, action_cap=1)
    os.remove(gate.ledger_path)
    with pytest.raises(NoReservation):
        gate.check(a, usd=0.01)


def test_the_module_level_verbs_are_the_same_gate(tmp_path, monkeypatch):
    """`theoria-arm/armtools/spend_check.py` calls `module.reserve(...)`. That
    shape is provided, and it is not a looser one."""
    import proxy.spend_gate as sg
    g = SpendGate(policy(tmp_path))
    monkeypatch.setattr(sg, "_DEFAULT_GATE", g)
    r = sg.reserve("a", 1.0, 1)
    sg.record(r, usd=0.5, actions=1)
    assert sg.totals().usd == 0.5
    with pytest.raises(SpendGateTripped):
        sg.check(r, usd=0.6)
    sg.release(r)
    with pytest.raises(NoReservation):
        sg.check(r, usd=0.01)


def test_there_is_no_environment_variable_that_relocates_the_pool():
    """A pool everyone can point somewhere else is a pool of one."""
    source = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "spend_gate.py"), encoding="utf-8").read()
    assert "os.environ" not in source and "getenv" not in source


def test_there_is_no_disabled_or_optional_form():
    source = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "spend_gate.py"), encoding="utf-8").read()
    for smell in ('if not enabled', 'enabled=False', '"enabled"', "'enabled'"):
        assert smell not in source


# -- 5. blindness is scoped, and it is recoverable --------------------------

def test_an_unpriced_call_does_not_stop_action_only_spend(gate):
    """The defect wiring the gate to egress exposed: refusing *everything* on
    one unpriced model call stopped the environment proxy, which spends no
    dollars, for every session sharing the pool -- permanently, because the
    ledger is append-only."""
    a = gate.reserve("a", usd_cap=10.0, action_cap=10)
    gate.record(a, usd=0.0, actions=1, unpriced=True)
    gate.check(a, usd=0.0, actions=1)                     # actions still flow
    with pytest.raises(SpendGateTripped) as exc:
        gate.check(a, usd=0.01)                           # dollars do not
    assert exc.value.rule == "UNPRICED_SPEND"


def test_a_price_correction_clears_the_blindness_and_adds_the_money(gate):
    a = gate.reserve("a", usd_cap=10.0, action_cap=10)
    gate.record(a, usd=0.0, actions=1, unpriced=True)
    totals = gate.price_unpriced(
        a, usd=0.42, resolves=1,
        reason="model added to proxy/pricing/; recomputed from the usage block "
               "the proxy ledger recorded verbatim")
    assert totals.unpriced_calls == 0
    assert totals.usd == 0.42
    gate.check(a, usd=0.01)                               # dollars flow again


def test_a_correction_without_provenance_is_refused(gate):
    a = gate.reserve("a", usd_cap=10.0, action_cap=10)
    gate.record(a, usd=0.0, actions=1, unpriced=True)
    with pytest.raises(SpendGateError):
        gate.price_unpriced(a, usd=0.42, resolves=1, reason="   ")


def test_a_correction_cannot_resolve_more_blindness_than_exists(gate):
    """Otherwise the count could be driven negative and the gate re-opened on
    nothing."""
    a = gate.reserve("a", usd_cap=10.0, action_cap=10)
    gate.record(a, usd=0.0, actions=1, unpriced=True)
    with pytest.raises(SpendGateError):
        gate.price_unpriced(a, usd=0.1, resolves=5, reason="wishful")


def test_a_correction_is_appended_never_edited(gate):
    a = gate.reserve("a", usd_cap=10.0, action_cap=10)
    gate.record(a, usd=0.0, actions=1, unpriced=True)
    before = lines(gate)
    gate.price_unpriced(a, usd=0.42, resolves=1, reason="price table updated")
    after = lines(gate)
    assert after[:len(before)] == before                  # nothing rewritten
    assert after[-1]["kind"] == "price_correction"
    assert after[-1]["reason"]


# -- 6. egress: the gate is on the socket, not beside it --------------------

def test_forward_without_a_permit_is_a_type_error():
    """'Forgot to check the gate' has to be a failure at the call site, not a
    discovery in the next incident report."""
    from proxy import forward as fwd
    with pytest.raises(TypeError):
        fwd.forward("http://127.0.0.1:1/x", "GET", {})     # no permit=


def test_forward_checks_the_permit_before_it_opens_a_socket(gate, monkeypatch):
    from proxy import forward as fwd
    a = gate.reserve("a", usd_cap=0.0, action_cap=0)
    permit = gate.permit(a, usd=0.0, actions=1)

    opened = []
    monkeypatch.setattr(fwd._OPENER, "open",
                        lambda *args, **kw: opened.append(1))
    with pytest.raises(SpendGateTripped):
        fwd.forward("http://127.0.0.1:1/x", "GET", {}, permit=permit)
    assert opened == [], "a socket was opened despite the refusal"


def test_the_proxies_take_a_reservation_before_they_can_serve(tmp_path):
    """Both proxies sit behind the gate on the same footing as the sealed-pile
    guard: constructed if not handed in, never a flag, never absent."""
    from proxy.env_proxy import EnvProxyConfig
    g = SpendGate(policy(tmp_path))
    cfg = EnvProxyConfig(run_id="r-test", arm="mock_arm", api_key="k",
                         require_key=False, spend_gate=g,
                         ledger_path=str(tmp_path / "ledger.jsonl"))
    assert cfg.spend_reservation is not None
    assert cfg.campaign == "mock_arm:r-test"
    assert g.totals().live[0]["holder"]["undeclared"] is True


def test_a_declared_budget_is_not_replaced_by_the_default(tmp_path):
    from proxy.env_proxy import EnvProxyConfig
    g = SpendGate(policy(tmp_path))
    mine = g.reserve("phase3-envelope", usd_cap=7.0, action_cap=70)
    cfg = EnvProxyConfig(run_id="r-test", arm="mock_arm", api_key="k",
                         require_key=False, spend_gate=g,
                         spend_reservation=mine, campaign="phase3-envelope",
                         ledger_path=str(tmp_path / "ledger.jsonl"))
    assert cfg.spend_reservation is mine
    assert cfg.spend_reservation_owned is False
    assert len(g.totals().live) == 1                       # no second claim


# -- 7. requests that happened are charged, even when the call failed -------

def test_attempts_before_a_mid_retry_refusal_are_still_charged(gate, monkeypatch):
    """A permit refused on attempt 3 raises, so there is no Response to read
    `attempts` from -- but attempts 1 and 2 opened real sockets against the real
    rate limit. Counting only the successful calls is how a pool under-reports."""
    from proxy import forward as fwd
    a = gate.reserve("a", usd_cap=1.0, action_cap=2)
    permit = gate.permit(a, usd=0.0, actions=1)

    class _Boom:
        def __enter__(self): raise OSError("upstream is down")
        def __exit__(self, *exc): return False
    monkeypatch.setattr(fwd._OPENER, "open", lambda *a, **k: _Boom())

    # Charge one action per attempt as the proxy does, so the reservation's
    # 2-action cap is reached partway through a 5-attempt retry loop.
    def charging_check():
        gate.check(a, actions=1)
        gate.record(a, actions=1)
    monkeypatch.setattr(permit, "check", charging_check)

    with pytest.raises(SpendGateTripped):
        fwd.forward("http://127.0.0.1:1/x", "GET", {}, max_attempts=5,
                    backoff=0.0, permit=permit)
    assert gate.totals().actions == 2          # both real attempts are on disk
    assert permit.attempts_made == 2


def test_the_permit_counts_an_attempt_that_threw(gate, monkeypatch):
    from proxy import forward as fwd
    a = gate.reserve("a", usd_cap=1.0, action_cap=10)
    permit = gate.permit(a, usd=0.0, actions=1)

    class _Boom:
        def __enter__(self): raise OSError("connection reset")
        def __exit__(self, *exc): return False
    monkeypatch.setattr(fwd._OPENER, "open", lambda *a, **k: _Boom())

    fwd.forward("http://127.0.0.1:1/x", "GET", {}, max_attempts=3,
                backoff=0.0, permit=permit)
    assert permit.attempts_made == 3           # a transport failure still cost


def test_a_gate_refusal_reaches_the_ledger_as_an_incident(tmp_path):
    """A budget stop that only appears as a 500 to the arm is INC-BA-003 again,
    one layer down: nobody else can see it."""
    from proxy.ledger import INCIDENT_KINDS
    assert "spend_gate_refused" in INCIDENT_KINDS


# -- 8. what the adversarial pass broke, and what now holds -----------------

def test_the_pool_is_one_file_for_every_worktree_of_this_repo():
    """The most damaging finding of the adversarial pass, and the least
    visible: `proxy/var/` is gitignored and CLAUDE.md *instructs* every agent to
    work in `.worktrees/<id>/`, so a ledger path resolved against the importing
    checkout gave one pool per worktree -- 51 of them, each carrying the full
    ceiling, and byte-identical provenance so nobody could tell afterwards."""
    import proxy.spend_gate as sg
    assert os.path.isdir(os.path.join(sg.POOL_ROOT, ".git")), sg.POOL_ROOT
    # POOL_ROOT is the main checkout; REPO may be a linked worktree of it.
    if sg.REPO != sg.POOL_ROOT:
        assert os.path.isfile(os.path.join(sg.REPO, ".git"))


def test_the_fingerprint_names_the_pool_file_absolutely(tmp_path):
    """A path relative to the checkout is identical in every worktree, so two
    runs against two different pools carried identical provenance."""
    g = SpendGate(policy(tmp_path))
    fp = g.fingerprint()
    assert os.path.isabs(fp["ledger_abspath"])
    assert fp["pool_root"]


def test_a_nan_spend_cannot_void_the_ceiling(gate):
    """NaN is not `< 0`, so a non-negative check lets it through -- and then
    every `>` against a NaN total is False and the ceiling is gone. The ledger
    is append-only, so it could not have been taken back."""
    a = gate.reserve("a", usd_cap=10.0, action_cap=10)
    with pytest.raises(SpendGateError):
        gate.record(a, usd=float("nan"))
    with pytest.raises(SpendGateError):
        gate.check(a, usd=float("nan"))
    with pytest.raises(SpendGateError):
        gate.reserve("b", usd_cap=float("nan"), action_cap=1)
    assert gate.totals().usd == 0.0


def test_an_infinite_spend_is_refused_by_rule_not_by_accident(gate):
    """`+inf` happened to fail closed through float comparison. A rule that
    holds by accident is not a rule."""
    a = gate.reserve("a", usd_cap=10.0, action_cap=10)
    with pytest.raises(SpendGateError):
        gate.record(a, usd=float("inf"))
    assert gate.totals().usd == 0.0


def test_blindness_cannot_be_cleared_for_nothing(gate):
    """`price_unpriced(usd=0.0, resolves=N)` accounted for N real calls at
    $0.00 and re-opened the gate on the strength of it."""
    a = gate.reserve("a", usd_cap=10.0, action_cap=10)
    gate.record(a, usd=0.0, actions=1, unpriced=True)
    with pytest.raises(SpendGateError):
        gate.price_unpriced(a, usd=0.0, resolves=1, reason="nothing to see")
    with pytest.raises(SpendGateTripped):
        gate.check(a, usd=0.01)                # still blind, still refusing
