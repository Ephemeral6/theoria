"""Reconstruct what `figures/SOURCES.sha256` claimed, at every revision it has had.

Written because V23's first pass published six drift numbers it had not measured
itself -- they came from a delegated audit, and an adversarial review reproduced
neither them nor the board item's "13 of 50". A count nobody can re-derive is the
thing this whole ticket is about, so here is the derivation, as a script that
ships beside its output.

**The metric, stated before it is computed.** The board item's claim is
"十三条已漂移 ... 而且是已提交的漂移（工作树是干净的）" -- drift that is already
committed. So for each revision R of the manifest, and each line
`(digest, path, status)` in it, the question is:

    does the digest R recorded for `path` match the content of `path`
    **as that same commit R had it**?

Answered from `git cat-file`, never from the working tree, so the answer does not
depend on which checkout this runs in -- the mistake that produced the wrong
manifest in the first place.

Three outcomes per line, and the distinction is the whole point:

* ``match``        -- recorded digest equals the blob at R. No drift.
* ``DRIFT``        -- path is in R's tree and the digests differ. Committed drift,
                      exactly what the ticket alleges.
* ``unverifiable`` -- path is not in R's tree at all. An untracked input, whose
                      content git never held, so no revision can be checked
                      against history. These are the `[untracked]` and
                      `ABSENT000…` lines, and the fact that they are
                      unverifiable-by-construction is the finding, not a gap in
                      this probe.

Run: python figures/runs/<id>/history_probe.py
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MANIFEST = "figures/SOURCES.sha256"
ABSENT = "ABSENT" + "0" * 58


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", REPO, *args],
        capture_output=True, text=True, check=True,
        env={**os.environ, "GIT_PAGER": "cat"},
    ).stdout


def git_bytes(*args: str) -> bytes | None:
    p = subprocess.run(["git", "-C", REPO, *args], capture_output=True)
    return p.stdout if p.returncode == 0 else None


def revisions() -> list[tuple[str, str]]:
    """(sha, iso-utc) for every commit that touched the manifest, oldest first."""
    out = []
    for line in git("log", "--reverse", "--date=iso-strict-local",
                    "--format=%H%x1f%cd", "--", MANIFEST).splitlines():
        if line.strip():
            sha, _, when = line.partition("\x1f")
            out.append((sha, when))
    return out


def parse(text: str) -> list[tuple[str, str, str]]:
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        head, _, bracket = line.rpartition("  ")
        digest, _, rel = head.partition("  ")
        rows.append((digest.strip(), rel.strip(), bracket.strip("[]")))
    return rows


def main() -> int:
    revs = revisions()
    print(f"{MANIFEST}: {len(revs)} revision(s)\n")
    header = f"{'revision':10} {'when (UTC+0800)':26} {'lines':>5} {'match':>6} {'DRIFT':>6} {'unver':>6}"
    print(header)
    print("-" * len(header))

    detail: list[str] = []
    for sha, when in revs:
        text = git_bytes("show", f"{sha}:{MANIFEST}")
        if text is None:
            continue
        rows = parse(text.decode("utf-8"))
        tree = set(git("ls-tree", "-r", "--name-only", sha).split("\n"))
        match = drift = unver = 0
        for digest, rel, status in rows:
            if rel not in tree:
                unver += 1
                continue
            blob = git_bytes("show", f"{sha}:{rel}")
            if blob is None:
                unver += 1
                continue
            actual = hashlib.sha256(blob).hexdigest()
            if digest == actual:
                match += 1
            else:
                drift += 1
                detail.append(f"  {sha[:8]} {rel}\n      manifest {digest}\n      blob     {actual}")
        print(f"{sha[:8]:10} {when:26} {len(rows):5} {match:6} {drift:6} {unver:6}")

    if detail:
        print("\ncommitted drift, line by line:")
        for d in detail:
            print(d)
    else:
        print("\nno committed drift at any revision.")

    print("\nEntry counts are the other number the ticket names. 50 is reproducible:")
    for sha, when in revs:
        text = git_bytes("show", f"{sha}:{MANIFEST}")
        n = len(parse(text.decode("utf-8"))) if text else 0
        print(f"  {sha[:8]} {when}  {n} entries")

    # --------------------------------------------------------------------
    # The second metric, and the one that actually bites.
    # --------------------------------------------------------------------
    # The table above asks "was the manifest true when it was written". The
    # answer is always yes, which is reassuring and not what anybody was worried
    # about. Drift happens *between* regenerations: the manifest stands still
    # while its declared sources move under it. So for each revision, compare it
    # against the tree at the last commit before the next regeneration -- the
    # worst state that manifest ever described. This is where RES-3's five
    # mismatches at baf16714 live, and where a real "N have drifted" claim would
    # have to come from.
    print("\nmaximum staleness each revision reached before the next regeneration:")
    print("(manifest at R vs the tree just before the next manifest commit)")
    for i, (sha, when) in enumerate(revs):
        text = git_bytes("show", f"{sha}:{MANIFEST}")
        if text is None:
            continue
        rows = parse(text.decode("utf-8"))
        if i + 1 < len(revs):
            end = f"{revs[i + 1][0]}~1"
            label = f"just before {revs[i + 1][0][:8]}"
        else:
            end = "HEAD"
            label = "HEAD"
        tree = set(git("ls-tree", "-r", "--name-only", end).split("\n"))
        drifted = []
        unver = 0
        for digest, rel, status in rows:
            if rel not in tree:
                unver += 1
                continue
            blob = git_bytes("show", f"{end}:{rel}")
            if blob is None:
                unver += 1
                continue
            if hashlib.sha256(blob).hexdigest() != digest:
                drifted.append(rel)
        print(f"  {sha[:8]} vs {label:24} {len(drifted):2} drifted, {unver} unverifiable")
        for rel in drifted:
            print(f"      {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
