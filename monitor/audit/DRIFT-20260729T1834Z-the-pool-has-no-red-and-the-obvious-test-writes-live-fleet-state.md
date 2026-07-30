# DRIFT-the-pool-has-no-red-and-the-obvious-test-writes-live-fleet-state

severity: high
dimension: 7（不可能变红的检查）
cycle: OPS-A 41
adversarial-review: 有，**跑了真的变异测试**（在 `%TEMP%` 副本上，仓库文件未动）。
判定 PARTLY REFUTED：结论被**实证加强**，但我原来说的机制错了，已按复核措辞改写。

## claim

**账号池现在是舰队派活的权威，而它的每一个判决都没有一条能变红的断言。**
更糟的一半：**把这个洞按最显然的方式补上，那条测试会写进正在运行的舰队的真实账号状态。**

## evidence

### 一、轮换判决：四个变异体全部存活

`monitor/tests/` 收集到 **222 个测试、21 个文件**。对 `quota.py` 跑覆盖率
（`test_quota.py` + `test_quota_autoexit.py` + `test_accounts.py`，37 passed）：
`quota.py:332-337` 与 `:384-386` 在 Missing 里，**一次都没执行过**。

在临时副本上做的四个变异，**全部 SURVIVED**（整套测试仍然全绿）：

| 变异 | 结果 |
|---|---|
| 整段删掉 `quota.py:382-386`（ROTATED 分支体） | **存活** |
| `:337` 改成恒 `return "hold"` | **存活** |
| `:337` 改成恒 `return "rotated"` | **存活** |
| 拆掉 `:327-330`「不许猜账号」的归属安全闸 | **存活** |

最后一条最难看：`quota.py:328-329` 的注释专门论证了「猜一个账号是危险的」，
**而那份论证没有任何断言在守着**。

### 二、新的派活闸门：两边都没有样本

`standing.py:165` 的 `not any(_acct.usable(a) for a in pool)` 是
`7a71b5ab` 之后决定六个常驻岗位起不起的**唯一**谓词。

* **测试侧**：全仓 222 个测试**没有一个 import `standing`**。
  `tests/test_standing_sweep.py` 名字像，实际只 import `board`（`:21`），
  断言全部走 `board.standing_verdict`。`scan.py:1109` 是懒加载，没有测试碰 `_fleet_rows`。
* **生产侧**：它自 **17:18:08Z** 起每一跳都被求值，**一次都没返回过真**。
  证据是四条 `START`（17:18:08 / 17:45:04 / 18:00:03 / 18:15:03Z），
  每一条都要求 `held == False`。
  （**不能**拿「日志里没有 `quota hold` 行」当证据——`elif held` 在
  `already running`／`busy` 之后，够不着；这是复核纠正我的一处。）

**绿的那一侧被证明会跑，红的那一侧从未存在过。** 按这仓库自己写在
`tests/test_accounts.py:4-6` 的标准（「每一道闸门都要有一个能让它变红的输入，
否则那道闸门只是装饰——20 道里 19 道从没被证明能变红」），这是**第 20 道**。

### 三、把洞补上的显然写法，会写进真实舰队状态

`monitor/tests/conftest.py:30-34` 的 `rig` 夹具只重定向了两样：

```python
    monkeypatch.setattr(quota, "LOGS", str(logs))
    monkeypatch.setattr(quota, "STATE", str(state))
```

`accounts.STATE` / `accounts.LOG` / `accounts.CONFIG` **一个都没动**。
而 `quota.py:335` 在轮换路径上调用 `accounts.mark_limited`，它
`save_state()` 到 **真的 `monitor/accounts_state.json`**、`log()` 追加到
**真的 `monitor/accounts.log`**。

今天之所以没出事，**只是因为归属先失败了**：rig 写出的日志不带
`_runner.py:122-123` 那个 `account=<id>` 头，`account_of_log` 返回 `None`，
`_rotate_on_limit` 在 `quota.py:330` 就返回 `"no-pool"`。
**也就是说：唯一挡住测试污染生产状态的东西，正是让这条分支测不到的那个缺陷。**

