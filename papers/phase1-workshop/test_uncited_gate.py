"""Negative control for verify_paper.py's check E.

A gate nobody has watched fail is a gate nobody has any reason to trust, so
every pin in this repository carries a control that makes it fail on purpose.
These are check E's: each one is a sentence built to slip past it, and the test
is that it does not.

The evasions in `test_evasions` are not hypothetical. They are the list the P16
work item names as the adversarial step -- spell the number out, put the path in
the next paragraph, hide the digit in backticks -- plus the ones found while
building the check.

Run:  python -m pytest papers/phase1-workshop/test_uncited_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_paper as vp  # noqa: E402


def scan(tmp_path: Path, body: str, rulings=None):
    """Run check E over a one-section scratch tree."""
    (tmp_path / "07_body.md").write_text(body, encoding="utf-8")
    flagged, hits, scanned = vp.scan_uncited(tmp_path, rulings or {})
    return flagged, hits, scanned


# --------------------------------------------------------------- it fires

def test_an_uncited_quantity_fails(tmp_path):
    """The defect P15 found the expensive way, in miniature."""
    flagged, _, _ = scan(tmp_path, "The arm completed 41 cells in 939 actions.\n")
    assert len(flagged) == 1
    assert "41" in flagged[0][3] and "939" in flagged[0][3]


def test_a_cited_quantity_passes(tmp_path):
    flagged, _, _ = scan(
        tmp_path, "The arm completed 41 cells (`baseline-arms/ledger.jsonl`).\n")
    assert flagged == []


def test_the_abstract_is_exempt(tmp_path):
    """The paper's one declared exemption, and it must stay one."""
    (tmp_path / "00_abstract.md").write_text("It scored 41 of 939.\n", encoding="utf-8")
    flagged, _, _ = vp.scan_uncited(tmp_path, {})
    assert flagged == []


# ------------------------------------------------------------- the evasions

EVASIONS = [
    pytest.param(
        "The register drove thirty-seven of thirty-eight metrics to threshold.\n",
        id="spelled-out numerals",
    ),
    pytest.param(
        "The pooled spread is `0.033244` across the arm.\n",
        id="digit hidden in backticks",
    ),
    pytest.param(
        "It reached 41 cells.\n\nThe ledger is `baseline-arms/ledger.jsonl`.\n",
        id="path parked in the next paragraph",
    ),
    pytest.param(
        "The count moved by zero across the second arm.\n",
        id="zero written as a word",
    ),
    pytest.param(
        "Cache creation ran to 116 470 tokens on the hour multiplier.\n",
        id="space-grouped thousands",
    ),
    pytest.param(
        "The run cost $6.32 against a re-derived $5.80.\n",
        id="money",
    ),
    pytest.param(
        "Coverage was 47 % of its own state-action pairs.\n",
        id="percentage",
    ),
    pytest.param(
        "The manifest's `cost.relative_delta` is −0.0827 on this run.\n",
        id="field name is not a citation",
    ),
]


@pytest.mark.parametrize("body", EVASIONS)
def test_evasions(tmp_path, body):
    flagged, _, _ = scan(tmp_path, body)
    assert len(flagged) == 1, f"slipped past check E:\n{body}"


# The second adversarial pass. Each of these was an observed `flagged == []`
# against a sentence carrying a real measurement.

ROUND_TWO = [
    pytest.param(
        "The cross-arm effect is .562 against a null of .188 (p = .003).\n",
        id="leading-dot decimal"),
    pytest.param(
        "Median wall-clock fell from `41s` to `12s`, and memory held at `1.4GB`.\n",
        id="unit-suffixed value in backticks"),
    pytest.param(
        "The context budget was `1000000` tokens per arm.\n",
        id="power of ten is all noughts and ones"),
    pytest.param(
        "Each arm ran under a cap of `100000` actions.\n",
        id="six-bit round number"),
    pytest.param(
        "The regression wasn't 40 percent by the end of the sweep.\n",
        id="contraction read as a frame index"),
]


