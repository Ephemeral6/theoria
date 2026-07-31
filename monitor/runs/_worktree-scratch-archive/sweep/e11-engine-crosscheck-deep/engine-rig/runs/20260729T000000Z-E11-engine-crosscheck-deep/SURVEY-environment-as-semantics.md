# 普查：环境事实被读成研究结论

范围：全仓（含所有领地），worktree `e11-engine-crosscheck-deep` @ `6ee0466`。
纯只读，除本文件外未写任何字节。

判据只有一条：**环境事实（崩溃 / 非零退出 / 超时 / 解码失败 / 资源上限 /
并发）有没有被转成一条关于被研究对象的断言。** 正当的错误处理不报。

## 汇总

扫了约 240 处判据点：60 处 `subprocess` 调用点、149 处 `except Exception`、
约 30 处预算 / 上限。**判为不安全的 37 处。**

这个仓库对这一类缺陷的自觉程度很不平均。同一个包里常常并排放着一个做对的
和一个做错的实现——`release/enumerate.py:220` 解析失败返回 `None` 判
`needs_human`，`release/check_redlines.py:207` 同样的代码解析失败返回 `[]`
判红线通过。**几乎每一条不安全的下面，都能在三十行内找到它自己的正确版本。**
这不是知识缺口，是修补没有扫干净。

---

## 不安全的

### 甲组：环境失败 → 一条**肯定的**实质结论，且无任何记录

| 位置 | 环境事实 | 被解释成 | 为什么危险 | 有没有被记录 |
|---|---|---|---|---|
| `a0-spike/pipeline/stages.py:260-263` | `synthesize` / `enumerate_frontier` 抛任何异常（bug、递归、内存、引擎版本错位）——裸 `except Exception:`，连 `as exc` 都没有 | 「这一类迁移不存在单个合取 guard」→ 走 `learn_dnf`，产出 `walk_UP_1`、`walk_UP_2`… | 规则集是 A0-spike 的头号产出（`a0_report.json` 的 `report["mine"]`）。**引擎崩溃和「世界的规则结构确实是析取的」产出完全相同的产物**，不可区分 | **没有。** 报告里没有一个字段说这条回退触发过 |
| `theoria-arm/inner/plan.py:172-173` | `step(state, action)` 抛异常 → `continue`，静默丢弃该后继 | 该后继不存在 → 队列排空 → `status: "unsat"`，detail 写「the whole reachable set (%d states) was enumerated and none satisfies the goal」 | **生成的 `step` 有文档保证是全函数**（`theory.py:196-205`：`frame persist -- ... which is what makes this total`），唯一声明的异常是 `AmbiguousTransition`，那本身是一条缺陷信号。所以这里被吞掉的每一个异常要么是已声明的违规、要么是崩溃，**没有一个是「动作不适用」**。异常越多，搜索树被剪得越狠，「穷举了整个可达集」这句话越假 | **没有。** 丢弃计数、异常类型都不记；且 `search_timeout` 会 fire surprise，`unsat` 不会——假 unsat 完全静默 |
| `theoria-arm/inner/certify.py:196` / `:206` | 同上：replay 走位时 `except Exception: break`；歧义检查时 `except Exception: pass` | `{"ok": true, ...,  "detail": "no (state, action) among %d x %d admitted two rules"}` — 约束 9 通过 | 与上条同源。分母 `len(states) x len(actions)` 是**名义积**，不是实际判过的对数：抛异常的对被算进了声明覆盖面却从未被裁决。**崩溃越多，健康证明越干净** | **没有。** 另有 off-by-one：循环取 `states[:400]`，detail 报 `len(states)`（可为 401） |
| `monitor/tests/mutants.py:83` | pytest 因**任何**理由非零——变异体造成 SyntaxError、collection error、import 崩溃、解码失败（`text=True` 无 `encoding=`，无 `timeout=`） | `"RED"` = 「测试抓住了这个变异体」 | 这是**研究有效性主张**本身：这套 harness 存在的全部理由是证明测试不是摆设。真正的阴性是 `SURVIVED`（退出 0），所以崩溃和成功落在错误边界的两侧。`main()` 打印 `all N mutants caught` 并退出 0 | **没有。** 唯一线索是 `caught` 为空串，而它从不被检查 |
| `release/check_redlines.py:207-208` | 被追踪的 `.json` / `.jsonl` 不可读、字节不是合法 UTF-8、或 JSON 畸形。`UnicodeDecodeError` 是 `ValueError` 的子类，`open(..., encoding="utf-8")` 无 `errors=` | `return []` → 无坏记录 → 主程序打印「**NO** record pairs a sealed id with payload — checked record by record」 | 封存堆红线闸门，决定 release 能不能生成。一次 parser 崩溃变成一句肯定的审计结论。同一个包里 `enumerate.py:205-221` 几乎同样的代码在同样的失败上返回 `None`、归类 `"?" / needs_human` | **没有。** 无未解析文件计数，无备注 |
| `battery/audit/gaming.py:368-372` | `from battery.audit.exploits import collect` 因任何理由失败 → `except Exception: return {}` | `tier_of` 全线回退到手写 prose 布尔；`audit()` 给每个 metric 写 `status: "prose only — no executed exploit"`，`n_demonstrated: 0`，`n_disagreements: 0`，`demoted_by_demonstration: []` | 被可执行 exploit 降级到 `reference` 的 metric **静默回到 `main` 表**。这个模块的全部意义是它自己写的那句：「where a metric has an executed exploit, its `accidental`/`defended` are facts about the code and they win」。一次 import 错误重新启用了它被写出来就是为了取代的不可证伪布尔 | **部分。** `n_demonstrated: 0` 与「还没写 exploit」完全同形，无错误字符串 |
| `a0-spike/pipeline/lean_stage.py:78` | `A0Audit.lean` 那一趟失败 / 崩溃 / 无输出 | `"uses_sorry": "sorryAx" in audited.stdout` → `False` = 「证明不依赖 `sorryAx`」 | `run_a0.py:251` 把它作为绿灯合取项 `not report["lean"]["uses_sorry"]`。审计没跑和审计说「没有 sorry」给出同一个值 | **没有。** `non_vacuous`（= `returncode == 0`）会是 `False`，但**它根本不在绿灯判据里** |
| `a0-spike/pipeline/run_a0.py:250-253` | 这台机器上没有 Lean 工具链 | `not report["lean"].get("available") or (...)` → 整趟 A0 **绿灯**，`main()` 返回 0 | 缺席直接满足合取项。三个兄弟实现明文拒绝这么做（`cold-start-a3/a3pipeline/certify_a3.py:34-37`：「reported as red, never downgraded to a pass」） | 产物里有 `available: false` 并打印 `lean skipped`，但**退出码和 ok 判据说通过** |

