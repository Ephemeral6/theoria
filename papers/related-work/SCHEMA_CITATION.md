# SCHEMA — attribution check

**Verdict: CONFIRMED.** `Theoria.md` is wrong and `baseline-arms/SCHEMA_LOCATE.md`
§1.1 is right. The canonical attribution is **Zeng et al.**, not **Feng et al.**
Guanning Zeng is first author; Haiwen Feng is eleventh and last.

* Run: `runs/20260728T034703Z-p23/00_schema/` — every query and every declined read.
* Checked: 2026-07-28. `SCHEMA_LOCATE.md`'s own check carries the same date.
* Searched under `README.md` red line 3 and `baseline-arms/INCIDENTS.md` INC-BA-001.
  **`schema-harness.github.io` and the HuggingFace trace dataset were never opened.**

---

## 1. What was claimed, and by whom

| source | attribution |
|---|---|
| `Theoria.md` (throughout) | "Feng et al." |
| `baseline-arms/SCHEMA_LOCATE.md` §1.1 | "Zeng et al." — Guanning Zeng first, Haiwen Feng last |

`SCHEMA_LOCATE.md` §1.1 gave the full list as: Guanning Zeng, Jiani Wang, Wenjie
Ma, Shaofeng Yin, Chenyang Wang, Shichen Liu, Angjoo Kanazawa, Wode Ni, Xiuyu Li,
Andrea Zanette, Haiwen Feng (Impossible Research / UC Berkeley / CMU), and §2.1
recorded that no paper exists — only a project webpage whose own BibTeX is
`@misc` / `howpublished = {Impossible Research}` / `year 2026`.

This run re-derived that from scratch, without reading `SCHEMA_LOCATE.md`'s
sources and without the prohibited page.

## 2. Field by field

### 2.1 Author list — **CONFIRMED**, exactly, all eleven, in order

> Guanning Zeng\*, Jiani Wang, Wenjie Ma, Shaofeng Yin, Chenyang Wang,
> Shichen Liu, Angjoo Kanazawa, Wode Ni, Xiuyu Li\*, Andrea Zanette\*, Haiwen Feng\*

**Source A** — Google Scholar citation record on Guanning Zeng's own profile
(`user=SU6ooAQAAAAJ`, `citation_for_view=…:YFjsv_pBGBYC`): the complete
eleven-author list in this order, publication date `2026/7`.

**Source B** — Haiwen Feng's own academic homepage, `havenfeng.github.io`: the
same eleven names in the same order, annotated "Project release", 2026.

