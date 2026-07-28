"""The normalised run record every metric reads.

Metrics never see a raw ledger.  Adapters (`battery/adapters/`) turn whatever a
source produces into the shapes below, and the metrics are written against
these alone.  That boundary is what lets the same metric definition be applied
to an A0 self-built world and to a live ARC ledger without a branch inside the
metric.

Design notes worth carrying:

* **`Step.state_key` is an opaque digest, not a state.**  Every exploration
  metric is about *state identity* — revisits, novelty, no-progress streaks —
  and identity is all they need.  Keeping the observation out of the metric
  layer also means a metric cannot accidentally learn a game's mechanics.
* **One action can return several frames.**  The live API returns a frame
  *list* per action (the Phase 1 cascade question).  `n_frames` keeps the count
  and `state_key` digests the last frame, which is the state the next action is
  chosen from.
* **Failures are steps too.**  A step that errored out has no observation but
  did consume a turn and a model call.  Dropping them would flatter the
  economy family; they are kept with `failed=True` and `state_key=None`.
* **Everything is optional.**  A source that cannot supply model calls, ground
  truth, or a theory yields a `Run` with those fields empty, and the affected
  metrics report `None` with a stated reason rather than a fabricated zero.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def digest(obj: Any) -> str:
    """A stable 16-hex-char identity for an observation."""
    body = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Step:
    """One environment interaction."""

    idx: int
    action: str                      # canonical string, for revisit keys
    state_key: Optional[str]         # digest of the resulting observation
    failed: bool = False
    n_frames: Optional[int] = None   # frames the environment returned
    level: Optional[int] = None
    won: bool = False
    # HTTP attempts the harness burned to produce this one logged step.  The
    # retry loop is collapsed into a single ledger row, so without this the
    # infrastructure's real cost is invisible: a step with `http_tries=8` cost
    # eight round trips and looks identical to one that cost one.
    http_tries: Optional[int] = None


@dataclass(frozen=True)
class Call:
    """One model invocation."""

    idx: int
    step_idx: Optional[int] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    cost_usd: Optional[float] = None
    duration_ms: Optional[int] = None
    is_error: bool = False
    # What the harness actually assembled and sent.  Kept because on a
    # one-shot-CLI arm the *token* context is constant by construction -- a
    # fresh process per turn re-reads the same fixed system prompt -- while the
    # growing history rides in the prompt body and shows up nowhere else.  E4
    # reads the token axis and finds nothing; E7 reads this one.
    prompt_chars: Optional[int] = None
    # Retry ordinal, and the decision this call belongs to.
    #
    # These are not the same axis and conflating them was a real defect in v0.
    # `bare_cc` writes one row per *attempt*: step 7 of one pilot run carries
    # three rows with three different token counts and three different prices,
    # because the model was invoked three times and billed three times.  So
    # summing cost over rows is correct -- nothing is double-counted, the money
    # was really spent.  But the economy family's shape metrics are defined per
    # *turn*, and three attempts at one step are one decision, not three.  v0
    # had only the row axis, so a run that retried looked like a run that
    # deliberated more.  `turn` is that second axis, and it is the battery's
    # answer to `INPUT_FORMAT.md` gap 5 until the ledger carries one natively.
    attempt: Optional[int] = None
    turn: Optional[int] = None

    @property
    def context_tokens(self) -> int:
        """What the model was asked to read — the thing that grows."""
        return (self.input_tokens + self.cache_read_tokens
                + self.cache_creation_tokens)


@dataclass(frozen=True)
class Concept:
    """One entry in the manual's word table."""

    name: str
    first_seen_step: Optional[int] = None    # first trace step exhibiting it
    admitted_revision: Optional[int] = None  # manual revision that admitted it
    compression_bits: Optional[int] = None   # + = the manual got shorter
    load_bearing: bool = False


@dataclass(frozen=True)
class Clause:
    """One rule, invariant or theorem in the manual."""

    name: str
    kind: str                       # rule | invariant | theorem
    # Witnesses the manual itself names.  `None` means the clause carries no
    # evidence annotation at all, which is a different fact from "no evidence"
    # and the evidence-coverage metric reports the two separately.
    evidence_transitions: Optional[int] = None
    coverage_num: Optional[int] = None
    coverage_den: Optional[int] = None
    proven: bool = False
    probe_pending: bool = False