### 乙组：环境失败 → 一条关于被观测系统的**否定**结论

| 位置 | 环境事实 | 被解释成 | 为什么危险 | 有没有被记录 |
|---|---|---|---|---|
| `theoria-arm/inner/certify.py:230` + `:239-249` + `:293-296` | `lean` 不在 PATH；或 900s 超时；或 `text=True` 无 `encoding=`，在 cp936 机器上 `UnicodeDecodeError` | `available=True` 且 `ok=False` → fire **`proof_failure`** surprise，其注册表定义是「a declared law will not go through」 | **`available` 的含义是「生成了 Lean 文件」，不是「检查器跑过了」**（`:230` 设在 `shutil.which` 之前）。所以「机器上没装 Lean」被 fire 成「这条声明的定律过不去」，喂进 theorize/repair 回路。且运行报告里 `proof_layer_available: True`，读者会以为证明层跑过 | 部分：异常串进 `detail`，但 **surprise kind 与真实拒绝完全相同** |
| `theoria-arm/inner/certify.py:107-109` → `armtools/timeline.py:190` | 初始状态 render 抛异常 | `checks["unambiguous"] = {"ok": True, "scope": "not_attempted"}`；timeline 只读 `.get("ok")` 并 `_tick()` | 人看的时间线上打印「constraint 9 ✓」——一条**从未执行过**的检查显示为通过。`scope` 在这一路上被丢掉 | `scope: "not_attempted"` 在 JSON 里，但渲染层不读 |
| `monitor/scan.py:516-525` | 中文 Windows 上 `schtasks` 输出 cp936，代码用 `encoding="utf-8", errors="replace"` 解，`已禁用` 变成替换字符 | `disabled = False` → `"运行中"` → 探针 `green` | 这个 watchdog 正是因为「OPS-M 和 OPS-R 都报告 TheoriaReflex 处于 Disabled 而板上无人提及」才被写出来（见其 docstring）。解码不匹配把那个盲区原样装回来，还加了个绿灯。**同仓 `agents.py:115` 与 `board.py:218` 对同一条命令用 `gbk` 解**——仓库自相矛盾 | 没有——它报 `green` |
| `monitor/reflex.py:168-172` | `schtasks` 状态词是 `正在运行` 而非 `Running`（`run()` 的 `text=True` 亦无 `encoding=`） | `live_workers` 停在 0 | 喂进 `range(target - live_workers)` → 在已有 7 个工人之上再拉起最多 `WORKER_MAX = 7` 个重复工人。**`agents.py:106-112` 用中文写明了这个 bug（「今天因此把八个活着的工人全报成已停」）并在那里修好了，这个调用点没修** | 没有。只有看起来正常的 `worker-spawn:` 事件 |
| `monitor/reflex.py:174-179` | `powershell` 缺失 / 失败 / 超时，或 `int(out)` 在空串或乱码上抛异常 | `free_gb` 保持初值 `99` → 内存准入门通过 | 一个安全闸门的 fail-**open** 默认值。探针失败读作「内存充裕」 | 没有。`worker-hold:low-memory` 只在成功路径发出 |
| `monitor/reflex.py:147` | `quota.py check` 因崩溃退出 1（`quota_state.json` 损坏、未处理的 `KeyError`） | `hold = (q.returncode == 2)` → `False` = 「我们没被限流」 | 熔断器自身崩溃被读成「预算正常」，于是舰队照常拉起并花钱。只有 `2` 表示 hold，**所有失败模式都表示正常** | 没有 |
| `monitor/quota.py:273-275` | `claude` CLI 因任何理由非零——鉴权过期、断网、CLI 崩溃（`timeout=120` 未捕获） | `st["last_ping_result"] = "CLOSED"`，打印 `window CLOSED` | 这里被研究的对象是供应商的配额窗口。「CLI 挂了」被写进磁盘，作为「窗口关闭」的**测量结果**；`resume():332` 据此拒绝解除 hold | 部分：`hint:` 回退到 `blob[-1]`，但状态字段是二值 `CLOSED` |
| `monitor/ci_merge.py:150-153` | `git merge-base` / `git diff` 失败（坏 object、fetch 竞态） | `base=""`, `out=""` → `dirs = set()` → 「这个分支没碰任何目录」 | `try_merge` 于是**跑零个闸门**、跳过未知领地检查、推上 master，并记 `MERGED … (dirs: ; gates: none)`——与一个合法的纯文档分支逐字节相同 | 记了，但记成一次**成功的合并** |
| `monitor/dispatch.py:97-106`（另有 `quota.py:155`、`scan.py:1254` 三份拷贝） | `tasklist` 失败 / 解码错误 / 返回码被忽略 | `str(pid) in out` → `False` → 「进程死了」 | `reap():139` 盖上 `entry["reaped"] = "exited"`，而 `reflex.py:213` 的复活回路把它当作「重新拉起」。一次工具抖动变成「会话死亡」并买下一个新 Opus 会话。`scan.py:1254` 同一事实渲染给人看是「失联（进程死亡且无产出）」 | 没有 |
| `monitor/dispatch.py:48-51` | `git` 非零，或 `text=True`（无 `encoding=`）在 cp936 下把中文 commit subject 搞坏 | `existing_branches()` → 空集 → `branch_taken()` False | 「没有分支存在」是派单的**防重跑保险**。一次 git 打嗝让每条提示词看起来都没人接，于是拉起一整支重复舰队 | 没有 |
| `monitor/board.py:216-224` | `schtasks` 非零 / stdout 为空（返回码从不检查） | `live = set()` → 每个 `W-*` 工人「已消失」 | `cmd_sweep` 随即**改动板面**：把活工人持有的每一份认领 `os.rename(claimed → items)`，两个工人于是能认领同一项。破坏性，不只是显示问题。（这里状态匹配本身是对的：`("Running", "正在运行")`——只有空输出没设防） | 记了 `SWEEP …(worker %s gone)`，但归因是假的 |
| `monitor/bus.py:51-62` | `in.jsonl` / `out.jsonl` 里一行畸形（并发追加写的典型产物）→ `except Exception: pass` | 该消息从 `rows` 中消失 | `cmd_status` 于是报「欠回执 无」——一条被丢掉的指令读作「agent 全都回了」。更糟：`cmd_send:72` 用 `len(read_jsonl(inbox)) + 1` 算 seq，丢一行就**复用一个 seq**，静默破坏 ack 配对 | 没有 |
| `monitor/scan.py:106-110` | 文件不可读（占用、权限、路径过长）→ `except Exception: continue` | 该文件未做 API key 检查 | 结果文本断言「全仓 **全部** 个文件已扫描」并返回 `green`。一条安全结论建立在可证不完整的扫描上，**且措辞主动否认了这个缺口** | 没有 |
| `monitor/scan.py:63-74` → `probe_pile_integrity:154-160` | `recon_ledger.jsonl` 中被截断的半行（并发追加的典型产物） | 该请求体不被检查 | 输出称「封存堆 %d 局零接触（已核对 %d 条请求体）」，而计数只数成功解析的行，因此自洽且不可察。这是 CLAUDE.md 称为对两条赛道均有约束力的切分保证 | 没有 |
| `monitor/scan.py:736-743` | `proxy/var/spend_gate.jsonl` 中损坏 / 截断的行 | 该笔支出被跳出 `total` | 在 $200 信封下报「剩 $%.2f」与 `green`，而实际花销被少算 | 没有 |
| `monitor/scan.py:537-546` | `git()` 已吞掉失败 → `commits` / `merges` 为 `""` | `or "0"` → `n=0` → `status = "green"` | 一次失败的 git 调用给出**可能范围内最令人安心的答案**：「spec.py 落后 0 个 commit」。而这个探针存在的唯一目的就是测量陈旧度 | 没有 |
| `monitor/agents.py:83-88` | 任何 git 失败，含 `timeout=60` | `return ""` → `commits` → 0 → `card["outputs"] = 0` | 「这个 agent 什么也没产出」是这张卡片的全部内容，而一次 git 超时就能生成它 | 没有 |
| `monitor/agents.py:113-123` | `schtasks` 返回码不检查；stdout 为空 | `_LIVE = set()`（全局缓存） | `worker_cards():188` 的 `"orphan": bool(now) and running is False` → 每个持有认领的工人都被标为孤儿。（此处 gbk 解码与双语匹配都是对的，只有失败分支没设防） | 没有 |
| `monitor/ci_merge.py:107-116` | `tasklist` 失败 | `m0_alive()` → `False` | 阻止 CI 在人类 M-0 会话裁决期间合并的互锁。工具失败即等于关闭互锁 | 没有 |
| `cold-start-a2/tools/verify_readonly.py:60-79` | `run_all.py` 崩溃 / 从未真正跑起来（缺依赖、import error） | 「0 files changed」，退出 0 → 「a full A2 run writes nothing into another track」 | `proc.returncode` 在 `:62` 被打印，但**不参与判据**（`return 1 if changed else 0`）。什么也没做的一趟自然什么也没改，而这个脚本的自述目的是**证明**只读性 | 仅 stdout；不进产物，不进退出码。（`cold-start-a3` 同构版本更好：`run_all_exit` 确实写进了 `readonly_report.json:71`，但派生的 `clean` 布尔仍然把它洗掉） |
| `arc-recon/recon.py:112-122` | `get_scorecard` / `close_scorecard` 抛异常（HTTP 4xx/5xx、超时） | `findings["scorecard"] = {"error": "KeyError: 'retrieve_response_fields'"}`——**整个探针结果被丢弃** | 失败路径只设 `<label>_result`（`:92`），于是 `main` 的 `scorecard["retrieve_response_fields"]` 抛 `KeyError`，被 `:120` 的宽 except 接住。真正的逐步 API 发现——`probe_scorecard` 的全部意义——从未到达 `recon_findings.json` | **归错因了。** 一个 API 事实被记成一个内部 `KeyError` |
| `cold-start-a2/a2pipeline/concepts.py:79-83` | `git rev-parse HEAD` 非零（不是仓库、`index.lock` 被另一条赛道占着、PATH 无 git） | `"repo_head_when_pinned": ""` | `except Exception` 只接住**启动**失败；非零退出 + 空 stdout 直接 `.strip()` → `""` 而非 `None`。这个 pin 的存在正是为了回答「哪些字节编译出了这个 exhibit」，而并发持锁是最现实的那个场景 | 静默降级：本该是 `null` 的位置写了 `""` |
| `exam/grading/selftest.py:512-521, 558` | 注入故障后检查体自身抛异常逃逸 | 转成一行失败（`["raised %s: %s"]`）→ `fault_matrix` 的 `caught_by` 记为**该故障被抓住** | 头条数字 `caught` / `n_uncaught` 无法区分「抓住了」和「崩了」。**降级理由**：故障是进程内 patch 的，崩溃通常确实由故障引起，且 `detail` 保留 `raised ...` 原文 | `detail` 保留 |
| `ablation-arm/ablcore/pin.py:61-69` + `run_arm.py:643` + `verify.py:221-224` | 另一条赛道在本次运行期间并发写 `engine-rig/` / `theory-compiler/` / `proxy/`；或哈希时 `OSError`（Windows 文件占用）**把该路径整个从字典里删掉** | `upstream_unchanged: False` → 只读声明判 **FAILED**，闸门红 | `pin.py` 自己的 docstring 就说「two sessions work this repo concurrently, so the other track's files legitimately change while this arm runs」，闸门却仍把这个 pin 当作关于**本 arm 行为**的红绿判据。`except OSError: continue` 还让一次瞬时读失败看起来像一次删除 | 部分：`upstream_files_changed` 列出路径，人可归因；代码里没有归因，也没有 `pre_run_dirty` 基线 |

