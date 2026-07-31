"""No tracked *artefact* may record where its builder stood -- repo-wide.

This is `exam/tools/check_artefact_locations.py` generalised past `exam/`.
V27 fixed one file (`exam/artifacts/build_manifest.json`, twelve absolute paths
naming whichever worktree ran `build_papers`) and left a gate behind so it could
not come back. The same channel is open in every other territory: at the time
this was written, 498 tracked files carried this machine's home directory
spelled out in full.

    python tools/check_locations.py            # 0 clean, 1 findings
    python tools/check_locations.py --verbose   # also list what is exempt

## Two scopes, two rules

**Artefact scope** -- tracked files under `*/artifacts/`, `figures/csv/`,
`figures/paper/`, `freeze/*.json|*.md`, `release/*.json|*.jsonl|*.md`,
`CONTRACTS/`. These are *generated*, they are what a Phase 4 release manifest
publishes, and a location baked into one of them churns on every rebuild and
generates merge conflicts between two branches that agree. Rule: **clean, or
pinned**. An exemption is `(path, sha256, reason)`; the sha256 means the
exemption dies the moment the file is regenerated, so a regeneration that is
still dirty comes back red instead of inheriting a licence granted to different
bytes.

**Run scope** -- tracked files under any `runs/` segment. These are the
provenance canon ("the disk is the memory"): they are captured tool output and
write-once records, and scrubbing a path out of a Fast Downward log falsifies a
third party's words about what it did. Rule: **exempt, but only by name and
date**. Every run directory that carries an absolute path is listed in
`tools/locations_allowlist.json` with a date, a file count and a reason. A run
directory that is *not* listed is red, and a listed one whose count has grown is
red: a write-once archive that gained an absolute path since the allowlist was
written is a new leak wearing the old one's clothes. The exemption is a
statement someone signed, not a silence in a glob.

**Out of scope entirely** -- `monitor/` (a fleet runtime whose logs, inbox and
CI conflict records are machine-local records by design, and whose
`prompts/ops/*.md` deliberately tell a session where the repository is),
`*/evidence/` (captured API-era ledgers), and every path that is source code or
prose. Hand-written code and prose are excluded because the two live examples in
this repository are a *negative-control fixture* (`fleet-study/verify.py`, whose
absolute path is the test vector a citation checker must reject) and three
*findings* (`freeze/VARIANCE_BASIS.md`, `papers/phase1-workshop/REVIEW.md`,
`fleet-study/data/README.md`, sentences that are *about* absolute-path defects).
A scanner that reddened on those would be asking prose to stop naming the bug.

## How to add an exemption

By hand, in `tools/locations_allowlist.json`. There is deliberately no
`--bless` flag and no regeneration script: a one-command refresh would turn
every new leak into an exemption the moment somebody was in a hurry, which is
the silence this gate exists to replace. `python tools/check_locations.py`
prints the path and the sha256 you need; the reason is yours to write.

## What this deliberately does not check

Whether two builds in two different directories agree byte for byte. That is the
empirical form of the same question, it catches channels nobody enumerated, and
it lives in `exam/verify.py`'s `location` stage. This is the cheap always-on
half.
"""
from __future__ import annotations

import fnmatch
import getpass
import hashlib
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ALLOWLIST = os.path.join(HERE, "locations_allowlist.json")

#: Generated surfaces. Anything matched here must be clean or pinned.
ARTEFACT_GLOBS: Sequence[str] = (
    "*/artifacts/*",
    "artifacts/*",
    "figures/csv/*",
    "figures/paper/*",
    "freeze/*.json",
    "freeze/*.md",
    "release/*.json",
    "release/*.jsonl",
    "release/*.md",
    "CONTRACTS/*",
)

#: Territories whose files are records of a machine, not products of a build.
OUT_OF_SCOPE_PREFIXES: Sequence[str] = ("monitor/",)
OUT_OF_SCOPE_GLOBS: Sequence[str] = ("*/evidence/*",)

