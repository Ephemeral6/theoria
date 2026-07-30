# figures · STATUS

The first `STATUS.md` this territory has had. Fourteen other territories keep one;
`figures/` kept `PLAN.md` (the design and its changelog), `RUN_STATE.md` (the P4
and P8 narratives) and `runs/<id>/` instead — and the gap showed. P10 wrote a
complete handover for the paper side and nothing in `figures/` recorded that it
was outstanding, so P13, V20 and V23 each rediscovered it from scratch. This file
exists to hold the standing rulings and the open handovers: **the things that are
true between runs**, which a run directory is the wrong shape for.

It deliberately asserts as few counts as possible. `README.md:148-151` is the
house rule — *a hand-copied count of the disagreements would become one of them* —
so where a number is load-bearing this file names the authority that measures it
instead of repeating it. Gate inventory: `verify.sh`'s own header. Source
inventory: `SOURCES.sha256`. Figure inventory: `build_all.py --list`.

## How this territory is verified

```bash
cd figures && bash verify.sh     # the stop gate; run it before every commit
```

It prints the tree, branch and commit before the first gate. That line is not
decoration: a green taken in the wrong worktree is byte-identical to a green
taken in the right one, and this pipeline has already published one confident
false negative on exactly that (V20 ran the gate in a linked worktree in which
the inputs under audit did not exist, got ten green, and reported the ticket
mistaken).

Two probes carry their own negative controls and must be shown refusing before
their green is read as agreement: `check_coverage.py --self-test`,
`reconcile_cost.py --selftest`, `check_tracking.py --selftest`. `verify.sh` runs
each control *before* the check it guards.

## Standing rulings

### D-F-006 · The envelope ledger shards are tracked, and the guarantee is derived from git rather than counted (V23, 2026-07-29)

`envelope_ledger` was written `tracked=False, optional=True, floor=0` because the
shards were untracked and "absent is the expected state". All fifteen are now
committed — `baseline-arms`' own commits brought the eleven `a7*` ones on
2026-07-28, A14 (`9307f139`) the four dev-pile ones the next day. The declaration
is now **`tracked=True`, with `optional=True` and `floor=0` kept**, and the
guarantee a floor was reaching for supplied instead by `tracked_but_missing()`:
every member git tracks must be on disk.

**Why not a floor of 15.** Because `release/LICENCE_POSTURE.md` classifies these
shards class B — excluded from the release by default, shipped as a digest plus a
reproduction script — so the release tree has none of them, and a numeric floor
turns gate 0 red there before any other gate runs. And because 15 is an asserted
completeness count of exactly the kind `PLAN.md` house rule 5 forbids. Deriving it
answers both: strictly stronger than a floor (a sixteenth committed shard going
missing is caught too), silent where git cannot be asked, and no number to age.

**Why not leave it.** `SOURCES.sha256`'s status column is written from
`Source.tracked` — a declared boolean, never a query. Gate 4 compares a committed
manifest against a freshly generated one, so both sides read that declaration and
agreed with it: the manifest asserted `[untracked]` about fifteen committed files
and every gate was green. `paper/index.json` published `"tracked": false` for the
same fifteen.

Measured separately, because the distinction is the finding: the declaration flip
alone changed **thirty assertions in two generated files and nothing else** —
`csv/`, `out/`, `paper/captions/` and `paper/INDEX.md` came out byte-identical.
That is the evidence that this was a false statement about the tree and not a
stale figure. fig02's plate did move afterwards, for a second and separate
reason: it prints the word "optional" about these shards on its own face, and
that word had to go with the declaration.

The floors on `theoria_run` (4) and `pilot_rollup` (6) stay. For a family that
nothing excludes downstream, a high-water mark somebody checked once is the right
instrument, and a floor read from the tree at build time would equal whatever the
tree holds and could never fail.

`check_tracking.py` (gate 13) exists so that this class cannot recur silently. It
reads the committed artefact and asks `git ls-files`, `os.path.isfile` and its own
sha256; it must never import `sources.py`. Shown failing on the tree it was
written for: `runs/20260729T172327Z-V23-figures-sources-absent/check_tracking.BEFORE.txt`,
fifteen problems at `580c645d`, where `verify.sh` was green on all thirteen gates.

### D-F-007 · Figures 5 and 6 are promoted; Figure 4's fate follows §6's (V23, 2026-07-29)

