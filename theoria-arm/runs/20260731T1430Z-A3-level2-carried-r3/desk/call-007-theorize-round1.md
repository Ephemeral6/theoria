# call-007-theorize-round1

model: `claude-opus-5` · 422347 ms · $1.493166 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 46403, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 46403, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 46403, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 46403, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 39782, "type": "message"}], "output_tokens": 39782, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 82,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4011,
 "distinct_states": 28,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 85,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 30,
 "steps": 30
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
9999999999999999999999999999999999999999999999999911111111111111
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

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 29,
  "n_states": 30,
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
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj0",
    "transitions": 29
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 4 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj1"
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 1,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj2",
    "transitions": 29
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
   "recolor": 40,
   "vanish": 13
  },
  "n_frames": 30,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 30,
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
    "frames_present": 30,
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
    "frames_present": 30,
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
    "frames_present": 30,
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
    "frames_present": 1,
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
    "baseline_bits": 25208,
    "compression_ratio": 0.526896,
    "events": 92,
    "gain_bits": 11926,
    "ms": 69,
    "script_bits": 13282,
    "split_by_color": false,
    "tracks": 18
   },
   {
    "baseline_bits": 25208,
    "compression_ratio": 6.235957,
    "events": 211,
    "gain_bits": -131988,
    "ms": 151,
    "script_bits": 157196,
    "split_by_color": true,
    "tracks": 77
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 85,
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
  "cells_needing_an_owner": 82,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4011,
  "distinct_states": 28,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 85,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 30,
  "steps": 30
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 85,
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
  "cells_dynamic": 85,
  "cells_used": 85,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 15,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.035294,
   "difference_rank": 15,
   "features": 425,
   "space_dimension": 410,
   "transitions": 29,
   "verdict": "THIN: 29 transitions constrain rank 15 of 425 features, so the null space has dimension 410 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 425,
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
     ]