#: A drive-letter path, a POSIX path under a home or temp root, or a worktree
#: segment. Deliberately not "any string containing a slash": repo-relative
#: paths are the fix, so they must not trip this.
#:
#: Two patterns are narrower than V27's originals, and both narrowings were
#: forced by running this repo-wide before trusting it:
#:
#: * `windows absolute path` requires the drive letter to be a *lone* letter.
#:   `[A-Za-z]:[\\/]` matches the `p:/` inside `http://`, so the first run
#:   reported all twelve paper SVGs (their DOCTYPE carries the W3C DTD URL) and
#:   `release/LICENCE_POSTURE.md` (which cites arcprize.org). Twelve false reds
#:   on the paper's own figures is how a gate gets switched off. `exam/` has no
#:   URLs in its artefacts, which is why the original never had to say this.
#: * `worktree segment` requires a path separator before `.worktrees`, so the
#:   sentence "one `rm -rf .worktrees/` from nonexistent" in `freeze/MANIFEST.json`
#:   is prose about worktrees rather than a location. The pre-fix exam blob is
#:   `...\theoria\.worktrees\...` and still matches.
#:
#: `backslash path separator` is defined but NOT enforced here -- see
#: `ENFORCED_PATTERN_NAMES`.
PATTERNS: List[Tuple[str, "re.Pattern[str]"]] = [
    ("windows absolute path", re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]")),
    ("posix home path", re.compile(r"/(?:home|Users)/[^\"\s]+")),
    ("temp directory", re.compile(r"(?i)(?:/tmp/|[\\/]Temp[\\/]|TMPDIR)")),
    ("worktree segment", re.compile(r"[\\/]\.worktrees[\\/]")),
    ("backslash path separator", re.compile(r"[A-Za-z0-9_.\-]\\[A-Za-z0-9_.\-]")),
]

#: What the gate actually fails on, per scope.
#:
#: `backslash path separator` is in neither. Inside `exam/artifacts` it was a
#: useful proxy, because every backslash there came from an absolute Windows
#: path. Repo-wide it fires on regex source in prose (`freeze/ENGINE_MANIFEST.md`
#: quotes `VERSION\s*=`), on a mojibake byte pair in `release/RULINGS_PROPOSED.md`,
#: on `\n` inside quoted Python in `CONTRACTS/verify.py`, and on genuinely
#: *relative* Windows paths such as `theory\generated\domain.pddl` in eight
#: cold-start artefacts. A relative path names no machine, which is the only
#: thing this gate is about; the absolute-path patterns already catch the case
#: the proxy was standing in for.
ARTEFACT_PATTERN_NAMES = frozenset({
    "windows absolute path", "posix home path", "temp directory",
    "worktree segment"})

#: The subset applied to run directories: locations only. `temp directory` is
#: dropped because captured tool output legitimately narrates its own scratch
#: directory by the thousand line, and the username pattern is dropped for the
#: same reason it is dropped from prose.
RUN_PATTERN_NAMES = frozenset({
    "windows absolute path", "posix home path", "worktree segment"})


#: Account names that are also English words. Searching for one of these finds
#: prose, not provenance.
COMMON_ACCOUNT_NAMES = frozenset({
    "user", "users", "admin", "administrator", "runner", "build", "builder",
    "test", "guest", "root", "default", "owner", "public"})


def _username_pattern() -> Optional[Tuple[str, "re.Pattern[str]"]]:
    """The building user's name, which is location by another route.

    Skipped when the name is too short or too common to search for without
    matching ordinary prose -- a false red here would be worse than the gap,
    because the absolute-path patterns already catch the paths it appears in.

    This machine's account is literally `user`, and V27's `len(user) < 4` guard
    lets a four-letter name through: the first repo-wide run reported all ten
    `figures/paper/**` SVGs, every hit being the substring inside
    `patternUnits="userSpaceOnUse"`. Ten false reds on the paper's own figures,
    from the gate that is supposed to protect them.
    """
    try:
        user = getpass.getuser()
    except Exception:                                     # pragma: no cover
        return None
    if len(user) < 5 or user.lower() in COMMON_ACCOUNT_NAMES:
        return None
    return ("building user's name", re.compile(re.escape(user)))


