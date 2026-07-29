# Search trace — line 5: proof-carrying code, certifying algorithms, specification validity

Run: `20260728T102014Z-P7`. Date of search: 2026-07-28.

**Verification rule applied.** Every record below required two *independent*
confirmations of authors + year + venue before being marked CONFIRMED. Nothing
was filled in from memory. Where a first-pass web-search snippet disagreed with
an authoritative record, the authoritative record won and the disagreement is
noted. One candidate is DROPPED, with the reason.

Sources used as authorities:

* **CrossRef REST API** (`api.crossref.org`) — publisher-deposited DOI metadata.
* **DBLP** (`dblp.org`) — independently curated CS bibliography, Schloss Dagstuhl.
* **E.W. Dijkstra Archive**, UT Austin (`cs.utexas.edu/~EWD`) — primary text.
* **UT Austin Libraries institutional repository** (`repositories.lib.utexas.edu`)
  — a separate cataloguing system from the `~EWD` web archive.
* **TU Eindhoven research portal** (`research.tue.nl`).

ACM Digital Library (`dl.acm.org`), USENIX (`usenix.org`), Semantic Scholar and
`web.archive.org` were attempted and returned 403 / 429 / connection refused from
this environment; they are therefore recorded as *attempted, unavailable* and
were not counted as confirmations.

---

## 1. Necula, "Proof-Carrying Code", POPL 1997 — **CONFIRMED**

Queries run:

* `Necula "Proof-Carrying Code" POPL 1997 ACM Digital Library pages`
* direct DOI lookup `10.1145/263699.263712`
* direct DBLP record lookup

**Source A** — https://api.crossref.org/works/10.1145/263699.263712
Confirmed: title "Proof-Carrying Code"; sole author George C. Necula;
container *Proceedings of the 24th ACM SIGPLAN-SIGACT Symposium on Principles of
Programming Languages — POPL '97*; publisher ACM Press, New York; year 1997;
pages 106–119; event Paris, France, 15–17 January 1997.

**Source B** — https://dblp.org/rec/conf/popl/Necula97.html
Confirmed independently: title "Proof-Carrying Code."; author George C. Necula;
venue POPL 1997; pages 106–119; DOI 10.1145/263699.263712.

Attempted, unavailable: https://dl.acm.org/doi/10.1145/263699.263712 (HTTP 403).

Verdict: **CONFIRMED**. Both sources agree on authors, year, venue and pages.

```bibtex
@inproceedings{necula1997pcc,
  author    = {George C. Necula},
  title     = {Proof-Carrying Code},
  booktitle = {Proceedings of the 24th {ACM} {SIGPLAN}-{SIGACT} Symposium on
               Principles of Programming Languages ({POPL} '97)},
  pages     = {106--119},
  year      = {1997},
  address   = {Paris, France},
  publisher = {ACM Press},
  doi       = {10.1145/263699.263712}
}
```

---

## 2. Necula & Lee, "Safe Kernel Extensions Without Run-Time Checking", OSDI 1996 — **CONFIRMED**

Queries run:

* `Necula Lee "Safe Kernel Extensions Without Run-Time Checking" OSDI 1996 Seattle pages 229`
* direct DBLP record lookup
* direct DOI lookup `10.1145/238721.238781`

**Source A** — https://dblp.org/rec/conf/osdi/NeculaL96.html
Confirmed: title "Safe Kernel Extensions Without Run-Time Checking."; authors
George C. Necula and Peter Lee; venue OSDI 1996; pages 229–243; DOI
10.1145/238721.238781.

**Source B** — https://api.crossref.org/works/10.1145/238721.238781
Confirmed independently: title "Safe kernel extensions without run-time
checking"; same two authors; container *Proceedings of the Second USENIX
Symposium on Operating Systems Design and Implementation*; year 1996; pages
229–243; event OSDI '96, Seattle, Washington, USA.

