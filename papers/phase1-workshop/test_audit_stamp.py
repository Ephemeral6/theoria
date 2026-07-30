"""Negative control for check G — `audit_stamp.py`.

Check G exists because `CITECHECK.md` and `REVIEW.md` both reported PASS while
pinning a `PAPER.md` that had since tripled: an audit performed once, reported
as a property of the current object. So the one thing this suite may not do is
repeat that mistake in test form. **Every tree here is synthetic**, built in
`tmp_path` and handed to `check(paper_dir, root)` — the parameters exist for
exactly this. A test pinned to the live `papers/phase1-workshop/` would go red
on the next paragraph anyone writes into `PAPER.md`, and a gate whose own tests
break on ordinary work is a gate that gets switched off; that is the receipt
`papers/verify.py`'s docstring already carries.

Every stamp here is *measured*, never typed. Hardcoding `bytes: 237` in a
fixture would make this file fail on Windows the moment a `\\n` became `\\r\\n`,
and it would also be the very defect G4 refuses.

One rule, one test, and each one asserts two things: that the check goes red,
and that the finding names the thing that is wrong. A red gate that does not say
what it caught sends the reader back to the archaeology this check was built to
end.

Run:  python -m pytest papers/phase1-workshop/test_audit_stamp.py
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_stamp as ag  # noqa: E402

PAPER_REL = "papers/phase1-workshop/PAPER.md"


# --------------------------------------------------------------- the scratch tree

def body(n: int, word: str = "line") -> str:
    """A paper of exactly `n` newlines — `wc -l` semantics, as the stamp says."""
    return "".join(f"{word} {i}\n" for i in range(n))


def measure_text(text: str) -> tuple[str, int, int]:
    """`measure()` for content that is not on disk, so a test can pin a state
    the tree has moved past without ever having to write it."""
    b = text.encode("utf-8")
    return hashlib.sha256(b).hexdigest(), b.count(b"\n"), len(b)


def write(path: Path, text: str) -> Path:
    """Write with LF, always, on every platform.

    `Path.write_text` translates `\\n` to `\\r\\n` on Windows, which would move
    every byte count in this file by one per line and make the fixtures disagree
    with themselves across platforms. The repository pins LF in `.gitattributes`
    for the same reason one directory up."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def make_tree(tmp_path: Path, lines: int = 31) -> tuple[Path, Path, Path]:
    """`(root, paper_dir, paper)` — a synthetic repository of one paper."""
    paper = write(tmp_path / PAPER_REL, body(lines))
    return tmp_path, paper.parent, paper


def fields_for(root: Path, rel: str = PAPER_REL, **overrides) -> dict:
    """A stamp measured off the real bytes of `rel`, then mutated on purpose."""
    sha, lines, nbytes = ag.measure(root / rel)
    f = {
        "target": rel,
        "sha256": sha,
        "lines": str(lines),
        "bytes": str(nbytes),
        "scope": "full text",
        "status": "binding",
        "date": "2026-07-30",
    }
    f.update({k: str(v) for k, v in overrides.items()})
    return f


def stamp_block(lines: list[str]) -> str:
    return "```audit-stamp\n" + "".join(f"{line}\n" for line in lines) + "```\n"


def report(paper_dir: Path, name: str, fields: dict | None = None,
           raw: list[str] | None = None, prose: str = "The audit ran.\n") -> Path:
    """Write an audit report. `raw` writes stamp lines verbatim (for the
    malformed cases); `fields` renders them; neither writes no stamp at all."""
    if raw is None and fields is not None:
        raw = [f"{k}: {v}" for k, v in fields.items()]
    head = f"# {name}\n\n"
    block = "" if raw is None else stamp_block(raw) + "\n"
    return write(paper_dir / name, head + block + prose)


def findings(notes: list[str]) -> str:
    return "\n".join(n for n in notes if n.strip().startswith("FAIL"))


# ------------------------------------------------------------------ the fixtures
# A control on the controls: if these drift, every byte count below drifts with
# them silently, so they are asserted rather than assumed.

def test_the_fixture_has_wc_l_line_semantics(tmp_path):
    """`lines` is the newline count, not the newline count plus one. The two old
    audits disagreed about this, and an off-by-one in a staleness stamp is
    indistinguishable from a paper that gained a line."""
    _, _, paper = make_tree(tmp_path, lines=31)
    _, lines, nbytes = ag.measure(paper)
    assert lines == 31
    assert nbytes == len(body(31).encode("utf-8"))
    assert paper.read_bytes().endswith(b"\n")
    assert b"\r" not in paper.read_bytes(), "CRLF crept in; every count below is wrong"


