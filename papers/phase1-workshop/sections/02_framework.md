## 2 · The framework, in the amount this paper needs

The full design is `Theoria.md`. This section carries only the parts the Phase 1
results are unintelligible without; §11 places the whole thing against its
neighbours.

### 2.1 Two books, and what each answers

The world model is not a network and not a simulator. It is two hand-maintained
documents (`Theoria.md` §1.7–§1.9):

* the **manual** (`cold-start-a0/theory/theory.dsl` for A0) says what the world *is* — a vocabulary of
  objects and properties, rules that fire events, a goal clause, and **laws**:
  universal assertions written in the manual's own vocabulary, where writing one
  down *is* incurring a proof obligation;
* the **playbook** (`playbook.dsl`, per `CONTRACTS/dsl_grammar_v0.1.md`) says how to *win* — entries at theorem level
  and at experience level, with the certificate and the heuristic derived from
  the same object.

The manual answers understanding; the playbook answers competence. Everything
downstream is generated from them: `Theoria.md` §1.10a's four co-derived forms
(Lean, Python, PDDL, Markdown) come from one source, so a disagreement between
forms is a bug that can be *seen* rather than a drift that cannot.

Two constraints matter for reading the results below.

**Prediction has no side door.** The only predictor allowed is the one generated
from the manual. `a0-spike/THEORIZE_LOG.md` T-8 is what that constraint is for:
when certify was rewired to replay history through the *compiled* manual rather
than through the miner's in-memory rule objects, the generated code immediately
walked the player off the board — an error in the transcription of correct mined
rules into the manual, which replaying through the rules could never have found.

**A concept's ticket of admission is that it shortens the manual**
(`Theoria.md` §1.8, constraint 5). §3.6 reports what happened when that criterion
collided with another of the framework's own.

### 2.2 Engines propose, the LLM adjudicates

The precise work is outsourced. Six engines carried the acceptances reported here
(`engine-rig/STATUS.md`): `mdl_segmenter` (segmentation by description length),
`cegis_miner` (guard synthesis), `zero_space` (GF(2) conservation laws),
`lp_potential` (pagoda-style potential weights by linear programming),
`fd_adapter` (classical planning), `probe_frontier` (which experiment splits a
guard frontier, priced in bits). Two more — `deadlock_carver` and `ic3_pdr` —
were added at milestone M9 in response to gaps the A0 cold start named, and are
not exercised by any result below.

Engines emit **candidates**, never verdicts. The stream is append-only and every
row's `status` is the literal string `"candidate"`
(`CONTRACTS/candidates_schema.md`, frozen v0.1;
`engine-rig/tools/validate_candidates.py` is its executable form). What enters
the manual, and why, is written down by the LLM in a `THEORIZE_LOG.md` — one
entry per proposal, with its evidence and its cost. Those logs are the primary
evidence for most of what follows, and they were written before the scores
existed.

The division has teeth in both directions. `a0-spike/THEORIZE_LOG.md` T-6
records the adjudicator proposing a conservation law — the box never changes
checkerboard colour — and `zero_space` returning a strictly stronger one: a null
space of dimension 2, with each coordinate's parity conserved separately. The
engine corrected the LLM, which is the direction the division of labour was
designed to work in.

### 2.3 The inner loop, and the word *certify*

`Theoria.md` §1.10d: **theorize → certify → probe → plan → commit.**

`certify` is used here in a narrower sense than the field's. It is two layers,
and both must pass:

* the **cheap** layer — full-history replay through the generated predictor,
  scored at the pixel, with every pixel the responsibility of the board or of
  some object;
* the **expensive** layer — the declared laws discharged in Lean, with
  `#print axioms` inspected. An empty axiom list is the pass condition; `sorry`,
  `native_decide` and `ofReduceBool` are all failures.

The two layers do different jobs and the paper turns on the difference. Replay
certifies *against the past*. Lean certifies *relative to the manual* — it can
sign a theorem that is false of the world, and §5 is a worked exhibit of exactly
that, as two files a reader can diff. Neither layer certifies the manual against
the world. That is what `probe` is for: an experiment, chosen by the engine for
how many bits it splits, whose prediction is written down *before* the action is
taken (`Theoria.md` §1.10e, constraint 7).

### 2.4 The failure taxonomy this paper is scored against

`Theoria.md` Phase 3 lists in advance where the framework is expected to die:
概念不成形 (concepts fail to form), 机制归纳错 (wrong mechanism induced), 调度失误
(the LLM does engine work by hand), 表达力不够 (the true rule cannot be written in
the DSL), 证明打不动 (the obligation will not discharge), 搜索爆炸 (planning blows
up), 戳探设计差 (probes do not discriminate), 修订抖动 (revision thrash).

Every acceptance report in this repository scores itself against that table
rather than against a success metric of its own choosing
(`cold-start-a0/A0_REPORT.md` §5, `cold-start-a0/prime/A0P_REPORT.md` §4). Where
a class comes back clean, the reports say so and then say why the clean verdict
is weak evidence. Where two classes were hit hard, they are the two this paper
spends most of its space on.

### 2.5 What Phase 1 was allowed to be

Phase 1 is the closed system: build it, and pass three offline acceptances
before any money is spent on play (`Theoria.md`, Part 2, Phase 1). The three are
**A0** (cold-start on a self-built world with known ground truth), **A1** (peg
solitaire spec → DSL → LP weights → Lean closure lemma with an empty dependency
set), and **A2** (port a model with a missing rule, produce the theorem that
type-checks and is false of the world, then run the full repair loop). Phase 2
is the metrics battery, read off trajectories that already exist at zero new
game spend.

`Theoria.md`'s Phase 4 deliverables clause is why this document exists:

> 每个阶段边界定义一个最小可发表单元——Phase 1 结:A0–A2 + 电池对既有轨迹的回算,
> 独立可成 workshop 文

This paper is that unit and nothing more. It reports the three acceptances, the
battery's recompute — its third round, labelled `battery_version: "v2"` in
`battery/artifacts/capability_spectrum.json` because both the reports and the
artefacts count from zero — and, in §6, an early read on claim C3 that the mandate
does not list as an acceptance at all. It reports no play, no
baseline comparison of the framework's own arms, and
no claim from the Phase 3 claim menu.
