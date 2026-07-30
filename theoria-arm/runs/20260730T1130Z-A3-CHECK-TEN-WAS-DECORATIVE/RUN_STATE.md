# A3 · 我上一轮加的那道闸门是装饰性的，而且我在同一份记录里点过这个缺陷的名

上一 leg 我给 `verify_provenance` 加了 check 10，理由写得很足：check 8 按
`_is_backfilled` 分流，`amend` 那条路从不读 `files[]`，于是四份清单列着不存在的
`trace.jsonl` 却全部放行——「一道只在一条代码路径上睁眼的检查比没有检查更糟，
因为它的绿会被当成覆盖」。

这一轮的对抗复核把同一句话对准了 check 10 本身。

## 一、实测：把 check 10 改成**不可能失败**，整套测试仍然全绿

```python
-    for row in survey:
+    for row in []:
```

`python -m pytest -q` → **272 passed**。也就是说，我声称是 check 10 守卫的那
两条测试，一条也没有执行过 check 10。

原因看一眼就清楚：`test_check_ten_catches_a_dangling_reference` 里那个
`dangling_for()` **把 check 10 的函数体逐行抄了一遍**——
`absent = [...]`、`explained = backfill._ignored_paths(...)`、集合差——
然后对着这份副本断言。它 `from armtools import verify_provenance`，
**然后再也没有调用过它**。另一条 `test_check_ten_is_actually_wired_into_the_run`
只断言检查的**名字字符串**出现在 `run().rows` 里，一道永久绿的检查照样满足。

**而这正是我在上一 leg 的 RUN_STATE §四里亲手点过名的缺陷**——
「一个把期望值从被测代码里读出来的测试，只断言了代码等于它自己」。
我在写下那句话的同一轮里，把它犯在了另一个文件上。
**给缺陷类命名不能防止它**：这是第二次验证这句话，上一次是
`.git/info/exclude` 那条机器相关性。

## 二、改法：调用真的 `run()`，读 check 10 自己的判词

`verdict(*paths)` 现在写好清单、跑 `verify_provenance.run(str(runs_root))`、
把 check 10 那一行取出来，三个方向各断言一次：

| 清单里列的 | 期望 |
|---|---|
| 存在的文件 | 绿 |
| 缺席但被 `.gitignore` 规则点名（`runs/*/trace.jsonl`） | 绿 |
| 缺席且无人解释 | **红**，且 detail 里点名 `gone.json`、不点名 `certify.json` |

**突变实测（两个，都被抓）**：

| 突变 | 旧测试 | 新测试 |
|---|---|---|
| M-X：`for row in survey` → `for row in []`（检查不可能失败） | 272 passed | **红**：`check 10 passed a dangling reference` |
| M-Y：`explained = set()`（规则不再解释任何东西） | 未覆盖 | **红**：被规则点名的缺席文件被误报成悬空 |

## 三、写这条测试的过程里，它当场抓到了第二个真空

我先写完 `verdict()`，跑，**红**了——但不是因为 check 10 有 bug，
而是因为临时目录里那个 run **不是 archive material**，于是
`verify_provenance` 里**每一道**检查都跳过它，check 10 的那一行永远是绿的。
换句话说：**我的新测试在第一次运行时就是真空的**，只是这次有东西告诉我。

告诉我的是我顺手加的 `test_check_ten_is_not_skipped_into_silence`——
它单独钉住「这个 fixture 是 archive material」。没有它，我会把一条
「调用了真 `run()`」的测试当成修好了，而它和抄函数体的那版一样什么都不断言。

`archive_material` 的门槛是：要有 `ledger.jsonl`、要有一条 `run_start`、
且 `env_upstream` 不是回环地址（否则归类为 `mock`）。`_archive_material_run()`
把这三条写成一个 helper，并在 docstring 里说明为什么每一条都是必需的。

**教训**：「测试调用了真代码」不等于「测试断言了什么」。
夹在中间的是「被测代码这次真的走到了那一行吗」，而这一步需要它自己的钉子。

## 四、一处刻意的桩，说明为什么它不削弱这条测试

check 8 会调 `armversion.scan()`，而它要遍历一个当前挂着 266 个工作树的仓库的
全部引用：**实测 136 秒**。三次 `run()` 就是七分钟进测试套件，
而**没人跑的套件正是这个文件存在的理由所要避免的**。所以测试里
`monkeypatch.setattr(armversion, "scan", lambda *a, **k: {})`。

桩掉的是**无关的另一道检查**，不是被测的这道；check 8 在临时树上的判词
全程没有被读过，断言只落在 check 10 那一行上。

（顺带记一笔，不属于本条：`verify_provenance` 完整跑一次要两分多钟，
门槛高到不会有人在提交前顺手跑。这是一条独立的、值得单独立项的观察。）

## 五、对抗复核提出、本轮**没有**处理的几条（原样记下，不软化）

复核还提出了三条我认为成立但没在本轮动的，留给下一世，别让它们蒸发：

1. **check 10 的作用域名不副实。** 它自称「every file a manifest lists」，
   实际只看 `archive_material` 的 12/35 个目录，**33 条列出的路径从不被检查**。
   这是 `verify_provenance` 全文件的设计（每道检查都有这个过滤），不是 check 10
   独有的缺陷——但检查的**名字**确实说大了。要么改名，要么让它覆盖全部。
2. **check 10 的判据是 `os.path.exists`，不是「在克隆里」。** 于是一条
   present-but-untracked 的路径在这里过、在克隆里悬空——
   **这道为终结「两台机器不一致」而写的检查，自己就是机器相关的**，同一个机制。
   今天只有一条列出的路径处于该状态且恰好被规则覆盖，所以两棵树一致；
   那是运气，不是这道检查。
3. **`_files_the_clone_carries()` 仍以 `os.walk` 起手**，只做减法（减掉被忽略的），
   从不问仓库「你到底装运什么」。一个未跟踪、又没被任何规则匹配的文件照样进
   `files[]`——实测：往 `runs/20260729T004020Z-leg01/` 扔一个
   `scratch_notes.txt` 就能让 check 8 在别人机器上变红。所以
   「答案不再取决于工作树」这句话**写大了**：只关掉了「被忽略」那一类。
   正解是 `git ls-files`，不是 `os.walk` 减 `check-ignore`。

第 3 条是这三条里最实的，也是我上一轮那句话的直接反例。
