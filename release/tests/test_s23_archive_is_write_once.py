"""`replicate.py` may read the S23 archive. It may not rewrite it.

The defect: `verify.sh` runs `release/runs/20260728T234923Z-S23/replicate.py`
on every green run, and the script's last act was to write its own output over
`before/` and `after/` -- an in-place mutation of a write-once run directory by
the check that exists to read it. It corrupted the record twice; `e184942e`
restored two files by hand and said the root cause was queued. This is the
queued fix, and these are the tests that keep it fixed.

What is pinned here:

* the module contains no writer aimed at the archive except the one behind
  `--adopt` (a structural check, because the failure mode is a *new* writer
  appearing, not the old one coming back);
* a mismatch on the strict side reports and returns 1 without touching a byte;
* the two sides are different kinds of claim -- `before/` is a frozen commit's
  output and is strict; `after/` is the working tree's output on the archive
  date and drifts legitimately;
* the whole thing is still green on this tree, and green means the archive was
  read, not rewritten.
"""
import importlib.util
import os
import shutil

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASE = os.path.dirname(HERE)
RUN_DIR = os.path.join(RELEASE, "runs", "20260728T234923Z-S23")
SCRIPT = os.path.join(RUN_DIR, "replicate.py")


def _load():
    spec = importlib.util.spec_from_file_location("_s23_replicate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def rep():
    return _load()


def _archive_state():
    state = {}
    for side in ("before", "after"):
        directory = os.path.join(RUN_DIR, side)
        for name in sorted(os.listdir(directory)):
            path = os.path.join(directory, name)
            with open(path, "rb") as fh:
                state["%s/%s" % (side, name)] = (fh.read(), os.path.getmtime(path))
    return state


# ------------------------------------------------------- the structural rule

def test_only_adopt_writes_into_the_archive(rep):
    """`HERE` is the archive. Every `open(..., "w")` under it must be `adopt`.

    Written structurally on purpose: the regression to guard against is a new
    convenience writer being added years from now, and a test that only replays
    the old bug would not see it.
    """
    import ast

    with open(SCRIPT, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), SCRIPT)

    def _opens_for_writing(func):
        for node in ast.walk(func):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "open"
                    and len(node.args) > 1
                    and isinstance(node.args[1], ast.Constant)
                    and set("wa") & set(str(node.args[1].value))):
                return True
        return False

    def _builds_an_archive_path(func):
        """`os.path.join(HERE, ...)` with no `CURRENT` in it is the archive."""
        for node in ast.walk(func):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "join"):
                dumped = ast.dump(ast.Tuple(elts=list(node.args), ctx=ast.Load()))
                if "'HERE'" in dumped and "'CURRENT'" not in dumped:
                    return True
        return False

    writers = [f.name for f in ast.walk(tree)
               if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
               and _opens_for_writing(f) and _builds_an_archive_path(f)]

    assert writers == ["adopt"], (
        "the archive must have exactly one writer, `adopt`, reached only by an "
        "explicit --adopt; found %s" % (writers or "none -- adopt() is gone"))


def test_current_is_untracked(rep):
    """The scratch directory must not dirty the tree, or `verify.sh` leaves a
    diff behind on every green run -- which is how the old bug looked."""
    with open(os.path.join(RUN_DIR, ".gitignore"), encoding="utf-8") as fh:
        ignored = fh.read()
    assert rep.CURRENT + "/" in ignored


# ------------------------------------------------------------ the comparison

def test_a_strict_mismatch_is_reported_not_repaired(rep, monkeypatch):
    before = _archive_state()
    doctored = [("before/check_redlines.planted.txt", "not what is archived\n")]
    differences, notes = rep.compare_with_archive(doctored)
    assert differences and not notes
    assert _archive_state() == before, "comparing rewrote the archive"


def test_a_drifted_after_side_is_a_note_not_a_failure(rep):
    """`after/` is the working tree's output on the archive date. A13
    (`1050b001`) changed the audit's wording afterwards; that is the calendar
    moving, not the claim failing."""
    doctored = [("after/contamination.planted.txt", "different wording\n")]
    differences, notes = rep.compare_with_archive(doctored)
    assert notes and not differences


def test_the_full_tree_capture_is_a_note_on_both_sides(rep):
    for side in ("before", "after"):
        rel = "%s/check_redlines.full_tree.txt" % side
        differences, notes = rep.compare_with_archive([(rel, "anything\n")])
        assert notes and not differences, rel


def test_a_missing_archived_copy_on_the_strict_side_is_a_difference(rep):
    differences, _ = rep.compare_with_archive(
        [("before/never_archived.txt", "x\n")])
    assert differences and "no archived copy" in differences[0][1]


def test_live_ledger_counts_are_masked_but_not_deleted(rep):
    """The audit line counts an append-only file another session writes to.

    Masked for the comparison so the archive does not disagree with itself over
    the calendar; left in the capture so a reader still sees the number.
    """
    a = "  ledger audit: baseline-arms/probe_log.jsonl  1955 calls, clean\n"
    b = "  ledger audit: baseline-arms/probe_log.jsonl  1956 calls, clean\n"
    assert rep._comparable(a) == rep._comparable(b)
    # and a real change on the same line is still visible
    c = "  ledger audit: baseline-arms/probe_log.jsonl  1956 records, clean\n"
    assert rep._comparable(b) != rep._comparable(c)
    # masking is scoped to that line
    assert rep._comparable("exit code: 2\n") == "exit code: 2\n"


# ------------------------------------------------------------- end to end

def test_the_replay_is_green_and_leaves_the_archive_alone(rep, capsys):
    before = _archive_state()
    code = rep.main()
    out = capsys.readouterr().out
    assert code == 0, out
    assert _archive_state() == before, "a green run modified the archive"
    assert "0 file(s) rewritten" in out


def test_the_run_writes_its_output_where_a_reader_can_diff_it(rep):
    current = os.path.join(RUN_DIR, rep.CURRENT)
    shutil.rmtree(current, ignore_errors=True)
    assert rep.main() == 0
    assert os.path.exists(os.path.join(
        current, "before", "check_redlines.planted.txt"))
