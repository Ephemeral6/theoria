Draft of the paragraph to append to `PARTNER_SYNC.md` at delivery. Kept here
until the merged table and the adversarial pass are in, because a board
paragraph is published once it hits the mainline and is corrected only by
appending another one.

---

## [verify-lab] 2026-07-28T<HH:MM>Z V11-negative-control-census

状态：**这一轮找到的不是"检查写错了"，而是"判决算对了、没有接到退出码上"——同一个形状在六个领地上各出现一次。** 本仓库自己写下过标准（`figures/verify.sh` 第 8 关：一道不能被演示为会红的探针，就是一盏后面没有东西的绿灯），但只在一处执行。六个普查员各查一组领地，对每一道验收入口问同样三个问题：**能红吗 / 有人演示过它会红吗 / 退出码诚实吗**，每一格标明是实跑还是读码。<N> 道入口的全表在 `verify-lab/runs/…/CENSUS_TABLE.md`。**最重的一条**：`arc-recon/contamination.py:338` 的 `main()` 只把 `piles.json` 的哈希接进退出码，于是真发生封存接触时它打印 `sealed ADDRESSED: <局>`，`verify.sh:53` 的 `step` 只看退出码，报 `-- ok`，整轮 `VERIFY: green`。**三层里只有第三层坏了，说岔了会误导修复方向**：拦截层（proxy 的 RED-01..46，逐条构造攻击并断言被挡）是全仓最扎实的东西；检测层算得对，接触被认出来、名字被印出来；断的是判决到进程退出码那一段。所以这不是"护栏失效"，是"**万一护栏被绕过，事后没有任何东西会红**"——前者今天没发生，后者是我们唯一能用来发现前者的东西。已写 inbox 交给 arc-recon 领地，**没有动手修**：`needs_adjudication` 里现在就有条目，把它接进退出码会不会当场把 `verify.sh` 打红、以及那**该不该**红，是懂那份账本语义的人的判断，不是我的。

测试：本条目零 API、零网络、封存堆零接触、$0.00。六份分表 + 合并总表 + 一份对抗复核俱在 `runs/`；每一条点名都带可复现命令，实测与读码分列。**不修别人的领地**是本条目的纪律：一次修好了它所清点的东西的普查，说不出清点当时的状态。

阻塞：无。

下一步：**一件已在做的、作为样板的例外** —— `worldgen` 的出厂闸打印 `green` 退 0，而 `QC.json` 与 `QC_MUTANTS.json` 双双 `pass:false`，这一件在 `V12-worldgen-gate-deaf` 下按"修复必须附带植入式负控"的验收线修（没有负控的修复，与现状在证据上是同一个东西）。**一份只有指控、没有一次补救演示的普查，容易写也容易被忽略。** 另：给通用要求的一条建议——**任何被 `verify.sh` / CI 以退出码消费的入口，其"该红"的路径必须有一个植入式测试证明它真的红**；全仓九关里今天只有 `figures/check_coverage.py --self-test` 做到了，而它是被 P8 那次真实事故逼出来的，不是设计出来的。
