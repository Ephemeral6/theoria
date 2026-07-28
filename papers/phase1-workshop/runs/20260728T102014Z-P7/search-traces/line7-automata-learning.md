# Search trace — active automata learning and FSM conformance testing

**Why this file exists.** `papers/phase1-workshop/REVIEW.md` issue 14 names two
uncited priors: Angluin's L\* (the reset assumption) and FSM conformance testing
(Chow's W-method; Vasilevskii). §3 already carried a `[bib: TODO]` at the sentence
that names the reset assumption — the last such marker left in the paper. This
line was not assigned to a subagent; it was run by the assembling session because
one marker remained and two lookups would close it.

Run 2026-07-28. Sources chosen independently: `api.crossref.org/works/<doi>`
resolved directly, plus a web search whose consolidated record was compared
field by field.

---

## `angluin1987lstar` — **CONFIRMED**

**Source A** — `https://api.crossref.org/works/10.1016/0890-5401(87)90052-6`,
resolved by DOI, not by title search:

| field | returned |
|---|---|
| title | Learning regular sets from queries and counterexamples |
| author | Angluin, Dana |
| container-title | Information and Computation |
| volume / issue | 75 / 2 |
| pages | 87-106 |
| issued | 1987-11 |

**Source B** — web search for the title plus venue plus volume. The ACM Digital
Library entry (`dl.acm.org/doi/10.1016/0890-5401(87)90052-6`) and the
ScienceDirect article page (`sciencedirect.com/science/article/pii/0890540187900526`)
both index it as *Information and Computation* **75(2):87–106, November 1987**,
with the same DOI. The two source families are independent: one is the
registration agency's metadata, the other the publisher's and ACM's own records.

**Verdict: CONFIRMED.** Every field agrees. Written to `references.bib` and used
at `papers/phase1-workshop/sections/03_a0.md`, replacing the last `[bib: TODO]`
in the paper, and at §11.3.

## `chow1978wmethod` — **CONFIRMED**, with one field note

**Source A** — `https://api.crossref.org/works/10.1109/TSE.1978.231496`:

| field | returned |
|---|---|
| title | Testing Software Design Modeled by Finite-State Machines |
| author | Chow, T.S. |
| container-title | IEEE Transactions on Software Engineering |
| volume / issue | **SE-4** / 3 |
| pages | 178-187 |
| issued | 1978-05 |

**Source B** — web search. The ACM DL mirror
(`dl.acm.org/doi/abs/10.1109/Tse.1978.231496`) and the Semantic Scholar record
both carry the same title, author, pages and year.

**Field note.** Crossref gives the volume as **SE-4**, which is the series-prefixed
form IEEE actually printed for *Transactions on Software Engineering* in that era.
Many secondary records — the SciRP reference listing among them — flatten it to
plain "4". The bibliography keeps `SE-4` and says so in the entry's note, so that
a later reader comparing against a flattened record does not "correct" it.

**Verdict: CONFIRMED.** Used at §11.3 for "replay coverage does not certify the
model".

## Vasilevskii — **NOT PURSUED, therefore NOT CITED**

`REVIEW.md` names Vasilevskii alongside Chow as an independent origin of the same
conformance-testing result. No lookup was run for it in this pass. It is a 1973
Russian-language *Kibernetika* paper whose bibliographic record varies across
transliterations, and confirming it properly needs a catalogue this pass did not
reach.

It is therefore **absent from `references.bib` and uncited in §11**, and §11.3
says so in the text rather than leaving the omission silent. This is the same rule
applied everywhere else in this run: a record that has not been confirmed twice
does not get written down, and the debt stays visible instead.

## Scope note

This line closes the *citation* half of REVIEW issue 14. It does not close the
substantive half — that "reversibility beats coverage" is a rediscovery rather
than a discovery. That is a claim-scoping edit to the abstract, tracked as item
14 in `papers/phase1-workshop/REVIEW_TRIAGE.md` and still open.
