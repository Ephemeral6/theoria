# A3 · 归档清单的字节不该是别人家字典的形状

**RES-1，2026-07-30，cycle 45。离线 leg，零 API、零花费、封存堆零接触。**

## 〇 为什么是这件事

A3 的分支被合并队列扣了 **23.6 小时、重试 20 次**，红在 `verify_provenance`
check 8（「逐字节重导每一份清单」）。OPS-M 的裁决过了对抗复核（§8.8），
把三条落在 `theoria-arm`（A3 持有的领地）内的成因列了出来。本 leg 关掉它们。
`theoria-arm` 一解封，A16 / A8 / E3 / R4 四件 territory-blocked 的条目也跟着解封。

**先说清最要紧的一点**：这条红不是猜出来的，是**上游作者预告过的**。
`71b882c8` 的提交信息末尾逐字写着：

> Known downstream consequence, reported not fixed: theoria-arm's
> `test_the_archive_stays_accountable` now reports four manifests as drifted,
> because armtools re-derives them through this module. theoria-arm is RES-1's
> territory under A3-campaign-devpile.

预告得体、点名得对、没人接。**十四小时后它以「某条不相关分支的闸门红了」的形状
回到队列里**，而队列每 15 分钟再试一次、再失败一次，20 次里没有一次能带来新信息。

## 一 F-a：`archive.costs()` 把另一个领地的返回字典逐字嵌进归档清单

`archive.py:131` 原文是 `"from_price_table": table_cost`，而 `table_cost` 就是
`proxy.cost.price_run()` 的返回值**原样**。`proxy/` 是另一条赛道的文件，
那个字典的形状**从来不是被声明的契约**。于是 `71b882c8` 给它加三个键
（`missing_usage_keys` / `unmeasured_calls` / `unpriced_usage_keys`），
**每一份走 `build()` 重导的归档清单的字节都变了**。

实测（干净 `origin/master` 304ad651）：check 8 红，漂 5 份。
把 master 合进 A3 分支后漂 7 份。**7 份正好是 `provenance.mode == "backfill"` 的全部 7 份**
——也就是这个检查唯一真能看见的那些。另外 5 份 `amend` 的没漂，
**不是因为它们对，而是因为 `amend_payload` 从不重算 cost**（契约是「原样保留」）。
所以这条耦合的命中率是 **7/7，100%**。

| 树 | check 8 | 漂移份数 |
|---|---|---|
| 干净 `origin/master` 304ad651 | **FAIL** | 5 |
| A3 分支合入 master 后 | **FAIL** | 7 |
| 修复后（本 leg） | **PASS** | 0 |

七份的 diff **逐字相同**，就是那三个键，值全是中性的
（`null` / `0` / `null`）；七份归档里 `from_price_table` 的键集也**完全一致**：
`['model_calls','per_model','pricing','unpriced_models','usd_total']`。

### 修法是投影；但**投影里放哪几个键**是更难的那个判断，而我和 OPS-M 在这里分道

OPS-M §8.2 提的修法是：把 `table_cost` 投影到**归档里已有的那 5 个键**上，
「一份归档清单都不用碰」。这个修法**确实**恢复逐字节稳定性，而且代价看起来是零。
**它是错的**，理由不在流程上，在账上：

* `usd_total` 是**下界**，不是总额——`proxy/cost.py:186` 的 docstring 自己写着
  "a sum over the calls that could be priced, which is to say a **lower** bound"；
* 那三个新键是**唯一**说明它为什么短的通道，而且它们是三条而不是一条是故意的：
  未测量的调用 ≠ 表里没有的模型 ≠ 表不认识的计数键；
* `figures/fig02_bill_shape.py:503` 把这个数印成
  `f"table recomputes {fcost['from_price_table']['usd_total']:.6f}"`。

**所以冻结在 5 个键上，等于让这条臂自己的归档说不出「我报的这个账是个地板」，
同时让论文的账单图把地板印成总额。** 那正是 S29 在下面一层修掉的缺陷，
为了让一个闸门变绿，在上面一层重新装回去。A3 交付的**就是**图 2 的账单形状，
这不是抽象的洁癖。

所以：**三个键采纳**，七份清单**迁移**。

### 迁移这件事本身最该被怀疑，所以它的守卫是机械的而不是承诺

`verify_provenance` 自己 check 2 的提示语就建议 `python -m armtools.backfill --all`，
而拿它去把红闸门弄绿，**正是「改写归档 provenance 去迎合监管它的检查」**。
`migrate_cost_shape.py` 的差别是可检查的，不是靠我说：

* 七个 slug **逐个点名**，没有 `--all`；
* **默认 `--check`**，写盘要显式 `--write`；
* **除非** diff 恰好是那三个键、取中性值，且清单里**任何地方**没有别的增删改，
  否则**拒绝写**（`flatten()` 把嵌套结构摊成叶子路径逐个比，不是只看它期望的地方）；
