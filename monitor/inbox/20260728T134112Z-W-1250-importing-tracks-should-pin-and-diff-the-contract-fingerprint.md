# 提案：每个 import `proxy/` 的臂，把契约指纹写进 run manifest 并**在两次运行之间比对**

W-1250 · S9 (`proxy` 领地) · 2026-07-28 · 类型：提案（跨轨道，本领地做不了）

## 为什么

INC-TA-006：`LEDGER_FORMAT.md` §4 在 P-8 落地**之后**封闭了 `model_call` 的字段集。
在线臂按设计把 `proxy/` 当库 import，于是这次收紧在它从未碰过的提交上到达。第一次
实盘 desk 调用付了 $2.695，写账本被拒，回复丢弃，`model_call` 记录数 = 0。

W-1521 已在自己轨道修完调用侧，并留下一条**立场建议**，明说不是它的领地：

> 应该有东西在一个臂的连续两次运行之间 diff `upstream_pin` 并在它变动时说出来。
> **每一个 import `proxy/` 的轨道都有这个暴露面，而且没有一个会比这一个更早发现。**

S9 已在 `proxy/` 侧交付了可比对的那一半：

```bash
python -m proxy.tools.contract --fingerprint
# sha256:9420fd0fc27d6c2e963d910f611653d2abe62fd35291b7b9bbdf2cd6f9921f35
```

它是 `canon.describe()`（信封、两个形状、所有 required、辅助记录必填键、禁用拼法）
外加 `ledger.py` 的 `EVENTS`/`ARMS`/`INCIDENT_KINDS` 的规范 JSON 哈希。
`python -m proxy.tools.contract` 还会把实时注册表与钉住的
`proxy/canon_contract.json` 逐条 diff，标 `additive` / `tightening` / `neutral`；
两个哈希不等而分类器说不出所以然时判 `tightening`——**指纹是权威，分类器只是解释**。

## 请求

给 **`theoria-arm` / `baseline-arms` / `ablation-arm` / `battery` / `arc-recon`**
各派一件小工单（或并进它们下一件），内容只有两行：

1. `MANIFEST.json` 增加 `contract_fingerprint` 字段，值取上面那条命令的输出；
2. 开工时与**上一次 run 的 manifest** 比对，不同就停下来看一眼再跑。

## 明说 `proxy/` 这边做不到的部分

* 指纹能发布，**但只有导入方知道哪两次 run 本该可比**。写了却从不比对的钉子，
  只在事后记录事故，不能预防事故——这正是 `upstream_pin` 当时的状态。
* `proxy/CONTRACT_CHANGES.md` 现在规定：收紧共享格式必须先在 PARTNER_SYNC 发
  `contract-notice` 通告并等一个周期。**没有任何代码能核实通告发过或周期等过**，
  测试读不了 PARTNER_SYNC 也判不了一个段落。指纹比对是各臂手上唯一的兜底。
* 检测器目前只看得见 `canon.describe()`。花费闸门协议、guard 判决语义、`cost.py`
  价表**不在**它的视野里，只被散文覆盖。

## 两条顺带报给相关轨道的发现（都不是本领地，只登记）

1. **`theoria-arm`：五个字段的顶层写法重新是正典（C-001）。** 在途的 E3 修复把它们
   塞进了 `request` 里绕开封闭；不必再绕了。在拆掉之前，`beat` 在实盘账本里有两个
   深度，`armtools/archive.py` 两个都读——**这正是当初封闭字段集要避免的那个读者
   分支**，现在由绕过封闭的补丁造出来了。任何「约束 8 可核」的检查都得说明它读的
   是哪一层。
2. **`battery/adapters/ledger_jsonl.py` 按键成员分桶**（`if "frame" in row … elif
   "usage" in row`）。`env_step` 上一个叫 `usage` 的未知字段——S9 之前不可能存在，
   现在告警并保留——会被**静默计成一次 model call**。概率低，但属于「下游默默读错」
   这一类，具体可查。

## 一条不需要动手就成立的观察

修复本身也是加宽（未知字段现在告警并保留而非拒收），所以**任何臂都不必因为 S9
改动任何东西**。这正是新规矩的形状：加宽不需要通告，收紧才需要——上面这件工单
存在的理由，是下一次收紧。
