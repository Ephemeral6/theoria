# S7-ledger-hashchain — the item was already done, the documents did not know

## What the item asked for, and why none of it was built

S7 asks for a forward hash chain over the proxy ledger: each record carrying the
previous record's digest, the head written into `run.json`, and an independent
`verify_chain()`. Estimated at "about 250 lines plus tests, inside one session".

All of it exists. It shipped as **S15-ledger-hashchain** (`cd94e19`, `3ddfedf`,
`96d0721`) on 2026-07-28, claimed 15:08Z and done 16:05Z — same territory, same
`D-024` / `RED-40` citation, same deliverable, same agent. S7 and S15 are the
same work item supplied to the board twice.

Verified rather than assumed, before touching anything:

* `proxy/ledger.py:248-263` — `record["prev"]` assigned inside the same lock as
  `seq`; `line_hash()` (`:123-133`) hashes the line's bytes as written.
* `canon.py:74` — `prev` is in the envelope, so a caller supplying one is
  refused (`canon.py:385-387`).
* `proxy/tools/verify_chain.py:55-170` — independent re-derivation, verdicts
  `PASS/FAIL/PARTIAL/UNCHAINED/EMPTY/MISSING`.
* `python -m pytest tests/test_chain.py -q` → **28 passed**.

So this run rebuilt nothing. The delivery is the gap that was actually open.

## The gap: three documents claiming the work was unbuilt

This is the failure mode this lane exists for — no error, no red test, and it
fails in the reassuring direction. A reviewer reading the proxy's own status
would have concluded the ledger had no chain, twenty-four hours after it got one.

1. `proxy/STATUS.md` carried the chain as a bullet under the heading
   **"What this does not yet do"**, describing it as "proposed in
   `monitor/inbox/20260728T2200Z-proxy-ledger-hash-chain.md`".
2. `proxy/REDTEAM.md` still opened its unclosed list with **"RED-40 stands."**
3. `proxy/STATUS.md`'s headline still read "295 tests pass". Actual: **323**.

## What was corrected, and what was deliberately left standing

The correction is not "RED-40 is closed", because it is not.

**RED-40 was never about editing a ledger.** The finding is that a file no proxy
ever wrote reconciles clean. The chain defeats tampering with an existing file —
edit, delete, insert, swap, front-truncate — but a forger writing from scratch
chains their own records just as easily. What defeats *that* is the head
published where the forger cannot reach it, and that half is still undone:
`runner.py:179-197` writes `ledger_head` into the per-run record, whose default
location `proxy/var/runs/` is gitignored. **The default path publishes nothing.**

Both documents now say the chain landed *and* that the original finding survives
it, in those terms. `STATUS.md`'s bullet stayed under "What this does not yet
do", because the part that is not done is the part that decides the question.

## The chain now runs on a gate path, with a control

Deferred follow-up from S15's own RUN_STATE, and the sharper half of the
problem: the chain had 28 unit tests and **ran in no gate**. A check that only
executes in a suite nobody runs at merge time is a claim, not an instrument —
the merge robot could have landed a commit that broke chaining outright.

`proxy/verify_contract.sh` gains one step, before the full suite. Per D-014 it
ships with a control that must trip: build a real five-record ledger, require
`verify_chain` to pass it, then flip one byte inside a landed record and require
a non-zero exit. The assertion message is the finding it would be reporting —
`EDITING A LANDED RECORD WENT UNDETECTED -- chain not checking`.

```
== the ledger chain verifies, and editing a landed record turns it red
clean stream: PASS
tampered stream: refused, exit 1
-- ok
```

Two false starts worth recording, since both were the gate catching me: the
first draft called `Ledger.append()` with a dict (the signature is
`append(event, run_id, arm, **fields)`), and the second used `env_step`, which
`canon` refuses without seven more fields. The fixture now uses the same
`env_meta` idiom `tests/test_chain.py` uses, and asserts the marker it later
edits is present — a control that silently stops editing anything is a control
that always passes.

## Verification

* `cd proxy && bash verify_contract.sh` → **VERIFY OK**, chain step green.
* `cd proxy && python -m pytest -q` → **323 passed**.

## Still open, and not attempted here

1. No gate compares a run's published head against a tracked manifest. Until
   one does, "the head is published" is discipline. This is the whole remainder
   of RED-40 and it is worth its own item.
2. `validate_ledger.py` has no chain check, so the chain is not on the scorer's
   audit path (S-12).
