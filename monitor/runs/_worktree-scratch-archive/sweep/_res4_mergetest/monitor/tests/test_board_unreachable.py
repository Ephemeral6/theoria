"""S35: the board prints "reserved, waiting for its researcher" over work that
researcher can never be offered.

Two guards, each correct alone. `cmd_claim` withholds any item whose
`released_by:` names the claimant -- that one stopped S22's claim/release
livelock (11 seconds between hand-back and re-offer). `LANE-NOT-YOURS` keeps
everyone else off a live researcher's queue. Their intersection is empty: an
item on a live lane, handed back by that lane's own owner, is claimable by
nobody at all.

And the board printed it as healthy. `cmd_list`'s reserved section walked
`candidates(lane)` and never asked `released_by`, so the same question had two
answers on two code paths -- claim said "not yours", list said "waiting for
you" -- with no error on either.

Measured on the live board, 2026-07-29T22:45Z (probe and JSON in
`monitor/runs/20260729T224500Z-S35/`): 11 items on the shelf, 1 reachable,
**10 unreachable**, of which 2 were printed under `reserved`:

    E18-survey-numbers-reproducible  lane=verify  owner=RES-3  released_by=RES-3
    S22-access-check-close           lane=infra   owner=RES-4  released_by=RES-4

E18 is the verify lane's **priority 1**. The requirement to check it was
written as a hedge ("if it is there too, it is a second sample rather than a
coincidence"); it is there.

The tests below come in pairs: what `list` may not say, and what the exit --
`reassign` -- has to do about it. Printing an unreachable item is not fixing
it; it had already been printed four times.

Everything is offline: a tmp board, no network, no API, no sealed pile, and
nothing under the real `monitor/board/`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import board                                                    # noqa: E402


OWNERS = {"campaign": "RES-1", "paper": "RES-2",
          "verify": "RES-3", "infra": "RES-4"}


def _fleet(tmp_path, monkeypatch, live=OWNERS):
    """A tmp board with `live`'s owners heartbeating **now**.

    The locks matter: a lane whose owner is stale is unsealed for generic
    workers, which is a second reason an item could be reachable and would
    blur every assertion here. Fresh locks mean the only thing under test is
    the hand-back.
    """
    home = tmp_path / "monitor"
    for sub in ("board/items", "board/claimed", "board/done", "ops-status"):
        (home / sub).mkdir(parents=True)
    monkeypatch.setattr(board, "HERE", str(home))
    monkeypatch.setattr(board, "BOARD", str(home / "board"))
    monkeypatch.setattr(board, "ITEMS", str(home / "board" / "items"))
    monkeypatch.setattr(board, "CLAIMED", str(home / "board" / "claimed"))
    monkeypatch.setattr(board, "DONE", str(home / "board" / "done"))
    monkeypatch.setattr(board, "LOG", str(home / "board" / "board.log"))
    monkeypatch.setattr(board, "OPS_STATUS", str(home / "ops-status"))
    monkeypatch.setattr(board, "LANE_OWNER", dict(OWNERS))
    monkeypatch.setattr(board, "prior_work", lambda iid, repo=None: [])
    for owner in live.values():
        (home / "ops-status" / ("%s.lock" % owner)).write_text(
            board.utc(), encoding="utf-8")
    return home


def _item(home, iid, lane="infra", territory="src", priority=2, deps="none",
          released_by=None, spend=None, where="items"):
    body = ["priority: %d" % priority, "cell: X", "territory: %s" % territory,
            "deps: %s" % deps]
    if lane:
        body.append("lane: %s" % lane)
    if spend:
        body.append("spend: %s" % spend)
    if released_by:
        body.append("released_by: %s" % released_by)
    body += ["", "# %s" % iid, "", "work."]
    path = home / "board" / where / ("%s.md" % iid)
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path


def _handed_back(home, iid, worker, reason, **kw):
    """An item its lane owner claimed and released -- through the real verbs,
    so the front matter and the body note are written the way the board writes
    them, not the way this file imagines it does."""
    _item(home, iid, **kw)
    assert board.cmd_claim(worker, kw.get("lane", "infra")) == 0
    assert board.cmd_release(iid, worker, reason) == 0
    return home / "board" / "items" / ("%s.md" % iid)


def _section(out, name):
    """Lines under `=== name ... ===`, up to the next section header."""
    lines, keep = [], False
    for line in out.splitlines():
        if line.startswith("==="):
            keep = line.startswith("=== " + name)
            continue
        if keep:
            lines.append(line)
    return lines


# ------------------------------------------------------- what `list` may not say

def test_an_item_its_own_owner_handed_back_is_not_reserved(tmp_path,
                                                           monkeypatch, capsys):
    """The defect verbatim: `list` printed S22 as reserved for RES-4 while
    `claim RES-4 --lane infra` would never offer it."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    capsys.readouterr()

    board.cmd_list()
    out = capsys.readouterr().out
    assert not any("S22-costly" in l for l in _section(out, "reserved")), \
        "printed as waiting for the one person who can never be offered it"
    assert any("S22-costly" in l for l in _section(out, "unreachable"))


