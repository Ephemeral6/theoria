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
2. **触发器是名单，名单会漏——而且已经被证明会漏。** 对抗性复核在触发器覆盖面上
   一口气找到四条（见下节 1/6/7/8）。修完之后名单**仍然是名单**：兜底只覆盖
   「点名封存局」，覆盖不了「一个谁都没预料到的、缺省全量的新入口」。
   这条 gap 不会因为修了九个洞而关闭，只会变窄。
   **`scan` 是它唯一的对冲**：入口漏了，落盘的名字漏不掉。
3. **OPS-B 提案的 B / C / E 三项本条目未做**，因为不在条目目标里：
   B（replay 页写进封存红线明文清单）属**不可逆损害**那一类，与本条目同级；
   C（§6 配额措辞改两层口径）、E（`recon_findings.json` 加 `superseded_by`）是账目质量。
   已另投 `monitor/inbox/`，**不代为决定，也不顺手改**——顺手改别人工单尾巴正是 E1 的错法。

---

## 对抗性复核 —— 派了一个专攻绕过的子代理，它找到 **9 条真绕过**

明令：只许读本地文件，**不许联网、不许搜索任何与 ARC 局有关的东西**；
每条发现必须**实跑确认**，找不到就说找不到，不许编。它交回的每一条我都复跑过。

**先说一件事：封存名匹配那部分它没打穿。** 全 id、4 字符前缀、逗号列表、
开发+封存混列、引号形式、`9ar25f0e` / `9ls20a` 的边界锚定——全部照设计工作。
**九个洞全在别处**：触发器的**覆盖面**、argv 被拍平成一个字符串、以及 Python 的真值判断。
**设计注意力去的地方守住了，出事的全是它周围的管道。**

| # | 绕过 | 原判定 | 现判定 |
|---|---|---|---|
| 1 | `make -C ARC-AGI-3-Agents play-local`（以及 `-f` `-s` `-j4` `--directory=` `gmake` `mingw32-make`） | **allow** | `deny_unfiltered` |
| 2 | `assert_local_pull_allowed(g for g in [])` —— 生成器 | **返回 `[]`，无异常** | `LocalEngineRefusal` |
| 3 | `make play-local GAME=ar25` | **allow** | `deny_unfiltered` |
| 4 | `... --game=ar25 && uv run main.py`（及 `;` `&` `\|\|` 换行、引号内、注释后） | **allow** | 按段判，取最重 |
| 5 | `--game=ar25 --game=` / `--game ar25 all` / `--game ar25 *` | **allow** | `deny_unknown` |
| 6 | `uv run main.py`、`python main.py -a random`、`python -m agents.main --agent=x`、`swarm_runner.py` | **allow** | `deny_default_all` |
| 7 | `import arc_agi_3`（触发器写的 `arc_agi` 前瞻排除了 `_` 与数字，对真实包名**永远不匹配**） | **allow** | `deny_default_all` |
| 8 | `curl .../tasks/LS20`、`ENVIRONMENT_FILES` —— 大小写 | **allow** | `deny_sealed` / 触发 |
| 9 | `scan` 漏掉空的封存目录（只看 filenames）与「目标是文件」 | **报 clean** | 两者都红 |

外加两条小的：非字符串输入抛 `TypeError` 而不是 `LocalEngineRefusal`
（撞死也算 fail-closed，但 `except LocalEngineRefusal` 的调用方接不住）；
`--json` 被从 argv **任意位置**剥掉，会把子命令自己的 `--json` 吃掉。都已修。

### 其中两条改的是规则，不只是正则，单独记

**(a) `make play-local GAME=ar25` 本来是我写在文档里的正面例子，而它是错的。**
`GAME=` 这个拼法**是我发明的**。手上唯一的证据（`browser-ops/TERMS.md` §4.2，
带原文与 URL）只为 **swarm runner** 记了 `--game`，而 `make play-local` 记的是
"Runs your agent against every game in the dataset"，**一个参数都没有**。
GNU make 对没被引用的变量覆盖**是沉默接受的**——Makefile 若不消费 `GAME`，
这条命令会打全 25 局，而命令行**看起来是过滤过的**。
**「看起来过滤过」比「看起来危险」更糟**：它是会被照抄的那一版。
拒 `verify-local` 的理由（一对没写名字的局无法对切分核验）逐字适用于
`play-local`（一个没验证过的变量）。所以 `play-local` 进了拒绝集。
**它可以出来——等 Makefile 进树里、并且被证明确实消费某个具名变量之后，不是之前。**

**(b) 生成器让 `assert_local_pull_allowed` 开放失败。** `if not game_ids`
对任何生成器对象都是假，于是 `(g for g in cfg if want(g))`——安全的列表推导
去掉方括号的那个孪生兄弟——**跳过了「说出你那四局」的拒绝**，返回空白名单，
调用方接着无过滤地拉。**调用点上什么都不显眼。** 现在先 materialize 再判空。

### 它明说打不穿的

切分闸门（缺失 / 损坏 / 被拓宽的 `piles.json` 一律拒绝，经 CLI 重定向 `PILES_PATH` 实测）；
小写封存名检测的全部形态；Windows junction 进缓存**没有**逃过 `scan_dir`。
它诚实登记了一条**未确认**：真符号链接（`mklink /D`）因权限建不出来，
所以 `followlinks=False` 那条理论缺口**它不认领为发现**——这条自律值得照录。

---

## 修复后的复测

| 检查 | 结果 |
|---|---|
| 九条绕过 + 全部变体逐条重跑 | 35 条命令，**still-allowed: 1** |
| 那 1 条 | `uv run main.py --game=ar25` —— **本来就该 allow**（swarm runner + 开发堆过滤，是唯一有文档依据的合法形态） |
| 控制组（合法过滤形态、`python -m pytest`、`git status`） | 全部仍 allow，没有被误伤 |
| API 开放失败探针（generator / filter / set / None / 裸字符串 / 含 None） | **6/6 REFUSED** |
| `python -m pytest`（arc-recon 全量） | **233 passed**（继承 82 + 新增 151） |
| `bash verify.sh` | **VERIFY: green** |

新增测试从 105 涨到 **151**，多出来的就是那九条各自的具名回归。
它们在测试文件里单独成块并写了理由，因为**教训是可推广的**，
而下一个改触发器的人需要先读到这个教训。
