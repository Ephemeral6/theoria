# S9 · 契约改动必须先通告

**W-1250, 2026-07-28, territory `proxy/`, branch `agent/s9-contract-change-protocol`,
base `ff796cd`.** 离线运行：零网络、零 API 花费、封存堆零接触。

## 起点

W-1521 在 `theoria-arm` 轨道报的实盘事故 INC-TA-006：`LEDGER_FORMAT.md` §4 在
**P-8 落地之后**把 `model_call` 的字段集封闭，而 P-8 早已在写
`beat`/`label`/`transport`/`proxied`/`proxy_gap` 五个字段。在线臂按设计把
`proxy/` 当库 import，于是这次收紧**在它从未碰过的提交上悄悄到达**。第一次实盘
desk 调用付了 **$2.695**，写账本时被拒，回复被丢弃，`model_call` 记录数 = 0；
臂自己的 `except Exception` 把它记成「desk 失败」，若不是当场停跑，$15 会照这个
样子烧完。

它在自己轨道修完了调用侧。协议侧它做不了 —— 那是 `proxy/` 的事，本条目。

## 做了什么

### 1. `canon.py` 改为加法安全（D-030）

未列出的字段**告警并保留**，不再拒收。理由不是「宽容一点」，而是：**账本记录是
事后写的**——写手看到 `model_call` 时请求已经发出、钱已经花掉。拒收无法把钱退
回来，只能销毁「它发生过」的唯一证据。**拒绝记录严格劣于记录一个读者可以跳过的
字段。**

仍然拒收的是「错」而不只是「不认识」的东西，这五条一条没动：

| 仍拒收 | 为什么不只是「不认识」 |
|---|---|
| v0 拼法（`frame`/`timestamp`…） | 一个东西两种拼法，正是 F-16 裁的漂移；报错点名替代字段与迁移器 |
| 五个美元拼法，**任意深度** | §5：只追加文件里的价格在改价当天就是错的，且无法更正。见下第 5 条：这条为了保持原样，反而被**扩大**了 |
| 调用方设置信封字段 | §2：`seq`/`ts` 是写手的，调用方设置就是伪造顺序 |
| 缺必填字段 | 记录不是有损，是不可解释 |
| 会产生「像样的错数」的类型 | `True` 求和为 1；裸帧写在列表位是丢观测 |

告警走 `canon.UnknownField`，并在 `Ledger.unknown_fields` 里按 `<event>.<field>`
计数——stderr 上的警告只有当时盯着的人看得到，计数是给运行报告看的。

**加宽时顺手堵掉的一个洞**：`model_call` 整体豁免「像密钥的字符串」模式扫描，理由是
§4 要求 `request`/`response` 逐字保留（RED-15）。但豁免的对象是那两个字段，而不是
`model_call` 这个 event —— 一个格式从没听说过的字段没有任何「逐字保留」的要求，而
在 S9 之前它根本到不了磁盘。让它继承逐字豁免，就是给「金库从没见过的凭证」开一条
**新**路。所以未知字段照环境流量那样过模式扫描，`request`/`response` 不变。

读侧同步：`validate_ledger.py` 把未列出字段记为 **notice**，**不改判决**。
`notices` 是独立出参而不是 `problems` 上的 `severity` 键，这样满仓库的
`assert validate_records(...) == []` 语义不变，也没人能因为忘了过滤就把提示
升级成失败。冻结评分器的 S-12 正是调它的——读侧因为一个可以忽略的字段判整跑失败，
就是同一个错误换个方向。

### 2. 五个字段正式入 §4

不是「顺手加的」，各有真实用途，文档逐个写清：

* **`beat`** —— 让 Theoria.md **约束 8**（大模型只在 theorize 与 probe design
  出现）**从账本上可核**，而不是在散文里被断言。按 `beat` 分组要么给出那两个值，
  要么给出反例。这是「可核的产物」与「关于产物的断言」之间的全部差别。
