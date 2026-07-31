# E18 · which unscripted numbers actually matter, and how far the disease spreads

*Census run 2026-07-30, read-only, against `cc7e414e`. Method: extract every
`ENGINE_TABLE.md` registry row whose locator is a regex against a file under
`runs/20260729T000000Z-E11-engine-crosscheck-deep/`; match every numeric token
in each value against `papers/phase1-workshop/PAPER.md` and all thirteen
`sections/*.md`; hand-read the context of every hit.*

## The headline the ticket did not know

**87** registry facts are probed out of E11 prose. **Two** of them reach the
paper body. Both are in §10.5, and both are load-bearing:

| registry key | value | paper site | why it matters |
|---|---|---|---|
| `lp.incomplete` | `639 / 2189 = 29.2 %` | `sections/10_adjudication.md:285`, `:288` = `PAPER.md:3019`, `:3022` | §10.5 is titled "Two published numbers that rest on a re-derivation". This is number one of the two. |
| `lp.no_farkas` | `638` | `sections/10_adjudication.md:289`, `:294` = `PAPER.md:3023`, `:3028` | carries the paper's "no exact Farkas dual" limitation |

`2189` itself appears nowhere in the paper — only the ratio and the numerator do.

**Three of the ticket's five named numbers are not in the paper at all**, and
neither is the fourth: `126 / 300` (`mdl.objid_worlds`), `1633 / 4000`
(`pf.infinity_rows`), `82 / 4000` (`pf.zero_cost_bug`) and `104 / 149`
(`cegis.lifted_tautological`) occur in no section and no figure. They are
unconfirmed *in `ENGINE_TABLE.md`*, not unconfirmed *in the paper*.

That does not shrink this ticket. The registry is what the paper draws from, the
four are published there under the same authority as the two that are quoted,
and the ticket's rule is written about the registry's contents, not about
today's citation graph. But it changes which finding is urgent, and the next
section is that finding — including the part of it this census originally got
wrong.

## The number that is unregistered and unscripted — corrected

**This section overstated its finding when first written on 2026-07-30, and the
overstatement is corrected here rather than deleted, because it propagated into
`tools/survey_numbers/lp_incomplete.py`'s docstrings and into a
`citation_is_wrong: true` field before an adversarial review caught it.**

> `sections/10_adjudication.md:289` = `PAPER.md:3023` — "638 are still infeasible
> at **bounds of 100, 10⁴ and 10⁶**"

**What was claimed:** that this is cited to `engine-rig/ENGINE_TABLE.md`, which
contains none of those strings, so the paper's strongest sentence about the 639
cites a file that does not contain it.