def tracked() -> List[str]:
    out = subprocess.run(["git", "ls-files"], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p.strip()]


def classify(rel: str) -> str:
    """-> 'artefact' | 'run' | 'skip'"""
    if any(rel.startswith(p) for p in OUT_OF_SCOPE_PREFIXES):
        return "skip"
    if any(fnmatch.fnmatch(rel, g) for g in OUT_OF_SCOPE_GLOBS):
        return "skip"
    if "runs" in rel.split("/"):
        return "run"
    if any(fnmatch.fnmatch(rel, g) for g in ARTEFACT_GLOBS):
        return "artefact"
    return "skip"


def run_dir(rel: str) -> str:
    """`a/runs/b/c/d.txt` -> `a/runs/b`; a stray file directly under runs/ is
    its own unit, so a loose `A4-COMMIT_MSG.txt` cannot hide behind a sibling."""
    parts = rel.split("/")
    i = parts.index("runs")
    return "/".join(parts[:i + 2])


def _searchable(rel: str, raw: str) -> str:
    """What to search: decoded string values for JSON, raw text otherwise.

    Inherited from V27's scanner, and inherited *with* its scar. The first
    version searched raw bytes and reported seven findings in four exam papers,
    every one false: JSON escapes a newline as the two characters backslash-n,
    so prose containing "asked:" before a line break literally holds `asked:\\n`
    on disk, which matches a drive-letter pattern and a backslash-separator
    pattern alike. A location scanner that fires on ordinary prose gets turned
    off within a day.
    """
    if not rel.endswith(".json"):
        return raw
    try:
        doc = json.loads(raw)
    except ValueError:
        return raw
    found: List[str] = []

    def walk(node):
        if isinstance(node, str):
            found.append(node)
        elif isinstance(node, dict):
            for k, v in node.items():
                found.append(str(k))
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(doc)
    return chr(10).join(found)


def _patterns(scope: str) -> List[Tuple[str, "re.Pattern[str]"]]:
    wanted = (ARTEFACT_PATTERN_NAMES if scope == "artefact"
              else RUN_PATTERN_NAMES)
    pats = [p for p in PATTERNS if p[0] in wanted]
    user = _username_pattern()
    if user and scope == "artefact":
        pats.append(user)
    return pats


def sha256(path: str) -> str:
    """Content digest, over LF-normalised bytes.

    Not the git blob hash and not the raw file hash. `core.autocrlf` is true on
    the machine this repository is developed on and only some paths carry an
    `eol=lf` attribute, so `freeze/VARIANCE_BASIS.md` checks out CRLF here and
    LF on a Linux clone. A raw digest would make every exemption expire at the
    checkout boundary -- the gate would be red on someone else's machine for a
    reason that is not about the file. The pin is a claim about content.
    """
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def scan(paths: Optional[Sequence[str]] = None) -> Dict[str, list]:
    """-> {'artefact': [(rel, what, sample)], 'run': [(rel, what, sample)]}"""
    findings: Dict[str, list] = {"artefact": [], "run": []}
    for rel in (paths if paths is not None else tracked()):
        scope = classify(rel)
        if scope == "skip":
            continue
        full = os.path.join(REPO, rel)
        if not os.path.exists(full):
            continue
        try:
            with open(full, encoding="utf-8") as fh:
                raw = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        text = _searchable(rel, raw)
        for what, rx in _patterns(scope):
            m = rx.search(text)
            if m:
                start = max(0, m.start() - 30)
                findings[scope].append(
                    (rel, what, text[start:m.end() + 40].replace("\n", " ")))
                break     # one finding per file is enough to make the point
    return findings


