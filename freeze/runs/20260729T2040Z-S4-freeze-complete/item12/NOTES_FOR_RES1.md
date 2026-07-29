# item 12（预算表）—— 交给 RES-1 的接线说明

**本子代理没有 `git add` / `commit` / `push`，也没有改 `freeze/verify.sh`。**
下面四件都是给 RES-1 的建议，逐条可粘。

---

## 1 · `freeze/verify.sh` 新阶段（可直接粘，编号待定）

当前 `verify.sh` 已用到 `[14]`，所以下面写作 `[15]`；若同期有别的子代理也在加阶段，
改数字即可，阶段之间无依赖。

```bash
# ------------- 15. the budget table still describes the ledgers
#
# Item 12 was ⛔ 缺 until this kit had a BUDGET_TABLE.md.  A budget table rots
# faster than the hash table does, because its numbers are sums over
# append-only files that keep growing: the moment a run spends a dollar, every
# total in a hand-copied table is false, and false in the direction of claiming
# more headroom than exists.  That is the direction that launches a campaign
# which cannot finish.
#
# The disposition split matters.  A DRIFT is a hard failure: the table claims a
# balance the ledgers do not produce.  POOL ABSENT is also a hard failure here
# and deliberately so -- `proxy/var/` is gitignored, so on a checkout without
# the pool the balance line is unverifiable, and an unverifiable balance must
# not go quietly green.  Use --allow-absent-pool only in a gate where the
# balance is explicitly not the thing under test.
echo "[15] the budget table still describes the ledgers"

bt_out="$(python "$HERE/build_budget_table.py" --verify 2>&1)"
if [ $? -eq 0 ]; then
  ok "build_budget_table.py --verify: balance, unit prices and per-cell projection all recompute"
else
  case "$bt_out" in
    *"POOL ABSENT"*)
      bad "the spend-gate pool is not in this checkout -- the balance in BUDGET_TABLE.md cannot be verified here" ;;
    *"CITATION DRIFT"*)
      bad "a path:line cited by BUDGET_TABLE.md has moved -- the table cites a line that no longer says what it claims" ;;
    *)
      bad "BUDGET_TABLE.md has drifted from the ledgers -- regenerate and read the diff before freezing" ;;
  esac
  printf '%s\n' "$bt_out" | sed 's/^/        /'
fi

# The verdict itself is a NOTE, not a failure, on the same principle as stage
# [11]: "no enumerated scenario fits the remaining balance" is a true statement
# about an unfinished kit, and this script must keep exiting 0 while ⛔ items
# stand.  It is loud because it is the single most consequential line in the
# file.
if printf '%s' "$bt_out" | grep -q "0 fit both"; then
  note "budget verdict: NO enumerated sealed-main-table scenario fits the remaining balance -- see BUDGET_TABLE.md §D-2 before authorising any spend"
fi
echo
```

**一处必须先看的耦合**：阶段 `[8]`（19-vs-21）当前只扫「四份草案」
（`MANIFEST_DRAFT` / `STATS_RULES` / `CLAIMS_TEXT` / `PENDING_FIVE`），
**`BUDGET_TABLE.md` 不在扫描范围内**。若你把它加进去，它里面有三处**合法**的 21：

| 处 | 用途 | 为什么合法 |
|---|---|---|
| `G5` 的「公开集 / 开发堆 / 封存堆 25 / 4 / 21」 | 切堆事实 | 不是分析单元计数 |
| `G5` 的「封存堆 21 局官方基线动作 14,121」与「÷ 21」 | S1 分母（21 局均值） | 本文已明写「这是 21 局的均值，不是 19 局的实数」，并挂了 ⛔ 12-C2 |
| `D` 节的「若监控定 21，把 `G6` 每一行 ×21/19」 | 上界口径的重标系数 | `PENDING_FIVE.md:130-135` 的「跑多少局 ≠ 统计分母」 |

**投影本身用的是 19**（`G5`/`G6`）。要加扫描请连带把这三处加进 allowlist 并写理由，
否则阶段 8 会因为一份诚实的文件判红。

---

## 2 · `freeze/build_manifest.py` 的 item 12

当前 `:218-227` 是：

```python
"n": 12, "name": "预算表", "status": "blocked",
"paths": ["proxy/pricing/pricing_v1.json", "proxy/cost.py",
          "theoria-arm/harness/budget.py", "baseline-arms/BUDGET_REPORT.md",
          "baseline-arms/out/campaign_gate.json"],
```

