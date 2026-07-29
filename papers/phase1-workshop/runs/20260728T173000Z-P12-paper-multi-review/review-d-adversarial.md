# Review (d) — the hostile referee: where this paper gets demolished in one sentence

**Reviewed state.** `papers/phase1-workshop/PAPER.md` v0.3, 2 572 lines, assembled from
`sections/*.md`. Every attack below quotes text I opened; every line number is
PAPER.md's, with the owning `sections/NN_*.md` file and its own line number beside it,
because that is where a fix has to land. Prior rounds consulted: `REVIEW.md`,
`REVIEW_TRIAGE.md`, `OPEN_ITEMS.md`. Where a defect was already logged I say so —
a knowingly-kept defect is a different finding from a missed one, and the difference
changes what a rebuttal can say.

**Remit.** Attackability only. Novelty, evidence sufficiency, reproducibility and lay
readability are other referees'. I looked for the sentences an unfriendly expert can
kill in one line from the floor.

---

## Recommendation

**Reject, and it is a closer call than the last round.** The work is real and the
self-audit discipline is the best I have seen in a draft at this stage — several
attacks I had loaded were already disarmed by the paper's own text, and I list them at
the end. But the paper has acquired, in v0.2/v0.3, a new and worse class of defect than
the one the previous referee found. `REVIEW.md` found *false statements about
artefacts*, and those have largely been fixed. What is here now is **false statements
about the paper itself**: §10.5, the section whose job is to state the minimum the paper
claims, claims *more* than the body allows, and the title and abstract claim two results
(transfer, the exam) that §10.5 explicitly declines to claim. A referee who reads only
the title, the abstract and §10.5 — which is what a program committee does — will find
the contradiction before reading a single result. That is fatal in a way that a
miscited JSON field is not, because it cannot be answered by "we fixed the citation".

Three of the five kill shots below are *internal contradictions introduced by the
sections added after both prior audits ran* (§6, §8, §9), and `OPEN_ITEMS.md` A4 already
predicts them in the abstract: "A third audit pass is owed: both existing audits predate
§6, §8, §9 and the renumbering." This is that pass finding what A4 said would be there.

All five are **writing fixes**. None needs an experiment. That is the good news and it
should be said plainly: this is a two-hour repair, not a re-run.

---

## The five sentences that sink this paper

Ranked by how badly each lands, and each written as the hostile expert would say it out
loud.

---

### 1. "Your subtitle sells me a transfer result and an examination instrument, and your §10.5 tells me transfer and the exam are unevidenced and not claimed — which of your own sentences would you like me to believe?"

**Target A** — PAPER.md L5–7 (`sections/00_abstract.md` L3–5), the subtitle:

> Phase 1 of Theoria: three offline acceptances and **a transfer result**, a passive
> metrics battery, **an examination instrument**, and a live run that spent nothing

**Target B** — PAPER.md L2324–2325 (`sections/10_limitations.md` L252–253), the closing
sentence of "§10.5 The one thing this paper claims":

> Everything else in `Theoria.md` — the ordering claim, the bill shape, **transfer**,
> **the exam**, the cost magnitude — is unevidenced here and is not claimed.

And in between, abstract result **(6)** (PAPER.md L100–106, `sections/00_abstract.md`
L67–73) reports the transfer arm winning "252/252 against the referee", abstract result
**(7)** (PAPER.md L106–111) reports the exam instrument, §6 is 197 lines of transfer and
§8 is 190 lines of exam, and §6.2 is *titled* "The bill" while §10.5 disclaims "the bill
shape".

**Is there a defence in the text?** A partial one, and it is not where it needs to be.
§2.5 (PAPER.md L388–389, `sections/02_framework.md` L121–123) says §6 is "an early read
on claim C3 that the mandate does not list as an acceptance at all", and §6 opens
(PAPER.md L1095–1098) with "A3 answers it for two levels of one game, which is the
weakest interesting reading of C3". So the *intended* distinction is between
`Theoria.md`'s claim C3 and this paper's weaker reading of it. Nothing in §10.5 makes
that distinction, and a hostile reader will not construct it for you. There is no
defence at all for "the exam", which §10.5 disclaims flatly while §8 exists.

**Status:** **missed.** Not in `REVIEW.md`, not in `OPEN_ITEMS.md`, not in
`REVIEW_TRIAGE.md` — all three predate §6 and §8, which is exactly the gap `OPEN_ITEMS`
A4 flags. This is new damage from the v0.2 expansion.

**Minimal edit that disarms it.** Rewrite the §10.5 disclaimer to name what is being
disclaimed rather than the topic: *"`Theoria.md`'s own claims — the ordering claim, C5's
cost magnitude, C3 at any strength beyond two levels of one game, and every Phase 4 exam
item — are unevidenced here and not claimed; §6 reports the weakest reading of C3 and §8
reports an instrument, not a result about subjects."* One sentence, and the subtitle
survives.

