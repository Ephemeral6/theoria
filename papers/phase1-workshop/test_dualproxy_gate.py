"""Negative control for verify_paper.py's check H.

A gate nobody has watched fail is a gate nobody has any reason to trust, so
every pin in this repository carries a control that makes it fail on purpose.
These are check H's.

H is unusual among the checks in this directory in that it has **two** modes
and they are not interchangeable, so the controls come in two families:

* the **model** side is a closed archive (`theoria-arm/evidence/
  model-proxy-401.jsonl`, one experiment, ended) and is checked for equality.
  `test_the_archive_is_an_equality_not_a_floor` is the control for that: a
  census that *grew* past the archive must still be red, because a number
  moving there is a change to the finding.
* the **environment** side is append-only and still growing (924/1009 across 24
  ledgers when S32 measured it, 2529/2620 across 37 two days later) and is
  checked as a floor. `test_the_monotone_direction_stays_green` is the control
  for that, and it is the most important test in this file: it exists to stop
  the next reader "fixing" the floor into an equality, which would turn the
  paper red the next time anyone plays a leg. A gate that reds on the
  experiment it is guarding is a gate that gets switched off.

The direction that matters is asymmetric and the tests say so: prose quoting
*less* traffic than the tree holds is a stale as-of figure, prose quoting
*more* is the paper overclaiming, and only the second is a failure.

Run:  python -m pytest papers/phase1-workshop/test_dualproxy_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_paper as vp  # noqa: E402


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

#: The census as the instrument reported it on 2026-08-02, in the shape
#: `count.census()` returns. Every test mutates a copy of this rather than the
#: repository, so the suite never depends on a ledger being played or not.
LIVE = {
    "env_proxy": {"requests_live_upstream": 2529, "requests_total": 2620,
                  "ledgers": 37},
    "model_proxy": {"model_calls": 65, "refused_401": 65, "succeeded": 0,
                    "bypass_attempts": 66, "records_total": 131},
}

#: The sentence the paper actually carries, wrapped and emphasised the way
#: `sections/09_preflight.md` wraps and emphasises it. The line break falls
#: between the number and the word it qualifies, which is exactly the shape a
#: per-line scanner cannot read -- so this string is a fixture, not a
#: paraphrase.
GAP_SENTENCE = (
    "a separate experiment in\n"
    "which the model CLI presented its own credential produced **66 "
    "`bypass_attempt`\n"
    "incidents and 65 consecutive 401s**, which is the sealing property "
    "working rather\n"
    "than a defect (`theoria-arm/evidence/model-proxy-401.jsonl`).\n"
)


def census(env=None, model=None) -> dict:
    """A copy of `LIVE` with the named fields overridden."""
    out = {k: dict(v) for k, v in LIVE.items()}
    out["env_proxy"].update(env or {})
    out["model_proxy"].update(model or {})
    return out


def scan(tmp_path: Path, body: str, cen=None):
    """Run check H's scanner over a one-section scratch tree."""
    (tmp_path / "09_body.md").write_text(body, encoding="utf-8")
    return vp.scan_dualproxy(sections=tmp_path, census=cen or census())


def tags(findings) -> list[str]:
    """The verdict word each finding leads with -- MISMATCH, OVERCLAIM, ..."""
    return [f.split()[0] for f in findings]


# --------------------------------------------------------------------------
# the instrument is real, and this suite is pointed at it
# --------------------------------------------------------------------------

def test_the_instrument_exists_where_the_check_looks_for_it():
    """If verify-lab moves, this must say so rather than quietly not run."""
    assert vp.DUALPROXY_COUNT.is_file(), vp.DUALPROXY_COUNT


def test_the_census_recomputes_and_has_the_fields_the_check_reads():
    """No network, no key, no model call -- and every field H names is there."""
    live = vp.dualproxy_census()
    for claim in vp.DUALPROXY_CLAIMS:
        assert isinstance(live[claim.field[0]][claim.field[1]], int), claim.tag


def test_the_fixture_agrees_with_the_instrument_on_the_closed_archive():
    """The archive is closed, so the fixture may be pinned to it exactly.

    The environment numbers deliberately are not compared: they grow, and a
    suite that asserted today's are tomorrow's is the bug this whole file is
    written against.
    """
    model = vp.dualproxy_census()["model_proxy"]
    for key in ("model_calls", "refused_401", "succeeded", "bypass_attempts"):
        assert model[key] == LIVE["model_proxy"][key], key


# --------------------------------------------------------------------------
# the unmutated case is green
# --------------------------------------------------------------------------

def test_the_live_paper_passes():
    ok, notes = vp.check_dualproxy()
    assert ok, "\n".join(notes)


def test_the_real_gap_sentence_passes(tmp_path):
    findings, observed, _ = scan(tmp_path, GAP_SENTENCE)
    assert findings == []
    assert sorted(v for *_, v, _ in observed) == [65, 66]


