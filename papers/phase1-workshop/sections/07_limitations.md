## 7 · Limitations and honesty clauses

`Theoria.md` §3.2 item 8 fixes, in advance, the list of things this project must
disclose. It is transcribed here clause by clause and answered for *this* paper,
followed by the limitations the individual acceptance reports raise on their own
account. Nothing in this section is a concession extracted by a reviewer; all of
it was written down by the runs themselves, and the paths are given so it can be
checked rather than believed.

### 7.1 The pre-declared clauses, answered

**(a) 便宜是预测 — "cheap" is a prediction, not a result.** `Theoria.md`'s cost
claim (C5, total spend 10⁸ → 10⁶) belongs to Phase 4 and is not evidenced here in
any form. This paper reports no cost comparison between arms. The battery's
economy family is `not-applicable` on the Theoria arm for a structural reason
given below.

**(b) 理解不消灭组合爆炸 — understanding does not abolish combinatorial
explosion.** PSPACE-hardness is untouched; the design's answer is engines and
caching, not a claim of tractability. Every world in this paper is tiny: 59
reachable states in A0 (`cold-start-a0/artifacts/score_vs_truth.json`), 57 in A0′
(`cold-start-a0/prime/artifacts/prime_report.json`), 55 in A2 with 148 in the
Lean enumeration (`cold-start-a2/A2_REPORT.md` §8), and a 5-hole board in A1
(`theory-compiler/STATUS.md`). Lean's `decide` is affordable at these sizes and
will not be at 10⁶; `theory-compiler/STATUS.md` records the sharper version — an
empty axiom list and a linearly-sized proof are **not simultaneously available**,
with the `computational` route empty-axiom at O(2ⁿ) (2³³ on the 33-hole English
board, not runnable) and the `algebraic` route linear but carrying `propext` and
`Quot.sound`. Both are honest; the trade-off is D-TC-008. **Scale is untested,
and no result here should be read as evidence about it.**

**(c) 仅确定性环境 — deterministic environments only.** Every world in this paper
is deterministic and self-built. `arc-recon/README.md` reports that the
cross-session determinism precheck now passes on all four development-pile games
(9/9, 3/3, 9/9, 9/9; `arc-recon/data/precheck.json`), so the target environment
appears to satisfy the assumption — but nothing here has been run under
stochasticity, and the framework as designed does not cover it.

**(d) 语法脚手架披露 — disclose the grammar scaffolding.** The DSL is ours, and it
did not stay fixed across the three acceptances. `dsl_grammar_v0.1` was frozen
before A0; A0's run produced an expressivity ledger of five gaps
(`cold-start-a0/THEORIZE_LOG.md` §E: E-01 guard negation, E-02 direction lifting,
E-03 the frame axiom, E-04 landmark declaration, E-05 weight vectors), and
`CONTRACTS/dsl_grammar_v0.2.md` was then authored to close them, with each
revision annotated with the ledger entry that forced it
(`theory-compiler/STATUS.md`). E-03 is the load-bearing disclosure: until v0.2,
the most important semantic fact about `step` — that an object no rule fires for
is unchanged — lived in a comment at the top of `theory.dsl` and was hard-coded
in all three backends. A manual whose default behaviour is a comment is not a
manual, and A0's results were produced under that condition. The ledger is
public, the grammar diff is public, and v0.1 was not edited.

**(e) 单一 benchmark 家族 — a single benchmark family.** This paper is weaker than
that clause anticipates: it reports **no benchmark result at all**. Every world
in §3–§5 was built by us; A1's is peg solitaire. The one thing recomputed over
ARC trajectories is the battery (§6), and those trajectories are a control-arm
pilot, not a Theoria result.

**(f) 封存堆污染分级与预训练先验 — sealed-pile contamination grading and the
pretraining-prior caveat.** Two entries, and both are worse than "clean":

* **INC-004.** A2 could not be the literal A2. The upstream game named in
  `Theoria.md`'s A2 item is in the sealed pile, and reading its released
  artifacts teaches its mechanics as effectively as playing it. The owner ruled
  option (b) — a self-built world isomorphic to the failure structure, with the
  isomorphism argument citing only the structural description already printed in
  `Theoria.md` §1.3 (`cold-start-a2/A2_REPORT.md` §1;
  `cold-start-a2/artifacts/loop_ledger.json` records the ruling as the run's
  authority). The same incident **downgrades that game's own seal**, from
  `never_audited` to `design_document_disclosed`, on the independent ground that
  `Theoria.md` discloses its mechanics in §1.3 and §3.2 — it was
  design-document-contaminated before the cut was ever made. **No claim about
  that game is made anywhere in this paper**, and any later claim must carry the
  caveat.
