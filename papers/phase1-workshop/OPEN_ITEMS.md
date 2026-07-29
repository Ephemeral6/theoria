# OPEN_ITEMS — what the two audits left, as a working checklist

`REVIEW.md` (adversarial referee) and `CITECHECK.md` (path/number/quote audit)
are kept unedited, including the unflattering parts — OUTLINE red line 3 covers
them. This file is the derived checklist, so that "kept unedited" does not become
"never acted on".

**Provenance of this list.** REVIEW.md was written against a `PAPER.md` of
75,885 bytes; CITECHECK.md against one of 91,244; and this pass added §6, §8 and
§9 on top of both. Neither audit has seen the current draft, and neither carries
a date — only mtimes. **CITECHECK is the later of the two and is the review of
record; REVIEW is the prior pass.** A third pass is owed and is item A1 below.

Verified-fixed items are struck from the list rather than repeated: of REVIEW's
six `[BLOCKING]` issues, four were closed by commit `080f05d` and confirmed still
closed in the current sections (the Lean weight table, the anti-circularity cite,
`not-ranked`, and the seeded-error attribution to Run A).

---

## A · Blocking, and new since both audits

| id | item | where | status |
|---|---|---|---|
| **A1** | ~~**§7 is a report of battery v0 and the battery is now v2.**~~ **Closed at P7** — §7 re-derived against `battery_version: "v2"`, every number read from `battery/artifacts/*.json` rather than from report prose. A2 is unblocked as a result. Original text of the item follows. **§7 is a report of battery v0 and the battery is now v2.** 26 runs / 2 arms / 29 metrics → 95 runs / 5 arms / 38 metrics; 24-of-29 → 31-of-38; 27 clusters → 32; and "there is no Schema arm and there may never be" is contradicted by a `schema_repro` arm that exists. Everything downstream — effect sizes, actions-per-call, ρ, P5, E5 — was computed over the v0 spectrum. **Cannot be patched number by number; §7 needs re-deriving against `battery_version: "v2"`.** | `sections/07_battery.md` | flagged in a standing note this pass; **re-derivation not done** |
| **A2** | Abstract asserts no benchmark game was played for any result, while §7 reports effect sizes over four played ARC games and §11 says so. The current wording qualifies it ("played *for* this paper"); confirm the qualification survives §7's re-derivation, since A1 changes what §7 claims. | `sections/00_abstract.md` | open, blocked on A1 |
| **A3** | "The miss was named … with its three pairs" overstates `THEORIZE_LOG.md` R-05, which names three *directions* and one cell. The "three pairs" gloss was written at M6, after the score existed. This is the sentence that turns an anecdote into evidence for the seal. | `sections/00_abstract.md`, `sections/01_intro.md` | open |
| **A4** | A third audit pass is owed: both existing audits predate §6, §8, §9 and the renumbering. | whole paper | open |

## B · Citation hygiene

