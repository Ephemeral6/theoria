---
name: handoff-close
description: 收工 ritual for a Theoria ticket — write RUN_STATE.md from the ticket context, append a correctly-formatted 状态/测试/阻塞/下一步 section to PARTNER_SYNC.md under an append-only guard that refuses to modify one byte another track wrote, stage only the declared territory (never `git add -A` at the repo root), and push the agent branch without touching master. Use at the end of a ticket, whenever the user says 收工 / 交付 / 写 RUN_STATE / 更新 PARTNER_SYNC / push 分支 / "wrap up" / "hand this off" / "report status to the board", and use `close` first when you want the pre-handoff checklist rather than the individual steps.
---

# handoff-close

The board is shared by ~14 concurrent sessions that never talk to each other.
Everything they know about your work, they read off `PARTNER_SYNC.md`,
`RUN_STATE.md` and the branch. This skill makes that record correct by
construction, and refuses the two mistakes that cost the fleet most: editing
someone else's paragraph, and `git add -A` at the repo root.

Run from **your worktree root**, after `verify-gate` is green.

## 1 — the checklist first

```bash
python .claude/skills/handoff-close/scripts/handoff_close.py close
```

Prints, and stops at, whatever is not yet true: run archive, MANIFEST,
RUN_STATE (and whether it still has TODOs in it), verify.sh, PARTNER_SYNC
append-only, nothing uncommitted, not on master. Add `--push` to push when
every line is green.

## 2 — RUN_STATE.md

```bash
python .claude/skills/handoff-close/scripts/handoff_close.py run-state
```

Writes the template into your run dir, pre-filled with prompt/branch/base/
territory from the ticket context. Its sections are the ones a later session
actually needs: **Delivered** (one paragraph per工单 item, each with the
artefact path and the number that proves it), **Gaps** (what the工单 asked for
and did not get — 做不到就如实报 gap), **Verification**, **Open items**.

Fill every `TODO`. `close` fails while any remains — a RUN_STATE with TODOs in
it is a false handoff.

## 3 — PARTNER_SYNC.md

```bash
python .claude/skills/handoff-close/scripts/handoff_close.py sync \
  --tag p24-fleet-skills \
  --status "四个 skill 落地，演练一遍，子代理照文档走通" \
  --tests  "rehearsal 12/12 green" \
  --blocked "无" \
  --next   "M-0 合并后由下一批会话实际使用"
```

Produces exactly the board's format:

```
## [<track>] <ISO8601> <milestone-tag>
状态：<one line>
测试：<pass/fail summary>
阻塞：<none / description>
下一步：<one line>
```

**The append-only guard is the point.** Before writing, your `PARTNER_SYNC.md`
must still be a byte-prefix-match of both `HEAD:PARTNER_SYNC.md` and
`<base>:PARTNER_SYNC.md`; after writing, it is re-checked. If you (or an editor,
or a reflow, or a "fixed a typo") changed one earlier byte, it refuses and tells
you the line number. Restore with `git checkout <base> -- PARTNER_SYNC.md` and
re-append.

Write only your own paragraphs. Nobody replies on this board — a section that
answers another track belongs in your own section as an observation.

`--body-file` takes a longer pre-written section (the format check still runs)
for the reports that need more than four lines.

## 4 — commit and push

```bash
python .claude/skills/handoff-close/scripts/handoff_close.py commit -m "P-24: 舰队技能库"
python .claude/skills/handoff-close/scripts/handoff_close.py push
```

* `commit` stages `<territory>` and `PARTNER_SYNC.md` by explicit pathspec, then
  **refuses if anything outside them got staged**. `--also <path>` for a path the
  工单 authorised, and it will appear in the refusal message if you forget.
* `push` refuses master/main, refuses a branch that disagrees with the ticket
  context, and refuses to push over uncommitted tracked changes. It never
  merges: M-0 does that.

## The line this skill will not let you cross

自报完成 and 核实 are two different columns on the monitor's board, and this
skill only ever fills the first. If `verify-gate` was red, say so in `阻塞` —
a green-sounding `状态` over a red gate is the exact failure the double column
was built to expose.