* **INC-BA-001.** The sealed pile is no longer 21 games at `never_audited`. While
  locating an upstream release, a search subagent read mechanics descriptions for
  **nine** sealed games before the page was judged unsafe, two of them
  materially (`baseline-arms/INCIDENTS.md`; `baseline-arms/TOUCHED_GAMES.md`).
  This was not an API call and no guard could have caught it; the institutional
  consequence recorded there is that the upstream artifact set is a
  read-it-and-you-contaminate-everything object whose only safe use is
  directory-name-exact selection of development-pile games. Phase 4's exam items
  must now avoid those nine.
* **Pretraining prior.** Public-game walkthroughs may already be in the
  pretraining corpus. The design's mitigation is that all three arms share a
  model so the *comparison* survives, plus the hard rule that game ids never
  enter model context. Any absolute phrasing of "induced from zero" is
  discounted accordingly. This paper makes no induction claim about any ARC game.

### 7.2 A correction to the repository's own summary

`CLAUDE.md` states that no game has been played and that all 25 are registered
`never_audited`. That was true when written and is **not true now**. The
baseline pilot played all four development-pile games — 12 cells (4 games × 3
models) plus 2 reruns, 109 successful actions, followed by a variance-envelope
campaign adding 44 more on one game — and all four are recorded at
`trajectories_reviewed`, because a model read the frames pixel-by-pixel and chose
actions from them (`baseline-arms/TOUCHED_GAMES.md`; `baseline-arms/ledger.jsonl`,
560 rows). No game was ever completed: `levels_completed` is 0 throughout, and
nothing reached level 2. This is the legitimate use of a development pile, and
recording it is the point of having one; it is corrected here because a paper
that repeated `CLAUDE.md`'s sentence would be repeating something false.

### 7.3 What the individual acceptances do not show

**The theorize step is not a measured LLM step.** This is the largest caveat in
the paper and it is stated first. `cold-start-a2/A2_REPORT.md` §8 puts it
plainly:

> Nothing about whether an LLM would have written these manuals. The theorize
> step is done by hand here, as in A0 — the DSL files are checked in as
> artefacts. A2 tests the instrument and the loop, not the theorizer.

The consequence is visible in the battery: `battery/REPORT_V0.md` records that
"A0 ran engines and hand adjudication with no LLM in the loop, so it has no model
calls", which is why **every economy metric is `not-applicable` on the Theoria
arm**. The adjudication records in `THEORIZE_LOG.md` are genuine and were written
before the scores existed, but nothing here measures a prompted theorize step
inside a harness, and no number in this paper should be read as one.

**The seal has one hole, in the same place twice.** In A0 and A0′ the same
instance built the world and adjudicated it (`cold-start-a0/A0_REPORT.md` §6.3;
`cold-start-a0/prime/A0P_REPORT.md` §5.5). No ground-truth file was opened before
M6 and every verdict is written to be re-derivable from the candidate stream
alone, but that is weaker than a genuine blind and the reports count it as a
threat to the result rather than a footnote. A2 mitigates differently rather than
better: it reuses an unmodified upstream compiler, hashes every imported file — 22 of them in
`cold-start-a2/artifacts/upstream_pin.json` — and verifies read-only-ness by
hashing 258 files before and after a full run (`cold-start-a2/A2_REPORT.md` §7,
which is where the 258 figure lives; the pin file does not carry it).

**No multi-round repair, anywhere.** Revision counts across the whole paper are
0 (A0), 0 (A0′ Run A) and 1 (A0′ Run B), each recorded as a `revisions` field in
`cold-start-a0/prime/artifacts/prime_report.json`. A2's loop ran its 修订 beat
once, but **no file in the tree states a revision count for A2** — the ledger's L4
beat records `re_derivable_from_grown_evidence: true` and no number — so "one
revision" for A2 is this paper's reading of the ledger, not a figure it can cite.
The failure class 修订抖动 is
unmeasured, and `cold-start-a0/prime/A0P_REPORT.md` §5.1 says so: nothing here
exercises a manual that must be revised, re-probed and revised again.

**The seeded error was of a convenient kind.** A0′ Run B's clause escaped the
declared arena, which is what let the Lean form catch it for free. A wrong rule
that stays inside the arena would have had only the coverage probe, and only
because the clause was untested; a wrong-but-*tested* clause would fail replay.
A right-looking-but-wrong clause on a tested firing state is covered by neither
mechanism, and `A0P_REPORT.md` §5.2 calls that gap real.

**A1 proved less than the manual asserts, and refused to hide it.** The peg
manual's `goal count(Peg, alive) = 1` was not proved. Three of the five singleton
end states are pinned by `engine-rig`'s own tests as *not derivable* by the linear
pagoda method — not merely unexported — and the compiler responds with
`CertificateGapError`, naming the uncovered end states and declining to generate,
rather than silently narrowing the theorem into one that reads stronger
(`theory-compiler/STATUS.md`, ledger entry E-06). The whole A1 verification also
ran on exactly **one** 5-hole fixture; the pipeline's generality is not supported
by this evidence.

