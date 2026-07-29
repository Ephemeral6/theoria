# human_actions.jsonl — how it was swept

26 rows, `2026-07-27T10:50Z` → `2026-07-28T19:04Z` (~32 h). Checker GREEN
(`python fleet-study/verify.py --data fleet-study/runs/20260728T233850Z-S17/harvest`):
61 commits resolved, 45 files present, 1 deleted-but-in-history, 0 unresolvable.

**By category** — `paste_launch_prompt` 9 · `adjudicate_direction` 3 ·
`correct_the_agent` 3 · `delegate_authority` (new) 2 · `approve_budget` 2 ·
`oauth_or_credential` 2 · `manual_trigger` 2 · `grant_permission` 1 ·
`supply_infrastructure` 1 · `request_feature` (new) 1. Confidence 14 high /
11 medium / 1 low; `utc_confidence` 1 exact, 25 inferred. **7 of 26 rows say the
action was automatable in principle** — H-04 (pile-cut confirmation; the same
class of ruling went to the monitor a day later), H-06 (toolchain install:
policy, not capability), H-09, H-11, H-17, H-20, H-23.

## Sweep

`git log --all` (549 commits, full bodies) against a 用户 / 人类 / the user / 授权 /
批准 / 粘贴 / manual / unblock pattern; `PARTNER_SYNC.md`; `monitor/{loop_state,
state,HANDOFF,CHARTER,spec.py,agents.py,board/board.log,mailbox,inbox,audit,ops,
res,ops-status,dispatch-logs}`; all 8 `monitor/bus/*/{in,out}.jsonl` read as raw
UTF-8 (bus.py stdout is mojibake here); `browser-ops/`; `baseline-arms/
{BUDGET_REPORT,INCIDENTS}.md`; `cold-start-a0/DECISIONS.md`; `arc-recon/`;
`fleet-study/data/*.jsonl`; and the four user-memory files under
`~/.claude/projects/.../memory/` — leads only, outside the repo, not citable.

**Provenance rule:** an app session (`APP-*`, `OPS-*`, `RES-*`) has no entry in
`monitor/dispatch-logs/` and no API can start one, so its appearance is a human
paste. Every `W-*` board worker **does** have a dispatch log, so none are human.

## What I could not determine

1. **The true number of pastes.** The 9 launch rows cover ~19 individual pastes,
   but the monitor's reincarnation discipline (restart every ~3 h against a 5 h
   quota window, `HANDOFF.md`) implies further 「继续」 pastes over 32 h that leave
   no trace. **The launch count is a floor, not a total.**
2. Whether H-08's $103 approval was a sentence or a paste (the tree pins the
   8-minute window, not the form); whether H-17 was a human ask at all
   (confidence low; caveat says so).
3. Exact minutes — 25 of 26 rows are bracketed by commits/logs, not observed —
   and anything the human said that produced no commit, file or bus message.

## Deliberately excluded

- **The permission wall.** The brief lists it as a human unblock; the record says
  otherwise. `monitor/loop_state.json:notes.launch-root-causes` and commit
  `cbd5d34` credit the whole three-layer fix (consent flag, settings.local
  defaultMode, `_runner.py --dangerously-skip-permissions`) to the monitor.
- **B-1 browser ops** is two events, both in: H-12 (extension) and H-13 (OAuth).
- **`monitor/worker.cmd` windows.** Three files say extra capacity is added *by the
  user* opening terminal workers; every `W-*` id in `board.log` has a dispatch log,
  so the mechanism was built and never used by a human. Counter-evidence, not a
  human action.
- **Never-performed asks:** registering `TheoriaServe` as administrator (raised 3
  cycles, worked around); the `team@arcprize.org` letter (drafted, unsent); the R2
  release-licence application; finding which account owns the `.env` key. Also the
  4-hour gate stoppage (16:37Z–22:18Z), escalated to the user twice by the auditor
  — commit `cbf3535` shows the monitor applied the fix itself.
- **Agent-authored "approvals" phrased as the user's:** `BUDGET_REPORT.md`'s
  「批准已到（工单 P-7）」 is the monitor's own ticket. H-08 is kept because it
  predates P-7; the P-7 relay is H-09, a paste.
