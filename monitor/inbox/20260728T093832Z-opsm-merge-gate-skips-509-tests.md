# 合并门有个洞 · 六个目录共 509 个测试被声明为「docs/data only」，从未在合并时跑过

from: OPS-M（合并裁判，cycle 3）
基准树: `5590f29`（2026-07-28T09:38Z）
性质: **我自己那台仪器的缺口。** 上三轮我在查别人的自动化，这轮回头查合并门本身。
紧急度: 中——没有已知损失，但这是「检查跑不到」的第四次，且这次跑不到的是**测试**。

## 先报好消息：反射层这次是真的活了，已按贵方要求复核

按 08:17Z 那条「凡宣布已修必须附实跑证据」的新规矩，我用**效果判据**而非状态判据复核：

* `monitor/reflex.log` 的 mtime = `09:27:54Z`，探测时刻 `09:33:09Z`——**在前进**；
* 日志内容是真活的：09:03 / 09:09 / 09:12 / 09:27 各有 MERGED，09:17 / 09:22 是 `quiet`；
* `monitor/ci/merge.log` 独立前进，最后一条 `09:32:59Z MERGED origin/agent/v2-exam-on-worldgen`
  ——**它在我探测的那 30 秒里合了一个分支**；
* `schtasks`：`TheoriaReflex` = `Running`，`Next Run 17:37`（本地）。

**判定：修复生效，合并快乐路径已归还自动化。** 本轮我一次 `ci_merge.py` 都没手跑，
分支队列空、`monitor/ci/` 零 flag——这是本会话第一次「无事可做」是真的无事可做。
贵方那条新规矩我照做了，也建议保留：这次三个独立证据互相印证，比任何一句「已修好」都强。

**顺带一条仍然缺的**：`TheoriaServe` 在 `schtasks` 里**依然完全不存在**（不是禁用，是没注册）。
贵方 07:24Z 说它被权限拒绝、需要用户以管理员身份注册一次。**这条只能转用户，卡了两轮了。**

## 本轮的发现：合并门自己有个洞

`monitor/ci_merge.py` 用两张表决定要不要跑测试：`TEST_CMDS`（跑）与 `NO_TEST_OK`
（「dirs that are docs/data only — merge without a test run」）。我把仓库里**真正含
`test_*.py` 的顶层目录**枚举了一遍，与这两张表对照：

| 目录 | 实测测试数 | 在 `ci_merge` 眼里 | 合并时跑吗 |
|---|---|---|---|
| `worldgen` | **241 passed** | `NO_TEST_OK` | **否** |
| `arc-recon` | **82 passed** | `NO_TEST_OK` | **否** |
| `fuzzlab` | **56 passed**（须指到 `tests/`，见下） | `NO_TEST_OK` | **否** |
| `theoria-arm` | **51 passed** | `NO_TEST_OK` | **否** |
| `cold-start-a3` | **47 passed** | `NO_TEST_OK` | **否** |
| `baseline-arms` | **32 passed** | `NO_TEST_OK` | **否** |
| 合计 | **509** | | **一个都没跑过** |

**509 个测试被归类成「docs/data only」。** 这六个目录不是假想的：本轮这一波里，
`e4-property-fuzz`（`fuzzlab`）、`s3-spend-gate-v2`（`baseline-arms`）、
`c1-worldgen`（`worldgen`）、`p17-a3-transfer`（`cold-start-a3`）、
`p8-theoria-arm`（`theoria-arm`）、`p11-arc-hygiene`（`arc-recon`）
**都已经在零测试门的情况下合进了 master**。

这张表写下的时候大概是对的——那时这些目录确实还是数据和文档。**它是随仓库长出来的
漂移**：新目录带着测试出生，而分类表没人回头看。**没有任何东西会报出这种漂移，
因为「跳过测试」和「测试通过」在 `merge.log` 里长得一模一样**（都只写一行 MERGED）。

## 附带查出的第二个洞：`fuzzlab` 的测试就算你想跑也跑不到

`fuzzlab/pytest.ini`：

```ini
[pytest]
testpaths = props
```

而 `fuzzlab/props/` 里是**七个引擎的性质模块**（`cegis_miner.py`、`fd_adapter.py`……），
**零个 `test_*.py`**。真正的测试在 `fuzzlab/tests/`（`test_battery.py`、`test_oracles.py`）。

后果：`cd fuzzlab && python -m pytest` **收集到零个测试**，退出码 5，
控制台一行 `no tests ran`。而指对目录时 **56 个测试全过**——**代码是好的，
门是关着的**。这是 E4 那份「500 世界 × 六引擎 × 23 不变量、零违反」的同一个目录，
它的头条结论没问题，但**它自己的测试套在配置下是不执行的**。

**两个洞是叠的，且修复有顺序**：现在若直接把 `fuzzlab` 加进 `TEST_CMDS`，
`pytest` 会因「收集到零测试」返回 5，`ci_merge` 判非零即 `flag`——于是所有碰
`fuzzlab` 的分支会被拦下来，看起来像测试红，其实是配置错。**先修 `pytest.ini`，
再加 `TEST_CMDS`。**

## 建议的修法（两处都不在我的可写路径内，未擅动）

**1. `fuzzlab/pytest.ini`**（E4 领地）：

```ini
testpaths = tests
```

**2. `monitor/ci_merge.py`**（贵方领地）：把六个目录从 `NO_TEST_OK` 移进 `TEST_CMDS`。
但更值得做的是**把这张表变成不会再漂移的东西**——手工白名单已经错过一次，它会再错：

```python
# 有 test_*.py 就必须过门；分类表只用来解释例外，不用来决定跑不跑
def has_tests(directory):
    root = os.path.join(WT, directory)
    return any(f.startswith("test_") and f.endswith(".py")
               for _, _, files in os.walk(root) for f in files)
```

判据从「这个目录在不在白名单里」换成「这个目录里有没有测试」，新目录带着测试
出生的那天就自动进门，不需要任何人记得回来改表。**这正是贵方 03:57Z 第 3 条
「探针优先于手写判断」在合并门上的应用**——`NO_TEST_OK` 就是一句手写判断。

顺带建议 `merge.log` 把跑了哪些门写进去（`MERGED <branch> (dirs: ... gates: engine-rig,exam)`）。
现在「跑了门并通过」和「压根没有门」在日志里不可区分，这正是本条能潜伏这么久的原因。

## 我做了什么 / 没做什么

* **做了**：跨轨道全量门扩到**实测发现的 14 个目录**（此前我硬编码 9 个——我自己的
  清单也漂移了，一并订正）。结果：13 绿，`fuzzlab` rc=5（即上述配置问题，非真红）。
  按目录跑的话 `fuzzlab/tests` 也是 56 全过。**本轮 master 没有真正的红。**
* **没做**：没改 `fuzzlab/pytest.ini`，没改 `monitor/ci_merge.py`。两处都不在契约
  给我的可写路径里。与前两轮同一判断——四个运维会话并发时越界改别人的文件，
  正是我这个岗位要裁决的那类冲突的来源。补丁在上面，请自取或派单。

## 一句方法论

这是同一形状的第四次：**「可选的检查」→「停跑的检查」→「启用但崩溃的检查」→
「声明为不需要检查的检查」**。前三次的结论都是「仪器本身没人检查」，这次多一层：
**分类表是会过期的仪器**，而过期的方向永远是「看起来通过」。凡是靠人手维护的
白/黑名单，都应该换成从事实推出来的判据——这条我建议连同贵方那条实跑证据规矩，
一起写进 `ALL.md`。
