# M-2 · RUN_STATE

Prompt: `(unset — owner rulings, 「B 按每战役」/「⟨r_min⟩ 就 0.5」, 2026-08-02)` ·
branch `agent/m-2-rulings-b-per-campaign-rmin` · base `c42f5ad4`.
Territory: `monitor`. Run archive: `monitor/runs/2026-08-04T124058Z-M-2-rulings`.
**Built on `agent/m-1-money-single-truth`**, which is pushed but not yet merged —
`money.json` and `INCIDENTS.md` exist only there, so M-1 is merged into this branch.

## Delivered

**1. B is per-campaign, recorded.** `money.json`'s `conflicting_reading`
`needs_human` is removed and replaced by `dev_pile_B.ruling`, carrying the
verbatim ruling, the superseded per-game reading (now descriptive), and the
consequence: **$60 is the whole dev-pile campaign's total, measured $129.0326 =
215 percent of it, overrun $69.03**. `INC-MON-001` gains a 裁决 section.

**2. The ruling exposed a second mechanism, and it is the more fundamental
one.** `theoria-arm/harness/campaign.py:475` sets `self.spent_usd = 0.0` in the
constructor, so `CAMPAIGN_USD` (200) and `GAME_USD` (60) bound **one
invocation**, not a cumulative allocation. Ten dev-pile campaigns each started
at $0, each stayed inside its own caps, and summed to $129.0326 — **no single
run ever breached**. B was therefore invisible to two instruments for two
different reasons: the dashboard could not **express** it (hard-coded $200
envelope, no campaign filter) and the harness cannot **accumulate** it. Because
the ruling makes B per-campaign, B is inherently cumulative across invocations,
so a per-invocation cap **cannot enforce it in principle** — changing 60 to
another number does not fix this. Filed to `theoria-arm`.

**3. ⟨r_min⟩ = 0.5 delivered to `freeze` as a ruling plus measured evidence,
never as an edit.** `freeze/` is another territory and is claimed by W-9201
(`S45`). Measured today with `python -m exam.tools.endpoint_verdict --table`:
`cert` is the **only** column separating `cheater-v4` from `oracle` (identical
on sens / spec / BA / cov(ii)), and 0.5 refuses `cheater-v4` (0.000) while
passing `oracle` (1.000) — **the ruled value is right**. Already in force and
needing no signature: `S_min = 0.50`, `c_min = 0.50`; `memoriser` is correctly
不可结论 on `cov(ii) = 0.000`.
**But the column it would sit on is not usable as written.**
`exam/endpoint.py:244-245` computes `certified_share = certified /
correct_positive`, which (a) returns `None` when the denominator is 0 — the `--`
seen for `denier` / `abstainer` / `null`, and `None < 0.5` is undefined, **the
exact hole §9.15 just closed for specificity**; (b) has an arm-choosable
denominator, so answering fewer positives correctly improves the ratio; (c)
pools the classes — `memoriser` reads `cert` 1.000 while certifying nothing in
class (ii). Recommendation delivered: define the floor on the **class-(ii)
certified rate**, denominator pinned to that class's item count.

**4. Third register collision resolved, and recorded as evidence.** Master's
`c42f5ad4` took `#15` (pool ceiling $214.90 → **$700.00**, actions 24000 →
40000) while this line of work held it. The rounds entry has now been
renumbered **three times: 12 → 14 → 15 → 16**, each time correctly by the same
precedent. `INC-MON-002` gains 补记二.

## Gaps — what was asked for and did not get

**1. Neither ruling closes its incident.** `INC-MON-001` stays open: the $69.03
is spent, and the harness half of the blindness belongs to another territory.
`INC-MON-002` stays open: its `needs_human` — a mutual-exclusion point for
number allocation — is precisely what the third collision shows discipline
cannot substitute for.

**2. The reason floor is not implemented here, and must not be.** `freeze/` is
claimed by another live session. This ticket delivers the ruling and the
evidence; the edit is theirs.

**3. Three requests to `theoria-arm` remain unanswered** (the mis-attributed
MANIFEST, `--ceiling` fail-closed, `GAME_USD` sharing one source), now joined by
a fourth: make the cumulative cap enforceable at all.

## Verification

| | |
|---|---|
| territory gate | `sh monitor/verify.sh` → **GREEN, exit 0**, first run, all four stages ok |
| money register | `monitor/tests/test_money_register.py` **9/9** against the live ledger |
| secret | **5/5 green** — no secret value in 13,177 tracked files |
| boundary | **1/1 green** — nothing changed outside `monitor/` |
| sealed | raw **1/2**, 6 files flagged; green with `--allow` on those 6 — disclosed in full below |
| MANIFEST | `monitor/runs/2026-08-04T124058Z-M-2-rulings/MANIFEST.json` |

**The sealed disclosure, in full, because three of the six are my own doing.**
Three are pre-existing and were established in M-1 (`monitor/spec.py`,
`state.json`, `index.html` — the ids are present at base and my added lines
contain none). **Three are self-inflicted**: `PARTNER_SYNC.md`'s 阻塞 line and
M-1's `RUN_STATE.md` and `NOTES.md` write the three sealed ids **out in full**
inside the disclosure text *about the guard* — which is what makes the
disclosure trip the guard. A fourth id at `PARTNER_SYNC.md:1182` sits in
someone else's S23 paragraph and is not mine.
**Why this is not a contamination event**: CLAUDE.md permits reading game ids
and status metadata — the prohibition is on mechanics — and the guard's own
message exempts a file whose job is registering contamination, which a guard
disclosure is. **Why it still matters**: every later branch touching these files
inherits a red guard and has to widen `--allow`, which is how a check decays
into a formality. **Not repaired here, deliberately**: M-1's archive is hashed
into its MANIFEST and `PARTNER_SYNC` is append-only, so rewriting either to
quiet a guard would cost more honesty than it buys. **Practice from now on**:
truncate ids in disclosure text. M-2's own six new files contain **zero** sealed
ids — checked, not assumed.

## Open, and deliberately not closed here

**1. The pool ceiling moved and nothing here had to change.** `c42f5ad4` raised
`usd_ceiling` to $700.00; `money.json` and `_spend_watch` treat it as a
**pointer**, so both followed automatically with no edit, and the dashboard now
reads 「池上限 $700.00，剩 $539.05」. That is the single-source-of-truth design
paying off within hours of landing. **B is still breached** — B is an allocation
inside the pool, not the pool.

**2. `S_min` and `c_min` need no signature.** Both are already 0.50 in the
evaluator. Only ⟨r_min⟩ was outstanding, and it is now ruled.

**3. The number churn is the finding, not the nuisance.** One entry renumbered
three times in one day, every handling correct. Correct handling three times did
not prevent a fourth collision — that is what "no mutual-exclusion point" means,
and it is not a discipline problem.