Attempted, unavailable:
https://www.usenix.org/conference/osdi-96/safe-kernel-extensions-without-run-time-checking
(HTTP 403 to the fetcher; the record appears in search indexing as USENIX
OSDI '96, consistent with A and B, but is not counted as a confirmation).

Note: a distinct reprint exists in *ACM SIGOPS Operating Systems Review*
(DOI 10.1145/248155.238781). The OSDI proceedings version is the one cited.

Verdict: **CONFIRMED**.

```bibtex
@inproceedings{necula1996safekernel,
  author    = {George C. Necula and Peter Lee},
  title     = {Safe Kernel Extensions Without Run-Time Checking},
  booktitle = {Proceedings of the Second {USENIX} Symposium on Operating
               Systems Design and Implementation ({OSDI} '96)},
  pages     = {229--243},
  year      = {1996},
  address   = {Seattle, Washington, USA},
  doi       = {10.1145/238721.238781}
}
```

---

## 3. Appel, "Foundational Proof-Carrying Code", LICS 2001 — **CONFIRMED**

Queries run:

* `Appel "Foundational Proof-Carrying Code" LICS 2001 sixteenth annual IEEE symposium logic in computer science pages`
* direct DBLP record lookup
* direct DOI lookup `10.1109/LICS.2001.932501`

**Source A** — https://dblp.org/rec/conf/lics/Appel01.html
Confirmed: title "Foundational Proof-Carrying Code."; sole author Andrew W.
Appel; venue LICS 2001; pages 247–256; DOI 10.1109/LICS.2001.932501.

**Source B** — https://api.crossref.org/works/10.1109/LICS.2001.932501
Confirmed independently: title "Foundational proof-carrying code"; author
A.W. Appel; container *Proceedings 16th Annual IEEE Symposium on Logic in
Computer Science*; publisher IEEE Computer Society; year 2001; pages 247–256.

**Supporting (venue string only)** —
https://sigmod.org/publications/dblp/db/conf/lics/lics2001.html
Confirmed the full proceedings title: *16th Annual IEEE Symposium on Logic in
Computer Science, 16–19 June 2001, Boston, Massachusetts, USA, Proceedings*,
IEEE Computer Society, 2001, ISBN 0-7695-1281-X.

**Discrepancy resolved.** A first-pass web-search snippet reported pages
"247–258". Both authoritative records (DBLP and CrossRef) give **247–256**.
The snippet was discarded.

Verdict: **CONFIRMED**.

```bibtex
@inproceedings{appel2001fpcc,
  author    = {Andrew W. Appel},
  title     = {Foundational Proof-Carrying Code},
  booktitle = {Proceedings of the 16th Annual {IEEE} Symposium on Logic in
               Computer Science ({LICS} 2001)},
  pages     = {247--256},
  year      = {2001},
  address   = {Boston, Massachusetts, USA},
  publisher = {IEEE Computer Society},
  doi       = {10.1109/LICS.2001.932501}
}
```

---

## 4. McConnell, Mehlhorn, Näher & Schweitzer, "Certifying algorithms", Computer Science Review 2011 — **CONFIRMED**

Queries run:

* `McConnell Mehlhorn Näher Schweitzer "Certifying algorithms" Computer Science Review 2011 volume issue pages`
* direct DOI lookup `10.1016/j.cosrev.2010.09.009`
* direct DBLP record lookup

**Source A** — https://api.crossref.org/works/10.1016/j.cosrev.2010.09.009
Confirmed: title "Certifying algorithms"; authors R.M. McConnell, K. Mehlhorn,
S. Näher, P. Schweitzer; journal *Computer Science Review*; volume 5, issue 2;
pages 119–161; year 2011; publisher Elsevier BV.

**Source B** — https://dblp.org/rec/journals/csr/McConnellMNS11.html
Confirmed independently, with full given names: Ross M. McConnell, Kurt
Mehlhorn, Stefan Näher, Pascal Schweitzer; *Computer Science Review* 5(2):
119–161, 2011.

Verdict: **CONFIRMED**.

```bibtex
@article{mcconnell2011certifying,
  author  = {Ross M. McConnell and Kurt Mehlhorn and Stefan N{\"a}her and
             Pascal Schweitzer},
  title   = {Certifying algorithms},
  journal = {Computer Science Review},
  volume  = {5},
  number  = {2},
  pages   = {119--161},
  year    = {2011},
  doi     = {10.1016/j.cosrev.2010.09.009}
}
```

---

## 5. Blum & Kannan, "Designing programs that check their work", JACM 1995 — **CONFIRMED**

Queries run:

* `Blum Kannan "Designing programs that check their work" Journal of the ACM 1995 volume 42 pages 269`
* direct DOI lookup `10.1145/200836.200880`
* direct DBLP record lookup

**Source A** — https://api.crossref.org/works/10.1145/200836.200880
Confirmed: title "Designing programs that check their work"; authors Manuel Blum
and Sampath Kannan; *Journal of the ACM*; volume 42, issue 1; pages 269–291;
year 1995; publisher ACM.

**Source B** — https://dblp.org/rec/journals/jacm/BlumK95.html
Confirmed independently: title "Designing Programs that Check Their Work.";
same authors; J. ACM 42(1): 269–291, 1995.

Note: an earlier conference version exists (STOC 1989, DOI 10.1145/73007.73015).
The JACM version is the one cited.

Verdict: **CONFIRMED**.

```bibtex
@article{blum1995checkers,
  author  = {Manuel Blum and Sampath Kannan},
  title   = {Designing Programs that Check Their Work},
  journal = {Journal of the ACM},
  volume  = {42},
  number  = {1},
  pages   = {269--291},
  year    = {1995},
  doi     = {10.1145/200836.200880}
}
```

---

## 6. De Millo, Lipton & Perlis, "Social processes and proofs of theorems and programs", CACM 1979 — **CONFIRMED**

Queries run:

* `De Millo Lipton Perlis "Social Processes and Proofs of Theorems and Programs" CACM 1979 volume 22 number 5 pages`
* direct DOI lookup `10.1145/359104.359106`
* direct DBLP record lookup (first guess `journals/cacm/MilloLP79` returned 404;
  correct key is `journals/cacm/DeMilloLP79`)

**Source A** — https://api.crossref.org/works/10.1145/359104.359106
Confirmed: title "Social processes and proofs of theorems and programs"; authors
Richard A. De Millo (Georgia Tech), Richard J. Lipton (Yale), Alan J. Perlis
(Yale); *Communications of the ACM*; volume 22, issue 5; pages 271–280; year
1979; publisher ACM.

**Source B** — https://dblp.org/rec/journals/cacm/DeMilloLP79.html
Confirmed independently: title "Social Processes and Proofs of Theorems and
Programs"; authors Richard A. DeMillo, Richard J. Lipton, Alan J. Perlis; CACM
22(5): 271–280, 1979.

**Name-form note.** CrossRef renders the first author "De Millo" (two words,
matching the journal byline); DBLP normalises to "DeMillo". The two-word form is
used in the record below. This is an orthographic variance, not a metadata
conflict.

Verdict: **CONFIRMED**.

```bibtex
@article{demillo1979social,
  author  = {Richard A. De Millo and Richard J. Lipton and Alan J. Perlis},
  title   = {Social Processes and Proofs of Theorems and Programs},
  journal = {Communications of the ACM},
  volume  = {22},
  number  = {5},
  pages   = {271--280},
  year    = {1979},
  doi     = {10.1145/359104.359106}
}
```

---

## 7. Fetzer, "Program verification: the very idea", CACM 1988 — **CONFIRMED**

Queries run:

* `Fetzer "Program Verification: The Very Idea" Communications of the ACM 1988 volume 31 issue 9 pages`
* direct DOI lookup `10.1145/48529.48530`
* direct DBLP record lookup (the CACM volume-31 index page truncated before
  issue 9, so the per-record URL was used instead)

**Source A** — https://api.crossref.org/works/10.1145/48529.48530
Confirmed: title "Program verification: the very idea"; sole author James H.
Fetzer (University of Minnesota, Duluth); *Communications of the ACM*; volume 31,
issue 9; pages 1048–1063; year 1988; publisher ACM.

**Source B** — https://dblp.org/rec/journals/cacm/Fetzer88.html
Confirmed independently: title "Program Verification: The Very Idea."; author
James H. Fetzer; CACM 31(9): 1048–1063, 1988; DOI 10.1145/48529.48530.

Verdict: **CONFIRMED**.

```bibtex
@article{fetzer1988veryidea,
  author  = {James H. Fetzer},
  title   = {Program Verification: The Very Idea},
  journal = {Communications of the ACM},
  volume  = {31},
  number  = {9},
  pages   = {1048--1063},
  year    = {1988},
  doi     = {10.1145/48529.48530}
}
```

---

## 8. Boehm, "Verifying and validating software requirements and design specifications", IEEE Software 1984 — **CONFIRMED**

Queries run:

* `Boehm "Verifying and Validating Software Requirements and Design Specifications" IEEE Software 1984 volume 1 pages 75`
* direct DBLP record lookup
* direct DOI lookup `10.1109/MS.1984.233702`

**Source A** — https://dblp.org/rec/journals/software/Boehm84.html
Confirmed: title "Verifying and Validating Software Requirements and Design
Specifications."; author Barry W. Boehm; *IEEE Software*; volume 1, issue 1;
pages 75–88; year 1984.

**Source B** — https://api.crossref.org/works/10.1109/MS.1984.233702
Confirmed independently: same title; author B.W. Boehm; *IEEE Software* 1(1):
75–88, 1984; publisher IEEE.

This is the paper carrying Boehm's formulation of the distinction —
verification asks whether the product is being built right, validation whether
the right product is being built. **The verified fact here is the bibliographic
record.** The wording of the formulation itself was not fetched from the
paywalled full text and is therefore paraphrased, not quoted, in the draft.

Verdict: **CONFIRMED**.

```bibtex
@article{boehm1984vandv,
  author  = {Barry W. Boehm},
  title   = {Verifying and Validating Software Requirements and Design
             Specifications},
  journal = {IEEE Software},
  volume  = {1},
  number  = {1},
  pages   = {75--88},
  year    = {1984},
  doi     = {10.1109/MS.1984.233702}
}
```

---

## 9. Dijkstra, "Notes on Structured Programming" (EWD249), 1970 — **CONFIRMED**, and the quotation located

This is the entry the brief flagged as most often mis-attributed. It was checked
against the **primary text**, not against quotation aggregators.

Queries run:

* `Dijkstra "testing shows the presence, not the absence of bugs" original source EWD Notes on Structured Programming 1969 NATO`
* `"Notes on Structured Programming" EWD249 1970 Dijkstra "second edition" T.H.-Report 70-WSK-03 Technological University Eindhoven`
* direct fetches of the EWD Archive transcription, the EWD BibTeX index, the UT
  Austin repository item, and the TU Eindhoven portal record

**Source A (primary text)** —
https://www.cs.utexas.edu/~EWD/transcriptions/EWD02xx/EWD249/EWD249.html
Confirmed by reading the document itself: title *Notes on Structured
Programming* (EWD 249); author Prof. dr. Edsger W. Dijkstra; dated August 1969,
second edition April 1970; report number **T.H.-Report 70-WSK-03**. The section
list was retrieved, and the section **"On the reliability of mechanisms"**
contains, under the heading "Corollary of the first part of this section:", the
sentence:

> "Program testing can be used to show the presence of bugs, but never to show
> their absence!"

(Note: a first attempt at
`https://www.cs.utexas.edu/~EWD/transcriptions/EWD02xx/EWD249.html` returned 404;
the working path has `EWD249/` as a directory.)

**Source B (bibliographic, independent cataloguing system)** —
https://repositories.lib.utexas.edu/items/e7a89f42-dbf6-4929-802d-c75d1cbac378
Confirmed: title "Notes on Structured Programming"; author Dijkstra, Edsger Wybe;
date April 1970; EWD number 249; handle https://hdl.handle.net/2152/126640;
DOI 10.26153/tsw/53177; note "circulated privately".

**Source C (supporting, same archive, different page)** —
https://www.cs.utexas.edu/~EWD/indexBibTeX.html
Confirmed the archive's own BibTeX: `@unpublished{EWD:EWD249, ... month = apr,
year = "1970", note = "circulated privately" }`.

**Source D (supporting, the published reprint)** —
https://research.tue.nl/en/publications/notes-on-structured-programming
Confirmed a separately published form: "Notes on structured programming",
E.W. Dijkstra, *APIC Studies in Data Processing* vol. 8, Academic Press, 1972,
pp. 1–82 — i.e. Dijkstra's contribution to Dahl, Dijkstra & Hoare,
*Structured Programming*.

Verdict: **CONFIRMED**, and the quotation is located precisely.

**Finding on the mis-attribution — this is the point the brief asked for.**

1. The sentence **Dijkstra actually wrote** is *"Program testing can be used to
   show the presence of bugs, but never to show their absence!"* It is in
   **EWD249, section "On the reliability of mechanisms"**. Verified against the
   primary text.
2. The form that circulates most widely — *"Testing shows the presence, not the
   absence of bugs"* — is **not Dijkstra's wording in EWD249**. It is a
   compression. See the DROPPED entry below for where it is usually said to come
   from and why that attribution was not accepted here.
3. Two further common mis-cites to avoid: the 1972 Academic Press volume is a
   *reprint* of EWD249, not the origin (Source D shows the two are distinct
   records); and EWD249 is dated 1970 in its second edition, so a bare
   "Dijkstra 1969" is at best ambiguous.

Recommended practice for the paper: cite EWD249 and quote Dijkstra's own
sentence verbatim. Do not use the compressed form.

```bibtex
@techreport{dijkstra1970notes,
  author      = {Edsger W. Dijkstra},
  title       = {Notes on Structured Programming},
  number      = {EWD249; T.H.-Report 70-WSK-03},
  institution = {Technological University Eindhoven},
  year        = {1970},
  month       = apr,
  note        = {Second edition; first version August 1969. Circulated
                 privately. E.W. Dijkstra Archive, University of Texas at
                 Austin. The sentence ``Program testing can be used to show the
                 presence of bugs, but never to show their absence!'' is in the
                 section ``On the reliability of mechanisms''.},
  doi         = {10.26153/tsw/53177},
  url         = {https://www.cs.utexas.edu/~EWD/transcriptions/EWD02xx/EWD249/EWD249.html}
}
```

---

## 10. Ammons, Bodík & Larus, "Mining specifications", POPL 2002 — **CONFIRMED**

Pursued as the optional specification-mining anchor, because it is the closest
prior work to the paper's actual delta: a specification obtained by generalising
from observed behaviour rather than written by hand.

Queries run: direct DOI lookup `10.1145/503272.503275`; direct DBLP record lookup.

**Source A** — https://api.crossref.org/works/10.1145/503272.503275
Confirmed: title "Mining specifications"; authors Glenn Ammons, Rastislav Bodík,
James R. Larus; container *Proceedings of the 29th ACM SIGPLAN-SIGACT Symposium
on Principles of Programming Languages*; year 2002; publisher ACM, New York;
pages 4–16; event POPL '02, Portland, Oregon.

**Source B** — https://dblp.org/rec/conf/popl/AmmonsBL02.html
Confirmed independently: title "Mining specifications."; same three authors;
POPL 2002; pages 4–16; DOI 10.1145/503272.503275.

Verdict: **CONFIRMED**.

```bibtex
@inproceedings{ammons2002mining,
  author    = {Glenn Ammons and Rastislav Bod{\'i}k and James R. Larus},
  title     = {Mining Specifications},
  booktitle = {Proceedings of the 29th {ACM} {SIGPLAN}-{SIGACT} Symposium on
               Principles of Programming Languages ({POPL} '02)},
  pages     = {4--16},
  year      = {2002},
  address   = {Portland, Oregon, USA},
  publisher = {ACM},
  doi       = {10.1145/503272.503275}
}
```

---

## DROPPED

### D1. "Testing shows the presence, not the absence of bugs" as NATO 1969 Rome report, p. 16 — **DROPPED**

The claim under test: that the compressed form of the quotation originates in
J.N. Buxton and B. Randell (eds.), *Software Engineering Techniques: Report on a
Conference Sponsored by the NATO Science Committee, Rome, Italy, 27–31 October
1969*, Scientific Affairs Division, NATO, Brussels, April 1970, **page 16**.

Queries run:

* `Dijkstra "testing shows the presence, not the absence of bugs" original source EWD Notes on Structured Programming 1969 NATO`
* `Buxton Randell "Software Engineering Techniques" NATO 1969 Rome report Dijkstra "testing shows the presence" page 16`
* `"nato1969" report page 16 Dijkstra quote ... transcript`
* `"Software Engineering Techniques" 1969 Rome report "Dijkstra" "presence" "absence of bugs" quoted page number scholarly citation`
* `"nato1969" PDF mirror ... alternative host`

Primary-document access attempts, all failed from this environment:

| URL | Result |
|---|---|
| https://homepages.cs.ncl.ac.uk/brian.randell/NATO/nato1969.PDF | TLS certificate expired |
| https://web.archive.org/web/2020/http://homepages.cs.ncl.ac.uk/brian.randell/NATO/nato1969.PDF | fetching from web.archive.org unavailable |
| https://archive.org/stream/softwareengineer00naur/softwareengineer00naur_djvu.txt | ECONNREFUSED |
| https://dl.acm.org/doi/book/10.5555/1102021 | HTTP 403 |
| https://onlinebooks.library.upenn.edu/webbin/book/lookupid?key=olbp48957 | ECONNREFUSED |
| https://en.wikiquote.org/wiki/Edsger_W._Dijkstra | ECONNRESET (two attempts) |
| https://www.semanticscholar.org/paper/c51ed897a5515b7e75a5ba57ce81cf3bd76950d6 | empty body returned |

What *was* obtained: the report's own existence, editors, sponsor, location and
date are well corroborated (ACM DL guide-book record 10.5555/1102021; the Online
Books Page listing; the Wikipedia article on the NATO Software Engineering
Conferences, which additionally states that a shorter version of Dijkstra's
*Notes on Structured Programming* was included in the Rome proceedings). But the
"page 16" locus for this particular sentence traces only to quotation-aggregator
sites and blog posts, which are not independent of one another.

Counter-evidence worth recording: Hillel Wayne's investigation of this exact
quotation —
https://buttondown.com/hillelwayne/archive/testing-can-show-the-presence-of-bugs-but-not-the/
— attributes it solely to EWD249 and gives Dijkstra's longer wording, with no
NATO citation at all.

**Verdict: DROPPED.** Two independent confirmations of the page-16 locus could
not be obtained, and the primary document could not be read. Per the brief's
rule, it is not cited. The paper should cite EWD249 (entry 9) and quote
Dijkstra's actual sentence. If a future session can open the Rome report, this
entry can be revisited; until then, asserting the NATO locus would be exactly
the fabrication this trace exists to prevent.

---

## Summary

**10 CONFIRMED** (entries 1–10), **1 DROPPED** (D1).

Every confirmed record has two independent authorities agreeing on authors,
year and venue; page ranges agree as well, with the single Appel discrepancy
resolved in favour of the two authorities against a search snippet.

The dropped item is a *locus* claim, not a paper. The bibliographic record it
would have supported — Dijkstra's quotation — survives via entry 9, where the
sentence was verified by reading the primary text rather than by trusting an
attribution.
