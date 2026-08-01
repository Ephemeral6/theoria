# CITECHECK — 2026-08-01 delta: the probe-frontier correction

```audit-stamp
target: papers/phase1-workshop/PAPER.md
sha256: cec3bd3e35bae4572b1dedc6b35128443c76adfc48e12f4e0298a08d07057c08
lines: 4057
bytes: 260623
scope: delta audit of the 2026-08-01 probe-frontier correction (six edited sites: the abstract, §1.5's closing note, §2.2, §2.3, new §11.3a and §11.4a, §11.5's closing note, §12); everything outside those edits is byte-unchanged from the state CITECHECK-2026-07-31.md pinned, and behind that the five-slice index in CITECHECK-2026-07-30.md remains the covering evidence
status: binding
date: 2026-08-01
```

**What this file is.** The successor `CITECHECK-2026-07-31.md`'s stamp names. It
is a **delta audit, not a re-audit**, on exactly the pattern that file
established: the 2026-08-01 edit qualified the paper's probe-beat claim and added
two limitation subsections, and this file audits the paths, numbers and quotes
those edits introduced — nothing else. For the unchanged remainder the covering
audit is still the chain behind it. Carrying that forward is a claim about
byte-identity of the untouched text, not a fresh reading of it, and it is said
here so nobody reads this stamp as a full re-audit.

**One thing about this delta is different from the last, and it is the reason
the delta exists.** The 2026-07-31 delta corrected a claim about an artefact the
paper ships. This one withdraws a claim about a *mechanism* — that the probe beat
closes the gap the paper's title names — on evidence produced after the paper was
written. §11.3a is the withdrawal; the sites elsewhere are pointers to it.

## Every quantitative claim the delta introduced, checked against its artefact

Column *how checked* distinguishes three grades, because they are not equally
strong: **recomputed** means this audit's own script recounted it from tracked
files; **read** means the figure was read out of a named artefact in another
territory and not independently recomputed; **derived** means it is arithmetic on
figures in the row above it.

