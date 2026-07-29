# Review E — the outside reader

**Seat:** competent CS researcher, does not work on this project, has never read
`Theoria.md`, knows world models / program synthesis / ITP at the level of a
well-read practitioner. One hour. Deciding whether this paper is worth my
attention.

**Protocol followed:** read `papers/phase1-workshop/PAPER.md` top to bottom, in
order, looking nothing up. Confusions recorded as they happened. Only after
finishing did I check whether the answers existed elsewhere in the tree; that
check is quarantined in §7 below so it cannot contaminate the reading record.

**Bias disclosure for the chair:** I am the reviewer least able to tell you
whether the work is *right*. I can only tell you what a stranger takes away in
an hour. Where I say "I did not believe X", read it as "the paper did not
make me believe X", which is a writing verdict, not a truth verdict.

---

## 1 · What I thought this paper was, after §1 — written before reading on

Verbatim from my notes at the §1/§2 boundary:

> This is about world models for agents. The pitch: everyone checks a learned
> world model by replaying the agent's own recorded history, and that check is
> broken, because a model can replay every frame it has ever seen and still be
> wrong about transitions the history happens not to contain. The authors'
> alternative is to write the world model as an explicit human/LLM-readable
> "theory" — two documents, a "manual" (facts) and a "playbook" (strategy) —
> compiled into Lean/Python/PDDL/Markdown, so that claims about the world become
> theorems you can machine-check rather than curves you can eyeball.
>
> The demonstration is a 9×9 toy world ("A0") they built themselves. Their
> induced model replays 276/276 frames and 22,356/22,356 pixels perfectly, and is
> wrong on 3 of 236 possible (state, action) pairs — and, crucially, they wrote
> down *which* three it would be wrong on before they looked. There is a second
> exhibit ("A2") where a rule is deleted, the system proves an impossibility
> theorem in Lean with no axioms, and the theorem is false — an 18-move solution
> exists. So: a real proof of a false thing, because the specification was wrong.
>
> Claim, as I have it: **replay-based validation of world models is
> insufficient in a specific, demonstrable way, and here is a machinery that
> makes the insufficiency visible and then repairs it.**
>
> Open questions I expect answered: what is the actual system, how much is
> automated vs. hand-written, does this scale past 59 states, and — the obvious
> one — is any of this better than a baseline?

**How far off was I?** On the *topic*, close. On the *claim*, badly off in one
direction and correctly suspicious in another.

Off: I read §1 as promising that the two-book/Lean machinery is the answer, and
that the paper would show it working. It does not. By §10.5 the paper's actual
position is that no comparison of any kind was run, the "theorize" step — the
one place an LLM would do the interesting work — was performed by hand and
checked in as a file, and every world is small enough to brute-force. §11.3 then
volunteers that the A2 exhibit is "analytically guaranteed by the construction"
and "not evidence about anything". Had I known at §1 that the paper's own last
page retracts the emphasis of its first page, I would have read §1 completely
differently.

Correctly suspicious: my "is any of this better than a baseline?" was answered
"no baseline was run", which the abstract does say — but says in the *last*
paragraph, after eight numbered results have already landed.

The thing I did not anticipate at all: this is not one paper. It is seven
loosely-joined reports (A0/A0′, A1, A2, A3, battery, exam, preflight) with a
shared limitations chapter. Nothing in §1 prepares you for that; §1.3 lists four
contributions and the paper delivers seven sections of results, three of which
(§6 exam-adjacent transfer, §8 exam, §9 preflight) are not in the contribution
list at all.

---

## 2 · Where exactly I got lost

Ordered by where it hurt, with the passage.

### 2.1 Blocking — I never learned what benchmark or environment this is about

The paper never introduces its problem domain. "ARC" first appears at line 1918,
**inside a code fence**, in §9:

> `arm -> env proxy -> key injection -> sealed-pile guard -> ARC -> ledger`

