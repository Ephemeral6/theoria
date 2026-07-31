"""S26 item 2: a probe that checks half an item must not be able to pass it.

`scan.build()` used one rule -- "the probe wins unless the hand-written status
is risk" -- applied with no record that it had fired. That let a probe covering
*part* of an item promote the whole item.

The live case: `p1-seal-test` is a conjunction, "no credential inside the arm"
AND "egress that bypasses the two proxies must fail". Its hand-written status is
`partial`, and its note says in as many words that the red-team surface is
unverified. Its probe, `credential_hygiene`, looks for the key's value in the
tree and never attempts an egress bypass -- and returns green. Green won. So the
board showed a passing cell for a test nobody has ever run, and `p1_green`
counted it.

The rule now: a probe may always downgrade, and may only upgrade when it covers
the whole item. Either way the disagreement is recorded instead of resolved in
silence.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scan                                                     # noqa: E402


def _item(status, scope=None, iid="x1", probe="p"):
    it = {"id": iid, "status": status, "note": "", "probe": probe}
    if scope:
        it["probe_scope"] = scope
    return it


def _pr(status):
    return {"status": status, "detail": ""}


# ------------------------------------------------------------ the live case

def test_a_half_covering_probe_cannot_pass_the_item():
    """p1-seal-test, exactly: hand partial, probe green, coverage partial."""
    ov = []
    kept = scan._reconcile(_item("partial", scope="partial", iid="p1-seal-test"),
                           _pr("green"), ov)
    assert kept == "partial", kept
    assert ov and ov[0]["item"] == "p1-seal-test", ov
    assert ov[0]["hand"] == "partial" and ov[0]["probe_said"] == "green"


def test_a_full_covering_probe_may_pass_the_item():
    """The companion green: the rule must not simply pin everything down.

    Without this, `return hand` would satisfy the test above and the probe layer
    would stop doing anything at all.
    """
    ov = []
    kept = scan._reconcile(_item("partial"), _pr("green"), ov)
    assert kept == "green", kept


# --------------------------------------------- downgrades are always allowed

def test_a_half_covering_probe_may_still_report_a_problem():
    """Partial coverage limits what a probe may *approve*, not what it may warn.

    Evidence that something is broken is worth acting on even from a check that
    does not cover everything; evidence of absence from a partial check is not.
    """
    ov = []
    kept = scan._reconcile(_item("green", scope="partial"), _pr("risk"), ov)
    assert kept == "risk", kept


def test_a_hand_written_risk_survives_a_green_probe():
    ov = []
    kept = scan._reconcile(_item("risk"), _pr("green"), ov)
    assert kept == "risk", kept


# ---------------------------------------------------- nothing happens silently

def test_every_disagreement_is_recorded():
    ov = []
    scan._reconcile(_item("partial", iid="a"), _pr("green"), ov)          # upgrade
    scan._reconcile(_item("green", scope="partial", iid="b"), _pr("risk"), ov)
    scan._reconcile(_item("partial", scope="partial", iid="c"), _pr("green"), ov)
    assert [o["item"] for o in ov] == ["a", "b", "c"], ov
    assert all(o["why"] for o in ov), ov


def test_agreement_is_not_recorded_as_a_disagreement():
    """A log that fires on every item is a log nobody reads."""
    ov = []
    kept = scan._reconcile(_item("green"), _pr("green"), ov)
    assert kept == "green" and ov == [], ov


# ------------------------------------------------- an unprobed item says so

def test_the_build_counts_and_names_items_nothing_checks(real_scan):
    """Eleven of the sixteen Phase 1 rows have no probe.

    Several are hand-written green, which on the board looked exactly like a
    green a machine had confirmed. The count has to be visible, or the headline
    "9/16" reads as sixteen checked things.
    """
    # `out_dir=` is still the rule and is now the fixture's responsibility:
    # `scan.build()` with no argument writes `state.json`, `index.html` and
    # `history.jsonl` **into the repository**. That made every run of
    # `monitor/verify.py` leave the tree dirty -- through its own test stage,
    # not through its scan stage, which has honoured `out_dir` since S13.
    # `verify.py`'s docstring says in as many words that the gate does not dirty
    # the workspace and explains why it must not: a gate that reports its own
    # output as a change can turn the *next* territory's gate red for a reason
    # that has nothing to do with the branch being merged. The scan stage was
    # fixed and the suite that runs beside it was not, so the property was false
    # while the paragraph asserting it stayed true-looking.
    #
    # S44: this was the sixth of six tests each paying ~55s for an identical
    # real scan. `conftest.real_scan` runs it once for the session.
    state = real_scan.state
    assert state["p1_unprobed"] > 0
    assert state["p1_unprobed"] + sum(
        1 for ph in state["phases"] if ph["id"] == "p1"
        for i in ph["items"] if i["_probed"]) == state["p1_total"]
    for ph in state["phases"]:
        if ph["id"] != "p1":
            continue
        for i in ph["items"]:
            if not i["_probed"]:
                assert "无探针" in i["_note"], i["id"]
