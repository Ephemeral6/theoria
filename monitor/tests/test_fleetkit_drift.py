"""`fleetkit/fleetkit/board.py` is an extraction of `monitor/board.py`. This is
the check that stops it drifting silently.

S40's diagnosis, and the measurement bears it out exactly: the fork is in a
THIRD state -- it looks the same, it is not the same, and nobody has ever said
which it is supposed to be. `fleetkit/README.md` calls `board.py` "ported:
atomic claim, territory exclusivity, lanes, sweep" and says nothing anywhere
about tracking, drift, or deliberate simplification. Neither document contains
the words track, sync, drift, diverge, fork, snapshot or upstream.

WHAT THE MEASUREMENT FOUND (runs/20260730T0625Z-S40/FINDINGS.md, every verdict
executed rather than read):

  18 shared functions: 8 behave identically, **0 COSMETIC**, 10 DIVERGENT
  (8 of the 10 differ in source; 2 more are byte-identical source that
  diverges through a module global).

The absent COSMETIC class is the whole point. Nothing here differs only in
wording -- every non-identical function returns a different answer for a
constructible input. And TWO of the divergent functions are byte-identical
source (`stale_lanes`, `territories_busy`): they diverge through a module
global. Reading the two files side by side scores them "same". That is why this
had to be a check and not a review.

WHY "DELIBERATE SIMPLIFICATION" IS NOT AVAILABLE AS AN ANSWER. The fork base
had exactly 18 top-level functions and fleetkit has exactly those 18 -- nothing
was dropped on purpose. The 18 functions monitor has and fleetkit lacks all
landed AFTER the fork (S21, S27, S28, S29, S34, S35, S35a; 7 commits against
fleetkit's 1). So the divergence is not a simplification, it is a stale
snapshot, and several of its consequences are outright defects:

  * `_PREFIX = ""` is never assigned, so fleetkit's `cmd_sweep` judges every
    worker dead and frees LIVE claims -- `fleetkit/KNOWN_TRAPS.md` entry 1 word
    for word, latent in the kit that ships the warning.
  * `LANE_OWNER = {}` makes any item carrying a `lane:` field invisible to
    `list` and unclaimable by any documented command, with no exit at all.
  * `meta()`'s regex uses `\\s*` where monitor uses `[ \\t]*`, so an empty front
    matter field silently takes its value from the NEXT LINE -- which drops
    items into the hole above without anyone having written a lane.

Documenting those as intended behaviour would be documenting bugs as features.
So the answer to S40 requirement 2 is TRACK, and this file is the mechanism.

HOW IT WORKS. Every function present in both files is compared as normalised
source. A difference is allowed ONLY if it is named in `DECLARED` below with a
reason. So the check is not "the files must be identical" -- that would be red
forever and therefore no check at all, the same trap S39 records. It is:

    a divergence must be DECLARED, or it is red.

That is what turns the third state into one of the two legitimate ones. A new
divergence -- monitor changes a criterion and fleetkit does not follow -- is red
on the next run. An intentional one costs one line and a reason.

WHY THIS FILE LIVES IN `monitor/` AND EDITS NOTHING IN `fleetkit/`. `fleetkit`
is a separate territory on the work board and S40 declares `territory: monitor`.
Keeping the extraction honest is the extractor's obligation, so the CHECK
belongs here; the fixes to fleetkit's own code and README belong to whoever
holds that territory, and are filed as a follow-up item rather than done here.

NORMALISATION. `monitor/board.py` is CRLF on disk and the fleetkit copy is LF; a
raw diff reports 714 changed lines where the real answer is 5 hunks. Comparing
without normalising would be 100% false positive on day one.
"""

from __future__ import annotations

import ast
import os
import textwrap

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MONITOR_BOARD = os.path.join(REPO, "monitor", "board.py")
FLEETKIT_BOARD = os.path.join(REPO, "fleetkit", "fleetkit", "board.py")