**Why that is wrong.** The parenthetical belongs to the *item heading* —
"**`lp_potential`'s 29.2 % incompleteness rate** (`engine-rig/ENGINE_TABLE.md`;
not quoted anywhere in this paper)" — and `ENGINE_TABLE.md` publishes exactly
that, verbatim, as `lp.incomplete = 639 / 2189 = 29.2 %`. §10.5 uses the same
heading-plus-artefact form for every entry (compare "…in
`engine-rig/runs/p13-fd-real/dividend.json`"). The bound sentence carries no
citation of its own; it attributes itself in prose, to "A reviewer rebuilt the
LP independently and re-derived it". `ENGINE_TABLE.md` also carries the 638 and
the 1 and `bound = 10`. Reading a heading's artefact reference as a citation for
every sentence under it is a misreading of the convention, and it is the kind of
misreading that gets made by someone looking for a defect.

**What is actually true, and still worth recording.** `ENGINE_TABLE.md` has **no
registry key** for the bound triple — the only bound key is
`lp.weight_bound = 10`. So before E18 those three numbers sat in the paper with
no registry entry and no script behind them, sourced from
`partials/lp_potential-via-exhaustive.md:275-277`. **Unregistered, not
miscited.** That is a smaller finding than the one first written, and it is the
one the recomputation was worth doing for.

One thing the first version got right and that survives: `verify_paper.py`'s
check E would not have caught a bad citation here, and says so itself at
`:63-67` and `:73-75` — it proves no quantitative block is *entirely* uncited,
and "any real path satisfies the block".

One more trap in the same sentence: the paper writes "of **639 silences**", using
`lp.incomplete`'s numerator against a **different denominator** — silences, not
the 2189 genuinely-unreachable worlds. A recomputation has to produce both
denominators or the paper's phrasing will not check out against the registry.

## Why the registry did not catch any of this

`engine_table.py:116-131`'s `md(path, regex)` probe runs `re.search` over a file
and returns capture group 1. It guarantees a **string-equality chain between two
documents**: the digits in the table are the digits currently in the report, and
if the report is edited the probe drifts (exit 1) or stops matching (exit 3).
It does not touch whether the report's digits correspond to a computation — for
these 87 facts the probed file is one of nine Markdown files in a directory
holding no script and no data, so the chain terminates in an author's memory.

**A regex over prose is a transcription check, not a recomputation check.** It
proves the paper's digits match the report's digits and proves nothing at all
about whether the report's digits match anything that ran.

Two details sharpen it. The `expect` value beside each probe is documented as "a
tripwire, not the source" (`engine_table.py:11-14`), so a mismatch always means
*the prose moved*, never *the number is wrong*. And `jf`/`jlf`
(`engine_table.py:134-149`) already read real JSON for other facts — so in the
rendered provenance table a prose-backed fact and a data-backed fact are
**typographically indistinguishable**.

That is also the repair: `jf()` exists, so re-pointing a probe from a Markdown
regex to this run's `counts/*.json` needs no new harness, and the existing
`--check` path — already bound by `tests/test_engine_table.py:25-38` and run
inside `verify.py` rung 1 — becomes a real recomputation gate for those keys.

## Every other run directory, same question

`data` = `.json/.jsonl/.csv/.txt/.log/.pddl/.sas/.plan`.

| directory | files | md | .py/.sh | data | verdict |
|---|---|---|---|---|---|
| `20260728T072633Z-E2-fd-ladder-bench` | 204 | 3 | 0 | 201 | data-backed |
| `20260728T141724Z-E5-cert-recheck` | 55 | 5 | 7 | 43 | data + scripts |
| `20260728T150713Z-E7-deadlock-claim-audit` | 1899 | 1 | 30 | 1822 | data + scripts |
| `20260728T164556Z-E9-engine-paper-table` | 8 | 3 | 0 | 5 | MANIFEST + captured stdout; no script |
| `20260728T191530Z-E6-engine-dividend` | 232 | 2 | 0 | 230 | data-backed |
| **`20260729T000000Z-E11-engine-crosscheck-deep`** | **10** | **9** | **0** | **1 (MANIFEST only)** | **markdown-only — this ticket** |
| `20260729T020000Z-E16-verdict-must-gate` | 11 | 1 | 9 | 1 | scripts |
| `20260729T034043Z-E17-held-out-validation` | 30 | 5 | 13 | 12 | data + scripts |
| `20260729T044500Z-E15-solver-status-bit` | 30 | 6 | 8 | 16 | data + scripts |
| `20260729T072000Z-E13-engine-section-numbers` | 4 | 1 | 0 | 3 | MANIFEST + captured stdout |
| **`20260729T080000Z-C11-tool-failure-as-truth`** | **8** | **7** | **0** | **1 (MANIFEST only)** | **markdown-only** |
| `20260729T143000Z-C10-unsolvable-proof-canon` | 1 | 0 | 0 | 1 | MANIFEST only, no report at all |
| `20260729T160000Z-E19-merge-clean-but-broken` | 2 | 0 | 0 | 2 | `EVIDENCE.txt` + MANIFEST |
| `p13-fd-real` | 15 | 3 | 0 | 12 | data-backed |

**Markdown-only and cited by the paper:** only E11 (laundered through
`ENGINE_TABLE.md`) and `C11-tool-failure-as-truth` — the latter cited twice
(`sections/10_adjudication.md:276`, `:337`), both times for a *qualitative*
claim carrying no number. Same structure, no numeric exposure today.

**One outside `engine-rig/`, folded into scope as a finding not a fix:**
`fuzzlab/runs/20260728T152000Z-V10-fuzz-mutation-power` is 7 `.md` and a
MANIFEST — nothing else — and it supplies **16** registry facts
(`ENGINE_TABLE.md:338`): the six `*.published`, the six `*.unaudited`, and
`rig.published_fields` / `rig.asserted_fields` / `rig.index_only_fields` /
`rig.unaudited_fields`. None of the 16 reaches the paper yet. It is the sixth
case of the same kind, one step before it becomes a paper problem, and it is in
`fuzzlab/` — another territory, so this ticket reports it rather than fixing it.

**Adjacent, same defect, outside the E11 remit:** `PAPER.md:3125` — "Mutation
testing found **14 of 19 mutants** surviving" — cites `E17/CORRECTIONS.md`, a
prose file, and is **in no registry key** under any name. The four `ho.adv_*`
keys quoted at `PAPER.md:3109-3112` are regexes against
`E17/ADVERSARIAL-heldout.md`, also prose — though E17 at least ships scripts
beside it.

## Coincidental matches checked and rejected

`112`/`105` battery blind-round attack counts (`PAPER.md:79`, `:2098`); `91`
"105 attacks, of which 91 landed" (`01_intro.md:93`); `82` "ρ = −0.899 over 82
shared runs" (`07_battery.md:292`); `49` "47/49 = 96 %" (`08_exam.md:43`);
`200`/`65` HTTP statuses and "65 consecutive 401s" (`09_preflight.md:32-34`);
`5.7`/`1.11`/`36`/`131` section numbers and line references. No E11 value
reaches any figure (`papers/phase1-workshop/figures/data/*.json` swept).
