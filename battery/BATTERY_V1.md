# BATTERY_V1 — 指标电池的冻结记录

`Theoria.md:368` 的冻结清单十三项，第 8 项：

> **指标电池 v1(定义与代码、逐指标方向预测)**

这份文件就是那一项。它把电池的**定义**、**计算代码的逐文件 sha256**、**逐指标
方向预测的快照哈希**、以及**抗游戏审计的裁决**一次性钉住，此后任何改动都必须走
「新版本 + 说明」，不得就地改。

| | |
|---|---|
| 冻结版本 | `BATTERY_V1` |
| 冻结时刻 (UTC) | 2026-07-28T19:01:03Z |
| base commit | `7df12a39d1dbdcaff593c487694173adbf4acebc` |
| 分支 | `agent/v5-battery-freeze` |
| 工单 | `V5-battery-freeze`（工人 W-252） |
| 检查方式 | `python -m battery.verify` |
| 冻结时测试 | `python -m pytest battery/tests -q` → **237 passed**（冻结前 214，本次新增 23 条，全部在 `tests/test_freeze.py`） |

---

## 0. 先读两条，否则这份记录会被误读

### 0.1 「v1」是清单上的位置，不是树上的版本号 —— 冻的是 SHA，不是标签

仓库里同时存在四个互相矛盾的「版本」：`METRICS.md` 标题写 battery v1，
`run_battery.py` 发的 `battery_version` 是 `"v2"`，`battery/__init__.py` 的
`__version__` 是 `0.1.0`，`PREDICTIONS.md` 已经追到 v2.1。**「v1」在这棵树上指不出
唯一状态**，而 `Theoria.md` 写下「电池 v1」时，指的是清单上的第 8 项，不是树上任何
一个自称 v1 的东西。

**裁决：冻 SHA，不冻标签。** `BATTERY_V1` 这个名字只标识「冻结清单第 8 项的第一次
提交」。它在树上对应的实际状态是：`run_battery` 自称的 **v2**，`PREDICTIONS.md` 的
**v2.1** 一节，报告 `REPORT_V2.md`。第 2 节的哈希是唯一无歧义的标识；日后要复原
「冻的是哪一版」，读哈希，不要读标签。

### 0.2 冻结不等于验收 —— 这套指标里没有一条通过了工序 1

`Theoria.md:325`（工序 1，区分力）：

> 每个候选指标必须在已知能力梯度上拉开差距(CC vs Schema,效应量入册)——**分不开
> 已知差异的指标,没资格测未知差异**。

在 `Theoria.md` 指定的那条梯度（CC vs Schema，88 条对照臂 run，逐局配对）上，
**38 条指标里通过工序 1 的有 0 条**：

| 工序 1 判决 | 条数 | 含义 |
|---|---|---|
| `underpowered` | 8 | 效应量算出来了，但配对局数不够，检验力上限到不了 p<0.05 |
| `no-data` | 23 | 至少一侧算不出值，工序 1 **无法执行**，不是执行了没过 |
| `not-ranked` | 7 | `neutral` 方向的诊断项，本就不参与排序 |
| **`discriminating`** | **0** | 代码里的「通过」判决 |

**但「0 条通过」必须连着下面这一段读，否则会被当成一个比实际更强的发现。**

`battery/audit/discriminate.py` 的 `_verdict()` 只发五种判决：`underpowered` /
`no-effect` / `wrong-direction` / `discriminating`，加上 `not-ranked` 与 `no-data`。
通过的那一种叫 `discriminating`。而 `underpowered` 这一支**排在最前面**：

```python
if test["p_value"] is not None and test["min_attainable_p"] > 0.05:
    entry["verdict"] = "underpowered"
```

4 局配对下双侧符号检验的最小可达 p 是 **0.125 > 0.05**，所以只要一条指标两边都有数，
它就必然先落进 `underpowered`，**`discriminating` 在这批材料上按构造不可达**。

所以准确的说法不是「38 条都测了、都没过」，而是：**在这批材料上，工序 1 的通过判决
根本到不了，而这件事在回算之前就被预注册了**（`PREDICTIONS.md:385-387`）：

> **Four paired games still cannot reach p<0.05.** Unchanged since v0. Every
> verdict below will read `underpowered`, and the effect sizes are the only
> thing anyone should read. Six non-tied paired games remains the floor, and
> this material does not supply them — it supplies a second arm on the same
> four games, which buys pairing quality, not power.

结论不因此变软，只是把因果说对：**这份冻结记录冻的是一台尚未被证明能分开任何已知
差异的仪器。** 按 `Theoria.md:325`，它目前「没资格测未知差异」。补法只有一条 ——
**更多非平局配对局**，不是换指标、不是改阈值。冻结的意义恰恰在此：Phase 4 的可信度
来自「先写死、再回算」，而不是来自仪器已经好用。谁引用本电池的任何一个数，都要连着
这一节一起引用。

---

## 1. 定义

### 1.1 五族 38 条

族与候选指标由 `Theoria.md:313-321` 规定，实现为 `battery/metrics/` 下的注册表：
`Card`（`battery/metrics/__init__.py:66`，装饰器 `@dataclass(frozen=True)` 在 `:65`）
持有 `metric_id / family / direction / needs / unit / definition / fn`，
`REGISTRY`（同文件 `:88`）由 `@metric` 装饰器在导入时填充。**`tier` 不在 `Card` 上**
—— 它由 `battery/audit/gaming.py:375` 的 `tier_of()` 机械算出，见第 4 节。

下表由冻结时的代码生成，逐列口径：

* **direction** —— 注册时写死的方向（哪一头是「更有能力」的读法），使得排序无法在
  数出来之后翻转。
* **tier** —— `main`（主表）或 `reference`（参考项），工序 4 机械裁决。
* **工序 1** —— CC vs Schema 上的判决（第 0.2 节）。
* **预注册** —— `blind` 表示写预测时未见过该指标在任何臂上的值；`[seen]` 表示见过，
  该行在它被读出的那条臂上是**后见**（post-diction），不是预测。
* **降级依据** —— `✓` 表示该条不是靠散文判断降级的，而是被一个**跑得起来的攻击**
  当场打下来的。

| id | 族 | direction | tier | 工序 1 | 预注册 | 降级由攻击证明 |
|---|---|---|---|---|---|---|
| `X1` | 探索 | lower | reference | underpowered | blind |  |
| `X2` | 探索 | higher | reference | underpowered | blind |  |
| `X3` | 探索 | higher | reference | underpowered | blind | ✓ |
| `X4` | 探索 | lower | reference | underpowered | blind |  |
| `X5` | 探索 | neutral | reference | not-ranked | blind | ✓ |
| `X6` | 探索 | higher | reference | no-data | blind |  |
| `P1` | 计划 | higher | reference | underpowered | blind |  |
| `P2` | 计划 | higher | reference | underpowered | blind | ✓ |
| `P3` | 计划 | lower | main | underpowered | blind |  |
| `P4` | 计划 | lower | main | no-data | blind |  |
| `P5` | 计划 | neutral | reference | not-ranked | blind | ✓ |
| `E1` | 经济 | neutral | reference | not-ranked | blind | ✓ |
| `E2` | 经济 | higher | main | no-data | blind |  |
| `E3` | 经济 | lower | main | no-data | blind |  |
| `E4` | 经济 | lower | reference | underpowered | blind |  |
| `E5` | 经济 | lower | reference | no-data | blind |  |
| `E6` | 经济 | neutral | reference | not-ranked | [seen] | ✓ |
| `E7` | 经济 | lower | reference | no-data | blind |  |
| `M1` | 机制 | lower | reference | no-data | blind | ✓ |
| `M2` | 机制 | higher | reference | no-data | blind |  |
| `M3` | 机制 | lower | main | no-data | blind |  |
| `M4` | 机制 | lower | reference | no-data | [seen] | ✓ |
| `M5` | 机制 | higher | reference | no-data | [seen] |  |
| `M6` | 机制 | neutral | main | not-ranked | [seen] |  |
| `K1` | 认识 | higher | reference | no-data | [seen] |  |
| `K2` | 认识 | higher | reference | no-data | [seen] | ✓ |
| `K3` | 认识 | higher | reference | no-data | blind |  |
| `K4` | 认识 | higher | reference | no-data | blind |  |
| `K5` | 认识 | higher | reference | no-data | blind |  |
| `K6` | 认识 | higher | reference | no-data | blind |  |
| `K7` | 认识 | neutral | main | not-ranked | [seen] |  |
| `K8` | 认识 | higher | reference | no-data | [seen] |  |
| `K9` | 认识 | higher | reference | no-data | blind |  |
| `K10` | 认识 | higher | reference | no-data | blind | ✓ |
| `K11` | 认识 | neutral | main | not-ranked | blind |  |
| `K12` | 认识 | higher | main | no-data | [seen] |  |
| `K13` | 认识 | lower | reference | no-data | [seen] |  |
| `K14` | 认识 | higher | reference | no-data | [seen] |  |

