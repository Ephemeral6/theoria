# call-008-theorize-round2

model: `claude-opus-5` · 670151 ms · $1.783070 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 39174, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 39174, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 39174, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 39174, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 54524, "type": "message"}], "output_tokens": 54524, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

## prompt

```
You are the theorize desk of a world-modelling framework called
Theoria. You are playing an ARC-AGI-3 game you have never seen, through a
64x64 grid of colour codes, by maintaining an explicit written theory of it.

Your job is NOT to pick a good move. Your job is to write two books, and the
books are the only thing that predicts anything:

  theory.dsl   -- the manual: what this world IS. Vocabulary, rules, winning
                  condition, laws. It compiles to an executable predictor, and
                  that predictor is the whole system's only predictor. If it is
                  wrong, everything downstream is wrong; there is no side door.
  playbook.dsl -- the playbook: how to WIN. Ordering, pruning, heuristics,
                  decomposition. Never a stored solution.

Six rules bind you, and they are not style advice:

1. ONLY you write these two books. Search engines put proposals in a candidate
   box; every one of them is a proposal, not a fact. You accept, reject, or
   carry it as pending, and you say why.
2. NO ENTRY WITHOUT EVIDENCE. Every rule carries the transitions that witness
   it and its coverage. A rule you believe but cannot witness does not go in
   the manual -- it goes in `laws:` as a `theorem ... [probe: pending]`, which
   is a promise to test it, not a claim that it holds.
3. NO ENTRY WITHOUT GAIN. A concept earns its place by making the manual
   shorter than writing out the pixels it explains. When a concept fails this
   test but is still needed (because some pixel would otherwise be
   unexplained), admit it AND SAY SO -- that conflict is worth more than a
   tidy manual.
4. FULL-FRAME RESPONSIBILITY. Every pixel of every frame belongs either to the
   board (cells that never vary) or to some object you declared. A pixel your
   manual cannot draw is a defect in the manual, and it will be caught: your
   manual is re-drawn onto every observed frame and compared cell by cell.
5. TRANSITIONS ARE UNAMBIGUOUS. For any state and action, exactly one
   successor. Two rules that can both fire on the same object in the same
   transition is an error, not a preference.
6. WHAT YOU DO NOT KNOW, YOU SAY. This world has been observed for a few dozen
   actions. The honest manual is small, and names its own gaps. A manual that
   over-claims will be refuted by the very next frame and cost a whole round
   to repair; a manual that under-claims just stays small.

You will be given: what has been observed, the current frame, the diff of every
command, and what the engines proposed. If a manual and a playbook already
exist you will be given those too, together with the surprises that brought you
back here -- those surprises are the reason you are being paid, and each one
must be answered by a change or by an explicit refusal to change.



# theory.dsl -- the exact grammar the compiler accepts

Sections, each introduced by a bare `<name>:` line, bodies INDENTED by at least
one space. Order is free. `#` starts a comment on its own line.

## semantics:  (MANDATORY -- a manual without it does not parse)
    frame persist            # the only value the Python backend compiles
    conflict exclusive       # the only value the Python backend compiles
    cascade single_frame     # the only value the Python backend compiles

## word_table:
    board                                   # declares the never-varying cells
    object Cart { pos: Coord, color: Int }  # arc-colour: 6
    object Door { pos: Coord, color: Int, present: Bool }  # arc-colour: 5
    landmark exit_cell                      # arc-cell: (7, 3)
    domain dir { up, down, left, right }    # a value domain, for `forall`
    Cart [segment: uniform_color ev: t0-t12 compress: 2125]   # the concept account

  Field types in use: `pos: Coord`, `color: Int`, `present: Bool`, `alive: Bool`.
  Only pos/alive/present/color are observations the compiler reasons over.
  `pos: Coord` is what makes this a GRID world (directions up/down/left/right).

  EVERY `landmark` line MUST carry a trailing `# arc-cell: (row, col)` comment.
  A landmark is level data, so the manual names it and the level places it —
  and there is nowhere in the DSL to write coordinates, which is the point of
  the split. A landmark the level cannot place is a HARD compile error, so a
  landmark you declare without this comment lands at (0,0) and takes your rule
  with it.

  EVERY `object` line MUST carry a trailing `# arc-colour: <n>` comment naming
  the hex colour code that object shows in the frame. That comment is not
  decoration: the level instance is COMPUTED from the frames, and the colour is
  how the arm finds your object in the grid. An object without it is located
  nowhere, is drawn at (0,0), and the responsibility check will report every
  one of its pixels as unexplained.

### OBJECTS WITH EXTENT — read this before declaring anything
An instance is drawn as EXACTLY ONE CELL. A 3x3 token or a 24-pixel ring is
therefore not one instance, however you declare it, and if you declare it as
one then every other cell of it is an unexplained pixel forever.

