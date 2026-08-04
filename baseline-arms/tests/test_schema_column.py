"""Acceptance for `harness/schema_column.py`.

The guard half of these tests is written negative-control-first. A check that
has never been seen to say no has not been shown to check anything, so every
rule here is driven with a fabricated violation and required to refuse it
*before* it is shown passing on the tree.

The measurement half skips when the payload is absent -- it is gitignored, and
a linked worktree does not contain it -- but the skip is loud and the numbers
it would produce are pinned in `SCHEMA_ARM_RULING.md` and in the run record,
so a reader without the payload is not left guessing.
"""

import json
import os

import pytest

from harness import schema_column as sc

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------------------
# Negative controls.  Each of these must be refused.
# --------------------------------------------------------------------------

FABRICATED = [
    # The placeholder, filled.
    ("复现值：98.98%", "filled-repro-cell"),
    ("⟨复现值: 97.2%⟩", "filled-repro-cell"),
    ("reproduction score: 98.98", "filled-repro-cell"),
    ("we obtained a reproduction score of 91.4% on the sealed pile",
     "filled-repro-cell"),
    # The table row, filled in place.
    ("| Schema(复现口径) | 98.98%(上游)/ 96.10% | ~10⁸ | world_model.py |",
     "filled-repro-cell"),
    # The upstream ledger relabelled as our own work.
    ("we reproduced Schema on the development pile", "upstream-called-reproduction"),
    ("本轮复现了 Schema 的四局", "upstream-called-reproduction"),
    ("our Schema reproduction covers 4 games", "upstream-called-reproduction"),
    ("Schema 复现臂给出的效应量", "upstream-called-reproduction"),
]


@pytest.mark.parametrize("text,rule", FABRICATED)
def test_guard_refuses_fabricated_reproduction_claims(text, rule):
    findings = sc.check_text(text, label="<fabricated>")
    assert findings, "guard passed a fabricated violation: %r" % text
    assert any(f["rule"] == rule for f in findings), \
        "wrong rule fired for %r: %r" % (text, [f["rule"] for f in findings])


#: The other half of a negative control: the sentences the ruling itself has to
#: be able to write.  A guard that also refuses these would force the ruling to
#: be written around the guard, and a guard you write around is off.
PERMITTED = [
    "`⟨复现值⟩` 保持空白，官方 harness 未发布，复现不可能。",
    "It is not a reproduction: the Schema harness was never published.",
    "we never reproduced Schema and this document rules that we will not",
    "`Theoria.md:271` 的 `⟨复现值⟩` 至今空白，且这是合规留空",
    "Schema 复现臂不存在（SCHEMA_LOCATE.md）",
    "98.98% is upstream's number over 25 games, cited as upstream.",
    "the arm is `schema_upstream`, an ingested non-reproduced reference",
]


@pytest.mark.parametrize("text", PERMITTED)
def test_guard_permits_the_honest_wording(text):
    assert sc.check_text(text, label="<permitted>") == []


def test_guard_reports_line_numbers_not_just_a_boolean():
    text = "clean line\nclean line\n复现值：98.98%\n"
    findings = sc.check_text(text, label="doc.md")
    assert [f["line"] for f in findings] == ["3"]


def test_guard_is_green_on_this_track_today():
    """The positive case, run last and only after the refusals are proven."""
    targets = []
    for name in sorted(os.listdir(TRACK)):
        if name.endswith(".md"):
            targets.append(os.path.join(TRACK, name))
    findings = sc.check_paths(targets)
    assert findings == [], json.dumps(findings, indent=2, ensure_ascii=False)


def test_unreadable_path_is_a_finding_not_a_pass():
    """Open-failure is the direction a guard must never fail in."""
    findings = sc.check_paths([os.path.join(TRACK, "no-such-file.md")])
    assert [f["rule"] for f in findings] == ["unreadable"]


# --------------------------------------------------------------------------
# Measurement.
# --------------------------------------------------------------------------

