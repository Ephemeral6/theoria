"""Build the shippable set from the manifest, and account for what is held back.

    python release/bundle.py                # write BUNDLE.jsonl + FRAME_HASHES.jsonl
    python release/bundle.py --dry-run      # report, write nothing
    python release/bundle.py --check        # fail if the bundle is stale or unsound

`enumerate.py` classifies every tracked file and writes `MANIFEST.jsonl`. That
is a judgement, not a package: nothing yet turns the judgement into the set that
actually ships, and a classification nobody acts on is a classification that
will be quietly overridden by whoever tars the directory. This is the acting-on.

Three properties, and each exists because its absence is a way to publish
something we may not:

* **Allow-list, never deny-list.** A file enters the bundle only if its verdict
  is exactly `releasable`. A new artefact class nobody has classified yet is
  therefore *out* by default. A deny-list ships everything nobody thought about.
* **What is held back is listed, with its hash.** `Theoria.md:379` sets the
  release's ambition at "the full public set + artifacts", and on frame data
  that cannot be met (`TERMS.md` §2: no republishing "without our express prior
  written permission"). The honest form of an unmet target is a named gap, so
  every withheld file appears in `FRAME_HASHES.jsonl` with its sha256 and the
  command that regenerates it. A reader with their own ARC key can rebuild the
  bytes and check them against the hash; a reader without one can still verify
  that what we describe is what we had.
* **The bundle refuses to be stale.** `--check` recomputes it and compares. A
  bundle built once and then drifting from the manifest is worse than none: it
  carries the authority of having been checked.

Nothing here applies for permission. That is a human decision and it is written
into `LICENCE_POSTURE.md`'s `needs_human` section, not actioned.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANIFEST = os.path.join(HERE, "MANIFEST.jsonl")
BUNDLE = os.path.join(HERE, "BUNDLE.jsonl")
WITHHELD = os.path.join(HERE, "FRAME_HASHES.jsonl")

#: The verdicts that ship, named one at a time so widening this is a visible
#: decision rather than a quiet edit.
#:
#: `releasable-flagged` is class C, *derived statistics* -- a file that mentions
#: ARC identifiers without carrying environment payload. `LICENCE_POSTURE.md`
#: rules it releasable; the flag is an instruction to a human reader, not a
#: reservation about the licence. Withholding all 146 of them would hold back
#: `CLAUDE.md` and `PARTNER_SYNC.md`, which is not caution, it is a broken
#: filter -- and a filter that over-withholds gets widened in a hurry by
#: whoever is shipping, which is how the under-withholding accident happens.
#: They ship, and they ship carrying their flag.
#:
#: Everything else is held back: `needs-written-permission` (class B, the
#: api-derived compilations `TERMS.md` §2 covers), `not-releasable` (class D,
#: upstream payload with no licence at all), and `needs_human` (class ?, which
#: nobody has classified -- out by default, because an unclassified artefact is
#: exactly the one nobody has thought about).
SHIPS = frozenset({"releasable", "releasable-flagged"})

#: How a withheld artefact is regenerated, per territory. A hash with no
#: recipe is not reproducible, it is just a promise.
RECIPES = (
    ("baseline-arms/schema_traces/", "NOT REGENERABLE BY US -- upstream "
     "third-party material that declares no licence at all (SCHEMA_PATH_A.md "
     "§7). We cannot relicense it and cannot rebuild it; obtain it from its "
     "own source."),
    ("battery/tests/fixtures/", "cd battery && python tests/make_fixture.py  "
     "# offline: this file is written by a tracked generator, not retrieved. "
     "It is held at class B only because the file alone cannot prove that "
     "(see `why`), so regenerating it is also how the reclassification gets "
     "settled."),
    ("theoria-arm/runs/", "python -m armtools.backfill --all  # then replay the "
                          "ledger; frames re-fetch with your own ARC_API_KEY"),
    ("baseline-arms/", "cd baseline-arms && python -m arms.run --replay <shard>  "
                       "# needs your own ARC_API_KEY"),
    ("arc-recon/", "cd arc-recon && python probe.py --game <id>  # needs your own "
                   "ARC_API_KEY"),
    ("engine-rig/", "cd engine-rig && python -m fixtures.generate_all  # offline, "
                    "byte-stable, no key needed"),
    ("a0-spike/", "cd a0-spike && python -m spike.run  # offline"),
)


def recipe_for(rel: str) -> str:
    for prefix, how in RECIPES:
        if rel.startswith(prefix):
            return how
    return ("no regeneration recipe is registered for this path; see "
            "release/REPRODUCING.md")


def read_manifest() -> list[dict]:
    if not os.path.exists(MANIFEST):
        raise SystemExit("no MANIFEST.jsonl -- run release/enumerate.py first")
    with open(MANIFEST, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def sha256(rel: str) -> str | None:
    path = os.path.join(ROOT, rel)
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Ships / held back. Every row lands in exactly one, and none is dropped.

    The count is asserted rather than trusted: a partition that silently loses
    a row is how a file ends up in neither the bundle nor the withheld list,
    which is the one outcome no reader can detect.
    """
    ships, held = [], []
    for row in rows:
        (ships if row.get("verdict") in SHIPS else held).append(row)
    assert len(ships) + len(held) == len(rows), "the partition dropped a row"
    return ships, held