### 丙组：`engine-rig` 自己领地内的（本次交叉复核的正主，单列）

`engine-rig` 的**引擎主体**在这条缺陷上是全仓最好的：`backends.py:70-88` 明写
「the exit code alone does not tell a proof from a shrug」，`proves_unsolvable`
（`:266-270`）对 exit 12 额外要求 optimal rung **且** 日志含
`"Completely explored state space"`，超时一律 `solved=False, proved_unsolvable=False`。
问题全部在 `tools/` 与两个引擎的内部上限里。

| 位置 | 环境事实 | 被解释成 | 为什么危险 | 有没有被记录 |
|---|---|---|---|---|
| `engine-rig/tools/p13_fd_dividend.py:129` | FD 裸退出码 12 | `unsolvable=done.returncode == 12`——字段就叫 `unsolvable` | **这正是同目录下 `backends.py:239-270` 为防止而存在的那个谓词，被重新实现了一遍且丢掉了两个附加条件。** 本次 E11 已把同一个「一个整数」错误跨赛道登记在 `cold-start-a0/certify/fd_unsat.py` 名下（`partials/deadlock-via-reachability.md:160-233`），**但没注意到 `engine-rig` 自己的 `tools/` 里也有一份**。同文件对 exit 22/23（内存耗尽 / 时间耗尽）完全没有分支 | `exit_code` 存了，但 `unsolvable` 是下游读的字段 |
| `engine-rig/engines/lp_potential/potential.py:170-171` | HiGHS 迭代上限（`status=1`）或数值困难（`status=4`） | `if not result.success: return None` → 与「LP 真的不可行」同一个值 | 该函数 docstring（`:120-124`）把 `None` 的语义写死为「if the goal is reachable, no such weight function exists, and the LP has to be infeasible」。**求解器资源耗尽和几何事实共用一个返回值。** `result.status` 与 `result.message` 被整个丢弃 | **没有** |
| `engine-rig/engines/zero_space/zerospace.py:141-143` | `if len(indices) > 8:` → 子集枚举静默退化为「单元素 + 全集」 | 被截断扫描漏掉的定律，`analyse:167-171` 归类为 `scope: "global"` | `global`（跨格的定律）与 `cell_local`（关于编码的定律）是**关于世界的两条不同实质主张**。`Law.as_json`（`:70-80`）发出 `scope` 而无任何截断标记。潜伏：>8 色/格才触发 | **没有** |
| `engine-rig/engines/mdl_segmenter/segmenter.py:177, 264-272` | `_match_cost` 遇 `IMPOSSIBLE = 10**6` 哨兵 → 返回 `kind=None` | 驱动的 `if kind is not None:` 把它与「格子和颜色都没变」**同等对待**——不发事件、不计 bit、轨迹静默延续 | 「我解释不了这个迁移」渲染成「什么也没发生」。潜伏，且**没有任何计数器或断言能告诉你它触发过没有** | **没有** |
| `engine-rig/engines/probe_frontier/reach.py:94-99` + `__init__.py:136-137` | 继承 500000 上限（触顶会抛异常） | payload 断言「the configuration is unreachable -- this experiment cannot be performed on this instance」 | 今天安全**仅仅因为触顶会抛**。`Reachability.as_json`（`:60-69`）有 `expansions` 而无上限，所以这条断言从产物本身无法自证 | **没有**（机制安全，产物不足） |
| `engine-rig/tools/p13_fd_dividend.py:317-318` + `:400-404` | 两趟 FD 都崩了 → `plan_length` 皆 `None`、`unsolvable` 皆 `False` | `same_answer: True` = 「guard 保住了答案」；表格行用 `%s` 打印出 `None -> None … yes` | 双重失败被发表成一条肯定的对照结论 | `fd_exit_code` 存了，但表读 `same_answer` |
| `engine-rig/tools/p13_fd_dividend.py:368-369` | FD 崩溃（exit 30/22/23/1）→ `fd.unsolvable=False` | `agree = ((stub.plan is None) == fd.unsolvable and …)` → 一个 stub 已证不可解的实例被记为**两个后端不一致** | 「FD 没回答」被读成「FD 给了相反答案」 | `fd_exit_code` 存了，但表读 `agree` |
| `engine-rig/bench/dividend.py:212` + `bench/report.py:191-195` | `fdrun.py:208` 把墙钟超时写成 `error="timeout after %ds"` | `"guard_refused": guarded.error` → `report.py:192` 把每个这样的行渲染成 `*refused*` | 一次超时被印成关于 **guard** 的陈述（「FD 拒绝了这次编译」）。JSON 保留原文，Markdown 不保留 | JSON 里可恢复，人看的表里不可 |

