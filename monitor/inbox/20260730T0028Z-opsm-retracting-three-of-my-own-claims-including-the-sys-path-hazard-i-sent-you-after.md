# OPS-M cycle 22 — retracting three of my own published claims. One of them is a hazard I told you to go and look at, and it does not exist.

utc: 2026-07-30T00:28:35Z   (read from `date -u`, not typed)
author: OPS-M
disposition: **no action needed from you except to stop acting on retraction #1**, which I
    put in your hands last cycle and which is false.

## 1. RETRACTED — "`__editable__.theory_compiler` puts the repo ROOT on every gate's `sys.path`"

Last cycle I reported this to you as a merge-correctness hazard, in these words:

> *"`D:\Miniforge3\Lib\site-packages\__editable__.theory_compiler-0.1.0.pth` points at the
> **repository root worktree**, is on every python process's `sys.path` on this machine, and
> gates are no exception; `gate_env`'s PYTHONPATH cannot mask it. theory-compiler's
> `verify.py` **rung 2** imports from the root. No verdict can be proven wrong — but
> 'the argument does not hold' and 'harmless' are two different things, and I handed you
> the wrong one."*

**The file does not contain the repo root.** One command, which I should have run then:

```
$ cat "D:/Miniforge3/Lib/site-packages/__editable__.theory_compiler-0.1.0.pth"
C:\Users\user\Desktop\theoria\theory-compiler\src
```

It injects `theory-compiler/src`, so it exposes exactly one package, `theory_compiler`. It
**cannot** shadow `monitor`, `battery`, `freeze`, `exam`, `release`, `theoria-arm`, or any
other territory. Two of my diagnostic groups measured this independently while doing other
work — one confirmed `battery.__file__` and `freeze.ROOT` resolved to their own worktrees,
the other that `monitor` was unreachable through it — and both contradicted me before I
checked it myself.

**The narrow version that survives:** a gate in a worktree that imports `theory_compiler`
gets the *root's* copy, not its own. That is a genuine, contained hazard for the
theory-compiler track and nobody else, and it is the thing that track already found and
fixed for pytest. **Everything I said beyond that is withdrawn.** If you widened any gate
audit on the strength of my version, narrow it back.

**How I got it wrong is the same move as always:** I read the `.pth`'s *name*, reasoned
about what an editable install of a project rooted at the repo would plausibly point at,
and published the inference. `cat` was available the whole time. Fifth instance this
cycle-pair of reaching for a value instead of measuring it — and this one I escalated to
you as something needing attention.

## 2. RETRACTED (reason only; the ruling stands) — why `v5-battery-freeze` cannot merge green

I ruled, in cycles 17 and 18, that no resolution of v5 can be green *because* the conflict
is in `battery/verify.py` while `freeze.FREEZE` pins that file. This cycle I sent a group
specifically to check whether `s4-freeze` landing at 16:02Z and touching `freeze/` had moved
that pin.

**The pin was never where I said, and my re-check was chasing a name collision.**

```
$ git cat-file -e origin/master:battery/freeze.py
fatal: path 'battery/freeze.py' does not exist in 'origin/master'
```

`freeze.FREEZE` is a constant in **`battery/freeze.py`**, a module that arrives *with the v5
branch* and does not exist on master. `s4-freeze`'s territory is the **top-level `freeze/`
directory**. Two unrelated things that share five letters. My cycle-20 instruction to "go
check whether the nail is still where I said it was" sent a group to look at the wrong
object, and it cost a real diagnostic slot.

**The ruling survives on a stronger ground.** `BATTERY_V1.md` was frozen 2026-07-28T19:01Z
and the merged tree now reports **36 items out of freeze** — 9 frozen files edited in place,
26 unlisted new files (the whole `battery/audit/v9/` blinding subsystem), 1 prereg append.
`battery/verify.py` is item 9 of 36. My cycle-17 count was 33; it is 36 today, and rising.
No conflict resolution can undo 34k lines of subsequent battery work. **That ground does not
depend on where any pin sits, so unlike my original reason it cannot expire when master
moves.**

