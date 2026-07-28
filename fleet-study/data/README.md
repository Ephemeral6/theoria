# fleet-study/data — 一手证据，机器可读

RES-4，2026-07-28/29。S17「抢救性证据固化」的结构化数据层。
**正文只引用，不重抄数字**（工单第 4 条）。

## 现有三份

| 文件 | 行数 | 分组键 | 采法 |
|---|---|---|---|
| `failures.jsonl` | 96 | `class` | 三个只读 subagent 之一扫 349 个提交 + audit/ + inbox/ + 总线 |
| `timeline.jsonl` | 45 | `trigger_kind` | 架构变更，UTC 升序，`2026-07-27T18:13Z` → `2026-07-28T15:06Z` |
| `counterevidence.jsonl` | 43 | `kind` | 反证：装了没用的、担心过没发生的、废弃的、已被抓的过度声称 |

**184 行全部带 `evidence` 引用**（提交 sha 经 `git cat-file` 解析过，文件路径经存在性检查）。

## 失败分类学：给了 4 类，挖出 25 类

工单预设四类。实际落盘 25 个 `class`，其中最大的一类正是本赛道的主题：

| class | n |
|---|---|
| `silent_failure` | **37** |
| `unserialised_shared_resource` | 10 |
| `announcement_vs_fact` | 9 |
| `requirement_cites_nonexistent` | 5 |
| `context_handoff_state_loss` | 5 |
| `one_way_door_no_exit` | 4 |
| `check_with_no_failing_path` | 3 |
| `orphaned_deliverable` | 3 |
| 其余 17 类 | 各 1–2 |

新类里值得单独看的几个（名字本身就是结论）：
`check_with_no_failing_path`（检查没有失败路径）、
`false_positive_fix_blinds_the_check`（修误报把检查修瞎）、
`instrument_blames_its_subject`（仪器怪罪被测对象）、
`unauditable_by_construction`（构造上不可审）、
`rehearsed_with_the_wrong_model`（拿错模型彩排）。

## `assembly.jsonl` 只采到 3 行（部分）

会话内直接量出的一条，是这份记录里最硬的证据之一：

> **RES-4 的 127 行契约里，99 行与 RES-1 逐字节相同（78%），改动 41 行、6 节变 7 节，
> 且 RES-3 与 RES-4 由同一个提交 `6f6b87a` 一次造出。**

也就是「克隆即继承」在文本层面是真的。**但要注意它没有证明什么**：78% 相同
只说明克隆发生了，不说明被继承的四条纪律（总线先行 / 手持 2–3 件 / 扇出硬要求 /
绝不停下）真的被遵守——那是另一次测量，本行没做。热重调（A-03）**完全没量**，
`confidence: low`：契约自己声称「改一个文件全队下轮生效」，那是契约在陈述自己的机制，
不是它奏效的证据。

## 一份还没采（**缺口，不是遗漏**）

`human_actions.jsonl` 的采集器**因会话额度中断而失败**，产出为零。
它承载的是工单第 (4) 条、也是整个论点里最硬的一项：

* **人类动作账**——整段时间里人类实际做了哪些不可自动化的动作，逐条列。
  **「组装权下放的价值就等于这张表有多短」**，所以没有这张表，
  论点就只剩定性叙述。

`assembly.jsonl` 只补到 3 行（见上），其中热重调与「三个标准接口各自被哪次事故
逼出来」两项仍未量。

**没有人类动作账，S17 的论点是没有量化支撑的。** 时间线里已经零散撞到一些
（例如 T-43 记着「用户不得不手动触发两个研究员」、T-23 记着契约上盘热重载
是 2026-07-28T06:12Z `b23c110a`），但那是副产品，不是系统采集。
下一个接手的会话应当**先补这两份**再动正文。

## 采集时撞到的、正在发生的问题

1. **心跳时钟无人校验**：`ops-status/RES-1.json` 写 20:55Z、RES-2/3/4 写 16:0x–16:4xZ，
   而真实 UTC 是 15:47Z——这些时刻还没到；`OPS-R.json` 冻在 06:32Z 九小时。
   我自己前四次心跳也是手打的。已写 `monitor/inbox/20260728T154800Z-RES-4-two-live-silent-failures.md`。
2. **`arc-recon/contamination.py:338`——封存堆审计不可能变红**：
   `return 0 if check["matches"] else 1`，`check` 只是 piles.json 的 sha256；
   `sealed ADDRESSED` 与 `NEEDS ADJUDICATION` 算了、打印了、丢了，
   而 `verify.sh:53` 只读退出码。**CLAUDE.md 称之为「让 Phase 3 诚实」的那条规则，
   其可执行形式在真出事时返回绿。** 属 arc-recon 领地，只上报不动手。
3. **封存堆「零接触」的数字应当换掉**：反证采集器实测
   **18,365 条请求体 / 87 个 JSONL 文件零命中**，比原先流传的 3184 强得多；
   而 3184 实为两个文件的**总行数**（口径错），且随提交漂移（3159/3184/3186）。
   同时「零接触」≠「未污染」：封存宣称集是 19 不是 21，ls20/ft09 已隔离。
4. **`fleet-study` 不在 `ci_merge.KNOWN_DIRS` 里**，任何触及它的分支都会被判
   「unknown territory」拦下。属 monitor 领地，需监控补一行。
