# S11 · 护栏只装了宽松那一半 — 补上封存那一半

worker `W-1410` · branch `agent/s11-sealed-halfguard` · base `6beb2e6` · 2026-07-28T14:13:24Z
territory `arc-recon`（外加 `CLAUDE.md` 与根 `.gitignore` 两处，由条目目标 (3) 明文授权）

**全程零网络、零 API 调用、零动作、封存堆接触 0。** 本条目不花钱，也不需要过花费闸门。

---

## 这件事的形状

OPS-B 的核查是对的，而且它指出的不是一个错误，是一个**缺口的形状**：
`ACCESS_CHECK.md` 第 8 项的题目是 "licensing"，所以同一个发现的封存那半**没有格子可填**，
于是它没有落地。许可结论本身一个字都不用改——它在许可维度上完全正确。
问题在于它**独自出现**：那句话说「缓存被允许」，同一段里没有一句说明**缓存里装的是什么**。

而 `browser-ops/TERMS.md` §4.2 记着另一半（附原文与 URL）：首跑 "download the game source"，
`make list-games` = "Print every game id available"，`make play-local` = "Runs your agent
against every game in the dataset"，swarm 的 `--game` 缺省即 "plays all available games"。

**照着「permitted，无需许可」去做的第一件事，会把全部 25 局的源码拉到磁盘并全部跑一遍。**
按 INC-BA-001 的判据，源码比轨迹更靠前一档：它直接给出机制的成品答案。

### 本轮独立确认的一条，值得单写

**本地引擎是账本看不见的那条路。** `contamination.py` 审的是「我们发过的每一次 API 调用」，
而本地跑一遍**不产生任何 API 调用**——不进 `recon_ledger.jsonl`，不进任何账本。
一个会话在本地把 25 局全跑一遍，`verify.sh` 的账本审计**从头到尾一片绿**，
21 局的源码已经在盘上了。现有仪器在**结构上**看不见它。

这就是为什么第 (2) 件必须是**新代码**，而不是往 `assert_playable` 里再加一条断言：
`assert_playable` 守的是 API 路径，它在这条路上根本不会被调用。

---

## 交付的三件

### (1) `ACCESS_CHECK.md` — 紧挨着结论 1 补封存侧

* §8a.1 结论 1 **原文一字未动**；紧随其后加一段，开头即
  「这句话是关于许可的，它没有说缓存里装什么」，点明 **permission is not containment**，
  并指向 §8b。
* 新增 **§8b「The containment half — "permitted" is not "safe"」**：
  上游四条缺省行为的原文表格、账本盲区那段、可执行的规则、护栏的五种拒绝、
  以及两条被测试钉住的性质（边界锚定、scan 不开文件）。
* 顶部条目表第 8 行补 "**Permitted ≠ safe**" 与护栏链接——只看表的人也会撞见它。

### (2) `local_engine_guard.py` — 可执行、fail-closed

形状照 `baseline-arms/SCHEMA_PATH_A.md` §3，理由也照抄它的：**反向名单遇到没预料到的
路径形状会开放失败，而开放失败不可撤销。** 五种拒绝，一种放行：

| 判定 | 触发 |
|---|---|
| `deny_default_all` | 命中触发器但**没有 `--game` 选择器**——上游缺省即全量，所以「沉默」是危险案例 |
| `deny_sealed` | 命令行任何位置点名 21 局之一（全 id 或 4 字符前缀），**先于** allow 分支判 |
| `deny_unknown` | 选择器 token 不是开发堆 id 或其精确前缀。上游把它当**前缀**用，`--game=s` 会同时命中 `sk48` 与五局封存 |
| `deny_unfiltered` | `make list-games` / `make verify-local`——**根本不接受过滤器** |
| 全盘拒绝 | `piles.json` 缺失、损坏、或不再哈希到 `CLAUDE.md` 钉住的值 |

四个入口：`check`（判定，退出 2 即拒）、`run`（判定通过才 exec，否则**什么都没跑**）、
`scan`（按**文件名**筛缓存目录）、`selftest`（离线自证）。
退出码沿用金丝雀的口径（0 / 2 / 1），调度器可读。

