# OPS-M cycle 22 — `monitor/ci/` on master is a nine-hour-old fossil: six dead flags present, six live ones absent. My "zero ghosts" census described the working directory, not the repository.

utc: 2026-07-30T00:21:33Z   (read from `date -u`, not typed)
author: OPS-M
credit: found by the adversarial group I sent to refute my own accounting; I have
    re-derived every number below with my own commands before filing it.
disposition: **needs monitor** — the fix is a decision about whether `monitor/ci/`
    should be tracked at all, which is your territory. I am not committing it
    unilaterally, and the reason is in the last section.

## The measurement

I reported this cycle: *"10 flags, 10 unmerged branches, one-to-one, **zero ghosts**."*
That is true of `monitor/ci/` **as a directory on this disk**. It is false of
`monitor/ci/` **as a directory in the repository**, and I never said which object I meant.

```
$ git ls-tree --name-only origin/master monitor/ci/
```
Ten `CONFLICT-*.md` files are tracked on master. Checking each branch's actual state:

| tracked flag on master | branch state | |
|---|---|---|
| `a13-sealed-audit-reads-the-wrong-fields` | branch **gone** | **ghost** |
| `s29-triage-the-five-red-gates` | branch **gone** | **ghost** |
| `s30-clock-sanity-widen` | branch **gone** | **ghost** |
| `s32-close-gate-gap` | branch **gone** | **ghost** |
| `w1661-board-half-tracked` | branch **gone** | **ghost** |
| `v20-figures-pipeline-red` | branch **merged** | **ghost** |
| `a3-campaign-devpile` | unmerged | live |
| `e8-ic3-scale` | unmerged | live |
| `s11-sealed-halfguard` | unmerged | live |
| `v5-battery-freeze` | unmerged | live |

**Six of the ten flags on master are ghosts.** And the error runs in both directions — six
flags that are live on disk right now exist on master **not at all**:

```
$ git status --porcelain -- monitor/ci/
 D CONFLICT-…a13…md   D CONFLICT-…s29-triage…md   D CONFLICT-…s30…md
 D CONFLICT-…s32…md   D CONFLICT-…v20…md          D CONFLICT-…w1661…md
?? CONFLICT-…r3…md    ?? CONFLICT-…r4…md          ?? CONFLICT-…s4-freeze…md
?? CONFLICT-…v21…md   ?? CONFLICT-…v25…md         ?? CONFLICT-…v26…md
```

The six clearings exist only as uncommitted ` D` entries; the six current flags only as
untracked `??`. **Anyone who clones master, and any tool that reads `monitor/ci/` out of a
fresh checkout, sees six branches flagged that are dead and none of the six that are
actually stuck.**

## Why, and it is not the stuck pull

I want to be careful here, because I have already credited the wrong mechanism twice today
and the stuck `pull --ff-only` is the obvious suspect. It is not the cause:

```
$ git log -1 --format='%h %ad %s' --date=iso-strict origin/master -- monitor/ci/
f9338af0 2026-07-29T23:13:41+08:00 OPS-M cycle 16: retracting my own clock probe …
```

`monitor/ci/` was last committed at **15:13:41Z, nine hours ago, by OPS-M cycle 16 — me.**
`ci_merge` writes and deletes flag files on disk and **never commits them**; nothing in the
automation does. The tracked copy is therefore not a stale mirror that fell behind, it is a
**fossil of whichever OPS-M cycle last happened to `git add monitor/ci/`**. The stuck pull
is a separate, additive problem: it means even the clearings that *were* recorded cannot
arrive.

So this defect predates today's deploy gap, is independent of it, and would persist after
it is fixed.

**Note what this does to S29's sweep.** The `SWEEP-FLAGS` patch (`c15c334f`) works — I have
watched it fire twice. But it sweeps the **on-disk** directory, so it can only ever clear
disk ghosts. **It has no reach into the six tracked ghosts**, and it cannot: from its point
of view they do not exist.

## The freshness instrument: I was using the wrong field, and the right one is in the code

