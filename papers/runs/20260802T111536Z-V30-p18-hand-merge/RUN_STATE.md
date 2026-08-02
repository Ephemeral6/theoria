# V30 · p18 引文审计分支的手工合并

**票号** `V30-p18-hand-merge` · **领地** `papers/`
**分支** `agent/v30-p18-hand-merge` · **基** `9e478dd8`（origin/master）
**开工** 2026-08-02T11:15:36Z · **工人** W-9201

边跑边写。

---

## 0 · 开工基线 —— **master 本来就是红的**

改任何东西之前，在干净的 master 检出上实测：

```
python -m pytest papers -q
  -> 2 failed, 272 passed, 1 xfailed
     FAILED papers/phase1-workshop/test_anchor_range.py::test_the_live_paper_is_green_and_its_anchors_are_in_range
     FAILED papers/test_verify_delegator.py::test_the_live_papers_tree_classifies_cleanly

python papers/phase1-workshop/verify_paper.py
  -> verify_paper: FAIL (3/7) -- C FIGDATA, E UNCITED, F BARE   (exit 1)
```

**这一条必须先写下来**：工单的验收线是「paper 门全绿才算合上」，
而**门在我动手之前就不绿**。所以「全绿」不可能是本单能达到的验收线，
除非本单顺带修掉三条与 p18 无关的门。本单不降低验收线，也不假装达到它：
如实记为 gap，并在下面给出合并本身是否正确的独立判据。

## 1 · 三件在读代码之前就必须知道的事

### （a）工单说「三个 commit」，实际是四个

```
0eb876f7 papers: the three sections nobody had ever citation-audited, audited -- 85 findings...
4f7e300d papers: the referee axis is current again...
bc910d8d papers: the referee pass and 45 gate tests existed on one disk only...
5f11953b papers: check G -- an audit report must pin what it audited...
```

`origin/master..origin/agent/p18-audits-cover-half-onmaster` = **4 个 commit**，
不是 3 个。差额本身不改变做法，但工单的计数不能照抄。

### （b）master 已经合过一个**同名孪生分支**

```
b9f833d2 merge agent/p18-audits-cover-half-the-paper: locator findings + the audit the green gate was hiding
9d0cb6b9 Merge remote-tracking branch 'origin/agent/p18-audits-cover-half-the-paper' into HEAD
```

本单要合的是 `p18-audits-cover-half-**onmaster**`，master 已经合掉的是
`p18-audits-cover-half-**the-paper**`。两者是同一件活的两个分支。
所以「p18 的内容还没上 master」这个前提**需要重新验证，不能假定**。

### （c）冲突的成因监控自己已经诊断过，而且是**人造的**

`5ad83b31`（OPS-M cycle 33）逐字：

> p18-audits-cover-half-onmaster's add/add conflict is **manufactured by the
> literal path** `runs/20260730T000000Z-P18-audits-cover-half` -- an all-zero
> timestamp, so two workers on the same item wrote the same directory. A real
> UTC stamp would have made them disjoint. The fifth path, `verify_paper.py`,
> is a **genuine content conflict** and belongs to RES-2 under CHARTER.

即：**12 次 `ci_merge` 失败里，六个 add/add 冲突是目录名撞车，不是内容分歧**。
时间戳被写成全零 `20260730T000000Z`，两个工人于是写进同一个目录。

## 2 · 实测的冲突面

`git merge origin/agent/p18-audits-cover-half-onmaster` → 7 个冲突：

| 文件 | master | p18 | 类型 |
|---|---|---|---|
| `REVIEW-2026-07-30.md` | 619 行 | 618 行 | add/add |
| `runs/…P18…/MANIFEST.json` | 183 行 | 13 行 | add/add |
| `runs/…P18…/RUN_STATE.md` | 309 行 | 121 行 | add/add |
| `runs/…P18…/citecheck-A-abstract-to-s3.md` | **810 行** | **77 行** | add/add |
| `runs/…P18…/citecheck-C-s7-to-s8.md` | **784 行** | **43 行** | add/add |
| `runs/…P18…/delta-old-vs-new.md` | 447 行 | 39 行 | add/add |
| `papers/phase1-workshop/verify_paper.py` | 2289 行 | 1093 行 | **content（真冲突）** |

