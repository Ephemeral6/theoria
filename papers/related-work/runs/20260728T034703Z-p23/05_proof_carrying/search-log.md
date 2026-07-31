# Search log — line 5, proof-carrying code

Run `20260728T034703Z-p23`. Every query issued, the tool used, one line on what came
back. Failures are logged as carefully as successes: several authoritative sources
(ACM DL, IEEE Xplore, ScienceDirect, ResearchGate, `dblp.org` proper) refused automated
access, and the working routes around them are the reusable part of this trail.

**Red line 3.** Every query below is bibliographic. No ARC game page, walkthrough,
leaderboard write-up, `schema-harness.github.io` page or ARC-AGI-3 trajectory dataset
was queried, returned or opened. No result began describing the mechanics of any
specific game. No back-off was triggered.

## Phase 1 — DBLP structured API (failed)

| # | tool | query / URL | result |
|---|---|---|---|
| 1 | WebFetch | `dblp.org/search/publ/api?q=Necula+proof-carrying+code&format=json` | timeout, 60s |
| 2 | WebFetch | `dblp.org/search/publ/api?q=Safe+Kernel+Extensions+Without+Run-Time+Checking` | ECONNRESET |
| 3 | WebFetch | `dblp.org/search/publ/api?q=Foundational+Proof-Carrying+Code` | ECONNRESET |
| 4 | WebFetch | `dblp.org/search/publ/api?q=Certifying+algorithms` | ECONNRESET |

Conclusion: the `dblp.org` host is unreachable from here. Mirror `dblp.uni-trier.de`
was found to work later (row 30) and is the route to use for DBLP on this machine.

## Phase 2 — first source: CrossRef via the `paper-search` CLI

| # | tool | query | result |
|---|---|---|---|
| 5 | paper-search (`-s dblp,crossref,semantic,openalex`) | `Proof-Carrying Code Necula` | 8 hits, all CrossRef (dblp/semantic/openalex returned 0). Found POPL '97 DOI `10.1145/263699.263712`, pp. 106--119, 1997, 1037 citing works. Also surfaced 4 same-titled reprints/encyclopedia chapters to be kept apart |
| 6 | paper-search (`-s crossref,semantic,openalex`) | `Safe Kernel Extensions Without Run-Time Checking` | OSDI '96 record, DOI `10.1145/238721.238781`, pp. 229--243, 252 citing works; plus the SIGOPS OSR 30(SI) reprint `10.1145/248155.238781` — flagged as a duplicate-record trap |
| 7 | paper-search | `Foundational proof-carrying code Appel` | LICS record DOI `10.1109/lics.2001.932501`, pp. 247--256; CrossRef date field corrupt (1970), year needs a second source |
| 8 | paper-search | `Certifying algorithms Mehlhorn McConnell` | *Computer Science Review* 5(2):119--161, DOI `10.1016/j.cosrev.2010.09.009`, 2011 |
| 9 | paper-search | `Program verification the very idea Fetzer` | CACM 31(9):1048--1063, 1988, DOI `10.1145/48529.48530`, **with full abstract** — the checkable summary comes from here. Also 1993 and 2001 Springer reprints of the same title |
| 10 | paper-search | `Social processes and proofs of theorems and programs` | CACM 22(5):271--280, 1979, DOI `10.1145/359104.359106`, **with full abstract**. Also a 1978 DTIC report, a 1980 *Mathematical Intelligencer* version (author mis-keyed "Upton"), a 1993 chapter and Appel's 2004 PLDI talk of the near-same title — four merge traps |
| 11 | paper-search | `Boehm verifying and validating software requirements and design specifications` | *IEEE Software* 1(1):75--88, **1984**, DOI `10.1109/ms.1984.233702` |
| 12 | paper-search | `DRAT-trim efficient checking and trimming using expressive clausal proofs` | SAT 2014 chapter, DOI `10.1007/978-3-319-09284-3_31`, pp. 422--429; LNCS volume number not given by CrossRef |
| 13 | paper-search | `Leroy formal verification of a realistic compiler CompCert` | CACM 52(7):107--115, 2009, DOI `10.1145/1538788.1538814`, **with full abstract** |

## Phase 3 — second source: Semantic Scholar Graph API, by DOI

All via WebFetch on `api.semanticscholar.org/graph/v1/paper/DOI:<doi>`.

