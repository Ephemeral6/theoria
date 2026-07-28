"""Generated files stay generated, and two runs stay the same run.

Both are repository-wide requirements rather than this arm's preferences
(`CLAUDE.md`: 生成物禁止手改; determinism is a requirement, not a nicety), and
both are the kind of property that decays silently -- a hand-edit to a generated
manual and a wall clock in an artefact each look like nothing until somebody
tries to reproduce a number.
"""

from __future__ import annotations

import os

import pytest

import build_theory
import run_arm

ARM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEORY = os.path.join(ARM, "theory")


def test_theory_on_disk_is_a_fresh_cut_of_upstream():
    payload = build_theory.build(check=True)
    assert payload["clean"], payload["differences"]


def test_the_check_notices_a_hand_edit(tmp_path):
    """`--check` is the whole defence against an edited generated file, so it
    has to be shown catching one. The edit is made and undone here rather than
    trusted to a reviewer's eye."""
    target = os.path.join(THEORY, "a0_base.dsl")
    with open(target, encoding="utf-8") as handle:
        original = handle.read()
    try:
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(original + "\n# a hand edit\n")
        payload = build_theory.build(check=True)
        assert payload["clean"] is False
        assert any("a0_base.dsl" in line for line in payload["differences"])
        assert any("not hand-edited" in line for line in payload["differences"])
    finally:
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(original)
    assert build_theory.build(check=True)["clean"]


def test_the_check_notices_a_proof_marker_put_back():
    """And it must notice on both channels -- the byte diff and the parser --
    because the AST check is the one that matters and the byte diff is the one
    that is easy."""
    target = os.path.join(THEORY, "a0_base.dsl")
    with open(target, encoding="utf-8") as handle:
        original = handle.read()
    assert "[status: empirical]" in original
    try:
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(original.replace("[status: empirical]",
                                          "[status: proven]", 1))
        payload = build_theory.build(check=True)
        assert payload["clean"] is False
        assert any("differs from a fresh cut" in line
                   for line in payload["differences"])
        assert any("survived the cut" in line
                   for line in payload["differences"]), (
            "only the byte diff fired. The parser-level check is the one that "
            "makes the cut a property of the AST rather than of the text.")
    finally:
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(original)
    assert build_theory.build(check=True)["clean"]


def test_the_cut_counts_are_recorded_where_verify_can_read_them():
    summary = build_theory.build(check=True)["summary"]
    assert summary["manuals_cut"] == 4 and summary["playbooks_cut"] == 1
    assert summary["n_theorems_deleted"] == 4
    assert summary["n_invariants_demoted"] == 7
    assert summary["n_soundness_bearing"] == 1
    # DESIGN.md §6: four shadows, one blade -- shadows 1 and 2 are the same
    # count because they are the same cut.
    assert (summary["shadow_1_directed_probe_targets_removed"]
            == summary["shadow_2_entries_no_longer_re_provable"]
            == summary["n_theorems_deleted"])
    deleted = {t["theorem"] for t in summary["theorems_deleted"]}
    assert {"unsolvable_no_button", "right_room_locked"} <= deleted, (
        "the two exhibits' theorems are the point: one true impossibility "
        "claim and one false one, and the cut deletes both")


@pytest.mark.slow
def test_two_runs_produce_the_same_run():
    result = run_arm.determinism()
    assert result["deterministic"], result["differences"]
    assert result["n_files"] > 30
    # The exemptions are named, not silent.
    assert result["exempt_field"] == "ts"
    assert result["ledgers_compared_modulo_ts"]
    assert "__pycache__" in result["not_compared_because"]


@pytest.mark.slow
def test_the_ledger_differs_only_in_its_wall_clock():
    """The one exemption, checked rather than assumed.

    `proxy.ledger` stamps every record with `ts`, which is right in a record of
    an event. What would not be right is any *other* field drifting under cover
    of that exemption.
    """
    import json

    roots = [os.path.join(ARM, "artifacts", "_determinism", "run%d" % i)
             for i in (1, 2)]
    for root in roots:
        run_arm.run_world(run_arm.WORLD_BY_KEY["a0-base"], out_root=root)
    paths = [os.path.join(r, "a0-base", "episode.jsonl") for r in roots]

    raw = [open(p, encoding="utf-8").read() for p in paths]
    assert raw[0] != raw[1], (
        "the two ledgers are byte-identical, so this test is not testing "
        "anything -- either the clock stopped or the run was cached")

    lines = [run_arm._ledger_lines_modulo_ts(p) for p in paths]
    assert lines[0] == lines[1]
    stamps = [json.loads(l)["ts"] for l in open(paths[0], encoding="utf-8")
              if l.strip()]
    assert all(stamps), "every record must carry a stamp, or `ts` is not the "\
                        "field that differs"
