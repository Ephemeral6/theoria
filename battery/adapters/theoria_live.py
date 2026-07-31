"""Adapter for the live Theoria arm's committed leg archives (read-only).

The five arms the battery has scored so far are two controls and three
*offline* theory bundles.  The live arm — `theoria-arm/`, the one that plays
ARC-AGI-3 through the environment proxy with the two books in the loop — has
committed leg archives under `theoria-arm/runs/` since the A3 campaign began,
and this module is the extractor for that dialect.  It reads, and nothing
else: no network, no model call, no write anywhere under the archive.

**What a leg archive is.**  One leg = one proxy-ledgered episode on one
development-pile game.  The producers are the arm's own harness
(`theoria-arm/harness/`), and the join between money and turns is the arm's
archive code (`armtools/archive.turn_series`, reduced per level by A8's
`armtools/curves.py`).  Per `theoria-arm/runs/20260731T1050Z-A8/RUN_STATE.md`
the reduction is authoritative and must not be re-derived here: a second
implementation of the turn join would be a second, unlabelled definition of
E2's input — exactly the failure `figures/sources.py` exists to catch.  So
this adapter *reads* `turn_series.json` (the join, with per-turn `call_idx`)
or `curves.json` (A8's per-level reduction) and never recomputes either.

**Files read, when present** (a leg is loaded from what it has, and what it
lacks is reported as absence, never as zero):

* `ledger.jsonl`   — the proxy ledger: `run_start` / `env_step` /
  `model_call` / `run_end`.  Steps and calls come from here and only here.
* `turn_series.json` — the archive join; its rows carry `call_idx`, the exact
  billed-call-to-turn assignment.  Preferred for `Call.turn`.
* `curves.json`    — A8's reduction; carries per-turn `model_calls` counts
  and a `join_confidence`.  Used only when `turn_series.json` is absent, and
  only when its call count reconciles with the ledger's — otherwise
  `Call.turn` stays `None` and `model.Run.turn_costs()` falls back to
  one-call-per-turn, which is the documented degrade, not an error.
* `books/theory.dsl`, `books/playbook.dsl` — the two books, parsed by the
  *same* readers every other theory-bearing adapter uses (`a0.parse_dsl`,
  `a0.parse_playbook`, `a2.parse_word_table_accounts`): two parsers for one
  grammar would eventually disagree about a clause count.
* `certify.json`   — the certify desk's records; the **last** entry's cheap
  replay check is the current manual's replay score (`matched`/`transitions`).
* `probes.jsonl`   — design and result records, keyed by `probe_id`.
* `surprises.jsonl` — the seven-kind surprise record, counted into notes.

**Membership is content-based, not name-based.**  A directory is a leg of the
live arm iff its `ledger.jsonl` opens with a `run_start` whose `arm` is
`"theoria"` and whose `spend_gate.campaign` starts with
`theoria-arm:A3-campaign`.  Every such leg names a real game, and the pile
guard runs on that id before anything else is read — a sealed or unknown id
refuses the whole load (`battery.guard`, default deny), because an adapter
that quietly skipped a sealed leg would be an adapter that taught the battery
to ignore the one line it must never cross.

**A zero-step leg is refused, not scored.**  A8's own floor, inherited with
its reason: zero in a cost curve reads as "cheap", not as "did not happen".
A leg whose ledger carries no `env_step` is excluded and the exclusion is
recorded with both numbers, so "nothing played" stays distinguishable from
"the extractor lost every row".

**No ground truth, no held-out set.**  Live games have no
`ground_truth.json`, so `Run.truth` is `None` and the mechanism family
reports not-applicable — correctly.  The manual is certified against the same
live transitions it was mined from, so both held-out fields stay `None` and
`held_out_frame` says so; a live leg's K2 must never be read against A0's or
a0-spike's (see `battery/model.py` on `held_out_frame`).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from battery.adapters.a0 import parse_dsl, parse_playbook
from battery.adapters.a2 import parse_word_table_accounts
from battery.guard import Piles, load_piles
from battery.model import Call, Concept, Run, Step, Theory

HERE = os.path.dirname(os.path.abspath(__file__))          # battery/adapters
REPO = os.path.dirname(os.path.dirname(HERE))
LIVE_ROOT = os.path.join(REPO, "theoria-arm", "runs")

#: The campaign prefix that makes a leg archive this arm's.  Content-based:
#: the ledger's own `run_start` declares it, so a renamed directory neither
#: joins nor escapes the arm.
CAMPAIGN_PREFIX = "theoria-arm:A3-campaign"

ARM = "theoria"
SOURCE = "theoria-arm-live"


def _read_json(path: str) -> Optional[Any]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _run_start(path: str) -> Optional[Dict[str, Any]]:
    """The ledger's first record, iff it is a `run_start`; else None."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        first = fh.readline().strip()
    if not first:
        return None
    try:
        row = json.loads(first)
    except json.JSONDecodeError:
        return None
    return row if row.get("event") == "run_start" else None


