# call-009-theorize-round1

model: `claude-opus-5` · 396162 ms · $1.305992 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 38518, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 38518, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 38518, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 38518, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 35725, "type": "message"}], "output_tokens": 35725, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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

## The playbook as it stands

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
  "detail": "7/13 transitions replay exactly",
  "matched": 7,
  "ok": false,
  "transitions": 13
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
  "detail": "no (state, action) among 14 x 5 admitted two rules, and all 70 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 70,
  "pairs_nominal": 70,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 14,
  "states_reconstructed": 14,
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
# theory.dsl -- sixth edition.
#
# WHAT THIS ROUND ACTUALLY BOUGHT: NOTHING FROM THE WORLD, AND I SAY SO FIRST.
# The store is identical to last round in every number I can check: states 14,
# steps 14, dynamic_cells 99, cells_needing_an_owner 75, constant_cells 3997,
# distinct_states 10, actions_used the same six. NO COMMAND WAS PRESSED. The
# round was spent re-certifying the manual I already had. Constraint 6 says the
# honest manual is small; a round with no new observation is a round in which
# the manual MUST NOT GROW A RULE, and this one does not. Every rule below is
# byte-identical to the fifth edition. What is new is verification I did by
# hand, and one repair I computed and then refused.
#
# 1. THE ONE SURPRISE IS THE ONE I PRICED, BY CELL AND BY TRANSITION INDEX.
#    replay_mismatch at t=7, ACTION1, one cell (53,62), manual 2, world 3. The
#    fifth edition said, in the manual and again in the playbook: "replay
#    carries 1 wrong cell from transition 7 and 2 from transition 10" and
#    "row-53 divergences buy nothing". I answer this surprise with an EXPLICIT
#    REFUSAL TO CHANGE, not with silence, and the refusal has arithmetic behind
#    it -- see the_only_repair_available_to_the_meter_makes_replay_worse.
#
# 2. I PREDICTED THE CERTIFY REPORT LINE BY LINE AND IT CAME BACK LINE BY LINE.
#    Written before I saw it: 7 of 13 replay exactly, first divergence t=7, the
#    single cell (53,62) manual 2 world 3, responsibility 0 of 4096, 0 ambiguity
#    clashes. Returned: 7/13, t=7, (53,62) 2 vs 3, 0/4096 unexplained, 0
#    clashes, 70/70 pairs adjudicated, 0 step crashes. Five for five, including
#    the prediction of my own permanent failure. That is what a dated prediction
#    is for, and last round the same device killed my clock.
#
# 3. NEW, AND CHECKED BY HAND: EVERY COVERAGE COLUMN SUMS TO ITS TYPE. I
#    re-derived all 40 swap coverages from the current frame rather than
#    trusting them, and each type's k1 rules and k2 rules each partition its
#    instances exactly -- Field 14+8+1+1 = 24, Frame 14+2+2+4 = 22 and
#    16+2+4 = 22, Hollow 8+2+2 = 12 and 10+2 = 12, BarBody 4+4 = 8 and
#    2+2+2+2 = 8, Dot 1+8 = 9, Blank 8+4 = 12, BarCore 4+1+4 = 9 of 12. The
#    ONLY deficit anywhere is BarCore's 3, and those 3 are the meter cells I
#    have proven unwritable. 96 of 99 owned cells are covered in both
#    directions, and 96 is exactly the largest diff ever observed (t1, t2).
#    The manual's silence is now located to the cell by arithmetic, not by
#    assertion. See every_coverage_column_sums_to_its_type.
#
# 4. THE CENSUS WAS RE-READ OFF THE CURRENT FRAME, NOT COPIED. Box in the TOP
#    slot: 22 sixes (6+2+3+3+2+6 down rows 30-35) and 12 zeroes, ports 1 at
#    (32,16) and 2 at (33,16). Bar in the BOTTOM slot, four rows only: 3,3/3,3
#    at rows 36-37 and 2,2/2,2 at rows 38-39, cols 13-14, rows 40-41
#    background. Row 53: colour 2 from col 10 to col 60, colour 3 at 61, 62,
#    63. 24+8+12+12+22+12+9 = 99 = dynamic_cells, and 99-24 = 75 =
#    cells_needing_an_owner.
#
# WHERE I AM. S13 = S11 = W1, thirteen commands since RESET, both readouts
# blank, three meter cells lit.
#
# WHAT I STILL HAVE NOT SEEN, AFTER FOURTEEN STATES AND TWO ROUNDS OF NOT
# BEING BOUGHT A COMMAND: ACTION1 pressed in W1. ACTION2 in W0. ACTION4 in W1.
# ACTION5 and ACTION6 at all. A GameState other than NOT_FINISHED. Any cell
# outside rows 30-41 and row 53 changing.

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
  invariant field_instances count(Field) = 24 [status: census, recounted by hand from the current frame this round]
  invariant barbody_instances count(BarBody) = 8 [status: census, recounted]
  invariant barcore_instances count(BarCore) = 12 [status: census, 4 bar core + 1 port + 4 readout cores + 3 meter]
  invariant blank_instances count(Blank) = 12 [status: census, the dark readout at frame 0]
  invariant frame_instances count(Frame) = 22 [status: census, 6+2+3+3+2+6 read down the box in the current frame]
  invariant hollow_instances count(Hollow) = 12 [status: census, 4+2+2+4 read down the box in the current frame]
  invariant dot_instances count(Dot) = 9 [status: census, 8 readout dots plus the upper port pixel]
  invariant board_cells count(board) = 3997 [status: matches constant_cells exactly, unchanged this round]
  invariant total_owned_cells count(Field) + count(BarBody) + count(BarCore) + count(Blank) + count(Frame) + count(Hollow) + count(Dot) = 99 [status: matches dynamic_cells exactly, unchanged this round]

  theorem a_round_passed_with_no_new_command_and_the_manual_must_not_grow "Every store number is identical to last edition: states 14, steps 14, distinct_states 10, dynamic_cells 99, cells_needing_an_owner 75, constant_cells 3997, actions_used the same six, dynamic_box the same. NO COMMAND WAS PRESSED THIS ROUND. Therefore there is no new evidence, therefore constraint 2 forbids a new rule, and every rule in this file is byte-identical to the fifth edition. I state this at the top because the temptation in a round like this is to pay for the round with invention, and invention with no witness is exactly what constraint 2 exists to stop. What I did instead was verification I could do without spending a command: I re-read the census off the current frame, I re-derived all forty coverage figures, and I computed the one repair the replay mismatch invites and rejected it with arithmetic."
    [probe: passed]

  theorem the_certify_report_was_predicted_line_by_line "Before seeing it I wrote: 7 of 13 transitions replay exactly, first divergence at t=7, the single cell (53,62) manual 2 world 3, responsibility 0 of 4096 unexplained, 0 ambiguity clashes. Certify returned 7/13, first divergence t=7 ACTION1, cells_wrong 1 at (53,62) manual 2 world 3, cells_unexplained 0 of 4096, n_clashes 0 with 70 of 70 pairs adjudicated and 0 step crashes. Five predictions, five hits, and one of them was a prediction of my own permanent failure. This is the second consecutive round in which a dated prediction decided something -- last round the dated one DIED and took my period-4 clock with it, this round it lived and confirms that the divergence set is closed. A manual that can forecast its own certify report has located its ignorance, which is the only thing an under-claiming manual can offer."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem the_only_repair_available_to_the_meter_makes_replay_worse "The replay_mismatch surprise demands an answer, so here is the answer with numbers. The only repair the guard language admits is propagation: a BarCore wearing colour 2 whose RIGHT NEIGHBOUR is 3 becomes 3. It needs no counter, it fits the observed left-to-right filling, and it is wrong. Under cascade single_frame it would fire on the very next command after each tick, so (53,62) would turn 3 at command 5 while the world turned it at command 8, and (53,61) at command 6 while the world turned it at command 11. Summing wrong-cell-transitions: TODAY the cost is (53,62) wrong across transitions 7-12 and (53,61) across 10-12, nine in all, and it is BOUNDED because no rule of mine ever grounds on a meter cell. WITH THE REPAIR it is about ten, AND IT IS UNBOUNDED: the wave keeps walking left into (53,60), (53,59) and onward, turning cells that have NEVER CHANGED -- cells that are board, not instances -- into confident wrong drawings, and each new tick restarts it. I refuse the repair. A patch that buys no right cell and spends the board is worse than a declared gap, and the playbook already prunes it in two lines."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem every_coverage_column_sums_to_its_type "New this round and checked by hand rather than copied. For each type, the k1 rules partition its instances and so do the k2 rules, exactly. Field 14+8+1+1 = 24 both ways. Frame 14+2+2+4 = 22 going down and 16+2+4 = 22 coming up, and I verified the 16 by reading the current frame: of the 22 frame-0 colour-6 positions, in W1 sixteen show background, two show 3 at row 36 cols 13-14, and four show 2 at rows 38-39 cols 13-14. Hollow 8+2+2 = 12 and 10+2 = 12. BarBody 4+4 = 8 and 2+2+2+2 = 8. Dot 1+8 = 9. Blank 8+4 = 12. BarCore 4+1+4 = 9 OF 12. That single deficit of 3 is the whole of my ignorance about the swap, and it is the three meter cells. So 96 of 99 owned cells are covered in BOTH directions, and 96 is exactly the largest diff the world has ever produced (t1 and t2, when the readout was lit). The manual's silence is now bounded by arithmetic instead of by assertion."
    [depends: the_swap_rules_are_forty_and_constraint_three_is_still_failed  probe: passed]

  theorem the_period_four_clock_is_refuted_and_i_dated_the_prediction_that_died "Last edition but one I wrote, before the commands ran: commands 10 and 11 leave row 53 alone, command 12 turns (53,61) from 2 to 3. The world ticked at COMMAND 11 and left row 53 alone at 10, 12 and 13. Three ticks: command 4 on (53,63), command 8 on (53,62), command 11 on (53,61), intervals 4, 4, 3. The period is dead and I killed it with my own dated prediction rather than re-fitting it. Every counter computable from the log WITHOUT SPENDING A COMMAND fails: swap presses give 2, 5, 7; two-frame commands give 4, 7, 9; commands that changed a cell give 4, 8, 10; cumulative frames give 8, 15, 20 and including RESET 9, 16, 21; entries into W1 give the 3rd and 4th of five. Not one is periodic. What survives is a WALL-CLOCK reading -- a timer ticking in real time, landing 4, 4, 3 commands apart because my thinking time is not constant -- and I hold it loosely, because it explains a drift rather than stating a law. No command ran this round, so this theorem gained no new evidence and lost none."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help "The strongest negative result in the file, and proven rather than suspected. S5 and S7 are the SAME FRAME: distinct_states = 10 over 14 states is exhausted by exactly four coincidences, S0 = S2, S5 = S7, S8 = S9, S11 = S13, and I re-derived all four from the diffs this round -- t1 then t2 undoes to S0; t6 then t7 undoes to S5; t9 changed nothing; t12 then t13 returns the widget to S11 with no row-53 change. ACTION1 pressed in S5 changed 72 cells and no meter cell; ACTION1 pressed in S7 changed 73, the extra being (53,62) 2 to 3. Same frame, same key, different successor. NO GUARD OVER THE FRAME CAN WRITE THAT, counter or not, because the two states that disagree are pixel-identical and a guard has nothing else to look at. My compiled step is a function of the frame, so it is WRONG on the meter and must stay wrong. The cost is bounded and located: 1 wrong cell from transition 7, 2 from transition 10, which is exactly what certify reported."
    [probe: passed]

  theorem the_probe_hashes_locate_the_tick_without_a_single_new_rule "From the round before this one, carried unchanged because no probe report was supplied this round and I cite only what I am shown. P-05 (ACTION2, t10) and P-07 (ACTION2, t12) fired from W1 states whose widgets are identical: my manual predicted the same hash both times and the world answered differently. Two visibly-alike starting states with different successors under one key means they were not alike, and (53,61) is the only cell that can differ. P-06 (ACTION1, t11) and P-08 (ACTION1, t13) answered identically, which says S11 = S13 and that no tick occurred at t13. A tick at t11 and nowhere else in t10-t13 entails both facts; no other placement does."
    [depends: the_period_four_clock_is_refuted_and_i_dated_the_prediction_that_died  probe: passed]

  theorem a_probe_goes_vacuous_exactly_when_the_world_ticks "Carried from last edition, still unadjudicated because no probe ran this round. P-06 was the one probe of four whose command ticked and the one probe of four with zero survivors; the other three had two survivors each. Falsifiable in one line: a vacuous probe on a command that leaves row 53 alone refutes it, and would be the first real evidence of a widget mechanism I have not stated. Its predecessor, the_vacuous_probes_were_replay_damage, was struck rather than reinterpreted when P-06 met the refutation clause I had written into it myself."
    [depends: the_probe_hashes_locate_the_tick_without_a_single_new_rule  probe: pending]

  theorem the_probe_tier_is_being_paid_in_clock_noise "Three probes reported 4.882643 bits of realised gain, which is log2(59/2) exactly, and every one was an ACTION1 or ACTION2 press in a configuration I already model to the cell. The gain is not about the widget: my replayed state has the meter cells wrong BY CONSTRUCTION, so my predicted hash cannot match, so every modelled command scores as maximally informative forever. The ranker locked onto the two keys I understand and spent four consecutive commands there; then a whole round passed in which NO COMMAND WAS PRESSED AT ALL. ACTION5 and ACTION6 remain unpressed after fourteen states and ACTION1-in-W1 remains unwitnessed after five ACTION1 presses. This is a systematic defect in what the arm can buy, not a run of bad luck, and it is why the playbook prunes any probe whose whole divergence lies on the clock frontier."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: pending]

  theorem exchange_versus_scroll_is_still_open_and_i_am_standing_where_it_can_be_asked "READING A, exchange: two 6-row slots trade images, ACTION1 and ACTION2 are the same swap, and the bar simply renders four rows in the bottom slot. READING B, scroll: a list steps by six rows, ACTION1 is one direction and ACTION2 the other, and the four-row glyph in W1's bottom is a THIRD item. Nine swap commands are observed -- A1 at t1, t6, t8, t11, t13 and A2 at t2, t7, t10, t12 -- and EVERY ACTION1 was pressed in W0 and EVERY ACTION2 in W1. ACTION1 HAS STILL NEVER FOLLOWED ACTION1, so the discriminating press is still unmade, and I am still standing in W1 where it costs one command instead of two. The evidence tilting to A: row 29 reads 5,5,3,3,5,5 at cols 11-16 and has NEVER changed in fourteen states, which a scroll window's top row should not survive -- unless the window begins at row 30, which is why this does not close the question."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem the_bar_is_six_rows_above_and_four_below_in_both_directions "The bar reads 3,3 / 3,3 / 2,2 / 2,2 / 3,3 / 3,3 down rows 30-35 at cols 13-14 in the top slot, and 3,3 / 3,3 / 2,2 / 2,2 down rows 36-39 in the bottom with rows 40-41 background -- re-read off the current frame again this round. Going down, the last two rows CLEAR; coming up they REGROW as 3, which is what the two k2 regrowth rules draw and what three further ACTION2 presses have witnessed without a replay complaint. The box, by contrast, renders 22 frame cells and 12 hollow cells in either slot without loss. So the swap is not an information-preserving exchange of two 6x6 windows: the bottom slot is lossy for the bar and the loss is restored from nowhere visible. Every swap since the readouts went dark has moved exactly 72 cells, the full 12x6 window, so no cell of that window is ever left standing."
    [probe: passed]

  theorem the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence "At t1 the LIT readout travelled with the box from rows 38-39 to rows 32-33 -- twelve cells of pattern moved six rows in the step the box did -- and the current frame confirms it from the other side: in W1 the port pixels read 1 at (32,16) and 2 at (33,16), six rows above their W0 seats. So the readout is bound to the box, not to the slot, which is why every swap since t2 has moved 72 cells rather than 96: both readouts are dark, so their 24 cells agree in both configurations. ACTION4 has been pressed exactly once, in W0, where bottom_port = (38,16) is 1. Unguarded, my k4 rules would light a strip the box has left whenever they fired in W1: 24 cells drawn confidently wrong. The guard colored(bottom_port, 1) makes them fire on nothing there, so my manual is SILENT about ACTION4 in W1. That silence is a declared gap, not a claim."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem barcore_is_five_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on the 4-cell core of the bar, the lower port pixel (39,16), four dots of the readout, and three meter cells (53,61) (53,62) (53,63). Twelve instances, one type, because the arm looks objects up by colour alone. The separators are all cells I have read: the bar core has colour 3 two rows above; the readout cores have a colour-1 dot immediately left; the port has colour 0 to its left; the frame-0 meter tip is the only instance whose rightof is off-board. No k1, k2, k3, k4 or k7 guard grounds on any meter cell in any state -- I re-checked this against every rule again this round, which is why those three cells can be wrong in replay without contaminating a single other cell, and why certify's divergence set is exactly the two cells I named."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem the_swap_rules_are_forty_and_constraint_three_is_still_failed "One law -- take the colour of the cell six away -- is forty rules. recolored takes an INTEGER LITERAL, so a target colour cannot be read out of a cell and must be named, and the law splits once per source colour, per target colour, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I will not dress that up: forty rules to explain 72 cells twice over is worse than a lookup table, and I keep it only because the alternative is 96 unexplained pixels. What buys part of it back is that a TYPE IS A FRAME-0 COLOUR, so a rule's source colour already says which half of the widget its instance lives in, and only the four truncation and regrowth rules need geometry on top. The consequence that drives the playbook is unchanged: every k1 rule demands that its instance still wear its frame-0 colour, true only in W0, so the whole family is silent in W1 BY CONSTRUCTION rather than by evidence, and five ACTION1 presses have all been in W0."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: passed]

  theorem no_goal_section_and_this_is_a_refusal_i_can_now_price "With no goal, is_goal is False everywhere, plan never returns sat, commit never runs, and every command is a probe. I accept that and still decline, for arithmetic. Fourteen states have returned NOT_FINISHED and no other GameState has ever been seen, so no observation distinguishes a win. The pos form is dead: nothing here moves, every rule is a recolour, and cegis_miner refuses every track for exactly that reason. That leaves counts, and the count that LOOKS like progress cannot be written: the meter fills row 53 from the right, so the natural goal is the meter full, but the un-ticked meter cells have never changed, which makes them BOARD rather than instances, so count(BarCore, color = 3) can never exceed 12 and 9 of those 12 are widget cells with nothing to do with the meter. The goal language cannot name a cell that is not yet an object. Logged as E-02. Every other count I can write names a configuration, and count(BarCore, color = 3) = 3 IS TRUE RIGHT NOW. A false goal converts a probe budget into a confident wrong plan, which is strictly worse than silence. WHAT ENDS THIS IS AN OBSERVATION: a GameState other than NOT_FINISHED, or any cell outside rows 30-41 and row 53 changing at all."
    [depends: the_probe_tier_is_being_paid_in_clock_noise  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where nothing fires I assert identity in the same voice I use for what I watched. Audit at S13 = W1, both readouts blank. ACTION2: fully predicted, 72 cells, witnessed here four times, the one action my manual draws in this configuration. ACTION3: witnessed inert here at t9. ACTION7: entailed inert by k3's watched twin, unwitnessed in W1, and I believe it. ACTION1: STILL PREDICTED SILENT ON ZERO WITNESSES, and this remains my largest forgery -- 20 rules and one structural reading ride on it, and the silence is an artefact of every k1 guard demanding a frame-0 colour, so it is a property of my rule-writing rather than a claim about the world. I expect to be wrong and I want to be. ACTION4: predicted silent because bottom_port is 5 here; a declared gap chosen over a wrong drawing. ACTION5, ACTION6: predicted silent, never pressed, no witness of any kind. And every one of these omits the meter: whichever key is pressed, (53,60) may turn 3 on it and I cannot draw that. A ranker prices a predicted identity at zero and pays 4.88 bits for the clock cells, so both effects push the same way -- THE COMMANDS I MOST NEED ARE THE ONES THE RANKER WILL NEVER BUY."
    [depends: exchange_versus_scroll_is_still_open_and_i_am_standing_where_it_can_be_asked, the_probe_tier_is_being_paid_in_clock_noise  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3997 constant cells, not just naming them board, and certify agrees at 0 of 4096 unexplained. A colour-4 panel fills rows 29-41 from col 17 to col 46 and carries a 4x4 block of colour 14 at rows 31-34, cols 42-45 -- the only colour-14 anywhere and the only structure on the panel. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them and why every mdl_segmenter blob is a 13x36 slab. Row 29 shows 5,5,3,3,5,5 at cols 11-16 and has never changed in fourteen states: the bar reads seven rows tall on screen while only six of it is alive. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the meter: colour 2 from col 10 to col 60, colour 3 at cols 61, 62, 63, re-read off the current frame. Row 54 is a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "The candidate excerpt supplied this round is cegis_miner and nothing else, and it is the SAME refusal profile as last round: every track either refused because the transition narrates vanish rather than move, or refused because the object is absent at frame 0, or mined to NoSeparatingGuard on transition 1 or 2. I take NO structure from it and I accept its verdict as the strongest negative result available here -- THIS WORLD DOES NOT NARRATE AS ONE MOVER, and a miner built for movers is right to refuse rather than invent one. The 2106-row stream contains no named object and no rule I can check. The honest accounting is that the engines contributed nothing to this edition, and since no command was pressed either, the only contributions this round are my own recount and my own rejected repair."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me, as one of these already has. CERTIFY, next run, unchanged if no command is pressed: 7 of 13 transitions replay exactly, first divergence t=7, single cell (53,62) manual 2 world 3, transitions 10-12 diverging by TWO cells inherited not newly earned, responsibility 0 of 4096, 0 clashes. STATE: S13 = W1, box top, bar four rows bottom, both readouts blank, three meter cells lit. ACTION1 HERE: my manual says nothing changes; I say that is false, and I name the outcomes in advance -- 72 cells at rows 30-41 cols 11-16 returning W0 exactly means exchange and twenty rules generalise by symmetry, any configuration never seen before means scroll and my word_table is a two-item special case, and genuine silence would be the most surprising result of the run. ACTION2 HERE: exactly 72 cells, no readout cell, no row-53 cell. ACTION4 HERE: my manual says nothing changes; I expect the twelve cells at rows 32-33 cols 17-22 to light instead. ACTION5, ACTION6: I predict only that whichever is pressed produces the largest single addition to this manual available. THE METER: I NAME NO COMMAND INDEX, because I was punished for naming one. I predict (53,60) turns 3 within the next five commands ACTUALLY PRESSED -- a round with no commands cannot adjudicate it and this round did not -- that it does so under whatever key happens to be pressed including an inert one, and that the intervals continue to vary."
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
# WHAT CHANGED THIS ROUND: NO COMMAND WAS PRESSED.
#   Every store number is identical to last round -- states 14, steps 14,
#   dynamic_cells 99, constant_cells 3997, distinct_states 10. The round was
#   spent re-certifying a manual that already forecast its own certify report.
#   That is the second failure mode this playbook now has to defend against.
#   Jaw one made the ranker re-press the keys I model; jaw two made it press
#   nothing at all. Both cost the same thing: the ONE question that only this
#   configuration can ask is still unasked, three rounds running.
#
# WHAT THE ROUND DID PRODUCE, WITHOUT SPENDING A COMMAND
#   * The certify report was predicted five for five, including the prediction
#     of my own permanent failure. The divergence set is closed: no unpriced
#     cell diverged anywhere in 13 transitions.
#   * All forty coverage figures re-derived by hand. Every type's k1 rules and
#     k2 rules each partition its instances exactly; the ONLY deficit is
#     BarCore 9 of 12, and those 3 are the meter. 96 of 99 covered both ways,
#     and 96 is the largest diff the world has ever produced.
#   * The one repair the mismatch invites -- meter propagates left when its
#     right neighbour is 3 -- was computed and REFUSED: it fires three
#     commands early, it does not reduce the wrong-cell total, and it walks
#     left into cells that are still board, unbounded. Arithmetic in the
#     manual.
#
# THE QUESTION THAT ONLY THIS CONFIGURATION CAN ASK -- UNCHANGED
#   ACTION1 has been pressed FIVE times and every one was in W0. ACTION2 four
#   times, every one in W1. ACTION1 HAS NEVER FOLLOWED ACTION1. Exchange and
#   scroll are both alive; row 29 never changing is evidence against scroll
#   and does not close it. In W1 one ACTION1 splits them: exchange returns W0
#   exactly, scroll shows a configuration never seen, silence would be the
#   most surprising outcome available. Any command that leaves W1 makes the
#   question cost two. I am in W1 now, and I have been in W1 for two rounds.
#
# THE TRAP THIS PLAYBOOK EXISTS TO DEFEAT, NOW WITH A THIRD JAW
#   Jaw one: every k1 rule demands its instance still wear its frame-0 colour,
#   true only in W0, so my silence on ACTION1-in-W1 is an artefact of rule
#   syntax, and a ranker prices a predicted identity at ZERO.
#   Jaw two: the clock makes every command I DO model score 4.88 bits.
#   Jaw three: a manual that correctly forecasts its own mismatch produces a
#   surprise report every round WITHOUT a command being pressed, and that
#   surprise can consume the round. A priced divergence is not news.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in fifteen entries. Zero constraint.
#   * ACTION1 in W1, ACTION2 in W0, ACTION4 in W1: silences with no witness.
#   * The meter's driver. Not a function of the frame -- two identical frames
#     disagree under the same key -- and not periodic in any count I can do.
#     It rides free on every command; it costs nothing to watch and must never
#     be paid for.
#   * The win condition. No GameState but NOT_FINISHED in fourteen states.
#     The goal language cannot name the un-ticked meter cells because they are
#     still board. The plan tier's silence is a true report of my ignorance.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * (53,62) is wrong in replay from transition 7 and (53,61) from
#     transition 10, permanently. Row-53 divergences buy nothing.
#   * ACTION1 here is predicted SILENT and I expect that to be wrong.
#   * ACTION4 here is predicted SILENT by a guard I added on purpose.
#   * ACTION2 here is predicted to the cell and repeats t7, t10 and t12.
#   * ACTION3 and ACTION7 here are predicted silent, ACTION3 witnessed silent.
#
# THE RANKED LIST -- UNCHANGED, BECAUSE NOTHING WAS OBSERVED THAT COULD
# CHANGE IT, AND CHANGING IT ANYWAY WOULD BE INVENTION
# 1. ACTION1, HERE, IN W1. Splits exchange from scroll, tests the largest
#    forged silence in the manual (20 rules, now known to cover 96 of 99
#    cells), askable only from where I am standing, three legible outcomes.
#    Unbought for three rounds.
# 2. ACTION5 or ACTION6. Never pressed in fifteen entries. Any outcome is the
#    largest single addition available -- including nothing, which after t9 I
#    know how to read -- and the cheapest place a win condition could come
#    from.
# 3. ACTION4, HERE. Tests the guard and the readout-follows-box reading in one
#    press, and relights the readout so the readout rules can be re-witnessed
#    in the other configuration.
# 4. The meter is checked for free in the raw diff of whatever is pressed.
#    Never spend a command on it.
#
# WHAT NOT TO PRESS, AND WHAT NOT TO DO INSTEAD OF PRESSING
#   ACTION2 here: drawn to the cell, witnessed four times, bits manufactured
#   by row 53. ACTION1 in W0: same, five witnesses. ACTION3 here: witnessed
#   inert in this exact state. ACTION7 here: entailed inert by a watched twin.
#   Anything chosen because the report says 4.88 bits: that is the clock.
#   AND: do not spend a round on certification alone. A surprise whose cells
#   the previous edition named by index is not a reason to re-open the manual.

order     press_something_rather_than_recertify_a_manual_that_forecast_itself [proof: lean]
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
order     answer_a_priced_surprise_with_a_stated_refusal_and_arithmetic     [proof: lean]
order     sum_the_wrong_cells_a_repair_would_cost_before_adopting_it        [proof: lean]
order     add_no_rule_in_a_round_that_bought_no_new_observation             [proof: lean]
order     verify_what_a_recount_can_settle_before_asking_the_world          [proof: lean]
order     date_a_prediction_by_index_so_a_wrong_period_can_be_killed        [proof: lean]
order     kill_a_fitted_period_the_moment_one_interval_breaks_it            [proof: lean]
order     test_every_counter_computable_from_the_log_before_spending_a_command [proof: lean]
order     prove_a_quantity_is_not_a_function_of_the_frame_before_guessing_its_guard [proof: lean]
order     find_two_identical_frames_with_different_successors_before_adding_a_rule [proof: lean]
order     honour_the_refutation_clause_you_wrote_into_your_own_theorem      [proof: lean]
order     strike_a_refuted_theorem_rather_than_reinterpret_it               [proof: lean]
order     count_a_coverage_figure_before_writing_it_down                    [proof: lean]
order     check_each_types_coverages_sum_to_its_instance_count              [proof: lean]
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
prune     rule_added_in_a_round_whose_store_counts_did_not_move => dead     [proof: lean]
prune     rule_over_a_quantity_shown_not_to_be_a_function_of_the_frame => dead [proof: lean]
prune     repair_that_does_not_reduce_total_wrong_cell_transitions => dead  [proof: lean]
prune     repair_whose_error_walks_into_cells_that_are_still_board => dead  [proof: lean]
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
heuristic coverage_deficits_between_a_types_rules_and_its_instance_count    [admissible: lean]
heuristic repairs_whose_wrong_cell_total_i_have_actually_summed             [admissible: lean]
heuristic counters_still_fitting_every_tick_in_the_log                      [admissible: lean]
heuristic reported_bits_that_survive_deleting_the_undrawable_cells          [admissible: lean]
heuristic consecutive_rounds_in_which_no_command_was_pressed                [admissible: lean]
heuristic consecutive_commands_spent_on_a_single_already_modelled_key       [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic rows_that_have_never_changed_and_constrain_a_structural_reading   [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic gamestates_other_than_not_finished_ever_returned                  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]

prefer    any_command_at_all_over_a_second_round_of_pure_certification      [ev: 1/1 rounds]
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
  {"id": "O-01", "subject": "cegis_miner tracks obj0-obj18 and the 2106-row stream", "verdict": "reject",
   "why": "Every track in the excerpt is either refused ('narrates vanish; only move/none are mined', 'object absent at frame 0') or mines to NoSeparatingGuard on transition 1 or 2, so the stream names no object and proposes no checkable rule; I accept its refusal as the correct negative result -- this world does not narrate as one mover -- and take no structure from it."},

  {"id": "O-02", "subject": "the seven frame-0 colour types (Field/BarBody/BarCore/Blank/Frame/Hollow/Dot)", "verdict": "entailed",
   "as": "unchanged word_table",
   "why": "Recounted by hand off the current frame this round rather than copied: box 22 sixes (6+2+3+3+2+6 down rows 30-35) and 12 zeroes, ports 1 at (32,16) and 2 at (33,16), bar 8 body and 4 core, readout 8 dots + 4 cores lit and 12 blanks, meter 3, empty slot 24; 24+8+12+12+22+12+9 = 99 = dynamic_cells and 99-24 = 75 = cells_needing_an_owner."},

  {"id": "O-03", "subject": "meter cells (53,61) (53,62) (53,63) as BarCore instances", "verdict": "accept",
   "why": "Their frame-0 colour is 2 so arc-instances:all hands them to BarCore with nothing written; re-checked this round that no k1/k2/k3/k4/k7 guard grounds on any of them in any state, which is why certify's divergence set is exactly those cells and nothing else."},

  {"id": "R-01", "subject": "self-proposed meter_propagates_left: BarCore colour 2 with right neighbour 3 becomes 3", "verdict": "reject",
   "why": "It is the only repair the guard language admits for the replay mismatch and I summed its cost: under cascade single_frame it fires the command after each tick, so (53,62) at command 5 against the world's 8 and (53,61) at command 6 against the world's 11; wrong-cell-transitions go from 9 to about 10 AND become unbounded as the wave walks left into (53,60) and beyond, which are still board cells that have never changed."},

  {"id": "R-02", "subject": "the forty k1/k2 swap rules", "verdict": "entailed",
   "why": "Kept byte-identical and re-verified without spending a command: each type's k1 coverages and k2 coverages each partition its instance count exactly (Field 24, Frame 22 both ways with the 16 read off the current frame, Hollow 12, BarBody 8, Dot 9, Blank 12), the sole deficit being BarCore 9 of 12; 96 of 99 covered, and 96 is exactly the largest diff ever observed (t1, t2)."},

  {"id": "R-03", "subject": "meter_first_tick_replay_patch", "verdict": "probe-pending",
   "why": "It fires only on ACTION1... corrected: only on key(4) with a colour-2 instance whose rightof is off-board, which no current instance satisfies since (53,63) is now 3, so it is inert going forward; a second ACTION4 press is what would test that it stays inert."},

  {"id": "L-01", "subject": "the_certify_report_was_predicted_line_by_line", "verdict": "accept",
   "why": "Five dated predictions, five hits: 7/13 replay, first divergence t=7, single cell (53,62) manual 2 world 3, 0/4096 unexplained, 0 clashes over 70/70 pairs -- including the forecast of my own permanent failure, which is the only thing an under-claiming manual can offer."},

  {"id": "L-02", "subject": "the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help", "verdict": "accept",
   "why": "S5 = S7 is forced by distinct_states = 10 over 14 states together with the four coincidences readable in the diffs, and ACTION1 changed 72 cells from S5 and 73 from S7; two pixel-identical states with different successors under one key cannot be separated by any guard over the frame, counter or not."},

  {"id": "L-03", "subject": "every_coverage_column_sums_to_its_type", "verdict": "accept",
   "why": "New this round and derived by hand from the current frame; it earns its place under constraint 3 by turning 'the manual is silent about the meter' from an assertion into an arithmetic deficit of exactly 3 cells in exactly one type."},

  {"id": "L-04", "subject": "a_round_passed_with_no_new_command_and_the_manual_must_not_grow", "verdict": "accept",
   "why": "states, steps, distinct_states, dynamic_cells, cells_needing_an_owner, constant_cells and actions_used are all identical to last round, so no observation exists to license a rule and every rule is kept byte-identical."},

  {"id": "L-05", "subject": "exchange_versus_scroll_is_still_open", "verdict": "probe-pending",
   "why": "Row 29 never changing in fourteen states is evidence against scroll but not decisive (a window starting at row 30 looks the same); one ACTION1 pressed here in W1 settles it and no command was pressed this round."},

  {"id": "L-06", "subject": "a_probe_goes_vacuous_exactly_when_the_world_ticks", "verdict": "probe-pending",
   "why": "Carried unadjudicated because no probe report was supplied this round; it is refuted by any vacuous probe on a command that leaves row 53 alone."},

  {"id": "L-07", "subject": "a goal section", "verdict": "reject",
   "why": "Fourteen states have returned only NOT_FINISHED so no observation distinguishes a win; the one count that looks like progress -- the meter filling -- cannot be written because the un-ticked cells are still board, and every writable count either names a configuration or is already true, so silence beats a reachable false goal."},

  {"id": "P-01", "subject": "replay_mismatch at t=7, cell (53,62), manual 2 world 3", "verdict": "reject",
   "why": "Answered by explicit refusal to change, as required: the fifth edition named this cell and this transition index in advance, the only repair available was computed and shown to increase and unbound the error (R-01), and no unpriced cell diverged anywhere in the 13 transitions."},

  {"id": "P-02", "subject": "next command: ACTION1 pressed here in W1", "verdict": "probe-pending",
   "why": "Only this configuration can ask it, it tests the 20-rule silence that is an artefact of every k1 guard demanding a frame-0 colour, and it has three legible outcomes (exact return to W0 = exchange, a configuration never seen = scroll, silence = the most surprising result available); unbought for three rounds."},

  {"id": "P-03", "subject": "ACTION5 or ACTION6", "verdict": "probe-pending",
   "why": "Never pressed in fifteen entries, so any outcome including inertness is the largest single addition available, and it is the cheapest place a GameState other than NOT_FINISHED could come from."},

  {"id": "E-01", "subject": "the meter tick", "verdict": "reject",
   "as": "theorem the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help",
   "why": "I wanted a rule turning the next row-53 cell from 2 to 3 on the right command; the guard language sees only the frame and two identical frames disagree, so I wrote a theorem plus an advertised, bounded, located replay cost instead."},

  {"id": "E-02", "subject": "a goal naming the meter full", "verdict": "reject",
   "as": "no goal section at all",
   "why": "count(BarCore, color = 3) cannot exceed 12 and 9 of those are widget cells, because the un-ticked meter cells have never changed and are therefore board rather than instances; the goal language cannot name a cell that is not yet an object."}
]
```
```