and then at §10.1(e) as "ARC trajectories". "ARC-AGI-3" is named exactly once,
in §11.1, at line 2371, on page ~22. Yet from the abstract onward the paper
leans on "games", "the sealed pile", "the development pile", "levels",
"scorecard", "the real API", "quota", "the referee". I spent §1–§8 unsure
whether "game" meant an ARC task, a Gym environment, or the authors' own toy
worlds — and it means both, in different sentences, without warning (§6 uses
"the same game" for two levels of a self-built world; §7 uses "4
development-pile games" for real ARC tasks).

A reader who does not already know what ARC-AGI-3 is — an interactive,
multi-level, pixel-grid game benchmark — cannot situate a single number in §7 or
§9. That is a one-paragraph fix and its absence is the largest single obstacle
in the paper.

### 2.2 Blocking — the arm names, and the term "arm" itself

"Five arms" is load-bearing throughout §7 and the five are **never enumerated**.
I collected, by scavenging: `bare_cc`, `schema_repro`, "the model ladder"
(which may be a sub-split of `bare_cc` rather than an arm), "the S1 campaign
shards", "the Theoria arm", "the ablation arm". That is six candidate names for
five slots and I could not resolve it. Line 1297: "95 runs across 5 arms" — I
cannot check any statement in §7 against a population I cannot name.

"bare Claude Code" (abstract, line 119) is used as if it were a standard
baseline. It is a commercial coding-agent product. It needs a sentence.

"Schema" is introduced at line 119 as a control arm and not explained until line
2370. In between it carries six pages of effect sizes.

### 2.3 Blocking — the metric identifiers

§7 is written in a private alphabet: K1–K14, X1–X4, P1–P5, E1–E7, M3, M6. Of
roughly thirty ids used, I count **eight** that are ever glossed, and most of
those in passing (P1 "actions per model call", E2 "front-load index", E5 "cost
per action", K2 "held-out accuracy", K4 "evidence coverage", X3 "novelty
front-loading", P4 "`ok_steps / optimal`", K12 "six self-reported booleans").
The rest are never defined anywhere in the paper.

Concretely, the table at lines 1346–1355 — the central empirical table of §7 —
has a `family` column and an `id` column and no `what it measures` column. I
read eight effect sizes without knowing what four of them are effects *on*.

K2 and K4 are worse than that: they are dropped into **§1**, at line 152, six
sections before §7.4 explains them.

### 2.4 Major — "acceptance", "arm", "track", "beat", "register", "tier", "pile", "referee", "the mandate", "the claim menu"

Project vocabulary presented as standard. The worst offenders:

* **"acceptance"** — in the subtitle ("three offline acceptances"), the abstract,
  and §1, meaning something like a pre-declared gate condition. Not explained
  until §2.5 at line 371, ~2,400 words in. On first read I parsed it as
  "acceptance test" and then as "paper acceptance" and got both wrong.
* **"track"** — three incompatible senses. (a) an agent session / development
  team (§4.2, "two tracks"); (b) an object trajectory in segmentation (§3.2, "90
  tracks", "3 tracks"); (c) "multi-track CEGIS" (§3.1), which I still cannot
  place. Sense (b) and sense (a) appear four lines apart in §3.
* **"beat"** — a step of the repair loop. Used in the abstract ("closes in six
  recorded beats") long before §5.5 shows what one is.
* **"register" / "tier" / `main` / `reference`** — a whole governance apparatus
  for metrics, used from line 93 (abstract) and never described as a system;
  §7.7 explains one part of it retroactively.
* **"the mandate"**, **"the claim menu"**, **"claim C2 / C3 / C5"** — these
  denote sections of a document I do not have. C3's actual content is given
  **only in untranslated Chinese** (see 2.5).
* **"the referee"** (§6) — I inferred "ground-truth simulator" from context.
* **"sealed pocket"** (§5.6, line 1006) versus **"sealed pile"** (everywhere).
  Two unrelated meanings of "sealed", one paragraph apart in a table.

### 2.5 Major — untranslated Chinese carrying content I needed

The paper glosses *most* Chinese, which makes the ungloassed instances more
jarring, not less. Untranslated and load-bearing:

* **Line 382–383** — the quote from `Theoria.md` that is the entire justification
  for this paper existing ("Phase 1 结:A0–A2 + 电池对既有轨迹的回算,独立可成
  workshop 文"). The one sentence that says what this document is *for* is in a
  language the sentence around it is not.
* **Lines 707, 709** — inside the §4.2 pipeline diagram: "数据文件为界，不 import
  对方代码" and "不信 verified 标志，全部义务重新验算". These are the annotations
  that explain what the data boundary *is*. The prose nearby paraphrases them,
  but a reader looking at the diagram gets nothing.
* **Line 819–822** — the whole `Theoria.md` A2 specification, quoted in Chinese
  with **no translation**, four paragraphs after §4.1 sets the precedent of
  translating exactly this kind of quote. §5 then spends six pages on how what
  was run differs from it. I could not check the difference claim because I could
  not read the original.
* **Line 1091** — claim C3 itself: "携两本书跨关，第二关边际成本 ⟨≪⟩". §6 is the
  test of C3. Its statement is untranslated.
* **Line 1290** — "同一本账,两次使用", the design rationale opening §7.
* **Line 761** — "独立复核".
* **Line 1339** — "`⟨复现值⟩` cell".

I have no objection in principle to quoting a Chinese-language design document.
I object to a paper that translates two thirds of them and leaves the other
third, with no visible rule, so the reader cannot tell whether an untranslated
phrase is unimportant or is the one that matters.

### 2.6 Major — three figures that are cited but not present

§3.1, §3.3 and §5.5 cite **Figure 1**, **Figure 2** and **Figure 3** and describe
what they show at length (lines 421–437, 497–504, 938–944). There is no figure in
the document — no image, no embed, no ASCII rendering, nothing. What is given
instead is a script path, an SVG path and a CSV path.

The description-in-lieu-of-figure passages are long and unreadable without the
plate. Line 421 spends a paragraph on "seventeen decisions with their verdicts,
one probe designed and never ruled on, the manual's two revisions with their
triggers, the three compiler defects, and the expressivity ledger" and then a
second paragraph on a disagreement between two implementations of the figure
script about whether the count is 17 or 18. I cannot see either.

(After-the-fact check in §7 below: the cited paths do not exist.)

### 2.7 Major — numbers whose denominator or unit I could not infer

* **"a score of 98.98 on replayed history"** (line 137, §1, third sentence). 98.98
  of what, on what, by whom? This is the paper's *hook* and it is the number I
  understood least. It turns out (§11.1, line 2378, twenty pages later) to be a
  prior system's self-reported percentage on a public set. At §1 I could not tell
  if it was this project's own result.
* **"Per-object accounts ... Cart +2967, Button −17, Door −13"** (§3.6, line
  636). Units never stated. I inferred "bits" from "a 21-bit declaration" two
  lines later, but +2967 bits for a cart on a 9×9 board did not obviously make
  sense to me.
* **"Script bits: 6511 vs 4423"** (§3.2) — same problem, plus an immediate
  parenthetical saying the artefact now reports 5704 over 6 tracks instead, and
  that the paper is deliberately quoting the *superseded* number. I could not
  work out whether the finding survives its own correction.
* **"1 433 computed values ... 2 066 metric slots `not-applicable` and 111
  `insufficient-data`"** (§7.1). 1433 + 2066 + 111 = 3610, and 95 runs × 38
  metrics = 3610. That checks — but I had to do the arithmetic myself to
  discover that these three partition one grid, and the fact that **57 % of the
  grid is not-applicable** is never commented on.
* **"K2 = 0.000 over 3 adversarial gaps and a0-spike's K2 = 1.000 over 39 960
  exhaustive cases"** (§7.4). Two numbers five orders of magnitude apart,
  presented in one clause, described as "non-comparable" — which is right, and
  is exactly why putting them in one sentence confused me.
* **"0 %" clause agreement rising to "all 20 ... once canonicalised"** (§6.4).
  "Canonicalised" is doing all the work and is never defined. 0 % → 100 % under
  an unspecified normalisation is not a measurement I can interpret.

### 2.8 Minor but constant — the citation format makes the prose unreadable

The binding rule (every number carries its artefact path) is defensible as
policy and is disastrous as typography. Representative sentence, §3.3:

> A0's three errors are not scattered: they are the Button pressed from above,
> from below and from the right (`cold-start-a0/artifacts/score_vs_truth.json`,
> whose `base.behavioural.accuracy` is `0.987288`).

Sentences routinely carry two or three inline monospace paths of 40+ characters.
I estimate 8–12 % of the body's word count is repo paths inside running prose.
The rule can be kept and the cost removed by moving paths to numbered endnotes or
to `PROVENANCE.md` (which the paper says already exists).

### 2.9 Minor — "paper" collides with "paper"

§8 calls the exam's four question types "papers": "Three of its four papers have
never been sat" (abstract, line 111). I read that as a statement about
publications and had to reread. §8's own title — "four papers, one sat" — has
the same problem. Rename to "sheets" or "sections" or anything else.

### 2.10 Minor — an apparently damaged sentence in the abstract

Lines 94–97:

> and the exploration
> family's declared signature separates the
> one gradient the design specifies *backwards*.

The ragged mid-clause line break plus the placement of "backwards" makes this
garden-path badly; on first read I parsed "specifies backwards" as a unit. It
recurs, better, at line 1386. Suggest: "…and the exploration family's signature
metric separates the design's own specified gradient **in the wrong direction**."

### 2.11 Minor — arms A0, A0′, A1, A2, A3 introduced out of order and unevenly

A0/A1/A2 are used in the abstract, defined in §2.5. A0′ is used in §1.3 and
introduced in §3.3. A3 is used in the abstract's result (6) without the label,
and is defined in §6 as testing a claim (C3) whose statement is untranslated.
`a0-spike` — a *fourth* cold start on a *different* world by the *other* track —
arrives in §3.5 and its numbers then reappear in §7.4 as if familiar. At that
point I was tracking five world-instances (A0, A0′, a0-spike, A2's world, A3's
L1/L2) and I lost which was which more than once.

---

## 3 · The paper's actual claim, in one sentence

**I cannot state it confidently, and I think that is the single most useful thing
in this review.**

Here is the honest version of my attempt: *"We built an instrument for
maintaining a world model as an explicit, machine-checkable theory; we ran it
end-to-end on four small deterministic worlds we constructed ourselves, and
report what broke."*

But that is a claim about an artefact, not a result, and the paper does not seem
to want to settle for it. §10.5 offers what looks like the authors' own version
and it is **six independent clauses joined by semicolons**, spanning A0, A0′, A1,
A2 and the battery. That is a table of contents, not a thesis.

The problem is not that the paper has no claim. It is that it has three
candidate claims that pull against each other and never resolve:

1. **The epistemic claim** (§1, and the title): replay-based validation is
   structurally insufficient, and here is the exhibit. — Retracted in §11.3:
   "this framework's own premise, not a finding… analytically guaranteed by the
   construction… It is not evidence about anything."
2. **The systems claim** (§1.3, §4, §9): the pipeline exists, connects, crosses a
   data boundary, and touches a live API safely. — Plausible and defended, but
   never stated as *the* claim, and buried under (1)'s rhetoric.
3. **The negative-result claim** (§7.7, §8.3): we made our own evaluation
   instruments adversarial and they mostly failed — 34/38 exploits still land, 17
   register entries contradicted by demonstration, a leak checker whose hook was
   optional and therefore silently did nothing on all four sheets. — This is,
   to my eye, the most interesting and most transferable material in the
   document, and it is claim number *five* in an eight-item abstract.

A reader deciding in one hour needs to know which of these three is the paper.
I finished not knowing.

---

## 4 · Is §1 persuasive?

**The hook lands. The section does not.**

Lines 135–142 are the best writing in the paper. "A world model can replay every
frame of its own history without a single error and still be bankrupt as an
account of the world" is a good sentence, and 276/276 frames + 22,356/22,356
pixels + accuracy 0.000 on the three held-out pairs is a genuinely arresting
juxtaposition. §1.1's "the miss was written down before it was measured" is
exactly the right move and I believed it.

Then §1 spends the rest of itself dismantling its own hook, and I think this is
the central craft failure of the paper:

* Line 190: the pre-registration seal "is a declaration written by the authors'
  own script, not a control".
* Line 193: "The seal has a hole… the same instance both built the A0 world at
  M1 and adjudicated it at M3".
* Line 176: the phrase "the three pairs R-05 named" is disowned as a later gloss.
* Line 211: the headline Lean pair is "*not* a minimal pair".
* Lines 251–264: a 14-line "Scope limit, stated here rather than deferred" that
  removes essentially every generalisation the reader has just formed.

Each of those is individually honest and I respect all of them. Collectively,
they mean that by line 264 the paper has told me: the finding was constructed,
the pre-registration is self-attested, the exhibit is not minimal, nothing was
played, and the LLM step was done by hand. **A reader who is not being paid stops
here.** Not because the work is bad — because the paper has just spent 130 lines
explaining why they shouldn't care, before ever explaining what "care" would
consist of.

Would I keep reading unpaid? Honestly: I would read to the end of §1 and then
skim to find a comparison table, find none, and close it. The thing that would
have kept me is the §7.7/§8.3 material, and nothing in §1 tells me it is coming.

Two smaller §1 problems:

* The **draft-status block** (lines 12–45) sits between the title and the
  abstract and is 500 words of internal version history — v0.2, v0.3, section
  renumbering, `OPEN_ITEMS.md`, `REVIEW_TRIAGE.md`, `CITECHECK.md`,
  `PROVENANCE.md`, "roughly five times a workshop budget". Whatever its value to
  the team, to an outside reader it is a 500-word notice reading *this is not
  finished*, placed before the first sentence of content. It must not survive
  into anything sent to a venue.
* **DC22** (line 219) is used with no explanation, in a sentence explaining that
  the paper's second exhibit reproduces "the structural shape `Theoria.md` §1.3
  describes under the name DC22". I could not tell whether DC22 was a game, a
  failure mode, a decision id, or a section. (§5.1 eventually says it is a sealed
  game; §1.2 does not.)

---

## 5 · Structure and length — what I would keep at 4,000 words

23,667 words by `wc -w`, against a stated ~4,000 budget. That is not a paper that
needs cutting; it is three or four different papers sharing a file. My advice is
therefore not "trim" but "choose".

### The choice I would make

**Publish the evaluation-instrument negative result.** §7.7, §7.4, §7.10 and §8.3
together are a coherent, self-contained, genuinely novel-feeling workshop paper:
*we built a metrics battery and an exam for agent world models, then attacked
them ourselves; here is what survived.* The findings that carried for me —

* an anti-gaming register that is *prose* is a register that lies: made
  executable, 34 of 38 exploits still land and 17 written entries were
  contradicted by their own demonstration;
* "K4 must never be reported without K2 beside it" — evidence coverage rewards
  exactly the caution held-out accuracy punishes, demonstrated on one manual;
* an **optional** hook meant two of five leak checks silently did nothing on all
  four sheets, and "it fails in the direction that looks like success";
* a single empty manual holds 19 of 20 epistemic/mechanism metrics at their best
  reading simultaneously;
* the honest power floor: a two-sided sign test over four paired games has a
  smallest attainable *p* of 0.125, stated up front and emitted on every run.

— are useful to anyone building agent evaluations, require no belief in the
Theoria framework at all, and are not analytically guaranteed by their own
construction, which is more than the A2 exhibit can say.

That is ~3,000 words, plus ~600 of framing and ~400 of related work.

### If instead the framework must be the paper

Keep, in this order and this budget:

| keep | § | words | why |
|---|---|---|---|
| The hook, cut to 3 paragraphs | 1 | 400 | 276/276 + 0.000 + R-05 written first. Stop there. Move every caveat to limitations. |
| What the system is | 2 | 600 | Two books, four forms, engines-propose/LLM-adjudicates, the two certify layers. This is the only section a stranger can't proceed without. Add: what ARC-AGI-3 is, one paragraph. |
| A0 vs A0′ | 3.1, 3.3 | 700 | The one table (line 506) is the clearest artefact in the paper. Keep the analytic-entailment admission — it is short and it is the honest framing. |
| The A2 exhibit | 5.3, 5.6 | 600 | Two Lean files, one true one false, identical axiom list. Keep §5.6's correction. |
| The battery's self-audit | 7.4, 7.7 | 700 | See above. |
| Limitations, compressed | 10 | 400 | Six bullets, not 2,500 words. |
| Related work | 11.1, 11.3 | 600 | §11.3 in particular. |

### What I would drop entirely, and why

* **§9 (preflight), ~1,900 words.** A run that sent zero actions and proved the
  credential path works. This is release-engineering evidence. It belongs in a
  repository STATUS file. The three incidental findings (18 retries for one
  RESET; no `score` field in live responses; close needs two tries) are API bug
  reports.
* **§6 (A3 transfer), ~1,900 words.** Interesting, but §6.5 lists six caveats
  that between them remove the result: the levels share all four mechanisms by
  construction, three level constants were handed to every arm, the denominator
  (a 100 % sweep) is admitted to be an upper bound and not realistic, and the
  playbook — half the "two books" — is "declared" rather than measured because
  no code path reads it. A ratio of 0.029 against a strawman denominator is not
  a workshop result.
* **§8 (exam), ~1,900 words** — *except* §8.3, which I would promote. Three of
  four sheets have never been sat; the fourth saturated at 46/46 on both tiers,
  and the section itself says the zero delta "is not a measurement". §8.5's
  finding about a `[status: proven]` invariant that is false on most boards is
  worth two sentences somewhere.
* **§4 (A1), ~1,300 words.** One 5-cell peg-solitaire fixture, and §4.5 concedes
  "the pipeline's generality is not supported by this evidence". Compress to a
  paragraph inside §2: *the compiler refuses to generate rather than narrowing a
  theorem it cannot certify*, which is the one genuinely admirable behaviour
  here, and is one sentence.
* **§10, ~2,500 words.** Almost entirely a restatement of caveats already made
  in §§3–9, plus §10.2, which corrects the repository's own `CLAUDE.md`. Nothing
  addressed to a reader.
* **The draft-status block, ~500 words.** Delete.
* **All internal identifiers.** R-05, T-6, T-8, T-9, T-10, O-01, O-04, L-02,
  E-01…E-06, D-014, D4, D-TC-008…013, D-A2-001…010, D-B-001…019, D-P8-002/004,
  INC-004, INC-BA-001/003, INC-TA-001/002/005, GAP 1, W-1, W-4, F-01, F-11,
  M1…M9, P-03, A3-I1. I counted well over sixty distinct opaque identifiers.
  Each is a lookup a reader cannot perform. They can all become prose.

### Sections that earn their space as written

§11 is the best-executed part of the paper and I would cut it least. §11.2's
per-neighbour positioning is careful, correctly hedged, and tells me exactly
where the work sits (potential heuristics, pagoda functions, version spaces,
action-model learning, proof-carrying code, specification mining). §11.3 is
worth more than any other page — it is where an author names, unprompted, the
two places the paper restates something the literature owns. Move a compressed
§11.3 to §1. It would cost the paper nothing it can defend and would buy it
enormous credibility.

---

## 6 · What I did not believe

Not "what is wrong" — I cannot check that. These are the places my instinct said
*too strong* or *does not follow*.

**6.1 — "The instrument cannot tell them apart, and is not supposed to."**
(abstract, §1.2, §5.6.) This is the headline artefact and I do not think it is a
finding. That a proof assistant will certify a theorem about a wrong model is
the definition of what a proof assistant does; no formal-methods reader will be
surprised. §5.6's correction makes it weaker still — the two files differ in
`Goal` **and** in four entries of the `step` table, i.e. they are theorems about
different goals over different transition functions. That is not a subtle pair of
near-identical artefacts; it is two different theorems. §11.3 agrees with me in
plainer language than I would have used. **The abstract should not lead with
this.**

**6.2 — "Reversibility of a mechanism mattered more than breadth of
trajectory."** (abstract item 2, §3 title.) §3.3 then says, in the paper's own
words, that A0′'s toggle "was *designed* so that every direction-by-polarity
combination would have its own witness", that the adjudication rule "mechanically
admits what it mechanically rejected in A0", and that "the outcome follows from
the construction; nothing was learned that was not built in". I agree with that
assessment — which means the title of §3 and the abstract's item (2) assert
something the section retracts. Also n=1 per arm, with **at least five** declared
differences between the two worlds (mechanism, explorer, rule count 7 vs 21,
state count, object identity), so "controlled contrast" is generous for what is a
paired anecdote.

**6.3 — The §6.2 transfer ratio.** "world actions 346 → 10, ratio 0.029." The
denominator is a 100 % exhaustive sweep which §6.5 item 3 concedes is "not
realistic". A ratio against an admitted upper bound is not a saving; it is an
artefact of how the control was defined. And §6.5's last paragraph says the
playbook — one of the two books whose *joint* transfer is the claim — is never
read or compiled by any code path in A3, and the test its docstring cites does
not exist. Half the claimed object was not transferred.

**6.4 — "252 of 252 reachable (state, action) pairs of a level it never
explored."** Presented as a strong transfer result. But §6.1 says the two levels
share all four mechanisms and differ only in layout, and §6.5 says the goal cell
and both portal exits were supplied by hand to every arm. Under a containment
condition that strong, 252/252 is close to arithmetic. The negative controls
(§6.3) are the interesting part and they show the *free* layer catching nothing.

**6.5 — Two "independently developed tracks" crossing a data boundary.** §4.2
concedes this fairly ("A reader should not picture two teams… two agent sessions
working one repository under one operator, sharing `CLAUDE.md`, `Theoria.md` and
`CONTRACTS/`"). Good. But the abstract still says "a second track developed
alongside it", and §10.5 still says "two independently developed tracks". Two
sessions of the same model, under the same operator, reading the same design
document, is not independence in the sense the word carries in a validation
argument. Defence in depth, yes — and §4.2 says exactly that. The abstract and
§10.5 should say it too.

**6.6 — X3's "backwards" result is read two ways at once.** §7.2 flags X3 as a
metric to retire ("Do not use until resolved") and simultaneously offers a
completely convincing substantive reading of it: "an arm that keeps clearing
levels finds new states late, while an arm that dies on step three saw everything
it will ever see in its first quarter." If that reading is right, the metric is
fine and **the design's prediction is wrong** — which the paper half-admits at
line 1396 ("the design's story… predicts the opposite curve") and then does not
follow up. That is the most consequential unclaimed finding in §7 and it is
filed as a metric defect.

**6.7 — "byte-identical across two consecutive recomputes"** as a reproducibility
claim (§7.1). The paper immediately says the determinism *test* runs against a
synthetic fixture, not the published artefacts, and that two of five arms live in
gitignored payloads absent from every checkout, so a clean recompute "silently
drops a whole arm and a whole campaign". Given that, "byte-identical" describes
this machine, twice, and I would not present it as reproducibility.

**6.8 — The pre-registration story does not survive its own footnotes.** §1.1's
seal is "a declaration written by the authors' own script, not a control"; the
same instance built and adjudicated the world; §7.3 records five A0 metrics
marked `[seen]` post-dictions; §7.3 also records that the v2 pre-registration's
seal "declares the two leaks that got through the written prohibition on values
anyway". Each disclosure is admirable in isolation. Together they mean the
pre-registration discipline is self-attested at every layer, and the paper leans
on it hard — "the miss was written down before it was measured" is the load-bearing
sentence of §1.

**6.9 — Nine sealed games were contaminated by a web search (§10.1(f),
INC-BA-001), two "materially".** The paper reports this cleanly and I want to
note only that it is disclosed in §10 on page ~20 and not mentioned in the
abstract, which says "sealed pile untouched by a check on the bytes". Both
statements are true about different things — API contact vs. knowledge — and the
abstract's phrasing will be read as the stronger one.

**6.10 — Eight results, no baseline.** The abstract enumerates eight results and
then says, in its last paragraph, "We claim none of the framework's comparative
results. No arm was run against a baseline." An eight-item results list with no
comparison of any kind is a list of things that happened, not results. I would
call them "eight reports" or "eight components" and put the disclaimer first.

---

## 7 · After-the-fact check — what turned out to be explained elsewhere

Run only after §§1–6 were written, per instructions. Nothing here changed the
record above.

**Explained elsewhere, and should have been in the paper:**

* **The metric alphabet.** `battery/METRICS.md` is a generated, complete
  glossary of all 38 metrics with their families and declared directions.
  `battery/PREDICTIONS.md` additionally gives every metric a readable name
  (`state_revisit_rate`, `novelty_frontload`, `actions_per_model_call`,
  `actions_per_call_trend`, `max_no_progress_streak`) and a one-line rationale.
  **None of this is in the paper.** Importing the id→name column alone would fix
  §2.3 above at a cost of ~15 words per table.
* **The arms.** `battery/PREDICTIONS.md` carries a table describing `bare_cc` and
  `schema_repro` in one line each ("in weights, in the transcript; acts, then
  reconsiders" / "`world_model.py`, replay-level; a fitted simulator, no
  theorems"). Excellent, and absent from the paper.
* **X3's status as "the signature prediction of the family"** is stated
  explicitly in `battery/PREDICTIONS.md` line 62, together with the design's
  reasoning ("once the manual closes there is nothing left to be surprised by. A
  flat novelty curve means the theory never closed"). With that sentence in hand,
  §7.2's backwards result reads as a falsification of the framework's internal
  story, which is much stronger than how §7.2 files it. The paper has the raw
  material for finding 6.6 and does not use it.
* **The Chinese mandate quote** at line 382 is translated nowhere in the paper
  but paraphrased in `papers/phase1-workshop/README.md`. One line, already
  written, not imported.

**Found to be worse than I assumed while reading:**

* **The three figures do not exist at the cited paths.** The paper cites
  `figures/fig06_concept_timeline.py`, `figures/fig07_a0_vs_a0prime.py`,
  `figures/fig05_a2_repair_loop.py`, plus `figures/out/light/*.svg` and
  `figures/csv/*.csv`. What exists is `figures/fig1_concept_timeline.py`,
  `fig2_coverage_accuracy.py`, `fig3_loop_ledger.py`, each with a `.txt`
  rendering and a `data/*.json`; there is no `out/` directory and no `csv/`
  directory at all. Six of the seven figure paths I spot-checked resolve to
  nothing. In a paper whose stated binding rule is that every quantitative claim
  carries a resolvable repo-relative path, and which advertises a mechanical
  path audit (`CITECHECK.md`), three broken figure citations are the finding
  that most undermines the rule.
* The `.txt` plain-text renderings **do** exist and are described in
  `README.md` as "for reading before anything is styled". Inlining those three
  text plates would have given me figures at zero cost.

**Confusions that were genuinely mine, not the paper's:** none that I found. Each
item in §2 is either undefined everywhere or defined only in a file the paper
does not send the reader to.

---

## 8 · Recommendation

As submitted to a workshop with a 4,000-word budget: **reject**, on length and
on the absence of a statable claim — but with the strong caveat that I think a
publishable 4,000-word paper is *inside* this file and is not the one the title
and abstract describe.

The fastest route to it, in priority order:

1. Decide which of the three claims in §3 above is the paper. My vote is the
   evaluation-instrument negative result (§7.7 + §8.3 + §7.4).
2. Add one paragraph saying what ARC-AGI-3 is, what an "arm" is, and naming the
   five arms.
3. Add a metric id→name column, copied from `battery/METRICS.md`.
4. Inline the three `.txt` figure plates and fix the six broken figure paths.
5. Translate the six remaining Chinese quotations, or drop them.
6. Move §11.3 to §1, delete the draft-status block, and let the caveats live in
   §10 rather than in the hook.
7. Move every repo path out of running prose into endnotes.

What I would not change: the disclosure culture. §5.6's self-correction of its
own source report, §7.3's "picking the flattering one is the failure the file
exists to prevent", §7.10's admission that the report's own recommendation list
is one round out of date, §8.3's "an optional check is a check that does not run,
and it fails in the direction that looks like success", and the whole of §11.3
are the reason I would read the next version. There is a real intellectual
seriousness here that the current draft buries under its own bookkeeping.
