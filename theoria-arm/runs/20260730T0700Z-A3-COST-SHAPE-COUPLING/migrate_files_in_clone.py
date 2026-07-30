"""Drop the artefacts the repository does not ship from a backfilled manifest's
`files[]` -- and prove that is all that happened.

Second pass, separate from `migrate_cost_shape.py` on purpose: it is a different
claim and deserves its own guard. `backfill._files_the_clone_carries` now drives
the traversal from the repository's ignore rules instead of from whatever
happens to be on the disk, so a re-derivation gives the same answer on every
machine. `20260729T004020Z-leg01`'s manifest was written on the machine that
still had the two excluded artefacts, so it lists them and must be brought into
line -- otherwise check 8 stays green here and stays red in every clone, which
is the defect, not the fix.

Only `provenance.mode == "backfill"` manifests are eligible. An `amend` manifest
is the one `archive.py` wrote at the end of its own run, kept verbatim by
contract (`amend_payload`: "left exactly as it was"), and `amend_payload` never
recomputes `files[]` -- so those four are not stale records, they are historical
ones, and editing them to satisfy a check would be exactly the move this whole
area is suspicious of. `verify_provenance`'s new "every file a manifest lists is
either in the clone or excluded by the repository's own rules" check is what
covers them, without rewriting a byte.

The guard: refuse unless every leaf outside `files` is identical, and the only
difference inside `files` is the removal of entries whose paths `git
check-ignore` independently confirms are excluded. Ledgers hashed before and
after.

Run from `theoria-arm/`:

    python runs/20260730T0700Z-A3-COST-SHAPE-COUPLING/migrate_files_in_clone.py
    python runs/20260730T0700Z-A3-COST-SHAPE-COUPLING/migrate_files_in_clone.py --write
"""

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from armtools import armversion, backfill              # noqa: E402

SLUGS = ("20260729T004020Z-leg01",)


def sha256_of(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def entry_path(entry):
    return entry.get("path") if isinstance(entry, dict) else entry


def without_files(manifest):
    return {k: v for k, v in manifest.items() if k != "files"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    runs_root = os.path.join(ARM, "runs")
    table = armversion.scan()
    report = {"wrote": bool(args.write), "runs": []}
    refused = []

    for slug in SLUGS:
        run_dir = os.path.join(runs_root, slug)
        manifest_path = os.path.join(run_dir, "MANIFEST.json")
        ledger_path = os.path.join(run_dir, "ledger.jsonl")

        with open(manifest_path, "rb") as fh:
            before_bytes = fh.read()
        before = json.loads(before_bytes.decode("utf-8"))
        ledger_before = sha256_of(ledger_path)

        payload = backfill.build(slug, runs_root=runs_root, table=table)
        after_bytes = backfill.render(payload)
        after = json.loads(after_bytes.decode("utf-8"))

        before_files = [entry_path(e) for e in before.get("files") or []]
        after_files = [entry_path(e) for e in after.get("files") or []]
        dropped = [p for p in before_files if p not in set(after_files)]
        gained = [p for p in after_files if p not in set(before_files)]

        # Independent confirmation, from git rather than from the code that did
        # the dropping: every path removed must be one the repository excludes.
        confirmed_ignored = backfill._ignored_paths(run_dir, dropped)

        # The surviving entries must be untouched, hashes included -- a dropped
        # entry is a different thing from a rewritten one.
        kept_before = {json.dumps(e, sort_keys=True)
                       for e in (before.get("files") or [])
                       if entry_path(e) not in set(dropped)}
        kept_after = {json.dumps(e, sort_keys=True)
                      for e in (after.get("files") or [])}

        ok = (without_files(before) == without_files(after)
              and dropped
              and not gained
              and set(dropped) == confirmed_ignored
              and kept_before == kept_after)

        row = {
            "slug": slug,
            "manifest_sha256_before": hashlib.sha256(before_bytes).hexdigest(),
            "manifest_sha256_after": hashlib.sha256(after_bytes).hexdigest(),
            "ledger_sha256_before": ledger_before,
            "paths_dropped": dropped,
            "paths_gained": gained,
            "dropped_confirmed_ignored_by_git": sorted(confirmed_ignored),
            "everything_outside_files_identical":
                without_files(before) == without_files(after),
            "surviving_entries_untouched": kept_before == kept_after,
            "safe": ok,
        }

        if not ok:
            refused.append(slug)
        elif args.write:
            with open(manifest_path, "wb") as fh:
                fh.write(after_bytes)
            row["ledger_sha256_after"] = sha256_of(ledger_path)
            row["ledger_unchanged"] = row["ledger_sha256_after"] == ledger_before

        report["runs"].append(row)

    report["refused"] = refused
    print(json.dumps(report, indent=1, sort_keys=True))

    if refused:
        print("\nREFUSED: %r. Something other than the removal of "
              "repository-excluded artefacts would have changed."
              % refused, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
