"""The register of artefacts that cost money, and the check that they survive.

    cd baseline-arms && python -m harness.cost_artefacts        # human report
    cd baseline-arms && python -m harness.cost_artefacts --json # machine form

Why this exists
---------------
A14 (2026-07-29) found the four full-campaign artefacts -- `$48.39` of real ARC
spend across the four development-pile games -- sitting untracked in the working
tree while `battery/runs/20260728T061147Z-v3/MANIFEST.json` was already citing
their sha256 as evidence.  One machine failure or one `git clean` and the money
was gone, along with the only source for the baseline column of the main table.

The lesson is not "remember to commit things".  It is that *the repository had
no way to state which artefacts are irreplaceable*, so nothing could notice.
`COST_ARTEFACTS.json` is that statement, and this module is the part that makes
it fail loudly.

The rule it enforces
--------------------
**An artefact whose creation spent money or hours is either committed, or has
its sha256 and provenance recorded in `COST_ARTEFACTS.json`.  Never neither.**

Two dispositions, and the difference is what the register promises:

* ``committed``  -- the payload is in git.  The file must exist, must be tracked,
  and its bytes must hash to the recorded digest.  Any of the three failing is
  RED: a tracked artefact that no longer matches its digest has been altered
  after being consumed as evidence, which is worse than never having stored it.
* ``hash-only``  -- the payload is deliberately not in git (too large, or a
  licence forbids republication).  The digest and provenance are the record.
  The file *may* be absent -- that is the accepted cost of the disposition, and
  is reported as ``absent`` rather than RED.  But if it is present, it must
  still match: a hash-only artefact that drifted is the same evidence break.

Line endings are part of the payload
------------------------------------
The four campaign JSONs were written by the harness in Python text mode on
Windows, so their bytes are CRLF, and the digest battery pinned was taken over
those CRLF bytes.  `baseline-arms/.gitattributes` sets `* text eol=lf`, so a
plain `git add` would have normalised them and every clone would have held a
file whose digest no longer matched the one already cited -- a silent break, no
error anywhere.  A14 added an `out/campaign/*.json -text diff` rule to switch
the translation off for those paths.  This module hashes **raw bytes** and never
normalises, so if that rule is ever removed this check goes red instead of the
evidence quietly rotting.

No credentials, no network, no spend
------------------------------------
Reads files and asks git which paths are tracked.  Nothing here opens a socket
or looks at `ARC_API_KEY`.
"""

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TERRITORY = os.path.dirname(HERE)
REGISTER = os.path.join(TERRITORY, "COST_ARTEFACTS.json")

SCHEMA = "baseline-arms/cost-artefacts@1"
DISPOSITIONS = ("committed", "hash-only")

# Verdicts.  `absent` is a pass only for hash-only entries; the caller decides,
# not this constant.  Everything else in this list is a failure, including
# `unverified` -- see `_head_blobs`.
OK = "ok"
ABSENT = "absent"
MISSING = "missing"
UNTRACKED = "untracked"
DRIFTED = "drifted"
HEAD_DRIFT = "head-drift"
UNVERIFIED = "unverified"