**干净合并的那几个是逐字节相同的**（本单实测 md5）：
`citecheck-B-s4-to-s6.md`（536 行）、`citecheck-D1-s9-to-s10.md`（607 行）、
`citecheck-D2-s11-to-s12.md`（706 行）、`COVERAGE.md`（91 行）——
四份 md5 两侧完全一致。这直接印证了 §1(b)：**p18 的产出已经有一部分逐字在 master 上**。

**每一个冲突里 master 侧都比 p18 侧大，而且大得多**（citecheck-A 是 810 对 77）。
这形状指向「master 已经超越 p18」而不是「两边各写了一半」。但**形状不是证据**，
所以下面三组比对是派出去逐条核的，不是我看行数猜的。

## 3 · 权限边界（先确认，再动手）

`monitor/CHARTER.md` 的硬边界表：`W-*`「改代码」= **领到的领地内**，
「写论文正文」= **否**。所以：

* `verify_paper.py` 是**门脚本、是代码**，且 `papers/` 正是本单领到的领地 → **可以改**。
* 论文正文（`PAPER.md` / `sections/*.md`）→ **一个字节都不碰**。
* 冲突里其余六个是 `runs/` 下的审计记录与 review 文档，**不是正文** → 可以合。

OPS-M 那句「`verify_paper.py` belongs to RES-2, not to me」说的是 **OPS 角色不能改代码**
（表里 OPS-A/B/M/R 的「改代码」是「否」），不是「工人不能改」。
本单按板上签发的 territory 行事。

## 4 · `git cherry` —— 四个 commit 里两个已经在 master 上

工单要求「`git log --cherry` 核对」。跑出来：

```
$ git cherry -v origin/master origin/agent/p18-audits-cover-half-onmaster
- bc910d8d  papers: the referee pass and 45 gate tests existed on one disk only…
- 4f7e300d  papers: the referee axis is current again, and REVIEW.md now says…
+ 5f11953b  papers: check G -- an audit report must pin what it audited…
+ 0eb876f7  papers: the three sections nobody had ever citation-audited, audited -- 85 findings…
```

`-` = master 上已有等价物，`+` = 没有。所以：

* **`bc910d8d` 与 `4f7e300d` 已经在 master 上**（经由孪生分支
  `p18-audits-cover-half-the-paper`，`b9f833d2` / `9d0cb6b9` 两笔合并）。
  这两个 commit 带的正是「45 个门测试」与「referee 轴刷新」——
  即工单描述里的两件事**已经落地了**。
* **`5f11953b` 与 `0eb876f7` 尚未落地**，后者正是「85 条 findings」那一笔。

**要紧的分寸**：`git cherry` 比的是 patch-id，对上下文敏感。
`+` 只说明「没有逐字等价的补丁」，**不等于内容不在 master 上**——
若 master 经另一条路径写进了同样的内容，patch-id 也会不同。
所以这一步只把范围缩小到两个 commit，**内容是否真的缺失，由下面的逐条比对回答**，
不由 cherry 回答。这也是为什么 §2 里「master 侧行数更大」不能当结论用。

## 5 · 逐条比对的结论：**这个分支的内容已经全部在 master 上**

三组独立比对（互不通气，各自只拿到自己那几个文件），结论一致。

### 5.1 决定性的那条证据不是判断，是 blob 哈希

`citecheck-A` 与 `citecheck-C` 的 **p18 侧 blob，与 master 那两次重写所基于的前像逐字节相同**：

```
citecheck-A: p18 blob = c47fbd24…  ;  master 重写 32cc229e^ 的前像 = c47fbd24…
citecheck-C: p18 blob = aee9a16a…  ;  master 重写 861b0af0^ 的前像 = aee9a16a…
```

即**master 的作者手里拿着的就是 p18 这份文本，然后在它上面重写**。时间也对得上：
p18 是 07-30 11:56，master 的两次重写是同日 15:32 与 17:12。

