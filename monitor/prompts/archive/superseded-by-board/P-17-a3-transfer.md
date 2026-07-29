# P-17 · A3 跨关迁移彩排：C3 的第一份离线证据

基准文件是 `Theoria.md`（1.10a 的 domain/problem 切分：「说明书是 domain 跨关不变，关卡布局是 problem 逐关实例——C3『迁移』的严格含义就是 domain 带得走」；Claim C3）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 最后十段、`cold-start-a0/`（含 prime）与 `cold-start-a2/` 的全套做法，跑两者测试，绿了开工。
分支制：`agent/p17-a3-transfer` + 独立 worktree；push 分支不碰 master。
领地：新建顶层 `cold-start-a3/`。其余只读（A0/A2 的世界与流水线可 import 复用）；PARTNER_SYNC 只追加。

目标：自建一个**两关世界**——同一套机制（推动、按钮-门、传送），不同布局（墙、起点、目标、portal 位置全变）——验证两本书跨关带得走：

1. **第一关冷启动**：全环跑通（沿用 A0′ 的可逆机关设计——F-12 裁决已采纳的准则），theory.dsl 落成 domain（机制）+ problem₁（布局）两部分，playbook 至少入一条定理级条目（死锁或地标序）。
2. **第二关零重学验证**：携 domain + playbook 进第二关，只从首帧提取 problem₂（布局重建，不许重新挖规则）；直接 certify + plan。度量并落账：第二关的 theorize 轮数（预期 0 或仅裁决新布局）、引擎调用量、到首个 plan 的成本——**与第一关同量对照，这就是 C3 的账单形状证据**。
3. **对照臂**：同一个第二关从零冷启动一遍（不带书），成本对照表二列并排——「白嫖」的量化。
4. **负对照**：第二关故意换一条机制（比如 portal 变单向），验证带旧 domain 的 certify 能抓住（渲染失配/重放失配触发 theorize），而不是无声地错下去——迁移的安全阀也要测。
5. `A3_REPORT.md` 收束：C3 在离线世界的成立范围与限制（这为 theoria-arm 在线跨关直接铺路）。

红线：零 API；生成物不手改；真值只在裁判 subagent 手里（同 A2 纪律）。

技巧：两关的冷启动与对照臂并行 subagent；负对照单独一个；回路循环推进。

收工仪式：runs/ 归档（prompt_id: P-17）；PARTNER_SYNC 追加；push 分支。全程自主，不停下来问。