* **`proxied` / `proxy_gap`** —— 把「完整记录」这条封闭性说到它**真实的大小**。
  `false` 表示这条是臂自己的写手写的、不是在 `model_proxy` 观测到的，完整性因此
  靠臂而非靠构造；`proxy_gap` 说清楚被什么挡住。分不清这两种情况的读者会把弱的
  读成强的。
* **`transport`** —— 跨臂比成本的承重件。CLI 子进程传输没有 prompt 缓存，缓存读
  是**结构性的零**而不是一个小数字（INC-TA-005）。
* **`label`** —— 一个 beat 内区分调用的短标签。

可选字段，不 bump `v`（§8：只有加**必填**字段才 bump）。

### 3. `CONTRACT_CHANGES.md` + 机械半边（D-031）

规则一句话：**加宽免费，收紧是破坏性变更**，必须先在 PARTNER_SYNC 发
`contract-notice` 通告、等一个周期、给兼容窗口（窗口期内旧写法**告警而非拒收**）。
文档给了收紧/加宽对照表（覆盖 §3/§4 字段、required、banned spellings、信封、
`EVENTS`/`ARMS`/`INCIDENT_KINDS`、类型检查、warning→error），以及一个只在
凭证泄漏/封存堆漏洞这类情况可走、且必须按事故立案的快速通道。

只有散文的协议还是散文，而 §1 里失败的正是散文。所以：

* `proxy/canon_contract.json` 钉住 `canon.describe()`，**外加** `ledger.py` 拥有的
  三个注册表 `EVENTS`/`ARMS`/`INCIDENT_KINDS`（`append` 对未注册的 arm/event 是
  硬拒收，检测器看不见它们就比 §2 那张表窄）；
* `python -m proxy.tools.contract` 把实时注册表与钉子做 diff，逐条标
  `additive` / `tightening` / `neutral`；
* `tests/test_contract_changes.py` 一旦两者不一致就让整套挂掉，失败信息就是岔路口。

分类器真正挣钱的地方是一个 set-diff 会**弄反**的区分：往 shape 的 `fields` 加名字
是**放宽**写手，往 `required` 加名字是**拒绝**写手——两者都是「列表变长了」。

**指纹是权威，分类器只是解释**（这条是复核逼出来的，见下）：两个哈希不等而分类器
说不出所以然时，判 `TIGHTENING`；解释了一半也算没解释。

**明说做不到的**：无法验证通告是否真的发了（测试读不了 PARTNER_SYNC 也判不了
一个段落），无法强制等待，且只看得见钉住的那份契约——花费闸门的协议、guard
的判决语义、`cost.py` 的价表只被散文覆盖，没有代码看着。它做到的是**取消这次
事故真正拥有的那个借口**：改契约的人不知道自己在做破坏性变更。

### 4. 本轮自己就按新协议走了一遍

`canon.describe()` 里 `closed_shapes` 这个键名现在是假的（形状不再封闭），改叫
`shapes`。但 `describe()` 是发布给本包无法枚举的读者的，**从发布面上删一个键就是
收紧**——所以 `closed_shapes` 作为弃用别名保留，登记为 C-003，窗口至少到
2026-08-11，并在 PARTNER_SYNC 发了 `contract-notice`。故意挑这么小的一件事来演：
在发布字典里改个键名大概是破坏性变更里最轻的，而这个量级的改动正是会被悄悄做掉的
那种——§1 就是这么发生的。

### 5. 对抗性复核逮到六个真缺陷，全部修完

一个独立子代理只被要求「找真缺陷，不要夸」。它逮到的，按严重度：

