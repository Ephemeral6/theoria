"""Registry numbers that are still backed by prose, each with a reason.

`ENGINE_TABLE.md`'s number registry probes 87 facts out of the cross-check run
`runs/20260729T000000Z-E11-engine-crosscheck-deep/`, which contains nine
Markdown files and a manifest — no script, no data.  Every one of those probes
is a `md(path, regex)`: it proves the table's digits match the report's digits
and proves nothing about whether the report's digits match a computation.

E18 gives as many of them as it can a script (`tools/survey_numbers/`) and
re-points the probe at the script's output.  The ones it does not are listed
here **with a reason**, because the alternative — leaving them out of both the
link map and this file — makes an unscripted number indistinguishable from a
scripted one by inspection, which is the original defect wearing a new hat.

`tests/test_survey_numbers.py::test_no_registry_entry_still_resolves_only_to_e11_prose`
fails if a registry key is prose-backed and absent from here, **and** fails if a
key is listed here but no longer prose-backed.  A stale exemption reads like
coverage, so it is an error too.

Adding an entry here is a real decision, not a formality.  Write the reason as
something a reader could act on.
"""

from __future__ import annotations

# key -> why it has no script yet.
#
# Kept as a plain dict rather than a set so that the reason travels with the
# exemption.  "Not requested" is not a reason; say what it would take.
UNSCRIPTED: dict[str, str] = {}


def declare(reason: str, *keys: str) -> None:
    for k in keys:
        UNSCRIPTED[k] = reason


# ---------------------------------------------------------------------------
# Families with no recomputation module at all.
#
# These are the two E11 partials nobody rescripted under this ticket.  None of
# their numbers reaches the paper body (the census in
# runs/20260730T120000Z-E18/SCOPE-census.md checked all 87 against PAPER.md and
# every sections/*.md), so they are unconfirmed in the registry rather than
# unconfirmed in the paper — a smaller problem, but the same kind.
# ---------------------------------------------------------------------------

declare(
    "cegis_miner numbers outside the lifted-rule survey: battery counts and the "
    "depth-4 subset sweep. tools/survey_numbers/cegis_lift_guard.py builds the "
    "corpus these would need; extending it means re-running the battery, not "
    "writing a new generator.",
    "cegis.battery_green",
    "cegis.battery_green_superset",
    "cegis.depth4_subsets",
    "cegis.lifted_bad",
    "cegis.lifted_bad_rows",
    "cegis.fixtureA_transitions",
)


# ---------------------------------------------------------------------------
# Numbers that a module computes but that are not yet wired into the link map.
#
# This block is expected to empty out.  It exists so that the gap between "a
# script produces it" and "the registry resolves to that script" is visible
# while it is open, instead of being discovered later by someone reading the
# provenance table and assuming.
# ---------------------------------------------------------------------------

declare(
    "computed by tools/survey_numbers/, not yet re-pointed in the link map.",
    "mdl.unrecoverable_pct",
    "pf.ulp",
)

# The five headline ratios that *do* have a counts JSON under
# runs/20260730T120000Z-E18/counts/ and are still probed out of the E11 partial.
# `mdl.objid` is the one of the six that was re-pointed; these five were not, and
# re-pointing each is a one-line edit to `tools/engine_table.py`'s link map plus
# a regenerated ENGINE_TABLE.md.  Listed separately from the block above because
# the artefact exists on disk today — this is a wiring debt, not a compute debt.
declare(
    "a counts JSON exists (runs/20260730T120000Z-E18/counts/<key>.json) and "
    "reproduces; the link map in tools/engine_table.py still resolves the key "
    "to the E11 Markdown. Re-point the probe at the JSON to clear this.",
    "cegis.lifted_tautological",
    "dl.claims_n",
    "lp.incomplete",
    "pf.infinity_rows",
    "zs.falsified_laws",
)


# ---------------------------------------------------------------------------
# Companion numbers of a family that *does* have a module.
#
# For each of these six families a module exists and recomputes the family's
# headline ratio from data.  The keys below are the surrounding numbers of the
# same E11 partial — corpus sizes, intermediate counts, the per-defect tallies —
# and they are still `md(path, regex)` probes.  Clearing one is not a new
# generator: it is emitting the quantity the module already carries as its own
# counts key, which means deciding what the number *is* (E11's prose does not
# always say) and re-running the family.  That decision is per-number, so they
# are declared rather than swept.
# ---------------------------------------------------------------------------