def test_list_and_claim_give_the_same_answer(tmp_path, monkeypatch, capsys):
    """The root cause, stated as a property: every id `list` reserves for a
    lane owner must be an id `claim` would actually hand that owner.

    This is the assertion that keeps the fix from rotting. A future exclusion
    added to `candidates()` alone cannot reintroduce the split, because both
    paths now ask one function."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    _item(home, "S40-fine", lane="infra", territory="other")
    _item(home, "E18-numbers", lane="verify", territory="engine-rig",
          priority=1)
    capsys.readouterr()

    board.cmd_list()
    out = capsys.readouterr().out
    for line in _section(out, "reserved"):
        iid = line.split()[1]
        lane = [p.split("=")[1] for p in line.split() if p.startswith("lane=")][0]
        offered = {r[1] for r in board.offers(OWNERS[lane], lane)[0]}
        assert iid in offered, \
            "%s is reserved for %s, who cannot claim it" % (iid, OWNERS[lane])


def test_the_unreachable_line_names_the_releaser_and_the_reason(tmp_path,
                                                                monkeypatch,
                                                                capsys):
    """The reason has been on disk the whole time -- `_record_release` writes
    it into the item body. Nothing read it back. A reader who cannot see *why*
    it was handed back cannot decide where to send it next, which is how an
    item gets printed four times and moved zero."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4",
                 "needs a spending authority; only RES-1 may spend")
    capsys.readouterr()

    board.cmd_list()
    line = " ".join(l for l in _section(capsys.readouterr().out, "unreachable")
                    if "S22-costly" in l or "reassign" in l)
    assert "RES-4" in line
    assert "needs a spending authority" in line
    assert "reassign" in line, "no exit printed next to the diagnosis"


def test_a_territory_blocked_item_is_not_called_unreachable(tmp_path,
                                                            monkeypatch,
                                                            capsys):
    """Negative control on the word. Territory exclusivity blocks an item too,
    but it has an exit that arrives on its own -- the neighbour delivers. Only
    items with **no** exit belong in the section that says so, or the section
    becomes noise and gets skimmed like the reserved one was."""
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "S36-neighbour", lane="infra", territory="monitor")
    assert board.cmd_claim("RES-4", "infra") == 0        # occupies `monitor`
    _item(home, "S37-waiting", lane="infra", territory="monitor")
    capsys.readouterr()

    board.cmd_list()
    out = capsys.readouterr().out
    assert not any("S37-waiting" in l for l in _section(out, "unreachable"))
    assert any("S37-waiting" in l for l in _section(out, "territory-blocked"))


def test_every_shelf_item_appears_in_some_section(tmp_path, monkeypatch,
                                                  capsys):
    """The fifth section existed to catch items that fall out of every other
    one -- and `reserved` defeated it, because an id printed there counts as
    shown. Whatever the sections are called, an item on the shelf has to turn
    up in one of them."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    _handed_back(home, "E18-numbers", "RES-3", "unstated-ish",
                 lane="verify", territory="engine-rig", priority=1)
    _item(home, "V9-open", lane="verify", territory="exam")
    _item(home, "W1-generic", lane=None, territory="docs")
    _item(home, "X1-blocked", lane="infra", territory="far", deps="NOPE-1")
    capsys.readouterr()

    board.cmd_list()
    out = capsys.readouterr().out
    for iid in ("S22-costly", "E18-numbers", "V9-open", "W1-generic",
                "X1-blocked"):
        assert iid in out, "%s is on the shelf and in no section" % iid


# ------------------------------------------------------------------- the exit

def test_reassign_puts_it_where_someone_can_claim_it(tmp_path, monkeypatch,
                                                     capsys):
    """The whole point. S22's remaining work needs real API spend and CHARTER
    gives that to RES-1 alone, so the exit is the campaign lane -- not another
    printout."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    capsys.readouterr()

    assert board.cmd_reassign("S22-costly", "campaign", "RES-4",
                              "remaining half needs API spend; CHARTER: RES-1") == 0
    assert board.cmd_claim("RES-1", "campaign") == 0, "still nobody's work"
    assert "S22-costly.RES-1.md" in os.listdir(board.CLAIMED)


