# RUN_STATE — P7, §11 related work and the battery section re-derived

**Worker** APP-P7 · **branch** `agent/p7-paper-section7` · **base** `f1346fb` ·
**started** 2026-07-28T10:20:14Z · **territory** `papers`

The machine-readable record is `MANIFEST.json`. This file is the narrative.

---

## What was asked, and what happened to each piece

### (1) §11 related work — six lines, real citations

Done. `sections/11_related.md` went from 17 `[bib: TODO]` markers and a draft note
admitting every one was an unfilled obligation, to **70 records in
`papers/phase1-workshop/references.bib`, 65 of them cited, and zero markers left
anywhere in the paper** — including the one in §3 that predated this ticket.

Method: six subagents in parallel, one per line, each required to cross-verify
every record against two independent sources and to record the exact URLs and what
each source confirmed. A seventh line (Angluin, Chow) was run by this session
because one marker survived the six. Traces are in `search-traces/`, one file per
line, plus `line0-schema-attribution.md` for the Schema check the ticket asked for
in passing.

**The binding rule was: a record that cannot be confirmed twice is not cited.**
It bit four times and each refusal is recorded rather than papered over:

* the **2016 Unsolvability IPC** — a website, a GitHub repo and a booklet, but no
  DOI and no proceedings entry. Not cited.
* **Lautenbach** on linear-algebraic trap calculation — one lookup, one 429, no
  second source. Not cited.
* **Vasilevskii** — named by REVIEW alongside Chow; a 1973 Russian-language paper
  whose record varies by transliteration. Not pursued, therefore not cited, and
  §11.3 says so in the paper's own voice.
* three individual **fields** left blank rather than guessed: AAAI-15 page
  numbers, Edelkamp ECP-01 pages (two conflicting values in circulation), and
  whether Beasley has a 1985 first edition.

### (2) The battery section — re-derived against v2

Done. `sections/07_battery.md` reported v0 (26 runs, 2 arms, 29 metrics) behind a
standing note saying so. It now reports **v2: 95 runs, 5 arms, 4 games, 38
metrics, 1 433 computed values**, with every number read from
`battery/artifacts/*.json` rather than transcribed from `battery/REPORT_V2.md`
prose. Where only the report carries a statement — the 7/18 and 11/18
pre-registration scoreboard, the 450-vs-27 median steps, ρ = −0.83 — it is
attributed to the report as a report's statement.

Three things changed shape rather than scale, and those are the section's new
content:

* **the specified gradient exists now.** CC vs Schema, paired by game. Ten of 38
  metrics pair, eight are rankable, every verdict is still `underpowered`, and X3
  — the exploration family's declared signature — separates it *backwards*.
* **P1 reads opposite on the two passes**: δ = −0.750 on the model ladder,
  δ = +1.000 on the specified gradient. `discrimination.json`'s own `role` field
  says in advance that disagreement between the passes is information rather than
  noise. The honest reading, and the one written, is that P1 reads plumbing in
  both.
* **the anti-gaming register became executable.** 38 exploits, 34 still land, 17
  register entries contradicted by their own demonstration.

Two corrections carried in from `REVIEW.md` while the section was open: the
determinism citation moves from D-B-001 to **D-B-008** (and now says the test runs
against a synthetic fixture), and the X5 "independent cross-check" claim is
**dropped** rather than repaired, because both counts descend from the same
explorer.

### (3) REVIEW.md's open items, triaged

Done. `papers/phase1-workshop/REVIEW_TRIAGE.md` sorts every open item by what the
fix costs: **31 writing, 7 re-derivations from existing artefacts, 2 that need an
experiment.** `OPEN_ITEMS.md` already derived a checklist from REVIEW *and*
CITECHECK; what it did not carry is that axis.

The headline for planning: **only two items in a 529-line adversarial review need
material that does not exist**, and both are the same shortage — four paired
games (six is the floor for the sign test to reach p < 0.05 at all) and no
theory-bearing control arm (21 of 38 metrics have never been checked against any
known gradient, and adding a whole second control arm moved that count by zero).
Neither is closable in Phase 1, and the triage says so rather than listing them
as work.

---

## Adversarial checks, and what they caught

Two passes, deliberately not run by the researchers who produced the records.

**`audit-sample-a.md`** — an auditor that did not read the original traces and did
not use their URLs sampled **20 of ~37 records (54 %, against a 20 % floor)**,
choosing adversarially: records whose own note admits an ambiguity, unusual author
or venue fields, system names absent from titles, and every DOI/volume/page range
in the sample resolved directly against Crossref or DataCite.

