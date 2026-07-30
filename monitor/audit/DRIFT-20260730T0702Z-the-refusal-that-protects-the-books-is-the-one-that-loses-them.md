# DRIFT-the-refusal-that-protects-the-books-is-the-one-that-loses-them
severity: high
dimension: 7（单向门／不可能变红的检查）

**pin:** `origin/master = 304ad651` @ 2026-07-30T06:34:27Z。
`git status --porcelain arc-recon/ proxy/` 在开工前后**均为空**——本节所有引用来自干净工作树，
等同于 pin（差异仅 CRLF 检出）。全套 `cd arc-recon && python -m pytest -q` → **326 passed, exit 0**。

---

## claim

`arc-recon` 在本区间新增的三道防线，各自有一个只有入口没有出口的地方；**其中第一条最重，
因为它在一条花钱的路径上，而它的失败形态正是同一个 commit 在隔壁分支上刚修好的那一个。**

---

## 一、结算守卫在记账之前抛异常，于是钱花了、账丢了（high）

`arc-recon/canary_schedule.py:392-397`：

```python
settlement_error = None
if gate is not None and reservation is not None:
    if "actions_executed" not in run:
        raise RuntimeError("the sweep returned no actions_executed, so there is nothing "
                           "honest to charge the pool -- refusing to settle at zero")
```

`raise` 在 `:435` 的 `_record_outcome(config, state, profile, record)` **之前**。
而**同一个文件、同一次改动**在隔壁分支上把这件事做对了——`:442-443`：

```python
if settlement_error is not None:
    raise settlement_error
```

即：先记账，再抛。**两条分支，同一个作者，同一次提交，一条延后抛出、一条当场抛出。**

这个文件自己在 `:405-413` 把这种形态的危害写得清清楚楚：

> The actions are **ALREADY SPENT** by the time this runs -- replay has returned. Refusing to write
> the record does not un-spend them; it only makes the next invocation repeat the spend ...
> **A standing task in that state re-spends on every wake-up and can never record progress.**

**实测**（在仓库之外的副本上，用它自己出厂的 fixture：`fake_replay(..., drop_actions=True)` + `FakeGate`）：
RuntimeError 如期抛出，随后 `sched.load_state()["profiles"]["quick"]` 是**空的**——
状态确实丢了。第二次实测：`sched.main(["run","--profile","quick","--force"])` **根本不返回退出码**，
RuntimeError 直接穿出 `main()`（`:647-652` 只映射 `SpendGate*` / `NoReservation`），
于是 CLI 以 shell 退出码 1 结束——而 `canary_schedule.py:46` 把 1 定义为
「**DRIFT —— incident filed, campaigns frozen**」。一个未被分类的崩溃因此冒充了一个最重的裁决。

**测试为什么没抓到**：`arc-recon/test_canary_schedule.py:550-565` 对这条路径只断言
`pytest.raises(RuntimeError)` 与 `gate.charges == []`；它的兄弟 `:524-548` 断言了「状态必须存活」
这条性质，**却从没被应用到 no-count 这条分支上**。

**可达性，说不利于自己的一面**：当前 replay 路径总会给出 `actions_executed`，所以这是潜伏的。
但 `proxy/var/spend_gate.jsonl` 的 **seq 12487** 是一条 `canary-quick`、`actions: 0` 的结算，
在 `canary_runs.jsonl` 里没有对应行——那条历史异常的形状恰好落在这里，
而该 run 自己的 `RUN_STATE` 把它的成因登记为**未解释**。

---

## 二、战役冻结是一道真正的单向门：没有任何代码能清掉它（medium）

`arc-recon/canary.py:169-170` 写 `{"frozen": True, …}`。
`:176-182` 的 `how_to_clear` 指名了出口：

> Do not delete this file. Adjudicate the drift first: either ... `canary.py rebaseline --reason ...`

而 `arc-recon/canary.py:533-572` 的 `def rebaseline(...)` 写 `CANARY_PATH`、报 incident，
**从头到尾没有引用过 `FREEZE_PATH`**。

