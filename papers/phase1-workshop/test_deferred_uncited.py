"""Negative controls for the two mechanisms V31 added to `verify_paper.py`.

`DEFERRED_UNCITED` (check E) and `_WALK_SKIP_PREFIXES` (check F) are both things
that turn a red gate green. That is the most dangerous shape a change to this
file can have, and `papers/verify.py`'s own docstring is a catalogue of what it
costs when such a thing is added without a control: *"a gate nobody can find is,
to every automated reader, a gate that does not exist"*. So each one is driven
until it fails here, and the properties that make it defensible rather than a
lowered bar are pinned individually.

The load-bearing claim about a deferral is that it moves the **exit code** and
nothing else -- the finding still prints, in the same shape, on every run. That
is what distinguishes it from `ADJUDICATED_UNCITED`, whose §8.4 entry was
withdrawn on 2026-07-30 precisely because a ruling suppresses the report. Half of
this file is about that one sentence being true.

    cd papers/phase1-workshop && python -m pytest test_deferred_uncited.py -q
"""

import os

import pytest

import verify_paper as vp

# The live entry, so the tests below are about the thing that actually ships
# rather than a fixture that resembles it. If the table is ever emptied the
# parametrisation collapses and `test_the_table_is_not_empty` says so, rather
# than the file passing vacuously -- an empty walk satisfies every loop.
LIVE = sorted(vp.DEFERRED_UNCITED.items())


def test_the_table_is_not_empty():
    """If it empties, delete this file rather than let it pass over nothing.

    Every other assertion here iterates `LIVE`, so an empty table turns the
    whole suite green while testing zero behaviour -- the exact silence
    `papers/verify.py` refuses in its own stage 1.
    """
    assert LIVE, ("DEFERRED_UNCITED is empty. That is good news, but it makes "
                  "every parametrised test in this file vacuous: remove them "
                  "with the mechanism, or keep a fixture entry.")


# --------------------------------------------------------------- the live tree

def test_the_live_deferral_is_applicable_and_matches_exactly_one_block():
    """The escape hatch in `check_uncited` cannot become the way one hides.

    A deferral whose section is absent from the tree being scanned is skipped
    silently -- that is what lets the other suites point `SECTIONS` at a scratch
    directory. On the live tree it must not be skipped, or an entry could be
    parked against a section that no longer exists and never be re-read again.
    """
    for (section, anchor), (opened, owner, record, reason) in LIVE:
        path = vp.SECTIONS / section
        assert path.is_file(), (
            f"deferral names {section}, which is not in sections/. On the live "
            f"tree that silently disables the entry.")
        text = path.read_text(encoding="utf-8")
        flat = " ".join(text.split())
        assert flat.count(" ".join(anchor.split())) == 1, (
            f"the anchor for {section} must occur exactly once in it; a "
            f"deferral is opened against one finding.")
        assert len(anchor) >= vp.MIN_ANCHOR
        assert opened and owner and reason
        assert (vp.ROOT / record).is_file(), record


def test_the_live_deferral_is_a_real_finding_not_a_pre_emptive_one():
    """It must be flagged by the scanner with the deferral table taken away.

    Otherwise an entry could be opened against a block that was never uncited,
    which reads as a disclosed defect and is in fact noise -- and worse, it
    would make the mechanism look exercised while nothing was deferred.
    """
    flagged, _hits, _scanned = vp.scan_uncited()
    reachable = {(name, flat) for name, _lineno, flat, _n, _w in flagged}
    for (section, anchor), _v in LIVE:
        assert any(name == section and anchor in flat
                   for name, flat in reachable), (
            f"{section} → {anchor!r} is deferred but the scanner does not flag "
            f"it. A deferral for a block that is not uncited is not a "
            f"disclosure, it is a decoration.")


