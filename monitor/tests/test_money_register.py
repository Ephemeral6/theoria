"""The money register, made checkable.

Before 2026-08-02 nothing in `monitor/tests` (39 files) matched `spend_gate`,
`gate-exception` or `登记簿`: every number in the register was a sentence a
human had typed, and no test could turn any of them red. A register nothing can
falsify is decoration. Two things went wrong under that cover and both are in
`monitor/INCIDENTS.md`:

* `INC-MON-001` — the dev-pile allocation B = $60 was spent to $129.03 (215%)
  while the dashboard cell stayed **green**, because `_spend_watch()` hard-coded
  a $200 envelope and summed the whole pool. B was not a quantity that
  instrument could express.
* `INC-MON-002` — two live entries both numbered `#12`, and which one keeps the
  number decides whether a paid $12.2517 leg has any authorisation at all.

`test_register_ids_are_unique_and_have_no_gap` below is the assertion that
would have caught the second on the day it was written.

**Why breaches are checked by SET EQUALITY rather than by "must not breach".**
B is already over, and so are two R1b reserves. A test asserting "no breach"
would be red forever, and a gate that is always red gets read as furniture. So
the contract is: *the breaches observed in the ledger must be exactly the
breaches declared in `money.json`*. A new, undeclared breach fails — which is
the job. A declared breach that has silently disappeared also fails — which
stops the register rotting. Recording a breach is therefore the only way to get
back to green, and that is the discipline this file exists to enforce.

Offline: reads two files, no network, no model call, spends nothing.
`proxy/var/` is gitignored, so on a fresh checkout the ledger is absent and the
ledger-dependent tests **skip** — they never degrade to green
(`monitor/accounts.py`'s 「不许有第三个值坍缩」).

Does not call `scan.build()`: `monitor/tests/test_gate_budget.py` holds the
one-real-scan rule for this suite.
"""

import json
import math
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
MONITOR = os.path.dirname(HERE)
ROOT = os.path.dirname(MONITOR)

MONEY = os.path.join(MONITOR, "money.json")

#: `proxy/var/` is gitignored, so a worktree does not have the pool even though
#: the box does. `THEORIA_SPEND_LEDGER` lets a worktree be checked against the
#: real ledger -- without it these tests would be permanently skipped anywhere
#: except the main checkout, and a test that only ever skips is not a test.
LEDGER = os.environ.get("THEORIA_SPEND_LEDGER") or os.path.join(
    ROOT, "proxy", "var", "spend_gate.jsonl")


def _money():
    with open(MONEY, encoding="utf-8") as fh:
        return json.load(fh)


