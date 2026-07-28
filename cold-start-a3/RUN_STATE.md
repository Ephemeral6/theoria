# RUN_STATE — cold-start-a3

Work order **P-17** (`monitor/prompts/P-17-a3-transfer.md`), branch
`agent/p17-a3-transfer`, worktree `theoria-wt-p17`.

## Status

**Complete.**  All five deliverables in the work order are done, plus two the
order did not ask for (a second negative control, and a blind control arm for
the theorize step).

| # | work order item | state |
|---|---|---|
| 1 | level 1 cold start, whole ring, `domain` + `problem₁`, playbook with a theorem-grade entry | **done** |
| 2 | level 2 zero-relearn with the carried books, metered against level 1 | **done** |
| 3 | control arm — level 2 from scratch, two-column cost table | **done**, and made *blind* rather than self-reported |
| 4 | negative control — one mechanism changed, the valve must catch it | **done**, two controls instead of one |
| 5 | `A3_REPORT.md` bounding C3 offline | **done** |

## Self-reported results, and how to check each without trusting this file

| claim | check |
|---|---|
| level 2 solved carrying the books, nothing relearned | `artifacts/bill_l2_transfer.json` — `engine_stages`, `candidates_adjudicated`, `theorize_rounds`, `dsl_clauses_written` all `0` |
| the domain travelled | `diff theory/generated_l1/theory.py theory/generated_l2/theory.py` — 35 lines, all level data |
| the transfer arm planned before spending an action | `cost_to_first_plan.world_actions == 0` in the same file |
| a wrong carried domain is caught | `artifacts/negative_controls.json` — `all_caught: true`, `none_claimed_a_win: true` |
| the books are not a private convention | `artifacts/domain_agreement.json` — `canonical_only_in_left: []` |
| nothing was faked | `python -m pytest` |

## Reproduce

```bash
cd cold-start-a3
python run_all.py                    # every arm, in order
python -m pytest                     # the suite
python -m tools.verify_readonly      # other tracks hashed before and after
```

## Ritual

* `runs/p-17/` — every artefact plus `MANIFEST.json` with `prompt_id`,
  `branch`, `base_commit`, `head_commit`, the determinism pins, and a sha256
  for each artefact and each book.
* `PARTNER_SYNC.md` — appended, own paragraphs only.
* branch pushed; `master` untouched.

## Territory

Created `cold-start-a3/` only.  `cold-start-a0`, `cold-start-a2`, `engine-rig`,
`theory-compiler`, `a0-spike`, `baseline-arms`, `battery`, `proxy`, `monitor`
and `arc-recon` were read and never written; `CONTRACTS/` is byte-unchanged and
a test asserts it.  Zero API calls, zero network, zero contact with the sealed
pile.

## Open, and deliberately not closed here

* **Four defects in the reused instrument** (D-A3-003/004/005/006/007) are
  reported to their owning tracks on `PARTNER_SYNC.md` and worked around inside
  `cold-start-a3/`.  None was fixed in place.
* **R-09** — the backend cannot compile a `?dir`-lifted rule — was confirmed a
  second time, blind, and cost the control arm a theorize round.  It is an
  expressiveness gap in the Python backend, not something this track can fix.
* **The theorize step is still a person.**  The control arm answers the
  "you already knew the answer" objection; it does not turn theorize into a
  measured component.  `A3_REPORT.md` §6.
* **No repair loop was run** on the caught negative controls.  A3 tests the
  valve; A2 ran the repair loop end to end on a different defect.
