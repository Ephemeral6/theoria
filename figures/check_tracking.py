"""Re-derive every claim ``figures/SOURCES.sha256`` makes, from outside it.

``SOURCES.sha256`` carries three claims per line: a digest, a path, and a status
in ``[brackets]``. Two of those are measurements and one is an **assertion**, and
that difference is what this probe exists for.

``verify.sh`` gate 4 diffs the committed manifest against a freshly generated
one. Both sides come out of ``sources.py``, so the gate proves the manifest is
what that module currently says -- and nothing more. The digest column survives
that arrangement because it is measured from the file either way. The status
column does not: ``sources.manifest_rows`` writes ``[tracked]`` or
``[untracked]`` from ``Source.tracked``, a boolean somebody *declared*. When A14
committed the fifteen ``baseline-arms/out/shards/ledger.*.jsonl`` shards while
the ``envelope_ledger`` rule still read ``tracked=False``, fifteen lines of the
committed manifest asserted ``[untracked]`` about files git tracked. Gate 4 was
green throughout, correctly by its own definition: both sides agreed, because
both sides were reading the same wrong sentence.

So this probe reads the *artefact*, not the module, and checks it against
authorities the artefact cannot influence:

* the status column against ``git ls-tree -r HEAD`` and ``os.path.isfile``;
* the digest column against a sha256 it computes itself;
* the ``ABSENT000…`` sentinel against the filesystem;
* the number of lines against a floor, because a probe that audits what is left
  of a truncated file and calls that green has audited nothing.

That is `check_coverage.py`'s house rule applied to a different surface: two
independently sourced descriptions of one fact can disagree, and the
disagreement is the finding. It also means this file must never import
``sources`` -- an oracle that asks the module under audit what to expect can
only prove that module self-consistent, which this directory has now paid for
twice (``PLAN.md`` §§264-274, 637-657).

The negative control is not optional and runs first under ``--selftest``. It
doctors the manifest under audit once per refusal branch this probe can reach --
both directions of the status mismatch, a corrupted digest, a present file
recorded absent, an absent line carrying a real digest, a status nobody
understands, a path that is not on disk, a path spelled with backslashes, and the
whole file truncated -- and requires a refusal for each. A probe that has never
been seen to refuse is a green light with nothing behind it, and a branch the
control never plants is a branch nobody has seen work: the first draft of this
control planted three defects and left six branches unexercised, including the
forward direction of the very mismatch the probe was written for.

    python check_tracking.py              # audit figures/SOURCES.sha256
    python check_tracking.py --selftest   # negative control, then the audit
    python check_tracking.py --manifest P # audit an arbitrary manifest
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
MANIFEST = os.path.join(HERE, "SOURCES.sha256")

#: The sentinel ``sources.manifest_rows`` writes for a declared-but-absent
#: source. Stated as a literal here rather than imported, per this file's
#: opening note -- if the two ever disagree, that is a finding and not a bug in
#: this probe.
ABSENT = "ABSENT" + "0" * 58

#: Statuses the manifest is allowed to write. An unknown one is a failure, not
#: a line to skip: a status this probe does not understand is a claim nobody is
#: checking.
PRESENT_STATUSES = {"tracked", "untracked"}
ABSENT_STATUSES = {"absent-optional", "absent-REQUIRED"}

#: How many source lines the manifest had when this floor was checked, stated as
#: a literal here for the same reason ``check_coverage.py`` states its inventory
#: as literals: this file may not import ``sources.py``, so it cannot ask how
#: many there should be, and *not asking* is the point.
#:
#: An adversarial review found the version of this probe without a floor
#: reporting ``1 manifest line(s): 1 tracked … every status re-derived from git``
#: over a manifest truncated from 61 lines to 1 -- literally true and materially
#: false, since 60 claims had been deleted rather than audited. P13 truncated
#: this exact file to zero bytes with a stray shell redirect, so that is not a
#: hypothetical. Growth is free; shrinkage is a finding.
MIN_SOURCE_LINES = 61


def parse(path: str) -> list[tuple[int, str, str, str]]:
    """``[(lineno, digest, relpath, status), ...]`` from a manifest file."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            # `<digest>  <path>  [<status>]` -- two spaces as the separator, and
            # a path may itself contain spaces, so split from the right.
            head, _, bracket = line.rpartition("  ")
            digest, _, rel = head.partition("  ")
            if not bracket.startswith("[") or not bracket.endswith("]"):
                raise ValueError(
                    f"{path}:{lineno}: no parsable [status] field (a single-space "
                    f"separator or trailing whitespace will also land here): {line!r}"
                )
            # `rel` is deliberately NOT stripped. Stripping it would silently
            # repair a path with a trailing space and defeat `noncanonical`'s
            # whitespace check -- quietly normalising a malformed claim is how a
            # probe comes to report green about something nobody wrote.
            rows.append((lineno, digest.strip(), rel, bracket[1:-1]))
    return rows


