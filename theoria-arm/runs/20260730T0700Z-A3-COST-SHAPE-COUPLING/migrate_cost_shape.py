"""Re-derive the archived manifests whose cost block predates S29 -- and prove
that nothing else in them moved.

This script rewrites files under `runs/`. That is the operation this area of the
repo is most suspicious of, and rightly: `verify_provenance`'s own check-2 text
suggests `python -m armtools.backfill --all`, and running that to make a red
gate green is *rewriting archived provenance to satisfy the check that polices
it*. So this is not that, and the difference is mechanical rather than a promise:

* it names its seven slugs explicitly -- there is no `--all` here;
* it refuses to write unless the change is **exactly** the addition of the three
  keys named in `EXPECTED_ADDED`, at a neutral value, under
  `cost.from_price_table`, and nothing else, anywhere in the manifest;
* it hashes every `ledger.jsonl` before and after and refuses if one moved. The
  ledger is the primary record; the cost block is a *view* re-derived from it.
  Re-deriving a view is not editing a record. Editing the record would be, and
  this is how you can tell the two apart afterwards;
* `--check` is the default. Writing requires `--write`.

Run from `theoria-arm/`:

    python runs/20260730T0700Z-A3-COST-SHAPE-COUPLING/migrate_cost_shape.py
    python runs/20260730T0700Z-A3-COST-SHAPE-COUPLING/migrate_cost_shape.py --write
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

#: The three keys `71b882c8` added to `proxy.cost.price_run()`'s return, with
#: the only values they may take here. A non-neutral value would mean the
#: re-derivation had discovered a real unmeasured call in an archived run --
#: which would be a finding to report, not a migration to wave through.
EXPECTED_ADDED = {
    "missing_usage_keys": None,
    "unmeasured_calls": 0,
    "unpriced_usage_keys": None,
}

#: Named, not discovered. Every archived manifest whose `provenance.mode` is
#: `backfill` and whose cost block was written before S29. The five `amend`
#: manifests are deliberately absent: `amend_payload` leaves the original
#: manifest exactly as written and never recomputes cost, so their blocks are
#: not stale, they are historical.
SLUGS = (
    "20260728T012311Z-g50t-first-contact-salvage",
    "20260728T012311Z-g50t-first-contact-salvage2",
    "20260728T014402Z-g50t-first-contact-salvage",
    "20260728T015354Z-g50t-first-contact-salvage",
    "20260729T004020Z-leg01",
    "20260729T004020Z-leg01-salvage",
    "preflight-20260728T012031Z",
)


def sha256(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def flatten(obj, prefix=""):
    """Every leaf in a nested structure, keyed by its path. Comparing these
    catches a change anywhere in the manifest, not just where we expect one."""
    out = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            out.update(flatten(value, "%s.%s" % (prefix, key) if prefix else key))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            out.update(flatten(value, "%s[%d]" % (prefix, i)))
    else:
        out[prefix] = obj
    return out


def diff_leaves(before, after):
    a, b = flatten(before), flatten(after)
    added = {k: b[k] for k in sorted(set(b) - set(a))}
    removed = {k: a[k] for k in sorted(set(a) - set(b))}
    changed = {k: (a[k], b[k]) for k in sorted(set(a) & set(b)) if a[k] != b[k]}
    return added, removed, changed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true",
                    help="actually write. Without it, nothing is written.")
    args = ap.parse_args(argv)

    runs_root = os.path.join(ARM, "runs")
    table = armversion.scan()
    report = {"wrote": bool(args.write), "runs": []}
    refused = []

    for slug in SLUGS:
        manifest_path = os.path.join(runs_root, slug, "MANIFEST.json")
        ledger_path = os.path.join(runs_root, slug, "ledger.jsonl")

        with open(manifest_path, "rb") as fh:
            before_bytes = fh.read()
        before = json.loads(before_bytes.decode("utf-8"))
        ledger_before = sha256(ledger_path)

        payload = backfill.build(slug, runs_root=runs_root, table=table)
        after_bytes = backfill.render(payload)
        after = json.loads(after_bytes.decode("utf-8"))

        added, removed, changed = diff_leaves(before, after)
        expected = {"cost.from_price_table.%s" % k: v
                    for k, v in EXPECTED_ADDED.items()}

        ok = (added == expected and not removed and not changed)
        row = {
            "slug": slug,
            "manifest_sha256_before": hashlib.sha256(before_bytes).hexdigest(),
            "manifest_sha256_after": hashlib.sha256(after_bytes).hexdigest(),
            "ledger_sha256_before": ledger_before,
            "leaves_added": added,
            "leaves_removed": removed,
            "leaves_changed": changed,
            "diff_is_exactly_the_three_s29_keys": ok,
        }

        if not ok:
            refused.append(slug)
        elif args.write:
            with open(manifest_path, "wb") as fh:
                fh.write(after_bytes)
            row["ledger_sha256_after"] = sha256(ledger_path)
            row["ledger_unchanged"] = row["ledger_sha256_after"] == ledger_before
            with open(manifest_path, "rb") as fh:
                row["manifest_sha256_on_disk_after_write"] = \
                    hashlib.sha256(fh.read()).hexdigest()

        report["runs"].append(row)

    report["refused"] = refused
    print(json.dumps(report, indent=1, sort_keys=True))

    if refused:
        print("\nREFUSED: %d manifest(s) would have changed something other "
              "than the three S29 keys. Nothing was written for them.\n"
              "This is the whole guard: a migration that cannot state exactly "
              "what it changes is indistinguishable from an edit."
              % len(refused), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
