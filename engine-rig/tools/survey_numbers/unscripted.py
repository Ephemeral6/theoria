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
