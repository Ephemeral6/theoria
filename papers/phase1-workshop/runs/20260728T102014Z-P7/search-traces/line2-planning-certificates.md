# Search trace — Line 2: certificates and admissible heuristics in classical planning

Run: `20260728T102014Z-P7`. Compiled 2026-07-28.
Scope: the `[bib: TODO]` in `papers/phase1-workshop/sections/11_related.md` §8.2, first
bullet ("Unsolvability certificates and admissible heuristics in planning"), plus the
provenance of the term *pagoda function* used by `engine-rig/engines/lp_potential`.

## Method and its limits — read this before trusting anything below

Every record below was checked against **two independent sources**. What counted as a
source, and what did not:

* **Publisher / proceedings landing page** — `ojs.aaai.org` (AAAI and ICAPS proceedings),
  `jair.org`, `ebooks.iospress.nl`, `aaai.org/ocs` (ECP-01 proceedings). Fetched and read.
* **Crossref REST API** (`api.crossref.org`) — queried directly, results transcribed below.
* **Semantic Scholar Graph API** (`api.semanticscholar.org`) — used where it responded;
  it rate-limited (HTTP 429) on most calls from this host, so it appears only in some entries.
* **Primary-document bibliographies** — for the pagoda line, the reference lists of three
  independent peer-reviewed / archived peg-solitaire papers, read out of the actual PDFs.
* **Conference programme documents** — the ECP-01 call-for-participation brochure.

Sources that were **not available** and therefore appear nowhere below:

* **DBLP** — `dblp.org` is unreachable from this host at the network layer. `curl` returns
  HTTP code `000` (connection failure, not 403/429); WebFetch returns `ECONNRESET`. Both the
  JSON API and the HTML record pages fail. DBLP keys quoted below are the ones **reported by
  the Semantic Scholar API's `externalIds` field**, not values read off DBLP itself, and are
  labelled as such.
* **OpenAlex** — daily quota exhausted (`{"error":"Rate limit exceeded", "dailyRemainingUsd":0}`).
* **openlibrary.org** and **archive.org** — DNS on this host resolves both to unrelated
  addresses (`31.13.73.169`, `199.96.63.53`); connections are refused. No library-catalogue
  record could be obtained for either book.
* **Wiley Online Library** returned HTTP 402 for the Culberson & Schaeffer article page;
  **loc.gov** returned 403; **Routledge** connection-refused; **tandfonline** 403.

Where a field could not be confirmed twice it is marked **UNVERIFIED** and is **omitted from
the BibTeX record** rather than guessed. No field below was filled in from memory.

Summary: **13 CONFIRMED, 1 DROPPED.**

---

## C1 — Pommerening, Helmert, Röger & Seipp, AAAI 2015

**Queries run**
* WebSearch: `"From Non-Negative to General Operator Cost Partitioning" AAAI 2015 Pommerening Helmert`
* Crossref: `query.bibliographic=From Non-Negative to General Operator Cost Partitioning`
* DBLP (`/search/publ/api` and `/rec/conf/aaai/PommereningHRS15`) — **failed, host unreachable**
* Semantic Scholar by DOI — **HTTP 404** for `10.1609/aaai.v29i1.9668` (five attempts); S2 does
  not appear to index this DOI. Not used.

**Source A** — https://ojs.aaai.org/index.php/AAAI/article/view/9668
Confirmed: title *From Non-Negative to General Operator Cost Partitioning*; authors Florian
Pommerening, Malte Helmert, Gabriele Röger, Jendrik Seipp, in that order; Proceedings of the
AAAI Conference on Artificial Intelligence, Vol. 29 No. 1; year 2015; DOI
`10.1609/aaai.v29i1.9668`; section "Main Track: Planning and Scheduling", Twenty-Ninth AAAI
Conference on Artificial Intelligence. Page range **not shown**.

**Source B** — `https://api.crossref.org/works?query.bibliographic=From+Non-Negative+to+General+Operator+Cost+Partitioning`
Confirmed independently: same exact title; same four authors in the same order; container
"Proceedings of the AAAI Conference on Artificial Intelligence"; volume 29; issued
`2015-03-04`; publisher AAAI; DOI `10.1609/aaai.v29i1.9668`. Crossref's `page` field is empty.

**Source C (page numbers, failed)** — https://aaai.org/papers/9668-from-non-negative-to-general-operator-cost-partitioning/
Confirmed title, the same four authors, "The Twenty-Ninth Conference on Artificial
Intelligence (AAAI 2015)", year 2015. Page numbers **not shown**.
A WebSearch summary asserted "pages 3335–3341"; that figure appears in **no** source I fetched
directly, so it is **UNVERIFIED** and omitted.

