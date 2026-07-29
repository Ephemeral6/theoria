# 领地：proxy / arc-recon

普查员：RES-3 / V11。工作副本 `.worktrees/v11-negative-control-census/`。
零网络（只跑离线套件与回环 sink）；封存堆零接触（封存 ID 仅作为字符串出现在
回环负控里，未向任何真实端点发出）；未读取 `.env` 的值。

实跑两次：
- `cd proxy && python -m pytest -q` → **exit 0，259 项全过**（`实测`）
- `cd arc-recon && python -m pytest -q test_hygiene.py test_canary_schedule.py` → **82 passed**（`实测`）

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据 |
|---|---|---|---|---|
| `proxy/guard.py` SealedPileGuard（封存护栏） | 是（实测） | 是（实测） | 不适用（库；代理侧映射 403） | `proxy/tests/test_guard.py:29,36,48,55`；`tests/test_seal.py:109,146,155`；`tests/test_redteam.py:523,539,545,559,584,595,620,644,680,690,704` |
| `proxy/guard.py` `load_piles` 切分完整性（钉死 sha256） | 是（实测） | 是（实测） | 不适用（raise `PilesIntegrityError`） | `tests/test_guard.py:19`（篡改切分）；`tests/test_redteam.py:620`（重新签名的切分 RED-30）、`:644`（RED-31） |
| `proxy/env_proxy.py` 请求闸（403 + `guard_block` + incident + 空帧 env_step） | 是（实测） | 是（实测） | 不适用（HTTP 403，非进程） | `tests/test_seal.py:109,125,146,155`；`tests/test_redteam.py:704` |
| `proxy/model_proxy.py` 提示词里的封存 ID | 是（实测） | 是（实测） | 不适用 | `tests/test_redteam.py:680`（RED-32） |
| `proxy/mock/arm_mock.py` `assert_sealed`（arm 持凭证即拒启动） | 是（实测） | 是（实测） | 不适用（raise `NotSealedError`） | `tests/test_seal.py:51-54` 参数化跑遍 `FORBIDDEN_ENV` |
| `proxy/redact.py` Vault / `scrub_outbound`（密钥密封） | 是（实测） | 是（实测） | 不适用 | `tests/test_ledger.py:92`；`tests/test_redteam.py:368,381,393,406,422,434,447,462,474,487`（RED-10..19） |
| `proxy/ledger.py` + `canon.py` 写入端拒绝（非规范字段 / 成本禁令 / frame_hash） | 是（实测） | 是（实测） | 不适用（raise，且不落盘） | `tests/test_canon.py:25-137`；`tests/test_redteam.py:887,907,917` |
| `proxy/tools/validate_ledger.py`（账本校验） | 是（实测） | 是（实测） | 是（读码：PASS→0 / FAIL→1，`validate_ledger.py:170`） | `tests/test_canon.py:137`（伪造 frame_hash）、`:152`（重复 seq）、`:159`（level 不可重算）；`tests/test_redteam.py:856` |
| `proxy/reconcile.py`（对账义务） | 是（实测） | 是（实测） | **部分**（读码：`reconcile.py:172` 把 `EMPTY` 与 `PASS` 一并判 0——不存在的 run-id 也退 0） | `tests/test_e2e.py:177`；`tests/test_redteam.py:772,791,803,818,830,855,872,933,981` |
| `proxy/scoring/`（冻结计分器 S-0..S-12 + 自哈希） | 是（实测） | 是（实测） | 是（读码：`scoring/__init__.py` 全 PASS→0 否则 1） | `tests/test_scoring.py:36`（改过的计分器拒绝计分）、`:161,168,178,185,194,201,211,219,227,242,253,270` |
| `proxy/replay.py`（replay 审计） | 是（实测） | 是（实测） | 是（读码：`replay.py:170`） | `tests/test_e2e.py:140` 篡改账本 → replay FAIL + `replay_mismatch` incident |
| `proxy/tools/replay_spotcheck.py` | 是（实测） | 是（实测） | 是（读码：`replay_spotcheck.py:215`，`INSUFFICIENT` 也判非零） | `tests/test_migration.py:198,206,216,221` |
| `proxy/spend_gate.py` SpendGate（花费闸 / 配额闸，reserve+check+record） | 是（实测） | 是（实测） | 不适用（raise `SpendGateTripped` / `Unavailable` / `NoReservation`） | `tests/test_spend_gate.py` 全 60 项（缺策略、零上限、损坏账本行、过期租约、无预约花费、NaN/Inf、无 permit 的 forward…）；`tests/test_spend_gate_concurrency.py:148,163,175` 多进程竞态下上限仍守住 |
| `proxy/spend_gate.py` `__main__`（池子报表） | **否**（读码：`spend_gate.py:1214` 恒 `return 0`） | 否 | **否** | `verify_spend.sh:9` 把它写成"查池子是否在上限内"的办法，但超限它也退 0 |
| `proxy/verify_spend.sh` | 是（读码：`fail=1; exit "$fail"`） | 部分（读码） | 是（读码） | 内部三条 grep 式检查（无 off switch / 无绕过 socket）没有植入违例的负控；同一断言在 `tests/test_spend_gate.py:419,426` 里从内部再断一次，但同样只在干净仓库上跑通。**未跑：会调用 `baseline-arms/harness/ledger.py`，属别的领地** |
| `proxy/tools/upgrade_ledger.py` | 部分（读码：不认识的记录 raise；`main` 恒 0） | 是（读码） | 部分 | `tests/test_migration.py:148,153`（拒绝不认识的记录 / 拒绝二次抬升）——靠 raise 非零而非 `return` |
| `proxy/cost.py`、`proxy/runner.py` | 否（读码：报表 / 跑手，恒 0） | 不适用 | 不适用（非闸门） | `cost.py:166`、`runner.py:269` |
| `arc-recon/precheck.py` `assert_playable`（封存护栏） | 是（实测） | 是（实测） | 是（读码：`precheck.py:414` → 2） | `test_hygiene.py:124`（`ls20` / `ft09` 被拒 + 开发局放行的负控）、`:132` |
| `arc-recon/canary.py` `compare`（漂移仪表） | 是（实测） | 是（实测） | 不适用（库） | `test_hygiene.py:54,62,70,77`——INC-003 的形状：缺步必须读作 INCOMPLETE 而非 PASS |
| `arc-recon/canary.py check-freeze` | 是（实测） | 是（实测） | 是（实测） | `test_hygiene.py:95-98` 直接断言退出码从 0 翻到 1 |
| `arc-recon/canary.py` `INVOCATION_CAP`（配额闸） | 是（实测） | 是（实测） | 是（读码：`canary.py:678` → 3） | `test_hygiene.py:140`（24 计划 > 20 上限 → `BudgetExceeded`） |
| `arc-recon/canary_schedule.py`（排程 + 闸门映射） | 是（实测） | 是（实测） | 是（实测） | `test_canary_schedule.py:341`（闸门拒绝即停）、`:359`（CLI 映射到 exit 5）、`:392`（每个可能的结局都有退出码）、`:246`（封存目标在排程前就被拒） |
| `arc-recon/contamination.py` `verify_piles_hash` | 是（读码） | **部分**（只在好文件上跑通） | 是（读码：`contamination.py:338`） | `test_hygiene.py:203` 只断言现网切分匹配；没有构造被篡改的 `piles.json` 断言 MISMATCH（proxy 侧 `test_guard.py:19` 有，arc-recon 侧没有） |
| `arc-recon/contamination.py` `sealed_api_contacts`（封存接触审计） | 是（实测） | 是（实测） | **否**（实测） | 负控在：`test_hygiene.py:419,431,474`。退出码：见下方点名 |
| `arc-recon/contamination.py` `claim_set` 的 `needs_adjudication` | 是（实测） | 是（实测） | **否**（实测） | 负控在：`test_hygiene.py:354,368,378`。退出码：见下方点名 |
| `arc-recon/verify.sh`（arc-recon 绿灯） | 是（读码：`fail=1; exit "$fail"`） | **部分** | **部分**（实测） | `verify.sh:53` 那一步的标签写着"pile cut, claim set and the sealed-contact audit"，但它调用的 `contamination.py` 只让切分哈希决定退出码 |
| `arc-recon/redact_ledger.py --check`（凭证/cookie 值落盘检查） | 是（读码：`redact_ledger.py:138` 有 offender → 1） | **否** | 是（读码） | 没有构造"账本里有 cookie 值"的 fixture 断言 `scan()` 报红；`test_hygiene.py:319` 的正控测的是**测试文件自己的** helper `_cookie_value_offenders`，不是 `redact_ledger.scan` |
| `arc-recon/client.py` 密钥密封（`_record` 里 `X-API-Key`→`<redacted>`） | 部分（读码：只是按 header 名替换，没有拒绝/告警路径） | **否** | 不适用 | `client.py:300`。没有任何测试把密钥值植入 body / response_body / 其他 header 再断言它不落盘 |
| `arc-recon/client.py` `load_api_key`（缺失即拒） | 是（实测） | 是（实测） | 不适用（raise） | `test_canary_schedule.py:429-433` |
| `arc-recon/cut_piles.py`（拒绝二次切分） | 是（读码：`cut_piles.py:136` → 2） | **否** | 是（读码） | 没有测试构造"piles.json 已存在"断言退 2 |
| `arc-recon/precheck.py` `main` | 部分（读码） | 不适用 | **否**（读码：FAIL/UNPLAYABLE 的局只进 `excluded`，`precheck.py:458` 仍退 0） | 只有封存拒绝(2)/超预算(3)非零。**未跑：需网络** |
| `arc-recon/recon.py`、`probe_stickiness.py`、`precheck_resume.py` | 否（读码：恒 0 / 无判据） | 不适用 | 不适用（采集脚本，非闸门） | **未跑：需网络** |

