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
| **B1** | Citations that violate the paper's own repo-relative rule — a bare filename where the rule requires a path. Nothing is *missing* from the tree; 22 distinct paths resolve only under an inferred base, 9 of them ambiguous across 6–24 real candidates (`STATUS.md` → 8 files, `THEORIZE_LOG.md` → 6, `theory.dsl` → 13, `raw_trace.jsonl` → 24). | 22 distinct, 30 occurrences | open; the 4 introduced by §6 in this pass were fixed here |
| **B2** | `.toolchain/` is cited and is not in the tree — correctly, since it is gitignored by design. Say so at the citation rather than leaving a dangling path. | 1 | open |
| **B3** | `PROVENANCE.md` cites `theory-compiler/src/certificate.py`; the real path is `theory-compiler/src/theory_compiler/certificate.py`. | 1 | open |
| **B4** | `PROVENANCE.md` attributes segmentation bits to `THEORIZE_LOG.md` O-03; they are in O-01. | 1 | open |

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
