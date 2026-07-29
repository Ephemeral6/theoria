# Reader brief

## Who you are

You are a fresh reader. You have never seen this world. You have no repository,
no source code beyond the documents printed below, no record of anyone playing
it, and no earlier conversation about it. Everything you are entitled to use is
printed in this message.

**Answer from this message alone.** Do not open, search, read or execute any
file, and do not look anything up. Nothing outside this message is part of the
question, and using it would not make your answer better -- it would make this
whole exercise worthless, which is the one outcome it cannot recover from. If
something you need is not printed here, answer `abstain`.

## What you have been given

**The manual and the playbook.** The manual describes the world; the playbook describes how to play it.

## What to do

Read the documents. Then answer every item on the question sheet below,
following the answer grammar exactly.

## How you will be marked

By a fixed rule, written down and committed before your answers existed, applied
mechanically. An answer outside the published grammar scores zero and the parse
failure is recorded; it is not read charitably.

## Your report

After the JSON object, and only after it, add one line beginning `TOOLS:` saying
which tools you used, or `TOOLS: none`. It is not marked. It is asked because the
value of this whole exercise rests on you having answered from this message
alone, and an honest report of a slip is worth far more to us than a clean-looking
result.


# The documents you were handed

=== MANUAL.dsl ===
# ----------------------------------------------------------
# A0 说明书 — sokoban-2（玩家走一格，箱子被推时滑两格）
# 由 theorize 裁决入册：引擎提案，LLM 裁决。
# 证据：341 条转移，60 个前缀重放 episode。裁决理由见 ../THEORIZE_LOG.md。
# ----------------------------------------------------------

word_table:
  board
  object Player { pos: Cell }
  object Box { pos: Cell }
  Player [segment: color-split-connected ev: t0-t340 compress: -39]
  Box [segment: color-split-connected ev: t0-t340 compress: -39]

semantics:
  # 三项都是对这个世界的断言，不是接线。措辞取自 CONTRACTS/dsl_grammar_v0.2.md
  # 的封闭值集；取哪个值由 probes/semantics_probe.py 在 47040 个可表示
  # (状态,动作) 对上反证另一个值定出，逐项裁决理由见 ../THEORIZE_LOG.md T-11。
  # 三个值恰好与 A0、A2 所报的相同——这是量出来的，不是抄来的（v0.2 §迁移
  # 明文禁止照抄），复算命令见 runs/20260728T040057Z-c2/RUN_STATE.md。

  # 反证：把 Box 换成 reset，38712/39960 个可观测对立刻错——只要玩家单走一步，
  # 没有任何开火规则提到箱子，reset 就把箱子传送回开局格。世界不这样。
  frame     persist

  # 反证：五条规则的守卫两两不交，全扫描 47040 对里同时开火的规则数上限为 1，
  # 认领同一对象的规则数上限也为 1（含 on_wall 层，故此项是无条件解除）。
  # 关键一步是把 slid 读宽：gen_exec 里它同时写 Box 和 Player，v0.2 §Discharging
  # conflict 的义务按对象算，读窄会低估要证的东西。另有独立的句法证明（route 1）
  # 在 THEORIZE_LOG T-11c：free(c) 蕴含 c≠Box.pos，这一条就切开了 walk 与 push2。
  conflict  exclusive

  # 反证：multi_frame 要把规则在中间态上重开火。A0 每条规则都守在
  # act=move(Player,dir) 上，动作不会自己熄灭，于是 walk 反复开火，
  # 一次 move 让玩家滑到撞墙为止——22582/39960 个可观测对因此错。
  # 箱子滑两格不是级联：那两格是**一条规则的一个效果**，整体施加；
  # multi_frame 说的是「规则集被重跑」，两者不是一回事。
  cascade   single_frame

events:
  # stayed(o) 是被 certify 逼出来的：blocked_* 原本写成 then moved(Player, dir)，
  # 生成的执行态照此把玩家推出棋盘。事件语汇缺一个「什么都没发生」。
  event moved(o, dir) | slid(o, dir) | stayed(o)

rules:
  rule walk [ev: t0,t1,t2 cov: 262/262]
    when act=move(Player, dir) and free(ahead(Player, dir)) then moved(Player, dir)

  # box_ahead_free was forced by the held-out test, not by replay: the crossed
  # cell always has odd parity and every wall in `match` has even parity, so no
  # evidence from that level alone could pin it down (THEORIZE_LOG T-9).
  rule push2 [ev: t3,t9,t27 cov: 267/267]
    when act=move(Player, dir) and Box.pos = ahead(Player, dir) and free(ahead(Box, dir)) and free(beyond(Box, dir)) then slid(Box, dir)

  rule blocked_wall [ev: t5,t11 cov: 16/16]
    when act=move(Player, dir) and not free(ahead(Player, dir)) and not Box.pos = ahead(Player, dir) then stayed(Player)

  # two rules, because guards are conjunctions and "the box cannot move" is a
  # disjunction over which of the two cells is obstructed
  rule blocked_box_crossing [ev: t7,t19 cov: 24/24]
    when act=move(Player, dir) and Box.pos = ahead(Player, dir) and not free(ahead(Box, dir)) then stayed(Player)

  rule blocked_box_landing [ev: t31,t44 cov: 28/28]
    when act=move(Player, dir) and Box.pos = ahead(Player, dir) and free(ahead(Box, dir)) and not free(beyond(Box, dir)) then stayed(Player)

