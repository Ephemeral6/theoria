# E1-property-fuzz · 性质测试战役：用随机世界轰炸六引擎

基准 `Theoria.md`（1.10b 选型总原则：零噪声、要求精确——精确的东西必须经得起对抗性随机输入）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 尾十段、`engine-rig/` 各引擎 README，跑 engine-rig 测试绿了开工。
分支制：`agent/e1-property-fuzz` + 独立 worktree；push 分支不碰 master。领地：新建顶层 `fuzzlab/`（engine-rig 只读 import）。

目标：hypothesis（或自写生成器）驱动的性质测试战役，给论文的"引擎可信"提供弹药：

1. **随机小世界生成器**：参数化生成确定性网格世界（尺寸/对象数/规则型随机，seed 全记录）+ 对应轨迹；
2. **逐引擎不变量**（每引擎 ≥3 条，例）：mdl_segmenter——分割覆盖全帧且脚本可逆放回原帧；cegis_miner——前沿内每个守卫真的与全部证据一致、前沿外无一致守卫（完备性抽查）；zero_space——报出的每条律在全轨迹上真守恒；lp_potential——证书三条件独立复核器恒过、可采纳启发恒 ≤ 真实距离（BFS 小空间验证）；fd_adapter——返回的计划真的合法且长度最优（小空间对拍）；probe_frontier——报的分裂熵与暴力枚举一致；
3. 失败案例最小化后归档（失败是战利品：每个都是引擎的真 bug 或文档化的边界），**不修 engine-rig**——bug 以报告形式落 `fuzzlab/BUGS.md` 并 PARTNER_SYNC 知会；
4. 目标量：≥500 个随机世界过全套，seed 表落盘可复演。

技巧：逐引擎并行 subagent；失败最小化循环自动跑；Stop-hook：`fuzzlab/verify.sh` = 全 seed 复跑一致。留痕边跑边写 `fuzzlab/runs/<UTC>-e1/`。收工：RUN_STATE + MANIFEST(prompt_id: E1-property-fuzz) + PARTNER_SYNC + push。全程自主。
