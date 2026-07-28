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
