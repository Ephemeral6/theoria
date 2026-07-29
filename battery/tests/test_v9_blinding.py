"""The blinding step is reproducible, pinned, and fails loudly.

V9's whole claim rests on the attackers having seen the metrics and nothing
else.  Before V24 the step that produced what they saw read a hardcoded
absolute path into `.worktrees/v9-battery-gaming-audit`, and a worktree's HEAD
moves: by the time the branch reached `0d586b6f` that path resolved to a tree
containing the three defences the attacks had provoked.  Re-running the
"blinding" would have handed the attackers the answers, and said nothing.

So the tests here are not about `make_blind` computing correctly.  They are
about it being unable to blind against the wrong thing quietly:

* the ref is pinned to a sha and that sha is the one the V9 run manifest
  recorded as its `prereg_commit` -- the code constant and the provenance
  record cannot drift apart without a test going red;
* every failure mode raises rather than falling back;
* the tree it builds is byte-stable and matches a tracked digest;
* the recorded claims about that tree still hold, in both directions -- no
  post-attack vocabulary, and the one registered leak still present.

The last is the one worth keeping.  A blinding regression does not announce
itself: the tree still builds, the attacks still run, the verdict still comes
out.  The only way it shows is a check that knows what the blind is supposed
to contain.
"""
import io
import json
import os
import re
import subprocess
import sys

import pytest

from battery.audit.v9 import make_blind as mb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
V9 = os.path.join(ROOT, "battery", "audit", "v9")
DIGESTS = os.path.join(V9, "BLIND_DIGESTS.json")
V9_MANIFEST = os.path.join(
    ROOT, "battery", "runs", "20260729T021247Z-V9-battery-gaming-audit",
    "MANIFEST.json")

# The branch tip the pre-V24 hardcoded path resolved to.
WORKTREE_HEAD = "0d586b6f99615fd87375d14441e0cc290fed8086"


@pytest.fixture(scope="module")
def repo():
    return mb.repo_root(ROOT)


@pytest.fixture(scope="module")
def tree(repo):
    _, contents = mb.contents_at(mb.BLIND_REF, repo)
    return contents


# --- the pin ---------------------------------------------------------------

