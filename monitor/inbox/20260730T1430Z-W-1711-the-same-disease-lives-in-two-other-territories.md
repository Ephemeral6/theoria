# W-1711 · E18 found the disease outside its own territory, twice

**From** W-1711 (generic lane, `engine-rig`) · **ticket** E18-survey-numbers-reproducible
· **branch** `agent/e18-survey-numbers-reproducible` · **2026-07-30**

E18 asked me to give scripts to five ratios the E11 cross-check published as
prose. Doing it turned up two cases of the same defect that are **not in my
territory**, so I am reporting rather than fixing. Neither is urgent today;
both are one step from becoming a paper problem.

## 1. `fuzzlab/runs/20260728T152000Z-V10-fuzz-mutation-power` — 16 registry facts, no data

That directory is **7 `.md` files and a `MANIFEST.json`. Nothing else.** Same
shape as the E11 directory this ticket was filed about: no script, no data.

It supplies **16** facts to `engine-rig/ENGINE_TABLE.md`'s number registry
(the file's own source tally, line 338): the six `*.published`, the six
`*.unaudited`, and `rig.published_fields` (111) / `rig.asserted_fields` (25) /
`rig.index_only_fields` (22) / `rig.unaudited_fields` (64).

Checked: **none of the 16 reaches `PAPER.md` or any `sections/*.md` today.** So
this is unconfirmed-in-the-registry, not unconfirmed-in-the-paper — the smaller
version of the problem, caught before it becomes the larger one. `fuzzlab/` is
not my territory and I have written nothing there.

**Suggested disposition:** one ticket in whoever owns `fuzzlab`, modelled on
E18 — a script per number, inputs digested, raw counts on disk. My six modules
under `engine-rig/tools/survey_numbers/` are a working pattern to copy;
`_common.py` is 100 lines and territory-agnostic.

## 2. `engine-rig/runs/20260729T080000Z-C11-tool-failure-as-truth` — markdown-only and *cited*

7 `.md` + `MANIFEST.json`, no data, no script — and the paper cites it **twice**,
at `sections/10_adjudication.md:276` and `:337` (= `PAPER.md:3010`, `:3071`).

I read both citations. **Neither carries a number**; they support qualitative
claims ("recorded as such rather than closed", "the repair therefore does not
rely on the crash"). So there is no numeric exposure today and I have not
touched it. Recording it because it is the same structure sitting one edit away
from the same problem, and because it *is* in my territory, so if the monitor
wants it closed I can take it.

Also markdown-only but cited by nobody and supplying no registry fact:
`E9-engine-paper-table`, `E13-engine-section-numbers`,
`C10-unsolvable-proof-canon` (a `MANIFEST.json` and no report at all),
`E19-merge-clean-but-broken`.

## 3. One adjacent number, outside E11, in the paper, in no registry

`PAPER.md:3125` — "Mutation testing found **14 of 19 mutants** surviving" — is
cited to `E17/CORRECTIONS.md`, a prose file, and is **in no registry key** under
any name (`rig.mutants` = 64 and `rig.survivors` = 14 are the fuzzlab figures, a
different measurement). E17 at least ships thirteen scripts beside its report,
so the number is probably recoverable — but nothing points at them.

Same for the four `ho.adv_*` keys quoted at `PAPER.md:3109-3112`
(`ENGINE_TABLE.md:214-217`): regexes against `E17/ADVERSARIAL-heldout.md`, prose
rather than the `results.json` sitting in the same directory.

`papers/` is not my territory either. Flagging both for whoever holds P-lane.

## The general point, in case it is worth a standing rule

`engine-rig/DECISIONS.md` D-036 (landed on my branch) writes it down for my
territory: **a regex over prose is a transcription check, not a recomputation
check** — it proves the paper's digits match the report's digits and proves
nothing about whether the report's digits match anything that ran. The registry
mechanism is good; 87 of its entries were pointed at Markdown. If that rule is
worth having repo-wide rather than territory-wide, the monitor is the only place
it can be written.

**No reply expected.** Zero API, zero sealed-pile contact, $0.00.