# ------------------------------------------------------------------------- G1

def test_a_report_with_no_stamp_is_refused(tmp_path):
    """The pre-P18 state exactly: a report a reader cannot date without `git
    log`. It is refused rather than skipped, because skipping it is how two
    unpinned audits sat green for weeks."""
    root, paper_dir, _ = make_tree(tmp_path)
    write(paper_dir / "REVIEW.md", "# REVIEW\n\nI read the paper. It was fine.\n")
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    assert "REVIEW.md" in findings(notes)
    assert "no ```audit-stamp block" in findings(notes)


def test_parse_stamp_reports_the_absence_rather_than_raising(tmp_path):
    """`parse_stamp` returns `(None, err)` on purpose: the caller has to keep
    going and report on the other files, so one bad report may not abort the
    walk."""
    fields, err = ag.parse_stamp("# REVIEW\n\nNo stamp here.\n")
    assert fields is None
    assert err is not None and "audit-stamp" in err


# ------------------------------------------------------------------------- G2

def _mutate(root, **overrides):
    return [f"{k}: {v}" for k, v in fields_for(root, **overrides).items()]


def _drop(root, key):
    return [f"{k}: {v}" for k, v in fields_for(root).items() if k != key]


G2_CASES = [
    pytest.param(lambda r: _drop(r, "scope"), ["missing", "scope"], id="missing-key"),
    pytest.param(lambda r: _drop(r, "date"), ["missing", "date"], id="missing-date"),
    pytest.param(lambda r: _mutate(r, status="partial"),
                 ["'partial'", "binding/stale", "third value"], id="status-partial"),
    pytest.param(lambda r: _mutate(r, status="mostly current"),
                 ["'mostly current'", "third value"], id="status-mostly-current"),
    pytest.param(lambda r: _mutate(r, lines="twelve"),
                 ["lines", "'twelve'", "not an integer"], id="lines-not-a-number"),
    pytest.param(lambda r: _mutate(r, bytes="1,318"),
                 ["bytes", "'1,318'", "not an integer"], id="bytes-with-a-comma"),
    pytest.param(lambda r: _mutate(r, sha256="4208b69c"),
                 ["'4208b69c'", "64 lowercase hex"], id="sha-truncated"),
    pytest.param(lambda r: _mutate(r, sha256=ag.measure(r / PAPER_REL)[0].upper()),
                 ["64 lowercase hex"], id="sha-uppercase"),
    pytest.param(lambda r: _mutate(r, sha256="z" + ag.measure(r / PAPER_REL)[0][1:]),
                 ["64 lowercase hex"], id="sha-not-hex"),
    pytest.param(lambda r: _mutate(r) + ["this stamp is basically current"],
                 ["not `key: value`", "basically current"], id="prose-in-the-block"),
]


@pytest.mark.parametrize("build,expected", G2_CASES)
def test_a_malformed_stamp_fails_and_names_the_field(tmp_path, build, expected):
    """Each of these is a stamp that *looks* stamped. The finding has to name
    the offending field, or the author is left diffing a seven-line block by
    eye."""
    root, paper_dir, _ = make_tree(tmp_path)
    report(paper_dir, "CITECHECK.md", raw=build(root))
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    text = findings(notes)
    assert "CITECHECK.md" in text
    for token in expected:
        assert token in text, f"the finding never names {token!r}:\n{text}"


def test_a_third_status_is_the_defect_the_stamp_exists_to_refuse(tmp_path):
    """S28's lesson, restated here: the moment a status can mean "sort of", the
    stale case stops being loud. This is the one G2 case with a rationale rather
    than a syntax rule, so it is pinned on its own as well."""
    root, _, _ = make_tree(tmp_path)
    assert ag.STATUSES == ("binding", "stale")
    fields, err = ag.parse_stamp(stamp_block(_mutate(root, status="under review")))
    assert fields is None
    assert "under review" in err and "third value" in err


def test_extra_keys_and_comments_do_not_break_a_good_stamp(tmp_path):
    """The counterpart to the G2 battery: a stamp that carries more than the
    seven required keys is legal, and a strict parser here would push authors to
    strip the context that makes the block readable."""
    root, paper_dir, _ = make_tree(tmp_path)
    raw = _mutate(root) + ["# a comment", "", "auditor: OPS-A", "notes: two passes"]
    report(paper_dir, "CITECHECK.md", raw=raw)
    ok, notes = ag.check(paper_dir, root)
    assert ok, findings(notes)