`FREEZE_PATH|campaign_freeze` 全 `arc-recon/*.py` 共 11 处命中：一个写者（`canary.py:169`）、
一个读者（`:189`）、一处断言（`:194`）、两处测试 monkeypatch、其余是文档串。
**没有任何地方写 `frozen: False`，也没有任何地方 unlink 这个文件。**

按契约的两问回答：**谁把它退出来——没有人，代码里没有出口。那条路径今天被调用过吗——没有。**
`arc-recon/data/campaign_freeze.json` 磁盘上不存在，`canary_runs.jsonl`（6 行，全是 `PASS ×4`）
里没有 DRIFT。**所以严重度在门上，不在事故上。** 一旦进门：`canary_schedule.py:325`
永远返回 `gated`（退出码 5），不带 `--force` 出不来；`assert_campaigns_unfrozen()` 对其他所有赛道抛异常，
而没有任何脚本化的解法。

---

## 三、唯一能看见本地缓存的仪器，指着两个它不可能落在的目录（medium）

`CLAUDE.md` 说得很重：本地跑不打 API、不进 `recon_ledger.jsonl`、
`contamination.py` 的审计会一路绿——**「the guard is the only instrument that sees it」**。
那个仪器就是 `scan`，由 `arc-recon/verify.sh:89-90` 驱动：

```bash
python local_engine_guard.py scan environment_files ../environment_files
```

`local_engine_guard.py:751-755` 的 `scan` **只接受显式根目录，没有发现逻辑、没有默认值**。
而 guard 自己的测试写着（`test_local_engine_guard.py:229-232`）：
「本仓库没有 Makefile，所以上游 agent 仓库只能是一个**子目录**，`make -C <dir> play-local` 才是自然写法」
——即：它自己假设的检出位置，其 `environment_files/` **不被上面两个根中的任何一个覆盖**。

我读跑了这一步：两个根都报 `absent -- nothing cached, nothing to refuse`，退出 0；
深度 ≤4 的 `find` 找不到任何 `environment_files` 目录。
再加上 `.gitignore:30` 的 `environment_files/` 是**不带前导斜杠**的模式，**在任何深度都匹配**,
所以嵌套一层的缓存对 `git status` 也是隐形的。
**今天不致命（哪里都没有缓存），但这道闸门现在是空过的，而且会继续对着一个深一层的缓存空过。**

`verify.sh` 本身是干净的：`step()`（`:24-34`）是朴素的 `if "$@"; then … else fail=1; fi`，
没有管道、没有 `|| true`、没有子 shell，`:99` 是 `exit "$fail"`。**问题在它看哪儿，不在它认不认。**

---

## 顺带两条，不单独开档

* **`canary_schedule.py:292-296` 的 docstring 说 `proxy/spend_gate.py`「尚未在 master 上，
  所以 `ImportError` 是一个真实状态」——它在 pin 上是被跟踪的**
  （`git ls-tree 304ad651 proxy/spend_gate.py` → blob `654720fe`），`from proxy.spend_gate import
  SpendGate` 在 pin 上成功，同区间的 S22 跑还真用了它。那个 `"spend_gate": "absent"` 分支是死的。
  这几行**不是本区间改的**，属于「区间碰过的文件里的既有陈旧」，记在这里备查。
* **S22-RESIDUE-FULL 的取证引用指向一个 gitignore 掉的文件。** `RUN_STATE.md:69/:135/:149`
  引 `spend_gate.jsonl` 的 seq 12998 / 13244-13246 / 12487——我逐条核过，**全部属实、分毫不差**。
  但 `git check-ignore -v proxy/var/spend_gate.jsonl` → `proxy/.gitignore:3:var/`，
  而该 run 的 `MANIFEST.json` **没有 `files[]`**。四个必填键齐全，`files[].sha256` 按 `CLAUDE.md`
  是可选的——所以一笔 32 动作花费的凭据，不会出现在 Phase 4 的释出清单里。低。

---

## 纪律维（第 1 维）：查了，是干净的——这一条我特意写下来

* **密钥零泄漏。** `ARC_API_KEY` 的字面值在 pin 的整个被跟踪树里不存在
  （`git grep -l -F <value> 304ad651` 与前 10 字符各查一次，均 rc=1；值从未被打印）。
  对区间内每一行新增做了 28+ 位字母数字串的形状扫描，10 处命中全部有主：
  一处是切堆的 sha256（`local_engine_guard.py:101`），八处是两个新 MANIFEST 里的
  `sha256` / `base_commit`。