3. The frozen scorer `arc_v1` has no chain check and no forged negative control.
4. `upgrade_ledger.py` handles neither shard-merge chain breaks nor
   `chain.enabled=false` on lifted streams.

## Recommendation to the board

Close S7 as a duplicate of S15 and do not re-supply it. If the remaining work is
wanted, item (1) above is the one that matters — the other three are tidying.

---

# Correction, 2026-07-29T07:10Z — this run closed S7 too early, and overstated its own novelty

An adversarial re-check of every claim above found six errors. They are recorded
here rather than edited away, because the run's whole subject is documents that
kept asserting something after it stopped being true.

## The one that matters: S7 was not a duplicate, and closing it was wrong

S7's item body carries a monitor verdict paragraph that S15's does not:

> **监控裁决：做，且现在做。** … 释出包（P5/R2）里要能附**链头哈希与复核脚本**。
> 与**花费闸门共用同一条链**即可。

Neither shipped, and this run did not notice:

1. **The release package carries neither the head hash nor the checking script.**
   `release/MANIFEST.jsonl` lists `proxy/tools/validate_ledger.py` and three
   siblings but **not** `proxy/tools/verify_chain.py` and not
   `proxy/tests/test_chain.py`; `grep -rn verify_chain release/` returns zero.
   The manifest was last regenerated ~70 minutes *before* the chain landed and
   never re-run. Verified directly: `grep -c verify_chain release/MANIFEST.jsonl`
   → `0`.
2. **The spend gate does not share the chain.** `proxy/spend_gate.py` keeps its
   own money ledger under its own OS file lock and never touches
   `proxy.ledger.Ledger`; it has no `prev` and no `line_hash`.

So the recommendation "close S7 as a duplicate of S15 and do not re-supply it"
would have discarded two live requirements. **S7 should not have been marked
done.** Reported to the monitor and re-supplied as a follow-up item.

## Five factual errors above

3. **"the chain ran in no gate" is false** — and it was the entire justification
   for the new gate step. Master's `verify_contract.sh` already ended with
   `pytest proxy -q`, and `tests/test_chain.py` lives under `proxy/`, so all 28
   chain tests were already running at merge time — including the
   edit-one-field case the new step re-tests, and the CLI/exit-code path. The
   new step is a tenth step duplicating a subset of the ninth. It is defensible
   as a fast, legibly-named canary and it does trip correctly, but "the merge
   robot could have landed a commit that broke chaining outright" was not true.
4. **"three documents" was two.** `proxy/STATUS.md` was counted twice (once for
   the stale bullet, once for the stale test count) and `REDTEAM.md` once.
5. **"twenty-four hours" was ~14h12m** (chain 2026-07-28T16:03Z → this run
   06:15Z). The same wrong figure went out on the bus.
6. **"independent re-derivation" is overstated.** `verify_chain.py:52` imports
   `line_hash` from `proxy.ledger` — the walk is independent, the hash primitive
   is shared, so a defect inside `line_hash` is invisible to both the verifier
   and the new control.
7. **"that half is still undone" (head publication) is overstated**, and
   contradicts this document's own "Still open" item 1, which put it correctly.
   The mechanism exists and is tested: `--emit-head` writes a head to a tracked
   path and refuses to do so for any non-PASS stream, and an arm can lift
   `ledger_head` into its tracked `MANIFEST.json`. What is missing is
   **enforcement** — no gate compares a run's head against a tracked manifest.

On the REDTEAM.md framing: "RED-40 stands" was itself **true** by this run's own
argument. The stale text was the future-tense paragraph beneath it describing
the chain as proposed. The edit replaced a correct headline with "half closed";
the paragraph beneath it is what needed replacing.

## One new finding the re-check surfaced

A **PARTIAL verdict can be manufactured to read as benign.** A record that omits
`prev` increments an `unchained` counter, appends **no break**, and then becomes
the predecessor for the next line. So deleting a mid-stream record and stripping
`prev` from every record after it yields `breaks == []` and verdict `PARTIAL` —
whose docstring offers the innocent reading, "a stream lifted from v0, or one
written across the change that introduced the chain". `runner.py` writes that
verdict into the run record with nothing distinguishing it from legacy data.

Two things limit it: `PARTIAL` exits non-zero, and `--emit-head` refuses any
non-PASS stream. But a deletion reported as "no breaks" is the wrong shape, and
`tests/test_chain.py` only ever builds the benign case. Worth its own item.