| id | item | count | status |
|---|---|---|---|
| **B1** | ~~Citations that violate the paper's own repo-relative rule — a bare filename where the rule requires a path.~~ **Closed at P17**, and the counts here were superseded by a measurement. The item's 22/30/9 is prose with no stated method, so it cannot be reproduced or told apart from drift; `runs/20260729T143500Z-P17-bare-filename-citations/census.py` is the executable form and reported **108 occurrences, 32 distinct, 13 ambiguous across 19 occurrences** over the 12 body sections. Of the 19: **14 resolved to a repo-relative path** by content evidence (an entry id, a quoted value, or a line count that only one candidate has) and rewritten; **5 ruled generic** — they name a *kind* of file rather than an artefact — in `verify_paper.py`'s `ADJUDICATED_BARE`, each with its reason printed on every run; **0 left unresolved**. Check **F BARE** is the standing executor: an ambiguous bare filename is red unless ruled. | measured: 108 occurrences, 32 distinct, 13 ambiguous | **closed** |
| **B2** | `.toolchain/` is cited and is not in the tree — correctly, since it is gitignored by design. Say so at the citation rather than leaving a dangling path. | 1 | open |
| **B3** | ~~`PROVENANCE.md` cites `theory-compiler/src/certificate.py`; the real path is `theory-compiler/src/theory_compiler/certificate.py`.~~ | 1 | **closed** — checked at P17: line 60 already carries the full `theory-compiler/src/theory_compiler/certificate.py`, and that is the only `certificate.py` in the tree. Fixed at some point after the audit; the checklist was not updated. |
| **B5** | **Opened at P17.** `CITECHECK.md` and `sections/05_a2.md` §5.6 report the same true finding with two different sizes for the same diff — the audit says **70 diff lines**, §5.6 says **52**. Re-measured at P17: 52 changed content lines is right under every convention (27 removed + 25 added); 70 is not reproducible directly, and the nearest artefact is `diff -U0`'s 69-line total output, which counts the 15 hunk headers and the 2 file headers as diff lines. The audits are kept unedited by OUTLINE red line 3, so the fix is not to edit `CITECHECK.md` but to state the counting convention where the number is used. §5.6 now does (`diff -u`, and what plain `diff` gives instead); the audit's 70 is left standing and recorded here so the next reader comparing the two documents does not read a contradiction into it. | 1 | **open — recorded, not reconciled** |
| **B6** | **Opened at P17, same class as B5.** `CITECHECK.md` faults §5.2's table for two compressed quotations presented inside quotation marks. Both were repaired earlier in this pass — the cells now carry the full source strings and both are exact substrings of `Theoria.md` — but the audit's class-D total still counts them, and the audits are kept unedited by OUTLINE red line 3. Recorded, not reconciled, so the next reader comparing the two documents does not read a live defect into a closed one. `CITECHECK.md` pins itself to a superseded `PAPER.md` digest and says to re-run if the hash has moved, which it has. | 2 | **open — recorded, not reconciled** |
| **B4** | ~~`PROVENANCE.md` attributes segmentation bits to `THEORIZE_LOG.md` O-03; they are in O-01.~~ **Neither O-03 nor O-01: the block is `D-A0-007`.** | 3 | **closed at P17, on the third answer.** B4 was right that O-03 is wrong and wrong about the replacement, and my first pass here repeated the error: I read the **§Segmentation operator** block as belonging to the O-01/O-02/O-03 heading run above it. It does not — it is a self-contained decision that names itself at `cold-start-a0/THEORIZE_LOG.md:86` ("Recorded as **D-A0-007**") and is followed by `### O-04`. Following an O-01 anchor lands a reader on a one-line entry about naming `obj0` the Button. Fixed in all three places: `PROVENANCE.md` lines 41 and 200, and `sections/03_a0.md`, which carried the same wrong anchor and which no check looks at — **check F resolves the file, nothing resolves the anchor inside it.** |

## C · Claims that outrun their evidence

