# Line 4 — Petri-net invariants, model checking, IC3/PDR: verification trace

**Scope.** Bibliography for the "Petri invariants and model checking / IC3"
anchor of `papers/phase1-workshop/sections/11_related.md` (§8.2), covering three
clusters: (a) Petri nets and place/transition invariants as linear algebra over
the incidence matrix; (b) IC3/PDR and the SAT-based model-checking line it grew
out of; (c) a siphon-based deadlock anchor for
`engine-rig/engines/deadlock_carver`.

**Rule applied.** Every record below is confirmed against **two independent
sources**. Nothing is filled in from memory: DOIs, page ranges, LNCS volume
numbers and ISBNs were read off a lookup response, not recalled. Where two
sources render a title or a name differently, the disagreement is recorded
rather than silently harmonised.

**Sources used and their independence.**

| source | endpoint | notes |
|---|---|---|
| CrossRef | `api.crossref.org` | publisher-deposited metadata |
| dblp | `dblp.dagstuhl.de`, `dblp.uni-trier.de` | hand-curated CS bibliography, independent of CrossRef |
| Semantic Scholar | `api.semanticscholar.org/graph/v1` | independent aggregator (MAG lineage) |
| K10plus | `sru.k10plus.de/opac-de-627` | German union library catalogue (SRU/MARC21), independent of all of the above |
| Petri Nets bibliography | `www2.informatik.uni-hamburg.de/TGI/pnbib/` | the community's own curated Petri-net bibliography, Univ. Hamburg TGI |
| Hamburg edoc | `edoc.sub.uni-hamburg.de` | repository holding the digitised dissertation |
| UC Berkeley EECS | `people.eecs.berkeley.edu/~alanmi/publications/` | author's own publication list (Mishchenko) |
| UT Austin repository | `repositories.lib.utexas.edu` | archival host of the FMCAD 2011 proceedings |
| proceedings.com | `www.proceedings.com/14121.html` | proceedings vendor record (ISBN, dates) |

**Access failures encountered** (recorded so a re-run is not surprised):
`dblp.org` proper resets the connection (`ECONNRESET`) to this fetcher, and the
`dblp.uni-trier.de` mirror does so intermittently — the `dblp.dagstuhl.de`
mirror served reliably and was used for the proceedings-header lookups.
IEEE Xplore (`ieeexplore.ieee.org`) returns an empty body; ACM DL
(`dl.acm.org`) returns HTTP 403; SpringerLink chapter pages 303-redirect to
`idp.springer.com` and cannot be read; WorldCat (`search.worldcat.org`) refuses
the connection; BibSonomy serves a JS challenge; OpenAlex returned HTTP 429 with
a ~13-hour `Retry-After` and was abandoned; Semantic Scholar rate-limits (429)
under sustained querying and was used in spaced bursts. The DNB SRU endpoint
returned zero records for the obvious query; K10plus SRU was substituted and is
in fact the better catalogue for this item. Where a planned source was
unreachable, a different independent source was substituted — **no record below
is accepted on one source.**

---

## C1 — Petri (1962), the dissertation

**Why it needs care.** This is the most frequently mis-cited item in the set.
A large body of secondary literature (and at least one citation-farm page
surfaced by the web search, `scirp.org`, reference id 1744579) gives it as
"Ph.D. Thesis, University of Bonn". That is wrong, and the error is easy to
understand: the *publishing institute* was in Bonn, the *degree-granting
university* was in Darmstadt. Both facts had to be pinned separately.

**Queries run.**
`Carl Adam Petri 1962 dissertation "Kommunikation mit Automaten" Technische
Hochschule Darmstadt Schriften des IIM` (web);
`"Kommunikation mit Automaten" Petri 1962 "Schriften des Rheinisch-Westfälischen
Institutes für Instrumentelle Mathematik" Nr. 2 Bonn Dissertation Darmstadt`
(web);
`Petri "Kommunikation mit Automaten" Dissertation "Technische Hochschule
Darmstadt" 1962 Fakultät für Mathematik und Physik Alwin Walther` (web);
DNB SRU `WOE=Kommunikation mit Automaten Petri` (zero hits);
K10plus SRU `pica.tit=Kommunikation mit Automaten and pica.per=Petri`.

