"""Measure the scope of verify_provenance check 10 -- what it sees and what it misses.

Read-only. Calls the real `armtools.backfill.survey` and the real
`armtools.backfill._ignored_paths`; reimplements nothing.

    cd theoria-arm && python runs/20260730T1400Z-A3-H3-SCOPE/measure_scope.py

Writes `scope.json` next to itself and prints a summary.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                      # noqa: E402,F401
from armtools import backfill                           # noqa: E402

REPO = _bootstrap.REPO
RUNS_ROOT = _bootstrap.path("runs")
SELF_SLUG = os.path.basename(HERE)

#: Read out of the live source rather than pasted, so the quote cannot rot.
#: `classify` is the whole predicate; `survey` is what copies it onto a row.
def _quote_predicate():
    import inspect
    src = inspect.getsource(backfill.classify)
    keep = [ln for ln in src.splitlines()
            if "archive_material" in ln or ln.strip().startswith(("return {", "if ", "for ", "def "))]
    return {"classify_full_source": src,
            "archive_material_branches": keep,
            "survey_row_assignment": [
                ln for ln in inspect.getsource(backfill.survey).splitlines()
                if "archive_material" in ln]}


def tracked_set(repo):
    """Every tracked path in the repo, repo-root-relative, forward slashes."""
    proc = subprocess.run(["git", "ls-files", "-z"], cwd=repo,
                          capture_output=True, check=True)
    return {p.replace(os.sep, "/")
            for p in proc.stdout.decode("utf-8", "replace").split("\0") if p}


def rel_to_repo(abs_path):
    try:
        return os.path.relpath(abs_path, REPO).replace(os.sep, "/")
    except ValueError:                       # different drive
        return None


def main():
    global ARCHIVE_MATERIAL_QUOTE
    ARCHIVE_MATERIAL_QUOTE = _quote_predicate()
    tracked = tracked_set(REPO)

    # Is the tree we are measuring the tree that is committed?  Recorded, not
    # assumed: another session edited armtools mid-measurement once already.
    dirty = sorted(
        ln for ln in subprocess.run(
            ["git", "status", "--porcelain", "--", "theoria-arm"], cwd=REPO,
            capture_output=True, check=False).stdout.decode(
                "utf-8", "replace").splitlines() if ln.strip())
    deleted_lines = len([
        ln for ln in subprocess.run(
            ["git", "diff", "--", "theoria-arm/armtools/backfill.py"], cwd=REPO,
            capture_output=True, check=False).stdout.decode(
                "utf-8", "replace").splitlines()
        if ln.startswith("-") and not ln.startswith("--")])

    survey = backfill.survey(RUNS_ROOT)
    real_repo = os.path.realpath(REPO)

    rows = []
    per_run = {}
    shadow_rows = []          # the same measurement over rows check 10 skips
    shadow_per_run = {}

    for srow in survey:
        in_scope = srow["archive_material"]
        slug = srow["slug"]
        run_dir = os.path.join(RUNS_ROOT, slug)
        mpath = os.path.join(run_dir, "MANIFEST.json")
        sink = rows if in_scope else shadow_rows
        sink_per_run = per_run if in_scope else shadow_per_run
        if not os.path.exists(mpath):
            sink_per_run[slug] = {"listed": 0, "no_manifest": True,
                                  "kind": srow["kind"]}
            continue
        with open(mpath, encoding="utf-8") as fh:
            manifest = json.load(fh)
        listed = [(e.get("path") if isinstance(e, dict) else e)
                  for e in (manifest.get("files") or [])]
        listed = [p for p in listed if p]

        # One batched check-ignore per run, through the real function.
        ignored = backfill._ignored_paths(run_dir, listed)

        real_run = os.path.realpath(run_dir)
        conv_counts = {"run_dir": 0, "repo_root": 0, "both": 0, "neither": 0}

        for p in listed:
            joined = os.path.join(run_dir, p)
            present = os.path.exists(joined)
            is_dir = os.path.isdir(joined)
            rp = os.path.realpath(joined)
            escapes = not (rp == real_run or rp.startswith(real_run + os.sep))
            absolute = os.path.isabs(p)

            rel_run = rel_to_repo(joined)
            is_tracked = bool(rel_run and rel_run in tracked)

            # convention: is the string meaningful against run_dir, or against
            # the repo root?  "meaningful" == resolves to something the repo
            # knows about: it exists on disk, or it is tracked in git.
            pn = p.replace(os.sep, "/").lstrip("./")
            repo_joined = os.path.join(REPO, p)
            repo_hit = os.path.exists(repo_joined) or pn in tracked
            run_hit = present or is_tracked
            if run_hit and repo_hit:
                conv = "both"
            elif run_hit:
                conv = "run_dir"
            elif repo_hit:
                conv = "repo_root"
            else:
                conv = "neither"
            conv_counts[conv] += 1

            sink.append({
                "slug": slug,
                "archive_material": in_scope,
                "kind": srow["kind"],
                "path": p,
                "repo_rel_if_run_relative": rel_run,
                "present": present,
                "tracked": is_tracked,
                "ignored": p in ignored,
                "is_dir": is_dir,
                "escapes": escapes,
                "absolute": absolute,
                "convention": conv,
            })

        sink_per_run[slug] = {
            "listed": len(listed),
            "kind": srow["kind"],
            "convention": conv_counts,
            "present": sum(1 for r in sink if r["slug"] == slug and r["present"]),
            "tracked": sum(1 for r in sink if r["slug"] == slug and r["tracked"]),
            "ignored": sum(1 for r in sink if r["slug"] == slug and r["ignored"]),
        }

    def sel(**kw):
        return [r for r in rows
                if all(r[k] == v for k, v in kw.items())]

    def shadow_sel(**kw):
        return [r for r in shadow_rows
                if all(r[k] == v for k, v in kw.items())]

    def name(r):
        return "%s/%s" % (r["slug"], r["path"])

    a = sel(present=True, tracked=False, ignored=False)
    b = sel(present=False)
    b_excused = [r for r in b if r["ignored"]]
    b_dangling = [r for r in b if not r["ignored"]]
    c = sel(present=True, tracked=False, ignored=True)
    d = sel(tracked=True)

    dirs = sel(is_dir=True)
    esc = sel(escapes=True)
    absol = sel(absolute=True)

    # G: predicate becomes "tracked OR ignored".  Newly dangling == listed
    # paths that pass today (present, or absent-but-ignored) but would fail:
    # not tracked and not ignored.
    passes_today = [r for r in rows if r["present"] or r["ignored"]]
    passes_after = [r for r in rows if r["tracked"] or r["ignored"]]
    newly = [r for r in passes_today if not (r["tracked"] or r["ignored"])]

    out = {
        "archive_material_predicate": {
            "where": "armtools/backfill.py::classify() -> dict, called by "
                     "armtools/backfill.py::survey(); survey() copies "
                     "kind['archive_material'] onto the row",
            "quoted_source_lines": ARCHIVE_MATERIAL_QUOTE,
            "in_words": ("there is no boolean expression -- `archive_material` "
                         "is a per-branch literal in `classify()`. False for "
                         "four kinds: `fixture` (slug matches FIXTURE_GLOBS), "
                         "`process_record` (no ledger records but a "
                         "MANIFEST.json), `empty` (no ledger records and no "
                         "manifest), `mock` (every run_start names a loopback "
                         "env_upstream). True for the remaining four: "
                         "`salvage`, `preflight`, `aborted_experiment`, "
                         "`experiment`. Equivalently: a run is archive "
                         "material iff its ledger has records AND those "
                         "records reached a non-loopback upstream AND the slug "
                         "is not a fixture glob."),
            "fixture_globs": list(getattr(backfill, "FIXTURE_GLOBS", ())),
        },
        "measurement_integrity": {
            "note": ("While this measurement was being taken (2026-07-30 "
                     "20:50-20:52 local) a concurrent session modified "
                     "theoria-arm/armtools/backfill.py, "
                     "theoria-arm/armtools/verify_provenance.py and "
                     "theoria-arm/tests/test_files_in_clone.py in the working "
                     "tree -- it appears to have implemented the very fix "
                     "question G asks about (check 10's predicate becomes "
                     "`paths_the_clone_ships` = `git ls-files` on the index, "
                     "OR an ignore rule, plus a `path_is_inside_the_run` shape "
                     "test and a third `unanswerable` verdict). This does NOT "
                     "invalidate the numbers here: `git diff` on backfill.py is "
                     "a single pure-addition hunk with zero deleted lines, so "
                     "`survey`, `classify` and `_ignored_paths` -- the only "
                     "backfill functions this script calls -- are byte-"
                     "identical to HEAD. The numbers therefore describe both "
                     "the committed code and the working tree."),
            "worktree_dirty_paths": dirty,
            "backfill_diff_deleted_lines": deleted_lines,
            "survey_row_count_is_a_moving_target": (
                "`runs/` gained two untracked directories during this session "
                "-- this scratch run and the concurrent session's "
                "20260730T1255Z-A3-H3-THE-CHECK-WAS-MACHINE-DEPENDENT. Both "
                "classify as not-archive-material (`empty` / "
                "`process_record`), so `rows_total` moved from 42 to 44 while "
                "`archive_material` stayed at 12 throughout. Every A-G count "
                "is over the 12 and is unaffected."),
            "check_10_observed_verdict": (
                "`python -m armtools.verify_provenance` run at 20:49-20:55 "
                "local reported all ten checks PASS, check 10 with the "
                "post-fix detail string. Consistent with A=0 and G=0: the "
                "check was green before the fix and is green after it."),
        },
        "meta": {
            "repo": REPO.replace(os.sep, "/"),
            "runs_root": RUNS_ROOT.replace(os.sep, "/"),
            "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                   capture_output=True,
                                   check=False).stdout.decode().strip(),
            "tracked_files_in_repo": len(tracked),
        },
        "survey": {
            "rows_total": len(survey),
            "rows_total_excluding_this_scratch_run": len(
                [r for r in survey if r["slug"] != SELF_SLUG]),
            "caveat": ("this measurement's own scratch directory %r is under "
                       "runs/ and so appears as a survey row (kind `empty`, "
                       "archive_material false). It does not affect any A-G "
                       "count." % SELF_SLUG),
            "archive_material": sum(1 for r in survey if r["archive_material"]),
            "not_archive_material": sum(1 for r in survey
                                        if not r["archive_material"]),
            "by_kind": {k: sum(1 for r in survey if r["kind"] == k)
                        for k in sorted({r["kind"] for r in survey})},
            "archive_material_slugs": sorted(r["slug"] for r in survey
                                             if r["archive_material"]),
            "excluded": [{"slug": r["slug"], "kind": r["kind"]}
                         for r in survey if not r["archive_material"]],
        },
        "totals": {
            "listed_paths": len(rows),
            "runs_with_files": sum(1 for v in per_run.values() if v["listed"]),
            "present": len(sel(present=True)),
            "tracked": len(d),
            "ignored": len([r for r in rows if r["ignored"]]),
        },
        "A_present_untracked_unignored": {
            "count": len(a), "paths": sorted(name(r) for r in a)},
        "B_absent": {
            "count": len(b),
            "excused_by_ignore": len(b_excused),
            "unexplained_dangling_today": len(b_dangling),
            "paths": sorted("%s  [ignored=%s]" % (name(r), r["ignored"])
                            for r in b)},
        "C_ignored_but_present": {
            "count": len(c), "paths": sorted(name(r) for r in c)},
        "D_tracked": {"count": len(d)},
        "E_shapes": {
            "directories": {"count": len(dirs),
                            "paths": sorted(name(r) for r in dirs)},
            "escapes_run_dir": {"count": len(esc),
                                "paths": sorted(name(r) for r in esc)},
            "absolute": {"count": len(absol),
                         "paths": sorted(name(r) for r in absol)},
        },
        "F_convention_per_run": per_run,
        "F_convention_totals": {
            k: sum(1 for r in rows if r["convention"] == k)
            for k in ("run_dir", "repo_root", "both", "neither")},
        "F_runs_listing_repo_root_relative": {
            slug: v["convention"]["repo_root"]
            for slug, v in sorted(per_run.items())
            if v.get("convention", {}).get("repo_root")},
        "G_newly_dangling_if_predicate_is_tracked_or_ignored": {
            "count": len(newly),
            "equals_A": sorted(name(r) for r in newly) ==
                        sorted(name(r) for r in a),
            "paths": sorted(name(r) for r in newly),
            "passes_today": len(passes_today),
            "passes_after": len(passes_after),
        },
        # H -- the same measurement over the survey rows check 10 *skips*
        #      (`archive_material` false).  Not part of A-G; recorded because
        #      the E14 repo-root-relative case lives entirely in here, i.e.
        #      outside check 10's scope, so no change to check 10's predicate
        #      can ever see it.
        "H_out_of_scope_manifests": {
            "runs_with_files": sum(1 for v in shadow_per_run.values()
                                   if v["listed"]),
            "listed_paths": len(shadow_rows),
            "present": len(shadow_sel(present=True)),
            "tracked": len(shadow_sel(tracked=True)),
            "ignored": len([r for r in shadow_rows if r["ignored"]]),
            "present_untracked_unignored": {
                "count": len(shadow_sel(present=True, tracked=False,
                                        ignored=False)),
                "paths": sorted(name(r) for r in
                                shadow_sel(present=True, tracked=False,
                                           ignored=False))},
            "absent": {
                "count": len(shadow_sel(present=False)),
                "paths": sorted("%s  [ignored=%s]" % (name(r), r["ignored"])
                                for r in shadow_sel(present=False))},
            "convention_totals": {
                k: sum(1 for r in shadow_rows if r["convention"] == k)
                for k in ("run_dir", "repo_root", "both", "neither")},
            "runs_listing_repo_root_relative": {
                slug: v["convention"]["repo_root"]
                for slug, v in sorted(shadow_per_run.items())
                if v.get("convention", {}).get("repo_root")},
            "per_run": shadow_per_run,
        },
        "rows": rows,
        "shadow_rows": shadow_rows,
    }

    with open(os.path.join(HERE, "scope.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")

    summary = dict(out)
    summary.pop("rows")
    summary.pop("shadow_rows")
    summary["H_out_of_scope_manifests"] = {
        k: v for k, v in summary["H_out_of_scope_manifests"].items()
        if k != "per_run"}
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