goal:
  goal Box.pos = target

laws:
  # zero_space 返回的零空间维数为 2：两个坐标的奇偶各自守恒，比我最初提的
  # (row+col) 更强。入册取强的一对，和式作为推论保留（见 THEORIZE_LOG T-6）。
  invariant box_row_parity (Box.pos.row) mod 2 = 1 [status: proven]
  invariant box_col_parity (Box.pos.col) mod 2 = 1 [status: proven]
  invariant box_parity (Box.pos.row + Box.pos.col) mod 2 = 0 [status: proven]

  theorem unsolvable_mismatch "箱子每次滑动两格，(row+col) 的奇偶不变；开局箱子在偶格，目标格是奇格，所以永远到不了"
    [depends: push2  probe: passed]

=== MANUAL.md ===
# The manual for this world

A deterministic rendering of the manual's source file (`MANUAL.dsl` in this bundle). It adds nothing; where it says more than the source, it is reading the source's compiled form and says so.

## What there is

- A **board**: a rectangular grid of cells that does not change while the game is played.
- A **Player**, which has one property: pos: Cell.
- A **Box**, which has one property: pos: Cell.

## What can happen

Three kinds of change, and no others: something **moved** one cell, something **slid** (further than one cell), or something **stayed** where it was.

## How things change

**walk**

When the Player is told to move in direction d, and
  - the cell one step from the Player in direction d is free,

then the Player moves one cell in direction d. Nothing else changes.

**push2**

When the Player is told to move in direction d, and
  - the Box is standing on the cell one step from the Player in direction d,
  - the cell one step from the Box in direction d -- the cell the Box would cross -- is free,
  - the cell two steps from the Box in direction d -- the cell the Box would land on -- is free,

then the Box slides two cells in direction d, and the Player advances one cell -- onto the cell the Box has just left.

**blocked_wall**

When the Player is told to move in direction d, and
  - the cell one step from the Player in direction d is NOT free,
  - the Box is NOT standing on the cell one step from the Player in direction d,

then nothing moves. The situation after the action is identical to the situation before it.

**blocked_box_crossing**

When the Player is told to move in direction d, and
  - the Box is standing on the cell one step from the Player in direction d,
  - the cell one step from the Box in direction d -- the cell the Box would cross -- is NOT free,

then nothing moves. The situation after the action is identical to the situation before it.

**blocked_box_landing**

When the Player is told to move in direction d, and
  - the Box is standing on the cell one step from the Player in direction d,
  - the cell one step from the Box in direction d -- the cell the Box would cross -- is free,
  - the cell two steps from the Box in direction d -- the cell the Box would land on -- is NOT free,

then nothing moves. The situation after the action is identical to the situation before it.

Exactly one of these rules applies to any situation and any action, so there is never a question of which one to use.

## When the game is won

- The game is won when the Box is standing on the target cell.

## What is always true

- **box_row_parity** (proven): `(Box.pos.row) mod 2 = 1` holds before the first action and after every action, whatever actions are taken.
- **box_col_parity** (proven): `(Box.pos.col) mod 2 = 1` holds before the first action and after every action, whatever actions are taken.
- **box_parity** (proven): `(Box.pos.row + Box.pos.col) mod 2 = 0` holds before the first action and after every action, whatever actions are taken.
- **unsolvable_mismatch**: 箱子每次滑动两格，(row+col) 的奇偶不变；开局箱子在偶格，目标格是奇格，所以永远到不了

## The words the rules are built from

These are the primitives the rules above use. They are not restated in the
manual's source; they are read off the manual's compiled executable form, which
is one of the forms the manual compiles to.

- A **cell** is written `(row, col)`. Row 0 is the top row and column 0 the
  left column.
- A **direction** `d` is one of UP, DOWN, LEFT, RIGHT. UP subtracts one from
  the row, DOWN adds one to the row, LEFT subtracts one from the column,
  RIGHT adds one to the column.
- **one step from X in direction d** is X's cell moved once by d;
  **two steps from X in direction d** is X's cell moved twice by d.
- A cell is **free** when all three of these hold: it is on the board, it is
  not a wall, and the Box is not standing on it. The Player never makes a cell
  un-free: the Player does not block anything, including itself.
- An action is always a move by the Player in one direction. There is no other
  kind of action.

=== PLAYBOOK.dsl ===
# ============================================================================
# A0 玩法书 — the strategic tier of the layered handover
#
# Four sentence forms and no others (constraint 10, CONTRACTS/dsl_grammar_v0.1):
# ordering, pruning, heuristics, preferences. There is deliberately no way to
# write a solution down here. A playbook that stored answers would turn the
# handover into passing notes rather than passing understanding.
#
# Every entry cites the manual clause it rests on, so that changing that clause
# invalidates the entry.
# ============================================================================

# Check the conservation law before searching at all. The law decides some
# boards outright, and it decides them in one arithmetic step; a search that
# runs first is a search that may run forever on a board that was already
# settled. Rests on: invariant box_row_parity, invariant box_col_parity.
order parity_check_before_search [proof: lean]

# The board is decided, and impossible, when the Box's row parity or its column
# parity differs from the target's. Nothing the Player does can change either.
# Rests on: invariant box_row_parity, invariant box_col_parity, rule push2.
prune parity(Box.pos) != parity(target) => dead [proof: lean]

