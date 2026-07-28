"""The battery's own four-process audit (`Theoria.md` Phase 2).

1. `discriminate_arms` — the gradient `Theoria.md` names, CC vs Schema, paired
   by game. `discriminate` — the within-`bare_cc` model ladder, kept as a
   secondary pass because it holds the harness fixed.
2. (pre-registration lives in `PREDICTIONS.md`, not in code)
3. `redundancy`  — twenty correlated numbers are not twenty findings.
4. `gaming`      — how would an arm cheat this, and could it do so by accident?

The point of putting these in the battery rather than in a write-up is that a
metric which fails process 1 or process 4 is demoted **by the code**, not by
whoever is writing the paper that week.
"""

from battery.audit.discriminate import discriminate, discriminate_arms
from battery.audit.gaming import GAMING_REGISTER, tier_of
from battery.audit.redundancy import cluster

__all__ = ["discriminate", "discriminate_arms", "cluster",
           "GAMING_REGISTER", "tier_of"]