| claim (as edited) | where | artefact | how checked | verdict |
|---|---|---|---|---|
| 56 probes designed, 52 completed | abstract, §2.3, §11.3a | `theoria-arm/runs/20260801T0000Z-A-probe-economics/README.md` §1 | **recomputed** — `runs/20260801T1200Z-P23-probe-frontier-contradicts-the-design/census.py` counts `phase` rows over the four legs' tracked `probes.jsonl`; AGREES | ok |
| frontier width 2 distinct predictions on every one of the 52 | abstract, §2.3, §11.3a, §12 | ibid.; `theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/MANIFEST.json` | **recomputed** — distinct values of `predictions` per design row; the set is `[2]`; AGREES. Recorded as *width*, not hypothesis count: the same rows carry 6/9/10/16/22/24 hypotheses | ok |
| 47 of 52 observations matched no hypothesis; 5 on-frontier | abstract, §1.5, §2.3, §11.3a, §11.5, §12 | ibid. | **recomputed** — result rows whose `survived` list is empty; AGREES | ok |
| zero monotone frontier shrinks, in any leg | §2.3, §11.3a | `theoria-arm/runs/20260801T0000Z-A-probe-economics/README.md` §1 | **recomputed** — strict decreases in successive hypothesis counts per leg; 0; AGREES | ok |
| realised information gain 0.000 bits on all 56 | abstract, §1.5, §2.3, §11.3a | ibid. | **read.** The census script does not recompute bits; it recomputes the frontier-shrink figure the arm derives it from. Stated as read, not as confirmed | ok, weaker |
| design-time price 0.5436–1.0000 bits | §2.3, §11.3a | ibid. (`predicted bits min 0.5436 median 0.8813 max 1.0000`) | **read** — the min and max of the arm's own printed row | ok |
| `cegis_miner` dispatched 48 times, refused 48 times, 0 errors, over the 8 live legs that carry an engine record | abstract, §2.2, §2.3, §11.3a, §12 | per-leg `engines_online.json` under `theoria-arm/runs/` | **recomputed** — 2 + 6 + 9 + 10 + 5 + 3 + 9 + 4 = 48 dispatches, same in `refused_with_reason`, `errored` 0 throughout. The two 2026-07-29 legs carry no engine record and are reported `absent`, never 0, which is why the sentence says *eight* legs and not ten | ok |
| 35 anchor-drift / 12 expressivity / 0 action-choice decomposition of the 47 | §11.3a | `theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/MANIFEST.json`, `measurement` block | **read, and not recomputable here** — the comparison is against per-frame hashes in a gitignored trace. The census records it as `unmeasurable_here` rather than reporting a zero, and §11.3a attributes it to the arm's manifest | ok, weaker |
| generated frontier contains the answer 43 of 52; ablation 5; 52 of 52 reconstructed; 9 still missed, 6 opening + 3 mid-leg | §11.3a | ibid., `replay` block | **read** — same gitignored-input caveat; the 5 is separately **recomputed** as the on-frontier count | ok, weaker |
| no live leg has run with the generated frontier on; default is ablation and byte-identical | §11.3a, abstract | ibid., `switch` and `classification` blocks (`"Not yet run live."`) | **read** — the manifest's own words | ok |
| zero level-completion rows across all ten live legs; `levels_completed: 0` on every leg of both rounds | abstract, §11.3a | tracked per-leg level records; `theoria-arm/runs/_rounds/20260731T231654Z-R1/round.json`, `.../20260801T001851Z-R1b/round.json` | **recomputed** — ten tracked files, zero rows in total; both round records read directly | ok |
| the six-leg reading is the battery's | §11.3a | `battery/STATUS.md` §B18; `battery/artifacts_live/live_arm_readings.json` (`n_runs: 6`) | **read**, and the paper says *ten* with the six named as a subset, so the two counts cannot be confused | ok |
| curves shortfall: $1.63 of $9.56 (r2), $1.68 of $13.44 (r3) | §11.4a | `theoria-arm/DECISIONS.md` D-A8-001 | **read** — the entry gives 4 of 5 calls and $7.926367 of $9.556852; 7 of 8 and $11.761053 of $13.439862 | ok |
| that shortfall is 12–17 % of the money | §11.4a | ibid. | **derived** — 1.630485/9.556852 = 17.1 %, 1.678809/13.439862 = 12.5 %. Arithmetic on the row above, stated as a range | ok |
| the arm's own self-check could not see it because the lost turn issued no ARC command | §11.4a | ibid., "Why the A8 self-check did not catch it" | **read** | ok |
| U3 census: `discharged` 14 → 17, `vacuous` 9 → 2, `unclassified` 0 → 4, `failing_obligation` 1 → 1, over 24 Lean books; 7 books moved | §11.4a | `freeze/runs/20260801T0700Z-E1-kind-census/COMPARISON.md`; `freeze/runs/20260801T0700Z-E1-kind-census/CENSUS.md` | **read** — the comparison table verbatim; the census table's 24 rows tally 17 + 2 + 4 + 1 | ok |
| the paradigm development is a deadlock theorem over 28 672 states with an empty axiom set | §11.4a | `freeze/STATS_RULES.md`, the quoted G1 argument | **read** — the line says 跨 28,672 个状态的死锁定理 … 是空公理集的. The paper does not repeat the "nine theorems" figure that appears only in a commit message | ok |
| the E2 demotion: attackers wrote the record, so the result is a property of the threshold; forty step records defeat the narrowed model; zero pairs is the hard blocker | §11.4a, §11.5 | `battery/runs/20260801T0300Z-E2L-frontload-step-axis/RUN_STATE.md` §1; `battery/STATUS.md`, the V-E2L note | **read** — both say 38/38 是一个发现说了 38 遍 in the same words | ok |

## Findings

* **One number was cut during the audit rather than cited.** A first draft of
  §11.4a said the paradigm development "reports an empty axiom list on all nine
  theorems". Nine is in commit `1c063290`'s message and in no tracked artefact
  this audit could open, and a commit message is not an artefact under the
  binding rule. The sentence now carries the state count and the empty axiom set,
  both of which `freeze/STATS_RULES.md` states.
* **Two bare filenames were introduced and removed.** The first draft wrote
  `trace.jsonl` and `levels.jsonl` unqualified; check **F BARE** matched them
  against 2 and 27 files respectively. Both were rewritten as descriptions
  ("a per-leg frame trace", "a tracked level record") with the counts still
  carried by a cited artefact. F's finding count went 24 → 26 → 24, i.e. back to
  its pre-existing level; no new ruling was added, because a ruling would have
  been an exemption where a rewrite was available.
* **The three-grade *how checked* column is itself a finding.** Six of the
  delta's headline quantities are recomputed here from tracked files; the two
  most rhetorically useful ones — the 35/12/0 decomposition and the 43-of-52
  replay — are **read** from another territory's manifest and cannot be
  recomputed by a reader of this repository, because their inputs are gitignored.
  The paper says so in §11.3a rather than letting the citation imply parity.
* **No claim of a live improvement was admitted.** Every site that mentions the
  generated frontier states default-off, offline-replay-only, and no live leg.
  This was checked site by site, because it is the exact error the section it
  sits in documents.

## What this audit did not do

It did not re-audit the unchanged text, did not open the figures, and did not
verify anything about the exam, the transfer chapter or the adjudication census.
It also did not run the arm: nothing here made an ARC call, a model call or a
network request, and no sealed-pile game appears in any file it touched.
