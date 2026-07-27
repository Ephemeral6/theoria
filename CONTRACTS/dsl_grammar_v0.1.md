# dsl_grammar_v0.1.md（冻结 v0.1，任何一方不得修改此文件本身）

## theory.dsl 四件套

word_table:
  board                                   # 从不共变者，沉淀为棋盘，隐式声明
  object <Name> { <field>: <Type>, ... }  # 对象类型，field 只放观测量（位置/颜色/形状等）
  <ObjName> [segment: <method> ev: <evidence-range> compress: <bytes>]  # 概念账目，可选标注

events:
  event <name>(<params>) | <name>(<params>) | ...   # 事件类型声明，如 moved(o,dir) | vanished(o)

rules:
  rule <name> [ev: <t1,t2,...>  cov: <k>/<n>]
    when <guard> then <event>
  # guard 语言（空间/对象谓词，可判定）：合取的 above(x)/free(x)/adjacent(x,y)/∈region、
  #   动作匹配 act=<ACTION>、对象属性比较。动作参数化到对象：click(Button_3)，不允许裸坐标 click(x,y)。

goal:
  goal <boolean expression over objects>

laws:
  invariant <name>  <linear-arith-expr over object counts/weights> = <const>   [status: proven|open]
  theorem <name> "<one-sentence explanation in vocabulary of word_table>"
    [depends: <rule-names>   probe: passed|pending]

## v1 表达力边界（两种语言分开管理）
- 守卫语言（rule 的 when 子句）：空间谓词 + 对象比较，证明走可判定过程（如 Lean 的 decide/omega）。
- 不变量语言（invariant/theorem 的断言体）：仅限线性算术、对象计数、mod-2 奇偶、有限权重函数（pagoda 型）。
  连通性谓词类不变量本版本不支持，遇到时记入表达力台账，不得擅自扩展本契约。
- domain/problem 分割：word_table + rules + laws 是 domain（跨关不变）；具体网格布局与初始状态是 problem（逐关实例）。

## playbook.dsl 四句型（仅此四种，不得新增）

order     <landmark-name>                         [proof: lean|none]
prune     <condition> ⇒ dead                       [proof: lean|none]
heuristic <name>(<params>)                         [admissible: lean|none]
prefer    <name>                                   [ev: <k>/<n>]   # 经验级，必须标注证据，无证明

硬性反作弊：playbook.dsl 不允许出现任何形式的字面动作序列句型
（例如 "solution: UP,UP,LEFT,..." 这类）。解是 plan 的输出，不是书的内容。
若解析器发现疑似字面解序列，必须报错拒绝，不得静默接受。
