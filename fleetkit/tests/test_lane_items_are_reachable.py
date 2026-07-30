"""S42 defect 2: a `lane:` item used to be unreachable by construction.

`board.py` carried

    #: Filled from fleet.json at import; empty means "no lane has an owner",
    #: which is the correct behaviour for a fleet that has not declared any.
    LANE_OWNER = {}

and the sentence was false twice over. There was no writer anywhere in the
package -- four occurrences, one assignment and three reads, no `.update`, no
`setdefault`, no monkeypatch, not in the tests and not in `verify.py`. And even
a wired-up `fleet.json` could not have supplied it: `FleetConfig.lanes` is a
`List[str]`, a schema with no room for a lane->owner mapping.

The consequence was not cosmetic. With `LANE_OWNER == {}` forever,
`stale_lanes()` returned `set()` forever, so `candidates()` dropped every
lane-tagged item from a generic worker's view; `cmd_list`'s reserved section
iterated `sorted(LANE_OWNER)` zero times and printed nothing at all rather than
an empty heading; and the 45-minute "the owner has gone stale" escape hatch
could never fire, because it was gated on the same empty dict. A `lane:` item
appeared in no section of `list` and had no exit but editing the file by hand.

## The decision, and why

**Deleted, not made true.** Making it true costs a config schema change
(`lanes: List[str]` -> a mapping, dragging `THEORIA_EXAMPLE` and
`REQUIRED_CONFIG` with it) to buy a reservation feature that no caller of this
package asks for -- fleetkit's callers are its own tests and `verify.py`, and
Theoria's monitor has its own board module and does not import this one. A
schema grown for a hypothetical user is how the original claim came to be
written without a mechanism behind it.

What is kept is the half that `FleetConfig.lanes: List[str]` *can* express, and
that the field's own docstring already describes: "lanes a standing agent can
be restricted to". A lane is a restriction the WORKER accepts, not a claim the
ITEM makes. So `--lane X` narrows; it never widens; and every lane-tagged item
is listed and claimable by anybody, which is the opposite of silently invisible.

That reversal has a consequence worth stating: the `spend: api` guard used to
read `not lane and ...`, so a worker that typed `--lane campaign` skipped it.
Under "lane can only narrow" that guard cannot be lane-conditional either, and
it no longer is.
"""

import os
import subprocess
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit import config                                     # noqa: E402


def _fleet(tmp_path):
    root = tmp_path / "newproject"
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    config.write_default(str(root), task_prefix="LaneProbe-",
                         territories=["src", "docs"])
    home = root / ".fleet"
    home.mkdir()
    return root, home


def _board(home, *args, expect=0):
    env = dict(os.environ)
    env["FLEET_HOME"] = str(home)
    env["PYTHONPATH"] = KIT + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, "-m", "fleetkit.board"] + list(args),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, cwd=str(home))
    assert r.returncode == expect, (args, r.returncode, r.stdout, r.stderr)
    return r.stdout


def _put_item(home, iid, cell, territory, lane=None, spend=None,
              generic_ok=None):
    items = home / "board" / "items"
    items.mkdir(parents=True, exist_ok=True)
    body = "priority: 2\ncell: %s\nterritory: %s\ndeps: none\n" % (cell,
                                                                  territory)
    for key, val in (("lane", lane), ("spend", spend),
                     ("generic_ok", generic_ok)):
        if val:
            body += "%s: %s\n" % (key, val)
    body += "\n# %s\n\nA toy item.\n" % iid
    (items / ("%s.md" % iid)).write_text(body, encoding="utf-8")


# ------------------------------------------------- the claim that was false

def test_the_package_no_longer_claims_a_lane_owner_map_it_cannot_build():
    """No dead sentence, and nothing left that could quietly reintroduce it."""
    src = open(os.path.join(KIT, "fleetkit", "board.py"),
               encoding="utf-8").read()

    assert "Filled from fleet.json at import" not in src, (
        "the false docstring is back")
    assert "LANE_OWNER" not in src, (
        "LANE_OWNER is back. If it is real this time it needs a data source: "
        "FleetConfig.lanes is a List[str] and cannot express lane->owner.")
    assert "stale_lanes" not in src, (
        "stale_lanes is back. It existed only to unfreeze lanes whose owner "
        "had gone quiet, and with no owners there is nothing to unfreeze.")
    assert "def config_root" in src and "def task_prefix" in src, (
        "sanity: the two functions that DO read fleet.json must still be here")


def test_fleet_config_lanes_is_still_a_list_of_names():
    """The schema the decision rests on. If this becomes a mapping, revisit."""
    cfg = config.FleetConfig("/tmp/x", task_prefix="P-",
                             territories=["src"], lanes=["infra", "paper"])
    assert cfg.lanes == ["infra", "paper"]
    assert all(isinstance(x, str) for x in cfg.lanes)


# ------------------------------------------------------------- reachability