def test_the_flattening_reads_across_the_line_break(tmp_path):
    """The claim is split by a newline and wrapped in `**`; H must still see it.

    Both halves matter. A scanner that reads line by line finds `66` with no
    `bypass_attempt incidents` after it and reports the paper's central
    concession as absent -- a false red. One that strips markdown badly turns
    `bypass_attempt` into two words and does the same.
    """
    _, observed, missing = scan(tmp_path, GAP_SENTENCE)
    assert missing == [c for c in vp.DUALPROXY_CLAIMS if not c.required]
    lines = sorted(lineno for _, _, lineno, _, _ in observed)
    assert lines == [2, 3], lines


# --------------------------------------------------------------------------
# mutate the instrument, the paper goes red
# --------------------------------------------------------------------------

def test_a_mutated_census_makes_the_live_gate_red(monkeypatch):
    """The acceptance requirement, run against the paper as it stands.

    Nothing about the prose changes. The instrument is made to say something
    else, and the gate must notice -- otherwise H is confirming that a number
    in the paper matches a number in the paper.
    """
    monkeypatch.setattr(vp, "dualproxy_census",
                        lambda: census(model={"bypass_attempts": 999}))
    ok, notes = vp.check_dualproxy()
    assert not ok
    body = "\n".join(notes)
    assert "ARCHIVE" in body and "MISMATCH" in body


def test_a_mutated_401_count_makes_the_live_gate_red(monkeypatch):
    monkeypatch.setattr(
        vp, "dualproxy_census",
        lambda: census(model={"model_calls": 12, "refused_401": 12}))
    ok, notes = vp.check_dualproxy()
    assert not ok
    assert "MISMATCH" in "\n".join(notes)


def test_a_model_call_that_succeeded_makes_the_gate_red(monkeypatch):
    """Good news is still a failure here, and the message has to say so.

    `succeeded > 0` means the model proxy has completed a request against a
    real provider, which is the fact §9.3 says does not exist. The section has
    to be rewritten before the gate can go green -- which is the check working.
    """
    monkeypatch.setattr(vp, "dualproxy_census",
                        lambda: census(model={"succeeded": 1}))
    ok, notes = vp.check_dualproxy()
    assert not ok
    assert "SUCCEEDED" in "\n".join(notes)


def test_calls_that_were_not_all_refused_make_the_gate_red(monkeypatch):
    monkeypatch.setattr(vp, "dualproxy_census",
                        lambda: census(model={"refused_401": 64}))
    ok, notes = vp.check_dualproxy()
    assert not ok
    assert "NOT-ALL-401" in "\n".join(notes)


def test_an_instrument_that_will_not_run_is_a_failure_not_a_skip(monkeypatch):
    """"The census was unavailable" must never print the way "it agrees" does."""
    def boom():
        raise RuntimeError("no such tree")
    monkeypatch.setattr(vp, "dualproxy_census", boom)
    ok, notes = vp.check_dualproxy()
    assert not ok
    assert "NOCENSUS" in "\n".join(notes)


# --------------------------------------------------------------------------
# the concession cannot be deleted in silence
# --------------------------------------------------------------------------

def test_deleting_the_gap_sentence_fails(tmp_path):
    """V29's whole point. The numbers going missing is a failure, not a note."""
    findings, _, missing = scan(
        tmp_path, "The shell seals the arm behind two proxies.\n")
    assert tags(findings) == ["ABSENT", "ABSENT"]
    assert [c.tag for c in missing if c.required] == [
        "model bypass_attempt incidents", "model 401s"]


def test_an_empty_sections_tree_fails(tmp_path):
    """A walk over nothing must not report the way a clean walk does."""
    findings, observed, _ = vp.scan_dualproxy(sections=tmp_path, census=census())
    assert observed == []
    assert tags(findings) == ["ABSENT", "ABSENT"]


def test_the_abstract_is_not_exempt(tmp_path):
    """Checks E and F exempt it; H must not.

    Their exemption is about citation, and an abstract carries no paths. H is
    about a number agreeing with an instrument, and the section every reader
    reads is the last place an overclaim should go unchecked.
    """
    (tmp_path / "00_abstract.md").write_text(
        "The proxy answered 4000 requests through the environment proxy.\n",
        encoding="utf-8")
    findings, observed, _ = vp.scan_dualproxy(sections=tmp_path, census=census())
    assert observed and "OVERCLAIM" in tags(findings)


# --------------------------------------------------------------------------
# the two modes, and the direction that matters
# --------------------------------------------------------------------------

def test_the_overclaim_direction_fails(tmp_path):
    """Prose claiming more traffic than the tree holds: the failing direction."""
    findings, _, _ = scan(
        tmp_path,
        GAP_SENTENCE + "\nThe shell forwarded 9000 requests to a live upstream.\n")
    assert tags(findings) == ["OVERCLAIM"]
    assert "2529" in findings[0]


