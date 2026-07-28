# P-20 · 级联语义在线裁决：单动作到底会不会返回多帧

基准 `Theoria.md`（Phase 1「一件轨迹作业」：级联语义裁决——step 建模「动作→帧序列」还是「动作→单帧」；这是 1.8 留的悬案，A0 的 D-A0-004 暂选了单帧）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 尾十段、`arc-recon/README.md` 与 incidents 尾部、`proxy/LEDGER_FORMAT.md`，绿了开工。
分支制：`agent/p20-cascade-probe` + 独立 worktree；push 分支不碰 master。领地：`arc-recon/`，**只新增 `arc-recon/cascade/` 子目录**——不改任何既有文件（P-11 的分支可能未合并，避开它碰过的路径，合并才干净）。

目标：用最少的动作在开发堆上正面回答——是否存在返回 len(frame)>1 的动作（动画/内部 tick）？

1. 设计判别序列（先写预测再打）：优先选可能触发级联的动作（推动可动物、按压类），4 局各 ≤7 动作，总预算 ≤30；每个响应记录 frame 列表长度、逐帧哈希。
2. 结论三选一落 `arc-recon/cascade/VERDICT.md`：(a) 观测到多帧——step 必须建模帧序列，A0 的 D-A0-004 需要修订通告（PARTNER_SYNC 知会 theory-compiler 轨道）；(b) 全部单帧——单帧假设在观测范围内成立，写明覆盖范围与不能排除什么；(c) 混合/异常——如实分档。
3. 顺带免费拿：这 ≤30 个动作的帧序列同时是跨会话残留与金丝雀的补充样本，交叉核对已有基线。

红线：封存堆零接触；密钥经环境读取不落盘；预算硬顶 30 动作，先算后花；重试策略沿用 INC-005 的包络（别重蹈 H-A 短 ID 的初判覆辙）。

前沿工具要求：4 局并行 subagent 各打各的（独立上下文互不污染预测）；判决文本过一个对抗性 subagent（专挑「说得比证据满」——这个仓库已经为此栽过两次）；Stop-hook 式收工——`cascade/verify.sh` 断言账目完整（每个动作有请求、响应、帧哈希三件套）。

留痕：边跑边落盘（`arc-recon/cascade/runs/<UTC>-p20/`，每个 API 响应即刻写入）；上下文即将蒸发是默认。
收工：RUN_STATE + MANIFEST(prompt_id: P-20) + PARTNER_SYNC + push 分支。全程自主，不停下来问。