## 三条高风险闸门的负控状况

- **封存护栏：有**（两层，都被演示过会红）
  - proxy 层：`proxy/tests/test_seal.py:109` 构造一个真实 HTTP 请求，body 里放封存局
    `dc22-fdcac232`，断言代理回 403 且 `rule == "sealed_pile"`；同一测试还起了一个**会乖乖
    伺服它的** mock 上游，证明拒绝是代理做的、不是上游做的。短 ID 形式在
    `test_guard.py:36`（`guard.verdict("dc22") is False`）和 `test_redteam.py:523`
    （RED-20，bare stem `ls20`，并断言上游 sink 什么都没收到）。
    另有大小写、百分号编码、全角/零宽、base64、跨字段拆分、header 参数、chunked body、
    只带 session guid 的命令（RED-21..RED-34）。
  - arc-recon 层：`test_hygiene.py:124`（`ls20`/`ft09` 拒、开发局放行的负控）、
    `:132`（花钱之前就拒）、`test_canary_schedule.py:246`（排程前就拒）。
  - **这条论文级承诺有可执行证据。** 259+82 项实测全绿。

- **密钥密封：部分**
  - proxy 侧 **有，而且很硬**：`test_redteam.py:368/381/393`（上游反射密钥到 body /
    header / 模型代理，断言 arm 拿不到）、`:422`（短于 `MIN_SECRET_LEN` 的密钥）、
    `:434`（vault 从没见过的第三方密钥）、`:462`（密钥当成 dict 的**键**）、
    `:474`（拆成两段 / base64）、`tests/test_ledger.py:92`、`tests/test_seal.py:82,97`。
    每一条都是"构造一次泄漏，断言被抓"。
  - arc-recon 侧 **没有**。`client.py:300` 只按 header 名把 `X-API-Key` 换成 `<redacted>`；
    `request_body` / `response_body` / 其他 header 完全不过滤，也没有 vault。
    `client.py` 的模块 docstring 与 `redact_ledger.py:1-13` 都在引用"凭证从不落盘"这条不变量，
    但**没有任何测试把一个密钥形状的值放进 body 或 response 再断言它没进
    `data/recon_ledger.jsonl`**。cookie 值那一半（INC-008）有很好的负控，密钥这一半没有。

