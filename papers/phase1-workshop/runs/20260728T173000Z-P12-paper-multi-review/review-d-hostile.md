# Review (d) — hostile referee

Target: `papers/phase1-workshop/PAPER.md` (2572 lines, v0.3).
Method: full read, then cross-read against the primary artefacts. The paper's own
audit files (`CITECHECK.md`, `REVIEW.md`, `OPEN_ITEMS.md`, `PROVENANCE.md`) were
**not** consulted; where a number is challenged below it was re-derived from the
JSON. Line numbers are `PAPER.md:N`.

This is not a balanced review. It is the case for rejection.

---

## 0 · Verdicts at a glance

| # | attack | verdict |
|---|---|---|
| 1 | "near-total evidence" in §5.2 is a denominator cut at the teleport | **LANDS** |
| 2 | A3 is not a transfer experiment; both levels are one `step()` | **LANDS** |
| 3 | The title promises what §2.3 says nothing in the paper does | **LANDS** |
| 4 | §10.5 "independently developed tracks" — retracted at §4.2 | **LANDS** |
| 5 | §10.5 "the one controlled comparison run" — retracted at §3.3 | **LANDS** |
| 6 | §11.3 states the abstract is wrong; the abstract was not changed | **LANDS** |
| 7 | Abstract (8) and §9.4 credit the preflight with a check §9.2 says it lacks | **LANDS** |
| 8 | "every link in the live chain" — two designed links were absent | **LANDS** |
| 9 | A0's "3 of 236 wrong" is one clause counted three times | **LANDS** |
| 10 | K7 is in the main table *and* retired as redundant | **LANDS** |
| 11 | The two A3 negative controls return byte-identical detection figures | **LANDS** |
| 12 | The battery's byte-identity claim has no evidence and cannot be run | **LANDS** |
| 13 | The only paper anyone has sat is one whose leak checks do nothing | **LANDS** |
| 14 | §3.2's MDL numbers cite an artefact that now says something else | **LANDS** |
| 15 | Abstract (6) "re-fits from a single frame" — three fields were supplied | **LANDS** |
| 16 | "The isomorphism is machine-checked" — against a paragraph | **LANDS** |
| 17 | A1's negative control certifies its own non-circularity | **LANDS** |
| 18 | Two `DECISIONS.md` records are demonstrably false; fifteen more are cited | **LANDS** |
| 19 | Lean gating: the load-bearing check skips rather than fails | **PARTIAL** |
| 20 | §7.7's tier arithmetic (19 → 6 → 9) | **FAILS** — it reconciles |
| 21 | The battery's headline counts (38/34/17/14/9/29/10; 1790 probes) | **FAILS** — all verified true |
| 22 | "accuracy 0.000" without a denominator | **FAILS** — the abstract now carries `(n = 3)` |

---

## 1 · Sentences that overclaim relative to their own evidence

Ranked by damage.

### 1.1 The A2 coverage defence — **LANDS**, and it is the worst one

> "**The history is near-exhaustive.** It covers **163 of the 164** reachable
> (state, action) pairs with the Cart in the left room, omitting exactly the pair
> that fires the deleted rule … The defect survives near-total evidence; it is
> not a coverage failure." — `PAPER.md:858–862`

**Rebuttal, one line:** *You cut the history at the teleport and then measured
coverage over the half of the world the cut left you — the artefact you cite says
the full sweep is 220/220 over 55 states, so your history covers 74 % of the
world, not 99.4 %.*

`cold-start-a2/artifacts/trace_summary.json` is unambiguous. `history_trace`
carries `"scope": "every reachable state with the Cart in the left room"`,
`states_in_scope: 41`, `state_action_pairs: 164`. `raw_trace` carries
`"scope": "every reachable state"`, `states_in_scope: 55`,
`state_action_pairs: 220`, `coverage: "220/220"`. And `cut_rule` says the cut
index *is* the portal transition. So the construction is: delete the teleport
rule; cut the trace at the teleport; define the denominator as the region the
teleport has not yet been used to leave; announce 163/164.

