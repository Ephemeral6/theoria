# Line 5 — proof-carrying code, certifying algorithms, specification validity

Ten confirmed records for the `[bib: TODO]` markers in
`sections/11_related.md` §8.2, covering the two paragraphs headed **"Proof-carrying
code"** and **"Specification validity"**. Verification trace, including the one
dropped item and the reasons:
`runs/20260728T102014Z-P7/search-traces/line5-pcc-spec-validity.md`.

Every record below was cross-checked against two independent authorities. Nothing
here was written from memory.

---

## Proof-carrying code

### `necula1997pcc`

George C. Necula. Proof-Carrying Code. In *Proceedings of the 24th ACM
SIGPLAN-SIGACT Symposium on Principles of Programming Languages (POPL '97)*,
Paris, France, pages 106–119. ACM Press, 1997. DOI 10.1145/263699.263712.

*What it did.* Established the arrangement in which an untrusted binary is
shipped together with a formal proof that it satisfies a safety policy, so that
the consumer discharges a proof check instead of extending trust to the producer.

*Our delta.* This is the ancestry of the name and of the §4 boundary discipline —
one track's engine emits a certificate, the other track's checker re-checks it —
but PCC certifies a program against a safety policy a human wrote down, whereas
here the property being certified concerns a world model whose rules were induced
from a transition ledger, so the certificate's own premises are fallible.

### `necula1996safekernel`

George C. Necula and Peter Lee. Safe Kernel Extensions Without Run-Time Checking.
In *Proceedings of the Second USENIX Symposium on Operating Systems Design and
Implementation (OSDI '96)*, Seattle, Washington, pages 229–243, 1996.
DOI 10.1145/238721.238781.

*What it did.* Introduced proof-carrying code in its original systems setting,
letting a kernel admit a foreign extension on the strength of an accompanying
proof rather than on run-time checks or on the extension's provenance.

*Our delta.* The motivation transfers exactly — the consumer must be able to
decide unaided, without re-running the producer's work — but the artefact crossing
our boundary is an unsolvability certificate over a mined rule set
(`engine-rig/interop/certificates/pagoda_5_11011_to_00010.json`) rather than a
memory-safety proof over machine code, and a passing check therefore establishes
consistency with the mined rules, not correctness against the world.

### `appel2001fpcc`

Andrew W. Appel. Foundational Proof-Carrying Code. In *Proceedings of the 16th
Annual IEEE Symposium on Logic in Computer Science (LICS 2001)*, Boston,
Massachusetts, pages 247–256. IEEE Computer Society, 2001.
DOI 10.1109/LICS.2001.932501.

*What it did.* Reduced the trusted base of proof-carrying code to a foundational
logic plus a machine semantics, on the argument that a certificate is only worth
as much as the axioms the checker is willing to assume.

*Our delta.* The same accounting question is what §5.6 answers badly: our
checker's trusted base is small and the Lean proof is real, yet the axioms it
rests on are the manual's induced rules, so shrinking the checker does not shrink
the exposure — the exposure lives in the premises, not in the proof engine.

---

## Certifying algorithms and result checking

### `mcconnell2011certifying`

Ross M. McConnell, Kurt Mehlhorn, Stefan Näher and Pascal Schweitzer. Certifying
algorithms. *Computer Science Review*, 5(2):119–161, 2011.
DOI 10.1016/j.cosrev.2010.09.009.

*What it did.* Surveyed and systematised the design of algorithms that return,
alongside each output, a witness whose validity an independent and simpler checker
can confirm, so that a single run is verified without verifying the implementation.

*Our delta.* Our engines are certifying in exactly this sense and the checker is
correspondingly simple, but a certifying algorithm's witness is checked against an
input that is given, whereas ours is checked against a rule set that was mined —
which moves the residual risk out of the algorithm and into the induction step
that produced its input.

### `blum1995checkers`

Manuel Blum and Sampath Kannan. Designing Programs that Check Their Work.
*Journal of the ACM*, 42(1):269–291, 1995. DOI 10.1145/200836.200880.

*What it did.* Formalised program checking as an input-by-input discipline —
confirm that this output is right for this input — and characterised which
problems admit checkers, deliberately setting aside verification of the program
as a whole.

*Our delta.* The instance-level framing is the one we adopt, and for the same
reason: we make no claim to have verified any engine. What we add is that the
instance being checked is itself a hypothesis about the world, so a check that
passes leaves the interesting failure mode — the rule that was never mined —
entirely untouched, which is the gap §5.6 walks into.

---

## Specification validity — the oldest caveat, and one we do not claim

### `dijkstra1970notes`

Edsger W. Dijkstra. *Notes on Structured Programming*. EWD249; T.H.-Report
70-WSK-03, Technological University Eindhoven, April 1970 (second edition; first
version August 1969; circulated privately). E.W. Dijkstra Archive, University of
Texas at Austin. DOI 10.26153/tsw/53177.

*What it did.* Stated, in the section "On the reliability of mechanisms", the
observation that has organised the field's expectations of testing ever since:
"Program testing can be used to show the presence of bugs, but never to show
their absence!"

*Our delta.* We take the sentence at face value and it is precisely why the
manual is proved rather than merely replayed; §5.6 then supplies the symmetric
half that the sentence does not cover — a proof shows the absence of bugs
relative to a specification, and when the specification is mined rather than
written, the proof can be sound and the artefact still false of the world.

**Citation note — this is frequently mis-attributed and the paper should not
repeat the error.** The sentence above is Dijkstra's own wording and it is in
EWD249. The widely circulated compression "Testing shows the presence, not the
absence of bugs" is *not* what EWD249 says; it is usually credited to the 1969
NATO Rome conference report (Buxton and Randell, eds., *Software Engineering
Techniques*, 1970, p. 16), an attribution we could not verify against the primary
document and have therefore dropped. Two further common errors: citing the 1972
Academic Press volume (Dahl, Dijkstra and Hoare, *Structured Programming*), which
reprints EWD249 rather than originating it; and citing a bare "Dijkstra 1969",
which is ambiguous between the first version and the April 1970 second edition
that is the archived document. Quote the sentence verbatim and cite EWD249.

### `demillo1979social`

Richard A. De Millo, Richard J. Lipton and Alan J. Perlis. Social Processes and
Proofs of Theorems and Programs. *Communications of the ACM*, 22(5):271–280, 1979.
DOI 10.1145/359104.359106.

*What it did.* Argued that mathematical proofs earn belief through a social
process of reading and reuse that program verifications do not undergo, and that
a formal verification therefore does not deliver the confidence its form suggests.

*Our delta.* We do not adopt the paper's conclusion — our proofs are machine-checked,
which answers its scepticism about unread formal arguments — but we inherit its
target: §5.6 is a case where the machine check succeeded and belief was still
misplaced, with the failure located in the statement being proved rather than in
the community's attention to the proof.

### `fetzer1988veryidea`

James H. Fetzer. Program Verification: The Very Idea. *Communications of the ACM*,
31(9):1048–1063, 1988. DOI 10.1145/48529.48530.

*What it did.* Pressed the distinction between proving properties of an abstract
program and establishing anything about the physical system it is supposed to
govern, arguing that verification cannot bridge that gap on its own.

*Our delta.* The gap Fetzer names is the one our exhibit falls into, one level up:
our proof is about the manual's own `step`, and the question of whether that
`step` is the game is not a question Lean is being asked — which is why the paper
treats the theorem's refutation by the world as evidence about the mining, not
about the prover.

### `boehm1984vandv`

Barry W. Boehm. Verifying and Validating Software Requirements and Design
Specifications. *IEEE Software*, 1(1):75–88, 1984. DOI 10.1109/MS.1984.233702.

*What it did.* Set out the verification/validation distinction as a practical
discipline for requirements and design — verification asking whether the artefact
is being built correctly against its specification, validation whether that
specification is the right one — and gave methods for the second.

*Our delta.* Our loop has verification and lacks validation in Boehm's sense, and
the substitute is not human review: the world supplies the validation signal by
refuting a theorem, and the refutation is routed into a mechanical repair of the
mined rules (`cold-start-a2/artifacts/loop_ledger.json`) rather than into a
rewrite of the specification by hand.

### `ammons2002mining`

Glenn Ammons, Rastislav Bodík and James R. Larus. Mining Specifications. In
*Proceedings of the 29th ACM SIGPLAN-SIGACT Symposium on Principles of Programming
Languages (POPL '02)*, Portland, Oregon, pages 4–16. ACM, 2002.
DOI 10.1145/503272.503275.

*What it did.* Obtained temporal specifications by generalising from observed
program traces rather than from a hand-written requirement, and named the
consequence directly — a mined specification is a hypothesis and can be wrong.

*Our delta.* This is the closest prior statement of our situation and the reason
§5.6's error is best called a *mining* error rather than a proof error; what
differs is the downstream use, since a mined specification here is not a lint
oracle but the premise set of a Lean theorem, so a bad mine is laundered into a
formally proved false statement rather than into a false alarm.

---

## Note for the §8.2 prose

The existing placeholder already says the right thing and should keep saying it:
§5.6 does not claim specification validity as a novel observation. The four
records above (`dijkstra1970notes`, `demillo1979social`, `fetzer1988veryidea`,
`boehm1984vandv`) are the anchors that make the disclaimer concrete, spanning
1970 to 1988 — the point is older than the method. `ammons2002mining` is the one
that carries the actual contribution, because it is where a specification stops
being hand-written; the delta is then only that the mined specification here is
consumed by a prover and repaired by a loop.

Suggested marker mapping for §8.2:

| placeholder | fill with |
|---|---|
| "Proof-carrying code [bib: TODO] is the ancestry of the name" | `necula1997pcc`, `necula1996safekernel`, `appel2001fpcc` |
| §4 boundary re-check, if a certifying-algorithms cite is wanted | `mcconnell2011certifying`, `blum1995checkers` |
| "the validation-versus-verification distinction ... long predate this work [bib: TODO]" | `boehm1984vandv`, `dijkstra1970notes`, `demillo1979social`, `fetzer1988veryidea` |
| "the specification error is a mining error" | `ammons2002mining` |