@pytest.mark.xfail(strict=True, reason=(
    "BUG in audit_stamp.py: `parse_stamp` gates lines/bytes on `str.isdigit()`, "
    "which is True for numeric characters that `int()` refuses -- superscript "
    "two is the short example. The stamp is therefore accepted as valid, and "
    "`check()` then raises ValueError at `int(f['lines'])` instead of returning "
    "a finding. That breaks parse_stamp's stated contract ('returning the error "
    "rather than raising, because every caller here is a check that has to keep "
    "going'): one exotic stamp aborts the walk and the other reports are never "
    "read. The fix is `.isascii() and .isdigit()`, or try/except int(). Not "
    "applied here -- this suite may not edit the gate."))
def test_a_numeric_but_uncastable_lines_value_is_a_finding_not_a_crash(tmp_path):
    root, paper_dir, _ = make_tree(tmp_path)
    report(paper_dir, "CITECHECK.md", raw=_mutate(root, lines="²"))
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    assert "not an integer" in findings(notes)


# ------------------------------------------------------------------------- G3

def test_a_binding_stamp_that_no_longer_covers_its_target_fails(tmp_path):
    """The whole finding, in miniature: `status: binding` against a paper that
    has moved. The finding must print both states and the signed drift, because
    "stale" is a label and "pinned at 9 lines, now 31, +22" is something a
    reader can act on without opening `git log`."""
    root, paper_dir, paper = make_tree(tmp_path, lines=31)
    old_sha, old_lines, old_bytes = measure_text(body(9))
    cur_sha, cur_lines, cur_bytes = ag.measure(paper)
    report(paper_dir, "CITECHECK.md", fields_for(
        root, sha256=old_sha, lines=old_lines, bytes=old_bytes, status="binding"))

    ok, notes = ag.check(paper_dir, root)
    assert not ok
    text = findings(notes)
    assert "CITECHECK.md" in text and "binding" in text
    # both states...
    assert old_sha[:8] in text and cur_sha[:8] in text
    assert f"{old_lines} lines" in text, "the pinned line count is not printed"
    assert f"{cur_lines} lines" in text, "the current line count is not printed"
    assert f"{old_bytes} bytes" in text and f"{cur_bytes} bytes" in text
    # ...and the drift, signed.
    assert f"{cur_lines - old_lines:+d} lines" in text
    assert f"{cur_bytes - old_bytes:+d} bytes" in text
    # ...and what to do about it, which is the half a bare FAIL leaves out.
    assert "stale" in text and "superseded_by" in text


def test_the_drift_is_signed_when_the_paper_shrinks(tmp_path):
    """A deletion is drift too. `{:+d}` is load-bearing: an unsigned "22 lines"
    reads as growth in both directions."""
    root, paper_dir, _ = make_tree(tmp_path, lines=9)
    old_sha, old_lines, old_bytes = measure_text(body(31))
    report(paper_dir, "REVIEW.md", fields_for(
        root, sha256=old_sha, lines=old_lines, bytes=old_bytes))
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    assert "-22 lines" in findings(notes)


def test_a_stamp_pinning_a_target_that_does_not_exist_fails(tmp_path):
    """A report can go stale by having its target renamed out from under it, and
    then it pins nothing at all."""
    root, paper_dir, _ = make_tree(tmp_path)
    fields = fields_for(root)
    fields["target"] = "papers/phase1-workshop/PAPER_OLD.md"
    report(paper_dir, "REVIEW.md", fields)
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    assert "PAPER_OLD.md" in findings(notes) and "does not exist" in findings(notes)


# ------------------------------------------------------------------------- G4

def test_a_binding_stamp_with_typed_numbers_fails(tmp_path):
    """The off-by-one: `wc -l` versus `wc -l` plus one. The sha is right, so the
    audit really did run against this text -- but the numbers beside it were
    typed, and those are what a human actually reads. `CITECHECK.md`'s prose
    said "1319 lines" of a blob with 1318 newlines, which is exactly one line of
    growth's worth of indistinguishable."""
    root, paper_dir, paper = make_tree(tmp_path, lines=31)
    _, cur_lines, cur_bytes = ag.measure(paper)
    report(paper_dir, "CITECHECK.md", fields_for(root, lines=cur_lines + 1))
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    text = findings(notes)
    assert f"{cur_lines + 1} lines" in text and f"{cur_lines} / {cur_bytes}" in text
    assert "wc -l" in text, "the finding must state the convention it is enforcing"
    assert "sha256 matches" in text, "or the author will re-run an audit they do not need"


