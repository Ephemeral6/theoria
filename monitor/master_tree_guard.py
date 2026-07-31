"""Fail-closed guard over the ONE working tree the fleet shares: master's.

WHY THIS EXISTS. Every agent is told to build a branch and a worktree under
`.worktrees/<slug>/` and work there. Twice on 2026-07-29/30 the work landed on
master's working tree instead -- RES-2 self-reported it
(`monitor/inbox/20260729T110500Z-RES-2-i-edited-master-working-tree.md`), and
RES-4 did it to itself during S38 when a `cd` failed to apply to the rest of a
command string and `monitor/scan.py` plus two new files were written to the
repo root instead of the worktree.

Neither instance raised anything. That is the whole problem. Master's working
tree carries the fleet's uncommitted shared state -- `board/`, `ops-status/`,
`bus/`, `ci/` -- so it is dirty by design, permanently, with ~200 paths. A
stray source edit is 1 line in a 200-line `git status` that everybody has
learned to page past. From there it goes one of two ways, both silent:

  * somebody's `git add` sweeps it into an unrelated commit, or
  * somebody's `git checkout --` / reset wipes it.

The change works, the tests pass, nothing errors. The only thing wrong with it
is WHICH BRANCH it is on, and no existing probe of the fleet's 25 looks at that.

WHAT IT SEPARATES. Not people -- paths. The monitor itself, `board.py` and
`bus.py` MUST write to master's tree; forbidding work there would forbid the
fleet from running. So the judgement is per-path, in three tiers:

  1. FLEET-STATE -- under a whitelisted prefix (`monitor/board/`,
     `monitor/ops-status/`, `monitor/bus/`, `monitor/mailbox/`, `monitor/ci/`,
     `monitor/inbox/`, the monitor's logs and state files). Dirty here is the
     normal condition and is never reported. This is the reason a blunt
     "master's tree must be clean" rule is useless: it would be red every
     minute of every day, and a gate that is always red is not a gate.

  2. MISWRITE (red) -- a TRACKED file, modified or deleted, NOT under a
     whitelisted prefix. `monitor/reflex.py`, `engine-rig/...`, a paper source.
     Tracked means git already knows the file, so "modified here" means someone
     edited a real source file on the shared tree, or that a code file landed
     in a whitelisted directory (see CODE_SUFFIXES). Two remedies, and the
     adjudication in FINDINGS.md found both in one sample: move it to the
     branch it belongs to, or commit it if master really is its home. Doing
     neither is the failure -- `monitor/reflex.py` was a 69+/115- rewrite that
     sat here unowned and survived by luck.

  3. UNFILED -- an UNTRACKED path outside the whitelist. Scratch dirs,
     `pytest-*` residue, a run directory nobody committed. Reported separately
     because the remedy differs (file it, ignore it, or delete it, rather than
     commit-or-branch), but it GATES exactly like tier 2.

     It did not, in the first version of this guard, and that was the defect an
     adversarial review found: the S38 incident this module's docstring cites
     was "`monitor/scan.py` PLUS TWO NEW FILES", and new files are untracked.
     So the gate exempted the majority of the very incident it was built for --
     agents doing item work create files far more often than they edit
     existing ones. Replayed, S39's own three deliverables landing on master's
     tree scored `red=False, miswrites=0, exit 0`.

     The justification written here for exempting them was also simply false:
     it claimed untracked files "cannot be swept into somebody else's commit".
     `git add -A`, `git add .` and `git commit -a` all sweep them, and `git add
     -A` is what produced the commit literally titled "On master: autostash"
     that this repo already carries.

     The worry that drove the exemption -- that gating untracked paths would
     make the guard red every day, which the item warns is the same as no gate
     -- was never measured. It is now: all NINE untracked non-whitelisted paths
     on the live tree were independently adjudicated in FINDINGS.md, and NOT
     ONE is legitimately mid-flight. Every one is a should-commit, should-
     ignore, should-delete or should-have-been-on-a-branch. So this tier is red
     today because there is really something to fix, and it goes green when the
     tree is actually clean -- which is what a gate is.

The whitelist is POSITIVE and the default is deny, the shape
`arc-recon/local_engine_guard.py` uses and for the same reason: a negative list
meets a path shape nobody foresaw and fails OPEN, and failing open here means
the next miswrite is as invisible as the last two.

Prefix matching is BOUNDARY-ANCHORED -- `monitor/board/` matches
`monitor/board/x.md` but a hypothetical `monitor/boardgame.py` does NOT match.
Same lesson `local_engine_guard.py` records for `ar25` vs `blobs/9ar25f0e/`.

WHICH TREE. Only the MAIN working tree is judged. A linked worktree under
`.worktrees/<slug>/` is SUPPOSED to have dirty source -- that is an agent doing
its job -- so running this there would invert the meaning. The main tree is
identified from `git worktree list --porcelain`, whose FIRST record is the main
tree, and never by globbing `.worktrees/*`: this repo has worktrees in TWO
places (`.worktrees/` and the harness's `.claude/worktrees/`), and S36 recorded
that three paid shards in `p11-arc-hygiene` evaded two separate checks at once
because those checks globbed only the first of the two. `git worktree list`
covers both by construction; a glob covers whichever one its author had in mind.

PARSING. Status is read with `--porcelain -z`, NUL-separated. The non-`-z`
format C-quotes any path with a non-ASCII or special character, and one of the
paths this guard was written to catch is literally a flattened Windows absolute
path (`C:UsersuserDesktoptheoriamonitorpermtest.txt`, colon and backslashes
eaten) which the quoted format renders as escaped octal. Unquoting that by hand
is a bug farm; `-z` emits the raw bytes and sidesteps it.

UNTRACKED DIRECTORIES COLLAPSE. git's default reports an untracked directory as
a single entry (`.claude/`), not as its contents, and the guard keeps that
default: `-uall` on the live tree would expand `.claude/worktrees/` into a
hundred whole checkouts and drown the report. So one amber line can stand for a
directory of any size -- `theoria-arm/runs/<id>/` is one line for eight files.
It still gates, so nothing is hidden by it; only the line count is compressed.

EXIT CODES.  0 = nothing outside the whitelist is dirty
             2 = at least one finding in EITHER tier -- red
             3 = the guard could not determine the answer (NOT a pass)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Iterable, Sequence

# --------------------------------------------------------------------------
# The whitelist. Everything here is fleet live state that BELONGS to master's
# working tree, uncommitted, as a matter of normal operation.
#
# Add to it only when a path is genuinely shared-mutable fleet state. Anything
# that is source, test, documentation, or an experiment artifact does NOT go
# here -- the point of the guard is that those belong on a branch.
# --------------------------------------------------------------------------

FLEET_STATE_PREFIXES: tuple[str, ...] = (
    "monitor/board/",       # the work board: items, claimed, done
    "monitor/ops-status/",  # heartbeats and locks
    "monitor/bus/",         # message bus: out.jsonl, cursor.json
    "monitor/mailbox/",     # retired channel, still written by old sessions
    "monitor/ci/",          # merge conflicts and merge log
    "monitor/inbox/",       # proposals awaiting review
    "monitor/audit/",       # auditor drift reports, written live by OPS-A
)

# Prefixes where only DIRECT children are fleet state -- a nested directory
# under one of these is not.
#
# `monitor/res/` holds one contract file per researcher, retuned by the monitor
# every cycle, so `monitor/res/RES-4.md` is fleet state. But the adjudication in
# runs/20260730T0440Z-S39/FINDINGS.md found `monitor/res/RES-3-notes/` -- a
# directory of per-item working notes written onto the shared tree while the
# items themselves were being worked on branches -- and judged it a MISWRITE.
# A plain `monitor/res/` prefix would excuse exactly that, which is the
# dangerous direction: a false negative on a real instance from the very sample
# this guard was built from. Found by re-reading the adjudication against the
# whitelist, not by a test.
FLEET_STATE_FLAT_PREFIXES: tuple[str, ...] = ("monitor/res/",)

# Individual files (not prefixes) that are fleet state: written by the
# monitor's own loop every cycle.
#
# Verified writer by writer, not assumed. `scan.py` writes `state.json`,
# `index.html`, `history.jsonl` and `crashes.jsonl` (all `out_dir or HERE`);
# `reflex.py:28` writes `loop_state.json`; `accounts.py` writes
# `accounts.json`. Deliberately NOT here: `monitor/app.html` (a source frontend
# that `scan.py` only ever reads) and `monitor/orphan_dispositions.json` (S36's
# hand-written adjudication ledger). Both are edited on purpose, so both should
# go red when left uncommitted -- whitelisting them because they sit in the
# same directory as the generated files is the mistake this list exists to
# avoid.
FLEET_STATE_FILES: frozenset[str] = frozenset(
    {
        "monitor/state.json",
        "monitor/index.html",       # generated dashboard
        "monitor/history.jsonl",    # scan.py:1621
        "monitor/crashes.jsonl",    # scan.py:3082
        "monitor/loop_state.json",  # reflex.py:28
        "monitor/accounts.json",    # accounts.py
        "monitor/accounts_state.json",
        "monitor/quota_state.json",
        "monitor/standing_state.json",
    }
)

# Suffixes that are CODE. A file with one of these is never fleet live state,
# no matter which directory it sits in.
#
# Without this, `_under_prefix` is a bare `startswith` and a whitelisted
# directory swallows arbitrary source: `monitor/board/helper.py`,
# `monitor/ci/patcher.py` and `monitor/audit/drift_tool.py` all classified as
# fleet state and were reported at no tier at all. The whitelisted directories
# hold `.md`, `.json`, `.jsonl` and `.log` -- never code -- so this costs
# nothing and closes the hole. Found by an adversarial review, not by a test.
CODE_SUFFIXES: tuple[str, ...] = (
    ".py", ".sh", ".bat", ".cmd", ".ps1", ".lean", ".pddl", ".c", ".h",
    ".cpp", ".rs", ".js", ".ts", ".html", ".css", ".sql", ".toml", ".cfg",
    ".ini", ".yaml", ".yml",
)

# Any *.log under monitor/ is fleet state (board.log, merge.log, reflex.log,
# standing.log, accounts.log ...). Matched by suffix within the monitor dir so
# a new log does not need a code change to stop being a false red.
FLEET_STATE_LOG_DIR = "monitor/"
FLEET_STATE_LOG_SUFFIX = ".log"

VERDICT_FLEET = "fleet-state"
VERDICT_MISWRITE = "miswrite"
VERDICT_UNFILED = "unfiled"


@dataclass(frozen=True)
class Entry:
    """One path from `git status --porcelain -z`, classified."""

    path: str
    code: str          # the two-character XY status code, verbatim
    tracked: bool
    verdict: str       # VERDICT_*
    reason: str


def _run(args: Sequence[str], cwd: str) -> str:
    """Run a git command and return stdout, or raise GuardError."""
    try:
        proc = subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired as exc:
        # A hung git must not hang the whole scan. `_run` has no timeout by
        # default and every probe runs inside a 10-minute loop.
        raise GuardError(f"{' '.join(args)} timed out after 60s") from exc
    except OSError as exc:  # git missing, cwd gone
        raise GuardError(f"could not run {' '.join(args)}: {exc}") from exc
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()
        raise GuardError(f"{' '.join(args)} failed ({proc.returncode}): {err}")
    return proc.stdout.decode("utf-8", "surrogateescape")


class GuardError(Exception):
    """The guard could not determine the answer. Never treated as a pass."""


def main_worktree(cwd: str = ".") -> str:
    """Absolute path of the repository's MAIN working tree.

    Read from `git worktree list --porcelain`, whose first `worktree ` record is
    the main tree. Deliberately NOT a glob over `.worktrees/` -- see the module
    docstring on why this repo has two worktree directories.
    """
    out = _run(["git", "worktree", "list", "--porcelain"], cwd)
    for line in out.splitlines():
        if line.startswith("worktree "):
            return os.path.normpath(line[len("worktree ") :].strip())
    raise GuardError("`git worktree list --porcelain` named no worktree")


def is_main_worktree(cwd: str = ".") -> bool:
    """True if `cwd` is inside the main working tree rather than a linked one."""
    top = os.path.normpath(_run(["git", "rev-parse", "--show-toplevel"], cwd).strip())
    return os.path.normcase(top) == os.path.normcase(main_worktree(cwd))


def _under_prefix(path: str, prefix: str) -> bool:
    """Boundary-anchored prefix test.

    `monitor/board/` matches `monitor/board/x.md`; it does not match
    `monitor/boardgame.py`. The prefixes all end in `/`, which is what supplies
    the boundary -- this helper exists to make that a stated invariant rather
    than an accident of how the constants happen to be spelled.
    """
    if not prefix.endswith("/"):
        raise GuardError(f"whitelist prefix must end in '/': {prefix!r}")
    return path.startswith(prefix)


def classify(path: str, code: str) -> Entry:
    """Judge one status entry. Positive whitelist; default deny."""
    tracked = "?" not in code

    # Order matters, and it is precision-first: an explicitly NAMED generated
    # file beats the suffix heuristic, and the suffix heuristic beats a
    # directory prefix. Getting this backwards made `monitor/index.html` -- the
    # generated dashboard, rewritten by every scan -- a permanent false red,
    # because `.html` is a code suffix.
    if path in FLEET_STATE_FILES:
        return Entry(path, code, tracked, VERDICT_FLEET, "whitelisted fleet state file")

    if path.endswith(CODE_SUFFIXES):
        # Ahead of the PREFIX whitelist: code is never fleet live state, and a
        # whitelisted directory must not launder it.
        return Entry(
            path,
            code,
            tracked,
            VERDICT_MISWRITE if tracked else VERDICT_UNFILED,
            "code on the shared tree",
        )

    if (
        path.startswith(FLEET_STATE_LOG_DIR)
        and path.endswith(FLEET_STATE_LOG_SUFFIX)
        and "/" not in path[len(FLEET_STATE_LOG_DIR) :]
    ):
        return Entry(path, code, tracked, VERDICT_FLEET, "monitor log")

    for prefix in FLEET_STATE_FLAT_PREFIXES:
        # `path == prefix` is git's collapsed form for "this whole untracked
        # DIRECTORY", not a file in it. Excusing that would wave through the
        # directory's entire contents on a rule written to admit only its
        # direct children.
        if path == prefix:
            break
        if _under_prefix(path, prefix) and "/" not in path[len(prefix) :]:
            return Entry(path, code, tracked, VERDICT_FLEET, f"direct child of {prefix}")

    for prefix in FLEET_STATE_PREFIXES:
        if _under_prefix(path, prefix):
            return Entry(path, code, tracked, VERDICT_FLEET, f"under {prefix}")

    if tracked:
        return Entry(
            path,
            code,
            True,
            VERDICT_MISWRITE,
            "tracked file changed on the shared tree, outside fleet state",
        )

    return Entry(path, code, False, VERDICT_UNFILED, "untracked, outside fleet state")


def parse_status_z(raw: str) -> list[tuple[str, str]]:
    """Parse `git status --porcelain -z` into (code, path) pairs.

    In `-z` form each record is `XY<space><path>NUL`. A rename or copy (`R`/`C`
    in either column) is followed by a SECOND NUL-terminated field holding the
    ORIGINAL path, which must be consumed but is reported under the new path.
    """
    fields = [f for f in raw.split("\0") if f != ""]
    out: list[tuple[str, str]] = []
    i = 0
    while i < len(fields):
        record = fields[i]
        i += 1
        if len(record) < 4 or record[2] != " ":
            raise GuardError(f"unparseable status record: {record!r}")
        code, path = record[:2], record[3:]
        if "R" in code or "C" in code:
            if i >= len(fields):
                raise GuardError(f"rename record {record!r} has no source field")
            i += 1  # consume and discard the original path
        out.append((code, path))
    return out


def inspect(cwd: str = ".") -> list[Entry]:
    """Classify every dirty path in the working tree containing `cwd`.

    One wrinkle, and it is a hole rather than a nicety. git collapses an
    untracked DIRECTORY to a single entry, so a wholly-untracked
    `monitor/ci/` arrives as one path that the whitelist excuses as a unit --
    taking whatever is inside it, including code, with it. That is defect 2 in
    a second costume, and the flat-prefix fix does not reach it.

    So any untracked directory that the whitelist would excuse is re-listed
    with `-uall` scoped to itself and its contents classified individually.
    Bounded on purpose: only whitelisted directories are expanded, never
    `.claude/` -- expanding that would enumerate a hundred whole checkouts.
    """
    raw = _run(["git", "status", "--porcelain", "-z"], cwd)
    entries: list[Entry] = []
    for code, path in parse_status_z(raw):
        entry = classify(path, code)
        if entry.verdict == VERDICT_FLEET and path.endswith("/") and "?" in code:
            expanded = _run(
                ["git", "status", "--porcelain", "-z", "-uall", "--", path], cwd
            )
            inner = parse_status_z(expanded)
            if inner:
                entries.extend(classify(p, c) for c, p in inner)
                continue
        entries.append(entry)
    return entries


def report(cwd: str = ".", require_main: bool = True) -> dict:
    """Full verdict for the main working tree.

    `require_main=True` refuses to judge a linked worktree, where dirty source
    is the expected condition and a red would be nonsense.
    """
    # Resolved ONCE. `is_main_worktree` and the `tree` field each used to spawn
    # their own `git worktree list --porcelain`, and the probe a third: six git
    # subprocesses per probe call, 0.85s on this repo's 221 worktrees against
    # 0.12s for the `git status` that does the actual work.
    main = main_worktree(cwd)
    if require_main:
        top = os.path.normpath(_run(["git", "rev-parse", "--show-toplevel"], cwd).strip())
        if os.path.normcase(top) != os.path.normcase(main):
            raise GuardError(
                "not the main working tree -- a linked worktree is SUPPOSED to have "
                "dirty source; pass --any-tree to override"
            )
    entries = inspect(cwd)
    miswrites = [e for e in entries if e.verdict == VERDICT_MISWRITE]
    unfiled = [e for e in entries if e.verdict == VERDICT_UNFILED]
    fleet = [e for e in entries if e.verdict == VERDICT_FLEET]
    return {
        "tree": main if require_main else os.path.abspath(cwd),
        "total": len(entries),
        "fleet_state": len(fleet),
        "unfiled": len(unfiled),
        "miswrites": len(miswrites),
        # BOTH finding tiers gate. Keeping them as separate counts is for
        # diagnosis -- the remedies differ -- not for severity.
        "red": bool(miswrites) or bool(unfiled),
        "miswrite_paths": [asdict(e) for e in miswrites],
        "unfiled_paths": [asdict(e) for e in unfiled],
    }


# --------------------------------------------------------------------------
# The commit-time half.
#
# `report()` above observes; it blocks nothing, and on a 10-minute scan cycle a
# miswrite can be swept into somebody's commit long before it is ever drawn on
# a page. The blocking half has to fire between the write and the commit, and
# this repo has NO anchor there: `.git/hooks/` holds only `.sample` files,
# `core.hooksPath` is unset, and there is no `.githooks/`. `ci_merge` runs the
# territory gates AFTER `git merge --no-ff` has already made the commit, in a
# throwaway worktree -- that is before the PUSH, not before the commit, and it
# never looks at the shared tree at all.
#
# So this is a new mechanism, and it is deliberately NOT installed by default.
# Installing it changes what happens to every other agent's commits on this
# machine, live, and direct commits on master's tree are a documented normal
# landing path for ops sessions -- a hook that refuses them would break the
# fleet to prevent a class of accident. `--install-hook` is therefore an
# explicit act, and the probe reports whether it has been performed, so this
# guard cannot become another of the seven "green in git, absent in
# production" checks the 2026-07-30 drift audit found.
# --------------------------------------------------------------------------

OVERRIDE_ENV = "THEORIA_ALLOW_MASTER_SOURCE_COMMIT"

HOOK_MARKER = "theoria-master-tree-guard"

HOOK_BODY = """#!/bin/sh
# {marker} -- installed by monitor/master_tree_guard.py install-hook
# Refuses a commit that would carry a source file off master's SHARED working
# tree. Passes silently in any linked worktree, where branch work belongs.
# Override for a deliberate direct-to-master commit:
#   {override}=1 git commit ...
#
# Fails OPEN if it cannot find itself. The hook lives in .git/, which no commit
# can change, so it outlives any checkout -- including a checkout of a commit
# from before the guard existed, and any bisect that walks through one. A hook
# that hard-failed there would block every commit on this machine for a reason
# having nothing to do with the commit, and the fleet's escape hatch would be
# to learn `--no-verify` by reflex, which costs more than the guard is worth.
# The interpreter is resolved the same way, and for the same reason: hard-coding
# `python` made the hook fail CLOSED on any python3-only box, and on Windows
# without Python where `python.exe` is the Store alias -- `exec: python: not
# found` returns 127 and git blocks EVERY commit, including a pure heartbeat.
# The absolute path baked in below is the interpreter that installed the hook;
# the PATH names are the fallback if that interpreter is later removed.
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
guard="$root/monitor/master_tree_guard.py"
if [ ! -f "$guard" ]; then
    echo "master-tree-guard: $guard not in this checkout -- allowing" >&2
    exit 0