def test_reassign_leaves_the_history_and_the_reason_on_disk(tmp_path,
                                                            monkeypatch,
                                                            capsys):
    """A reassignment is a decision, so it is written down where the next
    reader of the item finds it, and in board.log next to the claims and
    releases it is meant to explain."""
    home = _fleet(tmp_path, monkeypatch)
    path = _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    capsys.readouterr()

    board.cmd_reassign("S22-costly", "campaign", "RES-4", "CHARTER: only RES-1 spends")
    body = path.read_text(encoding="utf-8")
    assert "CHARTER: only RES-1 spends" in body
    assert "RES-4" in board.meta(str(path))[board.RELEASED_BY], \
        "the hand-back is history, not something a reassignment erases"
    log = (home / "board" / "board.log").read_text(encoding="utf-8")
    assert "REASSIGN S22-costly" in log and "campaign" in log


def test_reassign_clears_only_the_new_owner_from_released_by(tmp_path,
                                                             monkeypatch,
                                                             capsys):
    """If the target had handed it back before, the withhold guard would make
    the reassignment a no-op that reports success -- this lane's own disease.
    Clearing exactly the target is the deliberate, named, reasoned re-offer
    that the automatic one is not."""
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "C9-hard", lane="infra", released_by="RES-4, RES-1")
    capsys.readouterr()

    assert board.cmd_reassign("C9-hard", "campaign", "RES-4", "RES-1 has the tools") == 0
    m = board.meta(os.path.join(board.ITEMS, "C9-hard.md"))
    assert board.released_by(m) == {"RES-4"}
    assert board.cmd_claim("RES-1", "campaign") == 0


def test_reassign_refuses_without_a_reason(tmp_path, monkeypatch, capsys):
    """An unexplained reassignment is how an item goes round the lanes."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    capsys.readouterr()

    assert board.cmd_reassign("S22-costly", "campaign", "RES-4", "") != 0
    assert board.meta(os.path.join(board.ITEMS, "S22-costly.md"))["lane"] == "infra"


def test_a_stranger_cannot_pull_an_item_into_another_lane(tmp_path, monkeypatch,
                                                          capsys):
    """The mirror of LANE-NOT-YOURS. Reassignment moves work between queues,
    so an unguarded verb is a way to strip a lane bare -- the exact hole the
    self-declared `--lane` had."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "E18-numbers", "RES-3", "no time",
                 lane="verify", territory="engine-rig", priority=1)
    capsys.readouterr()

    assert board.cmd_reassign("E18-numbers", "infra", "RES-4", "I want it") != 0
    assert board.meta(os.path.join(board.ITEMS, "E18-numbers.md"))["lane"] == "verify"
    assert board.cmd_reassign("E18-numbers", "infra", "monitor", "RES-3 is out") == 0


def test_only_the_monitor_may_hand_an_item_back_to_the_lane_that_refused_it(
        tmp_path, monkeypatch, capsys):
    """Same lane in, same lane out, releaser cleared -- that is the livelock
    with a verb in front of it. A researcher must not be able to un-refuse
    their own refusal; the monitor deciding "try again" is a different act and
    leaves a signed line saying so."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    capsys.readouterr()

    assert board.cmd_reassign("S22-costly", "infra", "RES-4", "on reflection") != 0
    assert board.cmd_claim("RES-4", "infra") == 3, "it came back to the refuser"
    assert board.cmd_reassign("S22-costly", "infra", "monitor",
                              "spend approved, retry") == 0
    assert board.cmd_claim("RES-4", "infra") == 0


def test_reassign_refuses_work_that_is_claimed_or_delivered(tmp_path,
                                                            monkeypatch,
                                                            capsys):
    """`done/` is authoritative and a claim is somebody's context in flight;
    a verb that renames items must not reach into either."""
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "S40-mine", lane="infra")
    assert board.cmd_claim("RES-4", "infra") == 0
    _item(home, "S41-done", lane="infra", where="done")
    capsys.readouterr()

    assert board.cmd_reassign("S40-mine", "campaign", "monitor", "moving") != 0
    assert board.cmd_reassign("S41-done", "campaign", "monitor", "moving") != 0


def test_reassign_to_generic_unlanes_it(tmp_path, monkeypatch, capsys):
    """Not every stuck item belongs to another researcher. `generic` is the
    other exit: drop the lane and let a one-shot worker take it."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    capsys.readouterr()

    assert board.cmd_reassign("S22-costly", "generic", "RES-4", "any hand will do") == 0
    assert board.meta(os.path.join(board.ITEMS, "S22-costly.md"))["lane"] == ""
    assert board.cmd_claim("W-9999") == 0