This is the load-bearing sentence of the entire A2 section, because it is what
converts "we deleted a rule and the check that only sees the past did not see it"
into a claim about *evidence*. Remove it and §5 is the tautology §11.3 already
admits it is (`PAPER.md:2567–2572`). The qualifier "with the Cart in the left
room" is printed, so this is not concealment — it is worse: the paper prints the
restriction and then draws, in the next clause, the conclusion the restriction
forbids.

### 1.2 A3 as a transfer result — **LANDS**

> "Scored against the referee's copy, the **carried** manual is right on 252 of
> 252 reachable (state, action) pairs of a level it never explored"
> — `PAPER.md:1159–1161`; abstract at `PAPER.md:100–103`

**Rebuttal:** *Your own world file says "both levels are the same function under a
different `LevelSpec`" — 252/252 measures that the manual encodes `step()`, which
L1's 248/248 already established.*

`cold-start-a3/a3world/a3_world.py`, module docstring:

> "the mechanism set is defined once, in `step()`, and both levels are the same
> function under a different `LevelSpec`"

L2 is not a world the theory has never seen. It is L1's transition function with
different coordinates, and the paper says so itself at `PAPER.md:1119–1123` —
"the guard and effect functions are byte-identical." A domain that is byte-identical
across two problems scoring 100 % on the second is arithmetic, not a finding.
`cold-start-a3/artifacts/score_vs_truth.json` also carries the number the paper
declines to print: the **from-scratch control** on L2 scores 252/252 as well. The
transfer arm's accuracy is indistinguishable from the baseline's; only the bill
differs, and §6.5 item 3 concedes the bill's cold-start column is an upper bound
the authors chose.

### 1.3 The title — **LANDS**

> "Certifying a world theory against something other than its own past"
> — `PAPER.md:3`

**Rebuttal:** *Your §2.3 says "Neither layer certifies the manual against the
world" (`PAPER.md:349`), and the third thing that would — the probe — emitted
**zero** executable probes in A0 (`PAPER.md:513`).*

The paper's own account of what faces the world is `probe`. The census across the
whole paper: A0 = 0 executable probes; A0′ = 13, all on a clause the authors
seeded themselves; A2 = 5 designed, 4 run, 1 unrunnable; A3 = none; A1 = not
applicable. The title is cashed by four probes in one self-built world against a
rule the authors deleted.

### 1.4 "A machine-checked impossibility … between two independently developed tracks" — **LANDS**

> — `PAPER.md:2314–2316`, §10.5, *"The one thing this paper claims."*

**Rebuttal:** *Your §4.2 says "A reader should not picture two teams" and "not an
independent replication"; your claims paragraph then says "independently
developed tracks."*

See §2.1 below. This is the single most careless sentence in the paper, because
of where it sits.

### 1.5 "the one controlled comparison run" — **LANDS**

> "that reversibility of a mechanism mattered more than breadth of trajectory in
> the one controlled comparison run" — `PAPER.md:2312–2314`

**Rebuttal:** *§3.3 lists six variables that changed, then says "The outcome
follows from the construction; nothing was learned that was not built in"
(`PAPER.md:546`) — a comparison in which nothing was learned is not a controlled
comparison, and calling it one in the claims paragraph is not a summary, it is a
restoration.*

### 1.6 "A theory … re-fits from a single frame" — **LANDS**

> — abstract, `PAPER.md:100–101`

**Rebuttal:** *It re-fit from one frame and three answers you handed it —
the goal cell and both portal exits (`PAPER.md:1149–1151`, `PAPER.md:1238–1240`)
— and the goal cell is the one field without which there is no plan.*

