priority: 1
cell: A1
territory: baseline-arms
deps: none

# A14-campaign-json-untracked · 四份全战役产物花了钱、没进 git

审计（2026-07-29）确认：`git ls-files baseline-arms/out/campaign` **是空的**。
四份全战役 JSON（裸 CC 四局，实测花费 $48.39）躺在工作树里**没有被跟踪**——
一次机器故障、一次误清理，这笔钱就白花了，而它们是主表基线那一列的唯一来源。

好消息是它们已经被别处消费过并钉住了哈希：
`battery/runs/20260728T061147Z-v3/MANIFEST.json:145-148` 记着它们的 sha256。
**所以「该不该入库」这个问题已经有答案了：有人在拿它当证据用。**

做四件：

1. **逐份核对 sha256** 与 battery MANIFEST 里记的那四条是否一致。
   **不一致就先停下来报告**——那意味着产物在被消费之后又被改过，
   这比没入库严重得多。
2. **入库**：把四份 JSON 加进 git（连同它们的 MANIFEST/RUN_STATE，
   按留痕正典要有 `prompt_id` / `branch` / `base_commit` / `utc`）。
   体积大到不适合入库的话，**说明大小并给出替代方案**（例如只入摘要 + 哈希），
   不要默默不做。
3. **顺手查同类**：`out/` 下还有哪些花过钱或墙钟的产物没被跟踪？
   列一份清单，逐条给「入库 / 只入哈希 / 可重生成故不入」的判断与理由。
4. 把「花过钱的产物必须入库或留哈希」写进 `baseline-arms/STATUS.md`，
   并在 `PARTNER_SYNC.md` 追加一段。

零 API、零封存堆接触。**这一件是纯抢救，不产生新主张。**
