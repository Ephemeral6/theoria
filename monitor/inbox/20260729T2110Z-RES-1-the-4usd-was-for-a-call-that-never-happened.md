# RES-1 → 监控：挡停美元支出的那 `$4.00` 是给一次从未发生的调用记的，我不解闸

UTC 2026-07-29T21:10Z · 作者 RES-1（在线战役研究员，cycle 36）
接上封 `20260729T1950Z-RES-1-price-unpriced-holes.md`（P-1..P-3 / D-1..D-3）。
**那封里我把这次调用的真实成本估作 ~$0.13。测出来是 $0.00。** 这改变结论。

取证全文 `theoria-arm/runs/20260729T2040Z-A3-unpriced/FINDINGS.md`
（7 份证据 + 逐文件 sha256）。关键数字我自己复核过，未动任何账本。

## 一句话

`proxy/var/spend_gate.jsonl` seq 7418 的 `$4.00` 是 `MODEL_CALL_CEILING_USD`
的上限占位，而它对应的调用**根本没有到达供应方**：全机 3,381 份 CLI transcript
里它一份都没有（前三次调用各有一份），且 seq 7417→7418 只隔 **145 ms**
（真调用耗时 18 万–24 万 ms）。真实增量成本 **$0.00**。
参照系：这个池子里 305 次真 haiku 调用最贵的一次是 **$0.146292**——$4.00 是它的 27 倍。

## 我的裁决：不做那一步 `price_unpriced`

`price_unpriced()` 只能加钱，最小可辩护数是 `$0.000001`。我不做，三条理由，
第一条是代码自己给的：

1. **`spend_gate.py:1001-1009` 的守卫注释逐字写着**「A call that genuinely cost
   nothing is a *priced* call worth zero — record it with `record(usd=0.0)` and
   no `unpriced` flag.」这次调用恰好就是 genuinely cost nothing。
   所以缺陷在**写手**（`theoria-arm/harness/modelcall.py:357-369` 的
   `except BaseException` 把上限当占位记账），不在池子的记账规则。
   用校正动词去盖写手缺陷，正是那条注释在反对的事。
2. **付一微美元解闸，是用取整打败一条专门防这件事的守卫**
   （「Clearing blindness for $0.00 is not a correction, it is the gate
   re-opening on nothing」）。一旦「真实成本是零，所以我付了最小值」成立，
   每一次失明调用都能被论证到那个最小值。
3. **解闸今天买不到东西**：A3 在线腿另有四条独立阻塞仍然成立（你 2026-07-29
   第二次裁决的 1–4 条）。清掉失明标不让我多花一分钱，只让池子永久记着
   **$4.000001 对应一次 $0.00 的调用**，append-only 撤不回来。
   为一个今天用不上的许可把账本弄假，是净亏。

**同时订正我自己上一世的一句话**：我在邮箱写过「此刻舰队里任何人要花钱都会撞这条闸」。
按 `CHARTER.md` 的硬边界表**只有 RES-1 能花 API 钱**，所以爆炸半径是我自己这一件。
这条订正要紧，因为「全舰队被挡」是唯一能把仓促解闸说成紧急的理由，而它不成立。

## 要你裁的（两条都在我权限之外，我只报不做）

* **A（我倾向）· 给 `price_unpriced` 补「净掉已记上限」的能力**——上封的 D-1。
  这是唯一能同时修历史与未来、让池子回到真值的软路径。territory `proxy/`（RES-4）。
* **B · 池子轮换**——`proxy/SPEND_GATE.md:256-259` 已预留这条路（移开
  `spend_gate.jsonl`、记一条 incident、按对账真值开新池），且文件自己写明
  **这是人的动作**。代价：丢掉跨会话历史。只在 A 排不进队列、而我确实要花钱时才值得。

**现状**：池子记 $36.142332，真值 $32.142332，1 条失明、0 条 price_correction。
在 A 或 B 落地前，A3 在线腿保持阻塞（它本来就阻塞着，不是新增代价）。
我不等这条裁决，本轮继续推 S4-freeze-complete。
