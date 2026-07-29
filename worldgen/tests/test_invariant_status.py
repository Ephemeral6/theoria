"""`holds` / `violated` / `unverified` is a partition, and it sinks to the bad news.

The V19 defect was not that the code was wrong about any invariant.  It was that
the schema had two states for a three-state world: `holds` was a boolean, an
unexercised claim had no value for it, and `.get("holds", True)` supplied one.
So the tests that matter here are about the *shape* of the classification rather
than about any particular world:

* every row lands in exactly one class, and the three classes reconstruct the
  input — a third class that some rows can slip past is the two-class scheme
  again with an extra name;
* the class a malformed or unrecognised row falls into is `unverified`, never
  `holds`.  The whole failure being repaired is a default that pointed at the
  good news;
* `invariants_all_hold` is the conjunction over `holds`, not the negation of
  `violated`;
* and the machine-read verdict is never more optimistic than the Markdown
  rendered from the same dict, which is the invariant across the whole repair:
  the human-readable half of `ground_truth` was honest before V19 and only the
  machine-read half lied.

`test_invariant_gate.py` is the other half — the same properties asserted
through the real command line and its process exit code.
"""

import pytest

from worldgen.core import truth
from worldgen.tests import support

HOLDS, VIOLATED, UNVERIFIED = truth.INV_HOLDS, truth.INV_VIOLATED, truth.INV_UNVERIFIED


# --- adversarial rows -------------------------------------------------------
#
# Hand-built rows rather than rows from a world, because the point is what the
# classifier does with shapes a world does not currently produce: a row from an
# older writer, a row that contradicts itself, a row with a status nobody
# defined.  Each is (row, expected class, why).

ROWS = [
    ({"name": "a", "status": HOLDS, "verified": True, "holds": True},
     HOLDS, "the only shape that may count as holding"),
    ({"name": "b", "status": VIOLATED, "verified": True, "holds": False},
     VIOLATED, "an ordinary violation"),
    ({"name": "c", "status": UNVERIFIED, "verified": False},
     UNVERIFIED, "an ordinary prose-only claim"),

    # The defect itself, in the two shapes it shipped in.
    ({"name": "d", "statement": "prose"},
     UNVERIFIED, "no status and no holds key at all — the pre-V19 row"),
    ({"name": "e", "verified": False, "note": "prose only"},
     UNVERIFIED, "a pre-V19 writer's unverified row, which had no status field"),

    # Rows that disagree with themselves. None of them may resolve to `holds`.
    ({"name": "f", "status": HOLDS, "verified": True},
     UNVERIFIED, "claims to hold but carries no holds key"),
    ({"name": "g", "status": HOLDS, "verified": False, "holds": True},
     UNVERIFIED, "claims to hold but was never verified"),
    ({"name": "h", "status": HOLDS, "verified": True, "holds": False},
     VIOLATED, "says holds and does not hold — believed on the pessimistic side"),
    ({"name": "i", "status": VIOLATED, "verified": False},
     VIOLATED, "an unverified row that nevertheless declares a violation"),

    # Unrecognised and truthy-but-wrong values.
    ({"name": "j", "status": "probably", "verified": True, "holds": True},
     UNVERIFIED, "a status nobody defined is not a licence to count it"),
    ({"name": "k", "status": HOLDS, "verified": 1, "holds": 1},
     UNVERIFIED, "truthy is not True — identity, so a stray 1 cannot pass"),
    ({"name": "l", "status": HOLDS, "verified": True, "holds": "yes"},
     UNVERIFIED, "a string is not True"),
    ({"name": "m"},
     UNVERIFIED, "an empty row"),
]


@pytest.mark.parametrize("row,expected,why", ROWS,
                         ids=[r[0]["name"] for r in ROWS])
def test_each_adversarial_row_lands_where_it_should(row, expected, why):
    status = truth.classify_invariants([row])
    landed = [k for k in truth.INV_STATUSES if status[k]]
    assert landed == [expected], "%s: %s -> %s" % (row["name"], why, landed)