# A Box that cannot be pushed in any direction will never move again: every rule
# that moves the Box needs the Player standing behind it and both cells ahead of
# it free. Rests on: rule push2, rule blocked_box_crossing,
# rule blocked_box_landing.
prune no_direction_admits_a_push(Box.pos) => dead [proof: none]

# A lower bound on the number of pushes still needed: each push moves the Box
# two cells along one axis, so at best it takes half the remaining row distance
# plus half the remaining column distance. Rests on: rule push2.
heuristic pushes_remaining(Box.pos, target) [admissible: none]

# The empirical tier is EMPTY, and that is a finding rather than an omission.
# A `prefer` entry must carry a win rate or a node count (constraint 5), and no
# such measurement exists for this world yet. Writing one down without it would
# be inventing evidence. The tier stays open.

=== PLAYBOOK.md ===
# The playbook for this world

The manual says what the world does. This says how to win in it, and — more
usefully — how to avoid work.

Nothing here is a solution to any particular board. The playbook deliberately
contains no board, no position and no sequence of actions: those are outputs of
planning, not contents of a book.

## What the conservation law is for

The manual records that the Box's row parity and its column parity never change.
That is a fact about the world; here is what to do with it.

**Decide before you search.** Compare the Box's row parity with the target's row
parity, and the Box's column parity with the target's column parity. If either
disagrees, the board is impossible — not "no plan was found", but *there is no
plan*, and the reason fits on one line. Searching such a board is wasted effort
in the best case and unbounded effort in the worst.

**Shrink the search when you do search.** Even when the parities agree, the law
says the Box can only ever stand on cells matching its own row parity and its
own column parity. Three quarters of the board is unreachable for the Box before
a single action is considered. Any search that expands nodes placing the Box on
those cells is expanding nodes that cannot exist.

**The certificate is the explanation.** When a board is refused, the refusal is
checkable by anyone with the manual: this parity, that parity, they differ, the
law forbids the crossing. That is a different kind of answer from "my search
finished and found nothing", and it is the answer this framework is for.

## Deadlocks

A deadlock is a situation that is not yet lost by the goal condition but from
which the goal can no longer be reached. They are the daily business of this
world, far more common than a whole board being impossible.

**The Box is frozen.** The Box moves only when the Player stands directly behind
it *and* the cell it would cross *and* the cell it would land on are both free.
If, in every one of the four directions, at least one of those three conditions
can never be met, the Box will never move again. If it is not already on the
target, the board is lost.

**The two-cell slide makes edges wider than they look.** Because the Box travels
two cells, it cannot be pushed toward a wall that sits one *or* two cells away
in that direction — one cell away blocks the crossing, two cells away blocks the
landing. A Box that would be pushable in an ordinary one-cell world can be
immovable here. Reason about the pair of cells, never about the next cell alone.

**The Player is not a wall but the Box is.** The Box blocks the Player's walking;
the Player blocks nothing. So the Player can always be routed anywhere the walls
allow, provided the route does not pass through the Box — which is exactly the
constraint that makes some pushes unreachable even when the Box could accept
them.

## Choosing an action

**Count pushes, then count walking.** Each push closes two cells of the gap
between the Box and the target along one axis. So the number of pushes still
needed is at least half the remaining row distance plus half the remaining
column distance. This is a lower bound and can be used to order candidates; it
is not proven admissible for the total number of actions, because the walking
between pushes is not counted.

**Plan the pushes, then plan the walking.** The Box's route is the hard part and
the Player's route is almost always the easy part: the Player is unobstructed
except by walls and by the Box itself. Work out which sequence of pushes brings
the Box to the target — respecting both parities and the deadlocks above — and
only then work out how to get the Player behind the Box each time.

**Getting behind the Box costs actions, and turning around costs the most.**
Pushing the Box in a direction requires the Player to be on the cell immediately
opposite that direction. Continuing a push in the direction already being pushed
is free — the Player is already in place, having followed the Box. Changing the
push direction means walking around the Box, and the Box is in the way while you
do it. A route that pushes along one axis and then the other is usually cheaper
than one that alternates.

**Only pushes are irreversible.** Walking can always be undone. A push may not
be: whether the Box can be pushed back depends on whether the Player can get to
the far side of it and on what is behind it there. Treat every push as a
commitment and check the deadlock conditions before making it, not after.

## Where this book came from, and what it does not have

Every claim above is derived from clauses of the manual, and the derivation is
short in each case. That is the pre-registered prediction of the layered
handover: a reader given only the manual should be able to reconstruct this
book, and should end up at the same place after paying the search cost this book
saves. If that turns out to be false, this book contains something the manual
does not, and finding out what would be the interesting result.

There is no empirical tier — no "this move ordering wins 7 times in 10" — because
no such measurement exists for this world. An entry of that kind without the
count behind it would be invented evidence.


# The question sheet

You are a fresh reader of one framework's deliverable. You have been given a
bundle of documents and this sheet, and nothing else: no repository, no source
code beyond what the bundle contains, no record of anyone playing this world, no
earlier conversation. Everything you are entitled to use is in the bundle or in
the item itself.

The world is a grid world. The bundle says how it behaves. Each item that needs
one carries the geometry of a board and, where relevant, where the Player and
the Box are standing. Take the situation from the item, never from an earlier
item: every item stands alone.

P=Player  B=Box  #=wall  T=target cell  .=empty. Row 0 is the top row, column 0 the left column. If two of these share a cell the earlier letter is drawn, so the target is still the cell named in `target` even when it is not visible.