def test_a_binding_stamp_with_the_wrong_byte_count_fails(tmp_path):
    """The other half of G4. Bytes are the number the coverage percentage is
    computed from, so a typo there mis-states how much of the paper is covered.

    The overstatement direction is the one to pin: a stamp claiming *more* bytes
    than the target has is a report claiming coverage it does not have, which is
    the whole of P18. (This test asked for `cur_bytes - 400` until 2026-07-30;
    the fixture paper is 238 bytes, so that stamped `-162` and was refused by
    G2's integer rule before G4 ever ran -- it passed through the gate it was
    written to exercise. `test_...negative_byte_count...` below now covers the
    case it was accidentally testing.)"""
    root, paper_dir, paper = make_tree(tmp_path)
    _, _, cur_bytes = ag.measure(paper)
    report(paper_dir, "CITECHECK.md", fields_for(root, bytes=cur_bytes + 400))
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    assert f"{cur_bytes + 400} bytes" in findings(notes)
    assert "sha256 matches" in findings(notes), (
        "G4 must say the sha matched, or the author re-runs an audit they do not need")


def test_a_negative_byte_count_is_refused(tmp_path):
    """A byte count cannot be negative, and `isdigit()` is what refuses it. Pinned
    because it was previously refused only as a side effect of another test's
    arithmetic: nothing asserted it, so the day `lines`/`bytes` moved to a signed
    parse, a stamp of `-162` would have become a G4 mismatch finding -- reported
    as drift in the paper rather than as a malformed stamp."""
    root, paper_dir, paper = make_tree(tmp_path)
    report(paper_dir, "CITECHECK.md", fields_for(root, bytes=-162))
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    assert "not an integer" in findings(notes)


# ------------------------------------------------------------------------- G5

def test_a_stale_stamp_with_no_successor_fails(tmp_path):
    """An audit may be retired; it may not be retired into nowhere. The coverage
    claim it was carrying does not evaporate when the report does -- and this is
    the escape hatch G3 points every author at, so it has to terminate
    somewhere."""
    root, paper_dir, _ = make_tree(tmp_path)
    old_sha, old_lines, old_bytes = measure_text(body(9))
    report(paper_dir, "CITECHECK.md", fields_for(
        root, status="stale", sha256=old_sha, lines=old_lines, bytes=old_bytes))
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    text = findings(notes)
    assert "CITECHECK.md" in text and "superseded_by" in text
    assert "stale" in text


def test_an_empty_superseded_by_is_no_successor(tmp_path):
    """`superseded_by:` with nothing after it is the same nowhere, spelled
    differently, and `.strip()` is what makes the two identical."""
    root, paper_dir, _ = make_tree(tmp_path)
    old_sha, old_lines, old_bytes = measure_text(body(9))
    fields = fields_for(root, status="stale", sha256=old_sha,
                        lines=old_lines, bytes=old_bytes)
    fields["superseded_by"] = "   "
    report(paper_dir, "REVIEW.md", fields)
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    assert "superseded_by" in findings(notes)


# ------------------------------------------------------------------------- G6

def _stale_fields(root, successor):
    old_sha, old_lines, old_bytes = measure_text(body(9))
    f = fields_for(root, status="stale", sha256=old_sha,
                   lines=old_lines, bytes=old_bytes)
    f["superseded_by"] = successor
    return f


def test_a_successor_that_does_not_exist_fails(tmp_path):
    """The chain has to terminate on something a reader can open. A retirement
    naming a file that was never written is a coverage claim that has left the
    tree entirely."""
    root, paper_dir, _ = make_tree(tmp_path)
    report(paper_dir, "CITECHECK.md", _stale_fields(root, "CITECHECK-2026-08-01.md"))
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    text = findings(notes)
    assert "CITECHECK-2026-08-01.md" in text, "the finding must name the missing successor"
    assert "names no file" in text


