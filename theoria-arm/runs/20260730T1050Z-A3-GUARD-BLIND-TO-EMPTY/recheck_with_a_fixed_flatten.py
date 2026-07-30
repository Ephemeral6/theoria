"""The migration guard was blind to whole subtrees. Re-run the check without
the blindness, against the bytes that were actually on disk before the write.

`migrate_cost_shape.py` disclosed one gap in itself (`0 == 0.0`). An
adversarial pass found a second one, and it is structurally worse:

    flatten({"a": {}})  ->  {}
    flatten({"a": []})  ->  {}

`flatten` recurses into containers and only assigns `out[prefix] = obj` at a
non-container. An **empty** container runs a `for` loop zero times and reaches
no `else`, so it contributes no leaf at all. `diff_leaves` compares leaf key
sets, so a key whose value is `{}` or `[]` is invisible to all three of
`added` / `removed` / `changed`. It can be deleted, invented, or flipped
between the two container types and the guard reports "nothing changed" --
including the invention of an entire top-level block.

This is not the disclosed gap. `0 == 0.0` is blindness to a value's
representation at a leaf the guard can at least see. This is blindness to the
existence of the key, and it falsifies the docstring's "nothing else, anywhere
in the manifest" outright.

It is live rather than hypothetical: every one of the seven migrated manifests
carries `cost.from_price_table.per_model = {}` -- inside the very block the
migration rewrote.

So the guard's *verdict* was worth less than it claimed. That does not by
itself say the *migration* was wrong, and the two must not be conflated: the
committed diff (21 added lines, zero removed, zero modified) is independent
evidence and it still stands. This script settles the question directly, by
re-running the comparison with the blindness removed, against `before` bytes
taken from git rather than from a rerun.

Two fixes to `flatten`, both of which close a class rather than a case:

* **empty containers emit a leaf**, tagged with which container they were, so
  `{}` and `[]` are distinguishable and neither is invisible;
* **paths are tuples, not dot-joined strings.** The original joined segments
  with `"."`, so `{"a.b": 1}` and `{"a": {"b": 1}}` collide. This corpus has
  265 dotted keys -- `upstream_pin` is keyed by file path -- so the ingredients
  for that collision are already present, even though it has not yet bitten.

Run from `theoria-arm/`:

    python runs/20260730T1050Z-A3-GUARD-BLIND-TO-EMPTY/recheck_with_a_fixed_flatten.py
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ARM)

sys.path.insert(0, os.path.join(ARM, "runs",
                                "20260730T0700Z-A3-COST-SHAPE-COUPLING"))

import migrate_cost_shape as mig                      # noqa: E402

#: The commit that wrote the seven cost-shape migrations. Its parent holds the
#: bytes that were on disk before, which is the only honest `before`: a rerun
#: of `build()` today would produce the *after* shape and compare it with
#: itself.
MIGRATION_COMMIT = "53e6ea0b"

#: The commit that rewrote `files[]` from a disk walk to the repository's own
#: exclude rules. Its sibling guard is checked here too.
FILES_COMMIT = "46612a9c"

EMPTY_DICT = ("<empty>", "dict")
EMPTY_LIST = ("<empty>", "list")


def flatten(obj, prefix=()):
    """Every leaf keyed by its path, with empty containers counted as leaves
    and paths kept as tuples so no separator can create a collision."""
    out = {}
    if isinstance(obj, dict):
        if not obj:
            out[prefix] = EMPTY_DICT
            return out
        for key, value in obj.items():
            out.update(flatten(value, prefix + (key,)))
    elif isinstance(obj, list):
        if not obj:
            out[prefix] = EMPTY_LIST
            return out
        for i, value in enumerate(obj):
            out.update(flatten(value, prefix + (i,)))
    else:
        out[prefix] = obj
    return out


def diff_leaves(before, after):
    a, b = flatten(before), flatten(after)
    added = {k: b[k] for k in sorted(set(b) - set(a), key=repr)}
    removed = {k: a[k] for k in sorted(set(a) - set(b), key=repr)}
    changed = {k: (a[k], b[k]) for k in sorted(set(a) & set(b), key=repr)
               if a[k] != b[k] or type(a[k]) is not type(b[k])}
    return added, removed, changed


def _show(commit, path):
    out = subprocess.run(["git", "show", "%s:%s" % (commit, path)],
                         cwd=REPO, capture_output=True)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout.decode("utf-8"))


def _key(path_tuple):
    return ".".join(str(p) for p in path_tuple) or "<root>"


def main():
    report = {"migration_commit": MIGRATION_COMMIT,
              "flatten": "fixed: empty containers are leaves, paths are tuples",
              "blindness_demo": {}, "runs": [], "files_guard": {}}

    # -- 1. the blindness itself, on the shipped guard -------------------
    base = {"a": {}, "keep": 1}
    for label, mutant in (("empty dict -> empty list", {"a": [], "keep": 1}),
                          ("key deleted outright", {"keep": 1}),
                          ("whole top-level key invented",
                           {"a": {}, "keep": 1, "INVENTED": {}})):
        shipped = mig.diff_leaves(base, mutant)
        fixed = diff_leaves(base, mutant)
        report["blindness_demo"][label] = {
            "shipped_guard_sees_nothing": shipped == ({}, {}, {}),
            "fixed_guard_sees_it": fixed != ({}, {}, {}),
        }

    # -- 2. the seven migrations, rechecked ------------------------------
    expected = {("cost", "from_price_table", k): v
                for k, v in mig.EXPECTED_ADDED.items()}
    for slug in mig.SLUGS:
        rel = "theoria-arm/runs/%s/MANIFEST.json" % slug
        before = _show(MIGRATION_COMMIT + "^", rel)
        after = _show(MIGRATION_COMMIT, rel)
        entry = {"slug": slug}
        if before is None or after is None:
            entry["error"] = "could not read both sides from git"
            report["runs"].append(entry)
            continue
        added, removed, changed = diff_leaves(before, after)
        entry.update({
            "added": {_key(k): v for k, v in added.items()},
            "removed": {_key(k): v for k, v in removed.items()},
            "changed": {_key(k): v for k, v in changed.items()},
            "diff_is_exactly_the_three_s29_keys":
                added == expected and not removed and not changed,
        })
        report["runs"].append(entry)

    # -- 3. the sibling guard's set-blindness ----------------------------
    # `migrate_files_in_clone.py` compares surviving `files[]` entries as
    # Python *sets* of serialised entries. A set is order-blind and
    # duplicate-blind, and nothing else in that script covers list order, so
    # "surviving entries are byte-identical" is true entry-wise and unproven
    # list-wise. Checked here as a list.
    rel = "theoria-arm/runs/20260729T004020Z-leg01/MANIFEST.json"
    fb, fa = _show(FILES_COMMIT + "^", rel), _show(FILES_COMMIT, rel)
    if fb is not None and fa is not None:
        before_files = [f["path"] for f in fb.get("files", [])]
        after_files = [f["path"] for f in fa.get("files", [])]
        survivors = [p for p in before_files if p in set(after_files)]
        report["files_guard"] = {
            "before_count": len(before_files),
            "after_count": len(after_files),
            "dropped": [p for p in before_files if p not in set(after_files)],
            "survivor_relative_order_preserved": survivors == after_files,
            "after_has_no_duplicates": len(after_files) == len(set(after_files)),
        }

    print(json.dumps(report, indent=2, sort_keys=True, default=str))

    clean = all(r.get("diff_is_exactly_the_three_s29_keys")
                for r in report["runs"])
    files_ok = (report["files_guard"].get("survivor_relative_order_preserved")
                and report["files_guard"].get("after_has_no_duplicates"))
    return 0 if (clean and files_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