@pytest.mark.parametrize("body", ROUND_TWO)
def test_round_two_evasions(tmp_path, body):
    flagged, _, _ = scan(tmp_path, body)
    assert len(flagged) == 1, f"slipped past check E:\n{body}"


def test_a_result_in_a_heading_is_scanned(tmp_path):
    """Headings were `continue`d past without their text ever being emitted."""
    flagged, _, _ = scan(
        tmp_path, "## Repair recovers 38 percent of failed arms\n\nIt does.\n")
    assert len(flagged) == 1, "a result stated in a heading was never looked at"


def test_a_headings_own_number_is_not_a_quantity(tmp_path):
    """Scanning headings must not flag all 87 of them for being numbered."""
    flagged, _, _ = scan(tmp_path, "### 7.2a The effect sizes are not paired\n")
    assert flagged == []


def test_a_cited_heading_passes(tmp_path):
    flagged, _, _ = scan(
        tmp_path, "## Repair recovers 38 % (`battery/artifacts/gaming_audit.json`)\n")
    assert flagged == []


FRACTIONS = [
    pytest.param("The bill fell by a factor of three across the sweep.\n",
                 id="factor of"),
    pytest.param("Coverage was double the baseline on every arm.\n", id="double"),
    pytest.param("A third of the sealed games were quarantined.\n", id="a third"),
    pytest.param("Latency was halved and the arm count doubled.\n", id="halved"),
]


@pytest.mark.parametrize("body", FRACTIONS)
def test_fractions_and_multipliers_are_quantities(tmp_path, body):
    """The register a result slides into when it has no artefact."""
    flagged, _, _ = scan(tmp_path, body)
    assert len(flagged) == 1, f"slipped past check E:\n{body}"


def test_a_five_bit_label_is_still_not_a_quantity(tmp_path):
    """The counterpart to the round-number fix: real labels must stay exempt."""
    flagged, _, _ = scan(
        tmp_path, "The board `11011` reaches `00001`, `00010` and `01000`.\n")
    assert flagged == []


def test_backticked_ten_thousand_is_a_known_residual(tmp_path):
    """A limit, pinned so that it is a decision and not a surprise.

    `10000` is a genuine five-cell board label in this paper *and* a plausible
    action cap, and inside backticks the check cannot tell them apart. The
    exemption is kept, because dropping it would flag five real labels to catch
    one hypothetical cap. Write the cap unbackticked -- that form is caught, as
    the second assertion pins.
    """
    flagged, _, _ = scan(tmp_path, "Each arm ran under a cap of `10000` actions.\n")
    assert flagged == [], "if this now fires, the residual is closed -- delete this test"
    flagged, _, _ = scan(tmp_path, "Each arm ran under a cap of 10000 actions.\n")
    assert len(flagged) == 1


def test_a_line_anchor_does_not_hide_a_path_from_check_b(tmp_path):
    """E accepts any path-shaped token; B is what resolves it. B could not see
    a line-anchored one at all, so `foo.md:3` was checked by neither.

    Updated by P21: the anchor is still not part of the path, but it is now
    *captured* rather than discarded, so the number half of the citation has
    somewhere to be checked. Matching the tail and then throwing it away was the
    other half of the same hole."""
    m = vp.PATH_TOKEN.search("(`no/such/dir/thing.md:3`)")
    assert m.group(1) == "no/such/dir/thing.md"
    assert m.group("anchor") == "3"
    assert vp.classify("no/such/dir/thing.md") == "BROKEN"
    m = vp.PATH_TOKEN.search("(`papers/phase1-workshop/verify_paper.py:12-14`)")
    assert m.group(1) == "papers/phase1-workshop/verify_paper.py"
    assert m.group("anchor") == "12-14"
    # A citation with no anchor still has none -- the group is optional, not
    # defaulted, so `if anchor:` is the whole test at every call site.
    assert vp.PATH_TOKEN.search("(`papers/verify.py`)").group("anchor") is None


