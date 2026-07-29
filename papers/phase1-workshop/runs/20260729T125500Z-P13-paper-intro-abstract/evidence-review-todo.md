# Evidence review — everything the P12 round said about the abstract and §1

Compiled at P13 (2026-07-29) from the five P12 reviews, `REVISION.md`,
`OPEN_ITEMS.md`, `REVIEW_TRIAGE.md`, `OUTLINE.md`, `README.md` and the P13 brief.
Every "already fixed?" verdict below was checked against the **current**
`sections/00_abstract.md` (128 lines) and `sections/01_intro.md` (132 lines), not
assumed.

Sources, all under `papers/phase1-workshop/`:

| tag | file |
|---|---|
| **(a) domain** | `runs/20260728T173000Z-P12-paper-multi-review/review-a-domain.md` |
| **(b) methods** | `runs/20260728T173000Z-P12-paper-multi-review/review-b-methods.md` |
| **(c) repro** | `runs/20260728T173000Z-P12-paper-multi-review/review-c-repro.md` |
| **(d) adversarial** | `runs/20260728T173000Z-P12-paper-multi-review/review-d-adversarial.md` |
| **(d) hostile** | `runs/20260728T173000Z-P12-paper-multi-review/review-d-hostile.md` |
| **(e) lay** | `runs/20260728T173000Z-P12-paper-multi-review/review-e-lay.md` |
| **REVISION** | `runs/20260728T173000Z-P12-paper-multi-review/REVISION.md` |
| **BRIEF** | `runs/20260729T031000Z-P13-paper-intro-abstract/BRIEF.md` |
| **TRIAGE** | `REVIEW_TRIAGE.md` · **OPEN** `OPEN_ITEMS.md` · **OUTLINE** `OUTLINE.md` |

---

## 1 · Every finding that names the abstract or §1, sorted by severity

### 1A · BLOCKING — a referee can reject on this alone

---

**T1 · The subtitle sells a transfer result and an examination instrument; §10.5
disclaims both.** — (d) adversarial F1, "blocking", status **missed by all prior
rounds**.

> "Your subtitle sells me a transfer result and an examination instrument, and
> your §10.5 tells me transfer and the exam are unevidenced and not claimed —
> which of your own sentences would you like me to believe?"
> — (d) adversarial, kill shot 1

Targets: `sections/00_abstract.md` L3–5 vs `sections/10_limitations.md` L252–253.

**Fixed? NO.** Current subtitle (`00_abstract.md` L3–5): "three offline
acceptances and **a transfer result**, a passive metrics battery, **an
examination instrument**, and a live run that spent nothing". Current
`10_limitations.md` L252–253 still reads: "Everything else in `Theoria.md` — the
ordering claim, the bill shape, **transfer**, **the exam**, the cost magnitude —
is unevidenced here and is not claimed." Also seconded by (a) domain §4:
"§10.5's closing sentence … is contradicted by §6".