| # | DOI queried | result |
|---|---|---|
| 14 | `10.1145/263699.263712` | "Proof-carrying code", 1997, POPL; DBLP key `conf/popl/Necula97`. **Agrees** |
| 15 | `10.1145/238721.238781` | "Safe kernel extensions without run-time checking", 1996, USENIX OSDI; DBLP key `conf/osdi/NeculaL96`. **Agrees** |
| 16 | `10.1109/LICS.2001.932501` | "Foundational proof-carrying code", **2001**, LICS 16th Annual; DBLP key `conf/lics/Appel01`. **Agrees**; resolves CrossRef's corrupt date |
| 17 | `10.1016/j.cosrev.2010.09.009` | "Certifying algorithms", 2011, Computer Science Review; DBLP key `journals/csr/McConnellMNS11`. **Agrees** |
| 18 | `10.1007/978-3-319-09284-3_31` | DRAT-trim, 2014, SAT; DBLP key `conf/sat/WetzlerHH14`. **Agrees** |
| 19 | `10.1145/1538788.1538814` | Leroy, 2009, CACM; DBLP key `journals/cacm/Leroy09`. **Agrees** |
| 20 | `10.1145/48529.48530` | Fetzer, 1988, CACM. Title/venue/year **agree**; but DBLP key given as `books/sp/93/Fetzer93`, which belongs to the 1993 book chapter — record-merge artefact, logged, key not used |
| 21 | `10.1145/359104.359106` | De Millo/Lipton/Perlis, 1979, CACM; DBLP key `journals/cacm/DeMilloLP79`. **Agrees** |
| 22 | `10.1109/MS.1984.233702` | Boehm, IEEE Software — **year reported as 1989, conflicting with CrossRef's 1984**. DBLP key in the same record reads `journals/software/Boehm84`, i.e. self-inconsistent. Escalated to phase 4 |

## Phase 4 — resolving the Boehm year conflict

| # | tool | query / URL | result |
|---|---|---|---|
| 23 | WebSearch | `Boehm "Verifying and Validating..." IEEE Software 1984 volume 1 issue 1 ieeexplore` (domains limited to ieeexplore/dblp/doi/computer.org) | surfaced DBLP's *IEEE Software Volume 1, 1984* index and IEEE Xplore document 1695100; both point to 1984, vol. 1, no. 1, pp. 75--88 |
| 24 | WebFetch | `ieeexplore.ieee.org/document/1695100/` | page returned empty (JavaScript-rendered) — unusable |
| 25 | WebFetch | `dblp.org/rec/journals/software/Boehm84.html` | ECONNRESET |
| 26 | WebFetch | `api.openalex.org/works/doi:10.1109/MS.1984.233702` | Boehm, IEEE Software, **1984**, vol. 1, issue 1, pp. 75--88. Third source |
| 27 | WebFetch | `dblp.uni-trier.de/rec/journals/software/Boehm84.html` | **mirror works.** IEEE Software 1(1):75--88, **1984**. Second independent source |

**Resolved:** 1984. CrossRef + DBLP + OpenAlex agree; the DOI string encodes 1984 and
IEEE Software vol. 1 no. 1 is the journal's first issue. Semantic Scholar's 1989 is an
isolated aggregator error, disclosed in the line file.

## Phase 5 — abstracts, so every summary sentence is checkable (red line 5)

