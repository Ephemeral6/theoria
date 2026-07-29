"""Give a run that has no manifest one, out of its own evidence and nothing else.

`armtools/archive.py` writes a manifest at the end of a run. Five runs in this
arm's archive never got one: four salvages and an aborted pre-flight, all of
which ended without going through `archive`. This tool writes theirs
afterwards. The rule it works under is the whole point of it:

**every field is derived from the run's own records, or it is absent and said
to be absent.** Nothing is copied from the present working tree, because the
present working tree is months of commits away from what those runs ran. Where
`archive.build` calls `git rev-parse HEAD` and `_bootstrap.upstream_pin()` --
both of which describe *the machine writing the manifest*, not the run -- this
tool reads the branch and the pin off the ledger's own `run_start` record and
off `armtools.armversion`, which reconstructs the commit from the recorded
`arm_version` hash.

That distinction is not pedantry. `preflight-20260728T012057Z`'s manifest says
`base_commit: 606c582`, and 606c582's tree hashes to a *different*
`arm_version` than the one its own ledger recorded. The commit in that manifest
is where HEAD was when the manifest was written. The run ran against
uncommitted files. Both facts are true and only one of them was written down.

Two modes, and neither ever guesses:

* **create** -- a run with no `MANIFEST.json` gets one.
* **amend** -- a run that has one keeps every field it has; `utc` (required by
  CLAUDE.md and emitted by no version of `archive.py`) and a `provenance` block
  are added beside them. An existing `base_commit` is never overwritten, only
  checked, and the check's verdict is recorded next to it.

Output is byte-stable: no wall-clock timestamp enters a manifest, so running
this twice produces the same bytes and `armtools.verify_provenance` can assert
it.

    python -m armtools.backfill --all           # every run that needs it
    python -m armtools.backfill --slug <slug>
    python -m armtools.backfill --all --check   # verify only, write nothing
"""

import argparse
import fnmatch
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

from armtools import archive, armversion
from proxy.ledger import read_ledger

#: Slugs that are not archive material at all. A directory matching one of
#: these is a test's or a smoke's leftover: it proves nothing about the world,
#: cost nothing, and should not be under `runs/`. It is classified, reported,
#: and never given a manifest.
FIXTURE_GLOBS = ("pytest-*", "dryrun-*", "smoke*")

BACKFILL_PROMPT_ID = "S8-provenance-backfill"


# ------------------------------------------------------------------ evidence
def _unix(ts: Optional[str]) -> Optional[int]:
    if not ts:
        return None
    import datetime                                    # noqa: PLC0415
    for shape in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return int(datetime.datetime.strptime(ts, shape)
                       .replace(tzinfo=datetime.timezone.utc).timestamp())
        except ValueError:
            continue
    return None


def records_of(records: List[Dict[str, Any]],
               run_id: Optional[str]) -> List[Dict[str, Any]]:
    """The records belonging to one run, or a refusal.

    `LEDGER_FORMAT.md` §1 lets one file hold many runs, partitioned by
    `run_id`. Two of this arm's manifests carry `run_id: null` -- `archive.py`
    reads it from `run.json`'s summary and those runs never wrote one -- so the
    partition key is missing and something has to be done about it. Falling
    back to "all records" is right only when the file holds exactly one run.
    Where it holds more, this raises rather than silently attributing one run's
    actions to another: a wrong number in the archive is worse than a gap.
    """
    if run_id:
        return [r for r in records if r.get("run_id") == run_id]
    found = {r.get("run_id") for r in records if r.get("run_id")}
    if len(found) > 1:
        raise ValueError(
            "no run_id to partition by, and this ledger holds %d runs (%s). "
            "Refusing to guess which one this manifest describes."
            % (len(found), ", ".join(sorted(map(str, found)))))
    return records


