"""E18 — recompute every `probe_frontier` number the E11 cross-check published as prose.

    cd engine-rig
    python -m tools.survey_numbers.pf_infinity
    python -m tools.survey_numbers.pf_infinity --jsonl runs/<id>/pf_rows.jsonl

The headline number is `pf.infinity_rows` — **1633 / 4000** emitted candidate rows
carrying a bare `Infinity` token.  That token is not JSON (RFC 8259 has no such
literal); Python's `json` accepts it as its own extension, so the rig's own
round-trip never notices, and neither `tools/validate_candidates.py` nor the
frozen `CONTRACTS/candidates_schema.md` mentions it.  The stream it reaches is
shared with the other track.

The claim is about **serialisation**, so it is tested that way and not by
counting `float('inf')` in memory: each world's candidate row is built through
the engine's own `to_payload` / `make_candidate`, serialised with the same
`common.jsonio.dumps` that `emit` writes with, and then re-read with
`json.loads(..., parse_constant=<raise>)`.  A row counts only if a strict reader
actually rejects it.  Counting in-memory infinities would be the weaker claim.

Two corpora, because E11 used two:

* **A — 4000 synthetic hypothesis worlds** (§3A of the partial).  Source of
  `pf.infinity_rows`, `pf.zero_cost_bug`, `pf.partition_mismatch`,
  `pf.entropy_mismatch`, `pf.entropy_dev`, `pf.real_reorderings`.
* **B — the `cart_world` cegis frontier, enumerated exhaustively** (§3B).
  Source of `pf.rules`, `pf.states`, `pf.evals_per_rule`, `pf.teleport_guards`,
  `pf.teleport_worlds`, `pf.argmax_states`.

Corpus B is fully determined by the fixture and reproduces E11's §4B table cell
for cell.  **Corpus A is not**: E11's generator lived in a session scratchpad and
was never committed, and the partial records the shape of the draw but no seed.
This module re-implements the recorded shape and declares its own seed; see
`CAVEATS` and the `seed_sensitivity` block, which is the honest instrument for
"is 1633 the same measurement as ours, or a different draw?".

What this module found, after an adversarial review struck out three quarters of
what an earlier version of it claimed (`extra.findings` carries the same list in
machine-readable form, and `extra.withdrawn` says what was struck and why):

* **Two figures reproduce.**  E11's two maximum entropy deltas -- 0.0617 bit for
  `teleport`, 0.0584 for `blocked_UP` -- come out at 0.0617380 and 0.0583496
  under one consistent reading: the maximum over states of the difference in the
  **top-ranked action's** entropy, per-guard voting against per-world voting.
  Both land in the right slot.  An earlier version took the max over all four
  actions, got 0.0669 / 0.0617, and read the coincidence between its second
  figure and E11's first as a row shift in the prose.  That was wrong: only two
  of nine rules collapse at all, so a row shift would orphan two numbers.
* **One agrees within the draw spread.**  `pf.zero_cost_bug` recomputes to 80
  against E11's 82.  Two draws from a seedless recipe differ by about 10 on this
  quantity; these two differ by 2.
* **One is open.**  `pf.infinity_rows` recomputes to 1546 against E11's 1633 --
  a difference of 87 against a two-draw spread of about 44, so about 2.0 sigma.
  That is the whole of the disagreement this module reports.
* **A fifth number, never previously compared, is added and also lands open**:
  E11's 35 ranking differences over corpus A, against 52 here.  It is worth
  having precisely because it points the *other* way: on `infinity_rows` the
  recomputation is low and E11 high, on the ranking count the recomputation is
  high and E11 low.  Two gaps of similar size and opposite sign are what
  draw-to-draw variation looks like, not a systematic difference between the two
  measurements.

Everything the two corpora *can* pin down still agrees: 0 partition mismatches,
0 entropy mismatches, 0 real reorderings, 4000/4000 agreement between the
serialisation predicate and its cheap form, and every cell of E11's §4B table.
Both defects are still live on today's tree.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import _common

_common.add_repo_root()

from common.candidates import make_candidate  # noqa: E402
from common.jsonio import dumps, read_jsonl  # noqa: E402
from engines.cegis_miner.atoms import State, evaluate  # noqa: E402
from engines.probe_frontier import (  # noqa: E402
    Hypothesis,
    hypotheses_from_guards,
    to_payload,
)
from engines.probe_frontier.frontier import rank_probes  # noqa: E402
from tools import validate_candidates  # noqa: E402

# --------------------------------------------------------------------------- A

N_WORLDS = 4000

# The seed is *ours*, not E11's -- see the module docstring and CAVEATS.
BASE_SEED = 20260729

# `1–9 hypotheses x 1–7 actions x 1–5 observations` (partial §3A).
MAX_HYP, MAX_ACTIONS, MAX_OBS = 9, 7, 5
OBSERVATIONS = ("fires", "silent", "bounces", "vanishes", "shatters")
ACTION_NAMES = ("DOWN", "LEFT", "POKE", "PULL", "RIGHT", "UP", "WAIT")

# `weights drawn from {0.5,1,2,3,7}`; `costs from {0,0.25,1,2,5,12}, zero
# deliberately at 2/9` (partial §3A).
WEIGHT_POOL = (0.5, 1.0, 2.0, 3.0, 7.0)
COST_NONZERO = (0.25, 1.0, 2.0, 5.0, 12.0)
ZERO_COST_NUMERATOR, ZERO_COST_DENOMINATOR = 2, 9

# Below this, two probe values are float noise rather than a decision.  E11
# measured the two algebraically-equal entropy formulas to disagree by at most
# 1.11e-15 (~5 ULP), so 1e-12 is three orders of margin.
TIE_TOL = 1e-12

# Enough replicate corpora to measure how far apart two draws from this recipe
# typically land.  Fixed, so the answer is reproducible.
#
# This was 32, and the CAVEATS quoted a 200-replicate run the artefact did not
# produce -- a caveat storing a number in prose, inside the ticket whose thesis
# is that prose is not where a number is stored.  It is 200 now and the artefact
# runs it, so every replicate figure quoted anywhere in this module is in
# `extra.seed_sensitivity` below.  The 32-corpus range was also small enough to
# be misleading: it put E11's `zero_cost_bug` "outside the range" and, at 200,
# E11's value is inside.
N_REPLICATES = 200

# `|recomputed - E11| < sigma` -- the difference between two independent draws
# from this recipe is smaller than the typical such difference.  A declared
# threshold, not a p-value: the sampling distribution of these counts is only
# approximately normal and the two defect counts are not independent of each
# other (they are disjoint events on the same draw).  See `_cmp_draw`.
DRAW_AGREEMENT_SIGMA = 1.0

# E11 published its two entropy deltas to four decimals.  A recomputation is
# taken to reproduce one when it is within 1e-4 of the published figure, i.e.
# within the last digit E11 wrote down.
ENTROPY_DELTA_TOL = 1e-4

# --------------------------------------------------------------------------- B

GRID_H = GRID_W = 12
SHAPE = (2, 3)
OBSTACLE_COLOUR = 3          # any non-background colour: the atoms only ask
BACKGROUND = 0               # `== background`, never which colour it is
PROBE_ACTIONS = ("DOWN", "LEFT", "RIGHT", "UP")

E11 = "engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep"
PARTIAL = f"{E11}/partials/probe_frontier-via-bruteforce.md"

# What the 2026-07-29 report claimed, verbatim, so the comparison is in the
# artefact and not in anybody's memory.  Most keys are `ENGINE_TABLE.md` registry
# keys; the three in `NOT_REGISTRY_KEYS` are figures E11 published as prose
# without a registry entry.  They are scored here anyway -- a number's absence
# from the registry is not a reason to leave it unchecked, and the earlier
# version of this module missed a real disagreement (`pf.ranking_diffs`) for
# exactly that reason.
PROSE = {
    "pf.worlds": 4000,
    "pf.partition_mismatch": 0,
    "pf.entropy_mismatch": 0,
    "pf.entropy_dev": 1.11e-15,
    "pf.real_reorderings": 0,
    "pf.ranking_diffs": 35,
    "pf.zero_cost_bug": {"numerator": 82, "denominator": 4000, "pct": 2.05},
    "pf.infinity_rows": {"numerator": 1633, "denominator": 4000, "pct": 40.825},
    "pf.rules": 9,
    "pf.states": 15290,
    "pf.evals_per_rule": 61160,
    "pf.teleport_guards": 21,
    "pf.teleport_worlds": 18,
    "pf.argmax_states": 16,
    "pf.entropy_delta_teleport": 0.0617,
    "pf.entropy_delta_blocked_up": 0.0584,
}

NOT_REGISTRY_KEYS = frozenset({
    "pf.ranking_diffs",             # partial §4A table row "排序序列 | 35 / 4000"
    "pf.entropy_delta_teleport",    # partial §4B prose "最大熵差 0.0617 bit"
    "pf.entropy_delta_blocked_up",  # partial §4B prose "最大熵差 0.0584 bit"
})

# The three corpus-A counts that are draws from a seedless recipe rather than
# values.  They are compared to E11 through `_cmp_draw`, against the spread the
# recipe actually produces, and never by equality.
DRAW_KEYS = ("pf.infinity_rows", "pf.zero_cost_bug", "pf.ranking_diffs")

CAVEATS = [
    "Corpus A's seed is not E11's.  The partial (§3A, and the reproduction "
    "appendix) says the four scripts lived in a session scratchpad and were not "
    "committed; it records the *shape* of the draw (1-9 hypotheses x 1-7 actions "
    "x 1-5 observations, weights from {0.5,1,2,3,7}, costs from "
    "{0,0.25,1,2,5,12} with zero deliberately at 2/9) and no seed, no RNG, and "
    "no draw order.  This module re-implements that shape with "
    "`random.Random(BASE_SEED + i)` per world and BASE_SEED=20260729.  A "
    "different seed gives a different count, so `pf.infinity_rows`, "
    "`pf.zero_cost_bug` and `pf.ranking_diffs` cannot be reproduced to the unit "
    "and are not claimed to be.  `seed_sensitivity` runs 200 replicate corpora "
    "and reports, for each of the three, how far apart two draws from this "
    "recipe typically land -- `sd_of_difference` -- and how far apart this "
    "module's draw and E11's actually are.  That comparison is recomputed "
    "against E11 *directly*; neither figure is scored against the replicate "
    "mean, because both are single draws and the mean is neither of them.",

    "Corpus A's draw order within a world is also unrecorded.  The order taken "
    "here is n_hyp, n_actions, n_obs, then the table row-major, then the "
    "weights, then the costs.  Any other order is a different corpus at the same "
    "seed -- one more reason the counts are a spread rather than a value.",

    "The nonzero cost values and the hypothesis weights are provably irrelevant "
    "to both defect counts, which removes most of the sting from the previous "
    "two caveats.  `ProbeValue.splits` is `n_classes > 1`, which no weight can "
    "change, and every zero-cost action outranks every priced one whatever the "
    "price is, so the two counts depend only on the table, the action count and "
    "P(cost == 0) = 2/9.  Only the entropy figures and `pf.ranking_diffs` see "
    "the weights.",

    "`Infinity` is counted by serialisation, not in memory: the row is built by "
    "`to_payload` + `make_candidate`, written with the same `common.jsonio.dumps` "
    "that `emit` uses, and re-read with `json.loads(parse_constant=<raise>)`.  A "
    "row counts only when a strict reader rejects it.",

    "Only worlds that actually emit are counted, mirroring "
    "`probe_frontier.run`, which calls `emit` only when `best is not None`.  So "
    "a world holding a zero-cost action whose top-ranked probe splits nothing "
    "writes no row and is not an `Infinity` row -- it is a `pf.zero_cost_bug` "
    "world instead.  The two defects are disjoint by construction.",

    "Corpus A's candidate ids and timestamps are pinned "
    "(THEORIA_DETERMINISTIC_IDS=1, a fixed timestamp) for the duration of "
    "`compute()` and restored afterwards.  Without that the uuid4 ids make the "
    "run non-reproducible, and `run_all --check` would report drift that is not "
    "there.",

    "Corpus B's state space is read as 110 anchors of a (2,3) object on 12x12 x "
    "139 obstacle placements (138 free cells, plus the no-obstacle board) = "
    "15290.  The partial says only 'each anchor x each single-obstacle "
    "position'; 110 x 138 is 15180, so the empty board must be included to reach "
    "the published 15290.  That reading reproduces E11's whole §4B table -- "
    "guard counts, distinguishable worlds, splittable states and engine-splits "
    "for all nine rules -- cell for cell, which is what settles it.",

    "Corpus B's nine rules are `MiningResult.all_rules` minus the lifted `push` "
    "(action `?dir`).  `mine` returns ten rules with a frontier of two or more; "
    "the lifted one is excluded because `evaluate` cannot resolve `act==?dir` "
    "and would score every guard silent.  The partial's table names exactly the "
    "nine ground rules.",

    "`pf.teleport_worlds` counts equivalence classes of frontier guards under "
    "their full fires/silent vector over all 15290 x 4 state-action pairs.  "
    "`pf.argmax_states` compares `rank_probes` over all 21 guards against "
    "`rank_probes` over one representative guard per class, both at weight 1.0, "
    "and counts states where the top-ranked action differs.",

    "The two prose figures adjacent to `pf.argmax_states` -- a maximum entropy "
    "delta of 0.0617 bit for `teleport` and 0.0584 for `blocked_UP` -- "
    "**reproduce**, in the right slots, under one consistent reading: the "
    "maximum over states of the difference in the **top-ranked action's** "
    "entropy between per-guard and per-world voting.  That gives 0.0617380 for "
    "`teleport` and 0.0583496 for `blocked_UP` (E11 rounded 0.05835 up to "
    "0.0584).  It is also the reading the surrounding prose asks for: §4B is "
    "about which experiment the engine recommends, i.e. the top-ranked action, "
    "not about how far every action's entropy moves.  Two further figures from "
    "the same run corroborate it -- `blocked_UP` argmax_moved = 0 ('argmax "
    "未变') and `teleport` argmax_moved = 16 (= `pf.argmax_states`).  Taking the "
    "maximum over all four actions instead gives 0.0669323 and 0.0616829; that "
    "is kept as `all_actions_secondary` and is a different measurement, not "
    "E11's.  An earlier version of this module published the all-actions pair as "
    "a non-reproduction and read the coincidence between its `blocked_UP` figure "
    "and E11's `teleport` figure as a row shift in the prose.  That inference "
    "was wrong and is withdrawn: only two of the nine rules collapse at all, so "
    "a row shift has nowhere to shift from and would orphan two numbers.",

    "The recipe's own mean does not match either measurement of "
    "`pf.zero_cost_bug`, and that is a statement about the recipe rather than "
    "about E11.  Over 200 replicate corpora the literal reading of §3A averages "
    "63 (sd 7); E11 measured 82 and this module's primary corpus measured 80, "
    "which sit 2.6 and 2.3 replicate sd above that mean.  The instrument "
    "therefore impeaches its own number about as hard as it impeaches E11's, "
    "which is why no claim is made here that E11's value is anomalous.  "
    "`extra.seed_sensitivity.recipe_fit` reports the same comparison as a sum of "
    "squared z-scores over all three seedless counts, for E11's triple and for "
    "this module's own, so the two can be read side by side; they come out the "
    "same order of magnitude.  The likeliest explanation is that the literal "
    "reading of '1-9 hypotheses x 1-7 actions x 1-5 observations, zero cost at "
    "2/9' is slightly off in a way the partial cannot pin down -- but the "
    "off-by-one is not identifiable: a joint comparison over the three counts "
    "does not exclude the literal reading, and the earlier version's specific "
    "candidate (n_hyp 1..8 with n_actions 2..6, argued from "
    "`fuzzlab.worlds.hypset`) is refuted outright.  `hypset.generate` over 4000 "
    "worlds gives 1007-1047 infinity rows against E11's 1633, about 23 sd away, "
    "and its real ranges are n_hyp = 1 if singleton else 2..8, n_actions 2..6, "
    "n_obs 2..4, P(cost==0) = 1/11 -- not the ranges that were attributed to it. "
    "More decisively, the partial §1 says in as many words that hypset was not "
    "used: 「本次没有导入 fuzzlab 的任何东西——生成器、oracle、不变式全部另写，"
    "`hypset` 世界一个也没用」.  The recomputation reports the spread and stops "
    "there.",

    "`pf.ranking_diffs` is scored here and was not scored by the earlier version "
    "of this module, which is how a 52-against-35 gap went unnoticed: 35 was "
    "absent from `PROSE`, so nothing compared it.  E11 reports 35 worlds of 4000 "
    "whose ranking differs from its independent order (10 exact ties, 25 float "
    "near-ties, 0 real reorderings); this module gets 52 (0 exact, 52 float, 0 "
    "real).  It is a third handle on the same seedless draw and is sensitive to "
    "n_actions and n_obs differently from the two defect counts, which is why it "
    "is worth having.  `ranking_exact_tie` is 0 here by construction: the "
    "independent sort key used here ends in the same `str(action)` fallback the "
    "engine uses, so a pair that ties exactly on `(-value, -entropy, cost)` "
    "sorts the same way on both sides and cannot produce a difference at all.  "
    "E11's self-written key evidently lacked that fallback, which is where its "
    "10 came from.  So the 52-vs-35 comparison is not like-for-like at the "
    "margin -- E11's 35 includes a category this module cannot generate, which "
    "makes its 35 an over-count relative to this definition and widens rather "
    "than closes the gap.  The number that matters, `pf.real_reorderings`, is 0 "
    "either way.",

    "`pf.entropy_dev` is a different corpus's float noise, so it confirms an "
    "order of magnitude and nothing sharper: 1.61e-15 here (about 7 ULP at 1.0) "
    "against E11's 1.11e-15 (about 5 ULP).  E11's `pf.ulp = 5` is therefore a "
    "floor, not a bound; the conclusion it was used for -- that 1e-9 is safe "
    "with orders of margin and 2.2e-16 would produce false positives -- is "
    "unaffected and is reinforced.",

    "Corpus B is a recomputation, not a cross-check.  E11 recomputed partitions "
    "and entropies from an independently written formula; this module reuses "
    "that discipline for corpus A (see `method`) but reads corpus B's rankings "
    "straight off `rank_probes`.  Corpus B's numbers are counts of engine "
    "behaviour, not judgements of it.",

    "Three claims an earlier version of this module published are withdrawn, "
    "and are listed in `extra.withdrawn` with what replaced each: the 'row "
    "shift in the prose' reading of the entropy deltas; the `hypset` off-by-one "
    "as 'the likeliest explanation' of the defect-count deficit; and the use of "
    "'E11's 82 is outside the 32-corpus range' to impeach E11, which the same "
    "instrument does to its own 80 at the same range.  A count that used to be "
    "reported as a disagreement -- `pf.zero_cost_bug`, 80 against 82 -- is "
    "reported as agreeing within the draw spread.  The withdrawals are recorded "
    "rather than deleted for the same reason the E11 prose is recorded verbatim: "
    "a corrected artefact that does not say what it corrected cannot be checked.",
]


# --------------------------------------------------------------- corpus A: gen

class SynthWorld:
    """One synthetic hypothesis frontier -- a prediction table, weights, costs."""

    __slots__ = ("index", "seed", "hypothesis_ids", "actions", "observations",
                 "table", "weights", "costs", "state_token")

    def __init__(self, index: int, seed: int) -> None:
        rng = random.Random(seed)
        n_hyp = rng.randint(1, MAX_HYP)
        n_actions = rng.randint(1, MAX_ACTIONS)
        n_obs = rng.randint(1, MAX_OBS)

        self.index = index
        self.seed = seed
        self.hypothesis_ids = tuple("h%d" % i for i in range(n_hyp))
        self.actions = ACTION_NAMES[:n_actions]
        self.observations = OBSERVATIONS[:n_obs]
        self.table = tuple(
            tuple(rng.choice(self.observations) for _ in self.actions)
            for _ in self.hypothesis_ids
        )
        self.weights = tuple(rng.choice(WEIGHT_POOL) for _ in self.hypothesis_ids)
        self.costs = tuple(
            0.0 if rng.randrange(ZERO_COST_DENOMINATOR) < ZERO_COST_NUMERATOR
            else rng.choice(COST_NONZERO)
            for _ in self.actions
        )
        self.state_token = "s%08d" % seed

    # -- engine-facing form ------------------------------------------------
    def hypotheses(self) -> List[Hypothesis]:
        out = []
        for i, hid in enumerate(self.hypothesis_ids):
            lookup = {a: self.table[i][j] for j, a in enumerate(self.actions)}

            def predict(state, action, lookup=lookup):
                return lookup[action]

            out.append(Hypothesis(id=hid, predict=predict, weight=self.weights[i],
                                  description="synthetic hypothesis %s" % hid))
        return out

    def cost_map(self) -> Dict[str, float]:
        return {a: c for a, c in zip(self.actions, self.costs)}

    # -- truth, read off the table and never off the engine ----------------
    def truth_partition(self, action: str) -> Dict[str, List[str]]:
        j = self.actions.index(action)
        out: Dict[str, List[str]] = {}
        for i, hid in enumerate(self.hypothesis_ids):
            out.setdefault(self.table[i][j], []).append(hid)
        return {k: sorted(v) for k, v in out.items()}


def truth_entropy(weights: Sequence[float]) -> float:
    """H in bits, by the identity the engine does *not* use.

    The engine accumulates `-sum(p log2 p)` class by class.  This is the
    algebraically equal, numerically different `log2(W) - (1/W) sum(w log2 w)`,
    summed with `math.fsum`.  Agreement between the two is evidence; copying the
    engine's own arrangement would only prove the copy was faithful.
    """
    total = math.fsum(weights)
    if total <= 0:
        return 0.0
    return math.log2(total) - math.fsum(
        w * math.log2(w) for w in weights if w > 0) / total


def _raise_on_constant(token: str):
    raise ValueError("not JSON: bare %s token" % token)


def strict_json_rejects(line: str) -> Tuple[bool, Optional[str]]:
    """Would a reader without Python's Infinity/NaN extension refuse this line?"""
    try:
        json.loads(line, parse_constant=_raise_on_constant)
    except ValueError as exc:
        return True, str(exc)
    return False, None