**逐条定义的正文不在这里重复** —— 它在 `battery/METRICS.md`，由
`python -m battery.docs` 从注册表生成，`battery/tests/test_docs.py` 保证它与代码
不会漂。冻结记录钉的是**生成它的代码**（第 2 节），不是它的渲染结果；改定义只能改
代码，而改代码会让本记录失效。`METRICS.md` 自身的一处内部矛盾见第 7 节 W-C。

### 1.2 三个主终点里，电池只拥有一个

`Theoria.md:373` 规定：

> **主终点限三个**——U3 达成率、判决题准确率(含特异度)、前载指数配对差;电池其余
> 指标一律标探索性、不作确证主张,免多重比较稀释

对照本电池的注册表，逐条落点：

| 主终点 | 电池里的 id | 由谁计算 |
|---|---|---|
| 前载指数配对差 | **`E2`**（`frontload_index`，`battery/metrics/economy.py:85`） | **本电池** |
| 判决题准确率(含特异度) | **无** | 考卷轨道（`exam/grading/mark.py:95` 的 `confusion()`，特异度在 `:136`），不在电池内 |
| U3 达成率 | **无** | **全仓没有任何实现** |

**这是本记录必须明写的两条。**

其一，**三个主终点里，电池只计算其中一个。** 判决题准确率有实现、但在考卷轨道，
不受本冻结记录的哈希保护，需要冻结清单上的另一项来钉。

其二，**U3 达成率没有任何实现，因此它不能被清单上的任何一项冻住。** 查证过：
`proxy/scoring/` 是 `arc_v1`，即 ARC scorecard 的读取器（`score` /
`levels_completed` / `total_actions`），`proxy/` 下**不出现 `U3` 这个串**；U1–U4 是
`Theoria.md:262` 的说明书质量阶梯（U3 = 证得动吗），全仓唯一提到 `U3` 的 Python 是
`ablation-arm/verify.py` 里一句「还欠证书」的备注。**主终点少一个打分器，这不是电池
的缺口，是冻结清单的缺口**（W-J）。

其余 37 条一律是探索性指标，不作确证主张。

---

## 2. 计算代码指纹（逐文件 sha256）

### 2.1 口径

* **哈希算法**：sha256，over 文件字节，**先把 CRLF 归一成 LF**。实现见
  `battery/freeze.py` 的 `sha256_file()`，口径取自 `proxy/scoring/__init__.py:64`
  的 `_sha256_file` 先例（引文在 `:71`）—— *The freeze is about the rule, not about
  the file's transport encoding.* `battery/.gitattributes` 已把本领地全部文件钉成 LF，所以在
  `battery/` 内归一前后一致；归一是为了让这份记录在 `core.autocrlf=true` 的克隆上
  也复现得出来（这棵仓库的 `core.autocrlf` 确实是 `true`）。
* **排序**：仓库相对路径、正斜杠、`sorted()`。
* **缺文件即失败**：`fingerprint()` 对记录在案却不在盘上的文件抛异常，而不是跳过。
  会悄悄消失的冻结文件不算冻住了。
* **成员资格本身也被冻**：`unlisted()` 会走一遍 `battery/`，任何**没被任何桶、也没被
  显式列入 `NARRATIVE` 的文件**都判失败 —— 走的是**每一个文件，不只是 `.py`**。
  理由有三个，全都是实际打穿过这道闸的攻击：新增一个 `battery/metrics/xxx.py`
  会在冻结之外计算已发布的数；新增一个 `battery/tests/conftest.py` 能让测试不再反对；
  而 `pytest.ini` 是 pytest 的 rootdir 配置，一行 `addopts` 就能把任何一条会反对的
  测试 deselect 掉。只查 `.py` 的版本对后两者是瞎的。

### 2.2 code —— 改了就会动到已发布的数（48 个文件）

收录判据：这个文件被编辑后，`REPORT_V2.md` 或 `battery/artifacts/` 里可能有数字改变。

```freeze:code
sha256:fa19d34106854261c17eb7aef1b9ca7a38e2b4b86e8f9a177aa8bd8bf212cdda  battery/.gitattributes
sha256:e6afc029c058ae1fd2087c32b601a88ea055b0a912db9b6ae6b43a1c597ded01  battery/.gitignore
sha256:a95a21199eb2b07d2ef8b504470c68b92c73f792ca5d04c02e0bde137ed6c9cd  battery/__init__.py
sha256:63c89a12119c327acced38083364bfb86d4115c156d539958de890761d29937d  battery/adapters/__init__.py
sha256:f8b9acf2236f70b1637ca58fa7a8a3aa4f59b078410c6e2d7612c54a8eb374d3  battery/adapters/a0.py
sha256:8dbda3718f39618c190d344aeaa7a515335d7ab3268d83392567ec1ce8287f29  battery/adapters/a0_spike.py
sha256:0ea7d8502fc60a062ccd976904ff4be8d2a1e1f6e4e67b6bc6cdc455ab50aeaa  battery/adapters/a2.py
sha256:2ed988947b33f224378be927f9643f3bba5c71d403f7eafbfe62ae1b400e6a36  battery/adapters/ledger_jsonl.py
sha256:540cb3979b32210f63b57e4c144d4c7ac40cda255a474b1d4c4bb07b523284cb  battery/adapters/schema_traces.py
sha256:a940f6fb589873b21a9166281f55562579426865c46b097c1590816b7613da65  battery/adapters/theoria_live.py
sha256:efeee73d8d93a17b16603d262584c6788da86591defa30b5acc282860800a8c9  battery/audit/__init__.py
sha256:628da2d7cee0871faaca4a07fd6be868698df817241fd371af0524fdb31bba99  battery/audit/contrast.py
sha256:6ce5592cc5add65bcbc28e994ad4201d3afac3455a0dd67812dbc21ac045e46d  battery/audit/discriminate.py
sha256:84452e9030d47bb0dfacdd0abb64130b392938e1c041468aba5bb07e0d7c144c  battery/audit/exploits/__init__.py
sha256:43af26980114d98b3f19a578119633525dfd8fc26ecd80c9589f210bee81e240  battery/audit/exploits/economy.py
sha256:dd5cfc8b72201d3bd4b4cedf133ea8780873b80a0fb81ef9c424fad559f1b71e  battery/audit/exploits/exploration_planning.py
sha256:08e39aaa524bf6c617ba8f1fe4dfd6c7e9de8fbe833f4ed393adea65d111111e  battery/audit/exploits/mechanism_epistemic.py
sha256:f73af86bfb49496b053dce065f73a9688b88a2ed2a3faf8b01f8f6b7fc472a83  battery/audit/frontload.py
sha256:0ade8fbb241ff8f6971d73cb3566f0362ef0d960dd80b719999b4acdcbb4e6ad  battery/audit/gaming.py
sha256:eac82aaf1e237c617a87888330d1471f400f0c76068ba0c3f68f84858bf0cbe8  battery/audit/live_arm.py
sha256:284903121b6c9f5aaec919ee9235413017827f9f6b63e9e96be8e08c0083a3f0  battery/audit/live_economy.py
sha256:740eb1601196a37d7a1b439e01faffbe4b538b6cc410be9303637ad16b0d0492  battery/audit/live_tiers.py
sha256:35b43770c4d72b7da6ec72220c0a73cdddd05ad4e101e9da9a642f72e39cd6fd  battery/audit/redundancy.py
sha256:c6715761f70e2ed5eebe8352984a3af0be713ab5cad0970435d329286aefc0c5  battery/audit/stats.py
sha256:96e1e2175c80cafc7ad2c23864243037ac4a0fe638ebb122f0b3e98627008ffd  battery/audit/threat.py
sha256:6c57412f6311abf1a99f508e078caefdfc31287ea062f66b7b2cc6265fb256ba  battery/audit/v9/BLIND_DIGESTS.json
sha256:832753c4aaf3390f0d0818ca3ad1a683c4a46b0729ee608cfd2b58293da42a70  battery/audit/v9/__init__.py
sha256:1c098265a04e4c31a0a31a9ba2d0de6d8ed850423a0c54947e445a2ab058eb73  battery/audit/v9/attack.py
sha256:62ea523b50adf23f3a7aa922f9de41b4bb76b8b4311c566fc0f951df807ec22e  battery/audit/v9/attacks/__init__.py
sha256:bfef834ec7883a5a6b901b2be171f1aebf7189b451198f1ba9e66b410a5eea90  battery/audit/v9/attacks/a1.py
sha256:dba36c6e9bf186c8cdf9301dae5ea389c805deea3a39a956e2c9cf47111e7aa8  battery/audit/v9/attacks/a2.py
sha256:bc8bfb45c070f94d64a0be2881319c9cdf68f46762453c8aef6f4560dda2f02b  battery/audit/v9/attacks/a3.py
sha256:773a1b2864b89b8148a8a36a45488b04189b53001b6c62558b9ba4b382701cbb  battery/audit/v9/attacks/a4.py
sha256:74a575f4596e7a3ce9d3973e80c14c4a37f6d26f3da3bc775b1de1ed205f3a9a  battery/audit/v9/attacks/a5.py
sha256:0254f79de23ce848f343d8099dd344e868b76b6077a48bf016b80c330d11e635  battery/audit/v9/attacks/a6.py
sha256:be1a2ba6bb0e63bf57a91f5f84a75f15e9530f043a73a8652f1ce6b5f8e69f74  battery/audit/v9/attacks/a7_review.py
sha256:c5e1142abc9e71ce31967c631ba2f503fc2aee3f655c332636e87b220228127f  battery/audit/v9/check.py
sha256:bd9a9fcead5cc07336f3a12992228a37be8f39fabd7553b1f3db3e614034e411  battery/audit/v9/make_blind.py
sha256:9634c7016c9b0fc76f0ec72efc18c5c178d1fea06dd531bcd30353d613843cf2  battery/audit/v9/mutants.py
sha256:0cf1a4a74b2e30f1f5b011796472dd497607cd200fb11a6365e022ec2f18f5ab  battery/audit/v9/prereg.py
sha256:8052490d8b7266fcc0e96fa3fd1ae9398d412d604d1757c4dd5204a22ce2ad7d  battery/audit/v9/run.py
sha256:c099deba3d0bc38c1bfeb8d549da4f1611f38c692dc64e5d4b93177797f34b57  battery/audit/v9/verdict.py
sha256:85ffd4087ed9d41e1ddd31510dc3a9a545657afb44709faabab38d33487aa46d  battery/audit/validation.py
sha256:681274d0b0d2392423078bb541219a4c7c63bcb90d5a6801ee507d0d772c0874  battery/guard.py
sha256:0a65812f6bda74c6a692c5fe0402946bd4fa23bf4560c46adc1ee9cbd7a905f0  battery/metrics/__init__.py
sha256:445e7fd1747b9cb19e0fae5defa193143c29dddc7aebdca5acfbbec9876a8df3  battery/metrics/economy.py
sha256:e040bb7377ab5b604e47ae3e70067c1a10bfc0a42950e60784ed6374c687b4ce  battery/metrics/epistemic.py
sha256:023f03ae264c6d9b7748252a48e219b98dfcad0c54f9eb79c5278c640f7e4874  battery/metrics/exploration.py
sha256:00bde2a0de3cd3f2359f737e46150de755b88a838c63307e72040146196ba8d8  battery/metrics/mechanism.py
sha256:5af3b1284a08bdbb9e8e13adaf47fad89553b1411171e67047d63b85d35b597a  battery/metrics/planning.py
sha256:f7793573d7bb509f9b05852a3a38955ac201da3e4c8ceff4589a39decb68a897  battery/model.py
sha256:4551307f5b1a58adb7ec215d513089ba670b1737b81ada5a5863afe796d67343  battery/pytest.ini
sha256:891ce0eb6d2fbd8217064e03fa1cb4d7c821f92f80c2a6c7cfef359b77d159bb  battery/run_battery.py
```

