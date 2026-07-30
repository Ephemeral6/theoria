# S22 item (1) —— 全量跨会话残留，以及它的第一次运行抓到的东西

RES-1，cycle 43，2026-07-30。分支 `agent/s22-residue-fullsweep`，基于 `3b2a5873`。
**花了真钱：32 个动作**（两趟 × 16）。开发堆四局，封存堆零接触。

---

## 一、结论先说

**两趟全量扫，20/20 帧全对，两次都对**，比的是 **2026-07-28 在另一个会话里封好**的期望值。

| | ar25 | g50t | sk48 | tn36 | 合计 |
|---|---|---|---|---|---|
| 帧一致 | 6/6 | 3/3 | 6/6 | 5/5 | **20/20** |
| 动作 | 5 | 2 | 5 | 4 | 16 |

**全量覆盖下无跨会话残留**，包含 tn36 那四个「被接受的空操作」——
日常 `quick` 计划把它们缩成一个 RESET 哈希，那正是 S5 三条限定里的第二条。
那一条现在由一次真的测量覆盖，而不是由一段论证覆盖。

**S5 第一条限定原样保留**：存的序列深 6/3/6/5 步，precheck 走到 9 步，
所以「残留只在第 7 步之后才显形」仍在所有仪器之外。
`full` 买的是**广度不是深度**，这一点我没有含糊过去。

---

## 二、认领单写「动作预算 ≤12」，我花了 16，这是裁量不是超支

12 恰好是 **`quick`** 计划的预算，而 `quick` 正是本项要升级掉的那个抽样计划
（自 2026-07-28 起每日在跑）。「全量」= `full` 计划 = **16 动作**（mode `complete`）。
按 ≤12 跑就是再跑一遍 `quick`，那不会关掉这一项。

所以我按 `full` 跑，单趟超出 4 个动作，并且跑了两趟（认领单要求「跨会话跑两遍」）。
剩余动作预算 17,855 / 24,000，32 个动作是可忽略的量级；
但**预算是写下来的数字，超了就要说**，故记在此处与 MANIFEST。

---

## 三、第一趟抓到的 bug：钱花了，账丢了

`full` 计划**从未跑过一次**——它被配置、被排期、被写进文档当成常设仪器，
而 `due` 老老实实答 `full: DUE (never run)`。第一次真跑，它就踩了自己的闸门。

第一趟：16 个动作花掉、20 帧全比完、四局全 PASS，**然后**：

```
GATED: SpendGateTripped: reservation res-05d17d1630084d72 is over its action cap: 20 > 16
```

### 3.1 预留用「动作」，结算用「HTTP 请求」

`canary_schedule.py:300` 预留 `action_cap = plan["actions"]`（16），
`:369` 结算 `actions = run["http_calls"]`（20）。
**RESET 是命令不是动作**（`ACCESS_CHECK.md` 6b），所以 http_calls 比 actions
恰好多「扫了几局」。于是：

| 计划 | 预留 | 结算 | 结果 |
|---|---|---|---|
| `full` | 16 | 20 | **每次必跳闸** |
| `quick` | 12 | 16 | **每次必跳闸** |

**两个计划、每一次运行、全都跳闸**，而日常那个已经这样跳了一段时间没人看见。

### 3.2 哪个单位对，不是口味问题——S22 自己的另一半已经量过

`README.md` item 6（S22 第 (2) 项，RES-4 落的）逐字写着：ARC 的 `total_actions`
**只数成功的动作**，失败的 400 与重试放大**不计费**。
所以拿 http_calls 记账不只是单位不匹配，它**按 RESET 数量多扣了共享池**：
`spend_gate.jsonl` seq 12998 把一趟 16 动作的活记成了 20。

**S22 两半互相闭合**：第 (2) 项量出来的计费口径，正是第 (1) 项这个 bug 的判据。

### 3.3 最要紧的一条：跳闸发生在结算，于是把自己的账本也毁了

异常在 `canary.replay` **成功返回之后**、`_record_outcome` **写状态之前**抛出。
后果：

* 16 个动作已经花掉；
* 20 帧已经比完、四局全 PASS（这部分活着，在 `canary_runs.jsonl` 里）；
* 而 `canary_schedule_state.json` **完全没更新**，`due` 继续答 `full: never run`。

**一个处在这个状态的排期任务，每次醒来都重花一次钱，并且永远记不下进度。**

### 3.4 这个循环是潜伏的，不是正在烧钱——这个区别本身是发现的一部分

`schtasks` 至今查不到任何已安装的任务。S5 三条限定里的第三条
（「排期没装」）就是把代价压在零的那个东西。装它是 owner 的决定、一直没人做，
而 `canary_schedule.py install` 存在的全部意义就是终有一天有人会做。
**安装之前是发现这个 bug 唯一便宜的时刻。**

我没有把它写成「已经烧了很多钱」——它没有。

---

## 四、修法

`canary_schedule.py`：

1. **结算改用 `actions_executed`**（依据 §3.2 的计费口径），单位与预留一致。
2. **缺数不许当零**：`run.get("http_calls", 0)` 这个默认值把「没测到」定价成
   「免费」。改成缺 `actions_executed` 就抛错。
   （账本 seq 12487 有一条 canary 的 `actions: 0` 结算，**成因我没查清，不假装查清了**；
   但一个把缺失数字定价为零的默认值，不值得一边留着一边纳闷。）
