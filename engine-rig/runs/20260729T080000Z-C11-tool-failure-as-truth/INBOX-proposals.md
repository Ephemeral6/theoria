# C11 — 四条越界发现：只登记，一个字节没动

engine-rig / C11 在自己领地内订正的同时，常设检查与 payload 决策把四件事推到了别人的门口。
**都没动手。** 这份文件是提案，供监控转成 inbox / 工单。

---

## 提案 1 —— `release/`：`release/checklist.py` 在 master 上就不能解析

**这条我建议优先，因为它伤的是别人，而且不是我推理出来的，是 `ast.parse` 直接拒收。**

```
$ git show HEAD:release/checklist.py | python -c "import ast,sys; ast.parse(sys.stdin.read())"
SyntaxError: unterminated string literal (detected at line 45)
```

第 43-47 行：

```python
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", newline="
")
```

`newline="\n"` 里的 `\n` 被写成了**一个真正的换行**。
**已提交**（`git show HEAD:` 的 blob 就是这样，不是 CRLF / checkout 产物），
所以 `python release/checklist.py`、`import release.checklist` 一律 `SyntaxError`。

讽刺的是我在写常设检查时**自己犯了同一个错**（heredoc 里的 `\n` 被展开），
`python -m tools.check_solver_status` 立刻炸给我看。区别只在于我的会被跑到。

**要查的问题不是怎么修那一行**（一望即知），**而是：这个文件上一次被执行是什么时候，
以及为什么没人发现。** `release/checklist.py` 的 `completeness()` 是发布清单的
打勾逻辑；如果它从没跑过，那清单的绿是从哪来的。

---

## 提案 2 —— theory-compiler 轨道：`cold-start-a0/certify/fd_unsat.py`

SURVEY-solver-status 的 U-3。我的常设检查**独立命中**了它（不是喂进去的）：

```
ERROR cold-start-a0/certify/fd_unsat.py:46: `is_unsat` is decided by a tool's status
      return bool(match) and int(match.group(1)) == FD_UNSOLVABLE_EXIT
```

`FD_UNSOLVABLE_EXIT = 12`，docstring 写「12 SEARCH_UNSOLVABLE — proved, not merely unfound」。
**engine-rig 侧对本仓安装的 FD 构建实测过，这与事实相反**
（`engines/fd_adapter/backends.py:70-88`、`DECISIONS.md` D-024、
`PARTNER_SYNC.md:449` 已公告）：`SEARCH_UNSOLVABLE` 住在 **11**，12 是
`SEARCH_UNSOLVED_INCOMPLETE`，而完备的 `astar(blind())` 穷尽状态空间后**也是 12**。

`cold-start-a0/` 对 engine-rig 是禁区（`CLAUDE.md`），所以**一个字节没动**。
可直接搬的正典是 `engine-rig/engines/fd_adapter/backends.proves_unsolvable`。
另需注意 `cold-start-a0/tests/test_followups.py:245-249` 把这个错映射写进了断言——
**那条测试固定该缺陷，无法证伪它**，修的时候要一起改。

---

## 提案 3 —— `monitor/`：`reflex.py:147` 熔断器崩溃 = 「预算正常」

```
ERROR monitor/reflex.py:147: `hold` is decided by a tool's status
      hold = q.returncode == 2
```

`quota.py check` 只有退出 2 表示 hold。它因**任何**别的理由非零
（`quota_state.json` 损坏、未处理的 `KeyError`）都落到 `hold = False`，
于是舰队照常拉起并花钱。**所有失败模式都表示正常**，这是一个 fail-open 的钱闸。

同一份普查（SURVEY-environment 乙组）还点了 `reflex.py:174-179`（powershell 探针失败
→ `free_gb` 保持初值 99 → 内存准入门通过）和 `quota.py:273-275`（CLI 挂掉写成
`window CLOSED`）。这三条同源，建议一并处理。

一句方法上的诚实话：我的检查能命中 `:147` **是因为词形巧合**——`hold` 进断言词表
是为了「不变量 holds」，这里它是「暂停舰队」。语义上判对了，但别把它当成这条检查
在这一族上有召回的证据。

---