@dataclass
class Theory:
    """The two books, as far as a ledger reader can see them.

    Only a Theoria-shaped arm has one.  `Run.theory is None` for every arm that
    keeps its world model in weights, and the epistemic family reports that as
    a structural absence rather than a score of zero — the metric is
    inapplicable, not failed.
    """

    concepts: List[Concept] = field(default_factory=list)
    clauses: List[Clause] = field(default_factory=list)
    playbook_entries: int = 0
    deadlock_theorems: int = 0
    revisions: int = 0
    probes_designed: int = 0
    probes_executable: int = 0
    replay_pairs: Optional[int] = None
    replay_agree: Optional[int] = None
    held_out_pairs: Optional[int] = None
    held_out_agree: Optional[int] = None
    # **How the held-out set was drawn.**  Two arms in this repository both
    # report a "held-out accuracy" and they do not mean the same thing: A0's
    # denominator is the 3 state-action pairs its trace happened never to
    # cover, while a0-spike's is an exhaustive enumeration of all 39960
    # well-formed (state, direction) pairs.  A ratio over 3 adversarially
    # chosen gaps and a ratio over every case in the world are not comparable,
    # and reporting both as `K2` without this field would invite exactly that
    # comparison.  Free text, surfaced in K2's support and in the report.
    held_out_frame: Optional[str] = None


@dataclass(frozen=True)
class Beat:
    """One beat of the repair loop.

    `Theoria.md` Phase 1's A2 acceptance names six, in order:
    打脸 → 定位 → 戳探 → 修订 → 重证 → 解出 (refute, locate, probe, revise,
    re-prove, solve).  A loop that stops at 修订 has not repaired anything it
    can defend; the ordering is the content of the metric.

    **`env_actions` is derived, not recorded.**  No producer in the repository
    writes a per-beat cost, so the adapter computes it from the beat's own
    evidence (an episode length, a trace that grew).  Beats that consume no
    environment actions honestly report zero -- localisation and re-proof are
    offline work -- and a zero here means "cost nothing in the environment",
    not "did not happen"; `closed` carries that.
    """

    tag: str                    # L1..L6
    name: str                   # "打脸 · refutation"
    closed: bool
    env_actions: int = 0        # environment actions this beat consumed
    note: str = ""


@dataclass
class Repair:
    """One 打脸→修复 episode: the world contradicted the manual, and then what.

    This is U4's raw material — `Theoria.md` 1.11, *被打脸后修得好吗* — and U4
    is explicitly 排座次, an ordering, and 不当证据, not evidence.  Nothing
    computed from this structure may be cited in support of a claim.

    Two shapes of repair exist in the repository and they are not comparable
    without saying which is which, so `strategy` is mandatory in practice:

    * `patch`   — locate the culprit clause, probe it, rewrite it (A2)
    * `rebuild` — re-mine the whole world from fresh evidence (a0-spike)

    A patch that costs a fifth of a rebuild has not proven the arm is better;
    it has proven that patching is cheaper than rebuilding, which was never in
    doubt.  `battery/PREDICTIONS.md` registers that confound rather than
    letting the ratio be read as an arm ranking.
    """

    episode_id: str
    trigger: str = ""                 # what refuted the manual
    strategy: str = "unknown"         # patch | rebuild | unknown
    changed_clause: Optional[str] = None
    # Did the manual notice, and after how many actions?  `detected=False` with
    # a non-None `actions_examined` is the interesting case: the change never
    # fired differently in the evidence held, so a perfectly replaying manual
    # was silently wrong.
    detected: bool = False
    detection_actions: Optional[int] = None
    actions_examined: Optional[int] = None
    beats: List[Beat] = field(default_factory=list)
    beats_required: int = 6
    # Environment actions spent repairing, against the actions the original
    # theory cost.  The ratio is the metric; both halves are kept so a reader
    # can see which one moved.
    repair_actions: Optional[int] = None
    baseline_actions: Optional[int] = None
    # Downstream damage.  A repair that invalidates nothing is a theory whose
    # theorems were not load-bearing, so this is a diagnostic, not a penalty.
    invalidated_theorems: int = 0
    theorems_before: int = 0
    # Would this repair have left a theorem standing that is now false of the
    # world, if nobody had tracked the dependency?  This is the number that
    # says what dependency tracking is *for*.
    silently_wrong_without_tracking: bool = False
    notes: Dict[str, Any] = field(default_factory=dict)

    @property
    def beats_closed(self) -> int:
        return sum(1 for b in self.beats if b.closed)

    @property
    def env_actions(self) -> int:
        return sum(b.env_actions for b in self.beats)


