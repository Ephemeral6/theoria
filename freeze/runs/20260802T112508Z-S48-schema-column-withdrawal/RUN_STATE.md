# S48 — the Schema (复现口径) column is withdrawn, and the withdrawal is now enforceable

**Cell:** S48 · **Territory:** `freeze` · **Prompt id:**
`S48-schema-column-withdrawal-claims-text` · **Worker:** W-9204
**Branch:** `agent/s48-schema-column-withdrawal-claims-text` ·
**Base:** `9e478dd8` · **UTC:** 2026-08-02T11:25:08Z
**Spend:** $0.00 — no ARC action, no desk call, no model call, no network, zero
sealed-pile contact. Only `freeze/` was written, plus the `PARTNER_SYNC.md`
paragraph and `monitor/inbox/`.

---

## What landed

`baseline-arms` proposed on 2026-08-01 that `Theoria.md:271`'s **Schema（复现
口径）** column be **withdrawn** rather than left blank
(`monitor/inbox/20260801T0600Z-PROP-schema-column-withdrawal.md`, ruling in
`baseline-arms/SCHEMA_ARM_RULING.md`). Four territories were addressed; none had
moved. **This ticket is freeze's half only** — `CLAIMS_TEXT.md` — and the other
three are asked for rather than edited.

Four places in `CLAIMS_TEXT.md`, each dated 2026-08-02 in the text itself, each
new number carrying its coverage:

1. **The premise correction (was L23-28).** It said only the first sentence —
   *the `schema_repro` arm does not exist*. The second sentence had been true for
   six hours when that was written: **something else does exist**, the upstream
   trajectories on the 4 development-pile games, ingested as the
   `schema_upstream` reference row (8 runs, `battery` D-B-019). Both are now
   stated, with a coverage line that travels with every citation — 开发堆 4 局
   (not 25), 8 runs, and **1 of the 2 collections records tokens**, so every
   call-class metric has data from that one only. `needs_human` is removed:
   `SCHEMA_ARM_RULING.md` §3 prices and closes all three alternative routes.
2. **C1.** The arithmetic **never contained Schema** — `STATS_RULES.md` §1 judges
   a single-sample rate over the claim-layer 19, with the control arms
   constructively zero. So this is not a restatement forced by an absence; it is
   **removing a dependency that never bore weight**. And 「唯一」 now has its
   scope nailed to the text: 「**在本实验的同壳三臂中唯一**」, with an explicit
   disclaimer that the paper makes **no claim either way** about upstream
   Schema on U3/U4.
3. **C2 — the heaviest.** 「vs Schema 平坦」 is withdrawn, and **not because it
   was not measured**. E2 needs a per-call cost and the upstream corpus has no
   cost field under any spelling (`battery/adapters/schema_traces.py`); E2
   returns `not-applicable` on the whole arm, 8/8 runs. It is **unmeasurable on
   this material, not pending** — so it cannot sit in the claim text as a
   comparator and cannot be parked in the limitations section as a future fill.
   `battery/PREDICTIONS.md:78`'s direction pre-registration is left **verbatim
   untouched** — editing a pre-registration destroys it — and only its
   settlement moves: the `schema` term settles as **不可评**, scoring neither a
   hit nor a miss.
4. **C5.** The 成立版 second sentence no longer divides Theoria by upstream; it
   reports upstream as an **external reference**, 0.756–2.85 亿 per episode
   (dedup convention, 4 runs), and says in as many words that the two are
   different shells under different pricing conventions and **their ratio makes
   no claim**. Hard constraint 1 now says **withdrawn** rather than 合规留空,
   and deletes the 「实测 2.04–3.41 亿」 interval: it reproduces under neither
   counting convention measured this round (dedup 0.756–2.85 亿; naive traversal
   3.19–13.19 亿) and its provenance does not exist in this repository.
   **量级留，区间删。**

## The negative sample, and why it needed a rule about acquittal

The item's demand: after withdrawal, **anywhere still citing the `⟨复现值⟩`
placeholder must make freeze's verify red** — a withdrawn-but-citable
placeholder is the original problem under a new name.