def test_the_unreachable_section_empties_after_the_exit_is_used(tmp_path,
                                                                monkeypatch,
                                                                capsys):
    """End to end, because the requirement is that the item *moves*, not that
    it is described better while it sits there."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    board.cmd_reassign("S22-costly", "campaign", "RES-4", "CHARTER: RES-1 spends")
    capsys.readouterr()

    board.cmd_list()
    out = capsys.readouterr().out
    assert not _section(out, "unreachable")
    assert any("S22-costly" in l for l in _section(out, "reserved"))


def test_board_empty_does_not_tell_the_refuser_that_others_can_take_it(
        tmp_path, monkeypatch, capsys):
    """Found by running the fixed board against the live one, 01:50Z:

        BOARD-EMPTY（1 件被扣下：你自己交回过 —— S22-access-check-close。别人仍可领）

    Nobody else can: LANE-NOT-YOURS holds everyone outside infra off it. This
    is the same sentence as the reserved section, in the place where it does
    the most damage -- it is the one line a reader acts on immediately, and it
    tells them to stop worrying about the item.

    The claim is true for an *unlaned* item, which is why the sentence exists;
    the negative control below keeps it for that case."""
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    capsys.readouterr()

    assert board.cmd_claim("RES-4", "infra") == 3
    out = capsys.readouterr().out
    assert "别人仍可领" not in out, "it told the refuser someone else would do it"
    assert "reassign" in out, "no exit offered where the reader is looking"

    # NEGATIVE CONTROL: an unlaned item really can go to anyone else, and the
    # sentence has to survive for that case -- the fix is a distinction, not a
    # deletion.
    _item(home, "W1-generic", lane=None, territory="docs")
    assert board.cmd_claim("W-1") == 0
    assert board.cmd_release("W1-generic", "W-1", "not for me") == 0
    capsys.readouterr()

    assert board.cmd_claim("W-1") == 3
    assert "别人仍可领" in capsys.readouterr().out


# ------------------------------------ the disagreement that was billed in money

def test_the_fleet_loop_does_not_launch_a_session_for_unclaimable_work(
        tmp_path, monkeypatch, capsys):
    """`standing.work_for` counted `len(candidates(lane))` and launched a real
    session whenever that was positive. For a lane whose only item its owner
    had handed back, the launched session ran `claim`, got BOARD-EMPTY and
    exited -- every `MIN_RELAUNCH_MIN`, for as long as the item sat there. Two
    items sat there for 14.9 and 12.9 hours.

    This is the same two-answers defect as the reserved section, and it is the
    expensive end of it: `list` misleads a reader, this one spends."""
    import standing                                              # noqa: E402
    home = _fleet(tmp_path, monkeypatch)
    _handed_back(home, "S22-costly", "RES-4", "needs a spending authority")
    monkeypatch.setattr(standing, "unread_count", lambda a: 0)
    capsys.readouterr()

    w = standing.work_for("RES-4", "infra")
    assert w["claimable"] == 0, "counted work its own owner can never be handed"
    assert w["any"] is False, "a session would be launched to claim nothing"

    # NEGATIVE CONTROL: the same lane with one item nobody handed back.
    _item(home, "S40-fine", lane="infra", territory="other")
    assert standing.work_for("RES-4", "infra")["claimable"] == 1


# ------------------------------------------- the reason the exit needs as input

def test_release_without_a_reason_is_refused(tmp_path, monkeypatch, capsys):
    """`main()` turned a missing reason into the string `unstated`, and E18 --
    the verify lane's priority 1 -- has carried exactly that since
    2026-07-29T12:37:38Z. A word that looks like a reason and carries none is
    the third value this fleet keeps finding: whoever routes the item next has
    nothing to route it on."""
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "S22-costly", lane="infra")
    assert board.cmd_claim("RES-4", "infra") == 0
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv",
                        ["board.py", "release", "S22-costly", "RES-4"])
    assert board.main() != 0
    assert "S22-costly.RES-4.md" in os.listdir(board.CLAIMED), \
        "refused, so the claim is untouched"

    monkeypatch.setattr(sys, "argv",
                        ["board.py", "release", "S22-costly", "RES-4",
                         "needs", "a", "spending", "authority"])
    assert board.main() == 0
    body = (home / "board" / "items" / "S22-costly.md").read_text(encoding="utf-8")
    assert "needs a spending authority" in body