The board asked: the three plates the paper does not cite must either enter the
body or go offline, with the disposition recorded here. The ruling is **not uniform
across the three**, and the first draft of it was — on a premise that turned out to
be backwards. See the correction box below; it is left in because how this ruling
was wrong is more useful than a clean-looking ruling.

| paper № | plate | ruling | home | why |
|---|---|---|---|---|
| Figure 5 | `fig03_capability_spectrum` | **promote** | `sections/07_battery.md` §7.1 | §7.1 states the matrix as a bare list of totals — 38 metrics × 5 arms, 1 433 values, 2 066 `not-applicable`, 111 `insufficient-data`. The plate draws exactly that, with absence hatched and outlined rather than zeroed. In scope: `OUTLINE.md`'s mandate is "Phase 1 结:A0–A2 + 电池对既有轨迹的回算", so the battery recompute belongs, and §7 is the paper's strongest material by its own reviewers' account |
| Figure 6 | `fig02_bill_shape` | **promote** | `sections/07_battery.md` §7.8 | E2 and E3 are two of Phase 4's three pre-registered primary endpoints, and §7.8 argues about them in prose only. The plate is the construction they are defined by, including the eight-turn refusal §7.8 describes in words |
| Figure 4 | `fig04_a3_transfer` | **hold — do not promote into §6 yet** | would be `sections/06_a3_transfer.md` §6.2 | The plate is a faithful redraw of §6.2's own table, and §6 is under live recommendation to be cut or demoted by two independent P12 seats. Promoting a figure into a section two reviewers want gone is not a disposition, it is a bet. Its fate follows §6's: full section → promote per P10's text; demoted to an appendix → the plate goes with it; cut → retire the plate and delete it from `build_all.FIGURES` |

**Why promote at all, rather than retire.** For Figures 5 and 6: each is a redraw
of a claim the body already makes in prose, in the section its own reviewers rate
highest. Retiring those removes evidence rather than removing a burden, and V20's
*"a figure nobody cites is a burden that will drift"* is right about the cost and
answered by the gates rather than by deletion.

**Blocked upstream of all three, and this is not a figures defect.** The paper
**embeds no figure at all** — P12's lay seat: *"three figures that are cited but not
present … There is no figure in the document — no image, no embed, no ASCII
rendering, nothing."* So Figures 1–3 are cited and unrenderable today, and
promoting three more citations into that document adds three more. Whoever executes
D-F-007 should fix the embedding first; otherwise "cited" and "reaching a reader"
stay different things, which is the condition this ruling exists to end.

**A quieter authority conflict, resolved and named.** `OUTLINE.md`'s own figure
table lists **three** figures and does not contain `fig02`/`fig03`/`fig04`, while
`figures/paper_map.py` assigns six. So "three plates reach no reader" is arguably
the paper's design rather than an omission. I resolved it toward six, because the
pipeline built, captioned, hashed and published all six and the release manifest
carries all six — but the paper side is entitled to resolve it the other way, and
if it does, the honest consequence is retirement, not silence.

> **CORRECTION (same run, after adversarial review).** This ruling first read
> *"promote, all three"*, and its single stated justification was: *"§6 and §7 are
> precisely the two sections P12's two reviewers independently named as weakest on
> evidence."* Every part of that is wrong, and it is a reversal rather than an
> overstatement:
>
> * P12 ran **five** independent seats, not two — domain, methods,
>   reproducibility, hostile, lay. Its own mid-run note warns *"Do not treat two
>   reviews as five."*
> * The word "weakest" is applied to no section by any seat. The domain seat calls
>   §7's anti-gaming register *"The widest daylight in the paper."*
> * The one documented independent convergence says the opposite of what I claimed:
>   the domain and lay seats, without seeing each other, both flagged that §7.7 is
>   the paper's **best** material and is buried as item four of four.
> * Both seats that discuss §6 want **less** of it. The lay seat, asked to cut,
>   drops §6 outright: *"A ratio of 0.029 against a strawman denominator is not a
>   workshop result."* The domain seat's MAJOR M4 offers demoting §6 to an
>   appendix.
>
> So the only argument I had offered for promoting Figure 4 was an argument against
> it. The plate is unchanged and still good; its home section is the problem. I had
> read a review summary rather than the reviews, and a ruling in this file is
> permanent record — which is exactly where that shortcut costs the most.

