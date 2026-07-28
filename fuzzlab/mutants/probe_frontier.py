"""`probe_frontier` mutants — eighteen defects, and the seam had to be built.

## The seam, and why this module installs one

Every other property module funnels its engine call through one private helper
(`props/zero_space.py:_analyse`), which is what `mutants/__init__.py` documents
the seam as. **`props/probe_frontier.py` has no such helper**: it calls
`engine.partition_for(...)` and `engine.rank_probes(...)` directly, and its only
private names — `_truth_partition`, `_class_weights` — are *oracle* side. Those
are not seams: corrupting them fakes the judge, not the engine, and any invariant
would then be measured against a lie about the world instead of a lie about the
answer.

`engine` itself is an attribute of the props module, but it is a *module object*
and `mut.applied` requires the seam to be callable, so it cannot be named as one.

So this module installs the missing helper at import time, on the props module,
without editing either file:

* `props._call_partition_for` and `props._call_rank_probes` are added — plain
  functions delegating to the real engine;
* `props.engine` is replaced by a proxy that forwards everything to the real
  `engines.probe_frontier`, except the two entry points, which it dereferences
  **from the props module by name at call time** so that `mut.applied`'s rebind
  is seen.

The engine is still untouched — `engines.probe_frontier` is never patched, only
read — and the lie is still told between engine and property, which is where
`mutants/__init__.py` says it belongs. What is not preserved is the framework's
assumption that the seam already exists; that is a real gap and it is reported
rather than papered over.

Two entry points rather than one on purpose: `partition_matches_truth` is the
only invariant that goes through `partition_for`, and the other three go through
`rank_probes`. One combined seam would make every partition mutant also visible
to the ranking invariants and destroy the per-invariant attribution.

## What the result type allows a mutant to be

`ProbeValue.value`, `.splits` and `.n_classes` are **properties**, not fields:

    value    = entropy / cost   (inf when cost == 0)
    splits   = len(partition) > 1

So no mutant can make `value` disagree with `entropy / cost`, and none can make
`splits` disagree with its own partition — both are **unfalsifiable by
construction**, exactly as `dimension == len(basis)` is for `zero_space`. `splits`
can only be lied about *through* `partition`, and `value` only through `entropy`
or `cost`. That is why `pf-splits-*` corrupt the partition and why there is no
`pf-value-*`.

## The tolerance ladder

`props/probe_frontier.py:EPS = 1e-9` is an absolute band on the entropy
comparison. An invariant with a tolerance has a *resolution*, and the resolution
is a number nobody had written down. `pf-entropy-shift-*` is one mutant per rung
(1e-16 … 1e-3) offsetting every reported entropy by a fixed amount and re-sorting
so that only the entropy invariant is touched. The rung where kills start is the
measurement; the rungs below it are **designed to survive** and their survival is
the datum, not a failure of the battery.

## `expect_kill` on a mutant designed to survive

`Mutant.__post_init__` rejects an empty `expect_kill`, so a mutant written to
demonstrate a gap cannot be registered as "expect nothing". The convention used
here, and it is a convention and not a prediction: **`expect_kill` names the
invariant that owns the claim**, and any mutant whose description begins with
`EXPECTED SURVIVOR:` is one I predicted before the run would *not* be killed.
Those show up as `predicted_but_missed`, which is the right column for them —
but the reader must know they were pre-registered as gaps rather than as failed
guesses. This is written here, before the run, so that it cannot be a retrofit.

## Two things deliberately not mutated, because they are not promises

* **Tie order.** `rank_probes` sorts by `(-value, -entropy, cost, str(action))`,
  which is total — action names are unique per world — so there are no tied keys
  to reorder. A "swap two equal entries" mutant would be injecting a behaviour
  the engine never exhibits.
* **Partition dict insertion order.** `as_json()` sorts the classes before
  emitting them, so key order carries nothing. A mutant that only permuted keys
  would be a false accusation against `partition_matches_truth`, which compares
  dicts and not sequences.
"""

from typing import Any, Dict, List, Tuple

from fuzzlab import mutants as mut
import fuzzlab.props.probe_frontier as _props

ENGINE = "probe_frontier"
PARTITION_SEAM = "_call_partition_for"
RANK_SEAM = "_call_rank_probes"


# ------------------------------------------------------------------ the seam

