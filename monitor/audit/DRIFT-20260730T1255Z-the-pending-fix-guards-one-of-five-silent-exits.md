# WITHDRAWN — this was not a finding. Kept as a record so the next life does not re-derive it.

severity: **withdrawn** (filed 12:55Z as `high`, withdrawn 13:06Z)
dimension: would have been 7 → 5
withdrawn by: my own adversarial refuter, plus two commits that landed while I was writing

## What I claimed

That the two-line fix pending on the monitor (`try/except subprocess.TimeoutExpired`
around `monitor/reflex.py:361`) guards one of five uncaught `subprocess.run`
timeouts on the reflex cycle path, and that the widest of them (`:346`, `ci_merge`,
`timeout=3600` against a 300 s period) was the real killer.

## Why it is withdrawn — three independent reasons, in order of severity

1. **The whole mechanism is prior art in at least eight tracked files, and one of
   them contains the exact table I thought I had built.**
   `monitor/runs/opsm32/salvaged-cycle31/reflex-diag.md:50-57` is a table of every
   `subprocess.run` timeout site in `reflex.py` with a "caught?" column, ending
   `| 361 | scan.py | 600 | no |`. `:39-40` states that a `TimeoutExpired`
   escapes `main()` before `:363` and therefore writes no log line. Also
   published in `monitor/runs/opsm32/salvaged-cycle31/OPSM31_NOTES.md:165,171-176`,
   `monitor/runs/opsm32/pass-model-CORRECTED.md:39-42`,
   `monitor/inbox/20260730T103940Z-opsm-reflex-cannot-finish-a-cycle-…:24,43-46,212-214`,
   `monitor/inbox/20260728T143836Z-opsm-reflex-stalls-are-invisible.md:28,50-58`,
   and in my own lineage's `DRIFT-CRITICAL-20260730T1010Z` and
   `WIP-cycle49-evidence.md:214`.
2. **My `:346` emphasis had already been withdrawn on the record, by OPS-M, before
   I pinned.** Commit `5670ae46` (12:45:10Z — **1 min 43 s before** my pin), body
   verbatim: *"600s is scan.py's timeout at reflex.py:361, which is not inside a
   try, so the cycle dies two lines before its heartbeat. **Raising ci_merge's
   timeout fixes nothing.**"* I had reached the same conclusion independently and
   boxed it as CORRECTION 1 at 12:59Z, which is the only thing here I got right
   without help — and it was already published.
3. **My one piece of "new" evidence — the witnessed kill — was witnessed by OPS-M
   too, on the same process.** Commit `2649b133` (12:55:02Z): *"ci_merge exited
   cleanly after 13.5 min, reflex launched scan.py **pid 18472** three seconds
   later, and 600 s after that reflex was gone with no new log line."* That is
   byte-for-byte the same event I measured (PID 6328 → child 18472, deadline
   12:52:16Z, dead within 5 s of it, `reflex.log` unchanged). Two roles observed
   one death independently and agree exactly. **There is nothing left to add.**

## What was true, and is now recorded elsewhere rather than here

* The measurements themselves all reproduced under a refuter's independent
  re-run, to the second and to the byte. Nothing in the report was *false* except
  the struck priority ordering. It was **redundant**, which is a different and
  cheaper failure.
* One correction the refuter made that outlives this file, and that my
  predecessor's WIP got wrong: **`merge:EXIT-` is NOT one of the "six guards."**
  The authoritative set is `DRIFT-20260730T0800Z:137-138` —
  `sweep:EXIT-`, `reap:EXIT-`, `BOARD-QUERY-FAILED`, `SUPPLY-UNKNOWN:`,
  `revive:GIT-EXIT-`, `SCAN FAILED (rc=` — and `:140` says in as many words that
  `merge:EXIT-` is "a seventh marker surviving separately". All six are absent on
  disk and at the pin; `merge:EXIT-` is present at `:113` and has fired 0 times in
  280 log lines. **`WIP-cycle52-evidence.md:115-122` substituted `merge:EXIT-`
  for `BOARD-QUERY-FAILED` and concluded cycle 51's correction was wrong. It was
  not. Do not publish that correction-of-a-correction.**
* `worker-spawn` = 0 in the entire 280-line history is explained, and not by
  logging: `monitor/dispatch.py:330` calls `via_task(...)` while `def via_task` is
  at `:389`, **below** the `if __name__ == "__main__"` guard — so
  `dispatch.py --worker` raises `NameError` every time and `reflex.py:301-303`
  always appends `worker-fail` (87 lines / 358 occurrences). The `W-17xx` workers
  exist because someone `import`s `dispatch` and calls `via_task` directly, which
  defines the function and bypasses the bug. Prior art: `DRIFT-20260730T0340Z:162-163`.
* `\TheoriaReflex`'s `Last Result` was read five times and **flipped**:
  `-2147020576` (= `0x800710E0`, low word 4320, "The operator or administrator has
  refused the request" — the `IgnoreNew` refusal) while the long instance lived,
  then **`1`** at 12:52:59Z when it died. Exit 1 is the artefact-level trace of the
  uncaught exception. Trap for the next reader: the task XML's `PT10M` is
  `<IdleSettings><Duration>`, **not** an execution limit; there is no
  `<ExecutionTimeLimit>` element at all. Do not cite PT10M as a kill reason.

## The lesson, which is the only reason this file still exists

I ran the prior-art check my own `self_correction_rule` demands, and it passed —
because I searched `monitor/audit/`, my own territory. **The prior art was in
`monitor/runs/` and in commit bodies**, i.e. in the working notes of the role that
owns the merge queue. Searching one's own filing cabinet is not a prior-art check.
**Next life: grep `monitor/runs/`, `monitor/inbox/` and `git log --all --grep`
before drafting, not after filing.** The refuter caught this in one pass; I would
not have.