- **账本完整性：有（proxy），部分（arc-recon）**
  - proxy：`tests/test_canon.py:137/152/159` 三个**故意损坏的记录** fixture 断言
    `validate_records` 必须报出 `frame_hash_mismatch` / `duplicate_seq` /
    `level_does_not_recompute`；`test_redteam.py:772..993`（RED-35..RED-46）整整一类
    "伪造记录"攻击，全部断言 `reconcile_run(...)["verdict"] == "FAIL"`，包括
    整份手写账本（RED-40）、追加第二条 `run_end`（RED-35）、借另一个 arm 的记录凑账
    （RED-38）、把成本藏进 `usage`（RED-42）。
    `test_e2e.py:140` 篡改账本后 replay 必须 FAIL 并留下 incident。
  - arc-recon：`recon_ledger.jsonl` 没有"故意损坏 → 必须 FAIL"的 fixture。
    `redact_ledger.scan()` 只在真实（干净）账本上跑通。

## 点名：没有负控的闸门

1. **`arc-recon/redact_ledger.py` 的 `scan()`** —— 它是 `verify.sh:56` 那一步的全部内容
   （"no credential or cookie value reached the ledger"）。没有任何 fixture 构造一条带
   cookie 值的账本行断言它必须报红。`test_hygiene.py:319`
   （`test_the_cookie_value_detector_can_actually_fail`）看起来像负控，但它测的是**测试文件
   内部定义的** `_cookie_value_offenders`，与 `redact_ledger.scan` 是两份代码。