---

### 2. "Your own §11.3 instructs the abstract not to read as if the exhibit were evidence — and your abstract opens by calling it one of 'Eight results.'"

**Target A** — PAPER.md L2567–2572 (`sections/11_related.md` L239–244), the final
paragraph of the paper's body:

> **"Prediction perfect, understanding broken" is this framework's own premise, not a
> finding.** §5's procedure is to take a certified manual, delete a rule that never
> fires in the retained history, and observe that replay over that history does not
> notice — which is analytically guaranteed by the construction. The exhibit has value
> as a teaching object and as a test of the instrument. **It is not evidence about
> anything, and the abstract should not read as though it were.**

**Target B** — PAPER.md L63 (`sections/00_abstract.md` L61):

> instrument, and one live run that spent nothing. **Eight results.**

...followed by result **(4)**, PAPER.md L81–88, which is that exhibit.

The paper does not merely fail to take its own instruction; it moved in the wrong
direction. `REVIEW.md` issue 14 and `OPEN_ITEMS.md` §D both say the abstract "still
reads as 'four results' where the honest scope is an instrument-and-artefact
contribution". Between then and now the count went to **eight**.

**Is there a defence in the text?** Yes, and it is genuinely good — the abstract's own
closing paragraph (PAPER.md L124–126) says "The contribution is an instrument and a
demonstration artefact … not a result about world models." But it says that *109 lines
after* the words "Eight results", and a referee reading top-down has already written
down the count. A defence that arrives after the claim is a defence that arrives after
the reviewer's note.

**Status:** **logged and knowingly open.** `OPEN_ITEMS.md` §D, final paragraph: "What is
**not** closed is the consequence: the abstract still reads as 'four results' where the
honest scope is an instrument-and-artefact contribution". The authors know. They have
now made it worse by four.

**Minimal edit.** Delete "Eight results." and replace with "Eight artefacts; one
contribution." Or move the abstract's own closing paragraph to sit immediately after the
list. Either kills the attack in one line.

---

### 3. "Your section called 'the one thing this paper claims' claims three things your own body spends pages retracting."

**Target** — PAPER.md L2310–2317 (`sections/10_limitations.md` L238–245), §10.5:

> that on those worlds a manual can be perfect on replay and wrong about the world in a
> way that was **predicted in advance and later measured**; that reversibility of a
> mechanism mattered more than breadth of trajectory in the **one controlled comparison
> run**; that a machine-checked impossibility can be produced whose weights crossed a
> data boundary between **two independently developed tracks**

Three phrases, three retractions elsewhere in the same paper:

| §10.5 says | the body says | where |
|---|---|---|
| "the one **controlled** comparison run" | "'Identical except' would be a false description and is not used here" — 7 vs 21 rules, 59 vs 57 states, 236 vs 228 pairs, Button vs Switch — and "**The outcome follows from the construction; nothing was learned that was not built in.**" | PAPER.md L494–495, L539–546 (`sections/03_a0.md` L100–101, L145–152) |
| "two **independently developed** tracks" | "They are two agent sessions working one repository under one operator … **A reader should not picture two teams.** What crosses the boundary is therefore a *defence-in-depth* result, not an independent replication" | PAPER.md L718–724 (`sections/04_a1.md` L45–51) |
| "**predicted in advance and later measured**" | "That stamp is **a declaration written by the authors' own script, not a control**: the only thing that could make it auditable is git history, which this paper does not appeal to." | PAPER.md L189–191 (`sections/01_intro.md` L57–59) |

The one-sentence version an expert says out loud: *"You spent §3.3 explaining that the
contrast is not controlled and §4.2 explaining that the tracks are not independent, and
then you wrote both words back into the sentence that is supposed to be your floor."*

**Is there a defence in the text?** No. §10.5 is unqualified and is the last substantive
paragraph before Related Work. It is also the paragraph that carries the most rhetorical
weight in the whole draft, because its heading promises minimality.

