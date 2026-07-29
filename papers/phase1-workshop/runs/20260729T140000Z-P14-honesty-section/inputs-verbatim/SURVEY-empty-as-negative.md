# 普查：空结果被当成阴性结果

只读普查，RES-3 派出。工作树 `.worktrees/e11-engine-crosscheck-deep/`
（分支 `agent/e11-engine-crosscheck-deep`）。除本文件外未写任何文件，未打网络，
未读 `.env` 的值，封存堆零接触。

## 汇总

扫了约 40 处「空 → 判断」的分叉；判为**不安全**的 8 处，其中 4 处是同一条
根因的不同出口（扫描面是硬编码清单，从没和树上实际存在的文件对过）。
另有 6 处是**做对了的样板**，值得当作修法的模板。

---

## 不安全的（最重要的在前）

| # | 位置 | 空的是什么 | 被解释成 | 扫描面有没有被报告 | 为什么危险 |
|---|---|---|---|---|---|
| 1 | `arc-recon/contamination.py:60-63,159-177`；`arc-recon/tools/ledger_invariants.py:97-100,344-364` | `OTHER_LEDGERS` 只列了 2 个路径，扫出的违规集合为空 | `"all_clean": true`，CLI `return 0` | **报了扫了几个（`ledgers_scanned`），从没报过树上有几个** | 树上实际有 **34 个** ledger/probe_log 文件（`baseline-arms/out/shards/` 下 20 个、`theoria-arm/runs/` 下 9 个、另 5 个），审计只看 3 个。caveat 文字甚至点名了 "shards" —— 知道漏了却仍然输出肯定断言 `all_clean` 并据此退出 0。「在 3 份里找到 0 处」被写成了「干净」。 |
| 2 | 同上，`contamination.py:163-168`；`ledger_invariants.py:346-355` | 文件不存在 → `clean: None` → **被 `scanned` 过滤掉** | 不参与 `all(...)`，即不影响 `all_clean` | 只体现在 `present: false` 字段里 | 账本**消失**这件事本身不能让审计失败。删掉一份脏账本 = 通过。`ledger_invariants.py:94-96` 的注释写着「a file that is not there is not a file that is clean」，但代码把它排除出全称量词，效果恰好是当成 clean。 |
| 3 | `monitor/scan.py:77-84`（`git()`）→ `probe_territory_discipline` 第 274、281 行 | `git()` 用 `except Exception: return ""` 吞掉一切失败 | `unmerged` 空、`log` 空 → `findings` 空 → `{"status": "green", "detail": "三类检查全空：无冲突标记、无未合并路径、近 40 个提交无跨领地改动。"}` | 否 —— detail 反而**断言**了「近 40 个提交」这个从没被读到的事实 | 这是本次普查里最纯粹的一例「工具失败被当成世界的性质」。git 不在 PATH、仓库锁住、超时 30s —— 任何一种，盘面都报绿，并且报的是一句具体的、听起来核实过的话。 |
| 4 | `monitor/scan.py:124-127`（`probe_credential_hygiene` 的收尾 green） | `leaks` 列表为空 | `{"status": "green", "detail": "密钥只出现在 .env…；全仓 %s 个文件已扫描" % "全部"}` | **假报了** —— 「全部」是硬编码字符串常量，不是计数 | 这一处比不报扫描面更坏：它声称了一个自己没有测量的覆盖面。而 `os.walk` 循环里有 `SKIP_DIRS` 剪枝和 `except Exception: continue`（第 107-109 行），凡是读不开的文件都静默跳过——恰恰是二进制/加密/权限异常的文件，最值得看的那类。 |
| 5 | `proxy/reconcile.py:55,172` | 某 run 没有任何 `env_step` 记录 | `verdict: "EMPTY"`，而 `main` 是 `return 0 if all(r["verdict"] in ("PASS","EMPTY") for r in reports) else 1` | verdict 名字诚实（`EMPTY` 不叫 `PASS`），但退出码把它并进了通过 | 判决词做对了、闸门做错了。更糟的是复合：`--all` 的 targets 来自 `run_ids(args.ledger)`，所以一个**根本没往账本写过**的 run 连 `EMPTY` 都不会出现，直接从对账面上消失。「没跑」和「跑了对上了」在退出码上完全同形。 |
| 6 | `release/check_redlines.py:~208-210`（记录级扫描器的 `except (OSError, ValueError): return []`） | 文件打不开或 JSON 坏掉 | 返回空 violations 列表，与「这份文件干净」逐字节同形 | 否 | 调用方拿到 `[]` 无从分辨。同一文件 `check_sealed` 第 230-232 行 `except OSError: continue` 同病：读不了的文件从红线扫描面里静默蒸发。 |
| 7 | `baseline-arms/harness/audit_cells.py:120-135` | `cell` 里字段缺失 | `(cell.get("model_calls") or 0)` 等把「字段不存在」变成 `0` 再参与相等判断 | 否 | 字段悄悄消失 + 该 run 的账本分片没加载 → 两边都是 0 → 对账通过。同函数 148-150 行 `if idxs and idxs != list(range(...))`：`idxs` 空时连续性检查静默跳过。（对照组见下面「做对了的」第 6 条，proxy 的收工闸**故意不**这么默认。） |
| 8 | `release/reproduce.py:243-248` | 某 target 在 manifest 里覆盖 0 个路径 | `grade: "reproduced"`，detail「all 0 artefact(s) hash exactly as the manifest records」 | **是**（`n_artefacts` 如实写了 0），这一点救了它 | 空集合上的全称量词恒真：`changed = [p for p in paths ...]` 在 `paths` 为空时必空。等级词是肯定断言。因为 `n_artefacts` 有报，列在末位。 |