**VERDICT: CONFIRMED** (pages UNVERIFIED, omitted).

```bibtex
@inproceedings{pommerening-et-al-aaai2015,
  author    = {Florian Pommerening and Malte Helmert and Gabriele R{\"o}ger and Jendrik Seipp},
  title     = {From Non-Negative to General Operator Cost Partitioning},
  booktitle = {Proceedings of the Twenty-Ninth {AAAI} Conference on Artificial Intelligence
               ({AAAI} 2015)},
  volume    = {29},
  year      = {2015},
  publisher = {{AAAI} Press},
  doi       = {10.1609/aaai.v29i1.9668}
}
```

---

## C2 — Seipp, Pommerening & Helmert, ICAPS 2015

**Queries run**
* Crossref: `query.bibliographic=New Optimization Functions for Potential Heuristics`
* DBLP — **failed, host unreachable**
* Semantic Scholar title search — HTTP 429 on all four attempts. Not used.

**Source A** — https://ojs.aaai.org/index.php/ICAPS/article/view/13714
Confirmed: title *New Optimization Functions for Potential Heuristics*; authors Jendrik Seipp,
Florian Pommerening, Malte Helmert (all University of Basel), in that order; Proceedings of the
International Conference on Automated Planning and Scheduling, Vol. 25 No. 1; year 2015;
pages 193–201; DOI `10.1609/icaps.v25i1.13714`.

**Source B** — Crossref API, same query.
Confirmed independently: identical title; same three authors in the same order; container
"Proceedings of the International Conference on Automated Planning and Scheduling"; volume 25;
issued `2015-04-08`; page `193-201`; publisher AAAI; DOI `10.1609/icaps.v25i1.13714`.

**VERDICT: CONFIRMED.**

```bibtex
@inproceedings{seipp-et-al-icaps2015,
  author    = {Jendrik Seipp and Florian Pommerening and Malte Helmert},
  title     = {New Optimization Functions for Potential Heuristics},
  booktitle = {Proceedings of the Twenty-Fifth International Conference on Automated
               Planning and Scheduling ({ICAPS} 2015)},
  volume    = {25},
  pages     = {193--201},
  year      = {2015},
  publisher = {{AAAI} Press},
  doi       = {10.1609/icaps.v25i1.13714}
}
```

---

## C3 — Pommerening, Röger, Helmert & Bonet, ICAPS 2014

**Queries run**
* Crossref: `query.bibliographic=LP-Based Heuristics for Cost-Optimal Planning`
* DBLP — **failed, host unreachable**
* Semantic Scholar — HTTP 429. Not used.

**Source A** — https://ojs.aaai.org/index.php/ICAPS/article/view/13621
Confirmed: title *LP-Based Heuristics for Cost-Optimal Planning* (note the capitalised
hyphenated "LP-Based", which is easy to garble as "LP-based"); authors Florian Pommerening,
Gabriele Röger, Malte Helmert, Blai Bonet, in that order; Vol. 24 No. 1; year 2014;
pages 226–234; DOI `10.1609/icaps.v24i1.13621`.

**Source B** — Crossref API, same query.
Confirmed independently: identical title; same four authors in the same order; container
"Proceedings of the International Conference on Automated Planning and Scheduling"; volume 24;
issued `2014-05-11`; page `226-234`; publisher AAAI; DOI `10.1609/icaps.v24i1.13621`.

**VERDICT: CONFIRMED.**

```bibtex
@inproceedings{pommerening-et-al-icaps2014,
  author    = {Florian Pommerening and Gabriele R{\"o}ger and Malte Helmert and Blai Bonet},
  title     = {{LP}-Based Heuristics for Cost-Optimal Planning},
  booktitle = {Proceedings of the Twenty-Fourth International Conference on Automated
               Planning and Scheduling ({ICAPS} 2014)},
  volume    = {24},
  pages     = {226--234},
  year      = {2014},
  publisher = {{AAAI} Press},
  doi       = {10.1609/icaps.v24i1.13621}
}
```

---

## C4 — Helmert & Domshlak, ICAPS 2009 (LM-cut)

**Queries run**
* Crossref: `query.bibliographic=Landmarks, Critical Paths and Abstractions: What's the Difference Anyway?`
* DBLP — **failed, host unreachable**
* Semantic Scholar — HTTP 429. Not used.

