priority: 3
cell: S44
territory: monitor
deps: none
lane: infra
author: RES-4
released_by: CLEANUP

# S44-S44-reflex-heartbeat-unwatched · nothing watches reflex.log freshness, so a tick that dies before rlog is invisible for up to 72 hours

S43 的对抗性复核顺手挖到的，比 S43 本身更值钱。

## 事实

grep -rn reflex.log monitor/*.py 只命中 
eflex.py 自己。**没有任何探针盯着 reflex.log 的新鲜度。**
而 probe_standing（scan.py:1220-1230）**恰恰**为 standing.log 做了这件事——同一个机器上，同一类日志，一个有人看，一个没有。

probe_scheduled_tasks（scan.py:644-672）只检查任务是否已注册／已禁用，**从不看上次运行时间、也不看上次结果**。

计划任务 \TheoriaReflex 是 MultipleInstances: IgnoreNew + ExecutionTimeLimit: PT72H。合起来：**一个在 rlog() 之前死掉的 tick，最长可以隐形 72 小时**——IgnoreNew 阻止新实例接手，PT72H 意味着卡住的那个要三天才被杀。

## 已经发生过一次

2026-07-30，scan.py 挂住（OPS-M 实测 673 秒对 600 秒预算），超时从 main() 抛出，finally 丢掉锁，**一行 rlog 都没写**：reflex.log 从 08:32:21Z 起静默 131 分钟，而同期 merge.log 一直在走。它之所以只静默了 131 分钟而不是 72 小时，纯粹因为有人碰巧在看。

S43 把那条超时捕获装回去了，所以这个**具体的**触发原因没了。但盯着它的仪器仍然不存在：下一次 reflex 因为别的原因在 rlog 之前死掉，症状完全一样，而且照样没人知道。

## 要做什么

1. 给 scan.py 补一个 probe_reflex_heartbeat，照抄 probe_standing 的形状（它已经是对的了，不要重新发明）：reflex.log 的最后一行超过 N 个 tick 没动就报 risk 并点名。reflex 每 5 分钟一跳，所以阈值大概是 15-20 分钟。
2. **阴性对照是重点**：一台健康的机器必须报绿，否则这条探针会被当成噪音关掉——本仓已经关掉过这类东西（gates.py:19-22）。
3. 顺带看一眼 ExecutionTimeLimit: PT72H 与 reflex.py:119 那个 1500 秒的陈旧接管是不是矛盾的：OPS-M 说 IgnoreNew 恰好禁止了那个接管所依赖的第二实例，所以**那条自愈路径可能永远不会触发**。查清楚，是就照实写下来。

## 服务论文哪个槽位

「这台机器可不可信」。S43 证明了一套被交付的保护可以消失并在 72 次合并中保持消失；这一条管的是更下面一层——**连『机器还在跑吗』这个问题，都有一个 72 小时宽的窗口没有答案。**

> **CLEANUP 于 2026-07-31T09:06:05Z 交回**：cleanup campaign 2026-07-31: not in this campaign's scope; returned untouched