def load_allowlist(path: str = ALLOWLIST) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def adjudicate(findings: Dict[str, list], allow: dict) -> Tuple[list, list]:
    """-> (violations, notes). A violation is (kind, subject, why)."""
    violations: List[Tuple[str, str, str]] = []
    notes: List[str] = []

    pinned = {e["path"]: e for e in allow.get("artefacts", [])}
    for rel, what, sample in findings["artefact"]:
        entry = pinned.get(rel)
        if entry is None:
            violations.append(("artefact", rel, "%s: %s" % (what, sample[:80])))
            continue
        actual = sha256(os.path.join(REPO, rel))
        if actual != entry["sha256"]:
            violations.append((
                "artefact", rel,
                "pinned as %s..., on disk %s... -- the exemption was granted to "
                "different bytes, so it does not carry over"
                % (entry["sha256"][:12], actual[:12])))

    dated = {e["dir"]: e for e in allow.get("runs", [])}
    counts: Dict[str, int] = {}
    for rel, _what, _sample in findings["run"]:
        counts[run_dir(rel)] = counts.get(run_dir(rel), 0) + 1
    for directory, n in sorted(counts.items()):
        entry = dated.get(directory)
        if entry is None:
            violations.append((
                "run", directory,
                "%d file(s) record an absolute path and this run directory is "
                "not in the dated allowlist" % n))
        elif n > entry["files"]:
            violations.append((
                "run", directory,
                "allowlisted %s for %d file(s), now %d -- a write-once archive "
                "gained an absolute path after it was signed off"
                % (entry["dated"], entry["files"], n)))
        elif n < entry["files"]:
            notes.append("%s: allowlisted for %d, now %d (shrunk -- update the "
                         "count when convenient)" % (directory, entry["files"], n))
    for directory in sorted(set(dated) - set(counts)):
        notes.append("%s: allowlisted but clean now; the entry can be dropped"
                     % directory)
    for rel in sorted(set(pinned) - {f[0] for f in findings["artefact"]}):
        notes.append("%s: pinned but clean now; the entry can be dropped" % rel)
    return violations, notes


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    verbose = "--verbose" in argv
    findings = scan()
    allow = load_allowlist()
    violations, notes = adjudicate(findings, allow)

    n_art = sum(1 for r in tracked() if classify(r) == "artefact")
    n_run = sum(1 for r in tracked() if classify(r) == "run")
    print("locations: %d artefact file(s), %d run file(s) scanned; "
          "%d artefact finding(s), %d run finding(s)"
          % (n_art, n_run, len(findings["artefact"]), len(findings["run"])))
    print("           %d artefact exemption(s) and %d dated run-dir "
          "exemption(s) on file"
          % (len(allow.get("artefacts", [])), len(allow.get("runs", []))))
    if verbose:
        for entry in allow.get("artefacts", []):
            print("  PINNED %-58s %s" % (entry["path"], entry["reason"][:80]))
        for entry in allow.get("runs", []):
            print("  DATED  %-58s %s  %d file(s)"
                  % (entry["dir"], entry["dated"], entry["files"]))
    for note in notes:
        print("  note: %s" % note)

    if not violations:
        print("locations: clean -- every absolute path in a tracked artefact or "
              "run record is one somebody signed for")
        return 0
    print("\n%d violation(s):" % len(violations))
    for kind, subject, why in violations:
        print("  %-9s %-56s %s" % (kind, subject, why))
    print("\nAn artefact violation is fixed at the generator, then regenerated "
          "-- generated files are never hand-edited. A run violation is fixed "
          "either by fixing whatever wrote the path (if the run is still being "
          "produced) or by adding a dated entry to tools/locations_allowlist.json "
          "saying why this write-once record is allowed to name a machine. "
          "Deleting the pattern from a captured log is not one of the options: "
          "it falsifies a third party's output.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