class _EngineVia:
    """The real engine, with two calls routed through props-module attributes.

    Everything else falls through to `engines.probe_frontier` unchanged, so the
    property module cannot tell the difference and neither can the campaign.
    """

    def __init__(self, real: Any, module: Any) -> None:
        self._real = real
        self._module = module

    def partition_for(self, *args: Any, **kwargs: Any) -> Any:
        return getattr(self._module, PARTITION_SEAM)(*args, **kwargs)

    def rank_probes(self, *args: Any, **kwargs: Any) -> Any:
        return getattr(self._module, RANK_SEAM)(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)

    def __repr__(self) -> str:
        return "<probe_frontier engine via fuzzlab mutation seam>"


def _install_seam() -> None:
    if isinstance(_props.engine, _EngineVia):
        return
    real = _props.engine

    def _call_partition_for(hypotheses: Any, state: Any, action: Any) -> Any:
        return real.partition_for(hypotheses, state, action)

    def _call_rank_probes(hypotheses: Any, state: Any, actions: Any,
                          costs: Any = None) -> Any:
        return real.rank_probes(hypotheses, state, actions, costs)

    setattr(_props, PARTITION_SEAM, _call_partition_for)
    setattr(_props, RANK_SEAM, _call_rank_probes)
    _props.engine = _EngineVia(real, _props)


_install_seam()


# --------------------------------------------------------------- small tools

#: The engine's own ordering key, quoted from `frontier.py:rank_probes`.
def _key(value: Any) -> Tuple[Any, ...]:
    return (-value.value, -value.entropy, value.cost, str(value.action))


def _resort(ranked: List[Any]) -> List[Any]:
    """Re-sort under the engine's stated key.

    Used by every mutant that changes a field the key reads. Without it the list
    also comes back out of order and `ranking_is_sound` fires too, which would
    make a one-invariant measurement look like a two-invariant one.
    """
    ranked.sort(key=_key)
    return ranked


def _fresh(existing: Any) -> str:
    """An observation label no hypothesis in `hypset` can predict."""
    label = "__mutant_obs__"
    while label in existing:
        label += "'"
    return label


# ------------------------------------------------- partition_for corruptions

def _partition_merge(result: Any, args: Tuple[Any, ...],
                     kwargs: Dict[str, Any]) -> Any:
    keys = list(result)
    if len(keys) < 2:
        raise mut.inert("action induces one observation class; nothing to merge")
    result[keys[0]] = sorted(result[keys[0]] + result[keys[1]])
    del result[keys[1]]
    return result


def _partition_move_one(result: Any, args: Tuple[Any, ...],
                        kwargs: Dict[str, Any]) -> Any:
    keys = list(result)
    if len(keys) < 2:
        raise mut.inert("action induces one observation class; nowhere to move to")
    moved = result[keys[1]][0]
    result[keys[1]] = result[keys[1]][1:]
    result[keys[0]] = sorted(result[keys[0]] + [moved])
    if not result[keys[1]]:
        del result[keys[1]]
    return result


def _partition_drop_one(result: Any, args: Tuple[Any, ...],
                        kwargs: Dict[str, Any]) -> Any:
    for key in list(result):
        if result[key]:
            result[key] = result[key][1:]
            if not result[key]:
                del result[key]
            return result
    raise mut.inert("empty partition; no hypothesis to withhold")


def _partition_relabel(result: Any, args: Tuple[Any, ...],
                       kwargs: Dict[str, Any]) -> Any:
    keys = list(result)
    if not keys:
        raise mut.inert("empty partition; no class to mislabel")
    result[_fresh(result)] = result.pop(keys[0])
    return result


# --------------------------------------------------- rank_probes corruptions

def _entropy_shift(delta: float):
    def corrupt(result: Any, args: Tuple[Any, ...],
                kwargs: Dict[str, Any]) -> Any:
        if not result:
            raise mut.inert("no actions ranked; no entropy to offset")
        for value in result:
            value.entropy = value.entropy + delta
        return _resort(result)
    return corrupt


def _rank_swap_adjacent(result: Any, args: Tuple[Any, ...],
                        kwargs: Dict[str, Any]) -> Any:
    if len(result) < 2:
        raise mut.inert("fewer than two actions; no adjacent pair to transpose")
    result[0], result[1] = result[1], result[0]
    return result


def _rank_best_to_last(result: Any, args: Tuple[Any, ...],
                       kwargs: Dict[str, Any]) -> Any:
    if len(result) < 2:
        raise mut.inert("fewer than two actions; the best probe is also the last")
    result.append(result.pop(0))
    return result


def _rank_drop_action(result: Any, args: Tuple[Any, ...],
                      kwargs: Dict[str, Any]) -> Any:
    if not result:
        raise mut.inert("no actions ranked; nothing to withhold")
    result.pop()
    return result