def test_no_adversarial_row_is_ever_counted_as_holding_by_accident():
    """The single sentence this whole cell is about.

    Of the thirteen rows above, exactly one is well-formed enough to hold. If a
    future edit widens the `holds` branch, this fails before anything else does.
    """
    status = truth.classify_invariants([row for row, _e, _w in ROWS])
    assert status[HOLDS] == ["a"], status[HOLDS]


def test_the_three_classes_partition_the_input():
    """Total and disjoint, on the adversarial rows and not just the tidy ones."""
    rows = [row for row, _e, _w in ROWS]
    status = truth.classify_invariants(rows)
    landed = status[HOLDS] + status[VIOLATED] + status[UNVERIFIED]
    assert sorted(landed) == sorted(r["name"] for r in rows), (
        "a row escaped the partition, or was counted twice: %s" % status)
    assert len(landed) == len(set(landed)), "a row landed in two classes: %s" % status


def test_all_hold_is_not_merely_the_absence_of_violations():
    prose = {"name": "p", "statement": "prose", "verified": False,
             "status": UNVERIFIED}
    good = {"name": "q", "status": HOLDS, "verified": True, "holds": True}
    assert truth.all_invariants_hold([good]) is True
    assert truth.all_invariants_hold([good, prose]) is False, (
        "an unverified invariant did not count against `invariants_all_hold` — "
        "this is the V19 defect exactly")
    assert truth.all_invariants_hold([]) is True


def test_a_check_that_ran_on_nothing_is_unverified_not_holding():
    """The defect's other hiding place: a callable that never executed.

    `not violations` is vacuously true when there were no states to violate
    anything on, which is `.get("holds", True)` again — this time in a row that
    *has* a callable, where nobody would think to look. Reachable through
    `mutate.py`, which hands `check_invariants` an explicit state list.
    """
    world = support.world("t1-walk-maze")
    rows = {r["name"]: r for r in truth.check_invariants(world, [])}
    assert rows, "no invariants were produced at all"
    for name, row in rows.items():
        assert row["status"] == UNVERIFIED, (
            "%s reported %r on zero states" % (name, row["status"]))
        assert "holds" not in row, name
    assert truth.all_invariants_hold(rows.values()) is False


def test_the_same_invariants_do_verify_on_a_real_state_set():
    """The control for the test above: the rows are not permanently unverified,
    they are unverified *because there was no evidence*."""
    world = support.world("t1-walk-maze")
    rows = truth.check_invariants(world, support.reachable("t1-walk-maze"))
    assert truth.all_invariants_hold(rows) is True
    assert all(r["status"] == HOLDS for r in rows), rows


def test_rows_with_no_name_still_land_in_the_partition():
    """F10. The partition test above compares *names*, and a row with no name is
    invisible to it — two of them collapse to one `<unnamed>` entry under any
    set comparison. So the property that has to hold is the count, and it is
    enforced inside `classify_invariants` rather than only asserted here."""
    rows = [{"statement": "no name at all"},
            {"statement": "also no name"},
            {"name": "named", "status": HOLDS, "verified": True, "holds": True}]
    status = truth.classify_invariants(rows)
    total = sum(len(status[k]) for k in truth.INV_STATUSES)
    assert total == 3, status
    assert status[UNVERIFIED].count("<unnamed>") == 2, status
    assert status[HOLDS] == ["named"], status
    assert truth.all_invariants_hold(rows) is False


def test_duplicate_names_are_not_deduplicated_away():
    rows = [{"name": "same", "status": HOLDS, "verified": True, "holds": True},
            {"name": "same", "statement": "prose"}]
    status = truth.classify_invariants(rows)
    assert sum(len(status[k]) for k in truth.INV_STATUSES) == 2, status
    assert truth.all_invariants_hold(rows) is False


