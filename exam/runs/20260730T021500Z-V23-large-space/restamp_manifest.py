"""Re-stamp this run's MANIFEST.json from the directory's own bytes.

The manifest was maintained by hand for five rounds and fell behind its own
directory twice (round five found six stale hashes; round six found
`adversarial/round6-findings.md` present, tracked, and unlisted).  Hand
maintenance is the defect, so this regenerates the `files` block instead.

Metadata keys are read from the existing manifest and preserved verbatim --
this script re-stamps, it does not author.  Exclusions are explicit and
mirrored in the manifest's own `note`:

  * `__pycache__/`      byte-unstable, not an artefact
  * `BASELINE-cycle94.md`  another session's cycle log, not this run's artefact
  * `restamp_manifest.py` itself, which would otherwise be a hash of the
    generator inside the thing it generates

`_survey_manifests.py` was excluded here until cycle 107 on the grounds that it
"produces nothing this run claims". That was false: the run cites its census --
36 stale hashes across 8 of 13 manifests -- as evidence, and its sibling
`_survey_stale_kinds.py` was listed all along. An exclusion whose stated reason
is contradicted by the document it serves is the defect this file exists to
stop.

Usage:  python restamp_manifest.py [--check]
  (no args)  rewrite MANIFEST.json
  --check    exit 1 if the manifest does not match the directory, print the diff
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "MANIFEST.json")

EXCLUDED_NAMES = {
    "MANIFEST.json",
    "BASELINE-cycle94.md",
    "restamp_manifest.py",
}
EXCLUDED_DIRS = {"__pycache__"}


class WorkingCopyIsNotPublished(Exception):
    """A listed file's disk bytes are not the bytes git will publish."""


def _assert_published_bytes(rel, data):
    """`exam/.gitattributes` pins `* text eol=lf`, so for every file under
    `exam/` the working copy and the committed blob are the same bytes -- unless
    a tool wrote CRLF after checkout, which is not something git undoes in the
    working tree.  Round six's manifest was stamped over two such files, so its
    hashes did not match the bytes at the commit carrying them, which is exactly
    what the manifest's own `note` says they are.

    An earlier version of this docstring said "nothing could see it", and round
    seven refuted that: `git diff` prints `warning: in the working copy of
    '<path>', CRLF will be replaced by LF the next time Git touches it`, naming
    the file, regardless of `core.autocrlf`, and `git ls-files --eol` reports
    `i/lf w/crlf` outright.  What is true is narrower and still worth guarding:
    `git diff`'s *stdout* is empty, so a diff read for content shows nothing,
    and after a `git add` refreshes the stat cache even the warning stops.

    Hashing the disk bytes is only correct while the two coincide, so the
    coincidence is asserted rather than assumed."""
    if b"\r\n" in data:
        raise WorkingCopyIsNotPublished(
            "%s has CRLF in the working copy; exam/.gitattributes pins LF, so "
            "git will publish different bytes than these and the stamp would be "
            "wrong at the commit that carries it. Normalise the file first." % rel)


def artefacts():
    """Tracked files only, asked of git rather than of the disk.

    This walked the directory until round seven, which showed that any `.orig`,
    `.rej`, editor backup or intermediate output sitting in the run directory at
    stamping time was written straight into the provenance record -- the
    manifest would then pin a file the repository does not contain.  Asking git
    also makes the stamper and its coverage test agree on one definition of
    "what is in this run"; before, one walked the disk and the other walked the
    index.
    """
    repo = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=HERE,
                          capture_output=True, text=True, check=True).stdout.strip()
    rel_dir = os.path.relpath(HERE, repo).replace(os.sep, "/")
    listing = subprocess.run(["git", "ls-files", rel_dir], cwd=repo,
                             capture_output=True, text=True, check=True).stdout
    out = []
    for path in (p for p in listing.splitlines() if p.strip()):
        rel = path[len(rel_dir) + 1:]
        if rel in EXCLUDED_NAMES or rel.split("/")[0] in EXCLUDED_DIRS:
            continue
        out.append(rel)
    return sorted(out)


def stamp():
    out = []
    for p in artefacts():
        data = open(os.path.join(HERE, p), "rb").read()
        _assert_published_bytes(p, data)
        out.append({"path": p, "sha256": hashlib.sha256(data).hexdigest()})
    return out


def main():
    m = json.load(open(MANIFEST, encoding="utf-8"))
    checking = "--check" in sys.argv
    try:
        fresh = stamp()
    except WorkingCopyIsNotPublished as exc:
        if not checking:
            raise
        # Round seven: raising here aborted --check at the first offending file,
        # so one CRLF file suppressed the UNLISTED/ABSENT/STALE report for every
        # other path -- the audit this mode exists to produce.  And exit 1 was
        # the same code as "stale", so a caller could not tell a stale manifest
        # from a crashed checker.  Reported as a line, and exit 2.
        print("UNPUBLISHABLE  %s" % exc)
        print("MANIFEST NOT CHECKED (a working copy differs from what git "
              "publishes; normalise it and re-run)")
        return 2
    if checking:
        old = {e["path"]: e["sha256"] for e in m.get("files", [])}
        new = {e["path"]: e["sha256"] for e in fresh}
        bad = False
        for p in sorted(set(old) | set(new)):
            if p not in old:
                print("UNLISTED  %s" % p); bad = True
            elif p not in new:
                print("ABSENT    %s" % p); bad = True
            elif old[p] != new[p]:
                print("STALE     %s" % p); bad = True
        print("MANIFEST %s (%d entries)" % ("STALE" if bad else "matches", len(new)))
        return 1 if bad else 0
    m["files"] = fresh
    body = json.dumps(m, indent=1, sort_keys=True, ensure_ascii=False)
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body + "\n")
    print("re-stamped %d entries" % len(fresh))
    return 0


if __name__ == "__main__":
    sys.exit(main())