**一条我要收回的转述。** 交叉复核报来
`p13_fd_dividend.py:419-424` 会发表「zero, on both engines (None -> None)」这条
虚假的负结果。我复核后认为**不成立**：那条 prose 分支用 `%d` 格式化，
`"%d" % None` 抛 `TypeError`，会响亮地崩掉而不是发表。
真正落地的是同一函数 `:400-404` 的**表格**行——那里用 `%s`，
于是 `None -> None … yes` 确实会被印出来。上表第 6 条按后者记，不按前者。

### 丁组：`text=True` 无 `encoding=`（Windows 中文机器上，诊断信息恰在最需要时被销毁）

`a0-spike/pipeline/lean_stage.py:55`、`cross_form.py:43,152`、
`baseline-arms/harness/bare_cc.py:194`、`cold-start-a3/tools/verify_readonly.py:56`、
`exam/verify.py:71`、`exam/tools/archive_run.py`、`theoria-arm/inner/certify.py:239`、
以及 `engine-rig` 的四处：`backends.py:328-330`、`fdrun.py:201-203`、
`toolchain.py:124-127`、`tools/p13_fd_dividend.py:112-113`。

`UnicodeDecodeError` 在 subprocess 的读取线程里抛出，既不是 `OSError` 也不是
`SubprocessError`，因此 `a0-spike/pipeline/lean_stage.py:44` 那样的捕获接不住。
`release/reproduce.py:217-223` 用文字记录了这个缺陷曾经发生过——「it turned a
diagnosable error into a bare non-zero exit」——并在 `theoria-arm/harness/modelcall.py:241`
钉死了 `encoding="utf-8", errors="replace"`。**这几个调用点是漏网的。**
方向是保守的（崩溃，不是假绿），但这是本仓已经付过一次学费的那个失败。

