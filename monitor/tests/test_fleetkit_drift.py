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
constructible input. And TWO of the divergent functions were byte-identical
source (`stale_lanes`, `territories_busy`): they diverged through a module
global. Reading the two files side by side scores them "same". That is why this
had to be a check and not a review.

WHERE IT STANDS AFTER S42 (fleetkit territory, branch
`agent/s42-fleetkit-three-lies`). Three of the defects below are fixed in
fleetkit and their entries here have moved or gone, which is this file working
as designed rather than a regression:

  * `cmd_sweep` reads `task_prefix` from `fleet.json` instead of an unassigned
    `_PREFIX = ""`, and refuses (exit 3) when it cannot read one. Its entry
    survives as `stale`, not `defect`.
  * `LANE_OWNER` and `stale_lanes` are deleted, so lane OWNERSHIP is gone from
    fleetkit and lane-tagged items are listed and claimable by anybody.
    `stale_lanes` is no longer a shared function and its entry is deleted; the
    shared count is therefore 17, not 18.
  * `cmd_list` gained a `withheld` section, so no item on the board can be
    absent from the output any more.

`territories_busy` is still the byte-identical-yet-divergent case, now through
`meta` alone rather than through `meta` and `LANE_OWNER`.

WHY "DELIBERATE SIMPLIFICATION" IS NOT AVAILABLE AS AN ANSWER. The fork base
had exactly 18 top-level functions and fleetkit has exactly those 18 -- nothing
was dropped on purpose. The 18 functions monitor has and fleetkit lacks all
landed AFTER the fork (S21, S27, S28, S29, S34, S35, S35a; 7 commits against
fleetkit's 1). So the divergence is not a simplification, it is a stale
snapshot, and several of its consequences were outright defects:

  * `_PREFIX = ""` was never assigned, so fleetkit's `cmd_sweep` judged every
    worker dead and freed LIVE claims -- `fleetkit/KNOWN_TRAPS.md` entry 1 word
    for word, latent in the kit that ships the warning. (Fixed by S42.)
  * `LANE_OWNER = {}` made any item carrying a `lane:` field invisible to
    `list` and unclaimable by a plain claim, with no exit at all. (Fixed by
    S42, by deleting lane ownership rather than inventing a data source for
    it.)
  * `meta()`'s regex uses `\\s*` where monitor uses `[ \\t]*`, so an empty front
    matter field silently takes its value from the NEXT LINE. **Still open.**

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
#: Those whose source is BYTE-IDENTICAL and which diverge anyway, through a
#: module-level difference no text comparison can see. They are declared like
#: the rest, but exempted from
#: `test_declared_entries_still_describe_a_real_divergence`, which compares
#: source: by construction their source already matches, so that test would
#: demand their removal and delete the record of the subtlest finding here.
#:
#: S40 measured two. `stale_lanes` diverged through `LANE_OWNER`, and S42
#: deleted both from fleetkit, so it is no longer a shared function at all.
#: `territories_busy` remains: identical source, divergent behaviour, through
#: `meta`.
GLOBAL_ONLY: frozenset[str] = frozenset({"territories_busy"})

DECLARED: dict[str, tuple[str, str]] = {
    "heartbeat_age": (
        "stale",
        "S28 moved monitor to heartbeat_evidence, preferring the untracked "
        "ops-status/<a>.lock over the tracked .json. Measured: .json 3600s old "
        "with a fresh .lock gives monitor 0, fleetkit 60 -- which flips "
        "stale_lanes at STALE_MIN=45.",
    ),
    # `stale_lanes` was here, verdict `defect`: byte-identical source that
    # could only ever return set(), because the LANE_OWNER it iterated was
    # never assigned. S42 deleted LANE_OWNER and stale_lanes from fleetkit, so
    # the function is not shared any more and the entry is gone rather than
    # left behind. See `test_lane_ownership_is_gone_from_fleetkit` below, which
    # is what remains watching that decision.
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
        "{'deps:': X}, so a DIFFERENT item is excluded from candidates(). "
        "After S42 this is the only remaining case of identical source with "
        "divergent behaviour, and the one any side-by-side read still misses.",
    ),
    "candidates": (
        "stale",
        "Missing S34's `if iid in ready: continue`, so fleetkit re-offers "
        "delivered work whenever items/X.md and done/X.*.md both exist -- the "
        "ordinary post-merge state. Since S42 it also diverges deliberately: "
        "fleetkit has no lane reservation (a lane narrows a worker, it never "
        "widens one, so lane-tagged items are ordinary work), and its "
        "spend: api guard is unconditional where monitor's is written "
        "`not lane and ...`. Do NOT close this one by copying monitor.",
    ),
    "cmd_list": (
        "stale",
        "Missing S35's unreachable section, and the sections do not "
        "correspond: monitor prints reserved / territory-blocked / "
        "unreachable, fleetkit prints one `withheld` section with a reason per "
        "item. S42 closed the part that mattered -- the S28 incident was 11 "
        "items on the board and 8 mentioned nowhere, and fleetkit now names "
        "every item in items/ under exactly one heading, printing "
        "'reason unknown' rather than omitting anything it cannot explain.",
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
        "stale",
        "S40 measured this as a defect: _PREFIX = '' was never assigned, so "
        "the liveness test was always false, `live` always empty, and every "
        "W-* claim read as orphaned -- with a synthetic schtasks CSV, monitor "
        "freed only the Ready worker and fleetkit freed the Running one too. "
        "S42 fixed it, and the remaining divergence is of three other kinds. "
        "EXTRACTION: fleetkit reads task_prefix from fleet.json where monitor "
        "hardcodes 'TheoriaAgent-', and decodes schtasks with "
        "locale.getpreferredencoding where monitor hardcodes gbk. FIX BEYOND "
        "monitor: fleetkit refuses to sweep (exit 3) when the prefix is "
        "unreadable or the schtasks query failed, because not knowing whether "
        "a worker is alive is not the same as knowing it is dead; monitor "
        "still treats a failed query as an empty task table. STALE: fleetkit "
        "lacks include_standing/standing_verdict and S34's `if iid in "
        "done_ids(): continue`, so it can still re-offer delivered work.",
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

    assert len(shared) == 17, (
        f"shared function count moved: {len(shared)}. S40 measured 18; S42 "
        "deleted stale_lanes from fleetkit along with the LANE_OWNER it "
        "iterated, which is a deliberate removal, not drift."
    )
    assert len(divergent) == 8, (
        f"divergent-by-source count moved: {len(divergent)}. This counts only "
        "SOURCE differences. The behavioural total is 9: territories_busy is "
        "byte-identical and diverges through meta, which no text comparison "
        "can see."
    )
    assert len(divergent | GLOBAL_ONLY) == 9
    assert set(DECLARED) == divergent | GLOBAL_ONLY, (
        "DECLARED must name exactly the divergences, no more and no fewer"
    )


def test_the_function_that_diverges_without_any_source_difference():
    """The finding this whole file exists for.

    `territories_busy` is byte-identical in both files and still gives
    different answers, through `meta`. Any drift check that compares only
    source text will score it 'same' forever -- including this one, which is
    why the fact is asserted here rather than left to be rediscovered.

    S40 found two such functions. `stale_lanes` was the other, and it diverged
    through `LANE_OWNER`; S42 deleted both from fleetkit, so one remains.
    """
    mon, kit = _both()

    assert mon["territories_busy"] == kit["territories_busy"], (
        "territories_busy source diverged; its DECLARED entry says the "
        "divergence is behavioural only, and that claim now needs re-measuring"
    )
    assert mon["meta"] != kit["meta"], (
        "meta stopped diverging, so territories_busy may have stopped too -- "
        "re-measure before trusting either entry"
    )


def test_lane_ownership_is_gone_from_fleetkit():
    """S40 requirement 3, now settled -- and still watched.

    S40 left a test here asserting that fleetkit's LANE_OWNER docstring was
    still present and still false ("Filled from fleet.json at import": no
    assignment anywhere in the package, no `fleet.json` in the repo, and
    `FleetConfig.lanes: List[str]` unable to express a lane->owner map at all).
    That test was designed to go red the moment somebody fixed it. S42 did, by
    deleting the claim rather than inventing a data source for it, so this is
    the same watchpost pointed at the new state.

    Coming back is not forbidden -- but it costs a data source. Anyone who
    reintroduces LANE_OWNER has to make `FleetConfig` able to express it, and
    this test is what will ask for that.
    """
    kit_src = _read(FLEETKIT_BOARD)

    assert "Filled from fleet.json at import" not in kit_src, (
        "the false docstring is back in fleetkit/board.py"
    )
    bound = [n.id
             for node in ast.parse(kit_src).body if isinstance(node, ast.Assign)
             for n in node.targets if isinstance(n, ast.Name)]
    assert "LANE_OWNER" not in bound, (
        "LANE_OWNER is back in fleetkit. If it is real this time, it needs a "
        "source: check that FleetConfig.lanes is no longer a List[str], "
        "re-measure stale_lanes and territories_busy, and update DECLARED."
    )
    assert "def stale_lanes" not in kit_src, (
        "stale_lanes is back. It existed only to unfreeze a lane whose owner "
        "had gone quiet; with no owners there is nothing to unfreeze, and "
        "reintroducing it means reintroducing ownership."
    )


def test_fleetkits_sweep_reads_a_prefix_instead_of_shipping_an_empty_one():
    """S40's most damaging finding, and the assertion that it stays fixed.

    `_PREFIX = ""` was a module global nothing in the package ever assigned, so
    the liveness test in `cmd_sweep` was constantly false and every `W-*` claim
    read as an orphan -- the board took work off workers that were still
    running. `config.py` validated `task_prefix` as non-empty for exactly this
    reason while `board.py` never opened config at all.

    This is asserted from monitor rather than left to fleetkit's own suite
    because the whole point of S40 is that fleetkit's suite did not look.
    """
    kit_src = _read(FLEETKIT_BOARD)

    # Assignments, not mentions: board.py's docstrings name `_PREFIX` when they
    # explain what went wrong, and a check that cannot tell a binding from a
    # sentence about a binding would forbid saying so.
    bound = [n.id
             for node in ast.parse(kit_src).body if isinstance(node, ast.Assign)
             for n in node.targets if isinstance(n, ast.Name)]
    assert "_PREFIX" not in bound, (
        "a module-level prefix literal is back in fleetkit/board.py. The "
        "prefix must be read from fleet.json at the point of use; a literal "
        "is KNOWN_TRAPS.md entry 1 with the fuse already lit."
    )
    assert "def task_prefix" in kit_src, "fleetkit lost its config-backed prefix"
    assert "SWEEP-REFUSED" in kit_src, (
        "fleetkit's sweep no longer refuses when it cannot read a prefix. Not "
        "knowing whether a worker is alive is a third answer, and freeing the "
        "claim is the one thing it must not mean."
    )


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