```

The full proposal stream is 2810 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 26 states / 25 transitions
# (RESET + A1 A2 A3 A4 A5, then A2 A5 ten times over).
# 83 cells have ever changed; this manual names and owns all 83.
#
# WHAT THIS ROUND COST AND WHAT IT BOUGHT
#
#   Four commands -- A2 A5 A2 A5 -- for the FIFTH consecutive round. Four
#   refutations, P-17..P-20, chaining into a closed 4-cycle again (P-18
#   inert = P-17 manual, P-19 inert = P-18 manual, P-20 inert = P-19 manual,
#   P-17 inert = P-20 manual). The two wrong pixels are (63,53) at t22 and
#   (63,52) at t24: both were board at the instant they burned, both were
#   named in advance, both cost exactly one pixel. TWENTY refutations across
#   five rounds, every divergence set a subset of the meter's leading edge,
#   ZERO rules contradicted. Replay 21/21, responsibility 0/4096, ambiguity
#   0 clashes over 22 x 5 = 110 pairs.
#
#   LAST ROUND'S HYPOTHESIS IS DEAD, AND KILLING IT IS THE ROUND'S PRODUCT.
#   I suspected the command chooser read its menu off my rules' `act=key(n)`
#   literals -- certify then said `actions: 3`, `pairs_checked: 54`. I paid
#   two witnessed no-op rules to put key(1) and key(3) into the alphabet.
#   certify now says `actions: 5`, `pairs_checked: 110`. The alphabet
#   widened exactly as designed. THE COMMANDS DID NOT CHANGE. Alphabet width
#   is not the bottleneck. See the_key_alphabet_hypothesis_is_refuted.
#
#   AND THE REPLACEMENT IS WORSE, BECAUSE IT IS MY OWN DOING. I worked out
#   what my manual predicts for each of the five keys in each of the two
#   states this body has ever occupied. At spawn, exactly ONE key -- key(2)
#   -- has a successor that differs from the current state. One cell south,
#   exactly ONE key -- key(5). Every other key compiles to "nothing
#   happens". Any chooser that prefers an action predicted to do something,
#   which is the only signal left when `is_goal -> False`, is FORCED into
#   A2, A5, A2, A5 forever. Five rounds of oscillation are not a stubborn
#   ranker; they are my manual's silence being read as knowledge. See
#   my_manual_leaves_exactly_one_live_key_in_each_state_the_body_has_stood_in
#   and silence_is_a_prediction_and_three_of_my_spawn_silences_are_unwitnessed.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t25 compress: 47]
  Vacated [segment: dynamic_colour_5 ev: t2-t25 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20,t22,t24 cov: 264/264]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20,t22,t24 cov: 264/264]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12,t14,t16,t18,t20,t22,t24 cov: 10/10]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25 cov: 264/264]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25 cov: 264/264]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25 cov: 48/48]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25 cov: 18/18]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25 cov: 18/18]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25 cov: 18/18]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13,t17,t21,t25 cov: 18/18]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23 cov: 40/40]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23 cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23 cov: 40/40]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23 cov: 5/5]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11,t15,t19,t23 cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 47 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4013 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 12 [status: counted]

  theorem the_key_alphabet_hypothesis_is_refuted "Last round I hypothesised that the command chooser derives its candidate keys the way certify derives its adjudication list -- from the `act=key(n)` literals in my rules -- and that this, not ranking, was why four rounds bought A2 A5 A2 A5. The hypothesis made a sharp prediction and I paid for the experiment: two witnessed no-op rules, key1_inert_at_spawn and key3_inert_below_spawn, put key(1) and key(3) into the manual's alphabet. THE INSTRUMENT MOVED EXACTLY AS PREDICTED: certify went from `actions: 3, pairs_checked: 54` to `actions: 5, pairs_checked: 110`, with 0 clashes and 0 step crashes, so the two rules compiled, were adjudicated, and never fired wrongly. THE WORLD'S COMMANDS DID NOT MOVE AT ALL: t22 A2, t23 A5, t24 A2, t25 A5. Therefore alphabet width is NOT sufficient to change the choice, and the hypothesis in the form I stated it is dead. I cannot test necessity without shrinking the alphabet again, which would cost a round to learn nothing I could act on. This is a negative result and it is the honest product of the round: it cost two lines and four commands and it removes the explanation I would otherwise have spent a sixth round defending."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem my_manual_leaves_exactly_one_live_key_in_each_state_the_body_has_stood_in "THE REPLACEMENT EXPLANATION, and unlike the alphabet hypothesis it is checkable from the manual alone, without seeing the chooser. Ground every rule in the two states this body has ever occupied. AT SPAWN, body home, spawn_probe renders 9: key(1) fires key1_inert_at_spawn, which recolours (8,14) from 9 to 9, net zero cells. key(3) is blocked, its guard demanding spawn_probe render 5. key(4) has one rule, meter_burn_key4_next, and it needs a Glyph9 instance rendering 9 whose right neighbour renders 1 -- the only such cell would be the meter's leading edge, which is board and has no instance -- so net zero. key(5) has thirteen rules and TWELVE of them are guarded on colored(spawn_probe, 5); the thirteenth, key5_body_respawns, needs a Glyph9 rendering 5, and at spawn the ring renders 9 -- so net zero. key(2) fires key2_body_leaves and key2_body_arrives, 48 cells. ONE LIVE KEY. ONE CELL SOUTH, body at lattice (2,2), spawn_probe renders 5: key(1) blocked by the opposite sense of the same landmark test; key(3) fires key3_inert_below_spawn, 9 to 9, net zero; key(4) net zero as above; key(2) net zero, because key2_body_leaves ranges over Glyph9 and the body there is made of Vacated instances, while key2_body_arrives needs a Vacated destination and rows 20-24 are board; key(5) fires eleven rules, 71 cells. ONE LIVE KEY. So a chooser that prefers an action whose predicted successor differs from the current state -- the only signal available when the manual compiles is_goal to False -- has no choice to make at either cell. A2, A5, A2, A5 is not a ranking failure; it is the unique path through the transition function I wrote. I am naming this rather than repairing it, because the repair would be a rule with no witness and constraint 2 forbids that."
    [depends: key2_body_leaves, key5_body_respawns, the_goal_section_is_absent_on_purpose_and_the_ranking_had_no_choice_to_make  probe: passed]

  theorem silence_is_a_prediction_and_three_of_my_spawn_silences_are_unwitnessed "The compiled transition function is total: where no rule fires, the successor equals the current state. So my manual does not say `I do not know what key(4) does at spawn`, it says `key(4) does nothing at spawn`, in exactly the voice it uses for things it has seen. Audit the five keys at spawn. key(1) inert: WITNESSED at t1, zero cells changed. key(2) moves: witnessed eleven times. key(3) inert: NO WITNESS -- key(3) has been pressed once in this world's history, at t3, from one cell south. key(4) inert: NO WITNESS -- pressed once, at t4, from one cell south, where it burned a meter cell. key(5) inert: NO WITNESS -- pressed eleven times, all eleven from one cell south. THREE OF FIVE SILENCES AT SPAWN ARE FORGED DEATH CERTIFICATES. Worse, under the standard mapping that the_action_map defends, one of key(3) and key(4) is EAST, east of spawn is three lattice cells of unbroken floor, and that key moves the body 48 pixels -- so at least one of my three unwitnessed silences is almost certainly FALSE, and it is false in the most expensive possible way, by making the key look dead to anything that reads my predictions. This is the defect that matters. It is also the one I cannot fix inside the grammar."
    [depends: my_manual_leaves_exactly_one_live_key_in_each_state_the_body_has_stood_in, the_action_map_after_twentyfive_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_dsl_cannot_say_unknown_and_that_is_the_hole_i_would_most_like_closed "What I wanted to write is a third outcome for a (state, action) pair: not `no change` and not a named successor, but `unobserved, and the manual declines to predict`. There is no syntax for it -- rules produce events, absence of a rule produces identity, and the compiled step is documented total. What I wrote instead is this theorem plus playbook lines that rank a key by whether its predicted inertness rests on a witness. If a future desk gains one expressive extension, ask for this one before asking for `not`: an unwitnessed silence costs a whole round every time something downstream mistakes it for knowledge, and by my count it has now cost five."
    [depends: silence_is_a_prediction_and_three_of_my_spawn_silences_are_unwitnessed  probe: pending]

  theorem the_two_no_op_rules_still_fail_the_gain_test_and_i_keep_them_for_a_weaker_reason "Constraint 3 says a concept earns its place by shortening the manual, and key1_inert_at_spawn and key3_inert_below_spawn shorten nothing: each recolours one pixel to the colour it already has, each has exactly one witness on a transition where zero cells changed, and the manual would replay all 25 transitions identically without them. Last round I kept them to test the alphabet hypothesis; that hypothesis is now refuted, so THAT reason is gone and I say so. The reason I keep them anyway is weaker and I will not dress it up: deleting them narrows certify's adjudicated action set from five keys back to three, which removes information I can see for a benefit -- two lines -- that I cannot measure. They remain declared failures of the gain test, and they are the two cheapest deletions in this manual if a future desk needs the space."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_key_alphabet_hypothesis_is_refuted  probe: passed]

  theorem the_four_refutations_are_two_undrawable_pixels_rolled_forward "P-17 and P-19 are ACTION2, P-18 and P-20 ACTION5, and the diagnosis is arithmetic for the fourth round running. The inert fields form a CLOSED 4-CYCLE: P-18 inert = P-17 manual, P-19 inert = P-18 manual, P-20 inert = P-19 manual, P-17 inert = P-20 manual. That is the sharpest statement of the defect -- my manual says A2 then A5 returns the world exactly where it started, and it is right about all 4096 cells except the one the meter eats on each A2, and the harness rolls my predicted frame forward without resyncing so the error persists. The world burned (63,53) at t22 and (63,52) at t24; both were board at the instant they burned, owned by no object, drawable by no rule this grammar admits. t23 and t25 introduced nothing new: 48 body cells and 23 panel cells each, every one drawn by rules now carrying eleven and six witnesses. THE LEDGER IS TWO WRONG PIXELS AND FOUR REFUTATION REPORTS. Repair is arithmetic: both cells are dynamic now, Glyph9 goes 45 to 47, all four transitions replay exactly, and the identical bill will be presented at (63,51)."
    [depends: meter_burn_key2_next, the_meter_edge_saturates_the_refutation_channel  probe: passed]

  theorem the_meter_edge_saturates_the_refutation_channel "A law of this manual rather than of this world, and after five rounds the most expensive fact on the board. Each of the 64 cells of the row-63 bar burns EXACTLY ONCE, 9 to 1, advancing leftward. At the instant a cell burns it has never changed, so it is board, so no instance exists for it, so no rule of mine draws it. Therefore: (1) my three burn rules have ZERO predictive value on the leading edge and full value on replay, which is a division of labour and not a contradiction; (2) EVERY press of a key that burns is scored a refutation regardless of what else it teaches, so refutation-fired cannot discriminate between commands; (3) the correct reading of a refutation is its DIVERGENCE SET, and where that set is a subset of the bar's leading edge the manual is not implicated. All twenty refutations across five rounds have been exactly that. Deleting the burn rules does not help -- the wrong-pixel count at the moment of the burn is identical -- and keeping them is strictly better because they make every past transition replay. RIGHT NOW all twelve meter instances render colour 1, so meter_burn_key2_next and meter_burn_key4_next match nothing and my manual predicts NO burn at (63,51) under any key. That is not a claim about the world; it is the shape of the hole."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right. TWELVE burns now: (63,63) t2, (63,62) t4, then one per even index through (63,52) at t24. Thirteen silences: every odd index t1 through t25. The current frame confirms it to the cell -- row 63 reads 9 through col 51 and 1 from col 52 to col 63. READING A, ACTION-KEYING: burns iff the key is 2 or 4. READING B, COMMAND PARITY: burns iff the command index is even. BOTH SCORE 25/25 AND NEITHER HAS GAINED A BIT IN FOUR ROUNDS, because every command since t5 has been key 2 at an even index or key 5 at an odd index -- the exact diagonal on which the two readings are numerically identical. THE SEPARATOR IS STILL FREE AND STILL CHEAP: the next index is 26, EVEN, so ANY odd key there -- 1, 3 or 5 -- settles it in one command, and an even key there settles nothing. The compounding argument is unchanged and has now been ignored four times: an odd key at an even index separates, and the even key it displaces separates again at the following odd index, so odd-then-even collects the separation twice and even-then-odd never. I encode reading A because it is the only one the guard language can express -- there is no command counter and no phase pixel -- and I still expect B, because at t3 and t4 the body stood at lattice (2,2) with left and right both void, ACTION3 and ACTION4 were blocked identically, and only ACTION4 burned."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_meter_is_a_budget_and_it_is_still_not_the_binding_constraint "Twelve of sixty-four bar cells consumed after twenty-five commands. I do not know that exhaustion ends the game -- no frame has shown it -- but both readings price out survivably. Under reading A the bar burns only on keys 2 and 4, so a route made of eastward and southward steps burns once per step and 52 steps remain. Under reading B every second command burns and 104 commands remain. The route I can see: spawn (1,2) east three cells to (1,5) beside the knob, an unknown number of interactions there, three cells back west, seven cells south down lattice column 2 to (8,2), five cells east to the socket at (8,7) -- about nineteen steps plus interactions plus identification probes, comfortably inside 52. The meter has never been the binding constraint. Twenty of twenty-five commands buying nothing is."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9, and the split is now 11/11 WITH NO EXCEPTIONS. ACTION2 returned SEVEN frames at t2, t8, t12, t16, t20, t24 and NINE frames at t6, t10, t14, t18, t22. Read the panel configuration of the state each press acted FROM: t2 from state 1 (A), t8 from 7 (A), t12 from 11 (A), t16 from 15 (A), t20 from 19 (A), t24 from 23 (A) -- seven frames; t6 from 5 (B), t10 from 9 (B), t14 from 13 (B), t18 from 17 (B), t22 from 21 (B) -- nine frames. ACTION2 animates in 7 internal frames under configuration A and 9 under B, eleven for eleven. ACTION5 returned nine frames all eleven times regardless of configuration, and every no-op returned one. THE NET EFFECT IS IDENTICAL IN ALL ELEVEN ACTION2 PRESSES -- 48 body cells, rows 8-18, cols 14-18, plus one burn -- so this costs nothing in replay and buys nothing in prediction, and it remains the ONLY evidence that the panel does anything besides display. I record as a limitation of my own semantics, not of the world: `cascade single_frame` compares only the net, so up to eight intermediate frames per command are discarded unread, and something distinguishable happens inside them."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over ELEVEN toggles -- every odd index t5 through t25 -- 23 cells every time, and ACTION2 has never touched a panel pixel in eleven presses. CONFIGURATION A (states 0-4, 7-8, 11-12, 15-16, 19-20, 23-24): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B (states 5-6, 9-10, 13-14, 17-18, 21-22, 25, and the current frame, which reads 222/2.2/222 at cols 1-3 and 999/9.9/999 at cols 5-7 with row 5 dark at 1-3 and lit at 5-7): slot 1 is a hollow colour-2 ring with dark underline, slot 2 a hollow colour-9 ring with dark centre and lit underline. mdl_segmenter corroborates independently and by frame index: colour-1 nine-cell tracks obj1 (0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16), obj12 (19-20), obj14 (23-24); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17-18), obj13 (21-22), obj15 (25). Twelve alternations read off an engine that has never seen my rules. Its obj0 (colour 9, eight cells, 3x3, present in all 26 frames) and obj2 (colour 9, 1x3, all 26) persist while it narrates 22 MOVE events: the hollow ring and the lit underline do not appear and vanish, they TRAVEL between slot 1 and slot 2. So the panel is one marker with two seats and colour 9 marks the occupied seat. What the seats HOLD is still unknown and I will not guess. I cannot model it as a moving marker either: the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring travelling four columns is not expressible as a move, and ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_still_cannot_test_it "Unchanged in kind, stronger in count, and now doubly load-bearing. The guard colored(spawn_probe, 5) has ELEVEN positive witnesses -- every ACTION5 press, all with the body away and the panel toggling -- and STILL NO NEGATIVE ONE, because ACTION5 has never been pressed with the body at home. Every ACTION5 in this window immediately followed an ACTION2, so `ACTION5 was pressed` and `the body was away from spawn` are the same event eleven times over and no guard can be credited over the other. By the letter of no-entry-without-gain the atom is unearned. I keep it because dropping it changes no replay, and because it is the guard that makes key(5) predicted-inert at spawn -- which, per my_manual_leaves_exactly_one_live_key, is half the reason the command stream is stuck. One ACTION5 pressed at home settles three things at once: the guard itself, the meter parity (key 5 is odd, index 26 is even, so reading A predicts no burn and reading B predicts a burn at (63,51)), and the identity of ACTION5 (UNDO returns the body to (2,2) for 48 cells, while UP and RETURN both predict no motion from spawn). Zero cells is the only prediction this manual can make that costs exactly nothing if right."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, what_action5_is_and_the_two_cell_experiment_that_names_it  probe: pending]

  theorem the_action_map_after_twentyfive_transitions_and_the_standard_mapping_hypothesis "WITNESSED: ACTION2 IS DOWN, 11/11, six rows south, one lattice cell. ACTION5 returns the body from lattice (2,2) to (1,2), 11/11. NEGATIVE INFORMATION, and I state it as negative because that is all it is. At spawn (1,2) up and left are void while down and right are open floor, and ACTION1 did nothing at t1 -- so ACTION1 IS NEITHER DOWN NOR RIGHT. At (2,2) the body had just vacated rows 8-12 so UP WAS OPEN, and rows 20-24 cols 14-18 are floor so DOWN WAS OPEN, while left (cols 8-12) and right (cols 20-24) are void; ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else. It explains every no-op as a blocked move and it is the conventional mapping for this action family, which is a prior and not evidence. TWENTY COMMANDS ACROSS FIVE ROUNDS AND NOT ONE TOUCHED THIS QUESTION -- the map is exactly as constrained as it was at state 5. THE TEST IS ONE PRESS: the body stands at spawn, west is void, east is three lattice cells of unbroken floor, so either of ACTION3 and ACTION4 pressed here settles which is east -- if it steps it is east, and if it does not the other is east by elimination, ACTION1 having been excluded from east at t1. ACTION3 is the odd one of the pair and index 26 is even, so ACTION3 here also separates the meter readings: one press, two questions."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_and_the_two_cell_experiment_that_names_it "Three readings survive all ELEVEN ACTION5 presses because all eleven were made from exactly one cell south of spawn, where they are indistinguishable: UP (move one cell north), UNDO (revert the last move), RETURN (jump to spawn from anywhere). They separate the moment the body is somewhere else, and they separate differently by axis. FROM SPAWN ITSELF, which is where the body is now: UP predicts no motion (north of spawn is void), RETURN predicts no motion (already home), UNDO predicts 48 cells back to (2,2) -- so one press here splits UNDO from the other two for free. Two cells EAST at lattice (1,4): UP no move, UNDO one cell west to (1,3), RETURN spawn at (1,2) -- three different diffs, all legible in the raw pixel count, which is full separation. Two cells SOUTH at (3,2): UP and UNDO both predict (2,2) and only RETURN separates. So the eastward route answers this question completely and the southward route does not, which is one more reason to go east. Note the coupling I cannot yet break: the panel toggles on every effective ACTION5, eleven for eleven, so whatever ACTION5 is, the panel is its counter or its selector -- and the 7-versus-9 cascade split, now 11/11, says the panel's state is not merely cosmetic."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated one row per internal frame and the world reports the whole animation for a single action; cascade single_frame compares only the net effect, which is identical for all eleven ACTION2 presses (48 body cells, rows 8-18, cols 14-18) whether the command took 7 frames or 9. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, ELEVEN times. ONE PRESS IS ONE LATTICE CELL, 11/11, and every distance in the playbook rests on that."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_world_may_still_not_be_a_function_of_the_drawn_frame "Carried as a belief and NOT proven in this window, and this round I can say exactly why. To prove it I need two pixel-identical states from which the SAME action produced different successors. distinct_states is 24 against 26 states, so there are exactly two coincidences and I can name them: state 1 equals state 0 (ACTION1 changed nothing at t1) and state 3 equals state 2 (ACTION3 changed nothing at t3). From state 0 the world pressed ACTION1 and from state 1 it pressed ACTION2; from state 2 it pressed ACTION3 and from state 3 ACTION4. DIFFERENT KEYS BOTH TIMES, so neither pair tests functionality and the belief is untouched. What keeps it alive is the parity reading of the meter, which if true is one bit of hidden state flipping every command that no guard in this language can read, because no guard can read anything that is not a pixel. What strengthens it is the cascade length: ACTION2 took 7 frames or 9 depending on a panel configuration my rules never consult -- the same shape of dependence, one step less hidden. Operationally it matters in exactly one way: if parity wins, every burn rule I can write is an approximation with a known error rate, and I would rather say that once than rediscover it."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4013 + dynamic 83 = 4096, and 47+24+9 = 80 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 83. Consequence: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This is the fifth consecutive round in which that sentence, written in advance, was the entire content of every refutation. meter_burn_key2_next now replays t6 through t24 perfectly, because by replay time all ten of those cells are dynamic; it will still miss the THIRTEENTH burn at (63,51), because that cell is board today. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable too until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, 24 if I already had the leaves rule, 0 for the second step. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 83 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 12 are the burned right end of row 63: cols 52 through 63. 23+24+24+12 = 83 = dynamic_cells. By frame-0 colour: 47 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 12 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 47+9+24 = 80 = cells_needing_an_owner exactly, and 4096-83 = 4013 = constant_cells exactly. zero_space's global-law cell list is the same set -- it lists (2,1) and (2,3) but not (2,2), (10,14),(10,15),(10,17),(10,18) but not (10,16), and every burned bar cell -- and its single global law restates this census and nothing more."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so that the transition witnessing it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended eleven times and all eleven started at spawn, so no rule of mine turns Vacated pixels from 9 back to 5 on an ACTION2: rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below-six(?v), 5) then recolored(?v, 5). One ACTION2 from lattice (2,2) buys it, and twenty commands across four rounds each had the chance and none took it. (2) EAST-WEST MOTION. Whatever the east key turns out to be, it needs a pair: a leaves rule over Glyph9 guarded on colour 9 with rightof-six rendering 5, and its arrives twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) A THIRTEENTH BURN AT A CELL THAT IS STILL BOARD, which is not a missing rule but a missing instance and cannot be written at all. I state the price of all three in advance so it cannot be mistaken for a surprise: the first eastward step costs 48 wrong cells plus one if the bar burns, the first second-descent costs 24, and every fresh burn costs 1."
    [depends: key2_body_arrives, the_meter_edge_saturates_the_refutation_channel  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all 110 adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth below is row 69. So colored(off-board, k) is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen rules rest on this and every row and column discrimination in the panel is built from it: the k-th above is off-board exactly when k exceeds the row, so row 1 is above-twice equals wall, row 3 is a colour test on above-twice -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column: col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice, pairwise exclusive, which is why the ambiguity check reports 0 clashes at 26 states. Not one rule uses `not`, deliberately. The eight A-to-B slot-2 and underline rules could collapse to two if I could write that not all four neighbours are colour 1, and I decline to gamble a whole round's compile on discovering whether `not` before an equality atom parses. If a future desk wants the shorter form, try it on ONE rule, not on eight."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame and unchanged: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open, C=6 holds the knob, C=7 does not exist in this band; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2, plus a fragment of floor at row 48 cols 42-50 that is one row deep and cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in twenty-six frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it has been at spawn in fourteen of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed ELEVEN times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame, and the reading sharpened. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows, col 49 and col 43 are separator columns -- so what is drawn is the north, south and east walls of lattice cell (8,7), painted in colour 9, with the west wall at col 43 left as FLOOR. Inside it, rows 50-54 cols 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, col 50 rows 49-56 is a one-cell strip of floor that leads nowhere. Overlay the body standing in lattice (8,7) -- 5x5, aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in twenty-six frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel of it is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem pixel at (12,40), colour 8 filling col 40 from row 12 down to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18. It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in twenty-six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell -- the eight knob pixels other than its centre, plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Twenty-five commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after twenty-six states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. I have no witness for key(6) or key(7), so no rule can name them, so they sit outside the manual's alphabet -- which last round I thought was decisive and now know is not sufficient to explain anything, since keys 1 and 3 are inside the alphabet and were still never chosen."
    [depends: the_key_alphabet_hypothesis_is_refuted  probe: pending]

  theorem the_goal_section_is_absent_on_purpose_and_the_ranking_had_no_choice_to_make "Still absent, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and forty-six siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would be true of the body standing one cell south of spawn, which is not a win. I also checked the alternatives this round and they all fail: count(Glyph9, color = 5) = 24 is true of every state where the body is anywhere but home, and a Wire type on colour 8 would have zero instances because every colour-8 cell is constant, so count(Wire) = 0 would be true at RESET. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. I name the price of that choice plainly: with no goal section the manual compiles is_goal to False, no plan can terminate, and nothing in the manual ranks one command above another EXCEPT whether the command is predicted to change pixels -- and that criterion, as my_manual_leaves_exactly_one_live_key shows, admits exactly one command per state. The ranking never had a choice to make."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, my_manual_leaves_exactly_one_live_key_in_each_state_the_body_has_stood_in  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter keeps a positive gain of +9098 bits at compression_ratio 0.574 on split_by_color=false, against -112910 bits when split by colour -- its segmentation beats writing the pixels out, and I still owe it nothing structural. Its sixteen tracks are the round's best independent corroboration and they corroborate the panel toggle by frame index: colour-1 nine-cell tracks obj1 (0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16), obj12 (19-20), obj14 (23-24); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17-18), obj13 (21-22), obj15 (25). A,B,A,B, twelve times, derived by an engine that has never seen my rules. obj0 and obj2 persisting through all 26 frames while the segmenter narrates 22 moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 12 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 25 transitions constrain rank 13 of 415 features, null space dimension 402, nearly every vector in it a law true over these states and unfalsified rather than confirmed -- and its single global law is my census. cegis_miner refuses on every track and its verdict, `the world does not narrate as one mover`, remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The next command has index 26, which is EVEN, the body is at spawn, the panel is in configuration B, and twelve meter cells are burned. ACTION3 -- the command I most want -- I predict ZERO changed cells, because key3_inert_below_spawn requires the body AWAY and cannot fire at home, and because under the standard mapping ACTION3 is west and west of spawn is void. Zero cells says ACTION3 is not east, hence ACTION4 is east by elimination, AND kills the parity reading outright, an odd key at an even index that does not burn refuting B while confirming A. One cell at (63,51) and nothing else confirms parity and kills action-keying. 48 or 49 cells says ACTION3 IS east, and my manual draws none of them -- no east rules exist and rows 8-12 cols 20-24 are board -- which is the advertised price of the first step onto fresh ground and not a failure of physics. ACTION1 at spawn: ZERO cells, key1_inert_at_spawn firing as a no-op, and this is the one spawn silence I have a witness for; a burn at (63,51) would still kill action-keying. ACTION5 at spawn: ZERO cells, the only zero-pixel stake this manual can offer; 23 cells refutes the spawn_probe guard and puts thirteen rules into repair; 48 cells says ACTION5 is UNDO. ACTION4 at spawn: my manual says ZERO and my manual has no witness for that, so I expect it to be wrong -- 48 cells I cannot draw plus a burn I cannot draw, and no parity information, because an even key at an even index is where both readings agree. ACTION2: 48 cells I draw correctly plus a burn at (63,51) I cannot draw -- exactly one wrong pixel and NOTHING learned, because key2_body_leaves and key2_body_arrives are at 264/264 and a twelfth witness buys zero."
    [depends: the_action_map_after_twentyfive_transitions_and_the_standard_mapping_hypothesis, the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept in compressed form because the lesson is structural and cost a full round. Thirteen panel rules once carried colored(spawn_probe, 5) while the landmark line read a prose placeholder instead of a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The landmark now reads (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else -- which is exactly why the two no-op rules can use it as a home/away test in opposite senses. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key5_slot1_dims  probe: passed]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because a future desk will be tempted by the same repair I considered and rejected for the third time this round. To draw the leading-edge burn I would need an instance on a board cell. The arm offers exactly one lever, `arc-instances: all`, and its documented behaviour is to instance every cell OF THAT COLOUR THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance. The tempting workaround is a second declared type on colour 9 without arc-instances, hoping the arm seats one instance somewhere useful. I reject it: the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, the seat is unspecified, and any cell it landed on would be claimed twice, which is the constraint-5 error the grammar warns about in as many words. A landmark cannot help either, because landmarks are cells and every event in the language takes an object as its first argument. So the hole is a property of the arm, it is permanent for this level, and the only correct response is the one the playbook encodes: price the burn in advance and read refutations by their divergence set."
    [depends: the_meter_edge_saturates_the_refutation_channel  probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= READ THIS FIRST: LAST ROUND'S DIAGNOSIS WAS WRONG =========
# I said the chooser's menu was my rules' key alphabet, and that four rounds
# of A2 A5 A2 A5 were the whole menu rather than a bad pick. I paid two
# witnessed no-op rules to widen it. certify went from `actions: 3,
# pairs_checked: 54` to `actions: 5, pairs_checked: 110`. The alphabet
# widened. THE COMMANDS DID NOT. t22 A2, t23 A5, t24 A2, t25 A5. Alphabet
# width is not the bottleneck and that hypothesis is closed.
#
# ========= THE REPLACEMENT, AND IT IS THE MANUAL'S OWN FAULT =========
# Ground every rule in the only two cells this body has ever stood in.
#   At spawn:            key(2) changes 48 cells. keys 1,3,4,5 change NOTHING.
#   One cell south:      key(5) changes 71 cells. keys 1,2,3,4 change NOTHING.
# Exactly one live key per state, and the two live keys are exactly the two
# keys that have been pressed for five rounds. Anything that ranks by "does
# this action change pixels under the manual" -- the only signal left when
# is_goal compiles to False -- is FORCED into A2 A5 A2 A5. This is not
# stubbornness downstream; it is my manual's silence being read as knowledge.
#
# ========= AND THREE OF THOSE SILENCES ARE FORGED =========
# At spawn, key(1)'s inertness is WITNESSED (t1, zero cells). key(3)'s,
# key(4)'s and key(5)'s are NOT: key(3) and key(4) were each pressed once
# ever, both from one cell south; key(5) was pressed eleven times, all from
# one cell south. Under the standard mapping one of key(3)/key(4) is EAST,
# east of spawn is three lattice cells of unbroken floor, and that key moves
# 48 pixels. So at least one of my three unwitnessed silences is very likely
# FALSE. The DSL has no way to write "unknown"; these lines are the
# substitute.
#
# ------------------------------------------------------------------------
# THE BOARD AT STATE 25: body home at lattice (1,2); panel configuration B;
# TWELVE meter cells burned, cols 52-63 of row 63; next command index 26,
# EVEN. Eleven lattice cells reachable, the body has stood in TWO. Three
# steps east along lattice row 1 reach the cell beside the knob; the knob is
# the far end of one connected colour-8 wire whose near end is the comb; the
# comb gates every route to the socket at (8,7). 52 meter cells remain
# against a route of about nineteen steps: the budget is not binding, waste is.
#
# THE ARGUMENT FOR THE NEXT COMMAND, AS CRITERIA:
#
#  (1) A KEY WHOSE PREDICTED INERTNESS HAS NO WITNESS IS NOT A NO-OP, IT IS
#      AN UNTESTED CLAIM. Three of five keys at spawn are in that state.
#      Ranking them below key(2) because the manual draws nothing for them
#      is circular: the manual draws nothing for them because nobody has
#      ever pressed them here.
#
#  (2) THE EAST KEY IS ONE PRESS AWAY AND UNBLOCKED. East is key(3) or
#      key(4); key(1) was excluded from east at t1. At spawn west is void
#      and east is open floor, so either one settles it -- if it steps it is
#      east, if it does not the other is east by elimination.
#
#  (3) PARITY SEPARATION COMPOUNDS, SO TAKE THE ODD KEY FIRST. Twenty-five
#      commands, twenty-five times a key whose parity matched its index's,
#      zero separation between action-keying and command-parity. An odd key
#      at index 26 separates; the even key it displaces separates again at
#      index 27. Odd-then-even collects twice, even-then-odd never.
#
#  (4) EVERY REFUTATION SO FAR IS THE SAME UNDRAWABLE PIXEL. Twenty across
#      five rounds, every divergence set inside the meter's leading edge --
#      cells that were board at the instant they burned. Ranking by
#      refutation-fired therefore ranks key(2) first forever.
#
#  (5) A2 FROM SPAWN AND A5 FROM ONE CELL SOUTH ARE EXHAUSTED. Eleven
#      presses each, 264/264 coverage each, cascade split settled 11/11. A
#      twelfth witness buys nothing and costs one command and one bar cell.
#
#  (6) ONE PRESS IS ONE LATTICE CELL, 11/11. Distances are lattice cells.

