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
  * helper scripts named below, which are tools for reading the manifest rather
    than artefacts of the run

Usage:  python restamp_manifest.py [--check]
  (no args)  rewrite MANIFEST.json
  --check    exit 1 if the manifest does not match the directory, print the diff
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "MANIFEST.json")

EXCLUDED_NAMES = {
    "MANIFEST.json",
    "BASELINE-cycle94.md",
    "restamp_manifest.py",
    "_manifest_check.py",
    "_survey_manifests.py",
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
    what the manifest's own `note` says they are.  Nothing could see it: `git
    diff` is empty for these files, because check-in normalisation makes them
    equal again on the way into the index.

    Hashing the disk bytes is only correct while the two coincide, so the
    coincidence is asserted rather than assumed."""
    if b"\r\n" in data:
        raise WorkingCopyIsNotPublished(
            "%s has CRLF in the working copy; exam/.gitattributes pins LF, so "
            "git will publish different bytes than these and the stamp would be "
            "wrong at the commit that carries it. Normalise the file first." % rel)


def artefacts():
    out = []
    for root, dirs, files in os.walk(HERE):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for fn in sorted(files):
            rel = os.path.relpath(os.path.join(root, fn), HERE).replace(os.sep, "/")
            if rel in EXCLUDED_NAMES or os.path.basename(rel) in EXCLUDED_DIRS:
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
    fresh = stamp()
    if "--check" in sys.argv:
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