Note the *body* of the abstract already draws the distinction the subtitle does
not (L58–61: "plus a fourth section reporting an early read on claim C3 that the
mandate does not list as an acceptance"). The subtitle is what is unfixed.

---

**T2 · "Eight results." contradicts §11.3's own instruction to the abstract.**
— (d) adversarial F3, "blocking", status **logged and knowingly open**; (d)
hostile 2.4 "LANDS"; OPEN_ITEMS §D.

> **"Prediction perfect, understanding broken" is this framework's own premise,
> not a finding.** … which is analytically guaranteed by the construction. The
> exhibit has value as a teaching object and as a test of the instrument. **It is
> not evidence about anything, and the abstract should not read as though it
> were.** — §11.3, quoted by (d) adversarial and (d) hostile

> "The paper contains an instruction to fix its own abstract, and shipped the
> abstract unfixed. A referee does not need to construct this criticism; he only
> needs to quote the paper against itself." — (d) hostile 2.4

> "`OPEN_ITEMS.md` §D … 'the abstract still reads as "four results" where the
> honest scope is an instrument-and-artefact contribution'. The authors know.
> They have now made it worse by four." — (d) adversarial F3

**Fixed? NO.** `00_abstract.md` L61 still ends "…and one live run that spent
nothing. **Eight results.**", and result (4) — L79–86 — is exactly the exhibit
§11.3 names, led with "The headline artefact is a *pair* of Lean files".

Minimal edits already on file: (d) adversarial — 'Delete "Eight results." and
replace with "Eight artefacts; one contribution." Or move the abstract's own
closing paragraph to sit immediately after the list.' (a) domain m4 — "Reconcile
the counts; the preflight and the exam are apparatus, not results, by the
paper's own §9.4 and §8.4." (d) hostile 1.9 — for result (5): "That is a negative
result. Report it as one or drop it."

---

**T3 · The abstract leads with the artefact its own §11.3 and both hostile seats
say is not a finding.** — (e) lay 6.1; (d) hostile §7.1; (a) domain §1.3.

> "**6.1 — 'The instrument cannot tell them apart, and is not supposed to.'**
> (abstract, §1.2, §5.6.) This is the headline artefact and I do not think it is
> a finding. That a proof assistant will certify a theorem about a wrong model is
> the definition of what a proof assistant does; no formal-methods reader will be
> surprised. … **The abstract should not lead with this.**" — (e) lay

> "Every file your generator emits has identical tactic, dependency surface and
> axiom list; you have exhibited your generator's determinism, not a failure mode
> — and since the two theorems are about different goals, the instrument was
> never asked to tell them apart." — (d) hostile §7.1

**Fixed? NO.** `00_abstract.md` L83–86 still calls the pair "The headline
artefact" and closes result (4) on "The instrument cannot tell them apart, and is
not supposed to." `01_intro.md` §1.2 (L68–85) still gives it the second exhibit
slot and quotes the same sentence.

---

**T4 · The title asserts what §2.3 denies.** — (a) domain m1 + §5(1); (d) hostile
1.3 "LANDS"; (d) adversarial F8/kill shot 5, "blocking", **components logged,
synthesis missed**.

> "**The title** (`PAPER.md:3`): 'Certifying a world theory against something
> other than its own past'. §2.3 says '**Neither layer certifies the manual
> against the world**'. The title asserts the thing §2.3 denies. The honest title
> is about *making the gap visible*, not about certifying across it." — (a) domain

> "Your title promises certification against something other than the theory's
> own past, and every 'something other' in this paper is a file the same instance
> wrote in the same session." — (d) adversarial kill shot 5

The title lives in `sections/00_abstract.md` L1, so it is this rewrite's problem.
(d) adversarial supplies two alternatives: retitle to "*Certifying a world theory
against something other than its own trajectory*" ("true, cheap, and gives up
nothing the body claims"), **or** add one sentence to §1.3's scope limit:

> "'Something other than its own past' means the world's full transition function
> rather than the observed trajectory. In every acceptance but A1 that function is
> a file this project wrote; the seal, not a third party, is what separates it
> from the theorizer."

**Fixed? NO.** Title unchanged.

---

**T5 · The paper never says what benchmark or environment it is about.** — (e)
lay 2.1, first blocking finding.

> "The paper never introduces its problem domain. 'ARC' first appears at line
> 1918, **inside a code fence**, in §9 … 'ARC-AGI-3' is named exactly once, in
> §11.1, at line 2371, on page ~22. Yet from the abstract onward the paper leans
> on 'games', 'the sealed pile', 'the development pile', 'levels', 'scorecard',
> 'the real API', 'quota', 'the referee'. … That is a one-paragraph fix and its
> absence is the largest single obstacle in the paper."

Compounded by (a) domain m2: abstract (6)'s "second level of the same game" is a
self-built 9×9 world (`cold-start-a3/a3world/a3_world.py`) and "will be read as an
ARC game"; "'game', 'level' and 'referee' all import benchmark connotations the
object does not have. §6 is scrupulous; the abstract is not."

**Fixed? NO.** Neither "ARC" nor "ARC-AGI-3" appears anywhere in
`00_abstract.md` or `01_intro.md`. "game" appears in the abstract in both senses
(L98 "second level of the same game" = self-built; L116 "No game was played *for*
this paper" = ARC).

**Constraint:** OUTLINE red line 6 forbids a citation not cross-verified twice,
and REVISION records that the ARC-AGI benchmark is uncited and **cannot be cited
in an offline session**. So the fix here is a *definitional paragraph*, not a
citation.

---

**T6 · "No arm was run against a baseline" is false as written.** — (d)
adversarial F4, "major", **missed**.

> Abstract, `sections/00_abstract.md` L114: "No arm was run against a baseline."
> §6.1: "**Three arms were run against L2**, which is what makes the comparison a
> measurement rather than an anecdote" — and the three are *cold start*,
> *transfer*, and *blind control*. The cold-start arm is precisely a baseline for
> the transfer arm, and §6.2 tabulates the ratio between them.

> "The intended meaning — no external system, no Schema, no WorldCoder — is
> stated correctly two sentences later ('**None is across the framework's own
> arms**'), but that sentence is scoped by its antecedent to the *battery's*
> effect sizes, so it does not cover §6 either, and as written it is now false:
> §6.2's bill is across the framework's own arms."

Proposed fix, verbatim: "No arm was run against another system's baseline; §6's
three arms are all ours."

**Fixed? NO.** L115 still reads "No arm was run against a baseline."; L120 still
"**None is across the framework's own arms**".

---

**T7 · Abstract result (8) attributes to one run the properties of two.** — (b)
methods B4, "blocking"; (d) hostile 1.8 + 2.3 "LANDS"; (d) adversarial F16,
"major".

> Abstract L109–112: "**(8)** A live run against the real API that exercised the
> whole credential path — key injected in one place, **sealed pile untouched by a
> check on the bytes** — for **zero billable actions**."

> The preflight manifest "has zero billable actions … and **no byte scan**". The
> byte scan lives in `theoria-arm/runs/20260728T015354Z-g50t-first-contact/
> MANIFEST.json` — "and **that run spent**: `budget.actions_ok: 7`,
> `commands_sent: 40`, `cost.cli_reported_usd: 6.317658`." — (b) methods B4

> "§9.2 states this correctly … So the abstract contradicts the body. The
> abstract's exemption from the citation rule is 'each figure in it is cited
> where it recurs in the body' — here the recurrence refutes it."

> "Your eighth result is that you connected to a server and did nothing." — (d)
> adversarial F16. Fix: "renumber it out of the result list, or mark it
> '(apparatus)'."

**Required (b):** "Split result (8), or drop the byte-scan clause from it."

**Fixed? NO.** L110–112 verbatim as quoted.

---

**T8 · No LLM baseline anywhere, and no sentence explaining its absence.** — (d)
adversarial F19, "blocking", **missed by every prior round**.

> "The cheapest possible experiment — *hand a model the same 276-frame A0 trace
> and ask it what happens when the Cart pushes UP into the Button* — costs one
> prompt, has no game spend, touches no sealed pile, and is the direct test of
> whether the three held-out pairs required a pipeline. It was not run."

> "A referee will say: *'You have built an elaborate apparatus to fix a failure
> mode you never demonstrated a language model has.'*"

The proposed disarming paragraph is scoped to §10.3, but the rewrite owns the
intro's scope-limit paragraph, which is where a reader forms the expectation. The
suggested text: "*We also did not run the cheapest available control: prompting a
model directly for the held-out transitions of A0, or for an L2 plan from L1's
transcript. Nothing in Phase 1 establishes that the pipeline beats that baseline,
and no claim here depends on its doing so. It is a Phase 3 arm and it is not in
the tree.*"

**Fixed? NO.** No mention anywhere in `00_abstract.md` or `01_intro.md`.

---

**T9 · §1.3 still says "controlled".** — (d) adversarial F2 "blocking"; (b)
methods M11 "major"; (a) domain B4; TRIAGE issue 8; OPEN_ITEMS C1.

> "**Nobody checked §10.5, or §1.3 L232 (`sections/01_intro.md` L99, 'a
> controlled A0/A0′ contrast'), or the §3.3 heading itself.** The fix was applied
> to the place the reviewer named and not to the class of error."
> — (d) adversarial F2

> "§3.3 concludes that A0/A0′ '**demonstrates the mechanism rather than tests
> it**' … But `PAPER.md:230–233` (§1.3 item 1) still advertises 'a **controlled**
> A0/A0′ contrast'." — (b) methods M11

**Fixed? NO in §1.3; YES in the abstract.** `01_intro.md` L99 still reads "with a
**controlled** A0/A0′ contrast". The abstract L69–71 was already corrected to "a
design lesson **demonstrated by construction rather than a hypothesis tested**"
— (d) hostile explicitly credits this: "the abstract was corrected and §10.5 was
not." **Do not undo the abstract's wording while fixing §1.3's.**

---

**T10 · §1's hook lands and then §1 dismantles it.** — (e) lay §4, and the fifth
of the five blocking lay findings named in BRIEF.

> "**The hook lands. The section does not.** … Then §1 spends the rest of itself
> dismantling its own hook, and I think this is the central craft failure of the
> paper … Each of those is individually honest and I respect all of them.
> Collectively, they mean that by line 264 the paper has told me: the finding was
> constructed, the pre-registration is self-attested, the exhibit is not minimal,
> nothing was played, and the LLM step was done by hand. **A reader who is not
> being paid stops here.** Not because the work is bad — because the paper has
> just spent 130 lines explaining why they shouldn't care, before ever explaining
> what 'care' would consist of."

> "Would I keep reading unpaid? Honestly: I would read to the end of §1 and then
> skim to find a comparison table, find none, and close it. The thing that would
> have kept me is the §7.7/§8.3 material, and nothing in §1 tells me it is
> coming."

**Fixed? NO** — the current §1 is structurally unchanged (hook L1–29, then five
disclosures at L57–59, L61–66, L42–51, L79–82, L119–132).

**Critical reading note.** The lay reviewer's prescription is *relocate*, not
*delete*: "Keep, in this order and this budget: | The hook, cut to 3 paragraphs |
1 | 400 | 276/276 + 0.000 + R-05 written first. Stop there. **Move every caveat to
limitations.**" See §4 of this file for what must survive the move.

---

### 1B · MAJOR — a referee will name it in the meeting

---

**T11 · The best contribution is buried as item 4 of 4 in §1.3.** — (a) domain
M8 + §1.3 + §3; (e) lay §3 + §5; REVISION "the structural recommendation both
independent reviewers reached".

> "**The executable anti-gaming register (§7.7).** Not the battery — the *audit*.
> … I have not seen a metric suite audited this way … **The paper undersells this
> badly** — it is item 4 of 4 in §1.3 and gets one clause in §10.5." — (a) domain

> Contribution table, row 4: "**The widest daylight in the paper.** I know of no
> metric suite that ships a runnable exploit per metric and reports how many still
> land. **This should be contribution 1, not 4.**" — (a) domain §3

> "**Publish the evaluation-instrument negative result.** §7.7, §7.4, §7.10 and
> §8.3 together are a coherent, self-contained, genuinely novel-feeling workshop
> paper … are useful to anyone building agent evaluations, require no belief in
> the Theoria framework at all, and are not analytically guaranteed by their own
> construction, which is more than the A2 exhibit can say." — (e) lay §5

> "(a) and (e) never saw each other and converged … That is a restructuring
> decision about what the paper *is*." — REVISION

**Fixed? NO.** `01_intro.md` L112–117 still has the battery as contribution 4 of
4, and describes it as a recompute, not as an audit — the word "exploit" does not
appear in the intro at all.

---

**T12 · §1.3 lists four contributions; the paper delivers seven result
sections.** — (e) lay §1.

> "The thing I did not anticipate at all: this is not one paper. It is seven
> loosely-joined reports (A0/A0′, A1, A2, A3, battery, exam, preflight) with a
> shared limitations chapter. Nothing in §1 prepares you for that; §1.3 lists four
> contributions and the paper delivers seven sections of results, three of which
> (§6 exam-adjacent transfer, §8 exam, §9 preflight) are not in the contribution
> list at all."

**Fixed? NO.** `01_intro.md` L93–117 still lists exactly four.

---

**T13 · §1 asserts the seal flatly where §1.1 later disclaims it — and the
abstract asserts it with no disclaimer at all.** — (d) adversarial F18 "minor,
logged (C7)"; (d) hostile 3.1 "LANDS"; (b) methods M1; (e) lay 6.8.

> Abstract L66–68: "The miss was named in the adjudication log, by direction,
> *before* the ground truth was opened." §1.1 L57–59: "That stamp is a declaration
> written by the authors' own script, not a control: the only thing that could
> make it auditable is git history, which this paper does not appeal to."
> **The body's honesty is complete; the abstract's is not.** Fix: "…before the
> ground truth was opened, under a seal the authors' own script writes (§1.1)."
> — (d) adversarial F18

> "**Your pre-registration is a file you wrote, sealed by a script you wrote, in
> a repository whose history you decline to cite.**" — (d) hostile 3.1

**(b) methods M1 supplies new evidence the rewrite can use, and it cuts both
ways:**

> "**A0's seal gains nothing from it.** `848d683` ('M3 — theorize, by hand, with
> the reasoning kept') is 2026-07-28 01:02:02 and `38500b3` ('M6 — the score') is
> 01:03:04 — **62 seconds apart**, one batch at the end of a session. The history
> is consistent with the seal and corroborates nothing."
>
> "**The battery's pre-registration does check out.** `19eafb2` 14:20:35
> 'pre-register the CC vs Schema contrast, before reading the recon' precedes
> `82a6925` 14:29:44 … That is real, external, cheap corroboration of the paper's
> most-leaned-on discipline, and the paper does not cite it."
>
> "The asymmetry is the finding: the corroboration exists and is free where the
> paper's claim is strongest, and is unavailable where the claim is weakest. Say
> that, rather than declining git wholesale."

**Fixed? NO.** Abstract carries no seal caveat; §1.1 L57–59 carries the
disclaimer but not M1's git finding.

---

**T14 · Abstract (3): "a second track developed alongside it" — reviewers
disagree.** — (a) domain §5(3) and B5 say it is a leak; (d) hostile §7.2 says the
abstract is the *corrected* version.

> "**Abstract (3)** (`PAPER.md:77`): 'crosses a JSON data boundary into a
> **second track developed alongside it**'. Same problem as §10.5 clause 4;
> §4.2's correction never reaches the abstract." — (a) domain §5(3)

> "**The abstract is cleaner than §10.5 on both counts.** `PAPER.md:76–78` says
> 'a second track **developed alongside it**' … So the abstract was corrected and
> §10.5 was not. The paper's most-revised paragraph is not its most-quoted one."
> — (d) hostile §7.2

**Fixed? PARTIALLY / disputed.** Current abstract L75–76 reads "crosses a JSON
data boundary into a second track developed alongside it". §1.3 item 2
(`01_intro.md` L102–107) says "produced by an independent engine's LP" and does
*not* use "independently developed" — so the intro is already the safer wording.
Safest resolution, from §4.2's own text: "two sessions that do not import each
other's code" (proposed by (d) adversarial for §10.5).

---

**T15 · "95 runs across 5 arms" — the five arms are never enumerated, and "bare
Claude Code" and "Schema" are used unexplained.** — (e) lay 2.2, second blocking
lay finding.

> "'Five arms' is load-bearing throughout §7 and the five are **never
> enumerated**. I collected, by scavenging: `bare_cc`, `schema_repro`, 'the model
> ladder' … That is six candidate names for five slots and I could not resolve it."
>
> "'bare Claude Code' (abstract, line 119) is used as if it were a standard
> baseline. It is a commercial coding-agent product. It needs a sentence."
>
> "'Schema' is introduced at line 119 as a control arm and not explained until
> line 2370. In between it carries six pages of effect sizes."

(e) lay §7 names the fix material that already exists and is uncited:
`battery/PREDICTIONS.md` "carries a table describing `bare_cc` and `schema_repro`
in one line each ('in weights, in the transcript; acts, then reconsiders' /
'`world_model.py`, replay-level; a fitted simulator, no theorems'). Excellent, and
absent from the paper."

**Fixed? NO.** Abstract L88–89 "95 runs across five arms"; L117–118 names only
"bare Claude Code" and "released upstream Schema trajectories", both unexplained.

---

**T16 · Metric ids K2 / K4 are dropped into §1, six sections before they are
defined.** — (e) lay 2.3, third blocking lay finding.

> "K2 and K4 are worse than that: they are dropped into **§1**, at line 152, six
> sections before §7.4 explains them."
> …
> "**The metric alphabet.** `battery/METRICS.md` is a generated, complete glossary
> of all 38 metrics with their families and declared directions … **None of this
> is in the paper.** Importing the id→name column alone would fix §2.3 above at a
> cost of ~15 words per table." — (e) lay §7

**Fixed? PARTIALLY.** `01_intro.md` L20–22 does gloss them inline ("K4 evidence
coverage = 1.000 and K2 held-out accuracy = 0.000") — the *names* are there, the
*definitions* are not, and the ids themselves are still opaque. The abstract L92
also uses "the exploration family's declared signature" without naming X3.

---

**T17 · Two of five keywords advertise capabilities the paper disclaims.** — (a)
domain m3 + §5(5).

> "**Keywords** (`PAPER.md:128`): 'world models · **program synthesis** ·
> unsolvability certificates · interactive theorem proving · **agent
> evaluation**'. The paper runs no LLM agent (§10.3: the theorize step is done by
> hand) and measures no synthesis step. Two of five keywords advertise
> capabilities the paper explicitly disclaims."

**Fixed? NO.** `00_abstract.md` L127–128 unchanged.

---

**T18 · The intro's central number is cited to the weaker of two artefacts.** —
(b) methods M10.

> "the accuracy figure is cited to `score_vs_truth.json`; the *coverage* figure is
> cited only to `A0P_REPORT.md` §1, when the artefact exists and is decisive:
> `cold-start-a0/artifacts/trace_summary.json`, `covered_pairs: 233`, with
> `uncovered_pairs` listing exactly `cart=(2,2) pressed=0 act=DOWN`, `cart=(3,1)
> pressed=0 act=RIGHT`, `cart=(4,2) pressed=0 act=UP` — the same three in
> `score_vs_truth.json`'s `held_out.examples`. **That file is the strongest
> evidence in §3 and the paper does not cite it. This is the binding rule failing
> on the paper's best number.**"

> "The identity of the two fractions **is the paper's central finding** — the
> manual is wrong on exactly the pairs the trace never covered — and presenting
> them as two independent table rows with different roundings hides the very thing
> being claimed."

**Fixed? NO.** `01_intro.md` L16–19 asserts "The three it misses are exactly the
three pairs the trajectory could never have contained" and cites only
`score_vs_truth.json` `held_out.accuracy`. **This is the intro's load-bearing
sentence and it has a stronger artefact available:
`cold-start-a0/artifacts/trace_summary.json`.**

---

**T19 · The paper's "hook" number, 98.98, has no denominator.** — (e) lay 2.7,
first item.

> "**'a score of 98.98 on replayed history'** (line 137, §1, third sentence).
> 98.98 of what, on what, by whom? This is the paper's *hook* and it is the number
> I understood least. It turns out (§11.1, line 2378, twenty pages later) to be a
> prior system's self-reported percentage on a public set. At §1 I could not tell
> if it was this project's own result."

**Fixed? NO.** `01_intro.md` L5–6: "why a score of 98.98 on replayed history
(`Theoria.md` §3.1) stopped resolving anything about understanding."

---

**T20 · §1 vocabulary presented as standard: "acceptance", "beat", "DC22",
"referee", "register/tier".** — (e) lay 2.4 (major) and §4's second §1 problem.

> "**'acceptance'** — in the subtitle ('three offline acceptances'), the abstract,
> and §1, meaning something like a pre-declared gate condition. Not explained until
> §2.5 at line 371, ~2,400 words in. On first read I parsed it as 'acceptance test'
> and then as 'paper acceptance' and got both wrong."
>
> "**'beat'** — a step of the repair loop. Used in the abstract ('closes in six
> recorded beats') long before §5.5 shows what one is."
>
> "**'register' / 'tier' / `main` / `reference`** — a whole governance apparatus
> for metrics, used from line 93 (abstract) and never described as a system."
>
> "**DC22** (line 219) is used with no explanation … I could not tell whether
> DC22 was a game, a failure mode, a decision id, or a section. (§5.1 eventually
> says it is a sealed game; §1.2 does not.)"

Seconded by (a) domain m7: "'three offline acceptances' is internal milestone
vocabulary that reads as external validation. Consider 'three offline
milestones.'"

**Fixed? NO** on all four. Abstract L58 "three acceptances"; L82 "six recorded
beats"; L92–93 "the exploration family's declared signature"; `01_intro.md` L87
"under the name DC22".

---

**T21 · The draft-status block is 500 words of internal version history in front
of the first sentence of content.** — (e) lay §4 and §5.

> "The **draft-status block** (lines 12–45) sits between the title and the
> abstract and is 500 words of internal version history … Whatever its value to
> the team, to an outside reader it is a 500-word notice reading *this is not
> finished*, placed before the first sentence of content. **It must not survive
> into anything sent to a venue.**"

**Fixed? NO.** `00_abstract.md` L10–43. **Caution:** it contains the declaration
of the binding rule *and of the abstract's exemption from it*, which (d) hostile
lists among attacks that failed precisely because it is "declared up front" — see
§4.9 below.

---

**T22 · "Eight results" vs six claims; the preflight and the exam are apparatus.**
— (a) domain m4 + §5(7).

> "**Abstract 'Eight results'**. Counting the preflight (which spent nothing and
> establishes a property of the apparatus, §9.4's own words) and the exam (three
> of four papers never sat, §8.2) as 'results' inflates the count. §10.5 claims
> six things; the abstract advertises eight."

**Fixed? NO.** See T2.

---

**T23 · Every experiment is n = 1, and the cumulative fact is never stated.** —
(d) adversarial F14, "major", **components logged, synthesis missed**.

> "*'Eight results, eight n = 1s, and the one place you computed a p-value you
> also computed that no p-value is attainable.'* … Fix: one sentence in §10.3 —
> 'Every experiment in this paper is n = 1 in its own unit; the battery is the
> only quantitative arm and it is underpowered by arithmetic.' That converts the
> attack from a gotcha into a citation."

Relevant to the abstract because the abstract enumerates the eight. **Fixed? NO.**

---

**T24 · The sealed-pile contamination is disclosed on page 20 and the abstract's
phrasing reads stronger.** — (e) lay 6.9.

> "Nine sealed games were contaminated by a web search (§10.1(f), INC-BA-001), two
> 'materially'. The paper reports this cleanly and I want to note only that it is
> disclosed in §10 on page ~20 and not mentioned in the abstract, which says
> 'sealed pile untouched by a check on the bytes'. Both statements are true about
> different things — API contact vs. knowledge — and the abstract's phrasing will
> be read as the stronger one."

**Fixed? PARTIALLY.** The abstract L111–112 still says "sealed pile untouched by
a check on the bytes". `01_intro.md` L124–125 *does* now carry the pointer:
"though §10.1 records that the sealed pile is nonetheless no longer clean, for
reasons that have nothing to do with this paper's experiments" — that is the fix
landing in the intro but not the abstract.

---

### 1C · MINOR — costs credibility

**T25 · The damaged sentence in the abstract.** — (e) lay 2.10.

> Lines 94–97: "and the exploration / family's declared signature separates the /
> one gradient the design specifies *backwards*."
> "The ragged mid-clause line break plus the placement of 'backwards' makes this
> garden-path badly; on first read I parsed 'specifies backwards' as a unit. It
> recurs, better, at line 1386. Suggest: '…and the exploration family's signature
> metric separates the design's own specified gradient **in the wrong
> direction**.'"

**Fixed? NO.** `00_abstract.md` L92–94, ragged break intact.

**T26 · "paper" collides with "paper".** — (e) lay 2.9.

> "§8 calls the exam's four question types 'papers': 'Three of its four papers
> have never been sat' (abstract, line 111). I read that as a statement about
> publications and had to reread. … Rename to 'sheets' or 'sections' or anything
> else."

**Fixed? NO.** `00_abstract.md` L110.

**T27 · Arms A0, A0′, A1, A2, A3 introduced out of order and unevenly.** — (e)
lay 2.11.

> "A0/A1/A2 are used in the abstract, defined in §2.5. A0′ is used in §1.3 and
> introduced in §3.3. A3 is used in the abstract's result (6) without the label …
> At that point I was tracking five world-instances (A0, A0′, a0-spike, A2's
> world, A3's L1/L2) and I lost which was which more than once."

**Fixed? NO.** Abstract L59 "A0, A1 and A2"; result (6) L98 has no A3 label;
`01_intro.md` L99 uses "A0/A0′" with A0′ never introduced.

**T28 · The citation format makes the prose unreadable.** — (e) lay 2.8.

> "The binding rule (every number carries its artefact path) is defensible as
> policy and is disastrous as typography. … I estimate 8–12 % of the body's word
> count is repo paths inside running prose. The rule can be kept and the cost
> removed by moving paths to numbered endnotes or to `PROVENANCE.md`."

**Fixed? NO.** `01_intro.md` carries ~18 inline paths in 132 lines.
**Warning:** the *rule itself* is OUTLINE red line 1 and BRIEF states the intro is
not exempt. Any relocation must keep every path resolvable — see §5.

**T29 · Length.** — (a) domain m9; (e) lay §5; OPEN_ITEMS E1; TRIAGE §F(6).

> "23,667 words by `wc -w`, against a stated ~4,000 budget. That is not a paper
> that needs cutting; it is three or four different papers sharing a file. My
> advice is therefore not 'trim' but 'choose'." — (e) lay

(e) lay's §1 budget if the framework stays the paper: **"The hook, cut to 3
paragraphs | §1 | 400 words | 276/276 + 0.000 + R-05 written first. Stop there.
Move every caveat to limitations."** The current §1 is ~1,300 words.

**T30 · Draft-status word count is wrong.** — (b) methods MINOR 1.

> "`PAPER.md:13` — draft status says '~23 200 words'; `wc -w PAPER.md` = **23
> 667**."

**Fixed? NO.** `00_abstract.md` L12 still says "~23 200 words".

**T31 · Three figures cited and not present / broken paths — REFUTED, do not
action.** — (e) lay 2.6 and §7, filed BLOCKING; **refuted in REVISION**.

> "'Six of seven cited figure paths do not exist' (reviewer e, filed BLOCKING).
> **All nine `figures/…` paths cited by `PAPER.md` resolve.** The reviewer looked
> under `papers/phase1-workshop/figures/`, the deprecated parity witness, instead
> of the repo-root pipeline. The confusion is real and is its own item (P13); the
> defect is not." — REVISION

No figure is cited from `00_abstract.md` or `01_intro.md`, so this does not touch
the rewrite except as a caution not to "fix" it.

---

### 1D · Already fixed — verified against the current text; do not regress

| # | finding | source | evidence it is fixed |
|---|---|---|---|
| **X1** | R-05 "three pairs" overstates the log | REVIEW blocking 4 · OPEN A3 · TRIAGE issue 4 · (a) domain §4 clause 2 | `01_intro.md` L42–51 now names three **directions** and explicitly refuses the M6 gloss; abstract L66–67 says "by direction" |
| **X2** | `0.000` quoted to three decimals with no denominator | REVIEW issue 11 · OPEN C3 · (d) adversarial F15 "**closed; attack disarmed**" | abstract L64: "accuracy 0.000, over the three pairs (n = 3)" |
| **X3** | The abstract drops "unplanned" from the Lean catch | OPEN §F · TRIAGE §D | abstract L71–72: "caught by a coverage probe and, **unplanned**, by the Lean transcription" |
| **X4** | §1.1's seal gloss said "both certify layers and the plan" where the file says "M4 and M5" | OPEN §F · TRIAGE §D | `01_intro.md` L53–54: "after M4 and M5 were green — M5 being the unsolvable-variant milestone, not a planning stage" |
| **X5** | `01_intro.md` cited "§7.1" for the sealed-pile record after renumbering | TRIAGE §D table | `01_intro.md` L125 now cites **§10.1** |
| **X6** | The abstract asserted the A0/A0′ contrast as controlled | TRIAGE issue 8 · (d) hostile §7.2 | abstract L69–71: "a design lesson demonstrated by construction rather than a hypothesis tested" |
| **X7** | A3's 252/252 reported without the control's identical 252/252 | REVISION applied item 1 · (b) methods B3 | abstract L100–102: "and so does the from-scratch control, so the saving is in what each arm cost and not in what either got right" |
| **X8** | "no benchmark game was played for any result here" was false | REVIEW blocking 2 · OPEN A2 | abstract L116: qualified to "No game was played *for* this paper" — but see **T6**, which attacks the adjacent sentence |
| **X9** | The two Lean files "differ in their weight table and in nothing else" | REVIEW blocking 1, closed `080f05d` · (d) adversarial "attacks I could not land" #2 | `01_intro.md` L79–82 carries the "*not* a minimal pair" correction |
| **X10** | Every §1 number checked against its artefact | (c) repro §3, claims 1–8 | all eight §1/§3 values **CONFIRMED**; 51 of 51 across the paper |

---

## 2 · The lay reviewer's five blocking findings, and the evidence each fix needs

Source: `review-e-lay.md` §2 and §3, restated in
`runs/20260729T031000Z-P13-paper-intro-abstract/BRIEF.md`, which adds: **"A
rewrite that does not fix 1–4 has not done this item, whatever else it
improves."**

---

**L1 · The paper never names its benchmark or environment (lay 2.1).**

> "A reader who does not already know what ARC-AGI-3 is — an interactive,
> multi-level, pixel-grid game benchmark — cannot situate a single number in §7 or
> §9. That is a one-paragraph fix and its absence is the largest single obstacle
> in the paper."
>
> "I spent §1–§8 unsure whether 'game' meant an ARC task, a Gym environment, or
> the authors' own toy worlds — and it means both, in different sentences,
> without warning (§6 uses 'the same game' for two levels of a self-built world;
> §7 uses '4 development-pile games' for real ARC tasks)."

*Evidence the rewrite needs:*
- A one-paragraph definition of ARC-AGI-3 as an object, **written without a
  citation** (OUTLINE red line 6 + REVISION: the benchmark is uncited and cannot
  be cited offline). Available uncontroversial facts already in the tree:
  `arc-recon/data/piles.json` (25 public games, the 4/21 cut, sha256
  `3feca53e…41bbc19a`); `arc-recon/README.md`; `CLAUDE.md`'s pile-cut section.
- A **disambiguation rule for the word "game"**, applied everywhere in §1 and the
  abstract: ARC games are the four development-pile ids; the A0/A0′/A2/A3 worlds
  are self-built. (a) domain m2 asks specifically that abstract (6) say
  "self-built world", citing `cold-start-a3/a3world/a3_world.py`.
- The exact scope sentence already in the tree, from `01_intro.md` L119–125 and
  `cold-start-a2/A2_REPORT.md` §7.

---

**L2 · The five arms are never enumerated, and "arm" is never defined (lay 2.2).**

> "Line 1297: '95 runs across 5 arms' — I cannot check any statement in §7
> against a population I cannot name."

*Evidence the rewrite needs:*
- The five arm names, from `battery/artifacts/capability_spectrum.json`, verified
  by (b) methods and (c) repro independently: `bare_cc` 80 runs, `schema_repro` 8,
  `theoria_a2` 4, `theoria_a0` 2, `theoria_a0_spike` 1 — 95 total (c) repro claim
  35: "**CONFIRMED** — `bare_cc, schema_repro, theoria_a0, theoria_a0_spike,
  theoria_a2`".
- One-line descriptions, already written and uncited, from
  `battery/PREDICTIONS.md`: `bare_cc` — "in weights, in the transcript; acts, then
  reconsiders"; `schema_repro` — "`world_model.py`, replay-level; a fitted
  simulator, no theorems" (lay §7).
- A sentence saying what "bare Claude Code" is (a commercial coding-agent
  product) and that Schema is another team's agent on another team's
  infrastructure — the abstract L118–120 already says the latter.
- The base caveat from (b) methods MINOR 2: seven of the 95 runs have
  `game_id: null`, and `discrimination_arms.json` uses `control_runs: 88`, so
  "95 runs" and "4 games" have different bases.

---

**L3 · The metric alphabet is private; K2 and K4 land in §1 six sections early
(lay 2.3).**

> "§7 is written in a private alphabet: K1–K14, X1–X4, P1–P5, E1–E7, M3, M6. Of
> roughly thirty ids used, I count **eight** that are ever glossed."

*Evidence the rewrite needs:*
- The id→name column from `battery/METRICS.md` ("a generated, complete glossary
  of all 38 metrics with their families and declared directions") and
  `battery/PREDICTIONS.md`'s readable names (`state_revisit_rate`,
  `novelty_frontload`, `actions_per_model_call`, `actions_per_call_trend`,
  `max_no_progress_streak`).
- For §1 specifically, only two ids are needed: K4 = evidence coverage over 7
  annotated clauses; K2 = held-out accuracy over 3 pairs with 0 agreements —
  both already verified in `battery/artifacts/capability_spectrum.json`, run
  `a0-base` ((c) repro claims 7 and 8, both CONFIRMED). The cheapest fix is to
  drop the ids from §1 and keep the names, or to gloss each once.
- If the rewrite promotes the battery audit (T11), it will need X3's status:
  `battery/PREDICTIONS.md` line 62 states X3 is "the signature prediction of the
  family", with the design's reasoning: "once the manual closes there is nothing
  left to be surprised by. A flat novelty curve means the theory never closed."
  (lay §7 and 6.6 — "the most consequential unclaimed finding in §7".)
- **Caution from BRIEF:** the battery's effect sizes are **unpaired** ((b)
  methods B2) and P3's two statistics disagree. The intro must not restate the
  old framing.

---

**L4 · The claim cannot be stated (lay §3).** See §3 of this file in full.

*Evidence the rewrite needs:* a decision, not data. BRIEF: "**The one thing to
decide before writing** … If the next holder disagrees, that disagreement is the
item — write it down rather than splitting the difference."

---

**L5 · §1's hook lands and §1 then dismantles it (lay §4).** See T10.

*Evidence the rewrite needs:*
- A statement of what "caring" consists of, placed **before** the disclosures —
  the lay reviewer's own diagnosis is that the caveats arrive "before ever
  explaining what 'care' would consist of", and that "the thing that would have
  kept me is the §7.7/§8.3 material, and nothing in §1 tells me it is coming."
- A relocation target for the four disclosures (see §4). The lay prescription is
  "Move every caveat to limitations", i.e. §10 — which already contains §10.1(b)
  (scale), §10.1(e) (no benchmark result), §10.3 (the theorize step), §10.4
  (post-dictions).
- (e) lay §5's other structural recommendation, which costs nothing and buys
  credibility: "**Move a compressed §11.3 to §1.** It would cost the paper nothing
  it can defend and would buy it enormous credibility."

---

## 3 · The claim problem

### 3.1 §10.5's own attempt, quoted verbatim

From `papers/phase1-workshop/sections/10_limitations.md` L236–253, under the
heading **"### 10.5 The one thing this paper claims"**:

> That the pipeline runs end to end on self-built deterministic worlds; that on
> those worlds a manual can be perfect on replay and wrong about the world in a way
> that was predicted in advance and later measured; that reversibility of a
> mechanism mattered more than breadth of trajectory in the one controlled
> comparison run; that a machine-checked impossibility can be produced whose
> weights crossed a data boundary between two independently developed tracks and
> whose empty axiom list is a check that has been made to fail on purpose; that the
> refutation loop closed on a false theorem in six recorded beats; and that a
> passive metrics battery over existing trajectories, once its anti-gaming register
> was made executable rather than written, contradicted 17 of its own register
> entries by demonstration — 14 of them defence claims
> (`battery/artifacts/gaming_audit.json`) — and found the exploration family's
> declared signature separating the specified gradient backwards.
>
> Everything else in `Theoria.md` — the ordering claim, the bill shape, transfer,
> the exam, the cost magnitude — is unevidenced here and is not claimed.

The lay reader's verdict on it:

> "§10.5 offers what looks like the authors' own version and it is **six
> independent clauses joined by semicolons**, spanning A0, A0′, A1, A2 and the
> battery. **That is a table of contents, not a thesis.**" — (e) lay §3

(a) domain §4 grades it clause by clause: clauses 1, 5, 6, 7 **earned**; clause 2
earned "with a caveat the clause hides" (should say "predicted by direction");
clause 3 **not earned, BLOCKING**; clause 4 **not earned as phrased, BLOCKING**.
(d) adversarial calls it "**the single worst paragraph in the paper**", for three
reasons at once, the third being: "It is quotable whole. A referee can paste
sixteen lines and say: *'The authors' own statement of their minimum claim is
simultaneously stronger than their body and weaker than their title.'*"

**Note for the rewrite:** §10.5 is not this item's file. But the abstract and §1
must not be written so that they contradict a §10.5 that a later item will fix,
and (d) hostile's remedy #1 is "**Rewrite §10.5 to the abstract's wording, not
above it**" — i.e. the abstract is currently the *reference* wording, which raises
the cost of loosening it.

### 3.2 The three competing candidate claims

Verbatim from (e) lay §3, "The problem is not that the paper has no claim. It is
that it has three candidate claims that pull against each other and never
resolve":

> 1. **The epistemic claim** (§1, and the title): replay-based validation is
>    structurally insufficient, and here is the exhibit. — Retracted in §11.3:
>    "this framework's own premise, not a finding… analytically guaranteed by the
>    construction… It is not evidence about anything."
> 2. **The systems claim** (§1.3, §4, §9): the pipeline exists, connects, crosses a
>    data boundary, and touches a live API safely. — Plausible and defended, but
>    never stated as *the* claim, and buried under (1)'s rhetoric.
> 3. **The negative-result claim** (§7.7, §8.3): we made our own evaluation
>    instruments adversarial and they mostly failed — 34/38 exploits still land, 17
>    register entries contradicted by demonstration, a leak checker whose hook was
>    optional and therefore silently did nothing on all four sheets. — This is,
>    to my eye, the most interesting and most transferable material in the
>    document, and it is claim number *five* in an eight-item abstract.
>
> A reader deciding in one hour needs to know which of these three is the paper.
> I finished not knowing.

The lay reviewer's own vote, from §8: "**Decide which of the three claims in §3
above is the paper. My vote is the evaluation-instrument negative result (§7.7 +
§8.3 + §7.4).**"

### 3.3 What each reviewer says the real contribution is

**The domain referee (a), §0:**

> "This paper's real contribution is **an instrument for making a specific failure
> mode of induced world models reproducible, plus an unusually severe self-audit
> of a measurement battery.** That is worth a workshop slot. But the paper is
> currently positioned as a *wave* in the world-model literature (§11.1,
> `PAPER.md:2388`), and on that framing it will be rejected, because the third
> wave it claims already has occupants it does not cite."

And on the abstract's own framing, §1.2:

> "**Yes — and it is the best decision in the paper.** The abstract's closing
> sentence ('The contribution is an instrument and a demonstration artefact …
> not a result about world models', `sections/00_abstract.md:122–124`) is exactly
> the right altitude for what §§3–9 contain. … **But the paper does not hold that
> altitude.**"

**The outside reader (e), §3:**

> "Here is the honest version of my attempt: *'We built an instrument for
> maintaining a world model as an explicit, machine-checkable theory; we ran it
> end-to-end on four small deterministic worlds we constructed ourselves, and
> report what broke.'*
>
> But that is a claim about an artefact, not a result, and the paper does not seem
> to want to settle for it."

**The convergence, from REVISION:**

> "**The structural recommendation both independent reviewers reached.** (a) and
> (e) never saw each other and converged: the executable anti-gaming register
> (§7.7) is the paper's widest daylight and is buried as item four of four; (e)
> independently proposed cutting the paper to §7.7 + §7.4 + §8.3. That is a
> restructuring decision about what the paper *is*, at ~24 600 words against a
> ~4 000-word budget. **It is the right next item** and it is not a revision-list
> line."

**The two other seats agree on the altitude, not on the emphasis.** (b) methods
§5: "The paper says exactly this at `PAPER.md:120–124` ('The contribution is an
instrument and a demonstration artefact … not a result about world models'), and
**that framing is correct and should not be softened.**" (d) hostile §5's counter:
"Strip the self-referential and what remains, in twenty-three thousand words, is:
*the code runs, end to end, on worlds we wrote, and we found a great many defects
in it.* That is a systems report."

**BRIEF's proposed join** (`runs/20260729T031000Z-P13-paper-intro-abstract/
BRIEF.md`):

> "**a paper whose subject is what a score cannot see should lead with the
> instrument that proved its own metrics gameable, not with the exhibit that
> proves a prover proves what it is told.** If the next holder disagrees, that
> disagreement is the item — write it down rather than splitting the difference."

---

## 4 · What a rewrite could accidentally break

Four things in the current `01_intro.md` (plus five in `00_abstract.md`) were put
there deliberately, each closing a named finding. A rewriter who reads them as
clutter and cuts them **reopens a closed blocking issue**.

---

**4.1 · The R-05 pre-registration precision — `01_intro.md` L42–51.**

Current text:

> "Be precise about what was named, because the precision is the whole argument.
> R-05 names three **directions** — `press_up`, `press_down`, `press_right` — and
> one concrete configuration, 'drive the Cart to (2,2) and push DOWN into an
> unpressed Button'. It does not enumerate the coordinate pairs; the phrase 'the
> three pairs R-05 named' appears in `THEORIZE_LOG.md`'s seal section and
> `A0_REPORT.md` §2, both written at M6 *after* the score existed, **and this paper
> does not inherit that gloss as if it were the pre-registration.**"

**Why it is there.** It closes REVIEW.md blocking issue 4 = OPEN_ITEMS A3 =
REVIEW_TRIAGE issue 4, which TRIAGE ranks **first** in its "what should the next
pass do" ordering:

> "**Issue 4** (R-05 'three pairs'). One sentence, and it is the sentence that
> converts an anecdote into evidence for the seal. `W`." — TRIAGE §F(1)

> "R-05 names three *directions* and one cell; the 'three pairs' gloss was written
> at M6, after the score existed. This is the sentence that turns an anecdote into
> evidence for the seal — it is writing, but it is **the most load-bearing writing
> in the paper**." — TRIAGE §A(4)

**What is lost by cutting it.** The paper reverts to claiming a stronger
pre-registration than the log supports, on the one number the entire hook rests
on. (b) methods §4 calls the passage "**exemplary … Keep it**". (a) domain §4
requires the *reverse* direction of travel — §10.5's clause 2 should adopt the
intro's precision ("The clause should say 'predicted by direction'"), so the
intro is the reference text. Any shortening must preserve: (i) three
**directions**, not pairs; (ii) that the "three pairs" phrase is an M6 gloss;
(iii) that the paper declines to inherit it; (iv) the surviving claim — "R-05
named the three directions, predicted the manual would be wrong on them, and
predicted that replay would not notice. All three held."

---

**4.2 · The seal hole — `01_intro.md` L61–66.**

Current text:

> "The seal has a hole, and the log names it rather than hiding it: **the same
> instance both built the A0 world at M1 and adjudicated it at M3**
> (`cold-start-a0/THEORIZE_LOG.md`, preamble). No ground-truth file was read, and
> every verdict is written to be re-derivable from the candidate stream alone, but
> `cold-start-a0/A0_REPORT.md` §6.3 counts this as a threat to the result rather
> than a footnote, and this paper carries it the same way."

Together with L57–59:

> "That stamp is a declaration written by the authors' own script, not a control:
> the only thing that could make it auditable is git history, which this paper does
> not appeal to."

**Why it is there.** OPEN_ITEMS C7 ("The ground-truth seal is not auditable …
state plainly that it is a declaration and not a control"). It is also the paper's
pre-emption of (d) hostile §3.1 and (d) adversarial kill shot 5 — the single
attack both hostile seats rate highest on circularity. (d) adversarial's inventory
of self-authored ground truth cites **this exact sentence** as the paper's
disclosure for §3.

**What is lost by cutting it.** The disclosure stops being the authors' and
becomes the referee's. (d) hostile's whole §3 is "the pre-registration is a
self-timestamped file"; the current text concedes it in advance, which is the only
reason that attack is scored as disclosed rather than concealed. And (e) lay
6.8's list — "Each disclosure is admirable in isolation" — is the *cost* of
keeping it, not a reason to cut it. **If it moves to §10, the abstract must not
then assert the seal flatly (T13); the two are a package.**

*Upgrade available, not a deletion:* (b) methods M1's git finding — M3 and M6 are
62 seconds apart and corroborate nothing, while the battery's pre-registration
*is* corroborated by commits `19eafb2`/`82a6925` and `58e5f6b`/`5f85971`. "Say
that, rather than declining git wholesale."

---

**4.3 · The "not a minimal pair" correction — `01_intro.md` L79–82.**

Current text:

> "The two files are *not* a minimal pair — §5.6 corrects the source report on that
> point and says what the correction costs — but they do not need to be. Identical
> provenance and an identical empty axiom list, on one theorem that holds of the
> world and one that does not, is the whole demonstration."

**Why it is there.** It closes REVIEW.md **BLOCKING issue 1**, recorded in TRIAGE
§A(1) as "**closed** `080f05d` … the diff also touches `def Goal` and four `step`
entries; verified still closed". (d) adversarial lists it under "attacks I tried
and could not land":

> "**'Your two headline Lean files are not a minimal pair.'** Disarmed at
> `PAPER.md` L1014–1047 … which corrects its *own source report*, runs the diff,
> lists all 52 changed lines by kind, states what is lost … This was `REVIEW.md`'s
> blocking issue 1 and it is comprehensively closed."

**What is lost by cutting it.** The intro reasserts, uncorrected, the false
statement that a prior audit already blocked on — and (d) hostile 2.9 already
treats the paper's `DECISIONS.md` false records as evidence of a **base rate**
("two `DECISIONS.md` entries were checked adversarially and both were false").
Reintroducing this one converts a closed blocking issue into confirmation of that
base rate.

*Live tension:* (e) lay 6.1 and (d) hostile §7.1 argue the abstract should not
lead with the pair at all (T3). Demoting it is fine; asserting it *without* the
correction is not.

---

**4.4 · The scope-limit paragraph — `01_intro.md` L119–132.**

Current text (opening): "**Scope limit, stated here rather than deferred.** Every
pipeline result in this paper — A0, A0′, A1, A2 — was produced offline, on small
deterministic worlds this project built itself; no game was played for it and no
network was touched (`cold-start-a2/A2_REPORT.md` §7)."

It carries five distinct disclosures in fourteen lines:
1. offline, self-built worlds, no game played, no network — `A2_REPORT.md` §7;
2. the battery is passive, spends nothing new — `battery/REPORT_V2.md`;
3. no sealed-pile game played or read **and** the pointer to §10.1's contamination
   record;
4. "the theorize step is not a measured language-model step … 'A2 tests the
   instrument and the loop, not the theorizer.'" — `A2_REPORT.md` §8;
5. the forward pointer: "Section 7 collects the rest of the limitations; none of
   them are discovered there for the first time, because each acceptance report
   already states its own." *(note: this cross-reference is stale — §10 is
   limitations now, §7 is the battery; TRIAGE §D fixed five such and missed this
   one.)*

**Why it is there.** It is the intro-level instantiation of OUTLINE **red line
2** ("No experiment, no 'we show'. Anything not actually run is written as a
limitation or is absent") and of the paper's best-graded quality. (a) domain §5:

> "**Mostly yes, and conspicuously so.** … This is better than the field norm by a
> wide margin, and I want to say so before listing the sentences that leak."

Item 4 (the theorize step) is what (d) adversarial F19 identifies as the paper's
only defence against the missing-LLM-baseline attack, and what (d) hostile §5
lists among the concessions the paper does make. Item 3's contamination pointer is
the fix for (e) lay 6.9 landing in the intro.

**What is lost by cutting it.** Every one of the five disclosures becomes an
undisclosed overclaim, and three of them are attacks the hostile seats explicitly
withdrew *because* they are disclosed. The lay reviewer's complaint is about
**placement and volume** — "a 14-line 'Scope limit, stated here rather than
deferred' that removes essentially every generalisation the reader has just
formed" — and the prescription is "Move every caveat to limitations", not delete.
**If it moves, §10 must gain all five, and the stale "§7" cross-reference should
be corrected to §10 on the way.**

---

**4.5 · The abstract's penultimate paragraph — `00_abstract.md` L114–121.** (a)
domain §5, closing:

> "The abstract's penultimate paragraph ('We claim none of the framework's
> comparative results … **None is across the framework's own arms**') is
> **exemplary and should be kept verbatim**."

Caveat: T6 attacks its first sentence ("No arm was run against a baseline"), and
(d) adversarial F4 notes "None is across the framework's own arms" is "as written
… now false" for §6. Fix those two sentences; keep the paragraph.

**4.6 · The abstract's closing sentence — `00_abstract.md` L123–125.** "The
contribution is an instrument and a demonstration artefact … not a result about
world models." (a) domain: "exactly the right altitude … the best decision in the
paper". (b) methods §5: "**that framing is correct and should not be softened**".
(d) hostile §5: "`PAPER.md:124–126` gets closest". Three of five seats defend this
sentence. **Do not soften; consider moving it earlier** — (d) adversarial's
minimal edit for T2 is "move the abstract's own closing paragraph to sit
immediately after the list."

**4.7 · "(n = 3)" — `00_abstract.md` L64.** (d) adversarial F15: "**Closed.
Attack disarmed** … **Noted so the fix is not lost in a future trim.**"

**4.8 · "unplanned" — `00_abstract.md` L71–72**, and "a design lesson
demonstrated by construction rather than a hypothesis tested" — L69–71. Both are
applied fixes ((d) hostile §7.2 credits the second explicitly).

**4.9 · The declared exemption of the abstract from the path rule —
`00_abstract.md` L36–38.** "The abstract is the one exemption, by convention —
each figure in it is cited where it recurs in the body." (d) hostile §8, "attacks
I tried that failed": "**The abstract's exemption from the path rule.** Declared
up front at `PAPER.md:36–39` and each figure recurs cited in the body.
**Legitimate.**" The lay reviewer wants the whole draft-status block deleted
(T21) — if it goes, this declaration must be preserved somewhere, or every
unpathed number in the abstract becomes a red-line-1 violation. **And the
exemption is conditional: it only holds while each abstract figure recurs cited in
the body**, which (b) methods B4 shows is currently false for result (8).

---

## 5 · Red lines the rewrite must respect

**From `OUTLINE.md` §"Red lines, binding on every section":**

> 1. **Every number points at a file in this tree.** Cite with a repo-relative
>    path, e.g. `cold-start-a0/artifacts/score_vs_truth.json`. A number with no
>    path does not go in.
> 2. **No experiment, no "we show".** Anything not actually run is written as a
>    limitation or is absent. In particular: nothing about DC22, nothing about ARC
>    play, nothing about scale, nothing about an LLM writing the manuals.
> 3. **No report text is edited.** The four acceptance reports and `REPORT_V0.md`
>    are read-only sources. Quote them; do not revise them.
> 4. **Authorship is a placeholder.** No real names, no affiliations.
> 5. **The sealed pile is not touched.** The only sealed-pile statement permitted
>    is the INC-004 caveat, cited from `arc-recon/README.md` and
>    `cold-start-a2/A2_REPORT.md` §1.
> 6. **A bibliographic record that could not be cross-verified against two
>    independent sources is not cited.** Not softened, not hedged — absent.

Red line 6 is the reason (a) domain's whole missing-literature list — Chollet /
ARC-AGI, EMPA, Schema Networks, DreamCoder, Voyager, Popper, Daikon, Card et al.
— **cannot be actioned here**. REVISION:

> "**They cannot be added in this session, and adding them would be worse than
> leaving them.** … this session has no network. Citing from memory is exactly the
> failure the rule exists to prevent, in a section whose value is that it did not
> do that. Escalated instead: it needs a session with browsing, or OPS-B."

**From `README.md`:**

> "| `PAPER.md` | **generated** — do not hand-edit |"

Rebuild: edit `sections/00_abstract.md` and `sections/01_intro.md`, then
`python papers/phase1-workshop/assemble.py`. (c) repro verified this is
deterministic and that the committed `PAPER.md` is currently in sync with
`sections/*.md` (§5: two consecutive assembles gave sha256
`500867cdb66e38a2…`, "byte-identical to committed").

**From `BRIEF.md`, constraints specific to this item:**

> "Every number carries its artefact path (`sections/00_abstract.md` front matter
> states the rule; the abstract is the one declared exemption, **so the *intro* is
> not exempt**)."
>
> "**Three numbers changed under P11/P12 and the intro must not restate the old
> ones**: the A3 transfer result is a *cost* result, not an accuracy one (both arms
> score 252/252); the battery's effect sizes are unpaired and P3's two statistics
> disagree (§7.2a); 'four offline acceptances' is three plus an early read on C3."

**From the abstract's own front matter (`00_abstract.md` L34–43), which the
rewrite is bound by and may relocate but not silently drop:**

> "**The binding rule.** Every quantitative claim in the body carries the
> repo-relative path of the artefact it came from; `papers/phase1-workshop/
> PROVENANCE.md` is the index. The abstract is the one exemption, by convention —
> each figure in it is cited where it recurs in the body."
>
> "Their findings were applied, and both files are kept unedited — including the
> parts that are unflattering — so a reader can see what the rule caught."

**From `CLAUDE.md` (repo-wide):** work stays inside this worktree
(`.worktrees/p13-paper-intro-abstract/`); every run writes
`runs/<id>/MANIFEST.json` with `prompt_id`, `branch`, `base_commit`, `utc`; never
`git add -A` at the repo root; the pile cut is binding and reading about a sealed
game is an incident.

**One process red line, from `REVISION.md`, that governs how these findings may be
used:**

> "**Nothing here was actioned on a reviewer's word.** Every finding below was
> re-derived from the artefact before the paper was touched, and three were refuted
> that way."

Three P12 findings were refuted on checking — the six-broken-figure-paths finding
(lay 2.6/§7), "zero ARC-AGI citations" (nearly right: exactly one record,
`zeng2026schema`, and it cites the harness not the benchmark), and a stale
Figure-1 decision count. Treat the list above the same way.