* **`claim_set.json` 干净。** 本区间的 diff 只有 8 行，全是账本计数（`ledger_lines` 1231→1273）；
  `sealed_games_contacted` 两处都还是 `[]`。
* **封存局 id 出现在新代码里——查了，判为不构成违纪，理由写下来备核。**
  `test_local_engine_guard.py:203` 有 `re86-8af5384d`，`:358-492` 用 `ls20-9607627b` 做 fixture
  目录名，`:154-155` 的注释点了五个 s 开头的封存局。共 18 处命中，**全部在 guard 的代码、
  测试与注释里，零处在请求体、零处在 `recon_ledger.jsonl` 的新增行、零处在含有局面内容的 fixture 里。**
  判据：切堆禁的是**玩、看、读关于它的东西**；而 `piles.json` 本身就以被跟踪的形式列着全部 21 个
  封存 id，所以「写出 id」这件事仓库早已在做且必须做——**一个能拒绝封存局的守卫，
  必须有测试点名封存局，否则那些测试就成了不可能变红的检查。** 这是命名不是阅读。
  单独记一句供监控留意：`ls20` / `ft09` 已被 F-11 隔离，而 `re86-8af5384d` 没有。

## suggest（监控裁决，我不执行）

1. **一、把 `:392-397` 的 `raise` 改成和它隔壁 `:442-443` 一样的形状**——赋给 `settlement_error`，
   `_record_outcome` 之后再抛。改动极小，而且**同一文件里已经有正确写法可抄**。
   同时把 `test_canary_schedule.py:524-548` 那条「状态必须存活」的断言**也套到 no-count 分支上**，
   否则下次还是没有阴性样本。
   顺带把这个 RuntimeError 纳入 `main()` `:647-652` 的退出码分类——现在它冒充退出码 1，
   而 1 的语义是「DRIFT，incident 已立，战役冻结」。
2. **二、要么给 `rebaseline` 真的加上清 `FREEZE_PATH` 的那一步（它的 `how_to_clear` 已经这么承诺了），
   要么把 `how_to_clear` 改写成「这需要人手动删，且删除本身要立 incident」。**
   现在是最坏的第三种：文档指着一个不存在的出口。
3. **三、`scan` 要么自己发现（从仓库根递归找名为 `environment_files` 的目录），
   要么 `verify.sh` 把根列表改成一次全树扫。** 现在的两个硬编码根，按 guard 自己测试所设想的
   布局（上游仓库作为子目录）就是错的。

---

## 附录（OPS-A cycle 50，08:2Z）—— 同一形状的第二个实例，而它证明这不是一次疏忽，是**一个已经写好的修法没有传播到一个函数体之外的调用点**

pin `13bbcad9`。本附录不新开报告：正文 §一 已经把「先记账，再抛」一般化了，
这是它在第二个文件里的实例。**值得写下来的是差别，不是相同。**

### 一、实例：`exam/tools/sealed_drill.py:862` 的 `build_items()` 在任何 `write_json` 之前

`run()` 里 `build_items(spec_dir, out_dir)` 在 `:862`，而全部 `write_json` 在 `:925-927`。
`build_items` 能抛的东西全都会不经捕获地逃出 `run()`：`OracleTruncated`
（`exam/drill_wrapper.py:226`，`NODE_LIMIT = 400_000`）、`:408` 的 `guard.assert_synthetic_world`、
`:422` 的 `Variant` 校验。

**用合法的、通过完整校验的变体规格实跑复现，未打任何猴子补丁**
（`t3-full-house`，`step_limit: 400`，`win_tighten score_at_least 9999`）：

```
exam.drill_wrapper.OracleTruncated: t3-full-house: composed search exceeded 400000 nodes
exit code = 1
files written: variant_specs/drill-probe-large-budget.json   ← 仅此一个
```

无 `DRILL.json`、无 `truth.json`、无 `sheet.json`。而且 `OracleTruncated` 还不是最可能的触发器——
新变体里一个拼错的 `world` 或一个畸形算子会更早撞上 `:408`/`:422`，那是远比 40 万节点普通的失误。

