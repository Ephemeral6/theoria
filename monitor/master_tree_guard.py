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
     edited a real source file on the shared tree. This is the failure the item
     is about and it is the only tier that goes red.

  3. UNFILED (amber) -- an UNTRACKED path outside the whitelist. Scratch dirs,
     `pytest-*` residue, a run directory nobody committed. Worth naming,
     because that is where a lost deliverable hides, but it is not a miswrite
     and it does not gate: untracked files cannot be swept into somebody
     else's commit by `git add <path>` of an unrelated path, and half of them
     are legitimately mid-flight.

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
directory of any size. This does not weaken the RED tier, which concerns only
TRACKED files, and git never collapses those.

EXIT CODES.  0 = no miswrite (amber may still be reported)
             2 = at least one MISWRITE -- red
             3 = the guard could not determine the answer (not a pass)
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
    "monitor/res/",         # per-researcher contracts, retuned by the monitor
)

# Individual files (not prefixes) that are fleet state.
FLEET_STATE_FILES: frozenset[str] = frozenset(
    {
        "monitor/state.json",
        "monitor/accounts_state.json",
        "monitor/quota_state.json",
        "monitor/standing_state.json",
        "monitor/index.html",  # generated dashboard
    }
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
        )
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

    if path in FLEET_STATE_FILES:
        return Entry(path, code, tracked, VERDICT_FLEET, "whitelisted fleet state file")

    if (
        path.startswith(FLEET_STATE_LOG_DIR)
        and path.endswith(FLEET_STATE_LOG_SUFFIX)
        and "/" not in path[len(FLEET_STATE_LOG_DIR) :]
    ):
        return Entry(path, code, tracked, VERDICT_FLEET, "monitor log")

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
    """Classify every dirty path in the working tree containing `cwd`."""
    raw = _run(["git", "status", "--porcelain", "-z"], cwd)
    return [classify(path, code) for code, path in parse_status_z(raw)]


def report(cwd: str = ".", require_main: bool = True) -> dict:
    """Full verdict for the main working tree.

    `require_main=True` refuses to judge a linked worktree, where dirty source
    is the expected condition and a red would be nonsense.
    """
    if require_main and not is_main_worktree(cwd):
        raise GuardError(
            "not the main working tree -- a linked worktree is SUPPOSED to have "
            "dirty source; pass --any-tree to override"
        )
    entries = inspect(cwd)
    miswrites = [e for e in entries if e.verdict == VERDICT_MISWRITE]
    unfiled = [e for e in entries if e.verdict == VERDICT_UNFILED]
    fleet = [e for e in entries if e.verdict == VERDICT_FLEET]
    return {
        "tree": main_worktree(cwd) if require_main else os.path.abspath(cwd),
        "total": len(entries),
        "fleet_state": len(fleet),
        "unfiled": len(unfiled),
        "miswrites": len(miswrites),
        "red": bool(miswrites),
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
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
guard="$root/monitor/master_tree_guard.py"
if [ ! -f "$guard" ]; then
    echo "master-tree-guard: $guard not in this checkout -- allowing" >&2
    exit 0
fi
exec python "$guard" precommit
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


def precommit(cwd: str = ".") -> int:
    """The hook body. 0 lets the commit through, 1 refuses it."""
    try:
        if not is_main_worktree(cwd):
            return 0  # a linked worktree is where branch work belongs
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
            base = raw if os.path.isabs(raw) else os.path.join(
                _run(["git", "rev-parse", "--show-toplevel"], cwd).strip(), raw
            )
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
    body = HOOK_BODY.format(marker=HOOK_MARKER, override=OVERRIDE_ENV)
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
        print("\nAMBER -- untracked, outside fleet state (not a gate):")
        for e in result["unfiled_paths"]:
            print(f"  {e['code']} {e['path']}")


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