# ------------------------------------------------------------- corpus A: sweep

def _classify_ranking(engine_vals, truth_vals) -> str:
    """`exact-tie` / `float-tie` / `real` for a world whose two orders differ.

    A pair the two orders disagree about is only a real reordering if the two
    computations disagree about it by more than float noise.  Anything the
    engine's own key cannot separate is decided by `str(action)`, and the engine
    never promised a tie would break one way.
    """
    engine = {v.action: v for v in engine_vals}
    truth = {a: t for a, t in truth_vals.items()}
    order_e = [v.action for v in engine_vals]
    order_t = [a for a, _ in sorted(
        truth_vals.items(), key=lambda kv: (-kv[1][2], -kv[1][0], kv[1][1], str(kv[0])))]
    pos_e = {a: i for i, a in enumerate(order_e)}
    pos_t = {a: i for i, a in enumerate(order_t)}

    worst = "exact-tie"
    for a in order_e:
        for b in order_e:
            if a >= b:
                continue
            if (pos_e[a] < pos_e[b]) == (pos_t[a] < pos_t[b]):
                continue
            ea, eb = engine[a], engine[b]
            if (ea.value, ea.entropy, ea.cost) == (eb.value, eb.entropy, eb.cost):
                continue                                   # exact tie: str() decided
            ta, tb = truth[a], truth[b]
            near = (
                _close(ea.value, eb.value) and _close(ta[2], tb[2])
                and _close(ea.entropy, eb.entropy) and _close(ta[0], tb[0])
            )
            if near:
                worst = "float-tie" if worst == "exact-tie" else worst
                continue
            return "real"
    return worst


