# call-008-theorize-round1

model: `claude-opus-5` · 567998 ms · $1.678809 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 47179, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 47179, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 47179, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 47179, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 46877, "type": "message"}], "output_tokens": 46877, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
  "ACTION5",
  "RESET"
 ],
 "background": 0,
 "cascade_lengths": [
  1,
  7,
  9
 ],
 "cells_needing_an_owner": 84,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4009,
 "distinct_states": 30,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 87,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 34,
 "steps": 34
}
```

## The current frame

Each cell is one hex digit 0-f standing for a colour. Row numbers on the left, column numbers on top.

```
0000000000000000000000000000000000000000000000000000000000000000
0222099900000000000000000000000000000000000000000000000000000000
0202090900000000000000000000000000000000000000000000000000000000
0222099900000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000099900000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000555555555555555555555555555555500000000000000000000
0000000000000599999555555555555555555555555500000000000000000000
0000000000000599999555555555555555555558885500000000000000000000
0000000000000599599555555555555555555558885500000000000000000000
0000000000000599999555555555555555555558885500000000000000000000
0000000000000599999555555555555555555555855500000000000000000000
0000000000000555555555555555555555555555855500000000000000000000
0000000000000555555500000555555500000005850000000000000000000000
0000000000000555555500000555555500000005850000000000000000000000
0000000000000555555500000555555500000005850000000000000000000000
0000000000000555555500000555555500000005850000000000000000000000
0000000000000555555500000555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000588888500000000000000000005850000000000000000000000
0000000000000558888555555555555555555555850000000000000000000000
0000000000000588888888888888888888888888850000000000000000000000
0000000000000558888555555555555555555555550000000000000000000000
0000000000000588888500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000005555555550000000000000
0000000000000555555555555555555555555555555999999950000000000000
0000000000000555555555555555555555555555555555555950000000000000
0000000000000555555555555555555555555555555555555950000000000000
0000000000000555555555555555555555555555555555955950000000000000
0000000000000555555555555555555555555555555555555950000000000000
0000000000000555555555555555555555555555555555555950000000000000
0000000000000555555555555555555555555555555999999950000000000000
0000000000000000000000000000000000000000005555555550000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
9999999999999999999999999999999999999999999999991111111111111111
```

## Every command, and what changed

`t` indexes the state sequence. `frames` is how many grids one command returned -- more than one means the world took several internal steps for a single action.

- t0   RESET     frames=1   state=NOT_FINISHED (first frame)
- t1   ACTION1   frames=1   state=NOT_FINISHED no cells changed
- t2   ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-63, [5, 9] -> [1, 5, 9]
- t3   ACTION3   frames=1   state=NOT_FINISHED no cells changed
- t4   ACTION4   frames=1   state=NOT_FINISHED (63,62) 9->1
- t5   ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t6   ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-61, [5, 9] -> [1, 5, 9]
- t7   ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t8   ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-60, [5, 9] -> [1, 5, 9]
- t9   ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t10  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-59, [5, 9] -> [1, 5, 9]
- t11  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t12  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-58, [5, 9] -> [1, 5, 9]
- t13  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t14  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-57, [5, 9] -> [1, 5, 9]
- t15  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t16  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-56, [5, 9] -> [1, 5, 9]
- t17  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t18  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-55, [5, 9] -> [1, 5, 9]
- t19  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t20  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-54, [5, 9] -> [1, 5, 9]
- t21  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t22  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-53, [5, 9] -> [1, 5, 9]
- t23  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t24  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-52, [5, 9] -> [1, 5, 9]
- t25  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t26  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-51, [5, 9] -> [1, 5, 9]
- t27  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t28  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-50, [5, 9] -> [1, 5, 9]
- t29  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- ... 4 more

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 33,
  "n_states": 34,
  "refusals": [
   "ValueError: transition 4 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
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
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 1,
    "ms": 1,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj0",
    "transitions": 33
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 4 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj1"
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj2",
    "transitions": 33
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
    "track_id": "obj3"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
    "track_id": "obj4"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj5"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj6"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj7"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj8"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj9"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj10"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj11"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj12"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj13"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj14"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj15"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj16"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj17"
   }
  ],
  "verdict": "no track satisfies the miner's precondition (exactly one move event per transition). The world does not narrate as one mover."
 },
 "dispatched": [
  "mdl_segmenter",
  "cegis_miner",
  "zero_space"
 ],
 "mdl_segmenter": {
  "background": 0,
  "candidates": 18,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 13,
   "move": 26,
   "recolor": 42,
   "vanish": 13
  },
  "n_frames": 34,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 34,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj0"
   },
   {
    "color": 1,
    "first_frame": 0,
    "frames_present": 5,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj1"
   },
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 34,
    "n_cells": 3,
    "shape": [
     1,
     3
    ],
    "track_id": "obj2"
   },
   {
    "color": null,
    "first_frame": 0,
    "frames_present": 34,
    "n_cells": 1006,
    "shape": [
     50,
     38
    ],
    "track_id": "obj3"
   },
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 34,
    "n_cells": 64,
    "shape": [
     1,
     64
    ],
    "track_id": "obj4"
   },
   {
    "color": 2,
    "first_frame": 5,
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj5"
   },
   {
    "color": 1,
    "first_frame": 7,
    "frames_present": 2,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj6"
   },
   {
    "color": 2,
    "first_frame": 9,
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj7"
   },
   {
    "color": 1,
    "first_frame": 11,
    "frames_present": 2,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj8"
   },
   {
    "color": 2,
    "first_frame": 13,
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj9"
   },
   {
    "color": 1,
    "first_frame": 15,
    "frames_present": 2,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj10"
   },
   {
    "color": 2,
    "first_frame": 17,
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj11"
   },
   {
    "color": 1,
    "first_frame": 19,
    "frames_present": 2,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj12"
   },
   {
    "color": 2,
    "first_frame": 21,
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj13"
   },
   {
    "color": 1,
    "first_frame": 23,
    "frames_present": 2,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj14"
   },
   {
    "color": 2,
    "first_frame": 25,
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj15"
   },
   {
    "color": 1,
    "first_frame": 27,
    "frames_present": 2,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj16"
   },
   {
    "color": 2,
    "first_frame": 29,
    "frames_present": 5,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj17"
   }
  ],
  "variants": [
   {
    "baseline_bits": 25272,
    "compression_ratio": 0.52754,
    "events": 94,
    "gain_bits": 11940,
    "ms": 112,
    "script_bits": 13332,
    "split_by_color": false,
    "tracks": 18
   },
   {
    "baseline_bits": 25272,
    "compression_ratio": 6.252453,
    "events": 219,
    "gain_bits": -132740,
    "ms": 142,
    "script_bits": 158012,
    "split_by_color": true,
    "tracks": 81
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 87,
   "frame_cells": 4096,
   "full_frame": true,
   "reason": "frame is 4096 cells, no crop needed",
   "window_cells": 4096
  }
 },
 "not_dispatched": {
  "deadlock_carver": "needs a grounded PDDL task; same gate as fd_adapter",
  "fd_adapter": "needs theory.pddl, which needs a manual; runs at plan, not at dispatch",
  "ic3_pdr": "same graph requirement as lp_potential",
  "lp_potential": "needs an explicit state graph with enumerated moves; none exists for a 64x64 world whose dynamics are unknown",
  "probe_frontier": "needs a hypothesis frontier, which is theorize's output rather than its input; runs at probe"
 },
 "store": {
  "actions_used": [
   "ACTION1",
   "ACTION2",
   "ACTION3",
   "ACTION4",
   "ACTION5",
   "RESET"
  ],
  "background": 0,
  "cascade_lengths": [
   1,
   7,
   9
  ],
  "cells_needing_an_owner": 84,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4009,
  "distinct_states": 30,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 87,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 34,
  "steps": 34
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 87,
  "frame_cells": 4096,
  "full_frame": true,
  "reason": "frame is 4096 cells, no crop needed",
  "window_cells": 4096
 },
 "zero_space": {
  "cap": 240,
  "cells": [
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
    3
   ],
   [
    1,
    5
   ],
   [
    1,
    6
   ],
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
    3
   ],
   [
    2,
    5
   ],
   [
    2,
    6
   ],
   [
    2,
    7
   ],
   [
    3,
    1
   ],
   [
    3,
    2
   ],
   [
    3,
    3
   ],
   [
    3,
    5
   ],
   [
    3,
    6
   ],
   [
    3,
    7
   ],
   [
    5,
    1
   ],
   [
    5,
    2
   ],
   [
    5,
    3
   ],
   [
    5,
    5
   ],
   [
    5,
    6
   ],
   [
    5,
    7
   ],
   [
    8,
    14
   ],
   [
    8,
    15
   ],
   [
    8,
    16
   ],
   [
    8,
    17
   ],
   [
    8,
    18
   ],
   [
    9,
    14
   ],
   [
    9,
    15
   ],
   [
    9,
    16
   ],
   [
    9,
    17
   ],
   [
    9,
    18
   ],
   [
    10,
    14
   ],
   [
    10,
    15
   ],
   [
    10,
    17
   ],
   [
    10,
    18
   ],
   [
    11,
    14
   ],
   [
    11,
    15
   ],
   [
    11,
    16
   ],
   [
    11,
    17
   ],
   [
    11,
    18
   ],
   [
    12,
    14
   ],
   [
    12,
    15
   ],
   [
    12,
    16
   ],
   [
    12,
    17
   ],
   [
    12,
    18
   ],
   [
    14,
    14
   ],
   [
    14,
    15
   ],
   [
    14,
    16
   ],
   [
    14,
    17
   ],
   [
    14,
    18
   ],
   [
    15,
    14
   ],
   [
    15,
    15
   ],
   [
    15,
    16
   ],
   [
    15,
    17
   ],
   [
    15,
    18
   ],
   [
    16,
    14
   ],
   [
    16,
    15
   ],
   [
    16,
    17
   ],
   [
    16,
    18
   ],
   [
    17,
    14
   ],
   [
    17,
    15
   ],
   [
    17,
    16
   ]
  ],
  "cells_dynamic": 87,
  "cells_used": 87,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 17,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.03908,
   "difference_rank": 17,
   "features": 435,
   "space_dimension": 418,
   "transitions": 33,
   "verdict": "THIN: 33 transitions constrain rank 17 of 435 features, so the null space has dimension 418 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 435,
  "global_laws": [
   {
    "cells": [
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
      3
     ],
     [
      1,
      5
     ],
     [
      1,
      6
     ],
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
      3
     ],
     [
      2,
      5
     ],
     [
      2,
      6
     ],
     [
      2,
      7
     ],
     [
      3,
      1
     ],
     [
      3,
      2
     ],
     [
      3,
      3
     ],
     [
      3,
      5
     ],
     [
      3,
      6
     ],
     [
      3,
      7
     ],
     [
      5,
      1
     ],
     [
      5,
      2
     ],
     [
      5,
      3
     ],
     [
      5,
      5
     ],
     [
      5,
      6
     ],
     [
      5,
      7
     ],
     [
      8,
      14
     ],
     [
      8,
      15
     ],
     [
      8,
      16
     ],
     [
      8,
      17
     ],
     [
      8,
      18
     ],
```

