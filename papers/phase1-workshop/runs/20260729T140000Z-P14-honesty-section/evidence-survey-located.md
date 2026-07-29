# The adjudication survey: located, and digested against the source

Written for `P14-honesty-section`. Every claim below carries a path and a line.
Where the survey says something the code does not support, it is marked
**[SURVEY WRONG]**. Nothing here is reconstructed; where material does not exist,
it says so.

Repo HEAD when audited: `b05e1c9`. Survey base commit: `6ee0466`.

---

# Step 1 — Where the material lives

## 1.1 The four survey reports exist. They are untracked files in a sibling worktree.

```
C:\Users\user\Desktop\theoria\.worktrees\e11-engine-crosscheck-deep\
  engine-rig\runs\20260729T000000Z-E11-engine-crosscheck-deep\
    SURVEY-solver-status.md            420 lines   ~60 points,   3 unsafe
    SURVEY-empty-as-negative.md         92 lines   ~40 points,   8 unsafe
    SURVEY-environment-as-semantics.md 283 lines  ~240 points,  37 unsafe
    SURVEY-success-as-truth.md         118 lines  ~105 points,   8 unsafe
```

The arithmetic the work item quotes closes exactly:
`60 + 40 + 240 = 340` points, `3 + 8 + 37 = 48` unsafe (three passes);
the fourth pass is the separate `105 / 8`.
Sums stated at `SURVEY-solver-status.md:16-20`, `SURVEY-empty-as-negative.md:9-11`,
`SURVEY-environment-as-semantics.md:11-12`, `SURVEY-success-as-truth.md:8`.

**Git status of these four files: `??` — untracked.** Verified with
`git status --short` inside that worktree. They are on branch
`agent/e11-engine-crosscheck-deep` @ `6ee04667ca7e95619ca841e32947f8c87ea87dae`,
but they were never `git add`ed.

* **Not on any ref.** `git ls-tree -r --name-only <ref>` over every ref in
  `refs/heads` and `refs/remotes` returns zero files matching `SURVEY`.
* **Not pushed.** `origin` holds 17 remote-tracking refs; none is
  `origin/agent/e11-engine-crosscheck-deep`. `git rev-parse` on that name fails.
* **Not in the run's own manifest.** `engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/MANIFEST.json`
  lists no `SURVEY` file.
* The *committed* half of that run directory **is** merged to master
  (`git branch --contains agent/e11-engine-crosscheck-deep` includes `master`;
  `git ls-tree master` shows `CROSSCHECK.md`, `ADVERSARIAL-cegis.md`,
  `ADVERSARIAL-zero_space.md`, `MANIFEST.json`, `partials/`). Only the four
  surveys were left behind.

**So the work item's citation is right about the directory and wrong about the
tree.** The files are exactly where it says, on disk, in a worktree — they are
simply not in git.

**Why the earlier search reported "none anywhere in the repository."**
`BRIEF.md:66` records `find . -name "SURVEY*"` returning nothing. That search ran
from inside `.worktrees/p14-honesty-res2/`, and `.worktrees/` **does not exist**
inside a worktree — it is a gitignored directory of the primary checkout only.
`find` from `C:\Users\user\Desktop\theoria` finds all four immediately. This is a
search-root artefact, not a missing file.

**Single point of failure.** One machine-local, untracked, unpushed copy. If this
worktree is reaped (`monitor/reap_worktrees.py` exists), the primary evidence for
five board items and one paper section is gone. `monitor/audit/DRIFT-20260728T2107Z-decisions-are-now-being-made-on-evidence-master-cannot-see.md:11`
already flagged this class of problem for a *different* artefact set and did not
notice this one.

## 1.2 The material is split. Full list.

**Primary (untracked, worktree only):** the four `SURVEY-*.md` above.

**Digests on master** — these are what every downstream item actually cites, and
they are where several numbers first appear:

| Path | What it holds |
|---|---|
| `monitor/inbox/archive/20260729T063000Z-RES-3-the-pattern-you-named-appears-three-more-times.md` | Passes 1–3. The `340 / 48` total at `:168`; the `~45` immune control at `:96` and `:169`; the retraction at `:160-164`; the 29.2 % re-derivation at `:154-158`; the gold standard at `:135-137`. Cites the surveys at `:97-99` and `:171` — naming the branch, correctly, as the place they live. |
| `monitor/inbox/archive/20260729T104500Z-RES-3-the-dual-exists-and-it-has-a-different-shape.md` | Pass 4. `105 / 8` at `:7`; the `fd_adapter` positive result at `:16-19`; the two duals at `:33-57`; the no-held-out finding at `:61-73`; the `~97` at `:100`. |
| `monitor/board/claimed/P14-honesty-section.RES-2.md` | The citing work item. The four family names at `:19-20` — **they appear here and nowhere in any survey.** |
| `monitor/board/done/E14-crash-is-not-a-finding.RES-3.md`, `E15-solver-status-bit.RES-3.md`, `S23-unreadable-is-not-clean.W-1642.md`, `V19-unverified-is-not-true.RES-3.md`, `E16-verdict-must-gate.W-1650.md`, `C10-unsolvable-proof-canon.RES-3.md`, `C11-tool-failure-as-truth.RES-3.md`, `E17-held-out-validation.RES-3.md` | The survey's findings, institutionalised as work items. |
| `engine-rig/runs/20260729T080000Z-C11-tool-failure-as-truth/CORRECTIONS.md` | Site-by-site re-verification of the eleven engine-rig sites against the tree, with the survey's line numbers re-derived rather than copied (`:7-10`). The best secondary source for what was actually fixed. |
| `engine-rig/runs/20260729T034043Z-E17-held-out-validation/` | The held-out work. See §G. |

