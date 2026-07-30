# OPS-M cycle 29 — adversarial test of the "freeze stage 15 is structural" claim

Adversarial subagent, 2026-07-30. Nothing was merged, committed or pushed.
Raw evidence: `monitor/runs/opsm29/adv/` (`gate-*.json` = control.py records,
`tx-*.txt` = full `verify.sh` transcripts).

---

## (a) VERDICT: **PARTIALLY CONFIRMED — the mechanism is real, the causal
## attribution ("not a defect in the branches") is REFUTED.**

| Sub-claim | Verdict |
|---|---|
| `ci_merge.py:513` builds its probe worktree with `tempfile.mkdtemp()` in `%TEMP%`, outside the repo | **CONFIRMED** (verbatim, line 513) |
| `resolve_pool()` cannot find the live gitignored pool from `%TEMP%` | **CONFIRMED** |
| A *byte-perfect, freshly regenerated* budget table still fails stage 15 in `%TEMP%` | **CONFIRMED** — decisive controlled pair below |
| Each branch adds **exactly ONE** failure, and it is stage 15 / `BUDGET_TABLE` | **CONFIRMED** — 4 independent runs, `1 check(s) failed` each |
| Clean master is green (so the reds are not master's pre-existing bug) | **CONFIRMED** at gate level — but see the sting below |
| "The cause is structural, **not a defect in the branches**" | **REFUTED** — the branches' committed `BUDGET_TABLE.json` is *also* stale **inside** the repo, where the pool is found. The red is **overdetermined**: two independently sufficient causes. |
| "Stage 15 can NEVER go green under ci_merge, **for any branch**" | **CONFIRMED for any branch that keeps the current 15b**; over-broad as an absolute (a branch may edit 15b — see "not tested") |
| s4-freeze is an ancestor of s4-e23-tiers | **CONFIRMED** |

**The one thing the claim got wrong, and it matters for the ruling:** it names
`%TEMP%` as *the* cause and therefore declares the branches innocent. Moving the
probe worktree inside the repo — where `resolve_pool()`'s `.worktrees` fallback
**does** find the live pool — **does not turn the gate green.** Both branches
still fail, still with exactly one failure, still 15b. So "run ci_merge's probe
inside the repo" would *not* unblock these branches. Any remedy built on the
claim as written would fail.

---

## (b) Commands and observed output

### 1. What the code actually does

`monitor/ci_merge.py:513` — exact text:

```
    wt = tempfile.mkdtemp(prefix="ci-merge-")
```

`python -c "import tempfile;print(tempfile.gettempdir())"` → `C:\Users\user\AppData\Local\Temp`
(outside `C:\Users\user\Desktop\theoria`). Claim's mechanism premise: correct.

`freeze/build_budget_table.py:78-88` — `resolve_pool()` **has a fallback**, and
the claim does not mention it:

```python
def resolve_pool(rel):
    cand = os.path.join(REPO, rel.replace("/", os.sep))
    if os.path.exists(cand):
        return cand
    parts = REPO.replace("/", os.sep).split(os.sep)
    if ".worktrees" in parts:
        main = os.sep.join(parts[:parts.index(".worktrees")])
        cand = os.path.join(main, rel.replace("/", os.sep))
        if os.path.exists(cand):
            return cand
    return None
```

So: no env var, no committed fixture — but a worktree under `<repo>/.worktrees/`
**does** resolve the main checkout's `proxy/var/spend_gate.jsonl`. `%TEMP%` does
not. That is what makes experiment (c) decisive rather than redundant.

Stage numbering: master's `freeze/verify.sh` has stages **0–11 only**; stages
[12]–[17] arrive with the branches. Stage **[15b]** (`verify.sh:1157-1162` on
`origin/agent/s4-freeze`) is the failing check and it calls

```
bt_out="$(python "$HERE/build_budget_table.py" --verify 2>&1)"
```

with **no** `--allow-absent-pool`.

### 2. `build_budget_table.py --verify` across six locations (exit code is the gate)

```
### B: PRIMARY CHECKOUT (master, real repo root)
DRIFT: freeze/BUDGET_TABLE.json no longer describes this tree.
       sections that moved: balance, citations, pool, verdict
DRIFT: the generated block in freeze/BUDGET_TABLE.md is stale or was hand-edited.
CITATION DRIFT: freeze/STATS_RULES.md:777, freeze/STATS_RULES.md:791
rc=1

### C: %TEMP% clean master (opsm29-ctl)
       sections that moved: balance, citations, pool, projection, verdict
POOL ABSENT: the pool is gitignored (proxy/.gitignore:3) and this checkout does not have one; ...
CITATION DRIFT: freeze/STATS_RULES.md:777, freeze/STATS_RULES.md:791
rc=1

### D: in-repo clean master (.worktrees/opsm29-t1)
       sections that moved: balance, citations, pool, verdict
CITATION DRIFT: freeze/STATS_RULES.md:777, freeze/STATS_RULES.md:791
rc=1

### E: %TEMP% merged s4-freeze
       sections that moved: balance, pool, projection, verdict
POOL ABSENT: ...
rc=1

### F: %TEMP% merged s4-e23-tiers
       sections that moved: balance, pool, projection, verdict
POOL ABSENT: ...
rc=1

### G: in-repo merged s4-e23-tiers  (pool IS found — no POOL ABSENT line)
       sections that moved: balance, pool, verdict
rc=1
```

Two things fall out of this table:

* **The check is red in the primary repo checkout on clean master too** (B, rc=1).
  Master's *gate* is green only because master's `verify.sh` never calls the
  generator. So the branches are not introducing a break — they are **wiring in a
  check that was already failing on master's artefacts**, and they simultaneously
  **fix** master's `CITATION DRIFT` (the section-anchor rewrite in
  `build_budget_table.py`; the citation line is absent from E/F/G).