**Status:** **partially logged, and the residue is the worst part.**
`OPEN_ITEMS.md` C1 flags "controlled contrast" and C2 flags "independently developed
track" — but both are scoped to *the abstract*, and `REVIEW_TRIAGE.md` §B issue 8 records
"The body is now honest; the abstract is not." The abstract has since been fixed. Nobody
checked §10.5, or §1.3 L232 (`sections/01_intro.md` L99, "a controlled A0/A0′
contrast"), or the §3.3 **heading** itself (PAPER.md L485, `sections/03_a0.md` L91, "The
controlled contrast"). The fix was applied to the place the reviewer named and not to
the class of error.

**Minimal edit.** In `sections/10_limitations.md` L238–245: "controlled comparison run"
→ "one paired comparison, whose outcome §3.3 shows is entailed by the construction";
"two independently developed tracks" → "two sessions that do not import each other's
code"; "predicted in advance and later measured" → "predicted in the adjudication log
and later measured, under a seal that is a declaration and not a control". Then sweep
`sections/01_intro.md` L99 and `sections/03_a0.md` L91 for "controlled".

---

### 4. "Your transfer arm ran zero engine stages and adjudicated zero candidates because you defined it as the arm that does no induction — that is not a bill, it is your experimental design printed as a table."

**Target** — PAPER.md L1130–1144 (`sections/06_a3_transfer.md` L45–59), §6.2's bill
table and the paragraph under it:

> | engine stages | 1 | **0** | 0 |
> | candidates adjudicated | 35 | **0** | 0 |
> | theorize rounds | 5 | **0** | 0 |
> | DSL clauses written | 33 | **0** | 0 |
>
> The zeros are the interesting column, and the last row is why. Carrying the books
> removed the *inductive* work entirely …

The transfer arm is defined at PAPER.md L1115 as the arm "given L1's two books,
unchanged", and at L1118–1120 as one that "carried … unchanged and re-derived exactly
one thing: the problem instance." An arm that is handed a finished theory and forbidden
to re-derive it *cannot* run an engine stage, adjudicate a candidate, hold a theorize
round or write a clause. The four zeros are entailments of the arm's definition. They
are then quoted in the abstract (PAPER.md L101–102) as a result: "wins with zero engine
stages, zero adjudicated candidates and zero theorize rounds."

The two non-definitional rows are worse than they look, not better. The 0.032/0.029
ratios divide by a cold-start column the paper itself calls unrealistic — PAPER.md
L1241–1243 (`sections/06_a3_transfer.md` L156–158): "**100 % sweep coverage is not
realistic**, so the cold-start column is an upper bound on evidence rather than a
forecast. A cheaper cold start would make the transfer ratio larger, not smaller." So
the headline 34× saving is measured against a denominator the paper concedes nobody
would ever pay.

The sting is that **the paper already knows how to write this disclaimer and did not**.
§3.3, PAPER.md L539–546 (`sections/03_a0.md` L145–152), does it beautifully for A0/A0′:
"The sharper objection is **analytic entailment** … The outcome follows from the
construction; nothing was learned that was not built in." Nothing of the kind appears in
§6. A referee who reads §3.3 and then §6.2 will conclude the honesty is selective, and
selective honesty is more damaging than none, because it shows the authors can tell the
difference.

**Is there a defence in the text?** Partial and scattered. §6.5's six items are strong
and item 4 ("The bill is structural, not economic") is honest about units. But no
sentence in §6 says the zeros are definitional, and §6.1 asserts the opposite framing:
"Three arms were run against L2, **which is what makes the comparison a measurement
rather than an anecdote**" (PAPER.md L1109–1110, `sections/06_a3_transfer.md` L24–25).
What *is* genuinely empirical in §6 — 252/252 against the referee on an unexplored
level, and the negative controls showing the free static layer is blind — is buried under
a table of zeros that isn't.

**Status:** **missed.** §6 postdates both audits.

**Minimal edit.** One sentence under the table: *"Four of these zeros are entailments of
the arm's definition, not measurements: an arm handed a finished manual cannot run an
engine stage or adjudicate a candidate. What the table measures is the two frame/action
rows, and those divide by a cold-start column §6.5 calls an upper bound. The
non-definitional result of this section is 252/252 and §6.3's negative controls."* Then
in the abstract, replace "wins with zero engine stages, zero adjudicated candidates and
zero theorize rounds" with "wins, and scores 252/252 against the referee on a level it
never explored".

---

### 5. "Your title promises certification against something other than the theory's own past, and every 'something other' in this paper is a file the same instance wrote in the same session."

**Target** — PAPER.md L3 (`sections/00_abstract.md` L1):

> # Certifying a world theory against something other than its own past

Inventory of what the paper certifies against:

| §  | the "something other" | who authored it |
|---|---|---|
| §3 (A0/A0′) | `cold-start-a0/artifacts/ground_truth.json` | "the same instance both built the A0 world at M1 and adjudicated it at M3" — PAPER.md L193–195 (`sections/01_intro.md` L61–63) |
| §4 (A1) | peg solitaire — the one genuinely external world | mathematics; **one** 5-hole fixture (PAPER.md L2228–2229) |
| §5 (A2) | "this world's own transition function", a world built to have the defect, substituted for the sealed one | same project; ruling recorded as INC-004 |
| §6 (A3) | "the referee's copy" of a world at `cold-start-a3/a3world/a3_world.py` | same project; the blind control is "an author held blind to L1", and the blind broke (§6.6) |
| §7 (battery) | 38 metric definitions | "the battery's author also wrote the metric definitions, which is structurally impossible to blind" — PAPER.md L2293–2294 |
| §8 (exam) | four papers, a marker, and four synthetic subjects with pre-registered bands | same project; the one real sitting was by two subagents of the same model family, scoring 46.0/46.0 on a saturated sheet (PAPER.md L1780–1784) |
| §2.4 | the failure taxonomy the paper is "scored against" | `Theoria.md`, the project's own design document |

§2.4, PAPER.md L362–364 (`sections/02_framework.md` L95–97), makes the circularity
explicit without noticing:

> Every acceptance report in this repository **scores itself against that table rather
> than against a success metric of its own choosing**

A table of predicted failure modes, written by the same project in its own design
document, *is* a success metric of its own choosing. The sentence refutes itself in
place.

**Is there a defence in the text?** Every component is disclosed — §1.1's seal hole,
§10.1(e)'s "**no benchmark result at all**", §10.3's "The seal has one hole, in the same
place twice", §10.4's un-blindable metric author, §6.6's incident. The disclosure
discipline is genuinely exemplary. What is undefended is the **title**, which is never
reconciled with any of it. Nowhere does the paper say "the 'something other' in our
title is, in every case but peg solitaire, an artefact we also wrote."

**Status:** **the components are logged (C7, and §10 throughout); the title-level
synthesis is missed.** No prior audit reads the title against the inventory.

**Minimal edit.** Either retitle to something the paper delivers — *"Certifying a world
theory against something other than its own trajectory"* is true, cheap, and gives up
nothing the body claims — or add one sentence to §1.3's scope limit: *"'Something other
than its own past' means the world's full transition function rather than the observed
trajectory. In every acceptance but A1 that function is a file this project wrote; the
seal, not a third party, is what separates it from the theorizer."*

---

## Full findings

Severity: **blocking** = a reviewer can reject on this alone; **major** = a reviewer
will name it in the meeting; **minor** = costs credibility; **nit** = fix while passing.

### Overclaims and load-bearing hedges

**F1 · blocking · Title/abstract vs §10.5 on transfer and the exam.** Kill shot 1.
PAPER.md L5–7 vs L2324–2325 (`sections/00_abstract.md` L3–5 vs
`sections/10_limitations.md` L252–253). **Missed** by all prior rounds.

**F2 · blocking · §10.5 restores three hedges the body removed.** Kill shot 3.
PAPER.md L2310–2317 (`sections/10_limitations.md` L238–245). **Partially logged** —
`OPEN_ITEMS.md` C1/C2 name the same words in the abstract only; the abstract was fixed
and §10.5, §1.3 and the §3.3 heading were not.

**F3 · blocking · "Eight results." vs §11.3's own instruction.** Kill shot 2.
PAPER.md L63 vs L2571–2572 (`sections/00_abstract.md` L61 vs `sections/11_related.md`
L243–244). **Logged and knowingly open** (`OPEN_ITEMS.md` §D), and the count has since
risen from four to eight.

**F4 · major · "No arm was run against a baseline" is contradicted 993 lines later.**
Abstract, PAPER.md L116 (`sections/00_abstract.md` L114): "No arm was run against a
baseline." §6.1, PAPER.md L1109 (`sections/06_a3_transfer.md` L24): "**Three arms were
run against L2**, which is what makes the comparison a measurement rather than an
anecdote" — and the three are *cold start*, *transfer*, and *blind control*. The
cold-start arm is precisely a baseline for the transfer arm, and §6.2 tabulates the
ratio between them.

The attack: *"You say no arm was run against a baseline; §6.1 runs three arms against
one level and §6.2 prints the ratio."* The intended meaning — no external system, no
Schema, no WorldCoder — is stated correctly two sentences later ("**None is across the
framework's own arms**", L119–120), but that sentence is scoped by its antecedent to the
*battery's* effect sizes, so it does not cover §6 either, and as written it is now
false: §6.2's bill is across the framework's own arms. **Missed.** Fix: "No arm was run
against another system's baseline; §6's three arms are all ours."

**F5 · major · §7.10 says there is "still no multi-level run"; §6 is a multi-level
run.** PAPER.md L1666 (`sections/07_battery.md` L381), the §7.10 gap table:
"**M3 cross-level transfer (claim C3)** | still no multi-level run, and M3 is
additionally known to have no reachable value at all". §6 (PAPER.md L1086–1283) reports
two levels, three arms and two perturbed variants. The sentence is true *of the ledger
the battery reads* and false as printed in a paper that contains §6. **Missed.** Fix:
"no multi-level run **in the ledger the battery reads** — §6's A3 run is not in it, and
adding it is v3 work."

**F6 · major · §5.2's heading is an invitation.** PAPER.md L852
(`sections/05_a2.md` L40): "### 5.2 Why the substitution can make the claim stronger,
not weaker". The attack lands in one breath: *"You could not run the experiment your own
mandate specified, so you built the world yourself, and then wrote a section arguing
that being unable to run it improved your result."* The three arguments under the
heading are real (near-exhaustive history, history-as-prefix, machine-checked
isomorphism) and §5.1 states the loss plainly first, so the *content* survives; the
*heading* is what gets read aloud in a rejection. Compounding it: claim 3, "The
isomorphism is machine-checked, clause by clause" (PAPER.md L867–876), machine-checks the
built world against six phrases from `Theoria.md` §1.3 — i.e. against a paragraph this
project wrote about a game it is forbidden to look at. **Missed.** Fix: retitle to "What
the substitution costs, and the two things it buys", and add one clause to the
isomorphism table's caption naming what the check is against.

**F7 · minor · "83 tests and 83 pass" survives with its caveat, but §4 still reads as a
headline.** PAPER.md L745–751 discloses the Lean-toolchain dependency honestly (this is
a fix from `OPEN_ITEMS` C8 landing — credit). What is still open is
`REVIEW.md` issue 14's last bullet, unactioned in `REVIEW_TRIAGE.md` §B: `Theoria.md`
itself defines A1 as "判死赌的是管线接通,不是 LLM 灵感" — a plumbing test — and §4 is
quoted in the abstract as result (3). **Logged, open.**

### Circularity and self-grading

**F8 · blocking · The title vs the inventory of self-authored ground truth.** Kill shot
5. **Components logged, synthesis missed.**

**F9 · major · §2.4's self-refuting sentence.** PAPER.md L362–364
(`sections/02_framework.md` L95–97): "Every acceptance report in this repository scores
itself against that table rather than against a success metric of its own choosing". The
table is `Theoria.md`'s, which is the project's own design document. This is the
paper's central honesty device, and it is stated in a form a reader falsifies by reading
the clause's own referent. **Missed.** Fix: "…rather than against a metric chosen after
the run. The table is our own design document's, so it is a pre-registration, not an
external standard."

**F10 · major · The exam's only real result is the system grading itself.** PAPER.md
L1780–1784 (`sections/08_exam.md` L77–81): "Two fresh subagent readers, given a bundle
and a sheet and nothing else, each scored 46.0/46.0 on the handover paper." The paper
never says what the readers were. In a project whose whole apparatus is Claude Code
sessions, a referee will assume — correctly or not — that the examinee, the
question-setter, the rubric author and the marker's calibrator are the same model family
under one operator. *"Two instances of your own system sat an exam you wrote, marked by a
rubric you wrote, and got full marks; what did you learn?"*

**Defence present and strong:** the very next lines (PAPER.md L1786–1801) say "the
handover result is weaker than a perfect score sounds", quote the exam's own status file
("**The second number is not a measurement.** Both tiers hit the ceiling"), and report
`tier2_minus_tier1: null` rather than 0.000. §8.4 adds "n = 1 per handover tier, on a
saturated sheet". This is an *excellently* defended finding — the only thing missing is
naming what the readers were, which costs one clause. **Missed (the disclosure gap only).**
Fix: after "Two fresh subagent readers", add "— fresh instances of the same model family
as the rest of this project, so the exam is not externally sat —".

**F11 · minor · The anti-gaming audit is self-written, and says so.** 38 exploits written
by the author of the 38 metrics, reporting 34 landing. Fully disclosed at PAPER.md
L1447–1450 (`sections/07_battery.md`): "the author built the metric definitions, and a
definition can be tuned toward a hoped-for result without ever seeing data. Processes 1
and 4 exist to catch that, and **neither substitutes for a second pair of eyes**." I
tried this attack and it does not land. Listed here only so the authors know it was
tried. **Logged (W-1), open by nature.**

**F12 · minor · §6.4's blind control is one of the authors, and the blind broke.**
PAPER.md L1116, L1266–1273 (`sections/06_a3_transfer.md`). The disclosure (incident A3-I1,
scope limited to object and law *names*, verdicts fixed two rounds earlier, convergence
quoted from the preserved `as_written` snapshot) is exemplary and mostly disarms the
attack. What survives: the "0 % as written / 100 % canonicalised" headline (PAPER.md
L1213–1217) depends on a canonicalisation the same project wrote, and the paper does not
say who wrote it or whether it was fixed before the comparison. *"Your convergence result
is 0 % until you apply your own normaliser, and then it is 100 %."* **Missed (the
canonicalisation provenance only).** Fix: one clause naming where the canonicaliser
lives and when it was written relative to the blind arm's output.

### n = 1 dressed as a result

**F13 · blocking · §6.2's bill is a definition printed as a measurement.** Kill shot 4.
**Missed.**

**F14 · major · Every single experiment in this paper is n = 1, and the paper says so
seven separate times without ever saying it once.** A0: one world. A0′: one world, one
seeded error, one revision. A1: "the whole A1 verification also ran on exactly **one**
5-hole fixture" (PAPER.md L2227–2229). A2: one world, one deleted rule, one loop. A3: one
game, two levels, one transfer. The exam: one paper sat, two readers, saturated. The
preflight: one run, zero actions. The battery: four paired games with a sign-test floor of
p = 0.125 that no metric can clear.

Each disclosure is honest in place. The cumulative fact — **there is not a single
quantity in this paper supported by more than one instance** — is never stated, and a
hostile reader states it for you in one sentence: *"Eight results, eight n = 1s, and the
one place you computed a p-value you also computed that no p-value is attainable."*
**Missed as a synthesis; every component is logged.** Fix: one sentence in §10.3 —
"Every experiment in this paper is n = 1 in its own unit; the battery is the only
quantitative arm and it is underpowered by arithmetic." That converts the attack from a
gotcha into a citation.

**F15 · minor · K2 = 0.000 to three decimals over n = 3.** `REVIEW.md` issue 11 and
`OPEN_ITEMS` C3 asked for the denominator in the abstract. **It is there now** — PAPER.md
L66, "accuracy 0.000, over the three pairs (n = 3)". **Closed. Attack disarmed**, and
§7.4 goes further ("three decimal places over a denominator of three is a presentational
overstatement"). Noted so the fix is not lost in a future trim.

### Unfalsifiable framing

**F16 · major · Result (8) is a successful non-event.** PAPER.md L111–113
(`sections/00_abstract.md` L109–111): "**(8)** A live run against the real API that
exercised the whole credential path … for zero billable actions." *"Your eighth result
is that you connected to a server and did nothing."* Seventeen of the run's eighteen
RESET attempts returned 400 (PAPER.md L1924–1926), and the paper reports that as a
finding validating a retry envelope.

**Defence present and it is the right one:** §9.4 closes "It is a statement about the
apparatus, not about the framework" (PAPER.md L2068–2069, `sections/09_preflight.md`
L172–173), and §9.3 enumerates four things the run does not establish, including that
the spend gate was not wired at the time and that "a self-consistent ledger is not an
authenticated one". §9 is one of the most honest sections I have read. The attack lands
**only on the abstract**, which promotes an apparatus check into a numbered result.
**Missed at the abstract; fully defended in §9.** Fix: renumber it out of the result
list, or mark it "(apparatus)".

**F17 · minor · "Negative results are also results" is *not* used to launder anything —
and this is worth saying.** I went looking for it. The battery's failures (34/38 exploits
land, 17 register contradictions, X3 backwards, 21 metrics unvalidated after doubling the
arms) are reported as failures of the instrument, not repackaged as findings, and §7.2's
"the battery's validated metrics and its main-table metrics are very nearly disjoint sets"
is a sentence no author writes to flatter themselves. The one place a laundering *reading*
is available is §7.3's registered conditional — "if upstream logged no usage the whole
family resolves to `no-data`, 'a finding, not a failure of the prediction'" — and the
paper immediately reports **both** scoreboards (7/18 strict, 11/18 with the conditional)
"because picking the flattering one is the failure the file exists to prevent" (PAPER.md
L1414–1419). **No finding. Attack fails.**