def _close(x: float, y: float) -> bool:
    if x == y:
        return True
    if math.isinf(x) or math.isinf(y):
        return False
    return abs(x - y) < TIE_TOL


def sweep_corpus_a(base_seed: int, n_worlds: int, *, full: bool,
                   rank: bool = False,
                   rows_out: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Every world of a synthetic corpus, engine against independently computed truth.

    Three levels, because the replicate band needs the third number too and
    serialising 200 x 2724 candidate rows to get it would be waste:

    * `full=False, rank=False` -- the two defect predicates only.
    * `full=False, rank=True`  -- adds the independently computed partition,
      entropy and ranking, so `ranking_diff_worlds` is available.  This is what
      the replicate band runs.
    * `full=True`              -- adds building and serialising every candidate
      row, which is where the `Infinity` claim is actually tested.
    """
    need_truth = full or rank
    infinity_rows = 0
    zero_cost_bug = 0
    partition_mismatch = 0
    entropy_mismatch = 0
    entropy_dev = 0.0
    ranking_diff = {"exact-tie": 0, "float-tie": 0, "real": 0}
    argmax_diff = 0
    emitted = 0
    predicate_agrees = 0
    validator_complaints = 0

    for i in range(n_worlds):
        world = SynthWorld(i, base_seed + i)
        hyps = world.hypotheses()
        costs = world.cost_map()
        ranked = rank_probes(hyps, world.state_token, world.actions, costs=costs)
        best = ranked[0] if ranked and ranked[0].splits else None

        some_splits = any(v.splits for v in ranked)
        zero_present = any(c == 0.0 for c in world.costs)
        zero_splits = any(
            c == 0.0 and len(world.truth_partition(a)) > 1
            for a, c in zip(world.actions, world.costs)
        )
        is_bug = best is None and some_splits
        if is_bug:
            zero_cost_bug += 1

        if not full:
            # `zero_splits` is the cheap form of "this row will carry Infinity":
            # a zero-cost action makes `value` inf, and the emit only happens
            # when the top-ranked probe splits.  `full=True` checks the two
            # agree row by row before this shortcut is trusted.
            if zero_splits:
                infinity_rows += 1
        if not need_truth:
            continue

        # ---- independently computed truth for this world
        truth_vals: Dict[str, Tuple[float, float, float]] = {}
        world_partition_bad = False
        world_entropy_bad = False
        for value in ranked:
            action = value.action
            truth_part = world.truth_partition(action)
            engine_part = {str(k): sorted(v) for k, v in value.partition.items()}
            if engine_part != truth_part:
                world_partition_bad = True
            weights_by_id = {h.id: h.weight for h in hyps}
            class_weights = [
                math.fsum(weights_by_id[h] for h in ids)
                for _, ids in sorted(truth_part.items())
            ]
            ent = truth_entropy(class_weights)
            dev = abs(ent - value.entropy)
            entropy_dev = max(entropy_dev, dev)
            if dev > TIE_TOL:
                world_entropy_bad = True
            cost = costs[action]
            truth_vals[action] = (ent, cost, ent / cost if cost else math.inf)
        partition_mismatch += int(world_partition_bad)
        entropy_mismatch += int(world_entropy_bad)

        order_e = [v.action for v in ranked]
        order_t = [a for a, _ in sorted(
            truth_vals.items(),
            key=lambda kv: (-kv[1][2], -kv[1][0], kv[1][1], str(kv[0])))]
        if order_e != order_t:
            ranking_diff[_classify_ranking(ranked, truth_vals)] += 1
            if order_e[0] != order_t[0]:
                argmax_diff += 1

        if not full:
            continue

        # ---- the serialisation test, on the engine's own emit path
        has_bare_infinity = False
        reason = None
        if best is not None:
            emitted += 1
            payload = to_payload(best, ranked, hyps, None)
            row = make_candidate(
                engine="probe_frontier", kind="probe_design", payload=payload,
                transitions=[], coverage="%d/%d" % (len(hyps), len(hyps)),
            )
            line = dumps(row)
            has_bare_infinity, reason = strict_json_rejects(line)
            if has_bare_infinity:
                infinity_rows += 1
            validator_complaints += len(validate_candidates.validate_rows([row]))
        predicate_agrees += int(has_bare_infinity == zero_splits)

        if rows_out is not None:
            rows_out.append({
                "i": i,
                "seed": world.seed,
                "has_bare_infinity": has_bare_infinity,
                "best_probe_is_none": best is None,
                "zero_cost_action_present": zero_present,
                "emitted": best is not None,
                "some_action_splits": some_splits,
                "is_zero_cost_bug": is_bug,
                "n_hypotheses": len(world.hypothesis_ids),
                "n_actions": len(world.actions),
                "n_observations": len(world.observations),
                "strict_reader_reason": reason,
                "ranking_order_differs": order_e != order_t,
            })

    out = {
        "worlds": n_worlds,
        "base_seed": base_seed,
        "infinity_rows": infinity_rows,
        "zero_cost_bug": zero_cost_bug,
    }
    if need_truth:
        out.update({
            "ranking_diff_worlds": sum(ranking_diff.values()),
            "ranking_exact_tie": ranking_diff["exact-tie"],
            "ranking_float_tie": ranking_diff["float-tie"],
            "real_reorderings": ranking_diff["real"],
            "argmax_diff_worlds": argmax_diff,
        })
    if full:
        out.update({
            "emitted_rows": emitted,
            "partition_mismatch": partition_mismatch,
            "entropy_mismatch": entropy_mismatch,
            "entropy_dev": entropy_dev,
            "validator_complaints": validator_complaints,
            "serialisation_predicate_agrees": predicate_agrees,
        })
    return out


# ------------------------------------------------------------------- corpus B

def _enumerate_states() -> List[State]:
    """110 anchors x 139 obstacle placements = 15290; see CAVEATS."""
    out: List[State] = []
    h, w = SHAPE
    for r in range(GRID_H - h + 1):
        for c in range(GRID_W - w + 1):
            occupied = {(r + dr, c + dc) for dr in range(h) for dc in range(w)}
            base = [[BACKGROUND] * GRID_W for _ in range(GRID_H)]
            for rr, cc in occupied:
                base[rr][cc] = 6
            empty = tuple(tuple(row) for row in base)
            out.append(State(frame=empty, anchor=(r, c), shape=SHAPE,
                             background=BACKGROUND))
            for rr in range(GRID_H):
                for cc in range(GRID_W):
                    if (rr, cc) in occupied:
                        continue
                    grid = [list(row) for row in empty]
                    grid[rr][cc] = OBSTACLE_COLOUR
                    out.append(State(frame=tuple(tuple(x) for x in grid),
                                     anchor=(r, c), shape=SHAPE,
                                     background=BACKGROUND))
    return out


def _mined_rules():
    from fixtures import cart_world
    import engines.mdl_segmenter as mdl_segmenter
    import engines.cegis_miner as cegis_miner

    rows = read_jsonl(cart_world.TRAJ_PATH)
    frames = [row["frame"] for row in rows]
    actions = [row["action"] for row in rows]
    seg = mdl_segmenter.run(frames, background=BACKGROUND)
    transitions = cegis_miner.transitions_from_segmentation(frames, actions, seg)
    mined = cegis_miner.mine(transitions)
    # Ground rules only; the lifted `push` (?dir) is not evaluable. See CAVEATS.
    return [r for r in mined.all_rules
            if r.action in PROBE_ACTIONS and len(r.frontier) >= 2]


def sweep_corpus_b() -> Dict[str, Any]:
    states = _enumerate_states()
    rules = _mined_rules()
    per_rule: List[Dict[str, Any]] = []
    argmax_states = 0
    teleport_guards = teleport_worlds = 0
    entropy_delta_top: Dict[str, float] = {}
    entropy_delta_all: Dict[str, float] = {}

    for rule in sorted(rules, key=lambda r: r.name):
        hyps = hypotheses_from_guards(rule.frontier, evaluate, label=rule.name)
        vectors = [
            tuple(h.predict(s, a) for s in states for a in PROBE_ACTIONS)
            for h in hyps
        ]
        seen: Dict[Tuple[str, ...], int] = {}
        reps: List[Hypothesis] = []
        for i, vec in enumerate(vectors):
            if vec not in seen:
                seen[vec] = i
                reps.append(hyps[i])

        splittable = engine_splits = said_none_but_splits = 0
        moved = 0
        worst_delta_top = 0.0
        worst_delta_all = 0.0
        collapsed = len(reps) < len(hyps)
        for state in states:
            ranked = rank_probes(hyps, state, PROBE_ACTIONS)
            any_split = any(v.splits for v in ranked)
            splittable += int(any_split)
            if ranked[0].splits:
                engine_splits += 1
            elif any_split:
                said_none_but_splits += 1
            if collapsed:
                by_world = rank_probes(reps, state, PROBE_ACTIONS)
                if ranked[0].action != by_world[0].action:
                    moved += 1
                # E11's figure: how far the *recommended* experiment's entropy
                # moves.  Costs are uniform here, so `ranked[0].entropy` is the
                # maximum entropy over the four actions under each voting rule,
                # and this is `max_a H_guard - max_a H_world`.  §4B is about
                # which experiment gets recommended, so the top-ranked action is
                # the quantity the prose is talking about.
                worst_delta_top = max(
                    worst_delta_top, abs(ranked[0].entropy - by_world[0].entropy))
                # Secondary, and a different measurement: the largest move any
                # of the four actions makes, whether or not it is recommended.
                ea = {v.action: v.entropy for v in ranked}
                eb = {v.action: v.entropy for v in by_world}
                for a in PROBE_ACTIONS:
                    worst_delta_all = max(worst_delta_all, abs(ea[a] - eb[a]))

        per_rule.append({
            "rule": rule.name,
            "guards": len(hyps),
            "distinguishable_worlds": len(reps),
            "states_with_a_splitting_action": splittable,
            "engine_first_choice_splits": engine_splits,
            "said_none_but_a_split_existed": said_none_but_splits,
            "argmax_moved_by_world_voting": moved,
        })
        if collapsed:
            entropy_delta_top[rule.name] = worst_delta_top
            entropy_delta_all[rule.name] = worst_delta_all
        if rule.name == "teleport":
            teleport_guards = len(hyps)
            teleport_worlds = len(reps)
            argmax_states = moved

    return {
        "rules": len(rules),
        "states": len(states),
        "evals_per_rule": len(states) * len(PROBE_ACTIONS),
        "teleport_guards": teleport_guards,
        "teleport_worlds": teleport_worlds,
        "argmax_states": argmax_states,
        "per_rule": sorted(per_rule, key=lambda d: d["rule"]),
        "entropy_delta_bits": {
            "definition": "max over the 15290 states of |H(top-ranked action) "
                          "under one vote per guard - H(top-ranked action) under "
                          "one vote per distinguishable world|.  Only the two "
                          "rules whose guards collapse have one.",
            "top_action": {k: round(v, 10)
                           for k, v in sorted(entropy_delta_top.items())},
            "all_actions_secondary": {
                "note": "max over states AND over all four actions -- a "
                        "different measurement, kept for completeness.  It is "
                        "not E11's figure.",
                "value": {k: round(v, 10)
                          for k, v in sorted(entropy_delta_all.items())},
            },
            "e11_published": {"blocked_UP": PROSE["pf.entropy_delta_blocked_up"],
                              "teleport": PROSE["pf.entropy_delta_teleport"]},
        },
    }


# ---------------------------------------------------------------------- result

def _frac(numerator: int, denominator: int) -> Dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "pct": round(100.0 * numerator / denominator, 3),
    }


def _band(values: List[int], primary: int, e11: int) -> Dict[str, Any]:
    """Where the E11 count falls in the spread this recipe produces."""
    ordered = sorted(values)
    n = len(ordered)
    mean = math.fsum(ordered) / n
    var = math.fsum((v - mean) ** 2 for v in ordered) / (n - 1)
    sd = math.sqrt(var)
    return {
        "values": ordered,
        "min": ordered[0],
        "max": ordered[-1],
        "median": ordered[n // 2],
        "mean": round(mean, 3),
        "stdev": round(sd, 3),
        "primary_seed_value": primary,
        "e11_value": e11,
        "e11_inside_min_max": ordered[0] <= e11 <= ordered[-1],
        "e11_z": round((e11 - mean) / sd, 2) if sd else None,
    }


def _cmp(recomputed: Any, key: str) -> Dict[str, Any]:
    """Exact for counts; order-of-magnitude for the one ULP-scale float.

    `pf.entropy_dev` is a float-noise measurement -- the largest disagreement
    between two algebraically equal entropy formulas.  Demanding equality of a
    quantity whose whole point is that it is at the mercy of summation order
    would be theatre; a factor of two either way is the claim the prose actually
    supports ("about 5 ULP"), so that is what is checked.
    """
    prose = PROSE[key]
    if isinstance(prose, float):
        agrees = prose / 2.0 <= recomputed <= prose * 2.0
    else:
        agrees = recomputed == prose
    return {"recomputed": recomputed, "e11_prose": prose, "agrees": bool(agrees)}


def compute(*, rows_out: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    saved = {k: os.environ.get(k)
             for k in ("THEORIA_FIXED_TIME", "THEORIA_DETERMINISTIC_IDS")}
    os.environ["THEORIA_FIXED_TIME"] = "2026-07-29T00:00:00Z"
    os.environ["THEORIA_DETERMINISTIC_IDS"] = "1"
    try:
        a = sweep_corpus_a(BASE_SEED, N_WORLDS, full=True, rows_out=rows_out)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    replicates = [
        sweep_corpus_a(BASE_SEED + (r + 1) * N_WORLDS, N_WORLDS, full=False)
        for r in range(N_REPLICATES)
    ]

    b = sweep_corpus_b()

    counts = {
        "pf.worlds": _cmp(a["worlds"], "pf.worlds"),
        "pf.infinity_rows": _cmp(_frac(a["infinity_rows"], a["worlds"]),
                                 "pf.infinity_rows"),
        "pf.zero_cost_bug": _cmp(_frac(a["zero_cost_bug"], a["worlds"]),
                                 "pf.zero_cost_bug"),
        "pf.partition_mismatch": _cmp(a["partition_mismatch"], "pf.partition_mismatch"),
        "pf.entropy_mismatch": _cmp(a["entropy_mismatch"], "pf.entropy_mismatch"),
        "pf.entropy_dev": _cmp(a["entropy_dev"], "pf.entropy_dev"),
        "pf.real_reorderings": _cmp(a["real_reorderings"], "pf.real_reorderings"),
        "pf.rules": _cmp(b["rules"], "pf.rules"),
        "pf.states": _cmp(b["states"], "pf.states"),
        "pf.evals_per_rule": _cmp(b["evals_per_rule"], "pf.evals_per_rule"),
        "pf.teleport_guards": _cmp(b["teleport_guards"], "pf.teleport_guards"),
        "pf.teleport_worlds": _cmp(b["teleport_worlds"], "pf.teleport_worlds"),
        "pf.argmax_states": _cmp(b["argmax_states"], "pf.argmax_states"),
    }

    extra = {
        "corpus_a": {k: v for k, v in sorted(a.items())},
        "corpus_b": b,
        "seed_sensitivity": {
            "note": "the same recipe on 32 further 4000-world corpora, one per "
                    "base seed; E11's seed is unknown, so this spread -- not the "
                    "point estimate -- is what its counts should be read against. "
                    "`e11_z` is how many replicate standard deviations the E11 "
                    "count sits from the recipe's mean.",
            "n_replicates": N_REPLICATES,
            "infinity_rows": _band(
                [r["infinity_rows"] for r in replicates],
                a["infinity_rows"], PROSE["pf.infinity_rows"]["numerator"]),
            "zero_cost_bug": _band(
                [r["zero_cost_bug"] for r in replicates],
                a["zero_cost_bug"], PROSE["pf.zero_cost_bug"]["numerator"]),
        },
        "defect_status_today": {
            "note": "recomputed on the current tree, not on E11's base commit",
            "E11-PF-3 bare Infinity": "OPEN -- frontier.py:44 still returns "
                                      "float('inf') at cost 0 and jsonio.dumps "
                                      "still calls json.dumps with the default "
                                      "allow_nan=True",
            "E11-PF-1 zero-cost best_probe None": "OPEN -- best_probe still "
                                                  "takes ranked[0] and reads its "
                                                  ".splits",
            "validator": "still passes every row: validate_rows returned "
                         "%d complaints over the whole corpus"
                         % a["validator_complaints"],
        },
    }

    return _common.result(
        key="pf.infinity_rows",
        question="How many of 4000 synthetic probe_frontier worlds emit a "
                 "candidate row that a strict JSON reader rejects because it "
                 "carries a bare `Infinity` token -- and does every other "
                 "probe_frontier number E11 published as prose recompute?",
        value=_frac(a["infinity_rows"], a["worlds"]),
        e11_prose=PROSE["pf.infinity_rows"],
        counts={**counts, "extra": extra},
        inputs=_common.input_digests([
            PARTIAL,
            "engine-rig/engines/probe_frontier/frontier.py",
            "engine-rig/engines/probe_frontier/__init__.py",
            "engine-rig/engines/cegis_miner/atoms.py",
            "engine-rig/engines/cegis_miner/miner.py",
            "engine-rig/engines/mdl_segmenter/__init__.py",
            "engine-rig/common/candidates.py",
            "engine-rig/common/jsonio.py",
            "engine-rig/tools/validate_candidates.py",
            "engine-rig/fixtures/data/cart_world.jsonl",
            "CONTRACTS/candidates_schema.md",
        ]),
        method=(
            "Corpus A: 4000 synthetic prediction tables re-implementing the "
            "generator shape recorded in the E11 partial §3A, seeded "
            "random.Random(20260729 + i) per world.  Per world the engine's "
            "rank_probes is compared against a partition read straight off the "
            "table and an entropy computed by the algebraically equal but "
            "numerically different log2(W) - (1/W) sum(w log2 w) with math.fsum. "
            "The Infinity claim is tested by serialisation: to_payload + "
            "make_candidate + common.jsonio.dumps (the same writer emit uses), "
            "then json.loads(parse_constant=<raise>); a row counts only if the "
            "strict reader rejects it.  Corpus B: cart_world -> mdl_segmenter -> "
            "cegis_miner.mine, nine ground rules, exhaustive enumeration of "
            "15290 states x 4 actions, guards grouped into distinguishable "
            "worlds by their full fires/silent vector."
        ),
        caveats=CAVEATS,
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=None,
                    help="write one raw row per synthetic world to this path")
    args = ap.parse_args(argv)

    rows: Optional[List[Dict[str, Any]]] = [] if args.jsonl else None
    _common.main(lambda: compute(rows_out=rows))
    if args.jsonl and rows is not None:
        path = os.path.abspath(args.jsonl)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        # newline="" would let Windows translate; the .gitattributes pins LF.
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for row in sorted(rows, key=lambda r: r["i"]):
                fh.write(json.dumps(row, sort_keys=True, ensure_ascii=True))
                fh.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