def _payload_or_skip():
    """Skip on the payload, not on the directory that holds it.

    A33 (2026-08-04): `os.path.isdir(root)` was not enough, and this file's own
    docstring names the case it missed -- "a linked worktree does not contain
    it".  `schema_traces/` holds one *tracked* file, `MANIFEST.json`, and eight
    *gitignored* run collections.  So in a linked worktree the directory exists
    and the payload does not: `isdir` passed, `measure_cache_reads()` returned
    zero runs, and three tests below failed on empty data.

    The fourth was worse.  `test_measurement_does_not_reproduce_the_published
    _interval` asserts two flags are False, and both are False when there is
    nothing to measure -- so it went green on no data at all, which is the
    vacuous pass this suite is written negative-control-first to prevent.

    Checking for at least one collection directory costs a `listdir` and closes
    both.  It is not `sc.measure_cache_reads()` because that walk is the
    expensive part of this file and the guard runs on every test in it.
    """
    root = sc.resolve_root()
    if not os.path.isdir(root):
        pytest.skip("upstream payload absent at %s (gitignored; set %s)"
                    % (root, sc.ROOT_ENV))
    collections = [d for d in sorted(os.listdir(root))
                   if os.path.isdir(os.path.join(root, d))]
    if not collections:
        pytest.skip("upstream payload at %s holds no run collections -- only "
                    "the tracked MANIFEST.json came with this checkout, which "
                    "is what a linked worktree looks like. The numbers these "
                    "tests would produce are pinned in SCHEMA_ARM_RULING.md "
                    "and in the run record. (set %s to point at a full copy)"
                    % (root, sc.ROOT_ENV))
    return root


def test_measurement_does_not_reproduce_the_published_interval():
    """The finding this module exists for, asserted rather than narrated.

    `Theoria.md:271` says 实测 2.04–3.41 亿.  Neither counting convention puts
    the four measurable runs inside that interval.  If a future payload change
    makes this pass, the ruling's central factual claim has changed and should
    fail loudly here.
    """
    _payload_or_skip()
    report = sc.measure_cache_reads()
    assert report["table_claim_reproduced"] is False
    assert report["table_claim_reproduced_naive"] is False


def test_half_the_arm_records_no_token_usage_at_all():
    _payload_or_skip()
    report = sc.measure_cache_reads()
    assert report["n_runs"] == 8
    assert report["n_runs_with_token_usage"] == 4
    for name, entry in report["runs"].items():
        if entry["collection"] == "gpt_5_6_sol":
            assert entry["cache_read_tokens"] == 0
            assert entry["assistant_messages"] == 0


def test_dedup_matters_and_is_not_a_constant_factor():
    """The reason the naive walk is wrong, stated as a test.

    If the double-count were a fixed multiple somebody would eventually
    "correct" for it.  It is not: the ratio spans well over a factor of one
    between runs, so no single correction exists.
    """
    _payload_or_skip()
    report = sc.measure_cache_reads()
    ratios = [entry["cache_read_tokens_naive"] / entry["cache_read_tokens"]
              for entry in report["runs"].values()
              if entry["cache_read_tokens"]]
    assert len(ratios) == 4
    assert max(ratios) - min(ratios) > 0.5


def test_order_of_magnitude_survives_even_though_the_interval_does_not():
    """`~10⁸` is defensible on this material; the parenthetical is not."""
    _payload_or_skip()
    low, high = sc.measure_cache_reads()["cache_read_range"]
    assert 1e7 <= low and high < 1e9


def test_absent_events_file_gives_none_not_zero(tmp_path):
    assert sc._count_steps(str(tmp_path)) is None
    (tmp_path / "events.jsonl").write_text('{"kind":"action_taken"}\n',
                                           encoding="utf-8")
    assert sc._count_steps(str(tmp_path)) == 1


def test_missing_payload_is_refused_not_reported_as_zero():
    """`measure` must exit non-zero rather than print a clean empty report."""
    assert sc.main(["measure", "--root", os.path.join(TRACK, "no-such-dir")]) == 2
