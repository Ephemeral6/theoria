"""V9 — the blind, pre-registered re-run of process 4 (anti-gaming).

`battery/audit/gaming.py` and `battery/audit/exploits/` already exist: B14 made
the register executable and B15 landed four defences.  V9 does not replace
them.  V9 supplies the three disciplines that work did not have, and keeps its
own books so a disagreement between the two audits stays visible:

* **blind** — the attackers never saw `gaming.py`, `METRICS.md`, `STATUS.md`,
  `PREDICTIONS.md`, the reports, the artefacts, or the existing exploits.  What
  they were given, and what leaked anyway, is in `battery/BLINDING.md`.
* **pre-registered** — `battery/PREREG_V9.md` and `prereg.py` fix what counts
  as a successful attack *before* any attack ran, and the commit ordering is
  provable with `git merge-base --is-ancestor`.
* **poverty-certified** — an attack only counts as "gameable" if a mechanical
  check says the attacker did no real work.  A high score reached by honest
  work is evidence the metric *works*; conflating the two is the failure mode
  this package exists to rule out.
"""