### 二、**差别在这里，也是本附录唯一的贡献：正文那条丢的是账，这条留下的是一个陈旧的绿**

`DEFAULT_OUT`（`:89`）指向 `exam/runs/20260729T1030Z-V6-exam-on-sealed-dryrun`，
一个**被 git 跟踪**、里面躺着已提交的绿 `DRILL.json` 的目录。而 `build_items` 在 `:424`
**先写下每个变体规格**，才在 `:445` 调 `solve()`。对着那个目录的副本实测：

```
before:  DRILL.json md5 = 0c5df267...   variant_specs = 10 files
run:     exit=1
after:   DRILL.json md5 = 0c5df267...   variant_specs = 11 files
```

**输入被悄悄换掉了，判决没动。** 一个存证目录因此持有一个与自己输入不再对应的绿。
正文那条的危害是「钱花了、账丢了、下次重花」；这条的危害是「什么都没花，但存证在说谎」。
**这比正文那条更接近本项目最怕的东西**——`Theoria.md` 的整套纪律建立在 `runs/` 可信之上。

而且 `_gates`（`:723`）消费的是 `payload["findings"]`，所以这一抛**跳过的不是一个闸门，是全部**
（构造对照、证书、见证、校准），与文件自己在 `:9-10` 的承诺
（*"every gate is evaluated -- an early failure does not hide a later one"*）直接冲突。

### 三、**最要紧的一句：修法已经在同一个文件里了，作者写过一遍，只是没往前挪一个调用点**

`:333-339` 的注释逐字：

> `# M3: this used to escape and kill the run with a traceback, so a doctored cut produced no`
> `# DRILL.json and no RED block at all -- which contradicted the header's promise that every`
> `# gate is evaluated.`

`fire_the_guard` 被这样修好了；**紧邻的下一条语句 `build_items` 没有。**
所以这不是「作者不知道该怎么做」，而是**同一函数体内、同一作者、同一次修复，隔一个调用点就没有传播**。
这比正文原来的一般化更强：正文说的是「一个分支写对、一个写错」，这里是
「**已经诊断过、写过修法、并在注释里解释过为什么要这么修，然后没有应用到隔壁**」。

### 四、severity 与我自己的削弱

**medium，不是 high。** 三条削弱，都写下来：`DRILL.json` 在全树**没有任何程序化消费者**
（只有 `exam/DECISIONS.md`、`SEALED_DRILL.md`、`STATUS.md`、`PARTNER_SYNC.md` 与一个板面文件提到它）；
退出码仍然变红（未捕获异常 → rc 1）；`test_sealed_drill.py:35-37` 的模块级 fixture 直接调
`drill.run()`，所以在测试套里这一抛会让 53 条测试全部 setup 报错——很响。
**损失被限制在独立/CI 调用路径上**，而那正是存证目录被写坏的那条路径。

### 五、同一次扇出里被我**杀掉**的、本可以成为第三条的东西

`test_no_drill_item_claims_search_credit_without_a_measurement`（`test_sealed_drill.py:521`）
我一度判为「四条断言全是字面量自比、不可能变红」。**实跑推翻：** 把 `sealed_drill.py:517`
还原成修复前的裸 `"search_credible": True`（无 `state_space` 记录），该测试在 `:562` 失败——
**它是一条真正的回归钉。** 它的 docstring 第一行就写明契约是「必须从记录里读出、不得断言」，
不是量级。而我用来定罪的 `MAX_ENUMERATION = 200_000`（`rubrics_verdict.py:123`）管的是
`enumerate_states` 这个**针对 `Level` 的另一个枚举器**，drill 从不调用它；drill 自己的上限是
`NODE_LIMIT = 400_000`。**是我把两个同名不同管辖的常量当成了同一份契约。** 不归档。
（顺带一条对 RES-3 的更正：`worldgen/core/world.py:259` 的 `reachable(limit=200_000)` 约束的是
**原始世界状态**，不是复合状态空间——实测 `t3-full-house` + `step_limit=100` 可以合法产出
217,198 个节点且不截断。`monitor/inbox/20260730T0300Z-RES-3-…` 那条的机制描述需要这一处修正。）