def test_a_lane_tagged_item_is_listed(tmp_path):
    """Pre-S42 `list` printed only an empty available heading and stopped."""
    _root, home = _fleet(tmp_path)
    _put_item(home, "L1-laned", "L1", "src", lane="campaign")

    out = _board(home, "list")

    assert "L1-laned" in out, (
        "a lane-tagged item appears nowhere in `list`: %r" % out)
    assert "lane:campaign" in out, out


def test_a_lane_tagged_item_can_be_claimed_by_a_plain_worker(tmp_path):
    """No lane argument, no owner, no ceremony -- it is just work."""
    _root, home = _fleet(tmp_path)
    _put_item(home, "L1-laned", "L1", "src", lane="campaign")

    out = _board(home, "claim", "W-1")

    assert "CLAIM" in out and "L1-laned" in out, out
    assert os.listdir(home / "board" / "claimed") == ["L1-laned.W-1.md"]


def test_a_lane_tagged_item_has_an_exit(tmp_path):
    """claim -> done, end to end. Pre-S42 there was no exit but hand-editing."""
    _root, home = _fleet(tmp_path)
    _put_item(home, "L1-laned", "L1", "src", lane="campaign")
    _board(home, "claim", "W-1")
    _board(home, "done", "L1-laned", "W-1")

    assert os.listdir(home / "board" / "done") == ["L1-laned.W-1.md"]
    assert not os.listdir(home / "board" / "claimed")


def test_lane_narrows_and_only_narrows(tmp_path):
    """`--lane X` restricts the worker to X. It is a filter, not a key."""
    _root, home = _fleet(tmp_path)
    _put_item(home, "L1-infra", "L1", "src", lane="infra")
    _put_item(home, "L2-paper", "L2", "docs", lane="paper")

    out = _board(home, "claim", "W-1", "--lane", "paper")

    assert "L2-paper" in out, out
    assert os.listdir(home / "board" / "claimed") == ["L2-paper.W-1.md"]


def test_a_self_asserted_lane_cannot_take_work_that_spends_money(tmp_path):
    """The hole the old lane guard left open.

    The `spend: api` gate used to be written `not lane and ...`, so typing
    `--lane campaign` walked straight past it -- the worker's own word about
    itself acting as authorisation. Under "a lane can only narrow" the gate
    cannot be lane-conditional, so both of these must be refused.
    """
    _root, home = _fleet(tmp_path)
    _put_item(home, "A1-costly", "A1", "src", lane="campaign", spend="api")

    assert _board(home, "claim", "W-1", "--lane", "campaign",
                  expect=3).strip() == "BOARD-EMPTY"
    assert _board(home, "claim", "W-2", expect=3).strip() == "BOARD-EMPTY"
    assert os.listdir(home / "board" / "items") == ["A1-costly.md"]


def test_generic_ok_still_opens_that_gate(tmp_path):
    """The companion green: the guard is a guard, not a wall."""
    _root, home = _fleet(tmp_path)
    _put_item(home, "A1-costly", "A1", "src", lane="campaign", spend="api",
              generic_ok="yes")

    assert "CLAIM" in _board(home, "claim", "W-1")


# ------------------------------------------- nothing may vanish from `list`

def test_an_item_that_cannot_be_claimed_is_still_named_by_list(tmp_path):
    """The failure mode this whole item exists to kill.

    S28's incident was 11 items on the board and 8 of them mentioned nowhere in
    the output, which looks exactly like an empty board. Unclaimable is fine;
    unclaimable AND unmentioned is not.
    """
    _root, home = _fleet(tmp_path)
    _put_item(home, "A1-costly", "A1", "src", spend="api")
    _put_item(home, "B1-held", "B1", "docs")
    _put_item(home, "B2-blocked-by-territory", "B2", "docs")
    _put_item(home, "C1-waiting", "C1", "src", lane="infra")
    (home / "board" / "items" / "C1-waiting.md").write_text(
        "priority: 2\ncell: C1\nterritory: src\ndeps: Z9-never\nlane: infra\n",
        encoding="utf-8")
    _board(home, "claim", "W-1")            # takes B1-held, holding "docs"

    out = _board(home, "list")

    for iid in ("A1-costly", "B1-held", "B2-blocked-by-territory",
                "C1-waiting"):
        assert iid in out, ("%s appears nowhere in `list`:\n%s" % (iid, out))
    assert "withheld" in out, out
    assert "原因不明" not in out, (
        "list could not explain why something is unclaimable, which is a bug "
        "report the board just filed against itself:\n%s" % out)


def test_list_output_survives_the_console_code_page(tmp_path):
    """KNOWN_TRAPS territory: a print that raises is a command that did not run.

    Every string `list` can emit must encode in cp936 (and in cp437, for a
    machine that is not zh-CN). ASCII or Chinese only, no arrows, no glyphs.
    """
    _root, home = _fleet(tmp_path)
    _put_item(home, "L1-laned", "L1", "src", lane="campaign")
    _put_item(home, "A1-costly", "A1", "docs", spend="api")

    out = _board(home, "list")

    for codec in ("cp936", "gbk"):
        out.encode(codec)                   # raises if any glyph is unprintable
