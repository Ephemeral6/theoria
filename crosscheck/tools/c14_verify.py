"""Verify the C14 census: re-run it and check it lands on the committed record.

The census is the load-bearing artefact of C14 -- the number `0 of 303` is what
decides whether the framework may keep saying "four co-derived forms".  A number
that cannot be re-derived is an assertion, so this script re-runs the census into
a scratch directory and diffs the result against the committed
``census.json``.

Two tiers, deliberately separated:

* **hard** -- the action census (owed / good / defect tallies / per-file records
  / generated PDDL bytes).  Pure computation over tracked files: no toolchain, no
  network, no clock.  Any drift here is a real regression and fails the run.
* **soft** -- the Fast Downward columns.  ``.toolchain/`` is gitignored and
  machine-local by design, so on a machine without an FD build the census records
  ``SKIPPED`` and this tier reports SKIP.  A skip is not a pass and is printed as
  its own word, because "no planner ran" and "every domain was rejected" are
  different findings that look identical if you are careless.

    python -m crosscheck.tools.c14_verify [--run <run-dir>]

Exit 0 green, 1 red.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_RUN = os.path.join(
    REPO, "crosscheck", "runs",
    "20260730T120005Z-C14-four-forms-is-three-and-a-half")

# Fields of the summary block that do not depend on any local toolchain.
PURE_SUMMARY_FIELDS = (
    "actions_owed",
    "actions_semantically_non_empty",
    "actions_defective",
    "fraction_good",
    "by_defect",
    "dsl_files_seen",
    "theories_with_rules",
    "theories_compiled",
    "theories_refused",
    "rules_lost_to_refusal",
    "problem_goals_by_verdict",
)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_volatile(payload: dict) -> list:
    """Per-file records minus the parts that embed absolute machine paths."""
    out = []
    for rec in payload["files"]:
        rec = dict(rec)
        rec.pop("independent_checks", None)
        out.append(rec)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=DEFAULT_RUN,
                    help="run directory holding out/census.json")
    args = ap.parse_args(argv)

    committed_dir = os.path.join(args.run, "out")
    committed_path = os.path.join(committed_dir, "census.json")
    if not os.path.isfile(committed_path):
        print("RED  no committed census at %s" % committed_path)
        return 1
    committed = json.load(open(committed_path, encoding="utf-8"))

    failures, skips = [], []
    tmp = tempfile.mkdtemp(prefix="c14-verify-")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "crosscheck.tools.c14_pddl_census",
             "--out", tmp],
            cwd=REPO, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=1800)
        if proc.returncode != 0:
            print("RED  census re-run exited %s\n%s"
                  % (proc.returncode, (proc.stdout or "") + (proc.stderr or "")))
            return 1
        fresh = json.load(open(os.path.join(tmp, "census.json"), encoding="utf-8"))

        # --- hard tier 1: the headline numbers -----------------------------
        for field in PURE_SUMMARY_FIELDS:
            want, got = committed["summary"].get(field), fresh["summary"].get(field)
            if want != got:
                failures.append("summary.%s: committed %r, re-run %r"
                                % (field, want, got))

        # --- hard tier 2: every per-file record ----------------------------
        if strip_volatile(committed) != strip_volatile(fresh):
            cf = {r["dsl"]: r for r in strip_volatile(committed)}
            ff = {r["dsl"]: r for r in strip_volatile(fresh)}
            for dsl in sorted(set(cf) | set(ff)):
                if cf.get(dsl) != ff.get(dsl):
                    failures.append("per-file record drifted: %s" % dsl)

        # --- hard tier 3: the generated PDDL, byte for byte ----------------
        cdir = os.path.join(committed_dir, "fd_translate")
        fdir = os.path.join(tmp, "fd_translate")
        if os.path.isdir(cdir):
            names = sorted(n for n in os.listdir(cdir) if n.endswith(".pddl"))
            if not names:
                failures.append("no committed *.pddl to compare against")
            for name in names:
                fresh_pddl = os.path.join(fdir, name)
                if not os.path.isfile(fresh_pddl):
                    failures.append("re-run did not produce %s" % name)
                elif sha256(os.path.join(cdir, name)) != sha256(fresh_pddl):
                    failures.append("generated PDDL changed: %s" % name)
        else:
            failures.append("committed run has no fd_translate/ directory")

        # --- soft tier: the independent planner ----------------------------
        if not fresh.get("fd_translate_dir"):
            skips.append("Fast Downward: no build on this machine "
                         "(.toolchain/ is gitignored) -- FD columns unverified. "
                         "This is a SKIP, not a pass.")
        else:
            want = committed["summary"].get("domains_fast_downward_accepted")
            got = fresh["summary"].get("domains_fast_downward_accepted")
            if want != got:
                failures.append(
                    "summary.domains_fast_downward_accepted: committed %r, "
                    "re-run %r (differing FD build?)" % (want, got))

        # --- hard tier 4: the corpus does not depend on the caller's cwd ---
        # A worktree and the main checkout must yield the same population.  They
        # did not before the SKIP_DIRS fix: nested agent checkouts under
        # `.claude/worktrees/` carry full copies of the corpus, so the same
        # script reported 59 DSL files from a worktree and 237 from the main
        # checkout.  Pin it, or the denominator silently depends on where you
        # stood when you ran it.
        sys.path.insert(0, os.path.join(REPO, "crosscheck", "tools"))
        import c14_pddl_census as census_mod
        here = census_mod.dsl_files()
        main_checkout = None
        try:
            common = subprocess.run(["git", "rev-parse", "--path-format=absolute",
                                     "--git-common-dir"], cwd=REPO,
                                    capture_output=True, text=True, timeout=30)
            if common.returncode == 0:
                main_checkout = os.path.dirname(common.stdout.strip())
        except Exception:                                     # noqa: BLE001
            pass
        if main_checkout and os.path.isdir(main_checkout) and main_checkout != REPO:
            saved = census_mod.REPO
            try:
                census_mod.REPO = main_checkout
                there = census_mod.dsl_files()
            finally:
                census_mod.REPO = saved
            if sorted(here) != sorted(there):
                only_there = sorted(set(there) - set(here))[:5]
                failures.append(
                    "corpus depends on cwd: %d DSL files from this checkout, %d "
                    "from the main checkout (e.g. %s)"
                    % (len(here), len(there), ", ".join(only_there) or "-"))
        else:
            skips.append("corpus cwd-independence: only one checkout visible, "
                         "cross-root comparison not run")
        if any("worktrees" in rec["dsl"] for rec in committed["files"]):
            failures.append("a nested checkout leaked into the corpus "
                            "(a path under */worktrees/* is being counted)")

        # --- the claim itself ----------------------------------------------
        # Guard against the census silently measuring nothing: an empty corpus
        # would report 0 good out of 0 owed and read as a green run.
        if not committed["summary"]["actions_owed"]:
            failures.append("actions_owed is 0 -- the census measured an empty "
                            "corpus; the finding would be vacuous")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for line in failures:
        print("RED  %s" % line)
    for line in skips:
        print("SKIP %s" % line)
    if failures:
        print("\nC14 VERIFY: RED (%d)" % len(failures))
        return 1
    s = committed["summary"]
    print("green  census reproduces: %d of %d actions semantically non-empty "
          "(%.1f%%)"
          % (s["actions_semantically_non_empty"], s["actions_owed"],
             100 * (s["fraction_good"] or 0)))
    print("green  %d per-file records and all generated PDDL byte-identical"
          % len(committed["files"]))
    print("\nC14 VERIFY: GREEN%s" % (" (with %d skip)" % len(skips) if skips else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
