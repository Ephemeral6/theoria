# fleet-study/data — 一手证据，机器可读

S17「舰队航海日志」的结构化数据层。**正文只引用，不重抄数字**（工单第 4 条）。
叙述在 [`../EVIDENCE.md`](../EVIDENCE.md)，写作方针在 [`../IDEA.md`](../IDEA.md)。

| 采集轮 | 日期 | 采集者 | 结果 |
|---|---|---|---|
| 1 | 2026-07-28 | RES-4 | 184 行；会话额度中途死亡，两个缺口未补 |
| 2 | 2026-07-28 | W-1641 | **473 行**；两个缺口补齐，四个头部数字被推翻三个 |

## 七个数据集

| 文件 | 行数 | 主键 | 归并方式 |
|---|---:|---|---|
| `failures.jsonl` | 116 | `F-nn` | 追加 |
| `bus.jsonl` | 111 | `B-nn` | 追加，UTC 升序 |
| `deliveries.jsonl` | 90 | 板条目 slug | **状态表**，逐字段归并（见下） |
| `counterevidence.jsonl` | 57 | `C-nn` | 追加 |
| `timeline.jsonl` | 54 | `T-nn` | 追加，UTC 升序 |
| `human_actions.jsonl` | 26 | `H-nn` | 追加，UTC 升序 |
| `assembly.jsonl` | 19 | `A-nn` | 追加 |
| `census.json` | — | — | 由 `census.py` 重算，**禁止手改** |
| `census-history/` | — | — | 每日快照，供 `census_delta.py` 求增量 |

**全部 473 行都带可解析的 `evidence`**：`git:<sha>` 经 `git cat-file -t` 解析，
`file:<path>` 经存在性检查（工作树或 git 历史）。当前 **0 处无法解析**。

## 每天怎么加一轮

```bash
# 1. 采集：subagent 只写 runs/<UTC>-S17/harvest/，不碰 data/
# 2. 折进来（可重复跑，重跑是空操作）
python fleet-study/merge_harvest.py fleet-study/runs/<UTC>-S17/harvest
# 3. 校验（能变红：--selftest 注入 12 个缺陷）
python fleet-study/verify.py
# 4. 计数：先把旧快照挪进 census-history/，再重算，再求增量
cp fleet-study/data/census.json fleet-study/data/census-history/census.<UTC>.json
python fleet-study/census.py
python fleet-study/census_delta.py
```

**`deliveries.jsonl` 的归并规则值得单独记**，因为改错过一次：它按板条目的 slug
作键，同一个 slug 明天会带着更晚的状态回来（`open` → `claimed` → `done`）。
直接追加会撞 id，直接整行替换会**悄悄丢掉昨天的 `first_claim_utc`**——
而那正是交付账存在的理由。所以按字段归并：今天观测到的值胜出，
今天填 null 的字段保留昨天的，列表求并集。`merge_harvest.py` 的 docstring 是权威。

## 必须和数字一起读的四条

第 2 轮派了一个 subagent **专职推翻**本数据集自己的头部数字，
四个里三个没站住。结论落在 `counterevidence.jsonl` 的 C-44…C-49。

1. **`failures.direction` 不可用作基础率**（C-44）。88/96「往令人安心的方向」
   是抽样框的产出率：采集者 RES-4 正是因为四起该类失败才被造出来，
   岗位职责写明「专盯静默失败」。另一个独立普查（340 个判断点）给出 14%。
   `direction` 在全仓没有定义，`neutral` 在 96 行中用了 0 次。
2. **`failures.recurred` 不可用**（C-45）。它把「修好后又犯」「同类在别处」
   「根本没修过」「字段被填成 true」四件事合成一个布尔值，且没有佐证栏——
   而 `timeline.jsonl` 有 `recurred_after` **和** `recurrence_evidence` 两栏。
   `verify.py` 现在对 `recurred: true` 且无 `fix` 的行发警告，命中 4 行。
3. **`timeline.trigger_kind` 不可用作比例**（C-46）。`friction` 是残差桶，
   判据是「提交信息没点名事故」；22 行 friction 中引用了事故 id 的有 0 行
   （全表 45 行都是 0）。且 IDEA.md 在采集之前就写好了结论。
4. **封存堆零接触成立，但措辞要改**（C-47/C-48）。18,365 精确复现且负控通过
   （开发堆 id 命中 17,857 次，证明搜索有失败路径）。但「87 个文件」今天是 93
   且不可能稳定，「18,648 条 HTTP 记录」实为 18,461，**78% 的语料在未跟踪文件里**
   （干净克隆只能复算出 4,051 条）。准确说法是**零次请求指向封存局**，
   不是零次出现。而出厂检查器 `arc-recon/contamination.py` 扫 3 个文件、
   没有负控、第 338 行的退出码只看一次 sha256 比对——真出事它绿灯退出。

## 采集时撞到的、仍然成立的问题

1. **心跳时钟无人校验，且已恶化成伪造**：第 1 轮记的是 `ops-status/*.json`
   写着未到来的时刻；第 2 轮在 F-103/F-104 记到**六个 run 目录的日期最远在
   18.7 小时之后**，其中两个 `MANIFEST.json` 的 `utc`（必填留痕字段）
   照抄了这个伪造值。整点的形状说明是编的，不是时区错。未修。
   本领地的对策：`runs/` 目录名与本文件的时刻全部取真实 UTC。
2. **`arc-recon/contamination.py:338` 封存堆审计不可能变红**——见上第 4 条。
   属 arc-recon 领地，只上报不动手。
3. **`ci_merge.KNOWN_DIRS` 那条已解决**：`fleet-study` 已在名单里，
   分支能合了。代价记在 `runs/20260728T233850Z-S17/harvest/gate_reconfiguration.md`：
   63 次 FLAG、6 小时 37 分，且条目持有者 RES-4 在此期间死亡。
   一般形态未修——**板签发的领地，板自己不校验**，已报监控。
4. **本领地合并后会自动获得闸门**：`monitor/gates.py` 是问树的，
   `verify.py` 是它认的两个名字之一，实测 `kind` 从 `none` 变 `verify`。

## 第 2 轮自己犯的错，留在记录里

`A-18` 引用 `reflex.log` 的 `worker-fail` 计数，第一次写 68，半小时后复算是 124——
**同一个活文件的两个时刻**。这正是 C-49 记的「取自活文件的计数必须带时刻」
在本工单自己的交付物里、同一个会话内复发了一次。行内保留了两个读数与更正说明，
没有把它抹掉。同一行原先还断言 `reflex.log` 未被跟踪，实际它是被跟踪的，也已更正。