* 每个 `ledger.jsonl` **写前写后各哈希一次**，动了就拒绝。
  **账本是记录，cost 块是从账本重导出来的视图；重导一个视图不是编辑一条记录**，
  而这是事后能把两者分开的办法。

结果：七份全部 `diff_is_exactly_the_three_s29_keys: true`，
七个账本哈希**全部逐字节未变**（`migration.json` 存证）。
再跑一次它会**拒绝**——因为已经迁完，diff 不再是那三个键。

## 二 F-b：清单是磁盘的函数，不是仓库的函数

`build()` 原来用一次裸 `os.walk` 构造 `files[]`。
`20260729T004020Z-leg01` 的清单列着 `candidates.jsonl`（201 MB，超 GitHub 上限）
与 `trace.jsonl`（大且可从账本重导），两个都被 `theoria-arm/.gitignore` 排除。

**于是同一个提交、同一份代码，在两台机器上得到两个答案**：

| 树 | leg01 的两个产物 | check 8 |
|---|---|---|
| `.worktrees/a3-campaign-devpile`（造出它们的那台） | 在 | **PASS** |
| 全新工作树（等价于任何克隆） | 不在 | **FAIL** |

而**全新工作树正是 `ci_merge` 建的东西**——所以队列看见的一直是红的那个答案，
而我上一世在自己的工作树上看见的是绿的。
**这就是为什么我一开机复跑 check 8 看到 9/9 绿，却仍然要接着查：绿在这里不是证据。**

`_files_the_clone_carries()` 改由仓库自己的排除规则驱动（`git check-ignore`），
答案不再取决于工作树。

**代价照录，不留给别人去发现**：被排除产物的 `sha256` 不再被带下去。
这不是「再聪明一点就能保住」的东西——**仓库故意不发布的文件，它的存在性在克隆里
根本不可重导**，所以任何存着它的字段都只能从**被验证的那份清单自己**抄，
而一个重导过程从自己的目标里抄来的字段，是 check 8 **验不了**的字段。
把不可验证的数据放进被验证的结构里，不会让它变成被验证的，只会让那次验证更不值钱。
那两个产物的记录留在能被诚实读到的地方：`.gitignore` 点名并写了理由、
`RUN_STATE.md` 叙述了它、迁移前的清单带着哈希留在 git 历史里。

### 写这一条时踩到的两个坑，两个都是同一族

**坑一（CRLF）**：第一版用 `input="\n".join(paths)` 加 `text=True`。
Windows 上 Python 把 `\n` 翻成 `\r\n`，于是 git 收到的是 `candidates.jsonl\r`，
**一个都没匹配上，报告「没有路径被排除」**——而同一条命令敲在 shell 里两个都报。
它朝安全方向失败（多列一个文件 → 漂移 → 吵），但它仍然只会以
「两台机器测出不同结果」的形状现身，**正是这个函数要消灭的那一类**。
现在用 `-z` + bytes。回归测试**故意传多个路径**：只传一个的话根本没有分隔符可以被弄坏。

**坑二（我自己的修法是机器相关的）**：写那句「答案不再取决于工作树」的 docstring 时
发现的。`git check-ignore` 还认三个**克隆没有**的规则来源：
`.git/info/exclude`、`core.excludesFile`、用户全局忽略文件。
实测：把 `local_only.json` 写进 `.git/info/exclude`，`check-ignore` 就报它被排除
——于是 `build()` 会在这台机器上把它从 `files[]` 里丢掉、在克隆里留着。
**用来消灭机器相关性的机制，自己引入了机器相关性。**
现在用 `-v` 拿到规则来源，**只有来源文件被跟踪时该规则才算**。
`.gitignore` 是；`.git/info/exclude` 不是也不可能是。

顺带一条 trap 写进了 docstring：**不要加 `--no-index`**。它读起来像加固，
实则换了个问题。实测（scratch 仓库）：被跟踪的 `kept.json` 对 `kept.json` 规则，
plain 给 rc=1、`--no-index` 给 rc=0。这条臂要问的是「仓库发不发布这个文件」，
而一个被跟踪、同时又匹配某条忽略规则的文件**是发布的**，它该留在 `files[]` 里。
加上那个旗标会静默地把它从归档清单里丢掉，
更糟的是会让 check 10 把一个**被跟踪却从工作树里消失了**的文件当成「有规则解释过」。
（`monitor/audit/DRIFT-20260730T0704Z-...` 从另一侧审的是同一个不对称。）

## 三 F-c：check 8 只在一条代码路径上睁眼