Worse than the paper says: `a3_world.py`'s docstring records that the exits are
supplied because `mdl_segmenter` **cannot** derive them (defect D-A3-003, "the
mover's track was absent from 19 of 326 frames"). §6.5 item 2 presents the
supply as a contract-sanctioned design choice; the world file presents it as a
workaround for an engine failure. Both are in the repository; only the flattering
framing is in the paper.

### 1.7 "The isomorphism is machine-checked, clause by clause" — **LANDS**

> — `PAPER.md:867`, with the six-row table at `868–876`

**Rebuttal:** *The other side of your isomorphism is a paragraph you wrote in your
own design document; a machine checked your world against your prose, which
establishes that you built what you described.*

Three of the six rows check the self-built world against compressed Chinese
sentences from `Theoria.md` §1.3. Nothing in the table touches DC22. "Machine-checked"
here means "a script compared an artefact to a string."

### 1.8 "exercised the whole credential path" / "every link in the live chain" — **LANDS**

> abstract `PAPER.md:112–113`; §9 heading `PAPER.md:1897`; docstring `PAPER.md:1917–1918`

**Rebuttal:** *§9.3 says the model proxy was not live and the spend gate was
wired seven hours after the run — two of the designed links were absent, so this
exercised most of the chain.*

`PAPER.md:2004–2011` (GAP 1, `proxied: false`) and `PAPER.md:2012–2020` (gate
wired 08:42 Z, run at 01:20 Z). The section body is honest; the heading and the
abstract are not.

### 1.9 "34 of 38 executable exploits still score a metric at or near its best value" — **LANDS as a framing**, not as a number

> — abstract, `PAPER.md:91–94`

The number is **true** (`gaming_audit.json`: 34 of 38 `demonstrated.succeeded`).
**Rebuttal:** *You are listing, as result five of eight, an instrument that fails
89 % of the tests its own author wrote for it, cannot reach significance on any
metric by arithmetic, and has 21 of 38 metrics never checked against any
gradient. That is a negative result. Report it as one or drop it.*

### 1.10 "the sealed pile untouched by a check on the bytes" — **LANDS**

Covered as a contradiction; see §2.3.

---

## 2 · Internal contradictions — found by cross-reading

### 2.1 "Independently developed" vs "not an independent replication"

- `PAPER.md:2315` (§10.5): "weights crossed a data boundary between two
  **independently developed tracks**"
- `PAPER.md:719–724` (§4.2): "They are two agent sessions working one repository
  under one operator, sharing `CLAUDE.md`, `Theoria.md` and `CONTRACTS/` …
  **A reader should not picture two teams.** What crosses the boundary is
  therefore a *defence-in-depth* result, **not an independent replication**."

These cannot both stand. §4.2 is the honest one; §10.5 is the one a reader quotes.
That §10.5 is titled *"The one thing this paper claims"* makes this the paper's
worst single line — the walk-back is 1 600 lines upstream of the claim, and the
claim restores the retracted wording verbatim.

### 2.2 "Controlled comparison" vs "demonstrates the mechanism rather than tests it"

- `PAPER.md:2313` (§10.5): "in the one **controlled comparison** run"
- `PAPER.md:231` (§1.3): "a **controlled** A0/A0′ contrast"
- `PAPER.md:485` (§3.3 heading): "The **controlled** contrast"
- against `PAPER.md:489–495`: A0 has 7 rules, A0′ has 21; 59 vs 57 states; 236 vs
  228 pairs; Button vs Switch; two deliberate variables. "'Identical except'
  would be a false description and is not used here."
- against `PAPER.md:546–548`: "The outcome follows from the construction; nothing
  was learned that was not built in. So this contrast **demonstrates the
  mechanism rather than tests it**."

The paper demolishes the word "controlled" in §3.3 and then keeps it in the
section heading, in the contributions list, and in the claims paragraph.

### 2.3 The preflight's byte scan belongs to a different run

- abstract `PAPER.md:112–113`: "A live run against the real API that exercised the
  whole credential path — key injected in one place, **sealed pile untouched by a
  check on the bytes** — for zero billable actions."
- §9.4 `PAPER.md:2065–2068`: "What **the preflight** does establish … the sealed
  pile is untouched by a **check on the bytes** rather than on the guard's
  self-report"
- §9.2 `PAPER.md:1984–1985`: "**The preflight manifest predates that scan and
  carries only the counters.**"

The byte scan (`game_ids_anywhere_in_the_records`) is in
`theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json` — the
**first-contact** run, which spent 7 actions. The abstract's "for zero billable
actions" and its "check on the bytes" are properties of two different runs, joined
by a dash. §9.4 repeats the conflation 80 lines after §9.2 disclaims it. This is a
contradiction *within a single section*, and the abstract inherits it.

### 2.4 §11.3 states the abstract is wrong, and the abstract was not changed

- `PAPER.md:2567–2572` (§11.3): "**'Prediction perfect, understanding broken' is
  this framework's own premise, not a finding.** §5's procedure is to take a
  certified manual, delete a rule that never fires in the retained history, and
  observe that replay over that history does not notice — which is **analytically
  guaranteed by the construction**. … It is **not evidence about anything, and the
  abstract should not read as though it were.**"
- abstract `PAPER.md:81–88`: leads result (4) with exactly that exhibit, calls the
  file pair "**the headline artefact**", and closes on "The instrument cannot tell
  them apart, and is not supposed to."

The paper contains an instruction to fix its own abstract, and shipped the
abstract unfixed. A referee does not need to construct this criticism; he only
needs to quote the paper against itself.

### 2.5 K7 is simultaneously a main-table finding and a retired duplicate

- `PAPER.md:1375–1376` (§7.2): "The main table holds nine metrics — E2, E3,
  **K7**, K11, K12, M3, M6, P3, P4"
- `PAPER.md:1640–1643` (§7.9): "retires 5 into representatives — … **K14 and K7
  into K5** (5 each)"

Verified: `gaming_audit.json` `main` = `[E2,E3,K11,K12,K7,M3,M6,P3,P4]`;
`redundancy.json` `eliminated` includes K7, `represented_by: K5`,
`rho_with_representative: 1.0`, `shared_runs: 5`. The paper's own gloss —
"Retired is not deleted, only excluded from being counted as a separate finding"
— means the main table of nine contains a metric excluded from being counted as a
separate finding. Neither section notices the other. And a Spearman ρ of exactly
1.0 over five points is not a redundancy result; it is five points.

### 2.6 Battery reproducibility: three sentences, mutually incompatible

`PAPER.md:1306–1321`, all in §7.1:

1. "Artefacts regenerate with `python -m battery.run_battery` … and **were
   byte-identical across two consecutive recomputes**." — cited to the *script*,
   not to any evidence. Under the draft's own binding rule (`PAPER.md:36–38`) this
   quantitative claim carries no artefact path, because there is none.
2. "The determinism *test* runs against a **synthetic fixture** rather than
   against the published artefacts."
3. "two of the five arms live in **gitignored payloads** … a recompute on a clean
   checkout **silently drops a whole arm and a whole campaign**."

So: the byte-identity claim is unevidenced, the only mechanical determinism check
tests something else, and no reader can reproduce the recompute at all. Also from
§7.1: **six of the seven artefacts carry no provenance block**, in the section of
a paper whose distinguishing virtue is provenance.

### 2.7 The exam's clean bill and the exam's only real result do not overlap

- `PAPER.md:1815–1816`: "The static checks come back clean: **1,790 declared
  probes across the four papers, 0 probe hits, 0 structural hits**."
- `PAPER.md:1836–1839`: "`leakage.json` records `label_sets_checked: []` for the
  **handover** and adaptation papers, so the positional and metadata checks still
  run on nothing for two of the four."
- `PAPER.md:1780–1784`: "**Only one paper has been sat by a real subject** … each
  scored 46.0/46.0 on the **handover** paper."

Verified against `exam/artifacts/leakage.json`: probes are 363 / 58 / 1284 / 85.
**1 284 of the 1 790 probes (72 %) are on the adaptation paper, which nobody has
sat.** The one paper that produced a real score got 58 probes and has both label
checks disabled. The clean bill is carried almost entirely by machinery no subject
has touched, and the one sat paper is the least checked of the four — and it
returned a perfect score. The paper states both halves and never joins them.

### 2.8 §3.2 quotes numbers its cited artefact no longer contains

`PAPER.md:479–483`: the MDL headline (6511 vs 4423 bits; 90 tracks vs 3) is
followed by "`engines_report.json` has since moved on — it now reports 5704 bits
over 6 tracks … so the artefact and the report disagree, and the paper quotes the
report the adjudication was actually made from."

Under the draft's binding rule, that is a quantitative claim whose artefact says
something else. The disclosure is honest; the choice is not defensible. A reviewer
opening the cited file finds different numbers, which is precisely the failure the
rule exists to prevent.

### 2.9 Two of the paper's own decision records are false

- `PAPER.md:952–959`: D-A2-010 says `locate.py` and `probe.py` "import no world
  module at all"; the paper shows they do (`probe.py:59`, `locate.py:36`).
- `PAPER.md:1014–1019`: D-A2-005 and `A2_REPORT.md` §4 say the two Lean files
  "differ in their weight table and in nothing else"; 52 lines change across 7
  hunks, including `def Goal` and four `step` entries.

The paper presents these as its integrity showing. A referee reads them as a
**base rate**: two `DECISIONS.md` entries were checked adversarially and both
were false. The paper cites roughly fifteen more `DECISIONS.md` and `STATUS.md`
entries as evidence without checking them. On the demonstrated hit rate, the
evidence base is not trustworthy.

---

## 3 · Circularity

### 3.1 The pre-registration is a self-timestamped file — **LANDS**

§1's whole rhetorical structure ("What makes this evidence rather than an
anecdote is the order of events", `PAPER.md:163`) rests on R-05 having been
written before the score. The paper's own account of the seal:

> "That stamp is a declaration written by the authors' own script, not a control:
> the only thing that could make it auditable is git history, **which this paper
> does not appeal to**." — `PAPER.md:190–191`

*One line:* **Your pre-registration is a file you wrote, sealed by a script you
wrote, in a repository whose history you decline to cite.** And the same instance
built the world it adjudicated (`PAPER.md:194`). The instrument that establishes
priority presupposes the good faith it is offered as evidence of.

### 3.2 Ground truth is the authors' own generator — everywhere

A0, A0′, A2 and A3 all score "against ground truth" where ground truth is a Python
file the same project wrote. A3 is the sharpest case: the "unseen" level and the
"seen" level are the same `step()` under two `LevelSpec`s, and the two "negative
controls" are boolean flags **inside that same function** (`a3_world.py:163–164`,
`portal_one_way`, `rewired_exit_b`; `L2_ONEWAY = _variant_of_l2(...)`). A negative
control implemented as a keyword argument to the system under test is not an
independent check; it is a unit test.

