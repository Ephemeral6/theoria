# AGENT-G — adversarial review of OPS-M's draft ruling on `s4-freeze` / `s4-e23-tiers`

Independent re-derivation. Nothing below is taken from `opsm31-out/` on trust; every
number was recomputed. Artefacts I produced: `advG-master-ctl.txt` (master control
gate run), `advG-merged.txt` (merged-tree gate run), `advG_probe.py` + its output,
`scratch/` (the `--allow-absent-pool` experiment).

Worktrees created (mine, disposable): `.worktrees/opsm32adv-s4f`,
`.worktrees/opsm32adv-mrg` (master + `s4-freeze` merged), `.worktrees/opsm32adv-ctl`
(pristine master).

---

## Headline

**Two things are wrong. One claim is REFUTED outright, one is mislabelled in a way
that will misdirect the person who has to fix it, and the ruling's framing of the two
branches as a "pair" is factually wrong. The DISPOSITION (hold both, send back to
`freeze/`'s owner) SURVIVES and is if anything better supported than the draft states.**

- **Claim 6 is REFUTED.** `--allow-absent-pool` is not inert. It returns rc=0.
- **Claim 1's label "ENVIRONMENT ARTIFACT" is wrong** and contradicts the ruling's own
  claim 3. The red is *true*: the committed table really is stale, in every checkout,
  including master's.
- **`s4-e23-tiers` strictly contains `s4-freeze`** (fast-forward descendant). They are
  not a pair of siblings; one supersedes the other.
- New finding the draft misses: a **third** independent breaker (`Mechanism C`,
  `pool.abspath_is_main_checkout`) that is red-by-construction between the main
  checkout and any worktree, with a byte-identical pool and zero staleness.

---

## Claim 1 — "the red is an ENVIRONMENT ARTIFACT, not branch-caused; tip and merged arms are byte-identical" — **WEAKENED**

The *evidence* survives. The *label* does not.

**What survives.** I diffed the four transcripts myself. `s4f-tip.txt` vs `s4f-mrg.txt`
and `s4e-tip.txt` vs `s4e-mrg.txt` differ in exactly 3 lines each, all three being the
`PATH-EXISTS` / `GATE cmd=` / `PYTHONPATH=` header lines that carry the worktree path.
No substantive line differs. "The merge contributes nothing" is correct.

I also ran the comparison the draft did *not* run, which is the one that actually
matters for claim 5, and it confirms the direction:

| tree | `freeze/verify.sh` | result |
|---|---|---|
| pristine `origin/master` (`cc7e414e`) | ends at `[14]` | **RC=0, DRAFT COMPLETE, 2 notes** |
| master + `s4-freeze` merged | ends at `[16]` | **RC=1, 1 check failed** |

(`advG-master-ctl.txt`, `advG-merged.txt`.) Single FAIL in the merged run, and it is
15b, exactly as claimed.

**What must be restated.** "Environment artifact" is the wrong noun, and it fights the
ruling's own claim 3. The pinned-vs-live numbers:

| ref | `pool.lines` pinned in `freeze/BUDGET_TABLE.json` |
|---|---|
| `cc7e414e` (master) | 11,874 |
| `s4-freeze` | 12,929 |
| `s4-e23-tiers` | 12,995 |
| **live pool, during this review** | **14,057 → 14,068 → 14,088** |

Master's own committed budget table is stale by 2,214 lines *right now*. Master is
green solely because master's `verify.sh` never looks. The branch did not introduce a
defect and did not hit an environment quirk — it added a check that truthfully reports
a pre-existing condition. The branch's own header comment says so in as many words:
"the pool still grows with every proxied call, so a red here after a spend is still the
gate working."

Why this matters operationally, not just rhetorically: if OPS-M publishes the words
"environment artifact", `freeze/`'s owner will reasonably go looking for an
*environment* fix — make the pool reachable inside `%TEMP%\ci-merge-*`, e.g. by
teaching `resolve_pool` to consult `git rev-parse --git-common-dir` instead of
string-matching `.worktrees`. Mechanism B proves that fix would not help: the pool
would then be found and the table would be stale anyway. The ruling would have sent
the owner down the one road it has itself already closed.

**Restate as:** *the red is real and pre-existing, is not caused by the merge, and is
not fixable by regenerating the table — 15b as written pins live append-only data and
is therefore unsatisfiable by construction.*

## Claim 2 — Mechanism A (`resolve_pool` walk-up fails under `%TEMP%`) — **SURVIVED**

I re-derived this from the branch's own module rather than reading the prior probe.
Loaded `.worktrees/opsm32adv-mrg/freeze/build_budget_table.py`, substituted `REPO`,
called `resolve_pool("proxy/var/spend_gate.jsonl")`:

```
C:\Users\user\Desktop\theoria                              -> ...\proxy\var\spend_gate.jsonl
C:\Users\user\Desktop\theoria\.worktrees\opsm32adv-mrg     -> ...\proxy\var\spend_gate.jsonl
C:\Users\user\Desktop\theoria\.worktrees\anything-at-all   -> ...\proxy\var\spend_gate.jsonl
C:\Users\user\AppData\Local\Temp\ci-merge-3o91k447         -> None
C:\Users\user\AppData\Local\Temp\ci-merge-zzzzzzzz         -> None
```

`tempfile.gettempdir()` = `C:\Users\user\AppData\Local\Temp`; `".worktrees" in
parts` is `False`. `monitor/ci_merge.py:513` is `wt = tempfile.mkdtemp(prefix="ci-merge-")`,
confirmed by reading it. The walk-up is guarded by a literal `if ".worktrees" in parts`,
so it cannot fire there.

I tried the alternatives the brief suggested and they do not hold:
- *Not* a permissions/unreadable-file problem — `resolve_pool` returns `None` from
  `os.path.exists` being False, and the file is readable from every path that finds it.
- *Not* a cwd problem — `HERE` comes from `os.path.abspath(__file__)` and `REPO` from
  `os.path.dirname(HERE)`, so the gate's cwd is irrelevant.
- `freeze/verify.sh:1158` is `bt_out="$(python "$HERE/build_budget_table.py" --verify 2>&1)"`
  with no `--allow-absent-pool`. Confirmed by reading the line.

Mechanism A is correctly identified.

## Claim 3 — Mechanism B (live append-only pool ⇒ any committed table goes stale) — **SURVIVED, and understated**

Confirmed and sharpened. During this review the pool went 14,057 → 14,088 in roughly
five minutes. `advG_probe.py` shows the committed-vs-live `pool` diff on the merged
tree: `lines` 12,929→14,057, `max_seq` 12,929→14,057, `actions` 5,737→6,967, `sha256`
`40135ef5…`→`36c521be…`, `campaigns` 109→110.

Sections that move: `['balance', 'pool', 'verdict']`.

Corroboration the draft does not use: the author *already tried* re-pinning. Between
`s4-freeze` and `s4-e23-tiers` the only freeze deltas include a regenerated
`BUDGET_TABLE.json` (12,929 → 12,995) — and `s4-e23-tiers` is red anyway, 7 attempts
running. The remedy of "just regenerate" has been empirically tested by the branch
owner and has failed twice.

## Claim 4 — "no table is green in both states" — **SURVIVED** (this is the load-bearing claim and it is airtight)

I attacked this hardest, per brief item 3, by reading `main()`'s comparison in full
rather than trusting the summary. The comparison is:

```python
strip = lambda blob: {k: v for k, v in json.loads(blob).items() if k != "generated_from"}
if strip(on_disk) != strip(text):
```

There is **no** tolerance, **no** window, **no** `max_seq` bound, **no** env var
(`grep environ` in `build_budget_table.py` returns nothing relevant), and **no** flag
that removes a section from this comparison. The only exclusion is `generated_from`.
The four CLI flags are the whole surface: `--verify`, `--allow-absent-pool`,
`--emit-pool-digest`, `--self-test`. None of them touch the comparison.

Empirically (`advG_probe.py`), the three states:

| committed table | checkout | sections that move | verdict |
|---|---|---|---|
| `present: true` (as shipped) | pool reachable | `balance, pool, verdict` | RED |
| `present: true` (as shipped) | pool absent (`%TEMP%`) | `balance, pool, projection, verdict` | RED |
| regenerated `present: false` | pool reachable | `balance, pool, projection, verdict` | RED |

The `pool` dict is `{present, path, why}` when absent and a 15-field dict when present,
so the `pool` section is *structurally* unequal across the two states. No committed
JSON can match both. Claim 4 is not merely observed, it is closed.

**New finding — Mechanism C, which the draft misses.** `read_pool` emits

```python
"abspath_is_main_checkout": os.path.normpath(path) != os.path.normpath(os.path.join(REPO, rel)),
```

This is `True` when the pool was found *by walking up* (i.e. from a worktree) and
`False` in the main checkout. All three refs pin `True`. So a table regenerated in the
**main checkout** is red in **every worktree**, and vice versa, on this field alone,
with a byte-identical pool and zero elapsed time. (The field's name is also inverted
relative to its meaning, which is worth telling the owner.) This is a third,
staleness-independent breaker and it strengthens claim 4.

## Claim 5 — "`[15]` exists only on these branches; merging makes `freeze/` permanently red for every subsequent branch" — **SURVIVED on mechanism, WEAKENED on the word "permanently"**

Re-derived from scratch, all four links:

1. Master's `freeze/verify.sh` ends at `[14]`. Confirmed.
2. Master's `verify.sh` **never invokes `build_budget_table.py`** — grep returns only
   two hits, both inside quoted table-row *data* strings about budget arithmetic, not
   invocations. (It also never invokes `build_engine_manifest.py`, so all of `[15]` is
   new.) Note master *does* already ship `freeze/build_budget_table.py` and
   `freeze/BUDGET_TABLE.json`; what the branch adds is the *invocation*.
3. I actually performed the merge (brief item 1): `git merge --no-ff --no-edit
   origin/agent/s4-freeze` onto `origin/master` in `.worktrees/opsm32adv-mrg`. **Clean,
   no conflict**, 19 files changed, `freeze/verify.sh` +753 lines. The merged
   `freeze/verify.sh` hashes to `e2c509ff…`, **byte-identical to
   `origin/agent/s4-freeze:freeze/verify.sh`**. It does not resolve in master's favour;
   verify.sh is not conflicted; `[15]` and `[16]` land verbatim.
4. `[15]` is unconditional and fatal, per brief item 2. I read the shell: 15b is
   `bt_out="$(python "$HERE/build_budget_table.py" --verify 2>&1)"` / `if [ $? -eq 0 ]`
   / else `bad ...`, and `bad()` is `red "  FAIL  $*"; FAIL=$((FAIL+1))`. There is no
   guard, no file-existence precondition, no `note`/warning downgrade, no early
   `exit` before it. It is not skippable. `WARN` does not affect rc; `FAIL` does.
   The transcript confirms rc=1 with `FAIL` count 1.
5. `monitor/gates.py:gate_for` returns `kind="verify"` from `find_gate`, and
   `ci_merge.py` runs a gate per touched directory — so a branch touching `freeze/`
   runs it, and one not touching `freeze/` does not. Territory scope is as claimed.

So the mechanism is right and the master-green → merged-red transition is measured, not
theorised.

**What must be restated.** "Permanently red for EVERY subsequent branch" overstates it
in one way that a careful reader will catch. `ci_merge` runs the gate on the *merged*
tree. A `freeze/` branch whose content *is* the 15b repair would therefore be gated by
its own fixed `verify.sh` and could merge. The block is real but self-clearing by the
fix; it is not a deadlock. Restate as: *merging lands `[15]` in master and makes the
`freeze/` gate red for every subsequent `freeze/` branch except one that repairs 15b
itself.* That is still decisive — it converts two flags into a territory-wide block —
but the corrected wording is what makes the recommendation in claim 7 coherent rather
than paradoxical.

## Claim 6 — "`--allow-absent-pool` is inert" — **REFUTED**

This is the one outright error. The flag is functional; the draft's own reasoning about
ordering is correct but the conclusion drawn from it is too strong.

Experiment (`scratch/`, reproducing `verify.sh`'s own relocation technique): copy of
`build_budget_table.py` with `OUT_JSON`/`OUT_MD` redirected to a scratch dir and
`resolve_pool` stubbed to `return None`, i.e. the queue's `%TEMP%` state exactly.

```
1. regenerate the table in a POOL-ABSENT state              -> rc=0, wrote table
2. --verify, no flag           (pool absent, table absent)  -> rc=1   POOL ABSENT: ...
3. --verify --allow-absent-pool (same state)                -> rc=0   "still describes this tree"
```

Step 3 is green. `--allow-absent-pool` therefore **is** the flag it says it is.

What is true is narrower: *given the table currently committed on these branches*
(which pins `pool.present: true`), the flag cannot help, because the JSON section
comparison has already set `rc = 1` on the `pool`/`balance`/`verdict` drift before
control reaches `if not args.allow_absent_pool`. The flag is dead **against this
table**, not dead in general.

**Why the distinction changes what OPS-M should say.** As written, claim 6 tells the
owner "the flag you built is useless." That is false and will cost the owner a round
trip. The accurate statement is that there *is* a configuration in which the queue goes
green — commit a `present: false` table and add `--allow-absent-pool` to
`verify.sh:1158` — and the reason to reject that configuration is not that the flag is
inert but that claim 4 then bites from the other side: such a table is red in every
real checkout, so the gate would pass in the only place it is enforced and fail
everywhere a human runs it. That is a worse gate, not a fixed one, and saying *that* is
what actually justifies claim 7.

**Restate as:** *`--allow-absent-pool` works, but it cannot rescue this table: the
`pool` section drift sets rc=1 before the flag is consulted. Committing a
`present: false` table so the flag can fire does make the queue green — and makes the
gate red in every real checkout, which is claim 4 from the other direction.*

## Claim 7 — "the fix belongs to `freeze/`'s owner: compare the pool-independent sections, check the pool half only where a pool exists" — **SURVIVED, needs one correction of scope**

I could not find a better owner or a cheaper correct fix. The prescription is right in
kind. One scope correction, from `advG_probe.py`:

The pool-dependent set is **four** sections, not one: `pool`, `balance`, `verdict`, and
`projection`. `balance` carries `gate_visible_usd`, `gate_visible_headroom_usd`,
`pool_only_measured_usd`, `programme_measured_usd`, `remaining_measured_usd`,
`gate_blind_spot_usd`, `actions_used`, `actions_remaining`; `verdict` and `projection`
are computed downstream of `balance["remaining_measured_usd"]` and
`balance["actions_remaining"]`. "Compare the pool-independent sections" is therefore a
larger carve-out than it sounds — it removes the *entire balance half* of the budget
table from the pinned check, which is the half `[15]`'s header says the stage exists to
protect. The owner should be told that plainly, because the honest fix may be that the
balance cannot be pinned at all and belongs in `POOL_DIGEST.json` (regenerated, not
verified) with 15b checking only structure and citations. `--emit-pool-digest` and
`POOL_DIGEST.json` already exist for approximately this purpose; that is the thread to
pull.

Also worth handing over: **Mechanism C** (`abspath_is_main_checkout`) must be fixed too,
or the table stays unpinnable across checkout kinds even after the staleness problem is
solved. The draft does not mention it, and an owner who fixes only A and B will be red
again immediately.

---

## Brief item 7 — the two branches are not a pair — **the draft's framing is wrong**

```
git merge-base --is-ancestor origin/agent/s4-freeze origin/agent/s4-e23-tiers  -> YES
git merge-base <the two tips>  ->  f47b6b30  (== s4-freeze's tip)
```

`s4-e23-tiers` is a **fast-forward descendant** of `s4-freeze`. It contains all seven of
`s4-freeze`'s commits plus two more (`39480314` E2/E3 two-tier ruling, `6eaf2da2`
MANIFEST regen) and adds `freeze/tier_conj.py`. No other branch has either as an
ancestor.

Consequences the draft should absorb:
- They are not two independent flags with a common cause; they are **one lineage flagged
  twice**, and the second flag is the author's own re-attempt after re-pinning the table.
  The 13-attempt and 7-attempt counts are not independent evidence.
- `s4-freeze` is **superseded**. Whatever disposition applies, `s4-freeze` should be
  retired rather than sent back separately; sending both back invites the owner to fix
  the same defect twice.
- It also means the draft's "for both branches the tip-alone and merged arms are
  byte-identical" is two observations of nearly the same tree, which is weaker
  independent support than it reads as. (It does not change the conclusion.)

## Brief item 8 — self-interference: did OPS-M's own measuring manufacture the evidence? — **No, and I can show it**

This was the most promising line of attack and it fails cleanly.

- `freeze/verify.sh` does not write to the pool. `grep spend_gate|spend_policy|proxy/`
  over the merged `verify.sh` returns two hits, both in comments. `build_budget_table.py`
  opens the pool read-only.
- Attribution of the growth, from the pool itself: of the last 1,200 records, 567 are
  `arc-recon-canary-quick` and the remainder are
  `theoria-arm:A3-campaign-devpile:...` pytest/gate traffic. The last 12 records at
  `12:47:16–12:47:21Z` are all `A3-campaign-devpile:g50t-5849a774` pytest records.
- **Zero** records in the entire 14,088-line pool carry a campaign matching
  `freeze|budget|ops-m|opsm`.

So the drift is driven by another agent's campaign, not by OPS-M's measurement. If
anything this *strengthens* claim 3: the pool grows without OPS-M doing anything at all,
which is precisely why no pinned table can survive.

One caveat to record honestly: because A3's pytest runs write `reserve`/`spend`/`release`
records, **any** agent running **any** proxy-touching test suite grows the pool. The
staleness clock is repo-wide and outside `freeze/`'s control. That is an argument for
claim 7's fix, not against it.

## Brief item 6 — the strongest case for the OPPOSITE disposition, honestly assessed

I built the best case I could for "merge them anyway". It is real but it loses.

**For merging:**
1. **The red is true, and the branch author says so.** `[15]`'s header states "a red here
   after a spend is still the gate working." On that reading OPS-M is refusing to merge a
   working gate because the thing it detects is inconvenient. Master today ships a
   budget table stale by 2,214 pool lines and a `verify.sh` that is green because it
   does not look. Merging replaces a silent falsehood with a loud truth. This is a
   genuinely uncomfortable position for the ruling and OPS-M should say it out loud
   rather than let the word "artifact" paper over it.
2. **Real content is stranded.** 19 files, ~3,475 insertions: 13 endpoint-wording
   divergences closed with stage `[16]` and its two negative controls, the S4-E1
   endpoint-1 holes, the E2/E3 two-tier ruling with `freeze/tier_conj.py`, three run
   manifests. `[16]` is green in both arms. None of that is implicated in the red.
3. **The hold is long and the merge is clean.** 13 and 7 attempts, `s4-freeze` held since
   2026-07-29T23:09Z. The merge has no conflict. Nothing else depends on these branches,
   so the hold is pure delay, not a growing conflict risk.

**Why it loses:** merging is not "accept one honest red." It installs an
**unsatisfiable** check into master's `freeze/` gate — unsatisfiable in the strong sense
established under claim 4, where no committed JSON is green in both pool states and
(Mechanism C) none is green across checkout kinds either. A permanently-red territory
gate in `ci_merge` is not a signal, it is a signal *destroyed*: every subsequent
`freeze/` branch flags for the same reason, and the next real `freeze/` defect arrives
into a gate that was already red and is indistinguishable from it. The correct way to
keep argument 1's honesty is to keep the red **out** of the merge gate and hand the
owner a check that can pass — i.e. claim 7.

Argument 2 is the one with actual weight, and it points at an amendment rather than a
reversal: `[16]`'s work is separable from `[15]`'s defect, so the send-back should ask
for a re-push that keeps `[16]` and repairs `[15]`, not a re-push from scratch.

---

## Bottom line

**Publish it AMENDED. Do not publish as written.** The disposition (HOLD, return to
`freeze/`'s owner) is correct, survived every attack I could mount, and is supported by
one measurement the draft does not contain — pristine master's `freeze/verify.sh` is
RC=0 green and the merged tree is RC=1 red with 15b as the single failure. But three
statements in the draft are wrong or misleading, and two of them would actively
misdirect the owner.

Required amendments:

1. **Strike claim 6 and replace it.** `--allow-absent-pool` is not inert — it returns
   rc=0 (`scratch/`, step 3). Say instead: the flag works, but the `pool` section drift
   sets rc=1 before it is consulted; and the configuration in which it *would* fire
   (`present: false` table + the flag in `verify.sh`) is rejected because it makes the
   queue green while making the gate red in every real checkout.
2. **Relabel claim 1.** Not "environment artifact" — the red is real and pre-existing;
   master's own committed table is stale by 2,214 pool lines and master is green only
   because its `verify.sh` never invokes the checker. Say "15b pins live append-only
   data and is unsatisfiable by construction." Otherwise the owner will attempt an
   environment fix (`resolve_pool` via `git rev-parse --git-common-dir`) that
   Mechanism B already rules out.
3. **Fix the pair framing.** `s4-e23-tiers` fast-forward-contains `s4-freeze`. One
   lineage, flagged twice; the 13/7 counts are not independent. Retire `s4-freeze` as
   superseded and return only `s4-e23-tiers`.

Recommended additions:

4. Soften claim 5's "permanently": the block spares a branch that repairs 15b, which is
   what makes the send-back actionable.
5. Add **Mechanism C** to the hand-off: `pool.abspath_is_main_checkout` is red-by-
   construction between the main checkout and any worktree, independent of staleness. An
   owner who fixes only A and B goes red again immediately. Note the field's name is
   inverted relative to its value.
6. Correct claim 7's scope: the pool-dependent set is `pool`, `balance`, `verdict`,
   `projection` — the whole balance half. Point the owner at the already-existing
   `--emit-pool-digest` / `POOL_DIGEST.json` as the intended home for unpinnable
   figures.
7. Record that `[16]` (endpoint wording, with negative controls) is green in both arms
   and is not implicated, so the send-back asks for a repair of `[15]`, not a redo.