Four kinds of question appear, distinguished by each item's `kind` field.

  kind = "step_semantics"
      One action is taken from the given situation. Say what the situation is
      afterwards and which clause of the manual accounts for it.
      Answer grammar, exactly:
          player=(row,col); box=(row,col); rule=<name>
      All three fields, in any order, separated by semicolons. `<name>` is one
      of: walk | push2 | blocked_wall | blocked_box_crossing | blocked_box_landing
      All three fields must be right; two out of three scores nothing.

  kind = "name_class"
      A name is pointed at. Say whether it is something each individual board
      supplies (`level_data`) or something the world fixes once for every board
      (`world_law`). Whether the name appears in the manual is not the question.
      Answer grammar, exactly one word: level_data | world_law

  kind = "optimal_action"
      Answer grammar, exactly:
          action=<A>; plan_len=<n>
      `<A>` names an action that begins a shortest sequence of actions ending
      with the Box on the target cell, and `<n>` is how many actions that
      shortest sequence contains. Where several actions begin some shortest
      sequence, any one of them is accepted; you do not have to find them all.
      `<A>` is one of: UP | DOWN | LEFT | RIGHT | none
      If the Box can never reach the target from the situation given, answer
      `action=none; plan_len=none`. The two halves are marked separately and are
      worth half the item each.

  kind = "rule_justification"
      A claim about this world is stated, together with a list of the manual's
      clauses. Name every listed clause the claim's truth depends on, and no
      others.
      Answer grammar, exactly:
          rests_on=<clause>+<clause>+...
      Depends on means: the claim's truth uses **what that clause does** -- the
      `then` half of it, the change it makes. A clause whose effect changes
      nothing the claim is about does not belong in your answer, even if a
      differently written clause in its place would have broken the claim. Order
      does not matter and a repeated name is counted once.
      Every clause you name that belongs earns; every clause you name that does
      not belong costs the same amount. Naming all of them is not a strategy.
      The full set is worth the whole item.

  kind = "counterexample"
      A sentence from the manual is quoted and you are asked for a situation at
      which it is false.
      Answer grammar, exactly:
          level=<board id>; player=(row,col); box=(row,col)
      The board id must be one of the boards the item lists. The situation must
      be legal on that board. It is marked by recomputing the quoted sentence at
      the situation you name.

Any item may instead be answered `abstain`. An abstention scores nothing and is
recorded as an abstention, not as a wrong answer; a guess that turns out wrong is
recorded as a wrong answer. An answer that is not a sentence of the grammar above
scores nothing and the parse failure is recorded. `abstain` and `none` are not
the same word: `none` is a claim about the world, `abstain` is a claim about you.

Submit a single JSON object whose keys are exactly the `item_id` values on this
sheet -- every one of them, none omitted, none invented -- and whose values are
answer strings. Nothing else: no commentary, no reasoning, no extra keys.

