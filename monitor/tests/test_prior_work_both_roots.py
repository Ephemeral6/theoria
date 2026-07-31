"""`prior_work` must see BOTH worktree roots, not one of them.

This machine keeps worktrees in two places: `.worktrees/`, which CLAUDE.md tells
every agent to use, and `.claude/worktrees/`, which the harness creates on its
own without asking. Until S41, `prior_work` did
`os.listdir(repo/'.worktrees')` and nothing else.

That is not a hypothetical. S36 recorded three PAID shards sitting in
`.claude/worktrees/p11-arc-hygiene` that evaded two separate checks at once,
because both checks globbed only the first root. So the one check whose entire
job is to stop duplicated paid work was blind in the only directory where
duplicated paid work has ever actually occurred -- and blind in the reassuring
direction: silence, a successful claim, two sessions starting the same run.

The positive control below (`test_a_wip_only_under_dot_claude_warns`) is the
regression that defines the item. The negative controls are what keep the
warning worth reading at all: it sits at the end of a long item body, and a
warning that fires on every claim is one nobody reads.
"""

import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import board                                                    # noqa: E402

MONITOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------------------
# Rig. Nothing here touches this machine's real 252 worktrees: `prior_work`
# already takes a `repo` argument, and every git call it makes goes through
# `board._git`, so a tmp_path directory plus a stubbed `_git` is a complete
# world. A test that read the live roots would change its own verdict every
# time somebody reaped a worktree.
# --------------------------------------------------------------------------

def _fake_git(monkeypatch, branches=(), registered=(), ahead="3"):
    """Stand in for the three read-only git calls `prior_work` makes.

    `registered` is what `git worktree list --porcelain` reports AFTER the main
    checkout, which real git always emits first. Paths are printed with forward
    slashes, as git does on Windows -- the normalisation that reconciles those
    with `os.path.join`'s backslashes is exactly what pass 2 depends on to tell
    a registered worktree from an orphan.
    """
    def fake(repo, *args):
        if args[0] == "branch":
            return list(branches)
        if args[0] == "rev-list":
            return [ahead]
        if args[0] == "worktree":
            lines = ["worktree %s" % str(repo).replace("\\", "/"),
                     "HEAD 0000000000000000000000000000000000000000",
                     "branch refs/heads/master", ""]
            for p in registered:
                lines += ["worktree %s" % str(p).replace("\\", "/"),
                          "HEAD 1111111111111111111111111111111111111111",
                          "branch refs/heads/agent/x", ""]
            return lines
        return []
    monkeypatch.setattr(board, "_git", fake)


class Repo:
    """A fake checkout with the two worktree roots under it."""

    def __init__(self, path):
        self.path = str(path)
        os.makedirs(os.path.join(self.path, ".worktrees"), exist_ok=True)
        os.makedirs(os.path.join(self.path, ".claude", "worktrees"),
                    exist_ok=True)

    def worktree(self, root, name):
        """Create a checkout directory under `root` and return its full path."""
        full = os.path.join(self.path, os.path.normpath(root), name)
        os.makedirs(full, exist_ok=True)
        return full

    def loose_file(self, root, name):
        full = os.path.join(self.path, os.path.normpath(root), name)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write("not a worktree\n")
        return full


def _repo(tmp_path, name="checkout"):
    return Repo(tmp_path / name)


# ------------------------------------------------------- the positive control

def test_a_wip_only_under_dot_claude_warns(tmp_path, monkeypatch):
    """THE regression. No branch, no commit, nothing under `.worktrees/` --
    only a harness-made checkout under `.claude/worktrees/`. Before S41 this
    returned `[]` and the claim went through in silence."""
    r = _repo(tmp_path)
    wt = r.worktree(".claude/worktrees", "p11-arc-hygiene")
    _fake_git(monkeypatch, branches=[], registered=[wt])

    out = board.prior_work("P11-arc-hygiene", r.path)

    assert out, "a checkout for this item exists under .claude/worktrees and " \
                "nothing was said -- this is S36 happening again"
    assert ".claude/worktrees/p11-arc-hygiene" in "\n".join(out)


