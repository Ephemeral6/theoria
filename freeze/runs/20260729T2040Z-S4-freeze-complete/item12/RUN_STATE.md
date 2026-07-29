# item 12 · 预算表 —— RUN_STATE

工单 `S4-freeze-complete` 第 12 项。分支 `agent/s4-freeze`。
叙述在此，机器可读的清单在 `MANIFEST.json`。

## 交付

| 路径 | 是什么 |
|---|---|
| `freeze/BUDGET_TABLE.md` | 预算表本体。散文是判断，`G1`–`G9` 是生成的 |
| `freeze/BUDGET_TABLE.json` | 机器层的落盘形态，`--verify` 的比较对象 |
| `freeze/build_budget_table.py` | 生成器 + `--verify` / `--allow-absent-pool` / `--emit-pool-digest` |
| `freeze/POOL_DIGEST.json` | 追踪的、脱敏的池摘要（C2 的补救）。**是否提交由 RES-1/监控拍** |
| `NOTES_FOR_RES1.md` | `verify.sh` 阶段片段、`build_manifest.py` item 12、`MANIFEST_DRAFT` 行 12、以及阶段 8 的耦合警告 |
| `probe_ledgers.py` / `probe_1h_cache.py` / `probe_checks.py` | 三个散点复算脚本，保留以便逐数复核 |

## 关键结论（全部在 `BUDGET_TABLE.md` 里带出处）

1. **闸门盲区 $67.41。** 真实已花 $103.55（追踪账本自报），闸门只看得见 $36.14——
   池子从 2026-07-28T09:26 才存在，而 INC-BA-003 那场并发 S1 战役的 $50.39
   在任何池外。真实余额 **$111.35**，闸门以为 $178.76。
2. **封存主表 12 个枚举情景，装得下的是 0 个。** 最便宜的 $175.55 > $111.35；
   能测出主终点的 `S1` 半边是 $3,935–$518,995。
3. **且格子会死。** q = 47/48（争用条件下的唯一实测）下 n=2 只出 0.78/19 格；
   够到 14/19 要 n=64 → $5,618（最便宜）至 $518,995。
   算术属 RES-1 §5.7，本文独立复核一致（一处取整细化：n=64 而非 63）。
4. **占位 $4.00（seq 7418）** 已逐个总数量化其影响；单价一律剔除，余额一律双报。
5. **冻结价目表算不回 89.6% 的付费历史**（缺 `claude-haiku-4-5-20251001` 别名），
   且对能算的那部分比真实账单低 **8.39%**（1h 缓存写倍率，解释 7.09 个点）。

## 起草期间的两次实时验证

* `--verify` 抓到 `STATS_RULES.md` 的 ⟨n⟩ 裁定从 `:705` 移到 `:712`
  （RES-1 插入 §5.7），报 `CITATION DRIFT`。引用表按设计烂了一次，闸门响了。
* `--verify` 抓到池子在起草期间从 11,863 行 / 5,181 动作长到
  11,874 行 / 5,190 动作（$0.0000，全部测试流量），报 `THE BALANCE MOVED`。

## 红线遵守

* 只写 `freeze/` 下的路径。`baseline-arms/`、`proxy/`、`arc-recon/`、`monitor/` 只读。
* 没有 `git add` / `commit` / `push`；没有改 `freeze/verify.sh`。
* 没有对 `proxy/var/spend_gate.jsonl` 或任何账本写过一个字节（全部以只读方式打开）。
* **封存局只用了 id 与计数**：`claim_set.json` 的 `len()` 与 `piles.json` 的 `len()`。
  19 局的官方基线动作实数**没有去读**，挂成 ⛔ 12-D1 交监控裁定；
  投影用 21 局均值代替并明标为估计。
* `.env` 的值未出现在任何交付物里（已逐文件比对确认）。