```json
{
  "items": [
    {
      "action": "RIGHT",
      "board": [
        ".PB....",
        ".......",
        ".....#.",
        "#....T.",
        "...##..",
        "...#...",
        ".#....."
      ],
      "item_id": "v11-step-01",
      "kind": "step_semantics",
      "level": {
        "height": 7,
        "level_id": "kiln",
        "target": [
          3,
          5
        ],
        "walls": [
          [
            2,
            5
          ],
          [
            3,
            0
          ],
          [
            4,
            3
          ],
          [
            4,
            4
          ],
          [
            5,
            3
          ],
          [
            6,
            1
          ]
        ],
        "width": 7
      },
      "points": 2.0,
      "prompt": "The Player takes the action RIGHT. Give the situation after the action and the clause that accounts for it.",
      "state": {
        "box": [
          0,
          2
        ],
        "player": [
          0,
          1
        ]
      },
      "tags": [
        "step_semantics",
        "level:kiln"
      ]
    },
    {
      "action": "LEFT",
      "board": [
        ".BP.....",
        ".##..#..",
        "....#..#",
        ".......#",
        "..T.....",
        "........",
        "........",
        "........"
      ],
      "item_id": "v11-step-02",
      "kind": "step_semantics",
      "level": {
        "height": 8,
        "level_id": "warren",
        "target": [
          4,
          2
        ],
        "walls": [
          [
            1,
            1
          ],
          [
            1,
            2
          ],
          [
            1,
            5
          ],
          [
            2,
            4
          ],
          [
            2,
            7
          ],
          [
            3,
            7
          ]
        ],
        "width": 8
      },
      "points": 2.0,
      "prompt": "The Player takes the action LEFT. Give the situation after the action and the clause that accounts for it.",
      "state": {
        "box": [
          0,
          1
        ],
        "player": [
          0,
          2
        ]
      },
      "tags": [
        "step_semantics",
        "level:warren"
      ]
    },
    {
      "action": "DOWN",
      "board": [
        "........",
        ".......#",
        ".#.....#",
        ".P......",
        "..#.#...",
        ".....B..",
        "..##.#..",
        ".....T.."
      ],
      "item_id": "v11-step-03",
      "kind": "step_semantics",
      "level": {
        "height": 8,
        "level_id": "flume",
        "target": [
          7,
          5
        ],
        "walls": [
          [
            1,
            7
          ],
          [
            2,
            1
          ],
          [
            2,
            7
          ],
          [
            4,
            2
          ],
          [
            4,
            4
          ],
          [
            6,
            2
          ],
          [
            6,
            3
          ],
          [
            6,
            5
          ]
        ],
        "width": 8
      },
      "points": 2.0,
      "prompt": "The Player takes the action DOWN. Give the situation after the action and the clause that accounts for it.",
      "state": {
        "box": [
          5,
          5
        ],
        "player": [
          3,
          1
        ]
      },
      "tags": [
        "step_semantics",
        "level:flume"
      ]
    },
    {
      "action": "RIGHT",
      "board": [
        "P.......",
        ".##..#..",
        "....#..#",
        ".......#",
        "..T.....",
        "...B....",
        "........",
        "........"
      ],
      "item_id": "v11-step-04",
      "kind": "step_semantics",
      "level": {
        "height": 8,
        "level_id": "warren",
        "target": [
          4,
          2
        ],
        "walls": [
          [
            1,
            1
          ],
          [
            1,
            2
          ],
          [
            1,
            5
          ],
          [
            2,
            4
          ],
          [
            2,
            7
          ],
          [
            3,
            7
          ]
        ],
        "width": 8
      },
      "points": 2.0,
      "prompt": "The Player takes the action RIGHT. Give the situation after the action and the clause that accounts for it.",
      "state": {
        "box": [
          5,
          3
        ],
        "player": [
          0,
          0
        ]
      },
      "tags": [
        "step_semantics",
        "level:warren"
      ]
    },
    {
      "action": "LEFT",
      "board": [
        ".......",
        ".......",
        ".....#.",
        "#P...T.",
        "...##..",
        "...#.B.",
        ".#....."
      ],
      "item_id": "v11-step-05",
      "kind": "step_semantics",
      "level": {
        "height": 7,
        "level_id": "kiln",
        "target": [
          3,
          5
        ],
        "walls": [
          [
            2,
            5
          ],
          [
            3,
            0
          ],
          [
            4,
            3
          ],
          [
            4,
            4
          ],
          [
            5,
            3
          ],
          [
            6,
            1
          ]
        ],
        "width": 7
      },
      "points": 2.0,
      "prompt": "The Player takes the action LEFT. Give the situation after the action and the clause that accounts for it.",
      "state": {
        "box": [
          5,
          5
        ],
        "player": [
          3,
          1
        ]
      },
      "tags": [
        "step_semantics",
        "level:kiln"
      ]
    },
    {
      "action": "RIGHT",
      "board": [
        "..#.PB",
        "......",
        ".T.##.",
        "...##.",
        ".....#",
        "....#."
      ],
      "item_id": "v11-step-06",
      "kind": "step_semantics",
      "level": {
        "height": 6,
        "level_id": "cairn",
        "target": [
          2,
          1
        ],
        "walls": [
          [
            0,
            2
          ],
          [
            2,
            3
          ],
          [
            2,
            4
          ],
          [
            3,
            3
          ],
          [
            3,
            4
          ],
          [
            4,
            5
          ],
          [
            5,
            4
          ]
        ],
        "width": 6
      },
      "points": 2.0,
      "prompt": "The Player takes the action RIGHT. Give the situation after the action and the clause that accounts for it.",
      "state": {
        "box": [
          0,
          5
        ],
        "player": [
          0,
          4
        ]
      },
      "tags": [
        "step_semantics",
        "level:cairn"
      ]
    },
    {
      "action": "DOWN",
      "board": [
        "P.......",
        "B##..#..",
        "....#..#",
        ".......#",
        "..T.....",
        "........",
        "........",
        "........"
      ],
      "item_id": "v11-step-07",
      "kind": "step_semantics",
      "level": {
        "height": 8,
        "level_id": "warren",
        "target": [
          4,
          2
        ],
        "walls": [
          [
            1,
            1
          ],
          [
            1,
            2
          ],
          [
            1,
            5
          ],
          [
            2,
            4
          ],
          [
            2,
            7
          ],
          [
            3,
            7
          ]
        ],
        "width": 8
      },
      "points": 2.0,
      "prompt": "The Player takes the action DOWN. Give the situation after the action and the clause that accounts for it.",
      "state": {
        "box": [
          1,
          0
        ],
        "player": [
          0,
          0
        ]
      },
      "tags": [
        "step_semantics",
        "level:warren"
      ]
    },
    {
      "definition": "the cell the Box occupies before any action is taken",
      "item_id": "v11-name-01",
      "kind": "name_class",
      "name": "start_box",
      "points": 1.0,
      "prompt": "Is `start_box` supplied by each individual board, or fixed by the world for every board?",
      "tags": [
        "level_data_vs_world_law"
      ]
    },
    {
      "definition": "a name introduced in the manual's `events:` section",
      "item_id": "v11-name-02",
      "kind": "name_class",
      "name": "slid",
      "points": 1.0,
      "prompt": "Is `slid` supplied by each individual board, or fixed by the world for every board?",
      "tags": [
        "level_data_vs_world_law"
      ]
    },
    {
      "definition": "the name written in the manual's `goal:` clause",
      "item_id": "v11-name-03",
      "kind": "name_class",
      "name": "target",
      "points": 1.0,
      "prompt": "Is `target` supplied by each individual board, or fixed by the world for every board?",
      "tags": [
        "level_data_vs_world_law"
      ]
    },
    {
      "definition": "the number of rows a board has",
      "item_id": "v11-name-04",
      "kind": "name_class",
      "name": "height",
      "points": 1.0,
      "prompt": "Is `height` supplied by each individual board, or fixed by the world for every board?",
      "tags": [
        "level_data_vs_world_law"
      ]
    },
    {
      "definition": "a name used inside rule guards, applied to an object and a direction",
      "item_id": "v11-name-05",
      "kind": "name_class",
      "name": "beyond",
      "points": 1.0,
      "prompt": "Is `beyond` supplied by each individual board, or fixed by the world for every board?",
      "tags": [
        "level_data_vs_world_law"
      ]
    },
    {
      "definition": "the cells of one board that are not on the board's floor",
      "item_id": "v11-name-06",
      "kind": "name_class",
      "name": "walls",
      "points": 1.0,
      "prompt": "Is `walls` supplied by each individual board, or fixed by the world for every board?",
      "tags": [
        "level_data_vs_world_law"
      ]
    },
    {
      "definition": "a name introduced in the manual's `laws:` section",
      "item_id": "v11-name-07",
      "kind": "name_class",
      "name": "box_col_parity",
      "points": 1.0,
      "prompt": "Is `box_col_parity` supplied by each individual board, or fixed by the world for every board?",
      "tags": [
        "level_data_vs_world_law"
      ]
    },
    {
      "definition": "a name introduced in the manual's `rules:` section",
      "item_id": "v11-name-08",
      "kind": "name_class",
      "name": "push2",
      "points": 1.0,
      "prompt": "Is `push2` supplied by each individual board, or fixed by the world for every board?",
      "tags": [
        "level_data_vs_world_law"
      ]
    },
    {
      "definition": "a name used inside rule guards, applied to a cell",
      "item_id": "v11-name-09",
      "kind": "name_class",
      "name": "free",
      "points": 1.0,
      "prompt": "Is `free` supplied by each individual board, or fixed by the world for every board?",
      "tags": [
        "level_data_vs_world_law"
      ]
    },
    {
      "definition": "a name introduced in the manual's `rules:` section",
      "item_id": "v11-name-10",
      "kind": "name_class",
      "name": "blocked_box_landing",
      "points": 1.0,
      "prompt": "Is `blocked_box_landing` supplied by each individual board, or fixed by the world for every board?",
      "tags": [
        "level_data_vs_world_law"
      ]
    },
    {
      "board": [
        ".....B.",
        "..#....",
        "P..#...",
        ".#.....",
        ".#..T..",
        ".....#."
      ],
      "item_id": "v11-opt-01",
      "kind": "optimal_action",
      "level": {
        "height": 6,
        "level_id": "stile",
        "target": [
          4,
          4
        ],
        "walls": [
          [
            1,
            2
          ],
          [
            2,
            3
          ],
          [
            3,
            1
          ],
          [
            4,
            1
          ],
          [
            5,
            5
          ]
        ],
        "width": 7
      },
      "points": 2.0,
      "prompt": "Name an action that begins a shortest sequence of actions ending with the Box on the target cell, and the length of that shortest sequence. If there is no such sequence, answer `action=none; plan_len=none`.",
      "state": {
        "box": [
          0,
          5
        ],
        "player": [
          2,
          0
        ]
      },
      "tags": [
        "optimal_action",
        "level:stile",
        "dead"
      ]
    },
    {
      "board": [
        "P.......",
        ".......#",
        ".#.....#",
        "...B....",
        "..#.#...",
        "........",
        "..##.#..",
        ".....T.."
      ],
      "item_id": "v11-opt-02",
      "kind": "optimal_action",
      "level": {
        "height": 8,
        "level_id": "flume",
        "target": [
          7,
          5
        ],
        "walls": [
          [
            1,
            7
          ],
          [
            2,
            1
          ],
          [
            2,
            7
          ],
          [
            4,
            2
          ],
          [
            4,
            4
          ],
          [
            6,
            2
          ],
          [
            6,
            3
          ],
          [
            6,
            5
          ]
        ],
        "width": 8
      },
      "points": 2.0,
      "prompt": "Name an action that begins a shortest sequence of actions ending with the Box on the target cell, and the length of that shortest sequence. If there is no such sequence, answer `action=none; plan_len=none`.",
      "state": {
        "box": [
          3,
          3
        ],
        "player": [
          0,
          0
        ]
      },
      "tags": [
        "optimal_action",
        "level:flume",
        "solvable"
      ]
    },
    {
      "board": [
        "........",
        ".##..#..",
        "....#.B#",
        ".......#",
        "..T.....",
        "........",
        ".......P",
        "........"
      ],
      "item_id": "v11-opt-03",
      "kind": "optimal_action",
      "level": {
        "height": 8,
        "level_id": "warren",
        "target": [
          4,
          2
        ],
        "walls": [
          [
            1,
            1
          ],
          [
            1,
            2
          ],
          [
            1,
            5
          ],
          [
            2,
            4
          ],
          [
            2,
            7
          ],
          [
            3,
            7
          ]
        ],
        "width": 8
      },
      "points": 2.0,
      "prompt": "Name an action that begins a shortest sequence of actions ending with the Box on the target cell, and the length of that shortest sequence. If there is no such sequence, answer `action=none; plan_len=none`.",
      "state": {
        "box": [
          2,
          6
        ],
        "player": [
          6,
          7
        ]
      },
      "tags": [
        "optimal_action",
        "level:warren",
        "solvable"
      ]
    },
    {
      "board": [
        "..#..B",
        ".....P",
        ".T.##.",
        "...##.",
        ".....#",
        "....#."
      ],
      "item_id": "v11-opt-04",
      "kind": "optimal_action",
      "level": {
        "height": 6,
        "level_id": "cairn",
        "target": [
          2,
          1
        ],
        "walls": [
          [
            0,
            2
          ],
          [
            2,
            3
          ],
          [
            2,
            4
          ],
          [
            3,
            3
          ],
          [
            3,
            4
          ],
          [
            4,
            5
          ],
          [
            5,
            4
          ]
        ],
        "width": 6
      },
      "points": 2.0,
      "prompt": "Name an action that begins a shortest sequence of actions ending with the Box on the target cell, and the length of that shortest sequence. If there is no such sequence, answer `action=none; plan_len=none`.",
      "state": {
        "box": [
          0,
          5
        ],
        "player": [
          1,
          5
        ]
      },
      "tags": [
        "optimal_action",
        "level:cairn",
        "dead"
      ]
    },
    {
      "board": [
        ".......",
        "...B...",
        ".....#.",
        "#....T.",
        "...##..",
        "...#...",
        ".#....P"
      ],
      "item_id": "v11-opt-05",
      "kind": "optimal_action",
      "level": {
        "height": 7,
        "level_id": "kiln",
        "target": [
          3,
          5
        ],
        "walls": [
          [
            2,
            5
          ],
          [
            3,
            0
          ],
          [
            4,
            3
          ],
          [
            4,
            4
          ],
          [
            5,
            3
          ],
          [
            6,
            1
          ]
        ],
        "width": 7
      },
      "points": 2.0,
      "prompt": "Name an action that begins a shortest sequence of actions ending with the Box on the target cell, and the length of that shortest sequence. If there is no such sequence, answer `action=none; plan_len=none`.",
      "state": {
        "box": [
          1,
          3
        ],
        "player": [
          6,
          6
        ]
      },
      "tags": [
        "optimal_action",
        "level:kiln",
        "solvable"
      ]
    },
    {
      "board": [
        "P.......",
        ".##..#..",
        "....#..#",
        ".......#",
        "..T...B.",
        "........",
        "........",
        "........"
      ],
      "item_id": "v11-opt-06",
      "kind": "optimal_action",
      "level": {
        "height": 8,
        "level_id": "warren",
        "target": [
          4,
          2
        ],
        "walls": [
          [
            1,
            1
          ],
          [
            1,
            2
          ],
          [
            1,
            5
          ],
          [
            2,
            4
          ],
          [
            2,
            7
          ],
          [
            3,
            7
          ]
        ],
        "width": 8
      },
      "points": 2.0,
      "prompt": "Name an action that begins a shortest sequence of actions ending with the Box on the target cell, and the length of that shortest sequence. If there is no such sequence, answer `action=none; plan_len=none`.",
      "state": {
        "box": [
          4,
          6
        ],
        "player": [
          0,
          0
        ]
      },
      "tags": [
        "optimal_action",
        "level:warren",
        "solvable"
      ]
    },
    {
      "board": [
        "........",
        ".......#",
        ".#.....#",
        ".P......",
        "..#.#...",
        ".....B..",
        "..##.#..",
        ".....T.."
      ],
      "item_id": "v11-opt-07",
      "kind": "optimal_action",
      "level": {
        "height": 8,
        "level_id": "flume",
        "target": [
          7,
          5
        ],
        "walls": [
          [
            1,
            7
          ],
          [
            2,
            1
          ],
          [
            2,
            7
          ],
          [
            4,
            2
          ],
          [
            4,
            4
          ],
          [
            6,
            2
          ],
          [
            6,
            3
          ],
          [
            6,
            5
          ]
        ],
        "width": 8
      },
      "points": 2.0,
      "prompt": "Name an action that begins a shortest sequence of actions ending with the Box on the target cell, and the length of that shortest sequence. If there is no such sequence, answer `action=none; plan_len=none`.",
      "state": {
        "box": [
          5,
          5
        ],
        "player": [
          3,
          1
        ]
      },
      "tags": [
        "optimal_action",
        "level:flume",
        "solvable"
      ]
    },
    {
      "board": [
        ".....P.",
        ".......",
        ".....#.",
        "#B...T.",
        "...##..",
        "...#...",
        ".#....."
      ],
      "item_id": "v11-opt-08",
      "kind": "optimal_action",
      "level": {
        "height": 7,
        "level_id": "kiln",
        "target": [
          3,
          5
        ],
        "walls": [
          [
            2,
            5
          ],
          [
            3,
            0
          ],
          [
            4,
            3
          ],
          [
            4,
            4
          ],
          [
            5,
            3
          ],
          [
            6,
            1
          ]
        ],
        "width": 7
      },
      "points": 2.0,
      "prompt": "Name an action that begins a shortest sequence of actions ending with the Box on the target cell, and the length of that shortest sequence. If there is no such sequence, answer `action=none; plan_len=none`.",
      "state": {
        "box": [
          3,
          1
        ],
        "player": [
          0,
          5
        ]
      },
      "tags": [
        "optimal_action",
        "level:kiln",
        "solvable"
      ]
    },
    {
      "candidates": [
        "walk",
        "push2",
        "blocked_wall",
        "blocked_box_crossing",
        "blocked_box_landing",
        "goal_box_on_target"
      ],
      "claim": "For every situation and every action there is at least one clause of the manual that says what happens.",
      "item_id": "v11-why-01",
      "kind": "rule_justification",
      "points": 3.0,
      "prompt": "Which of the listed clauses does this claim's truth depend on? Name every one that does and no others.",
      "tags": [
        "rule_justification",
        "why:total"
      ]
    },
    {
      "candidates": [
        "walk",
        "push2",
        "blocked_wall",
        "blocked_box_crossing",
        "blocked_box_landing",
        "goal_box_on_target"
      ],
      "claim": "On a board whose target cell has a different column parity from the cell the Box starts on, the game can never be won.",
      "item_id": "v11-why-02",
      "kind": "rule_justification",
      "points": 3.0,
      "prompt": "Which of the listed clauses does this claim's truth depend on? Name every one that does and no others.",
      "tags": [
        "rule_justification",
        "why:mismatch"
      ]
    },
    {
      "candidates": [
        "walk",
        "push2",
        "blocked_wall",
        "blocked_box_crossing",
        "blocked_box_landing"
      ],
      "claim": "A Player standing beside a wall, with no Box between, told to move into that wall, is in exactly the situation it was in before.",
      "item_id": "v11-why-03",
      "kind": "rule_justification",
      "points": 3.0,
      "prompt": "Which of the listed clauses does this claim's truth depend on? Name every one that does and no others.",
      "tags": [
        "rule_justification",
        "why:bump"
      ]
    },
    {
      "candidates": [
        "walk",
        "push2",
        "blocked_wall",
        "blocked_box_crossing",
        "blocked_box_landing"
      ],
      "claim": "Whatever the Player is told to do, the column the Box stands in keeps the parity it had before the action (odd stays odd, even stays even).",
      "item_id": "v11-why-04",
      "kind": "rule_justification",
      "points": 3.0,
      "prompt": "Which of the listed clauses does this claim's truth depend on? Name every one that does and no others.",
      "tags": [
        "rule_justification",
        "why:colparity"
      ]
    },
    {
      "candidates": [
        "walk",
        "push2",
        "blocked_wall",
        "blocked_box_crossing",
        "blocked_box_landing"
      ],
      "claim": "If the Box stands where no direction admits a push -- for every direction either the cell the Box would cross or the cell it would land on is not free, or the cell the Player would have to stand on is off the board or a wall -- then the Box will never move again, whatever the Player does.",
      "item_id": "v11-why-05",
      "kind": "rule_justification",
      "points": 3.0,
      "prompt": "Which of the listed clauses does this claim's truth depend on? Name every one that does and no others.",
      "tags": [
        "rule_justification",
        "why:frozen"
      ]
    },
    {
      "candidate_boards": {
        "cairn": {
          "board": [
            "..#..B",
            ".....P",
            ".T.##.",
            "...##.",
            ".....#",
            "....#."
          ],
          "height": 6,
          "walls": [
            [
              0,
              2
            ],
            [
              2,
              3
            ],
            [
              2,
              4
            ],
            [
              3,
              3
            ],
            [
              3,
              4
            ],
            [
              4,
              5
            ],
            [
              5,
              4
            ]
          ],
          "width": 6
        },
        "flume": {
          "board": [
            "........",
            ".......#",
            ".#.....#",
            ".P......",
            "..#.#...",
            ".....B..",
            "..##.#..",
            ".....T.."
          ],
          "height": 8,
          "walls": [
            [
              1,
              7
            ],
            [
              2,
              1
            ],
            [
              2,
              7
            ],
            [
              4,
              2
            ],
            [
              4,
              4
            ],
            [
              6,
              2
            ],
            [
              6,
              3
            ],
            [
              6,
              5
            ]
          ],
          "width": 8
        },
        "kiln": {
          "board": [
            ".....P.",
            ".......",
            ".....#.",
            "#B...T.",
            "...##..",
            "...#...",
            ".#....."
          ],
          "height": 7,
          "walls": [
            [
              2,
              5
            ],
            [
              3,
              0
            ],
            [
              4,
              3
            ],
            [
              4,
              4
            ],
            [
              5,
              3
            ],
            [
              6,
              1
            ]
          ],
          "width": 7
        },
        "stile": {
          "board": [
            ".....B.",
            "..#....",
            "P..#...",
            ".#.....",
            ".#..T..",
            ".....#."
          ],
          "height": 6,
          "walls": [
            [
              1,
              2
            ],
            [
              2,
              3
            ],
            [
              3,
              1
            ],
            [
              4,
              1
            ],
            [
              5,
              5
            ]
          ],
          "width": 7
        },
        "warren": {
          "board": [
            "........",
            ".##..#..",
            "....#.B#",
            ".......#",
            "..T.....",
            "........",
            ".......P",
            "........"
          ],
          "height": 8,
          "walls": [
            [
              1,
              1
            ],
            [
              1,
              2
            ],
            [
              1,
              5
            ],
            [
              2,
              4
            ],
            [
              2,
              7
            ],
            [
              3,
              7
            ]
          ],
          "width": 8
        }
      },
      "item_id": "v11-why-ce-01",
      "kind": "counterexample",
      "points": 3.0,
      "prompt": "Give a legal situation on one of these boards at which the quoted sentence is false.",
      "quoted": "The manual's `laws:` section contains the line\n    invariant box_row_parity (Box.pos.row) mod 2 = 1 [status: proven]\nwhich asserts that the row the Box stands in is always odd. Name a situation, on one of the boards listed in this item, at which that assertion is false. A situation is legal when both cells are on the board, neither is a wall, and the Player is not standing on the Box.",
      "tags": [
        "rule_justification",
        "counterexample"
      ]
    }
  ]
}
```