def test_a_successor_with_no_stamp_fails(tmp_path):
    """Otherwise the retirement just moves the unpinned claim one file along --
    which is the P18 state with an extra hop in it."""
    root, paper_dir, _ = make_tree(tmp_path)
    report(paper_dir, "CITECHECK.md", _stale_fields(root, "REVIEW.md"))
    write(paper_dir / "REVIEW.md", "# REVIEW\n\nA successor that pins nothing.\n")
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    text = findings(notes)
    assert "CITECHECK.md" in text and "REVIEW.md" in text
    assert "no valid stamp" in text
    assert "audit-stamp" in text, "the successor's own parse error must be quoted"


def test_a_successor_with_a_broken_stamp_fails(tmp_path):
    """Present but malformed is the same nowhere: G6 asks whether the successor
    says what *it* covers, not merely whether the file opens."""
    root, paper_dir, _ = make_tree(tmp_path)
    report(paper_dir, "CITECHECK.md", _stale_fields(root, "REVIEW.md"))
    report(paper_dir, "REVIEW.md", raw=_mutate(root, status="partial"))
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    assert "no valid stamp" in findings(notes)


# ------------------------------------------------------------------------- G7

def test_a_paper_directory_with_no_audits_is_red(tmp_path):
    """The most important assertion in this file.

    With no reports, G1-G6 are each vacuously satisfied and the check reports
    the *identical* green it would report for a fully stamped, fully current set
    of audits. That is the failure mode of `papers/verify.py` one level up: an
    empty walk that reads as a pass. Deleting `CITECHECK.md` must never be the
    cheapest way to clear check G.
    """
    root, _, paper = make_tree(tmp_path)
    paper_dir = paper.parent
    assert ag.audit_files(paper_dir) == []
    ok, notes = ag.check(paper_dir, root)
    assert not ok, "an empty walk passed check G"
    text = findings(notes)
    assert "no audit report" in text
    assert paper_dir.name in text
    for pattern in ag.AUDIT_GLOBS:
        assert pattern in text, "the finding must say what it looked for"


def test_a_directory_of_non_audits_is_still_red(tmp_path):
    """Files near the audits are not audits. `OPEN_ITEMS.md` and `README.md`
    live in the same directory and pin nothing, so their presence must not be
    mistaken for coverage."""
    root, _, paper = make_tree(tmp_path)
    paper_dir = paper.parent
    for name in ("README.md", "OPEN_ITEMS.md", "PROVENANCE.md", "OUTLINE.md"):
        write(paper_dir / name, f"# {name}\n\nNot an audit.\n")
    ok, notes = ag.check(paper_dir, root)
    assert not ok, "four unrelated markdown files satisfied check G"
    assert "no audit report" in findings(notes)


# ------------------------------------------------------------------------- G8

def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, timeout=120)


