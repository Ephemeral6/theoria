# Search log — 00_schema attribution check

* **Run**: `20260728T034703Z-p23`
* **Question**: is `Theoria.md`'s "Feng et al." correct, or is `baseline-arms/SCHEMA_LOCATE.md` §1.1 correct that the canonical attribution is "Zeng et al."?
* **Binding constraints**: `papers/related-work/README.md` red line 3; `baseline-arms/INCIDENTS.md` INC-BA-001.
* **Surfaces permitted**: arXiv, Semantic Scholar, DBLP, OpenReview, Google Scholar, CrossRef, OpenAlex, ORCID, authors' own academic homepages.
* **Surfaces forbidden**: `schema-harness.github.io` (any page), HuggingFace `schema-harness/arc-agi-3-schema-traces` (any file), any ARC-AGI-3 game page / walkthrough / leaderboard write-up / trajectory artefact.

## Standing mitigation applied to every WebSearch

Every `WebSearch` call in this run passed
`blocked_domains = ["schema-harness.github.io", "huggingface.co", "arcprize.org"]`.
This is belt-and-braces: it removes the prohibited surfaces from the result set
before any snippet can be rendered into context, so the "read it to judge it"
trap described in INC-BA-001 §"为什么没能事先避免" cannot fire through a snippet.

## Queries

