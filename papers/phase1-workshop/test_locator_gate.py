"""Negative control for `locator_findings()` -- the check that checks the rulings.

Checks E and F let a ruling exempt a block from citation on the strength of a
prose justification. Most of a justification is judgement, which no gate can
score. One part of it is a *fact*: when it says "cited one block above", either
the named artefact is in that block or it is not. Three rulings said it and were
wrong, and a wrong ruling is worse than no ruling -- it clears its whole block,
so the claims inside it read as adjudicated when nobody ever looked.

The controls here are the two shapes that actually shipped:

* the locator points at the wrong block (`07_battery.md`'s "the block below",
  which a hand row-sample audit had scored as slack), and
* the locator names nothing at all (`08_exam.md` §8.4's "cited one block above
  (one report per tier, both named there)"), which is unfalsifiable, and which
  exempted an 18-line six-bullet list carrying three claims that later turned
  out to be refuted.

The second is why "states a distance, names no artefact" is itself a finding
rather than a pass. Both entries written that way were wrong.

Run:  python -m pytest papers/phase1-workshop/test_locator_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_paper as vp  # noqa: E402


#: The shape of the real defect, in miniature. Four blocks: [0] the §8.2
#: heading, [1] the paragraph carrying both artefacts, [2] the §8.4 heading,
#: [3] the bullet list a ruling is written about.
#:
#: Two details here are load-bearing and both were got wrong first time round.
#: The list sits *directly under a heading*: `_blocks` merges a list into the
#: prose chunk above it, so putting a paragraph in between fuses the two and the
#: ruled block stops being the list. A heading terminates the chunk, which is
#: why the real §8.4 list is a block of its own. And it means "one block above"
#: resolves to the §8.4 *heading*, which cites nothing -- verbatim the shipped
#: defect: the ruling claimed the handover reports were one block up, and one
#: block up was a heading.
SECTION = """\
### 8.2 Handover

Both are reported once per tier, in `exam/artifacts/reports/tier1.report.json`
and `exam/artifacts/reports/tier2.report.json`.

### 8.4 What the exam does not establish

* **n = 1 per handover tier**, on a saturated sheet. Nothing here supports a
  variance claim about fresh readers.
"""

ANCHOR = "**n = 1 per handover tier**, on a saturated"


def find(tmp_path: Path, reason: str, section: str = SECTION, **kw):
    """Run `locator_findings` over a one-section scratch tree."""
    (tmp_path / "08_exam.md").write_text(section, encoding="utf-8")
    return vp.locator_findings({("08_exam.md", ANCHOR): reason}, tmp_path, **kw)


# ------------------------------------------------------------------ it fires

def test_a_locator_pointing_at_the_wrong_block_is_reported(tmp_path):
    """`07_battery.md`'s shape: the distance is real, the block is the wrong one."""
    out = find(tmp_path, "Restates the sample size cited one block above "
                         "(`exam/artifacts/reports/tier1.report.json`).")
    assert len(out) == 1
    msg = out[0][1]
    assert "LOCATOR" in msg and "1 block above" in msg
    # It must say where the artefact actually is, or the reader cannot fix it.
    assert "-2" in msg


def test_a_locator_that_names_no_artefact_is_reported(tmp_path):
    """§8.4's shape, and the one that cost the most.

    "both named there" names nothing a check can look for. The entry read as
    rigorous and asserted nothing, which is how it survived two audits.
    """
    out = find(tmp_path, "Restates the sample size of the handover result cited "
                         "one block above (one report per tier, both named there).")
    assert len(out) == 1
    assert "names no artefact" in out[0][1]


def test_a_locator_off_the_end_of_the_section_is_reported(tmp_path):
    out = find(tmp_path, "Cited nine blocks above "
                         "(`exam/artifacts/reports/tier1.report.json`).")
    assert len(out) == 1
    assert "off the " in out[0][1]


# ---------------------------------------------------------------- it is quiet

def test_a_true_locator_passes(tmp_path):
    """The same ruling with the true distance. This is the case that must not
    turn into noise: a gate with false positives is a gate that gets removed."""
    out = find(tmp_path, "Restates the sample size cited two blocks above "
                         "(`exam/artifacts/reports/tier1.report.json`, "
                         "`exam/artifacts/reports/tier2.report.json`).")
    assert out == []


def test_a_ruling_with_no_locator_is_not_this_checks_business(tmp_path):
    """Most rulings state no distance. Those are judgement calls and this check
    has nothing to say about them -- it scores the one falsifiable sentence."""
    out = find(tmp_path, "The arithmetic this paragraph explicitly declines to "
                         "report as a measurement.")
    assert out == []


def test_the_block_above_is_one_block_above(tmp_path):
    """The bare form, which takes a different branch of `RULING_LOCATOR`."""
    true_at_two = find(tmp_path, "Established in the block above "
                                 "(`exam/artifacts/reports/tier1.report.json`).")
    assert len(true_at_two) == 1        # block above is [2], which carries nothing


