# REVIEW_TRIAGE — every open item in `REVIEW.md`, sorted by what it would cost

`REVIEW.md` is an adversarial referee pass kept unedited under OUTLINE red line 3.
`OPEN_ITEMS.md` already derives a working checklist from it *and* from
`CITECHECK.md`. This file adds the one axis neither carries: **for each item still
open, is the fix writing, or does it need a run?** That is the axis that decides
what can be closed before a submission deadline and what cannot.

Written at P7 (2026-07-28). Scope: `REVIEW.md` only — its 15 major issues, its 44
checked numbers, and its 17 minor issues. `CITECHECK.md`-only findings are in
`OPEN_ITEMS.md` §B and are not repeated here.

## The three labels

| label | meaning |
|---|---|
| **W** (writing) | fix is a text edit against artefacts that already exist in the tree. No compute. |
| **R** (re-derive) | fix requires re-running or re-reading an existing artefact/script and transcribing new numbers. No new data, no API, no game spend. |
| **X** (new experiment) | fix requires material that does not exist: more games, a theory-bearing control arm, a new run. Cannot be closed at a desk. |

An item can be `W` for the paper and still leave a scientific gap open; where that
is the case the gap is named in the notes rather than hidden by the label.

---

## Summary

| label | major | minor + numbers | total |
|---|---|---|---|
| **W** — writing only | 10 | 21 | **31** |
| **R** — re-derive from existing artefacts | 3 | 4 | **7** |
| **X** — needs new experiment | 2 | 0 | **2** |
| closed / struck | 4 (of the 6 BLOCKING) | 3 | **7** |

**The headline for planning: only two items in the whole review need an
experiment**, and both are the same underlying shortage — four paired games, and
no theory-bearing control arm. Everything else in a 529-line adversarial review
is writing or transcription. That is a good position to be in and it should be
said plainly rather than left implicit.

---

## A · The six `[BLOCKING]` issues

| # | issue | label | status | note |
|---|---|---|---|---|
| 1 | §5.6 / §1.2 / abstract — "the two Lean files differ in their weight table and in nothing else" is false | **W** | **closed** `080f05d` | the diff also touches `def Goal` and four `step` entries; verified still closed |
| 2 | abstract — "no benchmark game was played for any result here" is false | **W** | open, blocked on the §7 re-derivation | current wording qualifies it to "played *for* this paper"; the qualification has to survive §7 moving to v2, which reports effect sizes over four played games |
| 3 | §5.5 — "`locate.py` and `probe.py` import no world module at all", falsified by one grep | **W** | **closed** `080f05d` | `probe.py:59` |
| 4 | §1 / abstract — "named, with its three pairs" overstates R-05 | **W** | **open** | R-05 names three *directions* and one cell; the "three pairs" gloss was written at M6, after the score existed. This is the sentence that turns an anecdote into evidence for the seal — it is writing, but it is the most load-bearing writing in the paper |
| 5 | §3.4 — seeded-error experiment cites the wrong field and Run A's numbers | **W** | **closed** `080f05d` | |
| 6 | §6.4 / §7.4 — "every discriminative verdict came back `underpowered` or `no-data`" is false | **R** | **closed** `080f05d` for v0; **reopens under v2** | there are three verdict values, not two. Under v2 the primary gradient reads differently again (`battery/artifacts/discrimination_arms.json`), so the sentence has to be re-derived, not merely corrected |

## B · The nine `[SHOULD FIX]` issues

| # | issue | label | note |
|---|---|---|---|
| 7 | §5.3 — "diff the files and the deletion is the whole diff" is false | **W** | header 13 → 45 lines, all coverage annotations rewritten, `events:` loses `jumped`, `laws:` swaps a theorem. Delete the sentence or state what else moved |
| 8 | §3.3 — the "controlled contrast" changes more than one variable, and the abstract says so while §3.3 denies it | **W** | 7 vs 21 rules, 59 vs 57 states, 236 vs 228 pairs, Button vs Switch. The body is now honest; the abstract is not. **Writing closes the contradiction; it does not make the contrast controlled** — a genuinely single-variable A0/A0′ pair would be an `X`, and is not proposed |
| 9 | §3.2 vs §11.2 — `zero_space` described two incompatible ways | **W** | empirical null space over observed transitions vs symbolically computed Petri invariants. It reads **data, not rules**. Fixed on the §11 side by P7; the §3.2 side still needs a matching pass |
| 10 | §4 — "independently developed track" and "independent adversarial review" oversell the setup | **W** | two sessions on one repo sharing one `CLAUDE.md`. Defence in depth, not independent replication. Say that |
| 11 | §7.3 / §7.5 — two "findings" entailed by their definitions | **W** | E5 is a price list by construction; the K4/K2 tension is partly definitional with `0.000` quoted to three decimals over **n = 3**. The abstract should carry the n. §7 already separates "found by running the instrument" from "deducible without data" — keep that distinction through the v2 rewrite |
| 12 | §10.3 — the Fast Downward paragraph implies A0/A0′ results ran on FD; they did not | **W** | |
| 13 | reproducibility — `CITECHECK.md` does not exist | — | **struck**: it exists |
| 14 | novelty — where the paper is re-illustrating, and where the related work is missing | **W** | **this is P7's own deliverable.** Five uncited priors: Angluin's L\* reset assumption; FSM conformance testing (Chow, Vasilevskii); version spaces (Mitchell); information-gain experiment design; specification validity (De Millo–Lipton–Perlis). The §11 rewrite fills them. The other half of the issue — "prediction perfect, understanding broken is setup, not finding" and "this is engineering, not a result" — is a **re-scoping of the abstract**, still open |
| 15 | §7.6 — a Phase 4 conclusion drawn in a Phase 1 paper | **W** | soften "C2's evidence weakens by however much of the effect capability explains" to "a confound to separate before Phase 4 freezes". Handled in the v2 rewrite of §7 |