def test_a_deferral_never_hides_the_finding():
    """The whole justification, as an assertion.

    A ruling clears its block and the reader of the output cannot tell the
    block exists. A deferral must print the section, the line, the quantities
    and the block text -- the same things an UNCITED line prints -- plus who
    owns it. If this test fails, the mechanism has become a ruling with a
    longer name and must be removed.
    """
    ok, notes = vp.check_uncited()
    assert ok, notes
    blob = "\n".join(notes)
    for (section, anchor), (opened, owner, record, _reason) in LIVE:
        assert f"DEFERRED  {section}:" in blob
        assert "STILL TRUE, not fixed" in blob
        assert owner in blob and opened in blob and record in blob
    # And the count is reported separately from the ruled and the uncited, so a
    # reader cannot mistake a deferred block for a ruled one.
    assert f"{len(LIVE)} uncited-and-deferred" in blob


def test_the_verdict_line_carries_the_deferral():
    """`papers/verify.py` stage 2 prints a sub-gate's *last* line and no more.

    A deferral visible only in the body of check E's output is invisible to the
    delegator, to `monitor/ci/merge.log`, and to every human reading either.
    """
    r = _run_gate()
    tail = [l for l in r.stdout.strip().splitlines() if l.strip()][-1]
    assert "verify_paper:" in tail
    assert "DEFERRED" in tail, tail
    assert "not fixed" in tail, tail


def test_the_gate_still_exits_zero_with_a_deferral_live():
    """Positive control: the point of the mechanism is the exit code."""
    assert _run_gate().returncode == 0


def _run_gate():
    import subprocess
    import sys
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, str(vp.HERE / "verify_paper.py")],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=str(vp.HERE), env=env)


# ------------------------------------------------- driving each guard until red

def _scratch(monkeypatch, tmp_path, body, deferrals, rulings=None):
    (tmp_path / "07_body.md").write_text(body, encoding="utf-8")
    monkeypatch.setattr(vp, "SECTIONS", tmp_path)
    monkeypatch.setattr(vp, "ADJUDICATED_UNCITED", {} if rulings is None else rulings)
    monkeypatch.setattr(vp, "DEFERRED_UNCITED", deferrals)
    return vp.check_uncited()


GOOD = ("2026-08-04", "RES-2", "CLAUDE.md", "because the repair is not mine")
ANCHOR = "the sheet was sat by 41 readers in one"
BODY = f"A claim: {ANCHOR} sitting.\n"


def test_a_deferral_turns_a_red_block_green_and_says_so(monkeypatch, tmp_path):
    """Positive control for the scratch harness itself."""
    red, _ = _scratch(monkeypatch, tmp_path, BODY, {})
    assert not red, "the fixture block must be uncited, or nothing below is tested"
    ok, notes = _scratch(monkeypatch, tmp_path, BODY, {("07_body.md", ANCHOR): GOOD})
    assert ok
    assert any("DEFERRED" in n for n in notes)


def test_a_deferral_matching_no_block_is_stale(monkeypatch, tmp_path):
    ok, notes = _scratch(
        monkeypatch, tmp_path,
        "A claim: 41 readers sat it (`papers/verify.py`).\n",
        {("07_body.md", ANCHOR): GOOD})
    assert not ok, "a deferral that defers nothing must not pass silently"
    assert any("STALE" in n and "deferral" in n for n in notes)


def test_a_deferral_matching_several_blocks_is_broad(monkeypatch, tmp_path):
    ok, notes = _scratch(monkeypatch, tmp_path, BODY + "\n" + BODY,
                         {("07_body.md", ANCHOR): GOOD})
    assert not ok
    assert any("BROAD" in n and "deferral" in n for n in notes)


def test_a_short_anchor_is_refused(monkeypatch, tmp_path):
    short = ANCHOR[:vp.MIN_ANCHOR - 1]
    ok, notes = _scratch(monkeypatch, tmp_path, BODY,
                         {("07_body.md", short): GOOD})
    assert not ok, "an anchor under MIN_ANCHOR matches prose, not a claim"
    assert any("ANCHOR" in n for n in notes)


def test_a_block_cannot_be_both_ruled_and_deferred(monkeypatch, tmp_path):
    """A ruling clears the block, so it would hide what the deferral discloses.

    Left unguarded, the cheapest way to get a silent green would be to ship
    both: the ruling suppresses the finding and the deferral stands beside it
    looking like disclosure.
    """
    key = ("07_body.md", ANCHOR)
    ok, notes = _scratch(monkeypatch, tmp_path, BODY, {key: GOOD},
                         rulings={key: "ruled as well"})
    assert not ok
    assert any("DOUBLE" in n for n in notes)