`freeze/schema_column_withdrawal.py`, wired into `verify.sh` as stage **[21]**
alongside its selftest, in the shape stage [19] already uses for the §3.0
withdrawal. The subtlety is that **recording a withdrawal necessarily names the
thing withdrawn** — "the `⟨复现值⟩` placeholder has been withdrawn" contains the
placeholder. A scanner that convicted on the token alone would make the
withdrawal unwriteable. So the rule is the one
`exam/tools/check_withdrawn_claims.py` reached for the same problem: a mention is
**acquitted when a withdrawal marker stands within two lines of it**, convicted
otherwise. Measured inventory: `复现值` occurs at four lines in `CLAIMS_TEXT.md`
and the bracketed token at two; every one is either ordinary prose (`无同壳复现
值`) or a withdrawal record.

**The positive control the item also asked for.** Only the reproduction claim was
withdrawn, not the material. The gate fails if the `schema_upstream` row
disappears, or if any citation of it loses its coverage. Withdrawing a claim and
deleting the evidence are different acts, and a gate that could not tell them
apart would license the second.

**Controls: 11/11, every one seen to fire** (`SELFTEST.txt`), including the
positive control that the real file passes unmutated. One of them caught a real
defect in the first draft: the C2 check scanned for the bare word `不可测`, which
also appears in the explanatory paragraph, so deleting the load-bearing sentence
left the gate green. It now scans the whole clause `**不可测**，而不是待测`.

## Gates

* `python freeze/schema_column_withdrawal.py --verify` → **exit 0**
* `python freeze/schema_column_withdrawal.py --selftest` → **11/11, exit 0**
* `bash -n freeze/verify.sh` → **syntax OK**
* `bash freeze/verify.sh` → **ran. Stage [21] PASS on both checks**; the script
  reports `DRAFT INCOMPLETE -- 3 check(s) failed`, and all three are master's
  own: `MANIFEST.json` drift, `BUDGET_TABLE` recompute, and
  `check_locations.py`. Clean master reproduces the same three in the same
  order, matching `runs/20260801T0700Z-E1-kind-census/RUN_STATE.md:80-84`.
  **This ticket adds no failure and removes none.**

  *Correction to this file's first version.* It said the script was blocked and
  never reached stage 0. Two early attempts were indeed killed by memory
  pressure — bash could not fork — but a later attempt completed, and reporting
  a transient block as a standing fact overstated it. The numbers above are from
  a completed run.

  One consequence worth carrying: the baseline is already red at 3, so **"freeze's
  verify goes red" cannot be shown by the exit code** — it is already 1. That is
  why the negative sample lives in the checker's `--selftest`, one mutation per
  rule each required to fire, which is the kit's own convention
  (`e2_withdrawal.py`) and why none of the three standing reds can mask a new
  `bad` line from stage [21].

## Gaps — stated, not worked around

1. **freeze's verify has three standing failures and this ticket closes none of
   them** — `MANIFEST.json` drift, `BUDGET_TABLE` recompute, and
   `check_locations.py`. They are master's, they predate this branch, and they
   are somebody's work but not this ticket's. Naming them here so that a future
   reader who runs `verify.sh` and sees red does not attribute it to stage [21],
   which passes.
2. **Three other `freeze` files still name the retired arm** —
   `MANIFEST_DRAFT.md:537`, `PENDING_FIVE.md:141,294`, `STATS_RULES.md:26,2099`
   all say `schema_repro` 不存在. That is half-right now: the arm does not exist,
   *and* `schema_upstream` does. None of them cites the `⟨复现值⟩` placeholder, so
   stage [21] is green, and the board item scopes this ticket to `CLAIMS_TEXT.md`
   — so they are left, named here, and raised in `monitor/inbox/`. The gate
   deliberately scans only `CLAIMS_TEXT.md` for the dead name rather than the
   whole territory, because widening it today would red the gate on files this
   ticket was told not to touch.
3. **Three other territories have not acted on the proposal**: `Theoria.md:271`'s
   main table row (owner's ruling), `battery`'s arm rename to `schema_upstream`,
   and `papers`' phase1-workshop follow-through. Asked for in `monitor/inbox/`.
4. **A standing factual error, registered and still uncorrected**
   (`SCHEMA_LOCATE.md` §1.1): the upstream specification is authored by **Zeng et
   al.**, not Feng et al. (Haiwen Feng is last author). Not freeze's file.
5. **Nothing here judges 98.98%.** It is upstream self-report over 25 games, of
   which 21 are permanently unauditable under the pile cut. It can exist only as
   a citation, and the text says so.

## Reproduce

```bash
python freeze/schema_column_withdrawal.py --verify
python freeze/schema_column_withdrawal.py --selftest
bash freeze/verify.sh          # stage [21]; needs memory headroom
```