**Source A** — https://ojs.aaai.org/index.php/ICAPS/article/view/13370
Confirmed: title *Landmarks, Critical Paths and Abstractions: What's the Difference Anyway?*
(comma after "Landmarks", no Oxford comma before "and Abstractions", colon before "What's",
question mark at the end); authors Malte Helmert, Carmel Domshlak, in that order; Vol. 19 No. 1;
year 2009; pages 162–169; DOI `10.1609/icaps.v19i1.13370`; Nineteenth International Conference
on Automated Planning and Scheduling. The landing page also confirms this is the paper that
introduces the landmark cut heuristic.

**Source B** — Crossref API, same query.
Confirmed independently: identical title character-for-character; same two authors in the same
order; container "Proceedings of the International Conference on Automated Planning and
Scheduling"; volume 19; issued `2009-10-16`; page `162-169`; publisher AAAI; DOI
`10.1609/icaps.v19i1.13370`.

**VERDICT: CONFIRMED.**

```bibtex
@inproceedings{helmert-domshlak-icaps2009,
  author    = {Malte Helmert and Carmel Domshlak},
  title     = {Landmarks, Critical Paths and Abstractions: What's the Difference Anyway?},
  booktitle = {Proceedings of the Nineteenth International Conference on Automated
               Planning and Scheduling ({ICAPS} 2009)},
  volume    = {19},
  pages     = {162--169},
  year      = {2009},
  publisher = {{AAAI} Press},
  doi       = {10.1609/icaps.v19i1.13370}
}
```

---

## C5 — Culberson & Schaeffer, *Computational Intelligence* 1998 (pattern databases)

**Queries run**
* Crossref: `query.bibliographic=Pattern Databases Culberson Schaeffer Computational Intelligence`
* Semantic Scholar by DOI: `DOI:10.1111/0824-7935.00065`
* Wiley Online Library article page — **HTTP 402 Payment Required**, could not be read.
* DBLP — **failed, host unreachable**

**Source A** — `https://api.crossref.org/works?query.bibliographic=Pattern+Databases+Culberson+Schaeffer+Computational+Intelligence`
Confirmed: title *Pattern Databases*; authors Joseph C. Culberson, Jonathan Schaeffer, in that
order; container "Computational Intelligence"; volume 14; page `318-334`; issued `1998-08`;
publisher Wiley; DOI `10.1111/0824-7935.00065`; type journal-article.

**Source B** — `https://api.semanticscholar.org/graph/v1/paper/DOI:10.1111/0824-7935.00065`
Confirmed independently: title *Pattern Databases*; authors J. Culberson, J. Schaeffer; year
1998; `journal.name` = "Computational Intelligence", `journal.volume` = "14"; ISSN `0824-7935`;
`externalIds.DBLP` = `journals/ci/CulbersonS98`; `externalIds.DOI` = `10.1111/0824-7935.00065`.

**Caveat recorded, not suppressed.** S2's top-level `venue` string for this record reads
"International Conference on Climate Informatics" — an S2 venue-merge artefact caused by the
"CI" / "Comput Intell" abbreviation collision (the same `publicationVenue` object lists
"Computational Intelligence" among its `alternate_names`, carries the journal's ISSN
`0824-7935`, and points at the Wiley journal page). The `journal` field, the ISSN and the
DBLP key `journals/ci/...` all agree with Crossref, so the venue is *Computational
Intelligence*. The garbled `venue` string is noted here so nobody later "corrects" this
entry into the wrong venue.

Precursor paper, deliberately **not** cited: Culberson & Schaeffer, "Searching with pattern
databases", LNCS / Advances in Artificial Intelligence 1996, pp. 402–416, DOI
`10.1007/3-540-61291-2_68` (seen in the same Crossref result set). The 1998 journal article is
the canonical reference.

**VERDICT: CONFIRMED.** (Issue number UNVERIFIED — neither source reported one; omitted.)

```bibtex
@article{culberson-schaeffer-1998,
  author  = {Joseph C. Culberson and Jonathan Schaeffer},
  title   = {Pattern Databases},
  journal = {Computational Intelligence},
  volume  = {14},
  pages   = {318--334},
  year    = {1998},
  doi     = {10.1111/0824-7935.00065}
}
```

---

## C6 — Edelkamp, ECP-01 (planning with pattern databases)

This one needed a different second source: **Crossref has no record of it** (the query returned
only unrelated later Edelkamp papers), and Semantic Scholar's record is unusable — its top hit
"Planning with Pattern Databases / S. Edelkamp" carries `year: 2014`, an empty `venue`, and no
DOI, i.e. a MAG-derived stub with the wrong year. Neither was used.

**Queries run**
* Crossref: `query.bibliographic=Planning with Pattern Databases Edelkamp` — **no matching record**
* Semantic Scholar title search — record found but **rejected as unreliable** (see above)
* WebSearch: `Edelkamp "Planning with Pattern Databases" ECP 2001 Sixth European Conference on Planning proceedings pages`