---

## 穷举触顶专查

问题只有一个：**靠穷举下结论的地方，有没有把「我没触顶」这件事报出来。**

| 位置 | 靠穷举下什么结论 | 有没有报告「未触顶」 |
|---|---|---|
| `engine-rig/runs/…E11…/partials/lp_potential-via-exhaustive.md:80-81` | `lp_potential` 健全性，3000 世界 / 505 312 态 | **有，全仓金标准。**「Every BFS ran to completion — no world hit `search.STATE_BUDGET`, so every "unreachable" below is a proof, not a timeout.」而且这个事实被**抬进了头条表**（`CROSSCHECK.md:40`：「505 312 states exhaustively enumerated, **no budget exhaustion**」）。上限被点名、未触顶被断言、认识论升级（proof 而非 timeout）被写成那个事实的**推论**而不是默认 |
| `engine-rig/runs/…E11…/partials/deadlock-via-reachability.md:241-242` | 50 条 deadlock / 不可解证书 | **有，同上。**「Every run exhausted its space — no budget was hit, so every "unreachable" here is a proof and not a timeout.」 |
| `engine-rig/bench/ladder.py:74-82` + `:226` | stub-bfs rung 的可解 / 不可解 | **有，做得最干净。** 触顶 → `solved: False`, **`proved_unsolvable: False`**, `error: "over budget: …"`；未触顶 → `proved_unsolvable: not result.solved`，并附注「BFS is complete, so an exhausted queue *is* a proof」。产物里正面记下 `stub_max_expansions`，`report.py:52` 把 `over budget` 与 `ERROR` 分成两列显示 |
| `engine-rig/engines/fd_adapter/search.py:145-146` | BFS 无解 | **机制安全，产物不足。** 触顶 `raise RuntimeError`，绝不返回 `None`——所以一个返回的 `SearchResult(None,…)` 蕴含未触顶。但 `SearchResult.as_json()`（`:108-116`）与 `deadlock_carver.PruningReport.as_json()`（`:74-83`）**都不写 `max_expansions`**。产物只有 `expansions`，读者无法自证 N < 上限；这个前提是隐含的，不是写下的 |
| `theoria-arm/inner/plan.py:155-167` | 规划器的 `unsat` | **有，写得很好，但被上游拆穿。** `search_timeout` 与 `unsat` 是两个不同 status，触顶记 `reached: "node cap"/"deadline"`、`expansions`、`frontier`、`seen`；`unsat` 的 detail 明写「this is a search result, not a theorem」。**但 `:172-173` 静默丢后继（见甲组第 2 条），所以「整个可达集」这句话本身没有保证**；且 `search_timeout` 会 fire surprise，`unsat` 不会 |
| `theoria-arm/inner/certify.py:191, 200` | 约束 9「无歧义」 | **没有，且分母高报。** `AMBIGUITY_SAMPLE_CAP = 400`：循环取 `states[:400]`，detail 却报 `len(states)`（可达 401）× `len(actions)`。触顶不报，被吞异常跳过的对也计入声明覆盖面。诚实的一点是标了 `scope: "sampled"` |
| `worldgen/core/world.py:259-271` | `reachable()` | **安全。** 超 `limit=200_000` 抛 `RuntimeError("reachable set exceeds %d states")`，绝不返回截断集 |
| `worldgen/core/solvability.py:34-51` | `solve()` → `None` = 不可解；`report()` 发 `certificate: exhaustive_reachability` | **安全（无上限）。** BFS 完全无预算，因此 `None` 是真穷举；证书语句正面写出 `len(states)` |
| `theory-compiler/src/theory_compiler/conflict.py:695-696, 809-813` | 冲突 sweep | **有。** 超限 → `{"status": "not swept"}` **并且** `raise ConflictError`，绝不判绿；`swept["pairs_examined"]` 正面落进 `EVIDENCE.json` |
| `theory-compiler/src/theory_compiler/strips.py:515-516` | STRIPS 可达集 | **安全。** 超限抛 `StripsError`；`verify()` 的统计进 `EVIDENCE.json` |
| `theory-compiler/…/generators/gen_lean_deadlock.py:380-398` | Lean 分情况证明 | **安全。** 超 `MAX_LEAN_CASES` 拒绝发射，而不是发一个注定超时的文件 |
| `engine-rig/engines/cegis_miner`（`miner.py:39-41`，`MAX_FRONTIER_SIZE`） | frontier 完整性 | **有。** 承诺穷举到 3 个 literal，更深的**报告为 truncated 而非静默丢弃**；本次 E11 交叉复核在该边界内确认零遗漏 |
| `cold-start-a0/prime/world/explorer.py:9-14` | A0′ 的覆盖率主张 | **有，且是方法论样板。** 预算是**看见缺口之前**就定死的一个比例，且「every world in the catalogue records the budget it actually used」 |
| `engine-rig/engines/probe_frontier/reach.py:94-99` | 「the configuration is unreachable」 | **没有。** 见丙组——机制安全（触顶抛异常），但 `as_json` 不带上限，产物无法自证 |
| `engine-rig/engines/lp_potential/potential.py:170` | 「无线性 pagoda」 | **没有。** HiGHS 的迭代上限 / 数值困难与真实不可行共用 `None` |
| `engine-rig/engines/zero_space/zerospace.py:141-143` | 定律的 `scope: global` | **没有。** >8 时子集枚举静默退化，`as_json` 无截断标记 |
| `engine-rig/engines/cegis_miner/miner.py:321-323` | frontier 完整性 | **有旗标，但对错了尺子。** `truncated = len(guard) > MAX_FRONTIER_SIZE`——一个 1-literal 的 guard 只枚举到深度 1，仍发 `frontier_truncated: false`。本次交叉复核已按**文档缺陷**正确低调处理（`partials/cegis_miner-via-bruteforce.md:206-217`，深度 3 上 125 处遗漏），因为 `frontier_max_size` 本身是发布且准确的 |
| `engine-rig/engines/deadlock_carver/carve.py:61, 254-280` | `MAX_PATTERN = 2`，触顶就停 | **没有，但不算缺陷。** `carve` 只作肯定断言（「every reachable state containing X is dead」），从不说「不存在 deadlock」；上限的理由写在 `:58-61` |
| `engine-rig/engines/ic3_pdr/pdr.py:237, 268` | `MAX_LEVELS = 64` | **构造上正确。** 触顶 `raise Ic3Error`，其 docstring 明写「An internal invariant of the search broke -- **never a property verdict**」 |
| `a0-spike/pipeline/stages.py:260` | 规则集 | **没有。** 见甲组第 1 条——这里连触没触顶都不是问题，异常本身就没被记 |

