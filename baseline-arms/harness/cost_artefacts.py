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
# not this constant.
OK = "ok"
ABSENT = "absent"
MISSING = "missing"
UNTRACKED = "untracked"
DRIFTED = "drifted"


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


def _tracked_paths(territory=TERRITORY):
    """Paths git tracks under the territory, territory-relative with / separators.

    Returns None if git cannot answer -- an unavailable git is not the same
    fact as an untracked file, and the caller must not confuse them.
    """
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--", "."],
            cwd=territory, capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return {p.replace(os.sep, "/") for p in out.decode("utf-8").split("\0") if p}


def check(register_path=REGISTER, territory=TERRITORY):
    """Adjudicate every register entry.  Returns (rows, problems)."""
    reg = _read_register(register_path)
    tracked = _tracked_paths(territory)
    rows, problems = [], []

    if tracked is None:
        problems.append("git ls-files failed, so 'committed' entries cannot be "
                        "checked for tracking; refusing to report them as ok")

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

        if not exists:
            verdict = MISSING if disposition == "committed" else ABSENT
        elif actual != pinned:
            verdict = DRIFTED
        elif disposition == "committed" and tracked is not None and path not in tracked:
            verdict = UNTRACKED
        else:
            verdict = OK

        rows.append({
            "path": path,
            "disposition": disposition,
            "verdict": verdict,
            "sha256": pinned,
            "actual_sha256": actual,
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
                "%s: disposition 'committed' but git does not track it -- this "
                "is exactly the A14 failure the register exists to catch"
                % path)

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