**Why it is still not done, and what would finish it.** The body text is
`papers/` territory. P10 wrote the three insertion paragraphs and their exact
anchors (`runs/20260728T134521Z-P10-figures-into-paper/HANDOVER-papers.md`, ready
to paste, style-matched to the three citations that exist); all three anchors are
still intact and unfollowed. P10, P13, V20 and V23 each held `figures` and none
held `papers`, which is the whole reason this has survived four runs. Handed over
again, with this ruling attached, in
`monitor/inbox/20260729T182000Z-W-1681-figures-4-5-6-promote-ruling.md`.

**The executable form of this ruling already exists and is not merged.** V20 wrote
`figures/check_figure_citations.py` — every name in `build_all.FIGURES` must be
cited in the paper's prose or declared in `NOT_CITED_ON_PURPOSE` with a reason,
and a declaration that goes stale in either direction fails. That is the right
gate. Its branch `agent/v20-figures-pipeline-red` has been held on a merge
conflict inside `figures/verify.sh` since 2026-07-29T14:49Z. Two notes for
whoever lands it: its three `NOT_CITED_ON_PURPOSE` reasons are factually wrong
(they say A3 transfer and the capability spectrum have no home section; §6 and
§7.1 are their home sections and were there when the reasons were written), and
they should be replaced by this ruling's row for each plate. V23 deliberately did
**not** write a second implementation of that gate.

## Open handovers

| what | owner | where it is written down |
|---|---|---|
| Figures 4/5/6 into `sections/06_a3_transfer.md` and `sections/07_battery.md` | `papers/` | D-F-007 above; `runs/…P10…/HANDOVER-papers.md`; `monitor/inbox/20260729T182000Z-W-1681-…` |
| `agent/v20-figures-pipeline-red` held on a conflict; its citation gate is the executable form of D-F-007 | monitor / merge queue | `monitor/ci/CONFLICT-origin_agent_v20-figures-pipeline-red.md` |
| No per-territory gate status exists anywhere, so a `figures/` gate broken from outside `figures/` reaches no dashboard | monitor | `runs/20260729T172327Z-V23-figures-sources-absent/FINDINGS.md` F-2; `monitor/inbox/20260729T182000Z-W-1681-…` |
| `fig06_concept_timeline`'s `EXPECTED_IDS` pins an id set from `cold-start-a0/THEORIZE_LOG.md`, a file the other track edits; it has gone red twice | cross-track contract | A12's run notes; filed to `monitor/inbox/` by A12, unresolved |
| `papers/phase1-workshop/README.md` still tells a reader to rebuild figures with the three retired ASCII extractors, not `build_all.py` | `papers/` | `runs/…P10…/HANDOVER-papers.md:141-145` |
| `release/reproduce.py` rebuilds the figures and never runs their stop gate | `release/` | V23 FINDINGS F-2 |
| **`figures/` cannot build in a default release tree, and never could.** `release/LICENCE_POSTURE.md:48` puts `baseline-arms/ledger.jsonl` in class B ("Default: excluded") and `sources.py` declares it required, so gate 0 goes red on the ledger before any other gate runs. Either the plates that read class-B inputs are declared unbuildable downstream, or those inputs get written permission | `release/` | `runs/20260729T172327Z-V23-figures-sources-absent/release_tree_probe.{py,txt}` |

## Known gaps in the figures themselves

Carried forward from `RUN_STATE.md:109-124`, still true, listed here because a
reader looking for the state of this territory will not think to look in a run
narrative from P4:

* fig02 has no Schema arm and cannot get one — the model ladder stands in for it,
  weaker by `battery/REPORT_V0.md`'s own note. Absence, not zero.
* fig02's cross-arm comparison is confounded by construction: every theoria run
  is a self-built world. The plate says so on its face, as a banner.
* fig06's clock covers one milestone of eight.
* fig07 has no battery panel for A0′.
* Gate 9 reports a standing `KNOWN DEFECT RESET_IN_DENOMINATOR` — 78 runs where
  `capability_spectrum.actions` counts the successful RESET, against
  `proxy/SCORING.md:60-62`. Reported on every run rather than subtracted.
* **Gates prove reproducibility, not correctness.** Look at the plates.