def _ledger_rows():
    if not os.path.exists(LEDGER):
        pytest.skip("proxy/var/spend_gate.jsonl absent (gitignored; a fresh "
                    "checkout has no pool) -- skipping, never passing")
    rows = []
    with open(LEDGER, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:                      # noqa: BLE001
                    continue
    return rows


def _charges_by_campaign(rows, kinds):
    out = {}
    for r in rows:
        if r.get("kind") not in kinds:
            continue
        c = str(r.get("campaign") or "未标注")
        out[c] = out.get(c, 0.0) + float(r.get("usd") or 0)
    return out


def _covered(campaign, entry, ts=None):
    """Is `campaign` inside this entry's envelope?

    `from_utc` is honoured and not optional. Register #12 covers the whole
    dev-pile *from the instant it landed*; ignoring that would put legs paid
    two days earlier inside its $15 envelope and manufacture breaches that
    never happened. The first draft of this file did exactly that.
    """
    cov = entry.get("covers") or {}
    if not any(n in campaign for n in (cov.get("campaign_substrings") or [])):
        return False
    frm = cov.get("from_utc")
    if frm and ts is not None and str(ts) < frm:
        return False
    return True


#: Campaigns the harness' own tests write into the real ledger. They charge
#: $0 but still emit `reserve` rows with a `usd_cap`, so a money check that
#: does not exclude them audits test doubles. Noticed 2026-08-02 by this file
#: failing; recorded rather than silently filtered.
_FIXTURE_MARKERS = ("pytest-", "_probe-")


def _is_fixture(campaign):
    return any(m in campaign for m in _FIXTURE_MARKERS)


# ============================================ 1. the register's own shape
def test_register_ids_are_unique_and_have_no_gap():
    """The assertion that would have caught INC-MON-002 on the day it landed.

    Order is deliberately NOT asserted: the house precedent
    (`baseline-arms/INCIDENTS.md:7-13`) is to renumber in place and never
    reorder paragraphs, so a corrected register is legitimately out of order.
    """
    ids = [e["id"] for e in _money()["register"]]

    assert len(ids) == len(set(ids)), (
        "duplicate register id(s): %s -- this is INC-MON-002's signature, and "
        "which entry keeps a duplicated number decides whether a paid leg has "
        "any authorisation" % sorted(i for i in set(ids) if ids.count(i) > 1))
    assert sorted(ids) == list(range(min(ids), max(ids) + 1)), (
        "register ids have a gap: %s" % sorted(ids))


def test_the_id_check_can_actually_fail():
    """Negative control. A guard never seen refusing has not been shown to guard."""
    ids = [10, 11, 12, 12, 13]
    assert len(ids) != len(set(ids))
    ids = [10, 11, 13]
    assert sorted(ids) != list(range(min(ids), max(ids) + 1))


def test_the_rendered_register_agrees_with_money_json_on_the_id_set():
    """`spec.py` is prose, `money.json` is the numbers -- but the ids must agree.

    This is the join that stops the two drifting into two registers.
    """
    import sys                                         # noqa: PLC0415
    if MONITOR not in sys.path:
        sys.path.insert(0, MONITOR)
    import spec                                        # noqa: PLC0415

    note = [i for p in spec.PHASES for i in p["items"]
            if i["id"] == "p3-gate-exception"][0]["note"]
    rendered = {int(n) for n in re.findall(r"\*\*#(\d+)\s", note)}
    declared = {e["id"] for e in _money()["register"]}

    missing = declared - rendered
    assert not missing, (
        "money.json declares register entries the rendered register does not "
        "mention: %s" % sorted(missing))


# ================================================ 2. the numbers reproduce
def test_settled_totals_reproduce_from_the_ledger():
    money = _money()
    charges = _charges_by_campaign(_ledger_rows(), set(money["pool"]["_charge_kinds"]))

    checked = 0
    for entry in money["register"]:
        if entry.get("settled_usd") is None or not (entry.get("covers") or {}):
            continue
        got = sum(v for k, v in charges.items() if _covered(k, entry))
        assert abs(got - entry["settled_usd"]) <= 0.01, (
            "register #%s says settled $%.4f, the ledger says $%.4f"
            % (entry["id"], entry["settled_usd"], got))
        checked += 1

    assert checked >= 4, "only %d entries carried a settled figure" % checked


def test_no_paid_dev_pile_campaign_is_unregistered():
    """Every campaign that actually charged money is covered by some entry.

    'At least one', not 'exactly one': a batch envelope and a round envelope
    legitimately both cover the same leg. What must never happen is a leg
    covered by none -- that is spending with no authorisation on record.
    """
    money = _money()
    charges = _charges_by_campaign(_ledger_rows(), set(money["pool"]["_charge_kinds"]))
    needle = money["allocations"]["dev_pile_B"]["campaign_substring"]

    orphans = []
    for campaign, usd in sorted(charges.items()):
        if needle not in campaign or usd <= 0:
            continue
        if not any(_covered(campaign, e) for e in money["register"]):
            orphans.append((campaign, round(usd, 4)))

    assert not orphans, (
        "dev-pile campaigns that charged money and are covered by no register "
        "entry: %s" % orphans)


# ============================================= 3. breaches, by set equality
def test_allocation_breaches_are_exactly_the_declared_ones():
    money = _money()
    charges = _charges_by_campaign(_ledger_rows(), set(money["pool"]["_charge_kinds"]))

    observed, declared = set(), set()
    for name, alloc in money["allocations"].items():
        needle, cap = alloc.get("campaign_substring"), alloc.get("usd")
        if not needle or cap is None:
            continue
        spent = sum(v for k, v in charges.items() if needle in k)
        if spent > cap:
            observed.add(name)
        if alloc.get("breached"):
            declared.add(name)

    assert observed == declared, (
        "allocation breaches drifted from the record.\n"
        "  in the ledger but not declared (write it down): %s\n"
        "  declared but no longer in the ledger (stale): %s"
        % (sorted(observed - declared), sorted(declared - observed)))


def test_reserve_caps_are_within_declaration_or_are_declared_breaches():
    money = _money()
    rows = _ledger_rows()
    ceiling = money["pool"]["model_call_ceiling_usd"]

    declared = set()
    for entry in money["register"]:
        for b in entry.get("known_reserve_breaches") or []:
            declared.add(b["campaign_substring"])

    # Only campaigns that actually charged money. A reserve raised by a test
    # double that then spent $0 is not a money event, and the ledger carries
    # plenty of those.
    charges = _charges_by_campaign(rows, set(money["pool"]["_charge_kinds"]))
    paid = {c for c, usd in charges.items() if usd > 0 and not _is_fixture(c)}

    observed = set()
    for r in rows:
        if r.get("kind") != "reserve":
            continue
        campaign = str(r.get("campaign") or "")
        cap = r.get("usd_cap")
        if cap is None or campaign not in paid:
            continue
        ts = r.get("ts") or r.get("utc")
        for entry in money["register"]:
            per_leg = (entry.get("declared") or {}).get("usd_per_leg")
            if per_leg is None or not _covered(campaign, entry, ts):
                continue
            if float(cap) > per_leg + ceiling + 1e-9:
                observed.add(next((n for n in declared if n in campaign),
                                  campaign))

    assert observed == declared, (
        "reserve-cap breaches drifted from the record.\n"
        "  over the declared per-leg envelope but not written down: %s\n"
        "  written down but no longer over: %s"
        % (sorted(observed - declared), sorted(declared - observed)))


# ================================================== 4. the unit guard
def test_action_cap_is_read_in_outbound_units_not_actions():
    """The negative control against a misreading that reached a draft.

    `action_cap 5616` against a declared 300 actions is NOT an 18.7x breach:
    the pool counts outbound ARC HTTP requests, not scorecard actions, and
    5616 is exactly what 300 declared actions converts to. #10 and #11 settled
    compliant carrying the same 5616. Dividing the two is dividing two units.
    """
    pool = _money()["pool"]
    expected = pool["outbound_fixed"] + math.ceil(
        300 * pool["outbound_per_action"] * pool["outbound_tail_safety"])

    assert expected == 5616, (
        "the declared conversion no longer reproduces the 5616 that #10, #11 "
        "and #14 all carry: got %d" % expected)
    assert expected / 300 > 18, (
        "if this ratio ever stops looking alarming the guard has lost its "
        "point: it is alarming, and it is still not a breach")


def test_the_reserve_check_would_catch_a_new_undeclared_breach():
    """Negative control for the set-equality contract itself."""
    declared = {"20260801T001851Z-R1b-g50t-a"}
    observed = declared | {"20260899T000000Z-R9-invented"}
    assert observed != declared
    assert sorted(observed - declared) == ["20260899T000000Z-R9-invented"]