**高 · 告警自己就是新的拒收。** `warnings.warn` 在环境过滤器为 `error` 时抛异常
（`python -W error`、`PYTHONWARNINGS=error`、加固过的 CI、进程里别处遗留的
`simplefilter("error")`），而 `UnknownField` 继承 `UserWarning` → `Exception`，
臂的 `except Exception` 照单全收——**同一条丢失的记录、同一笔已付的钱**，
用「替换拒收的那个告警」重新造了一遍 INC-TA-006。子代理跑出来了：`-W error` 下
账本文件根本没被创建。修法：`ledger.append` 传自己的通知器，先记账（不会抛），
再把 `warnings.warn` 包在 `try/except` 里。新增两条测试，一条在 pytest 里用
`simplefilter("error")`，一条在 `verify_contract.sh` 里开真子进程带真 `-W error`。

**高 · `contract` 算了两个指纹却从不比较。** `report()` 打印 pinned/live 两个哈希，
判决却只看分类器建模过的那些 delta——于是任何它没建模的变化不是被**标错**（那是看得见的），
而是被**放行**（看不见）。修法：**指纹是权威，分类器只是解释**。加 `residual()`：
把分类器看的部分剥掉，剩下的两边不等就说明这次改动它没读懂，判 `TIGHTENING`。
而且是「解释了一半也算没解释」——一条 additive 不许替没人看过的部分背书。

**高 · 分类器在唯一已排期的那次改动上发假通行证。** `classify()` 把 `shapes` 和
`closed_shapes` 双双豁免出「已发布键」的 diff，而 C-003 排的正是 2026-08-11 移除
`closed_shapes`。更糟的是我那条测试的 docstring 声称覆盖了它，测试体删的却是
`auxiliary_required`。**一个洞的形状恰好等于下一次排期改动的检测器，比没有检测器更坏。**
修法：豁免去掉，测试参数化成三个键（含 `closed_shapes`），并断言报错点名那个键。

**中 · 冻结评分器的行为变了，冻结记录没变。** S-12 委托给 `tools/validate_ledger.py`，
后者查 `canon.py`——所以本轮改动让 S-12 对同一条流从 FAIL 变 PASS，而 `arc_v1.py`
的哈希一个字节没动，`verify_frozen()` 报全清。**给一条行为部分住在 import 里的规则
冻结源码，是半个冻结，而半个冻结读起来像整个。** 修法：`frozen.json` 的 `arc_v1`
条目**追加**（不改写）`depends_on`，`verify_frozen` 一并核对；`sha256`/`version`
不动，因为语料里没有任何一次已评分的运行会改数——旧写手根本产不出那种流。

**中 · §5 被我自己的加宽悄悄削小了。** 「账本里永不出现美元数字」是**文件**的性质
（RED-42）。加法安全之前，价格只能藏在 §4 要求逐字保留的块里；之后
`{"billing":{"cost_usd":2.695}}` 可以搭一个没人听说过的字段进来——而它前一天是被
拒收的。修法：禁用拼法在**每个未知字段内部递归扫描**，`usage` 也从「看一层」改成
看到底（「一层」从来不是性质，只是第一次攻击的深度）。**在一处加宽不等于别处不用干活**：
本来靠着你正在拆掉的约束撑着的性质，必须用它自己的理由重新立起来。

**中 · 五个字段写了类型、没有检查。** §4 表里 `proxied` 是 `bool | null`，
`check_types` 一条没加。`bool("false")` 是 `True`——**一条臂自己写的记录会被读成
proxy 观测到的**，正是这个字段被加进来要防的那件事。修法：五个字段各自加类型检查。

**中 · 绿灯脚本那句「逐字抄自 `modelcall.py`」快要变成假话。** 臂有一个在途修复
把五个字段**塞进 `request` 里**绕开封闭（master 上仍是顶层写法）。C-001 之后不必再绕，
但在它拆掉之前 `beat` 在实盘账本里有两个深度，`armtools/archive.py` 两个都读——
**这正是封闭当初要避免的那个读者分支**。修法：脚本注释改成如实的两条 caveat；
§4 里「按 `beat` 分组」那句加上「说到它真实的大小」；PARTNER_SYNC 明确宣告顶层写法
重新是正典。