---

## 做对了的（当样板）

1. **`release/checklist.py:136-138`** —— `if not hits: return "ABSENT", "nothing in the
   manifest satisfies this item"`。空匹配判成「缺席」而不是「通过」。同文件
   `completeness()` 的 docstring 把这条讲透了：打勾只回答「有没有东西匹配上」，
   是清单能问的最弱的问题。
2. **`release/reproduce.py:198-212`** —— 重现前先查基线是否已经和 manifest 不符，
   不符就判 `manifest-stale` 并**拒绝给分**，理由写在代码里：拿陈旧基线做比较，
   量的是基线。命令非零退出判 `command-failed`，与 `drifted` 分开。这正是
   「跑了、结果相同」与「根本没跑」被显式区分的样子。
3. **`arc-recon/tools/ledger_invariants.py:307-313`** —— 报告里带一个
   `live_key_comparison` 字段，注释写明：命名成这样，是为了让读者能把
   **通过的检查**和**没能运行的检查**区分开；INC-003 的全部教训就是一次
   不可能失败的比较被读成了一次通过的比较。
4. **`release/check_redlines.py:216-221`** —— 封存堆读不出来时返回
   `["…this check did not run"]`，而不是零违规。
5. **`fuzzlab/props/lp_potential.py:118-124`** —— `three_conditions_hold` 的 docstring
   明确**拒绝**重新推导 `inv_init`，因为它恒真：「一条去『检查』重言式的性质，
   报出的是一次它没挣到的通过」。同文件 `certificate_implies_unreachable` 在 BFS
   撞预算时发 `finding.skipped(...)` 而不是裸 `return []`；`fd_adapter.py:106`
   在无 plan 时点名了这个情形归哪条不变式管。
6. **`proxy/tests/test_spend_gate_egress.py:89-118`** —— 四条测试的名字就是判据：
   `test_a_missing_usage_block_is_not_a_free_call`、`test_a_typod_usage_key_is_not_a_free_call`、
   `test_a_truncated_stream_is_not_a_cheap_call`、
   `test_a_usage_value_that_int_rejects_does_not_erase_the_call`。缺失字段**不**默认成 0。

补充对照：`ledger_invariants.scan` 把 `malformed_lines` 单独计数并折进 `clean`
（第 303-308 行），而 `monitor/scan.py:63-75` 的 `iter_jsonl` 对坏行 `except: continue`。
同一个仓库里两种读 jsonl 的写法，一种能看见腐坏，一种看不见。

---

## 我不确定的

* **`monitor/scan.py:381-392`（`probe_dispatch_board`）** —— 注释非常清醒，写着
  「『空』在这里不等于『无事』，报 green 会让盘面看起来比现实干净」，
  然后仍然 `return {"status": "green", …, "retired": True}`。detail 文字诚实
  （说明已被工作板取代），`retired` 标志也在，所以聚合层**可能**已经把它排除了。
  没追到聚合逻辑，不定罪。
* **`monitor/scan.py:139-158`（`probe_pile_integrity`）** —— 报了扫描面
  （「已核对 %d 条请求体」），这是正确的做法，所以没进上面的表；但它
  (a) 只看 2 份账本，与第 1 条同源；(b) 只查 `request_body`，
  不查 URL —— 而 `contamination.py:130` 是查 URL 的。一个出现在 URL 路径里的
  封存 id 在这个探针眼里不存在。够不够算「肯定断言」取决于「零接触」这句话的读法。
* **`fuzzlab/props/lp_potential.py:100,132`** —— `if cert is None: return []`
  是条件式不变式的空前件，注释说明了（incompleteness is allowed），
  合法。但对一个只数 findings 的调用方，「没出证书」和「出了证书且查过没问题」
  仍是同一个空列表。是否需要一个 `finding.skipped` 计数，交给引擎组判。
* **`exam/tools/run_matrix.py:69`（`if not items: return None`）**、
  **`figures/check_coverage.py:184`（`if not rows and slug in note_blob: continue`）**
  —— 后者要求 note 里按名字提到该 slug 才放行，是个像样的护栏；两处都没追到
  消费端，不下判断。

---

## 一条贯穿性的建议（不是修改，只是判据）

上面 8 条里有 4 条（#1 #2 #3 #6）共享同一个形状：**扫描面是一份硬编码的清单
或一次可能失败的外部调用，而没有任何东西把它和树上实际存在的东西对过**。
「在 N 个对象里找到 0 个」这句话里，只有 N 是可信度的载体，而这些审计要么不报 N，
要么报的是自己扫了几个而不是本该扫几个。可执行的判据是：
**任何输出肯定断言的审计，必须同时输出「本该覆盖的对象数」和「实际覆盖的对象数」，
并在两者不等时拒绝给出肯定断言。**