五条不显然的收录，理由写在这里而不是留给日后推断：

* **`audit/exploits/*.py` 不是文档，是代码。** `tier_of()`（`gaming.py:386`）在有
  实跑攻击时优先采信攻击的裁决，所以改一个 exploit 就会把一条指标在主表和参考项
  之间搬家 —— 那是已发布的数。
* **`adapters/*.py` 决定一个 `Run` 里有什么**，因而决定每一个值。K12 的分母
  `beats_required` 就住在适配器里（`adapters/a2.py:540`），不在指标里。
* **`guard.py`** 写出每份产物 provenance 里的 `piles_sha256`，并设定每条 run 的
  `pile`。
* **`.gitattributes`（非 Python）**：收录它是**保守**，不是必需，理由要说准 ——
  `sha256_file()` 先把 CRLF 归一成 LF 再算，所以它改了**并不会**让上面任何一条哈希
  失效（`test_the_digest_survives_a_crlf_checkout` 正是断言这一点）。它被冻是因为
  别的消费者没有这层归一：git diff、别的轨道的工具、以及释出清单里那些**不归一**的
  原始哈希（`release/enumerate.py`），看到的都是落盘字节。它与 `.gitignore` 是这
  47 个里仅有的两个按 §2.2 的收录判据（「改了会动到已发布的数」）不合格的条目，
  如实标注在此。
* **`pytest.ini`（非 Python）**：pytest 的 rootdir 配置。加一行
  `addopts = -k "not ..."` 就能让任何一条会反对的测试根本不跑，而闸门照样报绿 ——
  实测过，`VERIFY PASS` 且 exit 0，唯一的破绽是尾行从 `226 passed` 变成
  `225 passed, 1 deselected`。现在这一行本身被冻，且 `verify.py` 把 `deselected`
  当失败处理。

**同一个常数散在多处，是本冻结真正的暴露面**，逐条哈希盖得住，但改的人必须知道它们
要一起动：`MEDIUM_EFFECT = 0.33` 有两个具名副本（`audit/discriminate.py:58`、
`audit/contrast.py:57`），外加 `audit/stats.py:76` 里一个同值的**裸字面量**——
后者是 Romano 阶梯 small/medium 的分界，改它动的是**标签**（`magnitude()` 的返回串）
而不是判决，耦合是真的，但两者不是同一种东西；`CONTROL_ARMS` 在
`audit/discriminate.py:48` 与 `audit/validation.py:41` 两处；降级规则本身在
`audit/gaming.py` 写了两遍（`tier_of` 与 `_register_tier`），并在
`audit/exploits/__init__.py:116` 被**故意重新实现**了第三遍。

### 2.3 docs —— 渲染器与它渲染出来的两份文档（3 个文件）

```freeze:docs
sha256:c6861db536020501cf7319a399050a5257568cffbba2696504d53e4f0adc652b  battery/METRICS.md
sha256:cb090a6344194c406d18189073a766f5d04fc39865cbac74d3030ccdc2de0d0d  battery/audit/REDUNDANCY.md
sha256:d5a1ab7643eaa577aaf352043986aab52acefc762937bfdb988f50ece9588da2  battery/docs.py
```

**`METRICS.md` 是被冻的，不只是被记录的。** 早先的设计把它当成生成物、只冻
`docs.py`，那是错的：实测过一条攻击，改 `validation_material.json` 的 14 个
`summary` 字段再跑一次 `python -m battery.docs`，`METRICS.md` 的
「Never validated on a control arm」从 **21 改到 7**、14 行的验证材料列改成
「process 1: separates」，而 `test_docs.py` 照样绿（它比的是
`METRICS.md == render()`，而 `render()` 读的正是被改过的产物），闸门 `VERIFY PASS`。
读者是把 `METRICS.md` 当作「这台仪器是什么」来读的，所以它进 gated 桶。

### 2.4 suite —— 整个测试目录（22 个文件）

```freeze:suite
sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  battery/tests/__init__.py
sha256:cca81e2a41a124605a2c6bc1f2f13f8638e899bdedd50025ac397e7f53d0b8dc  battery/tests/fixtures/ledger_fixture.jsonl
sha256:0c9c1400f6a12bac17dde66210808f25d154b572f18931c88e95d4cc75ae594e  battery/tests/make_fixture.py
sha256:9ee055ea6bbfc31aa1836e7cd69eec87e928736ffc8e33b831fb96f430a93488  battery/tests/test_adapter_a0_spike.py
sha256:b5e411b62e7cab867c2bf018016e431bcea30241941a1a12aab05f08f6fdae1a  battery/tests/test_adapter_a2.py
sha256:e31e8a514fd7218d2429ea271d3af1ff7fa07db892fe5e8ef4760b30f078f75a  battery/tests/test_adapter_schema_traces.py
sha256:cc02391839b6288b1dfd480b218a3d5c1811b00cca46c69ddb6385b588b455bd  battery/tests/test_adapters.py
sha256:08cf804a6cb50d84fb7b24d1aa3f6faca6aa3291727453dae50a265dcb40fca1  battery/tests/test_determinism.py
sha256:b12bdb824280d7c6a9815732d70b10c974266df6d67bb644ac98ae51f76c5858  battery/tests/test_discriminate_arms.py
sha256:a5714be4319b4342699b9b5be5f79874e6858f9e30dd55f53524fb9ddec35b64  battery/tests/test_docs.py
sha256:acff06624ab89bb455834b8bf260f2e2cd7b8a9891d0398c20ac9966e3964408  battery/tests/test_exploits_economy.py
sha256:051709eb517f44fe3b89a9836fa4cee2885cf4d1b27a1bc381e5f453ec6200cf  battery/tests/test_exploits_exploration_planning.py
sha256:e7e4799ef6dbeb96271b46fa819cc7ebb5efd7fe6089d8e49fda1eaa6f2d7d3a  battery/tests/test_exploits_mechanism_epistemic.py
sha256:5b17a09cba2ffb176698dcbffad3a58b7c31c2b31562be22350d6dc8e2d8c793  battery/tests/test_freeze.py
sha256:9c9d32c97323d05e714477bc733886f688cf41db115b448f16c0ae32c6b24215  battery/tests/test_guard.py
sha256:4c2d99c7b111afe6aa669bc44596c8cce59c33d7c8f2a4abb006f8d93090515a  battery/tests/test_live_economy.py
sha256:74b8b440da5947f2b128d6746d08527ee9449176df27402ec3eeb8885c6e6831  battery/tests/test_live_tiers.py
sha256:a4d1324c3ec79877b5dd7c1ba8d125880ba2d7cbcdd9c23a1f24daceb30d7085  battery/tests/test_metrics.py
sha256:9f73b2e81991b5f8330c3c0c32d781a7e16c54bdf61f51799ff5d7bfe4e511e4  battery/tests/test_theoria_live.py
sha256:ef17a8811a2d5d71490a2d9157c14e012596cca84e98c0724e090e13446ff63c  battery/tests/test_threat_and_frontload.py
sha256:31a4c70a2e1647ec94fdcd08620e5972a9904528c1fe5f9c4c00e49b67d1966b  battery/tests/test_turn_axis.py
sha256:ca5b597ca953a268d02006df377ceb60da734a2a0c77bb9f8c779868f295950c  battery/tests/test_v9_blinding.py
sha256:c6c2b2ee23f28a5ed063cfdeddbe36c3e40590e8beaedebc3be91ba9ffc2f890  battery/tests/test_v9_defences.py
sha256:e771bb2b9d9dbe233302f4eed29a67afdc8dc577c87410cf967e8d488f091c08  battery/tests/test_v9_prereg.py
sha256:0afa70ccd9884a5ad838f1025119ef0aa8aac2b5b7ca0fee33c508dbfc435a32  battery/tests/test_v9_verdict_rule.py
sha256:790102a0380ef449bfaf273fa6fa3b74f61d4c1045f286999c0a143df7beb7f5  battery/tests/test_verify_separation_claim.py
```