def test_the_monotone_direction_stays_green(tmp_path):
    """**Read this before making the env comparison an equality.**

    `theoria-arm/runs/` is append-only. A prose figure written when S32
    measured 924/1009 across 24 ledgers is not wrong once the tree reaches
    2529/2620 across 37 -- it is an as-of number that has been overtaken, which
    is what an as-of number does. An equality here would have gone red on the
    next leg anyone played, and this test is what stops it being introduced as
    a tidy-up.
    """
    body = (GAP_SENTENCE + "\nThe environment proxy forwarded 924 requests to "
            "a live upstream across\n24 ledgers, 1009 environment-proxy "
            "requests in all.\n")
    stale_prose_fresh_tree = scan(tmp_path, body)[0]
    assert stale_prose_fresh_tree == []

    # ... and it stays green as the tree keeps growing.
    grown = census(env={"requests_live_upstream": 99999,
                        "requests_total": 99999, "ledgers": 400})
    assert scan(tmp_path, body, grown)[0] == []


def test_an_env_number_equal_to_the_live_one_passes(tmp_path):
    findings, observed, _ = scan(
        tmp_path, GAP_SENTENCE + "\n37 ledgers were written.\n")
    assert findings == []
    assert 37 in [v for *_, v, _ in observed]


def test_the_archive_is_an_equality_not_a_floor(tmp_path):
    """The mirror image of the test above, and the reason both exist.

    Applying the environment side's floor to the model side would accept a
    census reporting *more* bypass incidents than the archive holds. The
    archive is one finished experiment; it does not grow, so a bigger number
    there means the evidence changed and the section has to be re-read.
    """
    grown = census(model={"bypass_attempts": 67})
    findings, _, _ = scan(tmp_path, GAP_SENTENCE, grown)
    assert tags(findings) == ["MISMATCH"]


def test_a_shrunken_env_census_fails_the_instrument_floor():
    """An emptied `theoria-arm/runs/` must not read as a clean bill of health.

    No section quotes a denominator, so every prose comparison passes over
    nothing -- H would print PASS on a tree with no environment evidence in it.
    The floor on the instrument itself is what closes that, and it is the same
    device as `MIN_SECTIONS` and `MIN_SCANNED`.
    """
    findings = vp._archive_findings(
        census(env={"requests_live_upstream": 0, "requests_total": 0,
                    "ledgers": 0}))
    assert tags(findings) == ["UNDERRUN", "UNDERRUN", "UNDERRUN"]


def test_the_instrument_floor_is_a_floor(monkeypatch):
    """It must not fire on a tree that has merely grown past S32's reading."""
    assert vp._archive_findings(
        census(env={"requests_live_upstream": 10 ** 6,
                    "requests_total": 10 ** 6, "ledgers": 900})) == []


def test_a_census_missing_a_field_is_reported_not_skipped(tmp_path):
    """The instrument changing shape is a finding, not a silent pass.

    `census.get(...)` returning None would otherwise compare a real prose
    number against nothing and call it agreement.
    """
    broken = census()
    del broken["model_proxy"]["bypass_attempts"]
    findings, _, _ = scan(tmp_path, GAP_SENTENCE, broken)
    assert tags(findings) == ["NOFIELD"]


# --------------------------------------------------------------------------
# the patterns read what they claim to, and not more
# --------------------------------------------------------------------------

def test_a_bare_401_in_prose_is_not_read_as_a_count(tmp_path):
    """§9.2 says "the request returns 401" four paragraphs earlier.

    No digit qualifies it, and reading the sentence as a claim about a count
    would red the gate on prose that claims nothing.
    """
    findings, observed, _ = scan(
        tmp_path,
        GAP_SENTENCE + "\nSent directly the request returns 401, sent through "
        "the proxy it returns 200.\n")
    assert findings == []
    assert len([1 for c, *_ in observed if c.tag == "model 401s"]) == 1


@pytest.mark.parametrize("body,expected", [
    pytest.param("It produced 66 bypass_attempt incidents.", 66,
                 id="unwrapped, one line"),
    pytest.param("It produced **66** `bypass_attempt` incidents.", 66,
                 id="each half emphasised separately"),
    pytest.param("It logged 1,234 bypass_attempt incidents.", 1234,
                 id="comma-grouped"),
])
def test_the_incident_pattern_survives_reformatting(tmp_path, body, expected):
    _, observed, _ = scan(tmp_path, body + "\nand 65 consecutive 401s.\n")
    assert expected in [v for *_, v, _ in observed]


def test_space_grouped_thousands_are_a_known_gap(tmp_path):
    """Documented rather than fixed, and pinned so the docstring cannot lie.

    `9 000` is read as `000`, the trailing group -- not skipped, which is what
    an earlier draft of the note beside `_CARD` claimed. The consequence is
    asymmetric and this test records both halves: on the floor side the
    mis-read is *smaller* than the live figure, so an overclaim written that
    way is accepted; on the equality side it is a red on a true sentence.

    If this ever goes red because someone widened `_CARD`, delete it along with
    the gap note -- the failure would be a fix, not a regression.
    """
    _, observed, _ = scan(
        tmp_path, GAP_SENTENCE + "\nIt forwarded 9 000 requests to a live "
        "upstream.\n")
    assert [v for c, *_, v, _ in observed if c.tag.startswith("env")] == [0]

    # ... and the overclaim it hides. 9000 is well past the live 2529.
    findings, _, _ = scan(
        tmp_path, GAP_SENTENCE + "\nIt forwarded 9 000 requests to a live "
        "upstream.\n")
    assert findings == [], "the gap is real; this is what it costs"
