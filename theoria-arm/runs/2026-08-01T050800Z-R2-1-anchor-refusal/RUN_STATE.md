# R2-1 · RUN_STATE

Prompt: `(unset — owner instruction, "你开始修", 2026-08-01)` · branch
`agent/r2-1-roll-forward-drift` · base `4c08ea6` · 2026-08-01.
Territory: `theoria-arm`. Run archive: `theoria-arm/runs/2026-08-01T050800Z-R2-1-anchor-refusal`.

## Delivered

**1. The anchor is computed on every path.** `probe.design` called
`anchor_drift` only under `if cfg.generated:`, and `generated` is not the
default — so on exactly the four legs that were paid for on 2026-07-31, the one
number that says whether the experiment is about this world was never taken.
It is now `report["anchor"]`, written unconditionally
(`theoria-arm/inner/probe.py`). It costs no action and no model call, which is
what lets it be unconditional. One dict, referenced by both `report["anchor"]`
and the `frontier` block, so two readings of one fact cannot disagree —
`ProbeEconomy.observe` already refuses to recompute vacuity for that reason.

**2. It is now a refusal, not just a reading.** Nothing read the anchor: a
repo-wide grep for `anchor_drift` outside tests found the write and no
consumer, and `ProbeEconomy.gate`'s two refusals (frontier collapse, bits
floor) cannot see it. It is now the **fourth** unconditional refusal in
`theoria-arm/inner/loop.py`, beside the vacuous streak, the repeat and the
theorize cap, and it is asked **first** — the other three price an experiment,
the anchor asks whether there is one. On the archived legs this refuses 35 of
52 designed probes, and all 35 of those had landed off-frontier
(`runs/20260801T0900Z-R2-frontier-by-generation/MEASUREMENT.json`,
`totals.off_frontier_while_drifted = 35`), so it is a saving, not a trade.

**3. `_roll_forward` says how far it got.** It swallowed a raising `step` with
a bare `break` and returned the half-rolled state, so a manual that crashed on
action 3 of 40 handed back a 37-action-stale state and said nothing. It now
returns `(state, rollout)` with `actions_replayed` / `actions_in_trace` /
`stopped_early` / `stopped_because`. **The returned state is unchanged, byte
for byte** — this is the instrument, not the repair.

**4. The decision is on the record.** `theoria-arm/DECISIONS.md` `D-R2-002`,
including the split of `D-R2-001` decision 3's premise (below) and the
narrowed guarantee (Gaps).

**5. Tests.** `theoria-arm/tests/test_anchor_refusal.py`, 15 tests. Every check
that can say no is watched saying no **and** saying yes: an anchored probe must
still be spent; a manual with no `render`, or a design with no store, must not
be refused (silence is not evidence); a clean replay must not report itself as
stopped early.

## Gaps — what the工单 asked for and did not get

**1. The drift itself is unrepaired, and that is the whole of it.** The manual
still desynchronises permanently on one mispredicted transition; 35 of 52 is a
statement about how often, not a thing this ticket fixed. The arm will now
refuse those probes and explore instead of paying for them, which is the honest
behaviour and not a fix for the underlying `step`. Re-seating remains open.

**2. `D-R2-001` decision 3's premise needed splitting, and this ticket did not
test either half.** It reads: "Re-seating the manual's state on the world's
frame ... would make certify's replay trivially green — destroying the only
instrument that currently detects a wrong manual." `loop._roll_forward` has
exactly one call site and `certify.py` runs its **own** replay (its own local
state, from `initial_state()` over `store.actions`, reporting
`first_divergence` / `step_raised`). So *narrow* re-seating — of the value that
one call site receives — would not touch certify; *broad* re-seating, of how
the arm maintains manual state everywhere, would. `D-R2-001` does not
distinguish them and the distinction is the entire cost of the decision it
deferred. This ticket needed neither and did neither.

**3. A guarantee was narrowed and a guard test was rewritten.** Detail in
`D-R2-002`; summary here because it is a gap against `D-R2-001`, not against
this工单. `test_the_design_report_grows_no_key_on_the_default` asserted the
design report is byte-identical with the frontier switch at its default. It
failed on this branch — correct behaviour for a guard — and it bundled two
properties. The **frontier does not move on the default** (same hypotheses,
same order, same ids) still holds, untouched, and keeps its own neighbouring
tests, both green. The **report is byte-identical and the arm behaves
identically** is now false, deliberately: the anchor must be on the default
path because the default path is the one that spent the money, and an
instrument that must be switched on to see the defect it was built for is the
defect. The test now asserts the surviving property and is **renamed**
`test_the_default_switch_changes_nothing_except_the_anchor_reading`, because a
name that claims more than it checks is worse than a failure. **Cost, stated
rather than waved: `ablation` is no longer a byte-exact replay of 2026-07-31.**