2. **`arc-recon/client.py` 的密钥落盘防线** —— 见上，无构造式泄漏测试。
3. **`arc-recon/contamination.py` 的 `verify_piles_hash()`** —— 只有正向断言
   （`test_hygiene.py:203`）。被篡改的切分文件必须 MISMATCH 这一条没有被演示过。
   （proxy 侧的同名保证有 `test_guard.py:19` 与 RED-30/31 顶着，所以整体风险不高，
   但 arc-recon 的 `verify.sh` 依赖的是自己这一份。）
4. **`arc-recon/cut_piles.py` 的"拒绝二次切分"** —— 无测试。
5. **`proxy/verify_spend.sh` 的三条 grep 式检查**（无 off switch / 每个 socket 都过 permit）
   —— 只在干净仓库上跑通，没有植入一个违例文件证明它会红。

## 点名：退出码撒谎的闸门

1. **`arc-recon/contamination.py`（最严重）** —— `contamination.py:338`
   `return 0 if check["matches"] else 1`：退出码**只**反映 `piles.json` 的哈希。
   两条它自己会大声打印的红色结论完全不影响退出码：
   - `all_ledger_audit()["all_clean"] is False`（**某个封存局被真的请求过**）
   - `claim_set()["needs_adjudication"]` 非空（某局泄漏级别到了 material 却没被隔离）

   **实测（在 worktree 内、只用临时目录、未改任何被跟踪文件）**：
   - 植入一行 `vc33-5430563c / mechanics_disclosed / 无 claims` 到临时 log →
     打印 `NEEDS ADJUDICATION (excluded from clean): vc33-5430563c`，
     **EXIT CODE = 0**。
   - 把一个含 `POST /api/cmd/RESET {"game_id":"ls20-9607627b"}` 的临时账本加进
     `OTHER_LEDGERS` → 打印 `sealed ADDRESSED: ls20-9607627b`，**EXIT CODE = 0**。

   后果：`arc-recon/verify.sh:53` 的那一步标签写着 "pile cut, claim set and the
   **sealed-contact audit**"，它会打印 `-- ok`，脚本最后打印 `VERIFY: green`。
   也就是说，**"封存堆零接触"这条承诺的自动化绿灯，在真的发生接触时不会变红**。
   （负控本身是有的、在函数层面很扎实——红的是从函数到退出码这一段线断了。）

2. **`proxy/spend_gate.py` 的 `__main__`** —— `spend_gate.py:1214` 恒 `return 0`。
   `verify_spend.sh:9` 明说"要知道池子是否在上限内，跑 `python -m proxy.spend_gate`"，
   而它超限也退 0。（真闸门 `SpendGate.reserve/check/record` 是 raise，那一侧健康。）

3. **`proxy/reconcile.py`** —— `reconcile.py:172` 把 `EMPTY` 与 `PASS` 一起判 0。
   `--run-id` 打错字、或指向一个没有 `env_step` 的 run，退出码是绿的。

4. **`arc-recon/precheck.py`** —— `precheck.py:458` 恒 0：确定性检查判 `FAIL` /
   `UNPLAYABLE` 的局只被写进报告的 `excluded` 字段，退出码不变。
   只有封存拒绝（2）和超预算（3）非零。（需网络，未跑，读码。）

## 我不确定的

- **`proxy/verify_spend.sh` 我没跑**：它内部会执行 `baseline-arms/harness/ledger.py`，
  那是别的领地，可能写文件。所以该脚本整体是 `读码`；它包住的 pytest 部分我单独跑了（全绿）。
- **`arc-recon/verify.sh` 我没整脚本跑**：它会 `contamination.py --json`，
  那一步**会重写被跟踪的 `arc-recon/data/claim_set.json`**。我只跑了它包住的 pytest，
  以及在临时目录里以库函数形式复现了 `contamination.main([])` 的退出码（不带 `--json`，
  不写任何仓库文件）。
- `contamination.OTHER_LEDGERS` 只列了 `baseline-arms/ledger.jsonl` 和 `probe_log.jsonl`。
  当前工作树里还有未跟踪的 `baseline-arms/out/shards/ledger.*.jsonl` /
  `probe_log.*.jsonl`，不在扫描范围内。模块自己的 `caveat` 承认了这点
  （"evidence over the files scanned, not a proof over all traffic"），
  所以我没把它记成撒谎，只记成覆盖面缺口——但它和上面第 1 条叠加时，
  "零接触"的可执行证据比标签看起来弱。
- proxy 套件跑出 exit 0 与 259 个点，但 `-q` 的汇总行在本机被吞了（跑了三次都一样），
  所以"259 项"是数点数得来的，不是 pytest 自报的。
- 我没有评估 `release/check_redlines.py`（按指示不算 proxy 的负控），
  也没有检查任何主工作树文件。
