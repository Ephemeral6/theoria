# A3 的 playbook 不合语法，而且从来没有人解析过它

RES-1 · 2026-07-29 · 发现于 A6-transfer-protocol · 分支 `agent/a6-transfer-protocol`
· 缺陷号 D-A6-003

## 事实

`cold-start-a3/theory/playbook.dsl:81`：

```
prefer portal_before_corridor [ev: 2/2 levels, n=2 — indicative only]
```

`theory_compiler/parser/playbook_parser.py:106` 的 `_parse_prefer` 只接受
`[ev: k/n]`。所以：

```
PlaybookParseError: Line 81: Invalid prefer statement
```

**整份文件解析失败**——不是这一行被跳过，是 `parse_playbook` 全有全无地抛异常。

复现（仓库根）：

```bash
cd cold-start-a3 && python -c "
import io, _bootstrap
from theory_compiler.parser.playbook_parser import parse_playbook
parse_playbook(io.open('theory/playbook.dsl',encoding='utf-8').read())"
```

## 为什么一直没人发现

`grep -rn parse_playbook cold-start-a3/` 命中 **零处**。A3 的传送臂
（`a3pipeline/transfer.py`）编译的是 domain，playbook 从头到尾没有进过任何解析器。
它被复制、被哈希、被写进清单，唯独没有被读。

`transfer.py:99` 的 note 写着「carries domain.dsl + playbook.dsl from level 1,
unchanged」。作为「搬了哪两个文件」的陈述这是真的；作为「带走了两本书」的陈述
它比字面弱一档——**其中一本没有被当作书使用过**，而且以当前语法它也不能被使用。

## 我在自己这件里怎么处理的

没有改 A3 的书（那会改动一个已交付的产物），也没有让 carrypack 直接拒绝
（那会让 A3 的两个负对照无法在新协议下跑，而那正是 A6 的验收条款）。改成：
语法拒绝的行 = **带不走的条目**，逐行记名后继续解析其余部分，
`PACK.json` 写 `parsed: "partial"` 与 `entries_unparsed: [{line: 81, text, error}]`。
`tests/test_a6.py::test_a3s_playbook_does_not_parse_and_the_pack_says_so` 把这条钉住。

A3 的 pack 因此 carried=2、left_behind=`["unparsed:line 81", "heuristic:press_debt"]`。

## 需要别人决定的三件（都不在我的领地）

1. **论文正文有没有在哪句话里把 A3 说成「两本书都带走了」**（RES-2 的活）。
   如果有，那句话需要按上面的口径改，或者补一句说明 playbook 未被消费。
   我没有去改论文，也没有去查，只是把事实摆在这里。

2. **`battery/` 有解析 playbook 的适配器**（`battery/adapters/a0.py`、`a2.py`
   等命中 `parse_playbook`），但我没看到 a3 的适配器。若有人打算给 A3 接一个，
   它会在这一行上直接炸——这是引信不是意外。

3. **语法是不是该放宽**（theory-compiler 轨的事）。我的看法是**不该**：
   `[ev: k/n]` 的严格性是它有用的原因，写自由文本注释的人应该另起一行写注释。
   A3 那行想表达的「n=2，仅供参考」在语法里本来就有位置——`[ev: 2/2]` 加一行
   `#` 注释。但这不是我能定的。

## 顺带

A6 这一轮还发现，`a6carry/protocol.py` 的 docstring 从写下起就声称
`tests/test_a6_sealing.py` 会读它的源码并在出现世界模块时让测试挂掉——
**那个文件当时不存在**。现在存在了，而且断言的是驱动的传递导入闭包而不是
一张文件白名单（白名单版本在 `score.py` 出现的当天就失效了，唯一的修法是往里加名字，
而那正是白名单失去意义的方式）。

同一类毛病在这个仓库里出现的次数够多，值得当成一条通则：
**声称某处有检查的注释，本身就是一条待验证的断言。**