| id | item | where |
|---|---|---|
| **C1** | "Controlled contrast" changes at least two variables (7 vs 21 rules, 59 vs 57 states, 236 vs 228 pairs, Button vs Switch), and the outcome is analytically entailed by the construction. §3.3's body is now honest; the abstract is not. |
| **C2** | "Independently developed track" / "independent adversarial review" oversells two sessions on one repo sharing one `CLAUDE.md`. Defence in depth, not independent replication. |
| **C3** | Two findings entailed by their definitions: E5 is a price list by construction, and the K4/K2 tension is partly definitional with `0.000` quoted to three decimals over **n = 3**. The abstract should carry the n. |
| **C4** | §5.3's "diff the files and the deletion is the whole diff" is false — the header goes 13 → 45 lines and every coverage annotation is rewritten. |
| **C5** | `zero_space` is described two incompatible ways: an empirical null space over observed transitions in §3.2, and symbolically computed Petri invariants in §12. It reads data, not rules. |
| **C6** | §7.6 draws a Phase 4 conclusion from a 4-game pilot the paper elsewhere says can certify nothing. |
| **C7** | The ground-truth seal is not auditable: it rests on a string the authors' own scorer writes. Cite commit hashes, or state plainly that it is a declaration and not a control. Same for the battery's pre-registration. |
| **C8** | A Lean toolchain is required and the paper does not say so — "83/83 tests pass" becomes 75 passed / 8 skipped without `lean` on PATH, and the empty-axiom-list claim evaporates into skips. Of 8 lean-gated items only 7 invoke `lean` and 6 read `#print axioms`. |
| **C9** | Battery determinism is asserted on the published artefacts but tested on a synthetic fixture. |
| **C10** | The pile hash reproduces only after LF normalisation; a Windows checkout gives a different digest, and the paper invites the reader to run the check. |
| **C11** | Two figure payload fields are hard-coded against their own docstrings (`revisions_driven_by_certify: 0`, `executable_probes: 0`). |
| **C12** | ~~Opened at P17: the proof-verb defect survives in §1's contribution list, §4's heading and §11.~~ **Closed at P18 by ruling** — `runs/20260729T181500Z-P18-certificate-verb-ruling/RULING.md`. Split three ways, because the three sites are not one defect: §1's bullet hung "machine-checked" on the **certificate**, a JSON document re-checked by Python, and is repaired; §4's heading and §11's recap hang it on the **impossibility**, a Lean theorem with an empty axiom list whose proof invokes the crossed weights at `theory-compiler/lean/TheoriaLean.lean:148`, and **stand unchanged** — C12's demand that they get the §5.2 treatment is refused, and the refusal is recorded so a later round does not re-open them on this item's authority. C12's own widening was false and was struck on the P17 branch before merge. §4.4 now names which development it describes (the five-goal hybrid, which is written to no tracked file) so that the shipped artefact is not read for it. |
| **C14** | **Opened at P17.** §5.2's table pairs the clause 模型重放 175/175 全对 (the model replays every frame correctly) with a check that establishes something else — `history_proposes_a_jump: false`, i.e. that the history's evidence does not induce the teleport. Both halves are true and the field is exact; the clause-to-check *link* is what nobody verified, and the `kind` column added at P17 is a promise that each row means what it says, so the mismatch now carries the paper's warrant. The honest repair needs a replay-accuracy measurement for the history-induced manual that the artefacts do not currently isolate (the nearest is row 3's `certify_cheap`, which is the play record against the generated model). Recorded rather than repaired, because the alternative was to invent the number or to silently re-map the rows. |
| **C15** | **Opened at P17.** Row 1's citation trail dead-ends. `cold-start-a2/artifacts/engines_diff.json` keys its two streams `candidates.jsonl` and `candidates_history.jsonl`, but the on-disk `candidates.jsonl` now holds a single `plan` record rather than the 23 mined rules the row is about: `a2pipeline/plan.py` deletes and re-emits the stream, so a later stage overwrote it. The rule set the exclusivity claim is checkable against survives in `engines_report.json` (`mining.rules`). A reader following the row into the file it names finds a plan. The paper's gate B checks that a path resolves, not that the file still holds what it is cited for. |
| **C13** | ~~§5.2's "The isomorphism is machine-checked, clause by clause" is the strongest verb in the paper on a non-proof object; flagged by P12's hostile round (LANDS) and again by P15, and passed over by both as out of scope.~~ **Closed at P17 by deliberate ruling** — `runs/20260729T160000Z-P17-machine-checked-ruling/RULING.md`. The claim is **deleted, not qualified**; the table it introduced is kept and given a `kind` column, because it is the paper's only clause-by-clause account of §5.1's substitution. Measured: **one** row is a Lean proof (and only its Lean half), the rest are computed properties, and **no clause in the table is refuted** — the refuted object is the manual's `unsolvable` theorem, which the old bare "refuted" cell did not name and which two readers, including the item's own author, misread as a failed clause. |

## D · Novelty and related work — the largest reviewer-facing gap

