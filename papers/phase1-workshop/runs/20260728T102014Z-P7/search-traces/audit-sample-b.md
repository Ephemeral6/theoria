# Audit sample B — DOIs resolved directly by the assembling session

A second, smaller adversarial pass, run by the session that assembled §11 rather
than by a subagent, on the principle that the assembler should not take the
researchers entirely on trust either. `audit-sample-a.md` is the larger 20 %
sample.

Method: `curl https://api.crossref.org/works/<doi>` and read the returned
`message` object directly. No rendered citation, no search-result snippet, no
reuse of the URLs the original researchers cited.

| record | title | authors | venue | year | vol / pages | verdict |
|---|---|---|---|---|---|---|
| `necula1997pcc` | "Proof-carrying code" ✓ | Necula, George C. ✓ | POPL '97 ✓ | 1997 ✓ | 106–119 ✓ | **CLEAN** |
| `murata1989petri` | "Petri nets: Properties, analysis and applications" ✓ | Murata, T. ✓ | Proceedings of the IEEE ✓ | 1989-04 ✓ | 77 / 541–580 ✓ | **CLEAN** |
| `hao2023rap` | "Reasoning with Language Model is Planning with World Model" ✓ | see note | EMNLP 2023 ✓ | 2023 ✓ | 8154–8173 ✓ | **CLEAN** |
| `cropper2022ilp30` | "Inductive Logic Programming At 30: A New Introduction" ✓ | not read — see note | — | — | — | **PARTIAL** |

## Notes

**`hao2023rap` — author-name forms differ between sources, and neither is wrong.**
CrossRef's deposit gives `Hong, Joshua` and `Wang, Daisy`; the ACL Anthology page
and the paper itself give *Joshua Jiahua Hong* and *Daisy Zhe Wang*. The
bibliography keeps the fuller forms, because the publisher's own page is the
better authority for a personal name and CrossRef deposits routinely drop middle
names. Recorded so that a later reader who resolves the DOI and sees a shorter
list does not conclude the entry was invented.

**`cropper2022ilp30` — title, venue and DOI confirmed; the author field was not
readable in this pass.** The local console encoding could not render the háček in
*Dumančić*, so the author list was not verified here. It was verified in
`line3-cegis-ilp.md` against the CrossRef publisher deposit and the JAIR page,
where the diacritic is confirmed present — and that trace also records that DBLP
alone strips it to "Dumancic". This entry is therefore **not** independently
re-confirmed by sample B, and rests on line 3's two sources.

**Title case.** CrossRef returns Murata's title in sentence case where the
bibliography has title case, which is a rendering convention rather than a
discrepancy. No entry was changed on this basis.

**Coverage.** Four records, one of them only partly. This sample is deliberately
small and is not a substitute for `audit-sample-a.md`; it exists so that at least
some of the set was resolved by the party that had an interest in the answer being
convenient.
