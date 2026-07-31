# Line 5 — proof-carrying code, certifying algorithms, and specification validity

*证明携带代码(名字的谱系). Arms `papers/phase1-workshop/sections/08_related.md` §8.2 —
both the **proof-carrying code** bullet and the **specification validity** bullet.*

Verified entries: **9**. Quarantined: **3**. BibTeX: `05_proof_carrying.bib`.
Search trail: `../runs/20260728T034703Z-p23/05_proof_carrying/search-log.md`.

---

## The ancestry of the name

§8.2 calls proof-carrying code "the ancestry of the name", so the first job on this
line is to establish *which publication the name descends from* — and the answer is
two publications, not one, which is the standard trap here.

The **term** is coined in Necula & Lee's OSDI '96 paper, whose abstract introduces it
in so many words: an application supplies binaries "in a special form called
proof-carrying code, or simply PCC". That paper's title never mentions it; it is a
systems paper about kernel extensions, and the name arrives inside it as machinery.

The **canonical citation** is Necula's POPL '97 paper, sole-authored, titled simply
*Proof-Carrying Code*. It is the paper that carries the name as its subject rather
than as a device, it is the one the literature cites by a wide margin (CrossRef
records ~1037 citing works against ~252 for the OSDI paper), and the author's own
publication page records it as recipient of the 2007 Award for the Most Influential
POPL 1997 Paper. **House rule for this repository: cite `necula1997pcc` for the idea
and the name; cite `necula1996kernel` alongside it only when the claim is specifically
about priority of the term or about the kernel-extension application.** Writing
"Necula & Lee, POPL 1997" or "Necula, OSDI 1996" — both of which appear in the wild —
crosses the two records and is the specific error this section exists to prevent.

Below the name sits a wider family that §8.2 is really appealing to: the discipline in
which **an artefact travels with the evidence for its own correctness and the consumer
re-checks rather than trusts**. Appel's foundational PCC asks who verifies the verifier
and shrinks the trusted base; McConnell et al. give the idea its general algorithmic
form, independent of safety policies and machine code; DRAT-trim and CompCert are the
two shapes it takes in practice — a certificate emitted per run and re-checked, versus
a compiler verified once and for all.

The last three entries are the other half of §8.2's demand. That section de-escalates
its own §5.6 exhibit to "the oldest caveat in formal methods" — a machine-checked proof
is only as good as the specification it is about — and needs a citation for a claim it
is deliberately *not* claiming as novel. Boehm supplies the verification/validation
distinction itself; De Millo, Lipton & Perlis and Fetzer supply "the arguments around
it" that §8.2 gestures at. These three are the entries most exposed to miscitation, so
each one's summary sentence below is restricted to what its own published abstract
says, and where I could not confirm a widely-repeated attribution I have said so rather
than repeating it.

**Our delta across the whole line.** Our certificates cross a data boundary as files
(`engine-rig/interop/certificates/`, e.g. `pagoda_5_11011_to_00010.json`) and the
consumer re-discharges them in Lean rather than trusting the producing engine — which
is the classical PCC boundary discipline, unchanged. What is not classical is the
provenance of the specification: in every work below, the property being proved was
*written by a human*, so a wrong specification is a human modelling error and the
repair is a human rewrite. In ours the specification was **induced from a transition
ledger by a mining engine**, so a specification error is a *mining* error — mechanically
attributable to the engine and the evidence that produced it, and therefore routable
into an automatic repair loop instead of back to an author.

---

## Proof-carrying code proper

### `necula1996kernel` — Necula & Lee, OSDI 1996

**What it did.** It gave an OS kernel a way to decide with certainty that an untrusted
binary is safe to run: the kernel publishes a safety policy, and the application
supplies its binary "in a special form called proof-carrying code, or simply PCC" that
carries a formal proof of adherence to that policy, which the kernel validates without
cryptography and without consulting any external trusted entity.

**Our delta.** This is where the name is born and where the trust boundary is drawn the
way §4 draws it, one-way and re-checked; our boundary carries a Lean certificate about
an *induced* world model rather than a machine-code safety policy fixed in advance by
the consumer.