def test_a_broad_ruling_cannot_silence_several_blocks(monkeypatch, tmp_path):
    """MIN_ANCHOR guards length, not genericity. A 47-character anchor of
    boilerplate silenced three distinct uncited blocks and reported nothing."""
    anchor = "the numbers in this paragraph come from the run"
    body = "".join(f"It reached {n} cells, {anchor}.\n\n" for n in (41, 42, 43))
    passed, notes = _verdict(monkeypatch, tmp_path, body, {("07_body.md", anchor): "x"})
    assert not passed, "one ruling silenced three blocks and passed"
    assert any("BROAD" in n for n in notes)


def test_a_path_shaped_token_is_not_satisfied_by_a_bare_identifier(tmp_path):
    """`Step.won` points at a field, not an artefact, and must not count."""
    flagged, _, _ = scan(tmp_path, "`Step.won` is populated on 41 of 46 runs.\n")
    assert len(flagged) == 1


def test_non_zero_asserts_an_absence_not_a_quantity(tmp_path):
    """"Three non-zero values exist" was flagged for the `zero` inside `non-`."""
    flagged, _, _ = scan(
        tmp_path, "Three non-zero values exist in the tree, all self-built.\n")
    assert flagged == []
    # ...but a bare `zero` still is a quantity.
    flagged, _, _ = scan(tmp_path, "The count moved by zero across the arm.\n")
    assert len(flagged) == 1


def test_a_brace_citation_is_a_citation(tmp_path):
    """Section 7 cites three sibling artefacts in one token; both checks were blind."""
    flagged, _, _ = scan(
        tmp_path,
        "Three rows carry it — `ablation-arm/artifacts/{a0,a2}/episode.jsonl` "
        "— each of 41 actions.\n")
    assert flagged == []


def test_a_ratio_does_not_cite_itself(tmp_path):
    """`233/236` has a slash. Without the NOT_A_PATH guard it was its own path."""
    flagged, _, _ = scan(tmp_path, "Coverage held at `233/236` on the second arm.\n")
    assert len(flagged) == 1, "a backticked fraction cleared its own block"


def test_an_invented_filename_is_not_a_citation(tmp_path):
    """Check B skips bare filenames by design, so E is the only reader there."""
    flagged, _, _ = scan(
        tmp_path, "The arm reached 41 cells (`ledger_summary.jsonl`).\n")
    assert len(flagged) == 1, "a plausible name for a file that does not exist"


def test_a_real_bare_filename_still_cites(tmp_path):
    """The counterpart: the paper's dominant idiom must keep working."""
    flagged, _, _ = scan(
        tmp_path, "The arm reached 41 cells (`THEORIZE_LOG.md`).\n")
    assert flagged == []


def test_brace_expansion_requires_every_sibling_to_resolve():
    token = "ablation-arm/artifacts/{a0-base,a2-base,a2-charitable}/episode.jsonl"
    assert len(vp.expand_braces(token)) == 3
    assert vp.classify(token) == "ok"
    assert vp.classify("ablation-arm/artifacts/{a0-base,nope}/episode.jsonl") == "BROKEN"


# -------------------------------------------------------- the false positives

NOT_CLAIMS = [
    pytest.param("The ordering is stated in §7.10a and again in §11.5.\n", id="section ref"),
    pytest.param("Sections 6, 8 and 9 report without claiming.\n", id="section word"),
    pytest.param("Figure 3 plates the repair loop.\n", id="figure ref"),
    pytest.param("Phase 1 is the closed system.\n", id="phase ref"),
    pytest.param("Metrics E2, K12, P4 and X3 are in the main table.\n", id="metric ids"),
    pytest.param("Recorded as INC-BA-001 and ruled by F-11.\n", id="dashed ids"),
    pytest.param("Draft v0.4 supersedes v0.2 under Lean 4.9.0.\n", id="versions"),
    pytest.param("The Cart is at (6,4) and the world puts it at (7,6).\n", id="coordinates"),
    pytest.param("The histogram reads `[7, 0, 0, 0, 0, 0, 0]` for the run.\n", id="vector"),
    pytest.param("Committed at `f58959e7` and discharged at `672044a8`.\n", id="shas"),
    pytest.param("The owner ruled on 2026-07-28, wired at 08:42 Z.\n", id="date and clock"),
    pytest.param("The beats are L1 through L6 of the ledger.\n", id="beat ids"),
    pytest.param("Enumeration is O(2^n) on that board.\n", id="complexity class"),
]


