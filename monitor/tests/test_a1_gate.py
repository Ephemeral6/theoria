"""S26: the Phase 1 gate must be able to decide.

`probe_a1_state` computed both halves of its criterion, formatted them into its
`detail` string, and then returned `partial` unconditionally. The evidence never
reached the verdict, so the gate could neither open nor close -- and a gate that
cannot close is a gate that gets stepped over. It was: Theoria.md 305 makes an
all-green Phase 1 the precondition for spending game money, and money was spent
across this one at 9/16.

Written before the fix, per the ticket. Each case builds the world on purpose;
the green companions exist because a probe hardwired to `risk` would satisfy
every red assertion while being exactly as useless.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scan                                                     # noqa: E402


def _tree(tmp_path, monkeypatch, bridge, consumed):
    """A throwaway repo with either half of the A1 bridge present or absent."""
    root = tmp_path / "repo"
    interop = root / "engine-rig" / "interop"
    interop.mkdir(parents=True)
    if bridge:
        (interop / "certificate_export.py").write_text(
            "def export_certificate():\n    pass\n", encoding="utf-8")
    # A consumer is source under theory-compiler (not under runs/) naming the
    # schema id both sides stamp, or the interop directory it lives in.
    src = root / "theory-compiler" / "src"
    src.mkdir(parents=True)
    (src / "compile.py").write_text(
        'SCHEMA = "lp_potential/pagoda_certificate@1"\n' if consumed
        else "def compile_books():\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(scan, "ROOT", str(root))
    return root


# ------------------------------------------------------- the three verdicts

def test_both_halves_connected_is_green(tmp_path, monkeypatch):
    """The negative sample's positive twin: a tree that must be allowed through.

    Without this, the fix could be `return risk` and every red test would pass.
    """
    _tree(tmp_path, monkeypatch, bridge=True, consumed=True)
    r = scan.probe_a1_state()
    assert r["status"] == "green", r


def test_only_the_export_side_is_partial(tmp_path, monkeypatch):
    """Half connected is the state the old code always claimed, for once truly."""
    _tree(tmp_path, monkeypatch, bridge=True, consumed=False)
    r = scan.probe_a1_state()
    assert r["status"] == "partial", r


def test_only_the_consumer_side_is_partial(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch, bridge=False, consumed=True)
    r = scan.probe_a1_state()
    assert r["status"] == "partial", r


def test_neither_half_is_risk(tmp_path, monkeypatch):
    """Nothing built at all must not read the same as half built."""
    _tree(tmp_path, monkeypatch, bridge=False, consumed=False)
    r = scan.probe_a1_state()
    assert r["status"] == "risk", r


# ---------------------------------------------------------- the negative sample
#
# Item 4 of the ticket, stated as one assertion rather than four: the verdict
# must be a function of the tree. A probe whose output does not vary with its
# input is the defect being fixed, and it is invisible in any single-case test.

def test_the_verdict_varies_with_the_tree(tmp_path, monkeypatch):
    seen = {}
    for bridge in (True, False):
        for consumed in (True, False):
            _tree(tmp_path / ("b%sc%s" % (bridge, consumed)), monkeypatch,
                  bridge=bridge, consumed=consumed)
            seen[(bridge, consumed)] = scan.probe_a1_state()["status"]
    assert len(set(seen.values())) == 3, (
        "a gate that returns one verdict for every world is the bug: %s" % seen)
    assert seen[(True, True)] == "green"
    assert seen[(False, False)] == "risk"


def test_the_detail_still_names_which_half_is_missing(tmp_path, monkeypatch):
    """The old detail string was the only useful thing here; keep it."""
    _tree(tmp_path, monkeypatch, bridge=True, consumed=False)
    d = scan.probe_a1_state()["detail"]
    assert "未接" in d, d
    _tree(tmp_path / "two", monkeypatch, bridge=False, consumed=True)
    d = scan.probe_a1_state()["detail"]
    assert "未建" in d, d


# ------------------------------------------- the criterion has to mean something
#
# Making the evidence decide is only half the fix. The old `consumed` test was
# the bare word "certificate" anywhere under theory-compiler, and the Lean
# proofs say it in prose -- "the certificate's pattern: at(b1,c11)". A gate that
# opens on a word in a comment is worse than one that never opens, because it
# opens by accident and 0.31 of the paper's weight sits behind it.

def test_a_comment_mentioning_certificates_does_not_open_the_gate(tmp_path,
                                                                  monkeypatch):
    root = _tree(tmp_path, monkeypatch, bridge=True, consumed=False)
    lean = root / "theory-compiler" / "proofs"
    lean.mkdir(parents=True)
    (lean / "Deadlock.lean").write_text(
        "/-- The certificate's pattern: at(b1,c11) -/\n", encoding="utf-8")
    r = scan.probe_a1_state()
    assert r["status"] == "partial", (
        "prose in a proof comment is not a consumer: %s" % r)


def test_an_artefact_under_runs_is_not_a_live_consumer(tmp_path, monkeypatch):
    """A certificate quoted in a past run log says something happened once."""
    root = _tree(tmp_path, monkeypatch, bridge=True, consumed=False)
    runs = root / "theory-compiler" / "runs" / "20260728T000000Z-old"
    runs.mkdir(parents=True)
    (runs / "gen_forms.py").write_text(
        'SCHEMA = "lp_potential/pagoda_certificate@1"\n', encoding="utf-8")
    r = scan.probe_a1_state()
    assert r["status"] == "partial", (
        "an artefact under runs/ is not the bridge being wired up now: %s" % r)


def test_the_real_repository_still_reads_green(tmp_path):
    """Guard against tightening the criterion until it stops matching reality.

    theory-compiler/src/theory_compiler/certificate.py really does read the
    export, so the honest verdict on this tree is green -- and the old code
    never said so.
    """
    r = scan.probe_a1_state()
    assert r["status"] == "green", r