order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     take_the_separation_that_compounds_before_the_one_that_does_not   [proof: lean]
order     buy_the_probe_that_closes_two_questions_before_one_that_closes_one [proof: lean]
order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full     [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]

prune     ranked_only_because_the_manual_predicts_it_changes_pixels => dead  [proof: lean]
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

heuristic keys_whose_inertness_here_rests_on_no_witness                      [admissible: lean]
heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                    [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed     [ev: 3/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on              [ev: 0/20 commands]
prefer    a_key_whose_parity_differs_from_the_command_index                 [ev: 0/25 commands]
prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree       [ev: 11/13 no_ops]
prefer    a_press_at_home_that_splits_up_from_undo_from_return              [ev: 11/11 key5]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 25/25 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                    [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                     [ev: 2/7 keys]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered           [ev: 1/1 levels]
```

## Why you are being called: the surprises that fired

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '6d0db422effc0cdc', the world answered 'ba530aab6f501769'

```json
{
 "action": 2,
 "observed": "ba530aab6f501769",
 "predictions": {
  "inert": "6ac765de5c59b51e",
  "manual": "6d0db422effc0cdc",
  "without_key1_inert_at_spawn": "6d0db422effc0cdc",
  "without_key2_body_arrives": "6ac765de5c59b51e",
  "without_key2_body_leaves": "6ac765de5c59b51e",
  "without_key3_inert_below_spawn": "6d0db422effc0cdc",
  "without_key5_body_clears": "6d0db422effc0cdc",
  "without_key5_body_respawns": "6d0db422effc0cdc",
  "without_key5_slot1_dims": "6d0db422effc0cdc",
  "without_key5_slot1_lights": "6d0db422effc0cdc",
  "without_key5_slot2_centre_darkens": "6d0db422effc0cdc",
  "without_key5_slot2_centre_resets": "6d0db422effc0cdc",
  "without_key5_slot2_ring_resets": "6d0db422effc0cdc",
  "without_key5_slot2_row1_lights": "6d0db422effc0cdc",
  "without_key5_slot2_row2_left_lights": "6d0db422effc0cdc",
  "without_key5_slot2_row2_right_lights": "6d0db422effc0cdc",
  "without_key5_slot2_row3_lights": "6d0db422effc0cdc",
  "without_key5_underline1_dims": "6d0db422effc0cdc",
  "without_key5_underline1_lights": "6d0db422effc0cdc",
  "without_key5_underline2_dims": "6d0db422effc0cdc",
  "without_key5_underline2_lights": "6d0db422effc0cdc",
  "without_meter_burn_key2_next": "6d0db422effc0cdc",
  "without_meter_burn_key2_rightmost": "6d0db422effc0cdc",
  "without_meter_burn_key4_next": "6d0db422effc0cdc"
 },
 "probe_id": "P-21"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'c530010f3b45d4ae', the world answered 'cf2157b5311a6e35'

```json
{
 "action": 5,
 "observed": "cf2157b5311a6e35",
 "predictions": {
  "inert": "6d0db422effc0cdc",
  "manual": "c530010f3b45d4ae",
  "without_key1_inert_at_spawn": "c530010f3b45d4ae",
  "without_key2_body_arrives": "c530010f3b45d4ae",
  "without_key2_body_leaves": "c530010f3b45d4ae",
  "without_key3_inert_below_spawn": "c530010f3b45d4ae",
  "without_key5_body_clears": "6d0db422effc0cdc",
  "without_key5_body_respawns": "6d0db422effc0cdc",
  "without_key5_slot1_dims": "c530010f3b45d4ae",
  "without_key5_slot1_lights": "6d0db422effc0cdc",
  "without_key5_slot2_centre_darkens": "c530010f3b45d4ae",
  "without_key5_slot2_centre_resets": "6d0db422effc0cdc",
  "without_key5_slot2_ring_resets": "6d0db422effc0cdc",
  "without_key5_slot2_row1_lights": "c530010f3b45d4ae",
  "without_key5_slot2_row2_left_lights": "c530010f3b45d4ae",
  "without_key5_slot2_row2_right_lights": "c530010f3b45d4ae",
  "without_key5_slot2_row3_lights": "c530010f3b45d4ae",
  "without_key5_underline1_dims": "c530010f3b45d4ae",
  "without_key5_underline1_lights": "6d0db422effc0cdc",
  "without_key5_underline2_dims": "6d0db422effc0cdc",
  "without_key5_underline2_lights": "c530010f3b45d4ae",
  "without_meter_burn_key2_next": "c530010f3b45d4ae",
  "without_meter_burn_key2_rightmost": "c530010f3b45d4ae",
  "without_meter_burn_key4_next": "c530010f3b45d4ae"
 },
 "probe_id": "P-22"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'eb6ce939c989359a', the world answered '9c6d40686d791ac6'

```json
{
 "action": 2,
 "observed": "9c6d40686d791ac6",
 "predictions": {
  "inert": "c530010f3b45d4ae",
  "manual": "eb6ce939c989359a",
  "without_key1_inert_at_spawn": "eb6ce939c989359a",
  "without_key2_body_arrives": "c530010f3b45d4ae",
  "without_key2_body_leaves": "c530010f3b45d4ae",
  "without_key3_inert_below_spawn": "eb6ce939c989359a",
  "without_key5_body_clears": "eb6ce939c989359a",
  "without_key5_body_respawns": "eb6ce939c989359a",
  "without_key5_slot1_dims": "eb6ce939c989359a",
  "without_key5_slot1_lights": "eb6ce939c989359a",
  "without_key5_slot2_centre_darkens": "eb6ce939c989359a",
  "without_key5_slot2_centre_resets": "eb6ce939c989359a",
  "without_key5_slot2_ring_resets": "eb6ce939c989359a",
  "without_key5_slot2_row1_lights": "eb6ce939c989359a",
  "without_key5_slot2_row2_left_lights": "eb6ce939c989359a",
  "without_key5_slot2_row2_right_lights": "eb6ce939c989359a",
  "without_key5_slot2_row3_lights": "eb6ce939c989359a",
  "without_key5_underline1_dims": "eb6ce939c989359a",
  "without_key5_underline1_lights": "eb6ce939c989359a",
  "without_key5_underline2_dims": "eb6ce939c989359a",
  "without_key5_underline2_lights": "eb6ce939c989359a",
  "without_meter_burn_key2_next": "eb6ce939c989359a",
  "without_meter_burn_key2_rightmost": "eb6ce939c989359a",
  "without_meter_burn_key4_next": "eb6ce939c989359a"
 },
 "probe_id": "P-23"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '6ac765de5c59b51e', the world answered '70eb49bbc21b44e9'

```json
{
 "action": 5,
 "observed": "70eb49bbc21b44e9",
 "predictions": {
  "inert": "eb6ce939c989359a",
  "manual": "6ac765de5c59b51e",
  "without_key1_inert_at_spawn": "6ac765de5c59b51e",
  "without_key2_body_arrives": "6ac765de5c59b51e",
  "without_key2_body_leaves": "6ac765de5c59b51e",
  "without_key3_inert_below_spawn": "6ac765de5c59b51e",
  "without_key5_body_clears": "eb6ce939c989359a",
  "without_key5_body_respawns": "eb6ce939c989359a",
  "without_key5_slot1_dims": "eb6ce939c989359a",
  "without_key5_slot1_lights": "6ac765de5c59b51e",
  "without_key5_slot2_centre_darkens": "eb6ce939c989359a",
  "without_key5_slot2_centre_resets": "6ac765de5c59b51e",
  "without_key5_slot2_ring_resets": "6ac765de5c59b51e",
  "without_key5_slot2_row1_lights": "eb6ce939c989359a",
  "without_key5_slot2_row2_left_lights": "eb6ce939c989359a",
  "without_key5_slot2_row2_right_lights": "eb6ce939c989359a",
  "without_key5_slot2_row3_lights": "eb6ce939c989359a",
  "without_key5_underline1_dims": "eb6ce939c989359a",
  "without_key5_underline1_lights": "6ac765de5c59b51e",
  "without_key5_underline2_dims": "6ac765de5c59b51e",
  "without_key5_underline2_lights": "eb6ce939c989359a",
  "without_meter_burn_key2_next": "6ac765de5c59b51e",
  "without_meter_burn_key2_rightmost": "6ac765de5c59b51e",
  "without_meter_burn_key4_next": "6ac765de5c59b51e"
 },
 "probe_id": "P-24"
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
  "detail": "25/25 transitions replay exactly",
  "matched": 25,
  "ok": true,
  "transitions": 25
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
  "detail": "no (state, action) among 26 x 5 admitted two rules, and all 130 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 130,
  "pairs_nominal": 130,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 26,
  "states_reconstructed": 26,
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

=== PLAYBOOK ===
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

=== LOG ===
```json
[
  {"id": "O-01", "subject": "Glyph9 (colour 9, arc-instances: all)", "verdict": "accept",
   "as": "Glyph9 recounted 47 -> 49",
   "why": "store.dynamic_cells went 83 -> 85 and cells_needing_an_owner 80 -> 82; the two new cells are (63,51) burned at t26 and (63,50) burned at t28, both frame-0 colour 9, which the current frame confirms since row 63 now reads 9 through col 49 and 1 from col 50."},

  {"id": "O-02", "subject": "Vacated / Spent / Dark counts", "verdict": "accept",
   "as": "24 / 9 / 3 unchanged",
   "why": "no colour-5, colour-1 or colour-0 cell became dynamic this round; 49+24+9+3 = 85 = dynamic_cells and 49+9+24 = 82 = cells_needing_an_owner, so the census closes exactly."},

  {"id": "O-03", "subject": "mdl_segmenter obj16 (colour 1, frames 27-28) and obj17 (colour 2, frame 29)", "verdict": "entailed",
   "why": "they are the seventh colour-1 and seventh colour-2 appearance of the same 3x3 panel slot; the alternation A(27-28) B(29) is exactly what key5_slot1_dims and key5_slot1_lights already predict, so they buy corroboration and not a new type."},

  {"id": "O-04", "subject": "mdl_segmenter obj3 (1006-cell colour-null blob)", "verdict": "reject",
   "why": "connected_components(4) merged the maze floor with the body ring because the mover is floor-adjacent; declaring it would claim pixels Vacated and Glyph9 already own, which is the constraint-5 double claim."},

  {"id": "R-01", "subject": "colored(spawn_probe, 5) on thirteen panel rules", "verdict": "reject",
   "as": "deleted from key5_slot1_dims, key5_underline1_dims, key5_slot2_row1_lights, key5_slot2_row3_lights, key5_slot2_row2_left_lights, key5_slot2_row2_right_lights, key5_slot2_centre_darkens, key5_underline2_lights, key5_slot1_lights, key5_underline1_lights, key5_slot2_ring_resets, key5_slot2_centre_resets, key5_underline2_dims",
   "why": "the atom has 13 positive witnesses and no possible negative one, because every ACTION5 followed an ACTION2 so 'key 5 pressed' and 'body away' are the same 13 events; it explains no pixel the act= guard does not, deleting it leaves all 29 transitions replaying identically, and constraint 3 therefore requires the deletion rather than merely permitting it."},

  {"id": "R-02", "subject": "panel rule mutual exclusion after R-01", "verdict": "accept",
   "as": "verified by hand under both configurations",
   "why": "the A-to-B set reads colour 9, 1 or 0 and the B-to-A set reads colour 2, 9 or 0 on disjoint types and colours; within each set rows are separated by above^k = wall and columns by leftof^k = wall, the same discriminations certify already scored at 0 clashes over 130 pairs, and no cell is claimed twice."},

  {"id": "R-03", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept",
   "as": "cov 264/264 -> 312/312, ev extended with t26, t28",
   "why": "two more identical 48-cell descents, rows 8-18 cols 14-18, net effect unchanged from all eleven earlier presses."},

  {"id": "R-04", "subject": "meter_burn_key2_next", "verdict": "accept",
   "as": "cov 10/10 -> 12/12, ev extended with t26, t28",
   "why": "(63,51) and (63,50) are now dynamic and typed Glyph9, so the rule replays both transitions it could not predict; 1 + 1 + 12 = 14 = the burned cells the current frame shows at cols 50-63."},

  {"id": "R-05", "subject": "key5_body_clears / key5_body_respawns", "verdict": "accept",
   "as": "cov 264/264 -> 312/312, ev extended with t27, t29",
   "why": "two more identical 48-cell returns; these two rules never carried the deleted guard and are untouched by R-01."},

  {"id": "R-06", "subject": "the eight A-to-B panel rules", "verdict": "accept",
   "as": "seven witnesses each (t5..t29 step 4), cov 56/21/21/21/7/7/7/21",
   "why": "t29 is the seventh A-to-B toggle and the current frame reads configuration B pixel for pixel (222/2.2/222 at cols 1-3, 999/9.9/999 at cols 5-7, row 5 dark left and lit right); 8+3+3+3+1+1+1+3 = 23 panel cells."},

  {"id": "R-07", "subject": "the five B-to-A panel rules", "verdict": "accept",
   "as": "six witnesses each (t7..t27 step 4), cov 48/18/48/6/18",
   "why": "t27 is the sixth B-to-A toggle; 8+3+8+1+3 = 23, the same panel cells in the reverse direction."},

  {"id": "R-08", "subject": "an east-motion rule pair", "verdict": "probe-pending",
   "why": "no eastward step has ever been witnessed and the destination cells rows 8-12 cols 20-24 are board, so neither the leaves rule nor its arrives twin has a witness or an owning object; the text is held in the_rules_i_still_have_no_witness_for_and_will_not_write so it costs one paste when a witness arrives."},

  {"id": "R-09", "subject": "key2_floor_leaves (a second descent from lattice (2,2))", "verdict": "probe-pending",
   "why": "all thirteen descents started at spawn, so no rule turns Vacated pixels from 9 back to 5 on an ACTION2; one press of ACTION2 from one cell south buys it and twenty-four commands have each had the chance."},

  {"id": "L-01", "subject": "invariant board_cells and meter_cells_burned", "verdict": "accept",
   "as": "4013 -> 4011 and 12 -> 14",
   "why": "store reports constant_cells 4011 and the current row 63 shows fourteen colour-1 cells at cols 50-63; both are counted from frames, not assumed, and the status field says counted."},

  {"id": "L-02", "subject": "the_parity_diagonal (action-keying vs command-parity)", "verdict": "probe-pending",
   "why": "fourteen burns all at even indices under keys 2 and 4, fifteen silences all at odd indices under keys 1, 3 and 5 -- both readings score 29/29 and the four new commands again sat on the diagonal where they coincide; index 30 is even so any odd key separates them there."},

  {"id": "L-03", "subject": "the_cascade_length split (7 frames from A, 9 from B)", "verdict": "accept",
   "as": "13/13, no exceptions",
   "why": "t26 acted from state 25 which is configuration B and returned 9 frames; t28 acted from state 27 which is A and returned 7; this is the only evidence the panel is functional rather than cosmetic, and cascade single_frame discards it by construction."},

  {"id": "L-04", "subject": "the_key_alphabet_hypothesis", "verdict": "reject",
   "as": "kept as a compressed refuted theorem",
   "why": "certify widened from 3 to 5 adjudicated actions exactly as the hypothesis required and the command stream did not move for two further rounds; alphabet width is not sufficient to change the choice."},

  {"id": "L-05", "subject": "zero_space global law and its THIN self-report", "verdict": "entailed",
   "why": "rank 15 of 425 features against 29 transitions leaves a 410-dimensional null space, and the single law it emits enumerates exactly the 85 dynamic cells my dynamic_census already lists, including the omission of the two aperture pixels and slot 1's centre."},

  {"id": "L-06", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "reject",
   "as": "true of the arm, false of the world",
   "why": "there is one mover, a rigid 24-pixel ring; the arm gives one instance per cell so a lattice step is 24 simultaneous recolours and no single move event, which is why motion costs a rule pair per direction."},

  {"id": "P-21", "subject": "refutation P-21 (ACTION2 at t26)", "verdict": "accept",
   "as": "divergence = {(63,51)}, manual not implicated",
   "why": "the cell was board at the instant it burned, so no instance existed and no rule could draw it; every without_* prediction equals the manual's except the two key2 body rules, which is the signature of a single undrawable pixel."},

  {"id": "P-22", "subject": "refutation P-22 (ACTION5 at t27)", "verdict": "accept",
   "as": "inherited error, no new divergence",
   "why": "P-22's inert field equals P-21's manual field, so the harness rolled my wrong frame forward without resyncing; the 71 cells of t27 were all drawn correctly."},

  {"id": "P-23", "subject": "refutation P-23 (ACTION2 at t28)", "verdict": "accept",
   "as": "divergence = {(63,50)} plus the inherited (63,51)",
   "why": "same undrawable leading edge one cell further left; the closed 4-cycle P-22 inert = P-21 manual, P-23 inert = P-22 manual, P-24 inert = P-23 manual, P-21 inert = P-24 manual is the arithmetic of a persistent one-pixel offset."},

  {"id": "P-24", "subject": "refutation P-24 (ACTION5 at t29)", "verdict": "accept",
   "as": "inherited error, no new divergence",
   "why": "twenty-fourth refutation in six rounds and the twenty-fourth whose divergence set lies inside the meter's leading edge; zero rules have ever been contradicted."},

  {"id": "P-25", "subject": "ACTION5 pressed at spawn", "verdict": "probe-pending",
   "why": "the command R-01 makes worth buying: 23 cells vindicates the cut, 0 cells refutes it and puts thirteen rules into repair, 71 cells says ACTION5 is UNDO, and (63,49) burning or not settles meter parity because key 5 is odd and index 30 is even -- three bits in one legible diff, with a fourth free on the following A2 via the 7-versus-9 cascade."},

  {"id": "P-26", "subject": "ACTION3 or ACTION4 pressed at spawn", "verdict": "probe-pending",
   "why": "these are the two remaining forged silences; west of spawn is void and east is three lattice cells of unbroken floor, so either press names the east key outright or names it by elimination, and ACTION3 additionally separates the meter readings at an even index."},

  {"id": "E-01", "subject": "a third transition outcome meaning 'unobserved, no prediction'", "verdict": "probe-pending",
   "as": "wrote the_dsl_cannot_say_unknown plus playbook orders that rank a key by whether its predicted inertness rests on a witness",
   "why": "the compiled step is total, so absence of a rule is indistinguishable from a witnessed no-op; this round I found the one lever the grammar does offer -- deleting an unearned guard turns an unwitnessed silence into a falsifiable claim -- but it only works where a guard exists to cut, and for key(3) and key(4) at spawn there is no rule at all."},

  {"id": "E-02", "subject": "a burn rule for the bar's leading edge", "verdict": "reject",
   "as": "wrote i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed",
   "why": "arc-instances: all instances only cells the board cannot explain, a never-varying cell is exactly what the board explains, and a second colour-9 type would be indistinguishable from Glyph9 by an arm that looks objects up by colour alone -- so every fresh burn costs exactly one pixel, permanently, and the correct response is to price it rather than to patch it."},

  {"id": "E-03", "subject": "a click action carrying coordinates", "verdict": "probe-pending",
   "as": "wrote two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click",
   "why": "the guard language has nowhere to put two coordinates, so a click rule would fire on every click anywhere; the knob is a 3x3 target the body appears unable to stand on, which is the shape a click is for, and if a click drives this world my manual can record its effect and never its precondition."},

  {"id": "E-04", "subject": "a goal predicate", "verdict": "reject",
   "as": "no goal section; wrote the_goal_section_is_absent_on_purpose",
   "why": "the socket interior is board so count() cannot range over it, the winning ring cells would type as Vacated and be indistinguishable from the 24 cells one step south of spawn, and every alternative I checked is true in states that are not wins -- a goal true in the wrong state stops a planner at its first step, which is worse than is_goal -> False."}
]
```
```
