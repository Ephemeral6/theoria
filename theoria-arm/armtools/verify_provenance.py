"""Is this arm's archive accountable? Nine checks, and it exits non-zero if not.

The archive is what Phase 4 reads back to account for every ARC action this arm
ever spent. That only works if three things hold, and each of them failed here
at least once before this file existed:

* **every run under `runs/` has a manifest.** Five did not.
* **no directory under `runs/` is a fixture.** Two were, and by directory
  listing they were indistinguishable from experiments that cost money.
* **every billed action has a number the API itself confirms.** Two runs died
  before closing their scorecard, so their manifests said `scorecard: null`
  while the number sat, unreferenced, in a salvage run's ledger.

Nothing here calls the network, spends an action, or reads the working tree's
opinion of anything. Everything is checked against the ledgers.

    cd theoria-arm && python -m armtools.verify_provenance
"""

import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

from armtools import backfill
from proxy.ledger import read_ledger

REQUIRED = ("prompt_id", "branch", "base_commit", "utc")


class Checks:
    def __init__(self) -> None:
        self.rows: List[Dict[str, Any]] = []

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        self.rows.append({"check": name, "ok": bool(ok), "detail": detail})
        return bool(ok)

    @property
    def failed(self) -> List[Dict[str, Any]]:
        return [r for r in self.rows if not r["ok"]]