**Source A** — https://www.aaai.org/ocs/index.php/ECP/ECP01/paper/view/7280
(AAAI's hosted ECP-01 proceedings.) Confirmed: title *Planning with Pattern Databases*; author
Stefan Edelkamp; "Proceedings of the Sixth European Conference on Planning (ECP-01)"; year 2001;
publication date 25 October 2001; track "Long Papers".

**Source B** — https://ecp01.icaps-conference.org/Brochure.pdf
(The ECP-01 call-for-participation brochure and programme, read out of the PDF directly rather
than through the fetcher's text extraction.) Confirmed: **"6th European Conference on Planning
(ECP-01), Toledo, Spain, September 12–14, 2001"**, Programme Chair Amedeo Cesta, Local
Arrangements Chair Daniel Borrajo. The Wednesday 12 September programme, session "Domain
Independent Planning 1" (10:30–11:20), lists: *"S. Edelkamp, Planning with Pattern Databases"*.
This independently confirms author, exact title, venue and year.

**Page numbers: UNVERIFIED and omitted.** A WebSearch summary reported "pages 13–24" and also
noted a competing "13–34" in circulation. Neither number appears in any source I fetched
directly. Two conflicting values from an unfetched source is exactly the situation this trace
exists to prevent, so no page range is recorded.

**VERDICT: CONFIRMED** (pages UNVERIFIED, omitted).

```bibtex
@inproceedings{edelkamp-ecp2001,
  author    = {Stefan Edelkamp},
  title     = {Planning with Pattern Databases},
  booktitle = {Proceedings of the Sixth European Conference on Planning ({ECP} 2001)},
  address   = {Toledo, Spain},
  year      = {2001}
}
```

---

## C7 — Eriksson, Röger & Helmert, ICAPS 2017 (unsolvability certificates)

**Queries run**
* Crossref: `query.bibliographic=Unsolvability Certificates for Classical Planning`
* Semantic Scholar title search (same string)
* DBLP — **failed, host unreachable**

**Source A** — https://ojs.aaai.org/index.php/ICAPS/article/view/13818
Confirmed: title *Unsolvability Certificates for Classical Planning*; authors Salomé Eriksson,
Gabriele Röger, Malte Helmert, in that order; Vol. 27 No. 1; year 2017; pages 88–97; DOI
`10.1609/icaps.v27i1.13818`; publication date 5 June 2017. Abstract confirms the topic:
solvable-task plans are routinely validated, whereas for unsolvable tasks no such validation
capability existed.

**Source B** — Crossref API, same query. Confirmed independently: identical title; same three
authors in the same order; container "Proceedings of the International Conference on Automated
Planning and Scheduling"; volume 27; issued `2017-06-05`; page `88-97`; DOI
`10.1609/icaps.v27i1.13818`.

**Source C** — `https://api.semanticscholar.org/graph/v1/paper/search?query=Unsolvability+Certificates+for+Classical+Planning`
Third confirmation: title, year 2017, venue "International Conference on Automated Planning and
Scheduling", `journal.pages` `88-97`, authors Salomé Eriksson / Gabriele Röger / M. Helmert,
`externalIds.DBLP` = `conf/aips/ErikssonRH17`, `externalIds.DOI` = `10.1609/icaps.v27i1.13818`.

Related work seen and **not** cited (recorded so it is not re-found later as if new): Eriksson,
Röger & Helmert, "Inductive Certificates of Unsolvability for Domain-Independent Planning",
IJCAI-18, pp. 5244–5248, DOI `10.24963/ijcai.2018/730`; and Röger, "Towards Certified
Unsolvability in Classical Planning", IJCAI-17, pp. 5141–5145, DOI `10.24963/ijcai.2017/738`
(single-author sister-conference/abstract track). Both are Crossref-visible if wanted.

**VERDICT: CONFIRMED.**

```bibtex
@inproceedings{eriksson-et-al-icaps2017,
  author    = {Salom{\'e} Eriksson and Gabriele R{\"o}ger and Malte Helmert},
  title     = {Unsolvability Certificates for Classical Planning},
  booktitle = {Proceedings of the Twenty-Seventh International Conference on Automated
               Planning and Scheduling ({ICAPS} 2017)},
  volume    = {27},
  pages     = {88--97},
  year      = {2017},
  publisher = {{AAAI} Press},
  doi       = {10.1609/icaps.v27i1.13818}
}
```

---

## C8 — Eriksson, Röger & Helmert, ICAPS 2018 (proof system)

**Queries run**
* Crossref: `query.bibliographic=A Proof System for Unsolvable Planning Tasks`
* Semantic Scholar — HTTP 429 on all four attempts. Not used.
* DBLP — **failed, host unreachable**

**Source A** — https://ojs.aaai.org/index.php/ICAPS/article/view/13899
Confirmed: title *A Proof System for Unsolvable Planning Tasks*; authors Salomé Eriksson,
Gabriele Röger, Malte Helmert, in that order; Vol. 28 No. 1; year 2018; pages 65–73; DOI
`10.1609/icaps.v28i1.13899`.

**Source B** — Crossref API, same query. Confirmed independently: identical title; same three
authors in the same order; container "Proceedings of the International Conference on Automated
Planning and Scheduling"; volume 28; issued `2018-06-15`; page `65-73`; publisher AAAI; DOI
`10.1609/icaps.v28i1.13899`.

**VERDICT: CONFIRMED.**

```bibtex
@inproceedings{eriksson-et-al-icaps2018,
  author    = {Salom{\'e} Eriksson and Gabriele R{\"o}ger and Malte Helmert},
  title     = {A Proof System for Unsolvable Planning Tasks},
  booktitle = {Proceedings of the Twenty-Eighth International Conference on Automated
               Planning and Scheduling ({ICAPS} 2018)},
  volume    = {28},
  pages     = {65--73},
  year      = {2018},
  publisher = {{AAAI} Press},
  doi       = {10.1609/icaps.v28i1.13899}
}
```

---

## C9 — Hoffmann, Kissmann & Torralba, ECAI 2014 (unsolvability heuristics)

**Queries run**
* Crossref: `query.bibliographic=Distance Who Cares Tailoring Merge-and-Shrink Heuristics to Detect Unsolvability`
* Semantic Scholar — HTTP 429. Not used.
* DBLP — **failed, host unreachable**

**Source A** — Crossref API, above query.
Confirmed: title returned HTML-escaped as `&ldquo;Distance&rdquo;? Who Cares? Tailoring
Merge-and-Shrink Heuristics to Detect Unsolvability` — i.e. the word *Distance* is in
typographic double quotes inside the title; container "ECAI 2014" in the series "Frontiers in
Artificial Intelligence and Applications"; year 2014; publisher IOS Press; DOI
`10.3233/978-1-61499-419-0-441`. Crossref's author names are mangled by the same HTML-entity
problem (`Hoffmann J&ouml;rg`, `Kissmann Peter`, `Torralba &Aacute;lvaro`) and are recorded
here only as evidence of *which* names, not of their order or spelling.

**Source B** — https://ebooks.iospress.nl/doi/10.3233/978-1-61499-419-0-441
(IOS Press, the publisher.) Confirmed and **corrects** Crossref's mangling: authors are
**Jörg Hoffmann, Peter Kissmann, Álvaro Torralba**, given-name-first, in that order; book
ECAI 2014; series Frontiers in Artificial Intelligence and Applications, volume 263; year 2014;
pages 441–446; DOI `10.3233/978-1-61499-419-0-441`; publisher IOS Press.

**VERDICT: CONFIRMED.** The title's internal quotation marks around *Distance* are real; both
sources carry them and they must survive into the bibliography.

```bibtex
@inproceedings{hoffmann-et-al-ecai2014,
  author    = {J{\"o}rg Hoffmann and Peter Kissmann and {\'A}lvaro Torralba},
  title     = {``{D}istance''? {W}ho Cares? {T}ailoring Merge-and-Shrink Heuristics to
               Detect Unsolvability},
  booktitle = {Proceedings of the Twenty-First European Conference on Artificial
               Intelligence ({ECAI} 2014)},
  series    = {Frontiers in Artificial Intelligence and Applications},
  volume    = {263},
  pages     = {441--446},
  year      = {2014},
  publisher = {{IOS} Press},
  doi       = {10.3233/978-1-61499-419-0-441}
}
```

---

## C10 — Helmert, JAIR 2006 (Fast Downward)

**Queries run**
* Crossref: `query.bibliographic=The Fast Downward Planning System Helmert Journal of Artificial Intelligence Research`
* Semantic Scholar by DOI: `DOI:10.1613/jair.1705`
* DBLP — **failed, host unreachable**

**Source A** — https://www.jair.org/index.php/jair/article/view/10457
(JAIR, the publisher.) Confirmed: title *The Fast Downward Planning System*; author M. Helmert;
Journal of Artificial Intelligence Research; volume 26; year 2006; DOI `10.1613/jair.1705`;
publication date 12 July 2006. Page range **not shown on the landing page**. Abstract confirms
the causal graph heuristic, multi-valued planning tasks, and the win in the classical track of
IPC-4 at ICAPS 2004.

**Source B** — Crossref API, above query. Confirmed independently: identical title; author
M. Helmert; container "Journal of Artificial Intelligence Research"; volume 26; page `191-246`;
issued `2006-07-12`; publisher AI Access Foundation; DOI `10.1613/jair.1705`.

**Source C** — `https://api.semanticscholar.org/graph/v1/paper/DOI:10.1613/jair.1705`
Third confirmation of title, year 2006, `publicationVenue` = "Journal of Artificial Intelligence
Research" (type: journal, ISSN `1076-9757`), author M. Helmert, DOI `10.1613/jair.1705`.
Note: S2 additionally links `arXiv:1109.6051` and DBLP key `journals/corr/abs-1109-6051` — that
is the arXiv deposit of the same article, not a separate publication; do not cite it separately.

Page range `191--246` rests on Crossref alone among the sources I fetched, but is consistent
with JAIR volume 26 and is the universally used range; it is included with that noted.

**VERDICT: CONFIRMED.**

```bibtex
@article{helmert-jair2006,
  author  = {Malte Helmert},
  title   = {The Fast Downward Planning System},
  journal = {Journal of Artificial Intelligence Research},
  volume  = {26},
  pages   = {191--246},
  year    = {2006},
  doi     = {10.1613/jair.1705}
}
```

---

## C11 — Berlekamp, Conway & Guy, *Winning Ways* (provenance of "pagoda function")

This is the entry the brief flagged for extra care, so the trace is correspondingly long. Two
questions were separated and answered separately: **(i) is "pagoda function" really theirs?**
and **(ii) what is the correct bibliographic record for the book?**

### (i) Attribution of the term — three independent primary sources

**Source A** — Jefferson, Miguel, Miguel & Tarim, "Modelling and Solving English Peg Solitaire"
(the authors' PDF at https://hugues-talbot.github.io/files/Peg_Solitaire_1.pdf; the refereed
version is *Computers & Operations Research*, ScienceDirect `S0305054805000195`). Page 2,
introduction, reads: *"the major results on Peg Solitaire can be found in ... Berlekamp, Conway
and Guy [5] on the necessary conditions for feasibility, using Pagoda functions"*. Its
reference list, page 25, entry [5], verbatim:

> [5] E.R. Berlekamp, J.H. Conway, R.K. Guy. Winning ways for your mathematical plays, vol.2:
> games in particular. Academic Press, London, 1982. p. 729-730.

and entry [3], verbatim:

> [3] J. D. Beasley. The ins and outs of peg solitaire. Oxford University Press, Oxford, 1992.

**Source B** — Kiyomi & Matsui, "Integer Programming Based Algorithms for Peg Solitaire
Problems", RIMS Kôkyûroku 1185 (2001), pp. 100–108
(https://www.kurims.kyoto-u.ac.jp/~kyodo/kokyuroku/contents/pdf/1185-11.pdf). Page 101:
*"In the well-known book 'Winning ways for Mathematical Plays [3]', Berlekamp, Conway and Guy
discussed variations of problems related to peg solitaire problems. They showed the
infeasibility of the peg solitaire problem 'sending scout 5 paces out into desert' by using the
pagoda function approach."* Page 102, §3, repeats: *"In [3], Berlekamp, Conway and Guy proposed
the pagoda function approach for showing the infeasibility of some peg solitaire problems."*
Its reference list, page 107, entry [3], verbatim:

> [3] Berlekamp, E. R., Conway, J. H., and Guy, R. K.: Winning Ways for Mathematical Plays.
> Academic Press, London, 1982.

This source also supplies the definition that matches `engine-rig/engines/lp_potential` exactly
(page 102): a real-valued `pag : {1..n} → R` on holes is a *pagoda function* when every
vertically or horizontally consecutive triple `(i1,i2,i3)` satisfies
`pag(i1) + pag(i2) ≥ pag(i3)`; then `pag(p) ≥ pag(p')` whenever `p'` follows `p` by a jump, so
`pag(p_s) < pag(p_f)` proves the instance infeasible. Kiyomi & Matsui also record (their
reference [7]) that E. Kanno's 1997 Tokyo bachelor thesis gave a linear-programming algorithm
for finding a pagoda function — the earliest LP formulation I found, in Japanese and not
independently verifiable, so it is **not** cited.

**Source C** — G. I. Bell, "Designing peg solitaire puzzles", arXiv:1608.01609v3 (9 Sep 2017),
reference list page 13, entry [2], verbatim:

> [2] E. Berlekamp, J. Conway and R. Guy, Purging pegs properly, in *Winning Ways for Your
> Mathematical Plays*, 2nd ed., Vol. 4, Chap. 23: 803–841, A K Peters, 2004.

This names the chapter — **chapter 23, "Purging Pegs Properly"** — and locates it in the second
edition's Volume 4.

Three independent sources, two of them peer-reviewed, all attribute the pagoda-function
technique to Berlekamp, Conway & Guy's *Winning Ways*. **Attribution CONFIRMED.**

### (ii) The book record

Two editions are in circulation and the volume number differs between them; this is the trap.

* **First edition:** Academic Press, London, 1982; peg solitaire is in **Volume 2, "Games in
  Particular"**; the pagoda pages are given as 729–730 by Jefferson et al. Confirmed by
  sources A and B above, which agree on authors, title, publisher and year.
* **Second edition:** A K Peters, 2004; the same chapter 23 is in **Volume 4**, pp. 803–841
  (Winning Ways 2nd ed. uses pagination continuous across its four volumes).
  Confirmed by source C above, and independently by:

**Source D** — `https://api.crossref.org/works/10.1017/S0025557200177435`, the review record for
this volume: title "Winning ways for your mathematical plays, volume 4", reviewer Nick Lord
(Tonbridge School), *The Mathematical Gazette* 89(514), March 2005, pp. 177–178, DOI
`10.1017/s0025557200177435`. The full review title as indexed by the publisher reads
"... volume 4 (2nd edn), by E. R. Berlekamp, J. H. Conway & R. K. Guy. Pp. 204 $39. 2004.
ISBN 1 56881 144 6 (A. K. Peters)." — confirming edition, year, publisher, ISBN and extent
from a peer-reviewed journal that is not the publisher. (204 pages for a volume paginated
803–1006 is consistent.)

Routledge's own product page and library catalogues could not be reached (see the Method
section), so the ISBN `1-56881-144-6` rests on the Gazette review title plus a WebSearch
summary; it is recorded here but omitted from the BibTeX as a single-strong-source field.

**VERDICT: CONFIRMED.** I recommend citing the **second edition, Volume 4**, because it is the
edition in print and because the chapter locator is verified; the 1982 Volume 2 record is given
in a `note` since most of the peg-solitaire literature cites it.

```bibtex
@incollection{berlekamp-conway-guy-2004,
  author    = {Elwyn R. Berlekamp and John H. Conway and Richard K. Guy},
  title     = {Purging Pegs Properly},
  booktitle = {Winning Ways for Your Mathematical Plays},
  edition   = {2nd},
  volume    = {4},
  chapter   = {23},
  pages     = {803--841},
  publisher = {A K Peters},
  year      = {2004},
  note      = {First edition: Academic Press, London, 1982, vol.~2 (\emph{Games in
               Particular}); the pagoda-function material is at pp.~729--730 there}
}
```

---

## C12 — Beasley, *The Ins and Outs of Peg Solitaire*

**Queries run**
* WebSearch: `Beasley "The Ins and Outs of Peg Solitaire" Oxford University Press 1985 "Recreations in Mathematics" ISBN`
* openlibrary.org, archive.org, loc.gov, iri.upc.edu catalogue — **all unreachable or 403/TLS-failed**
* Semantic Scholar by paper id `f0fa0ea5...` — HTTP 429 on all six attempts

**Source A** — Jefferson et al., reference [3], read out of the PDF (see C11 for the URL):
> [3] J. D. Beasley. The ins and outs of peg solitaire. Oxford University Press, Oxford, 1992.

Also cited in that paper's introduction as the survey of the mathematical results, and in §8 as
the source for Long-hop Solitaire (its chapter 8).

**Source B** — Bell, arXiv:1608.01609v3, reference [1], read out of the PDF:
> [1] J. Beasley, *The Ins and Outs of Peg Solitaire*, Oxford Univ. Press, 1992.

Two independent scholarly bibliographies agree on author, exact title, publisher and the year
**1992**.

**Year caveat, recorded not suppressed.** A WebSearch summary reported a **1985** Oxford
University Press edition in the series *Recreations in Mathematics*, ISBN 978-0-19-853203-3.
That is entirely plausible — 1985 hardback, 1992 paperback reissue — but **no catalogue I could
reach confirmed it**, and no source I fetched directly states 1985. The record below therefore
carries 1992, the year both fetched sources give. Anyone with library access should re-check
before submission; if the 1985 first edition is confirmed, prefer it.

**VERDICT: CONFIRMED** (year 1992; ISBN and series UNVERIFIED, omitted).

```bibtex
@book{beasley-1992,
  author    = {John D. Beasley},
  title     = {The Ins and Outs of Peg Solitaire},
  publisher = {Oxford University Press},
  address   = {Oxford},
  year      = {1992}
}
```

---

## C13 — Kiyomi & Matsui, CG 2000 (pagoda function as a linear program)

Added because it is the closest published analogue of what `lp_potential` actually does: it
solves for a pagoda function by linear programming and uses the result as an infeasibility
certificate.

**Queries run**
* Crossref: `query.bibliographic=Integer Programming Based Algorithms for Peg Solitaire Problems Kiyomi Matsui`
* Semantic Scholar title search (same string)

**Source A** — Crossref API, above query. Confirmed: title *Integer Programming Based Algorithms
for Peg Solitaire Problems*; authors Masashi Kiyomi, Tomomi Matsui, in that order; container
"Computers and Games" in the series "Lecture Notes in Computer Science"; pages 229–240;
issued 2001; publisher Springer Berlin Heidelberg; DOI `10.1007/3-540-45579-5_15`.

**Source B** — `https://api.semanticscholar.org/graph/v1/paper/search?query=Integer+Programming+Based+Algorithms+for+Peg+Solitaire+Problems+Kiyomi+Matsui`
Confirmed independently: identical title; authors Masashi Kiyomi, Tomomi Matsui; venue
"Computers and Games" (type: conference); `journal.pages` `229-240`; DOI
`10.1007/3-540-45579-5_15`; `externalIds.DBLP` = `conf/cg/KiyomiM00`.

**Year discrepancy, resolved and recorded.** Crossref gives 2001 (the LNCS volume's publication
year); S2/DBLP give 2000 (the conference year, CG 2000, Hamamatsu). LNCS volume 2063 appeared in
2001. The record below uses **2001** with the conference year in a note. The LNCS volume number
2063 is **UNVERIFIED** by the two sources above (Crossref returned no `volume` for the
book-chapter) and is omitted.

The separate RIMS Kôkyûroku 1185 (2001), pp. 100–108 version of this paper is the one whose text
is quoted in C11; S2 lists it as a distinct record with no DOI. Cite the LNCS version.

**VERDICT: CONFIRMED.**

```bibtex
@inproceedings{kiyomi-matsui-2001,
  author    = {Masashi Kiyomi and Tomomi Matsui},
  title     = {Integer Programming Based Algorithms for Peg Solitaire Problems},
  booktitle = {Computers and Games},
  series    = {Lecture Notes in Computer Science},
  pages     = {229--240},
  year      = {2001},
  publisher = {Springer},
  doi       = {10.1007/3-540-45579-5_15},
  note      = {Presented at CG 2000}
}
```

---

## D1 — Unsolvability International Planning Competition (UIPC 2016) — **DROPPED**

**Queries run**
* WebSearch: `"Unsolvability International Planning Competition" 2016 UIPC Muise Lipovetzky booklet citation`

**What exists:** a competition web site (`unsolve-ipc.eng.unimelb.edu.au`), a GitHub repository
of domains and generators (`AI-Planning/unsolve-ipc-2016`), a planner-abstracts booklet, and
organiser attribution to Christian Muise and Nir Lipovetzky.

**Why dropped:** none of these is a bibliographic record I could cross-verify in two independent
indexes. There is no DOI, no proceedings entry, and no publisher record; Crossref and the
proceedings hosts have nothing. A citation would have had to be assembled out of a web page and
a search-engine summary, which is precisely the failure mode this trace is written to avoid.

**Recommendation:** if §8.2 wants to point at the competition, cite the URL as a web resource
with an access date and say so plainly, or drop the mention. Do not manufacture a
paper-shaped entry for it.

---

## Not pursued (recorded so they are not mistaken for gaps)

* Eriksson, Röger & Helmert, "Inductive Certificates of Unsolvability for Domain-Independent
  Planning", IJCAI-18, pp. 5244–5248, DOI `10.24963/ijcai.2018/730` — Crossref-visible, a
  short sister-conference companion to C7/C8. Redundant here.
* Röger, "Towards Certified Unsolvability in Classical Planning", IJCAI-17, pp. 5141–5145,
  DOI `10.24963/ijcai.2017/738` — Crossref-visible, single-author overview. Redundant here.
* Culberson & Schaeffer, "Searching with pattern databases", 1996, DOI
  `10.1007/3-540-61291-2_68` — precursor to C5.
* Avis & Deza, "On the solitaire cone and its relationship to multi-commodity flows",
  *Mathematical Programming* 90(1), 2001, pp. 27–57 — the polyhedral treatment of the same
  object as the pagoda cone. Seen in search results and in the bibliographies of C11's sources
  A and B, but **not itself verified against two fetched sources**, so not offered as a
  citation. A good lead if the paper later wants the polyhedral framing.