@pytest.mark.parametrize("body", NOT_CLAIMS)
def test_structure_is_not_a_claim(tmp_path, body):
    flagged, _, _ = scan(tmp_path, body)
    assert flagged == [], f"structural token flagged as a quantitative claim:\n{body}"


# ------------------------------------------------------- the adjudication table

# Long enough to clear MIN_ANCHOR. An 18-character anchor read fine here and
# would have been rejected in the real table, which is the wrong way round for
# a fixture: the control must obey the rule it is controlling.
RULING = ("07_body.md", "is a multiple of 1/16 at this n")


def test_a_ruling_silences_its_block_and_only_its_block(tmp_path):
    body = "Every δ is a multiple of 1/16 at this n.\n\nThe arm reached 41 cells.\n"
    flagged, hits, _ = scan(tmp_path, body, {RULING: "arithmetic on the cited n"})
    assert hits[RULING] == 1
    assert [f[1] for f in flagged] == [3], "the ruling silenced a block it was not written for"


def test_a_ruling_that_matches_nothing_is_stale(tmp_path):
    flagged, hits, _ = scan(
        tmp_path, "The arm reached 41 cells.\n", {RULING: "arithmetic on the cited n"})
    assert hits[RULING] == 0, "a ruling for a sentence that no longer exists must go stale"
    assert len(flagged) == 1


def test_rewriting_a_ruled_claim_retires_its_ruling(tmp_path):
    """The reason the key is a verbatim anchor rather than a line number."""
    _, hits, _ = scan(
        tmp_path, "Every δ is a multiple of 1/32 at this n.\n",
        {RULING: "arithmetic on the cited n"})
    assert hits[RULING] == 0


# The three above test the scan. These drive `check_uncited` itself, because the
# pass/fail decision lives there and a counter nobody gates on is not a gate --
# a mutation that deleted the stale list left all of the tests above green.

def _verdict(monkeypatch, tmp_path, body, rulings):
    (tmp_path / "07_body.md").write_text(body, encoding="utf-8")
    monkeypatch.setattr(vp, "SECTIONS", tmp_path)
    monkeypatch.setattr(vp, "ADJUDICATED_UNCITED", rulings)
    return vp.check_uncited()


def test_a_stale_ruling_fails_the_check(monkeypatch, tmp_path):
    passed, notes = _verdict(
        monkeypatch, tmp_path,
        "Coverage is 47 % (`cold-start-a0/A0_REPORT.md`).\n",
        {RULING: "arithmetic on the cited n"})
    assert not passed, "a ruling that excuses nothing must not pass silently"
    assert any("STALE" in n for n in notes)


def test_a_live_ruling_passes_and_prints_its_reason(monkeypatch, tmp_path):
    passed, notes = _verdict(
        monkeypatch, tmp_path,
        "Every δ is a multiple of 1/16 at this n.\n",
        {RULING: "arithmetic on the cited n"})
    assert passed
    assert any("ruled" in n and "arithmetic on the cited n" in n for n in notes), \
        "a check that hides its rulings is worse than no check"


def test_an_uncited_block_fails_the_check(monkeypatch, tmp_path):
    passed, notes = _verdict(monkeypatch, tmp_path, "It reached 41 cells.\n", {})
    assert not passed
    assert any("UNCITED" in n for n in notes)


# --------------------------------------------------- the two escape hatches
# Both were found by the adversarial pass, both were closed, and neither was
# pinned. A closed hatch with no control on it is a hatch that reopens on the
# next refactor with nothing to notice.