**4. Two pre-existing reds on master were not fixed, by choice.** Both are in
this territory but neither is this ticket's, and both are carried verbatim
under Verification. Fixing them here would have mixed a money constant and
another ticket's run artefacts into this branch.

## Verification

| | |
|---|---|
| verify.sh | `-- 6/7 green  <<< NOT GREEN (1 red)` — the red is `tests`, red on the two pre-existing failures below and on nothing else |
| tests | 674 tests: **672 passed, 2 failed**. Baseline at base `4c08ea6` was 657 passed / 2 failed — same two, +15 tests. (pytest's final summary line did not reach the capture file; counts derived from the progress block and cross-checked against the baseline total.) |
| — the two reds, verbatim | `FAILED tests/test_arm.py::test_the_archive_stays_accountable` — `re-deriving every manifest reproduces it byte for byte / drifted: ['20260731T231654Z-R1-g50t-a', '20260731T231654Z-R1-sk48-b', '20260801T001851Z-R1b-g50t-a', '20260801T001851Z-R1b-sk48-b']`<br>`FAILED tests/test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive` — `AssertionError: claude-opus-5: ceiling $12.00 is below $13.4480, which is what this table's own stated rule -- max(timeout x rate, 4x worst call) -- produces from the archive.` |
| — why not fixed here | The first is the R1/R1b run archives (`curves/` still untracked); committing another ticket's run artefacts from this branch is the cross-ticket collision the branch discipline exists to prevent. The second raises a **spend ceiling constant**, and the owner has just ruled on money (`register #13`); raising a money limit inside an unrelated ticket is not this ticket's call. |
| MANIFEST | `theoria-arm/runs/2026-08-01T050800Z-R2-1-anchor-refusal/MANIFEST.json` — 7 artefacts, reproduces (`[PASS] MANIFEST hashes reproduce`) |
| sealed-pile API calls | 0. Offline throughout: no key, no network, no model call, no action sent. Guard: `[PASS] sealed pile untouched` — 21 sealed / 4 dev, no sealed id in 7 changed files |
| credentials | `[PASS] credential never entered a tracked file` — `.env` gitignored and untracked; no secret value in 12,761 tracked files |
| boundary | `[PASS] boundary -- only theoria-arm changed`; `PARTNER_SYNC.md` appended, never edited |

## Open, and deliberately not closed here

**1. The next round's probe counts are not comparable to R1/R1b.** This changes
live behaviour on the default path — on the archived legs, 35 of 52 designed
probes become refusals. It arrives outside the one-knob-per-round protocol
because it is a defect repair rather than a treatment. **Whoever runs R3 must
state this in the round record**, or the drop in probes will be read as an
effect of their knob.

**2. A merge note.** `phase3/c1-theorize-deferral` also has staged changes to
`theoria-arm/inner/loop.py` and `theoria-arm/DECISIONS.md`. Checked: its
`loop.py` hunks end at line 1164, mine start at 1206; it inserts into
`DECISIONS.md` at :567, I append at EOF. No overlap, no conflict expected —
recorded so whoever merges second does not have to re-derive it.

**3. A defect this ticket caught in itself, kept because the shape recurs.**
The first draft of `_roll_forward` counted `FrameStore.actions`' trailing
`None` as an early stop. `world/frames.py` says the last element must be `None`
— "there is no action after the final observed frame" — so it is the designed
end of the trace, and `stopped_early` was true on **every clean leg**. A flag
true on healthy runs is not an instrument. **The refusing test passed the whole
time; only the anchored twin failed.** That is the second time on this arm that
only a negative control could tell a working check from a check that always
fires.

**4. The entropy floor still has never refused anything.** 52/52 on the paid
legs. This ticket gives it a sibling that demonstrably can say no, but does not
establish that the floor itself checks anything. Someone should watch it refuse.

**5. `theoria-arm/verify.sh` is new.** It did not exist before this ticket;
generated by `.claude/skills/verify-gate`. It will stay red while the two
pre-existing failures stand, which means the next session in this territory
inherits a red gate that is not theirs either.