---

## 做对了的（样板）

同一条缺陷的正确写法，本仓已经有一整套，按可复制程度排：

* **给「跑不起来」一个第三种取值。** `monitor/ci_merge.py:203-213`：
  `if r.returncode == NO_TESTS_COLLECTED: flag(... "gate misconfigured, not a red suite")`，
  注释写着「read as "green" it would be the fourth time this repo mistook a
  check that cannot run for a check that passed」。
  `arc-recon/precheck.py:264-307`（INC-003）：**UNPLAYABLE ≠ FAIL ≠ PASS**——
  两趟都在第一个动作上死掉、`None == None`、报 PASS「环境是确定性的」，
  正是这条缺陷被抓住并修好的现场。
  `arc-recon/canary.py:326-357`：只有两侧俱在的哈希不匹配才是 DRIFT，
  不完整的 replay 是 INCOMPLETE 并有自己的退出码 4。
  `monitor/gates.py:99-117`：`none` 是显式第三态，并在每行合并日志渲染成 `UNGATED:<dir>`。
  `fuzzlab/props/finding.py:83-100`：`VIOLATED` / `RAISED` / `SKIPPED` 三分，
  `failures()` 只返回 `VIOLATED`；建不出自己世界的 generator 进独立的
  `generator_errors`——「A generator that cannot build its own world is a
  fuzzlab defect, not an engine one, and must not be filed as an engine finding.」