def test_a_stale_anchor_is_left_to_the_stale_rule(tmp_path):
    """Not this check's finding. Two checks reporting one defect print two
    reasons for it, and the STALE rule already owns this one."""
    (tmp_path / "08_exam.md").write_text(SECTION, encoding="utf-8")
    out = vp.locator_findings(
        {("08_exam.md", "a sentence no longer in the paper"):
         "Cited one block above (`exam/artifacts/reports/tier1.report.json`)."},
        tmp_path)
    assert out == []


def test_a_missing_section_is_not_a_locator_finding(tmp_path):
    out = vp.locator_findings(
        {("99_absent.md", ANCHOR): "Cited one block above (`a/b.json`)."},
        tmp_path)
    assert out == []


# ------------------------------------------------------------------ the wiring

def test_an_invalid_ruling_does_not_silence_its_block(tmp_path):
    """The whole point. A ruling whose stated evidence is false is dropped
    *before* the scan, so its block reports UNCITED -- rather than being cleared
    by an entry that has itself never been checked.

    Without this, the §8.4 list was exempt and check E reported green over it.
    """
    (tmp_path / "08_exam.md").write_text(SECTION, encoding="utf-8")
    ruling = {("08_exam.md", ANCHOR):
              "Cited one block above (one report per tier, both named there)."}

    # As the ruling shipped: the block is silent.
    flagged, _, _ = vp.scan_uncited(tmp_path, ruling)
    assert [f for f in flagged if ANCHOR.split("**")[1] in f[3]] == []

    # With the locator checked: the ruling is invalid, so the block is scored.
    invalid = {k for k, _ in vp.locator_findings(ruling, tmp_path)}
    assert invalid == set(ruling)
    flagged, _, _ = vp.scan_uncited(
        tmp_path, {k: v for k, v in ruling.items() if k not in invalid})
    assert len(flagged) == 1


# ------------------------------------------------- decoy paths (adversarial D1)

def test_a_path_in_a_correction_note_cannot_confirm_a_locator(tmp_path):
    """The adversarial review's HIGH finding, as the one-word edit that found it.

    A correction note records what was at the **wrong** place. Harvesting every
    backticked path in the justification and passing on `any()` of them therefore
    let the note vouch for the falsehood it was written to document -- and the
    more careful the ruling's prose, the more decoys it supplied.
    """
    out = find(tmp_path,
               "Restates the sample size cited one block above "
               "(`exam/artifacts/reports/tier1.report.json`). "
               "(Corrected 2026-07-30: this read \"two blocks above\" and the "
               "block one above is the heading, which cites `Theoria.md`.)",
               section=SECTION.replace("### 8.4 What the exam",
                                       "### 8.4 See `Theoria.md`. What the exam"))
    assert len(out) == 1, "a path named only in the correction note cleared it"


def test_a_contrast_in_a_later_sentence_cannot_confirm_a_locator(tmp_path):
    """Same defect, without a correction note: only the locator's own sentence
    is read, so a path named while saying where the evidence is *not* is inert."""
    out = find(tmp_path,
               "Restates the sample size cited one block above. "
               "Set against `exam/artifacts/reports/tier1.report.json`, which is "
               "the contrast this bullet is drawn from.")
    assert len(out) == 1
    assert "names no artefact" in out[0][1]


# ----------------------------------------------- line locators (adversarial D5)

LINES = """\
Preamble paragraph that cites `runs/x/evidence.json` and is the evidence.

Line one of the ruled block.
Line two of it.
Line three of it.
Line four of it.
The anchor sentence with 42 in it lives on line 7 of the file.
"""


def test_a_line_locator_is_measured_from_the_anchor_not_the_block(tmp_path):
    """A writer counting lines counts from the sentence being ruled on.

    Measuring from the block's first line instead made this **true** locator
    report as running off the end of a seven-line section -- dropping a correct
    ruling, and giving a wrong reason for it.
    """
    (tmp_path / "90_t.md").write_text(LINES, encoding="utf-8")
    out = vp.locator_findings(
        {("90_t.md", "The anchor sentence with 42 in it lives"):
         "The evidence is six lines above -- `runs/x/evidence.json`."},
        tmp_path)
    assert out == [], out and out[0][1]


def test_a_line_locator_that_is_genuinely_wrong_still_fires(tmp_path):
    """The other half: fixing the false positive must not cost the true one."""
    (tmp_path / "90_t.md").write_text(LINES, encoding="utf-8")
    out = vp.locator_findings(
        {("90_t.md", "The anchor sentence with 42 in it lives"):
         "The evidence is two lines above -- `runs/x/evidence.json`."},
        tmp_path)
    assert len(out) == 1


# ------------------------------------------------------- the live tables hold

@pytest.mark.parametrize("table,as_token", [
    ("ADJUDICATED_UNCITED", False),
    ("ADJUDICATED_BARE", True),
])
def test_every_shipped_ruling_states_a_true_locator(table, as_token):
    """Run against the real sections. This is the test that would have caught
    all three, and it is the one that keeps catching them as the prose moves --
    a locator decays with the paragraphs around it, silently and by default.
    """
    out = vp.locator_findings(getattr(vp, table), anchor_is_token=as_token)
    assert out == [], "\n".join(m for _, m in out)
