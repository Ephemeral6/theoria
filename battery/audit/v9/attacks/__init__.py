"""The six blind attack modules, exactly as their authors delivered them.

`a1`…`a6` were written by six agents that never saw each other, never saw
`battery/audit/gaming.py` or `battery/audit/exploits/`, and never saw which
metrics were in the main table.  Each worked from a docstring-stripped copy of
`battery/model.py` and `battery/metrics/` and nothing else; `battery/BLINDING.md`
records what leaked anyway.

Split by metric, not by difficulty, so no attacker could infer from its own
assignment which metrics the project cares about:

| module | metrics |
|---|---|
| `a1` | X1 X2 X3 X4 X5 X6 |
| `a2` | P1 P2 P3 P4 P5 E6 |
| `a3` | E1 E2 E3 E4 E5 E7 |
| `a4` | M1 M2 M3 M4 M5 M6 |
| `a5` | K1 K2 K3 K4 K5 K6 K13 |
| `a6` | K7 K8 K9 K10 K11 K12 K14 |

**Kept unedited on purpose.** These modules are evidence, and an aggregator who
tidies the evidence is an aggregator whose findings cannot be audited.  Where a
module's own comment disagrees with the verdict table, the verdict table is
derived and the comment is the attacker's belief; both stay.
"""

from battery.audit.v9.attacks import a1, a2, a3, a4, a5, a6

MODULES = (a1, a2, a3, a4, a5, a6)

__all__ = ["MODULES", "a1", "a2", "a3", "a4", "a5", "a6"]
