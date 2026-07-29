# b2 — baseline-arms（盲判，13 个入口）

判定员未见任何探针输出（树里无 `verify-lab/`）。全部 `读码`。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据强度 | 证据 |
|---|---|---|---|---|---|
| baseline-arms/harness/arc_client.py | 是 | 是 | 不适用 | 读码 | `arc_client.py:248` `raise SealedGameError`、`:261` `raise spend.NoSpendBinding`、`:342` `raise ArcApiError`（均冒到调用者）。负控打的是本文件：`tests/test_transport.py:273-279` `pytest.raises(SealedGameError)` 两例 + `:279` 绿侧对照；`tests/test_spend_binding.py:36-39`（无 binding 必须 raise）、`:86-102`（断言 `opened == []`，拒绝必须发生在 socket 之前）。本文件无 `__main__`、无退出码路径 |
| baseline-arms/harness/bare_cc.py | 是 | 是 | 部分 | 读码 | `bare_cc.py:573` `return 0 if summary["outcome"] not in ("no_reset_window","api_unusable") else 1`；`:299` `raise NoSpendBinding`；`:169/:197/:203` `raise ModelError`。负控打本文件：`tests/test_spend_binding.py:42-44` `pytest.raises(NoSpendBinding)` 直击 `bare_cc.play`；`tests/test_transport.py:217-253` 全 400 重试路径断言。退出码只对 2 个 outcome 变红：`:367 spend_ceiling_hit`、`:425 model_error`、`:432 gave_up/unparseable_reply`、`:480 failure_grind`、`:532 spend_gate_tripped` 都打印并落进 JSON，进程仍退 0 |
| baseline-arms/harness/campaign_status.py | 是 | 否 | 是 | 读码 | `campaign_status.py:18-19` 无 checkpoint 时 `return 1`；`:38` `s["game_id"]` 无保护，畸形 JSON 会 KeyError 冒顶。全树搜 `campaign_status` 在 `test_*.py`／`*.sh`／任何 runner 里零命中 |
| baseline-arms/harness/fetch_schema_traces.py | 是 | 是 | 是 | 读码 | `:164` `raise WhitelistError`（partition 的二次更严检查）、`:219` `raise WhitelistError`（socket 前）、`:183` `raise RuntimeError`、`:263-266` 打印 "refusing" 并 `return 4`。负控打本文件：`tests/test_whitelist.py:92-100` monkeypatch 掉 `classify` 使其放行封存路径，断言 `pytest.raises(WhitelistError)`；`:57-61` 对每个封存 id 断言 `deny_sealed`。唯一缺口：`main()` 本身没被测过 |
| baseline-arms/harness/ledger.py | 部分 | 否 | 不适用 | 读码 | `:105` `raise ValueError`（arm 不在 `ARMS`）只对调用者成立；`__main__`（`:242-243`）只 print 一个 report，所有读取都被 `os.path.exists` 保护、`json.JSONDecodeError` 被吞（`:177-178`、`:219`）。负控：`test_*.py` 里只有 monkeypatch 目标（`test_transport.py:154`、`test_spend_binding.py:54`），无人构造坏 arm；唯一执行它的是 `proxy/verify_spend.sh:98`，纯绿侧冒烟 |
| baseline-arms/harness/probe_action_variants.py | 是 | 否 | 是 | 读码 | `:98` `return 0 if any_ok else 1`；`:50` `assert_playable` 可抛 SealedGameError。全树零测试命中。`:97` 打印 `VERDICT: no ACTION shape works` 与非零退出一致 |
| baseline-arms/harness/probe_api.py | 是 | 否 | 是 | 读码 | `:81` `return 0 if playable else 1`。全树零测试命中。`:79` 打印 `PLAYABLE ...: NONE` 时确实走 `return 1` |
| baseline-arms/harness/run_pilot.py | 是 | 否 | 部分 | 读码 | `:71` `return 2`（`--only-game` 无匹配）、`:78` `assert g not in sealed`、`:42-43` SealedGameError 重新抛出。全树零测试命中。`:44-49` 把每个 cell 的任意异常吞成 `outcome="harness_error"`，`:51` 打印出来，`:95` 仍 `return 0` —— 十二个 cell 全炸也退 0 |
| baseline-arms/harness/summarise_campaign.py | 是 | 否 | 否 | 读码 | `:131` 无 cell 时 `return 1`；`run_campaign.load_cells:189` 的 `json.loads` 无保护。全树搜 `summarise_campaign` 零命中（gate 逻辑的负控在 `test_spend_binding.py:184-250`，打的是另一份文件 `run_campaign.py`）。`:183` `run_campaign.print_gate` 会打印 `=== budget gate: RED ===` 和 `TRIPPED: ...`，`:184` 照样 `return 0` |
| baseline-arms/harness/summarise_envelope.py | 部分 | 部分 | 不适用 | 读码 | 无任何设计好的非零返回，`:297` 恒 `return 0`；`:140` 的 `raise ValueError` 带 `# pragma: no cover` 且 CLI 不可达。负控：`tests/test_envelope.py:142-143` 有一条自称负控的差分对照（断言污染确实改变了数字），但全文件无 `pytest.raises`、无坏输入必败、无人调用 `main` |
| baseline-arms/harness/summarise_pilot.py | 是 | 否 | 不适用 | 读码 | `:116` 无 pilot 输出时 `return 1`；`:40` `json.load` 与 `:47` `cell["game_id"]` 无保护。全树零测试命中。它只逐字转述数据里的 outcome，自己不产出 FAIL/mismatch 类判决 |
| baseline-arms/harness/unit_prices.py | 部分 | 否 | 否 | 读码 | `main`（`:289-303`）没有任何非零返回分支，只有 `:73-74` 的无保护 `json.load` 崩溃能红。负控：`tests/test_envelope.py:173-213` 只测 `aggregate()` 且全部从绿侧比数字。`:229-232` 会打印 `MIXED in ... -- the split is not trustworthy`，`:303` 仍 `return 0` |
| baseline-arms/runs/20260728T103135Z-a7/await_quota.py | 是 | 否 | 是 | 读码 | `:93` 超过 `--give-up-after` 时 `return 1`；`:34` `parse_utc` 对坏 `--until` 抛 ValueError。全树搜 `await_quota` 只有它自己的 3 处自引用，零测试、零 runner |

判定员附注：

1. 13 个入口里**没有一个的 `main()` 退出码被任何测试或脚本验证过** —— 全树 `test_*.py`
   中零处调用 `.main(...)`，唯一的 sh runner `proxy/verify_spend.sh:98` 只从绿侧跑 `ledger.py`。
2. 负控集中在三个文件：`fetch_schema_traces`、`arc_client`、`bare_cc`；其余 10 个零命中。
3. 两处最硬的「退出码不诚实」：`unit_prices.py:229-232` 与 `summarise_campaign.py:183-184`，
   都是打印 RED/不可信之后退 0。
4. 最没把握的一格是 `summarise_envelope` 的「有负控」：`test_envelope.py:142-143` 自称
   negative control 且确实可执行，但断言的是「数字变了」而非「坏输入必败」，压到 `部分`。
5. `summarise_envelope` / `unit_prices` 的「能红」判 `部分`：存在能让它非零退出的输入
   （畸形 JSONL 崩溃），但没有任何判决驱动的非零路径。
