"""Provenance archive: every run this track has ever paid for, findable.

`monitor/METHOD.md` rows 8 and 9 ask for two things this track had been doing
only implicitly. Row 8 wants a chain from an artifact back to the prompt that
commissioned it, the branch it ran on and the commit it ran at. Row 9 wants
failed runs archived on the same terms as successful ones, and a seed recorded
so a failure can be replayed.

Until now the evidence existed -- `out/pilot_*.json`, `out/campaign_cells.jsonl`,
a 5 MB `ledger.jsonl` -- but nothing tied a run to the ticket that ordered it,
and the only way to enumerate the runs was to know which files to open. This
builds `runs/`: one directory per run, one MANIFEST over all of them.

Three rules it follows:

  * **Originals are not moved and not rewritten.** An entry points at the
    evidence with a sha256 and a byte count; it does not copy it. The archive is
    an index over an append-only record, so anything that mutated the record to
    build the index would defeat the record.
  * **Failed runs are archived identically.** Fourteen pilot cells and three
    envelope cells, ten of the seventeen dead by the gate's own definition
    (`api_unusable` or `model_error`), plus the runs that appear in the ledger
    with no summary at all. A provenance archive that quietly held only the
    successes would misrepresent the spend, which is most of what there is to
    learn here. The MANIFEST's `counts.dead_runs` is the number to trust; this
    paragraph is prose and can drift.
  * **`seed` is null, and says why.** This arm has no seed to record: the model
    call is nondeterministic and the run id is a uuid4. Writing a number there
    to satisfy the field would be worse than the gap. `LEDGER_FORMAT.md` section
    "Replayable" already names the substitute -- the model side is not replayable
    in principle, so its inputs, outputs and usage are recorded verbatim instead
    -- and each entry points at those records.

    python -m harness.archive_runs              # build/refresh runs/
    python -m harness.archive_runs --verify     # re-hash and report drift
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

from . import interlock, ledger, summarise_pilot

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(TRACK)
RUNS_DIR = os.path.join(TRACK, "runs")
MANIFEST_PATH = os.path.join(RUNS_DIR, "MANIFEST.json")

MANIFEST_SCHEMA = "baseline-arms/runs/v1"

# Everything already on disk when P-12 opened was commissioned by an earlier
# ticket. METHOD.md row 8 wants the prompt id on the artifact; the honest value
# for work done before the archive existed is a back-annotation that says so.
RETRO_PROMPT = "retro:P-7"

# The three envelope cells P-12 actually ran, by run id. The rule used to be
# "ar25 is retro:P-7, everything else is P-12", which was true while the only
# non-ar25 envelope cells were P-12's own. The campaign has since been resumed
# and re-measured by other tickets, and that rule would stamp their cells P-12 --
# a provenance claim about who commissioned a paid run, invented by an else
# branch. Attribution is by name now, and anything the records cannot attribute
# gets UNATTRIBUTED rather than a plausible-looking id.
P12_ENVELOPE_CELLS = frozenset({
    "bare_cc-tn36-claude-haiku-4-5-20251001-62129e6a",
    "bare_cc-tn36-claude-haiku-4-5-20251001-bff3fc18",
    "bare_cc-tn36-claude-haiku-4-5-20251001-fbc7c11f",
})
UNATTRIBUTED = "retro:unattributed"

SEED_NOTE = (
    "no seed exists for this arm: the model call is nondeterministic and the "
    "run id is a uuid4. Per LEDGER_FORMAT.md the replay substitute is the "
    "verbatim model request/response/usage in the ledger; see evidence."
)


# --------------------------------------------------------------- provenance
def _git(*args: str) -> Optional[str]:
    try:
        proc = subprocess.run(("git",) + args, cwd=TRACK, capture_output=True,
                              text=True, timeout=30)
    except Exception:
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def provenance() -> Dict[str, Any]:
    dirty = _git("status", "--porcelain", "--", TRACK)
    return {
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": _git("rev-parse", "HEAD"),
        "worktree": os.path.realpath(REPO),
        "tree_dirty": bool(dirty),
    }


def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return "sha256:" + h.hexdigest()


_TRACKED: Optional[set] = None


def tracked_paths() -> set:
    """Repo-relative paths git knows about, in one call.

    Recorded per evidence pointer because it changes what the pointer means: a
    tracked file will be there on a fresh clone, a gitignored one (the pilot
    logs, the Path A payload) exists only on the machine that made it. An
    archive that did not distinguish them would promise reproducibility it
    cannot deliver.
    """
    global _TRACKED
    if _TRACKED is None:
        listing = _git("ls-files", "--full-name", "--", ":/")
        _TRACKED = set((listing or "").splitlines())
    return _TRACKED


def evidence(path: str) -> Dict[str, Any]:
    """A pointer to a source artifact: relative path, size, hash."""
    rel = os.path.relpath(path, REPO).replace(os.sep, "/")
    if not os.path.exists(path):
        return {"path": rel, "missing": True}
    kind = ("append_only" if rel in APPEND_ONLY else
            "snapshot" if rel in MUTABLE_SNAPSHOTS else "fixed")
    out = {"path": rel, "tracked": rel in tracked_paths(),
           # What the pointer promises. "fixed": these bytes, forever.
           # "append_only": these bytes are still the file's prefix.
           # "snapshot": nothing -- the file is rewritten in place.
           "stability": kind}
    if kind == "snapshot":
        # No hash and no size. Recording them would put a mutable file's
        # content into the archive's digest, so two builds either side of a
        # gate evaluation would disagree and the determinism check could not
        # tell that from a real change -- and a hash nobody can verify reads
        # like a promise.
        out["note"] = "current-state snapshot, rewritten in place; no hash recorded"
        return out
    out["bytes"] = os.path.getsize(path)
    out["sha256"] = sha256_file(path)
    return out


# ------------------------------------------------------------- run sources
def _spend(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "actions_ok": summary.get("actions_ok"),
        "actions_failed": summary.get("actions_failed"),
        "model_calls": summary.get("model_calls"),
        "http_calls_gameplay": summary.get("http_calls_gameplay"),
        "cost_usd": summary.get("cost_usd"),
        "wall_seconds": summary.get("wall_seconds"),
        "levels_completed": summary.get("levels_completed"),
    }


def _entry_from_summary(summary: Dict[str, Any], campaign: str, prompt_id: str,
                        sources: List[str]) -> Dict[str, Any]:
    return {
        "id": summary["run_id"],
        "kind": "run",
        "prompt_id": prompt_id,
        "campaign": campaign,
        "arm": summary.get("arm"),
        "game_id": summary.get("game_id"),
        "model": summary.get("model"),
        "budget": summary.get("budget"),
        "outcome": summary.get("outcome"),
        "started": summary.get("started"),
        "ended": summary.get("ended"),
        "card_id": summary.get("card_id"),
        "seed": None,
        "seed_note": SEED_NOTE,
        "spend": _spend(summary),
        "error": summary.get("error"),
        "summary": summary,
        "evidence": [evidence(os.path.join(TRACK, s)) for s in sources],
    }


def _pilot_sources(source_file: str) -> List[str]:
    sources = ["out/" + source_file, "ledger.jsonl", "probe_log.jsonl"]
    # The run log sits beside the summary, sometimes under a shortened stem
    # (pilot_ar25-0c556536.json -> pilot_ar25.log). Gitignored, so it is recorded
    # as evidence and flagged untracked rather than assumed present.
    stem = source_file[: -len(".json")]
    for candidate in ("out/%s.log" % stem, "out/%s.log" % stem.split("-")[0]):
        if os.path.exists(os.path.join(TRACK, candidate)):
            sources.append(candidate)
            break
    return sources


def pilot_entries() -> List[Dict[str, Any]]:
    """M4 pilot: 14 cells across 6 files, some dead, some superseded.

    Which cells count as superseded comes from `summarise_pilot.load_cells()`
    rather than from a rule reinvented here -- the pilot's own summary and this
    archive disagreeing about which fourteen cells there were, and which two of
    them were replaced, is exactly the kind of drift a provenance archive is
    supposed to make impossible.
    """
    kept, superseded = summarise_pilot.load_cells()
    dropped = {c["run_id"] for c in superseded}
    out = []
    for summary in kept + superseded:
        entry = _entry_from_summary(summary, "m4-pilot", RETRO_PROMPT,
                                    _pilot_sources(summary["_source"]))
        entry["superseded_by_rerun"] = summary["run_id"] in dropped
        entry["summary"] = {k: v for k, v in summary.items() if k != "_source"}
        out.append(entry)
    return out


def envelope_entries(cells_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """M5 variance envelope. All cells recorded, degraded ones included."""
    cells_path = cells_path or os.path.join(TRACK, "out", "campaign_cells.jsonl")
    if not os.path.exists(cells_path):
        return []
    out = []
    for line in open(cells_path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        cell = json.loads(line)
        if cell.get("game_id", "").startswith("ar25"):
            prompt = RETRO_PROMPT
        elif cell.get("run_id") in P12_ENVELOPE_CELLS:
            prompt = "P-12"
        else:
            prompt = UNATTRIBUTED
        entry = _entry_from_summary(
            cell, cell.get("campaign") or "phase3-variance-envelope", prompt,
            ["out/campaign_cells.jsonl", "out/campaign_gate.json",
             "ledger.jsonl", "probe_log.jsonl"])
        entry["repeat"] = cell.get("repeat")
        out.append(entry)
    return out


def schema_traces_entry() -> Optional[Dict[str, Any]]:
    """M6 Path A: a fetch, not a run. No actions, no dollars, and a guard log."""
    manifest_path = os.path.join(TRACK, "schema_traces", "MANIFEST.json")
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    files = manifest.get("files") if isinstance(manifest, dict) else None
    return {
        "id": "fetch-schema-traces-path-a",
        "kind": "fetch",
        "prompt_id": RETRO_PROMPT,
        "campaign": "m6-schema-path-a",
        "arm": None,
        "game_id": None,
        "model": None,
        "outcome": "complete",
        "seed": None,
        "seed_note": "a download has no seed; the dataset revision in "
                     "schema_traces/MANIFEST.json pins what was fetched",
        "spend": {"cost_usd": 0.0, "http_calls_gameplay": None,
                  "actions_ok": 0, "actions_failed": 0},
        "note": "development-pile directories only; the payload is gitignored "
                "under DECISIONS.md D-013 and reproduced from the hashes in "
                "its own MANIFEST",
        "file_count": len(files) if isinstance(files, (list, dict)) else None,
        "evidence": [evidence(manifest_path),
                     evidence(os.path.join(TRACK, "SCHEMA_PATH_A.md"))],
    }


def migration_entries() -> List[Dict[str, Any]]:
    """The F-16 canon lift. Not a run: no game, no dollars, no actions.

    Archived here because P-12 puts the conversion product and the migrator
    version in `runs/`, and because a derived artefact whose provenance is not
    recorded is indistinguishable from one somebody typed.
    """
    out = []
    root = os.path.join(TRACK, "runs", "_migrations")
    if not os.path.isdir(root):
        return out
    for name in sorted(os.listdir(root)):
        report_path = os.path.join(root, name, "report.json")
        if not os.path.exists(report_path):
            continue
        with open(report_path, encoding="utf-8") as fh:
            report = json.load(fh)
        produced = [p for p in (report.get("output"), report.get("sidecar")) if p]
        joins = report.get("joins") or {}
        out.append({
            "id": "migration-%s" % name,
            "kind": "migration",
            "prompt_id": "P-12",
            "campaign": "f16-ledger-canon",
            "finding": "F-16",
            "migrator": report.get("migrator"),
            "target_format": report.get("target_format"),
            "outcome": "complete" if not report.get("warnings") else "complete-with-warnings",
            "seed": None,
            "seed_note": "a migration has no seed; it is a pure function of "
                         "its inputs. `source` pins the ledger it read and "
                         "`joins` pins the probe log and run summaries it "
                         "joined against -- all three, because the output is a "
                         "function of all three and an earlier version of this "
                         "note claimed the first one pinned the whole thing",
            "spend": {"cost_usd": 0.0, "actions_ok": 0, "actions_failed": 0},
            "records": report.get("records"),
            "counts": report.get("counts"),
            "source": report.get("source"),
            "joins": joins,
            "produced": produced,
            "unfillable_fields": report.get("unfillable_fields"),
            "warnings": report.get("warnings"),
            "evidence": [evidence(os.path.join(root, name, "report.json"))]
            + [evidence(os.path.join(REPO, p["path"].replace("/", os.sep)))
               for p in produced],
        })
    return out


def ledger_only_entries(index: Dict[str, Dict[str, int]],
                        known: set) -> List[Dict[str, Any]]:
    """Runs the ledger records but no summary file names.

    The census was built from `out/pilot_*.json` and `out/campaign_cells.jsonl`,
    so a run whose summary was never written -- an interrupted invocation, a
    probe episode, anything killed before it returned -- was invisible to an
    archive whose docstring claims it holds every run this track has paid for.
    Seven such run_ids exist, costing $0.29 between them. They are archived from
    what the ledger itself carries, and marked so nobody mistakes a
    reconstruction for a summary.
    """
    out = []
    for run_id in sorted(set(index) - known):
        counts = index[run_id]
        out.append({
            "id": run_id,
            "kind": "run",
            "prompt_id": RETRO_PROMPT,
            "campaign": "unattributed",
            "arm": "bare_cc" if run_id.startswith("bare_cc-") else None,
            "game_id": None,
            "model": None,
            "outcome": "no_summary",
            "seed": None,
            "seed_note": SEED_NOTE,
            "spend": {"actions_ok": None, "actions_failed": None,
                      "model_calls": counts.get("model_call"),
                      "cost_usd": None, "http_calls_gameplay": None},
            "reconstructed_from_ledger": True,
            "note": "this run_id appears in ledger.jsonl but in no summary "
                    "file, so its outcome and spend were never written down. "
                    "The record of what it did is the ledger itself; "
                    "runs/_migrations/.../costs.sidecar.jsonl carries its "
                    "per-call dollars. Recorded rather than dropped: an "
                    "archive that silently held only the runs somebody "
                    "remembered to summarise would misstate the spend.",
            "ledger_records": counts,
            "evidence": [evidence(os.path.join(TRACK, "ledger.jsonl")),
                         evidence(os.path.join(TRACK, "probe_log.jsonl"))],
        })
    return out


def in_flight_note() -> List[Dict[str, Any]]:
    """The S1 full run is another session's and was still writing when this
    archive was built. Recording that it exists and was deliberately not
    archived is the honest move; archiving a file mid-write is not."""
    # Unconditional. An earlier version returned [] when no checkpoint was
    # visible, which made the one entry recording a deliberate omission a live
    # reading of another session's untracked directory -- it would have
    # evaporated on the next rebuild, and the archive would then have claimed
    # completeness it never had. A statement about what was left out has to
    # outlive the thing it was left out of.
    #
    # Game ids only, not their live status: the status of a running campaign
    # changes minute to minute, and putting it here made the archive's digest a
    # function of what another session happened to be doing.
    checkpoints = interlock.scan_checkpoints()      # across every worktree
    games = sorted(c.get("game_id") or os.path.basename(c["path"])
                   for c in checkpoints)
    return [{
        "id": "s1-full-run-not-archived",
        "kind": "excluded",
        "prompt_id": None,
        "reason": "the approved S1 haiku full run (BUDGET_REPORT.md 3.4) is "
                  "driven by a concurrent session and its checkpoints and "
                  "ledger shards were still being written when this archive "
                  "was built. Archiving a file mid-write would record a "
                  "hash that is true of nothing. INCIDENTS.md INC-BA-003.",
        "checkpoints": games,
        "campaigns_seen": len(games),
    }]


# ------------------------------------------------------------ ledger index
def ledger_run_index(path: Optional[str] = None) -> Dict[str, Dict[str, int]]:
    """`run_id` -> record counts. One pass, so each entry can say how much of
    the ledger is its own without anybody grepping 5 MB by hand."""
    path = path or os.path.join(TRACK, "ledger.jsonl")
    index: Dict[str, Dict[str, int]] = {}
    if not os.path.exists(path):
        return index
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = rec.get("run_id")
            if not rid:
                continue
            bucket = index.setdefault(rid, {"env_step": 0, "model_call": 0,
                                            "other": 0})
            if "action" in rec and "step_idx" in rec:
                bucket["env_step"] += 1
            elif "usage" in rec:
                bucket["model_call"] += 1
            else:
                bucket["other"] += 1
    return index


# ---------------------------------------------------------------- building
def build(prompt_id: str = "P-12") -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    entries.extend(pilot_entries())
    entries.extend(envelope_entries())
    fetch = schema_traces_entry()
    if fetch:
        entries.append(fetch)
    entries.extend(migration_entries())
    entries.extend(in_flight_note())

    index = ledger_run_index()
    for entry in entries:
        if entry["kind"] == "run":
            entry["ledger_records"] = index.get(entry["id"], {
                "env_step": 0, "model_call": 0, "other": 0})
    entries.extend(ledger_only_entries(index, {e["id"] for e in entries}))

    entries.sort(key=lambda e: (e["kind"], e.get("started") or "", e["id"]))

    os.makedirs(RUNS_DIR, exist_ok=True)
    written = []
    digest = hashlib.sha256()
    for entry in entries:
        directory = os.path.join(RUNS_DIR, entry["id"])
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, "run.json")
        payload = json.dumps(entry, indent=2, sort_keys=True,
                             ensure_ascii=True) + "\n"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
        digest.update(payload.encode("utf-8"))
        written.append(os.path.relpath(path, TRACK).replace(os.sep, "/"))

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "prompt_id": prompt_id,
        "generated_at": ledger.utcnow(),
        "provenance": provenance(),
        "counts": {
            "total": len(entries),
            "by_kind": _tally(entries, "kind"),
            "by_outcome": _tally([e for e in entries if e["kind"] == "run"],
                                 "outcome"),
            "dead_runs": sum(1 for e in entries if e["kind"] == "run"
                             and e["outcome"] in ("api_unusable", "model_error",
                                                  "no_reset_window",
                                                  "harness_error")),
        },
        "totals": {
            "cost_usd": round(sum((e.get("spend") or {}).get("cost_usd") or 0.0
                                  for e in entries), 4),
            "actions_ok": sum((e.get("spend") or {}).get("actions_ok") or 0
                              for e in entries),
            "actions_failed": sum((e.get("spend") or {}).get("actions_failed") or 0
                                  for e in entries),
        },
        "seed_policy": SEED_NOTE,
        "entries": [{"id": e["id"], "kind": e["kind"],
                     "prompt_id": e.get("prompt_id"),
                     "game_id": e.get("game_id"), "model": e.get("model"),
                     "outcome": e.get("outcome"),
                     "cost_usd": (e.get("spend") or {}).get("cost_usd"),
                     "path": "runs/%s/run.json" % e["id"]}
                    for e in entries],
        "files": written,
    }
    # A digest over the run records themselves, byte for byte, in the order they
    # were written. `generated_at` and the provenance block are deliberately
    # outside it, so re-running the archiver against an unchanged tree produces
    # the same value and a changed one is a real change.
    manifest["entries_sha256"] = "sha256:" + digest.hexdigest()

    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, indent=2, sort_keys=True,
                            ensure_ascii=True) + "\n")
    return manifest


def _tally(entries: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for e in entries:
        value = e.get(key) or "unknown"
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


# ----------------------------------------------------------------- verify
APPEND_ONLY = ("baseline-arms/ledger.jsonl", "baseline-arms/probe_log.jsonl",
               "baseline-arms/out/campaign_cells.jsonl",
               "baseline-arms/out/campaign_adjudications.jsonl")

# Rewritten in place every time the gate is evaluated: a current-state snapshot,
# not a record. Its hash in an entry is a point-in-time note, not a promise, and
# verifying it would make --verify fail every time anyone asked the gate a
# question. Existence is checked; content is not.
MUTABLE_SNAPSHOTS = ("baseline-arms/out/campaign_gate.json",)


def sha256_prefix(path: str, length: int) -> str:
    """Hash of the first `length` bytes."""
    h = hashlib.sha256()
    remaining = length
    with open(path, "rb") as fh:
        while remaining > 0:
            block = fh.read(min(1 << 20, remaining))
            if not block:
                break
            h.update(block)
            remaining -= len(block)
    return "sha256:" + h.hexdigest()


def check_evidence(ev: Dict[str, Any]) -> Optional[str]:
    """None if the pointer still holds, else what changed.

    An append-only file is verified over the prefix that existed when the
    archive was built, not over the whole file. Growth is what these files do:
    every gate evaluation appends a `campaign_gate` probe, so a whole-file hash
    made `--verify` fail on normal operation -- and it reported that with the
    same words it would use for real tampering, which is the way an integrity
    check stops being read. The prefix hash still catches the thing that
    matters: history rewritten under an append-only record.
    """
    path = os.path.join(REPO, ev["path"].replace("/", os.sep))
    if not os.path.exists(path):
        return "has since disappeared"
    if ev["path"] in MUTABLE_SNAPSHOTS:
        return None
    if ev["path"] not in APPEND_ONLY:
        return None if sha256_file(path) == ev["sha256"] else "content changed"
    size = os.path.getsize(path)
    if size < ev["bytes"]:
        return ("shrank from %d to %d bytes -- an append-only file cannot lose "
                "content" % (ev["bytes"], size))
    if sha256_prefix(path, ev["bytes"]) != ev["sha256"]:
        return ("its first %d bytes changed -- an append-only file's history "
                "must not be rewritten" % ev["bytes"])
    return None


def verify() -> Dict[str, Any]:
    """Re-check every referenced artifact and report what moved."""
    if not os.path.exists(MANIFEST_PATH):
        return {"ok": False, "problems": ["runs/MANIFEST.json does not exist"]}
    with open(MANIFEST_PATH, encoding="utf-8") as fh:
        manifest = json.load(fh)

    problems: List[str] = []
    checked = 0
    for item in manifest.get("entries", []):
        path = os.path.join(TRACK, item["path"].replace("/", os.sep))
        if not os.path.exists(path):
            problems.append("missing run record: %s" % item["path"])
            continue
        with open(path, encoding="utf-8") as fh:
            entry = json.load(fh)
        for ev in entry.get("evidence") or []:
            if ev.get("missing"):
                problems.append("%s: evidence recorded as missing: %s"
                                % (entry["id"], ev["path"]))
                continue
            checked += 1
            trouble = check_evidence(ev)
            if trouble:
                problems.append("%s: %s %s" % (entry["id"], ev["path"], trouble))
    return {"ok": not problems, "problems": problems, "evidence_checked": checked}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--prompt-id", default="P-12")
    args = ap.parse_args(argv)

    if args.verify:
        result = verify()
        print("verify: %s (%d evidence pointers checked)"
              % ("OK" if result["ok"] else "PROBLEMS", result["evidence_checked"]))
        for p in result["problems"]:
            print("  %s" % p)
        return 0 if result["ok"] else 1

    manifest = build(args.prompt_id)
    c = manifest["counts"]
    print("runs/: %d entries (%s)" % (c["total"], c["by_kind"]))
    print("  outcomes: %s" % c["by_outcome"])
    print("  dead runs archived: %d" % c["dead_runs"])
    print("  totals: $%.4f | %d actions ok | %d actions failed"
          % (manifest["totals"]["cost_usd"], manifest["totals"]["actions_ok"],
             manifest["totals"]["actions_failed"]))
    print("  %s" % manifest["entries_sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
