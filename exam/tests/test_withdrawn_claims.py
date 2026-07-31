"""The withdrawn-claim scanner, in both directions.

A scanner is two claims -- it fires on the thing, and it does not fire on
everything -- and only the first one is usually tested.  D-EX-031's location
scanner failed the second on its first run (seven hits, all false, all ordinary
prose) and that is the failure mode this file exists to keep out.
"""

from __future__ import annotations

import os

from exam.tools import check_withdrawn_claims as cw

FIXTURE_HIT = (
    "This is a class (ii) item.\n"
    "Enumeration is out of reach and only invariant reasoning answers.\n"
    "So the item is scored on the reason.\n"
)

FIXTURE_ACQUITTED = (
    "This is a class (ii) item.\n"
    "The sentence 'only invariant reasoning answers' is withdrawn (D-EX-028).\n"
    "What survives is the naive-enumeration claim.\n"
)

FIXTURE_CLEAN = (
    "Naive enumeration over the full state cannot terminate here, so the item\n"
    "is scored on selecting a method that is not that one. An exhaustive walk\n"
    "of the relaxed graph settles it in 600 nodes.\n"
)


def _scan_text(tmp_path, text, name="sample.md"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    rel = os.path.relpath(str(path), cw.REPO).replace(os.sep, "/")
    return cw.scan([rel])


def test_it_fires_on_the_withdrawn_sentence(tmp_path):
    hits = _scan_text(tmp_path, FIXTURE_HIT)
    assert len(hits) == 1
    assert hits[0]["pattern"] == "only-invariant-en"


def test_a_record_of_the_withdrawal_is_not_a_hit(tmp_path):
    """DECISIONS.md and STATUS.md have to be able to quote what they withdrew."""
    assert _scan_text(tmp_path, FIXTURE_ACQUITTED) == []


def test_the_corrected_wording_is_not_a_hit(tmp_path):
    """`exhaustive` and `enumeration` are ordinary words in this territory.

    A pattern that fired on them would be switched off within a day, and the
    withdrawal would go back to being a matter of record only.
    """
    assert _scan_text(tmp_path, FIXTURE_CLEAN) == []


def test_the_tracked_tree_is_clean():
    """The gate itself, over every tracked exam file. This is the assertion."""
    hits = cw.scan()
    assert hits == [], "\n".join(
        "%s:%s [%s] %s" % (h["file"], h["line"], h["pattern"], h["text"])
        for h in hits)


def test_the_generated_matrix_artifact_is_covered():
    """The last place the withdrawn claim survived was a *generated* artefact.

    `class_meaning` in `confusion_matrix.py` is written into
    `artifacts/matrix/verdict_confusion.json`. Three cycles after D-EX-028 it
    still read "only an invariant can answer", and the decision log said
    otherwise -- which makes the artefact the version a reader quotes and the
    log the version nobody reads.
    """
    from exam.grading.confusion_matrix import verdict_matrix
    meaning = verdict_matrix(modes=("oracle",), include_real=False)
    text = meaning["class_meaning"]["large_unsolvable"]
    assert "only an invariant" not in text
    assert "naive" in text.lower()


def test_the_runs_archive_is_exempt_on_purpose():
    """A gate that demanded the provenance archive be rewritten would be asking
    for the record to be falsified, which is worse than the defect it closes."""
    assert cw.EXEMPT_PREFIXES == ("exam/runs/",)
    assert not any(p.startswith("exam/runs/") for p in cw._tracked_exam_files())