| # | tool | query / URL | result |
|---|---|---|---|
| 28 | WebFetch | `dl.acm.org/doi/10.1145/263699.263712` | HTTP 403 |
| 29 | WebFetch | `sciencedirect.com/science/article/pii/S1574013710000560` | HTTP 403 |
| 30 | WebFetch | `usenix.org/legacy/publications/library/proceedings/osdi96/necula.html` | HTTP 403 |
| 31 | WebFetch | `cs.princeton.edu/~appel/papers/fpcc.pdf` | **success.** Header reads "To appear in LICS '01, 16th Annual IEEE Symposium on Logic in Computer Science"; full abstract captured verbatim (*quis custodiat ipsos custodes*, smallest set of axioms) |
| 32 | WebFetch | `api.openalex.org/works/doi:10.1016/j.cosrev.2010.09.009` | `abstract_inverted_index` null — no abstract. Also reports year **2010**, the online-first date; noted as a discrepancy against the 2011 issue year |
| 33 | WebFetch | `cs.utexas.edu/~marijn/publications/drat-trim.pdf` | DNS failure (ENOTFOUND) |
| 34 | WebSearch | `"Safe Kernel Extensions Without Run-Time Checking" Necula Lee OSDI 1996 abstract "proof-carrying code" term introduced` | **key result.** Abstract recovered: the kernel publishes a safety policy and the application supplies binaries "in a special form called proof-carrying code, or simply PCC". Establishes OSDI '96 as the origin of the term |
| 35 | WebSearch | `McConnell Mehlhorn Näher Schweitzer "Certifying algorithms" ... "certificate or witness" checker` | confirmed CSR 5(2):119--161, 2011; surfaced two open PDF mirrors |
| 36 | WebFetch | `alg.cs.uni-kl.de/.../CertifyingAlgorithms.pdf` | DNS failure (ENOTFOUND) |
| 37 | WebFetch | `people.mpi-inf.mpg.de/~mehlhorn/ftp/CertifyingAlgorithms.pdf` | PDF fetched but not parsed by the fetch tool; binary saved to local tool-results cache |
| 38 | Read (PDF, p.1) | the cached MPI PDF | **success.** Title, four authors with affiliations, and full abstract verbatim; footer "Preprint submitted to Elsevier / August 30, 2010" — explains OpenAlex's 2010 |
| 39 | WebSearch | `Wetzler Heule Hunt "DRAT-trim" SAT 2014 abstract clausal proof ... deletion` | LNCS **8561**, pp. 422--429, 2014; abstract content confirmed |
| 40 | WebFetch | `link.springer.com/chapter/10.1007/978-3-319-09284-3_31` | 303 redirect to `idp.springer.com` |
| 41 | WebFetch | the `idp.springer.com` authorize URL | 302 redirect back with `error=cookies_not_supported` |
| 42 | WebFetch | the redirected Springer chapter URL | **success.** Publisher of record confirms title, three authors, SAT 2014, LNCS **8561**, pp. 422--429, 2014, DOI, and full abstract verbatim |
| 43 | WebFetch | `alastairreid.github.io/RelatedWork/papers/necula:popl:1997/` | confirms title/author/POPL '97/1997/Paris; no abstract on the page |
| 44 | WebFetch | `people.eecs.berkeley.edu/~necula/Papers/pcc_popl97.pdf` | HTTP 404 |
| 45 | WebFetch | `api.semanticscholar.org/.../CorpusID:1797763` | HTTP 429 rate-limited |
| 46 | WebFetch | S2 Graph API, `10.1145/263699.263712`, `fields=abstract` | abstract field elided by publisher |
| 47 | WebFetch | `people.eecs.berkeley.edu/~necula/papers.html` | author's own citation line: "Presented at the ACM Symposium on Principles of Programming Languages (POPL'97), January 1997"; notes the 2007 Most Influential POPL 1997 Paper award; only a `.ps` download offered |
| 48 | WebSearch | exact-phrase `"proof-carrying code (PCC), a mechanism by which a host system can determine with certainty that it is safe to execute a program supplied"` | **phrase matches** the ACM DL record for DOI `10.1145/263699.263712` and the Google Scholar lookup for the same DOI. POPL '97 abstract wording confirmed without needing to defeat the 403 |

## Phase 6 — the specification-validity bullet and its traps

| # | tool | query / URL | result |
|---|---|---|---|
| 49 | WebSearch | `Boehm 1984 IEEE Software ... "am I building the right product" verification validation definition` | confirms bibliographic record again, but **does not** confirm the epigram is in the 1984 article; surfaced Ryan, "On the Use of the Terms Verification and Validation", which traces the attribution |
| 50 | WebFetch | the Ryan PDF on researchgate.net | HTTP 403 |
| 51 | WebFetch | `semanticscholar.org/paper/...Boehm/4eda9e97...` | page returned empty |
| 52 | WebSearch | `Boehm "Am I building the product right" ... 1984 "IEEE Software" quote page 75` | epigram broadly attributed to Boehm across many secondary sources; **no source reached quotes it with a page from the 1984 article**. Outcome: cite Boehm 1984 for the distinction, do not quote the epigram against it |
| 53 | paper-search | `Guidelines for verifying and validating software requirements and design specifications Boehm Euro IFIP 1979` | **no matching record.** CrossRef returns only the 1984 IEEE Software paper plus unrelated BSI standards. The 1979 Euro IFIP paper is not DOI-indexed → **quarantine Q1** |
| 54 | WebSearch | `Fetzer "Program verification: the very idea" rebuttal letters ACM Forum CACM 1989 volume 32 ...` | confirms rebuttals exist and are separate items: "The March 1989 issue ... printed eight pages of technical correspondence on the paper plus three pages of discussion in the ACM Forum". Surfaced DOI `10.1145/63334.315936` |
| 55 | WebFetch | `api.crossref.org/works/10.1145/63334.315936` | generic title "Technical correspondence", CACM **32(4):506--512, April 1989**, corporate author, no individual letter-writers listed — **conflicts with the March attribution in row 54** → **quarantine Q2** |

## Outcome

9 entries admitted with two agreeing independent sources each; 3 quarantined (Q1 Boehm
1979 Euro IFIP — zero sources; Q2 the 1989 CACM technical correspondence — single
source, internally inconsistent; Q3 Alkassar et al. 2011 — single source, coverage
already at target). Two metadata anomalies disclosed rather than silently corrected:
Semantic Scholar's 1989 for Boehm, and OpenAlex's 2010 for McConnell et al.
