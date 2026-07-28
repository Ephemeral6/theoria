"""Adapter for the A0 cold-start bundle (`cold-start-a0/`, read-only).

A0 is the battery's richest fixture and its only one with a *theory*: it is a
self-built world with published ground truth, a manual in the DSL, a playbook,
per-concept compression accounts and a replay score.  The epistemic family has
nothing else to eat, so this adapter is the one that makes that family real
rather than notional.

What A0 does **not** have is model calls: the whole cold start was engines and
hand adjudication, with no LLM in the loop.  The economy family therefore
returns `not-applicable` on A0 runs, and that is the correct answer, not a
gap to paper over — see `battery/METRICS.md`.

Three things this adapter has to reconstruct rather than read:

* **A trace step's identity.**  `raw_trace.jsonl` stores the state *before* the
  action, so row `t` pairs `frame[t]` with the action taken from it and the
  last row has `action: null`.  A normalised `Step` carries the state the
  action *produced*, so step `i` gets `frame[i+1]`.
* **Mechanism annotations.**  `Theoria.md` scopes the mechanism family to
  hand-annotated games, so the annotation table lives here, next to the world
  it describes.  Only `first_used` is read from `trace_summary.json`;
  `first_seen` is recomputed by scanning frames for the mechanism's marker, so
  the delay is measured against the trace rather than asserted.
* **Manual structure.**  `theory.dsl` is parsed with a small line reader.  It
  is deliberately shallow: the battery counts clauses and reads their evidence
  annotations, and has no business understanding the DSL's semantics.  The
  grammar's owner is the theory-compiler track; if the DSL moves, this reader
  degrades to zero counts rather than crashing, and `INPUT_FORMAT.md` records
  that this coupling is the adapter's weakest joint.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from battery.guard import Piles, load_piles
from battery.model import Call, Clause, Concept, Run, Step, Theory, Truth, digest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
A0_ROOT = os.path.join(REPO, "cold-start-a0")

# Per-instance mechanism annotation.  `marker` is the board colour that makes
# the mechanism visible; `used_key` is the field in `trace_summary.json` that
# records when the arm first exploited it.  `available_from` names another
# mechanism whose first use unlocks this one — the door is not a passage until
# the button has opened it, so measuring its delay from frame 0 would charge
# the arm for time in which the mechanism did not exist.
MECHANISMS: Dict[str, Dict[str, Any]] = {
    "a0-base": {
        "portal": {"marker": 3, "used_key": "portal_transitions"},
        "button": {"marker": 7, "used_key": "button_press_transitions"},
        "door_passage": {"marker": 5, "used_key": "door_entry_transitions",
                         "available_from": "button"},
    },
    "a0-no-button": {
        "portal": {"marker": 3, "used_key": "portal_transitions"},
    },
}

INSTANCES: Dict[str, Dict[str, str]] = {
    "a0-base": {
        "trace": "raw_trace.jsonl",
        "dsl": os.path.join("theory", "theory.dsl"),
        "plan": "plan_generated.json",
        "concepts_key": "a0-base",
        "score_key": "base",
    },
    "a0-no-button": {
        "trace": "raw_trace_no_button.jsonl",
        "dsl": os.path.join("theory", "theory_no_button.dsl"),
        "plan": "plan_generated_no_button.json",
        "concepts_key": "a0-no-button",
        "score_key": "variant",
    },
}

_CLAUSE_RE = re.compile(r"^\s*(rule|invariant|theorem)\s+([A-Za-z_][\w]*)")
_COV_RE = re.compile(r"cov:\s*(\d+)\s*/\s*(\d+)")
_EV_RE = re.compile(r"ev:\s*([^\]\s]+(?:\s*,\s*[^\]\s,]+)*)")
_PLAYBOOK_RE = re.compile(r"^\s*(order|prune|heuristic|prefer)\b")


def _read_json(path: str) -> Optional[Any]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _count_evidence(text: str) -> Optional[int]:
    """Witnesses named in an `ev:` annotation, or `None` if there is none.

    `ev: t6,t16,t21` is three; `ev: t0-t274` is a range and counts as its
    span.  Ranges only appear on word-table entries, where the annotation
    means "present throughout".

    An invariant carries no `ev:` — its support is the whole trace, certified
    by an engine rather than named clause by clause.  Returning `None` rather
    than `0` keeps "unannotated" distinguishable from "unsupported"; conflating
    them would make every proven invariant look like the manual's weakest line.
    """
    match = _EV_RE.search(text)
    if not match:
        return None
    total = 0
    for token in match.group(1).split(","):
        token = token.strip()
        span = re.match(r"^t(\d+)-t(\d+)$", token)
        if span:
            total += int(span.group(2)) - int(span.group(1)) + 1
        elif re.match(r"^t\d+$", token):
            total += 1
    return total


def parse_dsl(path: str) -> Tuple[List[Clause], int]:
    """Clauses and revision number from a `.dsl` manual.

    The revision comes from a `revision N` marker in the header comment.  A
    manual that exists but carries no marker is reported as revision 1 — it was
    written once — and `battery/DECISIONS.md` records that the marker is not
    reliable enough to be the concept-birth timeline's only source.
    """
    if not os.path.exists(path):
        return [], 0
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    clauses: List[Clause] = []
    revision = 1

    # A clause's annotation bracket does not always sit on the clause's own
    # line.  Every theorem in the repository puts it on the next one:
    #
    #     theorem unsolvable_mismatch "..."
    #       [depends: push2  probe: passed]
    #
    # A strictly line-by-line reader therefore reported `proven=False` and
    # `probe_pending=False` for precisely the clauses that carry a proof or a
    # pending probe -- silently, and on every arm at once.  The clause's text
    # is now the clause line plus any following bracket-only continuation
    # lines, which is the smallest change that reads the grammar as written.
    #
    # This stays deliberately shallow.  The grammar belongs to the
    # theory-compiler track; the battery counts clauses and reads annotations
    # and understands none of the semantics.  `INPUT_FORMAT.md` records the
    # coupling as this adapter's weakest joint, and the real fix is a
    # machine-readable manifest emitted next to the DSL.
    pending: List[str] = []          # the clause being accumulated
    pending_head: Optional[re.Match] = None

    def flush() -> None:
        if pending_head is None:
            return
        text = " ".join(pending)
        cov = _COV_RE.search(text)
        clauses.append(Clause(
            name=pending_head.group(2),
            kind=pending_head.group(1),
            evidence_transitions=_count_evidence(text),
            coverage_num=int(cov.group(1)) if cov else None,
            coverage_den=int(cov.group(2)) if cov else None,
            proven="status: proven" in text or "probe: passed" in text,
            probe_pending="probe: pending" in text,
        ))

    for line in lines:
        stripped = line.strip()
        rev = re.search(r"revision\s+(\d+)", stripped)
        if rev and stripped.startswith("#"):
            revision = int(rev.group(1))
        if stripped.startswith("#"):
            continue
        match = _CLAUSE_RE.match(line)
        if match:
            flush()
            pending_head, pending = match, [line]
            continue
        # A bracket on its own line belongs to the clause above it.  Anything
        # else -- a blank line, a section header, a `when`/`then` body -- ends
        # the clause, so an annotation further down the file cannot be
        # misattributed to a clause it does not belong to.
        if pending_head is not None and stripped.startswith("["):
            pending.append(line)
            continue
        if pending_head is not None and not stripped.startswith("["):
            flush()
            pending_head, pending = None, []
    flush()
    return clauses, revision


def parse_playbook(path: str) -> Tuple[int, int]:
    """(entries, deadlock theorems).

    A deadlock theorem is a `prune` entry that concludes `dead` — a proof that
    a region of the search space can never reach the goal.  `Theoria.md`
    counts these separately from ordinary pruning because they are the
    playbook's theorem-level content.
    """
    if not os.path.exists(path):
        return 0, 0
    entries = 0
    deadlocks = 0
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.lstrip().startswith("#"):
                continue
            if _PLAYBOOK_RE.match(line):
                entries += 1
                if "dead" in line and line.lstrip().startswith("prune"):
                    deadlocks += 1
    return entries, deadlocks


def _first_frame_with_colour(frames: List[List[List[int]]],
                             colour: int) -> Optional[int]:
    for i, frame in enumerate(frames):
        for row in frame:
            if colour in row:
                return i
    return None


def _mechanisms(instance: str, frames: List[Any],
                summary: Dict[str, Any]) -> Dict[str, Dict[str, Optional[int]]]:
    spec = MECHANISMS.get(instance, {})
    used: Dict[str, Optional[int]] = {}
    for name, entry in spec.items():
        hits = summary.get(entry["used_key"]) or []
        used[name] = min(hits) if hits else None

    out: Dict[str, Dict[str, Optional[int]]] = {}
    for name, entry in sorted(spec.items()):
        seen = _first_frame_with_colour(frames, entry["marker"])
        unlock = entry.get("available_from")
        if unlock is not None:
            # The mechanism does not exist before its unlock fires.
            unlocked_at = used.get(unlock)
            seen = unlocked_at if unlocked_at is not None else None
        out[name] = {"first_seen": seen, "first_used": used[name]}
    return out


def _concepts(accounts: List[Dict[str, Any]], frames: List[Any],
              revision: int) -> List[Concept]:
    concepts: List[Concept] = []
    for entry in sorted(accounts, key=lambda e: e.get("name", "")):
        colour = entry.get("colour")
        first_seen = (_first_frame_with_colour(frames, colour)
                      if colour is not None else None)
        concepts.append(Concept(
            name=entry.get("name", "?"),
            first_seen_step=first_seen,
            admitted_revision=revision,
            compression_bits=entry.get("script_delta_bits"),
            load_bearing=bool(entry.get("load_bearing")),
        ))
    return concepts


def _held_out_frame(behavioural: Dict[str, Any],
                    held_out: Dict[str, Any]) -> Optional[str]:
    """How A0's held-out set was drawn, in one line.

    `model.py` carries `held_out_frame` precisely so that A0's K2 and
    a0-spike's K2 cannot be read as the same quantity — one is a handful of
    adversarial gaps, the other an exhaustive enumeration. This adapter never
    populated it, so K2 went unguarded until v2.1, and `REPORT_V1.md`'s claim
    that the field is carried "on every theory-bearing run" was false.

    Composed from the artefact's own counts rather than written as a constant,
    so it cannot drift away from the numbers it describes.
    """
    pairs = held_out.get("held_out_pairs")
    if not pairs:
        return None
    replayed = behavioural.get("pairs")
    states = behavioural.get("reachable_states")
    where = []
    if replayed:
        where.append("%d replayed pairs" % replayed)
    if states:
        where.append("%d reachable states" % states)
    return ("%d state-action pair(s) the full-history trace never covered%s. "
            "Adversarial gaps left by the trace, not a sample drawn from the "
            "world -- not comparable with an exhaustive enumeration."
            % (pairs, " out of " + " over ".join(where) if where else ""))


def load_a0_runs(root: str = A0_ROOT, *,
                 piles: Optional[Piles] = None) -> List[Run]:
    piles = piles or load_piles()
    artifacts = os.path.join(root, "artifacts")
    summaries = _read_json(os.path.join(artifacts, "trace_summary.json")) or {}
    accounts = _read_json(os.path.join(artifacts, "concept_accounts.json")) or {}
    scores = _read_json(os.path.join(artifacts, "score_vs_truth.json")) or {}
    engines = _read_json(os.path.join(artifacts, "engines_report.json")) or {}
    playbook_entries, deadlocks = parse_playbook(
        os.path.join(root, "theory", "playbook.dsl"))

    probes = engines.get("probes") or []
    probes_executable = sum(
        1 for p in probes
        if p.get("tier") == "executable" or p.get("executable") is True)

    runs: List[Run] = []
    for instance in sorted(INSTANCES):
        spec = INSTANCES[instance]
        rows = _read_jsonl(os.path.join(artifacts, spec["trace"]))
        if not rows:
            continue
        rows.sort(key=lambda r: r.get("t", 0))
        frames = [r["frame"] for r in rows]
        summary = summaries.get(instance, {})

        # Row t holds the state *before* its action; the step that action makes
        # is identified by the state it lands in, which is row t+1's frame.
        steps: List[Step] = []
        for i, row in enumerate(rows[:-1]):
            steps.append(Step(
                idx=i,
                action=str(row.get("action")),
                state_key=digest(frames[i + 1]),
                failed=False,
                n_frames=1,
                level=0,
                won=bool(rows[i + 1].get("win")),
            ))

        clauses, revision = parse_dsl(os.path.join(root, spec["dsl"]))
        score = (scores or {}).get(spec["score_key"], {})
        behavioural = score.get("behavioural", {})
        held_out = score.get("held_out", {})

        theory = Theory(
            concepts=_concepts(accounts.get(spec["concepts_key"], []),
                               frames, revision),
            clauses=clauses,
            playbook_entries=playbook_entries,
            deadlock_theorems=deadlocks + sum(
                1 for c in clauses
                if c.kind == "theorem" and "unsolvable" in c.name),
            revisions=revision,
            probes_designed=len(probes),
            probes_executable=probes_executable,
            replay_pairs=behavioural.get("pairs"),
            replay_agree=behavioural.get("agree"),
            held_out_pairs=held_out.get("held_out_pairs"),
            held_out_agree=held_out.get("agree"),
            held_out_frame=_held_out_frame(behavioural, held_out),
        )

        plan = _read_json(os.path.join(artifacts, spec["plan"])) or {}
        truth = Truth(
            optimal_steps=plan.get("length") if plan.get("status") == "SAT"
            else None,
            mechanisms=_mechanisms(instance, frames, summary),
            levels=1,
        )

        runs.append(Run(
            run_id=instance,
            arm="theoria_a0",
            source="cold-start-a0",
            # A0's trace is a coverage walk over the reachable state space, not
            # an attempt to win -- THEORIZE_LOG.md calls it "one exploration
            # trace". Declaring that keeps the path-efficiency metrics from
            # scoring it, which they would otherwise do at 22.9x optimal.
            intent="explore",
            model=None,
            game_id=None,           # a self-built world belongs to no pile
            pile=piles.assert_playable(None),
            steps=steps,
            calls=[],               # A0 ran no model in the loop
            theory=theory,
            truth=truth,
            notes={
                "reachable_states": summary.get("reachable_states"),
                "state_action_pairs": summary.get("state_action_pairs"),
                "plan_status": plan.get("status"),
            },
        ))
    return runs


__all__ = ["load_a0_runs", "parse_dsl", "parse_playbook", "MECHANISMS"]
