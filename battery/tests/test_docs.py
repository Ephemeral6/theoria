"""METRICS.md is generated; this keeps it from drifting from the code."""

import os

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