def build() -> tuple[list[dict], list[dict]]:
    rows = read_manifest()
    ships, held = split(rows)

    bundle = []
    for r in sorted(ships, key=lambda r: r["path"]):
        row = {"path": r["path"], "sha256": r.get("sha256"),
               "size": r.get("size"), "class": r.get("class"),
               "verdict": r.get("verdict")}
        if r.get("verdict") == "releasable-flagged" or r.get("review"):
            # The flag travels with the file. A flag that lives only in the
            # manifest is a flag the person assembling the tarball never sees.
            row["flagged_for_review"] = r.get("review") or (
                "class C, derived statistics: mentions ARC identifiers without "
                "carrying environment payload. Releasable per "
                "LICENCE_POSTURE.md; read once before shipping.")
        bundle.append(row)

    withheld = []
    for r in sorted(held, key=lambda r: r["path"]):
        withheld.append({
            "path": r["path"],
            "sha256": r.get("sha256") or sha256(r["path"]),
            "size": r.get("size"),
            "class": r.get("class"),
            "verdict": r.get("verdict"),
            "why": r.get("evidence"),
            "regenerate": recipe_for(r["path"]),
        })
    return bundle, withheld


def write(bundle: list[dict], withheld: list[dict]) -> None:
    for path, rows in ((BUNDLE, bundle), (WITHHELD, withheld)):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")


def check() -> int:
    """Would rebuilding change anything? Reports rather than writes."""
    bundle, withheld = build()
    problems = []
    for path, rows in ((BUNDLE, bundle), (WITHHELD, withheld)):
        want = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
        have = (open(path, encoding="utf-8").read()
                if os.path.exists(path) else None)
        if have is None:
            problems.append("%s does not exist" % os.path.basename(path))
        elif have != want:
            problems.append("%s is stale -- rerun release/bundle.py"
                            % os.path.basename(path))

    # The property that matters most, checked directly rather than inferred
    # from the filter having run: nothing needing permission is in the bundle.
    shipped = {r["path"] for r in bundle}
    for row in read_manifest():
        if row.get("verdict") not in SHIPS and row["path"] in shipped:
            problems.append("%s ships despite verdict %r"
                            % (row["path"], row.get("verdict")))

    for problem in problems:
        print("FAIL %s" % problem)
    if problems:
        return 1
    print("OK  bundle is current: %d ship, %d held back" % (len(bundle),
                                                            len(withheld)))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    if args.check:
        return check()

    bundle, withheld = build()
    by_verdict: dict[str, int] = {}
    for row in withheld:
        by_verdict[row["verdict"]] = by_verdict.get(row["verdict"], 0) + 1

    print("ships:      %d files" % len(bundle))
    print("held back:  %d files" % len(withheld))
    for verdict, n in sorted(by_verdict.items()):
        print("   %-28s %d" % (verdict, n))
    missing = [r["path"] for r in withheld if not r["sha256"]]
    if missing:
        print("WARNING: %d withheld files have no hash: %s"
              % (len(missing), missing[:3]))

    if args.dry_run:
        print("(dry run: nothing written)")
        return 0
    write(bundle, withheld)
    print("wrote %s and %s" % (os.path.relpath(BUNDLE, ROOT),
                               os.path.relpath(WITHHELD, ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
