# P10 — figures into the paper: plan, written before any code

Worker `W-1253`, branch `agent/p10-figures-into-paper`, base `ff796cd`.

## The work order, and the one thing in it I cannot do

`monitor/board/items/P10-figures-into-paper.md` declares `territory: figures`
and then asks, in clause 4, for edits to the paper body — and closes with
**"不改 papers/ 之外的东西"** ("change nothing outside `papers/`"). Those two
sentences cannot both be obeyed: the territory line says `figures/` is the only
directory I may write, the body says `papers/` is.

The board resolves it, not me. `board.py` hands out an item only when its
territory is free; `figures` was free and **`papers` is held by `RES-2` under
`P9-paper-to-submittable`**. Had the item's territory been `papers` I could not
have claimed it at all. `.claude/skills/deterministic-figures/SKILL.md` says the
same thing independently: *"Figure work writes only inside `figures/`."*

So: **clauses 1–3 are delivered in `figures/`. Clause 4 is delivered as an
apply-ready package and not applied**, because applying it means editing
`papers/phase1-workshop/sections/*.md` while another session holds that
territory. This is recorded as a gap in `RUN_STATE.md`, not quietly dropped, and
handed over through `PARTNER_SYNC.md` and `monitor/inbox/`.

Worth saying plainly: RES-2's own P9 reconnaissance
(`papers/.../runs/20260728T115500Z-P9/FINDINGS.md`) already names the figure
wiring as *"real, and probably the largest piece"* of P9. The two items overlap
by construction. This one does the half that lives in `figures/`.

## Figure numbering — the mapping clause 1 asks for

"命名与 §编号对应". The paper cites **Figure 1/2/3** today
(`sections/03_a0.md`, `sections/05_a2.md`) against its own local
`papers/phase1-workshop/figures/fig{1,2,3}_*.py` ASCII scripts. The
deterministic pipeline's six plates are numbered after `Theoria.md` §3.2's
figure list (`fig02`…`fig07`), which is a *different* numbering that has never
matched the paper.

Paper figure numbers are assigned by **order of first citation**, which is the
publishing convention and the only numbering a reader can resolve:

| paper | § | pipeline plate | replaces |
|---|---|---|---|
| Figure 1 | §3 A0 | `fig06_concept_timeline` | `figures/fig1_concept_timeline.py` |
| Figure 2 | §3 A0′ | `fig07_a0_vs_a0prime` | `figures/fig2_coverage_accuracy.py` |
| Figure 3 | §5 A2 | `fig05_a2_repair_loop` | `figures/fig3_loop_ledger.py` |
| Figure 4 | §6 A3 | `fig04_a3_transfer` | — (new citation) |
| Figure 5 | §7 battery | `fig03_capability_spectrum` | — (new citation) |
| Figure 6 | §7 battery | `fig02_bill_shape` | — (new citation) |

**The existing three citations keep their numbers.** That is not luck, it is the
reason this ordering was chosen over the pipeline's: any other assignment would
renumber "Figure 1" and "Figure 2" in prose another session is editing right
now.

The pipeline slugs are **not** renamed. `fig02`…`fig07` are load-bearing —
`build_all.FIGURES`, `check_coverage.py`, `SOURCES.md`, `PLAN.md` and every
`Source.figures` tuple key on them, and `verify.sh` gate 6 diffs the committed
`out/` tree by those names. The paper numbering is a **second view** over the
same build, not a rename.

## What "发表规格" means here, concretely

The current `out/` tree is a screen profile: PNG at `savefig.dpi = 200`, SVG
vector. Three things a submission needs and it does not have:

1. **300 dpi** at the figure's declared physical size — the print standard.
2. **PDF** — what `\includegraphics` and every Markdown→PDF pipeline actually
   consume. `theme.py` already pins `pdf.compression = 0` for determinism, so
   the format was anticipated and never emitted. Verified deterministic with
   `metadata={"CreationDate": None}` before planning to ship it.
3. **A name the citation resolves to.** `figure1_concept_timeline.pdf` is
   findable from the string "Figure 1"; `fig06_concept_timeline.png` is not.

Both profiles come off the **same in-memory `Figure` object** in one build. Not
copied: copying creates a second artefact that can drift from the first. A gate
asserts the two SVGs are byte-identical, which is the checkable form of "the
paper shows the plate the pipeline built".

## Deliverables

1. `figures/paper_map.py` — the paper-number registry: number, section, slug,
   pipeline name. One place, imported by everything else.
2. `figures/theme.py` — `save()` gains the publication profile.
3. `figures/paper/{light,dark}/figureN_<slug>.{svg,png,pdf}` — generated.
4. `figures/paper/captions/figureN.md` — one caption per figure, **generated**,
   each naming the tree files its numbers came from and the run that produced
   them. Hand-written captions go stale; §10 of `PLAN.md` is a list of exactly
   that failure.
5. `figures/paper/INDEX.md` + `index.json` — 图号 → 生成脚本 → 数据源 → sha256,
   generated from `sources.py` + `paper_map.py`, never hand-maintained.
6. `figures/verify.sh` gates 9–11 — publication artefacts exist, SVGs identical
   across profiles, index matches a fresh build.
7. The clause-4 package: exact anchored replacement text for
   `papers/phase1-workshop/sections/{03_a0,05_a2,06_a3_transfer,07_battery}.md`,
   under `HANDOVER/`, applied by whoever holds `papers`.

## Honesty clauses carried forward

* Captions must not become a second home for the caveats. `README.md` is
  explicit that every plate's "must not let you conclude" line is on the
  figure's **face** via `theme.caveat`, because captions get dropped. Captions
  here carry **provenance** — which file, which run — and point at the face for
  the caveat.
* A figure whose data is absent is marked `pending` with what is missing, never
  drawn or cited as if complete.
* Nothing in `figures/` writes outside `figures/`.
* Zero API calls, zero network, zero spend. Sealed pile untouched — every source
  is a self-built world or a development-pile game, unchanged from what
  `SOURCES.sha256` already hashes.