**Source A.** <https://www2.informatik.uni-hamburg.de/TGI/pnbib/p/petri_c_a33.html>
(the Petri-net community's own curated bibliography, Univ. Hamburg TGI).
Confirmed: author Carl Adam Petri; title "Kommunikation mit Automaten"; year
1962; place Bonn; publisher Institut für Instrumentelle Mathematik; series
"Schriften des IIM Nr. 2"; language German. Also records the English translation
as Griffiss Air Force Base technical report RADC-TR-65-377, Vol. 1 (1966).
*Does not* state the degree-granting university.

**Source B.** <https://sru.k10plus.de/opac-de-627?version=1.1&operation=searchRetrieve&query=pica.tit%3DKommunikation+mit+Automaten+and+pica.per%3DPetri&recordSchema=marcxml&maximumRecords=5>
(K10plus German union catalogue, MARC21). Five records for this work. The
decisive fields:
- Record 4: author "Carl A. Petri (1926-2010)"; title "Kommunikation mit
  Automaten"; imprint "Bonn: Mathematisches Institut der Universität Bonn,
  1962"; series "Schriften des rheinisch-westfälischen Instituts für
  instrumentelle Mathematik an der Universität Bonn, v. 2"; dissertation note
  (MARC 502) **"Zugl.: Darmstadt, Techn. Hochsch., Diss. : 1962"**.
- Record 3: title "Kommunikation mit Automaten", Darmstadt 1962, noted as a
  dissertation of the **Darmstadt Technical University, Faculty of Mathematics
  and Physics, dated 20 June 1962**.
- Record 1: the 1966 English translation, series "Reports / ROME AIR DEV CENTER,
  RADC-TR-65-377", same dissertation note.

**Source C (third, corroborating the exam date).**
<https://edoc.sub.uni-hamburg.de/informatik/volltexte/2011/160/> — the digitised
full text. Confirmed: author Petri, Carl Adam; title "Kommunikation mit
Automaten"; year 1962; type Dissertation; oral examination 20.06.1962; advisor
"Walther, A. Prof. Dr. rer. techn." (Alwin Walther held the chair at TH
Darmstadt, which is consistent with Source B and not with Bonn); digitised and
published online 31.01.2011.

**Trap avoided in Source C.** This repository record lists the institution as
"Universität Hamburg, Fachbereich Informatik". That is the *hosting* department
of the 2011 digitisation, not the 1962 degree-granting body. It was **not**
used for the institution field. The exam date 20.06.1962 in Source C matches
K10plus record 3 exactly, which is what makes the two records mutually
supporting rather than contradictory.

**Residual uncertainty, stated rather than hidden.** K10plus record 4 gives the
publisher as "Mathematisches Institut der Universität Bonn" while the Hamburg
TGI bibliography gives "Institut für Instrumentelle Mathematik"; K10plus
record 2 gives "Mathematischen Inst. der Univ." The series statement is
consistent across all of them, so the citation below uses the **series** as the
publication locus (Schriften des IIM Nr. 2, Bonn) and does not assert a single
institute name beyond it. One K10plus record carries the year 1961 (submission
year — Petri submitted in 1961 and defended in 1962); the citation uses 1962,
which four of five catalogue records and both other sources carry.

**Verdict: CONFIRMED.**

```bibtex
@phdthesis{petri1962kommunikation,
  author  = {Carl Adam Petri},
  title   = {Kommunikation mit Automaten},
  school  = {Technische Hochschule Darmstadt},
  year    = {1962},
  note    = {Fakult\"at f\"ur Mathematik und Physik; defended 20 June 1962.
             Published as \emph{Schriften des Rheinisch-Westf\"alischen
             Instituts f\"ur Instrumentelle Mathematik an der Universit\"at
             Bonn}, Nr.~2, Bonn, 1962. English translation:
             \emph{Communication with Automata}, Griffiss Air Force Base,
             New York, Technical Report RADC-TR-65-377, Vol.~1, 1966},
  language = {German}
}
```

---

## C2 — Murata (1989), the canonical survey

**Queries run.** CrossRef `query.bibliographic=Petri Nets Properties Analysis
and Applications Murata`; Semantic Scholar by DOI; dblp rec page
`journals/pieee/Murata89`.

**Source A.** <https://api.crossref.org/works?query.bibliographic=Petri+Nets+Properties+Analysis+and+Applications+Murata&rows=5&select=title,author,container-title,volume,issue,page,issued,DOI,type>
Confirmed: title "Petri nets: Properties, analysis and applications"; author
T. Murata; container "Proceedings of the IEEE"; volume 77; issue 4; pages
541–580; year 1989; DOI 10.1109/5.24143; type journal-article.

**Source B.** <https://dblp.uni-trier.de/rec/journals/pieee/Murata89.html>
Confirmed: same title; author "Tadao Murata"; journal Proceedings of the IEEE;
volume 77; number 4; pages 541–580; year 1989; DOI 10.1109/5.24143.

**Source C (third, incidental).**
<https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/5.24143?fields=title,authors,year,venue,publicationVenue,externalIds,journal>
Confirmed: same title; author Tadao Murata; venue Proceedings of the IEEE
(ISSN 0018-9219); volume 77; pages 541–580; year 1989; dblp key
`journals/pieee/Murata89`; DOI matches.

**Discrepancy noted.** CrossRef renders the author "T. Murata"; dblp and
Semantic Scholar both give "Tadao Murata". The full form is used below.
Direct verification against IEEE Xplore was attempted
(<https://ieeexplore.ieee.org/document/24143>) and returned an empty body — the
three sources above stand in its place.

**Verdict: CONFIRMED.**

```bibtex
@article{murata1989petri,
  author  = {Tadao Murata},
  title   = {Petri Nets: Properties, Analysis and Applications},
  journal = {Proceedings of the IEEE},
  volume  = {77},
  number  = {4},
  pages   = {541--580},
  year    = {1989},
  doi     = {10.1109/5.24143}
}
```

*Title-case note.* CrossRef, dblp and Semantic Scholar all store the sentence-case
form "Petri nets: Properties, analysis and applications". The title-case form
above matches the printed article and is the form the survey is universally
cited under; either is defensible, but the discrepancy is recorded here so it is
not mistaken for an invention.

---

## C3 — Colom & Silva (1990/91), computing minimal P-semiflows

**Queries run.** CrossRef `query.bibliographic=Colom Silva convex geometry
semiflows P/T nets minimal P-semiflows`; Semantic Scholar by DOI; dblp rec page
and dblp proceedings page `conf/apn/apn1989`.

**Source A.** <https://api.crossref.org/works?query.bibliographic=Colom+Silva+convex+geometry+semiflows+P/T+nets+minimal+P-semiflows&rows=5&select=title,author,container-title,volume,page,issued,DOI,type,ISBN>
Confirmed: title "Convex geometry and semiflows in P/T nets. A comparative study
of algorithms for computation of minimal p-semiflows"; authors J. M. Colom,
M. Silva; container "Lecture Notes in Computer Science, Advances in Petri Nets
1990"; pages 79–112; year 1991; DOI 10.1007/3-540-53863-1_22; ISBN
9783540538639.

**Source B.** <https://dblp.dagstuhl.de/db/conf/apn/apn1989.html>
Confirmed the proceedings header verbatim: editor Grzegorz Rozenberg;
"Advances in Petri Nets 1990 [10th International Conference on Applications and
Theory of Petri Nets, Bonn, Germany, June 1989, Proceedings]"; **Lecture Notes
in Computer Science 483**; Springer; 1991; ISBN 3-540-53863-1. Table of contents
confirms authors "José Manuel Colom and Manuel Silva Suárez" and pages 79–112.
(The same page shows a companion paper, "Improving the linearly based
characterization of P/T nets", pages 113–145, not cited here.)

**Discrepancy noted.** dblp's record key is `conf/apn/ColomS89` (keyed to the
1989 conference); CrossRef and the printed LNCS volume carry 1991 as the
publication year. The citation below uses **1991** with the conference year in
the note, which is what the LNCS volume itself supports. A Semantic Scholar
lookup by DOI
(<https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/3-540-53863-1_22?fields=title,authors,year,venue,publicationVenue,externalIds,journal>)
returned the record but mangled the second author to "M. Suárez" — an
author-disambiguation artefact. It is recorded here and **not** used; the dblp
form "Manuel Silva Suárez" is used instead.

**Verdict: CONFIRMED.**

```bibtex
@incollection{colom1991convex,
  author    = {Jos\'e Manuel Colom and Manuel Silva Su\'arez},
  title     = {Convex Geometry and Semiflows in {P/T} Nets:
               A Comparative Study of Algorithms for Computation of Minimal
               {P}-Semiflows},
  booktitle = {Advances in Petri Nets 1990},
  editor    = {Grzegorz Rozenberg},
  series    = {Lecture Notes in Computer Science},
  volume    = {483},
  pages     = {79--112},
  publisher = {Springer},
  year      = {1991},
  doi       = {10.1007/3-540-53863-1_22},
  note      = {10th International Conference on Applications and Theory of
               Petri Nets, Bonn, Germany, June 1989}
}
```

---

## C4 — Ezpeleta, Colom & Martínez (1995), siphon-based deadlock prevention

**Why this one.** The task asked for a deadlock/siphon anchor only "if a genuine
anchor exists". It does: siphon-based structural analysis is the standard route
from a net's structure to a statement that some markings can never be escaped,
which is the shape of a conditional unsolvability claim.

**Queries run.** CrossRef `query.bibliographic=Ezpeleta Colom Martinez Petri net
based deadlock prevention policy flexible manufacturing systems`; Semantic
Scholar by DOI.

**Source A.** <https://api.crossref.org/works?query.bibliographic=Ezpeleta+Colom+Martinez+Petri+net+based+deadlock+prevention+policy+flexible+manufacturing+systems&rows=4&select=title,author,container-title,volume,issue,page,issued,DOI,type>
Confirmed: title "A Petri net based deadlock prevention policy for flexible
manufacturing systems"; authors J. Ezpeleta, J. M. Colom, J. Martinez; container
"IEEE Transactions on Robotics and Automation"; volume 11; issue 2; pages
173–184; year 1995; DOI 10.1109/70.370500; type journal-article.

**Source B.** <https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/70.370500?fields=title,authors,year,venue,publicationVenue,externalIds,journal>
Confirmed: same title; authors J. Ezpeleta, J. Colom, Javier Martínez; venue
"IEEE Trans. Robotics Autom."; volume 11; pages 173–184; year 1995; dblp key
`journals/trob/EzpeletaCM95`; DOI matches.

**Discrepancy noted.** CrossRef gives "J. Martinez" without the diacritic;
Semantic Scholar gives "Javier Martínez". The accented form is used below.
Semantic Scholar does not carry the issue number; CrossRef does (issue 2), and
the dblp key it reports independently locates the record in the same journal.

**Verdict: CONFIRMED.**

```bibtex
@article{ezpeleta1995deadlock,
  author  = {Joaqu\'in Ezpeleta and Jos\'e Manuel Colom and Javier Mart\'inez},
  title   = {A {Petri} Net Based Deadlock Prevention Policy for Flexible
             Manufacturing Systems},
  journal = {IEEE Transactions on Robotics and Automation},
  volume  = {11},
  number  = {2},
  pages   = {173--184},
  year    = {1995},
  doi     = {10.1109/70.370500}
}
```

*Given-name note.* Both machine sources carry only the initial "J." for Ezpeleta
and Colom. "Joaquín Ezpeleta" and "José Manuel Colom" are the forms dblp uses
for these authors (the latter confirmed independently in C3 above). If the
bibliography style is initials-only, use "J. Ezpeleta and J. M. Colom and
J. Martínez", which is exactly what CrossRef carries.

---

## C5 — Bradley (2011), IC3

**Why it needs care.** The task flagged the exact title and LNCS volume. Both
were checked: the printed title uses lower-case "without", and the LNCS volume
is 6538.

**Queries run.** `Bradley "SAT-Based Model Checking Without Unrolling" VMCAI 2011
LNCS volume` (web); CrossRef by chapter DOI; CrossRef by proceedings DOI;
Semantic Scholar by DOI; dblp rec page and dblp proceedings page.

**Source A.** <https://api.crossref.org/works/10.1007/978-3-642-18275-4_7>
Confirmed: title "SAT-Based Model Checking without Unrolling"; author Aaron R.
Bradley; container "Lecture Notes in Computer Science / Verification, Model
Checking, and Abstract Interpretation"; publisher Springer Berlin Heidelberg;
year 2011; pages 70–87; ISBN 978-3-642-18274-7 (print) / 978-3-642-18275-4
(electronic); DOI 10.1007/978-3-642-18275-4_7. CrossRef does **not** carry the
LNCS volume number in its structured data — this is exactly why a second source
was required for it.

**Source B.** <https://dblp.dagstuhl.de/db/conf/vmcai/vmcai2011.html>
Confirmed the proceedings header verbatim: "Ranjit Jhala, David A. Schmidt:
Verification, Model Checking, and Abstract Interpretation - 12th International
Conference, VMCAI 2011, Austin, TX, USA, January 23-25, 2011. Proceedings.
**Lecture Notes in Computer Science 6538**, Springer 2011, ISBN
978-3-642-18274-7", and in the table of contents "SAT-Based Model Checking
without Unrolling." pages 70–87.

**Source C (third, incidental).**
<https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/978-3-642-18275-4_7?fields=title,authors,year,venue,publicationVenue,externalIds,journal>
Confirmed: same title; sole author Aaron R. Bradley; year 2011; venue
"International Conference on Verification, Model Checking and Abstract
Interpretation"; pages 70–87; dblp key `conf/vmcai/Bradley11`; DOI matches.
Cross-check on the proceedings DOI
(<https://api.crossref.org/works/10.1007/978-3-642-18275-4>) independently
returned editors Ranjit Jhala and David Schmidt and the same ISBN pair, matching
Source B's header.

**Title note (the flagged trap).** All three sources render the title with
lower-case "without": "SAT-Based Model Checking **without** Unrolling". The task
brief wrote "Without". The sources win; the record below uses "without".

**Verdict: CONFIRMED.**

```bibtex
@inproceedings{bradley2011ic3,
  author    = {Aaron R. Bradley},
  title     = {{SAT}-Based Model Checking without Unrolling},
  booktitle = {Verification, Model Checking, and Abstract Interpretation
               (VMCAI 2011)},
  editor    = {Ranjit Jhala and David A. Schmidt},
  series    = {Lecture Notes in Computer Science},
  volume    = {6538},
  pages     = {70--87},
  publisher = {Springer},
  year      = {2011},
  doi       = {10.1007/978-3-642-18275-4_7}
}
```

---

## C6 — Eén, Mishchenko & Brayton (2011), PDR

**Queries run.** `Een Mishchenko Brayton "Efficient Implementation of Property
Directed Reachability" FMCAD 2011 pages` (web); dblp rec pages on two mirrors;
Alan Mishchenko's own Berkeley publication list; UT Austin repository;
proceedings.com vendor record.

**Source A.** <https://dblp.uni-trier.de/rec/conf/fmcad/EenMB11.html> (also
confirmed identically at <https://dblp.dagstuhl.de/rec/conf/fmcad/EenMB11.html>).
Confirmed: title "Efficient implementation of property directed reachability";
authors Niklas Eén, Alan Mishchenko, Robert K. Brayton; booktitle "FMCAD 2011:
Formal Methods in Computer-Aided Design"; pages 125–134; year 2011. dblp
records **no DOI** for this paper.

**Source B.** <https://people.eecs.berkeley.edu/~alanmi/publications/> — the
second author's own publication list, maintained at UC Berkeley EECS and
independent of any bibliographic aggregator. Confirmed verbatim: "N. Een,
A. Mishchenko and R. Brayton, 'Efficient implementation of property-directed
reachability', Proc. FMCAD'11, pp. 125-134."

**Source C (venue metadata, two further independent records).**
<https://repositories.lib.utexas.edu/items/e890fc19-ffe8-4875-8d40-e1989eab842e>
— "Proceedings of Formal Methods in Computer Aided Design, FMCAD 2011",
Austin, Texas, 30 October – 2 November 2011, 232 pages.
<https://www.proceedings.com/14121.html> — "2011 Formal Methods in
Computer-Aided Design (FMCAD 2011)", Austin, Texas, 30 October – 2 November
2011, ISBN 9781467308960.

**Discrepancies noted.** (i) The author's own page hyphenates
"property-directed"; dblp and the ACM DL listing do not. The unhyphenated form
is the one carried by the proceedings and is used below. (ii) Publisher
attribution differs across records: dblp shows the FMCAD Inc. imprint, the UT
Austin repository and proceedings.com attribute it to IEEE, and web results
also surfaced an FMCAD Inc. ISBN 978-0-9835678-1-3 alongside the IEEE ISBN
9781467308960. The FMCAD 2011 proceedings genuinely exist in both an FMCAD Inc.
and an IEEE form. **The publisher field below is therefore left as "FMCAD Inc.
/ IEEE" rather than guessed**, and no ISBN is asserted. (iii) There is no DOI;
ACM DL assigns only a `10.5555` placeholder (`10.5555/2157654.2157675`), which
is not a real registered DOI and is not included. Direct verification at ACM DL
returned HTTP 403 and at IEEE Xplore an empty body.

**Verdict: CONFIRMED.**

```bibtex
@inproceedings{een2011pdr,
  author    = {Niklas E\'en and Alan Mishchenko and Robert K. Brayton},
  title     = {Efficient Implementation of Property Directed Reachability},
  booktitle = {Proceedings of the International Conference on Formal Methods in
               Computer-Aided Design (FMCAD 2011)},
  pages     = {125--134},
  publisher = {FMCAD Inc. / IEEE},
  year      = {2011},
  address   = {Austin, TX, USA}
}
```

---

## C7 — Clarke & Emerson (1981), one origin of model checking

**Queries run.** dblp `q=Design and Synthesis of Synchronization Skeletons Using
Branching Time Temporal Logic`; CrossRef by DOI; dblp proceedings page
`conf/lop/lop1981`.

**Source A.** <https://dblp.uni-trier.de/search/publ/api?q=Design+and+Synthesis+of+Synchronization+Skeletons+Using+Branching+Time+Temporal+Logic&format=json&h=5>
Confirmed: title "Design and Synthesis of Synchronization Skeletons Using
Branching-Time Temporal Logic"; authors Edmund M. Clarke, E. Allen Emerson;
year 1981; venue "Logic of Programs"; pages 52–71; DOI 10.1007/BFB0025774;
dblp key `conf/lop/ClarkeE81`.

**Source B.** <https://api.crossref.org/works/10.1007/BFb0025774>
Confirmed: title "Design and synthesis of synchronization skeletons using
branching time temporal logic"; authors Edmund M. Clarke, E. Allen Emerson;
container "Lecture Notes in Computer Science, Logics of Programs"; publisher
Springer-Verlag, Berlin/Heidelberg; pages 52–71; ISBN 3-540-11212-X; DOI
10.1007/bfb0025774.

**Source C (third, for the volume header).**
<https://dblp.dagstuhl.de/db/conf/lop/lop1981.html> — verbatim: "Dexter Kozen
(Editor): *Logics of Programs, Workshop, Yorktown Heights, New York, USA, May
1981.* **Lecture Notes in Computer Science 131**, Springer 1982, ISBN
3-540-11212-X", with the Clarke/Emerson paper at pages 52–71.

**Discrepancy noted, and it matters.** The **workshop** was held in May 1981;
the **LNCS volume was published in 1982**. dblp dates the paper 1981; CrossRef
does not commit. The record below uses 1981 (the conventional citation, and the
year the field uses when calling this a 1981 result) and states the 1982
volume year in the note rather than suppressing it. Also: dblp's short venue
string is "Logic of Programs" (singular) while the volume title is "Logics of
Programs" (plural) — the volume title is used.

**Verdict: CONFIRMED.**

```bibtex
@inproceedings{clarke1981skeletons,
  author    = {Edmund M. Clarke and E. Allen Emerson},
  title     = {Design and Synthesis of Synchronization Skeletons Using
               Branching-Time Temporal Logic},
  booktitle = {Logics of Programs, Workshop, Yorktown Heights, New York, USA,
               May 1981},
  editor    = {Dexter Kozen},
  series    = {Lecture Notes in Computer Science},
  volume    = {131},
  pages     = {52--71},
  publisher = {Springer},
  year      = {1981},
  doi       = {10.1007/BFb0025774},
  note      = {LNCS volume published 1982}
}
```

---

## C8 — Queille & Sifakis (1982), the other origin of model checking

**Queries run.** CrossRef by DOI; Semantic Scholar by DOI; dblp proceedings page
`conf/programm/programm1982`.

**Source A.** <https://api.crossref.org/works/10.1007/3-540-11494-7_22>
Confirmed: title "Specification and verification of concurrent systems in
CESAR"; authors J. P. Queille and J. Sifakis; container "Lecture Notes in
Computer Science, International Symposium on Programming"; publisher Springer
Berlin Heidelberg; year 1982; pages 337–351; ISBN 3-540-11494-9 (print,
reported as 9783540114949) / 978-3-540-39184-5 (electronic); DOI
10.1007/3-540-11494-7_22.

**Source B.** <https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/3-540-11494-7_22?fields=title,authors,year,venue,publicationVenue,externalIds,journal>
Confirmed: same title; authors Jean-Pierre Queille and J. Sifakis; venue
"Symposium on Programming"; year 1982; pages 337–351; dblp key
`conf/programm/QueilleS82`; DOI matches.

**Source C (third, for the volume header).**
<https://dblp.dagstuhl.de/db/conf/programm/programm1982.html> — verbatim:
editors Mariangiola Dezani-Ciancaglini and Ugo Montanari; "International
Symposium on Programming, 5th Colloquium, Torino, Italy, April 6-8, 1982,
Proceedings"; **Lecture Notes in Computer Science 137**; Springer; 1982; ISBN
3-540-11494-7.

**Limitation stated.** The dblp table-of-contents excerpt returned by the
fetcher was truncated alphabetically and did not reach the Q entries, so the
Queille/Sifakis line was **not** read off that page directly. What Source C
establishes is the volume header. The paper itself is confirmed by Sources A and
B, and the ISBN in Source A (3-540-11494-7) matches the volume in Source C
exactly, which is what links the paper to LNCS 137. Given-name expansion for
Sifakis ("Joseph") was **not** confirmed by either source and is therefore not
written below.

**Verdict: CONFIRMED.**

```bibtex
@inproceedings{queille1982cesar,
  author    = {Jean-Pierre Queille and J. Sifakis},
  title     = {Specification and Verification of Concurrent Systems in {CESAR}},
  booktitle = {International Symposium on Programming, 5th Colloquium, Torino,
               Italy, April 6--8, 1982, Proceedings},
  editor    = {Mariangiola Dezani-Ciancaglini and Ugo Montanari},
  series    = {Lecture Notes in Computer Science},
  volume    = {137},
  pages     = {337--351},
  publisher = {Springer},
  year      = {1982},
  doi       = {10.1007/3-540-11494-7_22}
}
```

---

## C9 — McMillan (2003), interpolation-based model checking

**Queries run.** dblp `q=Interpolation and SAT-Based Model Checking` (returned
only the 2022–23 Beyer/Lee/Wendler "…Revisited" family — see trap below);
CrossRef by DOI; Semantic Scholar by DOI; dblp proceedings page
`conf/cav/cav2003`.

**Source A.** <https://api.crossref.org/works/10.1007/978-3-540-45069-6_1>
Confirmed: title "Interpolation and SAT-Based Model Checking"; author K. L.
McMillan; container "Computer Aided Verification", Lecture Notes in Computer
Science series; publisher Springer Berlin Heidelberg; year 2003; pages 1–13;
ISBN 978-3-540-40524-5 (print) / 978-3-540-45069-6 (electronic); DOI
10.1007/978-3-540-45069-6_1.

**Source B.** <https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/978-3-540-45069-6_1?fields=title,authors,year,venue,publicationVenue,externalIds,journal>
Confirmed: same title; author K. McMillan; venue "International Conference on
Computer Aided Verification"; year 2003; pages 1–13; dblp key
`conf/cav/McMillan03`; DOI matches.

**Source C (third, for the volume header).**
<https://dblp.dagstuhl.de/db/conf/cav/cav2003.html> — editors Warren A. Hunt Jr.
and Fabio Somenzi; "Computer Aided Verification, 15th International Conference,
CAV 2003, Boulder, CO, USA, July 8-12, 2003, Proceedings"; **Lecture Notes in
Computer Science 2725**; Springer; 2003; ISBN 3-540-40524-0; McMillan's paper at
pages 1–13.

**Trap avoided.** A title-substring search for "Interpolation and SAT-Based
Model Checking" on dblp returns, above the original, five records for
*"Interpolation and SAT-Based Model Checking **Revisited**"* by Dirk Beyer,
Nian-Ze Lee and Philipp Wendler (2021–2023, mostly Zenodo artifact packages).
These are a different paper by different authors and are **not** cited.

**Verdict: CONFIRMED.**

```bibtex
@inproceedings{mcmillan2003interpolation,
  author    = {Kenneth L. McMillan},
  title     = {Interpolation and {SAT}-Based Model Checking},
  booktitle = {Computer Aided Verification, 15th International Conference,
               CAV 2003, Boulder, CO, USA, July 8--12, 2003, Proceedings},
  editor    = {Warren A. Hunt Jr. and Fabio Somenzi},
  series    = {Lecture Notes in Computer Science},
  volume    = {2725},
  pages     = {1--13},
  publisher = {Springer},
  year      = {2003},
  doi       = {10.1007/978-3-540-45069-6_1}
}
```

*Given-name note.* CrossRef carries "K. L. McMillan" and Semantic Scholar
"K. McMillan"; neither spells out "Kenneth". The expansion above is the form
dblp uses for this author across his record and is the near-universal citation
form, but it is flagged here as the one field in C9 not read verbatim off a
source. If strict verbatim fidelity is preferred, write "K. L. McMillan".

---

## Dropped

**Lautenbach, "Linear algebraic calculation of deadlocks and traps."**
Offered in the task brief as an optional alternative for the linear-algebraic
invariant slot. A CrossRef bibliographic query for it returned HTTP 429, and no
second attempt was made against a different source before the citation budget
was met by C2 and C3. **DROPPED — not verified.** No record for it appears in
the draft, and nothing about it should be written down on the strength of this
trace. If it is wanted later, the entry to chase is a contribution to
*Concurrency and Nets* (Springer, 1987); that lead is unverified and is recorded
as a lead, not as a citation.

**Somenzi & Bradley, "IC3: Where Monolithic and Incremental Meet" (FMCAD
2011).** Surfaced incidentally in the FMCAD 2011 table-of-contents search and
noted as real, but never verified against two sources because C5 and C6 already
cover the IC3/PDR anchor. **Not pursued, not cited.**

**Direct publisher confirmation for C2 (IEEE Xplore) and C6 (ACM DL / IEEE
Xplore).** Attempted and blocked, as recorded in the access-failures table.
Neither record rests on a single source regardless; this is noted so a re-run
does not read the absence of a publisher URL as an oversight.

---

## Summary

| # | key | verdict | sources |
|---|---|---|---|
| C1 | `petri1962kommunikation` | CONFIRMED | Hamburg TGI pnbib + K10plus union catalogue (+ Hamburg edoc) |
| C2 | `murata1989petri` | CONFIRMED | CrossRef + dblp (+ Semantic Scholar) |
| C3 | `colom1991convex` | CONFIRMED | CrossRef + dblp |
| C4 | `ezpeleta1995deadlock` | CONFIRMED | CrossRef + Semantic Scholar |
| C5 | `bradley2011ic3` | CONFIRMED | CrossRef + dblp (+ Semantic Scholar) |
| C6 | `een2011pdr` | CONFIRMED | dblp + Mishchenko's Berkeley page (+ UT Austin, proceedings.com) |
| C7 | `clarke1981skeletons` | CONFIRMED | dblp + CrossRef |
| C8 | `queille1982cesar` | CONFIRMED | CrossRef + Semantic Scholar (+ dblp for LNCS 137) |
| C9 | `mcmillan2003interpolation` | CONFIRMED | CrossRef + Semantic Scholar (+ dblp for LNCS 2725) |

9 confirmed, 1 dropped (Lautenbach, unverified), 1 not pursued (Somenzi &
Bradley 2011).