* **In-repo runs find the pool** (no `POOL ABSENT`, `projection` no longer drifts)
  **and are still rc=1** — the `balance`/`pool` sections have genuinely moved.

### 3. Full `freeze/verify.sh` under ci_merge's exact invocation (`control.py`)

```
gate-ctl.json          7972a075778a GREEN  rc=0    (clean master, %TEMP%)
    | DRAFT COMPLETE -- all 13 items landed or annotated; 2 note(s)
gate-repomaster.json   7972a075778a GREEN  rc=0    (clean master, in-repo .worktrees)
    | DRAFT COMPLETE -- all 13 items landed or annotated; 2 note(s)
gate-tmpmf.json        308db9f16fa0 RED    rc=1    (master+s4-freeze, %TEMP%)
    | FAIL  BUDGET_TABLE.{json,md} no longer recompute from the ledgers -- regenerate and read the diff
    | DRAFT INCOMPLETE -- 1 check(s) failed
gate-tmpme.json        e16a2e3f6f08 RED    rc=1    (master+s4-e23-tiers, %TEMP%)
    | FAIL  BUDGET_TABLE.{json,md} no longer recompute from the ledgers -- regenerate and read the diff
    | DRAFT INCOMPLETE -- 1 check(s) failed
gate-repomf.json       41e2df4e9124 RED    rc=1    (master+s4-freeze, IN-REPO)
    | FAIL  BUDGET_TABLE.{json,md} no longer recompute from the ledgers -- regenerate and read the diff
    | DRAFT INCOMPLETE -- 1 check(s) failed
gate-repome.json       3e351d63c30f RED    rc=1    (master+s4-e23-tiers, IN-REPO)
    | FAIL  BUDGET_TABLE.{json,md} no longer recompute from the ledgers -- regenerate and read the diff
    | DRAFT INCOMPLETE -- 1 check(s) failed
```

Independent whole-transcript FAIL census (`bash verify.sh`, same cwd/PYTHONPATH/UTF-8 pin):

```
=== tx-ctl.txt      106: DRAFT COMPLETE -- all 13 items landed or annotated; 2 note(s)
=== tx-repomf.txt   115:  FAIL  BUDGET_TABLE.{json,md} no longer recompute ...
                    134: DRAFT INCOMPLETE -- 1 check(s) failed
=== tx-repome.txt   117:  FAIL  BUDGET_TABLE.{json,md} no longer recompute ...
                    144: DRAFT INCOMPLETE -- 1 check(s) failed
=== tx-tmpmf.txt    115:  FAIL  ...   135: DRAFT INCOMPLETE -- 1 check(s) failed
=== tx-tmpme.txt    117:  FAIL  ...   145: DRAFT INCOMPLETE -- 1 check(s) failed
tmpmf rc=1 / tmpme rc=1 / repomf rc=1 / repome rc=1 / ctl rc=0
```

**"Exactly ONE failure, and it is stage 15": CONFIRMED**, four times, in two
locations. Nothing else in the merged trees is red. Baseline clean master: zero
failures, `DRAFT COMPLETE`.

### 4. The decisive controlled pair — content held constant, location varied

Regenerated `BUDGET_TABLE.{json,md}` inside the repo (pool visible), then copied
the *same bytes* into a `%TEMP%` worktree of the *same merge commit content*, and
ran the **full gate** on both:

```
regen rc=0
freeze     GREEN (rc=0)     # .worktrees/opsm29adv-regen        head f3ffcfc5620a
freeze     RED   (rc=1)     # %TEMP%/opsm29adv-regen-tmp        head b8f7755432
```

and the generator alone on the same bytes:

```
### I2: in-repo regen worktree, --verify
freeze/BUDGET_TABLE.{json,md} still describes this tree
REAL rc=0

### J2: %TEMP%, freshly-regenerated table, --verify
DRIFT: ... sections that moved: balance, pool, projection, verdict
POOL ABSENT: the pool is gitignored (proxy/.gitignore:3) and this checkout does not have one; ...
REAL rc=1

### K2: %TEMP%, freshly-regenerated table, --verify --allow-absent-pool
DRIFT: ... sections that moved: balance, pool, projection, verdict
POOL ABSENT: ...
REAL rc=1
```