**Nothing is missing.** Every number the work item quotes traces to one of the
above. Two of them do not trace to what the item says they trace to — see §B.

---

# Step 2 — The digest

## A. The four failure families

**Finding first: no survey names four families.** The taxonomy
「退出码当证明、缺省值当成立、崩溃当发现、触顶当穷举」 is written at
`monitor/board/claimed/P14-honesty-section.RES-2.md:19-20`, by the monitor, over
the top of four reports that use four *different* and mutually incompatible
criteria (see §B). The nearest thing to an institutional definition is the four
board items opened on the survey's back —
`monitor/audit/DRIFT-20260728T2107Z-...:20` states that four of the five items
opened correspond to four "silent optimism" families. Those four are E14, E15,
S23, V19. **They do not map one-to-one onto the four names**: E15 covers both
"exit code as proof" and "cap as exhaustion"; S23 covers "empty as clean", which
the item's taxonomy does not name. The paper should either use the item's four
names and say they are the monitor's synthesis, or use the four board items.

Below: the item's four names, the nearest thing the surveys themselves define,
and one example each — **all four registered or fixed, none freshly dug.**

### Family 1 — exit code taken as proof

**Definition (the survey's own, `SURVEY-solver-status.md:7-11`):**

> 判据（监控给定）：把「工具失败/不确定」解释成「世界具有某性质」= **不安全**；
> 解释成「未知 / 未证明 / 需要更多工作 / 控制流」= 安全。只有前者算缺陷。
> 基准是 `Theoria.md:244` 约束 6 ——「全称断言必须带证明；裸 UNSAT 禁止。」

**Example — `engine-rig/tools/p13_fd_dividend.py`.**
Surveyed at `SURVEY-solver-status.md:38-42` (U-1) as line 129:

```python
unsolvable=done.returncode == 12,
```

while the same repository's own constant table at
`engine-rig/engines/fd_adapter/backends.py:74` reads
`FD_SEARCH_UNSOLVED_INCOMPLETE = 12` — 12 is "search stopped, found nothing",
not a proof.

**Current status: FIXED.** `engine-rig/tools/p13_fd_dividend.py:171`:

```python
unsolvable=backends.proves_unsolvable(rung, done.returncode, log),
```

with `exhausted_reported=backends.FD_EXHAUSTED in log,` at `:172` and a
conservative `rung` default at `:135-137`. The canonical predicate is at
`engine-rig/engines/fd_adapter/backends.py:239-270`, body at `:266-270`.
Registered as `monitor/board/done/C11-tool-failure-as-truth.RES-3.md`;
branch `agent/c11-tool-failure-as-truth` **is merged to master**.

**Caveat that must be written (§C.2):** the artefact was never regenerated.

### Family 2 — default value taken as truth

**Definition (nearest the surveys give, `SURVEY-solver-status.md:93`):** a tool
state meaning "this invariant is **not checkable**" (`verified: False`, no
`holds` key at all) rendered as `invariants_all_hold: true`.

**Example — `worldgen/core/truth.py:279`.** Surveyed at
`SURVEY-solver-status.md:89-141` (U-2):

```python
"invariants_all_hold": all(i.get("holds", True) for i in invariants),
```

Prose-only invariants are appended without a `holds` key at
`worldgen/core/truth.py:199-203`; only the verified branch sets it, at `:218`.
Escalated to a manifest-level claim at `worldgen/build.py:104` and
`worldgen/build.py:166-167`, where `invariant_failures: []` is derived from the
defaulted field. The survey counted independently
(`SURVEY-solver-status.md:114-124`): 13 of 35 built worlds carry at least one
unverified invariant and every one of them publishes `invariants_all_hold: true`.

**Current status: REGISTERED, NOT FIXED.** Line 279 is byte-for-byte as
surveyed. `monitor/board/done/V19-unverified-is-not-true.RES-3.md` is filed as
**done**, but `git branch --contains agent/v19-unverified-is-not-true` does
**not** include `master`. The board says done; master says unchanged. This is
itself an instance of the family — a done-marker read as a landed fix.

The shape worth quoting (`SURVEY-solver-status.md:137-138`): the Markdown
renderer at `worldgen/core/truth.py:333-339` prints
`_(prose only, unverified)_` honestly; only the machine-readable boolean lies,
and only the machine-readable one is consumed.

### Family 3 — crash taken as discovery

**Definition (the survey's own, `SURVEY-environment-as-semantics.md:6-7`):**

> 判据只有一条：**环境事实（崩溃 / 非零退出 / 超时 / 解码失败 / 资源上限 /
> 并发）有没有被转成一条关于被研究对象的断言。** 正当的错误处理不报。

**Example — `a0-spike/pipeline/stages.py`.** Surveyed at
`SURVEY-environment-as-semantics.md:28` as line 260: a bare `except Exception:`
(without even `as exc`) wrapping CEGIS synthesis, so an engine crash was recorded
as "this class of transition admits no single conjunctive guard" and produced a
**published DNF rule set**. `SURVEY-environment-as-semantics.md:28` (rightmost
column): 「**没有。** 报告里没有一个字段说这条回退触发过」.

**Current status: FIXED.** The catch is split:
`a0-spike/pipeline/stages.py:375` `except NoSeparatingGuard as exc:` (the
designed verdict, `reason = "no_separating_guard"` at `:379`) versus `:388`
`except Exception as exc:` which now sets `reason = "synthesis_crashed"` and
calls `account.record_crash(...)`. The crash reaches the payload
(`:233-234`, `unsound_after_crash` at `:219-220`) and takes the green light down
with it: `all_guards_searched` returns `not self.crashes` at `:276-277`.
Registered as `monitor/board/done/E14-crash-is-not-a-finding.RES-3.md`; branch
`agent/e14-crash-is-not-a-finding` **is merged to master**.

The companion site `theoria-arm/inner/plan.py:172` (surveyed at
`SURVEY-environment-as-semantics.md:29` as the worst-directioned finding of the
night — *every crash makes the health certificate look cleaner*) is also
**FIXED**: the site is now `theoria-arm/inner/plan.py:300`, the exception is
recorded at `:303`, and the sentence "the whole reachable set was enumerated" at
`:337` is now unreachable when any successor was pruned — `:320-341` routes a
non-zero crash count to `status: "unsat_unsound"`, `exhaustive: False`.

### Family 4 — hitting a cap taken as exhaustion

**Definition (the survey's own, `SURVEY-environment-as-semantics.md:111`):**

> 问题只有一个：**靠穷举下结论的地方，有没有把「我没触顶」这件事报出来。**

**Example — `engine-rig/engines/lp_potential/potential.py`.** Surveyed at
`SURVEY-environment-as-semantics.md:77` and `SURVEY-solver-status.md:142-152`
as lines 169-170:

```python
if not result.success:
    return None
```

`result.success` being false covers HiGHS status 2 (genuinely infeasible — no
linear pagoda exists), status 1 (**iteration cap**), 3 (unbounded) and 4
(numerical trouble). All four collapse to the same `None`, and the function's own
docstring pins that `None`'s meaning to a geometric fact. The engine cannot tell
"does not exist" from "I ran out".

**Current status: FIXED.** `engine-rig/engines/lp_potential/potential.py:34`
`HIGHS_INFEASIBLE = 2`; `:208-218`:

```python
if not result.success:
    # HiGHS status codes: 0 optimal, 1 iteration limit, 2 infeasible,
    # 3 unbounded, 4 numerical difficulties.  Only 2 is an answer.
    if result.status != HIGHS_INFEASIBLE:
        raise LpUnavailable(
            "linprog stopped without deciding feasibility: status %r (%s). "
            "This is a fact about the solver, not about the configuration, "
            "so no unreachability claim follows from it."
            % (result.status, getattr(result, "message", ""))
        )
    return None
```

`LpUnavailable` at `:41-52`. Registered as
`monitor/board/done/E15-solver-status-bit.RES-3.md` — **but note**
`agent/e15-solver-status-bit` is **not** merged to master; the fix landed via
`c6a5b82` / `3de10b7`, which are. A second cap site,
`engine-rig/engines/zero_space/zerospace.py`, is **REGISTERED-ONLY at the
artefact boundary** — see §F.3.

---

## B. The immune control

### B.1 The counts, as claimed, and as they actually enumerate

| Claim | Where claimed | What the surveys actually enumerate |
|---|---|---|
| ~45 legitimate exit-code readings | `monitor/board/claimed/P14-honesty-section.RES-2.md:9,21`; `monitor/inbox/archive/20260729T063000Z-...:96,169` | **The number 45 appears in no survey.** `SURVEY-solver-status.md:274-376` enumerates **51 table rows** across five sections (planner/search 19, LP 5, SAT/IC3 13, Lean 9, exam 5) **plus 13 backticked CI paths** in the prose at `:367-374` = **64 named legitimate sites**. |
| ~97 more from the fourth pass | `monitor/board/claimed/P14-honesty-section.RES-2.md:48`; `monitor/inbox/archive/20260729T104500Z-...:100` | **97 is `105 − 8`.** It is arithmetic residue, not an enumeration. `SURVEY-success-as-truth.md:43-79` names **8 exemplars**; `:81-95` names **7 more** as "verified but not independent" — a third category the item's ratio does not have. Total named: **15**. |
| — | — | `SURVEY-empty-as-negative.md:30-58` names a further **6** exemplars. |

**Total legitimate sites actually named across all four reports: 85** (64 + 15 + 6).
**Total unsafe: 56** (3 + 8 + 37 + 8).

### B.2 The internal arithmetic of the first pass does not close

`SURVEY-solver-status.md:16` says 「扫了 **约 60 处**」. The same report then
enumerates 3 unsafe (`:24-26`) + 2 latent (`:207-237`) + 1 declared ablation
(`:243`) + 6 doc-propagation sites (`:258-265`) + **64 legitimate** = **76 named
sites** against a stated scan surface of ~60. The legitimate list alone exceeds
the scan surface. Either the "~60" or the "~45" is wrong; nothing in the file
reconciles them. **This is precisely the defect
`SURVEY-empty-as-negative.md:87-92` states as its own cross-cutting
recommendation** — that any audit issuing an affirmative claim must publish both
the number of objects it *should* have covered and the number it *did*:

> **任何输出肯定断言的审计，必须同时输出「本该覆盖的对象数」和「实际覆盖的对象数」，
> 并在两者不等时拒绝给出肯定断言。**

The survey does not meet its own criterion. **Write the enumerable numbers
(85 / 56), not the item's 45 and 97.**

### B.3 The criterion for "unsafe" — written down in two of four reports, and they differ

| Report | Criterion written down? |
|---|---|
| `SURVEY-solver-status.md` | **Yes**, `:7-11`. Given by the monitor; baseline `Theoria.md:244` constraint 6. Failure/uncertainty → a property of the world = unsafe; → unknown / unproven / control flow = safe. |
| `SURVEY-environment-as-semantics.md` | **Yes**, `:6-7`, and it is a *different* criterion: has an **environment fact** (crash / non-zero exit / timeout / decode failure / resource cap / concurrency) been turned into an assertion about the object of study. |
| `SURVEY-empty-as-negative.md` | **No.** The file opens at `:1-12` with a summary and goes straight to the table. No criterion sentence exists. |
| `SURVEY-success-as-truth.md` | **No.** `:32-33` gives table *columns* (「成功信号 / 被断言成 / 有没有验证 / 验证独立吗」), which is a schema, not a threshold. |

**This is a finding and it belongs in the paper.** Two of the four passes — 48 of
the 56 unsafe judgements, including all 37 of the largest pass — ran against a
criterion that is either unstated or different from the one the work item
attributes to the whole. The 340 and the 48 are sums across incommensurable
rulers.

### B.4 The gold standard — verified verbatim

`engine-rig/bench/ladder.py:74-82`, exactly as the survey describes at
`SURVEY-environment-as-semantics.md:117` and `SURVEY-solver-status.md:289`:

```python
        except RuntimeError as exc:
            return {
                "config": "stub-bfs", "tier": backends.STUB,
                "solved": False, "proved_unsolvable": False,
                "plan_length": None,
                "nodes": {"expanded": None, "generated": None},
                "error": "over budget: %s" % exc,
                "timing": {"wall_seconds": None},
            }
```

`proved_unsolvable: False` (`:78`) **and** `error: "over budget"` (`:80`) in the
same dict — the cap recorded positively rather than absorbed. The cap itself is
published: `engine-rig/bench/ladder.py:226` `"stub_max_expansions": STUB_MAX_EXPANSIONS,`
with `STUB_MAX_EXPANSIONS = 200000` at `:51`, whose comment says the value was
chosen *deliberately small enough that the batch runs off the end of it*
(`SURVEY-environment-as-semantics.md:223-225`: 「预算耗尽被当作数据，而不是要藏起来的难堪」).
`:98` is the honest converse: `"proved_unsolvable": not result.solved` only on
the path where the budget was not hit.

**One qualification the survey does not make.** `engine-rig/bench/ladder.py:248`
excludes over-budget rows from the failure list:

```python
            if row.get("error") and "over budget" not in str(row["error"]):
```

That is consistent with the design — a non-answer is not a fault — but it means
the gold standard is a claim about the **artefact**, not about the **gate**. Say
so; the paper's whole argument is about that distinction.

---

## C. The two published numbers resting on a re-derivation

### C.1 `lp_potential`'s 29.2 %

**What was published, and where.** Not in the paper.
`grep -n "29\.2" papers/phase1-workshop/PAPER.md` returns nothing. It is
published in the engine table:

* `engine-rig/ENGINE_TABLE.md:109` — 「`lp_potential`'s incompleteness is **639 / 2189 = 29.2 %**, not the 46.6 %」
* `engine-rig/ENGINE_TABLE.md:249` — the provenance row, pointing at
  `runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/lp_potential-via-exhaustive.md`
* `engine-rig/ENGINE_TABLE.md:23` — the row-4 cell, which carries the number in
  full narrative form

**What the re-derivation showed.** The engine could not produce this number,
because `potential.py` discarded the bit. A reviewer rebuilt the LP themselves —
`engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/lp_potential-via-exhaustive.md:264-276`:

| | |
|---|---|
| HiGHS status 2 (infeasible) at `bound=10` | 639 / 639 |
| still infeasible at `bound = 100`, `10⁴`, `10⁶` | **638** |

So 638 of the 639 silences are the mathematics; **1** is the hard-coded
`bound=10` weight box (`:295`). The headline sentence, at
`monitor/inbox/archive/20260729T063000Z-...:156-158`:

> **所以 29.2% 那个不完备率仍然成立**——它成立是因为**复核员重新推导了引擎丢弃的那一位**，
> 不是因为引擎保留了它。**任何不重新推导的人，拿不到这个数。**

**Is the conclusion currently true? Yes.** 638/639 is the same rate to the digit
that 639/639 gives at this precision; the number survives the re-derivation. The
method was unsound — the engine's `None` could not distinguish an iteration cap
from infeasibility — and **the method is now fixed**
(`engine-rig/engines/lp_potential/potential.py:208-218`, §A family 4). A rerun
would now produce the number from engine output rather than from a reviewer's
reconstruction. **That rerun has not happened**: `ENGINE_TABLE.md:249` still
points at the reviewer's partial, and
`monitor/board/done/E15-solver-status-bit.RES-3.md` item 2 (「重发那 639 例」)
asks for exactly this.

`ENGINE_TABLE.md:23` is itself scrupulous about a second, separate limit that the
work item does not mention and the paper should not omit: for those 638 worlds
"no linear pagoda exists" still rests on **HiGHS returning float infeasibility —
no exact Farkas dual was produced**, so it remains a solver's claim and not a
proof.

### C.2 The three `fd_unsolvable: true` rows

**What was published.** `engine-rig/runs/p13-fd-real/dividend.json`, key
`cross_check`, exactly three rows of seven:

| index | instance | `fd_unsolvable` | `fd_exit_code` | `agree` | `stub_unsolvable` |
|---|---|---|---|---|---|
| `[1]` | `a0-spike/mismatch` | `true` | `12` | `true` | `true` |
| `[3]` | `cold-start-a0/no-button` | `true` | `12` | `true` | `true` |
| `[5]` | `cold-start-a2/holed` | `true` | `12` | `true` | `true` |

The other four rows are `false` / exit `0`. Counted directly from the file.

**What the re-derivation showed.** `SURVEY-solver-status.md:75-81`, stating the
mitigation before the accusation:

> `run_fd` 全仓只用 `BLIND = "astar(blind())"` 调用（:64, :302-303, :365），
> 这是**完备、可采纳、无成本界**的配置，所以在这个配置上「开列表清空 → 退出 12」
> 确实是证明 …… 而且这三条结论**当前是真的**：桩在三条上全部独立同意 …
> **所以是方法不健全，不是结论错。**

The independent agreement is real: `stub_unsolvable: true` on all three, and the
stub raises on budget exhaustion rather than returning `None`
(`engine-rig/engines/fd_adapter/search.py:145-146`), so its `None` implies
exhaustion.

**Is the conclusion currently true? Yes** — on all three rows, by a complete
unbounded blind search plus an independently-agreeing complete stub. **The method
was unsound**: the field was written by a bare `returncode == 12` with no check
of rung, log, or the plan file it had already read (`SURVEY-solver-status.md:53-59`).

**Two things the survey did not say, both material, both verified:**

1. **The artefact predates the fix and was never regenerated.**
   `git log -- engine-rig/runs/p13-fd-real/dividend.json` shows one commit,
   `cf400ce`. The tool was fixed later, in `2a1c30d` / `c6a5b82`. The three
   `true`s sitting in the committed artefact today are the *output of the
   defective line*, not of `proves_unsolvable`.
2. **The artefact cannot be re-adjudicated from itself.** Its `cross_check` rows
   carry only `agree, fd_exit_code, fd_expansions, fd_plan_length, fd_unsolvable,
   instance, status, stub_expansions, stub_plan_length, stub_unsolvable`. The new
   evidence fields `fd_answered`, `fd_rung`, `fd_exhausted_reported` are absent.
   The tool's own docstring at `engine-rig/tools/p13_fd_dividend.py:107-110`
   concedes this: the published p13 artefact predates the field, "which is why
   its three exit-12 rows could only be reconciled indirectly."

**Fair statement for the paper:** in both cases the conclusion is currently true
and the method should not have reached it. Neither is a retraction of a result.
One (29.2 %) has a fixed method and a stale citation; the other has a fixed
method and a stale artefact.

---

## D. The retraction

**What was claimed.** A cross-check paraphrase reported that
`engine-rig/tools/p13_fd_dividend.py:419-424` would publish a false negative —
prose reading "zero, on both engines (None -> None)" when both FD runs had
crashed.

**What withdrew it, and why.** The surveyor, in the survey itself —
`SURVEY-environment-as-semantics.md:85-90`:

> **一条我要收回的转述。** 交叉复核报来 `p13_fd_dividend.py:419-424` 会发表
> 「zero, on both engines (None -> None)」这条虚假的负结果。我复核后认为**不成立**：
> 那条 prose 分支用 `%d` 格式化，`"%d" % None` 抛 `TypeError`，会响亮地崩掉而不是发表。
> 真正落地的是同一函数 `:400-404` 的**表格**行——那里用 `%s`，
> 于是 `None -> None … yes` 确实会被印出来。上表第 6 条按后者记，不按前者。

The claim was replaced, not merely dropped: the table branch at `:400-404` is
recorded in its place (row 6 of the 丙组 table at
`SURVEY-environment-as-semantics.md:81`).

**Where it is recorded — three places, and the third partially re-opens it:**

1. `SURVEY-environment-as-semantics.md:85-90` — the retraction itself.
2. `monitor/inbox/archive/20260729T063000Z-RES-3-...:160-164` — carried forward
   to the monitor: 「**记在这里是因为收回本身也要留痕。**」
3. `engine-rig/runs/20260729T080000Z-C11-tool-failure-as-truth/CORRECTIONS.md:45-52`
   — C11 confirms the retraction was correct **and finds its conclusion
   incomplete**: `dividend.json` is written by `json.dump` in `main()` *before*
   `render()` is called, so in the double-crash scenario `same_answer: true` did
   reach the JSON artefact; the `%d` crash protected only the human-readable half.
   C11's fix therefore does not rely on the crash — it gives `same_answer` a third
   value.

**This is the strongest single item in the section.** A survey retracted a claim
against its own interest, published the retraction in place, and a downstream
worker then partially re-opened the retracted finding on a different mechanism —
also in place, also signed.

---

## E. The positive result — verified in the source

**Claim (`monitor/inbox/archive/20260729T104500Z-...:16-19`, restated at
`monitor/board/claimed/P14-honesty-section.RES-2.md:38-41`):** "a solver returned
a plan, therefore the instance is solvable" does not happen in this repository;
`fd_adapter` calls `validate_plan()` unconditionally on all three rungs, and the
validator deliberately does not import the searcher.

### E.1 Is `validate_plan()` unconditional on all three rungs? **Yes.**

`engine-rig/engines/fd_adapter/__init__.py`, function `solve_parsed`, lines
79–141. The tier fork is at `:109-128`:

```python
    tier, executable = backends.choose_tier(
        prefer=prefer,
        on_disk=bool(domain_path and problem_path),
        prune=prune,
    )
    if tier == backends.STUB:
        result = search.search(domain, problem, prune=prune)
        if result.plan is None:
            return None, result
        actions = [action.text() for action in result.plan]
        config = backends.fd_search_config(tier)
    else:
        config = backends.fd_search_config(tier, heuristic, executable)
        actions = backends.run_fast_downward(
            executable, domain_path, problem_path, tier=tier, heuristic=heuristic,
        )
        # FD keeps its node account to itself; the plan is in `actions`.
        result = search.SearchResult(None, 0, 0, 0, 0)
        if actions is None:
            return None, result
```

Both branches fall through to the `Plan(...)` construction at `:130-139` and then
to `:140`:

```python
    validate_plan(domain, problem, plan.actions)   # never emit an unchecked plan
    return plan, result
```

**No `if`, no `try`/`except`, no conditional expression, no tier test.** The only
tier-sensitive line in the whole construction is `:135`
(`optimal=tier != backends.FD_SATISFICING`). The two early returns at `:117-118`
and `:127-128` are the *no-plan* paths — there is no plan to validate on either.
`solve()` delegates at `:159`; `run()` delegates at `:199`. Everything this engine
publishes passes `:140`.

### E.2 Does the validator import the searcher? **No.**

`engine-rig/engines/fd_adapter/validate.py`, the complete set of import
statements in the file, `:25-33`:

```python
from typing import Dict, List, Sequence, Set, Tuple

from engines.fd_adapter.pddl import (
    Atom,
    Domain,
    Problem,
    _substitute,
    ground_actions,
)
```

There is no `import search` and no reference to `search` outside the docstring.

### E.3 The qualification the work item drops, and the survey keeps

`validate.py`'s own docstring, `:9-16`, states the limit of the guarantee:

> The shared premise is `pddl.ground_actions`, which this module and `search` both
> import.  That is not merely the parser.  `ground_actions` filters on static
> preconditions while it instantiates, and so decides which action instances could
> ever fire, with which effects -- it is the successor-generation layer.  A
> forgotten delete effect *there* is invisible here … So a plan passing this
> is a plan whose steps are legal under the shared grounding, not one legal under
> the PDDL as written.

`SURVEY-success-as-truth.md:91` records exactly this, filing `validate.py` under
「验了但不独立」 — independent of `search.py`, **not** independent of `pddl.py`'s
parser and `ground_actions()`, and explicitly the same grounding-layer blind spot
that `fuzzlab`'s oracle has.

`monitor/board/claimed/P14-honesty-section.RES-2.md:38-41` states the result flat:
「这是结构保证而非承诺」. **The survey is more careful than the item that quotes
it.** Write the guarantee with its scope: *no planner in this rig grades its own
answer; every rig-produced plan is replayed against the shared grounding, and the
grounding is the residual shared premise, named in the source.*

One more thing the survey flags and the item omits
(`SURVEY-success-as-truth.md:75-79`): `probe_frontier`'s
`REACHABLE` verdict inherits this guarantee from `:140` without restating it — if
that line ever moves, `reach()` degrades silently and its own source will not
change by a character.

---

## F. The dual cases — both computed, both published, **both now gated**

### F.1 `"admissible": True` — was a literal, is now derived

**Surveyed** at `SURVEY-success-as-truth.md:34` as
`engine-rig/engines/lp_potential/potential.py:255`, `"admissible": True,` — a
literal in the payload dict, with the real check sitting in the sibling
`admissibility_check` in the same payload, unread by the headline. The surveyor
tested it in memory: a certificate with `conditions.inv_closed=False`,
`holds=False` still produced `as_json()["admissible"] == True`.

**Current status: FIXED.** `engine-rig/engines/lp_potential/potential.py:357`:

```python
            "admissible": basis["admissible"],
```

`basis` computed at `:349` via `entitlement()` (`:294-336`), whose result at
`:335` is `"admissible": bool(proved) and (sampled is not False),`. The
itemised licence is now published alongside at `:358`
(`"admissible_basis": basis`). The docstring at `:342-347` names the old defect:
"It used to be the literal `True`, sitting beside an `admissibility_check` the
headline never read."

**What is published today.** `engine-rig/artifacts/candidates.jsonl`, line 22,
`kind: "heuristic"`, `status: "candidate"`:
`"admissible": true` alongside `"admissibility_check"` with three rows, all
`admissible: true`. The two now agree because the headline reads the sibling.

**[SURVEY WRONG] — `SURVEY-success-as-truth.md:109-112`** claims:

> `engine-rig/artifacts/candidates.jsonl` 当前只有一份，且不含 `admissible` /
> `plan_length_unchanged` 字段（实测 grep 为 0 命中），说明**第 1、2 条的产出路径
> 当前没被跑过** …… 所以这两条现在是**装好的雷、不是已爆的雷**。

At the survey's own base commit, `git show 6ee0466:engine-rig/artifacts/candidates.jsonl`
contains **one hit each** for `admissible` and `plan_length_unchanged`. The grep
result reported is wrong, and it is wrong in the direction that *understates*
severity: the mine had already fired, into a committed, sha256-pinned artefact.
Do not repeat the survey's mitigation.

### F.2 `deadlock_carver` — theorem and falsification side by side, now gated

**Surveyed** at `SURVEY-success-as-truth.md:35` and
`monitor/inbox/archive/20260729T104500Z-...:44-59` as
`engine-rig/engines/deadlock_carver/__init__.py:168-180`: `run()` was
`carve` → `pruning_report` → `emit` with **no `if` between the second and third**.
The report contains an empirical falsifier, `PruningReport.same_answer` ("did this
theorem change the instance's answer"), which was computed, serialised as
`plan_length_unchanged`, and then published **beside the theorem it refutes**,
with neither overriding the other.

**Current status: FIXED.** `run()` is now
`engine-rig/engines/deadlock_carver/__init__.py:279-298` and still reads
`carve → report → emit` — **the gate moved into `candidates()`**, at `:226`:

```python
    if refuted is not None and on_refutation == WITHHOLD:
        withheld = len(theorems)          # counted before the list is emptied
        theorems = []
```

with `refutation()` at `:166-189`, the policy constants `WITHHOLD` / `MARK` at
`:161-163`, `WITHHOLD` as the default parameter at `:281`, the `MARK` path
stamping `payload["refuted"] = True` at `:236-238`, and the `plan` row carrying
`refuted`, `refutation`, `invariants_withheld`, `on_refutation` at `:255-262`.
The docstring at `:198-203` names the old defect verbatim. Separately, `:100-105`
makes `same_answer` **raise** `UnfinishedComparison` rather than compare two
unfinished searches — closing the second-order version of the same defect.

**What is published today.** `engine-rig/artifacts/candidates.jsonl` line 41,
`kind: "plan"`, carries `"plan_length_unchanged": true` — i.e. not refuted, so
nothing is withheld. The gate exists and has not had to fire on this corpus.
Registered as `monitor/board/done/E16-verdict-must-gate.W-1650.md`; branch
`agent/e16-verdict-must-gate` **is merged to master**.

### F.3 The third dual, which is **not** fixed at the artefact boundary

`engine-rig/engines/zero_space/zerospace.py` — the field exists, the payload does
not carry it.

* `:145` `SUBSET_ENUMERATION_LIMIT = 8`; `:175` `if len(indices) > SUBSET_ENUMERATION_LIMIT:`
  degrades the enumeration to `[[i] for i in indices] + [indices]` and appends the
  cell to `truncated` at `:177`.
* The bit was added: `Law.scope_exhaustive` at `:45`, set at `:221`
  (`scope_exhaustive=not truncated_cells,`), `ZeroSpaceResult.truncated_cells` at
  `:104` with the property at `:107-108`. Tested at
  `engine-rig/tests/test_tool_failure_is_not_truth.py:390-397`.
* **It is deliberately not in the payload.** `Law.as_json` at `:75-92` ends at
  `:90` with `"scope": self.scope,` and no `scope_exhaustive`. The comment at
  `:76-82` gives the reason: `artifacts/candidates.jsonl` is sha256-pinned in
  `release/MANIFEST.jsonl` and candidate ids are content-addressed, so widening
  the payload re-hashes every `zero_space` row and invalidates a manifest this
  track does not own. Filed for the release track (C11).

So a reader of `candidates.jsonl` still cannot tell a proved `scope: "global"`
from an unsearched one — the survey's original complaint
(`SURVEY-environment-as-semantics.md:78`) stands at the artefact boundary. C11
records the gap without pretending otherwise
(`engine-rig/runs/20260729T080000Z-C11-tool-failure-as-truth/CORRECTIONS.md:205-222`).
**This is the cleanest example in the repository of a fix blocked by a release
pin rather than by disagreement, and it is worth a sentence.**

---

## G. The held-out-validation finding — and whether it is still true

### G.1 What the survey found

`SURVEY-success-as-truth.md:23-25`:

> **整个 `engine-rig` 没有任何一处留出验证。**
> `grep -rni "held.out|heldout|holdout|hold-out" engine-rig/` → **0 命中**（实测）。
> 形状 4（挖掘器只在拟合它的证据上自洽）在这个仓库里不是个别失误，是系统性缺席。

and `SURVEY-success-as-truth.md:89`: `zero_space.verify` re-checks each law on the
same trajectory the null space was solved from, so the `AssertionError` in `run()`
is "almost impossible to trigger" — 「验证存在、独立于代码、却在拟合它的证据上空转」.

### G.2 E17 landed, and it is merged

`engine-rig/runs/20260729T034043Z-E17-held-out-validation/` exists;
`monitor/board/done/E17-held-out-validation.RES-3.md` is filed done; and
`git branch --contains agent/e17-held-out-validation` includes `master`
(merge commit `a03fe99`). **This is not a stale done-marker.**

### G.3 Which cells now have genuine held-out validation

**Two of eight.**

| # | engine | held out? | figure |
|---|---|---|---|
| 3 | `zero_space` | **yes** | Z-S2 leave-one-operation-out: global `delta_hit` **13.1 %** over 1680 laws (`engine-rig/ENGINE_TABLE.md:82`); `cell_local` 92.9 % (`:22`) |
| 4 | `lp_potential` | **yes** | L-L1 leave-one-geometry-out over 289 `pegN` instances: only **26.4 %** of 1408 certificates still satisfy `inv_closed` on the withheld geometry; **58** are outright false against BFS ground truth (`engine-rig/ENGINE_TABLE.md:87-88`) |
| 1 | `mdl_segmenter` | **no** | `engine-rig/ENGINE_TABLE.md:20` |
| 2 | `cegis_miner` | **no** | `:21` |
| 5 | `fd_adapter` | **no** | `:24` |
| 6 | `probe_frontier` | **no** | `:25` |
| 7 | `deadlock_carver` | **no** | `:26` |
| 8 | `ic3_pdr` | **no** | `:27` |

Machine-enforced: `engine-rig/tests/test_engine_table.py:96-103` asserts
`"Held out (E17)" in row["boundary"]` **iff** the engine is `zero_space` or
`lp_potential`.

The standing rule is written into the table itself,
`engine-rig/ENGINE_TABLE.md:69-76`:

> **Where no held-out validation exists, a cell may say 「在观测证据上自洽」 and may
> not say 「已验证」.** … which for `zero_space` is a tautology exactly: the laws
> *are* the null space of the observed differences, so `verify()` re-checks
> `a·d = 0` on the same `d`.

and `:93-97`: "with them, those rows may state a held-out figure with its cut
named. **Without them, no row may.**"

### G.4 Four qualifications, all of which change how the paper should be written

**(i) `zero_space.verify` is still circular. E17 did not touch it.**
`engine-rig/engines/zero_space/zerospace.py:235-242`:

```python
def verify(result: ZeroSpaceResult, states: Sequence[Sequence[str]]) -> bool:
    """Re-check every reported law directly against the trajectory."""
    encoded = [encode(state, result.features) for state in states]
    for law in result.laws:
        values = {gf2.dot(law.vector, x) for x in encoded}
        if values != {law.value}:
            return False
    return True
```

and the caller, `engine-rig/engines/zero_space/__init__.py:51-53`, passes the
**same `states` object** it fitted on:

```python
    result = analyse(states, colors)
    if not verify(result, states):
        raise AssertionError("a recovered law does not hold on the trajectory")
```

E17's `MANIFEST.json` file list contains **no path under `engines/`**. It measured
around the defect with a parallel harness rather than fixing it.

**(ii) The survey's grep result is still literally true.**
`grep -rn -i "held_out\|held-out\|heldout\|holdout" engine-rig/engines` → **zero
hits today.** The held-out code lives in a new top-level package
`engine-rig/heldout/` (7 modules) plus `engine-rig/tests/test_heldout.py`;
`engine-rig/tools/engine_table.py` reads its results. No engine knows about it.

**(iii) One of E17's two headline numbers was taken away by its own adversarial
review.** `engine-rig/runs/20260729T034043Z-E17-held-out-validation/CORRECTIONS.md:16-38`:
the Z-S1 70/30 transition split scored **100.0 %**, and that measured nothing —
proved by mutation, making the splitter return *overlapping* train and test moved
**no published digit**. Novelty is now published: Z-S1 **0 of 2160** withheld rows
new; Z-S2 **7200 of 7200** new. Five further overturns are recorded at `:40-119`,
including (C2) that the `lp_potential` emit gate was scored against the *complete*
graph while fitting on the reduced one — handed the graph a partial-evidence
caller actually holds, **all 1408 certificates are emitted including all 58 false
ones**, each carrying `holds: true` and `sound_over_graph: true` into the shared
candidate stream (`engine-rig/ENGINE_TABLE.md:88-91`). Mutation testing found
**14 of 19 mutants survived**, all inside `heldout/`, which had no tests at all
(`CORRECTIONS.md:162-179`).

**(iv) Corpus scope.** `engine-rig/ENGINE_TABLE.md:99-104`: both measurements are
on synthetic families generated by the harness (`parityworld`, `pegN`). **No
live-game data and no other world family has been held out for any engine.** So
even rows 3 and 4 have no held-out backing for their `g50t` live-ARC figures.
Item 3 of the ticket — making the split rig-wide at fixture-generation time — was
**deliberately not done**
(`engine-rig/runs/20260729T034043Z-E17-held-out-validation/RUN_STATE.md:25-51`):
as specified it would hand every future engine a meaningless 100 % hit rate,
"precisely the defect this ticket was opened to remove, institutionalised."

### G.5 The direct answer for the paper's rewrite

**The blanket rewrite must not run, but not for the reason the addendum
anticipated.**

`monitor/board/claimed/P14-honesty-section.RES-2.md:45-47` instructs that every
"verified" in the body become 「在观测证据上自洽」 until E17 lands. Two things:

1. **E17 landed for two cells.** For `zero_space` and `lp_potential`, a
   held-out figure exists and the table is entitled to state it — with its cut
   named, and with the vacuous Z-S1 companion disclosed. For the other six the
   rewrite is correct and is already enforced by test.
2. **The paper has almost nothing to rewrite.** `papers/phase1-workshop/PAPER.md`
   contains **8** occurrences of "verified", at lines 25, 240, 709, 729, 1332,
   2406, 2574 and 2639. None is a claim about an engine's verification status:
   `:25` and `:2406` are about citation cross-verification, `:240`/`:709`/`:729`
   are about a certificate's own `verified` flag (and `:709` is the line that says
   the flag is *not* trusted), `:1332` is the pile digest, `:2639` is a citation
   the paper declines to make. `:2574` says outright:

   > no claim is made to have verified any engine

   There are **zero** occurrences of 「已验证」 in `PAPER.md`. A body-wide
   find-and-replace would change nothing that needs changing and would corrupt
   several sentences that are already correct.

**What should happen instead:** the honesty section states the two held-out
figures with their cuts, states that six of eight rows have no held-out
validation of any kind, states that `zero_space.verify` remains circular by
construction, and states that the two figures are on synthetic corpora only. That
is a finding worth a section. The blanket sweep is not.

---

# Appendix — where the surveys are wrong, in one list

| # | Survey claim | Reality |
|---|---|---|
| 1 | `SURVEY-success-as-truth.md:109-112`: `candidates.jsonl` has 0 hits for `admissible` / `plan_length_unchanged`, so the duals are "mines set, not fired" | At the survey's own base `6ee0466` the file contains 1 hit each. The mine had fired, into a sha256-pinned artefact. Understates severity. |
| 2 | `SURVEY-solver-status.md:16` "扫了约 60 处" vs `:274-376` | The legitimate list alone enumerates 64 sites, exceeding the stated scan surface. Fails the criterion `SURVEY-empty-as-negative.md:87-92` sets for everyone else. |
| 3 | "~45 legitimate exit-code readings" (`monitor/board/claimed/P14-honesty-section.RES-2.md:9`) | 45 appears in no survey. 51 table rows + 13 CI paths = 64. |
| 4 | "~97 more legitimate" (`...:48`) | `105 − 8`. Arithmetic residue; 15 sites are actually named. |
| 5 | "a structural guarantee rather than a promise" (`...:38-41`), unqualified | True of the searcher; `validate.py:9-16` and `SURVEY-success-as-truth.md:91` both name `pddl.ground_actions` as the residual shared premise. |
| 6 | The four family names (`...:19-20`) attributed to the survey | Written by the monitor. No survey names four families, and the four passes used four different (two unstated) criteria. |
| 7 | Retraction of `p13:419` as complete (`SURVEY-environment-as-semantics.md:85-90`) | Correct as far as it goes; `engine-rig/runs/.../C11.../CORRECTIONS.md:45-52` shows `dividend.json` is written before `render()`, so `same_answer: true` reached the JSON regardless. |
| 8 | `engine-rig/tests/test_tool_failure_is_not_truth.py:529-531` (C11, not a survey): "`monitor/gates.py` resolves engine-rig's gate to pytest — there is no `verify.sh`" | `monitor/gates.py:52` is `CANONICAL = ("verify.sh", "verify.py")` and `engine-rig/verify.py` exists, so `gate_for` (`:155-173`) returns kind `verify`, never reaching the pytest branch. The check still runs — `engine-rig/verify.py:75` invokes pytest — so the conclusion survives by accident, not by the stated inference. |

**Nothing in this file was reconstructed.** Every number was read from the file
named beside it, and every source claim in §A, §E, §F and §G was checked against
the current tree.