def test_the_conservation_check_is_itself_able_to_fail():
    """The negative control for the guard, not for the thing it guards.

    An earlier version of this test monkeypatched `classify_invariants` to
    truncate its input — which of course conserved the *truncated* input and
    never raised. The guard has to be reachable on its own to be testable at
    all, which is why it is a function.
    """
    lossy = {HOLDS: ["a"], VIOLATED: [], UNVERIFIED: []}
    with pytest.raises(ValueError, match="lost 1 of 2"):
        truth._conserving(lossy, 2)
    assert truth._conserving(lossy, 1) is lossy


def test_an_empty_table_still_partitions():
    status = truth.classify_invariants([])
    assert status == {HOLDS: [], VIOLATED: [], UNVERIFIED: []}


# --- against the real catalogue ---------------------------------------------

def _invariant_bullets(rendered):
    """The `* **name** — ...` lines under `## Invariants`, and nothing else.

    Deliberately structural. An earlier draft of this helper searched the whole
    document for the word "unverified" and matched the section's own summary
    line, which is the sort of near-miss that makes a test look green for the
    wrong reason in the other direction.
    """
    out, inside = [], False
    for line in rendered.splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Invariants"
            continue
        if inside and line.startswith("* **"):
            out.append(line)
    return out

# --- F1: a check that raises must not become a check that passed ------------
#
# `check_invariants` catches the exception, records it as a violation and
# breaks. The docstring spends a paragraph justifying that choice — and nothing
# pinned that the branch existed at all. Deleting the two `except` bodies down
# to a bare `continue` makes an invariant whose check raises on *every* state
# report `verified: True, holds: True, status: "holds"`, which is this cell's
# own sentence ("I could not check this" written as "this holds") rebuilt
# verbatim inside the function that was rewritten to prevent it. Two gate
# escapees, both silent.


def _one_invariant(monkeypatch, row):
    """Replace the whole invariant table with a single row."""
    monkeypatch.setattr(truth, "invariant_table", lambda _w: [dict(row)])


@pytest.mark.parametrize("seam", ["check", "edge_check"])
def test_a_check_that_always_raises_is_a_violation_not_a_pass(seam, monkeypatch):
    world = support.world("t1-walk-maze")
    calls = []

    def boom(*args):
        calls.append(args)
        raise RuntimeError("the check itself is broken")

    _one_invariant(monkeypatch, {"name": "always_raises",
                                 "statement": "injected", seam: boom})
    rows = truth.check_invariants(world, support.reachable("t1-walk-maze"))
    assert len(rows) == 1
    row = rows[0]
    assert calls, "the raising callable was never invoked"
    assert row["status"] == VIOLATED, (
        "a callable that raised on every input was reported as %r" % row["status"])
    assert row["holds"] is False, row
    assert row["violations"], row
    assert "error" in row["violations"][0], row["violations"]
    assert "RuntimeError" in row["violations"][0]["error"], row["violations"]
    assert truth.all_invariants_hold(rows) is False


@pytest.mark.parametrize("seam", ["check", "edge_check"])
def test_a_raising_check_still_reports_the_evidence_it_actually_gathered(seam,
                                                                        monkeypatch):
    """It broke on the first input, so the count is 1 — not the size of the
    input set it never got through."""
    world = support.world("t1-walk-maze")
    _one_invariant(monkeypatch, {"name": "always_raises", "statement": "injected",
                                 seam: lambda *_a: (_ for _ in ()).throw(
                                     RuntimeError("boom"))})
    row = truth.check_invariants(world, support.reachable("t1-walk-maze"))[0]
    key = "states_checked" if seam == "check" else "transitions_checked"
    assert row[key] == 1, (
        "%s reported %d after failing on the first input" % (key, row[key]))