def test_a_deferral_whose_record_is_gone_fails(monkeypatch, tmp_path):
    """The written argument is the only thing making a deferral auditable."""
    gone = ("2026-08-04", "RES-2", "papers/no/such/record.md", "reason")
    ok, notes = _scratch(monkeypatch, tmp_path, BODY,
                         {("07_body.md", ANCHOR): gone})
    assert not ok
    assert any("NORECORD" in n for n in notes)


def test_the_table_cannot_grow_past_the_ceiling(monkeypatch, tmp_path):
    """No expiry date only stays defensible while the table cannot grow.

    Nothing else here stops a second deferral, then a third: each one is
    individually well-formed, well-argued and green, and the check ends up
    switched off one row at a time. The ceiling is what makes growth a visible
    decision instead of an accumulation.
    """
    body = BODY + "\nAnother: 41 more readers sat the second sheet at once.\n"
    over = {("07_body.md", ANCHOR): GOOD,
            ("07_body.md", "41 more readers sat the second sheet"): GOOD}
    monkeypatch.setattr(vp, "MAX_DEFERRED", 1)
    ok, notes = _scratch(monkeypatch, tmp_path, body, over)
    assert not ok
    assert any("TOOMANY" in n for n in notes)


def test_the_live_table_is_within_the_ceiling():
    assert len(vp.DEFERRED_UNCITED) <= vp.MAX_DEFERRED


def test_a_broken_deferral_does_not_corrupt_the_ruling_counts(monkeypatch, tmp_path):
    """The summary line's arithmetic must be about the table it names.

    An earlier draft carried deferral failures by appending a sentinel to
    `stale`, which is `ADJUDICATED_UNCITED`'s list -- so one broken deferral
    reported one fewer *ruling* and one more *stale ruling*. The verdict was
    right and the numbers were false, which is the worse half: a reader checks
    the numbers.
    """
    ruling = ("07_body.md", "different claim entirely, ruled on elsewhere")
    body = BODY + "\nA different claim entirely, ruled on elsewhere: 41 rows.\n"
    ok, notes = _scratch(
        monkeypatch, tmp_path, body,
        {("07_body.md", ANCHOR): ("2026-08-04", "RES-2", "no/such/file.md", "r")},
        rulings={ruling: "ruled, and unaffected by the broken deferral"})
    assert not ok
    summary = next(n for n in notes if "claim blocks scanned" in n)
    assert "1 ruled" in summary, summary
    assert "0 stale rulings" in summary, summary
    assert "1 broken deferral(s)" in summary, summary


def test_an_absent_section_is_skipped_not_reported(monkeypatch, tmp_path):
    """The escape the other suites depend on, pinned so it stays narrow.

    It must skip *silently* -- reporting STALE against a section the run never
    looked at would be a false statement about the live paper, printed by a
    scratch-tree run.
    """
    ok, notes = _scratch(monkeypatch, tmp_path, "Nothing quantitative here.\n",
                         {("99_absent.md", ANCHOR): GOOD})
    assert ok
    assert not any("99_absent.md" in n for n in notes)


# ------------------------------------------- check F's corpus narrowing (V31)

def test_the_live_prefixes_are_well_formed():
    for prefix in vp._WALK_SKIP_PREFIXES:
        assert prefix.endswith("/"), prefix
        assert (vp.ROOT / prefix.rstrip("/")).is_dir(), prefix
    assert not vp._bad_skip_prefixes()


def test_a_prefix_that_names_nothing_takes_the_check_red(monkeypatch):
    """Same rule as a stale ruling: a declaration that stopped being true goes.

    Without this the archive could be deleted tomorrow and check F would go on
    narrowing its corpus forever, for a tree that is not there.
    """
    monkeypatch.setattr(vp, "_WALK_SKIP_PREFIXES", ("monitor/no-such-archive/",))
    assert [p for p, _ in vp._bad_skip_prefixes()] == ["monitor/no-such-archive/"]
    ok, notes = vp.check_bare()
    assert not ok, "an exclusion that excuses nothing must not pass silently"
    assert any("STALESKIP" in n for n in notes)