def test_a_short_anchor_cannot_silence_the_paper(monkeypatch, tmp_path):
    """The one-character ruling: `" "` is in every block, so it ruled them all."""
    passed, notes = _verdict(
        monkeypatch, tmp_path,
        "It reached 41 cells.\n\nThe register drove 37 of 38 metrics.\n",
        {("07_body.md", " "): "arithmetic on the cited n"})
    assert not passed, "a one-space anchor silenced every block and passed"
    assert any("ANCHOR" in n for n in notes)


def test_an_unbalanced_fence_fails_the_check(monkeypatch, tmp_path):
    """Everything after an unclosed ``` is skipped as code, claims included."""
    passed, notes = _verdict(
        monkeypatch, tmp_path,
        "```\nsome sample output\n\nIt reached 41 cells.\n", {})
    assert not passed
    assert any("FENCE" in n for n in notes)


def test_a_balanced_fence_is_still_skipped(monkeypatch, tmp_path):
    """The fence check must not turn legitimate code blocks into claims."""
    passed, _ = _verdict(
        monkeypatch, tmp_path,
        "```\nledger.jsonl: 41 cells, 939 actions\n```\n", {})
    assert passed, "a properly closed code block is not a quantitative claim"


# ------------------------------------------------------------- block assembly

def test_a_table_is_scored_with_the_sentence_that_introduces_it(tmp_path):
    body = (
        "The comparison is tabulated in `cold-start-a0/prime/A0P_REPORT.md`:\n"
        "\n"
        "| metric | A0 | A0' |\n"
        "|---|---|---|\n"
        "| coverage | 233/236 | 107/228 |\n"
    )
    flagged, _, _ = scan(tmp_path, body)
    assert flagged == [], "table rows must inherit their preamble's citation"


def test_a_table_with_no_preamble_citation_still_fails(tmp_path):
    body = (
        "The comparison is tabulated below:\n"
        "\n"
        "| metric | A0 | A0' |\n"
        "|---|---|---|\n"
        "| coverage | 233/236 | 107/228 |\n"
    )
    flagged, _, _ = scan(tmp_path, body)
    assert len(flagged) == 1


def test_a_wrapped_list_item_is_one_block(tmp_path):
    """The continuation line is not a new claim; it is the same sentence."""
    body = (
        "* `SURVEY-solver-status.md:274-376` names 51 table rows\n"
        "  that read a solver status correctly, plus 11 backticked paths.\n"
    )
    flagged, _, _ = scan(tmp_path, body)
    assert flagged == []


def test_a_fenced_block_is_not_prose(tmp_path):
    body = "```json\n{\"levels_completed\": 41, \"actions\": 939}\n```\n"
    flagged, _, _ = scan(tmp_path, body)
    assert flagged == []


def test_a_heading_breaks_the_merge_chain(tmp_path):
    """A table under a new heading must not inherit the last section's path."""
    body = (
        "Tabulated in `cold-start-a0/prime/A0P_REPORT.md`:\n"
        "\n"
        "### 3.2 A different subsection\n"
        "\n"
        "| metric | value |\n"
        "|---|---|\n"
        "| coverage | 233/236 |\n"
    )
    flagged, _, _ = scan(tmp_path, body)
    assert len(flagged) == 1, "a citation must not leak across a heading"


def test_a_numbers_only_heading_still_breaks_the_chain(tmp_path):
    """The case the sentinel is still load-bearing for.

    Since headings are emitted as blocks, a heading with text stands between
    the sections by itself. A heading that is *only* a number strips to nothing
    and emits no block, so the chain break is the only thing left.
    """
    body = (
        "Tabulated in `cold-start-a0/prime/A0P_REPORT.md`:\n"
        "\n"
        "### 3.2\n"
        "\n"
        "| metric | value |\n"
        "|---|---|\n"
        "| coverage | 233/236 |\n"
    )
    flagged, _, _ = scan(tmp_path, body)
    assert len(flagged) == 1, "a citation leaked across a bare numbered heading"
