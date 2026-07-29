# DRIFT-a-corrupt-heartbeat-switches-off-the-check-that-would-have-caught-it

severity: high
dimension: 7（单向门／不可能变红的检查），旁及 8（监控自身漂移）与 6（要求引用了不存在的东西）

**先说结论的边界**：本条的活体实例**没有造成任何损失**。它值 high 不是因为这次的后果，而是因为
(a) 一条**已交付的裁决**（S23）在监控自己的代码里被违反；(b) 一份损坏的心跳会**把该编号的陈旧检测本身关掉**（注入实测）；(c) 全仓没有一个负样本；(d) 没有任何东西阻止它对任何一个编号再次发生。

---

## evidence

### 一、把三种状态压成一种的那个 helper

`monitor/scan.py:69-76`：

```python
def read_json(path, default=None):
    if not exists(path):
        return default          # :70-71  文件不存在
    try:
        with open(rel(path), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default          # :75-76  解不开、坏了、权限、任何异常
```

八个调用点无法区分「没有这个文件」「文件坏了」「文件在但解不开」。

### 二、心跳的四个读者，没有一个把「解不开」当异常

| 读者 | 拿到什么 | 渲染成什么 |
|---|---|---|
| `_self_driving()` `scan.py:1073`（探针 `self_driving`，注册于 `:1401`） | `:1090` `read_json(path, {}) or {}` → `{}` | `:1111` → `RES-3 第None轮 None`；`:1100` 陈旧判据只用 mtime，文件新鲜，`:1113` 返回 **green** |
| `probe_ops_duty()` `scan.py:600` | `read_json(path, None)` → falsy | `:607-609` → `status: "missing"`、`state: "未启动"`、**`age_min: null`** |
| `agents.py:141-144`（`ops_cards`） | `except Exception: beat = None` | `state["agents"]["standing"]` 里该卡 `"state": "未启动"`、`"cycle": null`，而同一张卡 `age_min` 是 33 |
| `standing.py:294-299`（`occupied()`） | `except Exception: cycle = None` | 存活证据消失 |

**本条最硬的一格是第二行，且它是注入实测出来的，不是读码推的**：一旦 `age_min` 被设成 `null` 且 `status` 被钉死在 `"missing"`，那个编号此后**再也不可能**触发 `:613` 的 `age > stale_min` → risk。
**一份损坏的心跳，把针对该编号的陈旧检测关掉了。**（`probe_ops_duty` 的花名册是 OPS-A/B/M/R；活体四份 OPS 心跳目前都是合法 utf-8，所以这一格**没有活体实例**，只有注入实例——如实标注。）

第四行是**花钱路径**：`standing.occupied()` 决定要不要给同一个编号再起一个会话。契约 `monitor/prompts/ops/RES-3.md:36` 逐字称 cycle 是「你还活着的**唯一伪造不了的证据**」，而 `:298` 把它静默吞掉。本例未致损（`occupied()` 的阶梯是 board 活动 90min → lock 20min → cycle，RES-3 的 board 活动 48 分钟前仍在窗口内），属**潜在**后果。

### 三、唯一会说话的地方，和它这次为什么没说话

`_stamps_to_check()`（`scan.py:765-770`）**故意绕开 `read_json`**，自己 try/except 并把 `(label, path, None, err)` 入列；`probe_clock_sanity()` `:815-816` 收进 `unreadable`，`:852-855` 有一条写得很好的红：

> **N 处时间戳读不出来**：……**读不出不等于没问题。**

**正确的写法就在同一个文件里，`read_json` 上方约 700 行。**

但 `:845` 的 `if ahead: return` 排在它前面，是严格 if/elif 阶梯——两个互相独立的故障，先到的把后到的盖住。RES-3 在 22:25Z 损坏后经过的 3 次扫描，三次都被 `ahead`（手打时间超前）抢占。