### 3.3 A1's negative control certifies its own non-circularity — **LANDS**

> "An adversarial read-only pass — permitted to falsify but not to confirm, and
> **run inside the same project** rather than by a third party — ran that control.
> … **The same review confirmed** that `gen_lean.py` contains no hard-coded weight
> vector and that the move set is derived independently from the predictor, **so
> the cross-check is not circular**." — `PAPER.md:756–763`

*One line:* The evidence that your cross-check is not circular is a pass by the
same project that wrote the cross-check.

### 3.4 The battery grades itself with metrics it wrote and exploits it chose

`PAPER.md:1447–1450`: "the author built the metric definitions, and a definition
can be tuned toward a hoped-for result without ever seeing data. Processes 1 and 4
exist to catch that, and **neither substitutes for a second pair of eyes**."

So "34 of 38 exploits land" is a **lower bound produced by the person who chose
which 38 exploits to write** — and the four that were defended were defended by
the same person. The one adversarial exploit that came from outside the loop (K2's
free-text sampling frame, `PAPER.md:1482–1493`) broke the defence immediately.
That is the base rate for what an actual adversary does to this instrument.

### 3.5 A2's "truth is the referee" is enforced by intention

`PAPER.md:956–959`: "The isolation is enforced by **what those modules are
*allowed* to call**, not by the import graph." The world is in scope; the
discipline is that nobody looked. This is the same instrument as §3.1 — a
declaration standing in for a control — and the paper has already demonstrated
(D-A2-010) that the written form of this declaration was false.