def git_init(root: Path) -> None:
    """A throwaway repository in `tmp_path`, or a skip.

    G8 is the only rule that needs real history, and history cannot be faked
    cheaply. On a machine with no git the rule is unenforceable, which
    `_history_blobs` already treats as UNVERIFIED rather than as a pass -- so
    skipping here is consistent with the gate rather than papering over it."""
    try:
        version = subprocess.run(["git", "--version"], capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover
        pytest.skip(f"git unavailable: {exc}")
    if version.returncode != 0:  # pragma: no cover
        pytest.skip("git unavailable")
    if _git(root, "init", "-q").returncode != 0:  # pragma: no cover
        pytest.skip("git init failed in tmp_path")
    for cfg in (("user.email", "test@example.invalid"), ("user.name", "test"),
                ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
        _git(root, "config", *cfg)


def git_commit(root: Path, message: str) -> None:
    if _git(root, "add", "-A").returncode != 0:  # pragma: no cover
        pytest.skip("git add failed in tmp_path")
    done = _git(root, "commit", "-q", "-m", message)
    if done.returncode != 0:  # pragma: no cover
        pytest.skip(f"git commit failed in tmp_path: {done.stderr.strip()}")


def test_a_stamp_that_contradicts_its_own_blob_fails(tmp_path):
    """The one real way to defeat G3 is to stamp a sha you did not measure.

    A stale stamp is never compared against the current file -- that is the
    point of `stale` -- so without G8 an author could copy any sha out of `git
    log`, type any two numbers beside it, and the report would read as a
    honestly-retired audit of a state it never covered. Here the pinned sha *is*
    in history, at counts the stamp disagrees with.
    """
    root, paper_dir, paper = make_tree(tmp_path, lines=9)
    git_init(root)
    git_commit(root, "first draft")
    old_sha, old_lines, old_bytes = ag.measure(paper)

    write(paper, body(31))
    git_commit(root, "the assembled draft")

    fields = fields_for(root, status="stale", sha256=old_sha,
                        lines=old_lines + 7, bytes=old_bytes)
    fields["superseded_by"] = "CITECHECK-2026-07-30.md"
    report(paper_dir, "REVIEW.md", fields)
    report(paper_dir, "CITECHECK-2026-07-30.md", fields_for(root))

    ok, notes = ag.check(paper_dir, root)
    assert not ok, "a stamp contradicting the blob it names passed"
    text = findings(notes)
    assert "REVIEW.md" in text and old_sha[:8] in text
    assert f"{old_lines} lines / {old_bytes} bytes" in text, "the blob's real counts"
    assert f"{old_lines + 7} / {old_bytes}" in text, "the stamp's claimed counts"
    assert "history" in text


def test_a_sha_absent_from_history_is_not_a_failure(tmp_path):
    """Audits legitimately run against an uncommitted working tree -- the real
    `CITECHECK.md` records the paper being edited underneath it mid-pass. If
    absence from history were evidence, the gate would refuse the ordinary case
    and get switched off; absence is not evidence here."""
    root, paper_dir, paper = make_tree(tmp_path, lines=9)
    git_init(root)
    git_commit(root, "first draft")

    write(paper, body(31))            # edited, deliberately not committed
    cur_sha = ag.measure(paper)[0]
    history = ag._history_blobs(root, PAPER_REL)
    assert history, "the fixture proved nothing: git history was never readable"
    assert cur_sha not in history, "the fixture committed the state it meant to leave dirty"

    report(paper_dir, "CITECHECK.md", fields_for(root))
    ok, notes = ag.check(paper_dir, root)
    assert ok, findings(notes)


def test_a_stamp_agreeing_with_its_blob_passes(tmp_path):
    """The positive control for G8: a stale report whose numbers were actually
    measured from the sha beside them is exactly what the rule is protecting."""
    root, paper_dir, paper = make_tree(tmp_path, lines=9)
    git_init(root)
    git_commit(root, "first draft")
    old_sha, old_lines, old_bytes = ag.measure(paper)

    write(paper, body(31))
    git_commit(root, "the assembled draft")

    fields = fields_for(root, status="stale", sha256=old_sha,
                        lines=old_lines, bytes=old_bytes)
    fields["superseded_by"] = "CITECHECK-2026-07-30.md"
    report(paper_dir, "REVIEW.md", fields)
    report(paper_dir, "CITECHECK-2026-07-30.md", fields_for(root))

    ok, notes = ag.check(paper_dir, root)
    assert ok, findings(notes)


def test_no_history_is_reported_as_unverified_not_as_confirmed(tmp_path):
    """An unenforceable check must be silent about passing rather than claim a
    green it did not earn. Outside a repository G8 cannot run, and the note has
    to say so -- otherwise a reader takes the ok line as confirmation that the
    pinned counts were checked against the blob, which is the same
    once-performed-reported-as-current error one level down."""
    root, paper_dir, _ = make_tree(tmp_path)
    assert ag._history_blobs(root, PAPER_REL) == {}, "tmp_path is unexpectedly a repo"
    report(paper_dir, "CITECHECK.md", fields_for(root))
    ok, notes = ag.check(paper_dir, root)
    assert ok
    assert any("UNVERIFIED" in n for n in notes)


# ------------------------------------------------------------- the green case

def green_tree(tmp_path: Path) -> tuple[Path, Path]:
    """A correctly stamped binding audit, and a correctly retired one naming it.

    This is the state the gate is asking for, and it has to be reachable: a rule
    set nobody can satisfy is a rule set that gets deleted rather than met."""
    root, paper_dir, paper = make_tree(tmp_path, lines=31)
    old_sha, old_lines, old_bytes = measure_text(body(9))
    report(paper_dir, "CITECHECK-2026-07-30.md", fields_for(root))
    stale = fields_for(root, status="stale", sha256=old_sha,
                       lines=old_lines, bytes=old_bytes)
    stale["superseded_by"] = "CITECHECK-2026-07-30.md"
    report(paper_dir, "CITECHECK.md", stale)
    return root, paper_dir


def test_the_intended_state_passes(tmp_path):
    root, paper_dir = green_tree(tmp_path)
    ok, notes = ag.check(paper_dir, root)
    assert ok, findings(notes)
    assert findings(notes) == ""
    assert any("binding on" in n and "CITECHECK-2026-07-30.md" in n for n in notes)
    assert any("superseded by" in n and "CITECHECK.md" in n for n in notes)


def test_the_green_notes_say_what_is_covered(tmp_path):
    """A green that prints nothing is how the old pair stayed invisible. The ok
    line has to carry the sha and the counts, so the next reader sees the
    coverage without opening the report."""
    root, paper_dir = green_tree(tmp_path)
    sha, lines, nbytes = ag.measure(root / PAPER_REL)
    _, notes = ag.check(paper_dir, root)
    binding = [n for n in notes if "binding on" in n]
    assert len(binding) == 1
    assert sha[:8] in binding[0]
    assert f"{lines} lines" in binding[0] and f"{nbytes} bytes" in binding[0]
    # And the retired one says how much of the *current* paper it was.
    stale = [n for n in notes if "superseded by" in n]
    assert len(stale) == 1 and "%" in stale[0]


def test_a_paper_edit_turns_the_binding_audit_red_and_the_two_line_fix_clears_it(tmp_path):
    """The trade this gate makes, pinned end to end.

    Staleness is loud, not illegal: editing the paper goes red, and the author
    clears it by flipping `binding` to `stale` and naming a successor rather
    than by re-running a human audit. If this ever stops being a two-line fix,
    the gate blocks ordinary work and gets switched off.
    """
    root, paper_dir = green_tree(tmp_path)
    write(root / PAPER_REL, body(40))                   # somebody writes a section
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    assert "CITECHECK-2026-07-30.md" in findings(notes)

    # The two-line fix: status, and a name.
    old = fields_for(root)                              # measured before the edit? no --
    old["sha256"], old["lines"], old["bytes"] = (
        f for f in map(str, measure_text(body(31))))
    old["status"] = "stale"
    old["superseded_by"] = "REVIEW-2026-08-01.md"
    report(paper_dir, "CITECHECK-2026-07-30.md", old)
    report(paper_dir, "REVIEW-2026-08-01.md", fields_for(root))
    ok, notes = ag.check(paper_dir, root)
    assert ok, findings(notes)


# ------------------------------------------------------------- binding_audits

def test_binding_audits_names_the_currently_binding_report(tmp_path):
    """Exists so prose can point at whichever audit is binding *now*.
    `verify_paper.py` told readers "`CITECHECK.md` is the human audit that does
    that" while `CITECHECK.md` covered a third of the paper: a sentence that was
    true when written and became false with nobody editing it."""
    root, paper_dir = green_tree(tmp_path)
    assert ag.binding_audits("CITECHECK", paper_dir, root) == ["CITECHECK-2026-07-30.md"]
    assert ag.binding_audits("REVIEW", paper_dir, root) == []


def test_binding_audits_is_empty_when_every_report_is_stale(tmp_path):
    """The state the paper is actually in between audits, and the caller has to
    be able to tell -- an empty list is what makes "no current audit covers
    this" sayable in prose."""
    root, paper_dir, _ = make_tree(tmp_path, lines=31)
    old_sha, old_lines, old_bytes = measure_text(body(9))
    for name in ("CITECHECK.md", "CITECHECK-2026-07-30.md"):
        f = fields_for(root, status="stale", sha256=old_sha,
                       lines=old_lines, bytes=old_bytes)
        f["superseded_by"] = "REVIEW.md"
        report(paper_dir, name, f)
    report(paper_dir, "REVIEW.md", fields_for(root))
    assert ag.binding_audits("CITECHECK", paper_dir, root) == []
    assert ag.binding_audits("REVIEW", paper_dir, root) == ["REVIEW.md"]


def test_binding_audits_ignores_a_binding_stamp_that_has_gone_stale(tmp_path):
    """A report claiming `binding` on a moved paper is precisely the P18 defect;
    the accessor must not repeat the claim just because the file makes it."""
    root, paper_dir, _ = make_tree(tmp_path, lines=31)
    old_sha, old_lines, old_bytes = measure_text(body(9))
    report(paper_dir, "CITECHECK.md", fields_for(
        root, sha256=old_sha, lines=old_lines, bytes=old_bytes))
    assert ag.binding_audits("CITECHECK", paper_dir, root) == []


def test_binding_audits_ignores_an_unstamped_report(tmp_path):
    root, paper_dir, _ = make_tree(tmp_path)
    write(paper_dir / "CITECHECK.md", "# CITECHECK\n\nNo stamp.\n")
    assert ag.binding_audits("CITECHECK", paper_dir, root) == []


# --------------------------------------------------------------- what is an audit

def test_the_audit_set_is_the_declared_one(tmp_path):
    """`REVIEW_TRIAGE.md` is a disposition record *about* an audit, not an audit:
    it pins nothing, so demanding a stamp of it would be demanding a coverage
    claim it cannot make. The dated forms are in, because that is the shape a
    re-audit takes."""
    root, _, paper = make_tree(tmp_path)
    paper_dir = paper.parent
    audits = ("CITECHECK.md", "CITECHECK-2026-07-30.md", "REVIEW.md", "REVIEW-foo.md")
    others = ("REVIEW_TRIAGE.md", "README.md", "OPEN_ITEMS.md", "PROVENANCE.md",
              "CITECHECK.md.bak", "notes-REVIEW.md")
    for name in audits + others:
        write(paper_dir / name, f"# {name}\n")
    found = {p.name for p in ag.audit_files(paper_dir)}
    assert found == set(audits)
    assert "REVIEW_TRIAGE.md" not in found, "a triage record was demanded to be an audit"
    assert root == tmp_path


def test_a_triage_record_alone_does_not_satisfy_the_gate(tmp_path):
    """The two halves of the exclusion have to hold together: if
    `REVIEW_TRIAGE.md` is not an audit, then a directory holding only it is a
    directory with no audits, and G7 must fire. Excluding a file from the walk
    and from the count are the same decision."""
    root, _, paper = make_tree(tmp_path)
    write(paper.parent / "REVIEW_TRIAGE.md", "# REVIEW_TRIAGE\n\nDispositions.\n")
    ok, notes = ag.check(paper.parent, root)
    assert not ok
    assert "no audit report" in findings(notes)


def test_a_directory_is_not_an_audit_report(tmp_path):
    """`REVIEW-runs/` would match the glob and is not a file. `is_file()` is what
    stops the walk from trying to read it."""
    root, _, paper = make_tree(tmp_path)
    (paper.parent / "REVIEW-archive.md").mkdir(parents=True)
    assert ag.audit_files(paper.parent) == []
    ok, _ = ag.check(paper.parent, root)
    assert not ok
    assert root == tmp_path


def test_audit_files_is_deterministic(tmp_path):
    """Determinism is a stated requirement of this repository, and a gate whose
    findings reorder between runs cannot be diffed. The globs overlap and the
    implementation goes through a `set`, which is exactly where an order would
    otherwise come from the hash seed."""
    root, _, paper = make_tree(tmp_path)
    paper_dir = paper.parent
    for name in ("REVIEW.md", "CITECHECK.md", "REVIEW-b.md", "CITECHECK-a.md",
                 "REVIEW-a.md", "CITECHECK-b.md"):
        write(paper_dir / name, f"# {name}\n")
    runs = [ag.audit_files(paper_dir) for _ in range(5)]
    assert all(r == runs[0] for r in runs[1:])
    names = [p.name for p in runs[0]]
    assert names == sorted(names, key=str.lower)
    assert len(names) == 6
    # The findings inherit that order, which is the property a reader diffs.
    first = [n for n in ag.check(paper_dir, root)[1]]
    assert [n for n in ag.check(paper_dir, root)[1]] == first
    assert root == tmp_path


# --------------------------------------------------------- the walk keeps going

def test_one_broken_report_does_not_hide_the_others(tmp_path):
    """`parse_stamp` returns its error rather than raising for this reason: the
    check has to report on every file. A gate that stops at the first bad stamp
    turns one fix into n rounds of running it."""
    root, paper_dir, _ = make_tree(tmp_path, lines=31)
    old_sha, old_lines, old_bytes = measure_text(body(9))
    write(paper_dir / "REVIEW.md", "# REVIEW\n\nNo stamp at all.\n")
    report(paper_dir, "CITECHECK.md", fields_for(
        root, sha256=old_sha, lines=old_lines, bytes=old_bytes))
    report(paper_dir, "REVIEW-a.md", raw=_mutate(root, status="partial"))
    ok, notes = ag.check(paper_dir, root)
    assert not ok
    text = findings(notes)
    for name in ("REVIEW.md", "CITECHECK.md", "REVIEW-a.md"):
        assert name in text, f"{name}'s finding was swallowed by an earlier one"