低severity 三条：告警去重后只响一次而计数无人读（→ `runner.py` 把
`unknown_ledger_fields` 写进 `run.json`，e2e 断言干净跑为空）；`EVENTS`/`ARMS`/
`INCIDENT_KINDS` 写在 §2 表里却不在检测器视野（→ 纳入钉子，新增测试）；
`battery` 的 ledger adapter 按键成员分桶，`env_step` 上一个叫 `usage` 的未知字段会
被错分成 model call（→ 别人领地，写进 inbox 提案）。

它明确说**没**找到的：没有任何红队攻击被重开（禁用拼法列表没动，RED-39/41/42/43
仍然落在 `problems` 而不是 `notices`；凭证处理无新泄漏路径），API 变更对现存调用方
安全（`validate_records` 无人传第三个位置参数；`canon.check` 的返回值原本全被丢弃），
`canon_contract.json` 字节稳定，仓库里没有任何 warnings 过滤器会放大或吞掉
`UserWarning`。

## 测试

| | |
|---|---|
| 基线（base `ff796cd`） | `python -m pytest proxy -q` → **259 passed** |
| 交付后 | **295 passed**（+36） |
| 绿灯脚本 | `cd proxy && bash verify_contract.sh` → **VERIFY OK**，九步全绿 |
| 契约指纹 | `sha256:9420fd0fc27d6c2e963d910f611653d2abe62fd35291b7b9bbdf2cd6f9921f35` |

`verify_contract.sh` 里有四步是**把事故（和差点造出来的第二次事故）写成测试**：
用 master 上 `harness/modelcall.py` 的字段集驱动真的 `RunLedger`；开真子进程带真
`-W error` 断言记录仍然落盘；喂给校验器一条带 `a_field_from_2027` 的记录断言
`problems == []` 且恰好一条 notice；把 `canon.py` 的依赖哈希改坏，断言冻结评分器
拒绝评分。

## 缺口（如实登记，不降验收线）

1. **通告与等待无人核。** 见上，写在 `CONTRACT_CHANGES.md` §6 与 `STATUS.md`。
2. **钉子只覆盖 `canon.describe()`。** 花费闸门协议、guard 判决语义、价表不在
   检测器视野内；扩大钉子是显然的下一件，本轮没做。
3. **导入方那一半只能提议，不能实施。** `python -m proxy.tools.contract
   --fingerprint` 要进各臂的 run manifest 并**在两次运行之间做 diff**——这正是
   W-1521 对 `upstream_pin` 的立场建议（写了却从不比对的钉子只在事后记录事故）。
   各臂目录不是本领地，已写进 `monitor/inbox/` 作为提案。
4. **打错的字段名现在是磁盘上的错字**，不再是异常。这是有意的取舍：错字在告警、
   `unknown_fields` 计数（现已进 `run.json`）和校验器 notice 里三处看得见，而另一边
   失去的是整条记录。
5. **§5 是一份名字清单，不是价格探测器。** `usd_spent` 不在清单上，会被写下去——
   而这在辅助记录上一直如此（辅助载荷从来是开的），本轮只是让两个形状也这样。想让
   某个名字被拒，就把它加进 `BANNED_SPELLINGS`，那按 §2 是收紧，因而会被通告。
   写成了一条**测试**，免得被误读成保证。
6. **P-9 的一件钉住产物不再逐字节重现。** `runs/p9-shell-harden/MANIFEST.json` 钉了
   一份 `validate_file` 输出的 sha256，而报告现在多一个 `"notices": []`。没有任何东西
   在重算 `proxy/runs/*` 的哈希，所以它本会静默失败、且只对试图复现 P-9 的人失败。
   如实登记而不掩盖：那件产物在写下时是对的，为了迎合后来的格式去改过去某次运行的
   manifest，正是 `CANON_MIGRATION.md` §7 以同样理由拒绝的动作。
7. **`battery/adapters/ledger_jsonl.py` 按键成员分桶**（`if "frame" in row … elif
   "usage" in row`）。`env_step` 上一个叫 `usage` 的未知字段——S9 之前不可能存在——
   会被静默计成 model call。不是本领地，已写进 inbox。