Result: **24 clean, 1 defect, 0 unverifiable.** The defect was real —
`hao2023rap` carried arXiv's author forms on an entry whose venue, pages and DOI
all point at the EMNLP proceedings, where two authors appear without middle names.
Cross-version contamination, not invention, and fixed. It forced a rule rather
than a one-off: **where sources disagree on a personal name, follow the
proceedings of record**, which also changed `bruce2024genie`.

It also settled `hubert2026alphaproof`, whose own note said "pick a year
deliberately" and where nobody had — `year = 2025` was paired with the print
issue's volume, number and pages.

**`audit-sample-b.md`** — this session resolving four DOIs against Crossref
itself, on the principle that the assembler should not take the researchers
entirely on trust either. Three clean; the fourth could not be read locally
because the console encoding could not render a háček, which is recorded rather
than waved through.

**Two things now marked do-not-correct**, because both look like errors and are
not: AlphaGeometry's `-023-` DOI infix on a 2024 paper (Nature stamps the
submission year), and `muggleton1994ilptheory`'s `19--20` volume (a real combined
volume).

## The Schema attribution, checked independently

The ticket asked for this in passing. `baseline-arms/SCHEMA_LOCATE.md` §1.1
already reports that the canonical signing is **Zeng et al.**, not the "Feng et
al." that `Theoria.md` uses. That finding is confirmed here from sources this
session chose: the project page's own BibTeX (`@misc`, `howpublished = {Impossible
Research}`, `year = {2026}`, Zeng first, Haiwen Feng last) and, independently, a
co-author's public announcement naming Guanning Zeng as lead. Trace in
`search-traces/line0-schema-attribution.md`.

`Theoria.md` is not this track's file and is not edited. §11 now states the
correction in the paper's own voice, along with the two other facts about that
citation that matter: it is a project page with no venue, arXiv id, DOI or
released code, and its 98.98 % is self-reported.

## What went the wrong way, and is not hidden

**§7 grew from 1 953 to about 3 470 words**, and the paper is now ~22 600 words
against a workshop budget near 4 000. Some of that growth is legitimate — v2 has
three findings v0 did not — but the direction is wrong, and buying the words back
by under-reporting v2 would have been the worse trade. It is recorded as item F.6
in the triage, where it belongs: length is a whole-paper decision, not a §7 one.

**One record rests on secondary sources.** `openai.com` returns 403 to automated
fetching, so `brooks2024sora`'s contributor list was confirmed from independent
scholarly bibliographies rather than from the page. The `.bib` says so and asks
whoever finalises it to open the page once in a browser. Its publication date is
single-source and is therefore not asserted at all.

**A numbering defect found and not fixed.** The P6 renumber changed only the
`## n ·` heading line, so `sections/10_limitations.md` still numbers its
subsections 7.1–7.5. The paper therefore contains two §7.1s, and
`sections/01_intro.md:123` cross-references "§7.1" meaning the limitations one.
§11's own 8.1/8.2 headings were fixed here because that file is this ticket's; the
limitations file is not, and it is logged in the triage instead.

## Reproducibility caveat inherited from the battery

Two of the five arms live in gitignored payloads. A recompute of
`battery/artifacts/` on a clean checkout silently drops a whole arm and a whole
campaign unless `THEORIA_SCHEMA_TRACES` and `THEORIA_BASELINE_ARMS` are set. §7.1
now says this; the artefacts in the tree were produced with them set.

## Cost

Zero API calls to the game, zero game spend, zero sealed-pile reads, zero model
calls into any arm. Network was used for bibliographic verification only — DOI
resolution, catalogue and proceedings lookups.

## What the next pass should pick up, in order

1. **REVIEW issue 4** — "named, with its three pairs" overstates R-05, which names
   three *directions* and one cell. One sentence, and it is the sentence that
   turns an anecdote into evidence for the seal.
2. **The abstract**, which now trails §7. Its "no benchmark game was played for
   any result here" has to survive a §7 that reports effect sizes over four played
   games, and its "four results" framing is what REVIEW issue 14's unclosed half
   is about.
3. **The three stale-artefact transcriptions** — MDL bits (6511/90 → 5704/6), the
   Cart concept account (+2967 → 2125), and `battery/METRICS.md`'s own header,
   which still says "battery v1" against a registry of 38.
4. **`sections/10_limitations.md`'s subsection numbers**, and a sweep for the
   cross-references that now point at the wrong §7.
