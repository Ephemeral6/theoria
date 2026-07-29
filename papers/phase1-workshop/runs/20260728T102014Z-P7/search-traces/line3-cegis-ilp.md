# Line 3 — CEGIS, version spaces, ILP, action-model learning: verification trace

**Scope.** Bibliography for the "Program synthesis: CEGIS and ILP" anchor of
`papers/phase1-workshop/sections/11_related.md` (§8.2), plus the version-space
ancestry of `engine-rig/engines/cegis_miner`'s frontier return value and the
action-model-learning neighbour that mining transition rules from a ledger
sits next to.

**Rule applied.** Every record below is confirmed against **two independent
sources**. Nothing is filled in from memory: where a DOI appears it was read off
a lookup response, not recalled. Author lists, years, venues, volumes and page
ranges are transcribed from the source that carries them; where two sources
render a name differently (initials, diacritics, title case) the disagreement is
recorded rather than silently harmonised.

**Sources used and their independence.**

| source | endpoint | notes |
|---|---|---|
| CrossRef | `api.crossref.org` | publisher-deposited metadata |
| dblp | `dblp.uni-trier.de/search/publ/api` | hand-curated CS bibliography, independent of CrossRef |
| Semantic Scholar | `api.semanticscholar.org/graph/v1` | independent aggregator (MAG lineage) |
| OpenAlex | `api.openalex.org` | independent aggregator |
| JAIR | `www.jair.org` | publisher of record |
| UC Berkeley EECS | `www2.eecs.berkeley.edu/Pubs/TechRpts` | publisher of record for the tech-report form |

**Access failures encountered** (recorded so a re-run is not surprised): ACM DL
(`dl.acm.org`) returns HTTP 403 to this fetcher; ScienceDirect
(`www.sciencedirect.com`) returns 403; PhilPapers returns 403; `dblp.org`
proper resets the connection while the `dblp.uni-trier.de` mirror serves
normally; OpenAlex and Semantic Scholar both rate-limit (HTTP 429) under
sustained querying. Where a planned source was unreachable, a different
independent source was substituted — no record was accepted on one source.

---

## C1 — Solar-Lezama, Tancau, Bodík, Seshia, Saraswat (ASPLOS 2006)

**Queries run.**
`"Combinatorial sketching for finite programs" ASPLOS 2006 Solar-Lezama` (web);
CrossRef by DOI; Semantic Scholar by DOI; dblp `q=Solar-Lezama+sketching`.

**Source A.** <https://api.crossref.org/works/10.1145/1168857.1168907>
Confirmed: title "Combinatorial sketching for finite programs"; authors in order
Armando Solar-Lezama, Liviu Tancau, Rastislav Bodik, Sanjit Seshia, Vijay
Saraswat; container "Proceedings of the 12th international conference on
Architectural support for programming languages and operating systems";
publisher ACM; year 2006; pages 404–415; DOI 10.1145/1168857.1168907.

