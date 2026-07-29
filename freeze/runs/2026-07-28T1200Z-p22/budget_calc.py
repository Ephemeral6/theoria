import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(
    _os.path.abspath(__file__)))))
from tiers import tiers as _tiers
_T = _tiers()
"""P-22: budget envelope for the sealed campaign, extrapolated from measured unit prices.

Every input is cited.  Nothing here is a target; it is the arithmetic a human
needs in order to set <B>.
"""
PUBLIC_ACTIONS = 17135   # BUDGET_REPORT.md 3.1 (parenthetical)
DEV_ACTIONS    = 3014    # BUDGET_REPORT.md 3.1 table
SEALED_ACTIONS = PUBLIC_ACTIONS - DEV_ACTIONS
# Was `21` (the whole sealed pile) until 2026-07-29.  The campaign is costed
# over the games a claim may actually name -- 19 after F-11's quarantine -- and
# the number is read from the claim set rather than typed.  See freeze/tiers.py.
SEALED_GAMES   = _T["claim"]["n"]

# $/successful action, measured.  BUDGET_REPORT.md 2.1 (pilot) and 11.2 (envelope).
UNIT = {
    "haiku-4.5 (pilot)":    0.0342,
    "haiku-4.5 (envelope, degraded)": 0.0574,
    "opus-5 (pilot)":       0.1459,
}
ARMS = ["bare_cc", "theoria", "theoria_minus_theorems (ablation)"]

print(f"sealed pile: {SEALED_GAMES} games, {SEALED_ACTIONS} baseline actions "
      f"(= {PUBLIC_ACTIONS} public - {DEV_ACTIONS} dev)")
print(f"arms actually runnable: {len(ARMS)}  (schema_repro does not exist -> $0, absent)")
print()
print("S1 = give each arm the official baseline action count (BUDGET_REPORT.md 3.2's")
print("     optimistic lower bound; the envelope reached only 2-6% of it before aborting)")
print()
hdr = f"{'unit price basis':34} {'$/arm/rep':>11} {'n=1 (3 arms)':>13} {'n=2 (3 arms)':>13}"
print(hdr); print("-" * len(hdr))
for name, u in UNIT.items():
    per = SEALED_ACTIONS * u
    print(f"{name:34} {per:11,.0f} {per*len(ARMS):13,.0f} {per*len(ARMS)*2:13,.0f}")

print()
print("The Theoria arm is NOT priced by $/env-action -- its bill is dominated by")
print("theorize model calls, not by actions.  Measured anchor (PARTNER_SYNC,")
print("[theoria-arm] p8-first-contact): 3 runs, 11 actions, $2.05 total = $0.186/action,")
print("and a SINGLE online theorize call cost $1.31 (opus).  There is no measured")
print("theorize-rounds-per-game figure on a live ARC game, so the Theoria and")
print("ablation columns above are LOWER BOUNDS, not estimates.")
print()
print("Per-game hard cap arithmetic (the number a human actually has to set):")
for name, u in UNIT.items():
    print(f"  {name:34} mean baseline actions/game = {SEALED_ACTIONS/SEALED_GAMES:6.1f}"
          f"  ->  ${SEALED_ACTIONS/SEALED_GAMES*u:6.2f}/game/arm at S1")
print()
print("Wall clock, from BUDGET_REPORT.md 3.2 (haiku 45.8 h for 4227 attempted actions):")
H_PER_ACTION = 45.8 / 4227
for n in (1, 2):
    h = SEALED_ACTIONS * len(ARMS) * n * H_PER_ACTION
    print(f"  n={n}: {h:,.0f} h serial / {h/4:,.0f} h at 4-way parallel "
          f"= {h/4/24:.1f} days")
print()
print("Sanity check against the one gate that already exists: BUDGET_REPORT.md 9's")
print("G1 stop-loss is $50 for a 12-cell dev-pile envelope.  The sealed campaign is")
print(f"{SEALED_ACTIONS*len(ARMS)/ (12*30):.0f}x that cell count at S1 depth.")