def test_an_unregistered_orphan_warns(tmp_path, monkeypatch):
    """git has forgotten the registration; the working files are still there.

    Six of these exist on this machine (`_advscratch`, `_c1w_salvage`,
    `_e1_salvage`, `_res3_v26merge`, `opsm21-adv4-probe`,
    `opsm28-master-control`). `git worktree list` cannot see them and neither
    can `reap_worktrees.py`, so pass 1 alone would be a new blind spot in place
    of the old one.
    """
    r = _repo(tmp_path)
    r.worktree(".worktrees", "s41-salvage")
    _fake_git(monkeypatch, branches=[], registered=[])   # git knows nothing

    out = board.prior_work("S41-salvage", r.path)

    assert out
    joined = "\n".join(out)
    assert ".worktrees/s41-salvage" in joined
    assert "孤立" in joined, "an orphan must not be described as registered"


def test_an_orphan_under_dot_claude_also_warns(tmp_path, monkeypatch):
    """Both passes must cover both roots -- the orphan sweep too, not just
    `git worktree list`."""
    r = _repo(tmp_path)
    r.worktree(".claude/worktrees", "s41-harness-orphan")
    _fake_git(monkeypatch, branches=[], registered=[])

    out = board.prior_work("S41-harness-orphan", r.path)

    assert ".claude/worktrees/s41-harness-orphan" in "\n".join(out)


def test_a_registered_worktree_outside_both_roots_still_warns(tmp_path,
                                                              monkeypatch):
    """`ci_merge` builds throwaway worktrees under %TEMP%, and one is registered
    on this machine right now. The "two roots" model is already false; the point
    of using `git worktree list` rather than a wider glob is that it is
    root-agnostic by construction and needs no third constant.
    """
    r = _repo(tmp_path)
    elsewhere = tmp_path / "somewhere-else" / "s41-temp-tree"
    elsewhere.mkdir(parents=True)
    _fake_git(monkeypatch, branches=[], registered=[str(elsewhere)])

    out = board.prior_work("S41-temp-tree", r.path)

    assert out
    assert "s41-temp-tree" in "\n".join(out)


# ----------------------------------------------- what must NOT be reported

def test_a_brand_new_item_says_nothing(tmp_path, monkeypatch):
    """The control that keeps the warning readable. Both roots exist, both hold
    unrelated work, and there is nothing to say about this item."""
    r = _repo(tmp_path)
    a = r.worktree(".worktrees", "s21-app-session-death")
    b = r.worktree(".claude/worktrees", "p11-arc-hygiene")
    r.worktree(".worktrees", "_advscratch")             # an orphan, unrelated
    _fake_git(monkeypatch, branches=[], registered=[a, b])

    assert board.prior_work("S99-brand-new-item", r.path) == []


def test_a_loose_file_in_worktrees_is_not_a_worktree(tmp_path, monkeypatch):
    """`.worktrees/` holds 12 loose files -- probe scripts and findings dumps
    parked there by earlier sessions. One of them sharing a name with the item
    is not evidence that anybody is working it, and counting them would inflate
    every census by 12."""
    r = _repo(tmp_path)
    r.loose_file(".worktrees", "s41-notes.md")
    _fake_git(monkeypatch, branches=[], registered=[])

    assert board.prior_work("S41-notes", r.path) == []