def _run_start(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    for record in records:
        if record.get("event") == "run_start":
            return record
    return {}


def _mock_upstreams(records: List[Dict[str, Any]]) -> Optional[List[str]]:
    """The loopback upstreams this run talked to, if it *only* talked to those.

    `run_start.env_upstream` is the address the env proxy was pointed at, and it
    is written before anything can be spent. A live run names
    `https://three.arcprize.org`; a `--mock` run names a `127.0.0.1` port that
    `proxy.mock.arc_mock` was listening on. That is direct evidence about
    whether the ARC API was reached, and it is stronger than the slug, which any
    caller may choose freely.

    Returns None where any run_start names a non-loopback upstream, or where
    there is no `env_upstream` to read -- "not proven offline" is the safe
    answer, because the cost of wrongly calling a live run offline is dropping a
    billed run out of the archive's account.
    """
    seen: List[str] = []
    for record in records:
        if record.get("event") != "run_start":
            continue
        upstream = record.get("env_upstream")
        if not isinstance(upstream, str):
            return None
        host = urlparse(upstream).hostname or ""
        if host not in ("127.0.0.1", "::1", "localhost"):
            return None
        seen.append(upstream)
    return sorted(set(seen)) or None


def _run_end(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    for record in reversed(records):
        if record.get("event") == "run_end":
            return record
    return {}


def recovered_scorecards(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every scorecard this run read back from the API, whole.

    A salvage run's entire product is one of these: the aborted run it is
    salvaging died before it could close its own card, so the *only* record of
    what that run was billed is the close response sitting in the salvage's
    ledger. `archive.py` looks for the scorecard in `run.json`'s summary, which
    a salvage has none of, so the number was in the archive and unreachable
    from it.
    """
    out = []
    for record in records:
        http = record.get("http") or {}
        if http.get("path") != "/api/scorecard/close" or http.get("status") != 200:
            continue
        response = record.get("response")
        if isinstance(response, dict) and response.get("card_id"):
            out.append(response)
    return out


def opened_scorecards(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for record in records:
        http = record.get("http") or {}
        if http.get("path") != "/api/scorecard/open" or http.get("status") != 200:
            continue
        response = record.get("response") or {}
        if response.get("card_id"):
            out.append({"card_id": response["card_id"],
                        "request": record.get("request")})
    return out


def classify(slug: str, run_dir: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """What kind of thing is this directory? Decided from its contents."""
    for glob in FIXTURE_GLOBS:
        if fnmatch.fnmatch(slug, glob):
            return {"kind": "fixture",
                    "archive_material": False,
                    "why": ("slug matches %r: a test or smoke leftover, not an "
                            "experiment. It spent no quota and belongs outside "
                            "`runs/` (`harness.run.FIXTURE_RUNS_DIR`)." % glob)}

    if not records:
        if os.path.exists(os.path.join(run_dir, "MANIFEST.json")):
            return {"kind": "process_record", "archive_material": False,
                    "why": ("no ledger, but a manifest: a tooling or repair "
                            "pass that touched no environment. It has its own "
                            "manifest and there is nothing to derive")}
        return {"kind": "empty", "archive_material": False,
                "why": "no ledger records: nothing happened here to account for"}

    mock = _mock_upstreams(records)
    if mock:
        return {"kind": "mock", "archive_material": False,
                "why": ("every run_start names a loopback env_upstream (%s): "
                        "this ran against `proxy.mock.arc_mock`, reached no ARC "
                        "API and spent no quota, so there is no billed action "
                        "for the archive to account for. Not a `fixture` -- "
                        "these are committed offline proofs that other run "
                        "directories cite as evidence (see D-S8-018 and "
                        "`runs/20260728T152910Z-a3-desk-gate/RUN_STATE.md`), "
                        "and a fixture is a leftover nobody cites."
                        % ", ".join(mock))}

    start = _run_start(records)
    note = (start.get("note") or "").lower()
    end = _run_end(records)
    outcome = end.get("outcome")
    aborted = os.path.exists(os.path.join(run_dir, "ABORTED.md"))

    if "salvage" in note or outcome == "salvage":
        return {"kind": "salvage", "archive_material": True,
                "why": ("the run_start note or the run_end outcome says "
                        "salvage: this run exists to close another run's "
                        "orphaned scorecard, and carries that scorecard")}
    if "pre-flight" in note or "preflight" in note or slug.startswith("preflight-"):
        return {"kind": "preflight", "archive_material": True,
                "why": ("a pre-flight: the live chain exercised for zero billed "
                        "actions. Cheap, but live, and part of the account")}
    if aborted:
        return {"kind": "aborted_experiment", "archive_material": True,
                "why": "carries ABORTED.md: a live run stopped on a defect"}
    return {"kind": "experiment", "archive_material": True,
            "why": "a live run that reached its own end"}


def quota(records: List[Dict[str, Any]],
          scorecards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """What this run cost in ARC actions, from two independent sides.

    The ledger side counts successful non-RESET `env_step` records. The API
    side is whatever a closed scorecard says. Where both exist they must agree,
    and where they disagree that is the finding.
    """
    steps = [r for r in records if r.get("event") == "env_step"]
    ok = [r for r in steps if (r.get("http") or {}).get("status") == 200]
    actions = [r for r in ok if (r.get("action") or {}).get("name") != "RESET"]

    out: Dict[str, Any] = {
        "billed_actions_from_ledger": len(actions),
        "resets": len(ok) - len(actions),
        "env_steps": len(steps),
        "model_calls": sum(1 for r in records if r.get("event") == "model_call"),
    }
    totals = [c.get("total_actions") for c in scorecards
              if c.get("total_actions") is not None]
    if totals:
        out["billed_actions_from_scorecard"] = totals
        out["agree"] = all(t == len(actions) for t in totals)
        if not out["agree"]:
            out["note"] = ("the ledger and the API disagree about how many "
                           "actions this run was billed -- for a salvage run "
                           "this is expected and not a defect: the scorecard it "
                           "closed belongs to its parent run, whose actions the "
                           "salvage did not itself spend. See `parent_run`.")
    else:
        out["billed_actions_from_scorecard"] = None
    return out


def parent_of(slug: str, scorecards: List[Dict[str, Any]],
              runs_root: str) -> Optional[Dict[str, Any]]:
    """Whose scorecard did this run close?

    Two independent answers and they are cross-checked: the slug (a salvage is
    named after its parent) and `opaque.run_id` inside the scorecard, which the
    parent stamped when it opened the card. The second is the authoritative one
    -- the first is a naming convention and could be wrong.
    """
    if not scorecards:
        return None
    opaque = scorecards[0].get("opaque") or {}
    by_id = opaque.get("run_id")
    others = [c.get("card_id") for c in scorecards[1:]]

    by_slug = None
    for suffix in ("-salvage2", "-salvage"):
        if slug.endswith(suffix):
            candidate = slug[: -len(suffix)]
            for name in (candidate, candidate + "-aborted"):
                if os.path.isdir(os.path.join(runs_root, name)):
                    by_slug = name
                    break
            break

    out: Dict[str, Any] = {
        "parent_slug_from_naming": by_slug,
        "parent_run_id_from_scorecard_opaque": by_id,
        "card_id": scorecards[0].get("card_id"),
        "prompt_id_from_scorecard_opaque": opaque.get("prompt_id"),
    }
    if others:
        # Every salvage in this archive closed exactly one card. If one ever
        # closes two, "the parent" is not a single run and the fields above
        # describe only the first card -- said out loud rather than left for a
        # reader to discover from `scorecards_recovered`.
        out["other_cards_this_run_also_closed"] = others
        out["warning"] = ("this run closed %d scorecards; the parent fields "
                          "above describe only the first. The rest are in "
                          "`scorecards_recovered`." % len(scorecards))
    if by_slug:
        ledger = os.path.join(runs_root, by_slug, "ledger.jsonl")
        if os.path.exists(ledger):
            parent = [r for r in read_ledger(ledger) if r.get("run_id") == by_id]
            out["parent_ledger_carries_that_run_id"] = bool(parent)
            steps = [r for r in parent
                     if r.get("event") == "env_step"
                     and (r.get("http") or {}).get("status") == 200
                     and (r.get("action") or {}).get("name") != "RESET"]
            out["parent_billed_actions_from_ledger"] = len(steps)
            out["parent_billed_actions_from_scorecard"] = \
                scorecards[0].get("total_actions")
            out["reconciles"] = (len(steps) == scorecards[0].get("total_actions"))
    return out


# --------------------------------------------------------------- provenance
def provenance(records: List[Dict[str, Any]], run_dir: str,
               table: Dict[str, Any]) -> Dict[str, Any]:
    """Where each answer came from, and which questions have no answer."""
    start = _run_start(records)
    recorded = start.get("arm_version") or {}
    arm_sha = recorded.get("sha256")

    located: Dict[str, Any] = {"verdict": "no_arm_version_recorded"}
    if arm_sha:
        located = armversion.locate(arm_sha, table)
        unix = _unix(start.get("ts"))
        if located["verdict"] == "no_match" and unix is not None:
            located["window"] = armversion.nearest_by_time(unix, table)
        elif located["commits"] and unix is not None:
            # The commit is *not* "where the run ran from" -- in two cases here
            # it was created seconds AFTER the run started, because the fix
            # being tested was committed while the run was still going. What
            # the hash establishes is narrower and worth stating exactly: the
            # run's `.py` sources were byte-identical to the tree that commit
            # holds. Saying "the run ran at commit X" would be false.
            made = {c["commit"]: c["unix"] for c in table["commits"]}
            first = located["commits"][0]
            delta = made.get(first, 0) - unix
            located["relation_to_the_run"] = {
                "commit_committed_unix": made.get(first),
                "run_started_unix": unix,
                "commit_minus_run_start_s": delta,
                "claim": ("this run's arm sources were byte-identical to the "
                          "tree held by this commit. The commit was created "
                          "%d s %s the run started, so it is not 'the commit "
                          "the run ran from' -- it is the commit whose tree "
                          "the run's files match."
                          % (abs(delta), "after" if delta >= 0 else "before")),
            }

    notes: List[Dict[str, str]] = []
    derived: Dict[str, str] = {
        "utc": "ledger run_start.ts",
        "run_id": "ledger run_start.run_id",
        "game_id": "ledger run_start.game_id",
        "arm_version": "ledger run_start.arm_version",
        "upstream_pin": "ledger run_start.upstream_pin (NOT the working tree)",
        "guard": "ledger run_start.guard",
        "reconciliation / cost / constraint_8 / sealing":
            "armtools.archive, over this run's own ledger records",
    }
    missing: List[Dict[str, str]] = []

    if located["verdict"] == "matched":
        derived["base_commit"] = (
            "armtools.armversion: the arm_version this run recorded is "
            "reconstructed from exactly one commit's tree")
    elif located["verdict"] == "ambiguous":
        derived["base_commit"] = ("armtools.armversion: several commits share "
                                  "this arm_version; all are named")
        missing.append({
            "field": "base_commit (single value)",
            "why": ("%d commits have identical arm .py files, so the recorded "
                    "hash does not single one out" % len(located["commits"])),
        })
    else:
        missing.append({
            "field": "base_commit",
            "why": ("the arm_version this run recorded (%s, %s files) is "
                    "reconstructed by no commit reachable from any ref: the "
                    "run executed against uncommitted working-tree edits. The "
                    "commits it fell between are given under "
                    "`arm_version_lookup.window`; the exact sources are not "
                    "recoverable from git."
                    % ((arm_sha or "absent")[:12], recorded.get("files"))),
        })

    if not os.path.exists(os.path.join(run_dir, "run.json")):
        notes.append({
            "field": "run.json / summary",
            "why": ("this run never reached `_finish()`, so no `run.json` was "
                    "written. `outcome` and `elapsed_s` are taken from the "
                    "ledger's `run_end` record instead, which carries them; "
                    "`budget` and `world` were only ever in the summary and "
                    "are absent. Nothing required by CLAUDE.md is affected."),
        })

    return {
        "mode": "backfill",
        "tool": "armtools/backfill.py",
        "prompt_id_of_the_backfill": BACKFILL_PROMPT_ID,
        "rule": ("every field is derived from this run's own records or from "
                 "git; nothing is read from the working tree the backfill ran "
                 "on, and nothing is inferred that the evidence does not carry"),
        # `status` is about CLAUDE.md's four required fields and nothing else.
        # A run whose summary is gone but whose provenance is fully derived is
        # `complete` and says what it lost under `notes`; calling that
        # `incomplete` would flatten a real distinction the archive needs.
        "status": "complete" if not missing else "incomplete",
        "derived_from": derived,
        "missing": missing,
        "notes": notes,
        "arm_version_lookup": located,
    }


# ------------------------------------------------------------------- build
def build(slug: str, *, runs_root: Optional[str] = None,
          table: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    runs_root = runs_root or _bootstrap.path("runs")
    run_dir = os.path.join(runs_root, slug)
    ledger_path = os.path.join(run_dir, "ledger.jsonl")
    records = read_ledger(ledger_path) if os.path.exists(ledger_path) else []

    start = _run_start(records)
    mine = records_of(records, start.get("run_id"))
    run_id = start.get("run_id")
    end = _run_end(mine)

    table = table if table is not None else armversion.scan()
    kind = classify(slug, run_dir, mine)
    closed = recovered_scorecards(mine)
    opened = opened_scorecards(mine)
    prov = provenance(mine, run_dir, table)
    located = prov["arm_version_lookup"]

    branch = branch_of(slug, runs_root)
    if branch["value"]:
        prov["derived_from"]["branch"] = branch["source"]
        prov["notes"].append({
            "field": "branch",
            "why": ("no ledger record carries a branch name -- the arm never "
                    "writes one -- so this is inherited, not recorded. The "
                    "source is named in `derived_from.branch`. It is not a "
                    "statement this run made about itself."),
        })
    else:
        prov["missing"].append({
            "field": "branch",
            "why": ("no ledger record carries a branch name and there is no "
                    "parent run whose contemporaneous manifest recorded one. "
                    "`git branch --contains` was considered and rejected: it "
                    "answers which branches hold the commit today, which "
                    "changes as unrelated work is pushed."),
        })
        prov["status"] = "incomplete"

    prompt = prompt_id_of(mine, slug, runs_root)
    if prompt["value"]:
        prov["derived_from"]["prompt_id"] = prompt["source"]
    else:
        prov["missing"].append({
            "field": "prompt_id",
            "why": ("this run stamped no prompt on any scorecard it closed, "
                    "carries no p<N> tag, and is not a salvage with a parent "
                    "manifest to read one from"),
        })
        prov["status"] = "incomplete"

    files = sorted(
        os.path.relpath(os.path.join(root, name), run_dir).replace(os.sep, "/")
        for root, _dirs, names in os.walk(run_dir) for name in names
        if "__pycache__" not in root and name != "MANIFEST.json")

    orphans = [c["card_id"] for c in opened
               if c["card_id"] not in {s.get("card_id") for s in closed}]

    manifest: Dict[str, Any] = {
        # CLAUDE.md's four required fields come first and every one of them is
        # either a derived value or an explicit null with a reason in
        # `provenance.missing`.
        "prompt_id": prompt["value"],
        "branch": branch["value"],
        "base_commit": (located["commits"][0]
                        if located["verdict"] == "matched" else None),
        "utc": start.get("ts"),

        "slug": slug,
        "arm": "theoria",
        "run_id": run_id,
        "game_id": start.get("game_id"),
        "classification": kind,
        "provenance": prov,
        "arm_version": start.get("arm_version"),
        "guard": start.get("guard"),
        "upstream_pin": start.get("upstream_pin"),
        "outcome": end.get("outcome"),
        "elapsed_s": end.get("elapsed_s"),
        "note_at_run_start": start.get("note"),
        "quota": quota(mine, closed),
        "scorecards_recovered": closed,
        "scorecards_opened_and_never_closed": orphans,
        "parent_run": parent_of(slug, closed, runs_root),
        "ledger": {"path": "ledger.jsonl",
                   "format": "LEDGER_FORMAT v1.0",
                   "records": len(records),
                   "records_this_run": len(mine)},
        "reconciliation": archive.reconcile(mine, None),
        "cost": archive.costs(mine),
        "constraint_8": archive.constraint_8(mine, run_dir),
        "sealing": archive.sealing(mine),
        "files": [{"path": p, "sha256": _sha256(os.path.join(run_dir, p))}
                  for p in files],
    }
    if orphans:
        manifest["scorecards_opened_and_never_closed_note"] = (
            "this run opened a scorecard and no run -- this one or any other in "
            "the archive -- ever closed it. The API's own count of what it was "
            "billed was therefore never read back, and cannot be, offline. The "
            "ledger's own count stands unconfirmed; see `quota`.")
    return manifest


def branch_of(slug: str, runs_root: str) -> Dict[str, Optional[str]]:
    """Which branch this run was made on, if anything contemporaneous says.

    Nothing in a ledger records a branch: the arm does not write one. The only
    contemporaneous record is the parent run's manifest, whose `branch` field
    `archive.py` filled from `git rev-parse --abbrev-ref HEAD` in the same
    session, minutes earlier. A salvage inherits it, and the manifest says it
    inherited rather than observed it.

    `git branch --contains <derived commit>` is the tempting alternative and it
    is wrong: it lists the branches that hold the commit *now*, so the answer
    changes whenever anyone pushes anything, and a manifest built on it stops
    reproducing itself. That was caught by the reproducibility check, which is
    the point of having one.
    """
    for suffix in ("-salvage2", "-salvage"):
        if slug.endswith(suffix):
            base = slug[: -len(suffix)]
            for name in (base, base + "-aborted"):
                path = os.path.join(runs_root, name, "MANIFEST.json")
                if os.path.exists(path):
                    with open(path, encoding="utf-8") as fh:
                        value = json.load(fh).get("branch")
                    if value:
                        return {"value": value,
                                "source": ("inherited from the parent run %r's "
                                           "manifest, written in the same "
                                           "session; no ledger records a branch"
                                           % name)}
    return {"value": None, "source": None}


def prompt_id_of(records: List[Dict[str, Any]], slug: str,
                 runs_root: str) -> Dict[str, Optional[str]]:
    """Which prompt this run belongs to, and how that was established.

    Three sources, strongest first, and the one used is always named:

    1. `opaque.prompt_id` inside a scorecard the run closed -- the arm stamped
       it when it opened the card, and the API handed it back verbatim.
    2. the `p<N>` tag on the scorecard the run opened. Weaker: a tag is a label,
       not a field, but it was written by the same code at the same moment.
    3. the parent run's manifest, for a salvage. A salvage is named after its
       parent *and* closes its parent's card, so the link is checked, not
       assumed.

    If none of the three answers, the field stays null and `provenance.missing`
    says so. It is never filled in from what a reader would guess.
    """
    for card in recovered_scorecards(records):
        value = (card.get("opaque") or {}).get("prompt_id")
        if value:
            return {"value": value,
                    "source": "scorecard opaque.prompt_id, read back from the API"}

    for opened in opened_scorecards(records):
        tags = (opened.get("request") or {}).get("tags") or []
        for tag in tags:
            if isinstance(tag, str) and len(tag) > 1 and tag[0] in "pP" \
                    and tag[1:].isdigit():
                return {"value": "P-" + tag[1:],
                        "source": ("the %r tag on the scorecard this run "
                                   "opened; no opaque.prompt_id was stamped, "
                                   "because the card was never closed" % tag)}

    for suffix in ("-salvage2", "-salvage"):
        if slug.endswith(suffix):
            base = slug[: -len(suffix)]
            for name in (base, base + "-aborted"):
                path = os.path.join(runs_root, name, "MANIFEST.json")
                if os.path.exists(path):
                    with open(path, encoding="utf-8") as fh:
                        value = json.load(fh).get("prompt_id")
                    if value:
                        return {"value": value,
                                "source": ("the parent run %r's manifest; this "
                                           "run closed that run's scorecard"
                                           % name)}
    return {"value": None, "source": None}


def _sha256(path: str) -> Optional[str]:
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def amend(slug: str, *, runs_root: Optional[str] = None,
          table: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Write what `amend_payload` derives. See it for what "amend" means here."""
    runs_root = runs_root or _bootstrap.path("runs")
    result = amend_payload(slug, runs_root=runs_root, table=table)
    if result is None:
        return None
    manifest, added = result
    _write(os.path.join(runs_root, slug, "MANIFEST.json"), manifest)
    return {"slug": slug, "added": added}


def amend_payload(slug: str, *, runs_root: Optional[str] = None,
                  table: Optional[Dict[str, Any]] = None):
    """Add what CLAUDE.md requires and this arm's generator never wrote.

    Existing keys are never rewritten. `utc` is added because no version of
    `archive.py` emits it. `provenance` is added because the `base_commit`
    already in the file is the commit HEAD was at when the *manifest* was
    written, which for three of these four runs is demonstrably not the commit
    the *run* ran at -- and a reader has no way to tell without the check.
    """
    runs_root = runs_root or _bootstrap.path("runs")
    path = os.path.join(runs_root, slug, "MANIFEST.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    ledger_path = os.path.join(runs_root, slug, "ledger.jsonl")
    records = read_ledger(ledger_path) if os.path.exists(ledger_path) else []
    run_id = manifest.get("run_id")
    mine = records_of(records, run_id)
    start = _run_start(mine)
    run_id = run_id or start.get("run_id")

    table = table if table is not None else armversion.scan()
    prov = provenance(mine, os.path.join(runs_root, slug), table)
    prov["mode"] = "amend"
    prov["rule"] = ("this manifest was written by `armtools/archive.py` at the "
                    "end of its run and is left exactly as it was. Only the "
                    "fields below are added.")
    located = prov["arm_version_lookup"]

    claimed = manifest.get("base_commit")
    derived = located["commits"][0] if located["verdict"] == "matched" else None
    if derived and claimed:
        agrees = derived == claimed
        check = {
            "base_commit_in_this_manifest": claimed,
            "base_commit_the_arm_version_reconstructs": derived,
            "verdict": "agree" if agrees else "DISAGREE",
            "detail": ("the commit recorded here is the one whose tree hashes "
                       "to this run's recorded arm_version"
                       if agrees else
                       "the commit recorded here is NOT the one whose tree "
                       "hashes to this run's recorded arm_version. `archive.py` "
                       "wrote `git rev-parse HEAD` at the moment the manifest "
                       "was generated, which is after the run. The derived "
                       "commit is the one whose tree the run's sources match "
                       "byte for byte -- note that it may have been created "
                       "during or just after the run, so it is the "
                       "reproducible tree rather than a commit the run was "
                       "launched from. See "
                       "`arm_version_lookup.relation_to_the_run`."),
        }
    elif claimed:
        check = {
            "base_commit_in_this_manifest": claimed,
            "base_commit_the_arm_version_reconstructs": None,
            "verdict": "UNSUPPORTED",
            "detail": ("no commit reachable from any ref reconstructs this "
                       "run's recorded arm_version, so the commit named here "
                       "cannot be the tree the run ran against. `archive.py` "
                       "wrote `git rev-parse HEAD` at manifest-writing time. "
                       "The run's actual sources were uncommitted and are not "
                       "recoverable from git."),
        }
    else:
        check = {"verdict": "no_base_commit_recorded"}
    prov["base_commit_check"] = check
    if check.get("verdict") in ("DISAGREE", "UNSUPPORTED"):
        prov["status"] = "incomplete"
        prov["missing"].append({
            "field": "base_commit (reproducible)",
            "why": check["detail"],
        })

    added = {}
    if "utc" not in manifest and start.get("ts"):
        manifest["utc"] = start["ts"]
        added["utc"] = start["ts"]
    manifest["provenance"] = prov
    added["provenance"] = prov["status"]

    closed = recovered_scorecards(mine)
    if manifest.get("scorecard") is None and not closed:
        # The scorecard this run never closed itself may have been recovered by
        # a salvage run. Point at it rather than leaving `scorecard: null` to be
        # read as "there is no number".
        pointer = _scorecard_recovered_elsewhere(run_id, runs_root, slug)
        if pointer:
            manifest["scorecard_recovered_by"] = pointer
            added["scorecard_recovered_by"] = pointer["slug"]

    return manifest, added


def _scorecard_recovered_elsewhere(run_id: Optional[str], runs_root: str,
                                   self_slug: str) -> Optional[Dict[str, Any]]:
    if not run_id:
        return None
    for name in sorted(os.listdir(runs_root)):
        if name == self_slug or not os.path.isdir(os.path.join(runs_root, name)):
            continue
        ledger = os.path.join(runs_root, name, "ledger.jsonl")
        if not os.path.exists(ledger):
            continue
        for card in recovered_scorecards(read_ledger(ledger)):
            if (card.get("opaque") or {}).get("run_id") == run_id:
                return {
                    "slug": name,
                    "card_id": card.get("card_id"),
                    "total_actions": card.get("total_actions"),
                    "total_levels_completed": card.get("total_levels_completed"),
                    "score": card.get("score"),
                    "why": ("this run died before it could close its own "
                            "scorecard, so `archive.py` recorded `scorecard: "
                            "null`. The card was closed afterwards by the "
                            "salvage run named here, whose ledger holds the "
                            "API's own count. The number was never lost, only "
                            "unreachable from this file."),
                }
    return None


def _is_backfilled(runs_root: str, slug: str) -> bool:
    path = os.path.join(runs_root, slug, "MANIFEST.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return ((json.load(fh).get("provenance") or {}).get("mode")
                    == "backfill")
    except (OSError, ValueError):
        return False


def render(payload: Dict[str, Any]) -> bytes:
    """The exact bytes a manifest gets on disk.

    Separate from `_write` so a verifier can compare what a re-derivation
    *would* produce against what is on disk, without writing anything. A verify
    step that has to mutate the archive in order to check it is not a check.
    """
    return (json.dumps(payload, indent=1, sort_keys=True, default=str)
            + "\n").encode("utf-8")


def _write(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "wb") as fh:
        fh.write(render(payload))


def survey(runs_root: Optional[str] = None) -> List[Dict[str, Any]]:
    """Every directory under `runs/`, what it is, and whether it has a manifest."""
    runs_root = runs_root or _bootstrap.path("runs")
    out = []
    for slug in sorted(os.listdir(runs_root)):
        run_dir = os.path.join(runs_root, slug)
        if not os.path.isdir(run_dir):
            continue
        ledger = os.path.join(run_dir, "ledger.jsonl")
        records = read_ledger(ledger) if os.path.exists(ledger) else []
        start = _run_start(records)
        mine = records_of(records, start.get("run_id"))
        kind = classify(slug, run_dir, mine)
        out.append({
            "slug": slug,
            "kind": kind["kind"],
            "archive_material": kind["archive_material"],
            "why": kind["why"],
            "utc": start.get("ts"),
            "has_manifest": os.path.exists(os.path.join(run_dir, "MANIFEST.json")),
            "billed_actions_from_ledger":
                quota(mine, [])["billed_actions_from_ledger"],
        })
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--slug")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--survey", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="derive everything and report, but write nothing")
    ap.add_argument("--no-amend", action="store_true",
                    help="only create missing manifests; leave existing alone")
    args = ap.parse_args(argv)

    runs_root = _bootstrap.path("runs")
    if args.survey:
        print(json.dumps(survey(runs_root), indent=1, sort_keys=True))
        return 0
    if not (args.all or args.slug):
        ap.error("one of --slug / --all / --survey")

    table = armversion.scan()
    rows = survey(runs_root)
    if args.slug:
        rows = [r for r in rows if r["slug"] == args.slug]
        if not rows:
            ap.error("no run directory %r" % args.slug)

    report = {"created": [], "amended": [], "skipped": []}
    for row in rows:
        if not row["archive_material"]:
            report["skipped"].append({"slug": row["slug"], "why": row["why"]})
            continue
        # A manifest this tool wrote is rebuilt, not amended: amending it would
        # relabel a derived manifest as an `archive.py` one and the second run
        # would not reproduce the first. Only a manifest written by the
        # generator at the end of its own run is ever amended.
        if row["has_manifest"] and not _is_backfilled(runs_root, row["slug"]):
            if args.no_amend:
                report["skipped"].append({"slug": row["slug"],
                                          "why": "has a manifest; --no-amend"})
                continue
            if args.check:
                report["amended"].append({"slug": row["slug"], "check_only": True})
                continue
            report["amended"].append(amend(row["slug"], runs_root=runs_root,
                                           table=table))
            continue
        manifest = build(row["slug"], runs_root=runs_root, table=table)
        if not args.check:
            _write(os.path.join(runs_root, row["slug"], "MANIFEST.json"), manifest)
        report["created"].append({
            "slug": row["slug"],
            "kind": manifest["classification"]["kind"],
            "prompt_id": manifest["prompt_id"],
            "base_commit": manifest["base_commit"],
            "utc": manifest["utc"],
            "provenance": manifest["provenance"]["status"],
            "missing": [m["field"] for m in manifest["provenance"]["missing"]],
            "check_only": bool(args.check),
        })
    print(json.dumps(report, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