# --- F2: the published evidence count must come from work actually done -----
#
# `states_checked` was written as `len(states)` *outside* the loop and
# `transitions_checked` from a counter that a slice could bypass, so seven
# mutants — `states[:1]`, `transitions(...)[:1]`, `[::2]`, `= 0`, and dropping
# the key entirely — left artefacts reporting evidence they had never
# collected. Stage 2 of this cell rests entirely on those numbers ("84 to 10616
# transitions, not a default"), and nothing asserted they were non-zero or real.


@pytest.mark.parametrize("seam,key", [("check", "states_checked"),
                                      ("edge_check", "transitions_checked")])
def test_the_published_count_equals_the_number_of_calls_made(seam, key):
    """Counted by the callable itself, which is the only witness that cannot be
    fooled by a slice in the loop header."""
    import types

    world = support.world("t1-walk-maze")
    states = support.reachable("t1-walk-maze")
    calls = []

    def counting(*args):
        calls.append(args)
        return True

    original = truth.invariant_table
    truth.invariant_table = lambda _w: [{"name": "counted", "statement": "x",
                                         seam: counting}]
    try:
        row = truth.check_invariants(world, states)[0]
    finally:
        truth.invariant_table = original
    assert isinstance(original, types.FunctionType)
    assert row[key] == len(calls), (
        "%s published %d and the callable was invoked %d times"
        % (key, row[key], len(calls)))
    assert row[key] > 0, "the count is zero, so nothing was measured"


@pytest.mark.parametrize("world_id", support.WORLD_IDS)
def test_every_verified_row_publishes_a_non_zero_evidence_count(world_id):
    """No world may ship a verified verdict without saying how much it rests on.

    This is the assertion `FLIPS.md`'s stage-2 argument needed and did not have.
    """
    rows = truth.check_invariants(support.world(world_id),
                                  support.reachable(world_id))
    for row in rows:
        if row["status"] == UNVERIFIED:
            continue
        counts = [row[k] for k in ("states_checked", "transitions_checked")
                  if k in row]
        assert counts, (
            "%s/%s claims a verdict and publishes no evidence count"
            % (world_id, row["name"]))
        assert all(c > 0 for c in counts), (
            "%s/%s claims a verdict on zero evidence: %s"
            % (world_id, row["name"], counts))


@pytest.mark.parametrize("world_id", support.WORLD_IDS)
def test_the_transition_count_matches_the_worlds_real_transition_count(world_id):
    """An independent recount, so a halved or sliced loop cannot agree with
    itself."""
    world = support.world(world_id)
    states = support.reachable(world_id)
    expected = sum(1 for _ in world.transitions(states))
    for row in truth.check_invariants(world, states):
        if "transitions_checked" in row and row["status"] == HOLDS:
            assert row["transitions_checked"] == expected, (
                "%s/%s swept %d of the world's %d transitions"
                % (world_id, row["name"], row["transitions_checked"], expected))


# --- the same shape, one section over ---------------------------------------
#
# V19's fourth task was to sweep the file for other defaults pointing at good
# news. `to_markdown` had one: `corr.get("agrees", True)`, so a `truth` dict
# with no rule-correspondence verdict rendered a page that read as agreement.
# The full judgement of every candidate is in
# `runs/*-V19-unverified-is-not-true/`.

def _skeleton(**over):
    blob = {"world_id": "w", "spec": {"families": []}, "grid": [2, 2],
            "actions": ["UP"], "palette": {}, "rules": [], "invariants": [],
            "invariant_status": {HOLDS: [], VIOLATED: [], UNVERIFIED: []},
            "invariants_all_hold": True,
            "frame_determines_state": {"injective": True},
            "solvability": {"solvable": True, "optimal_length": 1,
                            "optimal_plan": ["UP"]},
            "reversibility": {"rules": {}, "rules_re_witnessable": 0,
                              "rules_total": 0, "reversibility_score": 1.0,
                              "rules_single_witness": [],
                              "claim_disagreements": []},
            "rule_correspondence": {"agrees": True, "cascade": []}}
    blob.update(over)
    return blob


