# figures/SOURCES.md — every input, and what depends on it

The executable form of this table is `figures/sources.py`; the hashes are in
`figures/SOURCES.sha256`, regenerated on every build and checked by
`figures/verify.sh`. This file is the prose version, and the place where an
**absent** source is named rather than left to be discovered.

No script in `figures/` opens a path that is not declared in `sources.py`. That
is not a style rule: an undeclared read is an unhashed read, and an unhashed
input is a figure that can change under you without the verification noticing.

## Tracked — required

| source key | path | figure | what is taken |
|---|---|---|---|
| `pilot_ledger` | `baseline-arms/ledger.jsonl` | fig02 | 560 records, two dialects in one file. Model-call rows carry `total_cost_usd`, `usage`, `step_idx`; env-step rows carry `arm`, `action`, `failed`, `frame` |
| `pilot_ar25` `pilot_g50t` `pilot_sk48` `pilot_tn36` | `baseline-arms/out/pilot_*.json` | fig02 | per-run roll-ups; used only to cross-check the cost curve's endpoint against the ledger's own sum |
| `capability_spectrum` | `battery/artifacts/capability_spectrum.json` | fig03, fig05, fig07 | `cards` (38 metrics with family/direction/unit), `runs` (31), each metric's `value` + `status` + `support` |
| `arm_contrast` | `battery/artifacts/arm_contrast.json` | fig03 | which metrics have cross-arm overlap — 7 of 38 — and the control arm |
| `gaming_audit` | `battery/artifacts/gaming_audit.json` | fig03 | tier demotions; the K4-never-without-K2 rule |
| `a2_loop_ledger` | `cold-start-a2/artifacts/loop_ledger.json` | fig05 | the six-beat account: `beat`, `claim`, `status`, `detail`, `evidence` |
| `a2_repair_report` | `cold-start-a2/artifacts/repair_report.json` | fig05 | what the repair changed |
| `a2_probe_report` | `cold-start-a2/artifacts/probe_report.json` | fig05 | L3: designed / executed / refuted / not-separable |
| `a2_refutation` | `cold-start-a2/artifacts/refutation.json` | fig05 | L1: the solved episode that contradicts the machine-checked theorem |
| `a0_theorize_log` | `cold-start-a0/THEORIZE_LOG.md` | fig06 | adjudication blocks with verdicts; the revision-history table |
| `a0_concept_accounts` | `cold-start-a0/artifacts/concept_accounts.json` | fig06 | per-concept verdict, `script_delta_bits`, the laws and rules naming it |
| `a0_candidates` | `cold-start-a0/artifacts/candidates.jsonl` | fig06 | the 28 engine proposals as they arrived |
| `a0_score_vs_truth` | `cold-start-a0/artifacts/score_vs_truth.json` | fig07 | 233 of 236 pairs; the three R-05 named before the score existed |

Plus one non-file source: `git log --follow cold-start-a0/THEORIZE_LOG.md`, read
through `sources.git_log()`. It supplies the only wall-clock axis fig06 has —
five committer timestamps. It is *not* hashed, because git history is not a
file; `sources.git_log()` returns `[]` on a shallow or git-less checkout and
fig06 degrades to its ordinal axis and says so.

## Declared and absent — named on purpose

These are in `sources.py` with `tracked=False, optional=True` so that they show
up in `SOURCES.sha256` as `ABSENT…` rather than being silently missing.

| source key | path | why it is not used |
|---|---|---|
| `envelope_ledger_ar25` … `_tn36` | `baseline-arms/out/shards/ledger.*.jsonl` | **Untracked in `master`.** They exist in one working tree and not in a clean checkout, so a figure built on them cannot be rebuilt — which fails the determinism requirement at its root, not at its margin. `fig02`'s extractor picks them up automatically if they appear. |
| `theoria_arm_ledger` | `theoria-arm/runs/ledger.jsonl` | Does not exist yet. This is the third column of figure 2. The extractor keys the arm axis off each record's own `arm` field, so when a Theoria cost ledger lands, adding it is one entry in `sources.py` and **zero** changes to the renderer. |

## What this means for figure 2

Figure 2 is specified in `Theoria.md` §3.2 as a **three-arm** per-turn cost
curve. It ships as `bare_cc` across the model ladder, because:

* there is no Schema arm — `baseline-arms/SCHEMA_LOCATE.md` says there may never
  be one, and `battery/DECISIONS.md` D-B-004 argues the model ladder is a
  *weaker* substitute rather than an equivalent;
* the Theoria arm has no cost ledger — `battery/REPORT_V0.md` records that A0
  ran engines and hand adjudication with no LLM in the loop, so every economy
  metric is `not-applicable` on it.

Both facts are drawn on the figure. A two-arm figure labelled as three arms
would be worse than a two-arm figure labelled as two.

## Pile discipline

Every source above is either a self-built world (`cold-start-a0`,
`cold-start-a2`, `a0-spike`) or a **development-pile** game
(`ar25-0c556536`, `g50t-5849a774`, `sk48-d8078629`, `tn36-ef4dde99`). No figure
reads anything belonging to a sealed game, and no figure reads an upstream
artefact. `cold-start-a2/artifacts/loop_ledger.json`'s own `authority` field
records the INC-004 ruling under which its DC22-isomorphic world was built
without reading any upstream DC22 artefact.

`cold-start-a0/` belongs to the theory-compiler track and is read **read-only**
here, as is `battery/`, `baseline-arms/` and `cold-start-a2/`. P-21 writes only
inside `figures/`.