### 5.2 master 把 p18 的产出明写在自己的 commit 里

`fe0d9357`（07-30 14:46）逐字：

> **papers: 161KB of finished citation audit existed on one disk only**
> P18. Slices B (§4-§6), D1 (§9-§10) and D2 (§11-§12) were complete on disk and
> untracked … **A and C are stubs and are named as such**

而 `citecheck-B` / `D1` / `D2` / `COVERAGE.md` 四份**本单实测 md5 两侧完全一致**。
所以 0eb876f7 那笔「85 条 findings」的产物，**逐字节已经在 master 上**——
`git cherry` 之所以报 `+`，是因为 patch-id 对上下文敏感，不是因为内容缺失。
（这正是 §4 预留的那个分寸，落到了实处。）

### 5.3 七个冲突逐个裁决：**全部取 master 侧**，理由逐条

| 文件 | 裁决 | 理由（不是「master 比较大」） |
|---|---|---|
| `citecheck-A` | master | p18 是 77 行**残稿**：只有 Pass A，B/C/D 三段无正文，九个数里五个不可证伪。master 810 行逐条枚举，并**逐项写明它改了 stub 的哪几个数**（Pass A 69/62/7/0 确认；B 8→12；C 9→8；D 14→25 / 4→5），还**撤回了 stub 三条「承重发现」中的一条**（§1.2 五族拆分按字段逐一核对为**不是缺陷**）。取 p18 = 用残稿换掉完整审计 |
| `citecheck-C` | master | p18 43 行，**最后一行逐字是「(report in progress — sections appended as each pass completes)」**，零条 findings。master 784 行，且**确认**了 stub 唯一两条可查断言（行映射、Pass A 五个计数）为正确 |
| `verify_paper.py` | master | p18 新增 41 行里 **40 行逐字出现在 master**，第 41 行只差 master 给 `CHECKS` 元组加的第四个字段 `reads_sections`。`audit_stamp.py`（门的真正实现）与 `test_audit_stamp.py` **两侧逐字节相同**。取 p18 = 丢掉 master 后来加的 section floor、MISCASED/LOCAL/UNSHAREABLE、anchor 越界、gitignore 作用域、locator 闸等 |
| `MANIFEST.json` | master | p18 的 **7 个键在 master 中全部存在且取值逐字相同**（本单用 json 逐键比对，missing=[] diff=[]）。master 另有 13 个键与全部 14 份产物的 sha256 |
| `RUN_STATE.md` | master | p18 的 121 行是 master 309 行的**严格前缀**——本单实测：p18 中不出现于 master 的非空行 **0 行** |
| `REVIEW-2026-07-30.md` | master | 618 vs 619 行，**唯一的差别是 stamp 里的 `status`**：p18 写 `binding`，master 写 `stale` + `superseded_by: REVIEW-2026-07-31.md`。而那个后继在 master 上确实存在（链条一直到 `REVIEW-2026-08-01.md` 才是 `binding`）。**取 p18 会把一份已被两代取代的评审重新标成 binding，check G 当场变红** |
| `delta-old-vs-new.md` | master | p18 39 行是**未填的模板**（末行 `*(filled in below as verification proceeds)*`）。master 447 行是填完的（A 66 行 / B 54 行 / C 19 行，合计 139）。且 master 第 42 行**逐字撤回了 p18 的一句断言**：p18 写「历史里不存在 91 244 字节的状态」，master 找到了那个状态（commit `080f05da`，1534 行）并写明「that assertion is withdrawn」。取 p18 = 把一条已被证伪的话放回去 |

**唯一一处 p18 有而 master 没有的文字**，如实记下：`delta-old-vs-new.md` 里
「Verdicts as recorded: A — no verdict; B — **Reject** as submitted; C — **Reject**,
"a closer call than the last round".」这一句。**但事实本身没丢**——
它逐字在 master 的 `runs/…P12…/review-d-adversarial.md:19`。判为不必回填。

### 5.4 合并结果：**与 master 逐字节相同**

```
$ git diff origin/master --stat
（空）
```