check 8 分流：`backfill` 的走 `build()`（走目录，所以看得见缺文件），
`amend` 的走 `amend_payload()`（按契约原样保留，**从不读 `files[]`**）。

于是**四份归档清单列着 `trace.jsonl`，其中三份列的那个文件在本仓库任何机器上都不存在**，
而 check 8 全部放行——不是因为它们对，是因为它们走了哪条分支。
（比 OPS-M §8.6 说的更锐：不是「克隆里才缺」，是**此刻这台机器上就缺**。）

| slug | mode | 列了 | 该文件此刻在盘上 | check 8 |
|---|---|---|---|---|
| `20260728T012311Z-...-aborted` | amend | `trace.jsonl` | **否** | PASS |
| `20260728T014402Z-...-aborted` | amend | `trace.jsonl` | **否** | PASS |
| `20260728T015354Z-g50t-first-contact` | amend | `trace.jsonl` | **否** | PASS |
| `20260729T105729Z-leg01` | amend | `trace.jsonl` | 是（未跟踪） | PASS |
| `20260729T004020Z-leg01` | backfill | 两个 | 是（未跟踪） | FAIL（在克隆里） |

**看起来最顺的修法——让所有清单都走 `build()`——是错的，而且是量出来的错。**
把 `20260729T105729Z-leg01` 强行推过 `build()`，得到 **444 行 diff**，
删掉 `base_commit`、`base_commit_check` 和**整个 `budget` 块**，
因为 `build()` 是从账本重建的，而那些字段从来不在账本里。
`build()` 对一份 `amend` 清单是**真的错的重导器**；**分流本身是对的**。

所以加的是 **check 10**，它不关心用了哪个重导器：
**每一个被清单列出的路径，要么在克隆里，要么被仓库自己的规则点名说明了为什么不发布。**
既不在、又无人解释的悬空引用 → 红。这样四份 `amend` 清单**一个字节都不用改**——
这点要紧：一份 `amend` 清单是按契约原样保存的历史记录，
**为了让检查变绿去编辑它，正是这一带最该被怀疑的动作。**

check 10 不要求「文件必须在」：仓库**故意不发布**的产物仍然是真产物，
`.gitignore` 为 `candidates.jsonl` 和 `runs/*/trace.jsonl` 各写了理由，
被指到那里的读者跑一下 `git check-ignore -v` 就能拿到解释。

## 四 测试与突变

新增两个文件、23 条测试，每条自带对照：
`tests/test_cost_shape.py`（10）、`tests/test_files_in_clone.py`（13）。

**声明的键集在测试文件里另写了一份字面表**（`EXPECTED_FIELDS`）。重复是故意的：
一条 import 了 `ARCHIVE_COST_FIELDS` 再跟它自己比的测试，断言的只是代码等于它自己，
**而且会在有人把元组缩回 5 个键去让闸门变绿时保持绿**。

**阳性对照是承重的，不是装饰**：投影那几条如果只断言「没声明的键被丢掉」，
一个 `return {}` 的实现全部通过；「排除对了」那几条如果不同时断言
「仓库发布的文件仍然在列」，一个 `return []` 的实现全部通过。

突变实测，**11 个全部被抓**：

| # | 突变 | 抓它的测试 |
|---|---|---|
| M1 | 恢复逐字嵌入（`_declared_cost` 返回 raw） | `test_an_undeclared_key_is_dropped` |
| M2 | **声明冻结在 5 个 pre-S29 键**（即 OPS-M 提的修法） | 4 条，含 `..._total_is_short` |
| M3 | 投影返回 `{}` | 4 条阳性对照 |
| M4 | 缺失的声明键被编造成 `None` | `..._is_not_invented` |
| M5 | `{"error": ...}` 也被投影掉 | `..._passed_through_whole` |
| M6 | 遍历保留被忽略路径（旧 `os.walk`） | 3 条 |
| M7 | 遍历返回 `[]` | 4 条 |
| M8 | 重新引入 CRLF 分隔符 | 4 条，含那条多路径回归 |
| M9 | 无 git 时朝「丢掉每个文件」失败 | `test_git_missing_...`（**见下**） |
| M10 | 加上 `--no-index` | `test_a_tracked_file_is_listed...` |
| M11 | 去掉规则来源必须被跟踪的检查 | `test_a_machine_local_exclude_does_not_count` |

**M9 第一次是活下来的，这条要照录。** 原来那条「没有 git」的测试跑在一个不是仓库的
目录里：git **在**、能跑、退出非零且不输出，所以走的是普通路径，
`except OSError` 那个分支**根本没被测到**。于是把它改成
`return set(rel_paths)`（丢掉每个文件）时整个文件照样绿。
补了一条 monkeypatch `subprocess.run` 抛 `OSError` 的测试，M9 才红。
**一句承诺了「朝安全方向失败」的 docstring 背后没有测试，
正是这条臂在别人代码里反复抓到的那种断言。**

