"""METRICS.md is generated; this keeps it from drifting from the code."""

import io
import os
import tempfile

from battery import docs


def test_committed_metrics_doc_matches_the_registry():
    with open(docs.TARGET, encoding="utf-8") as fh:
        committed = fh.read()
    assert committed == docs.render(), (
        "METRICS.md is stale. Regenerate with `python -m battery.docs`.")


def test_the_doc_is_regenerated_byte_identically(tmp_path):
    a = docs.write(str(tmp_path / "a.md"))
    b = docs.write(str(tmp_path / "b.md"))
    assert open(a, "rb").read() == open(b, "rb").read()


def test_every_metric_appears_in_the_doc():
    from battery.metrics import REGISTRY
    body = docs.render()
    for metric_id in REGISTRY:
        assert "`%s`" % metric_id in body


def test_predictions_file_is_present_and_names_every_family():
    """The pre-registration is part of the deliverable, not an optional extra."""
    path = os.path.join(os.path.dirname(docs.TARGET), "PREDICTIONS.md")
    with open(path, encoding="utf-8") as fh:
        body = fh.read()
    for family in ("Exploration", "Planning", "Economy", "Mechanism",
                   "Epistemic"):
        assert "## %s" % family in body
    assert "Seal declaration" in body, \
        "the pre-registration must state what its author had already seen"


def test_a_recompute_pointed_elsewhere_leaves_the_committed_docs_alone():
    """`--out` must mean `--out`.

    `REDUNDANCY.md` used to be written by `run_battery` to a fixed path, so
    every run of `tests/test_determinism.py` -- which drives the real pipeline
    over a six-run fixture -- quietly overwrote the committed audit document
    with a three-cluster version. The suite passed the whole time; the damage
    showed up as an unexplained dirty file in `git status`.
    """
    import battery.run_battery as rb

    before = io.open(docs.REDUNDANCY_TARGET, encoding="utf-8").read()
    with tempfile.TemporaryDirectory() as tmp:
        ledger = os.path.join(tmp, "ledger.jsonl")
        io.open(ledger, "w", encoding="utf-8", newline="\n").write("")
        try:
            rb.main(["--out", os.path.join(tmp, "artifacts"),
                     "--ledger", ledger, "--a0", "none"])
        except SystemExit:
            pass
        assert not os.path.exists(
            os.path.join(tmp, "artifacts", "REDUNDANCY.md"))
    assert io.open(docs.REDUNDANCY_TARGET, encoding="utf-8").read() == before