**F18 · minor · The seal is asserted flatly in the abstract and disclaimed in §1.1.**
Abstract L67–68: "The miss was named in the adjudication log, by direction, *before* the
ground truth was opened." §1.1 L189–191: "That stamp is a declaration written by the
authors' own script, not a control: the only thing that could make it auditable is git
history, which this paper does not appeal to." **Logged** (`OPEN_ITEMS` C7, open). The
body's honesty is complete; the abstract's is not. Fix: "…before the ground truth was
opened, under a seal the authors' own script writes (§1.1)."

### The obvious missing baseline

**F19 · blocking · Nobody ever asked a language model to do any of this, and the paper
never says why not.**

This is the first question from the floor and the paper has no answer in it. The
framework's premise is that an explicit theory beats a world model implicit in weights.
The cheapest possible experiment — *hand a model the same 276-frame A0 trace and ask it
what happens when the Cart pushes UP into the Button* — costs one prompt, has no game
spend, touches no sealed pile, and is the direct test of whether the three held-out pairs
required a pipeline. It was not run. Nor was its analogue for A3 (*show a model L1's
transcript and L2's first frame and ask for a plan*), which is the direct test of whether
carrying "two books" beats carrying a transcript.

What the paper says instead, at PAPER.md L2178–2191 (`sections/10_limitations.md`
L106–119): "**The theorize step is not a measured LLM step.** This is the largest caveat
in the paper and it is stated first … nothing here measures a prompted theorize step
inside a harness, and no number in this paper should be read as one." That is a candid
statement of the gap. **It is not an answer to the question.** The question is not "did
you measure your own theorize step" — it is "did you check that the baseline you are
implicitly beating actually loses". A referee will say: *"You have built an elaborate
apparatus to fix a failure mode you never demonstrated a language model has."*

Nothing in the tree suggests this would be expensive. `grep` over `sections/` returns no
mention of an LLM baseline, an ablation of the theory, or a prompted-model control
anywhere; §7.10 names "a theory-bearing control arm" as the missing thing, which is the
*opposite* ablation — adding books to a baseline, not removing the pipeline from
Theoria.

**Status:** **missed.** `REVIEW.md`, `OPEN_ITEMS.md` and `REVIEW_TRIAGE.md` all discuss
missing *control arms for the battery*; none asks for a plain LLM baseline on the
acceptances. `REVIEW_TRIAGE.md` §E lists exactly two experiments the whole review
needs, and neither is this one.

**Minimal edit that disarms it without running anything.** A paragraph in §10.3, next to
the theorize caveat: *"We also did not run the cheapest available control: prompting a
model directly for the held-out transitions of A0, or for an L2 plan from L1's
transcript. Nothing in Phase 1 establishes that the pipeline beats that baseline, and no
claim here depends on its doing so. It is a Phase 3 arm and it is not in the tree."*
That converts a fatal omission into a declared scope limit — which is the move this paper
is otherwise unusually good at, and it simply has not made it here.

**Better still:** run it. It costs one prompt and no quota, it is inside the development
pile's permissions, and if the model *fails* the three A0 pairs, that single number is
worth more to this paper than §4, §8 and §9 combined.

---

## The single worst paragraph in the paper

**§10.5, PAPER.md L2310–2325 (`sections/10_limitations.md` L238–253).** Both paragraphs
of it, read together.

It is the worst not because it is the least honest — §6.2 is less honest — but because
it is **the paragraph a rejection quotes**, for three reasons at once:

1. Its heading, "The one thing this paper claims", is a promise of minimality, so any
   excess in it is read as bad faith rather than as sloppiness.
2. It is the paragraph a PC member reads third, after the title and the abstract, and it
   contradicts both — the first paragraph claims more than §3.3 and §4.2 allow
   ("controlled", "independently developed"), and the second claims *less* than the
   subtitle and the abstract promise (transfer and the exam disclaimed).
3. It is quotable whole. A referee can paste sixteen lines and say: *"The authors'
   own statement of their minimum claim is simultaneously stronger than their body and
   weaker than their title."* There is no rebuttal to that except an edit.

Runner-up: **§6.2's paragraph under the bill table** (PAPER.md L1140–1144), for the
reason in kill shot 4 — it is the one place where the paper's characteristic move
(name the analytic entailment, demote the claim, keep the honest residue) is conspicuously
*not* made, in a section written after the referee who taught them the move.

---

## Attacks I tried and could not land

The paper's self-audit discipline is real, and these are the attacks it kills before I
can make them. I list them because a rebuttal should know which shots are already
covered, and because a referee who invents defects is useless.

1. **"Your A0/A0′ contrast is n = 1 and the outcome was built in."** Fully disarmed at
   PAPER.md L538–554 (`sections/03_a0.md` L144–160), which not only concedes analytic
   entailment but says the *usual* disclaimer (n = 1) "is not the one that bites" and
   supplies the sharper objection itself. I cannot say it better than the paper does. The
   residue is only that §10.5 and §1.3 forget it (F2).

2. **"Your two headline Lean files are not a minimal pair."** Disarmed at PAPER.md
   L1014–1047 (`sections/05_a2.md`), which corrects its *own source report*, runs the
   diff, lists all 52 changed lines by kind, states what is lost ("the repaired file does
   not prove the *world's* real goal unreachable"), and names the exhibit a future version
   should ship. This was `REVIEW.md`'s blocking issue 1 and it is comprehensively closed.

3. **"An empty axiom list proves nothing — you never showed the check can fail."**
   Disarmed twice: §4.3's negative control (`w .p1 := 7` → `decide proved … is false`,
   all four theorems `[sorryAx]`, exit 1) and — better — §6.6's vacuous Lean output kept
   in the tree at `cold-start-a3/theory/generated_l1_vacuous/` "precisely so that an empty
   axiom list is not read as a guarantee on its own" (PAPER.md L1279–1282). Keeping a
   known-vacuous artefact on purpose is a move I have not seen in a submitted paper.

4. **"You claim two independent tracks and they are two sessions on one machine."**
   Disarmed at PAPER.md L718–724: "A reader should not picture two teams … a
   *defence-in-depth* result, not an independent replication." Only §10.5 reopens it (F2).

5. **"Your battery's author wrote its metrics."** Disarmed at PAPER.md L1447–1450 and
   L2293–2294 — stated as "structurally impossible to blind", with the five `[seen]`
   post-dictions named individually rather than passed off as predictions.

6. **"Your 1 790 leak probes finding zero hits is security theatre."** Disarmed, and
   with the best sentence in the paper attached: PAPER.md L1818, "That number is worth
   almost nothing on its own, and the directory says why" — followed by the two real
   leaks the adversarial reader found, and the diagnosis that "an optional check is a
   check that does not run, and it fails in the direction that looks like success"
   (L1833). The instrument reports its own blindness with the number that flatters it.

7. **"Your contamination story is convenient."** Disarmed at real cost: §10.1(f) reports
   INC-BA-001, a subagent of this project reading mechanics for **nine** sealed games,
   with no upside to disclosing it. §10.2 then corrects the repository's own `CLAUDE.md`
   for saying no game had been played. A project that publishes its own contamination
   incident does not get accused of hiding one.

8. **"Your headline metric K4 = 1.000 is gamed."** Disarmed — the paper reports the
   gaming itself (K4 in the reference tier, `defended: false`, "K4 must never be reported
   without K2 beside it" written into `gaming_audit.json` rather than into prose), and
   §7.4 goes on to report that K2's *own* defence failed in the manner its
   pre-registration named in advance.

9. **"You cherry-picked which pre-registration scoreboard to report."** Disarmed at
   PAPER.md L1414–1419 — both numbers reported, "because picking the flattering one is
   the failure the file exists to prevent."

10. **"Your Fast Downward numbers are not from Fast Downward."** Disarmed at PAPER.md
    L2236–2258, which states it in bold, explains the `prefer="stub"` decision, notes
    that the stub is length-optimal so the verdicts are sound, and then cites all *three*
    disagreeing repository statements about whether FD was ever built and says which is
    later. This is `REVIEW.md` issue 12 closed properly.

11. **"§7's numbers are from an obsolete battery version."** Disarmed — this was
    `OPEN_ITEMS.md` A1, the paper's own top blocking item, and §7 has been fully
    re-derived against `battery_version: "v2"` with every figure read from
    `battery/artifacts/*.json`. Verified against the v0/v1/v2 counts quoted at PAPER.md
    L1294–1302.

---

## Summary table

| # | finding | severity | prior status |
|---|---|---|---|
| F1 | title/abstract promise transfer + exam; §10.5 disclaims both | **blocking** | missed |
| F2 | §10.5 restores "controlled", "independently developed", "predicted in advance" | **blocking** | partially logged (abstract only) |
| F3 | "Eight results." vs §11.3's own instruction to the abstract | **blocking** | logged, knowingly open |
| F8 | title's "something other than its own past" vs self-authored ground truth throughout | **blocking** | components logged, synthesis missed |
| F13 | §6.2's bill: definitional zeros as measurement, unrealistic denominator | **blocking** | missed |
| F19 | no LLM baseline anywhere, and no sentence explaining its absence | **blocking** | missed |
| F4 | "No arm was run against a baseline" vs §6.1's three arms | major | missed |
| F5 | §7.10 "still no multi-level run" vs §6 | major | missed |
| F6 | §5.2's heading argues the forced substitution improved the result | major | missed |
| F9 | §2.4's "not a success metric of its own choosing" refutes itself | major | missed |
| F10 | exam's only real sitting is the system grading itself; readers unnamed | major | missed (disclosure gap only) |
| F14 | every experiment is n = 1; never said once, cumulatively | major | components logged |
| F16 | abstract result (8) is a successful non-event | major | defended in §9, not in abstract |
| F7 | §4 reads as a headline; `Theoria.md` calls it plumbing | minor | logged, open |
| F12 | blind control's canonicaliser provenance unstated | minor | missed |
| F18 | seal asserted flatly in abstract, disclaimed in §1.1 | minor | logged (C7) |
| F11 | anti-gaming audit is self-written | minor | logged, open by nature |
| F15 | K2 n = 3 in the abstract | — | **closed; attack disarmed** |
| F17 | "negative results are results" laundering | — | **not present; attack fails** |