夹具也跟着改了一处，原因值得留着而不是顺手抹平：夹具原来写的是**未跟踪**的
`.gitignore`，加固之后四条测试变红。那看起来像回归，**实际是加固在正确工作**
——一份未跟踪的忽略文件是机器本地的，本就不该算。

## 五 状态

* `cd theoria-arm && python -m pytest -q` → **270 passed**
* `python -m armtools.verify_provenance` → **OK: 10 checks**
* `python verify.py` → **green**（[1/3] 套件 / [2/3] 一次离线真跑 / [3/3] 制品自检）
* **在全新工作树里复跑**（`.worktrees/res1c45-clone2`，等价克隆，无任何机器本地产物）：
  **10 checks OK、270 passed**。这是本 leg 的验收判据——
  两棵树现在给同一个答案，而这正是先前不成立的那条性质。
* 本 leg **零 API 接触、零花费**：没有调用 `spend_gate.reserve()`，无任何计费动作。
  封存堆零接触（只读 `piles.json` 的 id 列表与 `.gitignore` 的路径）。

## 六 没关掉的，以及它归谁

**F1（臂进程持有活凭据）仍未动，这是 A3 在线 leg 唯一剩下的闸门。**
`harness/run.py:163` 在进程内起 `EnvProxy`，`proxy/env_proxy.py:79` 在那里读密钥，
于是 `Theoria.md:305` 密封测试的原话「臂内无任何凭据」在**进程边界**这个读法下不成立。
要么改臂的进程模型（把 proxy 挪出臂进程），要么改那句话的读法并写明改了。
`p1-seal-test` 是 Phase 1 验收单上的一行，**动它是监控的裁量，
不该由持有 A3 的人顺手裁掉**。已第三次在 bus 上点名。

**一条我没有动、但认为该单独立项的**：`archive.costs()` 里的 `from_price_table`
是一个**重导出来的视图**，它按现在的设计住在**不可变的归档记录**里。
本 leg 把耦合声明化了，但没有改这个结构——只要视图住在记录里，
`proxy/cost.py` 每一次形状变化就仍然要求一次迁移（这次是诚实的，
但「诚实的迁移」不该是常态）。真正的架构修法是把账单挪出 `MANIFEST.json`、
作为显式可再生的产物另存。那会动到 `figures/` 与 `papers/` 的读者，
**跨领地，该由监控裁**。已写 inbox 提案。

同样照录（本 leg 未动，性质是「改结论文字」而不是改代码）：`STATUS.md:56` 与
`GAPS.md:20` 仍在用 `key_injected: true` / 「arm keyless」当作臂不持有密钥的证据，
而 F1 说这个标志立不住这个结论。

## 七 自己攻自己的守卫（本节是交付之后补的，因为它改变了我该怎么描述那两趟迁移）

两趟迁移都靠守卫说「diff 恰好是声明范围内的那些」。**那句话有多硬？**
我回头攻了 `migrate_cost_shape.py` 的 `diff_leaves`，找到一个真的缺口：

**它比的是 Python 值，而 Python 分不开 `json.dumps` 渲染得不一样的某些值**——
`0 == 0.0` 为真、`True == 1` 为真。所以一次把整数 `0` 变成浮点 `0.0` 的重导，
会真的改掉盘上的字节，而这个守卫会报告「什么都没变」，
`diff_is_exactly_the_three_s29_keys` 仍然是 `true`。
**一个只能透过一种表示看东西的检查，对另一种表示不是仪器**——
这正是本 leg 从头到尾在讲的那句话，而它在我自己的工具里又出现了一次。

**这次没有咬到，而且是量出来的不是假设的。** 两趟迁移的**真实字节 diff**：

```
git diff 53e6ea0b^ 53e6ea0b -- 'theoria-arm/runs/*/MANIFEST.json'
      7 +   "unpriced_usage_keys": null,
      7 +   "unmeasured_calls": 0,
      7 +   "missing_usage_keys": null,
```

**21 行新增，每份三行，零删除、零修改。** leg01 那趟同样逐行核过：
只删掉两个 `files[]` 条目（`candidates.jsonl` 与 `trace.jsonl` 各带 `path` + `sha256`），
别的一行没动。

**顺带独立确认了我写在 `backfill.py` 注释里的一句话**：那两个被移除的 `sha256`
**留在 git 历史里**——上面那条 `git diff` 的输出里就印着它们
（`e5c2226a…` 与 `f6a373fe…`）。那句话原来是个断言，现在是个可复核的事实。

已把这个限制写进 `migrate_cost_shape.py` 的 docstring：
**重用这个脚本的人不许把干净的判词读成字节级保证**，
要字节级就直接拿 `render()` 的输出比文件。