def git_committed() -> frozenset[str] | None:
    """Every path committed at ``HEAD``, or ``None`` if git cannot say.

    **``ls-tree -r HEAD``, not ``ls-files``.** The sentence this probe prints is
    "this build is not reproducible from a clean checkout", and ``ls-files``
    answers about the *index* -- so a ``git add`` that was never committed
    satisfies it, and the sentence would be false. ``HEAD`` is the authority for
    a claim about a clean checkout.

    **No pathspecs.** The first version passed all sixty-one manifest paths as
    pathspecs in one call, which an adversarial review broke three ways: a path
    outside the repo made git exit non-zero and poisoned every line with a false
    "git does not track it"; a single ``:(exclude)`` pathspec suppressed every
    other match; a glob inflated the authority set from 1 to 116. Untrusted
    strings from a file being audited have no business being pathspecs. One
    unfiltered listing, matched in Python.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", REPO_ROOT, "ls-tree", "-r", "-z", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "GIT_PAGER": "cat"},
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return frozenset(p for p in proc.stdout.split("\0") if p)


def noncanonical(rel: str) -> str | None:
    """Why ``rel`` is not a canonical repo-relative path, or ``None`` if it is.

    Checked rather than normalised. On a case-insensitive filesystem
    ``Baseline-Arms/BUDGET_REPORT.md`` hashes correctly and then fails to match
    git's spelling, so the probe would report "git does not track it" about a
    tracked file -- a true failure with a false diagnosis. Naming the real
    problem beats silently repairing it: ``sources.write_manifest`` cannot emit
    these, so one appearing means the manifest was written by something else.
    """
    if rel != rel.strip():
        return "has leading or trailing whitespace"
    if "\\" in rel:
        return "uses backslash separators; repo-relative paths use '/'"
    if rel.startswith("./") or rel.startswith("/"):
        return "is not repo-relative"
    if os.path.isabs(rel) or (len(rel) > 1 and rel[1] == ":"):
        return "is an absolute path"
    if ".." in rel.split("/"):
        return "contains a '..' segment"
    return None


def sha256_file(abspath: str) -> str:
    h = hashlib.sha256()
    with open(abspath, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(manifest: str) -> tuple[list[str], dict[str, int]]:
    """``(problems, counts)`` for one manifest. Empty problems means green."""
    rows = parse(manifest)
    problems: list[str] = []
    counts = {"lines": len(rows), "tracked": 0, "untracked": 0, "absent": 0, "hashed": 0}

    # A floor on coverage, checked before anything else. Without it this probe
    # reported green over a manifest truncated to one line: every claim it
    # audited passed, and sixty claims had been deleted rather than audited.
    if len(rows) < MIN_SOURCE_LINES:
        problems.append(
            f"{os.path.basename(manifest)} carries {len(rows)} source line(s); this "
            f"probe was written against {MIN_SOURCE_LINES}. Lines can only be added by "
            "declaring a source, so fewer than the floor means the manifest lost "
            "claims -- and a probe that audits what is left and calls that green is "
            "how a truncated file passes."
        )

    tracked = git_committed()
    if tracked is None:
        # Fail closed and stop. Continuing with an empty authority set produced
        # sixty-one false "git does not track it" lines burying the real cause.
        problems.append(
            "git could not list HEAD, so the status column could not be checked "
            "against anything. That is a failure and not a skip: the one column this "
            "probe exists for would be unaudited, and every other line's verdict "
            "would be an artefact of the missing answer."
        )
        return problems, counts

    for lineno, digest, rel, status in rows:
        where = f"{os.path.basename(manifest)}:{lineno}"

        why = noncanonical(rel)
        if why is not None:
            problems.append(
                f"{where}: path {rel!r} {why}. Left undiagnosed this becomes a false "
                "'git does not track it' about a file git tracks."
            )
            continue

        abspath = os.path.join(REPO_ROOT, *rel.split("/"))
        on_disk = os.path.isfile(abspath)
        in_git = rel in tracked

        if status not in PRESENT_STATUSES | ABSENT_STATUSES:
            problems.append(f"{where}: unknown status [{status}] for {rel}")
            continue

        if status in ABSENT_STATUSES:
            counts["absent"] += 1
            if on_disk:
                problems.append(
                    f"{where}: {rel} is recorded [{status}] with the ABSENT sentinel, "
                    "and it is on disk. A figure is drawing this file's absence while "
                    "the file is there."
                )
            if digest != ABSENT:
                problems.append(
                    f"{where}: {rel} is recorded [{status}] but carries a digest "
                    f"({digest[:12]}...) instead of the ABSENT sentinel."
                )
            continue

        # A present status. Three claims to re-derive.
        if not on_disk:
            problems.append(
                f"{where}: {rel} is recorded [{status}] but is not on disk; a manifest "
                "line for a file that is not there is not a hash, it is a hope."
            )
            continue
        counts["hashed"] += 1
        counts[status] += 1

        if digest == ABSENT:
            problems.append(
                f"{where}: {rel} carries the ABSENT sentinel and is on disk."
            )
        else:
            actual = sha256_file(abspath)
            if actual != digest:
                problems.append(
                    f"{where}: {rel}\n    manifest {digest}\n    disk     {actual}"
                )

        if status == "tracked" and not in_git:
            problems.append(
                f"{where}: {rel} is recorded [tracked] and is not committed at HEAD. "
                "This build is not reproducible from a clean checkout."
            )
        elif status == "untracked" and in_git:
            problems.append(
                f"{where}: {rel} is recorded [untracked] and is committed at HEAD. The "
                "declaration in sources.py has fallen behind the tree; gate 4 cannot "
                "see this, because both sides of gate 4 read that same declaration."
            )

    return problems, counts


# ---------------------------------------------------------------------------
# Negative control
# ---------------------------------------------------------------------------


def _doctor(rows: list[str], predicate, mutate) -> list[str] | None:
    """Return ``rows`` with the first line satisfying ``predicate`` mutated."""
    out = list(rows)
    for i, line in enumerate(out):
        if predicate(line):
            out[i] = mutate(line)
            return out
    return None


def _untracked_file_on_disk() -> str | None:
    """A repo-relative path that exists and is not committed, or ``None``.

    Needed to plant the *forward* mismatch -- a line claiming ``[tracked]`` about
    a file nobody committed. Discovered rather than hard-coded, because any path
    written down here would eventually be committed and silently stop planting
    anything.

    Ignored files count, so ``--exclude-standard`` is deliberately **not** passed.
    "On disk and not committed" is the condition being planted, and a gitignored
    ``__pycache__`` entry satisfies it exactly. It is also the only such file that
    reliably exists: in a clean checkout every non-ignored path is committed, and
    a control that quietly stops planting its most important case in exactly the
    tree CI uses is not a control.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", REPO_ROOT, "ls-files", "-z", "--others"],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "GIT_PAGER": "cat"},
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    for rel in sorted(p for p in proc.stdout.split("\0") if p):
        if noncanonical(rel) is None and os.path.isfile(
            os.path.join(REPO_ROOT, *rel.split("/"))
        ):
            return rel
    return None


