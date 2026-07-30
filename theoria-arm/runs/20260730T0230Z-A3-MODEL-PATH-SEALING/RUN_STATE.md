# A3 · 模型这条路的封存保证

**RES-1，2026-07-30，cycle 39。离线 leg，不花钱。**

## 〇 为什么这件事落在 A3 头上

监控 2026-07-29 第二次裁决驳回 A3 开跑，第 1 条理由是「真臂 66 条
`bypass_attempt`——封存保证只在 proxy 侧验过（A11 在飞）」。本轮先派了一路只读
复核去问「这条今天还立不立」，结论分成两半，而两半都不是原文写的那样：

* **「66 条在真臂上」是假的。** 131 行记录全部是 `arm: probe` /
  `run_id: probe-model-proxy`，来自臂存在之前的一次手工探针（D-P8-002）；
  A11 的逐条分类里 `c_actual_bypass` 66 个 **false**，`game_id` 键一个没有，
  25 个封存 id 连同词干逐一子串匹配零命中。**「A11 在飞」也是假的**——
  A11 已合入 master（`fd2ca10a` / `d8a83884`，两个内容提交都是 master 的祖先）。
* **但 A11 自己的裁决比这条工单更重，而且它在 master 上。**
  `theoria-arm/runs/20260729T013000Z-A11/FINDINGS.md:141-152` 逐字写着：
  proxy 侧封存护栏成立；**真臂侧尚不成立**，三条——(i) 臂进程持有活凭据，
  (ii) **模型这条路完全不过封存护栏**，(iii) 模型子进程的环境清洗可被配置绕开。
  「66 条不是问题。问题是找它们时翻出来的这三条，而它们没有一条被现有的检查覆盖。」

A3 是一件**会做模型调用**的花钱战役，(ii) 与 (iii) 正对着它的开跑路径，
而 A11 交付时没有为它们建条目。theoria-arm 这块领地当前由 A3 占着（工作板上
A16/A8/E3/R4 全部因此 territory-blocked），所以没有别人能写它。
**本 leg 就是把 (ii) 与 (iii) 关掉**，(i) 见末节，它不是我能在本领地关掉的。

## 一 F2：模型这条路从来没有咨询过切堆

环境这条路是有护栏的：`Run` → `EnvProxy` → `SealedPileGuard`，
`tests/test_bypass_negative.py` 把它钉死了——封存 id 进去，403，上游零请求。
**模型这条路一个字都不沾这套东西**：`harness/modelcall.py` 起一个 `claude -p`
子进程，对着另一个上游说话，臂与 desk 之间没有任何环节读过 `piles.json`。

唯一存在的检查是 `ModelDesk.forbid_in_prompt`，而它此前只装了**正在玩的那一局**：

```python
forbid_in_prompt=(game_id, game_id.split("-")[0])
```

读起来像够了，其实不够。这不是想象出来的管道——**第一组之所以存在**，正是因为
一次对抗性探针通过引擎 traceback 把 **6 处 `g50t`** 塞进了一个 20,975 字符的
prompt（`modelcall.py` 的 `forbid_in_prompt` 注释逐字记着）。而那条通道
**不知道也不在乎**它携带的 id 属于哪一堆：一个封存局的词干只要出现在某个
run 目录的 slug、Lean 诊断的绝对路径、或 `world/adapt.py` 记下的 `traceback` 里，
就同样进得去。

封存 id 进模型上下文是 `Theoria.md:353` 第四条通道**从里面**被打开：desk 是个
预训练模型，对它点名一个封存局，与 `CLAUDE.md` 逐字禁止的「读关于封存局的东西」
是同一种污染。

**改法**：`inner/loop.py` 新增 `_forbidden_substrings(game_id)`，
在原来那两项之外，把**封存堆全体的 id 与词干**加进去，来源是
`proxy.guard.SealedPileGuard`（另一赛道的文件，**只导入，不编辑**），
即**从冻结的切堆推出，不是抄一份字面表**——切堆变宽时这张表不会被落在后面。
读不到切堆则**失败关闭**：一个数不出封存堆的 run，没有资格承诺它把封存堆挡在了
prompt 外面。

## 二 F3：注释说它清洗，代码没有清洗

`_invoke` 里那两行注释写着 desk「must not inherit a base URL that would send it
somewhere unrecorded」，**而下面只有一行 `env.pop("ARC_API_KEY", None)`**。
`ANTHROPIC_BASE_URL` 一直原样继承自启动这条臂的那个 shell。

后果的形状是这件事真正的分量所在：操作者 shell 里一个 export，
就把**每一次 desk 调用**改道到这个账本永远看不见的端点——**而且什么都不会红**。
成本是从 CLI 自己的信封里回来的（`total_cost_usd`），所以那次 run 照样出一份
完整的、可信的、定价正确的记录。**一个被静默改道的 desk 比一个坏掉的 desk 更糟。**
`ANTHROPIC_BASE_URL` 也不是假想的名字：本文件的模块 docstring 里就记着
`ANTHROPIC_BASE_URL=<model proxy> claude -p ...` 这次实活。

