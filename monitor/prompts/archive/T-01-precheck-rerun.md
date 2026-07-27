# T-01 · 重跑确定性预检，改判 INC-001/INC-002（最高优先）

你在 Theoria 仓库（工作目录即仓库根）。先读 `CLAUDE.md`，再读 `Theoria.md` 的
Phase 1 一节（尤其「确定性预检」「一件接入核查」），然后读
`arc-recon/README.md` 与 `PARTNER_SYNC.md` 的最后三段。

## 背景

INC-002 断言「零次动作成功，在线 API 全线受阻」。baseline-arms 的假设排查
已把它推翻并找到根因线索（见 PARTNER_SYNC 的 [baseline-arms] 段）：
**去掉版本后缀的短 ID**（`sk48` 而非 `sk48-d8078629`）返回 200，同形状全 ID
请求带退避重试也间歇成功 —— 400 `game not found` 不是权限问题。
但 `arc-recon/data/incidents.jsonl` 与 README 的官方判决还停在「全线受阻」，
INC-001「开发堆只剩 1 局可玩」也随之不可信。

**一个必须处理的张力**：Theoria.md 把 game_id 的版本后缀当环境版本指纹。
如果改用短 ID 通信，指纹就丢了 —— 你的预检与账本要同时记录：请求用的短 ID、
目录里对应的全 ID（版本后缀），两者的映射每局入账；金丝雀重放以全 ID 为锚。

## 任务

1. 给 `arc-recon/precheck.py` 加一个显式的重试策略（指数退避 + 每步封顶重试数，
   全部参数入账；每次重试也逐条写进 ledger —— 重试不是作弊，瞒报重试才是）。
2. 只在**开发堆 4 局**（`ar25-0c556536` / `g50t-5849a774` / `sk48-d8078629` /
   `tn36-ef4dde99`）上重跑确定性预检：每局固定动作序列跨会话重放两遍，
   帧哈希逐一比对。哪局可玩、哪局真的 400 到底，逐局记录。
3. 据结果在 `arc-recon/data/incidents.jsonl` **追加**改判条目（不许改写旧行）：
   INC-001/INC-002 各一条 superseded-by 记录，写清新证据是什么。
   `arc-recon/README.md` 相应更新。
4. 把 `baseline-arms/` 整理提交（它现在整个目录未跟踪）：харness 代码 +
   probe_log.jsonl。提交信息说明它推翻了什么。
5. `PARTNER_SYNC.md` 末尾追加一段（格式见 CLAUDE.md），把改判说清楚。

## 红线

- **封存堆 21 局零接触**：任何请求体里不得出现封存局 game_id。piles.json 是
  哈希锁定的，别碰。
- 密钥只从根目录 `.env` 读 `ARC_API_KEY`，任何被跟踪文件、日志、提交信息里
  不得出现它的值；账本里一律 `<redacted>`。
- PARTNER_SYNC 只追加自己的段落，不改别人的。
- 动作配额是战役资源：预检每局控制在 ~20 个动作以内，总量先算后花。

## 验收

- 每局一个明确判决：PASS / FAIL / UNPLAYABLE，且判决逻辑经得起 INC-003 的教训
  （两侧都失败不得判 PASS；哈希须两侧俱在）。
- incidents.jsonl 里 INC-001/INC-002 有了带证据的后续条目。
- `python monitor/scan.py` 重跑后 F-02 应可关闭（如果你顺手更新
  `monitor/spec.py` 的 FINDINGS，把 F-02 标记为已解决并注明证据，更好）。