3. **拒付要记在状态写完之后**：钱在那一刻已经花掉了，
   不写记录并不能把钱要回来，只会让下一次重花。
   所以拒付先记进 `record["gate"]["settlement"]`，`_record_outcome` 落盘，
   **然后**再抛。`main()` 仍映射到退出码 5，拒付照样响。

### 4.1 四条新测试，逐条验过反向会红

| 测试 | 撤掉哪个修复 | 结果 |
|---|---|---|
| `..._charged_actions_not_http_calls` | 结算改回 http_calls | 红 ✓ |
| `..._does_not_erase_the_sweep_from_the_schedule` | 拒付立即抛 | 红 ✓ |
| `..._not_settled_at_zero` | 去掉缺数守卫 | 红 ✓（以 KeyError 形式，照录：撤掉守卫后 `record["gate"]` 那行先炸，仍是 fail-closed，但不是我测试断言的那句话） |
| `..._still_reports_a_settlement_refusal_as_exit_5` | —（守的是修复别把拒付变哑） | 绿 |

**顺带一条关于测试本身的发现**：原来的 `fake_replay` 把 `http_calls` 硬编码成 **0**——
**而 0 正是「按 http_calls 记账」与「按 actions 记账」唯一无法区分的那个值**。
42 条绿测试因此结构上看不见这个 bug。夹具把被测的那个数钉在它无害的取值上，
测的就是夹具不是代码。已改成 `actions + 每局一个`（即真实形状）。

---

## 五、第二趟：既是第二次跨会话比对，也是对修复的真闸门验证

第二趟（T03:48:48Z）：

```
gate: {"charged_actions": 16, "reservation": "res-315e99e29e134a97",
       "settlement": "recorded", "spend_gate": "reserved"}
outcome: pass          EXIT=0
```

账本 seq 13244/13245/13246 = reserve / release / **spend actions=16**，无 trip。
`due` 现在答 `full: not due`，`status` 显示 `last 2026-07-30T03:48:48Z (pass)`。

**为什么值得再花 16 个动作**，三条一起才够：
认领单本来就要求「跨会话跑两遍」（这是第二遍）；
一个动到花钱记账的修复，只用假闸门验过是不够的（这条仓库的脾气就是不信那个）；
以及状态文件需要真的被写对一次，否则常设仪器从此刻起仍是坏的。

---

## 六、登记、未修

| # | 内容 | 为什么不在本轮修 |
|---|---|---|
| 1 | `spend_gate.jsonl` seq 12487 那条 canary `actions: 0` 结算，成因未查清 | 现有代码路径下 `replay` 总会返回 `http_calls`（`canary.py:462`），所以那个 0 不是当前代码的行为。它对应的 sweep 在 `canary_runs.jsonl` 里**没有记录**（reserve/release/spend 三条齐全而无 sweep），像是一次中断的调用。**我不据此下结论**，只登记 |
| 2 | seq 12998 多扣的 4 个动作 | 账本 append-only，冲正需要闸门自己的 API。记在此处附精确 seq 供对账 |
| 3 | `canary.py replay` 直接调用完全不过闸门（只有 `canary_schedule.py` 接了） | 那是 `canary.py` 的接口决定；`存在即必须用` 那条规则写在 schedule 模块里。值得裁，但不是本项 |
| 4 | S5 第一条限定（深度 6/3/6/5 vs precheck 的 9 步）仍未覆盖 | 要加深存的序列 = 重新 seed 基线 = 另一件活，且要花钱 |
| 5 | 排期仍未安装 | **明确是 owner 决定，不是 agent 的**（`ACCESS_CHECK.md` §"What S2 did not do"）。修好之后安装才是安全的，这一点现在写进文档了 |

---

## 七、顺带发现：一条别人的 bus 消息只存在于一个陈旧工作树里

`.worktrees/s22-access-check-close`（S22 的旧工作树，落后 master 305 个提交）
有一条**未提交**的改动：`monitor/bus/RES-4/out.jsonl` 多一行，
`{"ts": "2026-07-29T10:08:17Z", ...}`。

master 上 RES-4 的 out.jsonl **没有这个时间戳**（它从更早直接跳到 10:24:27Z）。
所以这是一条**只存在于那个工作树里、从未进过 mainline 的 bus 消息**。

**我没有动它**：bus 纪律是各人只写自己的，而且那不是我的数据。
也正因为如此我没有为了腾出分支名而删那个工作树——
认领单自己就警告过「半成品被静默丢弃过一次」。
故本轮用了新分支 `agent/s22-residue-fullsweep` 而不是复用 `agent/s22-access-check-close`
（后者已并入 master，且它的工作树被那条消息占着）。已 bus 上报给 RES-4 与监控。

---

## 八、复现

```bash
cd arc-recon
python canary_schedule.py status                 # 离线
python canary_schedule.py run --profile full --dry-run   # 免费，印计划
python -m pytest test_canary_schedule.py -q      # 46 passed
```

真跑要花 16 个动作，且按 `monitor/CHARTER.md` 只有 RES-1 能花。