def _splits_collapse(result: Any, args: Tuple[Any, ...],
                     kwargs: Dict[str, Any]) -> Any:
    hit = False
    for value in result:
        if len(value.partition) > 1:
            ids: List[str] = []
            for block in value.partition.values():
                ids.extend(block)
            first = next(iter(value.partition))
            value.partition = {first: sorted(ids)}
            hit = True
    if not hit:
        raise mut.inert("no action separates anything here; splits is already False")
    return result


def _splits_fabricate(result: Any, args: Tuple[Any, ...],
                      kwargs: Dict[str, Any]) -> Any:
    hit = False
    for value in result:
        if len(value.partition) != 1:
            continue
        only = next(iter(value.partition))
        ids = value.partition[only]
        if len(ids) < 2:
            continue
        value.partition = {only: sorted(ids[1:]), _fresh(value.partition): [ids[0]]}
        hit = True
    if not hit:
        raise mut.inert(
            "no single-class action with two or more hypotheses; a split cannot "
            "be invented without inventing a hypothesis")
    return result


def _flatten_costs(result: Any, args: Tuple[Any, ...],
                   kwargs: Dict[str, Any]) -> Any:
    if not result:
        raise mut.inert("no actions ranked; no cost to misreport")
    for value in result:
        value.cost = 1.0
    return _resort(result)


def _probevalue_partition_relabel(result: Any, args: Tuple[Any, ...],
                                  kwargs: Dict[str, Any]) -> Any:
    hit = False
    for value in result:
        if not value.partition:
            continue
        first = next(iter(value.partition))
        value.partition[_fresh(value.partition)] = value.partition.pop(first)
        hit = True
    if not hit:
        raise mut.inert("every partition is empty; no class to mislabel")
    return result


def _probevalue_partition_move(result: Any, args: Tuple[Any, ...],
                               kwargs: Dict[str, Any]) -> Any:
    hit = False
    for value in result:
        keys = list(value.partition)
        if len(keys) < 2 or len(value.partition[keys[1]]) < 2:
            continue
        moved = value.partition[keys[1]][0]
        value.partition[keys[1]] = value.partition[keys[1]][1:]
        value.partition[keys[0]] = sorted(value.partition[keys[0]] + [moved])
        hit = True
    if not hit:
        raise mut.inert(
            "no action has two classes one of which can spare a hypothesis; a "
            "move here would change the class count and stop being class-count "
            "preserving")
    return result


# ------------------------------------------------------------------ catalogue

_PARTITION_CLAIM = (
    "partition_for groups the hypotheses by the observation each predicts and "
    "places every hypothesis in exactly one class -- "
    "engines/probe_frontier/frontier.py:partition_for is a single loop doing "
    "`partition.setdefault(h.predict(state, action), []).append(h.id)` over "
    "every hypothesis; README.md 'the action partitions the frontier into "
    "classes that agree with each other'."
)

_PROBEVALUE_PARTITION_CLAIM = (
    "ProbeValue.partition is that same grouping and is published as the probe "
    "design's `partition` -- frontier.py:probe_value sets "
    "`partition=partition_for(...)`, ProbeValue.as_json emits it, and "
    "__init__.py:to_payload puts it in the frozen `probe_design` payload "
    "(README.md 'Payload shape -- kind: \"probe_design\" (stable)')."
)

_ENTROPY_CLAIM = (
    "ProbeValue.entropy is the Shannon entropy in bits of the true partition's "
    "summed class weights -- frontier.py:probe_value passes "
    "`[sum(weights_by_id[i] for i in ids) for ids in partition.values()]` to "
    "entropy_of, which is math.log2-based; README.md prints it as `bits` and "
    "to_payload publishes it as `entropy_bits`."
)

_ORDER_CLAIM = (
    "rank_probes returns every candidate action exactly once, ordered by "
    "(-value, -entropy, cost, str(action)) -- frontier.py:rank_probes builds one "
    "ProbeValue per action in `actions` and sorts on exactly that key; its "
    "docstring: 'Every candidate action, best splitter first ... Ordering is "
    "total and deterministic'."
)

_COST_CLAIM = (
    "ProbeValue.cost is the caller-supplied path cost for that action -- "
    "frontier.py:rank_probes passes `cost=costs.get(action, 1.0)`, and "
    "ProbeValue.value is documented 'Bits per unit of path cost'; README.md "
    "'probes are ranked by bits per unit cost with a caller-supplied cost map "
    "(default 1)' and the planner tier charges a real plan length to it."
)

_SPLITS_CLAIM = (
    "ProbeValue.splits is true exactly when the action separates at least two "
    "hypotheses -- frontier.py:ProbeValue.splits is `n_classes > 1` over the "
    "partition, and __init__.py:run returns `best=None` unless `ranked[0].splits`, "
    "so this flag decides whether a probe is proposed at all."
)


