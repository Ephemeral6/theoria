# DRIFT-the-freeze-kit-says-what-protects-it-and-two-of-those-sentences-are-false
severity: high
dimension: 7（不可能变红的检查）+ 6（要求引用了不存在的东西）
cycle: 43 (OPS-A)

## claim

冻结套件里有三句话，各自声明「这一份被什么盯住」。**其中两句是假的，而且是可执行地假的**：
把该被盯住的东西改坏，`--verify` 仍然退出 0。这不是「闸门没接线」（那条我起草时写过，
被对抗性复核**推翻了**——七个脚本里五个确实接进了 `verify.sh`）。这条比那条窄，也比那条硬：
**闸门接没接是排程问题，而一句声称保护存在的注释是假的，读它的人会据此不再检查。**

## evidence

### 假句 1 —— `n_feasibility.py`：测量不在封条里（有两个存活变异体）

`freeze/n_feasibility.py:63`（主线）逐字：

> `#: 键名进闸门的哈希，所以增删一份测量必须是一次显式改动。`

`:121-124` 是那个哈希：

```python
def floors_digest():
    payload = json.dumps({"floors": FLOORS, "power": POWER,
                          "n_ruled": N_RULED}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
```

**`MEASUREMENTS` 不在 payload 里。** 注释说的那件事，代码没做。
而这个文件的头部自己记着它第一版就犯过同一个错（「第一版声称…**那句话是假的**」）——
**同一个文件在同一个属性上第二次说了假话。**

**变异测试（`%TEMP%` 副本，仓库文件未动，7 个变异体）**：

| 变异 | 结果 |
|---|---|
| `FLOORS` 下限 14→10 | **killed**（rc=1，这正是 stage 13 自带的负样本） |
| `POWER` 0.80→0.50 | **killed** |
| `cp_upper` 换成点估计 | **killed** |
| `A7-postfix` 的 `episodes` 9→90 | **存活**（rc=0） |
| 注入一份编造的第四条测量、`usable_as_q=True` | **存活**（rc=0） |
| 删掉 `usable_as_q` 守卫整块 | **存活**（今天条件恒假，删掉不可观测） |
| `verify()` → `return []` | **存活**（没有别的东西调 `verify()`） |

**代价是published的数字**：把 `episodes` 改成 90，`--verify` 绿着，表格印
`0/90 … CP 上端 0.0402`，而同一个程序 `:217` 硬编码的结论串仍断言 `0/9，CP 上端 0.3363`
——**后者就是 `freeze/STATS_RULES.md:825` 正在发布的那一行**（`| 0/9 | 0.0000 | 0.3363 | **0.9846** |`）。
文档行与代码之间没有任何东西相连。

### 假句 2 —— `residuals.py`：那张表并没有进任何哈希

`freeze/residuals.py:51` 逐字声明它那份硬编码 `DOCS` 名单为什么可以被信任：

> `所以这张表本身也进 verify.sh 的哈希`

实测：`freeze/MANIFEST.json` 的 61 条 pinned path 里，**`residuals`／`RESIDUALS.json`
出现 0 次**（`git show origin/master:freeze/MANIFEST.json | grep -c residuals` → `0`）。
它给自己那条已知局限（名单是手写的）提出的缓解措施**不存在**。

### 假句 3（较弱，但同族）—— `POOL_DIGEST.json` 的存在理由未达成

`freeze/BUDGET_TABLE.md:512-514` 说这份文件存在是「于是清单能哈希一份
『冻结时余额是这个数、池子是这个 sha256』的凭据」。文件确实被跟踪了，
**而 `MANIFEST.json` 里 `POOL_DIGEST` 出现 0 次**——凭据造出来了，没有被哈希，
所声明的用途未达成。

### 使这三条得以长期成立的条件：冻结套件零测试

`git ls-tree -r --name-only origin/master -- freeze/ | grep -v runs/` → 24 个文件，
**没有 `test_*.py`、没有 `tests/`**；
`git grep -ln "n_feasibility\|launch_gate\|build_manifest\|freeze.residuals\|from freeze\|import freeze" origin/master -- "*test*.py"` → **空**。
八个闸门／生成器模块，全仓**零**个 pytest import 其中任何一个。
套件的红只来自人手敲 `bash freeze/verify.sh` 加三个脚本内负样本（那三个是真的、也确实有效，见下）。
所以像上表 `verify() → return []` 这种变异，对**所有**现有检查都不可见。