#: Divergences that are known and accounted for. Key is the function name;
#: value is (verdict, why). A function that differs and is NOT here fails.
#:
#: `extraction` -- a deliberate edit made to make the code repo-agnostic. These
#:                 are correct and should stay.
#: `stale`      -- fleetkit is simply behind. Not a decision; debt with an
#:                 owner. Each names what monitor gained and when.
#: `defect`     -- fleetkit's version is WRONG, measurably, and the divergence
#:                 is the bug. These must not be closed by copying monitor
#:                 blindly; see the follow-up item.
#: The two whose source is BYTE-IDENTICAL and which diverge anyway, through
#: the LANE_OWNER global. They are declared like the rest, but exempted from
#: `test_declared_entries_still_describe_a_real_divergence`, which compares
#: source: by construction their source already matches, so that test would
#: demand their removal and delete the record of the subtlest finding here.
GLOBAL_ONLY: frozenset[str] = frozenset({"stale_lanes", "territories_busy"})

DECLARED: dict[str, tuple[str, str]] = {
    "heartbeat_age": (
        "stale",
        "S28 moved monitor to heartbeat_evidence, preferring the untracked "
        "ops-status/<a>.lock over the tracked .json. Measured: .json 3600s old "
        "with a fresh .lock gives monitor 0, fleetkit 60 -- which flips "
        "stale_lanes at STALE_MIN=45.",
    ),
    "stale_lanes": (
        "defect",
        "Source is BYTE-IDENTICAL; it diverges through the LANE_OWNER global. "
        "fleetkit's LANE_OWNER is {} and is never assigned anywhere in the "
        "package, so this function can only ever return set(). A 13-line body "
        "with a 6-line docstring narrating a real outage, which is a constant "
        "function. This is the case a side-by-side read scores as 'same'.",
    ),
    "meta": (
        "defect",
        "monitor's field regex is r'^%s:[ \\t]*(\\S+)', fleetkit's is "
        "r'^%s:\\s*(\\S+)', and \\s crosses newlines. Measured: 'lane:\\ncell: "
        "A3' yields lane='' in monitor and lane='cell:' in fleetkit; 'deps:\\n"
        "cell: B1' yields deps=['cell: B1'], an unsatisfiable dependency. "
        "Also monitor's dict carries released_by and fleetkit's does not, so "
        "every return value differs by one key.",
    ),
    "territories_busy": (
        "defect",
        "Source is BYTE-IDENTICAL; inherits meta()'s regex defect. An item "
        "with an empty territory: line gives monitor {'?': X} and fleetkit "
        "{'deps:': X}, so a DIFFERENT item is excluded from candidates().",
    ),
    "candidates": (
        "stale",
        "Missing S34's `if iid in ready: continue`, so fleetkit re-offers "
        "delivered work whenever items/X.md and done/X.*.md both exist -- the "
        "ordinary post-merge state. Also inherits stale_lanes.",
    ),
    "cmd_list": (
        "stale",
        "Missing the territory-blocked section (S28) and the unreachable "
        "section (S35). Measured: a territory-blocked item's id appears "
        "NOWHERE in fleetkit's entire output. That is verbatim the S28 "
        "incident -- 11 items on the board, 8 mentioned nowhere.",
    ),
    "cmd_claim": (
        "defect",
        "Four causes. No lane_denied guard, so a self-asserted --lane takes an "
        "item marked spend: api (measured: monitor exit 3 LANE-NOT-YOURS, "
        "fleetkit exit 0). No offers()/released_by. And `except OSError` where "
        "monitor has `except FileNotFoundError`: on Windows a sharing "
        "violation is swallowed and the board reports BOARD-EMPTY with no "
        "trace in board.log, because note() is only on the success path.",
    ),
    "cmd_release": (
        "defect",
        "Default reason 'unstated' with no RELEASE-NEEDS-A-REASON guard, and "
        "the reason is written to board.log and to nothing the next reader "
        "opens. Measured: the S22 claim/release/claim livelock reproduces -- "
        "monitor gives 0,0,3 and the item stays put; fleetkit gives 0,0,0 and "
        "hands the item straight back to the same worker.",
    ),
    "cmd_sweep": (
        "defect",
        "_PREFIX = '' is never assigned in the package, so the liveness test "
        "is always false, `live` is always empty, and every W-* claim reads as "
        "orphaned. Measured with a synthetic schtasks CSV: monitor frees only "
        "the Ready worker, fleetkit frees the Running one too. KNOWN_TRAPS.md "
        "entry 1, reproduced by the kit that ships it. config.py:78-83 "
        "validates task_prefix as non-empty for exactly this reason and "
        "board.py never reads config.",
    ),
    "main": (
        "stale",
        "No reassign verb (S35's exit) and no reconcile verb, and no reason "
        "gate on release.",
    ),
}


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _functions(source: str) -> dict[str, str]:
    """Top-level function name -> normalised source text."""
    tree = ast.parse(source)
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = "\n".join(lines[node.lineno - 1 : node.end_lineno])
            out[node.name] = textwrap.dedent(body).strip()
    return out