### 3.6 §5.2's "the substitution can make the claim stronger"

The isomorphism to DC22 is checked against `Theoria.md` §1.3 — a document by the
same authors — and §10.1(f) then reveals that `Theoria.md` §1.3 **is itself the
contamination** that downgraded DC22's seal (`PAPER.md:2141–2146`). The paper
validates its substitute world against the very text whose existence forced the
substitution.

---

## 4 · Load-bearing weasel words

**Hedges doing a result's work:**

| location | word | what it is covering |
|---|---|---|
| `PAPER.md:858` | "**near**-exhaustive" | a denominator restricted to 41 of 55 states |
| `PAPER.md:852` (§5.2 heading) | "**can** make the claim stronger" | a modal as a section conclusion; nothing below establishes it did |
| `PAPER.md:2107–2108` | the environment "**appears to** satisfy the assumption" | a determinism result the paper does not have |
| `PAPER.md:1824` | "taking a reader from 47.5 % to **essentially full marks**" | an unnumbered number, in a paper whose binding rule is that numbers carry paths — and §8.4 concedes these figures are "prose, not artefacts" |
| `PAPER.md:2208–2209` | "'one revision' for A2 is **this paper's reading** of the ledger" | there is no revision count for A2 in the tree |
| `PAPER.md:1121` | the diff is "**confined to**" four fields | i.e. the two levels are the same function |

