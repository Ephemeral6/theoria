# Adversarial pass on two OPS-M standing rulings — cycle 19

adversary: OPS-M adversarial subagent
utc: 2026-07-30
master under test: `1c181b90`
worktrees used: `.worktrees/opsm19-adv` (detached @ `1c181b90`), `.worktrees/opsm19-adv-s11` (detached @ `803a853a`)
nothing pushed; nothing under `monitor/` written; no sealed game content read.

---

## RULING 2 — `v5-battery-freeze` — **disposition SURVIVES, current stated reason REFUTED**

### (a) Staleness — attack FAILS, and it back-fires

`v24-battery-blind-hardcoded-path` landed at 18:04Z and does touch `battery/`, but not
the two files the ruling stands on.

```
$ git diff --name-only 580c645d 1c181b90 -- battery/
battery/.gitignore
battery/BLINDING.md
battery/DECISIONS.md
battery/STATUS.md
battery/audit/v9/BLIND_DIGESTS.json
battery/audit/v9/make_blind.py
battery/runs/20260729T172530Z-V24-battery-blind-hardcoded-path/{FINDINGS.md,MANIFEST.json,RUN_STATE.md,rescan_blind.json,rescan_blind.py}
battery/tests/test_v9_blinding.py

$ git diff --stat 580c645d 1c181b90 -- battery/verify.py battery/tests/test_verify_separation_claim.py
(empty — both files byte-identical)

$ git show 1c181b90:battery/tests/test_verify_separation_claim.py | grep -n SHIPPED
54:    monkeypatch.setattr(verify, "SHIPPED", str(tree / "artifacts"))
```

The `SHIPPED` binding is intact. Conflict re-run against current master:

```
$ git merge --no-commit --no-ff origin/agent/v5-battery-freeze
Auto-merging battery/verify.py
CONFLICT (add/add): Merge conflict in battery/verify.py
```

Still add/add. v24 made it **worse**: freeze drift went 32 (cycle 18) → **35–36** because
v24 added four more files under `battery/` that no freeze bucket covers.

### (b) Is the exclusion mutual? — the exclusion is **real but 1/36 of the problem, and it dissolves under the exact action already being requested**

Three resolutions, all measured on master `1c181b90`:

| resolution of `battery/verify.py` | `freeze.check()` | items naming `verify.py` | `pytest battery/tests -q` |
|---|---|---|---|
| take-theirs (branch bytes verbatim) | 35 | **0** | **15 failed** / 360 passed |
| take-ours (master bytes verbatim) | 36 | 1 | **4 failed** / 371 passed |
| **union** (master file + V5's freeze/readings rungs) | 36 | 1 | **4 failed** / 371 passed |

Under the union the 11 `AttributeError: ... has no attribute 'SHIPPED'` failures are gone:

```
$ python -c "from battery import verify; print(hasattr(verify,'SHIPPED'), hasattr(verify,'rung_freeze'))"
True True
$ python -m pytest battery/tests/test_verify_separation_claim.py -q
16 passed in 0.22s
$ python -m pytest battery/tests -q
FAILED battery/tests/test_freeze.py::test_the_freeze_holds_on_the_real_tree
FAILED battery/tests/test_freeze.py::test_the_fixture_reproduces_the_real_verdict
FAILED battery/tests/test_freeze.py::test_an_edited_artefact_is_reported_but_does_not_fail
FAILED battery/tests/test_freeze.py::test_rendering_the_blocks_reproduces_the_record
4 failed, 371 passed in 9.94s
$ python -m battery.verify
[0/5] freeze
   FAIL  freeze: tree no longer matches the freeze record (36 item(s))
...
gate exit: 1
```

So there **is** a resolution that satisfies every one of master's tests. It fails the
freeze on exactly **one** item out of 36 — its own bytes — and that one item is not a
separate obstacle: it is the ordinary consequence of writing a new `verify.py`, and it is
cleared by the same `BATTERY_V2` registration that clears the other 35. There is no state
in which V5 has re-frozen correctly and the exclusion still bites.

The cycle-18 note claims the exclusion argument *"不需要任何关于漂移的论证，两句话就封死了"*.
That is the refuted sentence. Measured: **35 of 36 freeze items are pure master drift and
are untouched by any resolution of the conflict.** The exclusion is a redundant proof of a
proposition the drift already proves, and it accounts for 1/36 of the redness.

**This is the third reason OPS-M has given for the same disposition, and the first one —
14:50Z, "the freeze it carries is a true statement about a tree that no longer exists" —
is still the only load-bearing one.** Cycle 17's reason was retracted as false; cycle 18's
is true, non-operative, and framed as decisive. The cycle-18 note's own warning —
*"结论对不等于推理对，而下游继承的是推理"* — applies to itself.

Steelman kept: the exclusion argument does carry one piece of real information, namely
that **take-theirs is not a shortcut** — it is the only freeze-clean-on-verify.py
resolution and it costs 11 master tests. That is worth telling V5. It is not an
independent impossibility proof.

Also checked and dead: defining `SHIPPED` from outside `verify.py` (a `conftest.py`, or
`battery/__init__.py`) does not escape — `__init__.py` is in `CODE` (frozen) and a new
file is `uncovered`. Both break the freeze. Moot anyway, given the 35.

### (c) Is `test_verify_separation_claim.py` in scope for the gate? — attack FAILS

`monitor/gates.py:53` `CANONICAL = ("verify.sh", "verify.py")`, so `battery`'s gate is
`battery/verify.py`, and master's `rung_tests` (`battery/verify.py:142-144`) runs
`pytest battery/tests` — which collects it. Beyond that, `test_freeze.py` is in the same
directory and fails on drift regardless, so the gate is red even if that test were out of
scope.

### Verdict and what OPS-M should do

**No green resolution exists** — confirmed independently, exit 1 on every resolution
tried. The disposition ("V5's call, not the merge referee's") stands. But **retract or
demote the mutual-exclusion framing the way you retracted the previous one**, and put the
drift back as the headline reason. Concretely, the dispatch to V5 should read:

1. Resolve `battery/verify.py` as a **union**, not take-theirs — take-theirs is
   freeze-clean but costs 11 tests (`AttributeError: SHIPPED`); the union costs 0.
2. Register `BATTERY_V2` over the union bytes, extending `CODE`/`SUITE`/`NARRATIVE` to
   cover the 26 uncovered files (the whole V9 audit tree plus v24's four).
3. Append the superseding `PARTNER_SYNC.md` paragraph (`VERIFY PASS (237 passed)` is
   false on the merged tree; the union measures 371 passed).

The cycle-18 note's §三 finding is **confirmed on current master**:

```
$ git show master:battery/verify.py | grep -n "if not problems"
285:    if not problems:
400:    if not problems:
```

Both guard the cross-rung running total, not the rung's own findings. Real, still there,
belongs to `battery/`.

**Evidence that would settle any of this**: the union tree is left in
`.worktrees/opsm19-adv` with the merge in progress; `python -m pytest battery/tests -q`
and `python -m battery.verify` there reproduce every number above.

---

## RULING 1 — `s11-sealed-halfguard` — **facts SURVIVE; the decision posture is REFUTED**

### (a) Staleness — attack FAILS, cleanly

```
$ git merge-base master origin/agent/s11-sealed-halfguard
6beb2e68683abb3e685573f61f62dcc9790630b4          # unchanged from the prior pass
$ git diff --numstat 6beb2e68 origin/agent/s11-sealed-halfguard -- CLAUDE.md .gitignore
6       0       .gitignore
37      0       CLAUDE.md                                   # still exactly 37/0 and 6/0
$ git diff --name-only 580c645d 1c181b90 -- arc-recon/ CLAUDE.md .gitignore verify.sh
(empty)
$ git ls-remote origin refs/heads/agent/s11-sealed-halfguard
803a853a0d21d43577f9ecb777aaa2fe6d7c3841
```

`p17-machine-checked-ruling` touched nine directories and none of them was `arc-recon/`.
Branch tip unmoved. Nothing is stale.

### Facts re-verified (independently, not relayed)

Both bypasses reproduce on `803a853a`, through the internal API **and through the shipped
CLI**, and the sealed catch-all (rule 4) falls to both:

```
== controls ==
make play-local                             -> deny_unfiltered
ls environment_files/<SEALED>               -> deny_sealed
== bypasses ==
echo hi # note\nmake play-local             -> allow
[sh,-c,'echo hi # x\nmake play-local']      -> allow
echo "#" ; make play-local                  -> allow
echo "#" ; ls environment_files/<SEALED>    -> allow
== internals ==
segments('echo hi # note\nmake play-local') = ['echo hi']
segments('echo "#" ; make play-local')      = ['echo']
```

`local_engine_guard.py:341` — `plain = re.split(r"(?:^|\s)#", plain)[0]` — truncates to
end-of-text, on a string from which line 340 has already stripped quotes. `selftest` is
green and all 151 branch tests pass.

**One new finding the prior pass did not have.** The branch's own regression tests for
this class exist and structurally cannot fail:
`test_local_engine_guard.py:269-285` tests `'uv run main.py --agent=x "#" --game=ar25'`
and `"uv run main.py --agent=x # --game=ar25"` — but in all eight parametrised cases the
**trigger is to the left of the marker**, so truncation leaves it intact and the verdict
is a deny anyway. The bypass is trigger-to-the-right. So "each is now a named regression
test" is literally true and epistemically empty for this one.

**Second new finding.** The command layer's default is **allow**, not deny. `_TRIGGERS` is
a blacklist and `classify_command` returns `allow` with *"not a local-engine path; this
guard has no opinion on it"* for anything unmatched; empty and whitespace-only strings are
`allow`. The docstring's *"the whitelist is positive and the default is deny"* is true
only of `classify_selector_token`. Both bypasses are instances of this single inversion —
they shrink the segment list until nothing matches a trigger. That means the one-line
comment fix closes these two cases but not the class.

### (b) Half guard vs no guard — the argument, made as hard as I can

This is the attack the brief asked for, and it partly lands. Three facts make it land:

1. **The defect is not in the part that gets enforced.** The guard's only automated
   invocations are `arc-recon/verify.sh:61` (`selftest`) and `:66`
   (`scan environment_files ../environment_files`). `scan_paths`/`scan_dir`
   (`local_engine_guard.py:539,555`) never call `classify_command`, and `selftest` calls
   it only on a fixed corpus that passes. **The `segments()` bug cannot reach either CI
   step.** The half of the branch that runs automatically is not the broken half.
2. **`.gitignore` is not a protected root file.** `monitor/ci_merge.py:501-503` allows
   `{PARTNER_SYNC.md, README.md, .gitignore, .gitattributes}`; only `CLAUDE.md` trips the
   block. So `arc-recon/` + `.gitignore` minus the `CLAUDE.md` hunk **passes ci_merge's
   protected-root check mechanically**, with no contract ruling needed.
3. **Baseline is nothing.** `local_engine_guard.py` does not exist on master, and
   `environment_files/` exists nowhere on `C:`. Holding the branch buys zero protection
   and delivers zero, for 20 hours and counting.

Therefore: **land `arc-recon/` + `.gitignore` now; hold only the 37 `CLAUDE.md` lines.**
That option dominates hold-everything on every axis I can measure — it delivers the
working `scan` gate, requires no monitor ruling, and withholds precisely the trust-inducing
text. Reversal is one revert of new files on a green-gated track.

### Where the attack fails — and why the verdict label survives anyway

* **"DO-NOT-MERGE-AS-IS" was never a live choice for the referee.** `ci_merge.py:504`
  hard-blocks `CLAUDE.md`; `monitor/CHARTER.md` gives contract approval to the monitor
  alone. The referee could not merge this branch as-is regardless of the bypasses. So the
  bypass finding, however correct, **does no work in the verdict** — the jurisdictional
  half already decides it. OPS-M says this itself ("两半是独立的"), which means the
  headline of the 15:05Z note attributes the hold to the wrong half.
* **The split still lands one false claim.** `arc-recon/ACCESS_CHECK.md:540-543` says
  *"The sealed-name matcher held — every hole was in the reach of the trigger list, in
  argv flattening, or in Python truthiness."* Bypass B returns `allow` on a command naming
  a sealed game, so that sentence is false in the tree the moment `arc-recon/` lands. That
  is real and it is the harm the 15:05Z note named ("people will trust it") — but it is
  **one sentence**, excised in the same commit as the one-line fix OPS-M has already
  specified and verified.
* **Reachability cuts both ways and I will not overstate it.** `check -- <argv>` is the
  guard's documented and only command-vetting surface, and `check -- sh -c '<line>'` is
  the natural way to vet a compound line — so the bypass is reachable through the real
  entry point, and `run` mode (`:745-748`) then `subprocess.call`s the payload. But
  nothing calls the guard on a command automatically. It is a voluntary self-audit, and an
  agent that would construct `echo "#" ;` to launder a sealed read is an agent that would
  not run `check` at all. The branch concedes this itself (`:65-67`, "a pre-flight, not a
  sandbox"). Forward risk worth naming: `assert_local_pull_allowed` (`:486`) *does* route
  through `classify_command`, so the day someone wires it into a runner, the hole goes
  live automatically.

### Verdict and what OPS-M should do

Every fact in the 15:05Z ruling and the 17:48Z confirmation holds. **The label survives
trivially and for the wrong reason; the posture does not.** The 17:48Z note lists three
replies and says *"三种回法都行得通，我不替你选."* Refusing to rank them is the refutable
part: option (2) plus the verified one-liner dominates, and the note itself argues the
holding cost is real ("挂着的成本不是这一条分支"). A merge referee that has measured a
dominance and declines to state it has stopped one step short of its job.

Recommend OPS-M send a short superseding note that (i) states the recommendation instead
of the menu — land `arc-recon/` + `.gitignore`, hold `CLAUDE.md` — (ii) attaches the
one-line `segments()` fix, two regressions in trigger-to-the-right shape, and the
correction of the `ACCESS_CHECK.md` §8b.1 sentence as the conditions, and (iii) records
the two new findings above: the existing regression tests for this class are
trigger-to-the-left and cannot fail, and the command layer defaults to **allow**, so the
one-liner narrows the class rather than closing it.

**Evidence that would settle the remaining disagreement**: run the split merge
(`arc-recon/` + `.gitignore` only) into `1c181b90` and run `arc-recon/verify.sh`. If it is
green and `ci_merge` does not flag it, hold-everything is dominated as a matter of fact,
not of judgement.