**而它只差一行。** 复核在临时副本里只用现成夹具就够到了那条分支：

```python
rig.dead_session('P-8', '=== runner start P-8 model=opus account=a ===' + ... )
assert quota.check() == 0                       # ROTATED
assert accounts.window_state('a') == 'limited'
```

它**通过**。所以这是**缺一条测试，不是夹具做不到**——
任何人接到「给轮换分支补测试」这件活，最自然的写法就是加上那个 `account=a` 头，
然后在**真实账号台账上**把一个真账号标成 limited、`limits_seen` 加一、
往 `monitor/accounts.log` 追加一行 `LIMITED`。

**这一条对审计员是致命的**：`monitor/accounts.log` 正是我上一世
（cycle 40，`DRIFT-20260729T1729Z-…`）用来证明「轮换器执行了 ≥6 次」的**唯一账本**。
一条按显然写法写出来的测试，会在审计员自己的证据基里伪造条目。
`tests/test_accounts.py:36-38` 有自己的夹具、三样都重定向了，**做对了**；
`conftest.py` 的 `rig` 没有。

## suggest

**顺序很重要，第 1 条必须先落地，否则第 2 条会自己踩雷。**

1. **先把 `conftest.py` 的 `rig` 补齐**：`accounts.CONFIG` / `accounts.STATE` /
   `accounts.LOG` 一并 `monkeypatch` 进 `tmp_path`。
   顺手改掉夹具 docstring——它现在说「its own state file, logs and registry」，
   对 `quota` 是真的，对 `accounts` 是假的。
2. **再补轮换的三个阴性样本**（做完第 1 条之后）：
   `others != []` ⇒ `"rotated"`；`others == []` ⇒ `"hold"`（16:32:09Z 真的走过这条，行为正确）；
   以及**轮换分支必须留下一条 history 条目**——这一条现在会红，
   正好同时把上一世那条一直没落地的建议变成可验收的。
3. **给 `standing.py:165` 一条能变红的测试**：造一个两个账号都 limited 的池，
   断言 `quota_held()` 为真。全仓第一条 import `standing` 的测试。
4. **把「归属失败」与「池为空」在日志上分开**。`quota.py:316` 的 `"no-pool"`
   与 `:330` 的 `"no-pool"` 是同一个字符串两个完全不同的原因——
   复核最初也被这个同名坑了一次（它以为测试挂在 `:316`，实际挂在 `:330`）。

## 复核改了我什么（留痕）

* **杀掉「夹具没配池，所以结构上够不到」**：`monitor/accounts.json` 是真的存在的，
  `conftest` 从没重定向 `accounts.CONFIG`，所以测试里读的是**真池**，
  `quota.py:316` 反而是死代码。挂点是 `:330` 的**归属失败**，不是没池。
* **杀掉「结构上不可能」**：差一行日志头而已，复核把它跑通了。
* **杀掉「删掉或改掉都没有断言会红」的后半句**：把 `:383` 的
  `if rotated == "rotated":` 改成 `if True:` 会**红掉 9 个测试**。
  不可达的只有**分支体** `:384-386` 与决策 `:332-337`，`:382-383` 本身每次 `check()` 都在跑。
* **加进来（比我派它去查的东西更重要）**：`conftest` 的 accounts 隔离缺失。
  这一条是复核自己发现的，不在我的问题清单里。

## 复现命令

```bash
cd monitor && python -m pytest tests/test_quota.py tests/test_quota_autoexit.py \
    tests/test_accounts.py --cov=quota --cov-report=term-missing -q
cd monitor && python -m pytest tests/ --collect-only -q | tail -1   # 222 tests
grep -rl "import standing" monitor/tests/                            # 空
sed -n '30,34p' monitor/tests/conftest.py                            # 只重定向了 quota
sed -n '36,38p' monitor/tests/test_accounts.py                       # 这个文件做对了
sed -n '335p' monitor/quota.py                                       # 写真实台账的那一行
```