* **给失败一个真实值不可能取到的哨兵。** `monitor/_runner.py:97-107`：异常 → `code = -1`，
  同时镜像进 `exits.json`，「a dead session always leaves a cause of death」。
  `proxy/forward.py:31,134` 与 `theoria-arm/harness/arc.py:133-134`：
  传输失败 → status `-1`，永不与 HTTP 码混淆。

* **失败即拒绝出口，而不是失败即放行。** `proxy/spend_gate.py`：锁原语缺失、
  策略不可读、账本目录不可写、账本有一行不可解释、预留过期——**每一种都抛
  `SpendGateUnavailable` 并拒绝出网**；`_read_locked:543-579` 因一行坏数据而
  否决整个文件，理由写在旁边；无法定价的调用使总额成为一个**声明的下界**
  （`:870-879`）而不是静默的零。

* **把不可用记成不可用，并让下游听得见。** `arc-recon/client.py:271-280`：
  超时 / DNS / reset 得到 `status: -1`、`transport_error` 字段，
  以及一条**在异常重抛之前**写下的完整 ledger 行——因为污染审计
  「can only see what the ledger holds」。
  `figures/sources.py:421-455`：`git ls-files` 失败 → 规则进 `TRACKING_UNAVAILABLE`
  并由 `build_all.py` 报出来，「a weaker guarantee that nobody is told about is
  the failure mode this repository keeps rediscovering」。

* **拒绝把缺席算作满足。** `cold-start-a3/a3pipeline/certify_a3.py:34-37`：
  「reported as red, never downgraded to a pass」。
  `ablation-arm/verify.py:98-120`：「a gate that defaults a missing field to the
  value it wants would pass a run in which the field had silently disappeared.」
  `theory-compiler/src/theory_compiler/deadlock_certificate.py:264-270`：
  拒绝一个没有任何良构状态满足其 pattern 的证书——「it would still say nothing」。

* **要求「因正确的理由失败」。** `theory-compiler/tools/verify_c4.py:160-171`：
  负对照必须 `"closed_pinned" in control["output"]` 才算被正确拒绝，
  而不是只要被拒绝就算；`:70-74` 注明「an unexplained non-zero exit is the one
  outcome that must never be mistaken for "the proof did not go through"」。

* **把上限当上限而不是当结论。** `baseline-arms/harness/campaign.py:98-106`：
  `budget_exhausted` / `spend_ceiling_hit` / `episode_limit_hit` 是三个独立状态；
  `bare_cc.py:526-534`：「an episode killed by the budget tells you nothing about
  the API or about the arm」；`:441-443` 显式写下 `reached_api=False`，
  因为曾有一次审计把「还没调用就放弃」读成了「调用了并且失败」。
  `bare_cc.py:39-89`：`api_unusable` 与 `failure_grind` 分家的事后复盘。

* **`engine-rig/engines/fd_adapter/backends.py` 是本仓这条缺陷的参考实现。**
  `:70-88` 记下实测退出码，然后明确拒绝让退出码单独裁决——
  「the exit code alone does not tell a proof from a shrug」——
  并把 `FD_EXHAUSTED = "Completely explored state space"` 作为附加证据。
  `proves_unsolvable`（`:266-270`）对 exit 12 要求 optimal rung 且日志已穷尽，
  并在 satisficing rung 上**整个拒绝** exit 12（LAMA 在代价上界下搜索），
  docstring 写明这条拒绝的代价。`run_fast_downward:336-341`：既无 plan 文件
  又无证明 ⇒ `RuntimeError`，绝不返回 `None`——所以 `solve_parsed` 在结构上
  不可能从一次崩溃里返回「不可解」。
  `FdMeasurement`（`fdrun.py:112-123`）是真正的四值：
  solved / proved_unsolvable / **not_entitled** / error——`not_entitled` 就是
  「它穷尽了，但这一 rung 无权据此下结论」那一格，`report.py:56-58` 渲染成
  `*not entitled*`，`verify.py:54` 按值比对。
  `choose_tier`（`:146-151`）宁可抛 `FastDownwardMissing` 也不悄悄降到 stub：
  「asking for a named planner and silently getting another one is how a
  benchmark lies.」**回退到 BFS stub 的路径在结构上无法冒充 FD**：
  `Plan.backend` / `Plan.search` 都来自 `fd_search_config`，
  `bench/__main__.py:88` 打印 `NOT REACHABLE -- FD rungs absent`，
  `toolchain.probe` 写 `available: false` 且每个 FD 字段为 `None`。

