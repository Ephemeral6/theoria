# 2026-08-01T050800Z-R2-1-anchor-refusal · running notes

Prompt R2-1 · branch agent/r2-1-roll-forward-drift · base 4c08ea6
Opened 2026-08-01T05:08:00Z

## 2026-08-01T05:08:09Z

R2 (DECISIONS.md decision 3) measured the drift and built probe.anchor_drift, then deliberately left the wiring: 're-seating the manual's state would make certify's replay trivially green -- destroying the only instrument that detects a wrong manual. That is somebody else's call.' The owner made the call on 2026-08-01. This ticket does the wiring and does NOT re-seat, so the premise of that trade is never tested here. Read first: certify.py has its OWN replay loop (lines 185-240, its own local state from initial_state() over store.actions) and does not call loop._roll_forward at all. _roll_forward has exactly one call site, loop.py:1216, feeding the probe designer. So the two consumers were already separate.

## 2026-08-01T05:08:14Z

Three defects in the wiring, each fixed. (1) probe.design computed anchor_drift only under 'if cfg.generated:' and generated is NOT the default -- so on exactly the four paid legs of 2026-07-31 the number was never taken. Now unconditional, one dict referenced twice (report['anchor'] is report['frontier']['anchor']) so two readings cannot disagree. (2) Where it was taken, nothing read it: grep for anchor_drift outside tests found the write and no consumer; ProbeEconomy.gate's two refusals (n_frontier<=1, min_bits) cannot see it. Now an unconditional refusal in loop.py alongside the other three. (3) _roll_forward swallowed a raising step with a bare break and returned the half-rolled state; caller could not tell. Now returns (state, rollout) with actions_replayed / actions_in_trace / stopped_early / stopped_because. The returned state is unchanged -- not re-seated.

## 2026-08-01T05:08:27Z

The anchored twin earned its keep inside its own ticket. First draft of _roll_forward counted the None terminator of FrameStore.actions as an early stop. world/frames.py:190 says verbatim 'the last element must be None -- there is no action after the final observed frame', i.e. it is the designed end of the trace, not a failure. So stopped_early was True on every clean leg -- a flag true on healthy runs is not an instrument, and had only the refusing test existed it would have shipped green. test_roll_forward_reports_a_clean_replay caught it; the fix separates the benign terminator from a raising step, and the test now pins the terminator explicitly.

## 2026-08-01T05:11:32Z

What this ticket does NOT do, recorded so it is not mistaken for done. The drift itself is unrepaired: the manual still desynchronises on a mispredicted transition. The arm will now refuse those probes and explore instead of paying for them, which is the honest behaviour, not a fix for the underlying step. Re-seating remains open, and D-R2-002 splits it into the narrow reading (the one _roll_forward call site -- does NOT touch certify, since certify.py runs its own replay loop) and the broad one (how the arm maintains manual state everywhere -- would touch certify). D-R2-001 decision 3 did not distinguish them, and the distinction is the entire cost of the decision it deferred.

## 2026-08-01T05:11:46Z

Unconditional, not a knob -- and the precedent is explicit. loop.py's other three refusals (vacuous streak, repeat, theorize cap) carry a comment saying they 'are measurements, not policy, so refusing on them needs no switch and applies to every leg'. Drift is likewise a measurement, so the fourth joins them without a switch. CONSEQUENCE FOR THE NEXT ROUND, flagged rather than buried: this changes live behaviour, so the next leg's probe counts are NOT comparable to R1/R1b. On the archived legs it would have refused 35 of 52 designed probes and explored instead. That is a change in what the arm does, arriving outside the one-knob-per-round protocol because it is a defect repair rather than a treatment -- whoever runs R3 should state it in the round record rather than read the drop in probes as an effect of their knob.

## 2026-08-01T05:35:05Z

A GUARD TEST FAILED AND WAS REWRITTEN -- recorded loudly because rewriting a guard is how a line gets lowered. tests/test_frontier_generation.py::test_the_design_report_grows_no_key_on_the_default asserted the design report is byte-identical with the frontier switch at its default. R2 wrote it deliberately ('ablation -- the default -- did not move a byte'). It failed on this branch. It bundled two properties: (a) the FRONTIER does not move on the default -- still true, untouched, already covered by its own neighbouring tests, both green; (b) the REPORT is byte-identical and the arm behaves identically -- now false on purpose, because the anchor must be on the default path, which is the path that spent the money. The test now asserts (a) plus 'everything ranked on is byte-identical, only the anchor was added', and is RENAMED to test_the_default_switch_changes_nothing_except_the_anchor_reading so its name does not claim more than it checks. Cost stated, not waved: ablation is no longer a byte-exact replay of 2026-07-31.