**改法**：`SCRUBBED_FROM_DESK_ENV = ("ARC_API_KEY", "ANTHROPIC_BASE_URL",
"ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY")`，`_invoke` 逐个 pop。
后两个是「改道之后让对面真的应答」所需的凭据。CLI 用自己存的 OAuth bearer 认证，
所以拿掉这四个不影响它工作；将来若真需要把 desk 指到别处，那应当是一次**有记录的
行为**（显式传入并写明去了哪儿），而不是从某个 shell 继承来的。

## 三 阴性对照：两处修复各自回退，四条测试全红

`tests/test_desk_sealing.py`，4 条，每条**自带阳性对照写在同一个函数里**。

| 回退 | 结果 |
|---|---|
| `_forbidden_substrings` 退回只装当前局 | `test_every_sealed_id_and_stem_is_forbidden_in_a_prompt` 红 |
| 同上 | `test_a_sealed_stem_in_a_prompt_is_refused_before_the_subprocess` 红（改为死在 `NoSpendBinding`，即检查确实没拦住） |
| `SCRUBBED_FROM_DESK_ENV` 退回 `("ARC_API_KEY",)` | `test_the_desk_subprocess_inherits_no_redirect_and_no_game_credential` 红 |
| 同上 | `test_anthropic_base_url_is_named_by_the_scrub_list` 红 |

**第一版的第三条测试是假绿，照录。** 它遍历 `SCRUBBED_FROM_DESK_ENV` 来决定
要检查哪些变量——于是**常量缩水时它跟着缩水**。实测：把常量砍回
`("ARC_API_KEY",)`，另外三条全红，**这一条绿**，因为遍历一个单元素元组就只检查
一个元素。**一条从被测代码里读出自己期望的测试，断言的是代码等于它自己。**
已改为在测试文件里另写一份字面表 `MUST_NOT_REACH_THE_DESK`，重复是故意的：
将来谁要缩小清洗范围，这里会红，缩小就必须在这里被论证。

阳性对照同样是承重的，不是装饰：env 那条测试还断言
`THEORIA_DESK_CONTROL` **活着到达**子进程、`PATH` 在场——否则一个空的或построен错
的 env 字典能满足上面每一条「不在场」断言。forbid 那条则断言另外三个**开发堆**
游戏**仍然可以被点名**——否则一个「把注册表里所有 id 都禁掉」的实现会通过全部
检查，同时让每一个 prompt 都发不出去。

## 四 顺手改的一条既有测试，以及它为什么本来就弱

`tests/test_arm.py::test_the_desk_env_drops_the_game_credential` 原来是
`assert 'env.pop("ARC_API_KEY", None)' in source`——一条**源码文本**断言。
它钉的是拼写，不是行为：**它在整个 F3 敞开期间都是绿的**，就在那句
「must not inherit a base URL」的正下方；反过来，一次什么也没改变的重命名会让它变红。
两个方向都错。已改为成员断言并在 docstring 里写明真正的断言搬到了哪里
（`test_desk_sealing.py` 断的是交给 `subprocess.run` 的那个 env 字典本身）。

## 五 测试与状态

* `cd theoria-arm && python -m pytest` → **247 collected，全绿**
* `python verify.py` → **green**（[1/3] suite / [2/3] 一次离线真跑 / [3/3] 制品自检：
  11 条账本记录、13 个 run 文件、17 个 manifest 字段、sealing clean、dev pile only）
* 本 leg **零 API 接触、零花费**：没有调用 `spend_gate.reserve()`，
  没有任何计费动作；只读 `piles.json` 的 id 列表。

## 六 没关掉的那条，以及它归谁

**F1（臂进程持有活凭据）本轮没动。** `harness/run.py:163` 在进程内起
`EnvProxy`，`proxy/env_proxy.py:79` 在那里读密钥——于是「臂内无任何凭据」
这句 `Theoria.md:305` 密封测试的原话，在**进程边界**这个读法下不成立。
这条要么改臂的进程模型（把 proxy 挪出臂进程），要么改那句话的读法并写明改了。
两者都不是一次 `theoria-arm/` 内的编辑能诚实完成的，**也不该由持有 A3 的人
顺手裁掉**——`p1-seal-test` 是 Phase 1 验收单上的一行，动它是监控的事。
已在本轮的 bus 汇报里点名。

同样照录：`STATUS.md:56` 与 `GAPS.md:20` 仍在用 `key_injected: true` /
「arm keyless」当作臂不持有密钥的证据，而 F1 说这个标志立不住这个结论；
`evidence/README.md:30` 仍写着「This is the sealing property working, not a bug.」，
而 A11 说那句话**多说了一步**（真正执行的是 `PASSTHROUGH_REQUEST_HEADERS`
白名单，`bypass_attempt` 只是观测点）。三处都在本领地，但改它们要改的是**结论
文字**而不是代码，与本 leg 的两条是不同性质的动作，留给 A16 或监控裁。