def discover(root: str = LIVE_ROOT) -> List[Tuple[str, str]]:
    """`(slug, path)` for every live-arm leg archive under `root`, sorted.

    Sorted by slug so two walks of the same tree agree — determinism is a
    requirement here, not a nicety.
    """
    if not os.path.isdir(root):
        return []
    out: List[Tuple[str, str]] = []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if not os.path.isdir(path):
            continue
        start = _run_start(os.path.join(path, "ledger.jsonl"))
        if start is None or start.get("arm") != ARM:
            continue
        campaign = (start.get("spend_gate") or {}).get("campaign") or ""
        if campaign.startswith(CAMPAIGN_PREFIX):
            out.append((name, path))
    return out


# ------------------------------------------------------------------- steps

def _state_key(frame_hash: Optional[str]) -> Optional[str]:
    """The ledger's frame digest, trimmed to `model.digest`'s 16-hex shape.

    The ledger writes `sha256:<64 hex>`; `Step.state_key` is an opaque
    identity and every other adapter emits 16 hex chars, so the prefix is
    dropped and the digest truncated to match.  Identity is all the
    exploration family reads — a shared prefix of 16 hex chars colliding
    between two genuinely different frames is beyond the battery's care.
    """
    if not frame_hash:
        return None
    return frame_hash.split(":", 1)[-1][:16] or None


def _steps(ledger: List[Dict[str, Any]]) -> List[Step]:
    steps: List[Step] = []
    rows = [r for r in ledger if r.get("event") == "env_step"]
    rows.sort(key=lambda r: r.get("seq", 0))
    for i, row in enumerate(rows):
        http = row.get("http") or {}
        status = http.get("status")
        key = _state_key(row.get("frame_hash"))
        # A step that returned no frame gave the arm nothing to observe:
        # either the transport failed (status >= 400) or the environment
        # returned an empty frame list.  Both consumed a turn and a round
        # trip, so they stay in as failed steps rather than vanishing.
        failed = key is None or (isinstance(status, int) and status >= 400)
        steps.append(Step(
            idx=i,
            action=str(((row.get("action") or {}).get("name")) or "?"),
            state_key=None if failed else key,
            failed=failed,
            n_frames=row.get("n_frames"),
            level=row.get("level"),
            won=(row.get("state") == "WIN"),
            http_tries=http.get("attempts"),
        ))
    return steps


# ------------------------------------------------------------------- calls

def _call_usage(row: Dict[str, Any]) -> Dict[str, int]:
    """Token and cost totals summed over `response.modelUsage`.

    One CLI invocation can bill several models (a haiku subagent beside the
    opus main line); the ledger keeps them apart and the battery's `Call` is
    the invocation, so the sums are the honest per-call totals.
    """
    usage = ((row.get("response") or {}).get("modelUsage")) or {}
    out = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}
    cost = 0.0
    priced = False
    for entry in usage.values():
        out["input"] += int(entry.get("inputTokens") or 0)
        out["output"] += int(entry.get("outputTokens") or 0)
        out["cache_read"] += int(entry.get("cacheReadInputTokens") or 0)
        out["cache_creation"] += int(entry.get("cacheCreationInputTokens") or 0)
        if entry.get("costUSD") is not None:
            cost += float(entry["costUSD"])
            priced = True
    out["cost"] = cost if priced else None       # type: ignore[assignment]
    return out