**两条刻意的性质：**

* **前缀双侧边界锚定**——`blobs/9ar25f0e/` 不读作 `ar25`。这正是 SCHEMA_PATH_A §3.1
  第一次执行时踩的那个坑，所以它是一条测试而不是一句注释。
* **`scan` 不开任何文件。** 它是文件名筛子。有一条测试 monkeypatch 掉 `open`，
  只要 scan 期间被扫目录下有任何文件被打开就红。**下载不等于阅读**，
  而一个会引述它正在拒绝的文件的护栏，本身就是泄漏。

`test_local_engine_guard.py`：**105 例**，重点全在「护栏该红的时候确实红」——
21 局封存 × 6 种命令模板 × （全 id + 前缀）、缺省全量的 7 种写法、
选择器松 token、两堆前缀不相交且互不嵌套、CLI 退出码合约、
以及 `run` 被拒时 `subprocess.call` **一次都没被调用**。

### (3) `CLAUDE.md` — 进封存纪律一节

四条：必须点名开发堆四局；护栏在代码里而不是靠记性（附三条命令）；
**绿色的账本审计不能读成「这条路没人走过」**；`environment_files/` 已 gitignore、
且其中非开发堆的文件不得被打开。根 `.gitignore` 同步加了 `environment_files/`
（提案里的建议；Phase 4 释出清单会公开全部 tracked 文件，而这是 ARC 的内容不是我们的）。

---

## 测试与验收

| 检查 | 结果 |
|---|---|
| `python -m pytest`（arc-recon 全量） | **187 passed**（继承 82 + 新增 105） |
| `python local_engine_guard.py selftest` | green |
| `bash verify.sh` | **VERIFY: green**，含两条新步骤 |
| 网络 / API 调用 / 花费 | 0 / 0 / $0.00 |
| 封存堆接触 | **0**（本条目全程未打开任何一局的任何内容） |

**开工时先跑了一遍基线：82 passed，绿了才动手。**

### 写测试当场抓到的一个真缺陷

`load_piles(path: str = PILES_PATH)` 把切分文件路径**绑在了 import 时刻**的默认参数上——
运行期改 `PILES_PATH` 不生效，护栏会继续读一份已经被挪走的切分。
测试 `test_unreadable_cut_makes_the_cli_exit_two` 让它红了，改成调用时解析。
这条值得记：一个 fail-closed 的护栏，如果它读的是一份陈旧的切分，它的「fail-closed」是假的。

---

## 缺口，如实登记（不降验收线）

1. **护栏拦的是命令行，不是系统调用。** 一个进程只要不经过 `check`/`run`
   就能直接跑 `make play-local`。这是**纪律 + 工具**，不是沙箱。真正的强制需要
   proxy 层或文件系统层，那超出本条目范围，也超出 `arc-recon` 领地。
   缓解：`scan` 是**事后**探测器，挂在 `verify.sh` 上，所以「有人绕过去了」这件事
   会在下一次 verify 时被看见——但那时源码已经落盘了。
2. **触发器是名单，名单会漏。** 我按上游文档里出现过的调用形态写（make 目标、
   `main.py --agent`、`arc_agi` / `Arcade()` / `arc.make(`、`swarm`、`environment_files`），
   并加了一条兜底：**任何命令、无论是否命中触发器，只要点名封存局就拒**。
   兜底覆盖的是「点名封存局」，覆盖不了「一个我没预料到的、缺省全量的新入口」。
   本轮已派对抗性子代理专攻这一点，结论见下节。
3. **OPS-B 提案的 B / C / E 三项本条目未做**，因为不在条目目标里：
   B（replay 页写进封存红线明文清单）属**不可逆损害**那一类，与本条目同级；
   C（§6 配额措辞改两层口径）、E（`recon_findings.json` 加 `superseded_by`）是账目质量。
   已另投 `monitor/inbox/`，**不代为决定，也不顺手改**——顺手改别人工单尾巴正是 E1 的错法。

---

## 对抗性复核

见下节「对抗性复核结果」。
