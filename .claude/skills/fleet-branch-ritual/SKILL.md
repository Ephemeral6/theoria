---
name: fleet-branch-ritual
description: Start-of-ticket ritual for a Theoria fleet prompt (开工仪式) — cut agent/<ticket>-<slug> from the newest master, add an isolated git worktree, read the PARTNER_SYNC.md tail and the territory's STATUS/DECISIONS, then run the territory's test suite as a green baseline before anything is changed. Use at the very start of a session that was handed a monitor/prompts ticket (P-NN, A-N, B-N, R-N, M-0), or whenever the user says 开工 / 建分支 / 建 worktree / "start the ticket" / "set up a branch and worktree" / "get a baseline before I change code". Do not use for merges onto master, and do not use once the branch already exists.
---

# fleet-branch-ritual

Every Theoria ticket opens the same way, and the opening is where sessions
lose an hour: branching off a stale master, forgetting the worktree and
stepping on another session's tree, starting work without knowing whether the
suite was already red.

One command does all of it and leaves a machine-readable ticket context that
the other three fleet skills read.

## Do this

From the **main checkout** (`C:\Users\user\Desktop\theoria` / repo root):

```bash
python .claude/skills/fleet-branch-ritual/scripts/start_ritual.py \
  --ticket P-24 --slug fleet-skills --territory .claude/skills
```

Arguments you will actually vary:

| flag | meaning |
|---|---|
| `--ticket` | the prompt id exactly as the工单 writes it: `P-24`, `A-1`, `R-1` |
| `--slug` | the branch slug from the工单's 分支制 line: `agent/p24-fleet-skills` → `fleet-skills` |
| `--territory` | repo-relative dir the ticket may write to (`engine-rig`, `proxy`, `.claude/skills`) |
| `--worktree` | override path; default `<repo parent>/theoria-wt-<ticket>` |
| `--sections` | how many PARTNER_SYNC sections to print (default 3) |
| `--no-tests` | skip the baseline (only when the工单 says the territory has none) |
| `--now` | fix the UTC instant, for a reproducible rehearsal |

Then `cd` into the printed worktree path. **Every later command in the ticket
runs from there**, not from the main checkout.

## What it guarantees

1. **Base is the newest master.** `origin/master` unless local `master`
   already contains it. The resolved sha is printed and recorded — it becomes
   `base_commit` in your MANIFEST, so 溯源 works without you retyping it.
2. **Isolation.** A dedicated worktree, so the ~14 other sessions on this repo
   cannot see your half-finished tree and you cannot see theirs. It refuses to
   reuse a branch that already exists rather than silently moving it.
3. **Orientation before action.** PARTNER_SYNC tail + the territory's
   STATUS/DECISIONS/RUN_STATE/INCIDENTS, printed, not summarised.
4. **A baseline, honestly labelled.** The suite runs *before* you touch
   anything. If it is red, that is a fact about master — say so in
   PARTNER_SYNC and do not absorb it into your ticket.
5. **Ticket context** at `<worktree git dir>/fleet-ticket.json` — prompt_id,
   branch, base_commit, territory, seed, baseline. It lives in the git dir, so
   it can never be committed by accident. `runs-archive`, `verify-gate` and
   `handoff-close` all read it, which is why you never retype these values.

## Rules this skill will not bend

* **It never touches master.** No commit, no push, no checkout of master.
* **It never widens your territory.** `--territory` is the contract; the other
  skills enforce it at 收工 time.
* A red baseline is reported, never repaired here. Repairing another
  ticket's red from your branch is how two sessions collide.

## After it

`runs-archive` (留痕) → work → `verify-gate` (验收) → `handoff-close` (收工).

## Territory conventions

`reference/territories.md` lists which directories have suites, the special
commands (`fixtures.generate_all`, `tools.run_all`), and which territories are
prose-only so that "测试：不适用" is the honest line rather than a missing one.
