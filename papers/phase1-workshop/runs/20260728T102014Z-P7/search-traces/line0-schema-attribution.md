# Search trace — the Schema attribution, verified independently

**Why this file exists.** The P7 ticket asks, in passing, for the canonical
authorship of the Schema system to be checked: `baseline-arms/SCHEMA_LOCATE.md`
§1.1 reports that `Theoria.md` and several work orders write **Feng et al.**,
while the canonical signing is **Zeng et al.** This trace is a *second,
independent* confirmation of that finding, run from this session rather than
inherited from `baseline-arms/`.

Run 2026-07-28, tool: WebSearch + WebFetch.

---

## Queries

1. `Schema harness ARC-AGI-3 world model Zeng Impossible Research 98.98`
2. `"Guanning Zeng" Schema harness bibtex misc Impossible Research 2026 cite`
3. WebFetch on `https://schema-harness.github.io/` — **failed**: the page returned
   base64 image payloads and fragmented text to the fetcher; no author list, no
   BibTeX block recoverable. Recorded rather than retried, so the record is not
   mistaken for a direct read of the source page.
4. WebFetch on `https://news.ycombinator.com/item?id=48935905` — no authorship
   information in the thread. Useful only as a negative: the discussion's own
   complaint is that the release carries no author list, no code, and no paper.

## Source A — the project page's own BibTeX, surfaced through search

`https://schema-harness.github.io/` (via query 2). Entry type `@misc`, key
`schema2026`, `howpublished = {Impossible Research}`, `year = {2026}`. Author
field, in order:

> Zeng, Guanning and Wang, Jiani and Ma, Wenjie and Yin, Shaofeng and Wang,
> Chenyang and Liu, Shichen and Kanazawa, Angjoo and Ni, Wode and Li, Xiuyu and
> Zanette, Andrea and Feng, Haiwen

Title as given: `[schema]: Frontier Models with the Right Harness Achieve ~99% on
ARC-AGI-3 Public`.

**Confirms:** Zeng is first author; Feng is last; the record is an `@misc` with no
venue.

## Source B — a co-author's public announcement

`https://x.com/Zanette_ai/status/2077793189608775728`. Andrea Zanette — the
tenth-listed author — announces the work and writes: "Led by my incoming PhD
student @guanningzeng, together with an amazing team!"

**Confirms, independently of the project page:** Guanning Zeng leads the work.
This is a co-author's own statement, not a redescription of the page.

## Source C — third-party coverage (corroborating, not load-bearing)

`https://digg.com/tech/3a488ugi` and the search engine's own summary both give
the affiliations as Impossible Research / UC Berkeley / CMU, and the score pair as
**42.83 % → 98.98 % RHAE** on the 25 public games. Consistent with
`Theoria.md`'s "+56pp", and with `baseline-arms/SCHEMA_LOCATE.md` §1.

---

## Verdict

**CONFIRMED, two independent sources.** `Feng et al.` is wrong; the canonical
signing is **Zeng et al.**, with Haiwen Feng in last position.

## What may and may not be written

* **May:** `@misc`, `Zeng, Guanning and …`, `howpublished = {Impossible Research}`,
  `year = {2026}`, `url = {https://schema-harness.github.io/}`.
* **Must not:** an arXiv id, a DOI, or a venue. There is none.
  `baseline-arms/SCHEMA_LOCATE.md` §2.1 states this as a hard constraint and this
  trace found nothing to soften it: the Hacker News thread's own complaint is the
  absence of a paper and of code.
* **Must not:** treat 98.98 % as a measurement made here. It is self-reported on
  the public set, not independently verified by ARC Prize, and no arm of this
  paper was run against Schema. §11 already says so and the sentence stays.

## Note for the theory-compiler track

`Theoria.md` writes `Feng et al.` and is not this track's file to edit.
`baseline-arms/SCHEMA_LOCATE.md` §1.1 already records the correction for that
track; this trace is a second confirmation of it and changes nothing about who
owns the fix.

## Sources

* [schema-harness.github.io](https://schema-harness.github.io/)
* [Zanette announcement (X)](https://x.com/Zanette_ai/status/2077793189608775728)
* [Digg coverage](https://digg.com/tech/3a488ugi)
* [Hacker News thread](https://news.ycombinator.com/item?id=48935905)