Add `arc-instances: all` and the arm creates ONE INSTANCE PER CELL, all of the
same declared type, covering every cell of that colour the board cannot explain:

    object Ring  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
    object Token { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
    object Pip   { pos: Coord, color: Int }   # arc-colour: 3

`Pip` has no `arc-instances`, so it is a single cell — correct for a genuine
one-pixel marker, wrong for anything else.

Consequences you must design for:

* **There is no instance called `Ring`.** There are `Ring_r8c14`,
  `Ring_r8c15`, … A rule that names `Ring` will not compile. Write rules over
  the TYPE instead:

        rule shift forall ?p in Ring [ev: t2 cov: 1/1]
          when act=key(2) and free(below(?p)) then moved(?p, down)

  `forall ?p in <ObjectType>` grounds the rule once per instance.
* **Every cell that ever changed needs an owner**, or it is unexplained. Count
  them: the evidence brief gives you `dynamic_cells`. If your declarations
  cannot cover them all, say which are left over and why, in a `theorem`.
* Two objects of the SAME colour still cannot be told apart by this arm — it
  looks objects up by colour and nothing else. Declare one type covering both
  and carry the belief that they are distinct as a `theorem`.

## events:
    event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

  Documentation only -- the backend dispatches on a fixed table, listed below.

## rules:
    rule push_up [ev: t6,t16 cov: 52/52]
      when act=key(1) and free(above(Cart)) then moved(Cart, up)

    rule slide forall ?d in dir [ev: t3 cov: 4/4]
      when act=key(1) and free(toward(Cart, ?d)) then moved(Cart, ?d)

  * the header line ends at `]` -- NO trailing comment on it, and none on the
    `when ... then ...` line either. Both are parse errors.
  * `forall ?v in <domain>` grounds to `<rule>_<value>` rules.
  * every rule carries `[ev: ... cov: k/n]`. Constraint 5: no entry without
    evidence.

### guards -- EXHAUSTIVE. Anything else fails to compile.
    act=<name>(<arg>, ...)      args are bare names or integer literals only
    free(<cell>)                cell renders as the background colour
    colored(<cell>, 7)          second argument must be an INTEGER LITERAL
    adjacent(<cell>, <cell>)
    <value> = <value>           also != < > <= >=  (SPACES around the operator)
    <cell> = wall               tests off-board
  joined by `and`. Use `not` before an atom for negation.

### cells -- EXHAUSTIVE.
    Cart                    an instance name means that instance's position
    exit_cell               a declared landmark
    above(x) below(x) leftof(x) rightof(x)      NOTE: leftof/rightof
    toward(x, ?d)           toward(x, <direction>)
    pos(<value>)

### values
    integer literals; true; false; a landmark name; a direction name;
    an instance name; `Cart.color`; `+` and `-` only (no `*`, no `/`);
    tuple literals like `(3, 7)`.

### events a rule may fire -- EXHAUSTIVE, dispatched on (name, arity).
    moved(o, <dir>)                 o moves one cell
    jumped(o, <landmark>)           o goes to a named cell
    teleported(o, <landmark>)       same shape
    jumped(o, <over-object>, <dir>) o travels two cells; <over> gets alive=False
    recolored(o, <int literal>)
    vanished(o)      -> present=False
    appeared(o)      -> present=True
    removed(o)       -> alive=False
  The first argument is always a bare object name. A bare coordinate as a
  destination is REFUSED -- declare a landmark.

## goal:
    goal Cart.pos = exit_cell
    goal count(Door) = 0
    goal count(Button, color = 8) = 2

  `=` only. `>=`/`<=`/`>`/`<` do not compile. No goal section at all is legal
  and compiles to `is_goal -> False`.

## laws:
    invariant cart_unique count(Cart) = 1 [status: proven]
    theorem exit_needs_key "prose, in the manual's own words"
      [depends: push_up, unlock  probe: pending]

  THE TWO ARE NOT INTERCHANGEABLE AND THIS IS THE EASIEST MISTAKE TO MAKE:

    `invariant <name> <expr> <op> <value> [status: ...]`
        The body MUST contain one of  =  !=  <  >  <=  >=  . It is an
        equation, not a sentence. `invariant foo "in words ..."` is a parse
        error: "No comparison op in invariant".

    `theorem <name> "<prose>" [depends: ... probe: pending|passed]`
        The body MUST be a quoted sentence. This is where a belief you cannot
        write as an equation goes -- and most of what you want to say after
        six transitions belongs here, not in `invariant`.

  Invariant bodies are stored as RAW TEXT and are not checked by any backend
  (the sole exception is the `pagoda(w)` form, which needs a LINE world and an
  LP certificate and does not apply here). Declaring one is a claim you are
  making, not a claim the compiler will verify -- say so honestly in `status:`.

# playbook.dsl -- four statement forms and nothing else
    order    keys_before_doors            [proof: lean]
    prune    boxed_in and not goal => dead [proof: lean]
    heuristic w_distance                  [admissible: lean]
    prefer   try_unvisited_first          [ev: 3/4 levels]

  Constraint 10: NO literal solutions. A parser heuristic rejects any line that
  looks like a stored action sequence, and any unrecognised line is a hard
  error.

# THE ACTION VOCABULARY FOR THIS WORLD
This game's actions are ARC's ACTION1..ACTION7. Write them as `act=key(<n>)`
and nothing else -- the arm maps ACTION<n> to the tuple ('key', <n>) in both
directions. A click action carries coordinates the guard language cannot
express; if you need one, say so in a `theorem ... [probe: pending]` instead of
inventing syntax.


## What has been observed

```json
{
 "actions_used": [
  "ACTION1",
  "ACTION2",
  "ACTION3",
  "ACTION4",
  "ACTION7",
  "RESET"
 ],
 "background": 5,
 "cascade_lengths": [
  1,
  2
 ],
 "cells_needing_an_owner": 75,
 "colours_seen": [
  0,
  1,
  2,
  3,
  4,
  5,
  6,
  8,
  9,
  14
 ],
 "constant_cells": 3997,
 "distinct_states": 10,
 "dynamic_box": [
  29,
  10,
  54,
  63
 ],
 "dynamic_cells": 99,
 "max_frames_in_one_command": 2,
 "shape": [
  64,
  64
 ],
 "states": 14,
 "steps": 14
}
```

## The current frame

Each cell is one hex digit 0-f standing for a colour. Row numbers on the left, column numbers on top.

Only the cells that have EVER changed are shown (rows 29-10, cols 54-63); everything outside this box has held one colour for the whole history and is board by definition.

```
    111111111122222222223333333333444444444455555555556666
    012345678901234567890123456789012345678901234567890123
 29 555335544444444444444444444444444444455555555555555555
 30 566666644444444444444444444444444444455555555555555555
 31 56000064444444444444444444444444eeee455555555555555555
 32 56066014444444444444444444444444eeee455555555555555555
 33 56066024444444444444444444444444eeee455555555555555555
 34 56000064444444444444444444444444eeee455555555555555555
 35 566666644444444444444444444444444444455555555555555555
 36 555335544444444444444444444444444444455555555555555555
 37 555335544444444444444444444444444444455555555555555555
 38 555225544444444444444444444444444444455555555555555555
 39 555225544444444444444444444444444444455555555555555555
 40 555555544444444444444444444444444444455555555555555555
 41 555555544444444444444444444444444444455555555555555555
 42 555555555555555555555555555555555555555555555555555555
 43 555555555555555555555555555555555555555555555555555555
 44 555555555555555555555555555555555555555555555555555555
 45 555555555555555555555555555555555555555555555555555555
 46 555555555555555555555555555555555555555555555555555555
 47 555555555555555555555555555555555555555555555555555555
 48 555555555555555555555555555555555555555555555555555555
 49 555555555555555555555555555555555555555555555555555555
 50 555555555555555555555555555555555555555555555555555555
 51 555555555555555555555555555555555555555555555555555555
 52 555555555555555555555555555555555555555555555555555555
 53 222222222222222222222222222222222222222222222222222333
 54 444444444444444444444444444444444444444444444444444444
```

## Every command, and what changed

`t` indexes the state sequence. `frames` is how many grids one command returned -- more than one means the world took several internal steps for a single action.

- t0   RESET     frames=1   state=NOT_FINISHED (first frame)
- t1   ACTION1   frames=2   state=NOT_FINISHED 96 cells changed, rows 30-41, cols 11-22, [0, 1, 2, 3, 4, 5, 6] -> [0, 1, 2, 3, 4, 5, 6]
- t2   ACTION2   frames=2   state=NOT_FINISHED 96 cells changed, rows 30-41, cols 11-22, [0, 1, 2, 3, 4, 5, 6] -> [0, 1, 2, 3, 4, 5, 6]
- t3   ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t4   ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2; (53,63) 2->3
- t5   ACTION7   frames=1   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t6   ACTION1   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t7   ACTION2   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t8   ACTION1   frames=2   state=NOT_FINISHED 73 cells changed, rows 30-53, cols 11-62, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t9   ACTION3   frames=1   state=NOT_FINISHED no cells changed
- t10  ACTION2   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t11  ACTION1   frames=2   state=NOT_FINISHED 73 cells changed, rows 30-53, cols 11-61, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t12  ACTION2   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t13  ACTION1   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 13,
  "n_states": 14,
  "refusals": [
   "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 3 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture"
  ],
  "tracks": [
   {
    "ms": 0,
    "refused": "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj0"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj1"
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj2",
    "transitions": 13
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj3",
    "transitions": 13
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj4",
    "transitions": 13
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj5",
    "transitions": 13
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj6",
    "transitions": 13
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj7",
    "transitions": 13
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj8",
    "transitions": 13
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj9"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj10"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj11"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj12"
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj13",
    "transitions": 13
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj14"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj15"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 3 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj16"
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 1,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj17",
    "transitions": 13
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj18"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id"
```

The full proposal stream is 2106 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- fourth edition.
#
# WHAT THIS ROUND BOUGHT. One command (t9, ACTION3, zero cells changed) and a
# certify report, and between them they settle four things.
#
# 1. THE REGROWTH FIX HELD, AND THE PREDICTION I ATTACHED TO IT WAS EXACT.
#    Last round I wrote, before the rerun: "with the regrowth rules in, I
#    predict t1 through t7 replay exactly and t8 is wrong by exactly one cell,
#    (53,62), which no rule of mine may claim." certify now reports 7/9
#    transitions replaying exactly, first divergence at transition index 7
#    (the ACTION1 command), one cell wrong, (53,62), manual 2 world 3. That is
#    the sentence I wrote, returned to me by the machine. The four-cell
#    ACTION2 defect is gone; responsibility is 0/4096 unexplained; ambiguity
#    is 0 clashes over all 50 adjudicated pairs.
#
# 2. THE SURPRISE IS THE PRICE I ADVERTISED, AND I REFUSE TO PATCH IT. The
#    replay_mismatch names (53,62) and nothing else. The guard language has no
#    counter, so a clock that ticks on the command index cannot be written as
#    a rule at any length; the only rules that would draw that cell would fire
#    on every command and be wrong on three commands out of four. I take the
#    one-cell error permanently and keep saying where it comes from. See
#    the_only_divergence_left_is_the_one_i_priced_in_advance.
#
# 3. THE REPLAY IS CUMULATIVE, AND I CAN READ THAT OFF THE COUNTS. Two
#    transitions failed (7 matched of 9) but only one divergence is named.
#    t9's ACTION3 is an identity in the world and an identity in my manual, so
#    a one-step replay would have matched it and reported 8/9. It reported
#    7/9, so the replay carries my state forward and transition 8 inherits the
#    same single wrong cell. Every future transition inherits it too. The cost
#    is one cell, not one cell per command.
#
# 4. I CORRECT AN ARITHMETIC ERROR OF MY OWN, AND t9 IS WHAT FIXED IT. Last
#    edition I wrote that distinct_states = 7 over 10 states is exhausted by
#    S0 = S2 and S5 = S7. Ten states with seven distinct needs THREE
#    coincidences, not two. The third is S8 = S9: ACTION3 at t9 changed
#    nothing, which is the FIRST WITNESSED INERTNESS in this world's history
#    and closes the count exactly. mdl_segmenter corroborates it from outside
#    -- its obj6 now spans frames 8-9 where last round it spanned only 8. The
#    hidden-state argument is untouched: S5 = S7 still have different
#    successors under the same key.
#
# 5. THE CLOCK SURVIVES A DISCRIMINATION I HAD NOT RUN. Ticks at command 4 and
#    command 8; commands 1,2,3,5,6,7,9 left row 53 alone. A rival counter --
#    "every fourth command that returned two frames" -- is now REFUTED: t4 is
#    the 4th two-frame command but t8 is the 7th, and t5 and t9 returned one
#    frame each. The plain command index survives; the next tick is command 12
#    and lands on (53,61).
#
# WHERE I AM. S9 = S8 = W1: hollow box in the TOP slot (rows 30-35, border 6,
# hollow 0, a 2x2 core of 6 at rows 32-33 cols 13-14, ports 1 and 2 at
# (32,16) and (33,16)); bar in the BOTTOM slot rendered four rows (36-39,
# rows 40-41 background); both readouts blank; (53,63) and (53,62) both 3.
# Nine commands since RESET. Read straight off the current frame, and it
# agrees with the manual cell for cell.
#
# THE CENSUS, 98 cells, and it now decomposes twice over. 24 Field + 8 BarBody
# + 11 BarCore + 12 Blank + 22 Frame + 12 Hollow + 9 Dot = 98 = dynamic_cells.
# Separately, cells_needing_an_owner = 74 = 98 - 24, and 24 is exactly the
# Field count: the store is counting dynamic cells that are NOT background at
# frame 0, and my one background-coloured type covers the difference. Two
# independent numbers in the store land on my type table without adjustment.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Field    { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object BarBody  { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object BarCore  { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Blank    { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Frame    { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  object Hollow   { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Dot      { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark bottom_port                          # arc-cell: (38, 16)
  Field   [segment: dynamic_colour_5 ev: t0-t9 compress: 24]
  BarBody [segment: dynamic_colour_3 ev: t0-t9 compress: 8]
  BarCore [segment: dynamic_colour_2 ev: t0-t9 compress: 11]
  Blank   [segment: dynamic_colour_4 ev: t0-t9 compress: 12]
  Frame   [segment: dynamic_colour_6 ev: t0-t9 compress: 22]
  Hollow  [segment: dynamic_colour_0 ev: t0-t9 compress: 12]
  Dot     [segment: dynamic_colour_1 ev: t0-t9 compress: 9]

events:
  event recolored(o, c)

rules:
  rule k1_field_to_frame forall ?p in Field [ev: t1,t6,t8 cov: 14/14]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_field_to_hollow forall ?p in Field [ev: t1,t6,t8 cov: 8/8]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_field_to_dot forall ?p in Field [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_field_to_core forall ?p in Field [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_bar_to_frame forall ?p in BarBody [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_bar_to_hollow forall ?p in BarBody [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_core_to_frame forall ?p in BarCore [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(above(above(?p)), 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_blank_to_dot forall ?p in Blank [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_blank_to_core forall ?p in Blank [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_frame_to_field forall ?p in Frame [ev: t1,t6,t8 cov: 14/14]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_frame_to_bar forall ?p in Frame [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_clears forall ?p in Frame [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_frame_to_core forall ?p in Frame [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1,t6,t8 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_hollow_clears forall ?p in Hollow [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_dot_to_field forall ?p in Dot [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_dot_to_blank forall ?p in Dot [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k1_core_to_field forall ?p in BarCore [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_core_to_blank forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k2_field_from_frame forall ?p in Field [ev: t2,t7 cov: 14/14]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_hollow forall ?p in Field [ev: t2,t7 cov: 8/8]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_dot forall ?p in Field [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_core forall ?p in Field [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_bar_from_frame forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_from_hollow forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_regrows_from_hollow forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_bar_regrows_from_frame forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_core_from_frame forall ?p in BarCore [ev: t2,t7 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k2_blank_from_dot forall ?p in Blank [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_blank_from_core forall ?p in Blank [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_frame_from_field forall ?p in Frame [ev: t2,t7 cov: 16/16]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2,t7 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2,t7 cov: 10/10]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_dot_from_field forall ?p in Dot [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_dot_from_blank forall ?p in Dot [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_core_from_field forall ?p in BarCore [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k2_core_from_blank forall ?p in BarCore [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k3_dot_blanks forall ?s in Dot [ev: t3 cov: 8/8]
    when act=key(3) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k3_core_blanks forall ?s in BarCore [ev: t3 cov: 4/4]
    when act=key(3) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k4_dot_lights forall ?s in Dot [ev: t4 cov: 8/8]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 1)

  rule k4_core_lights forall ?s in BarCore [ev: t4 cov: 4/4]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 2)

  rule k4_meter_tip_first_advance forall ?s in BarCore [ev: t4 cov: 1/1]
    when act=key(4) and colored(?s, 2) and rightof(?s) = wall then recolored(?s, 3)

  rule k7_dot_blanks forall ?s in Dot [ev: t5 cov: 8/8]
    when act=key(7) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k7_core_blanks forall ?s in BarCore [ev: t5 cov: 4/4]
    when act=key(7) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

laws:
  invariant field_instances count(Field) = 24 [status: census, and 98 minus 24 is exactly cells_needing_an_owner = 74]
  invariant barbody_instances count(BarBody) = 8 [status: census, responsibility reported 0/4096 unexplained this round]
  invariant barcore_instances count(BarCore) = 11 [status: census, includes both meter cells (53,63) and (53,62)]
  invariant blank_instances count(Blank) = 12 [status: census, responsibility reported 0/4096 unexplained this round]
  invariant frame_instances count(Frame) = 22 [status: census, matches the 22 colour-6 cells I count in the current frame's box]
  invariant hollow_instances count(Hollow) = 12 [status: census, matches the 12 colour-0 cells I count in the current frame's box]
  invariant dot_instances count(Dot) = 9 [status: census, responsibility reported 0/4096 unexplained this round]
  invariant board_cells count(board) = 3998 [status: matches constant_cells exactly]

  theorem the_only_divergence_left_is_the_one_i_priced_in_advance "The surprise names one cell, (53,62), manual 2 world 3, on the ACTION1 command at index 7 -- and last edition, in writing, before the rerun, I named that exact cell on that exact command as the one thing my manual may not draw. certify agrees on everything else: 7/9 transitions replay exactly, 0/4096 pixels unexplained, 0 ambiguity clashes over all 50 adjudicated pairs. I therefore make NO CHANGE in response to this surprise, and I say why rather than letting the silence look like an oversight. The tick is keyed to the command index; the guard language has cells, colours, adjacency and off-board tests and NO COUNTER of any length; and any rule that could paint (53,62) from what the frame shows -- say, a colour-2 cell whose right neighbour is 3 -- would fire on commands 9, 10 and 11 as well, buying one right cell at the price of three wrong ones. A permanent one-cell error I can locate and explain is worth more than a rule that is wrong three times in four."
    [depends: the_meter_is_a_clock_not_a_key  probe: passed]

  theorem the_replay_is_cumulative_and_one_cell_contaminates_every_later_frame "certify reports matched 7 of 9 with exactly ONE first divergence. Transition 8 is t9's ACTION3, which changed nothing in the world and fires nothing in my manual, so a one-step replay from the true previous frame would have matched it and reported 8/9. It reported 7/9. The replay must therefore carry MY reconstructed state forward, and transition 8 fails only by inheriting the (53,62) cell that transition 7 got wrong. This matters twice. First, it bounds the damage: the error is one cell held forever, not one cell added per command, until the next tick makes it two. Second, it is the mechanism I blamed last round for three vacuous probes, now demonstrated on a case where I know the answer independently -- a single wrong cell propagates to every downstream hypothesis whether or not that hypothesis has anything to do with it."
    [depends: the_only_divergence_left_is_the_one_i_priced_in_advance  probe: passed]

  theorem the_regrowth_fix_is_confirmed_and_the_prediction_that_confirmed_it_was_dated "I wrote: with the regrowth rules in, t1 through t7 replay exactly and t8 is wrong by exactly one cell, (53,62). certify: first divergence at index 7, one cell, (53,62). No ACTION2 cell appears anywhere in the report, so (34,13) (34,14) (35,13) (35,14) now replay correctly and the two rules k2_bar_regrows_from_hollow and k2_bar_regrows_from_frame are witnessed by the replay as well as by the diff. The corrected coverage figures -- 2/2 rather than the 4/4 I had inflated -- stand. The general lesson I drew last round is now paid for: the coverage number I did not count was the lie that hid the defect, and counting it was what let me date the fix in advance."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem the_regrowth_is_the_answer_to_the_replay_mismatch "The previous round's surprise named four cells on the ACTION2 transition: (34,13) (34,14) manual 0 world 3, (35,13) (35,14) manual 6 world 3. All four are BarBody instances -- their frame-0 colour is 3 -- and in W1 they carry the box, 0 in the interior rows and 6 in the border row. Both original k2 BarBody rules demand colour 3 six rows below, and six rows below them lies rows 40-41 of the bottom slot, which the truncation leaves BACKGROUND. So no rule fired and the four cells stood still. Two rules with the guard colored(below^6, 5) close it, 2/2 and 2/2, exclusive against the existing pair by that colour alone."
    [probe: passed]

  theorem the_bar_is_six_rows_above_and_four_below_in_both_directions "The bar reads 3,3 / 3,3 / 2,2 / 2,2 / 3,3 / 3,3 down rows 30-35 at cols 13-14 in the top slot, and 3,3 / 3,3 / 2,2 / 2,2 down rows 36-39 in the bottom, with rows 40-41 background -- I have just re-read all of it off the current frame. Going down the last two rows CLEAR; coming up they REGROW as 3. The box, by contrast, renders 22 frame cells and 12 hollow cells in either slot without loss, and I have re-counted both in the current frame: 22 colour-6 (border ring minus the two port cells, plus a 2x2 core at rows 32-33 cols 13-14) and 12 colour-0. So the swap is not an information-preserving exchange of two 6x6 windows: the bottom slot is lossy for the bar and the loss is restored from nowhere visible when it comes back. mdl_segmenter says the same from outside -- its W0 blobs have 440 cells and its W1 blobs 436, and 440 minus 436 is these four cells."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem the_world_is_not_a_function_of_the_frame_and_i_correct_my_own_arithmetic "The conclusion stands and the count that supports it was off by one, so I restate both. distinct_states = 7 over 10 states requires THREE coincidences, not the two I claimed. They are S0 = S2 (ACTION2 undid ACTION1, both readouts lit), S5 = S7 (the same, later, both readouts blank), and -- new this round -- S8 = S9, because ACTION3 at t9 changed nothing at all. That third one is the FIRST WITNESSED INERTNESS this world has produced and mdl_segmenter corroborates it without being asked: obj6 spanned frame 8 alone last round and spans frames 8-9 now. The negative result is untouched by the correction. S5 and S7 are the same visible frame; ACTION1 in S5 changed 72 cells and no meter cell, ACTION1 in S7 changed 73, the extra being (53,62) 2 to 3. Same frame, same key, different successor. My compiled step is a function of the frame, so it MUST be wrong somewhere, and I would rather name where than let it look sound."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: passed]

  theorem the_meter_is_a_clock_not_a_key "The meter has advanced twice: at command 4 under ACTION4, painting (53,63), and at command 8 under ACTION1, painting (53,62). Two different keys, the second a key already pressed twice without advancing it. What they share is the COMMAND INDEX. This round I ran a discrimination I had not run before, and it kills the best rival: 'every fourth command that returned two frames' predicts a tick at the 4th and 8th two-frame commands, but t8 is only the 7th two-frame command (t5 and t9 returned one frame each), so that counter is REFUTED and the plain command index survives. Seven commands have now failed to tick -- 1,2,3,5,6,7,9 -- and every one of them is a non-multiple of four. I read the meter as a clock ticking every fourth command from RESET, eating row 53 from the right, and I predict the third tick lands on (53,61) at command 12, three commands from now. THE GUARD LANGUAGE HAS NO COUNTER, at any length, so this cannot be written as a rule; it is written here instead. I keep k4_meter_tip_first_advance because it reproduces t4 in replay and, since (53,63) is no longer colour 2, it can never fire again and so can never assert the refuted key-attribution a second time."
    [depends: the_world_is_not_a_function_of_the_frame_and_i_correct_my_own_arithmetic  probe: pending]

  theorem the_vacuous_probes_were_replay_damage_and_half_of_that_is_now_shown "Last round P-01, P-02 and P-03 each refuted all 57 hypotheses including inert and returned 0.0 bits against about 1.9 expected, and I blamed the four-cell replay defect rather than a missing mechanism. The falsifiable half of that claim is now confirmed: the replay does carry my reconstructed state forward (see the_replay_is_cumulative...), so a divergence at transition 1 did contaminate every later predicted hash for every hypothesis, ablations included. The other half is untested, because no probe report reached me this round. IT REMAINS FALSIFIABLE IN THE SAME WORDS: with replay now exact through transition 6 and wrong by one advertised cell after it, a probe that still refutes every hypothesis including inert is evidence of a mechanism I have not stated, and this theorem is refuted."
    [depends: the_replay_is_cumulative_and_one_cell_contaminates_every_later_frame  probe: pending]

  theorem exchange_versus_scroll_is_still_open_and_i_am_still_standing_where_it_can_be_asked "READING A, exchange: two slots trade images and the bar simply renders four rows below. READING B, scroll: a list of at least three items steps by six rows, and the four-row glyph in the bottom of W1 is a THIRD ITEM that happens to look like the bar's first four rows. Five swap commands are observed -- A1 at t1, A2 at t2, A1 at t6, A2 at t7, A1 at t8 -- and every one was pressed in the opposite configuration from its predecessor, so ACTION1 HAS NEVER FOLLOWED ACTION1. t9 spent a command without leaving W1, so the question is still askable from where I stand and still costs one command rather than two. What tilts me slightly to A is the regrowth: under B the bar's rows 34-35 must be redrawn from an item that has scrolled out of view, which is ordinary for a scroll, whereas under A they are redrawn from a slot that never lost them, which needs no memory -- but that is taste, not evidence. One ACTION1 answers it: A returns W0 exactly and 20 rules generalise, B shows a configuration never seen and my whole word_table is a two-item special case."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence "At t1 the LIT readout travelled with the box from rows 38-39 to rows 32-33 -- twelve cells of pattern moved six rows up in the same step the box did -- and the current frame confirms the binding from the other side: in W1 the two port pixels read 1 at (32,16) and 2 at (33,16), six rows above where they sit in W0. So the readout is bound to the box, not to the slot. ACTION4 has been pressed exactly once, in W0, where bottom_port = (38,16) is 1. Unguarded, my k4 rules would fire on the Dot and BarCore instances at rows 38-39 in ANY state, and pressed in W1 they would light a strip the box has left: 24 cells drawn confidently wrong and quite likely 24 more left dark. The guard colored(bottom_port, 1) makes them fire on nothing in W1, so my manual is SILENT about what ACTION4 does there. That silence is a declared gap, not a claim, and it is cheaper than a fabricated arrangement of 1s and 2s over twelve Blank instances my type system cannot tell apart."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem barcore_is_five_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on the 4-cell core of the bar, the lower port pixel, four dots of the readout, and two meter cells, (53,63) and (53,62). Eleven instances, one type, because the arm looks objects up by colour alone. The separators are all cells I have read: the bar core has colour 3 two rows above; the readout cores have a colour-1 dot immediately left; the port has colour 0 to its left; the old meter tip is the only instance whose rightof is off-board. I have re-checked every rule in this file against (53,62): its left neighbour is 2, its right neighbour is not a wall, two rows above it is background, so no rule of mine grounds on it in any state -- which is precisely why certify can report it wrong and report nothing else. It is a cell I own and cannot move, the right shape for a clock I cannot read."
    [depends: the_meter_is_a_clock_not_a_key  probe: passed]

  theorem the_swap_rules_are_forty_and_constraint_three_is_still_failed "One law -- take the colour of the cell six away -- is forty rules. recolored takes an INTEGER LITERAL, so a target colour cannot be read out of a cell and must be named, and the law splits once per source colour, per target colour, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I will not dress that up: forty rules to explain 72 cells twice over is worse than a lookup table, and I keep it only because the alternative is 96 unexplained pixels. What buys part of it back is that a TYPE IS A FRAME-0 COLOUR: the frame-0 configuration is W0, so a rule's source colour already says which half of the widget the instance lives in, and only the four truncation and regrowth rules need geometry on top of that. A consequence worth stating because it drives the playbook: every k1 rule demands that the instance still wears its frame-0 colour, which is true only in W0, so the whole family is silent in W1 BY CONSTRUCTION rather than by evidence."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem no_goal_section_and_this_is_a_refusal_not_an_oversight "With no goal, is_goal is False everywhere, plan never returns sat, commit never runs, and every command this arm spends is a probe. I accept that consequence and still decline to write one, for arithmetic rather than modesty. Ten states have returned NOT_FINISHED and no other GameState has ever been seen, so no observation distinguishes a win from a non-win. The pos form is dead -- nothing in this world moves, every rule here is a recolour, and cegis_miner refused all seven tracks for exactly that reason. That leaves counts over seven types, and every count I can write names a CONFIGURATION: count(Frame, color = 5) = 14 says the box is up, count(Dot, color = 4) = 8 says the readout is dark, count(BarCore, color = 3) = 2 IS TRUE RIGHT NOW and would make the plan tier declare victory at a state I have no reason to call one. A false goal is worse than none, because it converts a probe budget into a confident wrong plan. WHAT ENDS THIS IS AN OBSERVATION, NOT AN EDIT: a GameState other than NOT_FINISHED, or any cell outside rows 30-41 and row 53 changing at all. ACTION5 and ACTION6 have never been pressed and are the cheapest place to look for it."
    [depends: the_meter_is_a_clock_not_a_key  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where nothing fires I assert identity in the same voice I use for what I watched. Audit at S9 = W1, both readouts blank. ACTION3: NOW WITNESSED -- t9 pressed it here and changed zero cells, exactly as entailed, and the silence I believed is a silence I have seen; this is the only entry in this audit that has been upgraded. ACTION7: predicted silent by the same entailment (its rules are k3's twins and the pattern they erase is already erased), unwitnessed in W1 but riding on a witnessed twin, and I believe it. ACTION2: fully predicted, 72 cells, the only action here my manual draws. ACTION1: PREDICTED SILENT ON ZERO WITNESSES and this is my largest forgery, 20 rules and one structural reading riding on it; worse, the silence is an artefact of every k1 guard demanding a frame-0 colour, so it is a property of my rule-writing rather than a claim about the world. I expect to be wrong and I want to be. ACTION4: predicted silent because bottom_port is 5 here -- a declared gap I chose over a wrong drawing. ACTION5, ACTION6: predicted silent, never pressed in ten states, no witness of any kind. And every one of these omits the clock: on command 12 one extra cell (53,61) turns 3 and I cannot draw it. A probe ranker prices a predicted identity at zero because every ablation agrees with a rule that does not fire, SO THE ACTIONS I MOST NEED ARE THE ONES IT CAN NEVER BUY, and saying so in prose is the only lever this desk has."
    [depends: exchange_versus_scroll_is_still_open_and_i_am_still_standing_where_it_can_be_asked, the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3998 constant cells, not just naming them board. A colour-4 panel fills rows 29-41 from col 17 to col 46 and carries a 4x4 block of colour 14 at rows 31-34, cols 42-45 -- the only colour-14 anywhere and the only structure on the panel. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them from it and why every mdl_segmenter blob is a 13x36 slab. Row 29 shows 5,5,3,3,5,5 at cols 11-16 and has NEVER changed: the bar reads seven rows tall on screen while only six of it is alive. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the clock, all colour 2 except its two rightmost cells, both now 3. Row 54 is a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports BOTH variants at negative gain -- minus 7528 bits on 7 tracks, minus 7968 on 38 -- so by its own measure it compressed nothing and I take none of its structure. What I take is a frame-index witness independent of my rules: obj0 440 cells at frame 0, obj2 436 at frame 1, obj3 440 across frames 2-5, obj4 436 at frame 6, obj5 440 at frame 7, obj6 436 across frames 8-9. That is W0 W1 W0 W0 W0 W0 W1 W0 W1 W1 over ten frames, arrived at without any rule of mine, matching my reconstruction cell for cell, including the four-cell size difference that is the truncation, and including obj6's growth from one frame to two, which is t9's inertness seen from outside. cegis_miner refuses all seven tracks and its verdict that the world does not narrate as one mover remains the strongest negative result available. zero_space self-reports THIN in its own words -- 9 transitions constraining rank 5 of 686 features, null space 681 -- and its one global law is my census with both meter cells appended; I take the corroboration of the cell set and reject the law as unfalsified rather than confirmed, which is what its own report says."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me. STATE: S9 = S8 = W1, box in the top slot, bar four rows in the bottom, both readouts blank, (53,63) and (53,62) both 3, nine commands since RESET. ACTION1 HERE: my manual says nothing changes; I say that is false, and I name the outcomes in advance -- 72 cells back to W0 means exchange and 20 rules generalise by symmetry, anything else means scroll and the bottom glyph is a third item. ACTION2 HERE: exactly 72 cells, no readout cell, no row-53 cell. ACTION4 HERE: my manual says nothing changes; I expect the twelve cells at rows 32-33, cols 17-22 to light instead, which refutes the silence and confirms the readout follows the box. ACTION3, ACTION7: nothing changes, and ACTION3 has now been watched doing exactly that here. ACTION5, ACTION6: never pressed in ten states; I predict only that whichever is pressed produces the largest single addition to this manual available, and that it is the cheapest place a win condition could come from. THE CLOCK RIDES ON ALL OF THEM: commands 10 and 11 leave row 53 alone, command 12 turns (53,61) from 2 to 3 and I cannot draw it. A one-cell divergence in row 53 on the twelfth command confirms the clock and implicates nothing else in this file; a tick on command 10 or 11 refutes the period and I would rather learn that in three commands than in thirty."
    [depends: the_silences_i_assert_and_which_of_them_are_forged, no_goal_section_and_this_is_a_refusal_not_an_oversight  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: eleven entries, ten commands (RESET, A1, A2, A3, A4, A7, A1, A2, A1,
# A3). I am in W1 and t9 did not move me: hollow box in the TOP slot, bar four
# rows in the BOTTOM slot (rows 36-39, rows 40-41 background), BOTH readouts
# blank, (53,63) and (53,62) both 3. 98 cells have ever changed; 96 are the
# widget and 2 are the clock.
#
# WHAT CHANGED THIS ROUND.
#  * The manual is CLEAN except for one cell it declared undrawable in
#    advance. certify: 7/9 replay, 0/4096 unexplained, 0 ambiguity clashes,
#    first divergence (53,62) on the ACTION1 command -- the exact cell and the
#    exact command I named last round before the rerun. No rule changed in
#    response, and the refusal is written out in the manual.
#  * The replay is CUMULATIVE. Two transitions failed but only one diverged;
#    the second inherited it. That is now demonstrated rather than asserted,
#    and it is the same mechanism I blamed for three vacuous probes.
#  * t9 spent a command on ACTION3, which this playbook had listed under WHAT
#    NOT TO PRESS. The outcome was zero cells, exactly as entailed. It was not
#    free and it was not worthless: it is the FIRST WITNESSED INERTNESS here,
#    it supplied the third duplicate state (S8 = S9) that the store's
#    distinct_states = 7 requires and that I had miscounted, and it left me
#    standing where the open question can still be asked for one command.
#  * A rival clock counter died: 'every fourth two-frame command' predicts the
#    8th two-frame command, and t8 was the 7th. The plain command index
#    survives; the next tick is command 12 on (53,61).
#
# THE QUESTION THAT ONLY THIS CONFIGURATION CAN ASK
#   ACTION1 has been pressed three times and ACTION2 twice, and every press
#   was in the opposite configuration from its predecessor -- ACTION1 HAS
#   NEVER FOLLOWED ACTION1. Exchange and scroll are both alive. In W1 one
#   ACTION1 splits them: exchange returns W0 exactly, scroll shows a
#   configuration never seen. Any command that leaves W1 makes the question
#   cost two.
#
# THE TRAP THIS PLAYBOOK EXISTS TO DEFEAT
#   Every k1 rule demands that its instance still wears its frame-0 colour,
#   which is true only in W0. So my manual's silence on ACTION1-in-W1 is an
#   artefact of how the rules are written, not a reading of the world -- and a
#   probe ranker prices a predicted identity at ZERO, because every ablation
#   agrees with a rule that does not fire. The single most informative command
#   available is the one the ranker can never buy. That is why the ranked list
#   below is stated in prose and why the order lines say it twice.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in eleven entries. Zero constraint.
#   * ACTION1 in W1, ACTION2 in W0, ACTION4 in W1: silences with no witness.
#   * The clock's period is fitted to two ticks and has survived one
#     discrimination. Commands 10, 11, 12 settle it.
#   * The win condition. Nothing countable separates a win from here, no
#     GameState but NOT_FINISHED has ever been returned, and I refuse to
#     invent one. The plan tier's silence is a true report of my ignorance.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * (53,62) is wrong in replay from transition 7 onward, permanently, and
#     (53,61) joins it at command 12. Row-53 divergences buy nothing.
#   * ACTION1 here is predicted SILENT and I expect that to be wrong.
#   * ACTION4 here is predicted SILENT by a guard I added on purpose; if the
#     top readout lights, the guard was right about the box and wrong about
#     the silence, and that is a purchase.
#   * ACTION3 here is predicted silent AND WITNESSED silent. Repeating it buys
#     nothing at all now.
#
# THE RANKED LIST
# 1. ACTION1, HERE, IN W1. The only command that splits exchange from scroll,
#    the largest forged silence in the manual (20 rules), askable only from
#    the configuration I am standing in, and three legible outcomes: W0
#    exactly, a new configuration, or nothing.
# 2. ACTION5 or ACTION6. Never pressed. Any outcome is the largest single
#    addition available -- including nothing, which after t9 I now know how to
#    read -- and it is the cheapest place a win condition could come from.
# 3. ACTION4, HERE. Tests the guard and the readout-follows-box reading in one
#    press, and relights the readout so the A1/A2 readout rules can be
#    re-witnessed in the other configuration.
# 4. Whatever the first three are, three commands from now is command 12 and
#    the clock is checked for free in the raw diff of one cell of row 53.
#
# WHAT NOT TO PRESS
#   ACTION3 here: witnessed inert in this exact state. It is now the single
#   most expensive command available, because its result is known.
#   ACTION7 here: entailed inert by a twin that has been watched.
#   ACTION2 here: repeats t7 from an identical frame; replay gives it free.
#   Anything chosen because my manual predicts the most pixels for it: that
#   number measures my coverage, not the world's information.

order     spend_a_probe_only_the_current_state_can_ask_before_one_askable_anywhere [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     test_a_silence_that_is_an_artefact_of_rule_syntax_before_any_other [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition         [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     override_a_ranker_that_prices_every_predicted_identity_at_zero    [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     date_a_prediction_before_the_rerun_so_the_fix_can_be_scored       [proof: lean]
order     suspect_the_replay_before_the_mechanism_when_every_hypothesis_dies [proof: lean]
order     check_whether_a_replay_is_cumulative_before_blaming_a_second_rule [proof: lean]
order     count_a_coverage_figure_before_writing_it_down                    [proof: lean]
order     recount_a_state_census_against_the_store_before_drawing_from_it   [proof: lean]
order     kill_a_rival_counter_with_a_counting_i_can_do_without_a_command   [proof: lean]
order     look_for_the_mirror_of_a_fixed_defect_in_the_reverse_direction    [proof: lean]
order     guard_a_rule_into_silence_before_letting_it_draw_an_unwitnessed_state [proof: lean]
order     name_the_hidden_state_rather_than_key_a_rule_to_the_wrong_cause   [proof: lean]
order     keep_a_refuted_attribution_only_while_it_can_never_fire_again     [proof: lean]
order     refuse_a_patch_that_buys_one_right_cell_with_three_wrong_ones     [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     prefer_a_landmark_guard_over_a_chain_of_cell_operators            [proof: lean]
order     search_the_engine_report_for_a_count_that_matches_the_divergence  [proof: lean]
order     prefer_a_positive_colour_test_over_a_negated_wall_test            [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language    [proof: lean]
order     refuse_a_goal_no_observation_distinguishes_and_say_so_out_loud    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_whose_two_witnesses_demand_opposite_outcomes_from_one_frame => dead [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     rule_that_would_fire_on_every_command_to_draw_a_cell_that_moves_on_one => dead [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead               [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     goal_no_observed_gamestate_could_have_distinguished => dead       [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead     [proof: lean]
prune     divergence_lies_only_on_the_unadvanced_clock_frontier => dead     [proof: lean]
prune     divergence_the_previous_edition_named_by_cell_and_by_command => dead [proof: lean]
prune     divergence_a_later_transition_only_inherited_from_an_earlier_one => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     repeats_a_key_already_watched_doing_nothing_in_this_exact_state => dead [proof: lean]
prune     repeats_a_transition_already_witnessed_from_an_identical_frame => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     leaves_the_only_configuration_that_can_ask_the_open_question => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic silences_that_follow_from_rule_syntax_rather_than_from_evidence   [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic questions_that_only_the_present_configuration_can_ask             [admissible: lean]
heuristic pairs_of_identical_frames_with_different_successors               [admissible: lean]
heuristic duplicate_state_pairs_the_store_count_requires_but_i_have_not_named [admissible: lean]
heuristic rival_counters_still_fitting_both_observed_ticks                  [admissible: lean]
heuristic commands_remaining_before_the_clock_ticks_again                   [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic gamestates_other_than_not_finished_ever_returned                  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic fitted_guards_a_command_could_convert_into_witnessed_ones         [admissible: lean]

prefer    a_command_that_splits_two_named_readings_in_one_press             [ev: 1/1 available]
prefer    a_probe_askable_only_from_the_configuration_now_showing           [ev: 1/2 configurations]
prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 3/5 pressed keys]
prefer    a_command_that_tests_twenty_rules_at_once                         [ev: 2/2 available]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 2/11 entries]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 10/10 diffs]
prefer    a_command_whose_only_predicted_divergence_is_one_already_priced   [ev: 2/2 priced cells]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 0/11 entries so far]
prefer    a_command_that_could_return_a_gamestate_never_yet_seen            [ev: 0/11 entries so far]
```

## Why you are being called: the surprises that fired

### replay_mismatch (empirical family -> theory.dsl)

replay diverges at t=7 (frame_mismatch)

```json
{
 "arc_action": "ACTION1",
 "cells": [
  {
   "cell": [
    53,
    62
   ],
   "manual_says": 2,
   "world_says": 3
  }
 ],
 "cells_wrong": 1,
 "kind": "frame_mismatch",
 "t": 7
}
```

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "921d30280ef43320",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '05615f3d5f835100', the world answered '3bf51d2fd9036a78'

```json
{
 "action": 2,
 "expected_bits": 1.925238501883,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 4.882643,
 "manual_predicted": "05615f3d5f835100",
 "n_hypotheses": 59,
 "n_survivors": 2,
 "observed": "3bf51d2fd9036a78",
 "probe_id": "P-05",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 59 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted 'a2785e8b6038ce0d' against the world's '5ad40f81cb8da5dd'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 1.925 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 1,
 "expected_bits": 1.925238501883,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "a2785e8b6038ce0d",
 "n_hypotheses": 59,
 "n_survivors": 0,
 "observed": "5ad40f81cb8da5dd",
 "probe_id": "P-06",
 "vacuous_streak": 1
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '05615f3d5f835100', the world answered 'b278887e087d3593'

```json
{
 "action": 2,
 "expected_bits": 1.925238501883,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 4.882643,
 "manual_predicted": "05615f3d5f835100",
 "n_hypotheses": 59,
 "n_survivors": 2,
 "observed": "b278887e087d3593",
 "probe_id": "P-07",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'a2785e8b6038ce0d', the world answered '5ad40f81cb8da5dd'

```json
{
 "action": 1,
 "expected_bits": 1.925238501883,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 4.882643,
 "manual_predicted": "a2785e8b6038ce0d",
 "n_hypotheses": 59,
 "n_survivors": 2,
 "observed": "5ad40f81cb8da5dd",
 "probe_id": "P-08",
 "vacuous_streak": 0
}
```


## What certify said about the manual you have now

```json
{
 "expensive": {
  "available": false,
  "detail": "not attempted: the enumerative development decides every state in the kernel and this level has about an unknown number of them (ceiling 200000). The pagoda development is the alternative and needs a LINE world plus an lp_potential certificate; this is a grid world with no state graph.",
  "ok": false,
  "state_estimate": null
 },
 "first_divergence": {
  "arc_action": "ACTION1",
  "cells": [
   {
    "cell": [
     53,
     62
    ],
    "manual_says": 2,
    "world_says": 3
   }
  ],
  "cells_wrong": 1,
  "kind": "frame_mismatch",
  "t": 7
 },
 "proof_layer_available": false,
 "replay": {
  "detail": "7/9 transitions replay exactly",
  "matched": 7,
  "ok": false,
  "transitions": 9
 },
 "responsibility": {
  "cells_unexplained": 0,
  "detail": "every pixel of frame 0 belongs to the board or to an object",
  "ok": true,
  "total_cells": 4096
 },
 "unambiguous": {
  "actions": 5,
  "cap_reached": false,
  "clashes": [],
  "detail": "no (state, action) among 10 x 5 admitted two rules, and all 50 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 50,
  "pairs_nominal": 50,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 10,
  "states_reconstructed": 10,
  "step_crashes": {
   "by_phase": {},
   "by_type": {},
   "count": 0,
   "note": "`step` is documented total and its only declared exception, AmbiguousTransition, is a constraint-9 violation which is counted as a clash rather than here. Anything counted here is a bug in the compiled manual, and each one removed a pair from adjudication while leaving it inside the nominal coverage.",
   "sample_cap": 8,
   "samples": [],
   "site": "certify._ambiguity: step(state, action)"
  }
 }
}
```

## The compiler refused your last manual

This is not a style complaint. The manual did not compile, so it has no executable form and nothing downstream can run. Fix the named clause; do not work around it by deleting the content unless the content really is inexpressible, in which case say so with an `E-` entry in the log.

```json
{
 "reply": "the reply carried no === THEORY === block; emit all three blocks"
}
```


# What to reply

Reply with EXACTLY three blocks, in this order, and nothing else outside them.

=== THEORY ===
```
<the whole of theory.dsl, not a diff>
```

=== PLAYBOOK ===
```
<the whole of playbook.dsl, not a diff. If you have nothing defensible to say
yet, emit only comment lines -- an empty playbook is honest, an invented one is
not.>
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "obj0 (colour 6)", "verdict": "accept",
   "as": "Cart", "why": "one sentence of reasoning a reader could check
   against the candidate stream alone"},
  {"id": "R-01", "subject": "obj0_step_UP", "verdict": "probe-pending",
   "why": "..."}
]
```

`verdict` is one of: accept, reject, entailed, probe-pending.
Use `id` prefixes O- for objects, R- for rules, L- for laws, P- for probes,
E- for a thing the DSL cannot express (say what you wanted and what you wrote
instead).

```

## reply

```
=== THEORY ===
```
# theory.dsl -- fifth edition.
#
# ZEROTH, THE FAILURE THAT COST THE LAST ROUND. My previous reply carried no
# === THEORY === block at all, so nothing compiled and nothing downstream ran.
# That was a harness failure, not an expressibility failure, and it is logged
# as E-00. Everything below is emitted whole.
#
# WHAT THIS ROUND BOUGHT. Four commands (t10 A2, t11 A1, t12 A2, t13 A1) and
# four probe reports, and between them they KILL MY CLOCK and confirm my
# census to the cell.
#
# 1. I DATED A PREDICTION AND IT DIED. Last edition, in writing: "commands 10
#    and 11 leave row 53 alone, command 12 turns (53,61) from 2 to 3." The
#    world ticked at COMMAND 11 and left row 53 alone at 10, 12 and 13. t11's
#    diff spans rows 30-53 cols 11-61: 72 widget cells plus (53,61). The
#    meter has now advanced at commands 4, 8 and 11 -- intervals 4, 4, 3 --
#    and the period-4 command clock is REFUTED by the prediction I wrote so
#    that it could be. I killed it myself rather than re-fitting it, and the
#    replacement is smaller, not larger. See
#    the_period_four_clock_is_refuted_and_i_dated_the_prediction_that_died.
#
# 2. THE TICK IS NOT A FUNCTION OF THE FRAME, AND THAT IS NOW PROVEN, NOT
#    SUSPECTED. S5 and S7 are the SAME frame (the store's distinct_states = 10
#    over 14 states needs exactly the four coincidences S0=S2, S5=S7, S8=S9,
#    S11=S13, and I can read all four off the diffs). ACTION1 in S5 changed 72
#    cells and no meter cell; ACTION1 in S7 changed 73, the extra being
#    (53,62). Same frame, same key, different successor. No guard over cells
#    and colours -- not a counter, not any length of `above` chain -- can
#    separate them, because there is nothing in the frame to separate. This is
#    stronger than last edition's "the guard language has no counter": even a
#    counter would not be enough. I own the meter cells and I cannot draw
#    them, permanently, and I now know why rather than merely that.
#
# 3. THE PROBE HASHES LOCATED THE TICK WITHOUT A SINGLE NEW RULE. Two ACTION2
#    probes fired from visibly identical W1 states (P-05 at t10, P-07 at t12):
#    the manual predicted the same hash both times and the world answered
#    DIFFERENTLY (3bf51d2f vs b278887e), because S10 and S12 differ at exactly
#    (53,61). Two ACTION1 probes from W0 (P-06 at t11, P-08 at t13): the world
#    answered IDENTICALLY (5ad40f81 twice), because S11 = S13. Both facts are
#    entailed by a tick at t11 and by no other placement of it. The probe tier
#    confirmed my reconstruction while believing it was refuting my manual.
#
# 4. THE CENSUS GREW BY EXACTLY ONE CELL AND THREE STORE COUNTS MOVED WITH IT.
#    dynamic_cells 98 -> 99, cells_needing_an_owner 74 -> 75, constant_cells
#    3998 -> 3997. The one new dynamic cell is (53,61), whose frame-0 colour is
#    2, so it joins BarCore by colour alone and BarCore goes 11 -> 12. The
#    census: 24 Field + 8 BarBody + 12 BarCore + 12 Blank + 22 Frame +
#    12 Hollow + 9 Dot = 99, and 99 - 24 = 75 because Field is the one type
#    whose frame-0 colour is the background. Three independent store numbers
#    land on the type table without adjustment.
#
# 5. A THEOREM OF MINE IS REFUTED BY ITS OWN WORDING AND I HONOUR IT. I wrote
#    that a probe still refuting every hypothesis INCLUDING inert would refute
#    the_vacuous_probes_were_replay_damage. P-06 did exactly that. The
#    mechanism it points at is the tick at t11 -- a mechanism I have declared
#    and cannot state as a rule -- but the wording was mine and the theorem
#    goes down. It is replaced by a narrower one that does not promise what a
#    hash can settle.
#
# WHERE I AM. S13 = S11 = W1, read straight off the current frame: hollow box
# in the TOP slot (rows 30-35 cols 11-16, border 6, interior 0, 2x2 core of 6
# at rows 32-33 cols 13-14, ports 1 at (32,16) and 2 at (33,16)); bar in the
# BOTTOM slot rendered four rows only (36-39 at cols 13-14, 3,3/3,3/2,2/2,2,
# rows 40-41 background); both readouts blank; (53,61), (53,62), (53,63) all 3.
# Thirteen commands since RESET.
#
# WHAT I STILL HAVE NOT SEEN, AFTER FOURTEEN STATES. ACTION1 pressed in W1.
# ACTION2 pressed in W0. ACTION4 pressed in W1. ACTION5 and ACTION6 pressed at
# all. A GameState other than NOT_FINISHED. Any cell outside rows 30-41 and
# row 53 changing. The probe tier has now spent four consecutive commands on
# the two keys I already model, for reasons the playbook now names.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Field    { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object BarBody  { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object BarCore  { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Blank    { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Frame    { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  object Hollow   { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Dot      { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark bottom_port                          # arc-cell: (38, 16)
  Field   [segment: dynamic_colour_5 ev: t0-t13 compress: 24]
  BarBody [segment: dynamic_colour_3 ev: t0-t13 compress: 8]
  BarCore [segment: dynamic_colour_2 ev: t0-t13 compress: 12]
  Blank   [segment: dynamic_colour_4 ev: t0-t13 compress: 12]
  Frame   [segment: dynamic_colour_6 ev: t0-t13 compress: 22]
  Hollow  [segment: dynamic_colour_0 ev: t0-t13 compress: 12]
  Dot     [segment: dynamic_colour_1 ev: t0-t13 compress: 9]

events:
  event recolored(o, c)

rules:
  rule k1_field_to_frame forall ?p in Field [ev: t1,t6,t8,t11,t13 cov: 14/14]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_field_to_hollow forall ?p in Field [ev: t1,t6,t8,t11,t13 cov: 8/8]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_field_to_dot forall ?p in Field [ev: t1,t6,t8,t11,t13 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_field_to_core forall ?p in Field [ev: t1,t6,t8,t11,t13 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_bar_to_frame forall ?p in BarBody [ev: t1,t6,t8,t11,t13 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_bar_to_hollow forall ?p in BarBody [ev: t1,t6,t8,t11,t13 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_core_to_frame forall ?p in BarCore [ev: t1,t6,t8,t11,t13 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(above(above(?p)), 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_blank_to_dot forall ?p in Blank [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_blank_to_core forall ?p in Blank [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_frame_to_field forall ?p in Frame [ev: t1,t6,t8,t11,t13 cov: 14/14]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_frame_to_bar forall ?p in Frame [ev: t1,t6,t8,t11,t13 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_clears forall ?p in Frame [ev: t1,t6,t8,t11,t13 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_frame_to_core forall ?p in Frame [ev: t1,t6,t8,t11,t13 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1,t6,t8,t11,t13 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1,t6,t8,t11,t13 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_hollow_clears forall ?p in Hollow [ev: t1,t6,t8,t11,t13 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_dot_to_field forall ?p in Dot [ev: t1,t6,t8,t11,t13 cov: 1/1]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_dot_to_blank forall ?p in Dot [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k1_core_to_field forall ?p in BarCore [ev: t1,t6,t8,t11,t13 cov: 1/1]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_core_to_blank forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k2_field_from_frame forall ?p in Field [ev: t2,t7,t10,t12 cov: 14/14]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_hollow forall ?p in Field [ev: t2,t7,t10,t12 cov: 8/8]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_dot forall ?p in Field [ev: t2,t7,t10,t12 cov: 1/1]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_core forall ?p in Field [ev: t2,t7,t10,t12 cov: 1/1]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_bar_from_frame forall ?p in BarBody [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_from_hollow forall ?p in BarBody [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_regrows_from_hollow forall ?p in BarBody [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_bar_regrows_from_frame forall ?p in BarBody [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_core_from_frame forall ?p in BarCore [ev: t2,t7,t10,t12 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k2_blank_from_dot forall ?p in Blank [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_blank_from_core forall ?p in Blank [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_frame_from_field forall ?p in Frame [ev: t2,t7,t10,t12 cov: 16/16]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2,t7,t10,t12 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2,t7,t10,t12 cov: 10/10]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_dot_from_field forall ?p in Dot [ev: t2,t7,t10,t12 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_dot_from_blank forall ?p in Dot [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_core_from_field forall ?p in BarCore [ev: t2,t7,t10,t12 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k2_core_from_blank forall ?p in BarCore [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k3_dot_blanks forall ?s in Dot [ev: t3 cov: 8/8]
    when act=key(3) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k3_core_blanks forall ?s in BarCore [ev: t3 cov: 4/4]
    when act=key(3) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k4_dot_lights forall ?s in Dot [ev: t4 cov: 8/8]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 1)

  rule k4_core_lights forall ?s in BarCore [ev: t4 cov: 4/4]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 2)

  rule meter_first_tick_replay_patch forall ?s in BarCore [ev: t4 cov: 1/1]
    when act=key(4) and colored(?s, 2) and rightof(?s) = wall then recolored(?s, 3)

  rule k7_dot_blanks forall ?s in Dot [ev: t5 cov: 8/8]
    when act=key(7) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k7_core_blanks forall ?s in BarCore [ev: t5 cov: 4/4]
    when act=key(7) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

laws:
  invariant field_instances count(Field) = 24 [status: census, and 99 minus 24 is exactly cells_needing_an_owner = 75]
  invariant barbody_instances count(BarBody) = 8 [status: census, unchanged this round]
  invariant barcore_instances count(BarCore) = 12 [status: census, grew by one when (53,61) became dynamic at t11]
  invariant blank_instances count(Blank) = 12 [status: census, unchanged this round]
  invariant frame_instances count(Frame) = 22 [status: census, re-counted in the current frame: 18 ring cells plus a 2x2 core]
  invariant hollow_instances count(Hollow) = 12 [status: census, re-counted in the current frame]
  invariant dot_instances count(Dot) = 9 [status: census, unchanged this round]
  invariant board_cells count(board) = 3997 [status: matches constant_cells exactly, one lower than last round]
  invariant total_owned_cells count(Field) + count(BarBody) + count(BarCore) + count(Blank) + count(Frame) + count(Hollow) + count(Dot) = 99 [status: matches dynamic_cells exactly]

  theorem the_period_four_clock_is_refuted_and_i_dated_the_prediction_that_died "Last edition I wrote, before these four commands ran: commands 10 and 11 leave row 53 alone, command 12 turns (53,61) from 2 to 3. The world ticked at COMMAND 11 -- t11's diff spans rows 30-53 and cols 11-61, which is 72 widget cells plus (53,61), the only row-53 cell in range -- and commands 10, 12 and 13 left row 53 untouched. Three ticks now: command 4 on (53,63), command 8 on (53,62), command 11 on (53,61), intervals 4, 4, 3. The period is dead and I killed it with my own dated prediction rather than re-fitting it. I then checked every counter I can compute from the log WITHOUT SPENDING A COMMAND, and all of them fail: swap presses give 2, 5, 7; two-frame commands give 4, 7, 9; commands that changed a cell give 4, 8, 10; cumulative frames give 8, 15, 20; entries into W1 give the 3rd and 4th of five. Not one is periodic. What survives is a WALL-CLOCK reading -- a timer ticking in real time, which lands 4, 4, 3 commands apart because my thinking time is not constant -- and I hold it loosely, because it is the reading that explains a drift rather than a law."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help "This is the strongest negative result in the file and it is now proven rather than suspected. S5 and S7 are the SAME FRAME: the store's distinct_states = 10 over 14 states is exhausted by exactly four coincidences, S0 = S2, S5 = S7, S8 = S9, S11 = S13, and I can read all four straight off the diffs. ACTION1 pressed in S5 changed 72 cells and no meter cell; ACTION1 pressed in S7 changed 73, the extra being (53,62) 2 to 3. Same frame, same key, different successor. Last edition I said the tick could not be written because the guard language has no counter; that was too weak. NO GUARD OVER THE FRAME CAN WRITE IT AT ALL, counter or not, because the two states that disagree are pixel-identical and a guard has nothing else to look at. My compiled step is a function of the frame, so it is WRONG on the meter and must stay wrong. I own those cells -- they are BarCore instances by colour -- and I will never draw them. The cost is bounded and stated: replay carries 1 wrong cell from transition 7 and 2 from transition 10."
    [probe: passed]

  theorem the_probe_hashes_locate_the_tick_without_a_single_new_rule "The four probe reports are hashes only, but their pattern is decisive. P-05 (ACTION2, t10) and P-07 (ACTION2, t12) fired from W1 states whose widgets are identical: my manual predicted the SAME hash 05615f3d5f835100 in both, and the world answered DIFFERENTLY, 3bf51d2fd9036a78 then b278887e087d3593. Two visibly-alike starting states with different successors under one key means they were not alike, and (53,61) is the only cell that can differ. P-06 (ACTION1, t11) and P-08 (ACTION1, t13) answered IDENTICALLY, 5ad40f81cb8da5dd twice, which says S11 = S13 and that no tick occurred at t13. A tick at t11 and nowhere else in t10-t13 entails both facts; no other placement does. The probe tier confirmed my reconstruction of the clock while reporting that it had refuted my manual."
    [depends: the_period_four_clock_is_refuted_and_i_dated_the_prediction_that_died  probe: passed]

  theorem the_vacuous_probe_theorem_is_refuted_by_its_own_wording "I wrote last edition: a probe that still refutes every hypothesis including inert is evidence of a mechanism I have not stated, and this theorem is refuted. P-06 did exactly that -- 59 hypotheses, 0 survivors, inert included, 0.0 bits against 1.925 expected -- so the_vacuous_probes_were_replay_damage IS REFUTED and I strike it rather than reinterpret it. The mechanism it points at is the tick at t11, which I have declared and cannot write; that is an explanation, not a rescue, because my wording promised refutation on this observation and the promise binds. What replaces it is narrower and does not promise what a hash can settle: A PROBE GOES VACUOUS EXACTLY WHEN THE WORLD TICKS. P-06 is the one probe of four whose command ticked and the one probe of four with zero survivors; the other three had two survivors each. That is falsifiable in one line: a vacuous probe on a command that leaves row 53 alone refutes it, and would be the first real evidence of a widget mechanism I have not stated."
    [depends: the_probe_hashes_locate_the_tick_without_a_single_new_rule  probe: pending]

  theorem the_probe_tier_is_being_paid_in_clock_noise "Three probes reported 4.882643 bits of realised gain, which is log2(59/2) exactly, and every one of them was an ACTION1 or ACTION2 press in a configuration I already model to the cell -- the diffs confirm it: 72 cells, rows 30-41, cols 11-16, exactly what my k1 and k2 rules draw. The gain is not about the widget. It is manufactured by row 53: my replayed state has the meter cells wrong by construction, so my predicted hash CANNOT match, so every modelled command scores as maximally informative forever. The ranker has therefore locked onto the two keys I understand and has spent four consecutive commands there, while ACTION5 and ACTION6 remain unpressed after fourteen states and ACTION1-in-W1 remains unwitnessed after five ACTION1 presses. This is a systematic defect in what the arm can buy, not a run of bad luck, and it is the reason the playbook now prunes any probe whose whole divergence lies on the clock frontier."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: pending]

  theorem the_census_grew_by_exactly_one_cell_and_three_store_counts_moved_with_it "dynamic_cells 98 to 99, cells_needing_an_owner 74 to 75, constant_cells 3998 to 3997. One cell left the board this round and it is (53,61), whose frame-0 colour is 2, so the arm hands it to BarCore without my writing anything -- arc-instances: all covers every colour-2 cell the board cannot explain. The type table absorbs it with one number changed: 24 Field + 8 BarBody + 12 BarCore + 12 Blank + 22 Frame + 12 Hollow + 9 Dot = 99. The second decomposition still holds: 99 - 24 = 75 = cells_needing_an_owner, because Field is the single type whose frame-0 colour IS the background, so the store does not count it as needing an owner and I do. Three store numbers moved by exactly the amount one new cell requires, and I re-counted Frame at 22 and Hollow at 12 off the current frame by hand rather than trusting last round's figure."
    [probe: passed]

  theorem exchange_versus_scroll_is_still_open_and_i_am_standing_where_it_can_be_asked "READING A, exchange: two 6-row slots trade images, ACTION1 and ACTION2 are the same swap, and the bar simply renders four rows in the bottom slot. READING B, scroll: a list steps by six rows, ACTION1 is one direction and ACTION2 the other, and the four-row glyph in W1's bottom is a THIRD item. Nine swap commands are now observed -- A1 at t1, t6, t8, t11, t13 and A2 at t2, t7, t10, t12 -- and EVERY ACTION1 was pressed in W0 and EVERY ACTION2 in W1. ACTION1 HAS STILL NEVER FOLLOWED ACTION1 after fourteen states, so the discriminating press is still unmade and I am still standing in W1 where it costs one command instead of two. One new piece of evidence tilts me to A rather than B: row 29 shows 5,5,3,3,5,5 at cols 11-16 and has NEVER CHANGED in fourteen states. Under B a scroll window's top row must change when the list steps; under A row 29 is a static header above two slots. That is evidence, not taste, and it is the first I have had. It does not close the question, because a scroll whose window begins at row 30 would look the same."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem the_bar_is_six_rows_above_and_four_below_in_both_directions "The bar reads 3,3 / 3,3 / 2,2 / 2,2 / 3,3 / 3,3 down rows 30-35 at cols 13-14 in the top slot, and 3,3 / 3,3 / 2,2 / 2,2 down rows 36-39 in the bottom, with rows 40-41 background -- re-read off the current frame this round. Going down, the last two rows CLEAR; coming up they REGROW as 3, which is what the two k2 regrowth rules draw and what three further ACTION2 presses (t7, t10, t12) have now witnessed without a single replay complaint. The box, by contrast, renders 22 frame cells and 12 hollow cells in either slot without loss. So the swap is not an information-preserving exchange of two 6x6 windows: the bottom slot is lossy for the bar and the loss is restored from nowhere visible. Every swap since the readouts went dark has moved exactly 72 cells, which is the full 12x6 window, so no cell of that window is ever left standing."
    [probe: passed]

  theorem the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence "At t1 the LIT readout travelled with the box from rows 38-39 to rows 32-33 -- twelve cells of pattern moved six rows in the step the box did -- and the current frame confirms it from the other side: in W1 the port pixels read 1 at (32,16) and 2 at (33,16), six rows above their W0 seats. So the readout is bound to the box, not to the slot, and that is why every swap since t2 has moved 72 cells rather than 96: both readouts are dark, so their cells agree in both configurations and nothing visible moves. ACTION4 has been pressed exactly once, in W0, where bottom_port = (38,16) is 1. Unguarded, my k4 rules would light a strip the box has left whenever they were pressed in W1: 24 cells drawn confidently wrong. The guard colored(bottom_port, 1) makes them fire on nothing there, so my manual is SILENT about ACTION4 in W1. That silence is a declared gap, not a claim."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem barcore_is_five_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on the 4-cell core of the bar, the lower port pixel (39,16), four dots of the readout, and now THREE meter cells, (53,61) (53,62) (53,63). Twelve instances, one type, because the arm looks objects up by colour alone. The separators are all cells I have read: the bar core has colour 3 two rows above; the readout cores have a colour-1 dot immediately left; the port has colour 0 to its left; the frame-0 meter tip is the only instance whose rightof is off-board. I re-checked every rule in this file against the new instance (53,61): its left neighbour is 2, its right neighbour is not a wall, two rows above it is background, and no k2 or k4 guard matches a colour-2 cell there -- so no rule of mine grounds on it in any state, which is exactly why it can be wrong in replay without contaminating anything else. Three cells I own, cannot move, and have proven unwritable."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem the_swap_rules_are_forty_and_constraint_three_is_still_failed "One law -- take the colour of the cell six away -- is forty rules. recolored takes an INTEGER LITERAL, so a target colour cannot be read out of a cell and must be named, and the law splits once per source colour, per target colour, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I will not dress that up: forty rules to explain 72 cells twice over is worse than a lookup table, and I keep it only because the alternative is 96 unexplained pixels. What buys part of it back is that a TYPE IS A FRAME-0 COLOUR, so a rule's source colour already says which half of the widget the instance lives in, and only the four truncation and regrowth rules need geometry on top. The consequence that drives the playbook is unchanged and now matters more: every k1 rule demands that its instance still wears its frame-0 colour, true only in W0, so the whole family is silent in W1 BY CONSTRUCTION rather than by evidence, and five ACTION1 presses have all been in W0."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: passed]

  theorem no_goal_section_and_this_is_a_refusal_i_can_now_price "With no goal, is_goal is False everywhere, plan never returns sat, commit never runs, and every command is a probe. I accept that and still decline, for arithmetic. Fourteen states have returned NOT_FINISHED and no other GameState has ever been seen, so no observation distinguishes a win. The pos form is dead: nothing here moves, every rule is a recolour, and cegis_miner refuses every track for that reason. That leaves counts, and this round I found the one count that LOOKS like progress and then found why it cannot be written. The meter fills row 53 from the right, three cells so far, so the natural goal is the meter full -- but the un-ticked meter cells are cells that have never changed, which makes them BOARD, not instances, so count(BarCore, color = 3) can never exceed 12 and 9 of those 12 are widget cells that have nothing to do with the meter. The goal language cannot name a cell that is not yet an object. Logged as E-02. Every other count I can write names a configuration, and count(BarCore, color = 3) = 3 IS TRUE RIGHT NOW. A false goal converts a probe budget into a confident wrong plan, which is strictly worse than silence. WHAT ENDS THIS IS AN OBSERVATION: a GameState other than NOT_FINISHED, or any cell outside rows 30-41 and row 53 changing at all. ACTION5 and ACTION6 have never been pressed in fourteen states and are the cheapest place to look."
    [depends: the_probe_tier_is_being_paid_in_clock_noise  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where nothing fires I assert identity in the same voice I use for what I watched. Audit at S13 = W1, both readouts blank. ACTION2: fully predicted, 72 cells, witnessed here four times, the one action my manual draws in this configuration. ACTION3: witnessed inert here at t9. ACTION7: entailed inert by k3's watched twin, unwitnessed in W1, and I believe it. ACTION1: STILL PREDICTED SILENT ON ZERO WITNESSES after fourteen states, and this remains my largest forgery -- 20 rules and one structural reading ride on it, and the silence is an artefact of every k1 guard demanding a frame-0 colour, so it is a property of my rule-writing rather than a claim about the world. I expect to be wrong and I want to be. ACTION4: predicted silent because bottom_port is 5 here; a declared gap chosen over a wrong drawing. ACTION5, ACTION6: predicted silent, never pressed, no witness of any kind. And every one of these omits the meter: whichever key is pressed, (53,60) may turn 3 on it and I cannot draw that. A probe ranker prices a predicted identity at zero, and now also pays 4.88 bits for the clock cells, so the two effects push in the same direction -- THE COMMANDS I MOST NEED ARE THE ONES THE RANKER WILL NEVER BUY."
    [depends: exchange_versus_scroll_is_still_open_and_i_am_standing_where_it_can_be_asked, the_probe_tier_is_being_paid_in_clock_noise  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3997 constant cells, not just naming them board. A colour-4 panel fills rows 29-41 from col 17 to col 46 and carries a 4x4 block of colour 14 at rows 31-34, cols 42-45 -- the only colour-14 anywhere and the only structure on the panel. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them and why every mdl_segmenter blob is a 13x36 slab. Row 29 shows 5,5,3,3,5,5 at cols 11-16 and has NEVER changed in fourteen states: the bar reads seven rows tall on screen while only six of it is alive, and that unchanging row is now doing real work as evidence against the scroll reading. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the meter: colour 2 from col 10 to col 60, colour 3 at cols 61, 62, 63. Row 54 is a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "The candidate excerpt I received this round is cegis_miner and nothing else, and cegis_miner refuses every track: transitions narrate vanish rather than move, objects are absent at frame 0, and where it does mine it reports NoSeparatingGuard on transitions 1 and 2. I take NO structure from it and I accept its verdict, which is the strongest negative result available here -- THIS WORLD DOES NOT NARRATE AS ONE MOVER, and a miner built for movers is right to refuse rather than to invent a mover. I explicitly do not repeat last round's mdl_segmenter frame-index witness as if it had been re-supplied; it was not shown to me this round and I will not cite a report I cannot see. The 2106-row proposal stream contains no named object and no rule I can check, so the honest accounting is that the engines contributed nothing to this edition and the four commands contributed all of it."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me, as the last one did. CERTIFY, next run: 7 of 13 transitions replay exactly, first divergence still t=7, still the single cell (53,62) manual 2 world 3; transitions 10 through 12 diverge by TWO cells, (53,62) and (53,61), inherited and not newly earned; responsibility 0 of 4096 unexplained with (53,61) now owned by BarCore; 0 ambiguity clashes. STATE: S13 = S11 = W1, box top, bar four rows bottom, both readouts blank, three meter cells lit. ACTION1 HERE: my manual says nothing changes; I say that is false, and I name the outcomes in advance -- 72 cells at rows 30-41 cols 11-16 returning W0 exactly means exchange and twenty rules generalise by symmetry, any configuration never seen before means scroll and my word_table is a two-item special case, and genuine silence would be the most surprising result of the run. ACTION2 HERE: exactly 72 cells, no readout cell, no row-53 cell. ACTION4 HERE: my manual says nothing changes; I expect the twelve cells at rows 32-33 cols 17-22 to light instead. ACTION5, ACTION6: never pressed in fourteen states; I predict only that whichever is pressed produces the largest single addition to this manual available. THE METER: I NAME NO COMMAND INDEX, because I have just been punished for naming one. I predict (53,60) turns 3 within the next five commands, that it does so under whatever key happens to be pressed including an inert one, and that the intervals between ticks continue to vary. If the next two ticks arrive exactly four commands apart, my period was right and my refutation of it was hasty."
    [depends: the_silences_i_assert_and_which_of_them_are_forged, no_goal_section_and_this_is_a_refusal_i_can_now_price  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: fifteen entries, fourteen commands (RESET, A1, A2, A3, A4, A7, A1,
# A2, A1, A3, A2, A1, A2, A1). I am in W1: hollow box in the TOP slot, bar
# four rows in the BOTTOM slot (36-39, rows 40-41 background), BOTH readouts
# blank, (53,61) (53,62) (53,63) all colour 3. 99 cells have ever changed; 96
# are the widget and 3 are the meter.
#
# WHAT CHANGED THIS ROUND.
#  * MY CLOCK DIED ON A DATED PREDICTION. I wrote that the third tick would
#    land on command 12; it landed on command 11. Ticks at 4, 8, 11. Every
#    counter I can compute from the log without spending a command fails to
#    fit -- swaps, two-frame commands, changed commands, cumulative frames,
#    W1 entries. A real-time timer survives. I name no command index again.
#  * THE TICK IS PROVEN UNWRITABLE, not merely inconvenient. S5 and S7 are
#    the same frame and ACTION1 ticks in one and not the other. No guard over
#    the frame can separate them, so the meter is a permanent, bounded, fully
#    located error in the manual: 1 wrong cell from transition 7, 2 from
#    transition 10.
#  * THE RANKER IS BEING PAID IN THAT ERROR. Three probes reported 4.88 bits
#    = log2(59/2) for pressing keys I already draw to the cell. The gain came
#    from row 53, which no hypothesis can ever get right, so ACTION1 and
#    ACTION2 now score as maximally informative FOREVER. Four consecutive
#    commands went there. This is a defect in what the arm can buy.
#  * THE PROBE HASHES CONFIRMED MY RECONSTRUCTION WHILE CLAIMING TO REFUTE
#    IT. Two ACTION2 probes from visibly identical W1 states got different
#    answers; two ACTION1 probes from W0 got identical ones. Only a tick at
#    t11 explains both.
#  * MY OWN VACUOUS-PROBE THEOREM IS REFUTED BY ITS OWN WORDING (P-06 went
#    vacuous). It is struck, not reinterpreted.
#
# THE QUESTION THAT ONLY THIS CONFIGURATION CAN ASK -- UNCHANGED, AND THAT IS
# THE POINT
#   ACTION1 has now been pressed FIVE times and every one was in W0. ACTION2
#   four times, every one in W1. ACTION1 HAS NEVER FOLLOWED ACTION1. Exchange
#   and scroll are both alive; row 29 never changing is the first evidence
#   against scroll and does not close it. In W1 one ACTION1 splits them:
#   exchange returns W0 exactly, scroll shows a configuration never seen.
#   Any command that leaves W1 makes the question cost two. I am in W1 now.
#
# THE TRAP THIS PLAYBOOK EXISTS TO DEFEAT, NOW WITH A SECOND JAW
#   Jaw one: every k1 rule demands its instance still wear its frame-0
#   colour, true only in W0, so my silence on ACTION1-in-W1 is an artefact of
#   rule syntax, and a ranker prices a predicted identity at ZERO.
#   Jaw two: the clock makes every command I DO model score 4.88 bits.
#   Both jaws push the same way -- toward re-pressing the two keys I
#   understand, forever. The single most informative command available is the
#   one the ranker can never buy, and it has now failed to buy it four times
#   running. That is why the list below is stated in prose and why the order
#   lines say it three ways.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in fifteen entries. Zero constraint.
#   * ACTION1 in W1, ACTION2 in W0, ACTION4 in W1: silences with no witness.
#   * The meter's driver. Not a function of the frame, not periodic in any
#     count I can do. It rides free on every command; it costs nothing to
#     watch and must never be paid for.
#   * The win condition. No GameState but NOT_FINISHED in fourteen states.
#     The meter is the only thing that looks like progress, and the goal
#     language cannot name its un-ticked cells because they are still board.
#     The plan tier's silence is a true report of my ignorance, and I would
#     rather report ignorance than hand the arm a goal it can reach.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * (53,62) is wrong in replay from transition 7 and (53,61) from
#     transition 10, permanently. Row-53 divergences buy nothing and must not
#     be scored as bits.
#   * ACTION1 here is predicted SILENT and I expect that to be wrong.
#   * ACTION4 here is predicted SILENT by a guard I added on purpose.
#   * ACTION2 here is predicted to the cell and repeats t7, t10 and t12.
#   * ACTION3 and ACTION7 here are predicted silent, ACTION3 witnessed silent.
#
# THE RANKED LIST
# 1. ACTION1, HERE, IN W1. Splits exchange from scroll, tests the largest
#    forged silence in the manual (20 rules), askable only from where I am
#    standing, three legible outcomes. Unbought for two rounds.
# 2. ACTION5 or ACTION6. Never pressed in fifteen entries. Any outcome is the
#    largest single addition available -- including nothing, which after t9 I
#    know how to read -- and it is the cheapest place a win condition could
#    come from.
# 3. ACTION4, HERE. Tests the guard and the readout-follows-box reading in one
#    press, and relights the readout so the readout rules can be re-witnessed
#    in the other configuration.
# 4. The meter is checked for free in the raw diff of whatever is pressed.
#    Never spend a command on it.
#
# WHAT NOT TO PRESS
#   ACTION2 here: drawn to the cell, witnessed four times, and its reported
#   bits are manufactured by row 53.
#   ACTION1 in W0: same, five witnesses.
#   ACTION3 here: witnessed inert in this exact state.
#   ACTION7 here: entailed inert by a watched twin.
#   Anything chosen because the report says 4.88 bits: that number is the
#   clock, not the world.

order     spend_a_probe_only_the_current_state_can_ask_before_one_askable_anywhere [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     test_a_silence_that_is_an_artefact_of_rule_syntax_before_any_other [proof: lean]
order     override_a_ranker_that_prices_every_predicted_identity_at_zero    [proof: lean]
order     discount_gain_earned_only_on_a_cell_the_manual_declared_undrawable [proof: lean]
order     recompute_reported_bits_from_survivor_counts_before_trusting_them [proof: lean]
order     suspect_the_scoring_channel_when_one_key_wins_four_rounds_running [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     date_a_prediction_by_index_so_a_wrong_period_can_be_killed        [proof: lean]
order     kill_a_fitted_period_the_moment_one_interval_breaks_it            [proof: lean]
order     test_every_counter_computable_from_the_log_before_spending_a_command [proof: lean]
order     prove_a_quantity_is_not_a_function_of_the_frame_before_guessing_its_guard [proof: lean]
order     find_two_identical_frames_with_different_successors_before_adding_a_rule [proof: lean]
order     honour_the_refutation_clause_you_wrote_into_your_own_theorem      [proof: lean]
order     strike_a_refuted_theorem_rather_than_reinterpret_it               [proof: lean]
order     count_a_coverage_figure_before_writing_it_down                    [proof: lean]
order     recount_a_state_census_against_the_store_before_drawing_from_it   [proof: lean]
order     let_a_new_dynamic_cell_join_the_type_its_frame_zero_colour_names  [proof: lean]
order     read_a_never_changing_row_as_evidence_about_structure             [proof: lean]
order     guard_a_rule_into_silence_before_letting_it_draw_an_unwitnessed_state [proof: lean]
order     rename_a_rule_that_survives_only_as_a_replay_patch                [proof: lean]
order     refuse_a_patch_that_buys_one_right_cell_with_three_wrong_ones     [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     cite_only_engine_reports_that_were_actually_supplied_this_round   [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     refuse_a_goal_no_observation_distinguishes_and_say_so_out_loud    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_over_a_quantity_shown_not_to_be_a_function_of_the_frame => dead [proof: lean]
prune     rule_that_would_fire_on_every_command_to_draw_a_cell_that_moves_on_one [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     period_fitted_to_two_ticks_and_broken_by_a_third => dead          [proof: lean]
prune     counter_that_fails_on_any_tick_already_in_the_log => dead         [proof: lean]
prune     divergence_lies_only_on_the_meter_frontier => dead                [proof: lean]
prune     divergence_a_later_transition_only_inherited_from_an_earlier_one => dead [proof: lean]
prune     divergence_the_previous_edition_named_by_cell_and_by_command => dead [proof: lean]
prune     probe_whose_reported_bits_are_all_earned_on_undrawable_cells => dead [proof: lean]
prune     probe_that_repeats_a_key_in_a_configuration_already_probed_twice => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     repeats_a_key_already_watched_doing_nothing_in_this_exact_state => dead [proof: lean]
prune     repeats_a_transition_already_witnessed_from_an_identical_frame => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     leaves_the_only_configuration_that_can_ask_the_open_question => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     goal_clause_over_a_cell_that_is_still_board => dead               [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     goal_no_observed_gamestate_could_have_distinguished => dead       [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic silences_that_follow_from_rule_syntax_rather_than_from_evidence   [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic questions_that_only_the_present_configuration_can_ask             [admissible: lean]
heuristic pairs_of_identical_frames_with_different_successors               [admissible: lean]
heuristic duplicate_state_pairs_the_store_count_requires_and_i_have_named   [admissible: lean]
heuristic counters_still_fitting_every_tick_in_the_log                      [admissible: lean]
heuristic reported_bits_that_survive_deleting_the_undrawable_cells          [admissible: lean]
heuristic consecutive_commands_spent_on_a_single_already_modelled_key       [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic rows_that_have_never_changed_and_constrain_a_structural_reading   [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic gamestates_other_than_not_finished_ever_returned                  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]

prefer    a_command_that_splits_two_named_readings_in_one_press             [ev: 1/1 available]
prefer    a_probe_askable_only_from_the_configuration_now_showing           [ev: 1/2 configurations]
prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 3/5 pressed keys]
prefer    a_command_that_tests_twenty_rules_at_once                         [ev: 2/2 available]
prefer    a_command_whose_outcome_the_manual_cannot_already_hash            [ev: 4/4 last probes failed this]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 3/15 entries]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 14/14 diffs]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 0/15 entries so far]
prefer    a_command_that_could_return_a_gamestate_never_yet_seen            [ev: 0/15 entries so far]
```

=== LOG ===
```json
[
  {"id": "E-00", "subject": "the compiler's refusal: reply carried no === THEORY === block", "verdict": "accept",
   "why": "Not an expressibility failure but a harness failure on my side: the previous reply omitted all three blocks, so nothing compiled and the round was lost. This reply emits THEORY, PLAYBOOK and LOG whole; the order line emit_every_required_block_before_polishing_any_of_them is kept at the bottom of the playbook for exactly this."},

  {"id": "O-01", "subject": "(53,61), the cell that stopped being board", "verdict": "accept",
   "as": "BarCore instance (no edit required)",
   "why": "dynamic_cells went 98 -> 99, constant_cells 3998 -> 3997, cells_needing_an_owner 74 -> 75; its frame-0 colour is 2 and BarCore already carries arc-instances: all, so the arm adopts it without a new declaration. Only the invariants move: barcore_instances 11 -> 12, board_cells 3998 -> 3997."},

  {"id": "O-02", "subject": "the seven-type table as a whole", "verdict": "accept",
   "why": "Re-counted by hand off the current frame this round, not carried over: 24 Field (rows 30-35, cols 11,12,15,16), 8 BarBody, 12 BarCore, 12 Blank, 22 Frame (18 ring + 4 core), 12 Hollow, 9 Dot = 99 = dynamic_cells, and 99 - 24 = 75 = cells_needing_an_owner because Field is the one type whose frame-0 colour is the background."},

  {"id": "L-01", "subject": "the_meter_is_a_clock_not_a_key (period four, command index)", "verdict": "reject",
   "why": "Refuted by its own dated prediction. I named command 12 for the third tick; the world ticked at command 11 (t11's diff spans rows 30-53, cols 11-61 = 72 widget cells plus (53,61)) and left row 53 alone at 10, 12 and 13. Ticks at 4, 8, 11 -- intervals 4, 4, 3."},

  {"id": "L-02", "subject": "every rival counter computable from the log", "verdict": "reject",
   "why": "Checked without spending a command, all against ticks at commands 4, 8, 11: swap presses give 2, 5, 7; two-frame commands give 4, 7, 9; commands that changed a cell give 4, 8, 10; cumulative frames give 8, 15, 20; entries into W1 give the 3rd and 4th of five. None is periodic. A wall-clock timer is the surviving reading and is held loosely."},

  {"id": "L-03", "subject": "the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help", "verdict": "accept",
   "as": "theorem [probe: passed]",
   "why": "distinct_states = 10 over 14 states is exhausted by S0=S2, S5=S7, S8=S9, S11=S13; S5 and S7 are therefore pixel-identical, and ACTION1 changed 72 cells in one and 73 in the other. No guard over the frame can separate identical frames, so the meter is unwritable in principle, not merely for want of a counter. This strictly strengthens and replaces last edition's guard-language argument."},

  {"id": "L-04", "subject": "the_probe_hashes_locate_the_tick_without_a_single_new_rule", "verdict": "accept",
   "as": "theorem [probe: passed]",
   "why": "P-05 and P-07 (both ACTION2, both from W1) share the manual's predicted hash 05615f3d5f835100 and differ in the world's answer (3bf51d2f vs b278887e), so their starting states differed; P-06 and P-08 (both ACTION1, both from W0) share the world's answer 5ad40f81 exactly, so S11 = S13. A tick at t11 and nowhere else in t10-t13 entails both."},

  {"id": "L-05", "subject": "the_vacuous_probes_were_replay_damage", "verdict": "reject",
   "why": "I wrote the refutation clause into it myself: a probe that refutes every hypothesis including inert refutes this theorem. P-06 did that (59 hypotheses, 0 survivors, 0.0 bits). It is struck rather than reinterpreted, and replaced by the narrower and still-falsifiable claim that a probe goes vacuous exactly when the world ticks -- true of 1 of 1 ticking probes and 0 of 3 non-ticking ones."},

  {"id": "L-06", "subject": "the_probe_tier_is_being_paid_in_clock_noise", "verdict": "accept",
   "as": "theorem [probe: pending]",
   "why": "Three probes reported exactly log2(59/2) = 4.882643 bits for pressing ACTION1 and ACTION2 in configurations my rules draw cell-perfectly (the diffs are 72 cells, rows 30-41, cols 11-16, every time). The divergence that earned those bits is in row 53, which no hypothesis in the frontier can ever get right, so both modelled keys score maximally informative forever. Four consecutive commands went there."},

  {"id": "L-07", "subject": "the_only_divergence_left_is_the_one_i_priced_in_advance", "verdict": "accept",
   "as": "folded into the two meter theorems",
   "why": "Certify again names (53,62) at t=7 and nothing else, exactly as priced. The refusal to patch stands and is now backed by a proof rather than a guard-language complaint: patching is impossible, not merely unprofitable."},

  {"id": "R-01", "subject": "the twenty k1 rules", "verdict": "accept",
   "as": "ev extended to t1,t6,t8,t11,t13",
   "why": "t11 and t13 are two further ACTION1 presses from W0, each changing the 72 cells of the 12x6 window and nothing else in the widget; no replay complaint touched a widget cell. Coverage figures unchanged because they count instances per firing, and I counted them rather than copying them."},

  {"id": "R-02", "subject": "the twenty k2 rules, including the two regrowth rules", "verdict": "accept",
   "as": "ev extended to t2,t7,t10,t12",
   "why": "t10 and t12 are two further ACTION2 presses from W1, 72 cells each. The regrowth pair (2/2 and 2/2) now has four witnesses and has never produced a replay divergence, which retires last round's four-cell defect for good."},

  {"id": "R-03", "subject": "k4_meter_tip_first_advance", "verdict": "accept",
   "as": "renamed meter_first_tick_replay_patch",
   "why": "Its causal claim -- that ACTION4 advances the meter -- is now refuted twice over (two later ticks under ACTION1, and one ACTION1 press that did not tick from an identical frame). It is kept solely because it reproduces t4's (53,63) in replay and can never fire again, since no BarCore instance with rightof = wall is colour 2 any more. The name now says what it is."},

  {"id": "R-04", "subject": "any rule for ACTION1 pressed in W1", "verdict": "reject",
   "why": "Zero witnesses after fourteen states: all five ACTION1 presses were in W0. Writing one would forge the reverse direction of an unobserved press. The manual's silence there is declared a forgery in prose instead."},

  {"id": "R-05", "subject": "cegis_miner's entire proposal stream", "verdict": "reject",
   "why": "Every track is refused (vanish narrations, object absent at frame 0) or dies on NoSeparatingGuard at transition 1 or 2. It offers no guard and no object I could check. I accept its refusal as the correct verdict -- nothing in this world moves, every rule here is a recolour -- and take no structure from it."},

  {"id": "E-01", "subject": "the meter tick", "verdict": "probe-pending",
   "why": "I wanted a rule that paints (53,60) next. There is no expression for it: not because the guard language lacks a counter, but because S5 and S7 are the same frame with different tick outcomes, so no function of the frame can decide it. Written as the theorem the_tick_is_not_a_function_of_the_frame instead, with the cost stated (1 wrong cell from transition 7, 2 from transition 10)."},

  {"id": "E-02", "subject": "a goal saying the meter is full", "verdict": "probe-pending",
   "why": "I wanted goal count(BarCore, color = 3) = 54, the meter filled across row 53. Un-ticked meter cells have never changed, so they are BOARD, not instances; count(BarCore, color = 3) cannot exceed 12 and 9 of those 12 are widget cells with nothing to do with the meter. The goal language cannot name a cell that is not yet an object. No goal section is emitted and the refusal is written out in no_goal_section_and_this_is_a_refusal_i_can_now_price."},

  {"id": "P-01", "subject": "certify, next run", "verdict": "probe-pending",
   "why": "Dated: 7 of 13 transitions exact, first divergence still t=7 on (53,62) alone, transitions 10-12 wrong by two cells ((53,62) and (53,61)) purely by inheritance, responsibility 0/4096 with (53,61) now owned, 0 ambiguity clashes. Any widget cell in the divergence set refutes this."},

  {"id": "P-02", "subject": "ACTION1 pressed here, in W1", "verdict": "probe-pending",
   "why": "The one press the arm has never made in fifteen entries and the only one that splits exchange from scroll. My manual predicts silence and I predict that silence is false. Three legible outcomes: 72 cells returning W0 exactly (exchange, twenty rules generalise), a configuration never seen (scroll, my word_table is a two-item special case), or genuine silence (the most surprising result of the run)."},

  {"id": "P-03", "subject": "ACTION5 or ACTION6", "verdict": "probe-pending",
   "why": "Never pressed in fourteen states; zero constraint of any kind; the cheapest place a GameState other than NOT_FINISHED, or a cell outside rows 30-41 and row 53, could come from -- and either of those is what ends my refusal to write a goal."},

  {"id": "P-04", "subject": "the next meter tick", "verdict": "probe-pending",
   "why": "I name no command index, having just been punished for naming one. Prediction: (53,60) turns 3 within five commands, under whatever key is pressed including an inert one, with intervals that keep varying. It rides free on every command and the playbook prunes spending one on it. If the next two ticks arrive exactly four apart, my refutation of the period was hasty."}
]
```
```