@pytest.mark.parametrize("blob,why", [
    (_skeleton(rule_correspondence={"cascade": []}),
     "the block is present but carries no verdict"),
    ({k: v for k, v in _skeleton().items() if k != "rule_correspondence"},
     "the block is absent entirely"),
])
def test_an_unmeasured_rule_correspondence_does_not_render_as_agreement(blob, why):
    rendered = truth.to_markdown(blob)
    assert "was not measured" in rendered, (
        "%s, and the page reads as if the rules agreed with the world" % why)


def test_a_measured_agreement_still_renders_without_the_caveat():
    """The fix must not make every page say "not measured" — that is the
    over-correction, and it would train a reader to skip the line."""
    rendered = truth.to_markdown(_skeleton())
    assert "was not measured" not in rendered
    assert "disagrees with the world" not in rendered


# --- F4: the Markdown layer, exercised on worlds that are not clean ---------
#
# Every one of the 165 invariant bullets in the shipped catalogue is `holds`;
# there are zero violated and zero unverified rows. So the branches that render
# **VIOLATED** and **unverified** were never executed by any test, and four
# mutants proved it: delete the `**VIOLATED**` literal, delete the
# `**unverified**` literal, hard-code the summary line to `true`, and drop the
# unverified bullet entirely — **all four green**. A rendering layer exercised
# only on inputs that cannot go wrong is not exercised.
#
# These render from injected rows instead. `_skeleton` supplies the rest of the
# `truth` dict so `to_markdown` runs end to end, exactly as `truth.write` calls
# it.

_UNVERIFIED_ROW = {"name": "prose_claim", "statement": "a sentence nobody ran",
                   "verified": False, "status": UNVERIFIED,
                   "note": "prose only — no callable check"}
_VIOLATED_ROW = {"name": "broken_claim", "statement": "false on some state",
                 "verified": True, "holds": False, "status": VIOLATED,
                 "states_checked": 12, "violations": [{"state": [0, 0]}]}
_HOLDS_ROW = {"name": "good_claim", "statement": "true everywhere",
              "verified": True, "holds": True, "status": HOLDS,
              "states_checked": 12}


def _rendered(rows):
    blob = _skeleton(invariants=list(rows),
                     invariant_status=truth.classify_invariants(rows),
                     invariants_all_hold=truth.all_invariants_hold(rows))
    return truth.to_markdown(blob)


def test_the_markdown_says_VIOLATED_when_an_invariant_is_violated():
    rendered = _rendered([_HOLDS_ROW, _VIOLATED_ROW])
    bullets = _invariant_bullets(rendered)
    assert len(bullets) == 2, bullets
    bad = [b for b in bullets if "broken_claim" in b]
    assert bad and "**VIOLATED**" in bad[0], bullets


def test_the_markdown_says_unverified_when_an_invariant_is_unverified():
    rendered = _rendered([_HOLDS_ROW, _UNVERIFIED_ROW])
    bullets = _invariant_bullets(rendered)
    assert len(bullets) == 2, (
        "an invariant vanished from the rendered page: %s" % bullets)
    bad = [b for b in bullets if "prose_claim" in b]
    assert bad and "**unverified**" in bad[0], bullets


@pytest.mark.parametrize("rows,expected", [
    ([_HOLDS_ROW], "1 hold, 0 violated, 0 unverified"),
    ([_HOLDS_ROW, _VIOLATED_ROW], "1 hold, 1 violated, 0 unverified"),
    ([_HOLDS_ROW, _UNVERIFIED_ROW], "1 hold, 0 violated, 1 unverified"),
    ([_VIOLATED_ROW, _UNVERIFIED_ROW], "0 hold, 1 violated, 1 unverified"),
])
def test_the_summary_line_counts_are_not_hardcoded(rows, expected):
    assert expected in _rendered(rows), _rendered(rows)