七个冲突全部取 master 侧之后，合并树与 master **没有任何差异**。
这不是「合并失败」，这是**合并的正确结果**：这个分支的内容已经在 master 上，
合并提交的作用是**把历史接上**，让 `ci_merge` 不再第 13 次重试它。

## 6 · 85 条 findings 的重数 —— 数字对不上，而且**在合并之前就对不上**

工单第 3 条要求重数，并且「不许照抄旧数」。重数结果：

`0eb876f7` 的 commit message 自称 **21（B）+ 32（D1）+ 32（D2）= 85**。
但按三份文件**自己的 summary 表**重算：

| slice | 文件自报的分项 | 合计 |
|---|---|---|
| B | Pass B 错 **11** + Pass C 无引用 **7**（其中 1 条与 B 重叠）+ Pass D 不精确 **5** | **23**（去重 22） |
| D1 | 文件自己写「Findings by severity: 5 high, 8 medium, 19 low **(32 total)**」 | **32** |
| D2 | Pass B **9** + Pass C **9** + Pass D **4** | **22** |

**三者相加 = 76 或 77，不是 85。** 而且三份文件用的不是同一种口径：
D1 报的是**按严重度的总数**，B 与 D2 报的是**按 pass 的分项**，两种数法不可直接相加。

**要紧的是这一句**：这三份文件在分支与 master 上**逐字节相同**，
所以**这个差额不是合并造成的，也不是合并能修的**——它在 `fe0d9357` 落到 master 那天
就已经是这样了。commit message 里的 85 从来没有从文件自身的表里复算出来过。
本单**不去改那三份文件**（它们是别人的审计记录，且已在 master 上），
只把差额与口径不一致登记在此，并随 inbox 交给 papers 的所有者。

（顺带印证：master 自己的 `MANIFEST.json` 用的是第三种口径——
「332 enumerated rows total (66+57+70+73+66)」，数的是**行**不是 findings，
并特地注明「Row counts emitted by count_rows.py, not asserted」。
三种口径并存本身就是这个数不该被照抄的理由。）

## 7 · 验收实测

| 项 | 合并前（master） | 合并后 | 判定 |
|---|---|---|---|
| `python -m pytest papers -q` | 2 failed, 272 passed, 1 xfailed | **2 failed, 272 passed, 1 xfailed** | **无回归**（同一组失败） |
| `verify_paper.py` | FAIL (3/7) — C FIGDATA, E UNCITED, F BARE | **FAIL (3/7) — 同三条** | **无回归** |

合并树与 master 逐字节相同，所以两者必然一致——**这正是本次验收的形式**：
不是「门变绿了」，而是**「这次合并没有动任何东西」，且这一点是可验证的**。

**工单的验收线「paper 门全绿才算合上」本单达不到，如实记为 gap**：
门在我动手之前就是红的（§0），红的三条 C/E/F 与 p18 无关，
修它们属于 `papers` 正文与图数据的活，而 CHARTER 把**论文正文**判给 RES-2，
本单（W-*）不得下笔。**不降低验收线，也不假装达到**：本单交付的是
「合并正确且零回归」，而不是「门全绿」。

## 8 · 一个跑测试时掉出来的缺陷（不属本单，如实记）

跑 `python -m pytest papers -q` 之后 `git status` 出现：

```
 M papers/phase1-workshop/figures/fig1_concept_timeline.txt
```

**papers 的测试套件会改写一个被跟踪的生成物。** 改动内容是给「表达力账本」
加一条 `E-10`（`theoria-arm` 的前沿格烧灼，GAP R2-2），而**两侧分支的生成器
`fig1_concept_timeline.py` 里都没有 E-10**——说明磁盘上那份 `.txt` 相对于它自己的
生成器输入**已经陈了**，一跑测试就被重算出来。

本单**没有提交它**（`git checkout --` 还原）：它与 p18 合并无关，
且仓规「生成物禁止手改」的另一面是「生成物也不该被测试顺手改掉而无人发觉」。
登记为发现，随 inbox 交给 papers 所有者。