The full proposal stream is 3250 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 30 states / 29 transitions
# (RESET + A1 A2 A3 A4 A5, then A2 A5 twelve times over).
# 85 cells have ever changed; this manual names and owns all 85.
#
# WHAT THIS ROUND COST AND WHAT IT BOUGHT
#
#   Four commands -- A2 A5 A2 A5 -- for the SIXTH consecutive round. Four
#   refutations, P-21..P-24, chaining into a closed 4-cycle for the fifth
#   time (P-22 inert = P-21 manual, P-23 inert = P-22 manual, P-24 inert =
#   P-23 manual, P-21 inert = P-24 manual). The two wrong pixels are
#   (63,51) at t26 and (63,50) at t28: both were board at the instant they
#   burned, both named in advance, both cost exactly one pixel. TWENTY-FOUR
#   refutations across six rounds, every divergence set a subset of the
#   meter's leading edge, ZERO rules contradicted. Replay 25/25,
#   responsibility 0/4096, ambiguity 0 clashes over 130 pairs.
#
#   THIS ROUND I STOP DIAGNOSING AND CUT. Last round proved two things:
#   alphabet width is not the bottleneck (certify went 3 -> 5 actions, the
#   commands did not move), and my manual leaves EXACTLY ONE key with a
#   non-identity successor in each of the two cells this body has stood in.
#   A chooser with `is_goal -> False` and one live key has no choice to
#   make. Naming that twice bought nothing. So this round I removed the
#   thing that makes it true.
#
#   THE CUT: thirteen panel rules carried `colored(spawn_probe, 5)`. That
#   atom has THIRTEEN positive witnesses and ZERO negative ones, because
#   every ACTION5 in this world's history followed an ACTION2 and so was
#   pressed with the body away. `ACTION5 was pressed` and `the body is away`
#   are the same event 13/13 and no guard can be credited over the other.
#   Constraint 3 decides it: the atom explains no pixel that the action
#   guard does not already explain, it costs thirteen conjuncts, and
#   deleting it changes NO replay. It is deleted. The correlation that
#   survives is the one with a discriminating negative: the panel toggles on
#   13/13 ACTION5 and on 0/13 ACTION2, so the toggle is keyed to the ACTION,
#   not to the body. See the_spawn_probe_guard_is_deleted_and_here_is_the_bill.
#
#   CONSEQUENCE, STATED SO IT CAN COST ME: at spawn my manual now predicts
#   TWO live keys -- key(2) moves 48 body cells, key(5) toggles 23 panel
#   cells and moves nothing. That is the first time in six rounds this
#   manual has offered a ranking anything downstream could act on, and it is
#   also a 23-pixel stake on a claim no frame has ever tested.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Dark    { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  landmark spawn_probe  # arc-cell: (8, 14)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t29 compress: 49]
  Vacated [segment: dynamic_colour_5 ev: t2-t29 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20,t22,t24,t26,t28 cov: 312/312]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20,t22,t24,t26,t28 cov: 312/312]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12,t14,t16,t18,t20,t22,t24,t26,t28 cov: 12/12]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 cov: 312/312]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 cov: 312/312]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25,t29 cov: 56/56]
    when act=key(5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23,t27 cov: 48/48]
    when act=key(5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23,t27 cov: 18/18]
    when act=key(5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23,t27 cov: 48/48]
    when act=key(5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23,t27 cov: 6/6]
    when act=key(5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11,t15,t19,t23,t27 cov: 18/18]
    when act=key(5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 49 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4011 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 14 [status: counted]

  theorem the_spawn_probe_guard_is_deleted_and_here_is_the_bill "THE ROUND'S ONE STRUCTURAL CHANGE, and I want the reasoning auditable line by line because it is the first time in six rounds I have changed the manual for a reason other than arithmetic. THE ATOM: thirteen panel rules carried colored(spawn_probe, 5). THE EVIDENCE FOR IT: thirteen positive witnesses, every ACTION5 press, all with the body away. THE EVIDENCE AGAINST IT: none, and none is possible, because ACTION5 has never been pressed with the body at home -- every ACTION5 in this history immediately followed an ACTION2, so `ACTION5 was pressed` and `the body is away from spawn` are literally the same thirteen events and no guard can be credited over the other. THE DECIDING ARGUMENT IS CONSTRAINT 3, NOT TASTE: a conjunct earns its place by explaining a pixel the rest of the rule does not. This one explains nothing -- delete it and all 29 transitions still replay exactly, because the atom was true in every transition where its rules fired. Thirteen conjuncts, zero explained pixels, so it goes. THE CORRELATION THAT SURVIVES has a discriminating negative and that is the whole difference: the panel toggles on 13/13 ACTION5 presses and on 0/13 ACTION2 presses, so `keyed to the action` is separated from `keyed to body motion` by thirteen counterexamples, while `keyed to the action` and `keyed to the action AND the body being away` are separated by nothing. WHAT THIS COSTS ME: my manual now says key(5) at spawn toggles the panel, 23 cells, body unmoved. No frame has ever tested that. If it is wrong I pay 23 pixels and learn that the panel is coupled to something my rules cannot read, which is worth more than 23 pixels. WHAT IT BUYS: at spawn there are now TWO keys with a non-identity successor instead of one, so for the first time this manual expresses a preference a chooser could act on rather than a forced move."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, why_the_deleted_guard_was_half_the_reason_the_command_stream_was_stuck  probe: pending]

  theorem why_the_deleted_guard_was_half_the_reason_the_command_stream_was_stuck "Ground every rule in the two cells this body has ever stood in, BEFORE the cut. At spawn, spawn_probe renders 9: key(1) fired key1_inert_at_spawn, 9 to 9, net zero. key(3) blocked, its guard demanding spawn_probe render 5. key(4) net zero, because meter_burn_key4_next needs a Glyph9 rendering 9 whose right neighbour renders 1, and the only such cell is the bar's leading edge, which is board and has no instance. key(5) net zero, because THIRTEEN of its rules were guarded on colored(spawn_probe, 5) and the fourteenth, key5_body_respawns, needs a Glyph9 rendering 5 while every Glyph9 at spawn renders 9, 2, 0 or 1. key(2) fired 48 cells. ONE LIVE KEY. One cell south, body at lattice (2,2): key(1) blocked, key(3) inert-by-rule, key(4) net zero, key(2) net zero because key2_body_leaves ranges over Glyph9 while the body there is made of Vacated instances and key2_body_arrives needs a Vacated destination while rows 20-24 are board, key(5) fired 71 cells. ONE LIVE KEY. Two states, two live keys, and they are exactly the two keys pressed for six rounds. AFTER THE CUT, at spawn key(5) fires the five B-to-A panel rules for 23 cells, so spawn has two live keys and the forced move is gone at one of the two cells. One cell south is unchanged and still forced, which I state rather than hide: the cut fixes half the trap, and the half it fixes is the half the body is standing in."
    [depends: key2_body_leaves, key5_body_respawns, the_goal_section_is_absent_on_purpose_and_the_ranking_had_no_choice_to_make  probe: passed]

  theorem silence_is_a_prediction_and_two_of_my_spawn_silences_are_still_unwitnessed "The compiled transition function is total: where no rule fires, the successor equals the current state. So my manual does not say `I do not know what key(4) does at spawn`, it says `key(4) does nothing at spawn`, in exactly the voice it uses for things it has seen. Audit the five keys at spawn AFTER this round's cut. key(1) inert: WITNESSED at t1, zero cells. key(2) moves: witnessed thirteen times. key(5) now PREDICTS CHANGE, so it is no longer a silence at all -- it is a falsifiable claim, which is the improvement. key(3) inert: NO WITNESS, pressed once ever, at t3, from one cell south. key(4) inert: NO WITNESS, pressed once ever, at t4, from one cell south, where it burned a meter cell. TWO OF FIVE SILENCES AT SPAWN ARE STILL FORGED DEATH CERTIFICATES, down from three. Under the standard mapping that the_action_map defends, one of key(3) and key(4) is EAST, east of spawn is three lattice cells of unbroken floor, and that key moves the body 48 pixels -- so at least one of my two remaining unwitnessed silences is almost certainly FALSE, and false in the most expensive way, by making a live key look dead to anything that reads my predictions."
    [depends: why_the_deleted_guard_was_half_the_reason_the_command_stream_was_stuck, the_action_map_after_twentynine_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_dsl_cannot_say_unknown_and_that_is_the_hole_i_would_most_like_closed "What I want is a third outcome for a (state, action) pair: not `no change` and not a named successor, but `unobserved, and the manual declines to predict`. There is no syntax for it -- rules produce events, absence of a rule produces identity, and the compiled step is documented total. This round I found the only lever the grammar does offer, and used it: where a guard is unearned, DELETING it converts an unwitnessed silence into an unwitnessed PREDICTION OF CHANGE, and a prediction of change is testable in one command while a silence is invisible. That trick works only when there is an unearned guard to delete. For key(3) and key(4) at spawn there is no rule at all, so there is nothing to cut, and the silence stands. If a future desk gains one expressive extension, ask for this one before asking for `not`."
    [depends: silence_is_a_prediction_and_two_of_my_spawn_silences_are_still_unwitnessed, the_spawn_probe_guard_is_deleted_and_here_is_the_bill  probe: pending]

  theorem the_two_no_op_rules_still_fail_the_gain_test_and_i_keep_them_for_a_weaker_reason "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has one witness on a transition where zero cells changed, and the manual would replay all 29 transitions identically without them. They were bought to test the alphabet hypothesis, which is refuted, so THAT reason is gone. The reason I keep them is weaker and I will not dress it up: deleting them narrows certify's adjudicated action set from five keys to three, removing information I can see for a benefit -- two lines -- I cannot measure. Note the asymmetry with this round's cut, because it is the point: I DELETED an unearned guard and KEPT two unearned rules, and the difference is that deleting the guard changed a prediction from silence to a claim while deleting these rules would change no prediction at all. They remain declared failures of the gain test and the two cheapest deletions in this manual."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_key_alphabet_hypothesis_is_refuted  probe: passed]

  theorem the_key_alphabet_hypothesis_is_refuted "Kept compressed, because it is settled. I once hypothesised that the command chooser derives its candidate keys from the `act=key(n)` literals in my rules, and that this, not ranking, was why round after round bought A2 A5. I paid two witnessed no-op rules to widen the alphabet. THE INSTRUMENT MOVED EXACTLY AS PREDICTED: certify went from `actions: 3, pairs_checked: 54` to `actions: 5, pairs_checked: 110`, now 130 at 26 states, with 0 clashes and 0 step crashes. THE COMMANDS DID NOT MOVE AT ALL, then or since. Alphabet width is NOT sufficient to change the choice and the hypothesis in the form I stated it is dead. This is a negative result and it is what let this round look at guards instead of at the alphabet."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem the_four_refutations_are_two_undrawable_pixels_rolled_forward "P-21 and P-23 are ACTION2, P-22 and P-24 ACTION5, and the diagnosis is arithmetic for the fifth round running. The inert fields form a CLOSED 4-CYCLE: P-22 inert = P-21 manual, P-23 inert = P-22 manual, P-24 inert = P-23 manual, P-21 inert = P-24 manual. That is the sharpest statement of the defect -- my manual says A2 then A5 returns the world exactly where it started, and it is right about all 4096 cells except the one the meter eats on each A2, and the harness rolls my predicted frame forward without resyncing so the error persists. The world burned (63,51) at t26 and (63,50) at t28; both were board at the instant they burned, owned by no object, drawable by no rule this grammar admits. t27 and t29 introduced nothing new: 48 body cells and 23 panel cells each. THE LEDGER IS TWO WRONG PIXELS AND FOUR REFUTATION REPORTS. Repair is arithmetic: both cells are dynamic now, Glyph9 goes 47 to 49, all four transitions replay exactly, and the identical bill will be presented at (63,49)."
    [depends: meter_burn_key2_next, the_meter_edge_saturates_the_refutation_channel  probe: passed]

  theorem the_meter_edge_saturates_the_refutation_channel "A law of this manual rather than of this world, and after six rounds the most expensive fact on the board. Each of the 64 cells of the row-63 bar burns EXACTLY ONCE, 9 to 1, advancing leftward. At the instant a cell burns it has never changed, so it is board, so no instance exists for it, so no rule of mine draws it. Therefore: (1) my three burn rules have ZERO predictive value on the leading edge and full value on replay, which is a division of labour and not a contradiction; (2) EVERY press of a key that burns is scored a refutation regardless of what else it teaches, so refutation-fired cannot discriminate between commands; (3) the correct reading of a refutation is its DIVERGENCE SET, and where that set is a subset of the bar's leading edge the manual is not implicated. All twenty-four refutations across six rounds have been exactly that. Deleting the burn rules does not help -- the wrong-pixel count at the moment of the burn is identical -- and keeping them is strictly better because they make every past transition replay. RIGHT NOW all fourteen meter instances render colour 1, so meter_burn_key2_next and meter_burn_key4_next match nothing and my manual predicts NO burn at (63,49) under any key. That is not a claim about the world; it is the shape of the hole."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right. FOURTEEN burns now: (63,63) t2, (63,62) t4, then one per even index through (63,50) at t28. Fifteen silences: every odd index t1 through t29. The current frame confirms it to the cell -- row 63 reads 9 through col 49 and 1 from col 50 to col 63. READING A, ACTION-KEYING: burns iff the key is 2 or 4. READING B, COMMAND PARITY: burns iff the command index is even. BOTH SCORE 29/29 AND NEITHER HAS GAINED A BIT IN FIVE ROUNDS, because every command since t5 has been key 2 at an even index or key 5 at an odd index -- the exact diagonal on which the two readings are numerically identical. THE SEPARATOR IS STILL FREE AND STILL CHEAP: the next index is 30, EVEN, so ANY odd key there -- 1, 3 or 5 -- settles it in one command, and an even key there settles nothing. And this round's cut makes the cheapest separator legible: key(5) at spawn is now predicted to change 23 cells and no more, so a burn at (63,49) alongside those 23 confirms B and kills A, and their absence does the reverse, with the body's 48 pixels nowhere in the diff to confuse the count. I encode reading A because it is the only one the guard language can express -- there is no command counter and no phase pixel -- and I still expect B, because at t3 and t4 the body stood at lattice (2,2) with left and right both void, ACTION3 and ACTION4 were blocked identically, and only ACTION4 burned."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_meter_is_a_budget_and_it_is_still_not_the_binding_constraint "Fourteen of sixty-four bar cells consumed after twenty-nine commands. I do not know that exhaustion ends the game -- no frame has shown it -- but both readings price out survivably. Under reading A the bar burns only on keys 2 and 4, so a route made of eastward and southward steps burns once per step and 50 steps remain. Under reading B every second command burns and 100 commands remain. The route I can see: spawn (1,2) east three cells to (1,5) beside the knob, an unknown number of interactions there, three cells back west, seven cells south down lattice column 2 to (8,2), five cells east to the socket at (8,7) -- about nineteen steps plus interactions plus identification probes, comfortably inside 50. The meter has never been the binding constraint. Twenty-four of twenty-nine commands buying nothing is."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9, and the split is now 13/13 WITH NO EXCEPTIONS. ACTION2 returned SEVEN frames at t2, t8, t12, t16, t20, t24, t28 and NINE frames at t6, t10, t14, t18, t22, t26. Read the panel configuration of the state each press acted FROM: t2 from state 1 (A), t8 from 7 (A), t12 from 11 (A), t16 from 15 (A), t20 from 19 (A), t24 from 23 (A), t28 from 27 (A) -- seven frames; t6 from 5 (B), t10 from 9 (B), t14 from 13 (B), t18 from 17 (B), t22 from 21 (B), t26 from 25 (B) -- nine frames. ACTION2 animates in 7 internal frames under configuration A and 9 under B, thirteen for thirteen. ACTION5 returned nine frames all thirteen times regardless of configuration, and every no-op returned one. THE NET EFFECT IS IDENTICAL IN ALL THIRTEEN ACTION2 PRESSES -- 48 body cells, rows 8-18, cols 14-18, plus one burn -- so this costs nothing in replay and buys nothing in prediction, and it remains the ONLY evidence that the panel does anything besides display. I record it as a limitation of my own semantics, not of the world: `cascade single_frame` compares only the net, so up to eight intermediate frames per command are discarded unread, and something distinguishable happens inside them. Note the new consequence of this round's cut: if key(5) at spawn toggles the panel, the NEXT ACTION2 from spawn should take 7 frames instead of 9, which is a second, independent confirmation channel for the cut costing nothing extra."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over THIRTEEN toggles -- every odd index t5 through t29 -- 23 cells every time, and ACTION2 has never touched a panel pixel in thirteen presses. CONFIGURATION A (states 0-4, 7-8, 11-12, 15-16, 19-20, 23-24, 27-28): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B (states 5-6, 9-10, 13-14, 17-18, 21-22, 25-26, 29, and the current frame, which reads 222/2.2/222 at cols 1-3 and 999/9.9/999 at cols 5-7 with row 5 dark at 1-3 and lit at 5-7): slot 1 is a hollow colour-2 ring with dark underline, slot 2 a hollow colour-9 ring with dark centre and lit underline. mdl_segmenter corroborates independently and by frame index: colour-1 nine-cell tracks obj1 (0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16), obj12 (19-20), obj14 (23-24), obj16 (27-28); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17-18), obj13 (21-22), obj15 (25-26), obj17 (29). Fourteen alternations read off an engine that has never seen my rules. Its obj0 (colour 9, eight cells, 3x3, present in all 30 frames) and obj2 (colour 9, 1x3, all 30) persist while it narrates 26 MOVE events: the hollow ring and the lit underline do not appear and vanish, they TRAVEL between slot 1 and slot 2. So the panel is one marker with two seats and colour 9 marks the occupied seat. What the seats HOLD is still unknown and I will not guess. I cannot model it as a moving marker either: the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring travelling four columns is not expressible as a move, and ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem the_action_map_after_twentynine_transitions_and_the_standard_mapping_hypothesis "WITNESSED: ACTION2 IS DOWN, 13/13, six rows south, one lattice cell. ACTION5 returns the body from lattice (2,2) to (1,2), 13/13. NEGATIVE INFORMATION, and I state it as negative because that is all it is. At spawn (1,2) up and left are void while down and right are open floor, and ACTION1 did nothing at t1 -- so ACTION1 IS NEITHER DOWN NOR RIGHT. At (2,2) the body had just vacated rows 8-12 so UP WAS OPEN, and rows 20-24 cols 14-18 are floor so DOWN WAS OPEN, while left (cols 8-12) and right (cols 20-24) are void; ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else. It explains every no-op as a blocked move and it is the conventional mapping for this action family, which is a prior and not evidence. TWENTY-FOUR COMMANDS ACROSS SIX ROUNDS AND NOT ONE TOUCHED THIS QUESTION -- the map is exactly as constrained as it was at state 5. THE TEST IS ONE PRESS: the body stands at spawn, west is void, east is three lattice cells of unbroken floor, so either of ACTION3 and ACTION4 pressed here settles which is east -- if it steps it is east, and if it does not the other is east by elimination, ACTION1 having been excluded from east at t1. ACTION3 is the odd one of the pair and index 30 is even, so ACTION3 here also separates the meter readings: one press, two questions."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_and_the_experiment_this_rounds_cut_makes_cheap "Three readings survive all THIRTEEN ACTION5 presses because all thirteen were made from exactly one cell south of spawn, where they are indistinguishable: UP (move one cell north), UNDO (revert the last move), RETURN (jump to spawn from anywhere). FROM SPAWN ITSELF, which is where the body is now, the readings split on the body's 48 pixels: UP predicts no body motion (north of spawn is void), RETURN predicts no body motion (already home), UNDO predicts 48 cells back to (2,2). My manual after the cut predicts 23 panel cells and NO body motion, which is UP-or-RETURN; a 71-cell diff says UNDO and refutes nothing else, because the panel rules would have fired either way. So one press at spawn now yields THREE independent bits in a single legible diff: does the panel toggle without the body moving (the cut), does the body move (UP/RETURN versus UNDO), and does (63,49) burn (meter parity). Two cells EAST at lattice (1,4) would give full three-way separation of UP, UNDO and RETURN, which is one more reason the eastward route is the right one once the east key is named. The coupling I cannot yet break is the panel's: it toggles on every effective ACTION5, thirteen for thirteen, so whatever ACTION5 is, the panel is its counter or its selector -- and the 7-versus-9 cascade split, now 13/13, says the panel's state is not merely cosmetic."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_spawn_probe_guard_is_deleted_and_here_is_the_bill  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated one row per internal frame and the world reports the whole animation for a single action; cascade single_frame compares only the net effect, which is identical for all thirteen ACTION2 presses (48 body cells, rows 8-18, cols 14-18) whether the command took 7 frames or 9. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, THIRTEEN times. ONE PRESS IS ONE LATTICE CELL, 13/13, and every distance in the playbook rests on that."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_world_may_still_not_be_a_function_of_the_drawn_frame "Carried as a belief and NOT proven in this window. To prove it I need two pixel-identical states from which the SAME action produced different successors. distinct_states is 28 against 30 states, so there are exactly two coincidences and I can name them: state 1 equals state 0 (ACTION1 changed nothing at t1) and state 3 equals state 2 (ACTION3 changed nothing at t3). From state 0 the world pressed ACTION1 and from state 1 it pressed ACTION2; from state 2 it pressed ACTION3 and from state 3 ACTION4. DIFFERENT KEYS BOTH TIMES, so neither pair tests functionality and the belief is untouched. What keeps it alive is the parity reading of the meter, which if true is one bit of hidden state flipping every command that no guard in this language can read, because no guard can read anything that is not a pixel. What strengthens it is the cascade length: ACTION2 took 7 frames or 9 depending on a panel configuration my rules never consult -- the same shape of dependence, one step less hidden. Operationally it matters in exactly one way: if parity wins, every burn rule I can write is an approximation with a known error rate, and I would rather say that once than rediscover it."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4011 + dynamic 85 = 4096, and 49+24+9 = 82 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 85. Consequence: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This is the sixth consecutive round in which that sentence, written in advance, was the entire content of every refutation. meter_burn_key2_next now replays t6 through t28 perfectly, because by replay time all twelve of those cells are dynamic; it will still miss the FIFTEENTH burn at (63,49), because that cell is board today. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable too until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, 24 if I already had the leaves rule, 0 for the second step. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 85 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 14 are the burned right end of row 63: cols 50 through 63. 23+24+24+14 = 85 = dynamic_cells. By frame-0 colour: 49 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 14 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 49+9+24 = 82 = cells_needing_an_owner exactly, and 4096-85 = 4011 = constant_cells exactly. zero_space's global-law cell list is the same set -- it lists (2,1) and (2,3) but not (2,2), (10,14),(10,15),(10,17),(10,18) but not (10,16), and every burned bar cell -- and its single global law restates this census and nothing more."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so that the transition witnessing it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended thirteen times and all thirteen started at spawn, so no rule of mine turns Vacated pixels from 9 back to 5 on an ACTION2: rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below-six(?v), 5) then recolored(?v, 5). One ACTION2 from lattice (2,2) buys it, and twenty-four commands across five rounds each had the chance and none took it. (2) EAST-WEST MOTION. Whatever the east key turns out to be, it needs a pair: a leaves rule over Glyph9 guarded on colour 9 with rightof-six rendering 5, and its arrives twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) A FIFTEENTH BURN AT A CELL THAT IS STILL BOARD, which is not a missing rule but a missing instance and cannot be written at all. I state the price of all three in advance so it cannot be mistaken for a surprise: the first eastward step costs 48 wrong cells plus one if the bar burns, the first second-descent costs 24, and every fresh burn costs 1."
    [depends: key2_body_arrives, the_meter_edge_saturates_the_refutation_channel  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all 130 adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth below is row 69. So colored(off-board, k) is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen rules rest on this and every row and column discrimination in the panel is built from it: the k-th above is off-board exactly when k exceeds the row, so row 1 is above-twice equals wall, row 3 is a colour test on above-twice -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column: col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice, pairwise exclusive, which is why the ambiguity check reports 0 clashes. THIS ROUND'S CUT LEANS ON IT HARDER, because the deleted spawn_probe atom was the outermost guard on thirteen rules and every one of them now depends entirely on these row and column discriminations to stay mutually exclusive. I checked the panel rules pairwise by hand under both configurations before cutting: the A-to-B set and the B-to-A set are separated by the colour of the cell they read (9 or 1 against 2, 9 or 0), and within each set by row and column, so no cell is claimed twice. Not one rule uses `not`, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame and unchanged: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open, C=6 holds the knob, C=7 does not exist in this band; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2, plus a fragment of floor at row 48 cols 42-50 that is one row deep and cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in thirty frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it has been at spawn in sixteen of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed THIRTEEN times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows, col 49 and col 43 are separator columns -- so what is drawn is the north, south and east walls of lattice cell (8,7), painted in colour 9, with the west wall at col 43 left as FLOOR. Inside it, rows 50-54 cols 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, col 50 rows 49-56 is a one-cell strip of floor that leads nowhere. Overlay the body standing in lattice (8,7) -- 5x5, aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in thirty frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel of it is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem pixel at (12,40), colour 8 filling col 40 from row 12 down to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18. It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in thirty frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell -- the eight knob pixels other than its centre, plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Twenty-nine commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after thirty states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. I have no witness for key(6) or key(7), so no rule can name them, so they sit outside the manual's alphabet -- which I once thought decisive and now know is not sufficient to explain anything, since keys 1 and 3 are inside the alphabet and were still never chosen."
    [depends: the_key_alphabet_hypothesis_is_refuted  probe: pending]

  theorem the_goal_section_is_absent_on_purpose_and_the_ranking_had_no_choice_to_make "Still absent, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and forty-eight siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would be true of the body standing one cell south of spawn, which is not a win. The alternatives all fail too: count(Glyph9, color = 5) = 24 is true of every state where the body is anywhere but home, and a Wire type on colour 8 would have zero instances because every colour-8 cell is constant, so count(Wire) = 0 would be true at RESET. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. I name the price plainly: with no goal section the manual compiles is_goal to False, no plan can terminate, and nothing ranks one command above another EXCEPT whether the command is predicted to change pixels. Until this round that criterion admitted exactly one command per state. After the cut it admits two at spawn, which is the smallest possible improvement and the only one available without inventing a goal."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, why_the_deleted_guard_was_half_the_reason_the_command_stream_was_stuck  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me, and this is the first edition where the predictions differ from last round's. The next command has index 30, which is EVEN, the body is at spawn, the panel is in configuration B, and fourteen meter cells are burned through col 50. ACTION5 at spawn -- the command I most want after the cut -- I predict EXACTLY 23 CELLS: slot 1's eight ring pixels 2 to 9, underline 1's three 0 to 9, slot 2's eight ring pixels 9 to 1, its centre 0 to 1, underline 2's three 9 to 0, and NO body motion and NO burn. 23 cells vindicates the cut and, being an odd key at an even index with no burn, kills the parity reading outright. 24 cells, the same 23 plus (63,49), confirms parity. 0 cells says the deleted guard was real after all and puts thirteen rules into repair, which is the outcome I am buying. 71 cells says ACTION5 is UNDO and the panel is action-keyed, both at once. ACTION3 at spawn: I predict ZERO changed cells, because key3_inert_below_spawn requires the body AWAY and under the standard mapping ACTION3 is west and west of spawn is void; zero says ACTION3 is not east, hence ACTION4 is east by elimination, AND kills parity; 48 or 49 cells says ACTION3 IS east and my manual draws none of them, the advertised price of the first step onto fresh ground. ACTION1 at spawn: ZERO, key1_inert_at_spawn firing as a no-op, the one spawn silence I have a witness for. ACTION4 at spawn: my manual says ZERO and has no witness for it, so I expect to be wrong -- 48 undrawable cells plus a possible burn, and no parity information, because an even key at an even index is where both readings agree. ACTION2: 48 cells I draw correctly plus a burn at (63,49) I cannot draw -- exactly one wrong pixel and NOTHING learned, because key2_body_leaves and key2_body_arrives are at 312/312 and a fourteenth witness buys zero."
    [depends: the_spawn_probe_guard_is_deleted_and_here_is_the_bill, the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept in compressed form because the lesson is structural and cost a full round. Thirteen panel rules once carried colored(spawn_probe, 5) while the landmark line read a prose placeholder instead of a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. There is a coda this round: those same thirteen rules have now had that guard deleted for being unearned, so the atom that once broke the manual by pointing nowhere has ended by pointing somewhere and still not earning its keep. The landmark itself remains, reading (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else -- which is exactly why the two no-op rules can still use it as a home/away test in opposite senses. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because a future desk will be tempted by the same repair I considered and rejected for the fourth time this round. To draw the leading-edge burn I would need an instance on a board cell. The arm offers exactly one lever, `arc-instances: all`, and its documented behaviour is to instance every cell OF THAT COLOUR THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance. The tempting workaround is a second declared type on colour 9 without arc-instances, hoping the arm seats one instance somewhere useful. I reject it: the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, the seat is unspecified, and any cell it landed on would be claimed twice, which is the constraint-5 error the grammar warns about in as many words. A landmark cannot help either, because landmarks are cells and every event in the language takes an object as its first argument. So the hole is a property of the arm, it is permanent for this level, and the only correct response is the one the playbook encodes: price the burn in advance and read refutations by their divergence set."
    [depends: the_meter_edge_saturates_the_refutation_channel  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter keeps a positive gain of +11926 bits at compression_ratio 0.527 on split_by_color=false, against -131988 bits when split by colour -- its segmentation beats writing the pixels out, and I still owe it nothing structural. Its eighteen tracks are the round's best independent corroboration and they corroborate the panel toggle by frame index: colour-1 nine-cell tracks obj1 (0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16), obj12 (19-20), obj14 (23-24), obj16 (27-28); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17-18), obj13 (21-22), obj15 (25-26), obj17 (29). A,B,A,B, fourteen times, derived by an engine that has never seen my rules. obj0 and obj2 persisting through all 30 frames while the segmenter narrates 26 moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 14 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 29 transitions constrain rank 15 of 425 features, null space dimension 410, nearly every vector in it a law true over these states and unfalsified rather than confirmed -- and its single global law is my census. cegis_miner refuses on every track and its verdict, `the world does not narrate as one mover`, remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs a pair of rules per direction instead of one moved() event."
    [probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHAT CHANGED IN THE MANUAL, AND WHY IT MATTERS HERE =========
# For six rounds the commands were A2 A5 A2 A5. Two explanations were tried
# and both are closed: the chooser's alphabet (refuted -- certify widened
# 3 -> 5 actions, commands unmoved), and stubborn ranking (wrong -- there was
# nothing to rank). The real cause was in my own manual: it left EXACTLY ONE
# key with a non-identity successor in each of the two cells this body has
# stood in, and those two keys are exactly A2 and A5.
#
# This round I removed the cause instead of describing it. Thirteen panel
# rules carried `colored(spawn_probe, 5)`. That atom had 13 positive
# witnesses and ZERO negative ones -- every ACTION5 ever pressed followed an
# ACTION2, so "key(5) was pressed" and "the body is away" are the same
# thirteen events. Constraint 3 settles it: the atom explains no pixel, costs
# thirteen conjuncts, and deleting it changes no replay. Deleted.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   At spawn (where the body IS):  key(2) -> 48 body cells
#                                  key(5) -> 23 panel cells, body unmoved
#                                  keys 1,3,4 -> nothing
#   One cell south:                key(5) -> 71 cells; all others nothing
#
# TWO live keys at spawn, for the first time in six rounds. That is the whole
# product of the round and the lines below exist to spend it correctly.
#
# ========= AND TWO SILENCES ARE STILL FORGED =========
# key(1) inert at spawn is WITNESSED (t1, zero cells). key(3) and key(4)
# inert at spawn are NOT: each was pressed once ever, both from one cell
# south. Under the standard mapping one of them is EAST, east of spawn is
# three lattice cells of unbroken floor, and that key moves 48 pixels. At
# least one of those two silences is very likely FALSE.
#
# ------------------------------------------------------------------------
# STATE 29: body home at lattice (1,2); panel configuration B; FOURTEEN meter
# cells burned, cols 50-63 of row 63; next command index 30, EVEN. Eleven
# lattice cells reachable, the body has stood in TWO. Three steps east along
# lattice row 1 reach the cell beside the knob; the knob is the far end of one
# connected colour-8 wire whose near end is the comb; the comb gates every
# route to the socket at (8,7). 50 meter cells against a route of about
# nineteen steps: the budget is not binding, waste is.
#
# THE ARGUMENT FOR THE NEXT COMMAND, AS CRITERIA:
#
#  (1) KEY(5) AT SPAWN IS NOW THE CHEAPEST MULTI-BIT PROBE ON THE BOARD, and
#      it is the one command whose value the cut created. One press yields
#      three independent bits in one legible diff: 23 cells vindicates the
#      cut, 0 cells refutes it and puts thirteen rules into repair, 71 cells
#      says ACTION5 is UNDO; and (63,49) burning or not settles meter parity,
#      because key 5 is odd and index 30 is even. A fourth bit comes free on
#      the following command: if the panel toggled, the next A2 from spawn
#      takes 7 internal frames instead of 9.
#
#  (2) A KEY WHOSE PREDICTED INERTNESS HAS NO WITNESS IS NOT A NO-OP, IT IS
#      AN UNTESTED CLAIM. key(3) and key(4) at spawn are both in that state.
#      Ranking them below key(2) because the manual draws nothing for them is
#      circular: the manual draws nothing because nobody has pressed them here.
#
#  (3) THE EAST KEY IS ONE PRESS AWAY AND UNBLOCKED. East is key(3) or
#      key(4); key(1) was excluded from east at t1. At spawn west is void and
#      east is open floor, so either one settles it -- if it steps it is east,
#      if it does not the other is east by elimination.
#
#  (4) PARITY SEPARATION COMPOUNDS, SO TAKE THE ODD KEY FIRST. Twenty-nine
#      commands, twenty-nine times a key whose parity matched its index's,
#      zero separation between action-keying and command-parity. An odd key at
#      index 30 separates; the even key it displaces separates again at 31.
#
#  (5) EVERY REFUTATION SO FAR IS THE SAME UNDRAWABLE PIXEL. Twenty-four
#      across six rounds, every divergence set inside the meter's leading edge
#      -- cells that were board at the instant they burned. Ranking by
#      refutation-fired therefore ranks key(2) first forever.
#
#  (6) A2 FROM SPAWN IS EXHAUSTED. Thirteen presses, 312/312 coverage, cascade
#      split settled 13/13. A fourteenth witness buys nothing and costs one
#      command and one bar cell.
#
#  (7) ONE PRESS IS ONE LATTICE CELL, 13/13. Distances are lattice cells.

order     prefer_a_command_whose_outcome_splits_a_rule_the_cut_just_created  [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     take_the_separation_that_compounds_before_the_one_that_does_not   [proof: lean]
order     buy_the_probe_that_closes_three_questions_before_one_that_closes_one [proof: lean]
order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full     [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead    [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead     [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead              [proof: lean]
prune     repeats_a_key_already_pressed_from_this_very_cell => dead           [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead         [proof: lean]
prune     key_parity_equals_index_parity_while_the_two_readings_are_tied => dead [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                   [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead      [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead      [proof: lean]
prune     meter_exhausted and not goal => dead                                [proof: lean]

heuristic newly_unguarded_rules_a_command_would_put_to_first_test           [admissible: lean]
heuristic keys_whose_inertness_here_rests_on_no_witness                      [admissible: lean]
heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                    [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]

prefer    a_press_that_tests_a_guard_removed_for_failing_the_gain_test      [ev: 13/13 unguarded]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed     [ev: 2/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on              [ev: 0/24 commands]
prefer    a_key_whose_parity_differs_from_the_command_index                 [ev: 0/29 commands]
prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree       [ev: 15/17 no_ops]
prefer    a_press_at_home_that_splits_up_from_undo_from_return              [ev: 13/13 key5]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 29/29 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                    [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                     [ev: 2/7 keys]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered           [ev: 1/1 levels]
```

## Why you are being called: the surprises that fired

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '65612ce2b219fbe6', the world answered '132f0bf441d96376'

```json
{
 "action": 5,
 "observed": "132f0bf441d96376",
 "predictions": {
  "inert": "70eb49bbc21b44e9",
  "manual": "65612ce2b219fbe6",
  "without_key1_inert_at_spawn": "65612ce2b219fbe6",
  "without_key2_body_arrives": "65612ce2b219fbe6",
  "without_key2_body_leaves": "65612ce2b219fbe6",
  "without_key3_inert_below_spawn": "65612ce2b219fbe6",
  "without_key5_body_clears": "65612ce2b219fbe6",
  "without_key5_body_respawns": "65612ce2b219fbe6",
  "without_key5_slot1_dims": "65612ce2b219fbe6",
  "without_key5_slot1_lights": "70eb49bbc21b44e9",
  "without_key5_slot2_centre_darkens": "65612ce2b219fbe6",
  "without_key5_slot2_centre_resets": "70eb49bbc21b44e9",
  "without_key5_slot2_ring_resets": "70eb49bbc21b44e9",
  "without_key5_slot2_row1_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row2_left_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row2_right_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row3_lights": "65612ce2b219fbe6",
  "without_key5_underline1_dims": "65612ce2b219fbe6",
  "without_key5_underline1_lights": "70eb49bbc21b44e9",
  "without_key5_underline2_dims": "70eb49bbc21b44e9",
  "without_key5_underline2_lights": "65612ce2b219fbe6",
  "without_meter_burn_key2_next": "65612ce2b219fbe6",
  "without_meter_burn_key2_rightmost": "65612ce2b219fbe6",
  "without_meter_burn_key4_next": "65612ce2b219fbe6"
 },
 "probe_id": "P-25"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '70eb49bbc21b44e9', the world answered '132f0bf441d96376'

```json
{
 "action": 5,
 "observed": "132f0bf441d96376",
 "predictions": {
  "inert": "65612ce2b219fbe6",
  "manual": "70eb49bbc21b44e9",
  "without_key1_inert_at_spawn": "70eb49bbc21b44e9",
  "without_key2_body_arrives": "70eb49bbc21b44e9",
  "without_key2_body_leaves": "70eb49bbc21b44e9",
  "without_key3_inert_below_spawn": "70eb49bbc21b44e9",
  "without_key5_body_clears": "70eb49bbc21b44e9",
  "without_key5_body_respawns": "70eb49bbc21b44e9",
  "without_key5_slot1_dims": "65612ce2b219fbe6",
  "without_key5_slot1_lights": "70eb49bbc21b44e9",
  "without_key5_slot2_centre_darkens": "65612ce2b219fbe6",
  "without_key5_slot2_centre_resets": "70eb49bbc21b44e9",
  "without_key5_slot2_ring_resets": "70eb49bbc21b44e9",
  "without_key5_slot2_row1_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row2_left_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row2_right_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row3_lights": "65612ce2b219fbe6",
  "without_key5_underline1_dims": "65612ce2b219fbe6",
  "without_key5_underline1_lights": "70eb49bbc21b44e9",
  "without_key5_underline2_dims": "70eb49bbc21b44e9",
  "without_key5_underline2_lights": "65612ce2b219fbe6",
  "without_meter_burn_key2_next": "70eb49bbc21b44e9",
  "without_meter_burn_key2_rightmost": "70eb49bbc21b44e9",
  "without_meter_burn_key4_next": "70eb49bbc21b44e9"
 },
 "probe_id": "P-26"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '65612ce2b219fbe6', the world answered '121cbbc9c93803ed'

```json
{
 "action": 5,
 "observed": "121cbbc9c93803ed",
 "predictions": {
  "inert": "70eb49bbc21b44e9",
  "manual": "65612ce2b219fbe6",
  "without_key1_inert_at_spawn": "65612ce2b219fbe6",
  "without_key2_body_arrives": "65612ce2b219fbe6",
  "without_key2_body_leaves": "65612ce2b219fbe6",
  "without_key3_inert_below_spawn": "65612ce2b219fbe6",
  "without_key5_body_clears": "65612ce2b219fbe6",
  "without_key5_body_respawns": "65612ce2b219fbe6",
  "without_key5_slot1_dims": "65612ce2b219fbe6",
  "without_key5_slot1_lights": "70eb49bbc21b44e9",
  "without_key5_slot2_centre_darkens": "65612ce2b219fbe6",
  "without_key5_slot2_centre_resets": "70eb49bbc21b44e9",
  "without_key5_slot2_ring_resets": "70eb49bbc21b44e9",
  "without_key5_slot2_row1_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row2_left_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row2_right_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row3_lights": "65612ce2b219fbe6",
  "without_key5_underline1_dims": "65612ce2b219fbe6",
  "without_key5_underline1_lights": "70eb49bbc21b44e9",
  "without_key5_underline2_dims": "70eb49bbc21b44e9",
  "without_key5_underline2_lights": "65612ce2b219fbe6",
  "without_meter_burn_key2_next": "65612ce2b219fbe6",
  "without_meter_burn_key2_rightmost": "65612ce2b219fbe6",
  "without_meter_burn_key4_next": "65612ce2b219fbe6"
 },
 "probe_id": "P-27"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '70eb49bbc21b44e9', the world answered '121cbbc9c93803ed'

```json
{
 "action": 5,
 "observed": "121cbbc9c93803ed",
 "predictions": {
  "inert": "65612ce2b219fbe6",
  "manual": "70eb49bbc21b44e9",
  "without_key1_inert_at_spawn": "70eb49bbc21b44e9",
  "without_key2_body_arrives": "70eb49bbc21b44e9",
  "without_key2_body_leaves": "70eb49bbc21b44e9",
  "without_key3_inert_below_spawn": "70eb49bbc21b44e9",
  "without_key5_body_clears": "70eb49bbc21b44e9",
  "without_key5_body_respawns": "70eb49bbc21b44e9",
  "without_key5_slot1_dims": "65612ce2b219fbe6",
  "without_key5_slot1_lights": "70eb49bbc21b44e9",
  "without_key5_slot2_centre_darkens": "65612ce2b219fbe6",
  "without_key5_slot2_centre_resets": "70eb49bbc21b44e9",
  "without_key5_slot2_ring_resets": "70eb49bbc21b44e9",
  "without_key5_slot2_row1_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row2_left_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row2_right_lights": "65612ce2b219fbe6",
  "without_key5_slot2_row3_lights": "65612ce2b219fbe6",
  "without_key5_underline1_dims": "65612ce2b219fbe6",
  "without_key5_underline1_lights": "70eb49bbc21b44e9",
  "without_key5_underline2_dims": "70eb49bbc21b44e9",
  "without_key5_underline2_lights": "65612ce2b219fbe6",
  "without_meter_burn_key2_next": "70eb49bbc21b44e9",
  "without_meter_burn_key2_rightmost": "70eb49bbc21b44e9",
  "without_meter_burn_key4_next": "70eb49bbc21b44e9"
 },
 "probe_id": "P-28"
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
 "first_divergence": null,
 "proof_layer_available": false,
 "replay": {
  "detail": "29/29 transitions replay exactly",
  "matched": 29,
  "ok": true,
  "transitions": 29
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
  "detail": "no (state, action) among 30 x 5 admitted two rules, and all 150 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 150,
  "pairs_nominal": 150,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 30,
  "states_reconstructed": 30,
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
# theory.dsl -- world observed for 34 states / 33 transitions
# (RESET + A1 A2 A3 A4 A5, then A2 A5 twelve times, then A5 A5 A5 A5).
# 87 cells have ever changed; this manual names and owns all 87.
#
# WHAT THIS ROUND COST AND WHAT IT BOUGHT
#
#   Last round I deleted `colored(spawn_probe, 5)` from thirteen panel rules
#   on a gain-test argument, and said in as many words: my manual now
#   predicts key(5) at spawn toggles 23 panel cells, no frame has ever
#   tested that, if it is wrong I pay 23 pixels and learn something worth
#   more than 23 pixels. THE WORLD ANSWERED. Four commands, all ACTION5,
#   all at spawn, indices 30-33. The panel did not move. Not one panel
#   pixel changed in four presses. THE CUT WAS WRONG AND IT IS REVERSED:
#   the guard is restored on all thirteen rules, and it now has what it
#   never had before -- FOUR NEGATIVE WITNESSES. 13 toggles with the body
#   away, 0 toggles with the body home. The atom is earned.
#
#   THE SAME FOUR COMMANDS SETTLED THE OTHER OPEN QUESTION, and settled it
#   the other way. Row 63 now reads 9 through col 47 and 1 from col 48:
#   SIXTEEN burns, two more than at state 29. Four presses of an ODD key,
#   at indices 30, 31, 32, 33, burned exactly twice -- at 30 and at 32.
#   Reading A (burns iff the key is 2 or 4) predicted ZERO burns and is
#   DEAD. Reading B (burns iff the command index is even) predicted exactly
#   two, in exactly those places, and is now 33/33 with a discriminating
#   set. The meter is a command counter and no key touches it.
#
#   AND THE FOUR COMMANDS PROVED THE THING I HAVE CARRIED AS A BELIEF SINCE
#   STATE 5. s30 and s31 are pixel-identical (distinct_states 30 against 34
#   states = four coincidences: s1=s0, s3=s2, s31=s30, s33=s32). From s30
#   the world was given ACTION5 and returned s31 = s30, identity. From s31,
#   the same pixels, the world was given ACTION5 AGAIN and returned s32,
#   one pixel burned. SAME STATE, SAME ACTION, DIFFERENT SUCCESSOR. This
#   world is NOT a function of the drawn frame, and constraint 5 obliges my
#   manual to be one. See the_world_is_not_a_function_of_the_drawn_frame.
#
#   THE BILL, STATED PLAINLY: replay can no longer be perfect. t31 and t33
#   replay exactly (identity). t30 and t32 each miss by ONE pixel, the
#   parity burn, which no guard in this language can express and which was
#   board at the instant it burned. Expect 31/33. That is the floor, not a
#   defect I can repair, and I would rather post it than hide it behind an
#   action-keyed burn rule that is now known to be a mis-attribution.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Dark    { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  landmark spawn_probe  # arc-cell: (8, 14)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t33 compress: 51]
  Vacated [segment: dynamic_colour_5 ev: t2-t29 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20,t22,t24,t26,t28 cov: 312/312]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20,t22,t24,t26,t28 cov: 312/312]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12,t14,t16,t18,t20,t22,t24,t26,t28 cov: 12/12]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 cov: 312/312]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 cov: 312/312]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25,t29 cov: 56/56]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23,t27 cov: 48/48]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23,t27 cov: 18/18]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23,t27 cov: 48/48]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23,t27 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11,t15,t19,t23,t27 cov: 18/18]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

goal:

laws:
  invariant glyph9_instances count(Glyph9) = 51 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4009 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 16 [status: counted]

  theorem the_cut_is_reversed_and_the_guard_is_now_earned "THE ROUND'S FIRST STRUCTURAL CHANGE AND IT IS AN UNDO OF MINE. Last round I deleted colored(spawn_probe, 5) from thirteen panel rules, on the argument that its thirteen positive witnesses were confounded -- every ACTION5 in history had followed an ACTION2, so `key(5) was pressed` and `the body is away` were the same thirteen events, and constraint 3 says a conjunct with no discriminating negative explains no pixel. THE ARGUMENT WAS SOUND AND THE CONCLUSION WAS FALSE, and the difference between those two sentences is the whole value of this round. The manual then predicted 23 panel cells for key(5) at spawn; the world was asked four times and answered zero panel cells four times. THE ATOM NOW HAS FOUR NEGATIVE WITNESSES -- t30, t31, t32, t33, all ACTION5, all with the body home at spawn, all with the panel unmoved in configuration B, confirmed cell by cell in the current frame which still reads 222/2.2/222 at cols 1-3 and 999/9.9/999 at cols 5-7 with row 5 dark at 1-3 and lit at 5-7. So the guard is restored on all thirteen rules and it is no longer a correlation: 13/13 toggles with the body away, 0/4 with the body home. WHAT I WOULD DO AGAIN: buy a negative witness by removing an unearned guard, because an unwitnessed silence is invisible and an unwitnessed prediction of change is answered in one press. WHAT I WOULD DO DIFFERENTLY: the answer arrived on the FIRST press and the next three bought nothing new about the panel -- they were paid for by the meter, which is the only reason this round was not a waste."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_meter_is_command_parity_and_no_key_touches_it "SETTLED, and settled against the reading my rules encode. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right; the current frame reads 9 through col 47 and 1 from col 48 to col 63, SIXTEEN burns after thirty-three commands. Burns occurred at command indices 2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32 -- every even index, sixteen of them, no odd index ever. READING A said burns iff the key is 2 or 4. READING B said burns iff the index is even. For twenty-nine commands the two were numerically identical because every command was an even key at an even index or an odd key at an odd index; I said the separator was one odd key at an even index and cost one command. THIS ROUND SPENT FOUR ODD KEYS AT INDICES 30-33 AND READING A PREDICTED ZERO BURNS. Two burns happened, at 30 and 32, exactly where B says. READING A IS DEAD. The meter counts commands, not keys, and it does not care which key. CONSEQUENCE FOR MY THREE BURN RULES: their attribution is now KNOWN FALSE. I keep them anyway and say why -- they are the shortest expressible shadow of the true law, they draw 14 of the 16 burns on replay, and every alternative is worse. A key(5) burn rule would fire at t31 and t33 where nothing burned; an action-free burn rule would fire at every odd index from t5 on and lose seventeen transitions. Fourteen right, two structurally unreachable, and no better option inside this grammar."
    [depends: meter_burn_key2_next, meter_burn_key4_next, the_world_is_not_a_function_of_the_drawn_frame  probe: passed]

  theorem the_world_is_not_a_function_of_the_drawn_frame "PROVEN THIS ROUND, after carrying it as a belief since state 5. The proof needs two pixel-identical states from which the SAME action produced different successors, and the store hands me the pair: distinct_states is 30 against 34 states, so there are exactly four coincidences, and they are s1=s0, s3=s2, s31=s30, s33=s32. The first two are the old sterile pair -- different keys were pressed from each, so they test nothing. THE LAST TWO ARE NOT. Refutations P-25 and P-26 report the SAME observed hash 132f0bf441d96376, and P-27 and P-28 the same 121cbbc9c93803ed: so s31 = s30 and s33 = s32 to the pixel. Now read the transitions. t31 acted on s30 with ACTION5 and returned s31, which equals s30 -- identity. t32 acted on s31, THE SAME PIXELS, with ACTION5 AGAIN, and returned s32, which differs by one burned bar cell. Same state, same action, two different successors. The hidden bit is the command counter the meter reads and no guard in this language can. WHAT IT COSTS ME IS EXACT AND UNAVOIDABLE: constraint 5 obliges my manual to be a function of the frame, so my manual must be wrong about at least one member of every such pair, and it is wrong about t30 and t32 by exactly one pixel each. Expect replay 31/33 and do not read those two as repairable."
    [depends: the_meter_is_command_parity_and_no_key_touches_it  probe: passed]

  theorem the_four_refutations_are_one_experiment_and_it_paid_for_itself "P-25 through P-28 are four reports of ONE experiment: ACTION5 pressed four times at spawn. Their arithmetic is worth reading because it is how I reconstructed the round. The manual prediction of P-25 is the inert field of P-26 and vice versa -- that is the harness rolling my predicted frame forward without resyncing, so my toggled panel became my next starting point and toggled back, the same closed 2-cycle as the last five rounds. What is NEW is the observed column: P-25 and P-26 observed the same hash, P-27 and P-28 observed the same hash. The world's successors were change, no-change, change, no-change, and the changes are one pixel each at indices 30 and 32. THREE THINGS FELL OUT OF FOUR COMMANDS: the panel guard is earned (four negatives), the meter is command parity (reading A refuted), and the world is not a function of the frame (a pixel-identical pair with the same key and different successors). Compare the six rounds before it: twenty-four refutations, every divergence set a subset of the meter's leading edge, ZERO rules contradicted, nothing learned. A prediction the world can answer is worth more than a prediction that is safe, and this is the evidence for that claim rather than the slogan."
    [depends: the_cut_is_reversed_and_the_guard_is_now_earned, the_meter_is_command_parity_and_no_key_touches_it  probe: passed]

  theorem silence_is_a_prediction_and_exactly_two_of_my_spawn_silences_are_still_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says `I do not know`, it says `nothing happens`, in the same voice it uses for things it has seen. Audit the five keys at spawn after this round. key(1) inert: WITNESSED, t1, zero cells. key(2) moves 48 body cells: witnessed thirteen times. key(5) inert: WITNESSED FOUR TIMES, t30-t33, which is the round's gain -- it was an unwitnessed prediction of change last round and it is now a witnessed silence. key(3) inert: NO WITNESS at spawn, pressed once ever, at t3, from one cell south. key(4) inert: NO WITNESS at spawn, pressed once ever, at t4, from one cell south. TWO OF FIVE SILENCES AT SPAWN ARE FORGED DEATH CERTIFICATES and the elimination is now tight enough to say more: ACTION2 is down, ACTION1 is not east (t1, spawn, east open, nothing moved), ACTION5 is not east (t30-t33, spawn, east open, nothing moved). So EAST IS ACTION3 OR ACTION4, one of my two forged silences is FALSE, and one press of either settles which -- if it steps it is east, if it does not the other is east by elimination. That is the cheapest unclaimed bit on the board."
    [depends: the_action_map_after_thirtythree_transitions, the_cut_is_reversed_and_the_guard_is_now_earned  probe: pending]

  theorem the_action_map_after_thirtythree_transitions "WITNESSED: ACTION2 IS DOWN, 13/13, six rows south, one lattice cell. ACTION5 returns the body from lattice (2,2) to (1,2), 13/13, and does NOTHING at spawn, 4/4. NEGATIVE INFORMATION, stated as negative. At spawn (1,2) up and left are void while down and right are open floor; ACTION1 did nothing there at t1, so ACTION1 IS NEITHER DOWN NOR RIGHT; ACTION5 did nothing there four times, so ACTION5 IS NEITHER DOWN NOR RIGHT either. At (2,2) up was open (the body had just vacated rows 8-12) and down was open (rows 20-24 are floor) while left and right were void; ACTION3 and ACTION4 each did nothing there, so NEITHER IS UP AND NEITHER IS DOWN. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else -- and the something-else is now constrained too, see what_action5_is. The conventional mapping for this action family agrees, which is a prior and not evidence. THIRTY-THREE COMMANDS AND NOT ONE HAS TESTED THE EAST KEY. The test is one press from where the body stands."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_after_four_presses_at_home "Three readings survived thirteen presses because all thirteen were made from one cell south of spawn, where UP, UNDO and RETURN are indistinguishable. This round pressed it FOUR TIMES AT SPAWN and the body did not move a pixel. UP predicts exactly that -- north of spawn is void, the move is blocked. RETURN predicts exactly that -- the body is already home. UNDO in its plain form is REFUTED: t29 was an effective ACTION5 that carried the body home, so an undo at t30 would have carried it back south, and it did not. UNDO survives only in a stack variant where no-ops are not pushed and t29 emptied the stack; I record that variant rather than pretend it is dead, but I no longer rank it. THE SEPARATOR IS NOW CHEAP AND NAMED: press ACTION5 from any cell that is neither spawn nor one south with open floor above it. From lattice (1,3), one step east, UP is void so UP predicts nothing while RETURN predicts a 48-pixel jump west to spawn. That is one more reason the east key is the next thing to buy. The coupling I still cannot break is the panel's: it toggles on every effective ACTION5 and on no ineffective one, so it is a counter of ACTION5's successes, and the 7-versus-9 cascade split says its state is not merely cosmetic."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_cut_is_reversed_and_the_guard_is_now_earned  probe: pending]

  theorem the_panel_guard_is_earned_but_its_extrapolation_is_not "The restored guard reads colored(spawn_probe, 5), which is `cell (8,14) renders floor`, which is `the body is not at spawn`. Every one of the thirteen positives had the body at ONE specific cell, lattice (2,2), and every one of the four negatives had it at spawn. So a guard reading `the body is at (2,2)` -- a second landmark at (14,14) tested for colour 9 -- fits the same 13 positives and the same 4 negatives EXACTLY as well. The two guards differ only at cells the body has never occupied: from a third cell, spawn_probe says the panel toggles and a south_probe would say it does not. I choose spawn_probe because it is the guard that already replayed twenty-five transitions and because the panel reads as a counter of effective ACTION5s rather than of one location, but I am naming the confound BEFORE it costs me, unlike last round. THE PROBE: get the body to any third lattice cell and press ACTION5. Panel toggles, spawn_probe wins; panel still, the guard is really about (2,2) and thirteen rules need a different landmark."
    [depends: key5_slot1_dims, the_cut_is_reversed_and_the_guard_is_now_earned  probe: pending]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over THIRTEEN toggles -- every odd index t5 through t29 -- 23 cells every time; ACTION2 has never touched a panel pixel in thirteen presses; and ACTION5 AT HOME has never touched one in four presses. CONFIGURATION A: slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B, which states 29 through 33 and the current frame all show: slot 1 a hollow colour-2 ring with dark underline, slot 2 a hollow colour-9 ring with dark centre and lit underline. mdl_segmenter corroborates by frame index and has never seen my rules: colour-1 nine-cell tracks obj1 (0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16), obj12 (19-20), obj14 (23-24), obj16 (27-28); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17-18), obj13 (21-22), obj15 (25-26), obj17 (29 onward, and note it is the ONLY colour-2 track to run past two frames -- five frames, 29 through 33, which is the panel standing still for this round's four commands). Its obj0 (colour 9, eight cells, 3x3, all 34 frames) and obj2 (colour 9, 1x3, all 34) persist while it narrates 26 MOVE events: the hollow ring and the lit underline do not appear and vanish, they TRAVEL between the two slots. One marker, two seats, colour 9 marks the occupied seat. What the seats HOLD is still unknown and I will not guess. I cannot model it as a mover either: the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring travelling four columns is not a move, and ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9. ACTION2 returned SEVEN frames from configuration A (t2, t8, t12, t16, t20, t24, t28) and NINE from configuration B (t6, t10, t14, t18, t22, t26), 13/13 with no exception. ACTION5 returned nine frames on all thirteen effective presses; every no-op returned one. THE NET EFFECT IS IDENTICAL IN ALL THIRTEEN ACTION2 PRESSES, so this costs nothing in replay and buys nothing in prediction, and it remains the only evidence that the panel does anything besides display. I record it as a limitation of my own semantics: cascade single_frame compares only the net, so up to eight intermediate frames per command are discarded unread. LIVE PREDICTION, now that the panel is confirmed stuck in configuration B: the next ACTION2 from spawn must take NINE internal frames. Seven would mean the panel's effect on the animation is not what I think, and it would cost me nothing to find out because the diff is free."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_meter_edge_saturates_the_refutation_channel_and_parity_makes_it_worse "A law of this manual rather than of this world, and now the most expensive fact on the board. Each of the 64 cells of the row-63 bar burns EXACTLY ONCE, advancing leftward. At the instant a cell burns it has never changed, so it is board, so no instance exists for it, so NO RULE OF MINE CAN DRAW IT. Therefore my burn rules have zero predictive value on the leading edge and full value on replay -- a division of labour, not a contradiction. WHAT PARITY ADDS: before this round I could tell myself that only keys 2 and 4 burned, so a refutation on key 5 meant something. Now I know EVERY EVEN-INDEX COMMAND BURNS, whatever the key, so every even-index command is scored a refutation before it is even chosen, and refutation-fired carries ZERO information at even indices. The next index is 34, EVEN: whatever I press, (63,47) burns, I cannot draw it, and I am refuted by exactly one pixel. Read refutations by their DIVERGENCE SET; where that set is a subset of the bar's leading edge, the manual is not implicated. All twenty-eight refutations across seven rounds have been exactly that."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_meter_is_a_budget_and_it_is_now_priced_correctly "Sixteen of sixty-four bar cells consumed after thirty-three commands. Under the settled parity reading the bar buys 48 more burns and therefore about 96 MORE COMMANDS, since every second one burns. I do not know that exhaustion ends the game -- no frame has shown it -- but 96 commands against a route I can see costing about nineteen steps plus interactions plus identification probes is not the binding constraint. The route: spawn (1,2) east three cells to (1,5) beside the knob, an unknown number of interactions there, three cells back west, seven cells south down lattice column 2 to (8,2), five cells east to the socket at (8,7). THE BINDING CONSTRAINT IS THIRTY-THREE COMMANDS SPENT AND THE BODY HAVING OCCUPIED TWO LATTICE CELLS. Note that parity makes waste cheaper than I feared and repetition no cheaper: a wasted command still costs half a bar cell."
    [depends: the_meter_is_command_parity_and_no_key_touches_it, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_two_no_op_rules_still_fail_the_gain_test_and_i_keep_them_for_a_weaker_reason "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has one witness on a transition where zero cells changed, and the manual would replay identically without them. They were bought to test the alphabet hypothesis, which is refuted, so THAT reason is gone. The reason I keep them is weaker and I will not dress it up: deleting them narrows certify's adjudicated action set from five keys to three, removing information I can see for a benefit -- two lines -- I cannot measure. This round supplies a second, better reason: my one deletion of an unearned thing was reversed by the world four commands later. Conservatism about deletions is not a virtue in general, but it is the correct posture toward deletions that change NO prediction, and these two change none. They remain declared failures of the gain test and the two cheapest deletions in this manual."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_key_alphabet_hypothesis_is_refuted  probe: passed]

  theorem the_key_alphabet_hypothesis_is_refuted "Kept compressed, because it is settled. I once hypothesised that the command chooser derives its candidate keys from the act=key(n) literals in my rules, and that this was why round after round bought A2 A5. I paid two witnessed no-op rules to widen the alphabet. THE INSTRUMENT MOVED AS PREDICTED -- certify went from 3 actions and 54 pairs to 5 actions and now 150 pairs, 0 clashes, 0 step crashes -- and THE COMMANDS DID NOT MOVE. Alphabet width is not sufficient. What DID move the commands is now known: last round I gave key(5) at spawn a predicted 23-cell change and the chooser pressed key(5) four times. THE CHOOSER FOLLOWS THE MANUAL'S PREDICTED CHANGE. That is a lever and it is also a trap, because the honest manual after this round predicts change for exactly one key at spawn again."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_parity "Two expressive holes, and this round they interlock. FIRST: there is no third outcome for a (state, action) pair -- not `no change` and not a named successor, but `unobserved, the manual declines to predict`. Rules produce events, absence of a rule produces identity, and the compiled step is total. The one lever the grammar offers is deleting an unearned guard, which converts an unwitnessed silence into an unwitnessed PREDICTION OF CHANGE, testable in one press; I used it, it was answered, and the answer was no -- which is exactly what the lever is for. SECOND: the true meter law is `burns iff the command index is even`, and the guard language reads pixels and the action name and nothing else. There is no command counter, no phase pixel, and the frame provably does not determine the parity, since s30 and s31 are identical and only one of them was followed by a burn. So the parity law CANNOT be written here at all, at any length. If a future desk gains one expressive extension, ask for a state counter before asking for `not`."
    [depends: the_world_is_not_a_function_of_the_drawn_frame, the_cut_is_reversed_and_the_guard_is_now_earned  probe: passed]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4009 + dynamic 87 = 4096, and 51+24+9 = 84 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 87. Consequence: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This is the seventh consecutive round in which that sentence, written in advance, was the entire content of every refutation. The two cells burned this round, (63,49) and (63,48), are dynamic NOW, which is why Glyph9 went 49 to 51 and the burned count 14 to 16 -- but they were board when they burned, so t30 and t32 are one wrong pixel each even after the repair, and this time the repair does not even restore replay, because no rule of mine burns on key 5. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, plus one for the parity burn if the index is even, 24 for the second step, 0 thereafter. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 87 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 16 are the burned right end of row 63: cols 48 through 63, two more than last round. 23+24+24+16 = 87 = dynamic_cells. By frame-0 colour: 51 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 16 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 51+9+24 = 84 = cells_needing_an_owner exactly, and 4096-87 = 4009 = constant_cells exactly."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended thirteen times and all thirteen started at spawn, so no rule turns Vacated pixels from 9 back to 5 on an ACTION2: rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below-six(?v), 5) then recolored(?v, 5). One ACTION2 from lattice (2,2) buys it. (2) EAST-WEST MOTION. Whatever the east key is, it needs a pair: a leaves rule over Glyph9 guarded on colour 9 with rightof-six rendering 5, and its arrives twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) THE PARITY BURN, which is not a missing rule but an inexpressible one, and which will cost exactly one pixel on every even-index command for the rest of the game. I state all three prices in advance so none can be mistaken for a surprise."
    [depends: key2_body_arrives, the_meter_edge_saturates_the_refutation_channel_and_parity_makes_it_worse  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all 150 adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth below is row 69. So colored(off-board, k) is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen rules rest on this and every row and column discrimination in the panel is built from it: the k-th above is off-board exactly when k exceeds the row, so row 1 is above-twice equals wall, row 3 is a colour test on above-twice -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column: col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice, pairwise exclusive, which is why the ambiguity check reports 0 clashes. Restoring the spawn_probe conjunct only tightens this: it narrows all thirteen panel rules by the same atom, so no pair that was exclusive before can clash now. Not one rule uses `not`, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated one row per internal frame and the world reports the whole animation for a single action; cascade single_frame compares only the net, which is identical for all thirteen ACTION2 presses (48 body cells, rows 8-18, cols 14-18) whether the command took 7 frames or 9. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, THIRTEEN times. ONE PRESS IS ONE LATTICE CELL, 13/13, and every distance in the playbook rests on that."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame and unchanged: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open, C=6 holds the knob, C=7 does not exist in this band; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2, plus a fragment of floor at row 48 cols 42-50 that is one row deep and cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in thirty-four frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it has been at spawn in twenty of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed THIRTEEN times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows, col 49 and col 43 are separator columns -- so what is drawn is the north, south and east walls of lattice cell (8,7), painted in colour 9, with the west wall at col 43 left as FLOOR. Inside it, rows 50-54 cols 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, col 50 rows 49-56 is a one-cell strip of floor that leads nowhere. Overlay the body standing in lattice (8,7) -- 5x5, aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in thirty-four frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem pixel at (12,40), colour 8 filling col 40 from row 12 down to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18. It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in thirty-four frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell -- the eight knob pixels other than its centre, plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Thirty-three commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after thirty-four states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. I have no witness for key(6) or key(7), so no rule can name them, so they sit outside the manual's alphabet -- which I once thought decisive and now know is not sufficient, since keys 1 and 3 are inside the alphabet and were still never chosen."
    [depends: the_key_alphabet_hypothesis_is_refuted  probe: pending]

  theorem the_goal_section_is_empty_on_purpose "Still empty, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and fifty siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would be true of the body standing one cell south of spawn, which is not a win. The alternatives fail too: count(Glyph9, color = 5) = 24 is true of every state where the body is anywhere but home, and a Wire type on colour 8 would have zero instances because every colour-8 cell is constant, so count(Wire) = 0 would be true at RESET. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. I name the price plainly: is_goal compiles to False, no plan terminates, and nothing ranks one command above another except whether the command is predicted to change pixels -- which, with the guard restored, admits exactly ONE key at spawn again, and that key is the one that has been pressed thirteen times."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_key_alphabet_hypothesis_is_refuted  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The next command has index 34, EVEN, so (63,47) BURNS WHATEVER I PRESS and I cannot draw it: every option below carries exactly one guaranteed wrong pixel and refutation-fired therefore carries zero information this turn. The body is at spawn, the panel is in configuration B, sixteen meter cells are burned. ACTION3 at spawn: my manual predicts ZERO cells and has NO WITNESS for that, so this is the press I want -- 48 undrawable cells plus the burn means ACTION3 IS EAST and the map is closed; 1 cell, the burn alone, means ACTION3 is not east and therefore ACTION4 IS EAST by elimination, since ACTION1 and ACTION5 are both excluded from east at this very cell. Either answer names the east key. ACTION4 at spawn: the same experiment with the labels swapped. ACTION1 at spawn: 1 cell, key1_inert_at_spawn firing as a no-op, the silence I already have a witness for, nothing bought. ACTION5 at spawn: 1 cell, now WITNESSED four times, nothing bought. ACTION2 at spawn: 48 body cells I draw correctly plus the burn -- one wrong pixel and nothing learned, because key2_body_leaves and key2_body_arrives are at 312/312, except for one free datum, the cascade must be NINE frames from configuration B. If ACTION5 is pressed at spawn a fifth time and the panel moves, this manual is wrong twice over and I would want to know that more than anything else on this list."
    [depends: the_meter_is_command_parity_and_no_key_touches_it, silence_is_a_prediction_and_exactly_two_of_my_spawn_silences_are_still_forged  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept compressed because the lesson is structural and cost a full round. Thirteen panel rules once carried colored(spawn_probe, 5) while the landmark line read a prose placeholder instead of a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The coda, now complete: that same atom was deleted last round for failing the gain test and is restored this round with four negative witnesses. It has been wrong by pointing nowhere, wrong by being absent, and is now right for a reason I can state. The landmark reads (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because a future desk will be tempted by the same repair I have now rejected five times. To draw the leading-edge burn I would need an instance on a board cell. The arm offers exactly one lever, arc-instances: all, and its documented behaviour is to instance every cell OF THAT COLOUR THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance. The tempting workaround is a second declared type on colour 9 without arc-instances, hoping the arm seats one instance somewhere useful. I reject it: the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, the seat is unspecified, and any cell it landed on would be claimed twice, which is the constraint-5 error the grammar warns about in as many words. A landmark cannot help either, because landmarks are cells and every event in the language takes an object as its first argument. So the hole is a property of the arm, it is permanent for this level, and with parity confirmed it now costs one pixel on EVERY second command rather than only on key 2 and key 4."
    [depends: the_meter_edge_saturates_the_refutation_channel_and_parity_makes_it_worse  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter keeps a positive gain of +11940 bits at compression_ratio 0.527 on split_by_color=false, against -132740 bits when split by colour; its segmentation beats writing the pixels out and I still owe it nothing structural. Its eighteen tracks corroborate the panel by frame index and one of them corroborates THIS ROUND specifically: obj17, colour 2, first_frame 29, frames_present 5 -- the only colour-2 track longer than two frames, which is the panel standing still through t30-t33 exactly as the restored guard requires. obj0 and obj2 persisting through all 34 frames while the segmenter narrates 26 moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 16 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 33 transitions constrain rank 17 of 435 features, null space dimension 418, nearly every vector in it a law true over these states and unfalsified rather than confirmed -- and its single global law is my census. cegis_miner refuses on every track and its verdict, `the world does not narrate as one mover`, remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHAT THE LAST FOUR COMMANDS SETTLED =========
# Four presses of ACTION5 at spawn, indices 30-33. The panel did not move.
# Two bar cells burned, at indices 30 and 32.
#
#   1. THE CUT IS REVERSED. `colored(spawn_probe, 5)` is back on thirteen
#      panel rules and it now has FOUR NEGATIVE WITNESSES: 13/13 toggles
#      with the body away, 0/4 with the body home. ACTION5 at spawn is a
#      witnessed no-op.
#   2. THE METER IS COMMAND PARITY. Four ODD keys at indices 30-33 burned
#      exactly twice, at the two EVEN indices. The action-keyed reading
#      predicted zero burns and is dead. 33/33 for parity, with a
#      discriminating set at last. No key touches the meter.
#   3. THE WORLD IS NOT A FUNCTION OF THE DRAWN FRAME -- PROVEN. s30 and
#      s31 are pixel-identical; ACTION5 from s30 returned identity and
#      ACTION5 from s31 burned a cell. Same pixels, same key, two
#      successors.
#
# The wrong prediction was worth more than six safe rounds. But only the
# FIRST of the four presses answered it; presses two, three and four were
# the harness re-choosing the same key against a rolled-forward frame, and
# they were paid for by the meter alone. Buying a negative witness is right;
# buying it four times is not.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   At spawn (where the body IS):  key(2) -> 48 body cells
#                                  keys 1, 5 -> nothing, WITNESSED
#                                  keys 3, 4 -> nothing, NO WITNESS
#   Index 34 is EVEN, so (63,47) burns under every key and I cannot draw it:
#   one guaranteed wrong pixel this turn whatever is pressed, and
#   refutation-fired carries ZERO information at an even index.
#
# ========= THE ONE THING WORTH BUYING =========
# EAST IS ACTION3 OR ACTION4 AND ONE PRESS SETTLES IT.
#   ACTION2 is down (13/13). ACTION1 is not east -- pressed at spawn at t1
#   with east open, nothing moved. ACTION5 is not east -- pressed at spawn
#   four times this round with east open, nothing moved. Two candidates
#   remain and the body is standing where the test is free: east of spawn is
#   three lattice cells of unbroken floor, west is void.
#   Press ACTION3 (or ACTION4): if the body steps, that key is EAST and the
#   map is closed; if it does not, the OTHER is east by elimination. Both
#   outcomes name the east key. No other command on the board names anything.
#
# The advertised price of the step onto fresh ground: 48 pixels my manual
# cannot draw, because rows 8-12 cols 20-24 have never changed and are board.
# That is a refutation I have priced in advance and it must not be read as a
# defect. 24 pixels for the second step, 0 for the third.
#
# ------------------------------------------------------------------------
# STATE 33: body home at lattice (1,2); panel configuration B; SIXTEEN meter
# cells burned, cols 48-63 of row 63; next command index 34, EVEN. Eleven
# lattice cells reachable, the body has stood in TWO in thirty-four states.
# Three steps east along lattice row 1 reach the cell beside the knob; the
# knob is the far end of one connected colour-8 wire whose near end is the
# comb; the comb gates every route to the socket at (8,7). Under parity the
# bar buys about 96 more commands against a route of about nineteen steps:
# the budget is not binding, repetition is.

order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     buy_the_probe_that_closes_a_question_no_other_command_can_close  [proof: lean]
order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     ignore_refutation_pressure_entirely_when_the_index_is_even       [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     ranked_only_to_separate_the_two_meter_readings => dead             [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic live_readings_a_command_can_eliminate                             [admissible: lean]
heuristic commands_remaining_under_the_confirmed_parity_budget              [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 2/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 0/33 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 33/33 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_witnessed_no_op                [ev: 2/7 keys]
prefer    a_press_at_a_third_cell_that_splits_up_from_return               [ev: 4/4 key5_at_home]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

=== LOG ===
```json
[
  {"id": "P-25", "subject": "P-25/P-26 both observed 132f0bf441d96376; P-27/P-28 both observed 121cbbc9c93803ed", "verdict": "accept",
   "why": "Four ACTION5 presses at spawn, indices 30-33; equal observed hashes in each pair mean s31=s30 and s33=s32, so t31 and t33 were exact identities and t30/t32 changed one pixel each -- reconstructed independently by the store's distinct_states=30 against states=34, i.e. exactly four coincident pairs."},
  {"id": "P-26", "subject": "the panel did not toggle in four ACTION5 presses", "verdict": "accept",
   "as": "restored guard colored(spawn_probe, 5) on 13 panel rules",
   "why": "The cut I made last round predicted 23 panel cells per press and got 0 four times; the current frame still reads configuration B at rows 1-5 cols 1-7, identical to state 29, and mdl_segmenter's obj17 is a colour-2 track running 5 frames from 29 instead of the usual 2."},
  {"id": "P-27", "subject": "row 63 now reads 9 through col 47 and 1 from col 48", "verdict": "accept",
   "as": "the_meter_is_command_parity_and_no_key_touches_it",
   "why": "Sixteen burns after 33 commands, at exactly the even indices 2..32; four ODD keys at indices 30-33 produced burns at 30 and 32 only, which the action-keyed reading predicted would be zero."},
  {"id": "P-28", "subject": "s30 = s31 with ACTION5 giving identity then a burn", "verdict": "accept",
   "as": "the_world_is_not_a_function_of_the_drawn_frame [probe: passed]",
   "why": "Same pixels, same key, two different successors -- the exact pair the previous manual said it needed and could not find; the hidden bit is the command counter and no guard can read it."},
  {"id": "R-01", "subject": "colored(spawn_probe, 5) on key5_slot1_dims and 12 siblings", "verdict": "accept",
   "why": "Now 13 positive witnesses and 4 negative ones (t30-t33, body home, panel unmoved), so the conjunct discriminates and passes the gain test it failed last round on the evidence then available."},
  {"id": "R-02", "subject": "a key(5) burn rule to replay t30 and t32", "verdict": "reject",
   "why": "Any guard I can write over key(5) plus the bar's leading edge also fires at t31 and t33, where nothing burned, so it would trade two mismatches for four."},
  {"id": "R-03", "subject": "an action-free burn rule firing on every command", "verdict": "reject",
   "why": "It matches parity on even indices but also fires at every odd index from t5 on, where all leading-edge cells are already instanced at replay time -- seventeen new mismatches against two saved."},
  {"id": "R-04", "subject": "meter_burn_key2_rightmost, meter_burn_key2_next, meter_burn_key4_next", "verdict": "accept",
   "why": "Their causal attribution is now KNOWN FALSE -- the burns at t2, t4 and t6..t28 were parity burns that happened to fall on keys 2 and 4 -- but they draw 14 of the 16 burns on replay and both alternatives above are strictly worse; kept as a declared approximation, not as a claim."},
  {"id": "R-05", "subject": "key1_inert_at_spawn, key3_inert_below_spawn", "verdict": "accept",
   "why": "Still declared failures of the gain test: they change no prediction; kept only because deleting them narrows certify's adjudicated action set from 5 keys to 3 for no measurable benefit."},
  {"id": "R-06", "subject": "an east-leaves / east-arrives rule pair for ACTION3 or ACTION4", "verdict": "probe-pending",
   "why": "No witness exists -- east has never been pressed from a cell where it is open -- and the arrival pixels at rows 8-12 cols 20-24 are board, so the rule cannot be written and its first firing costs 48 undrawable pixels, priced in advance."},
  {"id": "R-07", "subject": "key2_floor_leaves, the second-descent rule", "verdict": "probe-pending",
   "why": "All thirteen descents started at spawn; one ACTION2 from lattice (2,2) would witness it and thirty-three commands have not bought that."},
  {"id": "O-01", "subject": "obj0/obj2/obj4 (colour 9 tracks)", "verdict": "accept", "as": "Glyph9, arc-instances: all, now 51 cells",
   "why": "Two more colour-9 cells became dynamic this round, (63,49) and (63,48), taking the type from 49 to 51 and the store's cells_needing_an_owner from 82 to 84."},
  {"id": "O-02", "subject": "obj1/obj6/obj8/obj10/obj12/obj14/obj16 (colour 1, 9 cells)", "verdict": "accept", "as": "Spent",
   "why": "Slot 2's solid block in configuration A, nine cells including its centre, unchanged this round."},
  {"id": "O-03", "subject": "obj5/obj7/.../obj17 (colour 2, 8 cells)", "verdict": "entailed", "as": "Glyph9 rendering 2",
   "why": "Slot 1's ring in configuration B is the same eight cells as in A, typed by frame-0 colour 9; obj17 running five frames from 29 is the panel standing still and is this round's independent corroboration."},
  {"id": "O-04", "subject": "obj3 (1006-cell colour-null blob)", "verdict": "reject",
   "why": "connected_components(4) merged the maze floor with the body ring; a second type on those pixels would claim cells Vacated already owns, which constraint 5 forbids."},
  {"id": "L-01", "subject": "dynamic_census", "verdict": "accept",
   "why": "23 panel + 24 spawn ring + 24 lower ring + 16 meter = 87 = dynamic_cells; 51+9+24 = 84 = cells_needing_an_owner; 4096-87 = 4009 = constant_cells."},
  {"id": "L-02", "subject": "invariant meter_cells_burned = 16, glyph9_instances = 51, board_cells = 4009", "verdict": "accept",
   "why": "Counted off the current frame's row 63 (48 nines then 16 ones) and reconciled with the store's three census numbers."},
  {"id": "L-03", "subject": "zero_space verdict THIN (rank 17 of 435, null space 418)", "verdict": "accept",
   "why": "Its own words; its single global law restates my census and nothing more, so nothing structural is owed to it."},
  {"id": "L-04", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "reject",
   "why": "True of the arm, false of the world -- there is one mover, a rigid 24-pixel ring, which the arm can only see as 24 simultaneous recolours."},
  {"id": "E-01", "subject": "the true meter law, 'burns iff the command index is even'", "verdict": "probe-pending",
   "why": "Inexpressible at any length: guards read pixels and the action name, there is no counter, and the frame provably does not determine the parity since s30 = s31 and only one of them burned. I wrote three action-masked burn rules instead and declared the attribution false in the_meter_is_command_parity_and_no_key_touches_it; the residue is exactly one wrong pixel per even-index command, forever."},
  {"id": "E-02", "subject": "a third transition outcome meaning 'unobserved, I decline to predict'", "verdict": "probe-pending",
   "why": "Still absent; absence of a rule compiles to identity, so every untested silence is asserted as fact. The only lever the grammar offers is deleting an unearned guard to convert a silence into a testable prediction of change -- I used it last round, the world answered no, and the answer was worth four commands."},
  {"id": "E-03", "subject": "replay can no longer reach 33/33", "verdict": "accept",
   "why": "t31 and t33 replay exactly; t30 and t32 miss by the one parity-burn pixel each. Expect 31/33, and read those two as the price of constraint 5 on a world that is not a function of its frame, not as a repairable defect."}
]
```
```
