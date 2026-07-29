"""The incision, asserted at every place the source claims it is asserted.

Two sentences in P-18's code named this file before it existed, and `STATUS.md`
recorded both as false-at-the-time:

* `certify_abl.py:33` — *"`tests/test_incision.py` asserts that nothing calls it."*
* `downgrade.py:22` — *"`downgrade_text` asserts it, and `tests/test_incision.py`
  asserts it again on every generated file."*

Both are made true here.  The second is worth stating precisely: `downgrade_text`
checks the transform *as it runs*, on whatever text it is handed; this file
checks the **files that shipped**, which is a different claim and the one a
reader of `theory/` actually depends on.
"""

from __future__ import annotations

import ast
import os

import pytest

from ablcore import certify_abl, compile_abl, downgrade, playbook, surprise

ARM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEORY = os.path.join(ARM, "theory")

#: Everything in the arm that could call the cut layer. `certify_abl.py` is
#: excluded because it *defines* it, and `tests/` because asserting that it
#: raises requires calling it.
def _arm_sources():
    for root, dirs, files in os.walk(ARM):
        dirs[:] = [d for d in dirs
                   if d not in {"__pycache__", "tests", "artifacts", "runs"}]
        for name in sorted(files):
            if name.endswith(".py") and name != "certify_abl.py":
                yield os.path.join(root, name)


# ------------------------------------------------------ C-2: no expensive layer

def test_the_expensive_layer_exists_and_refuses():
    """The seam is left visible in the source on purpose; it must still bite."""
    with pytest.raises(certify_abl.ObligationCut):
        certify_abl.expensive("anything", "at all")


def test_nothing_in_this_arm_calls_the_expensive_layer():
    """`certify_abl.py:33`'s sentence, executed.

    Parsed rather than grepped: a grep for `expensive(` would miss
    `getattr(certify_abl, "expensive")()` and would trip over the word appearing
    in a docstring. The AST is what the interpreter sees.
    """
    callers = []
    for path in _arm_sources():
        with open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (func.attr if isinstance(func, ast.Attribute)
                    else getattr(func, "id", None))
            if name == "expensive":
                callers.append("%s:%d" % (os.path.relpath(path, ARM), node.lineno))
    assert callers == [], (
        "the ablated arm calls its own cut layer at %s. There is nothing behind "
        "that seam -- it raises." % callers)


def test_the_cheap_layer_keeps_the_full_arm_vocabulary():
    """C-2 removed a layer, not a vocabulary. If the anomaly kinds drifted, a
    difference in the arms would be attributable to this file instead of to the
    cut."""
    assert certify_abl.ANOMALY_KINDS == (
        "render_mismatch", "contested_pixel", "unowned_pixel",
        "goal_mismatch", "ambiguous_transition")
    assert set(certify_abl.ANOMALY_TO_SURPRISE) == set(certify_abl.ANOMALY_KINDS)
    for kind in certify_abl.ANOMALY_TO_SURPRISE.values():
        assert kind in surprise.KINDS


# ------------------------------------------- C-1: no Lean form is ever emitted

def test_no_lean_form_is_emitted_and_the_omission_is_named():
    assert compile_abl.OMITTED_FORM == "theory.lean"
    for world in os.listdir(os.path.join(ARM, "artifacts")):
        directory = os.path.join(ARM, "artifacts", world)
        if not os.path.isdir(directory) or world.startswith("_"):
            continue
        assert not os.path.exists(os.path.join(directory, "theory.lean")), world
    assert not [p for p in _arm_sources() if p.endswith(".lean")]


# ------------------------------------- C-5: the shipped files carry no standing

@pytest.mark.parametrize("name", sorted(
    f for f in os.listdir(THEORY) if f.endswith(".dsl")))
def test_no_shipped_manual_carries_a_proof_marker(name):
    """`downgrade.py:22`'s second half: on every generated file, not on the
    transform's own input."""
    with open(os.path.join(THEORY, name), encoding="utf-8") as handle:
        text = handle.read()
    for marker in ("[status: proven]", "[proof: lean]", "[admissible: lean]"):
        assert marker not in text, "%s still carries %s" % (name, marker)
    survivors = [line.strip() for line in text.splitlines()
                 if line.strip().startswith("theorem ")]
    assert survivors == [], "%s still declares %s" % (name, survivors)


def test_the_parser_agrees_with_the_grep():
    """The file the arm runs on is the AST, not the text.

    `build_theory.verify_ast` is the check; this asserts it is actually clean on
    what shipped, so a cut that satisfied a grep and not the parser would fail
    here rather than three steps later inside the driver.
    """
    import build_theory

    report = build_theory.verify_ast()
    assert report["clean"], report["failures"]
    for name, entry in report["per_manual"].items():
        assert entry["theorems"] == 0, name
        assert entry["invariant_statuses"] == ["empirical"], (name, entry)


def test_the_downgrade_refuses_to_touch_anything_outside_laws():
    """`downgrade_text`'s own assertion, watched refusing.

    The transform is handed a manual whose `laws:` section is the last one, so a
    bug that ran past the section boundary would rewrite the file's tail. The
    assertion inside `downgrade_text` is what catches that, and a check nobody
    has seen fire is a check nobody has tested.
    """
    text = ("rules:\n  rule r1 [status: proven]\n"
            "laws:\n  invariant i1 x = 1 [status: proven]\n"
            "  theorem t1 \"because\"\n")
    result, report = downgrade.downgrade_text(text)
    assert report["invariants_demoted"] == ["i1"]
    assert [t["name"] for t in report["theorems_deleted"]] == ["t1"]
    # the `rules:` line above `laws:` keeps its marker: it is not a law.
    assert "rule r1 [status: proven]" in result
    assert "invariant i1 x = 1 [status: empirical]" in result
    assert "theorem t1" not in result


def test_the_playbook_demotion_names_what_it_costs():
    """C-5 is bookkeeping for `order`/`heuristic` and is not bookkeeping for
    `prune`. If that distinction were ever lost, the report would stop saying
    that an unproved deadlock rule can discard a real solution."""
    text = ("order o1 [proof: lean]\n"
            "prune p1 => dead [proof: lean]\n"
            "prefer f1\n")
    result, report = playbook.demote_text(text)
    assert report["count"] == 2
    assert report["theorem_tier_entries_remaining"] == 0
    assert len(report["soundness_bearing"]) == 1
    assert "prune p1" in report["soundness_bearing"][0]
    costs = {d["form"]: d["costs"] for d in report["entries_demoted"]}
    assert "search soundness" in costs["prune"]
    assert costs["order"] == "standing only"
    assert "[proof: lean]" not in result


# ------------------------------------------ P-3 / shadow 4: seven kinds -> six

def test_proof_failure_is_impossible_by_construction_not_by_convention():
    bus = surprise.SurpriseBus(ablated=True)
    with pytest.raises(surprise.ImpossibleSurprise):
        bus.raise_("proof_failure", {"why": "there is no proof to fail"})
    assert len(bus) == 0, "a refused surprise must not land on the bus anyway"

    assert len(surprise.KINDS) == 7
    assert len(bus.kinds_available()) == 6
    assert set(surprise.KINDS) - set(bus.kinds_available()) == {"proof_failure"}

    full = surprise.SurpriseBus(ablated=False)
    assert len(full.kinds_available()) == 7, (
        "the un-ablated bus must keep all seven, or the 7->6 claim is measuring "
        "this module rather than the cut")
    full.raise_("proof_failure", {"why": "the full arm can have one"})
    assert len(full) == 1