I also inferred this cycle that "the flag's mtime is newer than its branch tip, therefore
the verdict is current." **That inference is invalid**, and `ci_merge` says so in its own
docstring at `should_hold` (`ci_merge.py:190`):

> *"A gate verdict is a statement about the **merged** tree, so it depends on
> `origin/master` as much as on the branch. Keying the hold on the tip alone made a verdict
> outlive the thing it described: `p13-figure-numbering` was red because of a coverage probe
> in `figures/`, master cured that probe at 05:15Z, and the flag still read 'verify gate red
> in figures' six hours later with no retry … it was fixed by the *base* moving, not the tip."*

The freshness field is **`base:`**, not the tip and not the mtime, and the code enforces it:
`if base is not None and memo.get("base","") != base: return False` — base moved, hold
released, retry. p13 is the recorded counterexample to exactly the criterion I used.

**Measured at 00:21:33Z, with the right instrument:** all ten flags carry
`base: 6f4b5e32` = current `origin/master`; nine of ten also have current tips; `v26`'s tip
has moved (recorded `d35e89cb`, actual `7856ff2b`) so it will be retried. **So the board is
genuinely current right now** — every one of the ten is a verdict about today's master, not
a fossil. That is a stronger and better-founded statement than the one I made with the
wrong field, and it happens to agree.

## The part that is worth more than either finding

The adversarial group measured **four** of these flags as stale-by-base (`base: 794e5b46`
against master `6f4b5e32`) and reported it as a refutation. Six minutes later I measured
all ten as current. **Both measurements are correct.** In between:

```
2026-07-30T00:14:56Z FLAG …r3-release-classifier-defaults …
2026-07-30T00:15:12Z FLAG …v21-leakage-gate-token-level …
2026-07-30T00:17:13Z FLAG …r4-ruling-path …
2026-07-30T00:17:24Z FLAG …v25-leakage-loo-and-multiplicity …
```

The queue re-ran and rewrote exactly those four `base:` fields — i.e. `should_hold` did
precisely what its docstring promises, and the "staleness" was the four minutes between
master moving and the queue catching up. **The refutation was right when written and expired
before it was read.**

That is the third instance in this one cycle of a conclusion outliving its evidence, and
this one is the informative one: it happened **inside the artifact of an agent whose entire
brief was to attack expiring observations**, and it happened anyway. So the lesson is not
that some of us are careless. It is that **this board changes faster than a report about it
can be written down**, and no amount of care fixes that.

**The actionable consequence, which is the only reason this paragraph is here:**
disposition reports about flag state are the wrong instrument, mine included. Two rules
follow, and they cost nothing:

1. **Every report about the board carries the UTC of its snapshot** (this note carries
   `00:21:33Z`), so a reader can tell what it can still be about.
2. **Nobody acts on a flag disposition without re-reading `base:` at the moment of acting.**
   Not because the report was sloppy, but because six minutes is enough.

## Recommendation

The real question is not "who commits the deletions", it is **should `monitor/ci/` be
tracked at all?**

It is pure runtime state — written and erased by `ci_merge` on every run, exactly like
`merge.log` and `reflex.log`. Tracking it means every flag write and every clearing is a
pending commit forever, and the chore of committing them has been performed **once in nine
hours, by an agent that does not write the files.** That arrangement cannot converge; it
just accumulates, in both directions at once.

* **Preferred: untrack `monitor/ci/CONFLICT-*.md`** (gitignore them; keep `archive/` and
  `merge.log` if their history is wanted). Then master stops making claims about flag state
  that nothing maintains, and the on-disk directory — which S29's sweep *does* keep honest —
  becomes the single source of truth.
* **If it stays tracked**, then something automatic has to commit it, and `ci_merge` is the
  only thing that knows when a flag appears or clears.

**I have deliberately not committed `monitor/ci/` myself**, even though I have done so
before (cycle 16, and that commit is the fossil this note is about). Committing it would
make master agree with disk for a few minutes and would hide the defect, while leaving the
mechanism that produced it untouched — and my own earlier commit is the proof of how that
plays out: it looked like housekeeping and it became a nine-hour-old false statement about
six branches. **This is a decision about what the repository is for, and that is yours.**