**整个测试目录被冻，因为测试是这道闸的一半。** `verify.py` 跑冻结检查**和** pytest；
一套可以随便改的测试，就是一套可以被改到不再反对的测试。实测过：加一个 6 行的
`tests/conftest.py` 把 `battery.docs.render` 重绑成「读committed 的文件」，再手改
`METRICS.md` 把主表写成 12 条，`VERIFY PASS`、exit 0。此外，封存堆护栏的实际保护
（`test_guard.py` 里那五条断言）也住在这个目录里 —— 见 2.7。

代价如实说：**以后每加一个测试都要走一次版本升级**。这是有意收的价，不是疏忽。

### 2.5 freeze —— 冻结机制自身（2 个文件）

```freeze:freeze
sha256:8844d38021a59acc74f32c9e4fa71c2a38d947da2ffd554f1d54632905049efc  battery/freeze.py
sha256:02c1b68e5496f45004b87b115f9232cd621b922c246aad6fa1bb8d30cae7336b  battery/verify.py
```

收录它们，是为了让「悄悄把检查放松」这件事和「改一条指标」一样在 diff 里显形。
**这一条有一个逃不掉的边界，写在 §8.2。**

### 2.6 readings —— 记录、报告漂移、但**不作闸门**（8 份产物）

```freeze:readings
sha256:c851d749426b4a6f9a45c55a94ee39bb0f6e7002d05902b4c7baf38552f92ae0  battery/artifacts/arm_contrast.json
sha256:205d2a6cb9e8f0601d495bfc8a715048d35f5ac0d67c6f18d593d1c9d5123af6  battery/artifacts/capability_spectrum.json
sha256:8d8c7896a375239b701d323c7e312890caffaab03c1805a761300196b0cff8d3  battery/artifacts/discrimination.json
sha256:1e4f5f88e7db52a4d4bb0a2d1b92470594418ac0371ff3b40b540c3323548dbe  battery/artifacts/discrimination_arms.json
sha256:191c0ee8cf2c796a8f739f506dee52840bf2be02394be40a16a17e6ce0a07cce  battery/artifacts/gaming_audit.json
sha256:5518fe8a13e9c04ff0a84140a8ccfa1e799a3254410062640933fd9f11b612a6  battery/artifacts/redundancy.json
sha256:06313f87c8d6ebbee8dff2398ef48a625f378234f4aa71c19da1e79138822c38  battery/artifacts/validation_material.json
sha256:6deadace384a00848a945f226958f6db85ae8197ef1fb7cd1c2a1836d0b1406f  battery/artifacts_live/frontload_e2l.json
sha256:9ff3c5e78b7bd67cd6db8fb2dce5ae0fe852ce38e52ca9a2509f95fc1e0738c5  battery/artifacts_live/gaming_audit.live.json
sha256:a6d2602714f630b6a36ab7fed249c61637baac7f8d36979a0907707b304b5d3b  battery/artifacts_live/live_arm_readings.json
sha256:fa23ad802df8b883e3e81184d274b0013ad1d0e4e2482d921140c59ac38055dc  battery/artifacts_live/live_economy.json
sha256:3182b32b5a033137db3022ec34bac236dfec31922179ede3d9a3e26e0df7ae94  battery/artifacts_live/threat_model.json
```

产物是**读数**：Phase 4 的全部意义就是让电池去读它没读过的输入，因此拿产物当闸门会
按构造失败。但沉默也不对 —— 早先的设计连记录都不查，一个已发布的指标值是**免费**
可改的（实测：`capability_spectrum.json` 里 K1 从 `0.987288136` 改成
`0.499999999`，`VERIFY PASS`、exit 0）。现在的口径：`verify.py` 逐份比对并**报出
漂移，仍然 exit 0**：

```
note  readings: 1 of 7 artefacts differ from BATTERY_V1.md — battery/artifacts/gaming_audit.json
      Not a failure: artefacts are readings, and a recompute is supposed to
      change them. Record the new values in a new freeze version before
      publishing them.
```

### 2.7 cut —— 切堆（在 `battery/` 之外，但照冻不误）

```
cut-sha256: 3feca53e5ede695cfa46ae994cb95fd6b43abb9d97295e8c87e6302b41bbc19a
```

`arc-recon/data/piles.json` 不在本领地，但它不是读数，是**契约**：`CLAUDE.md` 公布
这个摘要，而开跑之后改切堆是事故，必须按事故登记。

**它自带的 `sha256` 字段挡不住任何人**：`guard.canonical_digest()` 是拿文档自己算的，
所以把一局从封存堆挪进开发堆、再把 `sha256` 字段重写一遍，`guard` 会干干净净地加载
（实测：`n_sealed` 20、`classify("bp35-0a0ad940") == "dev"`，而这套 provenance 会
跟着进每一份产物）。唯一能看见它的是**一个记在别处的期望值** —— 就是上面这一行，
住在被冻的 `battery/freeze.py` 的 `CUT_DIGEST` 里。

（单独改切堆而不动别的，`test_guard.py` 的五条断言也会抓住它；但那些断言在冻结前是
不受保护的文件，所以 2.4 与 2.7 是同一件事的两半。）

### 2.8 记录本身

`battery/BATTERY_V1.md`（本文件）**不哈希自己**。它的完整性由两件东西保证：它就是
记录的唯一副本（`freeze.py` 从这份文件里解析期望值，没有第二处真值），以及 git 历史。

---

## 3. 逐指标方向预测（工序 2）

### 3.1 快照入册

`Theoria.md:326`（工序 2）：*每个入册指标先写下三臂的方向性预测,预测先于回算。*
`battery/PREDICTIONS.md:5-7` 自己声明的纪律：

> **This file is append-only from the commit that introduces it.** A prediction
> that can be edited after the fact is not a prediction. Corrections go in a new
> dated section at the bottom, with the original left standing and wrong.

冻结即把当前快照哈希入册：

```freeze:prereg
sha256:b6050f7a47fdcd8a7c6c96fa1d238791dfd0d20f51de50b042e2082b5abd4085  battery/PREDICTIONS.md
prefix-bytes: 41355
prefix-sha256: sha256:b6050f7a47fdcd8a7c6c96fa1d238791dfd0d20f51de50b042e2082b5abd4085
```

**两个哈希，因为两种破法不是同一件事**（`battery/freeze.py` 的 `check()`）：

* `prefix-sha256` —— 冻结时的前 35087 字节（LF 计）必须逐字节不变。改动它 = 事后
  改预测，是预注册唯一存在意义所要防的那件事，直接判失败。
* `sha256` —— 全文哈希。前缀完好但全文变了 = 冻结之后**追加**了新预测。这是正当的
  工作、不正当的冻结：在仪器冻结之后写下的预测，需要一个记录它何时到达的新冻结版本
  （`BATTERY_V2.md`），不能靠悄悄变长的同一份文件。

### 3.2 append-only 到目前为止是真的成立的，而且是可机械核验的