## C · The "Numbers checked" table — every non-`match` verdict

44 claims were checked. 30 matched exactly. The rest:

| claim | verdict | label | note |
|---|---|---|---|
| R-05 "three pairs" | mismatch — overstated | **W** | = major issue 4 |
| A0′ Run B replay — wrong field, wrong run | mismatch | **W** | closed `080f05d` |
| the two Lean files | mismatch — false | **W** | closed `080f05d` |
| holed vs full DSL | mismatch — false | **W** | = issue 7, open |
| `probe.py`/`locate.py` | mismatch — false | **W** | closed `080f05d` |
| discriminative verdicts | mismatch | **R** | = issue 6; re-derives under v2 |
| MDL segmentation 6511 bits / 90 tracks | **stale — artefact has moved** to 5704 / 6 tracks | **R** | the live `engines_report.json` disagrees with the prose; 6511/90 are now `reidentification.*_before`. Transcription, not a run |
| per-object accounts — Cart +2967 | partial — stale | **R** | `concept_accounts.json` gives Cart 2125. The paper reports the Button/Door revision but not the Cart's. `PROVENANCE.md:42` cites the JSON that disagrees |
| A2 anomaly "cap" | match in substance, misleading as phrased | **W** | the cap is 40 and binds two anomaly kinds; 44 = 40 + 4 uncapped `goal_mismatch` |
| A1 tests "83/83, eight invoke `lean`" | partial — inflated, toolchain dependency undisclosed | **W** | 75 pass / 8 skip without `lean`; of the 8, **7** invoke `lean` and **6** read axioms. = `OPEN_ITEMS` C8 |
| P1 confound | partial | **R** | δ and ρ check out; the 27 % lower bound does not reproduce (28.3 % is the floor). **Superseded by v2**: on the *specified* gradient P1 now reads δ = +1.000 in the declared direction, opposite to the model ladder's −0.750 |
| E5 "a 9× spread" | partial — rounding artefact | **W** | true ratio 8.80× |
| X5 cross-check "independent" | overstated — not independent | **W** | both counts descend from `cold-start-a0/world/explorer.py` |
| `lp_potential` "sound but incomplete" | fact right, citation wrong | **W** | the phrase is in `engine-rig/DECISIONS.md` D-014 and three READMEs, not `STATUS.md` |
| pile digest | match, LF caveat undisclosed | **W** | a Windows checkout gives a third digest. = `OPEN_ITEMS` C10 |
| baseline pilot 109 actions | match, not reconstructible | **W** | the printed 12-row table sums to 107 |

## D · Minor issues

All **W** except where marked.

Struck (stale in the review itself): `CITECHECK.md` does not exist — it does · no
figure is cited — three now are.

Open, writing only: `PROVENANCE.md:60` wrong `certificate.py` path ·
`PROVENANCE.md:41` segmentation bits cited to O-03, they are in O-01 · §7.1 cites
`D-B-001` for determinism, it is **D-B-008** · §4.2 cites D4 for the `[1,2,3,2,1]`
vector, it is `theory-compiler/STATUS.md:30` · §3.1's "about six seconds" cited to
the wrong sections · §1.1's seal gloss says "both certify layers and the plan"
where the file says "M4 and M5" · §3.3 labels the explorer "exhaustive" one row
above quoting 99 % coverage · §3.3 renders 233/236 as "99 %" and "98.73 %" one
line apart · §3.5's "the other track" has no antecedent · §2.2 omits
`deadlock_carver` · §3.5's a0-spike corroboration is about reachability, not
reversibility · §10.1 cites the ARC determinism precheck without putting 9/9, 3/3,
9/9, 9/9 in the sentence · the abstract drops "unplanned" from the Lean catch ·
typography, mixed `·` and `—`, 重证 glossed two ways.

**Found at P7 and not in either audit — subsection numbers survived the
renumber. `W`, and now closed.** `runs/20260728T092517Z-P6/SECTION_RENUMBER.md`
says only the `## n ·` heading line changed in the three moved files, and that was
exactly the problem: `sections/10_limitations.md` numbered its subsections
**7.1–7.5** and `sections/11_related.md` numbered its **8.1–8.2**, so the paper
contained two §7.1s and two §7.3s and every "§7.x" was ambiguous between the
battery and the limitations sections.