def _turn_map(path: str, n_calls: int
              ) -> Tuple[Dict[int, int], Optional[str], str]:
    """`call_idx -> turn`, the join's confidence, and where the map came from.

    Reads the archive's own join rather than re-deriving it (module
    docstring).  Three outcomes, each labelled:

    * `turn_series.json` present — its rows carry `call_idx` lists, the exact
      assignment.  Confidence is the join's own `join_confidence`.
    * else `curves.json` present and its per-turn `model_calls` counts sum to
      the ledger's call count — sequential assignment in turn order, which is
      what the counts being equal licenses.
    * else — empty map; `Call.turn` stays None and `Run.turn_costs()` uses
      its documented one-call-per-turn fallback.
    """
    series = _read_json(os.path.join(path, "turn_series.json"))
    if isinstance(series, dict) and series.get("rows"):
        mapping: Dict[int, int] = {}
        for row in series["rows"]:
            for idx in (row.get("call_idx") or []):
                mapping[int(idx)] = int(row.get("turn", 0))
        conf = (series.get("join") or {}).get("join_confidence")
        return mapping, conf, "turn_series.json"

    curves = _read_json(os.path.join(path, "curves.json"))
    if isinstance(curves, dict) and curves.get("rows"):
        counts = [int(r.get("model_calls") or 0) for r in curves["rows"]]
        conf = curves.get("join_confidence")
        if sum(counts) == n_calls and n_calls > 0:
            mapping = {}
            idx = 0
            for row, n in zip(curves["rows"], counts):
                for _ in range(n):
                    mapping[idx] = int(row.get("turn", 0))
                    idx += 1
            return mapping, conf, "curves.json"
        return {}, conf, ("unjoined: curves.json counts %d billed call(s), "
                          "the ledger has %d" % (sum(counts), n_calls))
    return {}, None, "unjoined: no turn_series.json and no curves.json"


def _calls(ledger: List[Dict[str, Any]], path: str
           ) -> Tuple[List[Call], Dict[str, Any]]:
    rows = [r for r in ledger if r.get("event") == "model_call"]
    rows.sort(key=lambda r: (r.get("call_idx", 0), r.get("seq", 0)))
    mapping, confidence, source = _turn_map(path, len(rows))

    calls: List[Call] = []
    for i, row in enumerate(rows):
        idx = int(row.get("call_idx", i))
        usage = _call_usage(row)
        response = row.get("response") or {}
        http = row.get("http") or {}
        prompt = (row.get("request") or {}).get("prompt")
        calls.append(Call(
            idx=idx,
            step_idx=None,
            input_tokens=usage["input"],
            output_tokens=usage["output"],
            cache_read_tokens=usage["cache_read"],
            cache_creation_tokens=usage["cache_creation"],
            cost_usd=usage["cost"],
            duration_ms=response.get("duration_ms") or http.get("elapsed_ms"),
            is_error=bool(response.get("is_error"))
                     or (isinstance(http.get("status"), int)
                         and http["status"] >= 400),
            prompt_chars=len(prompt) if isinstance(prompt, str) else None,
            attempt=None,
            turn=mapping.get(idx),
        ))
    join_note = {
        "source": source,
        "join_confidence": confidence,
        "joined_calls": sum(1 for c in calls if c.turn is not None),
        "ledger_calls": len(calls),
    }
    return calls, join_note


# ------------------------------------------------------------------ theory

def _revisions(path: str, marker_revision: int) -> int:
    """Manual revisions: the snapshot directories, or the header marker.

    The books directory snapshots every revision (`books/snapshots/revNN-*`),
    which is a count the harness wrote as it went; the `revision N` header
    marker is the fallback, and `DECISIONS.md` already records that the
    marker alone is not reliable.  The larger of the two is the honest floor.
    """
    snapdir = os.path.join(path, "books", "snapshots")
    n = 0
    if os.path.isdir(snapdir):
        n = sum(1 for name in sorted(os.listdir(snapdir))
                if name[:3] == "rev" and
                os.path.isdir(os.path.join(snapdir, name)))
    return max(n, marker_revision)