The two agree name-for-name and position-for-position, and they are independent
(a bibliographic index vs. a co-author's self-maintained page). This satisfies
`README.md` red line 2.

**Zeng is first. Feng is last.** `Theoria.md`'s "Feng et al." names the last
author — the ordinary cause is reading a last-position senior-author credit as
the citation handle.

The `*` marks are worth carrying: `havenfeng.github.io` glosses them as
**project leads** — Zeng, Li, Zanette, Feng. Google Scholar's profile listing
independently renders `G Zeng*` and `X Li*` with the same asterisks. So Feng is
a project lead; he is simply not the first author, and "Feng et al." is still
the wrong citation form.

### 2.2 Title — **CONFIRMED**

> **`[schema]: Frontier Models with the Right Harness Achieve ~99% on ARC-AGI-3 Public`**

Both Google Scholar's profile listing and `havenfeng.github.io` render it with
the bracketed lowercase `[schema]` prefix. Google Scholar's *detail* view drops
the prefix and shows the subtitle alone ("Frontier Models with the Right Harness
Achieve ~99% on ARC-AGI-3 Public") — normal Scholar behaviour for a bracketed
leading token, not a competing title. `SCHEMA_LOCATE.md` did not record a title
at all, so this is new rather than confirmatory.

Note the title claims **~99%**, consistent with the **98.98%** that
`SCHEMA_LOCATE.md` §1 matched verbatim against `Theoria.md`.

### 2.3 Year and publication type — **CONFIRMED**: 2026, web-only, not a paper

Google Scholar gives publication date **2026/7** (July 2026) and, in place of a
venue, the project homepage URL. `havenfeng.github.io` calls it a **"Project
release"**. Three independent negative checks agree there is no paper:

| index | result |
|---|---|
| arXiv API, `au:"Guanning Zeng"` | 9 papers, none is SCHEMA |
| arXiv API, `all:"ARC-AGI-3"` | 14 papers; no SCHEMA title, and neither Zeng nor Feng is an author on any |
| DBLP, full record for Guanning Zeng | 2023–2026 complete; no SCHEMA / ARC-AGI entry |
| CrossRef, bibliographic query | no DOI-registered SCHEMA work |

This upholds `README.md` red line 4 and `SCHEMA_LOCATE.md` §2.1's hard
constraint: **there is no arXiv id to cite, and none may be invented.**

### 2.4 Has a preprint or peer-reviewed version appeared since? — **NO**

`SCHEMA_LOCATE.md`'s check was dated 2026-07-28; so is this one, so the window
for change was nil. Stated explicitly for the next re-check: as of 2026-07-28
the arXiv listing for `ARC-AGI-3` contains 14 papers and SCHEMA is not among
them, and Guanning Zeng's DBLP record ends at three 2026 CoRR entries, none of
them SCHEMA. **Status unchanged: web-only.**

Anyone re-running this needs only queries #18 and #19 in the search log.

### 2.5 Affiliations — **PARTIALLY CONFIRMED**

`SCHEMA_LOCATE.md` §1.1 gives "Impossible Research / UC Berkeley / CMU". Split
verdict, because the three are not equally checkable:

| claim | verdict | source |
|---|---|---|
| **CMU** | CONFIRMED | Guanning Zeng's Google Scholar profile states "Ph.D. Student, Carnegie Mellon University". Andrea Zanette's own site `azanette.com` is titled "Andrea Zanette – Carnegie Mellon University". |
| **UC Berkeley** | CONFIRMED | Haiwen Feng's Google Scholar profile and `havenfeng.github.io` both give UC Berkeley (postdoc with Angjoo Kanazawa and Trevor Darrell). Kanazawa, a co-author, is UC Berkeley faculty. |
| **Impossible Research** | **UNCONFIRMED** | See §3. |

One correction to `SCHEMA_LOCATE.md` §1.1, offered as refinement rather than
rebuttal: co-author **Xiuyu Li**'s homepage `xiuyuli.com` currently gives his
affiliation as **Member of Technical Staff at xAI**, and that page does not list
the SCHEMA project at all. Whether xAI is an affiliation *of the work* or simply
where Li is now is not determinable from a neutral surface, so **no xAI
affiliation is asserted here** — it is recorded only so a later reader does not
mistake the omission for an oversight.

No per-author affiliation is asserted in the BibTeX entry, because BibTeX has no
honest field for a partially-verified institutional triple.

---

## 3. What could not be confirmed, and why

**`howpublished = {Impossible Research}` — UNCONFIRMED by independent search.**

This is the one field where the prohibition bit. The string's only known source
is the BibTeX block published on `schema-harness.github.io`, and **that page is
off limits** — INC-BA-001 records it leaking the mechanics of nine sealed games
into a subagent's context, including substantive leaks on `ls20-9607627b` and
`ft09-0d8bbf25`, because it puts game content near the top and a page must be
read before it can be judged safe. The task brief forbade opening it *even to
read the BibTeX*.

Independent attempts to corroborate "Impossible Research" as an organisation
returned nothing: two targeted searches (log #15, #20) surfaced no such lab or
company, and none of the co-author profiles I read names it. That is a null
result, not a refutation — a small or newly-named research collective can be
absent from indexes without being fictitious, and the two verifiable
institutional threads (Berkeley, CMU) are exactly what an ad-hoc collective of
these particular authors would look like.

Accordingly the field is carried **second-hand on `SCHEMA_LOCATE.md` §2.1's
authority**, which the task brief designated as the source of record for that
BibTeX's shape, and it is flagged as single-sourced both here and in
`lines/00_schema.bib`. It is the only field in the entry that does not meet red
line 2's two-source bar.

Also unconfirmed, and unimportant: whether the canonical rendering is `[schema]`
or `[SCHEMA]`; and the exact per-author affiliation mapping.

Two intended sources were **unavailable for infrastructure reasons, not
prohibited ones** — Semantic Scholar returned HTTP 429 on three attempts and
OpenAlex returned 429 with `Retry-After: ~20h`. Neither was needed: the
two-source bar was met without them. A later re-check should try them first,
since they would independently settle §2.5 if either has indexed the work.

---

## 4. Recommended citation

Entry lives in `lines/00_schema.bib`. Cite as `@misc`, key `zeng2026schema`,
**no arXiv id, no venue, no DOI** — because none exists.

In prose: **"Zeng et al. (2026)"**. Never "Feng et al."

## 5. Correction owed to `Theoria.md` — recorded, not applied

**`Theoria.md` must be corrected from "Feng et al." to "Zeng et al."**

**Not done in this run.** `Theoria.md` is not this run's territory, and
`SCHEMA_LOCATE.md` §1.1 already declined the same edit on the same grounds
("`Theoria.md` 不属本轨道，不代改"). This is the second independent record of the
same outstanding correction; it is now confirmed rather than merely reported,
and it should be applied by whoever owns `Theoria.md`.

Scope of the fix, for whoever takes it: every occurrence of "Feng et al." as the
handle for SCHEMA. `SCHEMA_LOCATE.md` §1 established by grep that `Theoria.md`
carries **no citations at all** — no arXiv id, no URL, no reference section — so
the correction is confined to the inline attribution, and any bibliography added
later must use §4's `@misc` form rather than an invented arXiv id.