Both files are renumbered, and a sweep over every `§n.m` in `sections/` — machine
enumerated, then read one by one to separate references to *this* paper's sections
from references to another file's — found **five stale cross-references** and
three unattributed ones:

| where | said | means | fixed to |
|---|---|---|---|
| `01_intro.md` | §7.1 records the sealed pile is no longer clean | limitations | **§10.1** |
| `02_framework.md` | §8 places the whole thing against its neighbours | related work | **§11** |
| `03_a0.md` | §8.1's own table forbids overstating it | the three-waves table | **§11.1** |
| `10_limitations.md` ×2 | "the battery (§6)"; "rather than in §6" | the battery | **§7** |
| `05_a2.md` ×3 | bare "§1.4's three-way" | `Theoria.md` §1.4, not this paper's §1 | attributed |

The sweep also caught two things that are *not* numbering: the abstract's draft
note still said "§7 is known stale", which stopped being true when §7 was
re-derived; and §10.4 restated the battery's v0 figures (24 of 29) beside a §7
that now reports v2. Both corrected against the artefacts. **A restatement in one
section is a cross-reference too, and it goes stale the same way** — worth
remembering the next time a section is re-derived.

Open, **R**: `arc-recon/README.md:185` still says all 25 games are
`never_audited` while the same file says the log supersedes it — a repo fix, not a
paper fix, and it needs the log read · `battery/METRICS.md:7` and
`battery/DECISIONS.md:122` say "twenty-eight" against a registry that now holds
**38**; `METRICS.md` also still titles itself "battery v1". `METRICS.md`
advertises itself as generated and test-pinned, so this is a `battery/docs.py`
fix and a regeneration, not an edit.

---

## E · The two items that need an experiment

Everything above closes at a desk. These do not.

| id | item | what is actually missing | cheapest honest close |
|---|---|---|---|
| **X1** | **Statistical power.** REVIEW issue 6 and the whole battery section rest on a four-game development pile. A two-sided sign test over 4 paired games has a smallest attainable p of **0.125** (`battery/artifacts/discrimination_arms.json`, top-level `power`); **six** non-tied paired games are the floor for the test to be able to clear p < 0.05 at all. Unchanged from v0 through v2 — v2 tripled the run count to 95 and moved this by zero. | more *paired games*, not more runs. The pile cut binds: the development pile is four games and enlarging it is an incident, not a decision (`arc-recon/data/piles.json`, `CLAUDE.md`). So this is a Phase 3 design input, not a Phase 1 fix. | **do not close it — report the floor.** The battery already emits `min_attainable_p` on every ranked metric precisely so nobody reads 0.125 as a near miss. The paper's job is to keep saying so |
| **X2** | **A theory-bearing control arm.** 21 of 38 metrics — the entire epistemic family, the entire mechanism family, and P4 — have never been checked against any known gradient (`battery/artifacts/validation_material.json`, `n_unvalidated: 21`). v2 added an entire second control arm and the count moved by **zero**, metric for metric. | a control arm that *has books*. Not constructible from a baseline: `bare_cc` and `schema_repro` both keep no explicit theory, so every epistemic metric is structurally `not-applicable` on them. | **cannot be closed in Phase 1.** It is the ablation arm's job (`− 定理义务`), which is Phase 3 work. Until then the honest statement is the one v2 already makes: defences do not create material |

Two further items are **X-shaped but not on the paper's critical path**, and are
recorded so they are not mistaken for writing:

* **Issue 8's genuinely controlled A0/A0′ pair** would need a second A0′ built to
  change exactly one variable. Not proposed; the fix on the table is to stop
  calling the existing pair controlled.
* **Issue 14's "engineering, not a result"** is closed by re-scoping the abstract
  to an instrument-and-artefact contribution — which is writing. What it cannot
  close is that A2's headline observation is analytically entailed by its own
  construction. No experiment fixes that either; only a different claim does.

---

## F · Ordering, if the question is "what should the next pass do"

1. **Issue 4** (R-05 "three pairs"). One sentence, and it is the sentence that
   converts an anecdote into evidence for the seal. `W`.
2. **§7 re-derivation against battery v2.** Closes issue 6 and unblocks issue 2.
   `R` — done at P7 for §7 itself; the abstract still trails it.
3. **§11 related work.** Closes half of issue 14, the largest reviewer-facing
   gap. `W` — done at P7.
4. **Issues 7, 9, 10, 11, 12, 15** — six sentences, each deleting or qualifying an
   overclaim. `W`.
5. **The three stale-artefact transcriptions** (MDL bits, Cart account,
   `METRICS.md` count). `R`, cheap, and each is a number the paper's own binding
   rule says must match its file.
6. **Length.** ~11 500 words against a workshop budget near 4 000, and the draft
   has grown since the review. Not a correctness item and not on this list's
   axis, but it is the one thing above that gets *harder* every time another
   section lands.