def _replay(path: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """`(pairs, agree, entry_count)` from `certify.json`'s last record.

    The certify desk appends one record per certification; the last one is
    about the manual as it now stands, which is the manual this adapter
    parses.  `matched` is a real agreement count (the certifier replays every
    transition and counts exact matches), so — unlike A2's capped anomaly
    list — the ratio is legitimate here.
    """
    doc = _read_json(os.path.join(path, "certify.json"))
    if not isinstance(doc, list) or not doc:
        return None, None, None
    replay = (((doc[-1].get("cheap") or {}).get("checks") or {})
              .get("replay") or {})
    pairs = replay.get("transitions")
    agree = replay.get("matched")
    if pairs is None:
        return None, None, len(doc)
    return pairs, agree, len(doc)


def _probes(path: str) -> Tuple[int, int]:
    """`(designed, executed)` distinct probe ids from `probes.jsonl`.

    A design record carries the plan; a result record carries `observed`.
    Counting distinct ids keeps a probe that was designed once and executed
    once from being two probes, and a probe executed without a surviving
    design record still counts on both axes — it demonstrably existed and ran.
    """
    designed = set()
    executed = set()
    for row in _read_jsonl(os.path.join(path, "probes.jsonl")):
        pid = row.get("probe_id")
        if pid is None:
            continue
        if "design" in row or row.get("phase") == "design":
            designed.add(pid)
        if "observed" in row or row.get("verdict") is not None:
            executed.add(pid)
    return len(designed | executed), len(executed)


def _theory(path: str) -> Tuple[Optional[Theory], Dict[str, Any]]:
    dsl = os.path.join(path, "books", "theory.dsl")
    if not os.path.exists(dsl):
        return None, {"books": "absent -- this leg archived no books "
                               "directory; the epistemic family is "
                               "not-applicable, not zero"}
    clauses, marker_revision = parse_dsl(dsl)
    # The live games publish no object palette, so the word-table accounts
    # are parsed with an empty objects map: `compression_bits` and
    # `load_bearing` survive, `first_seen_step` stays None -- there are no
    # frames in the ledger to scan, only frame hashes.
    accounts = parse_word_table_accounts(dsl, {})
    revision = _revisions(path, marker_revision)
    concepts = [Concept(
        name=e["name"],
        first_seen_step=None,
        admitted_revision=revision,
        compression_bits=e.get("script_delta_bits"),
        load_bearing=bool(e.get("load_bearing")),
    ) for e in accounts]

    playbook_entries, deadlocks = parse_playbook(
        os.path.join(path, "books", "playbook.dsl"))
    deadlocks += sum(1 for c in clauses
                     if c.kind == "theorem" and "unsolvable" in c.name)
    pairs, agree, n_certs = _replay(path)
    designed, executed = _probes(path)

    theory = Theory(
        concepts=concepts,
        clauses=clauses,
        playbook_entries=playbook_entries,
        deadlock_theorems=deadlocks,
        revisions=revision,
        probes_designed=designed,
        probes_executable=executed,
        replay_pairs=pairs,
        replay_agree=agree,
        held_out_pairs=None,
        held_out_agree=None,
        held_out_frame=(
            "none: the manual is certified against the same live transitions "
            "it was mined from (certify.json, cheap replay). No held-out set "
            "exists on a live leg, so K2 here must never be compared with "
            "A0's 3-gap ratio or a0-spike's exhaustive enumeration."),
    )
    note = {
        "books": "books/theory.dsl + books/playbook.dsl",
        "certify_records": n_certs,
        "concept_source": ("word_table `compress:` annotations parsed from "
                           "books/theory.dsl; no object palette exists for a "
                           "live game, so first_seen_step is None throughout"),
    }
    return theory, note


# ------------------------------------------------------------------- the run

def _surprises(path: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in _read_jsonl(os.path.join(path, "surprises.jsonl")):
        kind = str(row.get("kind") or "unknown")
        counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items()))