## 落盘清单

```
proxy/canon.py                       加法安全；五字段入 MODEL_CALL_FIELDS；UnknownField；
                                     禁用拼法递归扫描；五字段类型检查
proxy/ledger.py                      _note_unknown（记账不会抛、告警包 try/except）；
                                     未知字段照过 scrub_keyish；arm/event 拒收的理由
proxy/tools/validate_ledger.py       notices 出参；未知字段不改判决
proxy/tools/contract.py              新：指纹（权威）、快照、方向分类器、residual、CLI
proxy/canon_contract.json            新：钉住的契约（含 events/arms/incident_kinds）
proxy/CONTRACT_CHANGES.md            新：协议 + C-001..C-004 变更账
proxy/scoring/__init__.py            verify_frozen 一并核对 depends_on
proxy/scoring/frozen.json            arc_v1 条目**追加** depends_on（sha256/version 不动）
proxy/runner.py                      run.json 写 unknown_ledger_fields
proxy/LEDGER_FORMAT.md               §4 五字段+类型 + §6 加法安全 + §7 前提失效 + §8 非对称
proxy/CANON_MIGRATION.md             §4/§6 与新行为对齐（对 baseline-arms 是加宽）
proxy/README.md, proxy/STATUS.md     同上
proxy/DECISIONS.md                   D-030, D-031
proxy/tests/test_canon.py            两条「拒收」改写为「保留 + 告警」，另新增 14 条
proxy/tests/test_contract_changes.py 新：20 条
proxy/tests/test_scoring.py          +1：依赖漂移让冻结开火
proxy/tests/test_e2e.py              +1：干净跑的 unknown_ledger_fields 为空
proxy/verify_contract.sh             新：绿灯脚本，九步
monitor/inbox/…-W-1250-…             提案：各臂钉指纹并逐跑比对
```

## 并入 S15（2026-07-29，W-1641）

交付后 `agent/s15-ledger-hashchain` 先落 mainline，`ci_merge` 每五分钟重报同一处
冲突。把 `origin/master`（`64157c1c`）合进本分支，两处真冲突，都是「两边各自在同一
位置追加」：

* `proxy/DECISIONS.md` —— 两边都写了 D-029。已发布的一侧（链）保号，本分支两条
  顺延为 **D-030 / D-031**，并同步 `canon.py` / `ledger.py` / `README.md` /
  `STATUS.md` / `CANON_MIGRATION.md` 与本文件里的引用。两侧条目一条不删。
* `proxy/runner.py` —— 两边各给 `record` 加一个键。**两个都留**：先 `ledger_head`
  （链的判决，读盘上的字节），后 `unknown_ledger_fields`（本跑写了什么，读内存里的
  `RunLedger`）。两者互不可推导，注释里写明了。

合并顺带触发本分支自己装的两个探测器，都按文档的办法重钉、没有放宽：

* `python -m proxy.tools.contract` 报 **TIGHTENING**（`ENVELOPE` 多了 `prev`）。
  按 §3 第 4 步 `--update` 重钉，并在 §5 记 **C-005**，其中写明这次收紧没有走通告
  ——它在本文件还没进 mainline 时就落了地——以及为什么重钉而不是回退：拒收的方向
  是**收紧**（能设 `prev` 的调用方就能伪造链），且仓库里没有任何调用方写 `prev`。
* `scoring.verify_frozen` 的 `depends_on` 因 `canon.py` 改动开火。重冻 canon.py 的
  哈希，`sha256`/`version` 不动；语料里没有一跑改数（既有账本都没有 `prev`）。
  重冻的理由与算式写进 `frozen.json` 的 `depends_on_refreezes`。

门禁：`bash proxy/verify_contract.sh` → VERIFY OK（九步全绿，proxy 全套 323 passed）；
另跑 `bash proxy/verify_spend.sh` → VERIFY: green。全程离线，无 API 调用，无花费。
