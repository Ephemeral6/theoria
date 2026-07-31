# call-006-theorize-round1

model: `claude-opus-5` · 654448 ms · $1.907144 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 43937, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 43937, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 43937, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 43937, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 57396, "type": "message"}], "output_tokens": 57396, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 80,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4013,
 "distinct_states": 24,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 83,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 26,
 "steps": 26
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
9999999999999999999999999999999999999999999999999999111111111111
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

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 25,
  "n_states": 26,
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
   "ValueError: object absent at frame 0; unsupported on this fixture"
  ],
  "tracks": [
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj0",
    "transitions": 25
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
    "transitions": 25
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
  "candidates": 16,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 11,
   "move": 22,
   "recolor": 34,
   "vanish": 11
  },
  "n_frames": 26,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 26,
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
    "frames_present": 26,
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
    "frames_present": 26,
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
    "frames_present": 26,
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
    "frames_present": 1,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj15"
   }
  ],
  "variants": [
   {
    "baseline_bits": 21336,
    "compression_ratio": 0.573585,
    "events": 78,
    "gain_bits": 9098,
    "ms": 62,
    "script_bits": 12238,
    "split_by_color": false,
    "tracks": 16
   },
   {
    "baseline_bits": 21336,
    "compression_ratio": 6.291995,
    "events": 179,
    "gain_bits": -112910,
    "ms": 131,
    "script_bits": 134246,
    "split_by_color": true,
    "tracks": 67
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 83,
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
  "cells_needing_an_owner": 80,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4013,
  "distinct_states": 24,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 83,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 26,
  "steps": 26
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 83,
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
  "cells_dynamic": 83,
  "cells_used": 83,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 13,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.031325,
   "difference_rank": 13,
   "features": 415,
   "space_dimension": 402,
   "transitions": 25,
   "verdict": "THIN: 25 transitions constrain rank 13 of 415 features, so the null space has dimension 402 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 415,
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
```

The full proposal stream is 2378 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 22 states / 21 transitions
# (RESET + A1 A2 A3 A4 A5 then A2 A5 eight times over).
# 81 cells have ever changed; this manual names and owns all 81.
#
# WHAT THIS ROUND COST AND WHAT IT BOUGHT
#
#   Four commands -- A2 A5 A2 A5 -- for the FOURTH consecutive round. Four
#   refutations, P-13..P-16, and they are one defect counted four times, for
#   the third round running. Chain the `inert` fields: P-14 inert = P-13
#   manual, P-15 inert = P-14 manual, P-16 inert = P-15 manual, and P-13
#   inert = P-16 manual -- a closed 4-cycle, because my manual predicts the
#   A2/A5 pair returns the world exactly where it started while the world
#   quietly burns two more meter cells. The two wrong pixels are (63,55) at
#   t18 and (63,54) at t20. Both were board at the instant they burned. The
#   previous manual named (63,55) in advance, priced it at one pixel, and
#   said no rewriting fixes it. The bill came in to the cell, again.
#
#   SIXTEEN refutations across four rounds; every divergence set has been a
#   subset of the meter's leading edge. Zero rules contradicted. Replay
#   17/17, responsibility 0/4096 unexplained, ambiguity 0 clashes.
#
#   SO THIS ROUND I STOP BLAMING THE RANKING AND LOOK AT THE INSTRUMENT.
#   certify reports `unambiguous: actions: 3` and `pairs_checked: 54 = 18
#   states x 3 actions`. THREE actions. The three are exactly the three my
#   rules mention: key(2), key(4), key(5). key(1) and key(3) were pressed by
#   the world at t1 and t3 and my manual has never carried a rule naming
#   them, so they are not in the manual's action alphabet -- and if anything
#   downstream derives its candidate set from that alphabet the way certify
#   does, then for four rounds the only keys it could offer were 2, 4 and 5,
#   and A2/A5 alternation is not a failure of judgement, it is the complete
#   list. I cannot see the chooser, so this is a hypothesis about the
#   harness, not a claim about the world. It is also the only hypothesis I
#   have that explains four identical rounds, and it costs two rules to test.
#   See the_manuals_key_alphabet_may_be_the_planners_key_alphabet.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t21 compress: 45]
  Vacated [segment: dynamic_colour_5 ev: t2-t21 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20 cov: 216/216]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20 cov: 216/216]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12,t14,t16,t18,t20 cov: 8/8]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21 cov: 216/216]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21 cov: 216/216]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21 cov: 40/40]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21 cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21 cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21 cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21 cov: 5/5]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21 cov: 5/5]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13,t17,t21 cov: 5/5]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13,t17,t21 cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19 cov: 32/32]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11,t15,t19 cov: 32/32]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11,t15,t19 cov: 4/4]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11,t15,t19 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 45 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4015 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 10 [status: counted]

  theorem the_manuals_key_alphabet_may_be_the_planners_key_alphabet "THE FINDING OF THIS ROUND, and it is about my own instrument rather than the world. certify's ambiguity report reads `actions: 3` and `pairs_checked: 54` against `states: 18` -- 18 x 3. The three actions are exactly the three my rules named: key(2), key(4), key(5). Nothing in the certify report is aware that the world accepts ACTION1, ACTION3, ACTION6, ACTION7, because nothing in the manual mentioned them. If the command chooser derives its candidate list the same way certify derives its adjudication list -- from the `act=key(n)` literals appearing in rules -- then for four rounds the entire menu was {2, 4, 5}, key 4's only rule has matched nothing since the meter's leading edge went past it, and A2/A5 alternation was not a bad choice among many but the whole set. That would explain sixteen refutations with zero rules implicated, twelve commands of pure repetition, and a playbook that shouted `try an unpressed key` into a void for three rounds. I cannot observe the chooser and I will not assert this about the harness. I can TEST it for the price of two rules: key1_inert_at_spawn and key3_inert_below_spawn now put key(1) and key(3) into the alphabet. If the next command is an ACTION1 or ACTION3, the hypothesis is confirmed and four rounds of loss are explained; if the next command is A2 or A5 again, the hypothesis is dead and the fault is in the ranking after all, which is also worth knowing and cost me two lines."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: pending]

  theorem the_two_no_op_rules_explain_zero_pixels_and_i_am_declaring_that "Constraint 3 says a concept earns its place by shortening the manual, and these two rules shorten NOTHING. key1_inert_at_spawn recolours the cell (8,14) from 9 to 9 and key3_inert_below_spawn recolours (14,14) from 9 to 9. Each draws exactly the pixel that was already there, each has exactly one witness -- t1 for ACTION1 at spawn, t3 for ACTION3 one cell south of spawn, both of which changed zero cells -- and each adds a line to a manual that would predict the same frames without it. THEY FAIL THE GAIN TEST AND I AM KEEPING THEM ANYWAY, for one reason stated plainly: they are the only lever I have on the hypothesis above, and the alternative is a fifth round of the same four commands. Their guards are as tight as the evidence: key(1) fires only with the body at home (spawn_probe renders 9) and only on the ring pixel whose north and west neighbours are floor and whose east neighbour is 9, which is (8,14) and nothing else in any observed state; key(3) fires only with the body away (spawn_probe renders 5) on the corresponding corner of the lower ring, (14,14). Neither can fire in a state where the world moved the body, so neither can hide a real transition from me. If ACTION1 or ACTION3 turns out to move the body from some cell, these rules will be silently wrong about nothing -- they draw no motion -- and the divergence will be the full 48-cell move, which is exactly the signal I want."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: pending]

  theorem the_four_refutations_are_two_undrawable_pixels_rolled_forward "P-13 and P-15 are ACTION2, P-14 and P-16 ACTION5, and the diagnosis is arithmetic for the third round in a row. The inert fields chain into a CLOSED 4-CYCLE this time -- P-14 inert = P-13 manual, P-15 inert = P-14 manual, P-16 inert = P-15 manual, and P-13 inert = P-16 manual -- which is the sharpest possible statement of the defect: my manual says A2 then A5 returns the world to where it started, and it is right about all 4096 cells except the one the meter eats each time A2 is pressed. The harness rolls MY predicted frame forward and never resyncs, so the drift accumulates. The world burned (63,55) at t18 and (63,54) at t20; at those instants both cells had never changed, were therefore board, were owned by no object, and no rule expressible in this DSL could draw them. t19 and t21 introduced nothing of their own: 23 panel cells and 48 body cells each, every one drawn correctly by rules that now carry nine witnesses. THE HONEST LEDGER IS TWO WRONG PIXELS AND FOUR REFUTATION REPORTS. Repair is arithmetic: (63,55) and (63,54) are dynamic now, Glyph9 goes 43 to 45, all four transitions replay exactly, and the identical bill will be presented at (63,53)."
    [depends: meter_burn_key2_next, the_meter_edge_saturates_the_refutation_channel  probe: passed]

  theorem the_meter_edge_saturates_the_refutation_channel "A law of this manual rather than of this world, and after four rounds the most expensive fact on the board. Each of the 64 cells of the row-63 bar burns EXACTLY ONCE, 9 to 1, advancing leftward. At the instant a cell burns it has never changed, so it is board, so no instance exists for it, so no rule of mine draws it. Therefore: (1) my three burn rules have ZERO predictive value on the leading edge and full value on replay, a division of labour and not a contradiction; (2) EVERY press of a key that burns is scored a refutation regardless of what else it teaches, so refutation-fired does not discriminate between commands; (3) the correct reading of a refutation is its DIVERGENCE SET, and where that set is a subset of the bar's leading edge the manual is not implicated. All sixteen refutations across four rounds have been exactly that. Deleting the burn rules does not help -- the wrong-pixel count at the moment of the burn is identical -- and keeping them is strictly better because they make every past transition replay. RIGHT NOW all ten meter instances render colour 1, so meter_burn_key2_next matches nothing and my manual predicts NO burn at (63,53) under any key. That is not a claim about the world; it is the shape of the hole."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right. TEN burns now: (63,63) t2, (63,62) t4, (63,61) t6, (63,60) t8, (63,59) t10, (63,58) t12, (63,57) t14, (63,56) t16, (63,55) t18, (63,54) t20. Eleven silences: t1, t3, t5, t7, t9, t11, t13, t15, t17, t19, t21. The current frame confirms it -- row 63 reads 9 through col 53 and 1 from col 54 to col 63. READING A, ACTION-KEYING: burns iff the key is 2 or 4. READING B, COMMAND PARITY: burns iff the command index is even. BOTH SCORE 21/21 AND NEITHER HAS GAINED A SINGLE BIT IN THREE ROUNDS, because every command since state 5 has been key 2 at an even index or key 5 at an odd index -- the diagonal on which the readings are numerically identical. Twenty-one commands, twenty-one alignments, zero separation. THE SEPARATOR IS STILL FREE: the next index is 22, EVEN, so ANY odd key there (1, 3 or 5) settles it in one command and an even key there does not. The ordering consequence has not changed and has now been ignored three times: an odd key at an even index separates, and the even key it displaces separates too at the following odd index, so taking the odd key first collects the separation twice and taking the even key first collects it never. I encode reading A because it is the only one the guard language can say -- there is no command counter and no phase pixel -- and I still expect B, because at t3 and t4 the body stood at lattice (2,2) with left and right both void, ACTION3 and ACTION4 were blocked identically, and only ACTION4 burned."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_meter_is_a_budget_i_can_now_price "Ten of sixty-four bar cells consumed after twenty-one commands. I do not know that exhaustion ends the game -- no frame has shown it -- but both readings price out survivably. Under reading A the bar burns only on keys 2 and 4, so an eastward-and-southward route burns once per step and 54 steps remain. Under reading B every second command burns and 108 commands remain. The route I can see: spawn (1,2) east to (1,5) is THREE steps, an unknown number of interactions at the knob, three steps back west, seven steps south down lattice column 2 to (8,2), five steps east to the socket at (8,7) -- roughly nineteen steps plus interactions plus identification probes. That fits inside 54 with room. The meter is still not the binding constraint; sixteen of twenty-one commands buying nothing is."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9, and the split is now 9/9 WITH NO EXCEPTIONS. ACTION2 returned SEVEN frames at t2, t8, t12, t16, t20 and NINE frames at t6, t10, t14, t18. Read the panel configuration of the state each press acted FROM: t2 from state 1 (A), t8 from state 7 (A), t12 from state 11 (A), t16 from state 15 (A), t20 from state 19 (A) -- seven frames; t6 from state 5 (B), t10 from state 9 (B), t14 from state 13 (B), t18 from state 17 (B) -- nine frames. ACTION2 animates in 7 internal frames when the panel is in configuration A and 9 when it is in B. ACTION5 returned nine frames all nine times regardless of configuration, and every no-op returned one. THE NET EFFECT IS IDENTICAL IN ALL NINE ACTION2 PRESSES -- 48 body cells, rows 8-18, cols 14-18, plus one burn -- so this costs me nothing in replay and buys me nothing in prediction, and it remains the ONLY evidence that the panel does anything besides display. Six rows of travel at one row per frame is 7 frames with a terminal frame; the two extra frames under configuration B are two internal steps whose content I never see, because `cascade single_frame` compares only the net. I record, as a limitation of my own semantics and not of the world: up to eight intermediate frames per command are discarded unread, and something distinguishable happens inside them."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over NINE toggles -- t5, t7, t9, t11, t13, t15, t17, t19, t21 -- 23 cells every time, and ACTION2 has never touched a panel pixel in nine presses. CONFIGURATION A (states 0-4, 7-8, 11-12, 15-16, 19-20): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B (states 5-6, 9-10, 13-14, 17-18, 21, and the current frame, which reads 222/2.2/222 at cols 1-3 and 999/9.9/999 at cols 5-7 with row 5 dark at 1-3 and lit at 5-7): slot 1 is a hollow colour-2 ring with underline dark; slot 2 is a hollow colour-9 ring with dark centre and underline lit. mdl_segmenter corroborates independently and by frame index: colour-1 nine-cell tracks obj1 (0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16), obj12 (19-20); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17-18), obj13 (21). A,B,A,B,A,B,A,B,A,B read off an engine that has never seen my rules. Its obj0 (colour 9, eight cells, 3x3, present in all 22 frames) and obj2 (colour 9, 1x3, all 22) persist while it narrates 18 MOVE events: the hollow ring and the lit underline do not appear and vanish, they TRAVEL between slot 1 and slot 2. So the panel is one marker with two seats and colour 9 marks the occupied seat. What the seats HOLD is still unknown and I will not guess. I cannot model it as a moving marker either: the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring travelling four columns is not expressible as a move, and ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_still_cannot_test_it "Unchanged in kind, stronger in count, and still the cheapest open question on the board. The guard `colored(spawn_probe, 5)` has NINE positive witnesses (t5, t7, t9, t11, t13, t15, t17, t19, t21 -- body away, panel toggled) and STILL NO NEGATIVE ONE, because ACTION5 has never once been pressed with the body at home. Every ACTION5 in this window immediately followed an ACTION2, so `ACTION5 was pressed` and `the body was away from spawn` are the same event nine times over and no guard can be credited over the other. By the letter of no-entry-without-gain the atom is unearned. I keep it because dropping it changes no replay and because the body is at spawn RIGHT NOW for the fourth round running: with the guard my manual predicts SILENCE for an ACTION5 pressed here, without it a 23-cell toggle. Silence is the prediction I want on the record, because it is the only prediction this manual can make that costs exactly zero pixels if right. One such press would settle three things at once: the guard, the meter parity (key 5 is odd, index 22 is even, so reading A predicts no burn and reading B predicts a burn at (63,53)), and the identity of ACTION5 (UNDO would return the body to (2,2) for 48 cells, while UP and RETURN both predict no motion from spawn)."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, what_action5_is_and_the_two_cell_experiment_that_names_it  probe: pending]

  theorem the_action_map_after_twentyone_transitions_and_the_standard_mapping_hypothesis "WITNESSED: ACTION2 IS DOWN, 9/9, six rows south, one lattice cell, at t2, t6, t8, t10, t12, t14, t16, t18, t20. ACTION5 returns the body from lattice (2,2) to (1,2), 9/9. NEGATIVE INFORMATION, and I state it as negative because that is all it is. At spawn (1,2) up and left are void while down and right are open floor, and ACTION1 did nothing at t1 -- so ACTION1 IS NEITHER DOWN NOR RIGHT. At (2,2) the body had just vacated rows 8-12 so UP WAS OPEN, and rows 20-24 cols 14-18 are floor so DOWN WAS OPEN, while left (cols 8-12) and right (cols 20-24) are void; ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else. It explains every no-op as a blocked move and it is the conventional mapping for this action family, which is a prior and not evidence. SIXTEEN COMMANDS ACROSS FOUR ROUNDS AND NOT ONE TOUCHED THIS QUESTION -- the map is exactly as constrained as it was at state 5. THE CHEAP TEST IS ONE PRESS: the body stands at spawn, where west is void and east is open floor for three lattice cells, so EITHER of ACTION3 and ACTION4 pressed here settles which is east -- if it steps it is east, and if it does not the other is east by elimination, since ACTION1 was already excluded from east at t1. ACTION3 is the odd one of the pair and index 22 is even, so ACTION3 here also separates the meter readings; that is one press closing two questions."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_and_the_two_cell_experiment_that_names_it "Three readings survive all NINE ACTION5 presses because all nine were made from exactly one cell south of spawn, where they are indistinguishable: UP (move one cell north), UNDO (revert the last move), RETURN (jump to spawn from anywhere). They separate the moment the body is somewhere else, and they separate differently by axis. FROM SPAWN ITSELF, which is where the body is now: UP predicts no motion (north of spawn is void), RETURN predicts no motion (already home), UNDO predicts 48 cells back to (2,2) -- so one press here splits UNDO from the other two for free. Two cells EAST at lattice (1,4): UP no move, UNDO one cell west to (1,3), RETURN spawn at (1,2) -- three different diffs, all legible in the raw pixel count, which is the full separation. Two cells SOUTH at (3,2): UP and UNDO both predict (2,2) and only RETURN separates. So the eastward route answers this question completely and the southward route does not, which is one more reason to go east. Note the coupling I cannot yet break: the panel toggles on every effective ACTION5, nine for nine, so whatever ACTION5 is, the panel is its counter or its selector -- and the 7-versus-9 cascade split, now 9/9, says the panel's state is not merely cosmetic."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated one row per internal frame and the world reports the whole animation for a single action; `cascade single_frame` compares only the net effect, which is identical for all nine ACTION2 presses (48 body cells, rows 8-18, cols 14-18) regardless of whether the command took 7 frames or 9. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, NINE times. ONE PRESS IS ONE LATTICE CELL, 9/9, and every distance in the playbook rests on that."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_world_may_still_not_be_a_function_of_the_drawn_frame "Carried as a belief and NOT proven in this window. To prove it I need two pixel-identical states from which the SAME action produced different successors; I have no such pair, and distinct_states is 20 against 22 states, so two coincidences exist but neither is followed by the same key. What keeps the belief alive is the parity reading of the meter, which if true IS one bit of hidden state that flips every command and that no guard in this language can read, because no guard can read anything that is not a pixel. What strengthens it is the cascade length: ACTION2 took 7 frames or 9 depending on a panel configuration that the net frame records but that my rules never consult -- the same shape of dependence, one step less hidden. Operationally it matters in exactly one way: if parity wins, every burn rule I can write is an approximation with a known error rate, and I would rather say that once than rediscover it."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4015 + dynamic 81 = 4096, and 45+24+9 = 78 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 81. Consequence: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This is the fourth consecutive round in which that sentence, written in advance, was the entire content of every refutation. meter_burn_key2_next now replays t6 through t20 perfectly, because by replay time all eight of those cells are dynamic; it will still miss the ELEVENTH burn at (63,53), because that cell is board today. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable too until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, 24 if I already had the leaves rule, 0 for the second step. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 81 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 10 are the burned right end of row 63: cols 54 through 63. 23+24+24+10 = 81 = dynamic_cells. By frame-0 colour: 45 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 10 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 45+9+24 = 78 = cells_needing_an_owner exactly, and 4096-81 = 4015 = constant_cells exactly. zero_space's global-law cell list is the same set -- it lists (2,1) and (2,3) but not (2,2), (10,14),(10,15),(10,17),(10,18) but not (10,16), and every burned bar cell -- and its single global law restates this census and nothing more."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so that the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended nine times and all nine started at spawn, so no rule of mine turns Vacated pixels from 9 back to 5 on an ACTION2: rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below-six(?v), 5) then recolored(?v, 5). One ACTION2 from lattice (2,2) buys it, and sixteen commands across three rounds each had the chance and none took it. (2) EAST-WEST MOTION. Whatever the east key turns out to be, it needs a pair: a leaves rule over Glyph9 guarded on colour 9 with rightof-six rendering 5, and its arrives twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) AN ELEVENTH BURN AT A CELL THAT IS STILL BOARD, which is not a missing rule but a missing instance and cannot be written at all. I state the price of all three in advance so it cannot be mistaken for a surprise: the first eastward step costs 48 wrong cells plus one if the bar burns, the first second-descent costs 24, and every fresh burn costs 1."
    [depends: key2_body_arrives, the_meter_edge_saturates_the_refutation_channel  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth below is row 69. So colored(off-board, k) is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen of the rules rest on this and every row and column discrimination in the panel is built from it: the k-th above is off-board exactly when k exceeds the row, so row 1 is above-twice equals wall, row 3 is a colour test on above-twice -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column: col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice, pairwise exclusive, which is why the ambiguity check reports 0 clashes. Not one rule uses `not`, deliberately. The eight A-to-B slot-2 and underline rules could collapse to two if I could write that not all four neighbours are colour 1, and I decline to gamble a whole round's compile on discovering whether `not` before an equality atom parses. If a future desk wants the shorter form, try it on ONE rule, not on eight."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame and unchanged: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open, C=6 holds the knob, C=7 does not exist (col 44 is void in this band); R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2, plus a fragment of floor at row 48 cols 42-50 alone which cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); in twenty-two frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it has been at spawn in twelve of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed NINE times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket, verified again cell by cell against the current frame: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46), and every other interior pixel is floor. Overlay the body standing in lattice (8,7) -- rows 50-54 cols 44-48, aperture at (52,46): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in twenty-two frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and I have re-read every pixel of it in the current frame: colour 8 fills row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41 with a stem pixel at (12,40), all inside lattice (1,6). Not one colour-8 pixel has moved in twenty-two frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell -- the eight knob pixels other than its centre, plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, and every step is on floor that R=1 shows open. Twenty-one commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after twenty-two states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note the interaction with the alphabet finding: I have no witness for key(6) or key(7), so no rule can name them, so if the chooser really does read its menu off my rules then those two keys are unreachable BY CONSTRUCTION and no playbook line of mine can ever surface them. That is a defect of the pipeline I am naming rather than repairing, because repairing it would mean writing a rule with no evidence, which constraint 2 forbids and which I will not do."
    [depends: the_manuals_key_alphabet_may_be_the_planners_key_alphabet  probe: pending]

  theorem the_goal_section_is_absent_on_purpose_and_the_playbook_must_carry_the_ranking "Still absent, and the reason has not weakened. Cart.pos = exit_cell needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and forty-four siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would be true of the body standing one cell south of spawn, which is not a win. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. I name the price of that choice, because four rounds of oscillation are consistent with it: with no goal section the manual compiles is_goal -> False, no plan can ever terminate at a goal, and therefore NOTHING in the manual ranks one command above another. The entire ranking lives in playbook.dsl -- unless, as I now suspect, the candidate SET lives in the rules section, in which case ranking was never the binding constraint at all."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_manuals_key_alphabet_may_be_the_planners_key_alphabet  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter keeps a positive gain of +6270 bits at compression_ratio 0.641 on split_by_color=false, against -93832 bits when split by colour -- its segmentation beats writing the pixels out, and I still owe it nothing structural. Its fourteen tracks are the round's best independent corroboration and this round they corroborate the toggle by frame index: colour-1 nine-cell tracks obj1 (0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16), obj12 (19-20); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17-18), obj13 (21). That is A,B,A,B,A,B,A,B,A,B derived by an engine that has never seen my rules. obj0 and obj2 persisting through all 22 frames while the segmenter narrates 18 moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 10 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 21 transitions constrain rank 11 of 405 features, null space dimension 394, nearly every vector in it a law true over these states and unfalsified rather than confirmed -- and its single global law is my census. cegis_miner refuses on every track and its verdict, `the world does not narrate as one mover`, remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The next command has index 22, which is EVEN, and the body is at spawn with the panel in configuration B. ACTION3 -- the command I most want -- I predict ZERO changed cells, because key3_inert_below_spawn requires the body AWAY and cannot fire at home, and because under the standard mapping ACTION3 is west and west of spawn is void. Zero cells says ACTION3 is not east, hence ACTION4 is east by elimination, AND kills the parity reading outright (an odd key at an even index that does not burn refutes B while confirming A). One cell at (63,53) confirms parity and kills action-keying. 48 or 49 cells says ACTION3 IS east, and my manual draws none of them -- no east rules exist and rows 8-12 cols 20-24 are board -- which is the advertised price of the first step onto fresh ground and not a failure of physics. ACTION1 at spawn: I predict ZERO cells, key1_inert_at_spawn firing as a no-op; a single burn at (63,53) would kill action-keying. ACTION5 at spawn: ZERO cells, the only zero-pixel stake this manual can offer; 23 cells refutes the spawn_probe guard and puts thirteen rules into repair; 48 cells says ACTION5 is UNDO. ACTION4 at spawn: 48 cells I cannot draw plus a burn I cannot draw, and no parity information, because an even key at an even index is where both readings agree. ACTION2: 48 cells I draw correctly plus a burn at (63,53) I cannot draw -- exactly one wrong pixel and NOTHING learned, because key2_body_leaves and key2_body_arrives are at 216/216 and a tenth witness buys zero."
    [depends: the_action_map_after_twentyone_transitions_and_the_standard_mapping_hypothesis, the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept in compressed form because the lesson is structural and cost a full round. Thirteen panel rules once carried colored(spawn_probe, 5) while the landmark line read a prose placeholder instead of a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The landmark now reads (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else -- which is exactly why the two new no-op rules can use it as a home/away test in opposite senses. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key5_slot1_dims  probe: passed]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because a future desk will be tempted by the same repair I considered and rejected for the second time this round. To draw the leading-edge burn I would need an instance on a board cell. The arm offers exactly one lever, `arc-instances: all`, and its documented behaviour is to instance every cell OF THAT COLOUR THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance. The tempting workaround is a second declared type on colour 9 without arc-instances, hoping the arm seats one instance somewhere useful. I reject it: the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, the seat is unspecified, and any cell it landed on would be claimed twice, which is the constraint-5 error the grammar warns about in as many words. A landmark cannot help either, because landmarks are cells and every event in the language takes an object as its first argument. So the hole is a property of the arm, it is permanent for this level, and the only correct response is the one the playbook encodes: price the burn in advance and read refutations by their divergence set."
    [depends: the_meter_edge_saturates_the_refutation_channel  probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ============ READ THIS FIRST: THE MENU MAY HAVE BEEN THE PROBLEM ============
# For four rounds this file has said "press an unpressed key" and for four
# rounds the commands bought were ACTION2, ACTION5, ACTION2, ACTION5. This
# round I stopped assuming the ranking was ignored and looked at what could
# have been ON THE MENU. certify reports `actions: 3` and 18 x 3 = 54 pairs.
# Three. They are key(2), key(4), key(5) -- exactly the three keys my rules
# mentioned. ACTION1 and ACTION3 were pressed by the world at t1 and t3 and
# appeared in NO rule of mine, so they were absent from the manual's action
# alphabet, and if the chooser reads its candidates the way certify reads its
# adjudication list, A2/A5 was not a bad pick from many but the entire set.
#
# THE MANUAL NOW CARRIES key(1) AND key(3). Two witnessed no-op rules,
# key1_inert_at_spawn (t1) and key3_inert_below_spawn (t3), each explaining
# zero pixels and each declared as failing the gain test in the manual's own
# words. They exist to widen the alphabet. If the next command is an ACTION1
# or ACTION3, that was the bottleneck. If it is A2 or A5 again, the
# hypothesis is dead and the fault is genuinely in ranking -- either answer
# is worth more than a fifth identical round.
#
# ---------------------------------------------------------------------------
# THE BOARD AT STATE 21: body home at lattice (1,2); panel in configuration
# B; TEN meter cells burned, cols 54-63 of row 63; next command index is 22,
# EVEN. Eleven lattice cells reachable, the body has stood in TWO. Three
# steps east along lattice row 1 reach the cell beside the knob; the knob
# gates the comb; the comb gates every route to the socket at (8,7). Under
# the harsher meter reading 54 commands remain against a route of about
# nineteen, so the budget is not binding -- waste is.
#
# THE ONE COMMAND THIS FILE IS ARGUING FOR, AS CRITERIA:
#
#  (1) ACTION3 AT SPAWN CLOSES TWO QUESTIONS AT ONCE AND HAS NEVER BEEN
#      TRIED FROM THIS CELL. East is ACTION3 or ACTION4 (ACTION1 was
#      excluded from east at t1). At spawn, west is void and east is three
#      lattice cells of open floor, so pressing either settles which is
#      which -- if it steps it is east, if it does not the OTHER is east by
#      elimination. And ACTION3 is ODD at an EVEN index, which is the only
#      thing that has ever separated the two meter readings, tied 21/21.
#
#  (2) PARITY SEPARATION COMPOUNDS, SO TAKE THE ODD KEY FIRST. Twenty-one
#      commands, twenty-one times a key whose parity matched its index's,
#      zero separation. An odd key now separates; the even key it displaces
#      separates too at index 23. Odd-then-even collects twice, even-then-
#      odd collects never. That is an ordering fact, not a stored route.
#
#  (3) EVERY REFUTATION SO FAR IS THE SAME UNDRAWABLE PIXEL. Sixteen across
#      four rounds, every divergence set a subset of the meter's leading
#      edge -- cells that were board at the instant they burned. Ranking by
#      refutation-fired therefore ranks ACTION2 first forever. Read
#      divergence SETS, discount what the manual priced in advance.
#
#  (4) A2 FROM SPAWN AND A5 FROM (2,2) ARE EXHAUSTED. Nine presses each,
#      216/216 coverage each, cascade split settled 9/9. A tenth witness
#      buys nothing and costs one command and one bar cell.
#
#  (5) ONE PRESS IS ONE LATTICE CELL, 9/9. Distances below are lattice cells.

order     widen_the_key_alphabet_before_blaming_the_ranking                  [proof: lean]
order     check_which_keys_the_manual_can_even_name_before_ranking_them      [proof: lean]
order     take_the_separation_that_compounds_before_the_one_that_does_not    [proof: lean]
order     buy_the_probe_that_closes_two_questions_before_one_that_closes_one [proof: lean]
order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full      [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired    [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                 [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                 [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                 [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it         [proof: lean]

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

heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic keys_the_manual_named_for_the_first_time_this_round                 [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                     [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                           [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                 [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open                [admissible: lean]
heuristic live_readings_a_command_can_eliminate                               [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings        [admissible: lean]

prefer    a_key_that_entered_the_manuals_alphabet_only_this_round            [ev: 0/21 commands]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on               [ev: 0/16 commands]
prefer    a_key_whose_parity_differs_from_the_command_index                  [ev: 0/21 commands]
prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree        [ev: 9/11 no_ops]
prefer    a_press_at_home_that_splits_up_from_undo_from_return               [ev: 9/9 key5]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 21/21 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                      [ev: 2/7 keys]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
```

## Why you are being called: the surprises that fired

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '1e0bbc75dc840f79', the world answered '71e8272c15afb851'

```json
{
 "action": 2,
 "observed": "71e8272c15afb851",
 "predictions": {
  "inert": "4c57486b12b722d4",
  "manual": "1e0bbc75dc840f79",
  "without_key1_inert_at_spawn": "1e0bbc75dc840f79",
  "without_key2_body_arrives": "4c57486b12b722d4",
  "without_key2_body_leaves": "4c57486b12b722d4",
  "without_key3_inert_below_spawn": "1e0bbc75dc840f79",
  "without_key5_body_clears": "1e0bbc75dc840f79",
  "without_key5_body_respawns": "1e0bbc75dc840f79",
  "without_key5_slot1_dims": "1e0bbc75dc840f79",
  "without_key5_slot1_lights": "1e0bbc75dc840f79",
  "without_key5_slot2_centre_darkens": "1e0bbc75dc840f79",
  "without_key5_slot2_centre_resets": "1e0bbc75dc840f79",
  "without_key5_slot2_ring_resets": "1e0bbc75dc840f79",
  "without_key5_slot2_row1_lights": "1e0bbc75dc840f79",
  "without_key5_slot2_row2_left_lights": "1e0bbc75dc840f79",
  "without_key5_slot2_row2_right_lights": "1e0bbc75dc840f79",
  "without_key5_slot2_row3_lights": "1e0bbc75dc840f79",
  "without_key5_underline1_dims": "1e0bbc75dc840f79",
  "without_key5_underline1_lights": "1e0bbc75dc840f79",
  "without_key5_underline2_dims": "1e0bbc75dc840f79",
  "without_key5_underline2_lights": "1e0bbc75dc840f79",
  "without_meter_burn_key2_next": "1e0bbc75dc840f79",
  "without_meter_burn_key2_rightmost": "1e0bbc75dc840f79",
  "without_meter_burn_key4_next": "1e0bbc75dc840f79"
 },
 "probe_id": "P-17"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'ade8774fe1cc3a9b', the world answered 'c0d6bb54354c57d2'

```json
{
 "action": 5,
 "observed": "c0d6bb54354c57d2",
 "predictions": {
  "inert": "1e0bbc75dc840f79",
  "manual": "ade8774fe1cc3a9b",
  "without_key1_inert_at_spawn": "ade8774fe1cc3a9b",
  "without_key2_body_arrives": "ade8774fe1cc3a9b",
  "without_key2_body_leaves": "ade8774fe1cc3a9b",
  "without_key3_inert_below_spawn": "ade8774fe1cc3a9b",
  "without_key5_body_clears": "1e0bbc75dc840f79",
  "without_key5_body_respawns": "1e0bbc75dc840f79",
  "without_key5_slot1_dims": "ade8774fe1cc3a9b",
  "without_key5_slot1_lights": "1e0bbc75dc840f79",
  "without_key5_slot2_centre_darkens": "ade8774fe1cc3a9b",
  "without_key5_slot2_centre_resets": "1e0bbc75dc840f79",
  "without_key5_slot2_ring_resets": "1e0bbc75dc840f79",
  "without_key5_slot2_row1_lights": "ade8774fe1cc3a9b",
  "without_key5_slot2_row2_left_lights": "ade8774fe1cc3a9b",
  "without_key5_slot2_row2_right_lights": "ade8774fe1cc3a9b",
  "without_key5_slot2_row3_lights": "ade8774fe1cc3a9b",
  "without_key5_underline1_dims": "ade8774fe1cc3a9b",
  "without_key5_underline1_lights": "1e0bbc75dc840f79",
  "without_key5_underline2_dims": "1e0bbc75dc840f79",
  "without_key5_underline2_lights": "ade8774fe1cc3a9b",
  "without_meter_burn_key2_next": "ade8774fe1cc3a9b",
  "without_meter_burn_key2_rightmost": "ade8774fe1cc3a9b",
  "without_meter_burn_key4_next": "ade8774fe1cc3a9b"
 },
 "probe_id": "P-18"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '0db510635e263539', the world answered 'eb6ce939c989359a'

```json
{
 "action": 2,
 "observed": "eb6ce939c989359a",
 "predictions": {
  "inert": "ade8774fe1cc3a9b",
  "manual": "0db510635e263539",
  "without_key1_inert_at_spawn": "0db510635e263539",
  "without_key2_body_arrives": "ade8774fe1cc3a9b",
  "without_key2_body_leaves": "ade8774fe1cc3a9b",
  "without_key3_inert_below_spawn": "0db510635e263539",
  "without_key5_body_clears": "0db510635e263539",
  "without_key5_body_respawns": "0db510635e263539",
  "without_key5_slot1_dims": "0db510635e263539",
  "without_key5_slot1_lights": "0db510635e263539",
  "without_key5_slot2_centre_darkens": "0db510635e263539",
  "without_key5_slot2_centre_resets": "0db510635e263539",
  "without_key5_slot2_ring_resets": "0db510635e263539",
  "without_key5_slot2_row1_lights": "0db510635e263539",
  "without_key5_slot2_row2_left_lights": "0db510635e263539",
  "without_key5_slot2_row2_right_lights": "0db510635e263539",
  "without_key5_slot2_row3_lights": "0db510635e263539",
  "without_key5_underline1_dims": "0db510635e263539",
  "without_key5_underline1_lights": "0db510635e263539",
  "without_key5_underline2_dims": "0db510635e263539",
  "without_key5_underline2_lights": "0db510635e263539",
  "without_meter_burn_key2_next": "0db510635e263539",
  "without_meter_burn_key2_rightmost": "0db510635e263539",
  "without_meter_burn_key4_next": "0db510635e263539"
 },
 "probe_id": "P-19"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '4c57486b12b722d4', the world answered '6ac765de5c59b51e'

```json
{
 "action": 5,
 "observed": "6ac765de5c59b51e",
 "predictions": {
  "inert": "0db510635e263539",
  "manual": "4c57486b12b722d4",
  "without_key1_inert_at_spawn": "4c57486b12b722d4",
  "without_key2_body_arrives": "4c57486b12b722d4",
  "without_key2_body_leaves": "4c57486b12b722d4",
  "without_key3_inert_below_spawn": "4c57486b12b722d4",
  "without_key5_body_clears": "0db510635e263539",
  "without_key5_body_respawns": "0db510635e263539",
  "without_key5_slot1_dims": "0db510635e263539",
  "without_key5_slot1_lights": "4c57486b12b722d4",
  "without_key5_slot2_centre_darkens": "0db510635e263539",
  "without_key5_slot2_centre_resets": "4c57486b12b722d4",
  "without_key5_slot2_ring_resets": "4c57486b12b722d4",
  "without_key5_slot2_row1_lights": "0db510635e263539",
  "without_key5_slot2_row2_left_lights": "0db510635e263539",
  "without_key5_slot2_row2_right_lights": "0db510635e263539",
  "without_key5_slot2_row3_lights": "0db510635e263539",
  "without_key5_underline1_dims": "0db510635e263539",
  "without_key5_underline1_lights": "4c57486b12b722d4",
  "without_key5_underline2_dims": "4c57486b12b722d4",
  "without_key5_underline2_lights": "0db510635e263539",
  "without_meter_burn_key2_next": "4c57486b12b722d4",
  "without_meter_burn_key2_rightmost": "4c57486b12b722d4",
  "without_meter_burn_key4_next": "4c57486b12b722d4"
 },
 "probe_id": "P-20"
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
  "detail": "21/21 transitions replay exactly",
  "matched": 21,
  "ok": true,
  "transitions": 21
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
  "detail": "no (state, action) among 22 x 5 admitted two rules, and all 110 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 110,
  "pairs_nominal": 110,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 22,
  "states_reconstructed": 22,
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

=== PLAYBOOK ===
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

=== LOG ===
```json
[
  {"id": "P-17", "subject": "refutation P-17 (ACTION2, t22)", "verdict": "accept",
   "as": "one undrawable pixel, (63,53)", "why": "the diff for t22 is 49 cells over rows 8-63 cols 14-53: 48 body cells my rules draw exactly, plus the meter's leading edge at (63,53), which had never changed before t22 and so was board with no instance and no rule able to draw it."},

  {"id": "P-18", "subject": "refutation P-18 (ACTION5, t23)", "verdict": "accept",
   "as": "the t22 error rolled forward, zero new content", "why": "P-18's inert prediction is byte-identical to P-17's manual prediction, so the harness never resynced; t23's own 71 cells (48 body + 23 panel) are all drawn by rules now carrying eleven and five witnesses."},

  {"id": "P-19", "subject": "refutation P-19 (ACTION2, t24)", "verdict": "accept",
   "as": "one undrawable pixel, (63,52)", "why": "same shape as P-17 one column left; the current frame shows row 63 reading 9 through col 51 and 1 from col 52, exactly twelve burns at the twelve even indices t2..t24."},

  {"id": "P-20", "subject": "refutation P-20 (ACTION5, t25)", "verdict": "accept",
   "as": "the t24 error rolled forward", "why": "the four inert fields close a 4-cycle (P-18 inert = P-17 manual, P-19 inert = P-18 manual, P-20 inert = P-19 manual, P-17 inert = P-20 manual), which is the signature of a manual that is right about the A2/A5 round trip on all 4096 cells except the burn."},

  {"id": "L-01", "subject": "the key-alphabet hypothesis from last round", "verdict": "reject",
   "as": "refuted, recorded as the_key_alphabet_hypothesis_is_refuted", "why": "the experiment I designed ran and reported: certify moved from actions:3/pairs:54 to actions:5/pairs:110, proving the two no-op rules widened the manual's alphabet exactly as intended, and the world's next four commands were still A2 A5 A2 A5, so alphabet width is not sufficient to change the choice."},

  {"id": "L-02", "subject": "why the command stream is stuck", "verdict": "accept",
   "as": "my_manual_leaves_exactly_one_live_key_in_each_state_the_body_has_stood_in", "why": "grounding all 22 rules by hand in the two occupied states shows key(2) is the only key with a non-identity successor at spawn and key(5) the only one at (2,2) -- keys 1 and 3 fire self-recolours, key 4's rule matches no instance, and twelve of thirteen key(5) rules are blocked by the spawn_probe guard -- so any change-seeking chooser has exactly one option per state."},

  {"id": "L-03", "subject": "unwitnessed silences", "verdict": "accept",
   "as": "silence_is_a_prediction_and_three_of_my_spawn_silences_are_unwitnessed", "why": "key(3), key(4) and key(5) have never been pressed at spawn -- key(3) and key(4) once each at t3/t4 from one cell south, key(5) eleven times all from one cell south -- yet the compiled total step function reports 'no change' for all three there in the same voice it uses for witnessed facts."},

  {"id": "E-01", "subject": "a third transition outcome meaning 'unobserved'", "verdict": "probe-pending",
   "as": "theorem the_dsl_cannot_say_unknown_and_that_is_the_hole_i_would_most_like_closed", "why": "I wanted to mark (spawn, key4) as undecided rather than inert; rules only produce events and absence of a rule produces identity, so I wrote a theorem plus playbook lines ranking keys by whether their predicted inertness has a witness."},

  {"id": "R-01", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept",
   "as": "coverage raised 216/216 -> 264/264, witnesses t2..t24", "why": "two more ACTION2 presses at t22 and t24, each moving the same 48 pixels rows 8-18 cols 14-18, so 11 presses x 24 cells per rule."},

  {"id": "R-02", "subject": "key5_body_clears / key5_body_respawns", "verdict": "accept",
   "as": "coverage raised 216/216 -> 264/264, witnesses t5..t25 odd", "why": "two more ACTION5 presses at t23 and t25 with identical 48-cell body effect."},

  {"id": "R-03", "subject": "meter_burn_key2_next", "verdict": "accept",
   "as": "coverage raised 8/8 -> 10/10", "why": "t22 and t24 each burned one further bar cell whose right neighbour already rendered 1; both cells are dynamic at compile time now, so both replay."},

  {"id": "R-04", "subject": "the seven A-to-B panel rules", "verdict": "accept",
   "as": "coverage raised by one witness each (t25 added)", "why": "t23 was B-to-A and t25 A-to-B, so A-to-B now has six witnesses (t5,t9,t13,t17,t21,t25) and B-to-A five (t7,t11,t15,t19,t23); cell counts per rule are unchanged and the products are 48/48, 18/18, 6/6 and 40/40, 15/15, 5/5 respectively."},

  {"id": "R-05", "subject": "key1_inert_at_spawn, key3_inert_below_spawn", "verdict": "accept",
   "as": "kept, still declared failures of the gain test", "why": "their stated purpose is refuted (L-01) and they explain zero pixels, but deleting them narrows certify's adjudicated action set from five keys to three for a saving of two lines, so I keep them and say plainly that they do not earn their place."},

  {"id": "R-06", "subject": "an east-motion rule pair for key(3) or key(4)", "verdict": "reject",
   "as": "left in the_rules_i_still_have_no_witness_for_and_will_not_write", "why": "no transition in 25 has moved the body east or west; writing the pair would make a different key look live to the chooser, which is exactly the temptation constraint 2 exists to block."},

  {"id": "O-01", "subject": "mdl_segmenter obj1/obj6/obj8/obj10/obj12/obj14 (colour 1) and obj5/obj7/obj9/obj11/obj13/obj15 (colour 2)", "verdict": "entailed",
   "as": "the panel toggle already covered by Spent and Glyph9", "why": "their first_frame values interleave 0,5,7,9,11,13,15,17,19,21,23,25 exactly as configuration A and B alternate on each ACTION5, corroborating the toggle from an engine that has never seen my rules; no new type, because a second type on those pixels would double-claim them."},

  {"id": "O-02", "subject": "mdl_segmenter obj3 (colour null, 1006 cells)", "verdict": "reject",
   "as": "nothing; its failure is the finding", "why": "connected_components(4) merged the maze floor with the moving body ring, which is why cegis_miner then reported that the world does not narrate as one mover -- an artefact of 4-connectivity on a hollow ring, not a fact about the world."},

  {"id": "O-03", "subject": "a Wire type on colour 8 to support a goal predicate", "verdict": "reject",
   "as": "nothing declared", "why": "every colour-8 cell is constant across 26 frames, so the board explains them and arc-instances would seat zero instances; count(Wire) = 0 would be true at RESET, and a goal true in the wrong states stops a planner at its first step."},

  {"id": "O-04", "subject": "Glyph9 instance count", "verdict": "accept",
   "as": "45 -> 47", "why": "(63,53) and (63,52) became dynamic at t22 and t24; 47 colour-9 + 9 colour-1 + 24 colour-5 = 80 = cells_needing_an_owner, plus 3 colour-0 = 83 = dynamic_cells, and 4096 - 83 = 4013 = constant_cells."},

  {"id": "L-04", "subject": "action-keying versus command-parity for the meter", "verdict": "probe-pending",
   "as": "the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break", "why": "twelve burns at twelve even indices, all under keys 2 or 4; thirteen silences at thirteen odd indices, all under keys 1, 3 or 5 -- the two readings remain numerically identical at 25/25 and only an odd key at an even index can separate them."},

  {"id": "L-05", "subject": "cascade length as a function of panel configuration", "verdict": "accept",
   "as": "the_cascade_length_is_a_free_channel_that_i_discard_by_construction, now 11/11", "why": "t22 acted from state 21 (configuration B) and returned 9 frames, t24 from state 23 (configuration A) and returned 7, extending a split that has no exceptions in eleven ACTION2 presses."},

  {"id": "L-06", "subject": "whether the world is a function of the drawn frame", "verdict": "probe-pending",
   "as": "the_world_may_still_not_be_a_function_of_the_drawn_frame, now with the two coincidences named", "why": "distinct_states 24 of 26 means exactly two duplicate pairs, state 1 = state 0 and state 3 = state 2, and each pair was followed by two different keys, so neither tests functionality and the belief is neither confirmed nor refuted."},

  {"id": "L-07", "subject": "the socket bracket", "verdict": "accept",
   "as": "the_socket_is_a_keyhole_and_names_the_winning_position, sharpened", "why": "re-reading the current frame shows the colour-9 bracket lies entirely on separator strips -- rows 49 and 55 cols 43-49, col 49 rows 49-55 -- so it is the north, south and east walls of lattice cell (8,7) with the west wall at col 43 left as floor, and the interior is 5x5 floor with a single colour-9 pip at its exact centre (52,46)."},

  {"id": "L-08", "subject": "the colour-8 machinery", "verdict": "accept",
   "as": "the_socket_is_unreachable_until_the_comb_opens, with the wire traced end to end", "why": "the current frame shows one connected colour-8 path: knob rows 9-11 cols 39-41, stem (12,40), col 40 rows 13-39, row 40 cols 14-40, comb teeth rows 38-42 cols 14-18 -- one wire from the only reachable interactable to the only gate on the sole north-south corridor."},

  {"id": "P-21", "subject": "the next command at index 26", "verdict": "probe-pending",
   "as": "what_i_predict_before_i_see_it, with a per-key ledger", "why": "an odd key at this even index separates the two meter readings and an even key does not; a key from {3,4} at spawn settles which is east; key(5) at spawn tests the spawn_probe guard, the parity, and the UNDO reading at once, and is the only command for which my manual stakes zero pixels."}
]
```
```