@pytest.mark.parametrize("rows,verdict", [
    ([_HOLDS_ROW], "`invariants_all_hold` is `true`"),
    ([_HOLDS_ROW, _VIOLATED_ROW], "`invariants_all_hold` is `false`"),
    ([_HOLDS_ROW, _UNVERIFIED_ROW], "`invariants_all_hold` is `false`"),
])
def test_the_markdown_prints_the_same_verdict_the_json_carries(rows, verdict):
    assert verdict in _rendered(rows), _rendered(rows)


def test_every_invariant_reaches_the_page():
    rows = [_HOLDS_ROW, _VIOLATED_ROW, _UNVERIFIED_ROW]
    bullets = _invariant_bullets(_rendered(rows))
    assert len(bullets) == 3, bullets
    for row in rows:
        assert any(row["name"] in b for b in bullets), (row["name"], bullets)


def test_the_markdown_and_the_json_use_one_classifier_not_two():
    """F3: `{verified: 1, holds: 1}` was `unverified` in the JSON and printed as
    `holds` on the page — two classifiers in one document, and the one a human
    reads was the more forgiving. That is this cell's thesis inverted."""
    row = {"name": "truthy", "statement": "verified and holds are the int 1",
           "verified": 1, "holds": 1, "status": HOLDS, "states_checked": 3}
    assert truth.classify_invariants([row])[UNVERIFIED] == ["truthy"]
    bullets = _invariant_bullets(_rendered([row]))
    assert len(bullets) == 1, bullets
    assert "**unverified**" in bullets[0], (
        "the page is kinder than the JSON about the same row: %s" % bullets[0])


def test_a_verified_row_with_no_evidence_count_is_flagged_on_the_page():
    """The old fallback printed `checked on no states: holds`, which reads as a
    rendering quirk rather than as a missing measurement."""
    row = {"name": "countless", "statement": "verified, count dropped",
           "verified": True, "holds": True, "status": HOLDS}
    bullets = _invariant_bullets(_rendered([row]))
    assert "unrecorded amount of evidence" in bullets[0], bullets


@pytest.mark.parametrize("world_id", support.WORLD_IDS)
def test_every_shipped_invariant_row_carries_an_explicit_status(world_id):
    """No row may rely on a default for its verdict, which is the failure mode."""
    rows = truth.check_invariants(support.world(world_id),
                                  support.reachable(world_id))
    assert rows, world_id
    for row in rows:
        assert row.get("status") in truth.INV_STATUSES, (
            "%s/%s has no explicit status" % (world_id, row.get("name")))
        if row["status"] == UNVERIFIED:
            assert "holds" not in row, (
                "%s/%s is unverified but carries a `holds` key, which is exactly "
                "the ambiguity V19 removed" % (world_id, row["name"]))
        else:
            assert isinstance(row.get("holds"), bool), (row, world_id)


@pytest.mark.parametrize("world_id", support.WORLD_IDS)
def test_the_json_verdict_is_never_kinder_than_the_markdown(world_id):
    """The load-bearing property of the repair, checked on the rendered text.

    Before V19 the Markdown said `prose only, unverified` for thirteen worlds
    while the JSON in the same dict said `invariants_all_hold: true`. The
    direction of the asymmetry is the whole point — a reader audits the
    Markdown and a gate reads the JSON — so it is asserted as an implication,
    not as an equality.
    """
    blob = truth.ground_truth(support.world(world_id), diagnose=False)
    bullets = _invariant_bullets(truth.to_markdown(blob))
    assert len(bullets) == len(blob["invariants"]), (
        "%s: the Markdown renders %d invariants and the JSON carries %d — a "
        "claim is visible to one reader and not the other"
        % (world_id, len(bullets), len(blob["invariants"])))
    bad = [b for b in bullets if "**unverified**" in b or "**VIOLATED**" in b]
    if bad:
        assert blob["invariants_all_hold"] is False, (
            "%s: the Markdown reports %d unverified or violated invariant(s) and "
            "the JSON still says every invariant holds:\n%s"
            % (world_id, len(bad), "\n".join(bad)))