## 我起草时写错、被对抗性复核推翻的部分（留痕）

对抗性 subagent 专门来推翻我这条，成绩如下，**我采纳它的全部**：

1. **「套件造了自检又一个都没接上」是假的**：`verify.sh` 的 15 个 stage 里
   literal 调用了 `tiers.py`、`launch_gate.py`、`build_manifest.py`、`n_feasibility.py`、`residuals.py`
   ——七个里接了五个。我原来的措辞会把一次排程遗漏说成系统性失败。
2. **`BUDGET_TABLE.json` 的 `dirty: true` 不该立案**：它已经是**登记在册的未决项**
   `RESIDUALS.json` code `A-3`，state `open`，owner RES-1，statement 逐字
   「一般形式仍成立且**没有执行形态**：哈希前必须复核工作树干净」。
   更要紧的是**套件里没有任何 `--verify` 检查 `generated_from`**
   （`build_budget_table.py:985` 显式 strip 掉它），所以接不接线都抓不到它。
   已登记 + 已声明无执行形态 = 有据的局限，不是漂移。
3. **`residuals.py` 的 `DOCS` 漏两份新文档不是「没人发现」**：
   `verify_sh_stage15.snippet.sh` 里有一整段专门点名它，连机制都说对了。
   而且**加进 `DOCS` 也没用**：`DECL` 正则要求行首 `**`，两份新文档里
   21 个和 41 个 ⛔ 全写在 blockquote 或表格单元里，`DECL` 命中 **0**；
   已被扫的 5 份里也有 3 份命中 0。（我起草时写的「28 个 ⛔」也是错的，实为 41。）
4. **`ENGINE_MANIFEST.md` 有第二张网**：它和 `build_engine_manifest.py`
   都在 `MANIFEST.json` entry 5 里带 sha256，所以 stage 12（硬失败）已经能抓手改。
   **真正一张网都没有的只有 `BUDGET_TABLE.{md,json}` 与 `POOL_DIGEST.json`。**

**并且我自己在复核这一条时错了一次，值得写下来**：我跑了一条
`any('ENGINE_MANIFEST' in p for p in paths)` 想验证对抗者，得到 `False`，
一度以为它错了。**是我错了**——`paths` 的元素是 dict 不是字符串，
子串测试对 dict 恒假。落笔前多跑一条命令看了 `paths[0]` 的实际形状才发现。
判据要按它真实的数据形状读，不能按想象的形状读。

## suggest（监控裁决，我一行代码都没动）

1. **把 `MEASUREMENTS` 放进 `floors_digest()` 的 payload**，或者把 `:63` 那句注释删掉。
   现在的状态是最坏的一种：一句让读者放心的假话。**并给它一个负样本**
   （改一个 episodes 必须变红），否则修完仍无从证明。
2. **`residuals.py:51` 要么删掉那句、要么把 `residuals.py` + `RESIDUALS.json`
   加进 `MANIFEST.json` 的 pinned paths**。后者更好，一行。
3. **`BUDGET_TABLE.{md,json}` 与 `POOL_DIGEST.json` 至少要进 `MANIFEST.json`**
   ——那是套件里唯一已经在跑的网，而这三份现在在网外。
4. **`freeze/` 需要第一个 pytest。** 优先级最高的一个用例不是覆盖率，
   是让 `verify() → return []` 变红：现在**没有任何东西调 `verify()`** 以外的东西能发现它。
5. 顺带（同族、我未验）：`stats["unowned"]` 在 `residuals.py` 里被硬编码为 `0`，
   那不是一次测量。

## 复核命令

```bash
git show origin/master:freeze/n_feasibility.py | sed -n '62,66p;119,126p'
git show origin/master:freeze/MANIFEST.json | grep -c residuals            # -> 0
git show origin/master:freeze/MANIFEST.json | grep -c POOL_DIGEST          # -> 0
git ls-tree -r --name-only origin/master -- freeze/ | grep -v runs/ | grep -c test_   # -> 0
git grep -ln "n_feasibility\|from freeze\|import freeze" origin/master -- "*test*.py" # -> empty
```

变异测试配方（不碰仓库）：
`git archive origin/master freeze arc-recon/data | tar -x -C "$TEMP/opsa-d7/repo"`，
在副本里替换一处后 `PYTHONIOENCODING=utf-8 python n_feasibility.py --verify; echo rc=$?`。