fi
for py in "{interpreter}" python3 python py; do
    if command -v "$py" >/dev/null 2>&1; then
        exec "$py" "$guard" precommit
    fi
done
echo "master-tree-guard: no python interpreter found -- allowing" >&2
exit 0
"""


def parse_name_status_z(raw: str) -> list[tuple[str, str]]:
    """Parse `git diff --cached --name-status -z` into (code, path) pairs.

    Fields alternate status/path, except `R`/`C` which carry a similarity score
    on the status field and are followed by TWO paths (old, then new). The new
    path is the one reported.
    """
    fields = [f for f in raw.split("\0") if f != ""]
    out: list[tuple[str, str]] = []
    i = 0
    while i < len(fields):
        code = fields[i]
        i += 1
        if i >= len(fields):
            raise GuardError(f"status {code!r} has no path field")
        path = fields[i]
        i += 1
        if code[:1] in ("R", "C"):
            if i >= len(fields):
                raise GuardError(f"rename status {code!r} has no destination field")
            path = fields[i]  # old path consumed above; report the new one
            i += 1
        out.append((code, path))
    return out


def staged_report(cwd: str = ".") -> dict:
    """What the pending commit would carry, classified.

    Everything in the index is by definition tracked-or-becoming-tracked, so
    the amber tier does not apply here: a path is either fleet state or a
    source file somebody is about to commit off the shared tree.
    """
    raw = _run(["git", "diff", "--cached", "--name-status", "-z"], cwd)
    entries = [
        Entry(
            path,
            code,
            True,
            VERDICT_FLEET if classify(path, code).verdict == VERDICT_FLEET else VERDICT_MISWRITE,
            classify(path, code).reason,
        )
        for code, path in parse_name_status_z(raw)
    ]
    offenders = [e for e in entries if e.verdict == VERDICT_MISWRITE]
    return {
        "staged": len(entries),
        "offenders": [asdict(e) for e in offenders],
        "red": bool(offenders),
    }


def _head_branch(cwd: str) -> str | None:
    """The checked-out branch name, or None when detached."""
    proc = subprocess.run(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        cwd=cwd,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace").strip() or None


def _operation_in_progress(cwd: str) -> str | None:
    """Name of an in-flight merge/rebase/cherry-pick/revert, if any.

    These commits are not somebody typing `git commit` after an accidental
    edit -- they are git replaying work that already exists. Refusing them is
    both wrong and destructive: the advice this guard prints (`git restore
    --staged`, `git stash push`) would throw away a conflict resolution.
    """
    git_dir = _run(["git", "rev-parse", "--path-format=absolute", "--git-dir"], cwd).strip()
    for marker, name in (
        ("MERGE_HEAD", "merge"),
        ("REBASE_HEAD", "rebase"),
        ("rebase-merge", "rebase"),
        ("rebase-apply", "rebase"),
        ("CHERRY_PICK_HEAD", "cherry-pick"),
        ("REVERT_HEAD", "revert"),
    ):
        if os.path.exists(os.path.join(git_dir, marker)):
            return name
    return None


def precommit(cwd: str = ".") -> int:
    """The hook body. 0 lets the commit through, 1 refuses it.

    Scope is deliberately narrow, and every exclusion below is a case an
    adversarial review demonstrated the first version got wrong:

      * a LINKED worktree -- branch work belongs there;
      * HEAD not on `master` -- an agent that reacts to being caught by
        branching and committing properly must not then be blocked by the same
        guard. The guard is about the shared MASTER tree, and gating on "which
        tree" alone refused commits on `agent/*` branches checked out in it;
      * a merge / rebase / cherry-pick / revert in progress -- see
        `_operation_in_progress`. This also settles the `pre-merge-commit`
        question: a clean `git merge --no-ff` fires `pre-merge-commit`, not
        `pre-commit`, so it was never gated -- and now that is consistent
        rather than accidental, because merges are out of scope on purpose.
        Merges are how branch work is SUPPOSED to reach master.
    """
    try:
        if not is_main_worktree(cwd):
            return 0  # a linked worktree is where branch work belongs
        if _head_branch(cwd) != "master":
            return 0  # a real branch, correctly used, in the main checkout
        busy = _operation_in_progress(cwd)
        if busy:
            return 0  # git replaying existing work, not a fresh edit
        result = staged_report(cwd)
    except GuardError as exc:
        # A hook that cannot decide must not silently allow: that is the
        # failure mode this whole item is about. But it also must not wedge
        # every commit on this machine over a git hiccup, so it says so loudly
        # and lets the commit proceed.
        print(f"master-tree-guard: could not check ({exc}) -- allowing", file=sys.stderr)
        return 0

    if not result["red"]:
        return 0

    if os.environ.get(OVERRIDE_ENV):
        print(
            f"master-tree-guard: {len(result['offenders'])} source path(s) staged on "
            f"master's tree; {OVERRIDE_ENV} set, allowing.",
            file=sys.stderr,
        )
        return 0

    try:
        sys.stderr.reconfigure(errors="backslashreplace")
    except (AttributeError, OSError):  # pragma: no cover
        pass
    print("", file=sys.stderr)
    print("REFUSED: this commit carries source off master's shared working tree.", file=sys.stderr)
    for e in result["offenders"]:
        print(f"  {e['code']:<4} {e['path']}", file=sys.stderr)
    print(
        "\nThese belong on a branch. Either move them:\n"
        "    git restore --staged -- <path>\n"
        "    git stash push -- <path>\n"
        "    cd .worktrees/<your-slug> && git stash pop\n"
        f"or, if this really is a deliberate direct-to-master commit:\n"
        f"    {OVERRIDE_ENV}=1 git commit ...\n",
        file=sys.stderr,
    )
    return 1


def hook_path(cwd: str = ".") -> str:
    """Where the pre-commit hook belongs, honouring `core.hooksPath`.

    Resolved against the COMMON git dir, not `--git-dir`: in a linked worktree
    the latter is `.git/worktrees/<name>`, which has no `hooks/` of its own, so
    installing there would cover one worktree and miss the main tree -- the
    same one-of-two-places mistake requirement 4 warns about.
    """
    configured = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=cwd,
        capture_output=True,
    )
    if configured.returncode == 0:
        raw = configured.stdout.decode("utf-8", "replace").strip()
        if raw:
            # A RELATIVE hooksPath must resolve against the MAIN working tree,
            # not `--show-toplevel`: in a linked worktree the latter is that
            # worktree's own root, so `install-hook` run from a worktree wrote
            # the hook into the worktree and `hook_installed()` then reported
            # False for a hook that was installed. That is precisely the
            # one-of-two-places bug the docstring above claims to avoid --
            # the test named for it passed only because the fixture never set
            # `core.hooksPath`, so it exercised the fallback branch instead.
            base = raw if os.path.isabs(raw) else os.path.join(main_worktree(cwd), raw)
            return os.path.join(os.path.normpath(base), "pre-commit")
    common = _run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd).strip()
    return os.path.join(os.path.normpath(common), "hooks", "pre-commit")


def hook_installed(cwd: str = ".") -> bool:
    """True only if OUR hook is in place -- not merely some pre-commit hook."""
    try:
        path = hook_path(cwd)
    except GuardError:
        return False
    if not os.path.isfile(path):
        return False
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return HOOK_MARKER in fh.read()
    except OSError:
        return False


def install_hook(cwd: str = ".", force: bool = False) -> tuple[bool, str]:
    """Write the pre-commit hook. Returns (changed, message)."""
    path = hook_path(cwd)
    if os.path.isfile(path) and not hook_installed(cwd) and not force:
        return (
            False,
            f"a different pre-commit hook is already installed at {path}; "
            "refusing to overwrite it (pass --force to replace)",
        )
    if hook_installed(cwd) and not force:
        return (False, f"already installed at {path}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = HOOK_BODY.format(
        marker=HOOK_MARKER,
        override=OVERRIDE_ENV,
        interpreter=sys.executable.replace("\\", "/"),
    )
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    os.chmod(path, 0o755)
    return (True, f"installed at {path}")


def _emit_human(result: dict) -> None:
    # The first live run of this guard crashed HERE, with UnicodeEncodeError:
    # the Windows console is cp936/GBK and one of the paths the guard exists to
    # catch is `C:UsersuserDesktoptheoriamonitorpermtest.txt` carrying U+F03A
    # (a private-use stand-in for the colon that got eaten). A gate that dies
    # while printing the finding it just made is worse than no gate -- it fails
    # after the work, so it looks like a tooling glitch rather than a finding.
    # Degrade the display, never the verdict. `--json` is unaffected: json.dumps
    # defaults to ensure_ascii=True and escapes it.
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, OSError):  # pragma: no cover - non-reconfigurable stream
        pass
    print(f"tree: {result['tree']}")
    print(
        f"dirty paths: {result['total']}  "
        f"(fleet state {result['fleet_state']}, "
        f"unfiled {result['unfiled']}, "
        f"miswrites {result['miswrites']})"
    )
    if result["miswrite_paths"]:
        print("\nRED -- tracked files changed on the shared tree:")
        for e in result["miswrite_paths"]:
            print(f"  {e['code']} {e['path']}")
        print(
            "\nEach is unowned work sitting where a stray `git add` can sweep it\n"
            "into someone else's commit and a `git checkout --` can wipe it.\n"
            "Two valid resolutions -- the adjudication in\n"
            "monitor/runs/20260730T0440Z-S39/FINDINGS.md found both in one sample:\n"
            "  * it belongs on a branch     -> git stash push -- <path>\n"
            "                                  cd .worktrees/<slug> && git stash pop\n"
            "  * master really is its home  -> commit it (monitor/spec.py is the\n"
            "                                  standing example)\n"
            "Doing neither is the failure. `monitor/reflex.py` was a 69+/115- rewrite\n"
            "that sat here unowned and survived by luck."
        )
    if result["unfiled_paths"]:
        print("\nRED -- untracked, outside fleet state (file / ignore / delete it):")
        for e in result["unfiled_paths"]:
            print(f"  {e['code']} {e['path']}")
        print(
            "\nA trailing `/` is one line for a whole directory -- git's default.\n"
            "These gate too: `git add -A` sweeps untracked files, and this repo\n"
            "already carries a commit titled \"On master: autostash\" that did it."
        )


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="master_tree_guard",
        description="Detect source writes that landed on master's shared working tree.",
    )
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument(
        "--any-tree",
        action="store_true",
        help="judge whatever tree we are in, not only the main one (testing)",
    )
    ap.add_argument(
        "-C",
        dest="cwd",
        default=".",
        help="run as if started in this directory",
    )
    ap.add_argument(
        "mode",
        nargs="?",
        default="check",
        choices=("check", "precommit", "install-hook", "hook-status"),
        help=(
            "check (default): classify the main tree; "
            "precommit: the hook body, judges the INDEX; "
            "install-hook / hook-status: manage the commit-time gate"
        ),
    )
    ap.add_argument("--force", action="store_true", help="replace a foreign pre-commit hook")
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.mode == "precommit":
        return precommit(args.cwd)

    if args.mode == "install-hook":
        try:
            changed, message = install_hook(args.cwd, force=args.force)
        except GuardError as exc:
            print(f"GUARD-ERROR: {exc}", file=sys.stderr)
            return 3
        print(("installed: " if changed else "unchanged: ") + message)
        return 0

    if args.mode == "hook-status":
        installed = hook_installed(args.cwd)
        try:
            where = hook_path(args.cwd)
        except GuardError as exc:
            print(f"GUARD-ERROR: {exc}", file=sys.stderr)
            return 3
        print(json.dumps({"installed": installed, "path": where}, indent=2))
        return 0 if installed else 2

    try:
        result = report(args.cwd, require_main=not args.any_tree)
    except GuardError as exc:
        print(f"GUARD-ERROR: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _emit_human(result)
    return 2 if result["red"] else 0


if __name__ == "__main__":
    sys.exit(main())
