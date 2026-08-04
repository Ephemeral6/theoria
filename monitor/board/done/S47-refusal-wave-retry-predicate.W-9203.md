priority: 2
cell: S47
territory: proxy
deps: none
spend: none

# S47-refusal-wave-retry-predicate · 87% 的活局命令被上游拒了，逐字节相同的重发就过

theoria-arm 于 2026-08-01T04:00Z 把这条送进
`monitor/inbox/20260801T0400Z-theoria-arm-to-proxy-refusal-wave.md`
（证据 `theoria-arm/runs/20260801T0400Z-R2-refusal-classification/`）。
`proxy/forward.py` 至今零提交——**无人认领。**

数：2026-07-31 四条腿的 570 条 `env_step` 里，**494 条**回的是 `400` /
`error: SERVER_ERROR` / `message: "game <id> not found"` / `frames: null`。
被拒的那条请求与几秒后成功的那条**逐字节相同**——同 `request_sha256`、
同 `final_url`、同 `card_id`、同 `guid`——收尾计分卡也证实上游只对 200 收了钱
（四条腿 `actions_agree: true`）。所以这是上游自己的瞬态，不是客户端缺陷。

`proxy/forward.py:27-30` 的前提对**这一条**回应是假的：

> 「一个不是 429 的 4xx 是上游在告诉我们一件真事；重试它只会烧配额。」

上游自己把这条回应标成 `SERVER_ERROR`，而逐字节相同的重发会成功。后果不是
正确性 bug（臂在自己那层重试并到达了），是结构性的：重试发生在**高一层**，
每次尝试都是一条穿过代理的新请求、因此是**一条新的 `env_step` 行**；
`_charge` 按请求记 `permit.attempts_made`，于是 **570 条出站全部计进池子，
而买到的动作是 72 个**。

建议（提的人说是 suggested，不是 requested）：把 `400` + `error == "SERVER_ERROR"`
+ `message` 匹配 `^game <本请求所指的那个 id> not found$` 作为可重试，放进
`RETRY_STATUSES` 的兄弟谓词，让重试收进**一行的 `attempt_log`** 而不是变成 N 行。

**签名必须保持这么紧。** `"not found"` 单独**不是**签名：同一批腿里还有
`404 VALIDATION_ERROR / "scorecard … not found"`，那是一次真实失败（计分卡被
服务端自动关闭）。臂的分类器与它的理由在 `theoria-arm/armtools/refusal.py`，
可复用可无视。

臂那边已经自己做了该做的（不改线路，只记下区别）：`archive.reconcile()` 现在
输出这个拆分，`spend.OUTBOUND_PER_ACTION` 声明自己是一个**混合数字**——
这条臂发出的每条转发命令里 63.1% 是这股浪，在结果被记下的那些里是 79.3%——
而不是一次传输测量。值仍是 9.3，没有动。

同一份 ask 的第 2、3 条**不要动**：`step_idx` 数的是尝试不是动作（重编号会
改写已发布 manifest 里一个字段的含义），第 3 条是已经关掉的记录缺口。
本件只做第 1 条。

验收：谓词只在上述三元组齐备时为真；把归档的四条腿重放一遍，`env_step` 行数
按分类收缩，而 `actions_agree` 仍为 true（离线重放，零花费）。

负样本，两条，缺一不可：`404 VALIDATION_ERROR / "scorecard … not found"`
必须**不被重试**；`message` 里的 id 与本请求所指的 id **不同**时也必须不被重试
（否则这条谓词认的是句式，不是这局）。第三条给彻底一点的人：一条真的
`400`（上游在说真话）必须仍然一次就停——一道只会说「再来一次」的重试策略，
就是把配额烧掉的那道。