**Strong verbs doing a hedge's work:**

| location | verb | what it should be |
|---|---|---|
| `PAPER.md:3`, `:57` | "**Certifying** … certified in two layers" | *checked against its own past, and against itself* — §2.3:349 says so |
| `PAPER.md:867` | "the isomorphism is **machine-checked**" | *a script compared the world to a paragraph we wrote* |
| `PAPER.md:231`, `:485`, `:2313` | "**controlled**" contrast/comparison | *illustration* — §3.3:548's own word |
| `PAPER.md:2315` | "two **independently developed** tracks" | *two sessions under one operator* — §4.2:719–721's own words |
| `PAPER.md:1170`, `:1184` | "two **negative controls**" | *two keyword arguments to the world under test* |
| `PAPER.md:87–88` | "The instrument **cannot** tell them apart, and is not supposed to" | a tautology in the indicative: two Lean files with different `Goal` definitions are not a pair the instrument is being asked to distinguish |

**The hedge-then-restore pattern**, which recurs and is the paper's signature
rhetorical defect: `PAPER.md:548` demotes the A0/A0′ finding to "demonstrates
rather than tests"; `PAPER.md:551–554` immediately asserts "The lesson itself
survives that demotion intact"; `PAPER.md:2313` then restores the strong wording
in the claims paragraph. The concession is real, local, and does not propagate.
Same pattern at §11.3 → abstract, and at §9.2 → §9.4 → abstract.

---

## 5 · The single most damaging true thing

**At full force.**

There is no result in this paper that is not either analytically entailed by a
construction the authors chose, or a self-administered report of failure. Take
them in order. A0's headline — a manual perfect on replay and wrong about the
world — is three rows of `score_vs_truth.json` in which the cart position is
*correct* in all three and a single boolean differs: one un-generalised clause,
counted once per direction, 1.3 % of a 9×9 world the authors built, adjudicated
by the instance that built it, with the priority claim resting on a stamp the
paper itself says only git history could audit and then declines to cite. A0′ is
conceded at `PAPER.md:546` to teach nothing that was not built in. A1 is one
5-cell fixture whose negative control was run inside the same project and which
certified its own non-circularity. A2 deletes a rule the authors wrote, cuts the
trace at the transition that rule fires, computes coverage over the remainder, and
calls the result "near-total evidence" — while §11.3 states in the paper's own
words that the whole exhibit is "analytically guaranteed by the construction" and
"not evidence about anything." A3 carries a domain between two `LevelSpec`s of one
`step()` function — the world file says so — scores 100 %, and does not print the
adjacent artefact field showing the from-scratch control scores 100 % too; its
negative controls are boolean flags inside the function under test. The battery
cannot reach p < 0.05 on any metric by arithmetic, leaves 21 of 38 metrics checked
against no gradient at all, and fails 34 of the 38 exploits its own author wrote —
and its most confident number, byte-identical recomputation, has no artefact and
cannot be reproduced on a clean checkout. The exam has three of four papers never
sat, and the fourth saturated at ceiling with both of its leak checks disabled.
The preflight ran one of two designed proxies with the spend gate not yet wired,
and the byte-level sealed-pile check the abstract advertises belongs to a
different run. Strip the self-referential and what remains, in twenty-three
thousand words, is: *the code runs, end to end, on worlds we wrote, and we found
a great many defects in it.* That is a systems report. It is not a paper about
world models, and the abstract's "Eight results" is eight restatements of one.