@dataclass
class Truth:
    """Ground truth, which only the development pile and A0 may have."""

    optimal_steps: Optional[int] = None
    # mechanism name -> {"first_seen": int, "first_used": int|None}
    mechanisms: Dict[str, Dict[str, Optional[int]]] = field(default_factory=dict)
    levels: Optional[int] = None


@dataclass
class Run:
    """One episode by one arm, normalised."""

    run_id: str
    arm: str
    source: str                      # which adapter produced this
    # What the run was *for*.  `explore` traces deliberately walk the state
    # space and must never be scored for path efficiency: A0's 275-step
    # coverage walk against a 12-step optimal plan reads as 22.9x redundant,
    # which measures the trace's purpose, not the arm's planning.  Metrics that
    # only make sense on a solve attempt declare it in `needs`.
    intent: str = "unknown"          # solve | explore | unknown
    model: Optional[str] = None
    game_id: Optional[str] = None    # None for self-built worlds
    pile: str = "synthetic"          # dev | synthetic; never sealed
    # Which campaign produced this run.  `baseline-arms/ledger.jsonl` holds
    # several campaigns in one file with nothing on the row to tell them apart,
    # and they are not interchangeable: the variance-envelope cells are
    # right-censored at ten cumulative failures by a harness rule, which is a
    # property of `bare_cc.py` and not of the arm.  Pooling them with the pilot
    # is what v0 did, and `DECISIONS.md` D-B-013 records why it stopped.
    campaign: Optional[str] = None
    steps: List[Step] = field(default_factory=list)
    calls: List[Call] = field(default_factory=list)
    theory: Optional[Theory] = None
    truth: Optional[Truth] = None
    repairs: List[Repair] = field(default_factory=list)
    notes: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok_steps(self) -> List[Step]:
        return [s for s in self.steps if not s.failed]

    def turn_costs(self) -> List[float]:
        """Cost per *decision*, in decision order.

        The economy family's shape metrics -- front-load index, convergence
        point -- are defined over turns, and a turn is a decision.  Retries of
        one decision are summed into it rather than becoming turns of their
        own, so an arm whose model call failed twice and succeeded once does
        not read as an arm that thought three times.  Total cost is unaffected;
        only its distribution over the axis is.

        Falls back to one-call-per-turn when the source carries no turn index,
        which is what every pre-`attempt` ledger row looks like.
        """
        buckets: Dict[int, float] = {}
        for i, call in enumerate(sorted(self.calls, key=lambda c: c.idx)):
            turn = call.turn if call.turn is not None else i
            buckets[turn] = buckets.get(turn, 0.0) + (call.cost_usd or 0.0)
        return [buckets[t] for t in sorted(buckets)]

    def capabilities(self) -> Dict[str, bool]:
        """What this run can and cannot be asked.

        Metrics consult this instead of guessing from empty lists, so an
        absent input is reported as `not-applicable` with a reason rather than
        silently becoming a zero.
        """
        return {
            "steps": bool(self.steps),
            "observations": any(s.state_key for s in self.steps),
            "model_calls": bool(self.calls),
            "cost": any(c.cost_usd is not None for c in self.calls),
            "theory": self.theory is not None,
            "truth": self.truth is not None,
            "optimal": bool(self.truth and self.truth.optimal_steps),
            "mechanisms": bool(self.truth and self.truth.mechanisms),
            "solve_attempt": self.intent == "solve",
            # Reached the goal, as opposed to having been *trying* to.
            # `solve_attempt` is an intent and every ledgered run declares it;
            # this is an outcome. Path efficiency may only be asked of a run
            # that arrived, because the ratio has no floor and a run that gives
            # up on step one scores better than any solve.
            "won": any(s.won for s in self.steps),
            "repairs": bool(self.repairs),
            "prompt_chars": any(c.prompt_chars for c in self.calls),
            "http_tries": any(s.http_tries is not None for s in self.steps),
            "failed_steps": any(s.failed for s in self.steps),
        }