declare(
    "companion number of the cegis_miner survey. "
    "tools/survey_numbers/cegis_lift_guard.py builds this corpus and computes "
    "cegis.lifted_tautological over it; emitting this key means adding it to "
    "that module's counts and re-running, not writing a generator.",
    "cegis.applicable_not_derivable",
    "cegis.frontier_missing_within",
    "cegis.ground",
    "cegis.lifted",
    "cegis.track0_motionless",
    "cegis.track0_rows",
    "cegis.track0_worlds",
    "cegis.transitions",
    "cegis.worlds",
)

declare(
    "companion number of the deadlock/planner family. "
    "tools/survey_numbers/deadlock_reach.py computes dl.claims_n over the same "
    "corpus; these are its adjudication tallies, which need the claim ledger "
    "read as data rather than counted in prose before they can be emitted.",
    "dl.claims",
    "dl.coverage_open4far",
    "dl.theorems",
    "dl.unadjudicated_arc",
    "dl.unadjudicated_exam",
    "dl.uncovered",
)

declare(
    "companion number of the lp_potential survey. "
    "tools/survey_numbers/lp_incomplete.py already solves every world these "
    "count over; each key needs its own definition pinned (E11's prose is "
    "ambiguous about the denominator for several) and then a counts entry.",
    "lp.admissibility_checks",
    "lp.box_blocked",
    "lp.campaign_n",
    "lp.certificates",
    "lp.correct_decline",
    "lp.false_certificates",
    "lp.h_always_zero",
    "lp.h_zero_pct",
    "lp.headline_46",
    "lp.heuristic_none_when_solvable",
    "lp.incomplete_of_all",
    "lp.max_npos",
    "lp.max_states",
    "lp.n500_incomplete",
    "lp.no_farkas",
    "lp.states",
    "lp.unreachable",
    "lp.weight_bound",
    "lp.worlds",
)

declare(
    "companion number of the mdl_segmenter survey. "
    "tools/survey_numbers/mdl_objid.py recomputes mdl.objid over this corpus; "
    "these are the per-defect and per-corpus tallies around it.",
    "mdl.cells",
    "mdl.cells_wrong",
    "mdl.events_repriced",
    "mdl.frames",
    "mdl.groundtruth_worlds",
    "mdl.inflated_worlds",
    "mdl.objid_undercharge",
    "mdl.objid_worlds",
    "mdl.operator_differs",
    "mdl.operator_same",
    "mdl.unrecoverable",
    "mdl.verdict_flips",
    "mdl.worlds",
    "mdl.worst_tracks",
)

declare(
    "companion number of the probe_frontier survey — the one family whose "
    "headline number does *not* reproduce (pf.infinity_rows disagrees with the "
    "E11 prose, see its counts JSON's caveats). Until that disagreement is "
    "adjudicated, re-pointing its neighbours would publish numbers derived from "
    "a recipe still under dispute.",
    "pf.argmax_states",
    "pf.entropy_dev",
    "pf.entropy_mismatch",
    "pf.evals_per_rule",
    "pf.partition_mismatch",
    "pf.real_reorderings",
    "pf.rules",
    "pf.states",
    "pf.teleport_guards",
    "pf.teleport_worlds",
    "pf.worlds",
    "pf.zero_cost_bug",
)

declare(
    "companion number of the zero_space survey. "
    "tools/survey_numbers/zero_space_span.py recomputes zs.falsified_laws over "
    "the parityworld corpus; these are the span/subset counts around it.",
    "zs.cell_local_in_span",
    "zs.cell_local_laws",
    "zs.cell_local_subsets",
    "zs.dirty_worlds",
    "zs.fixtureB_features",
    "zs.fixtureB_transitions",
    "zs.k2_clean",
    "zs.k3_dirty",
    "zs.same_span",
    "zs.worlds",
)


# ---------------------------------------------------------------------------
# Families with no module and no corpus in this rig.
# ---------------------------------------------------------------------------

declare(
    "fd_adapter numbers from the open4far planner run. Recomputing them needs a "
    "Fast Downward build, and `.toolchain/` is gitignored by design — a module "
    "here would be skipped on most machines, which is the defect D-037 is "
    "about wearing a new hat. These stay prose-backed until the planner run "
    "itself is archived as data.",
    "fd.open4far_actions",
    "fd.open4far_optimal",
    "fd.open4far_states",
)

declare(
    "the IC3 state count. There is no ic3 module in tools/survey_numbers/ and "
    "no ic3 corpus in this rig; the number came out of the E11 partial's own "
    "run and would have to be reproduced from that engine before it could be "
    "scripted.",
    "ic3.states",
)