## 提案 5 —— engine-rig 自己：`bench` 的 `guard_refused` 让 FD 超时逃过健全性判据

**建议单开工单。** C11 在自己领地内发现但**未修**，因为修它要改 `bench/report.py`
六处表格格式、改变 E2 已发布报告的形状，而本机无 FD 构建、无法实跑验证。

```python
# bench/dividend.py:855  def failures(report):  """Soundness violations only."""
# bench/dividend.py:874
            if row["guard_refused"]:
                continue
```

`guard_refused = guarded.error`，而 `error` 由 `fdrun.py` 的墙钟超时
（`"timeout after %ds"`）和崩溃兜底分支写入。`continue` 跳过 `failures()` 的两条义务
（最优档 plan 长度移动 = unsound compilation；guarded plan 未在原始 domain 上重放）。
`failures()` 经 `bench/__main__.py:148` 决定退出码——**这是 `tests/test_bench.py:622`
自己写的原话。**

链条：**FD 墙钟超时 / 崩溃 → `guard_refused` 为真 → 该行整个退出健全性判据 → bench 退出 0。**
`fdrun.py` 把 `not_entitled` 专门做成与 `error` 分立的第四值就是为了不让
「没资格下结论」和「跑挂了」同形，`:874` 把这层区分合了回去。

修法方向（仅记）：`failures()` 区分 `not_entitled` 与 `error`；
一次 `error` 应当**自己成为一条 finding**（「这一行没有被检查」），而不是 `continue`。

**未量化**：E2 已发布的 `dividend.json` 里有几行 `guard_refused` 非空、
那几行是否本来就会被判据放过——没算。论证的是机制，不是已放电。

## 提案 6 —— engine-rig（登记，不动手）：E5 运行记录里的 `text=True`

`engine-rig/runs/20260728T141724Z-E5-cert-recheck/manifest.py:57-59`：
`text=True` 无 `encoding=`、无 `timeout`、无异常处理，`git` 失败时 `head_commit`
静默写成 `""`。**在本领地内，但在 `runs/` 下**——那是一次已完成运行的冻结记录，
改它会让 provenance 与当时真正跑过的字节不符。按「provenance is canonical」登记不改。

（它此前逃过扫描，是因为常设检查的 skip 表里有 `runs`。**那条已修**：
`runs` 移出 skip 表，扫描面 88 → 95，且 `main()` 现在把扫描面与排除项一并打印。）

## 提案 4 —— `release/` + engine-rig：三个新字段进不了 candidate payload

C11 在 engine-rig 内加了三组「凭什么这么说」的字段，**都停在对象上没进产物**：

| 字段 | 在哪 | 它本来要回答什么 |
|---|---|---|
| `Law.scope_exhaustive` | `engines/zero_space/zerospace.py` | `scope: "global"` 是「证明了不是 cell-local」还是「没搜过」？（>8 色即触发，ARC 十色调色板跨过这条线） |
| `SearchResult.max_expansions` / `.exhaustive` | `engines/fd_adapter/search.py` | `plan is None` 是穷尽还是放弃？（代码里是穷尽，产物里看不出来） |
| `Reachability.basis` / `.budget` | `engines/probe_frontier/reach.py` | `status: "unreachable"` 凭什么？ |

**卡住它们的不是技术，是一份我不拥有的 manifest**：这三个 payload 汇进
`engine-rig/artifacts/candidates.jsonl`，其 sha256 被
`release/MANIFEST.jsonl:667`（`679fe331…7078cfdad`）钉住，且候选 `id` 是对 payload
内容寻址的 uuid5。实测：加上字段后 44 行里 9 行 zero_space 的 id 全变，
`tests/test_integration.py` 的新鲜度断言立刻红，必须重生成 `candidates.jsonl`。

而本工单明写「不要改任何已提交产物」，`CONTRACTS/candidates_schema.md` 又是冻结契约。
所以这是一次**协调**，不是一次提交：需要 release 轨道同意「重生成 + 重签 manifest」，
或者双方同意这三个字段走 payload 之外的通道。

**在此之前，那个缺口是真的**：产物读者仍然分不清「证明了」与「没搜」。
三处 `as_json()` 上方都留了注释说明字段为什么被扣住——是决定，不是遗漏。