**Source B.** <https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/1168857.1168907?fields=title,authors,year,venue,publicationVenue,externalIds>
Confirmed: same title; same five authors in the same order (rendered "Rastislav
Bodík", "S. Seshia", "V. Saraswat"); year 2006; venue "ASPLOS XII"; DBLP key
`conf/asplos/Solar-LezamaTBSS06`; DOI matches.

**Source C (third, incidental).** <https://dblp.uni-trier.de/search/publ/api?q=Solar-Lezama+sketching&format=json&h=15>
Confirmed: venue ASPLOS, year 2006, authors "Armando Solar-Lezama, Liviu Tancau,
Rastislav Bodík, Sanjit A. Seshia, Vijay A. Saraswat", same DOI.

**Discrepancy noted.** CrossRef drops the middle initials of Seshia and Saraswat
and the diacritic in Bodík; dblp carries both. The dblp form is used below.

**Verdict: CONFIRMED.**

```bibtex
@inproceedings{solarlezama2006sketching,
  author    = {Armando Solar-Lezama and Liviu Tancau and Rastislav Bod{\'\i}k and
               Sanjit A. Seshia and Vijay A. Saraswat},
  title     = {Combinatorial Sketching for Finite Programs},
  booktitle = {Proceedings of the 12th International Conference on Architectural
               Support for Programming Languages and Operating Systems (ASPLOS XII)},
  year      = {2006},
  pages     = {404--415},
  publisher = {ACM},
  doi       = {10.1145/1168857.1168907}
}
```

---

## C2 — Solar-Lezama, *Program Synthesis by Sketching* (PhD thesis, 2008)

**Queries run.**
`Solar-Lezama "Program Synthesis by Sketching" PhD thesis University of
California Berkeley 2008` (web); dblp `q=Solar-Lezama+program+synthesis+by+sketching`
(**0 hits — dblp does not index this thesis**); dblp `q=Solar-Lezama+sketching`
(15 hits, none a thesis entry); ACM DL guide-book entry `10.5555/1714168`
(HTTP 403, unusable).

**Source A.** <https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-176.html>
Confirmed: title "Program Synthesis By Sketching"; author Armando Solar-Lezama;
report number UCB/EECS-2008-176; issuing body EECS Department, University of
California, Berkeley; date issued 19 December 2008.

**Source B.** <https://people.csail.mit.edu/asolar/papers/thesis.pdf> — the
document itself, hosted independently at MIT CSAIL; title page read directly.
Confirmed: title "Program Synthesis by Sketching"; author Armando Solar-Lezama;
"A dissertation submitted in partial satisfaction of the requirements for the
degree of Doctor in Philosophy in Engineering-Electrical Engineering and
Computer Science", Graduate Division, University of California, Berkeley;
committee Rastislav Bodik (chair), Sanjit Seshia, Leo Harrington; **Fall 2008**.

**Discrepancy noted.** One web summary reported "January 2008, 211 pages" for a
ProQuest/ACM-guide listing; both primary sources say Fall 2008 / 19 Dec 2008.
The year 2008 is not in doubt; the January date was not corroborated and is not
used.

**Verdict: CONFIRMED.**

```bibtex
@phdthesis{solarlezama2008thesis,
  author = {Armando Solar-Lezama},
  title  = {Program Synthesis by Sketching},
  school = {University of California, Berkeley},
  year   = {2008},
  note   = {Technical report UCB/EECS-2008-176}
}
```

---

## C3 — Alur et al., "Syntax-guided synthesis" (FMCAD 2013)

**Queries run.**
CrossRef `query.bibliographic=Syntax-guided synthesis Alur FMCAD`; dblp
`q=Alur+syntax-guided+synthesis+fmcad`; OpenAlex by DOI. (Semantic Scholar by
DOI returned 404 for this record — noted, not used.)

**Source A.** <https://api.crossref.org/works?query.bibliographic=Syntax-guided+synthesis+Alur+FMCAD&rows=3>
Confirmed: title "Syntax-guided synthesis"; authors in order Rajeev Alur,
Rastislav Bodik, Garvit Juniwal, Milo M. K. Martin, Mukund Raghothaman, Sanjit
A. Seshia, Rishabh Singh, Armando Solar-Lezama, Emina Torlak, Abhishek Udupa;
container "2013 Formal Methods in Computer-Aided Design"; event Portland, OR;
publisher IEEE; year 2013; pages 1–8; DOI 10.1109/fmcad.2013.6679385.

**Source B.** <https://dblp.uni-trier.de/search/publ/api?q=Alur+syntax-guided+synthesis+fmcad&format=json&h=8>
Confirmed: same title, same ten authors in the same order (with "Rastislav
Bodík"); venue FMCAD; year 2013; pages 1–8; dblp key
`conf/fmcad/AlurBJMRSSSTU13`; IEEE Xplore document 6679385.

**Source C (third, incidental).** <https://api.openalex.org/works/doi:10.1109/fmcad.2013.6679385>
Confirmed: same title, same author order, venue "2013 Formal Methods in
Computer-Aided Design", 2013, pages 1–8.

**Verdict: CONFIRMED.**

```bibtex
@inproceedings{alur2013sygus,
  author    = {Rajeev Alur and Rastislav Bod{\'\i}k and Garvit Juniwal and
               Milo M. K. Martin and Mukund Raghothaman and Sanjit A. Seshia and
               Rishabh Singh and Armando Solar-Lezama and Emina Torlak and
               Abhishek Udupa},
  title     = {Syntax-Guided Synthesis},
  booktitle = {2013 Formal Methods in Computer-Aided Design (FMCAD)},
  year      = {2013},
  pages     = {1--8},
  publisher = {IEEE},
  doi       = {10.1109/FMCAD.2013.6679385}
}
```

---

## C4 — Mitchell, "Generalization as Search" (Artificial Intelligence, 1982)

**Queries run.**
CrossRef `query.bibliographic=Generalization as search Mitchell Artificial
Intelligence 1982`; CrossRef by DOI (to settle a garbled prefix in the first
response); OpenAlex by DOI; Semantic Scholar by DOI. ScienceDirect and
PhilPapers both 403; dblp reset the connection on three attempts for this query
and was not used.

**Source A.** <https://api.crossref.org/works/10.1016/0004-3702(82)90040-6>
Confirmed: title "Generalization as search"; author Tom M. Mitchell; container
"Artificial Intelligence"; volume 18; issue 2; pages 203–226; year 1982.

**Source B.** <https://api.semanticscholar.org/graph/v1/paper/DOI:10.1016/0004-3702(82)90040-6?fields=title,authors,year,venue,journal,externalIds>
Confirmed: title "Generalization as Search"; author Tom M. Mitchell; year 1982;
journal Artif. Intell., volume 18, pages 203–226; DBLP key `journals/ai/Mitchell82`.

**Source C (third, incidental).** <https://api.openalex.org/works/doi:10.1016/0004-3702(82)90040-6>
Confirmed: same title, author, journal, 1982, 18(2), 203–226.

**Trap avoided.** A CrossRef title-query response rendered the DOI as
`10.1016/0004-3712(82)90040-6`; the DOI-resolution call above shows the correct
Elsevier stem is `0004-3702`. The `3712` form does not resolve and is not used.
A second CrossRef hit — "Generalization as Search", *Readings in Artificial
Intelligence*, 1981, pp. 517–542, DOI 10.1016/b978-0-934613-03-3.50040-4 — is a
different (anthology) item and is not the record cited.

**Verdict: CONFIRMED.**

```bibtex
@article{mitchell1982generalization,
  author  = {Tom M. Mitchell},
  title   = {Generalization as Search},
  journal = {Artificial Intelligence},
  volume  = {18},
  number  = {2},
  pages   = {203--226},
  year    = {1982},
  doi     = {10.1016/0004-3702(82)90040-6}
}
```

---

## C5 — Lau, Wolfman, Domingos, Weld, "Programming by Demonstration Using Version Space Algebra" (Machine Learning, 2003)

**Queries run.**
dblp `q=Lau+Wolfman+Domingos+Weld+programming+by+demonstration+version+space+algebra`;
CrossRef by the DOI that query returned.

**Source A.** <https://dblp.uni-trier.de/search/publ/api?q=Lau+Wolfman+Domingos+Weld+programming+by+demonstration+version+space+algebra&format=json&h=8>
Confirmed: title "Programming by Demonstration Using Version Space Algebra";
authors Tessa A. Lau, Steven A. Wolfman, Pedro M. Domingos, Daniel S. Weld;
journal Machine Learning; year 2003; volume 53, number 1-2; pages 111–156;
DOI 10.1023/A:1025671410623; dblp key `journals/ml/LauWDW03`.

**Source B.** <https://api.crossref.org/works/10.1023/A:1025671410623>
Confirmed: same title; authors Tessa Lau, Steven A. Wolfman, Pedro Domingos,
Daniel S. Weld; Machine Learning; volume 53, issue 1-2; pages 111–156; 2003.

**Discrepancy noted.** dblp expands two middle initials ("Tessa A. Lau",
"Pedro M. Domingos") that CrossRef omits. The publisher-deposited (CrossRef)
form is used below, since it matches the printed byline.

**Verdict: CONFIRMED.**

```bibtex
@article{lau2003vsa,
  author  = {Tessa Lau and Steven A. Wolfman and Pedro Domingos and Daniel S. Weld},
  title   = {Programming by Demonstration Using Version Space Algebra},
  journal = {Machine Learning},
  volume  = {53},
  number  = {1--2},
  pages   = {111--156},
  year    = {2003},
  doi     = {10.1023/A:1025671410623}
}
```

---

## C6 — Muggleton, "Inductive Logic Programming" (New Generation Computing, 1991)

**Queries run.**
CrossRef `query.bibliographic=Inductive logic programming Muggleton New
Generation Computing 1991`; dblp `q=Muggleton+Inductive+Logic+Programming+year:1991:`
(the plain venue-name query returned 0 hits — dblp does not index full venue
titles that way); OpenAlex by DOI.

**Source A.** <https://dblp.uni-trier.de/search/publ/api?q=Muggleton+Inductive+Logic+Programming+year%3A1991%3A&format=json&h=10>
Confirmed: title "Inductive Logic Programming"; author Stephen H. Muggleton;
venue New Gener. Comput.; year 1991; volume 8, number 4; pages 295–318;
DOI 10.1007/BF03037089; dblp key `journals/ngc/Muggleton91`.

**Source B.** <https://api.crossref.org/works?query.bibliographic=Inductive+logic+programming+Muggleton+New+Generation+Computing+1991&rows=5>
Confirmed: title "Inductive Logic Programming"; author Stephen Muggleton;
container New Generation Computing; 1991; volume 8, issue 4; pages 295–318;
DOI 10.1007/bf03037089.

**Source C (third, incidental).** <https://api.openalex.org/works/doi:10.1007/bf03037089>
Confirmed: same title, author, journal, 1991, 8(4), 295–318.

**Discrepancy noted.** dblp gives the middle initial ("Stephen H. Muggleton");
CrossRef and OpenAlex do not. The printed byline on this paper is "Stephen
Muggleton"; that form is used.

**Verdict: CONFIRMED.**

```bibtex
@article{muggleton1991ilp,
  author  = {Stephen Muggleton},
  title   = {Inductive Logic Programming},
  journal = {New Generation Computing},
  volume  = {8},
  number  = {4},
  pages   = {295--318},
  year    = {1991},
  doi     = {10.1007/BF03037089}
}
```

---

## C7 — Muggleton & De Raedt, "Inductive Logic Programming: Theory and Methods" (Journal of Logic Programming, 1994)

**Queries run.**
dblp `q=Muggleton+De+Raedt+inductive+logic+programming+theory+and+methods`;
CrossRef by the DOI that query returned. (A first CrossRef title query hit
HTTP 429 and was retried as a DOI resolution.)

**Source A.** <https://dblp.uni-trier.de/search/publ/api?q=Muggleton+De+Raedt+inductive+logic+programming+theory+and+methods&format=json&h=5>
Confirmed: title "Inductive Logic Programming: Theory and Methods"; authors
Stephen H. Muggleton, Luc De Raedt; venue J. Log. Program.; year 1994; volume
19/20; pages 629–679; DOI 10.1016/0743-1066(94)90035-3; dblp key
`journals/jlp/MuggletonR94`.

**Source B.** <https://api.crossref.org/works/10.1016/0743-1066(94)90035-3>
Confirmed: title "Inductive Logic Programming: Theory and methods"; authors
Stephen Muggleton, Luc de Raedt; container "The Journal of Logic Programming";
volume 19-20; pages 629–679; year 1994.

**Discrepancy noted.** Title case on the final word differs ("Methods" in dblp,
"methods" in CrossRef) and CrossRef lower-cases the particle ("Luc de Raedt").
The dblp / conventional form is used. The volume is the combined special issue
19/20 in both sources — that is not a typo.

**Verdict: CONFIRMED.**

```bibtex
@article{muggleton1994ilptheory,
  author  = {Stephen Muggleton and Luc De Raedt},
  title   = {Inductive Logic Programming: Theory and Methods},
  journal = {The Journal of Logic Programming},
  volume  = {19--20},
  pages   = {629--679},
  year    = {1994},
  doi     = {10.1016/0743-1066(94)90035-3}
}
```

---

## C8 — Cropper & Dumančić, "Inductive Logic Programming At 30: A New Introduction" (JAIR, 2022)

**Queries run.**
JAIR article page (publisher of record); dblp
`q=Cropper+Dumancic+inductive+logic+programming+at+30`; CrossRef by DOI (to
check the diacritic on the second surname).

**Source A.** <https://www.jair.org/index.php/jair/article/view/13507>
Confirmed: title "Inductive Logic Programming At 30: A New Introduction";
authors Andrew Cropper, Sebastijan Dumančić; Journal of Artificial Intelligence
Research; volume 74; 2022 (published 15 June 2022); DOI 10.1613/jair.1.13507.

**Source B.** <https://dblp.uni-trier.de/search/publ/api?q=Cropper+Dumancic+inductive+logic+programming+at+30&format=json&h=8>
Confirmed: same title; authors Andrew Cropper, Sebastijan Dumancic (dblp strips
the diacritics); J. Artif. Intell. Res.; 2022; volume 74; **pages 765–850**;
DOI 10.1613/JAIR.1.13507; dblp key `journals/jair/CropperD22`.

**Source C (diacritic check).** <https://api.crossref.org/works/10.1613/jair.1.13507>
Confirmed: authors "Andrew Cropper" and "Sebastijan **Dumančić**" — the
publisher deposit carries the háček on both c's. That spelling is used.

**Trap avoided.** The same dblp query returns a *different* paper with a
near-identical name: Cropper, Dumančić, Evans & Muggleton, "Inductive logic
programming at 30", Machine Learning 111(1):147–172, 2022, DOI
10.1007/S10994-021-06089-1. Four authors, different journal, different pages.
It is not the record cited here. Two arXiv preprints (`abs/2008.07912` for the
JAIR paper, `abs/2102.10556` for the ML paper) also exist and are not cited.

**Verdict: CONFIRMED.**

```bibtex
@article{cropper2022ilp30,
  author  = {Andrew Cropper and Sebastijan Duman{\v{c}}i{\'c}},
  title   = {Inductive Logic Programming At 30: A New Introduction},
  journal = {Journal of Artificial Intelligence Research},
  volume  = {74},
  pages   = {765--850},
  year    = {2022},
  doi     = {10.1613/jair.1.13507}
}
```

---

## C9 — Evans & Grefenstette, "Learning Explanatory Rules from Noisy Data" (JAIR, 2018)

**Queries run.**
dblp `q=Evans+Grefenstette+learning+explanatory+rules+from+noisy+data`; JAIR
article page; CrossRef by DOI (the JAIR page does not print the page range).

**Source A.** <https://dblp.uni-trier.de/search/publ/api?q=Evans+Grefenstette+learning+explanatory+rules+from+noisy+data&format=json&h=8>
Confirmed: title "Learning Explanatory Rules from Noisy Data"; authors Richard
Evans, Edward Grefenstette; venue J. Artif. Intell. Res.; year 2018; volume 61;
pages 1–64; DOI 10.1613/JAIR.5714; dblp key `journals/jair/EvansG18`.

**Source B.** <https://www.jair.org/index.php/jair/article/view/11172> and
<https://api.crossref.org/works/10.1613/jair.5714>
JAIR confirmed: same title, both authors, JAIR volume 61, 2018 (published 26
January 2018), DOI 10.1613/jair.5714; the page range is not shown on that page.
CrossRef confirmed the page range 1–64 together with title, authors, journal,
volume and year.

**Trap avoided.** dblp also lists an IJCAI 2018 extended abstract of the same
name (pages 5598–5602, DOI 10.24963/IJCAI.2018/792) and a 2017 arXiv preprint
(`abs/1711.04574`). Neither is the record cited.

**Verdict: CONFIRMED.**

```bibtex
@article{evans2018dilp,
  author  = {Richard Evans and Edward Grefenstette},
  title   = {Learning Explanatory Rules from Noisy Data},
  journal = {Journal of Artificial Intelligence Research},
  volume  = {61},
  pages   = {1--64},
  year    = {2018},
  doi     = {10.1613/jair.5714}
}
```

---

## C10 — Cropper & Morel, "Learning programs by learning from failures" (Machine Learning, 2021) — Popper

**Queries run.**
dblp `q=Cropper+Morel+learning+programs+by+learning+from+failures`; CrossRef by
the DOI that query returned.

**Source A.** <https://dblp.uni-trier.de/search/publ/api?q=Cropper+Morel+learning+programs+by+learning+from+failures&format=json&h=8>
Confirmed: title "Learning programs by learning from failures"; authors Andrew
Cropper, Rolf Morel; venue Mach. Learn.; year 2021; volume 110, number 4; pages
801–856; DOI 10.1007/S10994-020-05934-Z; dblp key `journals/ml/CropperM21`.

**Source B.** <https://api.crossref.org/works/10.1007/s10994-020-05934-z>
Confirmed: same title; same two authors; container Machine Learning; volume 110,
issue 4; pages 801–856; year 2021. The abstract names the system **Popper** and
the three-stage generate/test/constrain loop.

**Trap avoided.** dblp also lists the 2020 arXiv preprint `abs/2005.02259`; the
journal version is cited.

**Verdict: CONFIRMED.**

```bibtex
@article{cropper2021popper,
  author  = {Andrew Cropper and Rolf Morel},
  title   = {Learning Programs by Learning from Failures},
  journal = {Machine Learning},
  volume  = {110},
  number  = {4},
  pages   = {801--856},
  year    = {2021},
  doi     = {10.1007/s10994-020-05934-z}
}
```

---

## C11 — Yang, Wu, Jiang, "Learning action models from plan examples using weighted MAX-SAT" (Artificial Intelligence, 2007) — ARMS

**Queries run.**
dblp `q=Yang+Wu+Jiang+learning+action+models+plan+examples+weighted+MAX-SAT`;
CrossRef by the DOI that query returned.

**Source A.** <https://dblp.uni-trier.de/search/publ/api?q=Yang+Wu+Jiang+learning+action+models+plan+examples+weighted+MAX-SAT&format=json&h=8>
Confirmed: title "Learning action models from plan examples using weighted
MAX-SAT"; authors Qiang Yang, Kangheng Wu, Yunfei Jiang (dblp disambiguates the
first as "Qiang Yang 0001"); venue Artificial Intelligence; year 2007; volume
171, number 2-3; pages 107–143; DOI 10.1016/J.ARTINT.2006.11.005; dblp key
`journals/ai/YangWJ07`.

**Source B.** <https://api.crossref.org/works/10.1016/j.artint.2006.11.005>
Confirmed: same title; authors Qiang Yang, Kangheng Wu, Yunfei Jiang in that
order; container Artificial Intelligence; volume 171, issue 2-3; pages 107–143;
year 2007.

**Verdict: CONFIRMED.**

```bibtex
@article{yang2007arms,
  author  = {Qiang Yang and Kangheng Wu and Yunfei Jiang},
  title   = {Learning Action Models from Plan Examples Using Weighted {MAX-SAT}},
  journal = {Artificial Intelligence},
  volume  = {171},
  number  = {2--3},
  pages   = {107--143},
  year    = {2007},
  doi     = {10.1016/j.artint.2006.11.005}
}
```

---

## Not pursued

**LOCM (Cresswell, McCluskey, West).** Named in the task as an optional
alternative to ARMS for the action-model-learning slot. One anchor is enough for
a one-sentence mention in a workshop related-work section, and ARMS (C11) is the
closer match to a ledger-driven miner, so no LOCM record was sought. **No LOCM
record is offered here** — nothing was written down that was not verified.

## Dropped

**None.** All eleven candidates cleared the two-source rule. Three near-miss
records were identified during verification and are explicitly *not* cited: the
1981 *Readings in AI* reprint of Mitchell; the four-author Machine Learning
"Inductive logic programming at 30"; and the IJCAI 2018 extended abstract of
Evans & Grefenstette. Each is recorded above under "Trap avoided" so a later
reader can see they were considered and rejected, not overlooked.

## Summary

| # | key | verdict |
|---|---|---|
| C1 | `solarlezama2006sketching` | CONFIRMED (CrossRef + Semantic Scholar + dblp) |
| C2 | `solarlezama2008thesis` | CONFIRMED (UC Berkeley EECS + thesis title page at MIT CSAIL) |
| C3 | `alur2013sygus` | CONFIRMED (CrossRef + dblp + OpenAlex) |
| C4 | `mitchell1982generalization` | CONFIRMED (CrossRef + Semantic Scholar + OpenAlex) |
| C5 | `lau2003vsa` | CONFIRMED (dblp + CrossRef) |
| C6 | `muggleton1991ilp` | CONFIRMED (dblp + CrossRef + OpenAlex) |
| C7 | `muggleton1994ilptheory` | CONFIRMED (dblp + CrossRef) |
| C8 | `cropper2022ilp30` | CONFIRMED (JAIR + dblp + CrossRef) |
| C9 | `evans2018dilp` | CONFIRMED (dblp + JAIR + CrossRef) |
| C10 | `cropper2021popper` | CONFIRMED (dblp + CrossRef) |
| C11 | `yang2007arms` | CONFIRMED (dblp + CrossRef) |

11 confirmed, 0 dropped, 1 not pursued (LOCM).
