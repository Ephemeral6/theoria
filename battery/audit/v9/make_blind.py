"""Build the blinded attacker trees for V9.

Strips every docstring and every comment from the battery code the attackers
are allowed to see, by round-tripping through `ast.unparse`.  What survives is
the computation and the registered `definition=` strings -- the metric's
definition and its code, which is exactly what PREREG_V9 §"blind" says an
attacker may have.  What does not survive is the prose: design intent, known
weaknesses, defence notes.

**The source is a git ref, not a directory.**  It used to be a hardcoded
absolute path into `.worktrees/v9-battery-gaming-audit`, which was wrong twice
over.  The small wrong: that path exists on one machine and only until the
worktree is pruned.  The large wrong: a worktree's HEAD moves.  That branch's
HEAD advanced from `9892d23c` -- the commit `make_blind.py`, `PREREG_V9.md` and
`BLINDING.md` all landed in, before any attack -- through `520dc5dd`, which
added the three defences the attacks provoked, to `0d586b6f`.  So anyone
re-running this file was reading four metric modules that had been edited
*because of* the attacks, and rebuilding a "blind" that showed the attackers
the answers.  Blinding that fails silently is worse than no blinding, because
it still produces a verdict.  Hence `BLIND_REF` is a pinned commit sha and not
a branch name: a branch name reproduces the same drift one indirection later.

Every path out of this module either produces the tree at the pinned ref or
raises `BlindingError` and exits non-zero.  There is no fallback to the working
tree, no fallback to a default directory, and no best-effort mode.
"""
import argparse
import ast
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys

# The commit the V9 attackers were blinded against: "battery V9:
# pre-registration, poverty certificate, blinding -- before any attack"
# (2026-07-29 09:52:28 +0800).  An ancestor of master, so it still resolves
# after .worktrees/v9-battery-gaming-audit and its branch are both deleted.
BLIND_REF = "9892d23caf72436c8ce8eefaa9ef59bfc2b03cc8"

OUT_ROOT = os.path.dirname(os.path.abspath(__file__))

COPY = [
    "battery/__init__.py",
    "battery/model.py",
    "battery/metrics/__init__.py",
    "battery/metrics/economy.py",
    "battery/metrics/epistemic.py",
    "battery/metrics/exploration.py",
    "battery/metrics/mechanism.py",
    "battery/metrics/planning.py",
]

# Docstring-stripped like COPY: the protocol, not the intent.
PROTOCOL = [
    "battery/audit/v9/check.py",
    "battery/audit/v9/attack.py",
]

# Empty package shims -- the real battery.audit imports the audit under test,
# so the attacker's copy needs the packages to exist and to be empty.
SHIMS = [
    "battery/audit/__init__.py",
    "battery/audit/v9/__init__.py",
]


class BlindingError(RuntimeError):
    """Blinding could not be performed exactly as specified.

    Raised instead of degrading.  Every caller lets it propagate; `__main__`
    prints it and exits 2.
    """


def _git(args, repo, binary=False):
    """Run git in `repo` and return stdout.  Raises BlindingError on failure."""
    try:
        proc = subprocess.run(
            ["git"] + args, cwd=repo, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )
    except OSError as exc:                      # git absent / not on PATH
        raise BlindingError(
            "cannot run git (%s); the blinded tree is built from a git ref and "
            "there is no non-git path to it" % exc)
    if proc.returncode != 0:
        raise BlindingError(
            "git %s failed (exit %d): %s"
            % (" ".join(args), proc.returncode,
               proc.stderr.decode("utf-8", "replace").strip()))
    return proc.stdout if binary else proc.stdout.decode("utf-8")