def _manifest(runs_root: str, slug: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(runs_root, slug, "MANIFEST.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def run(runs_root: Optional[str] = None) -> Checks:
    runs_root = runs_root or _bootstrap.path("runs")
    checks = Checks()
    survey = backfill.survey(runs_root)

    # 1 -- the archive holds no fixtures.
    fixtures = [r["slug"] for r in survey if r["kind"] == "fixture"]
    checks.check(
        "runs/ contains no test or smoke fixture", not fixtures,
        "found %r -- these belong under harness.run.FIXTURE_RUNS_DIR, not in "
        "the archive" % fixtures if fixtures else
        "every directory under runs/ is archive material or a process record")

    # 2 -- every archive-material run has a manifest.
    naked = [r["slug"] for r in survey if r["archive_material"]
             and not r["has_manifest"]]
    checks.check("every run has a MANIFEST.json", not naked,
                 "missing for %r -- run `python -m armtools.backfill --all`"
                 % naked if naked else "%d runs, %d manifests"
                 % (sum(1 for r in survey if r["archive_material"]),
                    sum(1 for r in survey if r["archive_material"]
                        and r["has_manifest"])))

    # 3 -- CLAUDE.md's four required fields are present, or explicitly absent
    #      with a reason. A null with a reason passes; a null without one does
    #      not, and neither does a missing key.
    bad: List[str] = []
    for row in survey:
        if not row["archive_material"]:
            continue
        manifest = _manifest(runs_root, row["slug"]) or {}
        stated = {m["field"].split(" ")[0]
                  for m in (manifest.get("provenance") or {}).get("missing", [])}
        for field in REQUIRED:
            if field not in manifest:
                bad.append("%s: no %r key at all" % (row["slug"], field))
            elif manifest[field] is None and field not in stated:
                bad.append("%s: %r is null and provenance.missing does not say "
                           "why" % (row["slug"], field))
    checks.check("prompt_id / branch / base_commit / utc are present or "
                 "explicitly accounted for", not bad, "; ".join(bad) or
                 "every manifest either carries the four or names what it lost")

    # 4 -- the billed-action total, from the ledgers, against the API's own
    #      arithmetic. This is the number Phase 4 has to be able to defend.
    ledger_total = 0
    api_total = 0
    per_run = []
    cards: Dict[str, Dict[str, Any]] = {}
    for row in survey:
        if not row["archive_material"]:
            continue
        ledger_path = os.path.join(runs_root, row["slug"], "ledger.jsonl")
        records = read_ledger(ledger_path) if os.path.exists(ledger_path) else []
        mine = backfill.records_of(records, None) if records else []
        spent = backfill.quota(mine, [])["billed_actions_from_ledger"]
        ledger_total += spent
        per_run.append({"slug": row["slug"], "billed": spent})
        for card in backfill.recovered_scorecards(mine):
            cards[card["card_id"]] = card
    api_total = sum(c.get("total_actions") or 0 for c in cards.values())
    checks.check(
        "billed actions reconcile: ledgers vs closed scorecards",
        ledger_total == api_total,
        "ledgers say %d, the %d closed scorecards say %d%s"
        % (ledger_total, len(cards), api_total,
           "" if ledger_total == api_total else " -- MISMATCH"))

    # 5 -- every run that spent an action has an API-confirmed number for it,
    #      whether in its own manifest or by a named pointer to the salvage
    #      that recovered it.
    unconfirmed = []
    for row in survey:
        if not row["archive_material"] or not row["billed_actions_from_ledger"]:
            continue
        manifest = _manifest(runs_root, row["slug"]) or {}
        if manifest.get("scorecard") or manifest.get("scorecard_recovered_by"):
            continue
        unconfirmed.append(row["slug"])
    checks.check("every run that spent actions can point at its scorecard",
                 not unconfirmed,
                 "no confirmed scorecard reachable from %r" % unconfirmed
                 if unconfirmed else
                 "each of the %d runs that spent an action carries its "
                 "scorecard or names the salvage holding it"
                 % sum(1 for r in survey if r["billed_actions_from_ledger"]))

    # 6 -- orphaned scorecards are declared, not silently dropped.
    #
    #      Drawn from the same population as check 4, and it has to be: `cards`
    #      above is built from archive material only, so scanning every ledger
    #      here compares an all-runs numerator against an archive-only
    #      denominator. A `--mock` run opens and closes MockArc's own card ids,
    #      which are not ARC scorecards and are never billed; counted
    #      asymmetrically they surface as orphans that no manifest can honestly
    #      declare. An orphan matters because it means real billed actions with
    #      no closed card behind them, and that is an archive-material question.
    opened: Dict[str, str] = {}
    for row in survey:
        if not row["archive_material"]:
            continue
        ledger_path = os.path.join(runs_root, row["slug"], "ledger.jsonl")
        if not os.path.exists(ledger_path):
            continue
        for card in backfill.opened_scorecards(read_ledger(ledger_path)):
            opened[card["card_id"]] = row["slug"]
    orphans = {cid: slug for cid, slug in opened.items() if cid not in cards}
    declared = set()
    for row in survey:
        manifest = _manifest(runs_root, row["slug"]) or {}
        declared.update(manifest.get("scorecards_opened_and_never_closed") or [])
    undeclared = sorted(set(orphans) - declared)
    checks.check("every scorecard opened and never closed is declared as such",
                 not undeclared,
                 "orphaned and undeclared: %r" % undeclared if undeclared else
                 "%d orphan(s), all declared in the manifest of the run that "
                 "opened them" % len(orphans))

    # 7 -- the sealed pile, from the bytes of every ledger in the archive.
    #      `archive.sealing` already does this per run; this is the whole
    #      archive at once, so a stray game id cannot hide in an unmanifested
    #      corner of it.
    seen: List[str] = []
    for row in survey:
        manifest = _manifest(runs_root, row["slug"]) or {}
        sealing = manifest.get("sealing") or {}
        seen.extend(sealing.get("sealed_game_ids_found") or [])
    checks.check("no sealed-pile game appears anywhere in the archive",
                 not seen, "sealed ids found: %r" % sorted(set(seen)) if seen
                 else "every manifest's sealing check is clean")

    # 8 -- the backfill is reproducible: re-deriving a manifest reproduces the
    #      bytes already on disk. A manifest that drifts on every run is not a
    #      record of anything. Nothing is written -- `backfill.render` gives the
    #      bytes a write *would* produce and they are compared in memory.
    checks.check(*_idempotence(runs_root, survey))

    # 9 -- no manifest claims a base_commit its own arm_version contradicts
    #      without saying so. Claiming one is allowed -- three of these runs
    #      predate the check -- but claiming one silently is not.
    silent = []
    for row in survey:
        if not row["archive_material"]:
            continue
        manifest = _manifest(runs_root, row["slug"]) or {}
        prov = manifest.get("provenance") or {}
        check = prov.get("base_commit_check") or manifest.get("base_commit_check")
        # A backfilled manifest needs no separate check: its `base_commit` was
        # *produced by* matching the recorded arm_version, so the derivation is
        # the verification. A manifest that got its commit from `git rev-parse
        # HEAD` needs one, because nothing about HEAD ties it to the run.
        derived = (prov.get("mode") == "backfill"
                   and (prov.get("arm_version_lookup") or {}).get("verdict")
                   in ("matched", "ambiguous"))
        if manifest.get("base_commit") and not (check or derived):
            silent.append(row["slug"])
    checks.check("every recorded base_commit carries its verification verdict",
                 not silent, "unverified base_commit in %r" % silent if silent
                 else "each base_commit is either derived from the recorded "
                      "arm_version or carries a check that says it is not")

    # 10 -- every path a manifest lists can be accounted for by a reader who has
    #       only the clone. This exists because check 8 cannot do it, and the
    #       reason is worth stating rather than leaving to be rediscovered.
    #
    #       Check 8 re-derives, and it dispatches: `backfill` manifests go
    #       through `build()`, which walks the run directory and so does notice a
    #       path that is not there; `amend` manifests go through
    #       `amend_payload()`, which by contract leaves the original manifest
    #       exactly as written and never looks at `files[]` at all. So four
    #       archived manifests list a `trace.jsonl` -- three of them list one
    #       that does not exist on any machine in this repository -- and check 8
    #       passes them, not because they are right but because of which branch
    #       they took. A check that opens its eyes on one code path is worse than
    #       no check, because its green gets read as coverage.
    #
    #       The tempting repair -- route everything through `build()` -- is
    #       wrong, and measurably so: forcing `20260729T105729Z-leg01` through it
    #       produces a 444-line diff that deletes `base_commit`,
    #       `base_commit_check` and the whole `budget` block, because `build()`
    #       reconstructs from the ledger and those fields were never in it.
    #       `build()` is genuinely the wrong deriver for an `amend` manifest. The
    #       dispatch is right; what was missing was this, which does not care
    #       which deriver a manifest uses.
    #
    #       What it demands is not "the file is here". An artefact the repository
    #       deliberately does not ship is still a real artefact -- `.gitignore`
    #       names `candidates.jsonl` (201 MB, over GitHub's limit) and
    #       `runs/*/trace.jsonl` (large, re-derivable from the ledger) and says
    #       why for each. A reader sent to one of those can run `git check-ignore
    #       -v` and get the reason. What must not happen is a manifest pointing
    #       at a file that is neither present nor explained anywhere: a dangling
    #       reference with no way for a reader to find out what became of it.
    #       And "in the clone" is asked of the **commit**, not of the disk. The
    #       first version of this check asked `os.path.exists`, and an
    #       adversarial pass measured what that costs: a path that is present
    #       here but committed nowhere passes, and dangles in every clone. A check
    #       written to end "the same commit gets two answers on two machines" was
    #       itself machine-dependent, by the same mechanism, one file away from
    #       the one it was policing. `backfill.paths_the_clone_ships` asks
    #       `git ls-tree HEAD`; the working tree is not consulted at all, which is
    #       what makes the answer the same everywhere -- and the manifest itself
    #       is read out of the commit too, by `blob_the_clone_ships`, because
    #       asking git which paths are shipped and then reading the *list* of
    #       them off the disk leaves the working tree deciding half the verdict.
    #       (The version in between
    #       asked the *index*, and that was wrong for the reason recorded in that
    #       function: with `git commit <paths>` as this repository's convention, a
    #       staged-never-committed path is exactly what gets left out of the
    #       commit, and it would have read as shipped.)
    #
    #       **Scope: every run whose own `MANIFEST.json` this commit ships**, not
    #       just the archive-material ones. The `archive_material` filter is what
    #       made this check's name a lie -- `20260729T080000Z-E14-crash-is-not-a-finding`
    #       has 23 listed paths that resolve nowhere relative to its run
    #       directory, and was green because it has no ledger, so `classify` calls
    #       it a `process_record` and every check skips it. Measured at the
    #       changeover: 12 runs and 107 paths examined before, 35 runs and 161
    #       paths after. The new filter is also what lets this check ask `HEAD`
    #       without punishing work in progress: a run whose manifest is not
    #       committed is invisible here, exactly as it is invisible to a reader
    #       with only the clone.
    #
    #       **Two path conventions, and a manifest may not mix them.** E14's 23
    #       paths are all repo-root-relative (`theoria-arm/runs/.../REPORT.md`,
    #       `a0-spike/pipeline/adapt.py`) and all shipped, so that is a second
    #       real convention rather than a broken manifest, and it is accepted as
    #       one. What is not accepted is one manifest using both: then "resolves
    #       somewhere" stops being a property of the manifest and starts being a
    #       search, and a wrong path can be smuggled in by happening to match at
    #       the other root. The convention a manifest is in also decides where
    #       its ignore rules are asked from, which the first draft got wrong in
    #       the direction of a red nobody could explain away.
    #
    #       Three verdicts, not two. If git cannot be asked, this check has no
    #       answer -- and "no answer" must not be rendered as either green (the
    #       failure mode that made the reflex layer quieter about a broken board
    #       than about an empty one) or as "everything is dangling" (a red naming
    #       paths that are probably fine).
    dangling = []
    top = backfill._repo_top(runs_root)
    shipped = backfill.paths_the_clone_ships(runs_root)
    examined = {"runs": 0, "paths": 0}
    for row in survey if shipped is not None and top else []:
        run_dir = os.path.join(runs_root, row["slug"])
        prefix = os.path.relpath(run_dir, top).replace(os.sep, "/")
        if "%s/MANIFEST.json" % prefix not in shipped:
            continue                      # in flight: no clone can see it either
        # The manifest is read out of the **commit**, not off the disk. Asking
        # git which paths are shipped and then reading the list of them from the
        # working tree would leave the working tree deciding half the answer: a
        # manifest committed once and edited since would be checked in its local
        # form, and a clone would check a different document. Half a repair reads
        # as a whole one, which is worse than none.
        blob = backfill.blob_the_clone_ships(runs_root,
                                             "%s/MANIFEST.json" % prefix)
        try:
            manifest = json.loads(blob.decode("utf-8")) if blob else {}
        except (ValueError, UnicodeDecodeError) as exc:
            dangling.append("%s: the MANIFEST.json this commit ships is not "
                            "readable JSON (%s)" % (row["slug"], exc))
            continue
        listed = [(e.get("path") if isinstance(e, dict) else e)
                  for e in ((manifest or {}).get("files") or [])]
        listed = [p.replace("\\", "/") for p in listed if p]
        examined["runs"] += 1
        examined["paths"] += len(listed)

        stray = {p for p in listed if not backfill.path_is_inside_the_run(p)}
        for path in sorted(stray):
            dangling.append("%s -> %s (not a path inside the run)"
                            % (row["slug"], path))
        rest = [p for p in listed if p not in stray]
        run_rel = {p for p in rest if "%s/%s" % (prefix, p) in shipped}
        root_rel = {p for p in rest if p in shipped} - run_rel
        if run_rel and root_rel:
            dangling.append(
                "%s mixes two path conventions: %r are relative to the run and "
                "%r to the repository root" % (row["slug"], sorted(run_rel),
                                               sorted(root_rel)))
            continue                    # its own fault; not also "dangling"
        # Which convention this manifest is written in, decided once for the
        # whole manifest. Root-relative only when nothing at all resolves inside
        # the run -- the shape `20260729T080000Z-E14-crash-is-not-a-finding`
        # actually has (23 paths, all `theoria-arm/...` or `a0-spike/...`, none
        # of them of the run). Anything in between was already caught above as
        # mixed, so this is not a second gate; it exists to name the anchor.
        by_root = bool(root_rel) and not run_rel
        resolved = root_rel if by_root else run_rel
        # **The anchor, and this is the part that was wrong.** `_ignored_paths`
        # runs `git check-ignore` from the directory it is handed, so asking it
        # about a root-relative path from inside the run directory asks about
        # `<run>/theoria-arm/...`: a path nobody wrote, which no rule matches, so
        # every unresolved path in a root-relative manifest was unexplainable by
        # construction. Rules must be asked from wherever the paths are written
        # from.
        anchor = top if by_root else run_dir
        # Residual, and not closable here: a manifest whose paths *all* happen to
        # resolve at the root is read as root-relative even if its author meant
        # them relative to the run. Telling those apart needs the manifest to
        # declare its convention, which is a schema change, not a check.
        unresolved = [p for p in rest if p not in resolved]
        explained = backfill._ignored_paths(anchor, unresolved)
        for path in sorted(set(unresolved) - explained):
            dangling.append("%s/%s" % (row["slug"], path))

    detail = ("%(runs)d manifests this commit ships, %(paths)d listed paths: "
              "every one is shipped too, or named by a `.gitignore` rule that "
              "says why it is not" % examined)
    if dangling:
        detail = "listed, not shipped, and unexplained: %r" % dangling
    if shipped is None or not top:
        detail = ("git could not be asked what this commit ships, so this check "
                  "has no answer -- no git, not a repository, or no commit yet")
        dangling = ["(no answer)"]
    checks.check("every file a shipped manifest lists is shipped too or "
                 "excluded by the repository's own rules",
                 not dangling,
                 detail)
    return checks


def _idempotence(runs_root: str, survey: List[Dict[str, Any]]):
    """Re-derive each manifest and compare against the bytes on disk.

    Only archive-material runs are re-derived. A process record -- a tooling
    pass that touched no environment and wrote its own manifest by hand -- has
    nothing to derive from, and running the deriver over it would invent a
    provenance block for a run that never had a ledger.
    """
    name = "re-deriving every manifest reproduces it byte for byte"
    try:
        from armtools import armversion                 # noqa: PLC0415
        table = armversion.scan()
        drifted, checked = [], 0
        for row in survey:
            if not row["archive_material"] or not row["has_manifest"]:
                continue
            slug = row["slug"]
            path = os.path.join(runs_root, slug, "MANIFEST.json")
            with open(path, "rb") as fh:
                on_disk = fh.read()
            if backfill._is_backfilled(runs_root, slug):
                payload = backfill.build(slug, runs_root=runs_root, table=table)
            else:
                result = backfill.amend_payload(slug, runs_root=runs_root,
                                                table=table)
                payload = result[0] if result else None
            checked += 1
            if payload is None or backfill.render(payload) != on_disk:
                drifted.append(slug)
        return (name, not drifted,
                "drifted: %r" % drifted if drifted else
                "%d manifests, all byte-stable under re-derivation" % checked)
    except Exception as exc:                            # noqa: BLE001
        return (name, False,
                "the check itself failed: %s: %s" % (type(exc).__name__, exc))


def main(argv=None) -> int:
    checks = run()
    width = max(len(r["check"]) for r in checks.rows)
    for row in checks.rows:
        print("%s  %-*s  %s" % ("PASS" if row["ok"] else "FAIL",
                                width, row["check"], row["detail"]))
    print()
    if checks.failed:
        print("FAILED: %d of %d" % (len(checks.failed), len(checks.rows)))
        return 1
    print("OK: %d checks" % len(checks.rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