`git log --numstat -- battery/PREDICTIONS.md`：四次提交，**每一次都是纯增加，删除
行数为 0**。

| commit | 增 / 删 | 批次 |
|---|---|---|
| `50d144c` | 127 / 0 | v0（25 条方向预测，三臂） |
| `104908c` | 113 / 0 | v1（新增 9 条指标，臂扩到 5 条） |
| `19eafb2` | 149 / 0 | v2（不新增指标；为全部 38 条写 CC vs Schema 方向预测） |
| `58e5f6b` | 119 / 0 | v2.1（四道防御的 tier/值预测，写在实现之前） |

127+113+149+119 = 508 = 当前行数。**没有任何一行被删过或改写过。**

在此之前，这条纪律的保证**只来自 git 历史**：仓库里没有任何机制核验它，
`tests/test_docs.py:30` 只检查文件存在、提到五个族名、且含 `"Seal declaration"`
（`:38-39`），不查内容、不查哈希、不查 append-only。本冻结引入的
`prefix-sha256` 是第一个把它变成可执行检查的东西。

### 3.3 预测的诚实度：11 条是后见，27 条是盲的

`STATUS.md` 的头号弱点 W-1 是「指标定义与预测出自同一人」。`PREDICTIONS.md` 用
`[seen]` 标记把这条弱点逐行摊开：写预测之前侦察报告已经把实际数值报上来的那些行，
在它被读出的那条臂上是**后见**，不是预测。

| 批次 | `[seen]` 的指标 | 条数 |
|---|---|---|
| v0 | K1, K2, K7, K8（均只在 A0 上） | 4 |
| v1 | E6, M4, M5, M6, K12, K13, K14 | 7 |
| v2 / v2.1 | 无行级标记；改为在封条里声明两处文件级泄漏 | 0 |
| **合计** | | **11 条 `[seen]` / 27 条盲** |

`[seen]` 是**按臂**的，不是全局的：一条指标可以在 A0 上是后见、在别的臂上仍是盲的。

另有 4 条 —— **X5、P5、E1、K11** —— 在 **v0 和 v1 里都没有方向预测**（v0 登记 25 条、
v1 再登记 9 条，并集 34 条，缺的正是这四条），四条都是 `neutral` 诊断项。其中
X5（`:332`）、P5（`:343`）、E1（`:354`）在 v2 各自有一行「not ranked」；**K11 连
自己的一行都没有**，只被 `:367` 那条「K1…K14 全 14 条在两条对照臂上都
`not-applicable`」的整族行覆盖，而那是**可算性预测，不是不排序登记**。

所以准确的计法是：38 条中 34 条有臂序预注册；v2 的**逐条**行只有 18 行
（X1–X6、P1–P5、E1–E7）—— 这正是 `REPORT_V2.md` 的 7/18 与 11/18 的分母；其余按族
整行覆盖。

### 3.4 已结算的预测