* **「没得比」不等于「比输了」。** `engine-rig/bench/dividend.py:216-221`：
  无可比对象时 `dividend_is_honest` 是 `None` 而**不是 `False`**，理由写在旁边：
  「nobody claimed a dividend there, so there is nothing to call dishonest.」
  `:290-300`：「A dividend of zero is a finding, not a failure」——
  只有**改变了的最优答案**才算健全性违规。
  `bench/report.py:204-217` 把那句「translator settled it before search」的结论
  卡在 `expansions_before == 0`（一个 int）上，于是失败运行产生的 `None`
  到不了那句话。
  `bench/ladder.py:51` 更进一步：**故意**把 stub 预算调小到让这批实例跑出界——
  「a table where the stub never fails would not show where the stub stops
  being the right answer.」预算耗尽被当作数据，而不是要藏起来的难堪。

* **把选择不修的隐患写清楚。** `cold-start-a3/a3pipeline/plan.py:70-82`：
  UNSAT 靠字符串匹配另一个组件里一条无版本的消息来判定——docstring 点名文件与行号、
  说明替代方案为何更差、并写明后果「the failure would look like a fact about the
  manual」。这是对一个不打算修的危险的正确处理方式。

---

## 我不确定的

1. **`cold-start-a0/certify/fd_unsat.py` 的 exit 12。** 本次 E11 的 `CROSSCHECK.md`
   已经把它登记为跨赛道矛盾（a0 单凭异常串把 12 读成「证明不可解」，
   `engine-rig/backends.py` 认为 12 有歧义、还要求 optimal rung 且状态空间已穷尽）。
   我复核的结论与那条一致，但**谁对**不是我能裁的：a0 的 `classify()` 确实把
   12（`SEARCH_UNSOLVABLE`）与 13（`SEARCH_UNSOLVED_INCOMPLETE`）分开了，
   两边的分歧在于 12 单独是否足够。不重复上报。
   **但有一件是新的**：那次跨赛道复核没有回头看自己家——
   `engine-rig/tools/p13_fd_dividend.py:129` 有一份**同样**的裸 `returncode == 12`。
   拿别人这条的那把尺子，量得到自己。

2. **`exam/grading/selftest.py` 的 fault matrix。** 故障是进程内 patch 的，
   崩溃几乎总是确实由注入的故障引起，所以记为 caught 大概率不假。
   但头条数字无法区分，我给不出「假 caught 有几个」。

3. **`ablation-arm/ablcore/pin.py` 的并发。** 判红也许正是想要的行为——
   宁可停下问人。我不确定它该被算作缺陷还是算作严格。它确实**没有**把
   「另一条赛道在写」与「本 arm 违规写了」分开，这一点是确定的。

4. **`monitor/scan.py:617-625`（`board.py list` 崩溃 → 「板已见底」）与
   `:519-521`（schtasks 非零 → 「未注册」）**：都归错了因，但方向是报警而不是假绿。
   按本次判据它们够不上「不安全」，列在这里以免被当成漏掉的。

5. `battery/audit/exploits` 目前能否 import，我**没有执行**任何代码去验证——
   纯静态阅读。那条发现说的是「若失败会怎样」，不是「它正在失败」。

---

## 一句话

**这个仓库知道这条缺陷，写下过它，也修过它——修了几十处，漏了三十七处。**
漏掉的那些几乎全都紧挨着自己的正确版本：`check_redlines.py:207` 挨着
`enumerate.py:220`；`reflex.py:169` 挨着 `agents.py:106-112` 那段用中文写明
「今天因此把八个活着的工人全报成已停」的注释；`p13_fd_dividend.py:129` 挨着
`backends.py:266-270`。所以这不是要引入新纪律，而是把已有的三种写法
（**第三种取值** / **不可能的哨兵** / **失败即拒绝出口**）
扫到还没扫到的调用点上。

优先级最高的四条，因为它们把环境失败变成了**肯定的**实质主张且毫无痕迹：

1. `a0-spike/pipeline/stages.py:260` — 引擎崩溃 → 发表的规则集。
2. `theoria-arm/inner/plan.py:172` 与 `inner/certify.py:206`（同源）——
   被吞的异常 → 「穷举了整个可达集」/「约束 9 通过」。
3. `release/check_redlines.py:207` — parser 崩溃 → 封存堆红线通过。
4. `engine-rig/tools/p13_fd_dividend.py:129` — 裸 exit 12 → `unsolvable`。

第 4 条最值得单独说一句，因为它是今晚这场交叉复核的**回旋镖**：
E11 用一把很好的尺子量出了另一条赛道把「我放弃了」写成「我证明了」，
而同一把尺子放在自己 `tools/` 上，量到的是同一个数字 12。