**Does the paper concede it?** In pieces, never assembled — and the assembly is
the damage. `PAPER.md:251–264` concedes offline and self-built. `PAPER.md:546`
concedes the A0′ entailment. `PAPER.md:2567–2572` concedes it for §5, and
explicitly instructs the abstract to stop implying otherwise. `PAPER.md:1447–1450`
concedes the battery's self-authorship. `PAPER.md:1251–1253` concedes theorize is
a person. `PAPER.md:124–126` gets closest — "The contribution is an instrument and
a demonstration artefact … not a result about world models." But §10.5, the
paragraph titled *"The one thing this paper claims"* (`PAPER.md:2308–2325`), then
asserts six positive claims, two of which use wording the body retracted, and the
abstract leads with the exhibit §11.3 says is not evidence. **The paper concedes
every premise of this attack and refuses its conclusion.** A referee will read that
as either a drafting failure or a decision, and neither reading favours acceptance.

---

## 6 · The reject argument

> This paper's abstract advertises eight results, but each one is either
> analytically entailed by a construction the authors chose — A2 deletes a rule
> and reports that a past-facing check does not see it, which §11.3 concedes is
> "analytically guaranteed" and "not evidence about anything"; A3 carries a domain
> between two parameterisations of a single `step()` function; A0′ is admitted at
> §3.3 to have taught nothing that was not built in — or is a self-administered
> failure report, such as a metrics battery that cannot reach significance on any
> metric by arithmetic and fails 34 of the 38 exploits its own author wrote.
> The paper's honesty is real but structurally decorative: §4.2 retracts
> "independent tracks", §3.3 retracts "controlled comparison", §9.2 denies the
> preflight the byte-level seal check, and §11.3 instructs the abstract to stop
> overreading §5 — and §10.5 and the abstract restore all four claims verbatim, so
> a reader who stops at the front page is misled by a paper that knows better on
> page 40. I recommend rejection: the one substantive evidential defence in the
> submission — that A2's defect "survives near-total evidence" — is refuted by the
> artefact it cites, whose `trace_summary.json` scopes the 163/164 to the left room
> only and reports 220/220 for the full sweep, meaning the history was cut at the
> deleted rule's own transition and coverage measured over what the cut left behind.

---

## 7 · The two targets I was asked to test

### 7.1 "A prover certifying a theorem about a wrong model is just what a prover is"

**Partly unfair, and the paper does have an answer — but the answer is not the one
it exhibits.**

The reader's charge is too cheap as stated. The paper's genuine delta is real and
correctly located at `PAPER.md:2516–2525` and `PAPER.md:2532–2537`: in
proof-carrying code and in the LLM-proving line, the specification is *written*
and denotes something definite; here it is *mined*, so the theorem's premises are
themselves fallible and a bad mine is "laundered into a formally proved false
statement." That is a coherent, non-trivial framing and the specification-mining
literature (`ammons2002mining`) is the right anchor. §5.4's quantification — the
same holed manual is green on 184 frames and red on the full sweep with 44
anomalies — is also a measurement rather than an assertion.

But the **exhibit does not carry that argument**, and §5.6 is where it collapses.
The two Lean files have different `def Goal` (`c10` vs `c34`) and four different
`step` entries: 52 changed lines across 7 hunks (`PAPER.md:1018–1027`). They are
two theorems about two different structures. "Identical in generator, tactic,
dependency surface and axiom list" is therefore a property of the **generator**,
true of every pair of files it emits — the paper has exhibited its own
determinism.

*One-line rebuttal to hand the authors:* **Every file your generator emits has
identical tactic, dependency surface and axiom list; you have exhibited your
generator's determinism, not a failure mode — and since the two theorems are about
different goals, the instrument was never asked to tell them apart.**

The paper knows: `PAPER.md:1041–1047` admits "What is lost with the false version
is a rhetorical minimal pair" and names the artefact that would have been the real
exhibit (`generated_repaired_stale/`, the repaired invariant against the *same*
goal, which fails). That file exists in the tree. The paper ships the wrong pair
as its headline and the right one as a footnote. **The reader's charge lands, but
for a different reason than the reader gave: not because provers are like that,
but because this particular pair does not instantiate the claim.**

