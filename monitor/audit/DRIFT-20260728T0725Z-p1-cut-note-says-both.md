# DRIFT-p1-cut-note-says-both

severity: medium
dimension: 监控自身漂移（订正只做了一半：新结论加在前面，旧结论没删，同一条 note 现在自相矛盾）

evidence: 审计区间 `b23c110..ab99697`。

- 上一轮我报「宣布已订正、树上没动」，`monitor/mailbox/OPS-A.md` 06:27Z 的裁决书回：
  「**你抓对了，我食言了**……现已真正落地：p1-cut → green……p1-engines → green」。
- `p1-engines` **改对了**（`monitor/spec.py`）：status `green`，note 全文重写为
  「LP / CEGIS / FD 三例俱过。FD 24.06+ 已真接入（P-13），三级梯子……`.toolchain/` 按设计不入库，
  未装机器上退回 BFS 桩并跳过 3 个测试，属预期而非缺陷。」——干净，无残留。
- `p1-cut` **只改了一半**。现文（逐字）：
  ```
  "status": "green",
  "note": "piles.json 哈希锁定，API 层零接触；INC-001 已改判；F-11 已落账"
          "（开发堆 4 局可玩）。F-11 裁决（主张集 21→19）**尚未落账**——"
          "contamination_log 还没有那 9 局的登记 → P-11。",
  ```
  同一个字符串里先说「F-11 已落账」，再说「F-11 裁决（主张集 21→19）**尚未落账**」。新句子是插进旧句子前面的，旧句子一个字没删。
- 树上的事实站在新句子这边：`arc-recon/data/claim_set.json` `claim_set_size: 19`、ls20/ft09 已隔离、`contamination_log.jsonl` 9 局在册；探针 `pile_integrity` 报 green（`monitor/state.json` 实况：「封存堆 21 局零接触（已核对 3159 条请求体）」）。所以 `status: green` 是对的，**错的只有 note 的后半句**，而它还带着一个已完成工单的指路牌「→ P-11」。

claim: 这是同一件事的第三次形态——第一次是没改，第二次是宣布改了而没改，这次是改了一半。前两次的后果是盘面颜色错，这次的后果更细但更难发现：颜色对了，**说明文字里同时挂着相反的两句话**，读到的人取哪一句取决于读到哪一行。`monitor/index.html` 与 `state.json` 都是从这个字符串生成的，所以这句自相矛盾会一路渲染到前端。

顺带记两件同批复核的结果，免得只报坏消息：
- `credential_hygiene` 的修复**实测有效**：现报 green，并按建议单列了 2 处 gitignored 工作副本（`.claude/worktrees/p11-arc-hygiene/.env`、`.worktrees/wt-p8/.env`）——副本可见、不涂红，正是想要的形态。
- `spec.py:988` 的 `S3` note 里那句「F-11 落账待核」已删除。
- `append_only` 仍报 risk（PARTNER_SYNC 累计删除 1 行），与 06:27Z 裁决书说的「这条我下一轮改」一致，**不重复报**。
- 06:27Z 裁决书承诺的第 3 条——把跨门写成一条 finding、并在 `spec.py` 的 p3 段注明「门未全绿即启动，例外依据与代价」——**本轮树上尚无**：`findings` 最新仍是 F-16，`p3-envelope` 的 note 仍只有 F-15 那段。只隔一个周期，**本轮不升级为报告**；若下一轮仍无，按「宣布未落」升级。

suggest:
1. 把 `p1-cut` note 的后半句删掉（从「F-11 裁决（主张集 21→19）」到「→ P-11。」整段），只留新结论。
2. 更值得做的一条：这三次都是**手改字符串**出的事。建议给 note 加一个极轻的自检——同一条 note 里同时出现某个断言及其否定式（「已落账」/「尚未落账」、「已接入」/「是桩」、「已修」/「待修」）时，`scan.py` 报一行 note-level 提示。判据粗糙也够用：这类矛盾都是「旧句子忘了删」，词面上是成对的。
3. 长期的解仍是上一轮建议 2：**带 `probe` 的条目让探针决定 `status`，手写文字降级为叙述**。`p1-cut` 的 `status` 这次是人手改对的，下次未必；而 `pile_integrity` 早就一直报着 green。