def _read_register(path=REGISTER):
    with open(path, encoding="utf-8") as fh:
        reg = json.load(fh)
    if reg.get("schema") != SCHEMA:
        raise ValueError("%s: schema is %r, expected %r"
                         % (path, reg.get("schema"), SCHEMA))
    entries = reg.get("artefacts")
    if not isinstance(entries, list) or not entries:
        raise ValueError("%s: 'artefacts' must be a non-empty list" % path)
    return reg


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:          # rb: the bytes are the evidence
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _head_blobs(territory=TERRITORY):
    """`{path: sha256 of the blob in HEAD}` for everything under the territory.

    **`HEAD`, deliberately, and not `git ls-files`.** `ls-files` reports the
    *index*, so a path that was `git add`ed and never committed reads back as
    tracked -- and this repository's convention is `git commit <paths>` rather
    than `commit -a` (CLAUDE.md: "Never `git add -A` at the repo root"), which
    is exactly the operation that leaves staged paths out of the commit. An
    index-only check would have called such an artefact safe while a fresh
    clone had no copy of it at all: the A14 failure one notch subtler, and
    green. An adversarial review of this module found precisely that hole.

    Hashing the blob **content** rather than just checking membership is what
    makes the eol rule verifiable. If the `out/campaign/*.json -text` rule in
    `.gitattributes` is ever dropped and the files re-added, git normalises
    CRLF to LF on the way into the object store; the working tree can still
    look right while every clone gets different bytes. Comparing the HEAD blob
    to the pinned digest catches that for all twelve committed artefacts,
    rather than for the four a single test happens to cover.

    Returns None if git cannot answer. An unavailable git is not the same fact
    as an untracked file and callers must not conflate them -- see UNVERIFIED.
    """
    try:
        listing = subprocess.run(
            ["git", "ls-tree", "-r", "-z", "HEAD", "--", "."],
            cwd=territory, capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None

    oids, paths = [], []
    for record in listing.split(b"\0"):
        if not record:
            continue
        meta, _, path = record.partition(b"\t")
        fields = meta.split()
        if len(fields) < 3 or fields[1] != b"blob":
            continue                      # submodule or tree; not our business
        oids.append(fields[2])
        paths.append(path.decode("utf-8").replace(os.sep, "/"))
    if not oids:
        return {}

    try:
        proc = subprocess.run(
            ["git", "cat-file", "--batch"], cwd=territory,
            input=b"\n".join(oids) + b"\n", capture_output=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    # `--batch` emits "<oid> <type> <size>\n<contents>\n" per request, so the
    # payload must be cut by the declared size -- contents are binary and may
    # contain newlines.
    blobs, buf = {}, proc.stdout
    at = 0
    for path in paths:
        end_of_header = buf.find(b"\n", at)
        if end_of_header < 0:
            return None
        header = buf[at:end_of_header].split()
        if len(header) < 3:
            return None
        size = int(header[2])
        start = end_of_header + 1
        blobs[path] = hashlib.sha256(buf[start:start + size]).hexdigest()
        at = start + size + 1             # skip the trailing newline
    return blobs


def check(register_path=REGISTER, territory=TERRITORY):
    """Adjudicate every register entry.  Returns (rows, problems)."""
    reg = _read_register(register_path)
    head = _head_blobs(territory)
    rows, problems = [], []

    if head is None:
        problems.append("git could not read HEAD, so 'committed' entries "
                        "cannot be checked; they are reported 'unverified', "
                        "never 'ok'")

    seen = set()
    for entry in reg["artefacts"]:
        path = entry["path"]
        if path in seen:
            problems.append("%s: listed twice in the register" % path)
        seen.add(path)

        disposition = entry["disposition"]
        if disposition not in DISPOSITIONS:
            problems.append("%s: disposition %r is not one of %s"
                            % (path, disposition, list(DISPOSITIONS)))
            continue

        pinned = entry.get("sha256", "")
        if len(pinned) != 64 or any(c not in "0123456789abcdef" for c in pinned):
            problems.append("%s: sha256 %r is not 64 lowercase hex digits"
                            % (path, pinned))
            continue

        full = os.path.join(territory, path.replace("/", os.sep))
        exists = os.path.isfile(full)
        actual = _sha256(full) if exists else None

        in_head = None if head is None else head.get(path)

        if not exists:
            verdict = MISSING if disposition == "committed" else ABSENT
        elif actual != pinned:
            verdict = DRIFTED
        elif disposition != "committed":
            verdict = OK
        elif head is None:
            # Unknown is not yes.  Never OK on a machine where the question
            # could not be asked.
            verdict = UNVERIFIED
        elif in_head is None:
            verdict = UNTRACKED
        elif in_head != pinned:
            verdict = HEAD_DRIFT
        else:
            verdict = OK

        rows.append({
            "path": path,
            "disposition": disposition,
            "verdict": verdict,
            "sha256": pinned,
            "actual_sha256": actual,
            "head_sha256": in_head,
            "bytes": os.path.getsize(full) if exists else None,
        })

        if verdict == DRIFTED:
            problems.append(
                "%s: bytes on disk hash to %s but the register pins %s -- the "
                "artefact was altered after it was recorded as evidence"
                % (path, actual[:12], pinned[:12]))
        elif verdict == MISSING:
            problems.append(
                "%s: disposition 'committed' but the file is not on disk"
                % path)
        elif verdict == UNTRACKED:
            problems.append(
                "%s: disposition 'committed' but it is not in HEAD -- a clone "
                "would not have it at all. Staging is not committing, and this "
                "is exactly the A14 failure the register exists to catch"
                % path)
        elif verdict == HEAD_DRIFT:
            problems.append(
                "%s: the working tree matches the register but the blob in "
                "HEAD hashes to %s -- a clone would get different bytes. The "
                "usual cause is eol translation: check that .gitattributes "
                "still exempts this path from `text eol=lf`"
                % (path, in_head[:12]))
        elif verdict == UNVERIFIED:
            problems.append(
                "%s: disposition 'committed' but HEAD could not be read, so "
                "its presence in the repository is unknown" % path)

    return rows, problems


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    rows, problems = check()

    if "--json" in argv:
        json.dump({"rows": rows, "problems": problems}, sys.stdout,
                  indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 1 if problems else 0

    for row in rows:
        size = "-" if row["bytes"] is None else "%.1f MB" % (row["bytes"] / 1e6)
        print("  %-8s %-10s %10s  %s"
              % (row["verdict"], row["disposition"], size, row["path"]))
    print()
    if problems:
        for p in problems:
            print("  RED  %s" % p)
        print("\ncost artefacts: RED (%d problem(s))" % len(problems))
        return 1
    committed = sum(1 for r in rows if r["disposition"] == "committed")
    hash_only = len(rows) - committed
    print("cost artefacts: green -- %d committed and byte-identical, %d "
          "hash-only" % (committed, hash_only))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