### 7.2 §10.5 and the abstract vs §4.2 and §3.3

**Both walk-backs are real, and §10.5 reverses both. Verified verbatim.**

- "independently developed tracks" (`PAPER.md:2315`) vs "A reader should not
  picture two teams … not an independent replication" (`PAPER.md:719–724`).
- "the one controlled comparison run" (`PAPER.md:2313`) vs "'Identical except'
  would be a false description and is not used here" (`PAPER.md:494–495`) and
  "nothing was learned that was not built in" (`PAPER.md:546`).

Two further items belong on the same list and were not raised by other readers:

- **The abstract is cleaner than §10.5 on both counts.** `PAPER.md:76–78` says
  "a second track **developed alongside it**" and `PAPER.md:69–72` says "a design
  lesson **demonstrated by construction rather than a hypothesis tested**." So the
  abstract was corrected and §10.5 was not. The paper's most-quoted paragraph is
  its least-revised one.
- **§10.5 also inherits §9's conflation** at one remove and §7's framing wholesale
  — its battery clause ("contradicted 17 of its own register entries … 14 of them
  defence claims") is the one item in §10.5 that survives checking intact
  (`gaming_audit.json`: `n_disagreements` 17, `defended` contradicted 14).

**§10.5 must be rewritten before submission.** As it stands it is the only
paragraph most referees will quote, and three of its six clauses are contradicted
by the body.

---

## 8 · Attacks I tried that failed

Recorded so the authors do not spend time on them.

- **§7.7's tier arithmetic** (19 → 6 → 9, "19 − 13 = 6, 13 − 3 returned, 6 + 3 = 9",
  `PAPER.md:1562–1566`). Reconciles. Four defences were implemented and three
  returned because K2's failed, which §7.4 states. Clean.
- **Every headline battery count.** Verified against `battery/artifacts/gaming_audit.json`:
  `n_demonstrated` 38, `demonstrated.succeeded` true for exactly 34, `n_disagreements`
  17, `defended` among `fields_contradicted` exactly 14, `main` 9, `reference` 29,
  `demoted_by_demonstration` 10. `redundancy.json`: `n_pairs` 703 = C(38,2),
  `n_pairs_measured` 257, `n_clusters` 32, `n_eliminated` 5. `leakage.json`:
  363 + 58 + 1284 + 85 = 1790, all `probe_hits` and `structural_hits` zero.
  **All true.** The paper's arithmetic is not where it is weak.
- **"accuracy 0.000" without a denominator.** Already fixed: the abstract carries
  `(n = 3)` at `PAPER.md:66`, per §7.4's own instruction. Attack withdrawn.
- **A0's 233/236 vs the battery's K2 = 0.000.** Both correct and both cited; the
  tension is the point of §7.4 and it is well made.
- **The abstract's exemption from the path rule.** Declared up front at
  `PAPER.md:36–39` and each figure recurs cited in the body. Legitimate.

One partial:

- **Lean gating** (`PAPER.md:747–751`): 8 of 83 tests skip when `lean` is absent,
  so "the empty-axiom-list claim evaporates into skips rather than failing
  loudly." The paper discloses this fully and correctly. It is not an overclaim —
  it is a reproducibility cost a referee will note and not reject on.

---

## 9 · What would actually rescue the paper

Not requested, stated in one line each because a reject recommendation that names
no remedy is lazy.

1. Rewrite §10.5 to the abstract's wording, not above it.
2. Re-derive §5.2's coverage over the full 220 pairs and state the real number
   (163/220), then argue from it — the argument survives, the rhetoric does not.
3. Ship `generated_repaired_stale/` as the §5.6 headline pair, since it is the
   minimal pair and it is already in the tree.
4. Demote A3 from "transfer" to "problem re-instantiation", and print the
   from-scratch control's 252/252 beside the transfer arm's.
5. Cut the battery, the exam and the preflight to one paragraph each with pointers.
   They are three negative results wearing the costume of three contributions, and
   they are 45 % of the length.