def _both() -> tuple[dict[str, str], dict[str, str]]:
    if not os.path.exists(FLEETKIT_BOARD):
        pytest.skip("fleetkit is not on this tree")
    return _functions(_read(MONITOR_BOARD)), _functions(_read(FLEETKIT_BOARD))


def test_every_divergence_is_declared():
    """The check itself: differ, or be declared.

    NOT "the two files must be identical" -- that would be red forever, which
    S39 records as the same thing as no gate.
    """
    mon, kit = _both()
    shared = sorted(set(mon) & set(kit))
    assert shared, "no shared functions -- the extraction relationship is gone"

    undeclared = [n for n in shared if mon[n] != kit[n] and n not in DECLARED]

    assert not undeclared, (
        "these functions drifted and nothing says why:\n  "
        + "\n  ".join(undeclared)
        + "\n\nEither port the change into fleetkit, or add an entry to "
        "DECLARED with a reason. A divergence nobody wrote down is how this "
        "fork reached the state S40 was filed about."
    )


def test_declared_entries_still_describe_a_real_divergence():
    """The other direction: a stale DECLARED entry is a lie of its own.

    When somebody finally ports a fix, its entry must be removed -- otherwise
    the table drifts into describing differences that no longer exist, and the
    next reader trusts it.
    """
    mon, kit = _both()
    shared = set(mon) & set(kit)

    resolved = [
        n for n in DECLARED
        if n in shared and mon[n] == kit[n] and n not in GLOBAL_ONLY
    ]

    assert not resolved, (
        "these are declared as divergent but are now identical:\n  "
        + "\n  ".join(sorted(resolved))
        + "\n\nDelete their DECLARED entries."
    )


def test_declared_names_all_exist_in_both_files():
    """A DECLARED entry for a function that is not in both files is dead text."""
    mon, kit = _both()
    shared = set(mon) & set(kit)

    orphans = sorted(n for n in DECLARED if n not in shared)

    assert not orphans, (
        "DECLARED names functions that are not in both files: %s" % orphans
    )


def test_every_declared_entry_has_a_verdict_and_a_reason():
    for name, entry in DECLARED.items():
        verdict, why = entry
        assert verdict in {"extraction", "stale", "defect"}, (name, verdict)
        assert len(why) > 40, f"{name}: a reason this short is not a reason"


def test_the_measured_divergence_count_is_pinned():
    """Requirement 1's number, kept honest.

    If this fails the fork moved -- in either direction -- and RUN_STATE's
    measurement needs re-running rather than the number being edited to match.
    """
    mon, kit = _both()
    shared = set(mon) & set(kit)
    divergent = {n for n in shared if mon[n] != kit[n]}

    assert len(shared) == 18, f"shared function count moved: {len(shared)}"
    assert len(divergent) == 8, (
        f"divergent-by-source count moved: {len(divergent)}. This counts only "
        "SOURCE differences. The behavioural total is 10: stale_lanes and "
        "territories_busy are byte-identical and diverge through the "
        "LANE_OWNER global, which no text comparison can see."
    )
    assert len(divergent | GLOBAL_ONLY) == 10
    assert set(DECLARED) == divergent | GLOBAL_ONLY, (
        "DECLARED must name exactly the divergences, no more and no fewer"
    )


