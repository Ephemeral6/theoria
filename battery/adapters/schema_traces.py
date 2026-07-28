"""Adapter for the upstream Schema-harness trajectories (`Path A`).

This is the control arm `Theoria.md` Phase 2 process 1 actually names. v0 and
v1 both reported that it did not exist; what does not exist is a Schema run
*we* performed, which is a different fact (`DECISIONS.md` D-B-019).

Source: `baseline-arms/schema_traces/`, two upstream collections
(`claude_fable_opus/`, `gpt_5_6_sol/`) x the four development-pile games.
The payload is gitignored — third-party data with no declared licence — so
this adapter is the only thing that reads it and only aggregate statistics
ever reach an artefact (D-B-020).

Four decisions worth carrying, because each one refuses a number rather than
inventing one:

* **The environment layer is one arm; the model-call layer is two.**
  `events.jsonl` is the same schema in both collections, down to the `kind`
  vocabulary, so every step-derived metric pools legitimately.  The session
  logs are a Claude Code transcript and a Codex rollout log respectively —
  unrelated formats — and only the first records token usage at all.  So calls
  are read from one collection and the report says the call-based metrics rest
  on half the arm.  Pooling two differently-defined call counts would have
  produced a comparable-looking number that is not comparable.

* **`events.jsonl` and the session logs do not join, so no turn axis is
  invented.**  Upstream anonymised ids with independent per-file counters:
  `tool_started.call_id` and the session-side tool ids share a surface form and
  have an *empty* intersection in all eight run directories.  A timestamp or
  ordinal alignment could be manufactured, and `Call.step_idx` would then carry
  a guess with the same type as a fact.  It is left `None`.

* **No cost field exists anywhere in the corpus**, under any spelling.  So
  `Call.cost_usd` stays `None` and the economy family's money metrics report
  `not-applicable` on this arm rather than zero.

* **`Step.failed` has no source and is not synthesised from `dead`.**  `dead`
  is a *game* state — the arm lost — while `failed` throughout this battery
  means the environment refused the action, which is an infrastructure event.
  Conflating them would hand this arm `bare_cc`'s 29% API failure rate as if it
  were a capability difference, in the one comparison where that confound does
  the most damage.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterator, List, Optional, Tuple

from battery.guard import Piles, load_piles
from battery.model import Call, Run, Step, Theory, Truth, digest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCHEMA_ROOT = os.path.join(REPO, "baseline-arms", "schema_traces")

# The payload is gitignored, which has a consequence worth stating rather than
# discovering: **a git worktree does not contain it.**  Ignored files are not
# checked out into a linked worktree, so an agent working on a branch in
# `.../theoria-wt-x/` sees `baseline-arms/` fully populated except for this
# directory, and the adapter silently finds nothing.
#
# `THEORIA_SCHEMA_TRACES` is the override.  Resolution order is explicit
# argument, then the environment, then the repo-relative default -- and
# whichever one answers is recorded in the run manifest, because "which copy of
# an untracked 87 MB payload did this number come from" is exactly the question
# a reader cannot otherwise ask.
SCHEMA_ROOT_ENV = "THEORIA_SCHEMA_TRACES"

ARM = "schema_repro"

# Collections, and whether their session log records token usage.  `False` is
# not a defect to work around: the Codex rollout log has no token fields at
# all, and a zero would be a fabrication.
COLLECTIONS: Tuple[Tuple[str, bool], ...] = (
    ("claude_fable_opus", True),
    ("gpt_5_6_sol", False),
)

# A trailing float on a run directory name is an upstream *score*.  It is
# stripped before the name becomes a `run_id`, because a run id travels into
# every artefact and a score has no business riding along in one -- see
# `PREDICTIONS.md` v2's seal declaration, which had to declare this leak.
_SCORE_SUFFIX = re.compile(r"_\d+(?:\.\d+)?$")


def _run_id(collection: str, dirname: str) -> str:
    return "%s/%s" % (collection, _SCORE_SUFFIX.sub("", dirname))


def _read_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def _canonical_action(row: Dict[str, Any]) -> str:
    """A stable action identity.

    Coordinates are part of it: clicking two different cells is two different
    actions, and every exploration metric keys transitions on this string.
    """
    action = row.get("action")
    x, y = row.get("x"), row.get("y")
    if x is None and y is None:
        return "ACTION%s" % action
    return "ACTION%s(%s)" % (action, json.dumps({"x": x, "y": y},
                                                sort_keys=True,
                                                separators=(",", ":")))


def _n_frames(row: Dict[str, Any]) -> Optional[int]:
    """Environment ticks this action produced.

    `ticks` is absent on some rows and `null` on others, and `ticks_truncated`
    marks the rows where upstream cut the list short.  A truncated count is a
    floor rather than a count, so it is reported as unknown instead of as a
    number that would silently understate the cascade.
    """
    if row.get("ticks_truncated"):
        return None
    ticks = row.get("ticks")
    return len(ticks) if isinstance(ticks, list) else None


def load_steps(events_path: str) -> Tuple[List[Step], Dict[str, Any]]:
    """Steps from `events.jsonl`, plus what the run's own bookend events say.

    `seq` is the sort key and nothing else: it does not start at zero and is
    not contiguous.  `step_index` is contiguous from zero and is the index.
    """
    rows = sorted(_read_jsonl(events_path), key=lambda r: r.get("seq", 0))

    steps: List[Step] = []
    meta: Dict[str, Any] = {"mispredictions": 0, "turns": 0,
                            "fallbacks": 0, "truncated_ticks": 0}
    for row in rows:
        kind = row.get("kind")
        if kind == "action_taken":
            if row.get("ticks_truncated"):
                meta["truncated_ticks"] += 1
            steps.append(Step(
                idx=int(row.get("step_index", len(steps))),
                action=_canonical_action(row),
                state_key=digest(row.get("grid")) if row.get("grid") else None,
                # No source, and deliberately not synthesised from `dead`.
                failed=False,
                n_frames=_n_frames(row),
                level=row.get("level"),
                won=bool(row.get("win")),
                http_tries=None,
            ))
        elif kind == "turn_started":
            meta["turns"] += 1
        elif kind == "turn_fallback":
            meta["fallbacks"] += 1
        elif kind == "model_mispredicted":
            # The only recorded world-model refutation in this corpus.  Counted
            # because it is the closest thing here to A2's 打脸 beat, and
            # emphatically *not* turned into a `Repair`: there is no located
            # clause, no probe, no revision and no re-proof, so a Repair built
            # from it would report a loop that upstream never ran.
            meta["mispredictions"] += 1
        elif kind == "run_finished":
            meta["final_state"] = row.get("state")
            meta["levels_completed"] = row.get("levels")
            meta["win_levels"] = row.get("win_levels")
            meta["has_world_model"] = row.get("has_world_model")
            meta["upstream_transitions"] = row.get("transitions")
    steps.sort(key=lambda s: s.idx)
    return steps, meta


def load_calls(session_path: str) -> Tuple[List[Call], Dict[str, Any]]:
    """Model calls from a Claude Code transcript.

    **Grouped by `requestId`, not one per record.**  One API request emits
    several `assistant` records in every one of the four claude run
    directories, so counting records would over-count invocations and would
    add the same `usage` block in several times.  Records with no `requestId`
    are their own group, which is what a transcript entry written outside a
    request looks like.

    `turn` is the group's ordinal.  That is the decision axis this arm can
    support: there is no join to `events.jsonl` (see the module docstring), so
    a turn here means "the nth model request", not "the nth environment step".
    The two coincide only if the arm acted once per request, which is not
    checkable from this material and is not assumed.
    """
    groups: List[str] = []
    by_request: Dict[str, Dict[str, Any]] = {}
    meta = {"assistant_records": 0, "api_errors": 0}

    for i, row in enumerate(_read_jsonl(session_path)):
        if row.get("type") != "assistant":
            continue
        meta["assistant_records"] += 1
        message = row.get("message") or {}
        usage = message.get("usage") or {}
        key = row.get("requestId") or "norequest-%d" % i
        if key not in by_request:
            by_request[key] = {"usage": usage, "error": False}
            groups.append(key)
        if row.get("isApiErrorMessage") or row.get("error"):
            by_request[key]["error"] = True

    calls: List[Call] = []
    for turn, key in enumerate(groups):
        usage = by_request[key]["usage"]
        is_error = bool(by_request[key]["error"])
        if is_error:
            meta["api_errors"] += 1
        calls.append(Call(
            idx=turn,
            # No join exists; a guessed step index would be a fact-shaped
            # guess.  Left None on purpose.
            step_idx=None,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            cache_read_tokens=int(usage.get("cache_read_input_tokens") or 0),
            cache_creation_tokens=int(
                usage.get("cache_creation_input_tokens") or 0),
            # No cost field exists anywhere in this corpus, under any spelling.
            cost_usd=None,
            duration_ms=None,
            is_error=is_error,
            prompt_chars=None,
            attempt=None,
            turn=turn,
        ))
    return calls, meta


def load_run(collection: str, run_dir: str, *, has_usage: bool,
             piles: Piles) -> Optional[Run]:
    events = os.path.join(run_dir, "events.jsonl")
    manifest = os.path.join(run_dir, "run.json")
    if not os.path.exists(events) or not os.path.exists(manifest):
        return None

    with open(manifest, "r", encoding="utf-8") as fh:
        head = json.load(fh)

    game_id = head.get("game_id")
    # The guardrail, before a single grid is digested.
    pile = piles.assert_playable(game_id)

    steps, meta = load_steps(events)

    calls: List[Call] = []
    call_meta: Dict[str, Any] = {}
    session = os.path.join(run_dir, "sessions", "session-001.jsonl")
    if has_usage and os.path.exists(session):
        calls, call_meta = load_calls(session)

    notes: Dict[str, Any] = {
        "upstream_collection": collection,
        "upstream_effort": os.path.basename(run_dir).split("_")[1]
                           if "_" in os.path.basename(run_dir) else None,
        "max_actions": head.get("max_actions"),
        "env_rows": len(steps),
        "call_rows": len(calls),
        "records_token_usage": has_usage,
        # Why several metric families will report not-applicable here, stated
        # in the run rather than left for a reader to infer from empty lists.
        "absent_by_construction": sorted([
            "cost — no cost field exists in this corpus",
            "failed steps — `dead` is a game state, not a refused action",
            "http_tries — upstream logs no retry count",
            "theory — the world model is Python source, not a record",
            "optimal_steps — no ARC game has a known shortest plan",
            "mechanisms — no per-game mechanism annotation exists",
        ] + ([] if has_usage else
             ["token usage — this collection's session log has no token "
              "fields"])),
    }
    notes.update(meta)
    notes.update(call_meta)

    return Run(
        run_id=_run_id(collection, os.path.basename(run_dir)),
        arm=ARM,
        source="schema_traces",
        intent="solve",           # upstream was trying to win
        model=head.get("model"),
        game_id=game_id,
        pile=pile,
        campaign="upstream-%s" % collection,
        steps=steps,
        calls=calls,
        # No manual, no concepts, no clauses.  The world model in these run
        # directories is Python source and prose; reading it would be a
        # separate decision with its own contamination argument, and a Theory
        # assembled from it would not be the one upstream reasoned with.
        theory=None,
        truth=Truth(levels=head.get("win_levels")),
        notes=notes,
    )


def resolve_root(root: Optional[str] = None) -> str:
    """Where the untracked payload actually is.  See `SCHEMA_ROOT_ENV`."""
    if root is not None:
        return root
    return os.environ.get(SCHEMA_ROOT_ENV) or SCHEMA_ROOT


def load_schema_runs(root: Optional[str] = None, *,
                     piles: Optional[Piles] = None) -> List[Run]:
    """Every upstream Schema run on disk, or nothing if the payload is absent.

    The payload is gitignored by `baseline-arms/.gitignore`, so on a fresh
    clone — or in any git worktree — this returns `[]` and the battery
    recomputes without a Schema arm, exactly as v1 did. That is a recorded
    property rather than a silent degradation: `discriminate_arms()` reports
    `available: false` and every artefact names the arms that were present.
    """
    piles = piles or load_piles()
    root = resolve_root(root)
    if not os.path.isdir(root):
        return []

    runs: List[Run] = []
    for collection, has_usage in COLLECTIONS:
        base = os.path.join(root, collection)
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            run_dir = os.path.join(base, name)
            if not os.path.isdir(run_dir):
                continue
            run = load_run(collection, run_dir, has_usage=has_usage,
                           piles=piles)
            if run is not None:
                runs.append(run)
    return sorted(runs, key=lambda r: r.run_id)