def test_a_loose_file_under_dot_claude_is_not_a_worktree(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    r.loose_file(".claude/worktrees", "s41-notes.md")
    _fake_git(monkeypatch, branches=[], registered=[])

    assert board.prior_work("S41-notes", r.path) == []


def test_the_main_checkout_is_never_reported(tmp_path, monkeypatch):
    """`git worktree list --porcelain` emits the main checkout as its FIRST
    record. If it were not dropped, a repo whose own directory name contains the
    slug would warn about itself on every single claim."""
    r = _repo(tmp_path, name="s41-prior-work")
    _fake_git(monkeypatch, branches=[], registered=[])

    assert board.prior_work("S41-prior-work", r.path) == []


def test_a_registered_worktree_is_reported_once_not_twice(tmp_path, monkeypatch):
    """Pass 2 must subtract pass 1. A registered checkout is also a directory
    sitting in `.worktrees/`, so a naive second sweep would report it again --
    once as registered and once as an orphan, contradicting itself."""
    r = _repo(tmp_path)
    wt = r.worktree(".worktrees", "s41-dedupe")
    _fake_git(monkeypatch, branches=[], registered=[wt])

    out = board.prior_work("S41-dedupe", r.path)

    assert sum(1 for line in out if "s41-dedupe" in line) == 1
    assert "孤立" not in "\n".join(out), "a registered worktree is not an orphan"


# ------------------------------------------------- how the hit is described

def test_the_two_roots_are_named_apart(tmp_path, monkeypatch):
    """The old text hard-coded `工作树 .worktrees/%s`, so a hit in the harness
    root would have been REPORTED as living in `.worktrees/` -- sending the
    reader to look where it is not."""
    r = _repo(tmp_path)
    a = r.worktree(".worktrees", "s41-twin")
    b = r.worktree(".claude/worktrees", "s41-twin")
    _fake_git(monkeypatch, branches=[], registered=[a, b])

    joined = "\n".join(board.prior_work("S41-twin", r.path))

    assert ".worktrees/s41-twin" in joined
    assert ".claude/worktrees/s41-twin" in joined


def test_a_registration_whose_directory_is_gone_says_so(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    ghost = os.path.join(r.path, ".worktrees", "s41-reaped")   # never created
    _fake_git(monkeypatch, branches=[], registered=[ghost])

    joined = "\n".join(board.prior_work("S41-reaped", r.path))

    assert "s41-reaped" in joined
    assert "已不在盘上" in joined


def test_branch_reporting_is_unchanged(tmp_path, monkeypatch):
    """S41 touched only the worktree half. The branch half carries its own
    news -- 0 commits ahead means 'already merged', not 'someone is working on
    it' -- and that distinction must survive."""
    r = _repo(tmp_path)
    _fake_git(monkeypatch, branches=["  agent/s21-app-session-death"],
              registered=[], ahead="0")

    joined = "\n".join(board.prior_work("S21-app-session-death", r.path))

    assert "已并入" in joined


def test_every_line_survives_this_host_s_console_encoding(tmp_path, monkeypatch):
    """cp936. A glyph outside it raises UnicodeEncodeError *after* `cmd_claim`
    has already renamed the item into `claimed/`: the board records a successful
    claim while the agent sees a traceback and no work. The new lines are longer
    and there are more shapes of them, so this control is re-run here rather
    than inherited."""
    r = _repo(tmp_path)
    a = r.worktree(".worktrees", "s41-enc")
    r.worktree(".claude/worktrees", "s41-enc-orphan")
    ghost = os.path.join(r.path, ".worktrees", "s41-enc-gone")
    _fake_git(monkeypatch, branches=["  agent/s41-enc"], registered=[a, ghost])

    for iid in ("S41-enc", "S41-enc-orphan", "S41-enc-gone"):
        out = board.prior_work(iid, r.path)
        assert out
        for line in out:
            line.encode("cp936")        # raises if an unencodable glyph is back


# --------------------------------------------------- it must never break claim

def test_git_returning_nothing_degrades_to_the_directory_sweep(tmp_path,
                                                               monkeypatch):
    """`_git` swallows every failure and returns `[]`. If that made pass 1 empty
    AND pass 2 depend on it, a git hiccup would silently restore the old blind
    spot. It must not: the sweep stands on its own."""
    r = _repo(tmp_path)
    r.worktree(".claude/worktrees", "s41-git-down")
    monkeypatch.setattr(board, "_git", lambda repo, *a: [])

    assert board.prior_work("S41-git-down", r.path)


def test_missing_roots_are_fine(tmp_path, monkeypatch):
    """Neither root has to exist -- a fresh clone has neither."""
    bare = tmp_path / "bare"
    bare.mkdir()
    _fake_git(monkeypatch, branches=[], registered=[])

    assert board.prior_work("S41-x", str(bare)) == []


def test_the_real_git_on_a_non_repo_neither_raises_nor_warns(tmp_path):
    """Unpatched `_git`, end to end. A claim that failed because git was
    missing, slow or mid-rebase would be a worse bug than the one S41 fixed."""
    r = _repo(tmp_path)
    assert board.prior_work("S41-nothing-here", r.path) == []


# --------------------------------------------------------------------------
# The never-again lint.
#
# Requested by RES-4 in place of a shared enumeration helper. A shared constant
# was considered and REJECTED: the sites that skip these directories are three
# unrelated shapes (enumerators, path walk-up, walk-skip sets), and importing
# one constant across territories would create exactly the cross-territory edge
# this repo forbids. A lint that lives in the territory it polices costs no
# import edge and catches the bug shape at the moment it is written.
#
# The shape it catches is ASYMMETRY, which is the S36 defect precisely: a skip
# set that names ONE worktree root and not the other. Its author knew the
# directories needed excluding and got half of them.
#
# What it deliberately does NOT catch: a set naming NEITHER root. That is a
# different decision (walk everything on purpose) rather than a half-done one --
# `scan.py:SKIP_DIRS` is such a set, and the API-key leak scan that uses it
# arguably SHOULD descend into worktrees, since a leaked key in a worktree is
# still a leaked key. Adjudicating that is not S41's business and would change
# what the leak scan covers.
# --------------------------------------------------------------------------

#: Spellings that mean "the `.worktrees/` root" and "the harness root".
_CLAUDE_ROOT = {".claude", ".claude/worktrees", ".claude\\worktrees"}
_MAIN_ROOT = {".worktrees"}

#: A set is only judged as a SKIP set if it also names one of these.
#:
#: Without this the lint fires on `ci_merge.py:KNOWN_DIRS`, which is a POSITIVE
#: allowlist of territories that happens to admit `.claude` as one -- the
#: opposite polarity, where naming `.worktrees` too would be the bug. Requiring
#: a machine-directory marker separates "things I refuse to descend into" from
#: "things I recognise", and every real skip set in this repo names `.git` or
#: `__pycache__` because those are the two nobody forgets.
_SKIP_SET_MARKERS = {".git", "__pycache__", ".pytest_cache", "node_modules",
                     ".venv", ".toolchain"}


def _string_literals(node):
    """Every plain string element of a set/list/tuple literal, or None."""
    if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        return None
    out = []
    for elt in node.elts:
        if not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
            return None
        out.append(elt.value)
    return out


def _monitor_sources():
    """Top-level `monitor/*.py`. Not `runs/` -- those are frozen provenance
    artifacts, and not `tests/` -- this file itself names both roots all over.
    """
    for name in sorted(os.listdir(MONITOR)):
        if name.endswith(".py"):
            yield name, os.path.join(MONITOR, name)


def asymmetric_sets(source, name="<source>"):
    """Every skip set in `source` that names one worktree root and not the other."""
    try:
        tree = ast.parse(source)
    except SyntaxError:                                       # pragma: no cover
        return []
    found = []
    for node in ast.walk(tree):
        values = _string_literals(node)
        if values is None:
            continue
        names = set(values)
        if not names & _SKIP_SET_MARKERS:
            continue                        # an allowlist, not a skip set
        has_main = bool(names & _MAIN_ROOT)
        has_claude = bool(names & _CLAUDE_ROOT)
        if has_main != has_claude:
            found.append(
                "%s:%d names %s but not %s -- %r"
                % (name, node.lineno,
                   ".worktrees" if has_main else ".claude/worktrees",
                   ".claude/worktrees" if has_main else ".worktrees",
                   sorted(names)[:8]))
    return found


def test_the_lint_fires_on_the_shape_it_is_looking_for():
    """A lint nobody has seen fail is a lint nobody knows works. These three
    synthetic sources are the S36 shape and its two innocent neighbours."""
    half_done = 'SKIP = {".git", "__pycache__", ".worktrees"}\n'
    assert asymmetric_sets(half_done), "the S36 shape went unreported"

    other_half = 'SKIP = {".git", "__pycache__", ".claude"}\n'
    assert asymmetric_sets(other_half), "asymmetry is symmetric -- both ways count"

    symmetric = 'SKIP = {".git", "__pycache__", ".worktrees", ".claude"}\n'
    assert asymmetric_sets(symmetric) == []

    allowlist = 'KNOWN = {"monitor", "proxy", ".claude"}\n'
    assert asymmetric_sets(allowlist) == [], \
        "a positive allowlist has the opposite polarity and must not be flagged"

    walks_everything = 'SKIP = {".git", "__pycache__", "node_modules"}\n'
    assert asymmetric_sets(walks_everything) == [], \
        "naming neither root is a decision, not a half-done exclusion"


def test_no_skip_set_in_monitor_names_one_worktree_root_but_not_the_other():
    asymmetric = []
    for name, path in _monitor_sources():
        with open(path, encoding="utf-8") as fh:
            asymmetric += asymmetric_sets(fh.read(), name)
    assert not asymmetric, (
        "a directory set names one worktree root and not the other. This "
        "machine has both, and S36 cost three paid shards to exactly this "
        "half-done exclusion:\n  " + "\n  ".join(asymmetric))


def test_board_still_knows_about_both_roots():
    """The constant the lint above is really protecting. If someone trims
    `WORKTREE_ROOTS` back to a single entry, the orphan sweep silently returns
    to covering one of two places and every test above still passes on the
    registered path."""
    roots = {r.replace("\\", "/") for r in board.WORKTREE_ROOTS}
    assert ".worktrees" in roots
    assert ".claude/worktrees" in roots