@pytest.mark.parametrize("bad", [
    "monitor/runs/_worktree-scratch-archive",       # no trailing slash
    "/monitor/runs/_worktree-scratch-archive/",     # absolute
    "monitor\\runs\\_worktree-scratch-archive\\",   # host separators
])
def test_a_malformed_prefix_takes_the_check_red(monkeypatch, bad):
    """The slashless form silently over-matches, so it cannot be left to review.

    `monitor/runs/_worktree-scratch-archive` prunes
    `monitor/runs/_worktree-scratch-archive-2/` as well -- a subtree nobody
    declared, excluded by a typo, and invisible in the output because the note
    prints the prefix as written.
    """
    monkeypatch.setattr(vp, "_WALK_SKIP_PREFIXES", (bad,))
    ok, notes = vp.check_bare()
    assert not ok, f"{bad!r} must not be accepted"
    assert any("STALESKIP" in n for n in notes)


def test_the_exclusion_is_announced_with_its_size():
    """Disclosing that an exclusion exists is not disclosing how much it excuses.

    A reader of the green line must be able to tell whether three files were set
    aside or four thousand, without opening the source.
    """
    ok, notes = vp.check_bare()
    assert ok, notes
    blob = "\n".join(notes)
    for prefix in vp._WALK_SKIP_PREFIXES:
        assert prefix in blob, "check F must name what it excluded"
        n_files, n_only = vp._skip_prefix_size(prefix)
        assert n_files > 0
        assert f"{n_files} file(s)" in blob, "and how many it excluded"
        assert f"{n_only} basename(s)" in blob


def test_the_exclusion_note_does_not_claim_the_archive_is_unpublished():
    """It is tracked, and `release/enumerate.py` enumerates by `git ls-files`.

    The first version of this note said "not the published tree", which an
    adversarial pass showed to be false. A gate whose stated evidence is wrong is
    this file's own named failure mode, so the claim is pinned rather than left
    to whoever next edits the sentence.
    """
    _ok, notes = vp.check_bare()
    blob = "\n".join(notes)
    assert "not the published tree" not in blob
    assert "tracked and released" in blob


def test_the_exclusion_prunes_the_archive_and_nothing_else(monkeypatch):
    """It must remove exactly the declared subtree from the basename index.

    The failure this guards is over-matching: a prefix comparison done on raw
    strings, or without the separator normalised, can prune a sibling whose name
    merely starts the same way.
    """
    monkeypatch.setattr(vp, "_BASENAMES", None)
    everything = {p for paths in _index().values() for p in paths}
    assert not any(p.startswith("monitor/runs/_worktree-scratch-archive/")
                   for p in everything)
    # ...and the rest of `monitor/runs/` survives, so the prune is not a prefix
    # match that ran away up the tree.
    assert any(p.startswith("monitor/runs/") for p in everything)


def _index():
    vp._candidates("anything")           # populates the cache
    return vp._BASENAMES


@pytest.mark.parametrize("token", [
    "PARTNER_SYNC.md", "mark.py", "validate.py", "potential.py",
    "p13_fd_dividend.py", "SURVEY-solver-status.md", "SURVEY-empty-as-negative.md",
    "SURVEY-environment-as-semantics.md", "SURVEY-success-as-truth.md",
])
def test_each_token_the_archive_made_ambiguous_is_unique_again(token):
    """Not "check F is green" -- that could be true for the wrong reason.

    These nine are the tokens the 2026-07-31 salvage duplicated. Each must
    resolve to exactly one path, and that path must not be in the archive: a
    token whose only survivor was the archived copy would have gone from
    ambiguous to *absent*, and check F reports those differently.
    """
    cands = vp._candidates(token)
    assert len(cands) == 1, cands
    assert "_worktree-scratch-archive" not in cands[0]