def selftest(manifest: str = MANIFEST) -> int:
    """Doctor the manifest under audit; every planted defect must be refused.

    One defect per branch this probe can reach, because a branch the control
    never plants is a branch nobody has seen work. The first version planted
    three, all on ``[tracked]`` lines, and an adversarial review pointed out that
    six of nine refusal branches were therefore never exercised -- including the
    forward direction of the very mismatch the probe was written for.
    """
    with open(manifest, encoding="utf-8") as fh:
        original = fh.read().splitlines()

    def body(line: str) -> bool:
        return bool(line.strip()) and not line.lstrip().startswith("#")

    def is_tracked_line(line: str) -> bool:
        return body(line) and line.endswith("[tracked]")

    stray = _untracked_file_on_disk()
    cases: list[tuple[str, list[str] | None]] = [
        (
            "a [tracked] line relabelled [untracked] (the A14 defect)",
            _doctor(
                original,
                is_tracked_line,
                lambda l: l[: -len("[tracked]")] + "[untracked]",
            ),
        ),
        (
            "a digest corrupted in its first byte",
            _doctor(
                original,
                is_tracked_line,
                lambda l: ("0" if l[0] != "0" else "1") + l[1:],
            ),
        ),
        (
            "a present file recorded absent",
            _doctor(
                original,
                is_tracked_line,
                lambda l: ABSENT + l[64:].replace("[tracked]", "[absent-optional]"),
            ),
        ),
        (
            "an unknown status nobody is checking",
            _doctor(
                original,
                is_tracked_line,
                lambda l: l[: -len("[tracked]")] + "[probably-fine]",
            ),
        ),
        (
            "a [tracked] line for a path that is not on disk",
            _doctor(
                original,
                is_tracked_line,
                lambda l: l.replace("  ", "  no/such/file.json  ", 1)[: l.find("  ")]
                + "  no/such/file.json  [tracked]",
            ),
        ),
        (
            "an absent-status line carrying a real digest",
            # The path must also be off disk, or the "recorded absent and it is
            # on disk" branch fires first and this one stays unexercised -- which
            # is what the first draft of this case did.
            _doctor(
                original,
                is_tracked_line,
                lambda l: l[:64] + "  no/such/file.json  [absent-optional]",
            ),
        ),
        (
            "a path spelled with backslashes",
            _doctor(
                original,
                is_tracked_line,
                lambda l: l[:64] + l[64:].replace("/", "\\"),
            ),
        ),
        (
            "the manifest truncated to a single source line",
            [l for l in original if not body(l)] + [next(l for l in original if body(l))],
        ),
    ]
    if stray is not None:
        # The digest has to be the stray's *real* one, or the digest check fires
        # first and the status branch this case exists for is never reached.
        stray_digest = sha256_file(os.path.join(REPO_ROOT, *stray.split("/")))
        cases.append(
            (
                f"a [tracked] line for {stray}, which is on disk and not committed "
                "(the forward direction of the A14 defect)",
                _doctor(
                    original,
                    is_tracked_line,
                    lambda l: f"{stray_digest}  {stray}  [tracked]",
                ),
            )
        )

    failures = []
    for label, doctored in cases:
        if doctored is None:
            failures.append(f"could not plant: {label} (no matching line in {manifest})")
            continue
        fd, tmp = tempfile.mkstemp(prefix="check_tracking.", suffix=".sha256")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(doctored) + "\n")
            problems, _ = audit(tmp)
            if problems:
                print(f"  refused: {label}", flush=True)
                print(f"           {problems[0].splitlines()[0]}", flush=True)
            else:
                failures.append(f"NOT refused: {label}")
        finally:
            os.unlink(tmp)

    if failures:
        print("negative control did not fire:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    note = "" if stray is not None else (
        " -- NOTE: the forward direction ([tracked] about an uncommitted file) could "
        "not be planted, because this tree holds no untracked file to point at. That "
        "branch is unexercised here"
    )
    print(f"negative control fires on all {len(cases)} planted defects{note}", flush=True)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", default=MANIFEST, help="manifest to audit")
    ap.add_argument(
        "--selftest",
        action="store_true",
        help="run the negative control first; a probe never seen to refuse proves nothing",
    )
    args = ap.parse_args(argv)

    # The control doctors the file actually under audit. It used to doctor the
    # committed manifest whatever --manifest said, so `--selftest --manifest P`
    # demonstrated a refusal on a file it was not about to check.
    if args.selftest and selftest(args.manifest) != 0:
        return 1

    problems, counts = audit(args.manifest)
    # Problems go to stderr and the summary to stdout, matching the other probes
    # in this directory. Flushed in order because verify.sh captures them into
    # one file with `2>&1`, and a transcript in which the negative control's
    # refusals appear *after* the failures they are meant to precede reads as
    # the probe having run backwards.
    sys.stdout.flush()
    if problems:
        print(f"{os.path.basename(args.manifest)}: {len(problems)} problem(s)", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print(
        f"{counts['lines']} manifest line(s): {counts['tracked']} tracked, "
        f"{counts['untracked']} untracked, {counts['absent']} absent; "
        f"{counts['hashed']} digest(s) recomputed, every status re-derived from git"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