| # | tool | query / URL | what came back |
|---|---|---|---|
| 1 | WebSearch | `Guanning Zeng arXiv` | Guanning Zeng is a real researcher, Ph.D. student at CMU. Surfaced his Google Scholar profile id `SU6ooAQAAAAJ`. No game content. |
| 2 | WebFetch | `scholar.google.com/citations?user=SU6ooAQAAAAJ&hl=en` | Profile: "Guanning Zeng (曾冠宁), Ph.D. Student, Carnegie Mellon University". 11 listed works. Entry 9 = `[SCHEMA]: Frontier Models with the Right Harness Achieve ~99% on ARC-AGI-3 Public`, **Zeng et al., 2026**. First independent hit on the attribution question. |
| 3 | WebSearch | `dblp Guanning Zeng` (allowed_domains: dblp.org) | Co-author graph only; no SCHEMA entry. |
| 4 | WebFetch | `scholar.google.com/citations?user=g5co-iIAAAAJ&hl=en` (Haiwen Feng) | "Haiwen Feng, UC Berkeley". No SCHEMA/ARC-AGI title among the 20 top-cited displayed. **Not evidence of absence** — profile default-sorts by citations and a 2026 web-only release sits below the fold. |
| 5 | WebFetch | Semantic Scholar graph API, `query=SCHEMA Frontier Models Right Harness ARC-AGI-3` | HTTP 429. |
| 6 | WebFetch | DBLP publ API, `q=Guanning Zeng` | `ECONNRESET`. |
| 7 | WebFetch | arXiv API, `au:"Guanning Zeng"`, max 60 | 9 papers, full ids+titles+authors. **None is SCHEMA.** Prompt explicitly forbade returning any abstract text. |
| 8 | WebFetch | CrossRef API, `query.bibliographic=SCHEMA harness ARC-AGI-3` | No DOI-registered SCHEMA work. Nearest hits are unrelated. Incidentally confirmed the SingularityNET comparison work (`SCHEMA_LOCATE.md` §4 路 B) as a real LNCS/AGI chapter: Rodionov, 2026, DOI `10.1007/978-3-032-33195-3_15`. |
| 9 | WebFetch | `scholar.google.com/citations?user=SU6ooAQAAAAJ&hl=en&sortby=pubdate` | Exact displayed title, truncated author string `G Zeng*, J Wang, W Ma, S Yin, C Wang, S Liu, A Kanazawa, W Ni, X Li*, ...`, source field = the project homepage URL, year 2026. Also yielded the `citation_for_view` id `YFjsv_pBGBYC`. |
| 10 | WebFetch | Semantic Scholar graph API (2nd attempt) | HTTP 429. |
| 11 | WebFetch | `scholar.google.com/citations?view_op=view_citation&...&citation_for_view=SU6ooAQAAAAJ:YFjsv_pBGBYC` | **Full author list, all 11, in order.** Publication date `2026/7`. Source = project homepage URL. See the declined-read note below regarding this page's Description field. |
| 12 | WebFetch | DBLP publ API (retry) | `ECONNRESET` again. |
| 13 | WebFetch | OpenAlex API, title search | HTTP 429, `Retry-After: 72412` (~20h). Not retried within this run. |
| 14 | WebFetch | Semantic Scholar graph API (3rd attempt) | HTTP 429. Abandoned. |
| 15 | WebSearch | `"Impossible Research" lab Haiwen Feng Xiuyu Li Andrea Zanette` | **No organisation called "Impossible Research" found.** Did confirm Feng = UC Berkeley postdoc (with Kanazawa and Darrell), PhD from MPI-IS; and Zanette = CMU (`azanette.com`). |
| 16 | WebFetch | `xiuyuli.com` (co-author's own homepage) | "Xiuyu Li, Member of Technical Staff at xAI". **Does not list the SCHEMA project.** Absence, not contradiction. |
| 17 | WebFetch | `havenfeng.github.io` (last author's own homepage) | **The second independent source.** Full author list with `*` marks, "Project release", 2026. Matches #11 exactly. |
| 18 | WebFetch | `dblp.org/search?q=Guanning+Zeng` (HTML view) | Full DBLP record, 2023–2026. **No SCHEMA / ARC-AGI entry.** Independent negative confirmation that no indexed publication exists. |
| 19 | WebFetch | arXiv API, `all:"ARC-AGI-3"`, max 60 | 14 papers. **No SCHEMA title; neither Zeng nor Feng appears as an author on any of them.** This is the strongest negative check available for "has a preprint appeared". Prompt forbade returning any abstract text. |
| 20 | WebSearch | `"Impossible Research" AI research organization Berkeley` | Returns BAIR, RDI, CHAI — no "Impossible Research". Remains unverifiable from neutral surfaces. |

## Points at which I declined to open something, and why

1. **`schema-harness.github.io` — never opened, at any point.** Its URL entered
   my context three times, unavoidably, as the *Source* metadata field of the
   Google Scholar records (#9, #11) and as a link target on the co-author
   homepage (#17). A URL string is not a page. INC-BA-001 records that this page
   puts game content near the top and materially leaked the mechanics of
   `ls20-9607627b` and `ft09-0d8bbf25` plus seven further sealed games into a
   subagent's context before that subagent could judge it unsafe. The task
   brief forbade opening it *even to read the BibTeX*. The BibTeX shape is
   therefore taken second-hand from `SCHEMA_LOCATE.md` §2.1, as instructed.

2. **HuggingFace `schema-harness/arc-agi-3-schema-traces` — never opened, never
   even queried.** `huggingface.co` was in `blocked_domains` on every search.
   Per INC-BA-001, that dataset holds a per-game `world_model_v*.py` and
   `notes.md` for **all 25** games, i.e. finished answers for the sealed pile;
   `piles.json` rule 2 makes reading those worse than playing the game.

3. **The Description/abstract field of the Google Scholar citation detail page
   (#11) — present, deliberately not transcribed.** This is the closest this run
   came to a hazard. That page carries a free-text description supplied by the
   work itself, and I had no way to know in advance whether it named specific
   games. I therefore constrained the fetch prompt to Title / Authors /
   Publication date / Source only, with an explicit instruction not to quote,
   summarise or paraphrase the Description, and to report merely that it exists.
   It came back as `Description field present, not transcribed.` **No game
   content reached my context.** Recorded here because the mitigation was
   load-bearing, not incidental.

4. **The abstracts of all 14 ARC-AGI-3 arXiv papers (#19) — not read.** I needed
   only titles and author lists for the negative check, so the fetch prompt
   forbade returning abstract text at all. Several of these are agent papers on
   the same benchmark and their abstracts are a plausible route for
   game-specific detail. Same restriction applied to #7.

5. **`arxiv.org/abs/2605.05138` (Rodionov, "Executable World Models for
   ARC-AGI-3") — not opened.** It surfaced twice (#8, #19) and is the 路 B
   candidate in `SCHEMA_LOCATE.md` §4, but it is out of scope for this run, and
   `SCHEMA_LOCATE.md` §4 路 B already warns its repository carries run artefacts
   with the same sealed-pile exposure.

6. **`arcprize.org` — blocked on every search.** Leaderboard and benchmark pages
   are explicitly out of bounds under the task brief.

## Contamination outcome

**No near-miss materialised. Zero game mechanics entered this context.** No
snippet in this run began describing the mechanics of any specific game, so the
"stop reading and record it" clause was never triggered. The only sealed-pile
identifiers that appear anywhere in this log are `ls20-9607627b` and
`ft09-0d8bbf25`, quoted from INC-BA-001 as the names of already-contaminated
games — no mechanical content attaches to them here.

This context did not touch the ARC API. Sealed-pile calls: **0**.