`verified:` **CrossRef** (DOI `10.1145/238721.238781`; container *Proceedings of the
Second USENIX Symposium on Operating Systems Design and Implementation*; pp. 229–243;
1996) and **Semantic Scholar Graph API** (DBLP key `conf/osdi/NeculaL96`; venue "USENIX
Symposium on Operating Systems Design and Implementation"; 1996). Both agree on title,
year and venue. Abstract text confirmed via the USENIX OSDI '96 program listing.

> **Duplicate-record note.** CrossRef also carries `10.1145/248155.238781` for the same
> paper as a journal article in *ACM SIGOPS Operating Systems Review* 30(SI):229–243 —
> the proceedings reprint. The `.bib` entry uses the OSDI proceedings record and notes
> the reprint; do not cite both as if they were two papers.

### `necula1997pcc` — Necula, POPL 1997

**What it did.** It set out proof-carrying code as a general mechanism by which a host
system can determine with certainty that it is safe to execute a program supplied,
possibly in binary form, by an untrusted source: the code producer ships a safety proof
attesting to the code's adherence to a previously defined safety policy, and the host
validates that proof quickly, without cryptography and without consulting external
agents.

**Our delta.** The consumer-re-checks-the-evidence discipline is taken over wholesale;
what changes is that the "previously defined safety policy" is, for us, not previously
defined — it is mined from data, so the proof can succeed against a specification that
is itself false of the world, which is the failure mode §5.6 exhibits and the reason our
loop does not terminate at the certificate.

`verified:` **CrossRef** (DOI `10.1145/263699.263712`; container *Proceedings of the
24th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages — POPL '97*;
pp. 106–119; 1997) and **Semantic Scholar Graph API** (DBLP key `conf/popl/Necula97`;
venue "ACM-SIGACT Symposium on Principles of Programming Languages"; 1997). Venue and
year corroborated a third time by the author's own publication page at UC Berkeley
("Presented at the ACM Symposium on Principles of Programming Languages (POPL'97),
January 1997"). The abstract wording quoted above was confirmed by exact-phrase search
against the ACM DL record for this DOI; the ACM DL page itself returns HTTP 403 to
automated fetches.

### `appel2001foundational` — Appel, LICS 2001

**What it did.** It posed *quis custodiat ipsos custodes* for PCC — who verifies the
verifier — and defined foundational proof-carrying code as verification from the
smallest possible set of axioms, using the simplest possible verifier and the smallest
possible runtime system.

**Our delta.** Same instinct about shrinking what must be trusted, applied one layer
out: our trusted base is the Lean kernel plus the replay harness, and the object we are
anxious about is not the verifier but the *specification* the verifier is handed.

`verified:` **CrossRef** (DOI `10.1109/LICS.2001.932501`; container *Proceedings 16th
Annual IEEE Symposium on Logic in Computer Science*; pp. 247–256) and **Semantic
Scholar Graph API** (DBLP key `conf/lics/Appel01`; year 2001). Year and venue
corroborated by the author's own PDF at Princeton, whose header reads "To appear in
LICS '01, 16th Annual IEEE Symposium on Logic in Computer Science"; the abstract quoted
above is taken verbatim from that PDF.

---

## The same idea in algorithmic form

### `mcconnell2011certifying` — McConnell, Mehlhorn, Näher & Schweitzer, 2011

**What it did.** It surveyed and theorised *certifying algorithms* — algorithms that
produce, with each output, "a certificate or witness (easy-to-verify proof) that the
particular output has not been compromised by a bug", which the user checks to be sure
of the output "without having to trust the algorithm" — arguing that for complex
algorithmic tasks only certifying algorithms are satisfactory, and proving the concept
universal.

**Our delta.** This is the cleanest statement of the discipline our engines are held to
— engines propose, and each proposal ships a witness the adjudicator re-checks — but a
certifying algorithm's specification is a fixed mathematical relation between input and
output, whereas ours is a mined world model, so our checker can certify faithfully and
still be wrong about the world.

`verified:` **CrossRef** (DOI `10.1016/j.cosrev.2010.09.009`; *Computer Science Review*
5(2):119–161; 2011) and **Semantic Scholar Graph API** (DBLP key
`journals/csr/McConnellMNS11`; venue "Computer Science Review"; 2011). The abstract
quoted above is verbatim from the authors' own preprint hosted at MPI for Informatics
("Preprint submitted to Elsevier, August 30, 2010").

> **Year note.** OpenAlex records this work as 2010, reflecting the online-first date on
> the preprint; CrossRef, Semantic Scholar and the DBLP key all give 2011, which is the
> journal issue year and what the `.bib` uses.

---

## Machine-checkable certificates in practice

### `wetzler2014drat` — Wetzler, Heule & Hunt, SAT 2014

**What it did.** It presented DRAT-trim, a satisfiability proof checker for the DRAT
clausal proof format which — unlike its predecessor DRUP-trim — can validate all
presently known SAT solving and preprocessing techniques, at a checking time comparable
to the running time of the proof-producing solver and with comparable memory use.

**Our delta.** This is the industrial form of our arrangement — a solver's answer is
worthless until an independent checker re-derives it from an emitted certificate — and
`engine-rig`'s certificate files are the same move at the boundary of §4; the
difference is that an UNSAT certificate is checked against a formula that was *given*,
while ours is checked against a `step` function the system itself induced.

`verified:` **Springer Nature Link**, the publisher of record (chapter DOI
`10.1007/978-3-319-09284-3_31`; *Theory and Applications of Satisfiability Testing —
SAT 2014*; LNCS volume 8561; pp. 422–429; 2014; abstract as quoted) and **CrossRef**
(same DOI, same page range, 2014). Corroborated a third time by **Semantic Scholar**
(DBLP key `conf/sat/WetzlerHH14`).

### `leroy2009compcert` — Leroy, CACM 2009

**What it did.** It reported the development and formal verification — proof of
semantic preservation — of CompCert, a compiler from Clight (a large subset of C) to
PowerPC assembly, using the Coq proof assistant both to program the compiler and to
prove it correct, so that safety properties proved of the source hold of the compiled
executable too.

**Our delta.** CompCert is the opposite pole from DRAT and from us: trust is
established once, in advance, for the whole translator, rather than per artefact at
consumption time; we cite it to mark that our certificates are deliberately of the
per-run, re-checked kind, because a world model induced from data has no fixed
specification to verify once and for all.

`verified:` **CrossRef** (DOI `10.1145/1538788.1538814`; *Communications of the ACM*
52(7):107–115; 2009; abstract as summarised above) and **Semantic Scholar Graph API**
(DBLP key `journals/cacm/Leroy09`; venue CACM; 2009).

---

## Specification validity — validation versus verification

### `boehm1984validating` — Boehm, IEEE Software 1984

**What it did.** It set out techniques and guidelines for verifying and validating
software requirements and design specifications — that is, for checking the
specification itself, at the requirements and design stage, before there is code for a
verifier to be correct about.

**Our delta.** This is the distinction §8.2 leans on when it concedes that a
machine-checked proof is only as good as its specification; our contribution is not the
distinction but a case in which the specification under validation was *induced by an
engine*, which makes its invalidity mechanically diagnosable and repairable rather than
a matter for human review.

`verified:` **CrossRef** (DOI `10.1109/MS.1984.233702`; *IEEE Software* 1(1):75–88;
1984) and **DBLP** (record `journals/software/Boehm84`; *IEEE Software* 1(1):75–88;
1984). Corroborated a third time by **OpenAlex** (same DOI, 1984, vol. 1, issue 1, pp.
75–88).

> **Metadata-disagreement note, disclosed under red line 2.** The **Semantic Scholar**
> record for this DOI reports the year as **1989**. This is an isolated error in that
> one aggregator: CrossRef, DBLP and OpenAlex agree on 1984, the DOI string itself
> encodes 1984, and *IEEE Software* volume 1 issue 1 is its first issue, published 1984.
> The entry is admitted on CrossRef + DBLP, with the S2 anomaly recorded here so that
> the `AUDIT.md` re-verification pass does not rediscover it as a fresh discrepancy.

> **Attribution caution — do not repeat the epigram from this citation.** Boehm is
> universally credited with the formulation *verification = "am I building the product
> right?", validation = "am I building the right product?"*, and this paper is the usual
> citation attached to it. **I could not verify that the epigram appears in this paper**:
> IEEE Xplore, the ACM DL mirror and ResearchGate all refused automated access, and no
> source I reached quotes it with a page number from the 1984 article. A competing locus
> exists — Boehm's 1979 Euro IFIP paper, quarantined below. Cite `boehm1984validating`
> for the verification/validation *distinction*; do **not** put the epigram in quotation
> marks against it without reading the article.

### `demillo1979social` — De Millo, Lipton & Perlis, CACM 1979

**What it did.** It argued that formal verifications of programs, however obtained,
will not play the role in computer science that proofs play in mathematics, and that
the absence of continuity, the inevitability of change, and *the complexity of
specification of significantly many real programs* make the formal verification process
hard to justify and manage.

**Our delta.** Their objection to specification complexity is the one we inherit most
directly, and we do not answer it by writing better specifications: our specifications
are mined, the objection reappears as mining error, and the loop is designed to absorb
that rather than deny it.

`verified:` **CrossRef** (DOI `10.1145/359104.359106`; *Communications of the ACM*
22(5):271–280; May 1979; abstract as summarised) and **Semantic Scholar Graph API**
(DBLP key `journals/cacm/DeMilloLP79`; venue CACM; 1979).

### `fetzer1988verification` — Fetzer, CACM 1988

**What it did.** It argued that program verification trades on an equivocation:
algorithms, as logical structures, are appropriate subjects for deductive verification,
whereas programs, as causal models of those structures, are not — so program
verification as a generally applicable and completely reliable guarantee of program
performance is "not even a theoretical possibility".

**Our delta.** Fetzer's gap is between the proved object and the physical machine; ours
is one step earlier and of the same shape — between the proved object and the *world
the object claims to be about* — and our answer is not a proof but an empirical one,
active experiment against the environment.

`verified:` **CrossRef** (DOI `10.1145/48529.48530`; *Communications of the ACM*
31(9):1048–1063; September 1988; abstract quoted above is verbatim from the CrossRef
record) and **Semantic Scholar Graph API** (title, venue CACM, year 1988 for the same
DOI).

> **Two cautions on this entry.** (i) The Semantic Scholar record for this DOI carries
> the DBLP key `books/sp/93/Fetzer93`, which belongs to the 1993 Springer book chapter
> of the same title, not to the CACM article — an S2 record-merge artefact. Title, venue
> and year in that record still agree with CrossRef, which is what red line 2 requires;
> the stray key is noted so it is not copied into the `.bib`. (ii) There are at least
> three separate works titled "Program Verification: The Very Idea" by Fetzer — the CACM
> article (1988) and book chapters in Springer's *Studies in Cognitive Systems* (1993,
> DOI `10.1007/978-94-011-1793-7_15`, and 2001, DOI `10.1007/978-94-010-0973-7_8`). The
> CACM article is the one to cite; the others are reprints and must not be merged with
> it or with each other.

---

## Quarantined

Not admitted to `05_proof_carrying.bib`. Recorded here so a later pass can finish the
job rather than repeat the search.

### Q1. Boehm, "Guidelines for verifying and validating software requirements and design specifications" (Euro IFIP 79, c. 1979)

**Why quarantined:** zero sources, not one. This is the other candidate locus for the
verification/validation epigram, and it is the reason the caution on
`boehm1984validating` is worded as it is. A CrossRef query returned no record matching
this title — the proceedings appear not to be indexed with a DOI — and no second source
was reached. Nothing about it is asserted here beyond that it is claimed to exist;
neither its exact title, its year, nor its page range has been confirmed, so no BibTeX
entry is written for it.

### Q2. The published rebuttals to Fetzer (CACM technical correspondence, 1989)

**Why quarantined:** single source, and that source is internally ambiguous. The brief
flags correctly that Fetzer's article and the rebuttals are separate items. They exist:
CrossRef carries DOI `10.1145/63334.315936` under the generic title "Technical
correspondence", *Communications of the ACM* 32(4):506–512, April 1989, with a corporate
author ("Tech Correspondence") and no individual contributors listed. But a secondary
account of the controversy places the eight pages of technical correspondence plus three
pages of ACM Forum discussion in the **March** 1989 issue, which does not match CrossRef's
32(4)/April. Citing a multi-author correspondence section by a generic title, with the
issue in doubt and the individual letter-writers unnamed, is exactly the kind of entry
red line 1 exists to keep out of the library. **Consequence for §8.2:** its
specification-validity sentence should cite Boehm, De Millo et al. and Fetzer for the
positions, and must not attribute rebuttal content to Fetzer's own article.

### Q3. Alkassar, Böhme, Mehlhorn, Rizkallah & Schweitzer, "An Introduction to Certifying Algorithms", *it — Information Technology* 53(6):287–293, 2011

**Why quarantined:** single source (CrossRef, DOI `10.1524/itit.2011.0655`, with
abstract). It is a genuine and relevant work — it is the one that extends the thesis to
*formally verified result checkers*, which is nearer to our Lean re-discharge than the
survey is — but I did not cross-verify it against a second source, because
`mcconnell2011certifying` already carries the line's claim and coverage was at target. A
later pass wanting the verified-checker angle should verify and admit this one first.

---

## Red line 3 — sealed pile

No back-off was required. Every query on this line was bibliographic and every source
reached was a publisher, an aggregator, an author's institutional page or a general web
search for bibliographic metadata. No ARC game page, walkthrough, leaderboard write-up,
`schema-harness.github.io` page or ARC-AGI-3 trajectory dataset was opened, returned or
read, and no search result began describing the mechanics of any specific game.
