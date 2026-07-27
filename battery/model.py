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
    model: Optional[str] = None
    game_id: Optional[str] = None    # None for self-built worlds
    pile: str = "synthetic"          # dev | synthetic; never sealed
    steps: List[Step] = field(default_factory=list)
    calls: List[Call] = field(default_factory=list)
    theory: Optional[Theory] = None
    truth: Optional[Truth] = None
    notes: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok_steps(self) -> List[Step]:
        return [s for s in self.steps if not s.failed]

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
        }