mut.register(
    # ------------------------------------------------ partition_for, 4 mutants
    mut.Mutant(
        id="pf-partition-merge-two-classes",
        engine=ENGINE, seam=PARTITION_SEAM, kind=mut.UNSOUND,
        claim=_PARTITION_CLAIM,
        description="merge the first two observation classes into one: the "
                    "engine now asserts that hypotheses predicting different "
                    "observations agree, which is the error that makes a probe "
                    "look less informative than it is.",
        corrupt=_partition_merge,
        expect_kill=("partition_matches_truth",),
    ),
    mut.Mutant(
        id="pf-partition-move-one-hypothesis",
        engine=ENGINE, seam=PARTITION_SEAM, kind=mut.UNSOUND,
        claim=_PARTITION_CLAIM,
        description="move one hypothesis from the second class into the first. "
                    "The class count usually survives; one hypothesis is filed "
                    "under an observation it does not predict, so `surviving()` "
                    "would keep a refuted hypothesis alive.",
        corrupt=_partition_move_one,
        expect_kill=("partition_matches_truth",),
    ),
    mut.Mutant(
        id="pf-partition-drop-one-hypothesis",
        engine=ENGINE, seam=PARTITION_SEAM, kind=mut.INCOMPLETE,
        claim=_PARTITION_CLAIM,
        description="drop one hypothesis from the partition entirely: the "
                    "frontier the probe reports is smaller than the frontier it "
                    "was given, and `coverage` in the payload is then a count of "
                    "hypotheses that were silently discarded.",
        corrupt=_partition_drop_one,
        expect_kill=("partition_matches_truth",),
    ),
    mut.Mutant(
        id="pf-partition-relabel-class",
        engine=ENGINE, seam=PARTITION_SEAM, kind=mut.UNSOUND,
        claim=_PARTITION_CLAIM,
        description="rename one observation class to a label no hypothesis "
                    "predicts. The grouping is intact; what the experimenter is "
                    "told to look for is not, and a manual inheriting this "
                    "states a false observable with the right shape.",
        corrupt=_partition_relabel,
        expect_kill=("partition_matches_truth",),
    ),

    # ---------------------------------- rank_probes: the entropy tolerance ladder
    mut.Mutant(
        id="pf-entropy-shift-1e-16",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.UNSOUND,
        claim=_ENTROPY_CLAIM,
        description="EXPECTED SURVIVOR: offset every reported entropy by 1e-16 "
                    "and re-sort. At the magnitudes hypset produces this is at "
                    "or below one ulp, so it is the floor of what any exact "
                    "comparison could see, tolerance or no tolerance.",
        corrupt=_entropy_shift(1e-16),
        expect_kill=("entropy_matches_bruteforce",),
    ),
    mut.Mutant(
        id="pf-entropy-shift-1e-12",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.UNSOUND,
        claim=_ENTROPY_CLAIM,
        description="EXPECTED SURVIVOR: offset every reported entropy by 1e-12, "
                    "three orders of magnitude inside EPS. Representable, so the "
                    "lie is really told; invisible, because the invariant's band "
                    "is wider than it.",
        corrupt=_entropy_shift(1e-12),
        expect_kill=("entropy_matches_bruteforce",),
    ),
    mut.Mutant(
        id="pf-entropy-shift-1e-9",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.UNSOUND,
        claim=_ENTROPY_CLAIM,
        description="offset every reported entropy by exactly EPS. The test is "
                    "`abs(diff) > EPS`, so this rung sits on the boundary and "
                    "whether it kills is decided by the rounding of "
                    "`fl(e + 1e-9) - e` on each world.",
        corrupt=_entropy_shift(1e-9),
        expect_kill=("entropy_matches_bruteforce",),
    ),
    mut.Mutant(
        id="pf-entropy-shift-2e-9",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.UNSOUND,
        claim=_ENTROPY_CLAIM,
        description="offset every reported entropy by 2e-9, the first rung "
                    "unambiguously outside EPS. This is the smallest offset the "
                    "invariant should catch on every world.",
        corrupt=_entropy_shift(2e-9),
        expect_kill=("entropy_matches_bruteforce",),
    ),
    mut.Mutant(
        id="pf-entropy-shift-1e-6",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.UNSOUND,
        claim=_ENTROPY_CLAIM,
        description="offset every reported entropy by 1e-6: still far below the "
                    "12 decimals `as_json` rounds to, so a reader of the payload "
                    "could not see it, and three orders outside EPS.",
        corrupt=_entropy_shift(1e-6),
        expect_kill=("entropy_matches_bruteforce",),
    ),
    mut.Mutant(
        id="pf-entropy-shift-1e-3",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.UNSOUND,
        claim=_ENTROPY_CLAIM,
        description="offset every reported entropy by 1e-3 -- visible in the "
                    "engine's own `%.3f bits` rendering. If this rung does not "
                    "kill, the invariant is not comparing anything.",
        corrupt=_entropy_shift(1e-3),
        expect_kill=("entropy_matches_bruteforce",),
    ),

    # --------------------------------- rank_probes: ranking, two strengths + one
    mut.Mutant(
        id="pf-rank-swap-adjacent",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.DEGRADED,
        claim=_ORDER_CLAIM,
        description="transpose the top two entries -- the weakest possible "
                    "reordering. Every field travels with its own ProbeValue, so "
                    "this is a pure order defect, and it hands the caller the "
                    "second-best probe first.",
        corrupt=_rank_swap_adjacent,
        expect_kill=("ranking_is_sound",),
    ),
    mut.Mutant(
        id="pf-rank-best-to-last",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.DEGRADED,
        claim=_ORDER_CLAIM,
        description="move the best probe to the end of the ranking -- the "
                    "strongest reordering short of a full reversal. Paired with "
                    "pf-rank-swap-adjacent to measure whether detection power "
                    "depends on the size of the disorder.",
        corrupt=_rank_best_to_last,
        expect_kill=("ranking_is_sound",),
    ),
    mut.Mutant(
        id="pf-rank-drop-action",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.INCOMPLETE,
        claim=_ORDER_CLAIM,
        description="drop the last-ranked action from the result. The order of "
                    "what remains is correct; an action the caller offered has "
                    "silently stopped being a candidate.",
        corrupt=_rank_drop_action,
        expect_kill=("ranking_is_sound",),
    ),

    # ------------------------------------------- rank_probes: the splits flag
    mut.Mutant(
        id="pf-splits-collapse-partition",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.UNSOUND,
        claim=_SPLITS_CLAIM,
        description="collapse each ProbeValue's partition to a single class, so "
                    "`splits` reads False for actions that really do separate "
                    "hypotheses. `run()` would then return best=None and report "
                    "that no experiment here is worth performing.",
        corrupt=_splits_collapse,
        expect_kill=("splits_flag_is_honest",),
    ),
    mut.Mutant(
        id="pf-splits-fabricate",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.UNSOUND,
        claim=_SPLITS_CLAIM,
        description="split a genuinely unanimous class in two, so `splits` reads "
                    "True where nothing is separated -- the `agreeing` flavour's "
                    "negative control inverted, and the failure that proposes an "
                    "experiment with no possible outcome.",
        corrupt=_splits_fabricate,
        expect_kill=("splits_flag_is_honest",),
    ),

    # ------------------------------------------------- deliberate gap probes
    mut.Mutant(
        id="pf-flatten-reported-costs",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.INCONSISTENT,
        claim=_COST_CLAIM,
        description="EXPECTED SURVIVOR: report cost 1.0 for every action -- the "
                    "engine ignoring the caller's cost map -- then re-sort under "
                    "the engine's own key so the returned order is internally "
                    "consistent. `value_bits_per_cost` in the payload is now "
                    "wrong for every non-unit-cost action and the ranking is the "
                    "one a cost-blind engine would give.",
        corrupt=_flatten_costs,
        expect_kill=("ranking_is_sound",),
    ),
    mut.Mutant(
        id="pf-probevalue-partition-relabel",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.UNSOUND,
        claim=_PROBEVALUE_PARTITION_CLAIM,
        description="EXPECTED SURVIVOR: relabel one class inside each "
                    "ProbeValue's partition, leaving the class count and the "
                    "entropy field alone. Same defect as "
                    "pf-partition-relabel-class, on the copy that reaches the "
                    "payload rather than on the one partition_matches_truth "
                    "inspects.",
        corrupt=_probevalue_partition_relabel,
        expect_kill=("partition_matches_truth",),
    ),
    mut.Mutant(
        id="pf-probevalue-partition-move",
        engine=ENGINE, seam=RANK_SEAM, kind=mut.UNSOUND,
        claim=_PROBEVALUE_PARTITION_CLAIM,
        description="EXPECTED SURVIVOR: move a hypothesis between two classes of "
                    "each ProbeValue's partition without emptying either, so the "
                    "class count -- and therefore `splits` -- is untouched and "
                    "the entropy field still matches the true weights. The "
                    "published grouping is wrong and nothing about it is derived.",
        corrupt=_probevalue_partition_move,
        expect_kill=("partition_matches_truth",),
    ),
)