**`lp_potential` is sound but incomplete.** It never certifies a solvable
configuration, but some genuinely unsolvable ones admit no linear pagoda
(`engine-rig/DECISIONS.md` D-014, `engine-rig/interop/README.md`; the phrasing is
`CLAUDE.md`'s). E-06 is that caveat arriving in practice.

**Every planning number in this paper came from the bundled BFS stub, not from
Fast Downward.** Fast Downward *was* built and wired into A0/A0′ and agrees with
the stub on all three instances including the UNSAT variant, with no caller code
changed (`cold-start-a0/BLOCKER_FAST_DOWNWARD.md`,
`cold-start-a0/artifacts/fd_real.json`, `cold-start-a0/STATUS.md`) — but that is
a separate conformance artefact. The reproducible pipeline (`run_all.py`,
`prime.run_prime`) calls `solve(..., prefer="stub")` **on purpose**, so its
checked-in artefacts stay byte-identical whether or not a planner is installed.
§3.1's 12-step plan and every other planning figure in §3 are the stub's. The
stub is length-optimal for unit costs, so SAT/UNSAT verdicts and plan lengths are
sound at these sizes; nothing about search at scale is evidenced. A2 likewise ran
on the stub (`cold-start-a2/A2_REPORT.md` §8), and `engine-rig`'s shipped default
is still the stub.

Reproducing `fd_real.json` needs Fast Downward built locally: the artefact records
an absolute path into a `.toolchain/` directory that is gitignored and not in the
tree. Three of the repository's own statements about this disagree —
`cold-start-a0/A0_REPORT.md` §5 and §6.5 say "still not connected", its §8 item 4
says FD "could not be built (three failed compiler attempts)", and
`BLOCKER_FAST_DOWNWARD.md` and `STATUS.md` record the successful install dated
2026-07-28. The install is the latest. None of the three was edited, as no report
in this repository is; where they disagree the paper cites all of them and says
which is later.

**A2's goal was supplied, not induced,** as was A0′'s: the truncated trace never
wins, and the goal is confirmed empirically afterwards rather than derived
(`cold-start-a0/prime/A0P_REPORT.md` §5.3).

**Two of A0's three real defects were in the compiler, not the theory**
(`cold-start-a0/A0_REPORT.md` §6.4). A wrong backend is indistinguishable, from
inside the loop, from a wrong manual — and one of those bugs manufactured a
*false* UNSAT, which under constraint 6 would have triggered a certificate
obligation for a theorem that is false. The four-co-derived-forms design is meant
to make that drift visible; here it took a human reading the plan output.

### 7.4 What the battery cannot yet certify

Restated from §6 so that the limitations section is complete on its own. Every
ranked metric's verdict in `battery/artifacts/discrimination.json` is
`underpowered` or `no-data` — 24 of 29, the other 5 being direction-less
diagnostics returned as `not-ranked` — and that is arithmetic rather than
softness: a
two-sided sign test over four paired games has a smallest attainable p of
**0.125**, so no metric can clear p < 0.05 on this data however cleanly it
separates, and six non-tied paired games is the floor for the test to be able to
clear the bar at all. There is no Schema arm and there may never be
(`baseline-arms/SCHEMA_LOCATE.md`); the model ladder is a substitute and
`battery/DECISIONS.md` D-B-004 argues why it is weaker. The battery's author also
wrote the metric definitions, which is structurally impossible to blind, and four
metrics on A0 are marked `[seen]` post-dictions in `battery/PREDICTIONS.md` rather
than being passed off as predictions.

One further data-integrity note belongs here rather than in §6: the ledger the
battery reads was produced in part by two concurrent sessions on the same track
sharing one budget and one API quota without knowing about each other
(`baseline-arms/INCIDENTS.md` INC-BA-003). The runs are individually accounted,
but any aggregate read off that ledger inherits the incident.

### 7.5 The one thing this paper claims

That the pipeline runs end to end on self-built deterministic worlds; that on
those worlds a manual can be perfect on replay and wrong about the world in a way
that was predicted in advance and later measured; that reversibility of a
mechanism mattered more than breadth of trajectory in the one controlled
comparison run; that a machine-checked impossibility can be produced whose
weights crossed a data boundary between two independently developed tracks and
whose empty axiom list is a check that has been made to fail on purpose; that the
refutation loop closed on a false theorem in six recorded beats; and that a
passive metrics battery over existing trajectories immediately found three of its
own metrics measuring something other than what they claim.

Everything else in `Theoria.md` — the ordering claim, the bill shape, transfer,
the exam, the cost magnitude — is unevidenced here and is not claimed.