| 批次 | 结算处 | 结果 |
|---|---|---|
| v0 | 无合并记分板；`REPORT_V0/V1.md` 散在正文里结算 | 未计分 |
| v1 | `REPORT_V1.md`「The pre-registration scoreboard」 | X6 证伪；E7 在引入它的同一次回算里被去冗余否掉；K14 在一条臂上证伪；K13 命中「且只是刚刚」；E6/M4/M5/M6/K12 如注册 |
| v2 | `REPORT_V2.md:111-149` | **严格计分 7/18 命中**；按注册时写下的经济族条件计分则 11/18。**两个数都公布**。五条行为族失手（X1、X3、X4、P2、P3）且**全部朝同一个方向** |
| v2.1 | `REPORT_V2.md:334-342` | 四条里三条按预注册翻转。主表 6→9 **数目命中、成员未中**（预测 P4/K2/K12 回归，实际 P4/K12/**E2** 回归） |

两条最该被引用的失败：**X3 在指定梯度上反着分**（|δ|=0.562，探索族的招牌指标），
以及 **K2 的防御以「defence theatre」形态失败** —— 而这个失败形态是 v2.1 封条在
写防御之前就预先点名的。

---

## 4. 抗游戏审计结论（工序 4）

### 4.1 规则（三条子句，`METRICS.md` 只写了第一条）

`Theoria.md:328`（逐字，含原文的 ASCII 标点）：

> **抗游戏审计**:逐指标写下"怎么刷它",判断各臂是否可能无意中优化它;刷得动又防不住的,降级为参考项,不入主表。

产物 `gaming_audit.json` 自己发布的规则串，是三条子句里最诚实的表述：

> `accidental and not defended -> reference; else main. Where an executed
> exploit exists its fields decide, because the prose register's booleans are
> unfalsifiable as written.`

机械实现分三处，缺一不可：

1. **散文规则** —— `audit/gaming.py:389-394`：`accidental and not defended →
   reference`，未登记即未审计即不入主表。
2. **实跑攻击优先** —— `audit/gaming.py:386-388`：有 demonstrated exploit 时，
   直接采信它的 `proposed_tier`，短路第 1 条。
3. **`succeeded` 闸** —— `audit/exploits/__init__.py:116-121`：攻击打不中（或电池
   已学会拒绝它）就不降级任何东西，不管散文猜过什么。`__post_init__` 每次都重算
   `succeeded`，所以 exploit 是活的回归测试，不是记录。

**冻结时，第 1 条对 38 条指标一条都没生效**（`n_demonstrated = 38`,
`n_prose_only = 0`）：所有 tier 都是第 2+3 条判的。`METRICS.md:14-15` 转述了第 1 条
（转述，非逐字）而只字未提第 2、3 条 —— 而 P4/K12/E2 之所以在主表，靠的正是第 3 条。
见第 7 节 W-C/W-D/W-K。

### 4.2 裁决

* **主表 9 条**：`E2`, `E3`, `K7`, `K11`, `K12`, `M3`, `M6`, `P3`, `P4`
* **参考项 29 条**：其余全部
* **攻击规模**：38 条指标、**39 个 exploit 对象**（E2 有两个：长度攻击与集中攻击；
  v2 时是 38 个，v2.1 给 E2 加了第二个）、**35 个当场打中**、17 条与散文登记相矛盾、
  **10 条纯靠实跑攻击降级**（`E1, E6, K10, K2, M1, M4, P2, P5, X3, X5`）。
* **可重跑**：三条路都在 —— `python -c "from battery.audit.gaming import audit;
  audit()"`（不落盘）、每次回算写出的 `artifacts/gaming_audit.json`、以及
  `battery/tests/` 里 67 个 exploit 测试。**审计不是一次性文档。**

主表这个 9 是走了 **19 → 6 → 9** 三步来的，不是一次算出来的：散文登记单独作用时是
19 条；38 个 exploit 实跑后砍到 6 条；v2.1 四道防御之后 P4、K12、E2 回归成 9 条。

### 4.3 两条必须随裁决一起引用的话

**其一，K2 的防御失败，且是以预先点名的形态失败的。** v2.1 要求 held-out 集声明
抽样框，而攻击方写一句话（*"the single pair we withheld after checking that the
manual already got it right"*）就满足了它，K2 仍然 1.000，仍然 `reference`。

**其二，E2 回到主表是机械规则的输出，不是安全证明。** 它是电池唯一拥有的 Phase 4
主终点（第 1.2 节）。`REPORT_V2.md:382-384` 拒绝手工推翻这个结果，并把它登记成警告
而不是放行 —— 那句话应当逐字进入任何引用 E2 的地方：

> A Phase 4 primary endpoint that is reachable at 0.993 without understanding
> anything is not safe merely because reaching it takes intent.

**但 E2 走到 `main` 的实际路径与报告叙述的不是同一条，这一条必须写下来**（W-K）。
`REPORT_V2.md` 讲的故事是「长度假象被插值关上，活下来的集中攻击被判非无意，于是升回
主表」。代码里发生的是：E2 有两个 exploit，`collect()` 在两者都不提议降级时按
**claim 文本的字典序**破平，返回的是那个**已经打不中的长度攻击**
（`succeeded = False`），于是 `tier_of("E2")` 走的是
`exploits/__init__.py:116-120` 的「攻击没打中 → main」那一支 ——
**0.993 那条集中攻击从头到尾没有被咨询过**。

两条路径碰巧都给出 `main`（集中攻击被判非无意，真去问它也是 `main`），所以 tier 是
over-determined，结论不变。但**产物本身佐证不了报告的叙述**：
`artifacts/gaming_audit.json` 的 E2 行发布的是那个死掉的长度攻击
（`claim` 写的是 *"a 0% lift bought by `ceil(n/4)`"*，`succeeded: false`），而
**字符串 `0.993` 在整份产物里一次都不出现**。引用 E2 的警告时，出处要写
`REPORT_V2.md`，不能写 `gaming_audit.json` —— 后者没有这个数。

---

## 5. 另外两道工序（`Theoria.md:330` 要，工单没点名）

工单只点了「定义 + 代码指纹 + 方向预测 + 抗游戏审计」四件，对应清单第 8 项的措辞。
但 `Theoria.md:330` 对电池 v1 的措辞是「定义 + 计算代码 + **逐指标区分力**与方向
预测」，`:327` 另有工序 3。两道一并冻在这里，缺一就不是电池 v1。

### 5.1 工序 1 · 区分力

结论已在第 0.2 节：**0 条通过**。口径记录如下，产物
`artifacts/discrimination_arms.json`（主口径）与 `artifacts/discrimination.json`
（次口径）：

| | |
|---|---|
| 梯度（主） | `bare_cc`（弱）vs `schema_repro`（强），**逐局配对**，`Theoria.md` 指定 |
| 对照臂 run 数 | 88 |
| 功效上限 | 双侧符号检验需 6 局非平局配对才可能到 p<0.05；试点只有 4 局 |
| 梯度（次） | `bare_cc` 内部的模型阶梯（haiku-4.5 < sonnet-5 < opus-5），**固定 harness 只变模型** |
| 两口径的关系 | 混杂方向不同，**两者不一致是信息，不是噪声** |

已登记的混杂（`discrimination_arms.json.confounds`，逐条随产物走）：Schema 一侧是
上游 agent 跑在上游基础设施上，**臂与 harness 是捆在一起的** —— 分开了的指标同时
分开了能力与管路；Schema 一侧是上游**释出**材料而非我们的复现，复现分数一栏永远空着；
上游未声明许可。

### 5.2 工序 3 · 去冗余

产物 `artifacts/redundancy.json` / `audit/REDUNDANCY.md`：

| | |
|---|---|
| 方法 | Spearman 秩相关；单连接聚类，阈值 `|ρ| ≥ 0.9`；构造上传递，因此结果不依赖指标到达顺序 |
| 阈值 / 最小共享 run | `THRESHOLD = 0.9`（`audit/redundancy.py:23`）、`MIN_SHARED = 4`（`:24`） |
| 指标对 | 703 对中只有 **257 对**共享了足够的 run 能算相关；446 对**根本算不了** |
| 结果 | 38 条 → **32 个簇、33 个代表**，淘汰 5 条 |
| 淘汰 | `E7`→E4（ρ=0.985）、`K14`→K5（ρ=−1.0）、`K7`→K5（ρ=1.0）、`K8`→K10（ρ=−0.968）、`X4`→X1（ρ=0.903） |
| 跨族簇 | 一个：`K6, X1, X4` |

**38 − 32 = 6 而淘汰只有 5，不是算错**：代表是**按族**留的，所以 33 个代表落在
32 个簇上 —— 唯一的跨族簇 `[K6, X1, X4]` 留了两个代表（K6 给认识族、X1 给探索族）。
展开：四个多成员簇 `{E4,E7}` `{K10,K8}` `{K5,K7,K14}` `{K6,X1,X4}` 共 10 条，留 5 个
代表（E4、K10、K5、K6、X1）、淘汰 5 条；其余 28 条各自成簇，28 + 4 = 32。

产物自带的免责，必须一起引用：*A cluster count near the metric count reflects thin
data, not twenty independent findings.* —— 32 个簇不是 32 个独立发现，是数据太薄。

**淘汰不是删除**：被代表的指标照样计算、照样报告、照样进相关矩阵，只是不再单独算作
一个发现。`K7` 同时是被淘汰项与主表项，两者不矛盾（前者是工序 3 的口径，后者是
工序 4 的）。

---

## 6. 冻了什么、没冻什么

### 6.1 没冻输入，这是有意的

电池是**被动仪器**：它读账本，不产生账本。Phase 4 的全部意义是把它指向它从未读过的
输入（封存堆）。**因此输入哈希只作记录，不作闸门** —— 拿它当闸门，第一次回算封存堆
就会按构造失败。

冻结时刻的输入读数，登记在此（不进 `verify` 的判据）：

| 输入 | sha256（前 16 位） | 状态 |
|---|---|---|
| `arc-recon/data/piles.json` | `d3140eff4889095f…`（**文件字节**摘要） | 已跟踪。**注意别和 `3feca53e…` 搞混**：后者是 §2.7 冻的**规范摘要**（去掉 `sha256` 字段后对载荷算），是 `CLAUDE.md`、`guard.py:72` 与每份产物 provenance 用的那一个。两个都对，量的是两样东西 |
| `baseline-arms/ledger.jsonl` | `0eef1cdf06795808…` | 已跟踪，**append-only，别的会话可能正在写** |
| `baseline-arms/out/campaign_cells.jsonl` | `816c627b16e7eb2f…` | 已跟踪，**但 run_battery 从不摘要它**，而它决定 `Run.campaign` |
| `baseline-arms/schema_traces/MANIFEST.json` | `817545a1cf382175…` | 已跟踪；**载荷本身 gitignored，在任何 worktree 里都不存在** |
| `baseline-arms/out/shards/ledger.*.jsonl` | 10 个分片 | glob 取，**上界不封**：主工作树里现有 4 个未跟踪分片，本 worktree 里没有 |
| `cold-start-a0/` · `a0-spike/` · `cold-start-a2/` | 116 / 38 / 83 个已跟踪文件 | 三个 bundle 里 `run_battery` 只摘要了 A0 的 `raw_trace.jsonl` 一个 |

**据此，一个如实的说法是：本冻结钉住了仪器，没有钉住读数。** 读数由
`capability_spectrum.json` 里的 provenance 块自带的摘要各自钉，而那套摘要有上表所列
的窟窿（W-F）。

**一条必须补的更正：`METRICS.md` 是混合文档，「仪器 / 读数」这条线不是沿文件边界
走的。** 实测确认了两件事：

* `gaming_audit.json` 的 tier 与 `METRICS.md` 的主表成员**与输入无关** —— exploit
  在冻结代码里构造合成 `Run`，不读任何文件；把账本截断到 300 行再回算，两者逐字节
  不变。所以把 tier 当作仪器属性是对的。
* 但 `METRICS.md` 的**验证材料列**与那句
  `**Never validated on a control arm (N):**` 是从 `validation_material.json`
  读回来的 —— 把账本截断到 300 行改动了 17 条指标的 summary，截断到 60 行把那个
  **21 变成了 24**。

所以本记录 W-H 里那句「21 条指标从未在任何对照臂上算出过」**是一个读数，不是仪器
属性**。Phase 4 对封存堆回算时，这个数会变，`METRICS.md` 会被重写 —— 而它是被
gated 的（§2.3），因此那次重写会**如实地把闸门顶失败**，逼出一个新冻结版本。这正是
想要的行为，写在这里以免被当成故障。

### 6.2 产物也只作记录

冻结时刻的七份产物（`python -m battery.run_battery` 的输出）的逐份 sha256 见 §2.6
的 `freeze:readings` 块。它们被记录、漂移被报告、但**不作闸门**，理由同 §6.1。

### 6.3 确定性

电池**由构造确定，而不是由 seed 确定**：生产管线里没有 `random`，没有墙钟
（`test_artefacts_carry_no_wall_clock`），JSON 一律 `sort_keys=True` + `newline="\n"`，
`PRECISION = 9`，`evaluate` 按 `sorted(REGISTRY)` 走，曲线拟合与统计量都是手写的 ——
`audit/stats.py:3-4` 的原话是 *"so it produces the same bits on every machine"*。
仓库里唯一的 seed 在测试夹具里。

主张的**实际覆盖面比 `REPORT_V2.md` 说的窄**，见 W-G。

---

## 7. 已知薄弱处（先自己说）

**W-A · 没有一条指标通过工序 1。** 第 0.2 节。按 `Theoria.md:325` 的话，这套指标目前
「没资格测未知差异」。功效缺口是 4 局对 6 局，不是靠改指标能补的，只能靠更多配对局。

**W-B · 电池唯一拥有的主终点 E2，是靠「攻击非无意」这条判据升回主表的。** 第 4.3 节。
0.993 的前载指数在不理解任何东西的情况下可达；规则说它安全，报告说它是警告。冻结
两者都记，不做调和。

**W-C · `METRICS.md` 自相矛盾，共 10 条指标。** tier 那一列由 `tier_of()`（实跑攻击）
渲染，下方「How each would be gamed」散文块由 `GAMING_REGISTER`（散文布尔）渲染，
两者对 X3、X5、P2、P5、E1、E6、M1、M4、K2、K10 给出不同答案。最难看的是 K10：散文
写着 *"it is why this metric stays in the main table"*，而同一份文件把它列在
Reference 里。`gaming.py:383-384` 说这是有意让分歧留在明面上，但渲染出来的效果读起来像
错误而不像登记在案的分歧。**冻结记录如实继承这个缺陷，不就地修**（修它要改 `docs.py`
或 `gaming.py`，那就是新版本的事）。

**W-D · `Exploit.defended` 对 P4/K12/E2 三条已经过期。** 三道防御都实现了，三个
exploit 对象仍写着 `defended=False`，只有 `succeeded` 翻了。结果碰巧是对的（第 3 条
子句先生效），但**任何逐条引用 `defended` 字段的表格都会引到一个代码已不再维护的
字段**。本记录因此不发布该字段。

**W-E · `REPORT_V2.md:204-205` 的工序 4 数字是 v2.1 之前的，现在三个都不对。**
那里写「38 exploits, 37 land … 13 metrics demoted by demonstration」；冻结时实测是
**39 / 35 / 10**。报告后半段的 v2.1 附录记了变化，前半段的数字没加注。引用请以本节
4.2 为准。

**W-F · 输入会漂，即使代码不漂。** 第 6.1 节：三个 bundle 未被摘要、
`campaign_cells.jsonl` 未被摘要、`$THEORIA_BASELINE_ARMS` 解析出的根路径完全不进
provenance、分片 glob 上界不封（主工作树与本 worktree 因此会读到不同的 run 集合）、
Schema 载荷在任何 worktree 里都不存在。

**W-G · 确定性主张的覆盖面比报告写的窄。** `test_determinism.py` 只逐字节比对
**七份产物里的四份**（`capability_spectrum` / `discrimination` / `redundancy` /
`gaming_audit`），且是在 `--a0 none` 下跑的 —— 三个 bundle 适配器与 Schema 适配器
**完全在该测试覆盖之外**。`REPORT_V2.md:5` 与 `:418` 说的「全部 7 份逐字节一致」是
人工验的一次，不是自动化保证的。

**W-H · 21 条指标从未在任何对照臂上算出过一次**（整个认识族、整个机制族、加 P4）。
对它们，工序 1 是**无法执行**，不是执行了没过。

**W-I · 定义、预测、防御、攻击全部出自同一只手。** 11 条 `[seen]`（第 3.3 节）是这条
弱点里可量化的那部分；不可量化的那部分是：写攻击的人和写防御的人是同一个，而 K2 的
「defence theatre」正说明这种自评会失败到什么程度 —— 也说明它至少会如实登记失败。

**W-J · 主终点三缺二，其中一个连打分器都没有。** 第 1.2 节：判决题准确率在考卷轨道，
需要清单上的另一项来盖；**U3 达成率全仓没有任何实现**，所以它不是「被别的项盖住了」，
而是**清单上任何一项都盖不住它**。Phase 4 若照现状开跑，三个主终点里有一个既没有
实现也没有冻结。

**W-K · E2 走到主表的实际代码路径，与报告叙述的那条不是同一条。** 第 4.3 节：
`collect()` 在两个 exploit 都不提议降级时按 claim 文本字典序破平，返回了那个**已经
打不中**的长度攻击，于是 `tier_of` 走「攻击没打中 → main」；0.993 那条集中攻击**从未
被咨询**。两条路径同给 `main`，所以 tier 没错，但 `collect()` 的 docstring 承诺的是
「the worst surviving case」，这里它没有兑现 —— 而这正是 `REPORT_V2.md:390-395`
以为已经修好的那个机制。**本记录不就地修它**（改 `collect()` 会重算 tier，那是
`BATTERY_V2` 的事），只把它登记下来，并把引用出处从 `gaming_audit.json` 改指
`REPORT_V2.md`：产物里没有 0.993 这个数。

---

## 8. 改动纪律 —— 冻结之后怎么动

**不得就地改。** 任何一条落在第 2 节四个块里的文件被编辑，`python -m battery.verify`
会失败，并给出这条信息：

> A frozen file has been edited in place. The numbers published under
> BATTERY_V1 were produced by the old file and cannot be compared with numbers
> produced by the new one — register a new freeze version (BATTERY_V2.md)
> instead of editing this one.

正确的流程是：

1. 改代码（或追加预测）。
2. 新建 `battery/BATTERY_V2.md`，说明**改了什么、为什么、预期影响哪些已发布的数**。
3. `python -m battery.freeze` 重新渲染四个块，贴进新记录。
4. `battery/freeze.py` 的 `RECORD` 指向新文件；**`BATTERY_V1.md` 原样留着**，不删
   不改 —— 在 `BATTERY_V1` 下发表过的数字，其口径必须永远可复原。

这与 `proxy/scoring/frozen.json` 的纪律是同一条（新 `scorer_id`，不改旧条目），也与
`PREDICTIONS.md` 的 append-only 是同一条。

### 8.1 闸门

`battery/verify.py` 是本领地的 verify 闸（`monitor/gates.py` 认 `verify.py` 为
canonical，没有就退化成裸 pytest；本领地此前没有，因此退化过）。它跑三道：

```bash
python -m battery.verify   # 1) 冻结记录 2) battery/tests 3) 产物漂移（只报不拦）
```

第 2 道不只看退出码：**被 deselect 或没被收集的测试和失败的测试一样处理**（尾行出现
`deselected`、或通过数掉到 200 以下，都判失败）。理由是实测的破法里最便宜的一条不是
改断言，是加一行 `addopts`。

`battery/tests/test_freeze.py` 是这道闸的**负样本**，17 个测试里 13 个是负样本，
逐个制造一种破法并断言检查确实报出对应的那一条：就地改指标 / 加未登记的指标模块 /
删除冻结文件 / 改 `METRICS.md` / 加 `tests/conftest.py` / 改 `pytest.ini` / 改一条
既有测试 / 篡改切堆并重新自封 / 记录里重复一行摘要 / 记录里重复一个块 / 重复
`prefix-bytes` / 事后改写预测（等长改写）/ 冻结后追加预测 / 截断预注册。另有一条
反向断言：**改产物只报不拦**。

**没被见过报警的闸门等于注释** —— 这是 S13 的教训。这里的每一条负样本都不是想出来
的，是先被打穿、后被补上的：交付前专门派了一个对抗性 subagent，目标是「改一个已发布
的数而让 `python -m battery.verify` 仍然 exit 0」，它成功了六次。上面 §2.3–§2.7 的
桶划分与本节的 deselect 检查，就是那六次的修补。

### 8.2 这道闸证不到的那件事（边界，如实写）

**`verify.py` 证明的是「在 `freeze.py` 诚实的前提下，树与记录相符」，而这个前提无法
在本领地内部建立。** 攻击者把 `check()` 改成永远返回空列表，冻结那一道就会报绿 ——
它是在进程内用攻击者自己那份 `freeze.py` 跑的。

现状下这仍然会被抓住，但只被一样东西抓住：`test_freeze.py` 的负样本会集体失败、
退出码 1。而要让那些负样本闭嘴，就得再改 `pytest.ini` 或加 `conftest.py` —— 两者
现在都被冻了，可一旦 `freeze.py` 已经被中和，冻结检查本身也已经死了，所以那层保护
在这个特定情形下是空的。**结论：对纯恶意，本领地内部没有解。**

正解在领地之外，记在这里供冻结清单收口时采纳：把 `battery/freeze.py` 的摘要记到它
管不着的地方 —— `monitor/gates.py` 的配置，或 Phase 4 释出清单 —— 由外部闸门在调用
`battery.verify` 之前先核一次；或者 CI 用 `git show <base_commit>:battery/freeze.py`
跑检查。在那之前，本记录不声称能防住改了 `freeze.py` 的人，只声称能防住改了别处的人。

---

## 9. 出处

| 主张 | 出处 |
|---|---|
| 冻结清单十三项、第 8 项措辞 | `Theoria.md:368` |
| 电池 v1 = 定义 + 计算代码 + 逐指标区分力与方向预测 | `Theoria.md:330` |
| 四道工序 | `Theoria.md:323-328` |
| 主终点限三个、其余标探索性 | `Theoria.md:373` |
| 分不开已知差异的指标没资格测未知差异 | `Theoria.md:325` |
| append-only 预注册纪律 | `battery/PREDICTIONS.md:5-7` |
| 「新版本，不就地改」的可执行先例 | `proxy/scoring/frozen.json`、`proxy/scoring/__init__.py:111` |
| LF 归一哈希口径 | `proxy/scoring/__init__.py:64`（引文 `:71`） |
| 工序 1 的判决词表与 `underpowered` 短路 | `battery/audit/discriminate.py:120-136` |
| 「4 局到不了 p<0.05」的预注册 | `battery/PREDICTIONS.md:385-387` |
| 切堆规范摘要与自校验 | `battery/guard.py:70-110`、`CLAUDE.md` |
| 判决题准确率的实现 | `exam/grading/mark.py:95`（特异度 `:136`） |
| 工序 1 判决与功效 | `battery/artifacts/discrimination_arms.json` |
| 工序 3 聚类 | `battery/artifacts/redundancy.json`、`battery/audit/REDUNDANCY.md` |
| 工序 4 裁决与规则串 | `battery/artifacts/gaming_audit.json`、`battery/audit/gaming.py:375-404` |
| 预注册记分板 | `battery/REPORT_V1.md`、`battery/REPORT_V2.md:111-149, 334-342` |
| E2 警告原句 | `battery/REPORT_V2.md:382-384`（**不在 `gaming_audit.json` 里**，见 W-K） |
| 电池自身的弱点清单 | `battery/STATUS.md`（W-1 … W-11） |

---

## 附：2026-07-31 增补 —— 活层级伴生产物（live tiers companion）

本次增补把 V9 之后的**现行**层级判定落成一份**另开的文件**，正是 `PREREG_V9.md`
§5 的处方（不修改任何已提交产物，冲结论另开文件、冲突留在明面上）执行成代码：

* 新增 `battery/audit/live_tiers.py`（入 `code` 桶）：从 `gaming.tier_of()` 重算
  逐指标现行层级，携带 V9 降级证据（R3：降级要点名 run 和数），并给出与冻结基线
  `battery/artifacts/gaming_audit.json` 的逐条分歧（9 条，冻结 main → 现行
  reference）。产物 `battery/artifacts_live/gaming_audit.live.json`（入
  `readings` 桶）**无时间戳、无绝对路径**，对固定的树逐字节可复现；生成器对解析到
  `battery/artifacts/` 之内的输出路径**直接拒绝**。
* `battery/verify.py` 增第 6 级：伴生产物与进程内重算不一致 → 红；
  `frozen_sha256` 与盘上冻结文件不再相符 → 红（基线被改写是预注册违规）；
  冻结-现行分歧表**只报告、不改 exit code**（它是已披露的永久事实）；分歧存在而
  `STATUS.md` 不再携带那句按冻结文件计数推导出的披露 → 红。
* `battery/tests/test_live_tiers.py`（入 `suite` 桶）：正反两向，负控照
  `test_freeze.py` 的样式逐条见红。

因此 §2.2 由 47 → 48 个文件、§2.4 由 21 → 22 个、§2.6 由 7 → 8 份，相应
`freeze:*` 块按 `python -m battery.freeze` 重渲。**冻结基线本身一个字节未动**
（`gaming_audit.json` 仍是 `191c0ee8cf2c…`）。被编辑的冻结文件只有
`freeze.py`（桶清单扩充）与 `verify.py`（新增一级）——即冻结机制自身；按 §2.5
的口径，机制的改动本就要在 diff 里露面，这一段就是那个露面。

---

## 附：2026-07-31 增补（二）—— 活臂读数伴生产物（live-arm readings companion）

活的 Theoria 臂（`theoria-arm/`，A3 战役）已有**已提交**的 leg 归档
（`theoria-arm/runs/`，proxy 账本方言：`run_start` / `env_step` / `model_call` /
`run_end`，外加 A8 的 `curves.json`、归档代码的 `turn_series.json`、两本书与
certify 记录）。本增补把**冻结的仪器指向这批材料**，走的是本文件上一个增补
（live tiers，2026-07-31）立下的同一条路：新模块、新测试、新 `artifacts_live/`
读数、桶清单扩充、块重渲、注明日期的增补段 —— 被编辑的冻结文件仍然只有
`freeze.py`（桶清单）与 `verify.py`（新增一级），即冻结机制自身。

* 新增 `battery/adapters/theoria_live.py`（入 `code` 桶）：活臂 leg 归档方言的
  提取器。成员资格按内容判定（账本自己的 `run_start` 声明 `arm: theoria` 且
  `spend_gate.campaign` 以 `theoria-arm:A3-campaign` 开头）；mock 上游的 rig leg
  被点名拒绝而不是沉默跳过；零步 leg 按 A8 自己的下限拒绝（成本曲线上的零读作
  「便宜」，不读作「没发生」）；封存堆 id 直接抛异常（`battery.guard`，默认拒绝）。
  turn 与钱的 join **读归档自己的产物**（`turn_series.json` 的 `call_idx`，或
  `curves.json` 的逐 turn 计数在能对账时顺序指派），从不重推 —— E2 的输入不许有
  第二个无标签的定义（A8 RUN_STATE 的原话）。两本书用与 A0/A2 **同一套**读取器
  解析（`parse_dsl` / `parse_playbook` / `parse_word_table_accounts`）。
* 新增 `battery/audit/live_arm.py`（入 `code` 桶）：把注册表 38 条指标全部
  `evaluate` 在活 leg 上，产物 `battery/artifacts_live/live_arm_readings.json`
  （入 `readings` 桶）无时间戳、无绝对路径，对固定的树逐字节可复现，并逐文件
  钉住它读过的输入的 sha256；写进 `battery/artifacts/` 之内的目的地直接拒绝
  （复用 `live_tiers.refuse_frozen_destination`，一个定义）。
* `battery/verify.py` 增第 7 级：伴生产物与进程内重算不一致 → 红；committed 行
  里出现非开发堆的局 → 红（闸门重读产物自己的行，不信任生成器）；认识族或
  经济族一个实测格都没有 → 红（空结果不算过，本闸自己的教条）。
* `battery/tests/test_theoria_live.py`（入 `suite` 桶）：21 条，正反两向，负控
  照 `test_freeze.py` 的样式逐条见红（篡改的伴生产物、封存 id、mock leg、
  零步 leg、冻结目录写入、缺失/坏 JSON 伴生产物）。

**约束（按预注册文本裁定，只测量、不确证）**：`PREDICTIONS.md` 在
`freeze:prereg` 下前缀与全文双重冻结 —— 冻结之后为活臂**新登记**方向预测需要
新冻结版本（§3.1），本增补一个字都没碰它；`PREREG_V9.md` §5 不修改任何已提交
产物，故活臂不并入 `battery/artifacts/` 的七份冻结读数；工序 1 的梯度是
CC vs Schema（`audit/discriminate.py` 的 `CONTROL_ARMS`，冻结代码），活臂不是
对照臂，把它接进 `run_battery.py` 就是就地改「改了就会动到已发布的数」的文件
（§2.2 收录判据）—— 那是 §8 点名的犯规。所以活臂落地为**测量材料**：不结算
任何预测、不动任何 tier、不进任何判别裁决。要把它变成确证材料，走 §8 的
新版本流程（`BATTERY_V2.md`）。

**读数（2026-07-31，4 条活 leg，全部 `g50t-5849a774`，62 个实测格）**：
认识族 11 条有活读数（K1、K3–K11、K14；如 K1 replay 在 r2 上 9/13 = 0.692），
经济族 5 条（E1、E4、E5、E6、E7；E1 在 r2 上 9.556852 USD 真金白银），另有
探索族 6 条（X1–X6）、计划族 4 条（P1–P3、P5）。E2/E3 在现有 leg 长度下
`insufficient-data`（不足 8 turn），机制族结构性 `not-applicable`（活局无
ground truth）—— 都是如实报告，不是缺陷。

因此 §2.2 由 48 → 50 个文件、§2.4 由 22 → 23 个、§2.6 由 8 → 9 份，相应
`freeze:*` 块按 `python -m battery.freeze` 重渲。**冻结基线与七份冻结读数
一个字节未动**（`gaming_audit.json` 仍是 `191c0ee8cf2c…`）。

**Amendment 2026-08-01 (readings refresh, live arm):** `battery/artifacts_live/live_arm_readings.json` re-derived after the r3 leg's harvest entered the archive (a new live run changes the recompute by design; rung 7 catches the stale copy). Blocks re-authored block-by-block via `freeze.render_blocks()` — changed: readings. No frozen code or predictions moved.

**Amendment 2026-08-01 (readings refresh, sk48 leg l1):** the sk48 leg
(`theoria-arm/runs/20260731T1500Z-A3-sk48-carried-l1`) landed on master at
`73760dc8` *after* the 2026-08-01 refresh above, and the readings companion was
not re-derived with it — so `battery` shipped **red on rung 7** on the mainline
until this commit. `battery/artifacts_live/live_arm_readings.json` re-derived
(`python -m battery.audit.live_arm`): 6 live legs, 116 measured cells. Readings
block hash updated in place; **no frozen code, artefact or prediction moved**
(`gaming_audit.json` still `191c0ee8cf2c…`). The staleness is not a defect of
the archive — rung 7 exists to make exactly this visible, and it did.

**Amendment 2026-08-01 (E2L 与威胁模型拆分入册):** 新增六个受冻文件——
`audit/threat.py`、`audit/frontload.py`（code）、
`tests/test_threat_and_frontload.py`（suite）、
`artifacts_live/threat_model.json`、`artifacts_live/frontload_e2l.json`
（readings）、`PREREG_E2L.md`（narrative，其完整性由 commit 祖先关系证明，
见该文件 §0）。因此 `freeze:code` 由 50 → 52 个文件、`freeze:suite`
23 → 24、`freeze:readings` 9 → 11，`freeze:*` 块按
`python -m battery.freeze` 逐块重渲，`freeze.py` 自身的摘要随之更新。
**冻结基线与既有七份冻结读数一个字节未动**（`gaming_audit.json` 仍是
`191c0ee8cf2c…`，切堆摘要仍是 `3feca53e…`）。E2L **未进
`battery.metrics.REGISTRY`**：它没过工序 1，不进回算、不进包络、不进主表。