**Status after P7: the citation half is closed, the claim-scoping half is not.**
Four of the five bullets below now have real, twice-verified citations in §12 —
Angluin and Chow for the reset assumption and conformance testing, Mitchell and
Lau for the version space, De Millo–Lipton–Perlis with Dijkstra, Fetzer and Boehm
for specification validity, and Ammons et al. for the mined-specification setting
that is the exhibit's *actual* point. §12.3 states in the paper's own voice which
of its framings the literature already owns. What is **not** closed is the
consequence: the abstract still reads as "four results" where the honest scope is
an instrument-and-artefact contribution, and the fifth bullet — "engineering, not
a result" — is untouched. Two named priors remain deliberately uncited because
they could not be confirmed twice: Vasilevskii, and information-gain experiment
design, for which no specific anchor was verified.

The original item, kept for the record. REVIEW's issue 5. Five priors go uncited,
and each maps onto a headline:

* "prediction perfect, understanding broken" restates the framework's own premise
  and is guaranteed by construction — setup, not finding;
* "reversibility beats coverage" is the reset assumption in active automata
  learning (Angluin's L\*), and "replay coverage does not certify the model" is
  FSM conformance testing (Chow's W-method; Vasilevskii);
* CEGIS's "frontier of consistent hypotheses" is a version space (Mitchell), and
  "which experiment splits the frontier, priced in bits" is information-gain
  experiment design;
* §5.6's point is the specification-validity problem (De Millo–Lipton–Perlis);
  §12 cites proof-carrying code but nothing for the exhibit's actual point;
* "engineering, not a result" applies to §4, §5.8, §7.1 and §3.1 — §4 should not
  read as a headline.

## E · Submission mechanics

| id | item | measure |
|---|---|---|
| **E1** | Length against a workshop budget. Was 11,451 words against ~4,000 at review time; the draft has grown since and this pass adds three sections. | ~3× and rising |
| **E2** | ~~`[bib: TODO]` markers with no bibliography file.~~ **Closed at P7.** `references.bib` holds 70 records, each cross-verified against two independent sources with traces in `runs/20260728T102014Z-P7/search-traces/`; 65 are cited and no marker remains in any section. Two priors REVIEW named are still uncited on purpose — Vasilevskii, and the 2016 Unsolvability IPC — because neither could be confirmed twice. | was 19 → **0** |
| **E3** | Placeholder authorship, affiliation and venue. | by design, until submission |
| **E4** | Typography: mixed `·` and `—` separators; Chinese terms glossed inconsistently (重证 as "re-proof" in §5.5 and "re-certify" in §1.3). | — |

## F · Minor, all open

`PROVENANCE.md` cite for the `[1,2,3,2,1]` vector points at D4, which never names
it (it is in `theory-compiler/STATUS.md`) · §3.1's "about six seconds" is cited to
the wrong sections of its report · §1.1's seal gloss says "after both certify
layers and the plan were green" where the file says "after M4 and M5", and M5 is
the unsolvable-variant milestone · §3.3 calls A0's explorer "exhaustive" one row
above quoting its coverage as 99 % · §3.3 renders the same fraction as "99 %" and
"98.73 %" one line apart · §3.5's "the other track" has no antecedent · §2.2 omits
`deadlock_carver`, which is shipped, tested and tagged · §3.5's a0-spike
corroboration is about reachability, not reversibility · §11.1(c) cites the ARC
determinism precheck without putting its numbers in the sentence · the abstract
drops the qualification that both catches of the seeded clause were contingent on
the experimenter's choice of error, and that the Lean catch is called *unplanned*
in its own report · `arc-recon/README.md` still says all 25 games are
`never_audited` while the same file says the log supersedes it · `battery/METRICS.md`
says "twenty-eight" against a registry that now holds 38.

## G · Stale in the audits themselves — struck, do not action

* REVIEW says `CITECHECK.md` does not exist. It does.
* REVIEW says no sentence references any figure. Three now do.
* CITECHECK's own header records the `PAPER.md` hash it audited and asks to be
  re-run if the hash has moved. It has moved, twice.
