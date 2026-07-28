# P-21 run trace — 2026-07-28T03:48:57Z

Branch `agent/p21-figures`, worktree `C:/Users/user/Desktop/theoria-wt-p21`,
base commit `dc9fad1`. Territory: new top-level `figures/`. Nothing outside it
was written except `.claude/skills/` (explicitly in scope) — every data
directory was read-only.

## Opening ritual

| read | outcome |
|---|---|
| `CLAUDE.md` | track boundaries, pile cut, credential discipline. P-21 writes only `figures/`; `cold-start-a0/` (theory-compiler's) read-only. |
| `Theoria.md` §3.2 | the figure list, line 416: 图2 账单形状, 图3 电池能力谱, 图4 迁移, 图5 DC22 案例, 图6 概念诞生时间线. Figure 4 is out of scope for P-21 (its data lives in `cold-start-a3`). |
| `PARTNER_SYNC.md` tail | the `proxy` track's ledger-canon work, the red-team pass, and — load-bearing for figure 2 — that `cost.py` never reads a record's own `pricing_ref`, and that no per-call cost *sequence* is written anywhere. Figure 2 therefore builds its sequence from the ledger's per-record `total_cost_usd` directly. |
| `battery/REPORT_V0.md` | the headline this pipeline exists to draw: K4 = 1.000 and K2 = 0.000 on the same manual. Also the rule that no `not-applicable` cell may be drawn as a zero. |
| `battery/REPORT_V1.md` | K2's two sampling frames (n=3 vs n=39960) and the instruction that comparing them directly is wrong. |
| `cold-start-a0/THEORIZE_LOG.md` | already contains a section literally titled *Revision history — the concept-birth timeline*. Figure 6's spine. |
| `cold-start-a2/THEORIZE_LOG.md`, `a0-spike/THEORIZE_LOG.md`, `theoria-arm/THEORIZE_LOG.md`, `cold-start-a3/THEORIZE_LOG.md` | surveyed |

Write permission checked before any planning, because two earlier dispatched
sessions in this repo hit a read-only harness and produced nothing. It was
green, so work proceeded.

## Decisions taken during planning

**D-F-001 — A0′ is `a0-spike`, not `a0-no-button`.** The brief says "A0 vs A0′
覆盖-准确率对照". Two readings were checked against
`battery/artifacts/capability_spectrum.json`:

* `a0-base` vs `a0-no-button` is the tidier *within-world* ablation, but
  `a0-no-button`'s K2 is `insufficient-data` — no accuracy contrast exists.
* `a0-base` vs `a0-spike` gives K4 = 1.000 on both, K1 0.987 vs 1.000, and K2
  **0.000 vs 1.000**. That is the coverage–accuracy contrast.

The cost of this reading is recorded on the figure itself: `a0-spike` is a
different world built by a different track, so the pair is a contrast, not a
controlled ablation, and the denominators differ by four orders of magnitude.

**D-F-002 — tracked sources only.** `baseline-arms/out/shards/ledger.*.jsonl`
(the envelope campaign ledgers) are untracked in `master`. A figure built on
them cannot be rebuilt from a clean checkout, so they are declared in
`sources.py` as known-absent and picked up automatically if they ever land.
This costs figure 2 the envelope campaign and is stated on its face.

**D-F-003 — English figure text.** matplotlib's bundled DejaVu Sans has no CJK
coverage. CJK labels would render as tofu boxes *and* make the SVG path data
depend on whichever system font got substituted, which breaks byte-identity
across machines. Prose stays bilingual; figures do not.

**D-F-004 — a CSV layer between data and image.** Not decoration: it is where a
reviewer checks a number without reading plotting code, and it makes the
determinism check diagnostic — if the render is stable but extraction is not,
the CSV diff says so first.

**D-F-005 — figure 2 ships with two arms, labelled as two.** No Schema arm
exists (`baseline-arms/SCHEMA_LOCATE.md`) and the Theoria arm has no cost
ledger. The model ladder substitutes, and `battery/DECISIONS.md` D-B-004's
argument that the substitute is *weaker* is carried onto the plate.

## Build order

1. `theme.py` / `sources.py` / `build_all.py` / `verify.sh` — the contract, written first so the five figure scripts could be built in parallel against a stable surface.
2. Smoke test: `theme.py` renders both themes, both formats, and two passes were byte-identical before any figure script existed. Determinism was established at the contract level rather than debugged per figure.
3. Five figure scripts, one subagent each, in parallel.
4. `verify.sh`.

## Verification

See `VERIFY.log` in this directory for the gate output.
