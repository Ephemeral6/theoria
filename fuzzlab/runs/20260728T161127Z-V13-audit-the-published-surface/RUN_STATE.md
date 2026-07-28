# V13 · audit the published surface

Prompt `V13-audit-the-published-surface`, lane `verify`, branch
`agent/v13-audit-the-published-surface`, base `68a8365`.
Input: `runs/20260728T152000Z-V10-fuzz-mutation-power/PUBLISHED_VS_AUDITED.md`
(V-10 branch merged into this one, so its mutation framework is present).

Machine-readable provenance: `MANIFEST.json`. Measured outputs: `partials/`.
Adversarial review: `ADVERSARIAL-1.md`.

## What was asked, and what was done

**1 · the effect invariant (main).** `cegis_miner` publishes `effect.*` and all
four existing invariants audited guards. Added
`effects_agree_with_the_evidence`, whose truth comes from
`fuzzlab/oracles/motion.py` — a new oracle that reads the world's rendered
frames and **imports nothing from `engines`**. It iterates `result.all_rules`,
so the lifted class (15.6% of published rules, previously unlooked-at) is in
scope. Also added `rules_fire_on_the_action_they_name`, and widened
`applicable_equals_support` to `all_rules`.

**2 · the rest by value.** Added `probe_frontier.costs_are_the_world's` (V-10's
rank 2). V-10's rank 3 (`mdl_segmenter.mdl_accounting_is_closed`) was **not**
done; the reason is recorded in `BUGS.md` § S4 along with the rest of the
unfinished ranking. `segment_operator` is a repair, not an audit, and fuzzlab
may not edit `engine-rig` — filed as a one-line engine fix, not as an invariant
that would fire forever.

**3 · honest coverage.** The four bare `return []` openers in
`props/lp_potential.py` became `finding.skipped` with reasons. Standing campaign
re-run. `BUGS.md` § "V-13 supersede" **appended** — the prior round's report is
not edited.

## Numbers

| | before | after |
|---|---|---|
| invariants | 23 | **26** |
| `lp_potential`, each of 4 | 500 / 500 evaluated | **267 / 500** |
| `cegis_miner`, each of 6 | 480 / 500 (four of them) | **465 / 500**, uniform |
| `probe_frontier.costs_are_the_world's` | — | **500 / 500** |
| cegis mutants | 8 | **15** |
| probe mutants | 18 | **20** |

`cegis_miner`'s coverage went **down**, and that is the result rather than a
regression: the old 480 counted worlds whose whole rule set was `blocked_<D>`
rules saying nothing ever happens.

Every new invariant is killed by at least one mutant, measured, and one mutant
(`cm-drop-effect-destination`) was pre-registered as a survivor and survived.
Two V-10 survivors are refuted: `cm-shrink-lifted-support` and
`pf-flatten-reported-costs` now die.

**An adversarial reviewer found five things and all five were real.** They are
logged individually in `BUGS.md` § S7, including the one that matters most: this
round's own `costs_are_the_world's` shipped a guard excluding the exact branch
its docstring twice claimed to check. Nothing was fixed silently. Two findings
belonging to other engines are in § S5 and § S6.

## The two things that went differently than planned

**The effect invariant filed 21 false accusations before it worked.** They were
real output, not a slip, and reading them (rather than counting them) found a
corpus defect: `_mine` mined `seg.tracks[0]`, which is a **static obstacle** in
21 of 57 minable worlds. Those `blocked_*` rules with `effect: none` are true of
a rock; the battery was simply not testing the engine in 37% of its worlds.
`_mine` now selects the mover's track. Detail in `MUTATION.md` § "A corpus
defect found by trying to file a false accusation" and `BUGS.md` § S2.

**A parallel cross-check (E-11) reads the same fact as an engine defect** —
1209 published rows judged false. This round disagrees and says why in
`BUGS.md` § S2: `Rule.as_json()` carries no object identifier, so a rule mined
off a rock is a true statement with an unnamed subject, and the defect that is
certainly real is the contract one. E-11's findings were treated as leads, not
as established fact; none of them is repeated here as confirmed.

## Discipline

* written: `fuzzlab/` only. `engine-rig/` **0 bytes**, `CONTRACTS/` **0 bytes**
  (`git status --porcelain -- engine-rig CONTRACTS` is empty).
* `BUGS.md` and `MUTATION.md` are **append-only** in this round: the diff is
  +154 / +173 lines and **0 deletions**.
* no network, no API calls, no `.env` read, zero sealed-pile contact.
* committed to this branch only; nothing pushed, master untouched.