def test_blind_ref_is_the_recorded_prereg_commit():
    """The constant in the code is the commit the run manifest recorded.

    This is the anchor for everything else.  `BLIND_REF` is otherwise just a
    sha somebody typed, and a sha nobody can check is not provenance.
    """
    with io.open(V9_MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    assert manifest["prereg_commit"] == mb.BLIND_REF, (
        "make_blind.BLIND_REF and the V9 run manifest's prereg_commit disagree; "
        "one of them moved")


def test_blind_ref_is_a_full_sha_not_a_branch():
    """A branch name would reproduce the defect one indirection later."""
    assert re.fullmatch(r"[0-9a-f]{40}", mb.BLIND_REF)


def test_blind_ref_resolves_without_the_worktree(repo):
    """It must resolve from the repo alone, not from `.worktrees/`."""
    assert mb.resolve(mb.BLIND_REF, repo) == mb.BLIND_REF
    src = os.path.join(ROOT, ".worktrees", "v9-battery-gaming-audit")
    assert mb.BLIND_REF not in src  # sanity: the pin is not a path


def test_pinned_ref_predates_the_defences(repo):
    """`unsound()` -- the defence the attacks provoked -- is not at the pin.

    If it ever is, either the pin moved or history was rewritten, and the
    blind is no longer a blind.
    """
    at_pin = mb.read_at(mb.BLIND_REF, "battery/metrics/__init__.py", repo)
    assert "def unsound" not in at_pin


# --- loud failure ----------------------------------------------------------

def test_unresolvable_ref_raises(repo):
    with pytest.raises(mb.BlindingError) as exc:
        mb.resolve("no-such-ref-v24", repo)
    assert "refusing to fall back" in str(exc.value)


def test_missing_file_at_ref_raises(repo):
    with pytest.raises(mb.BlindingError) as exc:
        mb.read_at(mb.BLIND_REF, "battery/does_not_exist.py", repo)
    assert "cannot be built from this ref" in str(exc.value)


def test_non_repo_directory_raises(tmp_path):
    """No git work tree means no ref, and no guessing a directory."""
    with pytest.raises(mb.BlindingError):
        mb.repo_root(str(tmp_path / "nope"))


def test_cli_exits_nonzero_on_a_bad_ref(tmp_path):
    """The failure has to reach the exit code, not just the logs."""
    proc = subprocess.run(
        [sys.executable, "-m", "battery.audit.v9.make_blind",
         "--ref", "no-such-ref-v24", "--out", str(tmp_path), "a1"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.returncode == 2, proc.stdout.decode("utf-8", "replace")
    assert b"BLINDING FAILED" in proc.stderr
    assert not os.listdir(str(tmp_path)), "wrote output despite failing"


# --- reproducibility -------------------------------------------------------

def test_blinded_tree_matches_the_tracked_digests(repo):
    with io.open(DIGESTS, encoding="utf-8") as fh:
        recorded = json.load(fh)
    sha, fresh = mb.digests_at(mb.BLIND_REF, repo)
    assert sha == recorded["commit"]
    running = "%d.%d" % sys.version_info[:2]
    assert fresh == recorded["files"], (
        "blinded tree differs from BLIND_DIGESTS.json. Recorded under Python "
        "%s, running %s -- ast.unparse output is version-dependent, so check "
        "that first." % (recorded["python"], running))


def test_blinding_is_byte_stable(repo):
    a = mb.digests_at(mb.BLIND_REF, repo)
    b = mb.digests_at(mb.BLIND_REF, repo)
    assert a == b


def test_build_writes_the_tree_it_promises(tmp_path, repo):
    dest = str(tmp_path / "a1")
    digests = mb.build(dest, mb.BLIND_REF, repo)
    _, expected = mb.digests_at(mb.BLIND_REF, repo)
    assert digests == expected
    for rel in mb.COPY + mb.PROTOCOL + mb.SHIMS:
        assert os.path.isfile(os.path.join(dest, rel.replace("/", os.sep)))


# --- what the blind is supposed to contain ---------------------------------

def test_no_prose_survives(tree):
    """No docstrings and no comments in anything the attacker receives.

    Comments are checked with `tokenize` rather than by searching for `#`,
    which would fire on every `#` inside a string literal.
    """
    import ast
    import tokenize
    for rel, text in tree.items():
        if not text:
            continue
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
                assert ast.get_docstring(node) is None, (
                    "%s still carries a docstring" % rel)
        comments = [t.string for t in
                    tokenize.generate_tokens(io.StringIO(text).readline)
                    if t.type == tokenize.COMMENT]
        assert not comments, "%s still carries comments: %s" % (rel, comments[:3])


def test_reason_strings_are_neutralised(tree):
    whole = "\n".join(tree.values())
    for old, _new in mb.NEUTRALISE:
        assert old not in whole, "un-neutralised reason string in the blind: %r" % old[:60]


def test_no_post_attack_vocabulary(tree):
    """BLINDING.md §3.8 / REPORT.md §9(d) recorded these as zero-hit."""
    whole = "\n".join(tree.values())
    for term in ("unsound(", "gaming.py", "GAMING_REGISTER", "how_to_game",
                 "a0-spike", "bare_cc", "main table", "reference layer"):
        assert term not in whole, "blinded tree leaks %r" % term
    assert not re.search(r"\bV9-P\d", whole)
    assert not re.search(r"\bD[123]\b", whole)


def test_the_registered_leak_is_still_there(tree):
    """Positive control for BLINDING.md §3.7.

    K2's `thin()` string contains the two real sampling-frame sizes, is not on
    the NEUTRALISE list, and reached attacker a5.  A rebuild that has lost it
    is not the tree the attackers saw, so its absence is a failure exactly as
    much as a new leak is.
    """
    whole = "\n".join(tree.values())
    assert "39960" in whole
    assert "3 adversarial gaps" in whole


def test_the_old_hardcoded_source_would_have_leaked(repo):
    """The defect V24 closed is real, and measured rather than asserted."""
    try:
        _, head_tree = mb.contents_at(WORKTREE_HEAD, repo)
    except mb.BlindingError:
        pytest.skip("worktree HEAD %s unreachable in this clone" % WORKTREE_HEAD[:12])
    _, pinned = mb.contents_at(mb.BLIND_REF, repo)
    differing = [r for r in pinned if pinned[r] != head_tree[r]]
    assert differing, "expected the branch tip to differ from the pinned ref"
    leaked = sum(t.count("unsound(") for t in head_tree.values())
    assert leaked > 0, (
        "the branch tip no longer carries the defence vocabulary; if that is "
        "genuine, this test and FINDINGS.md both need revisiting")


# --- the reason this file exists -------------------------------------------

SKIP_DIRS = {"runs", "artifacts", "__pycache__", "docs"}
DRIVE_PATH = re.compile(r"[A-Za-z]:[\\/]{1,2}(Users|home)", re.I)


def test_no_machine_absolute_paths_in_battery_source():
    """Live battery code resolves nothing from this machine's filesystem.

    `battery/runs/` and `battery/artifacts/` are exempt: an absolute path in a
    provenance record is a record of where something was, which is the point.
    Live code is different -- a path there means the experiment reproduces on
    one laptop, and reproducibility is a hard requirement of this repo.
    """
    offenders = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "battery")):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            if os.path.abspath(path) == os.path.abspath(__file__):
                continue
            with io.open(path, encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if DRIVE_PATH.search(line):
                        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
                        offenders.append("%s:%d: %s" % (rel, i, line.strip()))
    assert not offenders, "machine-absolute path in live battery code:\n" + "\n".join(offenders)