This is the claim's strong half, proved: **a branch that does everything right
still cannot pass stage 15 under ci_merge**, and `--allow-absent-pool` is not an
escape hatch (it suppresses only the POOL-ABSENT line's contribution to the exit
code; the `pool` JSON section still mismatches). RES-1 reported exactly this
misnaming in `monitor/inbox/20260730T0106Z-RES-1-15b-green-is-an-instant.md`;
K2 reproduces it.

And the mirror experiment — location held constant (in-repo), content varied —
is section 3's `gate-repomf`/`gate-repome` (RED) versus `gate-regen-inrepo`
(GREEN). Both variables are independently sufficient to produce the red. That is
what "overdetermined" means here, and it is why the claim's "not a defect in the
branches" does not survive.

### 5. Ancestry sub-claim

```
$ git merge-base --is-ancestor origin/agent/s4-freeze origin/agent/s4-e23-tiers
s4-freeze ancestor of e23: rc=0
$ git merge-base --is-ancestor origin/agent/s4-e23-tiers origin/agent/s4-freeze
reverse: rc=1
```

`f47b6b30` (s4-freeze tip) appears in `git log origin/master..origin/agent/s4-e23-tiers`.
**CONFIRMED**: s4-freeze is a strict ancestor of s4-e23-tiers.

### 6. Do the branches modify BUDGET_TABLE? (a listed refutation route — yes, they do)

```
$ git diff --stat master origin/agent/s4-freeze -- freeze/build_budget_table.py freeze/BUDGET_TABLE.json freeze/BUDGET_TABLE.md
 freeze/BUDGET_TABLE.json     |  32 ++++----
 freeze/BUDGET_TABLE.md       |  10 +--
 freeze/build_budget_table.py | 169 +++++++++++++++++++++++++++++++++++++++++--
```

The generator change is the CITED_LINES → CITED_IN_SECTION re-anchor, which
**fixes** the citation drift master still has. So "the branches genuinely modify
BUDGET_TABLE" is true but is not the reason they are red: the drift in the merged
trees is confined to `balance`/`pool`/`verdict`, all derived from the live
gitignored pool, none from tracked data.

---

## (c) What I could NOT test, and why

1. **Whether the branches' `BUDGET_TABLE.json` was green at the instant its
   author committed it.** That would need `proxy/var/spend_gate.jsonl`
   reconstructed as of `f47b6b30` / `6eaf2da2`. The ledger is append-only and
   carries `max_seq`, so it is probably reconstructible by truncation — I did not
   attempt it. Consequence: I can say the branch is stale **now** in-repo; I
   **cannot** say the author shipped it stale. The evidence is consistent with
   "regenerated correctly, then the pool moved" (only pool-derived sections
   drift), which is RES-1's documented "15b's green is an instant".
2. **Whether some branch could make stage 15 green under ci_merge by changing
   15b itself** (e.g. comparing `freeze/POOL_DIGEST.json` instead of recomputing
   the live pool, which is RES-1's proposed fix). Untested. This is why
   "NEVER … for any branch" is over-broad as literally written: it holds for any
   branch that keeps 15b's current body, which is the practically relevant set.
3. **I did not run `monitor/ci_merge.py` itself.** I used
   `monitor/runs/opsm29/control.py`, which replicates `gates.gate_for` +
   `cwd=<worktree>/freeze` + `gates.gate_env` + the UTF-8 pin. The failure text it
   produces is character-identical to the two `monitor/ci/CONFLICT-*.md` records,
   which is the cross-check that it is replicating faithfully — but it is a
   replica, not the real runner.
4. **`.worktrees/opsm29-t1`** (used for experiment D and `gate-repomaster.json`)
   was deleted by another session *after* those two runs completed. Both results
   were captured before it vanished; it cannot be re-run at that path.
5. **No timing/instrumentation of *how fast* the table goes stale.** RES-1
   measured `actions_test_like` moving 3791 → 3810 inside one minute; I did not
   independently reproduce that rate. My regenerated table was still green at
   full-gate time (minutes later), so the staleness window is at least minutes,
   not seconds — but I did not bound it.

## Artefacts left on disk (nothing committed)

Worktrees, all disposable: `.worktrees/opsm29adv-mf`, `.worktrees/opsm29adv-me`,
`.worktrees/opsm29adv-regen`, and `%TEMP%\opsm29adv-mf`, `%TEMP%\opsm29adv-me`,
`%TEMP%\opsm29adv-regen-tmp`. `%TEMP%\opsm29-ctl` was pre-existing and untouched.
Records: `monitor/runs/opsm29/adv/`.
