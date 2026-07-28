# assembly_new.jsonl — method note

Rows **A-04 … A-19** (16), continuing `fleet-study/data/assembly.jsonl` (A-01…A-03).
Read-only harvest; nothing outside this `harvest/` directory was written.

## Method

* Contract commits enumerated with `git log --all --format='%H|%ad|%s' --date=iso-strict --
  monitor/res/ monitor/ops/ monitor/prompts/ monitor/CHARTER.md monitor/bus/HOSTED.md` (9).
* Behaviour read from machine-written traces only, never from a contract's self-description:
  `monitor/board/board.log`, `monitor/bus/*/{in,out}.jsonl`, `monitor/ops-status/*.json`.
  Bus JSONL is parsed as UTF-8 directly — `bus.py` stdout is mojibake on this machine.
* Commit author dates are `+08:00`; every time in the dataset is converted to UTC.
* All 46 distinct citations re-checked: `git cat-file -t` returns `commit` for every
  `git:` sha; every `file:` path exists in the worktree. Zero failures.

## What was measured

* **Role creation → working: 71 s.** `6f6b87a` at 15:06:39Z; RES-4's first bus message
  15:07:50Z, first board claim 15:07:58Z, first delivered item 16:05:16Z (+58 m).
* **One clause, seven roles, one commit.** The `扇出纪律` block added by `fb813ce` is
  byte-identical (single sha256) in RES-1/2, OPS-A/B/M/R and `prompts/W-worker.md`.
* **37 agent instances from 3 contract families**, all clones (ops 68–70 %, RES-1/2 69 %,
  RES-3/4 78 % of RES-1); 25 W-* all boot from one template (`_runner.py:43`).
* **Hot reconfiguration: 4 real ones**, edit-to-observed-effect 4 m 56 s / 7 m 31 s /
  5 m 10 s / 42 m 13 s. Hardest case: standing researchers held **max 1 item for 4 h 16 m
  and 6 items**, then 2 in the same second 7 m 31 s after `fb813ce`. **All four were pushed
  by a bus/mailbox notice** — no silent-edit case exists. One refusal: OPS-A (15:03:32Z)
  reported its harness outranks the on-disk contract, a measured ceiling on the mechanism.
* **Auto-supply is a myth in this window:** `reflex.log` has 0 `worker-spawn` and
  68 `worker-fail`; capacity came from a human opening `worker.cmd` windows.
* Interfaces: bus `15ecf80`, board `32059928`, heartbeat `b23c110a` — each has a causal
  sentence in its own introducing commit, and each failure class recurred afterwards.

## Could not determine

1. **How many human actions a new role costs.** No launch/paste log exists anywhere in
   the repo (A-05, `confidence: low`). The `human_actions.jsonl` gap is still open.
2. **Whether a contract edit alone (no push) reconfigures anything.** All four observed
   reconfigurations were accompanied by a bus or mailbox message (A-08).
3. **Whether a `W-worker.md` edit reaches workers.** No worker activity follows the last
   edit (`99d1d5d`); template edits are inheritance at clone time, not hot reload (A-14).
4. **Whether the inherited disciplines were obeyed** by the clones, beyond the two
   self-reports in A-09/A-11. Not attempted here.
5. **The "12 h mailbox latency" as a measurement.** It is the 720-min sleep in OPS-R's
   contract; the mailbox only lived ~8 h 19 m. Largest *observed* silence: 8 h 13 m.
6. **Whether "the fleet" or "the monitor" edited the assembly machinery.** Every commit
   carries the same git identity, so authorship cannot separate them (A-19).
7. The slogans in the S17 order (`逐件派单不可扩展`, `分不清闲着与掉线`) appear **only**
   there and in `IDEA.md`, both downstream of this study — circular, so the rows cite the
   introducing commits' own docstrings and bodies instead.