def load_leg(slug: str, path: str, piles: Piles
             ) -> Tuple[Optional[Run], Optional[str]]:
    """One leg archive as a `Run`, or `(None, reason)` if it must not be one.

    The pile guard runs first and raises on a sealed or unknown id — that is
    a refusal, not an exclusion, and it must not be caught here.
    """
    ledger = _read_jsonl(os.path.join(path, "ledger.jsonl"))
    start = ledger[0] if ledger and ledger[0].get("event") == "run_start" \
        else None
    if start is None:
        return None, "ledger.jsonl does not open with a run_start record"

    game_id = start.get("game_id")
    pile = piles.assert_playable(game_id)      # raises on sealed/unknown

    upstream = str(start.get("env_upstream") or "")
    if not upstream.startswith("https://"):
        # The A3 campaign label is also worn by rig legs that played a local
        # mock upstream (`http://127.0.0.1:...`) -- gate proofs, desk proofs,
        # dry runs.  A mock leg is rig material, not arm material: its
        # environment answered from a script, so nothing it records measures
        # the arm against the world.  The guard runs *before* this refusal on
        # purpose -- a sealed id on a mock leg is still a sealed id.
        return None, ("refused: env_upstream is %r -- this leg played a "
                      "local mock, not the live environment" % upstream)

    steps = _steps(ledger)
    if not steps:
        # A8's zero-turn floor, inherited: an empty leg would write a
        # syntactically perfect row of zeros, and zero in a cost curve reads
        # as "cheap", not as "did not happen".
        return None, ("refused: 0 env_step records in a %d-record ledger -- "
                      "an empty leg is not a measurement" % len(ledger))

    calls, join_note = _calls(ledger, path)
    theory, theory_note = _theory(path)

    end = next((r for r in reversed(ledger) if r.get("event") == "run_end"),
               None)
    models = sorted({r.get("model") for r in ledger
                     if r.get("event") == "model_call" and r.get("model")})

    ledger_cost = sum(c.cost_usd for c in calls if c.cost_usd is not None)
    notes: Dict[str, Any] = {
        "slug": slug,
        "ledger_run_id": start.get("run_id"),
        "campaign_declared": (start.get("spend_gate") or {}).get("campaign"),
        "ledger_complete": end is not None,
        "outcome": (end or {}).get("outcome"),
        "levels_completed": (end or {}).get("levels_completed"),
        "turn_join": join_note,
        "ledger_cost_usd": round(ledger_cost, 9),
        "surprises": _surprises(path),
        "env_steps": len(steps),
        "model_calls": len(calls),
        "carried_books": os.path.exists(
            os.path.join(path, "books", "CARRIED.json")),
    }
    notes.update(theory_note)

    run = Run(
        run_id=slug,
        arm=ARM,
        source=SOURCE,
        intent="solve",                # the live arm plays to win, always
        model=" + ".join(models) if models else None,
        game_id=game_id,
        pile=pile,
        campaign="theoria-arm:A3-campaign-devpile",
        steps=steps,
        calls=calls,
        theory=theory,
        truth=None,                    # live games publish no ground truth
        repairs=[],
        notes=notes,
    )
    return run, None


def collect(root: str = LIVE_ROOT, *, piles: Optional[Piles] = None
            ) -> Tuple[List[Run], List[Dict[str, str]]]:
    """Every loadable live-arm leg, plus the exclusions with their reasons.

    Pure reads.  Raises on the first sealed or unknown game id rather than
    skipping it — see the module docstring.
    """
    piles = piles or load_piles()
    runs: List[Run] = []
    excluded: List[Dict[str, str]] = []
    for slug, path in discover(root):
        run, reason = load_leg(slug, path, piles)
        if run is None:
            excluded.append({"slug": slug, "reason": reason or "?"})
        else:
            runs.append(run)
    return runs, excluded


def load_theoria_live_runs(root: str = LIVE_ROOT, *,
                           piles: Optional[Piles] = None) -> List[Run]:
    """The runs alone, for callers that do not need the exclusion record."""
    return collect(root, piles=piles)[0]


__all__ = ["ARM", "CAMPAIGN_PREFIX", "LIVE_ROOT", "SOURCE", "collect",
           "discover", "load_leg", "load_theoria_live_runs"]