def test_the_two_globals_that_diverge_without_a_source_difference():
    """The finding this whole file exists for.

    `stale_lanes` and `territories_busy` are byte-identical in both files and
    still give different answers. Any drift check that compares only source
    text will score them 'same' forever -- including this one, which is why the
    fact is asserted here rather than left to be rediscovered.
    """
    mon, kit = _both()

    assert mon["stale_lanes"] == kit["stale_lanes"], (
        "stale_lanes source diverged; the LANE_OWNER note below may be stale"
    )
    assert mon["territories_busy"] == kit["territories_busy"]

    kit_src = _read(FLEETKIT_BOARD)
    assert "LANE_OWNER = {}" in kit_src, (
        "fleetkit's LANE_OWNER is no longer the empty literal -- if it is now "
        "populated, re-measure: stale_lanes and territories_busy may have "
        "stopped diverging, and their DECLARED entries would need removing."
    )


def test_the_false_docstring_is_still_there_and_still_false():
    """Requirement 3, as far as this territory can carry it.

    The fix belongs to whoever holds the `fleetkit` territory. What monitor can
    do is refuse to let the claim be forgotten: fleetkit says LANE_OWNER is
    "Filled from fleet.json at import", and it is not -- there is no
    assignment anywhere in the package, `fleet.json` exists nowhere in the
    repo, `board.py` imports config and never references it, and
    FleetConfig.lanes is a List[str] which cannot express a lane->owner map.
    False twice over: the mechanism does not exist and the data source could
    not supply it.

    This test goes red when somebody fixes it, which is the point -- at that
    moment this test and the DECLARED entries are what need updating.
    """
    kit_src = _read(FLEETKIT_BOARD)

    assert "Filled from fleet.json at import" in kit_src, (
        "the docstring changed -- if LANE_OWNER is now really populated, "
        "delete this test and re-measure the two functions that diverge "
        "through it"
    )
    body = kit_src.split("LANE_OWNER = {}")[0]
    assert "LANE_OWNER" not in body.split("#:")[0], "sanity: no earlier binding"
    after = kit_src.split("LANE_OWNER = {}", 1)[1]
    for mutation in ("LANE_OWNER =", "LANE_OWNER.update", "LANE_OWNER.setdefault"):
        assert mutation not in after, f"LANE_OWNER is now written via {mutation}"


# --------------------------------------------------------------------------
# Requirement 4: the check must actually go red when the fork drifts.
#
# The tests above read the two real files, so they cannot demonstrate a red
# without editing them. These drive the comparison logic directly with
# synthetic sources -- a check nobody has seen fail is a check nobody has
# seen work, and this repo has written that lesson down more than once.
# --------------------------------------------------------------------------

_MON = "def candidates():\n    return 1\ndef utc():\n    return 2\n"


def _undeclared(mon_src: str, kit_src: str, declared: set[str]) -> list[str]:
    """The predicate `test_every_divergence_is_declared` applies."""
    mon, kit = _functions(mon_src), _functions(kit_src)
    shared = sorted(set(mon) & set(kit))
    return [n for n in shared if mon[n] != kit[n] and n not in declared]


def test_a_new_undeclared_divergence_is_red():
    """monitor gains a criterion change, fleetkit does not follow, nobody
    declares it -- the S40 event, and it must fail."""
    kit = "def candidates():\n    return 1\ndef utc():\n    return 999\n"

    assert _undeclared(_MON, kit, set()) == ["utc"]


def test_the_same_divergence_declared_is_green():
    """...and one line with a reason clears it. That is the whole bargain:
    track it, or say why not."""
    kit = "def candidates():\n    return 1\ndef utc():\n    return 999\n"

    assert _undeclared(_MON, kit, {"utc"}) == []


def test_an_identical_fork_is_green():
    """The companion green: a checker that reds on everything is no checker."""
    assert _undeclared(_MON, _MON, set()) == []


def test_a_function_only_one_side_has_is_not_a_divergence():
    """Ported-vs-not is the module-level question fleetkit's README already
    answers. This check is about functions present in BOTH drifting apart."""
    kit = "def candidates():\n    return 1\n"

    assert _undeclared(_MON, kit, set()) == []


def test_line_ending_differences_alone_are_not_a_divergence():
    """monitor/board.py is CRLF and the fleetkit copy is LF. A raw diff calls
    that 714 changed lines; without normalising, this check would be 100%
    false-positive on its first run."""
    assert _undeclared(_MON, _MON.replace("\n", "\r\n"), set()) == []
