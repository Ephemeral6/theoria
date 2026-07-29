# Adversarial review of V-13 — disposition record

> **Read this first: this file is NOT the reviewer's report.**
>
> An independent adversarial agent was run against V-13 before delivery, with a
> read-only worktree and instructions to break two claims: (a) that the effect
> oracle does not use the machinery of the engine it judges, and (b) that the
> new mutants are not killed by construction.
>
> Its report was delivered to the coordinator, **not to this session**. Two
> requests for the verbatim text were sent and neither returned before delivery,
> so **the reviewer's own words are not archived here** — the original survives
> only in the reviewer's transcript
> (`tasks/a70138cdd77b67d7b.output`), and that transcript should be treated as
> the authoritative copy.
>
> What follows is **this author's disposition record**: each finding as relayed,
> what was done about it, and — for every factual claim — an independent
> re-measurement performed here rather than a restatement of the reviewer's
> number. Where my measurement disagreed with the relayed one, mine is given and
> the disagreement is flagged. Nothing in this file should be quoted as the
> reviewer's assessment.

Prompt `V13-audit-the-published-surface`. Findings accepted: **5 of 5**.
Findings rejected: **0**. All corrections are logged in `fuzzlab/BUGS.md` § S7,
in place, alongside the claims they correct.

---

## R1 — `costs_are_the_world's` excluded the branch its docstring claimed to check

**Finding.** The invariant's guard was `if expected > 0`, which is exactly the
complement of the zero-cost case, while two docstrings
(`props/probe_frontier.py`, module header and the invariant's own, "which is
checked below") claimed the zero-cost convention was asserted. An engine
returning `0.0` instead of `inf` at zero cost would pass silently.

**Independently verified here.** `frontier.py:42-44` is
`self.entropy / self.cost if self.cost else float("inf")` — the convention is
real and is the only falsifiable part of `value`, which is otherwise a property.
`worlds/hypset.py:21` generates zero costs deliberately: *"Zero is not a
hypothetical -- the ranking divides by it"*. Measured: **11 of 40** worlds carry
a free action (27.5%, consistent with the relayed 27.6%).

**Disposition: guard fixed, not the docstring.** Leaving a false "checked"
inside the invariant written to separate *not checked* from *checked and clean*
would have been this round's own defect one level up.

**Evidence the repair is real, both measured here:**

| | `pf-zero-cost-value-is-zero` |
|---|---|
| against the shipped `if expected > 0` guard | eval=11, **SURVIVED** |
| against the fixed guard | eval=11, **killed 11/11** |

---

## R2 — `_mined_subject`'s docstring was false, and had leaked into a user-visible message

**Finding.** The docstring was present tense, quoted a stale number, and named
the wrong cause ("the segmenter did not list the mover first"). That sentence
had been copied verbatim into the `finding.skipped` message, so anyone triaging
the finding would have been sent to the wrong engine.

**Independently verified here, and the relayed numbers did not reproduce.** The
relay reported *27 of 200 fallbacks, 25 of them shape-matching*. My measurement
on the shipped code over 500 worlds gives **15 fallbacks of 500**, of which
**14** have a track with the mover's exact bounding box whose `anchors` carry
`None`, and 1 has no `None` at all. The discrepancy is explained by a second
defect I found while checking: `_mine` was committing to the first segmentation
operator that mined *anything* rather than the first that mined *the mover*.
Fixing that moved subject-unknown worlds **54 → 15**. The relayed figures are
consistent with the pre-fix code; the instances cited (worlds 12 and 19)
reproduce exactly.

**Disposition:** docstring and message rewritten with the true cause. The
underlying `mdl_segmenter` track-continuity defect is written up with instances
and a reproducer as `BUGS.md` § S5, explicitly *not* asserted to share a root
with the parallel object-id bit-width report.

---

## R3 — a published number that the repository could not reproduce

**Finding.** `MUTATION.md` cited *"4455 transitions over 200 worlds"* for the
motion oracle's cross-check against `gridworld.Rules.step`. The shipped test
swept **five worlds, 93 transitions**. The measurement had really been made, but
only in a scratch script, so the repository published a figure it could not
regenerate.

**Disposition: the sweep is the test now.**
`tests/test_oracles.py:test_motion_agrees_with_the_generator_across_the_corpus`
runs 200 worlds and asserts `checked == 4455`, so the figure cannot drift from
the code without a test failing. Verified: passes, and 4455 is the true count.

---

## R4 — `cm-freeze-lifted-direction` does not test what it was described as testing

**Finding.** The mutant pins a lifted rule's `effect.direction` to a concrete
compass name, but the engine **never emits one** — a census of 357 rules found
`effect.direction` taking only `{None, "?dir"}`. So the mutant is the only thing
that can reach `_claimed_delta`'s `if direction in DELTA` branch, and what it
measures is the invariant's tolerance of a malformed field, not the semantics of
the variable. The description claiming it closed V-10's lifted-rule gap was an
overclaim.

**The decisive experiment, reproduced here.** Delete the two lines
`if direction in DELTA: return DELTA[direction]` and re-run:

```
cm-freeze-lifted-direction         eval=34  inert=6  SURVIVED
cm-lift-admits-a-wrong-direction   eval=32  inert=8  killed by effects_agree_with_the_evidence
```

**Disposition.** The claim is struck from the mutant's own `description`, in
place, rather than removed. A new mutant `cm-lift-admits-a-wrong-direction`
tests the path the engine actually produces — `?dir` resolved per witness to
`DELTA[action]` — by widening a lifted rule's support to a transition where the
mover did not move, which `miner.py:_normalise` forbids by construction. It is
**killed 32/32** and, as above, still dies with the branch deleted. That is the
mutant that licenses any claim about lifted rules being audited.

---

## R5 — dangling reference

`RUN_STATE.md` and `MANIFEST.json` referenced this file before it existed.
Resolved by this file, with the caveat at the top about what it is and is not.

---

## The reviewer's third argument on the E-11 dispute, which decided it

E-11 counted 1209 published `rule_hypothesis` rows as false because they carry
`effect: none` while the world's mover demonstrably moved. This round argued the
rows are true of their subject (a static obstacle) and that the caller, not the
engine, chose that subject. The reviewer supplied a third argument that holds
regardless of how the first two are read:

> **`fuzzlab` never publishes.** `props/cegis_miner.py:_mine` calls
> `engine.mine(transitions)` and never passes `out_path=` — the only argument
> that makes `cegis_miner.run()` emit candidates. There is no writer to
> `candidates.jsonl` anywhere in `fuzzlab`. So "1209 **published** rows" has no
> referent in this battery's output; the rows exist in memory, inside a property
> run, and nowhere else.

Verified here: `grep -rn "out_path" fuzzlab/` returns nothing outside comments.
Recorded as `BUGS.md` § S6, together with the contract defect the episode does
expose and which stands — `miner.py:Rule.as_json()` publishes no object
identifier, so a `rule_hypothesis` cannot say which object it describes.

---

## What the review did not overturn

On question (a), the independence of the effect oracle, nothing was refuted.
`fuzzlab/oracles/motion.py` imports only `typing`; every occurrence of the word
`engines` in that file is prose. The one genuinely contestable point — that
`_mined_subject` reads `transitions[0].state.shape` and `t.state.anchor`, which
originate in `mdl_segmenter` — is argued in the function's docstring: those are
*input* to the miner and the same input its guards are evaluated against, and
they are used only to establish **which object** was mined, never **what
happened to it**. The truth of every effect comes from the pixels.