def repo_root(start=None):
    """The work tree containing this file.  Raises if there is not one."""
    start = start or OUT_ROOT
    if not os.path.isdir(start):
        raise BlindingError("no such directory: %s" % start)
    try:
        proc = subprocess.run(
            ["git", "-C", start, "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as exc:
        raise BlindingError("cannot run git (%s)" % exc)
    if proc.returncode != 0:
        raise BlindingError(
            "%s is not inside a git work tree, so a ref cannot be resolved; "
            "refusing to guess a source directory" % start)
    return proc.stdout.decode("utf-8").strip()


def resolve(ref, repo):
    """Pin `ref` to a full commit sha.  Raises if it does not name a commit."""
    sha = ""
    try:
        sha = _git(["rev-parse", "--verify", "--quiet", "%s^{commit}" % ref],
                   repo).strip()
    except BlindingError:
        sha = ""
    if not sha:
        raise BlindingError(
            "ref %r does not resolve to a commit in %s -- refusing to fall "
            "back to the working tree or to any directory, because a tree "
            "built from anything but the pinned commit is not the blind"
            % (ref, repo))
    return sha


def read_at(sha, rel, repo):
    """The exact blob bytes of `rel` at `sha`, decoded as UTF-8.

    `cat-file blob` rather than `git show`: it bypasses the smudge and eol
    filters, so what gets hashed downstream is what the commit records rather
    than what this machine's `core.autocrlf` would have produced.
    """
    try:
        raw = _git(["cat-file", "blob", "%s:%s" % (sha, rel)], repo,
                   binary=True)
    except BlindingError as exc:
        raise BlindingError(
            "%s is missing at %s -- the blinded tree cannot be built from this "
            "ref (%s)" % (rel, sha[:12], exc))
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BlindingError("%s at %s is not UTF-8: %s" % (rel, sha[:12], exc))


def strip(text):
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                rest = body[1:]
                node.body = rest if rest else [ast.Pass()]
    return ast.unparse(ast.fix_missing_locations(tree)) + "\n"


# Runtime reason strings that survive docstring-stripping and give away design
# intent (why a guard exists, what confound it fights).  Replaced with terse
# equivalents in the blinded tree; status and value are untouched, only the
# human-readable reason.  Recorded in battery/BLINDING.md.
NEUTRALISE = [
    ("this trace is a coverage walk, not an attempt to win; scoring it for "
     "path efficiency would measure the trace's purpose rather than the arm",
     "run intent is not 'solve'"),
    ("this run never reached the goal, and path efficiency has no floor -- a "
     "run that gives up on step one scores better than any solve, so scoring "
     "a loss would rank failure as excellence",
     "no step is marked won"),
    ("this arm records no repair episode; an arm with no manual cannot be "
     "refuted by one, so the absence is structural",
     "the run records no repair episode"),
    ("no step in this run failed, so there is no failure to respond to",
     "the run records no failed step"),
    ("multi-level runs exist but the cross-level annotation schema is not yet "
     "defined; see STATUS.md",
     "no cross-level mechanism annotation"),
    ("fewer than %d turns; the same early-exit confound as E2",
     "fewer than %d turns"),
    ("fewer than eight transitions; quartiles meaningless",
     "fewer than eight transitions"),
]


def blind(text):
    """Strip the prose, then neutralise the reasons that leak intent."""
    text = strip(text)
    for old, new in NEUTRALISE:
        text = text.replace(old, new)
    return text


def contents_at(ref=BLIND_REF, repo=None):
    """{relpath: blinded text} for one attacker's tree, without touching disk.

    Returns `(sha, contents)`.  The six attackers' trees are identical to each
    other -- they differ only in the two Markdown briefs, which this module
    never wrote -- so one map characterises the whole blind.  This is what the
    regression test reads, and it is why the test needs no scratch directory.
    """
    repo = repo or repo_root()
    sha = resolve(ref, repo)
    out = {rel: blind(read_at(sha, rel, repo)) for rel in COPY + PROTOCOL}
    for rel in SHIMS:
        out[rel] = ""
    return sha, out


def digests_at(ref=BLIND_REF, repo=None):
    """`(sha, {relpath: sha256})` for the blinded tree at `ref`."""
    sha, contents = contents_at(ref, repo)
    return sha, {rel: hashlib.sha256(text.encode("utf-8")).hexdigest()
                 for rel, text in sorted(contents.items())}


def build(dest, sha, repo):
    """Write one attacker's blinded tree.  Returns {relpath: sha256}."""
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    _, contents = contents_at(sha, repo)
    digests = {}
    for rel, text in sorted(contents.items()):
        target = os.path.join(dest, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with io.open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        digests[rel] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digests


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*",
                    help="attacker names, one tree each (e.g. a1 a2 ... a6)")
    ap.add_argument("--ref", default=BLIND_REF,
                    help="git ref to blind (default: the pinned V9 commit %s). "
                         "Override only for a new audit round, and record the "
                         "ref you used." % BLIND_REF[:12])
    ap.add_argument("--out", default=os.path.join(OUT_ROOT, "v9-blind"),
                    help="output root (default: %(default)s)")
    ap.add_argument("--digests", action="store_true",
                    help="print the blinded tree's sha256 map and exit "
                         "without writing anything")
    args = ap.parse_args(argv)

    repo = repo_root()
    sha = resolve(args.ref, repo)
    if sha != resolve(BLIND_REF, repo):
        print("WARNING: blinding against %s, not the pinned V9 ref %s"
              % (sha[:12], BLIND_REF[:12]), file=sys.stderr)

    if args.digests:
        _, digests = digests_at(sha, repo)
        json.dump({"ref": args.ref, "commit": sha,
                   "python": "%d.%d" % sys.version_info[:2],
                   "files": digests}, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if not args.names:
        ap.error("no attacker names given; nothing to build")

    trees = {}
    for name in args.names:
        trees[name] = build(os.path.join(args.out, name), sha, repo)
        print("built", name, "from", sha[:12])

    manifest = os.path.join(args.out, "BLIND_MANIFEST.json")
    with io.open(manifest, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"ref": args.ref, "commit": sha,
                   "python": "%d.%d" % sys.version_info[:2],
                   "trees": trees}, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("wrote", manifest)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BlindingError as exc:
        print("BLINDING FAILED: %s" % exc, file=sys.stderr)
        sys.exit(2)
