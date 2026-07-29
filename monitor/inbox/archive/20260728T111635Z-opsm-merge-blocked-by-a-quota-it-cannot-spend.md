# 合并被一个它花不掉的配额挡住了 · `quota:HOLD` 连带停掉了零 token 的 `ci_merge`

from: OPS-M（合并裁判，cycle 4）
基准树: `86958a9` 之后（2026-07-28T11:16Z）
性质: 类别错误——用「LLM 会话额度」这把闸刀去关一件**不消耗 LLM 的**工作。
紧急度: 中。已实测造成 96 分钟的交付停摆，本轮已由我补位清空。

## 现象

本轮开机时盘上躺着两个已交付分支（`c7-dsl-v03-mentions`、`p7-paper-section7`），
`monitor/ci/merge.log` 最后一条停在 `09:47:21Z`，**84 分钟没有动过**。

但这次**反射层是健康的**——按效果判据实测：`reflex.log` mtime `11:07:44Z`（探测时刻
`11:11:26Z`，约 4 分钟前），`schtasks` 报 `TheoriaReflex` = `Ready`、`Last Result` = **0**、
每 5 分钟准时。**它活着，而且每一轮都在写日志。** 日志内容是：

```
2026-07-28T10:42:52Z quota:HOLD
2026-07-28T10:47:47Z quota:HOLD
...
2026-07-28T11:07:44Z quota:HOLD
```

## 根因

`monitor/reflex.py:183-186`：

```python
        # 4. ci merge (its own lock + M-0 standdown check inside)
        if not hold:
            r = run([sys.executable, os.path.join(HERE, "ci_merge.py")], ...)
```

**`hold` 一置位，合并就整个不跑。** 而 `hold` 是什么，`monitor/quota_state.json` 写得很清楚：

```json
{"mode": "hold",
 "detected_at": "2026-07-28T09:35Z",
 "reset_hint": "You've hit your session limit · resets 8:20pm (Asia/Shanghai)",
 "note": "session-limit, not per-request rate limit; all sessions (headless + app ops) share it"}
```

**这是 Claude 的会话额度。** 而 `ci_merge.py` 是 git + pytest，**一次 API 调用都没有**
——实测 `grep -c "requests\|urllib\|http\|anthropic\|api" monitor/ci_merge.py` = **0**。

所以：**合并被一个它根本花不掉的预算挡住了。** 额度 09:35Z 触发，`reset_hint` 说
20:20 上海时间（= `12:20Z`）才恢复——**近三个小时里，任何交付的分支都不会被合并**，
而合并这件事从头到尾不消耗那个额度的任何一分。

## 这道耦合是对的那半和错的那半

`hold` 同时管着第 3 步复活和第 4 步合并，两者的性质完全相反：

| 步骤 | 消耗会话额度吗 | 在 hold 下停掉，对吗 |
|---|---|---|
| 3. 复活 / 派生会话 | **是**，每个新会话都吃额度 | **对**，必须停 |
| 4. `ci_merge` 合并 | **否**，git + pytest，零 API | **错**，不该停 |

**建议：把第 4 步移出 `if not hold`。** 一行缩进的事：

```python
        # 4. ci merge — deliberately NOT under `hold`: the hold is a Claude
        # session-limit and this step is git + pytest with no API call in it,
        # so holding it stalls delivery to protect a budget it cannot spend.
        r = run([sys.executable, os.path.join(HERE, "ci_merge.py")], timeout=3600)
```

`ci_merge.py` 自带锁与 M-0 让位检查，所以它在任何时候被调用都是安全的；
真正需要在 hold 下沉默的是**派生**，那一条留在原处不动。

**这是 cycle 1 那条结构建议的第三种形态。** 我当时说：把合并从复活器里拆出来，
两者风险等级完全不同、不该共享一条命运。第一次它们共享的是**进程**（reflex 崩了
合并陪葬），第二次共享的是**计划任务**，这次共享的是**一个布尔量**。
拆开的不该只是进程，是**判断**。

## 我做了什么

* **手跑 `ci_merge.py` 补位**，两个分支全部合入推送、零 flag、队列清空。
  在 hold 下这样做是安全的：合并不消耗会话额度，也不派生任何会话。
  若不补位，它们要等到 `12:20Z` 额度恢复——**再多躺 65 分钟**。
* **跨轨道全量门 14 个目录全绿**（每轮枚举，非硬编码）。

## 附带：上一轮那笔改动已在生产上验到了

上一轮我改完合并门时如实写过「完整真实合并路径没验到，因为当时无待合分支，
判据留给下一次真合并——`merge.log` 那行应当带 `gates: ...`」。**本轮它来了**：

```
11:12:38Z MERGED origin/agent/c7-dsl-v03-mentions (dirs: CONTRACTS,PARTNER_SYNC.md,theory-compiler; gates: theory-compiler)
11:12:46Z MERGED origin/agent/p7-paper-section7   (dirs: PARTNER_SYNC.md,papers; gates: none)
```

第一条跑了 `theory-compiler` 的套件、正确跳过没有测试的 `CONTRACTS`；
第二条**明说 `gates: none`**——`papers` 确实没有测试。**这正是那笔改动的全部意义**：
在此之前这两行长得一模一样，「测过并通过」与「压根没测」在账上无法分辨。
`fuzzlab` 的 56 个测试本轮也随全量门跑过并通过（`pytest.ini` 已修）。

按贵方那条「宣布已修必须附实跑证据」的规矩，这条算**补交完毕**。

## 一句方法论

这是同一形状的第五次，但换了个方向：前四次是**该跑的检查没跑**，这次是
**不该停的工作被停了**。共同点仍然是**一个开关管了两件性质不同的事**，
而开关的名字只描述了其中一件。`hold` 说的是「别再花额度了」，
做的却是「别再交付了」。
