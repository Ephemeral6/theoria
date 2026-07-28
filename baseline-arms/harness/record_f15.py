"""Write the F-15 adjudication for the ar25 cells. Idempotent; run once.

Kept as a script rather than done by hand so the record goes through
`adjudications.validate` on the way in, and so the exact wording of the ruling
has a diff attached to it.

    python -m harness.record_f15
"""

import sys

from . import adjudications, ledger, run_campaign

FINDING = "F-15"

AR25_CELLS = [
    "bare_cc-ar25-claude-haiku-4-5-20251001-24d8edcd",
    "bare_cc-ar25-claude-haiku-4-5-20251001-1ebe643b",
    "bare_cc-ar25-claude-haiku-4-5-20251001-0d8cdab8",
]


def main(argv=None) -> int:
    already = adjudications.suspended("G4")
    if all(rid in already for rid in AR25_CELLS):
        print("F-15 already recorded for all %d cells; nothing to do"
              % len(AR25_CELLS))
        return 0

    recorded = [c["run_id"] for c in run_campaign.load_cells()]
    unknown = [rid for rid in AR25_CELLS if rid not in recorded]
    if unknown:
        print("refusing: these run_ids are in no recorded cell: %s" % unknown)
        return 2

    record = {
        "kind": "degraded",
        "finding": FINDING,
        "authority": "monitor",
        "recorded_at": ledger.utcnow(),
        "recorded_by": "P-12",
        "game_id": "ar25-0c556536",
        "run_ids": AR25_CELLS,
        "scope": ["G4"],
        "reason": (
            "The monitor ruled these three cells degraded rather than "
            "representative: ar25 x haiku is not re-run and not re-tiered, the "
            "envelope carries it on its own line marked degraded, and the "
            "remaining three games continue under the unchanged protocol. Two "
            "causes were separated in BUDGET_REPORT.md 11.2 and both hold. "
            "Proximate: actions_failed >= 10 is an absolute abort threshold "
            "that does not scale with the action budget, so at a 30-action "
            "budget and a 0.6 success rate all three cells failed exactly 10 "
            "actions -- standard deviation zero -- and api_unusable was very "
            "nearly guaranteed by construction. Distal: a real degradation "
            "under INC-BA-003 contention, three measures moving together "
            "against the M4 pilot at the same tier."
        ),
        "evidence": [
            "monitor finding F-15 (monitor/state.json)",
            "BUDGET_REPORT.md section 11.1 -- the three cells, 10 failed actions each",
            "BUDGET_REPORT.md section 11.2 -- threshold artefact and real degradation, separated",
            "BUDGET_REPORT.md section 11.3 -- the abort threshold was NOT raised to clear the gate",
            "INCIDENTS.md INC-BA-003 -- two concurrent campaigns on one quota",
            "out/campaign_gate.json -- the RED record these cells produced",
        ],
        "does_not_cover": (
            "The dollars, HTTP calls and wall time these cells spent stay in "
            "every total and every spend clause. G1/G1b/G2/G3/G5/G6a/G6b/G6c/G7 "
            "count them unchanged. Only G4's consecutive-dead-cell streak "
            "excludes them."
        ),
    }

    adjudications.append(record)
    print("recorded %s for %d cells" % (FINDING, len(AR25_CELLS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
