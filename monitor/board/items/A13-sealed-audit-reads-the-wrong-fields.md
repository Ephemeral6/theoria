priority: 1
cell: S2
territory: arc-recon
deps: none
lane: infra

# A13-sealed-audit-reads-the-wrong-fields · 封存审计在一份没有那些字段的账本上报「干净」

57 个 agent 的对抗性普查（2026-07-29）里最重的一条。**这是封存纪律的守门人，
而它现在的绿灯是构造出来的，不是查出来的。**

1. **`arc-recon/contamination.py:163`** —— 它按 HTTP 账本的字段（`url` /
   `request_body` / `response_body`）去读 `baseline-arms/ledger.jsonl`，
   而那 560 条记录**只有顶层 `game_id`**。于是 `sent` 恒空、`contacts` 恒空。
   :197 的防呆分支（`clean = ... if (present and not unreadable) else None`）
   只防「文件缺失或损坏」——文件在、每行都解析得开，**所以它返回 True**，
   印成「560 calls, sealed ADDRESSED: NONE」，而 `claim_set.json` 已经把这个
   绿灯落盘了。
2. **`arc-recon/cascade/verify.py:166`** —— A7 断言「封存池不出现在任何请求体里」，
   实现是**完整 id 的子串测试**：短 id（`ls20`，INC-005 记录过活 API 会用这种形式）、
   URL 里的 id、`request_body: None` 全部无声通过。而 README 明说这批账本不参与
   `contamination.py` 的全账本审计——**所以 A7 是这些文件上唯一的封存检查，
   且严格弱于它替代的那个**。`probe.py:216` 已经在写 `{"tags": [..., "ar25"]}`
   这种裸词干请求体。
3. **`arc-recon/contamination.py:333`** —— 登记时 `if game_id not in register: continue`，
   一次无计数、无 problem 的静默丢弃。实测：把 `ls20-9607627b` 写成 `ls20`，
   claim_set 从 19 涨到 20、`ls20` 从隔离进入 clean、闸门全绿、problems 为空，
   而 `test_hygiene.py` 四条断言照常通过。

做四件：

1. **「我不认识这个文件的任何字段」必须判 `unreadable`，不是 clean。**
   读取器加一条形状检查：一份记录里一个已知字段都没有，就是没检查过。
2. **判据收敛到一处三重口径**（完整 id + 词干 + URL），`cascade/verify.py`
   引用它而不是自己写一遍——两份实现已经漂移，这条工单就是账单。
   并注意 `verify.py:74` 只遍历四个开发局的账本，
   一个 `ledger.<封存 id>.jsonl` 放进目录**根本不会被打开**。
3. **登记时 id 不在切分内 → append 一条 problem**（一行）。
4. **三条各配一个阴性样本**：一条 `{"game_id": <封存 id>, "action": "RESET"}` 的
   episode 记录、一条裸词干请求体、一条错拼的隔离登记。**三条现在都能骗过闸门，
   修完必须让它们全部变红。**

服务论文 WP2 与 WP6 的全部可信度。零 API、零封存堆接触（本件只读已有账本，
**不许为了测试去碰任何封存局**——阴性样本用构造的假记录）。