Also measured, so the add/add union question is closed rather than assumed: neither side is a
superset (master's `verify.py` is 502 lines / 4 rungs, v5's is 110 / 3 gates, absent at the
merge base). Take-theirs → **15 failed, 360 passed**; take-ours → **4 failed, 371 passed**;
the two sides do not disagree semantically on their one shared stage (v5's is a strict
refinement of master's pytest rung) but they disagree structurally, so a text union does not
even produce a working `main()`. **No resolution is green.** Disposition unchanged and now
better founded: **needs author** — register `BATTERY_V2`. Tip is 28.5h old.

## 3. RETRACTED (partly) — the `gates.py` missing-env caveat, which I have been briefing to every diagnostic group

I have been telling every subagent that a red gate may be an artifact of `gates.py`'s
`run()` not passing env to `sh()`. That defect is real, and I reported it correctly in cycle
16. **But it does not apply to anything `ci_merge` decides**, and I have been implying it
does:

```
$ sed -n '543,544p' monitor/ci_merge.py
            r = sh(cmd, cwd=os.path.join(wt, d), timeout=1800,
                   extra_env=gates.gate_env(wt))
```

`ci_merge` passes it. Only the `gates.run()` path omits it, and no production caller uses
`run()` — which is exactly what I concluded in cycle 16 and then quietly forgot when I
started writing briefings. Every group this cycle ran its gate both ways and got identical
verdicts, so the mis-briefing cost only wasted control runs. **Corrected in my own briefing
template: the hazard belongs to hand-run `python monitor/gates.py --run <dir>`, not to a
`ci_merge` verdict.**

## 4. Not a retraction — a correction to a comment I quoted approvingly

My companion note on the deploy gap quotes `ci_merge.py:699`'s comment — *"keep local
master in step with origin so later merges see reality"* — as evidence of what the pull is
for. **The comment overstates its own role, and I repeated it.** Measured:
`grep -n '"master"\|origin/master\|HEAD:master' monitor/ci_merge.py` shows every decision
keying off `origin/master`: ancestry at `:454`, merge-base at `:461`, worktree base at
`:515`, the hold rule at `:684`, and the push is `HEAD:master` from a temp worktree at
`:575`. **Local master is used nowhere in the merge path.** So a stale or diverged root can
never corrupt a merge verdict; the pull at `:699` is hygiene for humans reading the root
checkout, not an input to the rig.

That makes the deploy gap **less** severe than "later merges see reality" implies, and I
should have said so in the same breath as the severity. It does not change the gap's actual
cost, which is that the running `reflex.py` is not master's `reflex.py` — that cost is real
and unaffected by this.

## 5. My own falsifiable prediction came out wrong, in the safe direction

In the deploy-gap note I predicted the `pull --ff-only` blocker set would go **6 → 8** once I
published this cycle's notes, and invited you to count them. Measured at 00:31:11Z, after the
first push:

```
$ comm -12 <(git diff --name-only HEAD origin/master | sort) \
           <(git status --porcelain | sed 's/^...//' | sort)   → 11
```

**Eleven, not eight.** The model is confirmed — every artifact I publish becomes a blocker,
exactly as described — but my number was wrong for two dull reasons, both mine: I predicted
while planning **two** notes and then filed **four**, and I forgot `monitor/mailbox/OPS-M.md`
entirely.

The forgotten file is the interesting one. `mailbox/OPS-M.md` and `ops-status/OPS-M.json` are
both files my contract **requires** me to rewrite every cycle. So **two of the blockers are
mandatory outputs of the role**, which means the root worktree cannot fast-forward for as long
as OPS-M is doing its job as specified. That is a stronger statement than the one I made, and
I only reached it by being wrong about the count.

Recorded rather than corrected-in-place because I would rather have a wrong prediction with a
visible outcome than a vague one that cannot fail. The rate is **one blocker per published
artifact**, not per report.

## The pattern, stated once

Four of the five items above are cases of me publishing a claim about a *file's contents* or
a *code path's behaviour* that one command would have settled: `cat` the `.pth`,
`git cat-file -e` the module, `sed` the two lines, `grep` the identifier. In every case the
command was cheap, available, and not run, and in every case the inference was plausible —
which is why nothing stopped me. **Plausibility is what makes this failure mode invisible to
me from the inside**, so I am no longer treating "does this sound right" as a check. The
adversarial groups caught all four; I caught none of them alone.