**建议：加三条路径，`status` 不动。**

```python
"paths": ["freeze/BUDGET_TABLE.md", "freeze/BUDGET_TABLE.json",
          "freeze/build_budget_table.py",
          "proxy/spend_policy.json", "proxy/pricing/pricing_v1.json",
          "proxy/cost.py", "theoria-arm/harness/budget.py",
          "baseline-arms/BUDGET_REPORT.md",
          "baseline-arms/out/campaign_gate.json"],
```

`proxy/spend_policy.json` 现在**不在**清单里，而它是上限的唯一权威落点
（`:4` 的 $214.90）。一份哈希了价目表却没哈希上限的预算清单，
能证明「一次调用值多少」，证明不了「一共许花多少」。

**`status` 仍应是 `blocked`**：`Theoria.md:377` 要的三个数
（⟨$/局硬顶、总局数、止损⟩）依然是 ⟨…⟩，只有监控能填。
表存在 ≠ 预算已定。现有 note 说的是「三个数还写作 ⟨…⟩」，那句**仍然为真**，
不必改；只需在 note 末尾加一句「表已落盘于 `freeze/BUDGET_TABLE.md`，
`build_budget_table.py --verify` 是它的闸门」。

若决定提交 `freeze/POOL_DIGEST.json`（见下），把它也加进 paths。

---

## 3 · `freeze/MANIFEST_DRAFT.md` 第 12 行 / §12

`:56` 的总览行与 `:385-409` 的 §12 现在都写「⛔ **缺**」。建议：

* 总览 `:56` → `| 12 | 预算表 | ⚠ 有，**三个数仍 needs_human** | `freeze/BUDGET_TABLE.md`（本套件）|`
* §12 标题 → `## 12. 预算表 ⚠ —— 表已落盘，三个数未填`
* §12 正文首句「**树上没有「预算表」这个东西。**」**已不成立**，
  按套件惯例（`:266` 对消融臂那条的写法）划掉并注明日期，而不是删掉。
* `:59` 的计数「✅ 3 · ⚠ 8 · ⛔ 2」→ `✅ 3 · ⚠ 9 · ⛔ 1`（只剩第 5 项引擎清单）。
  **请你自己核一遍这个计数**，同期还有别的子代理在动别的行。

---

## 4 · `freeze/POOL_DIGEST.json` 要不要进 git —— 需要你或监控拍

`proxy/var/spend_gate.jsonl` 是 gitignore 的（`proxy/.gitignore:3`），
所以**决定余额的那个文件进不了冻结清单**。已实现的补救：

```bash
python freeze/build_budget_table.py --emit-pool-digest
```

生成 2 KB 的追踪脱敏摘要（白名单式：`holder`/pid/host、`reservation_id`、
`policy_sha256`、全部 `detail` 载荷都不抄；已实测确认里面没有主机名、
没有 reservation id、没有任何凭据形状的串）。

**拍板点**：进 git 则冻结时的余额在案且可引用（当期**完全没有**这件事）；
不进则 `MANIFEST.json` 永远缺一行，且 `SPEND_GATE.md:256-259` 写明的
「删掉池子就重置总数」没有任何 tracked 的东西记得删之前是多少。
两条限度写在 `BUDGET_TABLE.md` 的 `E·C2`。

---

## 5 · 与我无关的两处现存红

跑 `bash freeze/verify.sh` 当期 `DRAFT INCOMPLETE -- 2 check(s) failed`：

* `[12] MANIFEST.json 漂移` —— 逐条比过，漂的是
  `battery/audit`、`proxy/cost.py`、`baseline-arms/out/campaign`、
  `freeze/STATS_RULES.md`、`freeze/VARIANCE_BASIS.md`、`envelope.json`，
  并且 item 13 的 status 会从 `blocked` 翻成 `partial`。**没有一条是我加的文件**
  （我加的四个路径都不在 `build_manifest.py` 的 ITEMS 里）。
* `[14] residuals.py` —— `freeze/RESIDUALS.json` 不存在（`FileNotFoundError`）。
  那是别人在飞的东西。**我的 15 条 ⛔ 缺口在 `BUDGET_TABLE.md` §F，
  格式是表格而不是 `RESIDUALS.json` 的 schema**；若 `residuals.py` 要接管它们，
  编号已经是 `12-A1`…`12-E4` 的形式，逐条带 owner 与落点，可直接搬。