**抢占是真的，但不是「不可达」——我的草稿这么写过，被自己的对抗者用监控自己的日志证伪了。** `monitor/refresh.log`（`scan.py:3109` 的 stdout 落盘处，**该文件本身是 GBK**）记录了 101 次带该探针的扫描：`ahead` 分支渲染 65 次，**`unreadable` 分支渲染 36 次（36%）**，最近一次 07-30 04:24（本地时）。
所以准确说法是**非确定性的延迟检测**：那一支会自己浮出来，只是不知道等几跳；在它浮出来之前，一份读不出的心跳在盘面上完全无害。

### 四、负样本缺失

`monitor/tests/` 里**没有任何测试写过一份非 UTF-8 或解不开的心跳文件**。两个 helper 都硬写 utf-8：`test_probes_injection.py:33`、`test_session_liveness.py:39`。

### 五、这条规则一周前就被逐字裁决过，落在别人身上

`monitor/board/done/S23-unreadable-is-not-clean.W-1642.md`（**已交付**），裁决逐字：

> **读不开 / 解不开 / 认不出，一律是 `needs_human`，绝不是「无发现」**

并要求「各配一个负样本」。它落地在 `release/check_redlines.py` 与 `arc-recon/contamination.py`。
`probe_clock_sanity:853` 那句「读不出不等于没问题」**就是从 S23 抄来的措辞**。

**监控把这条规则用在了别人身上，没用在自己身上。**

一周后 S28 又做了一次同形普查——第二个提交的标题逐字是 *five probes that reported a state they had not measured*，证据在 `monitor/runs/20260729T2035Z-S28/EVIDENCE-2-scan.md`，修了 5 处——**而 `read_json` 一个字节没被碰**；它在整个 `monitor/runs/`、`monitor/board/`、`monitor/inbox/` 里出现 **0 次**。一个被 8 个调用点共享的 helper，两轮针对同一形状的普查都从它旁边走过去了。

### 六、活体实例（只作为「触发条件存在」的证据）

工作树 `monitor/ops-status/RES-3.json`，630 字节，mtime `2026-07-29T22:25:04Z`，**GBK 编码**，位置 94 的 `0xbe` 让严格 utf-8 解码失败。当时 RES-3 在 cycle 83 正常干活。

活体 `monitor/state.json`（mtime 22:38:42Z）：

* `/probes/self_driving/status` = **green**，detail 逐字含 `RES-3 第None轮 None（9 分钟前）`
* `/agents/standing[RES-3]` 的 `state` = **`"未启动"`** ← 这是一句**主动的假话**，不是沉默
* `/probes/clock_sanity` = risk，讲的是别人的超前时间，**不含 RES-3**

**根因不是「一次异常写入」。** 心跳由 agent 手写（`monitor/prompts/ops/*.md` 给的是一行 JSON 字面量），而 `monitor/prompts/ops/` 里**没有一个文件提过 utf-8**；这台机器 codepage 是 936，`Set-Content` / `>` 默认写 ANSI。已提交的 18 个历史版本 0 个非 utf-8（17 个含中文），所以这是**第一次**发生——**也没有任何东西阻止它对任何一个编号再次发生**。

### 七、盘面可见性的准确范围（我草稿里最不准的一段，已收窄）

`clock_sanity` 与 `self_driving` 的 detail **进不了 `index.html`**：`render()` 只显式画三条探针（`scan.py:2096-2098`），另加 `spec.py` 里绑定的 5 条（`"probe":` 在 spec.py 出现 5 次）——25 条探针里只有 8 条的 detail 上得了那一页。它们只到达 `state.json`、`app.html` 的「实况探针」折叠、以及 `refresh.log`。
而活体 `probe_scheduled_tasks` 现报 **`TheoriaServe` 未注册**，app.html 是 `fetch state.json` 的纯渲染器，**现在拉不到数据**。

---

## claim

监控读心跳的 helper 把「文件没有」「文件坏了」压成同一个值，于是一份 GBK 心跳在盘面上渲染成两个 `null` 外加一句「未启动」的假话，而**零个探针为此变红**。同一个文件里 700 行之外就写着正确的做法，且这条规则在 `S23-unreadable-is-not-clean` 里已被逐字裁决并落地到另外两个领地——**监控没有把它用在自己身上**。最重的一格是：一份损坏的 OPS-* 心跳会把 `age_min` 置为 `null`，从此该编号**永远不可能**触发陈旧告警——**要检测这件事的检查，被这件事本身关掉了**。

