"""E18: recompute the `zero_space` numbers the E11 cross-check published as prose.

The headline is **102** -- the number of vectors `zero_space` published as
conservation laws that a *legal transition of the same world* falsifies:

    zerospace.py:282   differences = [encoded[t] ^ encoded[t+1] for t in ...]
    zerospace.py:284   basis       = gf2.null_space(differences, len(features))

The null space is taken over the differences the **sampled trajectory happened
to produce**.  Quantify instead over every `(reachable state, operation)` pair
the world admits and 102 of those vectors, in 13 of 200 `parityworld` worlds,
have odd increment on some transition.

**Read the caveats before quoting 102.**  It is *not* a defect count.
`engine-rig/DECISIONS.md` **D-003** pre-registers this exact mechanism -- fewer
observed differences means a larger recovered invariant space, "still sound" --
three months before the cross-check measured it.  E11's own `CROSSCHECK.md:92`
retracts the defect reading and keeps the number.  This module recomputes the
*count*; it does not re-open the adjudication, and CAVEATS[0] says so in the
artefact so that a bare `102` cannot be read the way the original was.

Sources under audit, both in
`engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/`:
`partials/zero_space-via-lp.md` (Chinese) and `ADVERSARIAL-zero_space.md`.

Run:

    cd engine-rig
    python -m tools.survey_numbers.zero_space_span
    python -m tools.survey_numbers.zero_space_span \
        --jsonl runs/20260730T120000Z-E18/raw/zero_space_span.jsonl

Takes about 25 s: 200 worlds, each fully enumerated (up to 512 reachable states
and 3072 transitions), plus a census of the committed `theoria-arm` candidate
streams.  The committed counts are
`runs/20260730T120000Z-E18/counts/zs.falsified_laws.json`, written by
`tools.survey_numbers.run_all`.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from tools.survey_numbers import _common

_common.add_repo_root()

from engines.zero_space import zerospace as ZS                 # noqa: E402
from fixtures import pair_flip                                 # noqa: E402
from fuzzlab.oracles import gf2 as ORACLE                      # noqa: E402
from fuzzlab.worlds import parityworld as PW                   # noqa: E402

# ------------------------------------------------------------------ the corpus
# Stated verbatim in the partial, section "方法与规模": "N = **200** 个
# `parityworld` 世界，种子 **1..200 连续**，在看任何结果之前选定，未挑种子."
SEED_LO = 1
SEED_HI = 200
N_WORLDS = SEED_HI - SEED_LO + 1

# The partial's own reachability budget: "200/200 个世界的可达集均 <= 512 状态,
# 无一触及 400k 上限".  Kept so that a corpus change that blows past it is
# reported rather than silently truncated.
REACHABILITY_BUDGET = 400_000

G50T = "theoria-arm/runs/20260728T015354Z-g50t-first-contact/candidates.jsonl"
ARM_ROOT = "theoria-arm"

E11 = "engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep"

INPUTS = [
    "engine-rig/engines/zero_space/__init__.py",
    "engine-rig/engines/zero_space/README.md",
    "engine-rig/engines/zero_space/gf2.py",
    "engine-rig/engines/zero_space/zerospace.py",
    "engine-rig/fixtures/data/pair_flip.jsonl",
    "engine-rig/fixtures/pair_flip.py",
    f"{E11}/ADVERSARIAL-zero_space.md",
    f"{E11}/CROSSCHECK.md",
    f"{E11}/partials/zero_space-via-lp.md",
    "fuzzlab/oracles/gf2.py",
    "fuzzlab/prng.py",
    "fuzzlab/worlds/common.py",
    "fuzzlab/worlds/parityworld.py",
]

# The partial's 13-world table, transcribed so the comparison is in the artefact.
# Columns: seed, k, n_cells, "轨迹步数", eng_dim, true_dim, falsified.
# NOTE the fourth column: the partial's header says *steps* and its values are
# *state counts* (= steps + 1).  See CAVEATS -- the values agree 13/13 under the
# state-count reading and 0/13 under the step reading, so the header is what is
# wrong, not the data.
E11_DIRTY_TABLE: List[List[int]] = [
    [12, 4, 6, 18, 11, 10, 1],
    [21, 4, 8, 12, 23, 18, 9],
    [35, 4, 7, 26, 15, 14, 1],
    [60, 4, 8, 9, 25, 21, 22],
    [64, 4, 6, 17, 12, 10, 6],
    [80, 4, 8, 16, 23, 18, 10],
    [86, 4, 7, 7, 22, 13, 18],
    [92, 3, 7, 7, 17, 13, 13],
    [98, 3, 5, 7, 9, 7, 4],
    [111, 3, 4, 4, 9, 6, 7],
    [126, 4, 4, 8, 9, 5, 6],
    [142, 3, 4, 13, 7, 6, 2],
    [156, 3, 6, 13, 11, 8, 3],
]


# ----------------------------------------------------------- the verdict, local
# The single judgement this module makes about a law is here, in three lines of
# stdlib, exactly as the partial's `increment_is_even`.  It does not go through
# `engines/zero_space/gf2.py` (the code under audit) and it does not go through
# `fuzzlab/oracles/gf2.py` (used only for the `true_dim` column), so the 102 is
# independent of both.

def increment_is_even(law_vector: int, difference: int) -> bool:
    """Does the integer potential `P(x) = |supp(a) & x|` change by an even amount?

    A GF(2) law `a` is conserved across `x -> y` iff `a . (x ^ y) = 0`, i.e. iff
    the support meets the flipped bits an even number of times.
    """
    return bin(law_vector & difference).count("1") % 2 == 0


# ------------------------------------------------------------------- one world

def _survey_world(seed: int) -> Dict[str, Any]:
    """Everything the eleven figures need from one `parityworld`, in one pass."""
    world = PW.generate(seed)
    colors = world.colors
    k = len(colors)

    result = ZS.analyse(world.states, colors)
    features = result.features
    n_features = result.n_features
    index = {(f.cell, f.color): i for i, f in enumerate(features)}

    def encode(state: Sequence[str]) -> int:
        vector = 0
        for cell, color in enumerate(state):
            vector |= 1 << index[(cell, color)]
        return vector

    # -- every legal transition, not just the sampled ones --------------------
    # `apply_operation` has no precondition (verified by the adversarial review
    # by reading it), so the transition relation is exactly
    # reachable-states x operations.  BFS in operation-declaration order; the
    # counts below do not depend on the order, and everything is sorted anyway.
    start = tuple(world.states[0])
    seen: Set[Tuple[str, ...]] = {start}
    queue = collections.deque([start])
    transitions: List[Tuple[Tuple[str, ...], int]] = []
    over_budget = False
    while queue:
        state = queue.popleft()
        encoded_state = encode(state)
        for operation in world.spec.operations:
            nxt = tuple(PW.apply_operation(list(state), operation, colors))
            transitions.append((state, encoded_state ^ encode(nxt)))
            if nxt not in seen:
                if len(seen) >= REACHABILITY_BUDGET:
                    over_budget = True
                    continue
                seen.add(nxt)
                queue.append(nxt)

    differences = sorted({d for _, d in transitions})
    true_basis = ORACLE.null_space(differences, n_features)

    # -- the falsification verdict, law by law --------------------------------
    on_trajectory = {tuple(s) for s in world.states}
    groups: Dict[int, int] = {}
    for i, feature in enumerate(features):
        groups[feature.cell] = groups.get(feature.cell, 0) | (1 << i)

    n_falsified = 0
    n_falsified_cell_local = 0
    n_falsified_cell_local_subset = 0
    first_witness_on_trajectory = 0
    any_witness_on_trajectory = 0
    n_cell_local = 0
    n_cell_local_subset = 0
    n_cell_local_subset_in_span = 0

    structural = ZS.cell_local_subspace(features)

    for law in result.laws:
        if law.scope == ZS.CELL_LOCAL:
            n_cell_local += 1
            cells = {f.cell for f in law.support()}
            # `local_laws` only ever emits subsets of one cell's feature group.
            assert len(cells) == 1, "cell_local law spanning cells: %r" % (cells,)
            whole_group = law.vector == groups[next(iter(cells))]
            if not whole_group:
                n_cell_local_subset += 1
                if ORACLE.in_span(law.vector, structural, n_features):
                    n_cell_local_subset_in_span += 1

        witnesses = [state for state, diff in transitions
                     if not increment_is_even(law.vector, diff)]
        if not witnesses:
            continue
        n_falsified += 1
        # The partial counted "反例起点在轨迹上" off the *first* witness in its
        # enumeration order and got 91; the adversarial review counted "some
        # witness is on the trajectory" and got 100.  Both are computed.
        first_witness_on_trajectory += witnesses[0] in on_trajectory
        any_witness_on_trajectory += any(w in on_trajectory for w in witnesses)
        if law.scope == ZS.CELL_LOCAL:
            n_falsified_cell_local += 1
            cell = next(iter({f.cell for f in law.support()}))
            if law.vector != groups[cell]:
                n_falsified_cell_local_subset += 1

    # -- the consistency control: same span from the same evidence ------------
    # The oracle takes differences against state 0, the engine takes consecutive
    # differences.  Different rows, provably the same span -- which is why this
    # agreeing 200/200 is a control and not evidence (ADVERSARIAL section 4).
    encoded = [encode(s) for s in world.states]
    oracle_basis = ORACLE.null_space([x ^ encoded[0] for x in encoded[1:]], n_features)
    same_span = ORACLE.same_span(oracle_basis, result.basis, n_features)

    return {
        "seed": seed,
        "flavour": world.spec.flavour,
        "k": k,
        "n_cells": world.spec.n_cells,
        "n_operations": len(world.spec.operations),
        "n_features": n_features,
        "n_trajectory_states": len(world.states),
        "n_trajectory_transitions": result.n_transitions,
        "n_reachable_states": len(seen),
        "n_legal_transitions": len(transitions),
        "n_distinct_differences": len(differences),
        "engine_dimension": result.dimension,
        "true_dimension": len(true_basis),
        "n_laws": len(result.laws),
        "n_falsified": n_falsified,
        "same_span": same_span,
        # not part of the jsonl contract, dropped before it is written
        "_extra": {
            "over_budget": over_budget,
            "n_cell_local": n_cell_local,
            "n_cell_local_subset": n_cell_local_subset,
            "n_cell_local_subset_in_span": n_cell_local_subset_in_span,
            "n_falsified_cell_local": n_falsified_cell_local,
            "n_falsified_cell_local_subset": n_falsified_cell_local_subset,
            "first_witness_on_trajectory": first_witness_on_trajectory,
            "any_witness_on_trajectory": any_witness_on_trajectory,
            "n_global": len(result.global_laws()),
            "n_undetermined": len(result.undetermined_laws()),
            "truncated_cells": list(result.truncated_cells),
        },
    }


# --------------------------------------------------------------- Fixture B leg

def _fixture_b() -> Dict[str, Any]:
    """`zs.fixtureB_features` / `zs.fixtureB_transitions`, from the fixture."""
    rows = [json.loads(line) for line in
            Path(pair_flip.TRAJ_PATH).read_text(encoding="utf-8").splitlines()
            if line.strip()]
    states = [row["state"] for row in rows]
    result = ZS.analyse(states, list(pair_flip.COLORS))
    return {
        "n_states": len(states),
        "n_features": result.n_features,
        "n_transitions": result.n_transitions,
        "dimension": result.dimension,
        "difference_rank": result.difference_rank,
        "n_cell_local": len(result.cell_local_laws()),
        "n_global": len(result.global_laws()),
    }


# ------------------------------------------------------------------ g50t leg
# A census of what was *published*, not a check that any of it holds.  Deciding
# that needs reachability enumeration over the live ARC game, which is not
# possible offline -- both E11 sources say so and this module inherits the gap.
# `g50t-5849a774` is a development-pile game (`arc-recon/data/piles.json`), so
# reading its artefacts is permitted; nothing here is written outside engine-rig.

def _zs_rows(path: Path) -> List[Dict[str, Any]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if obj.get("engine") == "zero_space":
            out.append(obj)
    return out


def _g50t() -> Dict[str, Any]:
    root = _common.repo_root()
    path = root / G50T
    if not path.exists():                                     # pragma: no cover
        return {"present": False}

    rows = _zs_rows(path)
    groups: Dict[Tuple[int, int, int, str], int] = collections.Counter()
    for obj in rows:
        payload = obj["payload"]
        groups[(len(payload["features"]), payload["space_dimension"],
                payload["difference_rank"], obj["evidence"]["coverage"])] += 1
    # Ties broken by the sorted key, so the modal group is stable.
    modal = min(sorted(groups), key=lambda key: (-groups[key], key))
    n_features, dimension, rank, coverage = modal
    coverage_full = all(
        obj["evidence"]["coverage"].split("/")[0]
        == obj["evidence"]["coverage"].split("/")[1] for obj in rows)

    # The whole `theoria-arm` territory, which is where CROSSCHECK.md's 2911 lives.
    arm_total = 0
    arm_by_file: Dict[str, int] = {}
    arm_modal_group = 0
    for candidate_path in sorted((root / ARM_ROOT).rglob("candidates*.jsonl")):
        found = _zs_rows(candidate_path)
        if not found:
            continue
        rel = candidate_path.resolve().relative_to(root).as_posix()
        arm_by_file[rel] = len(found)
        arm_total += len(found)
        for obj in found:
            payload = obj["payload"]
            if (len(payload["features"]), payload["space_dimension"],
                    payload["difference_rank"]) == (n_features, dimension, rank):
                arm_modal_group += 1

    return {
        "present": True,
        "rows": len(rows),
        "coverage_full": coverage_full,
        "modal_n_features": n_features,
        "modal_space_dimension": dimension,
        "modal_difference_rank": rank,
        "modal_transitions": int(coverage.split("/")[1]),
        "modal_rows": groups[modal],
        "modal_text": "%d features, %d transitions, difference_rank %d, %d-dim law space"
                      % (n_features, int(coverage.split("/")[1]), rank, dimension),
        "groups": [{"n_features": g[0], "space_dimension": g[1],
                    "difference_rank": g[2], "coverage": g[3], "rows": groups[g]}
                   for g in sorted(groups, key=lambda key: (-groups[key], key))],
        "scope_counts": dict(sorted(collections.Counter(
            obj["payload"]["scope"] for obj in rows).items())),
        "arm_rows": arm_total,
        "arm_rows_in_modal_group": arm_modal_group,
        "arm_by_file": dict(sorted(arm_by_file.items())),
    }


# ------------------------------------------------------------------ assembling

def _ratio(numerator: int, denominator: int) -> Dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "pct": round(100.0 * numerator / denominator, 4) if denominator else None,
        # The literal the `ENGINE_TABLE.md` registry publishes, so a re-pointed
        # probe can read one field instead of re-rendering the fraction.
        "text": "%d/%d" % (numerator, denominator),
    }


def _row(recomputed: Any, prose: Any, registry_key: Optional[str] = None,
         **extra: Any) -> Dict[str, Any]:
    """One table row.

    `registry_key` is the `ENGINE_TABLE.md` key this row can re-point.  `None`
    means the number is real but the registry does not publish it.
    """
    row: Dict[str, Any] = {
        "recomputed": recomputed,
        "e11_prose": prose,
        "agrees": recomputed == prose,
        "registry_key": registry_key,
    }
    row.update(extra)
    return row


def compute(jsonl_path: Optional[str | Path] = None) -> Dict[str, Any]:
    rows = [_survey_world(seed) for seed in range(SEED_LO, SEED_HI + 1)]
    rows.sort(key=lambda r: r["seed"])
    extra = [r["_extra"] for r in rows]

    def total(field: str) -> int:
        return sum(int(e[field]) for e in extra)

    falsified = sum(r["n_falsified"] for r in rows)
    dirty = [r for r in rows if r["n_falsified"]]
    k2 = [r for r in rows if r["k"] == 2]
    k3 = [r for r in rows if r["k"] >= 3]
    same_span = sum(1 for r in rows if r["same_span"])

    engine_dim = sum(r["engine_dimension"] for r in rows)
    true_dim = sum(r["true_dimension"] for r in rows)

    fixture_b = _fixture_b()
    g50t = _g50t()

    recomputed_table = [
        [r["seed"], r["k"], r["n_cells"], r["n_trajectory_states"],
         r["engine_dimension"], r["true_dimension"], r["n_falsified"]]
        for r in dirty
    ]

    composition = collections.Counter((r["flavour"], r["k"]) for r in rows)

    counts: Dict[str, Any] = {
        # --- the eleven the ticket names -------------------------------------
        "zs.worlds": _row(
            len(rows), N_WORLDS, registry_key="zs.worlds",
            note="parityworld seeds %d..%d, contiguous, chosen before any result"
                 % (SEED_LO, SEED_HI)),
        "zs.same_span": _row(
            _ratio(same_span, len(rows)), _ratio(200, 200),
            registry_key="zs.same_span",
            note="control, not evidence: the oracle's rows (x_t ^ x_0) and the "
                 "engine's (x_t ^ x_{t+1}) provably span the same subspace"),
        "zs.falsified_laws": _row(
            falsified, 102, registry_key="zs.falsified_laws",
            note="NOT a defect count -- see caveats[0]; D-003 pre-registers the "
                 "mechanism and calls it sound"),
        "zs.dirty_worlds": _row(
            len(dirty), 13, registry_key="zs.dirty_worlds",
            seeds=[r["seed"] for r in dirty]),
        "zs.k2_clean": _row(
            _ratio(sum(1 for r in k2 if r["n_falsified"]), len(k2)), _ratio(0, 135),
            registry_key="zs.k2_clean"),
        "zs.k3_dirty": _row(
            _ratio(sum(1 for r in k3 if r["n_falsified"]), len(k3)), _ratio(13, 65),
            registry_key="zs.k3_dirty"),
        "zs.cell_local_laws": _row(
            total("n_cell_local"), 1271, registry_key="zs.cell_local_laws"),
        "zs.cell_local_subsets": _row(
            total("n_cell_local_subset"), 329, registry_key="zs.cell_local_subsets",
            note="cell_local laws whose support is a *proper* subset of the "
                 "cell's feature group; the rest are whole-group encoding laws"),
        "zs.cell_local_in_span": _row(
            total("n_cell_local_subset_in_span"), 0,
            registry_key="zs.cell_local_in_span",
            note="of the proper-subset ones, how many lie in the engine's own "
                 "cell_local_subspace(); zero means none of them is an encoding law"),
        "zs.fixtureB_features": _row(
            fixture_b["n_features"], 16, registry_key="zs.fixtureB_features",
            note="8 cells x 2 colours; recomputed from fixtures/data/pair_flip.jsonl, "
                 "not from the probe_frontier partial the registry regexes"),
        "zs.fixtureB_transitions": _row(
            fixture_b["n_transitions"], 40, registry_key="zs.fixtureB_transitions"),

        # --- the g50t group CROSSCHECK.md:102-107 quotes ----------------------
        "g50t.space_dimension": _row(
            g50t.get("modal_space_dimension"), 366, registry_key=None,
            note="modal published group on the live g50t run (development pile)"),
        "g50t.n_features": _row(
            g50t.get("modal_n_features"), 370, registry_key=None),
        "g50t.difference_rank": _row(
            g50t.get("modal_difference_rank"), 4, registry_key=None),
        "g50t.arithmetic_holds": _row(
            g50t.get("modal_space_dimension")
            == g50t.get("modal_n_features") - g50t.get("modal_difference_rank"),
            True, registry_key=None,
            note="366 = 370 - 4 is arithmetic, not a bug (CROSSCHECK.md:105)"),
        "arm.zero_space_rows": _row(
            g50t.get("arm_rows"), 2911, registry_key=None,
            note="CROSSCHECK.md:104 calls these '2911 such rows'; only "
                 "%s of them are in the 370/366/4 group -- see caveats"
                 % g50t.get("arm_rows_in_modal_group")),

        # --- registry keys the same census already covers ---------------------
        "zs.g50t_rows": _row(
            g50t.get("rows"), 1821, registry_key="zs.g50t_rows"),
        "zs.g50t_modal_transitions": _row(
            g50t.get("modal_transitions"), 6,
            registry_key="zs.g50t_modal_transitions"),
        "zs.g50t_worst": _row(
            g50t.get("modal_text"),
            "370 features, 6 transitions, difference_rank 4, 366-dim law space",
            registry_key="zs.g50t_worst"),
        "zs.g50t_coverage_full": _row(
            g50t.get("coverage_full"), True, registry_key="zs.g50t_coverage_full"),

        # --- supporting figures from the same loop, also prose-only in E11 ----
        "support.engine_dim_total": _row(
            engine_dim, 1832, registry_key=None,
            note="the partial's '1832 vs 1788'"),
        "support.true_dim_total": _row(true_dim, 1788, registry_key=None),
        "support.no_reverse_direction": _row(
            all(r["engine_dimension"] >= r["true_dimension"] for r in rows), True,
            registry_key=None,
            note="engine dimension is >= the true dimension in every world; the "
                 "disagreement is one-directional, which is what 'still sound' means"),
        "support.cell_local_whole_group": _row(
            total("n_cell_local") - total("n_cell_local_subset"), 942,
            registry_key=None),
        "support.falsified_cell_local": _row(
            total("n_falsified_cell_local"), 51, registry_key=None),
        "support.falsified_cell_local_from_subsets": _row(
            _ratio(total("n_falsified_cell_local_subset"),
                   total("n_falsified_cell_local")), _ratio(51, 51),
            registry_key=None,
            note="every falsified cell_local law is a proper-subset one; no "
                 "whole-group encoding law was ever falsified"),
        "support.witness_on_trajectory_first": _row(
            total("first_witness_on_trajectory"), 91, registry_key=None,
            note="the partial's 91 -- first counterexample in enumeration order"),
        "support.witness_on_trajectory_any": _row(
            total("any_witness_on_trajectory"), 100, registry_key=None,
            note="the adversarial review's correction: 100, not 91; both "
                 "reproduce, and the review's diagnosis of the gap is confirmed"),
        "support.max_reachable_states": _row(
            max(r["n_reachable_states"] for r in rows), 512, registry_key=None),
        "support.worlds_over_budget": _row(
            sum(1 for e in extra if e["over_budget"]), 0, registry_key=None,
            note="reachability budget %d states; the partial reports no world "
                 "touching it" % REACHABILITY_BUDGET),
        "support.composition": _row(
            [[flavour, k, composition[(flavour, k)]]
             for flavour, k in sorted(composition)],
            [["free", 2, 36], ["free", 3, 34], ["free", 4, 31], ["planted", 2, 99]],
            registry_key=None,
            note="the partial's 'planted/k=2 99, free/k=2 36, free/k=3 34, "
                 "free/k=4 31'"),
        "support.dirty_world_table": _row(
            recomputed_table, E11_DIRTY_TABLE, registry_key=None,
            columns=["seed", "k", "n_cells", "n_trajectory_states",
                     "engine_dimension", "true_dimension", "n_falsified"],
            note="the partial's 13-row table, transcribed; its fourth column is "
                 "headed 轨迹步数 (steps) but holds the state count -- see caveats"),
        "support.truncated_cells": _row(
            total("n_undetermined"), 0, registry_key=None,
            note="E15's UNDETERMINED scope never fires here: parityworld has at "
                 "most 4 colours per cell against SUBSET_ENUMERATION_LIMIT=%d, so "
                 "no scope label in this corpus is budget-decided"
                 % ZS.SUBSET_ENUMERATION_LIMIT),
        "fixtureB.dimension": _row(
            fixture_b["dimension"], 9, registry_key=None,
            note="the '9 维空间' the adversarial review pairs with 40 transitions"),
    }

    disagreements = sorted(k for k, v in counts.items() if not v["agrees"])

    caveats = _caveats(
        falsified=falsified, dirty=dirty, g50t=g50t, fixture_b=fixture_b,
        disagreements=disagreements,
        subset_total=total("n_cell_local_subset"),
        cell_local_total=total("n_cell_local"),
    )

    if jsonl_path is not None:
        _write_jsonl(Path(jsonl_path), rows)

    inputs = list(INPUTS)
    if g50t.get("present"):
        inputs.extend(g50t["arm_by_file"])

    return _common.result(
        key="zs.falsified_laws",
        question=(
            "How many vectors that zero_space published as conservation laws over "
            "200 parityworld worlds are falsified by some legal transition of the "
            "same world -- i.e. hold on the sampled trajectory but not under the "
            "stronger quantifier lp_potential uses?"
        ),
        value=falsified,
        e11_prose=102,
        counts=counts,
        inputs=_common.input_digests(inputs),
        method=(
            "Corpus: %d parityworld worlds, fuzzlab.worlds.parityworld.generate(seed) "
            "for seed in [%d,%d]. For each world: engines.zero_space.zerospace."
            "analyse(world.states, world.colors) for the laws under audit; then BFS "
            "from world.states[0] applying every declared operation to every "
            "reachable state (apply_operation has no precondition, so the transition "
            "relation is reachable-states x operations) to enumerate ALL legal "
            "transitions, budget %d states. A law `a` is falsified iff some "
            "transition x->y has bin(a & (enc(x) ^ enc(y))).count('1') odd -- three "
            "lines of stdlib, calling neither the engine's gf2 nor the oracle's. "
            "true_dim is fuzzlab.oracles.gf2.null_space over the distinct reachable "
            "differences; same_span compares that oracle's trajectory null space "
            "against result.basis. cell_local laws are classified whole-group vs "
            "proper-subset against the feature groups, and the proper-subset ones "
            "tested for membership in the engine's own cell_local_subspace(). "
            "Fixture B is analysed from fixtures/data/pair_flip.jsonl. The g50t "
            "block is a census of committed candidate JSONL under theoria-arm/ "
            "(read-only, development-pile game). No network, no API, no RNG beyond "
            "the seed stream."
            % (N_WORLDS, SEED_LO, SEED_HI, REACHABILITY_BUDGET)
        ),
        caveats=caveats,
    )


def _caveats(*, falsified: int, dirty: List[Dict[str, Any]], g50t: Dict[str, Any],
             fixture_b: Dict[str, Any], disagreements: List[str],
             subset_total: int, cell_local_total: int) -> List[str]:
    return [
        # -- the one the ticket insists on, and it goes first ------------------
        "WHAT %d MEANS, AND WHAT IT DOES NOT. It is a count of laws that hold "
        "under the engine's *declared* quantifier -- the observed trajectory -- "
        "and fail under a *stronger* one: every legal transition reachable from "
        "the initial state. It is NOT a defect count and it is NOT an arithmetic "
        "error. `engine-rig/DECISIONS.md` D-003 pre-registers exactly this "
        "mechanism ('If a pair never fires, the observed difference space is "
        "smaller and the recovered invariant space is correspondingly larger -- "
        "still sound, but weaker than the ground truth') three months before it "
        "was measured, and `zerospace.py:209` puts the quantifier on the method "
        "signature: 'Is this vector one of the conservation laws the evidence "
        "supports?'. E11's own CROSSCHECK.md:92-101 retracts the defect reading "
        "and keeps the number. Two facts in this module's own output say the "
        "same thing quantitatively: the engine's dimension is >= the true "
        "dimension in 200/200 worlds (never below -- soundness is one-"
        "directional), and the elimination itself agrees with an independent "
        "GF(2) oracle in 200/200. This module recomputes the count. It does not "
        "re-open the adjudication. A bare '%d' with no note is how the original "
        "misreading happened."
        % (falsified, falsified),

        "QUANTIFIER, stated exactly. 'Legal transition' here means (reachable "
        "state, declared operation). `parityworld.apply_operation` has no "
        "precondition -- it unconditionally shifts every cell in the operation's "
        "support -- so every such pair is legal and no impossible transition is "
        "enumerated. This is *weaker* than `lp_potential`'s `check_exactly::"
        "inv_closed`, which quantifies over move instances irrespective of "
        "reachability. The partial chose the weaker one so every counterexample "
        "starts from a genuinely reachable state, and says so: %d is a LOWER "
        "BOUND. A stronger quantifier can only find more." % falsified,

        "SHARED DEPENDENCY, unavoidable. `parityworld.apply_operation` produces "
        "both the trajectory under audit and this module's reachability graph. "
        "If it is itself wrong, both paths are wrong in the same direction -- "
        "which can only *mask* a finding of this shape (over-reported laws), "
        "never manufacture one. The falsification verdict "
        "(`increment_is_even`) is three lines of stdlib and touches neither "
        "`engines/zero_space/gf2.py` (the code under audit) nor "
        "`fuzzlab/oracles/gf2.py`; the oracle is used only for the `true_dim` "
        "column and for `same_span`.",

        "SAME_SPAN IS A CONTROL, NOT EVIDENCE. 200/200 reproduces, but the "
        "adversarial review's sharpening is the point: the oracle takes "
        "differences against state 0 and the engine takes consecutive "
        "differences, and those two row sets are linear combinations of each "
        "other, so equal spans is a theorem rather than an observation. It "
        "cannot come out any other way, and `fuzzlab/props/zero_space.py::"
        "law_space_is_complete` -- which makes the same comparison -- therefore "
        "carries zero information in this direction.",

        "COMMIT 2a1c30d (C11) MOVES NOTHING, and neither do the two zero_space "
        "commits after it. 2a1c30d added `truncated_cells` / `scope_exhaustive` "
        "bookkeeping to `local_laws` and renamed the literal 8 to "
        "`SUBSET_ENUMERATION_LIMIT`; 3de10b7b and 99204472 (E15) added the "
        "`undetermined` scope and its payload keys. All three are inert on this "
        "corpus for one checkable reason: `parityworld` uses at most 4 colours, "
        "so a cell's feature group is at most 4 wide against a limit of %d, the "
        "truncation branch is never entered, and `support.truncated_cells` "
        "counts 0 `undetermined` laws across all 200 worlds. The arithmetic "
        "path -- `gf2.null_space`, `local_laws`'s subset enumeration, "
        "`quotient_basis` -- is byte-identical to E11's base ed592a6. These are "
        "today's numbers regardless: the recomputation runs on today's code, "
        "which is the number of record."
        % ZS.SUBSET_ENUMERATION_LIMIT,

        "NO fuzzlab/props DRIFT ON THIS PATH. The V-13 corpus repair (eb61aa98) "
        "changed which object `fuzzlab/props/_mine` selects, moving the "
        "`cegis_miner` numbers. This corpus does not route through "
        "`fuzzlab/props` at all -- it calls `fuzzlab.worlds.parityworld.generate` "
        "directly, exactly as the partial did. `git log ed592a6..HEAD` shows "
        "zero commits touching `fuzzlab/worlds/parityworld.py`, "
        "`fuzzlab/oracles/gf2.py`, `fuzzlab/prng.py` or `fuzzlab/worlds/"
        "common.py`, so there is no second caliber to report. "
        "`fuzzlab/props/zero_space.py` did move (e1319503) and is deliberately "
        "not called here.",

        "PROSE SLIP, off by one, in the partial -- no registry number moves. The "
        "13-world table's fourth column is headed 轨迹步数 ('trajectory steps') "
        "and its values are *state counts*: seed 12 is listed at 18, and the "
        "world has 18 states / 17 transitions. Under the state-count reading the "
        "table matches 13/13 (`support.dirty_world_table` agrees); under the "
        "step reading it matches 0/13. The same off-by-one reaches a quoted "
        "payload: the partial's hand-checkable example says seed 111's law "
        "carries `coverage: 4/4` and seed 12's carries `coverage 18/18`, but "
        "`zero_space/__init__.py:34` sets coverage to "
        "`n_transitions/n_transitions`, which is 3/3 and 17/17. The adversarial "
        "review's own transcript of seed 111 ('轨迹 AACA -> BACA -> ACBC -> "
        "CBBC') shows 4 states and 3 transitions, consistent with this. The "
        "underlying data is right; two rendered strings are not.",

        "91 vs 100, both reproduced. The partial says 91 of the %d "
        "counterexamples start from a state the trajectory itself visited; the "
        "adversarial review recomputed 100 and diagnosed the difference as the "
        "partial having looked only at the first counterexample in its "
        "enumeration order. Both are in `counts`: first-witness gives exactly "
        "91 and any-witness exactly 100, which confirms the diagnosis as well as "
        "the numbers. 100 is the better figure; 91 is a conservative "
        "under-count. Neither is in the registry." % falsified,

        "`zs.fixtureB_features` IS REGISTERED AGAINST THE WRONG DOCUMENT. The "
        "registry (`tools/engine_table.py:607`) regexes 16 out of "
        "`partials/probe_frontier-via-bruteforce.md`, not out of either "
        "zero_space source. Recomputed here from the fixture itself: "
        "`fixtures/pair_flip.py` declares 8 cells and 2 colours, `analyse` "
        "builds %d features over %d states and %d transitions, and reports a "
        "%d-dimensional law space (%d cell_local + %d global). Both fixture "
        "numbers are now derived from the fixture rather than from a third "
        "engine's report."
        % (fixture_b["n_features"], fixture_b["n_states"],
           fixture_b["n_transitions"], fixture_b["dimension"],
           fixture_b["n_cell_local"], fixture_b["n_global"]),

        "THE g50t GROUP IS A CENSUS OF WHAT WAS PUBLISHED, NOT A CHECK THAT IT "
        "HOLDS. 366 / 370 / 4 all recompute from "
        "`theoria-arm/runs/20260728T015354Z-g50t-first-contact/candidates.jsonl` "
        "as the modal published group (%s rows of %s), and 366 = 370 - 4 is "
        "arithmetic. What is NOT computable offline is whether any of those 366 "
        "laws survives the quantifier this module applies to parityworld: that "
        "needs reachability enumeration over the live ARC game. Reported as a "
        "gap, exactly as both E11 sources report it. `g50t-5849a774` is a "
        "development-pile game so reading the artefact is permitted; nothing "
        "under `theoria-arm/` was written."
        % (g50t.get("modal_rows"), g50t.get("rows")),

        "CROSSCHECK.md's '2911 such rows in theoria-arm' OVER-ATTRIBUTES, and "
        "the total is what reproduces. There are exactly 2911 `zero_space` rows "
        "across all committed `candidates*.jsonl` under `theoria-arm/` (1821 + "
        "728 + 362, in the g50t first-contact run and its two aborted "
        "predecessors), so 2911 is right as a *row count*. But 'such rows' reads "
        "as rows in the 370/366/4 group, and only %s are: the other two groups "
        "are 365/362/3 (1448 rows) and 370/365/5 (365 rows). The digit is "
        "correct; the sentence attaches it to the wrong set."
        % g50t.get("arm_rows_in_modal_group"),

        "SCOPE IS THE SECOND FINDING AND IT IS NOT ABOUT THE QUANTIFIER. Of %d "
        "`cell_local` laws, %d have a support that is a *proper subset* of a "
        "cell's colour group, and 0 of those lie in the engine's own "
        "`cell_local_subspace()` -- they are world facts filed as encoding "
        "artefacts. Confirmed from the other side: all 51 falsified "
        "`cell_local` laws are proper-subset ones and no whole-group encoding "
        "law was ever falsified. The reason the partial gave for this being "
        "invisible ('all 15 tests run on Fixture B') was overturned by the "
        "adversarial review -- 10 of 15 do, and two hand-built worlds actually "
        "trigger the divergence. The correct reason is that no test asserts "
        "anything about what `scope` *means*. This module measures the labels; "
        "it does not adjudicate which definition is right."
        % (cell_local_total, subset_total),

        "GAP -- ONE FAMILY ONLY. Every parityworld number here is a fact about "
        "`parityworld`. `gridworld`, `blockworld`, `hypset` and `jumpgraph` are "
        "never fed to this engine, by the battery or by anything else, so there "
        "is no evidence about behaviour on any other family and none is claimed.",

        "GAP -- `run_all --only X --check` reported STALE for every count file "
        "written by a *different* module, because the stale sweep did not know "
        "the run was deliberately partial. Fixed in `run_all.py` (stale "
        "detection is skipped when `--only` is given); a full `--check` still "
        "reports staleness. This was pre-existing and affects every sibling "
        "module's stated acceptance command, not just this one.",

        ("Every figure agrees with E11." if not disagreements
         else "Disagrees with E11 on: " + ", ".join(disagreements)),
    ]


JSONL_FIELDS = ("seed", "flavour", "k", "n_cells", "n_operations", "n_features",
                "n_trajectory_states", "n_trajectory_transitions",
                "n_reachable_states", "n_legal_transitions",
                "n_distinct_differences", "engine_dimension", "true_dimension",
                "n_laws", "n_falsified", "same_span")


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    """One raw row per world, sorted by seed, LF-terminated, keys sorted."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps({k: row[k] for k in JSONL_FIELDS},
                                    sort_keys=True) + "\n")


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--jsonl", metavar="PATH", default=None,
                        help="write one raw row per world to PATH")
    args = parser.parse_args()
    _common.main(lambda: compute(jsonl_path=args.jsonl))


if __name__ == "__main__":
    _main()