---

## suggest

1. **`read_json` 分出第三个返回值**，与 S28 给 `standing.py` 加 `CLAIMABLE_UNKNOWN = -1` 同形（`standing.py:304`，docstring `:307-320` 逐字写着「板查询崩溃被 `except Exception` 写成 `0`……那**比真空板更安静**」）。八个调用点各自决定「读不出」该算什么，默认**不许**算成好消息。
2. **`probe_ops_duty` 的 `age_min: null` 优先修**：它不是渲染缺陷，是把陈旧检测关掉。解不开时应报 risk 且 `age_min` 照常由 mtime 计算——**mtime 永远读得到，和文件内容无关**。
3. **`probe_clock_sanity` 的 if/elif 阶梯改成累加**：`ahead`、`unreadable`、`drifted` 三类互相独立，应当合并进同一条 detail，而不是先到者独占返回槽。（这条不急——36% 的基础率说明它会自己浮出来。）
4. **补负样本**：给 `test_probes_injection.py` 与 `test_session_liveness.py` 各加一个写 GBK 心跳的用例，断言至少一个探针变红。S23 的裁决本来就要求「各配一个负样本」。
5. **在 `monitor/prompts/ops/*.md` 的心跳模板旁边写一句「必须 UTF-8」**，并给出这台机器上不会写错的写法。这是唯一能阻止复发的一条，且最便宜。
6. **`monitor/refresh.log` 是 GBK**：探针 detail 给人看的第三条路径落进了一个乱码文件。顺手修。

---

## 立案过程留痕（对抗者改写了这份报告的一半）

我的草稿被一个专门找反例的对抗者审过，**它纠正了我十条事实，其中三条是承重的**：

* **「在盘面上一个字都没有」——假。** `state.json` 里有两处关于 RES-3 的字。准确说法是「渲染成两个 `null` 外加一句假话，零个探针变红」。
* **「`:852` 那一支在实践中不可达」——被监控自己的 `refresh.log` 证伪**（101 次扫描里它渲染了 36 次）。这把结论从「结构性不可达」降成「非确定性的延迟检测」，**分量差一个数量级**，而我本来会把它当成前者发出去。
* **「`probe_clock_sanity` 是唯一捕获这个异常的地方」——假。** 还有三处捕获后丢弃（`read_json:75`、`agents.py:143`、`standing.py:298`）。它是唯一**报告**它的地方。

它还找到了**比我给它的更硬的东西**：`probe_ops_duty` 的 `age_min: null` 会永久关掉陈旧检测（注入实测）；`standing.occupied()` 这条**花钱**路径也吞 cycle；以及 `S23-unreadable-is-not-clean` 这个比我引的 S28 强得多的先例——那是同一条规则的**直接豁免**，不是形状相似。

它也指出我的实验方法有一处失真：`git archive origin/master monitor` 出来的树缺 `PARTNER_SYNC.md` 与其他领地的 `runs/`，所以我量到「1 处读不出」，**生产是 18 处**（17 条 manifest 非 ISO8601Z 的噪声）。RES-3 能排进 detail 的 `[:4]` 是排序碰巧，不是设计。**下次直接把 `scan.ROOT` 指向真树只读跑，不要 archive。**

对抗者未能验证：`agents.ops_cards` 的「未启动」有没有真的画到人眼前（app.html 的常驻卡片模板只用 `cycle` 与 `age_min`，没用 `state`，未跑浏览器）；`TheoriaServe` 未注册持续了多久；RES-3 那次 GBK 写入的直接成因（按隔离契约未读 dispatch 日志与 transcript）；`unreadable` 平均要等多少跳浮出来（36% 是基础率，但 `ahead` 的持续有自相关）；RES-3 在 22:25Z 之后是否仍然活着。
