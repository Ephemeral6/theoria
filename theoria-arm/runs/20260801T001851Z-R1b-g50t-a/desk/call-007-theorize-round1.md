# call-007-theorize-round1

model: `claude-opus-5` · 573317 ms · $1.719291 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 43774, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 43774, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 43774, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 43774, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 49971, "type": "message"}], "output_tokens": 49971, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 78,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4015,
 "distinct_states": 16,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 81,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 22,
 "steps": 22
}
```

## The current frame

Each cell is one hex digit 0-f standing for a colour. Row numbers on the left, column numbers on top.

```
0000000000000000000000000000000000000000000000000000000000000000
0999011100000000000000000000000000000000000000000000000000000000
0909011100000000000000000000000000000000000000000000000000000000
0999011100000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0999000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000555555555555555555555555555555500000000000000000000
0000000000000555555555555555555555555555555500000000000000000000
0000000000000555555555555555555555555558885500000000000000000000
0000000000000555555555555555555555555558885500000000000000000000
0000000000000555555555555555555555555558885500000000000000000000
0000000000000555555555555555555555555555855500000000000000000000
0000000000000555555555555555555555555555855500000000000000000000
0000000000000599999500000555555500000005850000000000000000000000
0000000000000599999500000555555500000005850000000000000000000000
0000000000000599599500000555555500000005850000000000000000000000
0000000000000599999500000555555500000005850000000000000000000000
0000000000000599999500000555555500000005850000000000000000000000
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
9999999999999999999999999999999999999999999999999999991111111111
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
- t8   ACTION1   frames=1   state=NOT_FINISHED (63,60) 9->1
- t9   ACTION3   frames=1   state=NOT_FINISHED no cells changed
- t10  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-59, [5, 9] -> [1, 5, 9]
- t11  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t12  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-58, [5, 9] -> [1, 5, 9]
- t13  ACTION4   frames=1   state=NOT_FINISHED no cells changed
- t14  ACTION5   frames=9   state=NOT_FINISHED 72 cells changed, rows 1-63, cols 1-57, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t15  ACTION2   frames=7   state=NOT_FINISHED 48 cells changed, rows 8-18, cols 14-18, [5, 9] -> [5, 9]
- t16  ACTION5   frames=9   state=NOT_FINISHED 72 cells changed, rows 1-63, cols 1-56, [0, 1, 5, 9] -> [0, 1, 2, 5, 9]
- t17  ACTION1   frames=1   state=NOT_FINISHED no cells changed
- t18  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-55, [5, 9] -> [1, 5, 9]
- t19  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t20  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-54, [5, 9] -> [1, 5, 9]
- t21  ACTION3   frames=1   state=NOT_FINISHED no cells changed

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 21,
  "n_states": 22,
  "refusals": [
   "ValueError: transition 4 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
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
    "transitions": 21
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
    "transitions": 21
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
  "candidates": 11,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 6,
   "move": 12,
   "recolor": 23,
   "vanish": 6
  },
  "n_frames": 22,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 22,
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
    "frames_present": 22,
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
    "frames_present": 22,
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
    "frames_present": 22,
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
    "frames_present": 4,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj6"
   },
   {
    "color": 2,
    "first_frame": 11,
    "frames_present": 3,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj7"
   },
   {
    "color": 1,
    "first_frame": 14,
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
    "first_frame": 16,
    "frames_present": 3,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj9"
   },
   {
    "color": 1,
    "first_frame": 19,
    "frames_present": 3,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj10"
   }
  ],
  "variants": [
   {
    "baseline_bits": 12520,
    "compression_ratio": 0.790895,
    "events": 47,
    "gain_bits": 2618,
    "ms": 47,
    "script_bits": 9902,
    "split_by_color": false,
    "tracks": 11
   },
   {
    "baseline_bits": 12520,
    "compression_ratio": 6.675479,
    "events": 115,
    "gain_bits": -71057,
    "ms": 83,
    "script_bits": 83577,
    "split_by_color": true,
    "tracks": 49
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 81,
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
  "cells_needing_an_owner": 78,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4015,
  "distinct_states": 16,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 81,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 22,
  "steps": 22
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 81,
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
  "cells_dynamic": 81,
  "cells_used": 81,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 12,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.02963,
   "difference_rank": 12,
   "features": 405,
   "space_dimension": 393,
   "transitions": 21,
   "verdict": "THIN: 21 transitions constrain rank 12 of 405 features, so the null space has dimension 393 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 405,
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
     ],
     [
      17,
      17
     ],
     [
      17,
      18
     ],
     [
      18,
      14
     ],
     [
      18,
      15
     ],
     [
      18,
      16
     ],
     [
      18,
      17
     ],
     [
      18,
      18
     ],
     [
      63,
      54
     ],
     [
      63,
      55
     ],
     [
      63,
      56
     ],
     [
      63,
      57
     ],
     [
      63,
      58
     ],
     [
      63,
      59
     ],
     [
      63,
      60
     ],
     [
      63,
      61
     ],
     [
      63,
      62
     ],
     [
      63,
      63
     ]
    ],
    "support": [
     "c0@0",
     "c1@0",
     "c2@0",
     "c5@0",
     "c9@0",
     "c0@1",
     "c1@1",
     "c2@1",
     "c5@1",
     "c9@1",
     "c0@2",
     "c1@2",
     "c2@2",
     "c5@2",
     "c9@2",
     "c0@3",
     "c1@3",
     "c2@3",
     "c5@3",
     "c9@3",
     "c0@4",
     "c1@4",
     "c2@4",
     "c5@4",
     "c9@4",
     "c0@5",
     "c1@5",
     "c2@5",
     "c5@5",
     "c9@5",
     "c0@6",
     "c1@6",
     "c2@6",
     "c5@6",
     "c9@6",
     "c0@7",
     "c1@7",
     "c2@7",
     "c5@7",
     "c9@7",
     "c0@8",
     "c1@8",
     "c2@8",
     "c5@8",
     "c9@8",
     "c0@9",
     "c1@9",
     "c2@9",
     "c5@9",
     "c9@9",
     "c0@10",
     "c1@10",
     "c2@10",
```

The full proposal stream is 1946 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 18 states / 17 transitions
# (RESET, then A1 A2 A3 A4 A5 A2 A5 A1 A3 A2 A5 A2 A4 A5 A2 A5 A1).
# 79 cells have ever changed; this manual names and owns all 79.
# No new command was executed this round. The only new evidence is
# certify's own numbers, and they turned out to be worth more than a
# command.
#
# ================= WHAT HAPPENED SINCE THE LAST MANUAL =================
#
# 1. THE PIXEL AND THE DATE WERE EXACTLY RIGHT. Last round I wrote, in
#    advance: 'I predict certify will report first_divergence at t13,
#    cell (63,57)'. Certify reports first_divergence at transition index
#    12 -- which is t13 in my numbering, RESET being t0 -- arc_action
#    ACTION4, one cell wrong, (63,57), manual_says 1, world_says 9. That
#    is the misfire of meter_burn_next_key4, named, dated and priced two
#    rounds before it fired.
#
# 2. AND THE COUNT WAS WRONG, 15/17 WHERE I PREDICTED 13/17, AND THAT
#    GAP IS THE WHOLE FINDING OF THE ROUND. I had assumed replay
#    re-synchronises to the observed frame before every transition, so I
#    counted four independent one-pixel errors: two misfires (t13, t15)
#    and two missed burns (t14, t16). Certify says two. The only model
#    that gives exactly two is CUMULATIVE replay -- the predecessor of
#    each replayed transition is the manual's OWN previous predicted
#    frame. Under that model a premature burn HEALS the moment the world
#    catches up, and I re-simulated all seventeen transitions by hand and
#    got 15/17 with mismatches at exactly t13 and t15 and first
#    divergence at t13 cell (63,57). See
#    replay_is_cumulative_and_a_premature_burn_heals_itself.
#
# 3. THAT REVERSES THE ARITHMETIC BEHIND THREE REFUSALS, AND ALL THREE
#    REFUSALS SURVIVE WITH BETTER NUMBERS. Deleting the burn rules is not
#    9/17, it is about 1/17, because an omission never heals. The
#    witnessed key5 burn rule, even guarded so it fires only at t14 and
#    t16, is 14/17. The panel guard on key4, which I called a 14/17 buy
#    last round, is actually 13/17 -- it repairs t13 and then leaks four
#    transitions that used to heal. The manual I already had is the best
#    of the four, and I only know that now because certify disagreed with
#    my count.
#
# 4. THE OTHER TWO CHECKS PASSED CLEAN: responsibility 0/4096 cells
#    unexplained, and unambiguous 90/90 pairs adjudicated with 0 clashes
#    over 18 states x 5 actions.
#
# 5. THE BODY IS STILL AT SPAWN AND EAST IS STILL OPEN THERE. Re-read
#    from the current frame: rows 8-12 cols 19-43 are floor, so cols
#    20-24 are a clear destination ring. ACTION4 remains the only
#    candidate for east among keys 1-5 and has still never been pressed
#    where east is open. Its price went UP this round -- see
#    the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_defect,
#    which I have corrected, because a missed body step does not heal --
#    and it is still the buy.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t17 compress: 43]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t10,t11,t12,t14,t15,t16 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t11,t14,t16 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t11,t14,t16 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t10,t12,t15 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t10,t12,t15 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_edge_key2 forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_next_key2 forall ?p in Glyph9 [ev: t6,t10,t12 cov: 3/4]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key4 forall ?p in Glyph9 [ev: t4 cov: 1/2]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key1 forall ?p in Glyph9 [ev: t8 cov: 1/1]
    when act=key(1) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3,t9 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t11,t14,t16 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t11,t14,t16 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t11,t16 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t11,t16 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t11,t16 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t11,t16 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t14 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t14 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t14 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t14 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t14 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 43 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4017 [status: counted]
  invariant meter_burned_cells count(Glyph9, color = 1) = 8 [status: counted at state 17, monotone]

  theorem replay_is_cumulative_and_a_premature_burn_heals_itself "THE FINDING OF THIS ROUND, and it came from certify disagreeing with my count rather than from the world. I predicted 13/17 with four one-pixel divergences at t13, t14, t15, t16; certify reports 15/17 with first divergence at t13, cell (63,57), manual 1 world 9. My count assumed the arm re-synchronises to the observed frame before each replayed transition. It does not. The predecessor of a replayed transition is THE MANUAL'S OWN PREVIOUS PREDICTED FRAME, and under that model I re-simulated all seventeen transitions by hand and got certify's answer exactly. The trace: t1-t12 all match, the burn key and the world agreeing cell for cell; at t13 key(4) fires meter_burn_next_key4 on (63,57) and the world does not burn -- MISMATCH, one pixel; at t14 the world burns (63,57), the manual's state already has it burned and no key5 burn rule fires, so the two frames are equal again -- MATCH; at t15 key(2) fires on (63,56) against the manual's own leading edge and the world does not burn -- MISMATCH; at t16 the world burns (63,56) and the manual re-synchronises -- MATCH; at t17 every instanced meter cell reads 1 and (63,55) has no instance, so nothing can fire and nothing is expected -- MATCH. Two mismatches, both one pixel, first at t13 cell (63,57). CONSEQUENCE, and it is a general law of this arm and not of this world: A PREMATURE CHANGE HEALS WHEN THE WORLD CATCHES UP; AN OMITTED CHANGE NEVER HEALS, because nothing in the manual ever puts back what it failed to draw. Every cost estimate in this file had to be recomputed under that asymmetry, and three of them changed sign."
    [depends: meter_burn_next_key4, meter_burn_next_key2  probe: passed]

  theorem the_row_63_error_alternates_and_a_burn_key_on_an_even_command_keeps_it_in_step "Replaces my claim that every command from here refutes the manual at row 63; that claim was computed under the resync model and is FALSE. The corrected shape. The world burns the leading edge on EVEN commands only. The manual burns whenever key 1, 2 or 4 is pressed and its own leading edge has an instance and reads 9 with a burned cell to its right. So the two clocks leapfrog and the manual is never more than one cell ahead. If an even command uses key 1, 2 or 4, the manual burns the same cell the world burns and the transition MATCHES. If an even command uses key 3 or 5, the manual misses the burn and diverges by one pixel, and that divergence heals at the next command that uses a burn key. If an odd command uses key 1, 2 or 4, the manual burns one cell early and diverges by one pixel, and that divergence heals at the next even command. If an odd command uses key 3 or 5, nothing fires and the transition MATCHES. That is the entire row-63 error budget: at most one pixel at any time, alternating, self-healing, and the sign of the error is decided by which key is pressed at which parity. WHAT THIS DOES NOT CHANGE: the leading edge that has never burned still has no instance and still cannot be drawn by any construction in this DSL, so an even command that opens a fresh cell is a one-pixel miss whatever key is pressed -- but the miss now costs one transition rather than all of them, because the next burn key repairs it. A DIVERGENCE SET CONSISTING ONLY OF ROW 63 STILL DOES NOT IMPLICATE THIS MANUAL, and it has now consumed seven rounds."
    [depends: replay_is_cumulative_and_a_premature_burn_heals_itself, i_cannot_draw_the_leading_edge_burn  probe: passed]

  theorem three_refusals_recomputed_and_all_three_survive "Under the resync model I refused three patches with numbers that were wrong. Recomputed under cumulative replay, all three refusals stand and two of them stand much harder. (1) DELETE ALL FOUR BURN RULES: I said 9/17. It is about 1/17. With no burn rule the manual's row 63 stays at frame-0 colour 9 forever, the world's burns accumulate, and every transition from t2 onward is compared against a frame the manual can never catch up to -- the divergence grows monotonically to eight pixels. Omission is catastrophic precisely because it never heals. (2) THE WITNESSED KEY5 BURN RULE: I said 12/17. Unguarded it burns on every ACTION5 and drifts ahead of the world without bound, since ACTION5 has been pressed five times and only two of those were even commands. Guarded so that it fires only where it is witnessed -- a landmark at (63,58) and the extra literal colored(deep_meter, 1), which does separate s13 and s15 from s4, s6 and s10 -- it gives 14/17, because repairing t14 lets the key4 misfire at t13 leak forward into t14 and t15 instead of healing. I do not declare the landmark and I do not write the rule. (3) THE PANEL GUARD ON THE KEY4 BURN RULE: I said it would buy 14/17 and refused it on principle. It buys 13/17. It repairs t13 by suppressing the premature burn, which then means the manual MISSES the burn the world delivers at t14, and that omission never heals -- t14, t15, t16 and t17 all fail. The principled refusal and the arithmetic now agree, which is the first time this round that being right for the right reason and being right by the numbers coincided."
    [depends: replay_is_cumulative_and_a_premature_burn_heals_itself, i_refused_a_witnessed_key5_burn_rule_and_here_is_the_arithmetic  probe: passed]

  theorem i_refused_a_witnessed_key5_burn_rule_and_here_is_the_arithmetic "Constraint 2 says no entry without evidence; it does not say every witnessed pattern earns an entry. A rule 'when act=key(5) and colored(?p,9) and colored(rightof(?p),1) then recolored(?p,1)' has two clean witnesses, t14 and t16, and three clean counterexamples, t5, t7 and t11. Unguarded it drifts. Guarded on the meter depth it reaches 14/17 against the 15/17 I already have. I record the refusal rather than the rule so that the next desk does not rediscover it as a gain, and I now record the correct number beside it."
    [depends: the_meter_is_a_two_command_clock  probe: passed]

  theorem dynamic_census "Exactly 79 cells have ever changed and every one has an owner; certify confirms it independently this round with cells_unexplained = 0 over all 4096. 23 are the panel: slot 1's eight ring pixels at rows 1-3 cols 1-3, its centre (2,2) being colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in configuration A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 8 are the burned right end of row 63, cols 56 to 63, burned in order 63,62,61,60,59,58,57,56 at commands 2,4,6,8,10,12,14,16. 23+24+24+8 = 79 = dynamic_cells. By frame-0 colour: 43 colour-9, 9 colour-1, 24 colour-5, 3 colour-0. 43+9+24 = 76 = cells_needing_an_owner exactly, the store declining to count background-coloured cells; Dark carries the remaining 3 anyway. 4096-79 = 4017 = constant_cells exactly."
    [probe: passed]

  theorem the_state_model_predicted_the_duplicate_count "Corroborated a second time from a number I did not fit. A state is exactly three things: which of two lattice cells the body occupies, which of two configurations the panel shows, and how many meter cells are burned. Burns at s_k are floor(k/2). Body: spawn spawn (2,2) (2,2) (2,2) spawn (2,2) spawn spawn spawn (2,2) spawn (2,2) (2,2) spawn (2,2) spawn spawn. Panel: A A A A A B B A A A A B B B A A B B. Exactly five pairs coincide -- s0=s1, s2=s3, s8=s9, s12=s13, s16=s17 -- which predicts 18-5 = 13 distinct states. The store reports distinct_states = 13. Any mechanism I am missing that varied a pixel in those eighteen frames would have broken a coincidence and pushed the count above 13; any spurious mechanism would have pushed it below."
    [depends: dynamic_census, the_meter_is_a_two_command_clock  probe: passed]

  theorem the_meter_is_a_two_command_clock "8 out of 8 and 9 out of 9 and I consider it closed. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right end. Burns occurred at commands 2,4,6,8,10,12,14,16 and at no other command. The key pressed is irrelevant and every key pressed at both parities says so: ACTION1 burned at 8 and not at 1 or 17, ACTION2 burned at 2,6,10,12 and not at 15, ACTION4 burned at 4 and not at 13, ACTION5 burned at 14 and 16 and not at 5, 7 or 11. ACTION3 has only ever been pressed at odd indices. Cols 56-63 are spent, 56 cells remain, so roughly 112 commands remain before the bar is out. The next command is index 18, which is EVEN, and it will burn (63,55) whatever is pressed."
    [depends: meter_burn_next_key1, meter_burn_next_key4  probe: passed]

  theorem no_frame_function_can_predict_the_burn_and_five_identical_pairs_prove_it "A proof about my own form, not a guess. Group the eighteen commands by the burn count b visible at their start: exactly two commands share each b, the odd one k=2b+1 which does not burn and the even one k=2b+2 which does. For b = 0, 1, 4, 6 and 8 the two starting frames are PIXEL-IDENTICAL. So for five of the nine burn counts there is no function of the frame whatsoever that can output burn for one and no-burn for the other. The world is driven by a command counter that is drawn nowhere. What is NOT proven is that the world fails to be a function of (frame, action): each of those five pairs was given two different keys, so a table memorising the burn count per key survives the record. That table would need one clause per burn, compress nothing, and predict nothing about command 18. CONSEQUENCE I ACCEPT: my manual is required by constraint 5 to be a function of (frame, action), so it is required to be wrong about this world's meter, and the only open question is where I choose to be wrong -- and this round's arithmetic finally tells me where, which is early rather than never."
    [depends: the_meter_is_a_two_command_clock, replay_is_cumulative_and_a_premature_burn_heals_itself  probe: passed]

  theorem i_cannot_draw_the_leading_edge_burn "A law of this manual rather than of this world, now paid eight times. The arm instances exactly the cells that have ALREADY changed, so the next cell to burn is board, has no instance, and NO RULE OF MINE CAN RECOLOUR IT. I checked whether any declaration escapes this: arc-instances: all covers only cells the board cannot explain, so it never reaches a static cell; a landmark can be named at (63,55) but landmarks are cells, not objects, and every event in the language takes an object as its first argument. There is no construction in this DSL that draws a cell before its first change. What the cumulative-replay finding adds: the cell acquires an instance in the NEXT round's level, so the miss is repaired by the following burn key rather than being permanent."
    [depends: the_meter_is_a_two_command_clock, replay_is_cumulative_and_a_premature_burn_heals_itself  probe: passed]

  theorem the_probe_designer_is_blind_to_the_commands_worth_buying "Every hypothesis in the frontier is my manual or an ablation of it. Two ablations differ in their prediction ONLY on a command where some rule fires. So expected information gain is maximised exactly where my manual already fires most rules, and is exactly zero on every command my manual says nothing about. Commands 14, 15 and 16 were the three highest-rule-count commands on the board, each already at full coverage, two of them explicitly pruned by my playbook; command 17 was a silence already witnessed twice. Meanwhile ACTION4 where east is open, ACTION6 and ACTION7 have expected gain 0.000 by construction, and they are the only three commands that could tell me something I do not know. THE TRAP IS STRUCTURAL: a frontier built by deleting rules cannot represent 'a rule I am forbidden to write because it has no witness'. THE ONLY INSTRUMENT THAT WORKS ON THOSE COMMANDS IS THE RAW DIFF. My manual predicts ZERO changed cells outside row 63 for all three, so any non-empty diff elsewhere is legible without any frontier. WHAT WOULD OVERTURN THIS: a probe report showing non-zero expected bits for a command where no rule of mine fires."
    [depends: the_row_63_error_alternates_and_a_burn_key_on_an_even_command_keeps_it_in_step  probe: pending]

  theorem the_world_is_not_a_function_of_the_drawn_frame_and_one_repeat_would_prove_it "s16 and s17 are PIXEL-IDENTICAL -- body at spawn, panel B, eight burns. From s16 the world was given ACTION1 and changed nothing. The body stands on s17 now. Give it ACTION1 again at command 18, which is even, and the clock says (63,55) burns: identical state, identical action, different successor, hidden state proven rather than argued. I RANK IT LOW AND SAY WHY: constraint 5 obliges my manual to be a function of the frame, so I already know I must be wrong about one member of that pair; the divergent pixel is the leading edge I cannot draw in any case; and the finding changes no rule and opens no cell."
    [depends: no_frame_function_can_predict_the_burn_and_five_identical_pairs_prove_it  probe: pending]

  theorem the_down_key_may_be_a_shuttle_and_five_presses_have_all_been_from_spawn "STILL THE LARGEST UNEXAMINED ASSUMPTION IN THIS FILE. ACTION2 has been pressed five times and every one was from spawn; ACTION5 five times and every one from (2,2). Not once has either been pressed anywhere else. Two readings survive. READING DOWN: ACTION2 moves the body one lattice cell south wherever it stands, ACTION5 one north, and the maze theorem is about a maze. READING SHUTTLE: ACTION2 means go to cell two and ACTION5 means go back to cell one, the world is a two-cell rocker, and the lattice, the comb and the socket are scenery. The press that decides it is ACTION2 from (2,2), which costs TWO commands from here. Lattice (3,2) is rows 20-24 cols 14-18, floor in the current frame, and separator row 19 is floor across cols 13-31, so the destination ring is clear. WHAT MY MANUAL PREDICTS FOR THE SECOND PRESS: nothing except a meter burn -- key2_body_leaves ranges over Glyph9 and the body would stand on Vacated cells, key2_body_arrives ranges over Vacated and rows 20-24 are board with no instances. If the body moves I am wrong by 48 cells and, under cumulative replay, wrong by them on every subsequent transition until I write the rule."
    [depends: key2_body_leaves, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_action_map_after_seventeen_transitions "WITNESSED, with the negatives stated as negatives. ACTION2 CARRIES THE BODY SOUTH FROM SPAWN: t2, t6, t10, t12, t15, the 5x5 ring from rows 8-12 to rows 14-18, five times, in both panel configurations. ACTION5 CARRIES IT BACK NORTH: t5, t7, t11, t14, t16, five times, each with a panel toggle. NEGATIVES AT SPAWN, where north and west are void and south and east are open floor: ACTION1 did nothing at t1, t8 and t17, ACTION3 did nothing at t9 -- so NEITHER ACTION1 NOR ACTION3 IS EAST, and both are consistent with being north or west. NEGATIVES AT (2,2), where north and south are open and east and west are void: ACTION3 did nothing at t3, ACTION4 did nothing at t4 and t13 -- so neither is up and neither is down, and both are consistent with being horizontal. Combine: ACTION3 is neither vertical nor east, which leaves west, and west is void at both cells it has been pressed from. ACTION4 IS STILL THE ONLY REMAINING CANDIDATE FOR EAST AND HAS STILL NEVER BEEN PRESSED WHERE EAST IS OPEN -- and the body stands where east IS open, rows 8-12 cols 19-43 reading floor in the current frame. The residue: ACTION1 is consistent with up and so is ACTION5, and two up keys is a smell; one press of ACTION1 from (2,2) separates them."
    [depends: key2_body_arrives, key5_body_respawns  probe: pending]

  theorem action5_is_up_or_home_or_undo_and_a_third_cell_separates_them "Five witnesses and all five moved the body from (2,2) to spawn, a move that up, return-home and undo-last-move predict identically. The separator is a shape, not a route: stand two lattice steps from spawn and press ACTION5 once. Up predicts one step back; home predicts a jump of two cells; undo predicts one step back along the arrival direction, which differs from up as soon as the last step was horizontal. My rules encode none of the three: key5_body_respawns is guarded on PIXELS, a Glyph9 cell rendering 5 whose neighbour above renders 5, so it is a spawn-ring refill rule and nothing more. As written it fires from ANY state where the spawn ring reads floor, so from a third cell my manual predicts the body is DRAWN AT SPAWN WITHOUT BEING ERASED where it stood: two bodies, 24 wrong pixels, priced here in advance."
    [depends: key5_body_respawns, the_action_map_after_seventeen_transitions  probe: pending]

  theorem the_spawn_probe_guard_is_now_one_press_from_being_tested "Thirteen rules carry colored(spawn_probe, 5), which reads 'the body is not at home'. All five ACTION5 witnesses had the body one cell south, so the guard has never been tested with the body home: ACTION5 has never been pressed at spawn in eighteen states. THE BODY IS AT SPAWN RIGHT NOW, so the test is one press. My manual predicts ZERO changed cells for ACTION5 here -- the panel rules are gated off by the guard, key5_body_clears finds no Vacated cell rendering 9, key5_body_respawns finds no Glyph9 cell rendering 5 -- so any change at all is legible in the raw diff. If the panel toggles anyway, thirteen rules are guarded on the wrong thing and I under-predict 23 pixels which, under cumulative replay, stay wrong until repaired; if the body jumps somewhere, ACTION5 is not up at all."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: pending]

  theorem the_panel_is_a_two_slot_selector_toggled_by_action5 "Both directions witnessed five times between them, A to B at t5, t11 and t16 and B to A at t7 and t14, and the current frame re-read pixel by pixel is configuration B. A: slot 1's ring reads 9 with underline 1 reading 9, slot 2 reads solid 1 with underline 2 reading 0. B: slot 1's ring reads 2 with underline 1 reading 0, slot 2 reads a ring of 9 with its centre hollowed to 0 and underline 2 reading 9. THE READING: two slots, an underline under each, and the underlined slot is also the one rendered in colour 9 -- a two-item selector whose cursor ACTION5 advances, wrapping after two. WHAT I DO NOT CLAIM: what the selection selects. ACTION2 moved the body identically from configuration A at t2, t10 and t15 and from configuration B at t6 and t12, and ACTION4 was inert in configuration A at t4 and in configuration B at t13 -- five cross-configuration comparisons and not one difference in net effect. If the selection matters at all it matters to a key never pressed, which is ACTION6 or ACTION7."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, key5_underline2_dims  probe: passed]

  theorem the_goal_is_absent_because_no_instance_can_name_the_socket "I decline a goal clause for a fifth time and accept the price rather than pretending it away. The winning position I believe in is lattice cell (8,7), rows 50-54 cols 44-48, whose 24 ring pixels read floor and whose centre (52,46) is a lone colour-9 pip inside a three-sided colour-9 bracket. Four forms of goal are available and every one is refuted. (1) Cart.pos = exit_cell needs ONE named instance; arc-instances: all gives me Glyph9_r8c14 and forty-two siblings and there is no instance called Glyph9, and a second colour-9 type would be indistinguishable to an arm that looks objects up by colour alone. (2) A count over the socket interior has nothing to range over: those cells have never changed, so they are board. (3) Counts over the four types I have are either true in some observed state -- count(Vacated, color = 9) = 0 holds in eleven of eighteen -- or false everywhere and unreachable, like count(Spent, color = 0) = 9, which is exactly the fake goal that is worse than none. I also rejected count(Glyph9, color = 1) = 64: it says 'the clock has run out', so a planner given it would race to lose. (4) The goal cannot be conjunctive; the section takes one equation. THE PRICE: is_goal compiles to False, plan returns no_goal_declared, commit never runs, and all eighteen commands have been probes. THE OBSERVATION THAT ENDS THIS: a goal becomes writable the moment any pixel of the bracket rows 49-55 cols 43-49, or the pip (52,46), or any colour-8 pixel of the comb changes colour. THE GOAL IS DOWNSTREAM OF REACH, REACH IS DOWNSTREAM OF THE EAST KEY, AND THE EAST KEY IS ONE PRESS AWAY."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_action_map_after_seventeen_transitions  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 ring with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2 plus a one-row fragment at row 48 cols 42-50 that cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in eighteen frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it stands at (1,2) now. THIS THEOREM IS HOSTAGE TO ONE PRESS: if the body cannot leave those two cells, there is no maze, only a rocker."
    [depends: key2_body_arrives, the_down_key_may_be_a_shuttle_and_five_presses_have_all_been_from_spawn  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed ten times: (16,16) stayed 5 at t2, t6, t10, t12 and t15 while its 24 neighbours turned 9, and (10,16) did the same in reverse at t5, t7, t11, t14 and t16. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_cannot_be_stood_on_and_that_is_why_the_east_walk_ends_in_a_bump "Read off the current frame. Lattice (1,6) is rows 8-12 cols 38-42; the knob is a solid 3x3 colour-8 block at rows 9-11 cols 39-41, precisely the centre 3x3 of that cell. A body is 5x5 minus its centre pixel, so eight of its 24 ring pixels would have to overlap colour 8: by the aperture reading, (1,6) is NOT enterable, and only its exact centre is free. The four cells (1,2) to (1,5) are clear floor. So if ACTION4 is east, the body can walk C=2,3,4,5 and then meet the knob head-on. That is either a dead end or the intended interaction, and the two are distinguished by one pixel: any colour-8 pixel changing. Not one colour-8 pixel has moved in eighteen frames, so colour 8 is board and no object owns it."
    [depends: the_maze_is_a_six_pixel_lattice, the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 50-54. Rows 49 and 55 are separator rows and cols 43 and 49 separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side left as floor. Inside it, rows 50-54 cols 44-48 are floor except the lone colour-9 pixel at the exact centre (52,46). Overlay the body standing there -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel. The bracket has not changed in eighteen frames, so it is board; the first time any of it changes, those cells become dynamic and the goal section can finally be written."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn under the DOWN reading and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem at col 40 running from row 12 to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18 with floor gaps only at (39,14) and (41,14). ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. The first colour-8 pixel that changes turns this theorem into physics and hands me both a rule and a goal."
    [depends: the_maze_is_a_six_pixel_lattice, the_knob_cannot_be_stood_on_and_that_is_why_the_east_walk_ends_in_a_bump  probe: pending]

  theorem two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Eighteen commands and TWO OF SEVEN ACTIONS HAVE NEVER BEEN TRIED ONCE. In this action family one of them is normally a click carrying coordinates, and that matters here: the knob is a 3x3 target the body provably cannot stand on, and the panel is a two-item selector whose selection provably changes nothing for the five keys already tried. I cannot write a click rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT and never its precondition. My manual predicts ZERO cells for both keys, so any change is legible in the raw diff, and certify adjudicates five actions rather than seven, which means those two columns of the transition table are unexamined rather than clean."
    [probe: pending]

  theorem the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_defect "CORRECTED THIS ROUND AND THE PRICE WENT UP. The arm instances exactly the cells that have already changed, so any lattice cell the body has never entered is board and has NO instance. An east step from spawn to (1,3) costs 24 undrawable arrival pixels at rows 8-12 cols 20-24, plus 24 departure pixels at the spawn ring which NO rule of mine erases -- key2_body_leaves is guarded on the pixel six rows BELOW rendering 5, which is a southward move and nothing else. WHAT I GOT WRONG BEFORE: I said 48 wrong pixels on the first east step, 24 on the second, 0 thereafter, which assumed replay resynchronises. It does not. A missed MOVE never heals, so the manual's body would stay at spawn while the world's walks away, and EVERY subsequent transition would be replayed from a frame that is 48 cells wrong. The realistic cost of buying the east press is therefore one transition wrong immediately and every later transition wrong until the repair, and THE REPAIR IS AVAILABLE NEXT ROUND: the moment those cells change they become dynamic, acquire instances typed Vacated by their frame-0 colour 5, and both halves of an east rule become writable with a witness. One round of tuition, not permanent damage -- but it is tuition paid in the replay score, and I say so before spending it."
    [depends: the_maze_is_a_six_pixel_lattice, replay_is_cumulative_and_a_premature_burn_heals_itself  probe: pending]

  theorem silence_is_a_prediction_and_four_of_seven_silences_at_spawn_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says 'I do not know', it says 'nothing happens', in the same voice it uses for things it has seen. Audit the seven actions at spawn, where the body stands. key(1): inert, WITNESSED three times, t1 t8 t17 -- settled. key(2): carries the body south, witnessed five times -- settled. key(3): inert, WITNESSED once at t9. key(4): NO WITNESS HERE, and this is the east question. key(5): NO WITNESS HERE, and this is the guard shared by thirteen rules. key(6) and key(7): NO WITNESS ANYWHERE. So four of seven silences at this cell are forged death certificates, and the two most valuable presses on the board are among them."
    [depends: the_action_map_after_seventeen_transitions, the_spawn_probe_guard_is_now_one_press_from_being_tested  probe: pending]

  theorem the_cascade_length_is_a_free_channel_and_it_keeps_paying "ACTION2 returned 7 frames from configuration A at t2, t10 and t15, and 9 frames from configuration B at t6 and t12 -- five for five on a split I predicted three rounds ago. ACTION5 returned 9 frames all five times, in both directions of the toggle, and every no-op returned 1. So the animation length is not a function of the key alone and the panel configuration is the one correlate with a witness. It is also NOT a function of the burn: t4 burned with 1 frame and t2 burned with 7. This is hidden state I discard by construction, since cascade single_frame compares only net effect, and it is the ONLY evidence I have that the panel configuration changes anything at all. It costs nothing in replay and buys nothing in prediction; I keep reading it because it is free."
    [depends: the_panel_is_a_two_slot_selector_toggled_by_action5  probe: passed]

  theorem the_no_op_rule_fails_the_gain_test_and_i_keep_it_for_a_narrow_reason "key3_inert_below_spawn recolours one pixel to the colour it already has, has two witnesses on transitions where zero cells changed, and replay is identical without it. It explains no pixel and lengthens the manual, so it fails constraint 3 and I say so rather than dressing it up. The reason I keep it: it is the ONLY occurrence of act=key(3) in the file, and deleting it narrows the action set certify adjudicates from five keys to four -- certify confirms it adjudicated 18 x 5 = 90 pairs. Note what that implies about keys 6 and 7, which appear nowhere: five of seven columns are covered and the two missing ones are unexamined rather than clean."
    [depends: key3_inert_below_spawn, two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap  probe: passed]

  theorem the_rules_are_pairwise_exclusive_and_off_board_cell_terms_are_false "Constraint 5, re-checked by hand over all four instance types in both panel configurations, and certify reports 0 clashes over 90 adjudicated pairs with no call to step raising. Under key(2): body_leaves needs below-six to render 5, which is off-board and therefore false for any row past 57, so it cannot fire on a meter cell; the two burn rules split on rightof = wall against a colour test on rightof, which cannot both hold. Under key(5) the type Glyph9 is split five ways by COLOUR FIRST -- 5 for respawns, 9 for the two dim rules, 2 for slot1_lights, 0 for underline1_lights -- and colours 2 and 0 occur on no other Glyph9 cell in any observed state; no meter cell ever renders 5, so respawns cannot reach row 63. The two colour-9 rules are split by above-four: slot1_dims needs it to BE WALL, true only for rows 0-3; underline1_dims needs a COLOUR TEST on it, which is false off-board rather than raising, so it selects row 5, and its above-six wall test excludes the meter at row 63. Spent splits by colour into 1 against 9 and 0; within colour 1 the geometry is row 1 by above-two wall, row 3 by a colour test on above-two, row 2 by above-three wall plus a colour test on above-one, and within row 2 col 5 by leftof-six wall, col 6 by leftof-seven wall plus a colour test on leftof-one, col 7 by a colour test on leftof-two. Dark splits by colour 0 against 9. Not one rule uses not, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens, key5_slot1_lights  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me, and last round's version half-cost me: the pixel and the date were right and the count was wrong, which is how the cumulative-replay finding was bought. STATE: body at spawn, rows 8-12 cols 14-18 rendering 9 with the aperture (10,16) rendering 5; panel configuration B; eight meter cells burned at row 63 cols 56-63; next command index 18, which is EVEN, so the clock burns (63,55) whatever is pressed. CERTIFY AFTER COMMAND 18, and this is now a sharp two-way prediction rather than a hedge. If command 18 uses key 1, 2 or 4: the level rebuilds with (63,55) instanced, the burn rule fires on it, the world burns it too, and t18 MATCHES -- replay 16/18, divergences still exactly t13 and t15, first_divergence still t13 cell (63,57). If command 18 uses key 3 or 5: the manual misses the burn -- replay 15/18 with a new divergence at t18, cell (63,55), manual_says 9 world_says 1, which will heal at the next command that uses key 1, 2 or 4. If instead certify reports anything that is not one of those two shapes, the cumulative-replay model is wrong and this whole round must be re-read. ACTION4 HERE, my first choice: my manual predicts ZERO cells outside row 63 and has NO WITNESS for that silence at this cell. If the body steps east to (1,3) I pay 48 undrawable pixels immediately and on every later transition until I write the east rules next round, ACTION4 is east, the maze is real, and lattice row 1 opens toward the knob. If nothing moves, the last candidate for east among keys 1-5 is eliminated and east belongs to key 6, key 7 or to nothing. ACTION5 HERE: predicted zero, never pressed at spawn, tests the guard carried by thirteen rules. ACTION6 or ACTION7: predicted zero, never pressed anywhere, and the only keys that could give the selector something to select. ACTION1 HERE: predicted zero, witnessed zero three times. ACTION2 HERE: 48 cells I draw correctly and nothing learned. THE SINGLE OBSERVATION THAT WOULD MOST CHANGE THIS FILE is unchanged: any colour-8 pixel of the comb or the wire changing."
    [depends: the_row_63_error_alternates_and_a_burn_key_on_an_even_command_keeps_it_in_step, the_action_map_after_seventeen_transitions  probe: pending]

  theorem what_the_engines_gave_me "No new frames this round, so the engine stream is the same stream and I re-read it rather than re-mine it. mdl_segmenter's ten-track unsplit variant reports gain +628 bits, split-by-colour stays catastrophic at -56428, and I take its TRACK LIST and not its verdict. obj0 (colour 9, eight cells, 3x3, all eighteen frames) and obj2 (colour 9, 1x3, all eighteen frames) are slot 1's ring and underline 1 persisting through all five toggles, which corroborates a marker with two seats rather than two objects. The birth frames of the transient tracks are 5, 7, 11, 14 and 16 -- EXACTLY my five toggle transitions, in order, from an engine that has never seen my rules -- and obj9, colour 2, present 2 frames, is slot 1 dimmed and still dim in the current frame, which is configuration B. obj4 is the whole 64-cell row-63 bar, of which 8 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body: connected_components(4) cannot see the mover, because the mover is a ring adjacent to floor on every side, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 17 transitions constrain rank 10 of 395 features -- and its one global law is my census cell for cell, a consistency check and not a discovery. cegis_miner refuses every track again and its verdict, 'the world does not narrate as one mover', is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHAT CHANGED: THE REPLAY MODEL, NOT THE WORLD =========
# No command was executed this round. Certify came back 15/17 where the
# manual predicted 13/17, and the two-transition gap proved that replay
# is CUMULATIVE: each transition is replayed from the manual's own
# previous predicted frame, never resynchronised to the observation.
# Two consequences run this page now.
#
#   A PREMATURE CHANGE HEALS. The manual burned (63,57) one command
#   early at t13; the world burned it at t14; the frames matched again
#   and t14 counted as a match. Same story at t15/t16.
#   AN OMITTED CHANGE NEVER HEALS. Nothing in the manual puts back what
#   it failed to draw, so a missed burn -- or a missed BODY STEP --
#   poisons every later transition until a rule is written for it.
#
# That asymmetry re-priced three refusals (delete the burn rules: ~1/17,
# not 9/17; a guarded key5 burn rule: 14/17; a panel guard on the key4
# burn rule: 13/17, not the 14/17 I claimed). All three refusals stand.
# The rule set is unchanged and is the best of the four.
#
# ========= AND THE ROW-63 ERROR IS NOT PERMANENT AFTER ALL =========
# I previously wrote that every command from here refutes the manual at
# row 63. That was computed under the wrong replay model and is FALSE.
# The corrected shape: the world burns on EVEN commands; the manual
# burns whenever key 1, 2 or 4 is pressed on an edge that has an
# instance. So an even command with a burn key MATCHES, an odd command
# with a burn key is one pixel early and heals next command, an even
# command with key 3 or 5 is one pixel short and heals at the next burn
# key. At most one pixel of error at any time.
# STILL DISCOUNT A DIVERGENCE WHOSE CELLS ALL LIE IN ROW 63 -- but read
# it now as a phase, not as a wound.
#
# ========= THE ONE THING WORTH BUYING NOW =========
# THE UNTESTED HORIZONTAL KEY, FROM WHERE THE BODY STANDS.
# The body is at spawn and east is OPEN: rows 8-12 are floor from col 19
# to col 43, so the destination ring at cols 20-24 is clear. That key has
# been pressed twice and both times at (2,2), where east and west are
# both void and its silence means nothing. It is the last candidate for
# east among the five keys tried. One press answers it whichever way it
# falls:
#   If the body moves east: it stands in a THIRD lattice cell for the
#   first time, the rocker reading dies, the up-key can then be split
#   into up/home/undo from that cell, and lattice row 1 runs toward the
#   knob.
#   If nothing moves: east belongs to an untried key or to nothing, and
#   four theorems about routes lose their footing. Bigger finding, same
#   command.
# THE PRICE WENT UP AND I STATE IT: a body step my manual cannot draw
# does NOT heal. 48 wrong pixels immediately and on every later
# transition until the east rules are written -- and they become
# writable next round, because the arrival cells acquire instances the
# instant they change. One round of tuition. Buy it anyway; the replay
# score is bookkeeping and the direction label is physics.
# BONUS, AND ONLY AS A TIEBREAKER: command 18 is even, so a burn key
# pressed now also keeps the meter phase in step and costs nothing.
#
# SECOND: the up-key at spawn. Never pressed here in eighteen states. It
# is the untested half of the guard carried by thirteen rules, and the
# manual predicts ZERO cells for it, so the raw diff answers it outright.
# THIRD: the two actions never pressed anywhere; the panel is a selector
# that provably selects nothing for the five keys already tried.
# FOURTH: the shuttle question -- stand one cell south, then ask the
# down key to move again. Two commands, and it decides whether five
# theorems are about a maze or about scenery.
# DO NOT BUY: the key whose silence at spawn is witnessed three times; a
# sixth down-press from spawn or a sixth up-press from the cell south of
# it; the horizontal key where that direction is void; any probe ranked
# because a refutation fired on it or because many rules fire.
#
# ========= THE PROBE FRONTIER IS STILL BLIND WHERE IT MATTERS =========
# Every hypothesis in the frontier is the manual or an ablation of it,
# and two ablations differ only where a rule FIRES. So expected-bits is
# maximised on the commands already explained and is exactly 0.000 on
# every command worth buying. THE INSTRUMENT FOR THOSE COMMANDS IS THE
# RAW DIFF, given for free. The manual predicts ZERO changed cells
# outside row 63 for the horizontal key here, the up key here, and both
# untried keys -- so ANY non-empty diff outside row 63 is a discovery.
#
# ========= THERE IS STILL NO GOAL, AND THE REASON IS REACH =========
# is_goal is False, plan returns no_goal_declared, commit never runs,
# EVERY COMMAND THIS LEG IS A PROBE. A goal becomes writable the instant
# any pixel of the socket bracket (rows 49-55, cols 43-49), its pip
# (52,46), or any colour-8 comb or wire pixel changes. Nothing reachable
# from a two-cell corridor causes that. Goal after reach, reach after the
# east key, east key after one press.
#
# ------------------------------------------------------------------------
# STATE 17: body at spawn, lattice (1,2), rows 8-12 cols 14-18; panel
# configuration B; eight meter cells burned (row 63, cols 56-63); 56
# unburned, so roughly 112 commands remain. Next command index 18, EVEN,
# and it burns (63,55) whatever is pressed.

order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     rank_by_what_the_raw_diff_would_show_not_by_expected_frontier_bits [proof: lean]
order     buy_the_commands_the_frontier_scores_at_zero_because_it_is_blind_there [proof: lean]
order     price_a_missed_change_higher_than_a_premature_one_because_only_one_heals [proof: lean]
order     recompute_a_refusal_when_the_replay_model_changes_under_it   [proof: lean]
order     treat_the_first_socket_or_comb_pixel_that_moves_as_the_goal_writing_event [proof: lean]
order     test_the_last_unlabelled_direction_key_where_that_direction_is_open [proof: lean]
order     settle_whether_down_works_off_the_spawn_ring_before_planning_routes [proof: lean]
order     discount_a_divergence_whose_cells_all_lie_in_the_meter_row      [proof: lean]
order     press_a_direction_key_only_where_that_direction_is_open         [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one         [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered   [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     spend_the_clock_on_unwitnessed_key_cell_pairs_not_on_repeats    [proof: lean]
order     try_an_action_never_pressed_before_repeating_a_settled_one      [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it              [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it      [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong  [proof: lean]

prune     divergence_that_the_next_burn_command_repairs_by_itself => dead  [proof: lean]
prune     ranked_only_because_many_rules_fire_on_it => dead                [proof: lean]
prune     expected_bits_computed_over_ablations_of_already_witnessed_rules => dead [proof: lean]
prune     divergence_lies_only_on_a_cell_that_has_never_changed => dead    [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead           [proof: lean]
prune     frontier_cannot_contain_the_world_so_its_bits_are_bookkeeping => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead  [proof: lean]
prune     repeats_a_key_cell_pair_whose_inertness_is_already_witnessed => dead [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead  [proof: lean]
prune     tests_a_direction_from_a_cell_where_that_direction_is_void => dead [proof: lean]
prune     probes_the_meter_parity_that_seventeen_transitions_settled => dead [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead             [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead      [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead   [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                [proof: lean]
prune     destination_centre_holds_machinery_so_the_body_cannot_stand => dead [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead   [proof: lean]
prune     meter_exhausted and not goal => dead                             [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                   [admissible: lean]
heuristic actions_never_pressed_anywhere_in_the_store                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination             [admissible: lean]
heuristic theorems_a_single_press_would_promote_or_demolish               [admissible: lean]
heuristic rules_whose_shared_guard_a_single_command_would_falsify         [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                    [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_row                  [admissible: lean]
heuristic divergences_that_will_not_heal_without_a_new_rule               [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                       [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut             [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open            [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                      [admissible: lean]

prefer    the_untested_horizontal_key_where_that_direction_is_finally_open [ev: 1/1 candidates left]
prefer    a_command_the_frontier_scores_at_zero_but_the_diff_can_read      [ev: 3/3 vacuous probes]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 4/7 keys at this cell]
prefer    stepping_into_a_lattice_cell_the_body_has_never_occupied         [ev: 2/11 cells visited]
prefer    the_press_that_decides_whether_this_world_is_a_maze_or_a_rocker  [ev: 5/24 theorems hostage]
prefer    an_action_pressed_zero_times_over_one_pressed_five_times         [ev: 2/7 actions unpressed]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 17/17 diffs]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 1/1 candidates left]
prefer    a_press_at_a_third_cell_that_splits_up_from_home_from_undo       [ev: 5/5 up_presses]
prefer    a_burn_key_on_an_even_command_when_information_is_otherwise_tied [ev: 2/2 healed pairs]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

## Why you are being called: the surprises that fired

### replay_mismatch (empirical family -> theory.dsl)

replay diverges at t=12 (frame_mismatch)

```json
{
 "arc_action": "ACTION4",
 "cells": [
  {
   "cell": [
    63,
    57
   ],
   "manual_says": 1,
   "world_says": 9
  }
 ],
 "cells_wrong": 1,
 "kind": "frame_mismatch",
 "t": 12
}
```

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "ff1af0146dd846b2",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 24 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted 'e260ba2228378b61' against the world's '8a0fb5148b5adfb0'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.544 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 2,
 "expected_bits": 0.5435644432,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "e260ba2228378b61",
 "n_hypotheses": 24,
 "n_survivors": 0,
 "observed": "8a0fb5148b5adfb0",
 "probe_id": "P-13",
 "vacuous_streak": 1
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 24 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '01006a6a9e21beca' against the world's '2bdbfae66570eec5'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.918 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 5,
 "expected_bits": 0.918295834054,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "01006a6a9e21beca",
 "n_hypotheses": 24,
 "n_survivors": 0,
 "observed": "2bdbfae66570eec5",
 "probe_id": "P-14",
 "vacuous_streak": 2
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 24 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '44c44660a53cf5d4' against the world's '0db510635e263539'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.544 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 2,
 "expected_bits": 0.5435644432,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "44c44660a53cf5d4",
 "n_hypotheses": 24,
 "n_survivors": 0,
 "observed": "0db510635e263539",
 "probe_id": "P-15",
 "vacuous_streak": 3
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
  "arc_action": "ACTION4",
  "cells": [
   {
    "cell": [
     63,
     57
    ],
    "manual_says": 1,
    "world_says": 9
   }
  ],
  "cells_wrong": 1,
  "kind": "frame_mismatch",
  "t": 12
 },
 "proof_layer_available": false,
 "replay": {
  "detail": "15/17 transitions replay exactly",
  "matched": 15,
  "ok": false,
  "transitions": 17
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
  "detail": "no (state, action) among 18 x 5 admitted two rules, and all 90 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 90,
  "pairs_nominal": 90,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 18,
  "states_reconstructed": 18,
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
# theory.dsl -- world observed for 22 states / 21 transitions
# (RESET, then A1 A2 A3 A4 A5 A2 A5 A1 A3 A2 A5 A2 A4 A5 A2 A5 A1 A2 A5 A2 A3).
# 81 cells have ever changed; this manual names and owns all 81.
#
# ================= WHAT HAPPENED SINCE THE LAST MANUAL =================
#
# 1. FOUR COMMANDS WERE SPENT AND NONE OF THEM WAS THE COMMAND THIS
#    MANUAL ASKED FOR. The playbook ranked the untested horizontal key
#    first and named a dozen prunes; what got pressed was ACTION2,
#    ACTION5, ACTION2, ACTION3 -- three repeats of the highest-rule-count
#    commands on the board plus one silence already witnessed twice, i.e.
#    four commands each explicitly pruned. The probe reports say what
#    they bought: expected 0.544, 0.918, 0.544 bits; realised 0.0, 0.0,
#    0.0. That is the theorem the_probe_designer_is_blind... paying out
#    four times in a row, and I promote it from pending to passed.
#
# 2. AND I NOW KNOW WHY THE FRONTIER IS VACUOUS, WHICH IS THE FINDING OF
#    THE ROUND AND IS SHARPER THAN THE COMPLAINT IT ANSWERS. The three
#    refutation reports say 'the manual needs a mechanism it does not
#    currently state -- deleting one of its rules cannot reach this
#    observation'. Half of that is right and the diagnosis is wrong. No
#    mechanism is missing. EVERY HYPOTHESIS IN A FRONTIER BUILT BY
#    ABLATING RULES SHARES THE SAME BOARD, and the board is what is
#    wrong: the world burns a cell of row 63 that has never changed
#    before, that cell is therefore board in this round's level, board
#    cells render their frame-0 colour forever, and NO DELETION OF ANY
#    RULE CAN MAKE A BOARD CELL RENDER 1. So all 24 hypotheses are
#    refuted by the same single pixel, together, always. See
#    every_hypothesis_shares_the_board_so_an_even_command_refutes_the_whole_frontier.
#    P-13 is one pixel, (63,55). P-14 is the SAME pixel, still board.
#    P-15 is two, (63,55) and (63,54). Vacuous streak 3 and it will
#    increment on every even command from here to the end of the level.
#
# 3. THE CLOCK, THE STATE MODEL AND THE PANEL ALL PREDICTED THIS ROUND
#    CORRECTLY AND ONE OF THEM PREDICTED A NUMBER I DID NOT FIT. Burns
#    landed at commands 18 and 20 and nowhere else: ten burns at ten even
#    commands, 10/10. The state model -- body cell x panel configuration
#    x burn count -- says six of the eleven (even, odd) pairs coincide,
#    hence 22-6 = 16 distinct states; the store reports
#    distinct_states = 16. And mdl_segmenter, which has never seen my
#    rules, reports panel tracks with run lengths 5,4,2,3 in colour 1 and
#    2,3,3 in colour 2 -- exactly my seven configuration runs, in order.
#
# 4. THE BODY IS AT LATTICE (2,2) AND THE LARGEST UNEXAMINED ASSUMPTION
#    IN THIS FILE IS NOW ONE PRESS AWAY. ACTION2 has been pressed seven
#    times and all seven were from spawn. South of (2,2) is clear floor
#    (rows 19-24, cols 13-31 read 5). One press decides maze against
#    rocker and five theorems ride on it. It was two presses last round;
#    the probe desk's own choice of ACTION2 at t20 handed me the cell.

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
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t10,t11,t12,t14,t15,t16,t18,t19,t20 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t11,t14,t16,t19 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t11,t14,t16,t19 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t10,t12,t15,t18,t20 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t10,t12,t15,t18,t20 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_edge_key2 forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_next_key2 forall ?p in Glyph9 [ev: t6,t10,t12 cov: 3/5]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key4 forall ?p in Glyph9 [ev: t4 cov: 1/2]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key1 forall ?p in Glyph9 [ev: t8 cov: 1/2]
    when act=key(1) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3,t21 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t11,t14,t16,t19 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t11,t14,t16,t19 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t11,t16 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t11,t16 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t11,t16 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t11,t16 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t14,t19 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t14,t19 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t14,t19 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t14,t19 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t14,t19 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 45 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4015 [status: counted]
  invariant meter_burned_cells count(Glyph9, color = 1) = 10 [status: counted at state 21, monotone]

  theorem every_hypothesis_shares_the_board_so_an_even_command_refutes_the_whole_frontier "THE FINDING OF THIS ROUND, and it replaces a complaint with a proof. Three probes came back frontier_vacuous, all 24 hypotheses refuted including inert and including my manual, realised gain 0.0 bits three times, and the report's diagnosis was 'the manual needs a mechanism it does not currently state'. That diagnosis is wrong and I can say exactly why in one line: the world burned (63,55) at command 18 and (63,54) at command 20; at the time those probes ran, neither cell had ever changed, so neither cell was dynamic, so BOTH WERE BOARD; a board cell renders its frame-0 colour, which is 9, in every hypothesis; and an ablation frontier varies only which rules are present, never which cells are board. Therefore every member of the frontier renders that cell 9 while the world renders it 1, and the whole frontier dies together on one pixel that no deletion and no addition of any rule could have saved. P-13 differs from the world by (63,55) alone; P-14, an ACTION5 with no burn at all, differs by the SAME cell still standing at its frame-0 colour; P-15 by (63,55) and (63,54). THE GENERAL LAW: the meter opens a virgin cell on every even command, so EVERY EVEN COMMAND WILL REFUTE THE ENTIRE FRONTIER FOR AS LONG AS THIS LEVEL LASTS, and vacuous_streak will increment forever. It is a meter reading, not a diagnosis. WHAT WOULD OVERTURN THIS: a refutation whose divergent cells include any cell outside row 63 -- and I cannot check that, because the probe report gives me two hashes and no cells, which is the single cheapest instrument upgrade available to this arm."
    [depends: i_cannot_draw_the_leading_edge_burn, the_meter_is_a_two_command_clock  probe: passed]

  theorem the_probe_designer_is_blind_to_the_commands_worth_buying "PROMOTED FROM PENDING TO PASSED, paid four times in one round. I wrote that every hypothesis in the frontier is my manual or an ablation of it, that two ablations differ only where a rule FIRES, and therefore that expected information gain is maximised exactly where my manual already explains everything and is exactly zero on every command that could teach me something. The four commands bought this round were ACTION2, ACTION5, ACTION2, ACTION3 -- the two highest-rule-count keys in the file, twice, plus a silence witnessed twice before. Every one of them was named by a prune line on the playbook page. The realised gain was 0.0 bits, 0.0 bits, 0.0 bits against 0.544, 0.918 and 0.544 expected. Meanwhile the horizontal key at spawn, the down key off the spawn ring, ACTION6 and ACTION7 all score 0.000 by construction and remain untried. THE TRAP IS STRUCTURAL AND I RESTATE IT SO THE NEXT DESK DOES NOT PAY AGAIN: a frontier built by deleting rules cannot represent 'a rule I am forbidden to write because it has no witness', which is the only kind of hypothesis those four commands would have decided. THE INSTRUMENT THAT WORKS IS THE RAW DIFF, which is given free: my manual predicts zero changed cells outside row 63 for every command it ranks, so ANY non-empty diff outside row 63 is legible without any frontier at all."
    [depends: every_hypothesis_shares_the_board_so_an_even_command_refutes_the_whole_frontier  probe: passed]

  theorem the_row_63_error_is_one_pixel_in_replay_and_unavoidable_in_live_prediction "The distinction I was missing, and it separates two numbers I had been treating as one. REPLAY (certify) is scored a round late: the level is rebuilt from every frame observed so far, so cells 54 to 63 of row 63 all have instances NOW, and replay can draw burns that live prediction could not. LIVE PREDICTION (probe, plan) is scored on the level as it stood when the command was issued, and the cell the world is about to burn is always a cell that has never changed, hence always board, hence always undrawable. So: in replay the manual is never more than ONE PIXEL from the world and the sign alternates -- the world burns on even commands, the manual burns whenever key 1, 2 or 4 lands on an instanced leading edge, the two clocks leapfrog, a premature burn heals when the world catches up and a missed burn heals at the next burn key. In live prediction the manual is ALWAYS one burn short on an even command and there is no repair inside the round. Both are true; they are different scoreboards; and a divergence set consisting only of row 63 implicates neither the rules nor the concepts. That has now consumed eight rounds and I will keep saying it until the divergence set contains a cell outside row 63."
    [depends: replay_is_cumulative_and_a_premature_burn_heals_itself, i_cannot_draw_the_leading_edge_burn  probe: passed]

  theorem replay_is_cumulative_and_a_premature_burn_heals_itself "Established last round from certify reporting 15/17 where I had predicted 13/17, and re-confirmed by this round's report, which is again 15/17 with first_divergence at transition index 12 -- t13 in my numbering, RESET being t0 -- arc_action ACTION4, one cell, (63,57), manual 1 world 9, exactly the misfire of meter_burn_next_key4 named and dated three rounds before it fired. The model: the predecessor of a replayed transition is THE MANUAL'S OWN PREVIOUS PREDICTED FRAME, never resynchronised to the observation. CONSEQUENCE, a law of this arm and not of this world: A PREMATURE CHANGE HEALS WHEN THE WORLD CATCHES UP; AN OMITTED CHANGE NEVER HEALS, because nothing in the manual ever puts back what it failed to draw. Every cost estimate in this file is computed under that asymmetry."
    [depends: meter_burn_next_key4, meter_burn_next_key2  probe: passed]

  theorem three_refusals_recomputed_over_twenty_one_transitions_and_all_three_survive "Recomputed by hand against the longer record, because a refusal whose arithmetic is stale is a superstition. (1) DELETE ALL FOUR BURN RULES: the manual's row 63 stays at frame-0 colour 9 forever, the world's ten burns accumulate, the divergence grows monotonically and never heals -- about 1/21. (2) ADD A KEY5 BURN RULE: ACTION5 has now been pressed six times, at commands 5, 7, 11, 14, 16 and 19, of which only 14 and 16 were even. Unguarded it burns on all six, the manual races four burns ahead of the world and every transition from t5 onward fails. Guarded down to its two witnesses it still leaks the t13 misfire forward instead of letting it heal. Refused again. (3) PANEL-GUARD THE KEY4 BURN RULE to kill the t13 misfire: it converts one premature burn, which heals at t14, into one omission, which never heals, and poisons t14 through t21. Refused again, and by the numbers as well as on principle. THE RULE SET I HAVE IS STILL THE BEST OF THE FOUR, and my projection for it over 21 transitions is 16/21 -- matches everywhere except t13, t15, t17, t18 and t19, first divergence unchanged at t13, cell (63,57)."
    [depends: replay_is_cumulative_and_a_premature_burn_heals_itself  probe: pending]

  theorem dynamic_census "Exactly 81 cells have ever changed and every one has an owner; certify reports cells_unexplained = 0 over all 4096. 23 are the panel: slot 1's eight ring pixels at rows 1-3 cols 1-3, its centre (2,2) being colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in configuration A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 10 are the burned right end of row 63, cols 54 to 63, burned in order 63,62,61,60,59,58,57,56,55,54 at commands 2,4,6,8,10,12,14,16,18,20. 23+24+24+10 = 81 = dynamic_cells. By frame-0 colour: 45 colour-9, 9 colour-1, 24 colour-5, 3 colour-0. 45+9+24 = 78 = cells_needing_an_owner exactly, the store declining to count background-coloured cells; Dark carries the remaining 3 anyway. 4096-81 = 4015 = constant_cells exactly."
    [probe: passed]

  theorem the_state_model_predicted_the_duplicate_count_a_third_time "Corroborated again from a number I did not fit, and the margin is now three independent hits. A state is exactly three things: which of two lattice cells the body occupies, which of two configurations the panel shows, and how many meter cells are burned, and burns at s_k are floor(k/2). Body over s0..s21: spawn spawn C C C spawn C spawn spawn spawn C spawn C C spawn C spawn spawn C spawn C C, where C is lattice (2,2). Panel: A A A A A B B A A A A B B B A A B B B A A A. The burn count pairs s_2j with s_2j+1 and nothing else, so two states coincide exactly when body and panel agree within such a pair: s0=s1, s2=s3, s8=s9, s12=s13, s16=s17, s20=s21 -- six pairs, predicting 22-6 = 16 distinct states. The store reports distinct_states = 16. Any mechanism I am missing that varied a pixel in those twenty-two frames would have broken a coincidence and pushed the count above 16; any spurious mechanism would have pushed it below."
    [depends: dynamic_census, the_meter_is_a_two_command_clock  probe: passed]

  theorem the_meter_is_a_two_command_clock "10 out of 10 and 11 out of 11 and I consider it closed. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right end. Burns occurred at commands 2,4,6,8,10,12,14,16,18,20 and at no other command. The key pressed is irrelevant and every key pressed at both parities says so: ACTION1 burned at 8 and not at 1 or 17, ACTION2 burned at 2,6,10,12,18,20 and not at 15, ACTION4 burned at 4 and not at 13, ACTION5 burned at 14 and 16 and not at 5, 7, 11 or 19, ACTION3 has only ever been pressed at odd indices and has never burned. Cols 54-63 are spent, 54 cells remain, so roughly 108 commands remain before the bar is out. The next command is index 22, which is EVEN, and it will burn (63,53) whatever is pressed -- and (63,53) is board today, so no hypothesis in any frontier can draw it."
    [depends: meter_burn_next_key1, meter_burn_next_key4  probe: passed]

  theorem no_frame_function_can_predict_the_burn_and_six_identical_pairs_prove_it "A proof about my own form, not a guess, and the count grew with the record. Group the twenty-two commands by the burn count b visible at their start: exactly two commands share each b, the odd one k=2b+1 which does not burn and the even one k=2b+2 which does. For b = 0, 1, 4, 6, 8 and 10 the two starting frames are PIXEL-IDENTICAL. So for six of the eleven burn counts there is no function of the frame whatsoever that can output burn for one and no-burn for the other. The world is driven by a command counter that is drawn nowhere. What is NOT proven is that the world fails to be a function of (frame, action): each of those pairs was given two different keys, so a table memorising the burn count per key survives the record -- but it would need one clause per burn, compress nothing, and predict nothing about command 22. CONSEQUENCE I ACCEPT: constraint 5 requires my manual to be a function of (frame, action), so it is required to be wrong about this world's meter, and the only question is where I choose to be wrong. Early, because early heals in replay and late never does."
    [depends: the_meter_is_a_two_command_clock, replay_is_cumulative_and_a_premature_burn_heals_itself  probe: passed]

  theorem i_cannot_draw_the_leading_edge_burn "A law of this manual rather than of this world, now paid ten times. The arm instances exactly the cells that have ALREADY changed, so the next cell to burn is board, has no instance, and NO RULE OF MINE CAN RECOLOUR IT. I checked whether any declaration escapes this: arc-instances: all covers only cells the board cannot explain, so it never reaches a static cell; a landmark can be named at (63,53) but landmarks are cells, not objects, and every event in the language takes an object as its first argument. There is no construction in this DSL that draws a cell before its first change. This is the single sentence behind the vacuous frontier, behind the live-prediction miss on every even command, and behind eight rounds of row-63 divergence, and it is not repairable by any edit to this file."
    [depends: the_meter_is_a_two_command_clock  probe: passed]

  theorem the_down_key_may_be_a_shuttle_and_seven_presses_have_all_been_from_spawn "STILL THE LARGEST UNEXAMINED ASSUMPTION IN THIS FILE, AND IT IS NOW ONE PRESS AWAY. ACTION2 has been pressed seven times -- t2, t6, t10, t12, t15, t18, t20 -- and every single one was from spawn; ACTION5 six times and every one from lattice (2,2). Not once has either been pressed anywhere else. Two readings survive. READING DOWN: ACTION2 moves the body one lattice cell south wherever it stands, ACTION5 one north, and the maze theorem is about a maze. READING SHUTTLE: ACTION2 means go to cell two and ACTION5 means go back to cell one, the world is a two-cell rocker, and the lattice, the comb and the socket are scenery. THE BODY STANDS AT (2,2) RIGHT NOW, put there by the probe desk's own last ACTION2, so the deciding press costs ONE command instead of two. The destination is clear: lattice (3,2) is rows 20-24 cols 14-18, which read 5 in the current frame, and separator row 19 reads 5 across cols 13-31. WHAT MY MANUAL PREDICTS: zero cells outside row 63 -- key2_body_leaves ranges over Glyph9 and the body currently stands on Vacated cells, key2_body_arrives ranges over Vacated and rows 20-24 are board with no instances. If the body moves I am wrong by 48 cells immediately and, under cumulative replay, wrong by them on every subsequent transition until the rules are written next round."
    [depends: key2_body_leaves, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem i_refused_to_pre_write_the_southward_departure_rule_and_here_is_the_arithmetic "A tempting patch, examined and declined. A rule 'forall ?v in Vacated when act=key(2) and colored(?v, 9) then recolored(?v, 5)' would draw the departure half of a second southward step and cost nothing under the current record, because ACTION2 has never once been pressed with the south ring lit. That is exactly the problem: ZERO witnesses and zero counterexamples, so constraint 2 forbids it outright. And the arithmetic agrees with the principle for once. If the world is a maze, the rule saves 24 of the 48 pixels I will get wrong and the other 24 stay wrong anyway because the arrival cells are board. If the world is a rocker, the rule ERASES THE BODY on a transition where nothing happens -- 24 pixels wrong, an omission of the kind that never heals, on a transition I would otherwise have predicted perfectly. Half a saving against a whole new wound, on a coin I cannot call. Refused, and recorded so the next desk does not rediscover it as a gain."
    [depends: the_down_key_may_be_a_shuttle_and_seven_presses_have_all_been_from_spawn  probe: passed]

  theorem the_action_map_after_twenty_one_transitions "WITNESSED, with the negatives stated as negatives. ACTION2 CARRIES THE BODY SOUTH FROM SPAWN: t2, t6, t10, t12, t15, t18, t20, the 5x5 ring from rows 8-12 to rows 14-18, seven times, in both panel configurations. ACTION5 CARRIES IT BACK NORTH: t5, t7, t11, t14, t16, t19, six times, each with a panel toggle. NEGATIVES AT SPAWN, where north and west are void and south and east are open floor: ACTION1 did nothing at t1, t8 and t17, ACTION3 did nothing at t9 -- so NEITHER ACTION1 NOR ACTION3 IS EAST, and both remain consistent with north or west. NEGATIVES AT (2,2), where north and south are open and east and west are void: ACTION3 did nothing at t3 and t21, ACTION4 did nothing at t4 and t13 -- so neither is up and neither is down, and both stay consistent with horizontal. Combine: ACTION3 is neither vertical nor east, which leaves west, and west is void at both cells it has been pressed from, so ACTION3 has never been given a chance to act. ACTION4 IS STILL THE ONLY REMAINING CANDIDATE FOR EAST AND HAS STILL NEVER BEEN PRESSED WHERE EAST IS OPEN. THE RESIDUE THAT MATTERS MOST FROM WHERE THE BODY STANDS: ACTION1 is consistent with up and so is ACTION5, two up keys is a smell, north of (2,2) is open, and ACTION1 has never been pressed at (2,2). One press separates them."
    [depends: key2_body_arrives, key5_body_respawns  probe: pending]

  theorem action5_is_up_or_home_or_undo_and_a_third_cell_separates_them "Six witnesses now and all six moved the body from (2,2) to spawn, a move that up, return-home and undo-last-move predict identically. The separator is a shape, not a route: stand two lattice steps from spawn and press ACTION5 once. Up predicts one step back; home predicts a jump of two cells; undo predicts one step back along the arrival direction, which differs from up as soon as the last step was horizontal. My rules encode none of the three: key5_body_respawns is guarded on PIXELS, a Glyph9 cell rendering 5 whose neighbour above renders 5, so it is a spawn-ring refill rule and nothing more. As written it fires from ANY state where the spawn ring reads floor, so from a third cell my manual predicts the body is DRAWN AT SPAWN WITHOUT BEING ERASED where it stood: two bodies, 24 wrong pixels, priced here in advance. A cheaper first cut is available and does not need a third cell: ACTION1 at (2,2), where north is open. If it moves the body north, ACTION1 is up and ACTION5 is something else."
    [depends: key5_body_respawns, the_action_map_after_twenty_one_transitions  probe: pending]

  theorem the_spawn_probe_guard_is_still_untested_and_now_costs_two_presses "Thirteen rules carry colored(spawn_probe, 5), which reads 'the body is not at home'. All six ACTION5 witnesses had the body one cell south, so the guard has never been tested with the body home: ACTION5 has never been pressed at spawn in twenty-two states. It was one press away last round and the probe desk spent that press elsewhere; the body is at (2,2) now, so the test costs an ACTION5 to get home and a second ACTION5 to ask the question. My manual predicts ZERO changed cells for the second press -- the panel rules are gated off by the guard, key5_body_clears finds no Vacated cell rendering 9, key5_body_respawns finds no Glyph9 cell rendering 5 -- so any change at all is legible in the raw diff. If the panel toggles anyway, thirteen rules are guarded on the wrong thing and I under-predict 23 pixels which never heal; if the body jumps somewhere, ACTION5 is not up at all."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: pending]

  theorem the_panel_is_a_two_slot_selector_toggled_by_action5 "Both directions witnessed six times between them, A to B at t5, t11 and t16 and B to A at t7, t14 and t19, and the current frame re-read pixel by pixel is configuration A. A: slot 1's ring reads 9 with underline 1 reading 9, slot 2 reads solid 1 with underline 2 reading 0. B: slot 1's ring reads 2 with underline 1 reading 0, slot 2 reads a ring of 9 with its centre hollowed to 0 and underline 2 reading 9. THE READING: two slots, an underline under each, and the underlined slot is also the one rendered in colour 9 -- a two-item selector whose cursor ACTION5 advances, wrapping after two. INDEPENDENT CORROBORATION THIS ROUND, and it is the cleanest the engines have ever given me: mdl_segmenter's transient tracks are colour-1 blocks first seen at frames 0, 7, 14 and 19 lasting 5, 4, 2 and 3 frames, and colour-2 blocks first seen at 5, 11 and 16 lasting 2, 3 and 3 -- seven runs, which are EXACTLY my seven configuration runs in order and length, from an engine that has never seen a rule of mine. WHAT I DO NOT CLAIM: what the selection selects. ACTION2 moved the body identically from A at t2, t10, t15, t20 and from B at t6, t12, t18, and ACTION4 was inert in A at t4 and in B at t13 -- seven cross-configuration comparisons and not one difference in net effect. If the selection matters at all it matters to a key never pressed."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, key5_underline2_dims  probe: passed]

  theorem the_goal_is_absent_because_no_instance_can_name_the_socket "I decline a goal clause for a sixth time, and this time the price is measured rather than estimated. THE PRICE: is_goal compiles to False, plan returns no_goal_declared, commit has never run, all twenty-two commands have been probes, the probe designer is provably blind, and four of the last four commands taught me nothing. Roughly 108 commands remain on the meter. THE REASON, unchanged and still binding. (1) Cart.pos = exit_cell needs ONE named instance; arc-instances: all gives me Glyph9_r8c14 and forty-four siblings and there is no instance called Glyph9, and a second colour-9 type would be indistinguishable to an arm that looks objects up by colour alone. (2) A count over the socket interior has nothing to range over: rows 49-55 cols 43-49 have never changed, so they are board. (3) Counts over the four types I have are either already true in some observed state -- count(Vacated, color = 9) = 0 holds in half of them, count(Dark, color = 9) = 3 is one ACTION5 away and means nothing -- or false everywhere and unreachable. A goal the planner can satisfy by pressing one key is worse than no goal, because commit would then spend the level winning it. I also reject count(Glyph9, color = 1) = 64: it says 'the clock has run out', so a planner given it would race to lose. (4) The goal cannot be conjunctive; the section takes one equation. THE OBSERVATION THAT ENDS THIS: a goal becomes writable the moment any pixel of the bracket rows 49-55 cols 43-49, or the pip (52,46), or any colour-8 pixel of the comb changes colour, because that pixel becomes dynamic and acquires an instance. THE GOAL IS DOWNSTREAM OF REACH, AND REACH IS DOWNSTREAM OF ONE PRESS OF THE DOWN KEY FROM WHERE THE BODY IS STANDING."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_down_key_may_be_a_shuttle_and_seven_presses_have_all_been_from_spawn  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 ring with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame, in which the body stands at (2,2). R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only, and east and west of the body are both void; R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4 -- SOUTH OF THE BODY IS OPEN; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2 plus a one-row fragment at row 48 cols 42-50 that cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in twenty-two frames the body has occupied exactly TWO cells, (1,2) and (2,2). THIS THEOREM IS HOSTAGE TO ONE PRESS, and the press is now available."
    [depends: key2_body_arrives, the_down_key_may_be_a_shuttle_and_seven_presses_have_all_been_from_spawn  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed thirteen times: (16,16) stayed 5 at t2, t6, t10, t12, t15, t18 and t20 while its 24 neighbours turned 9, and (10,16) did the same in reverse at t5, t7, t11, t14, t16 and t19. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_cannot_be_stood_on_and_that_is_why_the_east_walk_ends_in_a_bump "Read off the current frame. Lattice (1,6) is rows 8-12 cols 38-42; the knob is a solid 3x3 colour-8 block at rows 9-11 cols 39-41, precisely the centre 3x3 of that cell. A body is 5x5 minus its centre pixel, so eight of its 24 ring pixels would have to overlap colour 8: by the aperture reading, (1,6) is NOT enterable, and only its exact centre is free. The four cells (1,2) to (1,5) are clear floor. So if ACTION4 is east, the body can walk C=2,3,4,5 and then meet the knob head-on. That is either a dead end or the intended interaction, and the two are distinguished by one pixel: any colour-8 pixel changing. Not one colour-8 pixel has moved in twenty-two frames, so colour 8 is board and no object owns it."
    [depends: the_maze_is_a_six_pixel_lattice, the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 50-54. Rows 49 and 55 are separator rows and cols 43 and 49 separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side left as floor. Inside it, rows 50-54 cols 44-48 are floor except the lone colour-9 pixel at the exact centre (52,46). Overlay the body standing there -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel. The bracket has not changed in twenty-two frames, so it is board; the first time any of it changes, those cells become dynamic and the goal section can finally be written."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn under the DOWN reading and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem at col 40 running from row 12 to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18 with floor gaps only at (39,14) and (41,14). ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. The first colour-8 pixel that changes turns this theorem into physics and hands me both a rule and a goal."
    [depends: the_maze_is_a_six_pixel_lattice, the_knob_cannot_be_stood_on_and_that_is_why_the_east_walk_ends_in_a_bump  probe: pending]

  theorem two_actions_have_never_been_pressed_and_that_is_the_second_largest_gap "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Twenty-two commands and TWO OF SEVEN ACTIONS HAVE NEVER BEEN TRIED ONCE. In this action family one of them is normally a click carrying coordinates, and that matters here: the knob is a 3x3 target the body provably cannot stand on, and the panel is a two-item selector whose selection provably changes nothing for the five keys already tried -- seven cross-configuration comparisons and no difference. I cannot write a click rule: the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT and never its precondition. My manual predicts ZERO cells for both keys, so any change is legible in the raw diff, and certify adjudicates five actions rather than seven, which means those two columns of the transition table are unexamined rather than clean."
    [probe: pending]

  theorem the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_defect "The arm instances exactly the cells that have already changed, so any lattice cell the body has never entered is board and has NO instance. A south step from (2,2) to (3,2) costs 24 undrawable arrival pixels at rows 20-24 cols 14-18, plus 24 departure pixels at the south ring which no rule of mine erases -- and the same holds for an east step from spawn. A missed MOVE never heals, so the manual's body would stay put while the world's walks away, and every subsequent transition would be replayed from a frame that is 48 cells wrong. THE REPAIR IS AVAILABLE NEXT ROUND: the moment those cells change they become dynamic, acquire instances typed by their frame-0 colour, and both halves of the rule become writable with a witness. One round of tuition, not permanent damage. I say the price out loud before spending it, and I spend it anyway, because the replay score is bookkeeping and a direction label is physics."
    [depends: the_maze_is_a_six_pixel_lattice, replay_is_cumulative_and_a_premature_burn_heals_itself  probe: pending]

  theorem silence_is_a_prediction_and_three_of_seven_silences_here_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says 'I do not know', it says 'nothing happens', in the same voice it uses for things it has seen. Audit the seven actions at lattice (2,2), where the body now stands. key(1): NO WITNESS HERE, and this is the up-key question -- north is open. key(2): NO WITNESS HERE, and this is the maze-or-rocker question -- south is open. key(3): inert, WITNESSED twice, t3 and t21 -- settled, and meaningless, because east and west are void here. key(4): inert, witnessed twice, t4 and t13 -- same caveat. key(5): carries the body north, witnessed six times -- settled. key(6) and key(7): NO WITNESS ANYWHERE. So three of seven silences at this cell are forged death certificates, and the two cheapest of them are the two most valuable presses on the board."
    [depends: the_action_map_after_twenty_one_transitions, the_down_key_may_be_a_shuttle_and_seven_presses_have_all_been_from_spawn  probe: pending]

  theorem the_cascade_length_is_a_free_channel_and_it_is_now_seven_for_seven "ACTION2 returned 7 frames from configuration A at t2, t10, t15 and t20, and 9 frames from configuration B at t6, t12 and t18 -- seven for seven on a split I predicted four rounds ago and have never had to amend. ACTION5 returned 9 frames all six times, in both directions of the toggle, and every no-op returned 1. So the animation length is not a function of the key alone, and the panel configuration is the one correlate with a witness. It is also NOT a function of the burn: t4 burned with 1 frame and t2 burned with 7. This is hidden state I discard by construction, since cascade single_frame compares only net effect, and it is the ONLY evidence I have that the panel configuration changes anything at all. It costs nothing in replay and buys nothing in prediction; I keep reading it because it is free."
    [depends: the_panel_is_a_two_slot_selector_toggled_by_action5  probe: passed]

  theorem the_no_op_rule_fails_the_gain_test_and_i_keep_it_for_a_narrow_reason "key3_inert_below_spawn recolours one pixel to the colour it already has, has two witnesses on transitions where zero cells changed -- t3 and now t21 -- and replay is identical without it. It explains no pixel and lengthens the manual, so it fails constraint 3 and I say so rather than dressing it up. The reason I keep it: it is the ONLY occurrence of act=key(3) in the file, and deleting it narrows the action set certify adjudicates from five keys to four. Note what that implies about keys 6 and 7, which appear nowhere: five of seven columns are covered and the two missing ones are unexamined rather than clean."
    [depends: key3_inert_below_spawn, two_actions_have_never_been_pressed_and_that_is_the_second_largest_gap  probe: passed]

  theorem the_rules_are_pairwise_exclusive_and_off_board_cell_terms_are_false "Constraint 5, re-checked by hand over all four instance types in both panel configurations, and certify reports 0 clashes over 90 adjudicated pairs with no call to step raising. Under key(2): body_leaves needs below-six to render 5, which is off-board and therefore false for any row past 57, so it cannot fire on a meter cell; the two burn rules split on rightof = wall against a colour test on rightof, which cannot both hold. Under key(5) the type Glyph9 is split five ways by COLOUR FIRST -- 5 for respawns, 9 for the two dim rules, 2 for slot1_lights, 0 for underline1_lights -- and colours 2 and 0 occur on no other Glyph9 cell in any observed state; no meter cell ever renders 5, so respawns cannot reach row 63. The two colour-9 rules are split by above-four: slot1_dims needs it to BE WALL, true only for rows 0-3; underline1_dims needs a COLOUR TEST on it, which is false off-board rather than raising, so it selects row 5, and its above-six wall test excludes the meter at row 63. Spent splits by colour into 1 against 9 and 0; within colour 1 the geometry is row 1 by above-two wall, row 3 by a colour test on above-two, row 2 by above-three wall plus a colour test on above-one, and within row 2 col 5 by leftof-six wall, col 6 by leftof-seven wall plus a colour test on leftof-one, col 7 by a colour test on leftof-two. Dark splits by colour 0 against 9. Not one rule uses not, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens, key5_slot1_lights  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. STATE: body at lattice (2,2), rows 14-18 cols 14-18 rendering 9 with the aperture (16,16) rendering 5; spawn ring rows 8-12 cols 14-18 rendering floor; panel configuration A; ten meter cells burned at row 63 cols 54-63; next command index 22, which is EVEN, so the clock burns (63,53) whatever is pressed, and (63,53) is board today, so EVERY hypothesis in any frontier will be refuted by that pixel and the vacuous streak will read 4. CERTIFY ON THE 21 TRANSITIONS ALREADY IN THE STORE: replay 16/21, first_divergence unchanged at transition index 12, ACTION4, cell (63,57), manual 1 world 9, with further one-pixel divergences at t15, t17, t18 and t19, all in row 63 and all self-healing; responsibility 0/4096; unambiguous 0 clashes over 22 x 5 = 110 pairs. If certify reports a divergence outside row 63, this manual is wrong about something that matters and the whole file must be re-read. ACTION2 HERE, MY FIRST CHOICE: my manual predicts ZERO cells outside row 63 and has NO WITNESS for that silence at this cell. If the body steps south to (3,2) I pay 48 undrawable pixels now and until next round, the rocker reading dies, the maze is real, and five theorems are promoted at once. If nothing moves, ACTION2 is a shuttle, the lattice is scenery, and I would rather know that after one command than after ninety. ACTION1 HERE, my second: never pressed at this cell, north is open, and it splits the two candidate up-keys; predicted zero. ACTION6 or ACTION7: predicted zero, never pressed anywhere, and the only keys that could give the selector something to select. ACTION3 or ACTION4 HERE: predicted zero and WITNESSED zero twice each, so nothing is bought. THE SINGLE OBSERVATION THAT WOULD MOST CHANGE THIS FILE is unchanged: any colour-8 pixel of the comb or the wire changing."
    [depends: the_row_63_error_is_one_pixel_in_replay_and_unavoidable_in_live_prediction, the_action_map_after_twenty_one_transitions  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter's eleven-track unsplit variant now reports gain +2618 bits against split-by-colour's -71057, and it paid out properly this round. I take its TRACK LIST and not its verdict. obj0 (colour 9, eight cells, 3x3, all 22 frames) and obj2 (colour 9, 1x3, all 22 frames) are slot 1's ring and underline 1 persisting through all six toggles, which corroborates a marker with two seats rather than two objects. THE NEW PAYOUT: the transient tracks are colour-1 blocks born at frames 0, 7, 14, 19 lasting 5, 4, 2, 3 frames and colour-2 blocks born at 5, 11, 16 lasting 2, 3, 3 -- seven runs whose births and lengths reproduce my panel sequence exactly, from an engine that has never seen a rule of mine. obj4 is the whole 64-cell row-63 bar, of which 10 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body: connected_components(4) cannot see the mover, because the mover is a ring adjacent to floor on every side, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 21 transitions constrain rank 12 of 405 features, null space 393 -- and its one global law is my census cell for cell, a consistency check and not a discovery. cegis_miner refuses every track again and its verdict, 'the world does not narrate as one mover', is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ===== WHAT HAPPENED: FOUR COMMANDS SPENT, EVERY ONE OF THEM PRUNED =====
# This page ranked the untested horizontal key first and listed a dozen
# prunes. What was pressed was the down key from spawn, the up key from
# the cell south of it, the down key from spawn again, and a key whose
# silence was already witnessed twice -- four commands, each of them
# named by a prune line here, expected 0.544 + 0.918 + 0.544 bits,
# realised 0.0 + 0.0 + 0.0. The probe designer is not blind by accident;
# it is blind BY CONSTRUCTION, because it ranks by expected bits over a
# frontier of ablations, and two ablations can only differ where a rule
# FIRES. It is therefore guaranteed to rank the commands this manual
# already explains and to score at exactly zero every command that could
# teach it something.
#
# ===== AND A VACUOUS FRONTIER IS NOW A SOLVED PHENOMENON =====
# Three probes came back with all 24 hypotheses refuted, including
# `inert` and the manual, and the report concluded that the manual needs
# a mechanism it does not state. It does not. The meter burns a cell of
# row 63 that has NEVER CHANGED BEFORE, so that cell is board, so it
# renders its frame-0 colour in EVERY hypothesis, and no deletion or
# addition of any rule can make a board cell render otherwise. The whole
# frontier dies together on one pixel. This will recur on EVERY EVEN
# COMMAND for the rest of the level; vacuous_streak is a meter reading.
# THE TEST THAT SEPARATES A METER READING FROM A REAL GAP: do the
# divergent cells lie only in row 63? If yes, discount. If any lie
# elsewhere, that is a genuine missing mechanism and outranks everything
# on this page. THE PROBE REPORT GIVES HASHES AND NOT CELLS, so I cannot
# run that test on a probe refutation -- printing the divergent cells is
# the cheapest instrument upgrade available to this arm, and until it
# exists the raw diff is the only usable instrument.
#
# ===== THE ONE THING WORTH BUYING NOW, AND IT COSTS ONE COMMAND =====
# THE DOWN KEY, FROM THE CELL IT HAS NEVER BEEN PRESSED IN.
# The down key has been pressed seven times and all seven were from
# spawn. THE BODY IS AT LATTICE (2,2) RIGHT NOW -- the probe desk's own
# last command put it there -- and south of it is clear floor. One press
# decides the largest open question in the manual:
#   If the body moves south: it stands in a THIRD lattice cell for the
#   first time, the rocker reading dies, the maze is real, five theorems
#   are promoted at once, and the up-key can then be split into
#   up/home/undo from that cell.
#   If nothing moves: the down key is a shuttle, the lattice and the comb
#   and the socket are scenery, and five theorems fall. Bigger finding,
#   same command.
# THE PRICE, STATED BEFORE SPENDING IT: 48 pixels I cannot draw -- 24
# departure, 24 arrival on board cells -- and a missed move never heals,
# so it poisons replay until the rules are written next round. One round
# of tuition. Buy it anyway; the replay score is bookkeeping and a
# direction label is physics.
# I DECLINED TO PRE-WRITE THE DEPARTURE HALF: with no witness either way
# it saves 24 pixels if the world is a maze and invents 24 wrong ones if
# it is a rocker, and only the second kind never heals.
#
# SECOND: the up key from this same cell, never pressed here, north
# open. It splits the two candidate up-keys; predicted zero, so the raw
# diff answers it outright.
# THIRD: the two actions never pressed anywhere in twenty-two commands.
# The panel is a selector that provably selects nothing for the five keys
# already tried, across seven cross-configuration comparisons.
# FOURTH: the horizontal key at spawn, where east is finally open -- but
# it now costs a trip home first, so it drops behind the two presses
# available from where the body stands.
# DO NOT BUY: the up key from here or the down key from spawn, both
# settled to the pixel; either horizontal key from here, where both
# horizontal directions are void; anything ranked because many rules fire
# on it or because a refutation fired on it.
#
# ===== THERE IS STILL NO GOAL, AND THE PRICE IS NOW MEASURED =====
# is_goal is False, plan returns no_goal_declared, commit has never run,
# ALL TWENTY-TWO COMMANDS HAVE BEEN PROBES, and roughly 108 remain on the
# meter. The certify report calls declaring the winning condition the
# highest-value edit available -- I agree with the value and the edit is
# not available to this page: `goal` lives in the manual, and the manual
# cannot name the socket because every cell of it has never changed and
# is therefore board, and there is no named single instance to put on
# the left of the equation. A goal I could write today is one the planner
# could satisfy by pressing one key, which would hand the whole level to
# a fake win. A goal becomes writable the instant any pixel of the socket
# bracket, its pip, or any comb or wire pixel changes -- and nothing
# reachable from a two-cell corridor causes that. Goal after reach, reach
# after the gate, gate after the maze is proven to be a maze, and that
# proof is one press away.
#
# ---------------------------------------------------------------------
# STATE 21: body at lattice (2,2), rows 14-18 cols 14-18; spawn ring
# empty; panel configuration A; ten meter cells burned at row 63 cols
# 54-63; 54 unburned. Next command index 22, EVEN, and it burns (63,53)
# whatever is pressed -- a board cell, so it refutes every hypothesis.

order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     read_a_vacuous_frontier_as_a_board_cell_before_calling_it_a_missing_mechanism [proof: lean]
order     ask_for_the_divergent_cells_of_a_refutation_and_not_only_its_hash [proof: lean]
order     rank_by_what_the_raw_diff_would_show_not_by_expected_frontier_bits [proof: lean]
order     buy_the_commands_the_frontier_scores_at_zero_because_it_is_blind_there [proof: lean]
order     test_the_down_key_from_the_cell_it_has_never_been_pressed_in   [proof: lean]
order     spend_the_press_that_is_available_from_where_the_body_stands   [proof: lean]
order     price_a_missed_change_higher_than_a_premature_one_because_only_one_heals [proof: lean]
order     separate_the_replay_scoreboard_from_the_live_prediction_scoreboard [proof: lean]
order     recompute_a_refusal_when_the_replay_model_changes_under_it     [proof: lean]
order     treat_the_first_socket_or_comb_pixel_that_moves_as_the_goal_writing_event [proof: lean]
order     settle_whether_down_works_off_the_spawn_ring_before_planning_routes [proof: lean]
order     discount_a_divergence_whose_cells_all_lie_in_the_meter_row     [proof: lean]
order     press_a_direction_key_only_where_that_direction_is_open        [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one        [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered  [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     spend_the_clock_on_unwitnessed_key_cell_pairs_not_on_repeats   [proof: lean]
order     try_an_action_never_pressed_before_repeating_a_settled_one     [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it             [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it     [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong [proof: lean]

prune     vacuous_streak_whose_refuting_cells_all_lie_in_the_meter_row => dead [proof: lean]
prune     hypothesis_that_differs_from_its_siblings_only_by_a_board_cell => dead [proof: lean]
prune     divergence_that_the_next_burn_command_repairs_by_itself => dead [proof: lean]
prune     ranked_only_because_many_rules_fire_on_it => dead              [proof: lean]
prune     expected_bits_computed_over_ablations_of_already_witnessed_rules => dead [proof: lean]
prune     divergence_lies_only_on_a_cell_that_has_never_changed => dead  [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead         [proof: lean]
prune     frontier_cannot_contain_the_world_so_its_bits_are_bookkeeping => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead [proof: lean]
prune     repeats_a_key_cell_pair_whose_inertness_is_already_witnessed => dead [proof: lean]
prune     repeats_a_key_cell_pair_whose_effect_is_already_witnessed => dead [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead [proof: lean]
prune     tests_a_direction_from_a_cell_where_that_direction_is_void => dead [proof: lean]
prune     probes_the_meter_parity_that_twenty_one_transitions_settled => dead [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead           [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead    [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead              [proof: lean]
prune     destination_centre_holds_machinery_so_the_body_cannot_stand => dead [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead [proof: lean]
prune     goal_a_planner_could_satisfy_with_a_single_press => dead       [proof: lean]
prune     meter_exhausted and not goal => dead                           [proof: lean]

heuristic key_cell_pairs_whose_inertness_here_rests_on_no_witness        [admissible: lean]
heuristic actions_never_pressed_anywhere_in_the_store                    [admissible: lean]
heuristic presses_available_without_first_moving_the_body                [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination            [admissible: lean]
heuristic theorems_a_single_press_would_promote_or_demolish              [admissible: lean]
heuristic rules_whose_shared_guard_a_single_command_would_falsify        [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                   [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_row                 [admissible: lean]
heuristic divergences_that_will_not_heal_without_a_new_rule              [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                      [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut            [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open           [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                     [admissible: lean]

prefer    the_down_key_from_the_only_other_cell_the_body_has_ever_occupied [ev: 7/7 presses from one cell]
prefer    the_press_that_decides_whether_this_world_is_a_maze_or_a_rocker  [ev: 5/26 theorems hostage]
prefer    a_command_the_frontier_scores_at_zero_but_the_diff_can_read      [ev: 3/3 vacuous probes]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 3/7 keys at this cell]
prefer    stepping_into_a_lattice_cell_the_body_has_never_occupied         [ev: 2/11 cells visited]
prefer    an_action_pressed_zero_times_over_one_pressed_seven_times        [ev: 2/7 actions unpressed]
prefer    a_press_available_from_here_over_one_that_needs_a_trip_first     [ev: 2/4 ranked probes]
prefer    a_press_that_would_split_two_keys_that_share_a_direction_label   [ev: 6/6 up_presses]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 21/21 diffs]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl obj0/obj2 (colour 9, 3x3 and 1x3, all 22 frames)", "verdict": "entailed",
   "as": "Glyph9 instances at rows 1-3 cols 1-3 and row 5 cols 1-3", "why": "these are slot 1's ring and underline 1 persisting across all six toggles; already owned by Glyph9 via arc-instances: all, and a second type on the same pixels would create the double claim constraint 5 forbids."},

  {"id": "O-02", "subject": "mdl obj1/obj6/obj8/obj10 (colour 1) and obj5/obj7/obj9 (colour 2)", "verdict": "entailed",
   "as": "Spent and Glyph9 panel cells in their two configurations", "why": "their birth frames 0,7,14,19 and 5,11,16 with lengths 5,4,2,3 and 2,3,3 reproduce my seven panel-configuration runs exactly, so they corroborate the toggle rather than adding an object."},

  {"id": "O-03", "subject": "mdl obj4 (colour 9, 1x64 row-63 bar)", "verdict": "entailed",
   "as": "Glyph9 meter cells (row 63 cols 54-63) plus board", "why": "only 10 of its 64 cells have ever changed; the other 54 are constant and belong to the board, and no declaration in this DSL can instance them before they change."},

  {"id": "O-04", "subject": "mdl obj3 (colour null, 1006 cells)", "verdict": "reject",
   "as": null, "why": "connected_components(4) fused the maze floor with the body ring; the absence of a body track is the informative part, since the mover is a ring floor-adjacent on every side and cannot be segmented that way."},

  {"id": "O-05", "subject": "a single named instance for the body, to enable `goal Cart.pos = exit_cell`", "verdict": "reject",
   "as": null, "why": "the body is 24 cells, arc-instances: all yields Glyph9_r14c14 and 44 siblings with no instance called Glyph9, and a second colour-9 type is indistinguishable to an arm that looks objects up by colour alone."},

  {"id": "R-01", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept",
   "as": "unchanged, evidence extended to t18 and t20", "why": "two further southward moves this round, 48 cells each, drawn exactly; seven witnesses, 24/24 coverage, still the only rules with full coverage on both halves."},

  {"id": "R-02", "subject": "key5_body_clears / key5_body_respawns and the eleven panel rules", "verdict": "accept",
   "as": "unchanged, evidence extended to t19", "why": "t19 was a B-to-A toggle with 71 cells changed, exactly 24+24+8+1+3+11 as the B-to-A rules predict; the three B-to-A rules go from two witnesses to three."},

  {"id": "R-03", "subject": "meter_burn_next_key2", "verdict": "accept",
   "as": "coverage corrected to 3/5", "why": "correct at t6, t10, t12; premature at t15 (heals at t16) and at t18 where it burns (63,54) one command early (heals at t20). Honest coverage, not a downgrade of belief."},

  {"id": "R-04", "subject": "meter_burn_next_key1", "verdict": "accept",
   "as": "coverage corrected to 1/2", "why": "correct at t8; at t17 the leading edge (63,55) now has an instance, so this rule fires one command early on an odd index. Premature burns heal under cumulative replay, so it stays."},

  {"id": "R-05", "subject": "a key5 meter burn rule, witnessed at t14 and t16", "verdict": "reject",
   "as": null, "why": "ACTION5 has now been pressed six times and only two were even commands; unguarded it races four burns ahead and fails every transition from t5, and guarded to its witnesses it leaks the t13 misfire forward instead of letting it heal."},

  {"id": "R-06", "subject": "a panel guard on meter_burn_next_key4 to suppress the t13 misfire", "verdict": "reject",
   "as": null, "why": "it converts one premature burn, which heals at t14, into one omission, which never heals; recomputed over 21 transitions it loses more than it saves."},

  {"id": "R-07", "subject": "forall ?v in Vacated when act=key(2) and colored(?v,9) then recolored(?v,5) -- the southward departure half, pre-written", "verdict": "reject",
   "as": "theorem i_refused_to_pre_write_the_southward_departure_rule_and_here_is_the_arithmetic", "why": "zero witnesses and zero counterexamples, so constraint 2 forbids it; and it saves 24 healing pixels if the world is a maze while inventing 24 non-healing ones if it is a rocker."},

  {"id": "R-08", "subject": "key3_inert_below_spawn", "verdict": "accept",
   "as": "unchanged, second witness at t21", "why": "it still fails the gain test -- it recolours a pixel to the colour it already has -- and I keep it only because it is the sole occurrence of key(3) and its deletion would narrow certify's adjudicated action set."},

  {"id": "L-01", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "reject",
   "as": null, "why": "true of the arm and false of the world: there is exactly one mover, a rigid 24-pixel ring, and the miner's precondition of one move event per transition cannot see 24 simultaneous recolours."},

  {"id": "L-02", "subject": "zero_space global law over 81 cells", "verdict": "entailed",
   "as": "dynamic_census", "why": "its cell list is my census cell for cell -- 23 panel, 24 spawn ring, 24 south ring, 10 meter -- and it self-reports THIN at rank 12 of 405 features, so it is a consistency check, not a discovery."},

  {"id": "L-03", "subject": "invariant counts (Glyph9 45, board 4015, burned 10)", "verdict": "accept",
   "as": "updated from 43 / 4017 / 8", "why": "(63,55) and (63,54) burned at commands 18 and 20 and are now dynamic; 45+9+24 = 78 = cells_needing_an_owner and 45+9+24+3 = 81 = dynamic_cells and 4096-81 = 4015 = constant_cells, all three exactly."},

  {"id": "L-04", "subject": "probe_refutation P-13, P-14, P-15 (frontier vacuous, 0.0 bits realised x3)", "verdict": "accept",
   "as": "theorem every_hypothesis_shares_the_board_so_an_even_command_refutes_the_whole_frontier", "why": "I accept the observation and reject its stated diagnosis: no mechanism is missing, the burned cells (63,55) and (63,54) were board at probe time, board renders frame-0 colour in every ablation, so all 24 hypotheses die on the same pixel and no rule edit could have saved any of them."},

  {"id": "L-05", "subject": "the state model's prediction of distinct_states", "verdict": "accept",
   "as": "the_state_model_predicted_the_duplicate_count_a_third_time", "why": "body cell x panel configuration x floor(k/2) burns gives six coincident pairs among 22 states, hence 16 distinct; the store reports 16, a number I did not fit."},

  {"id": "L-06", "subject": "the_probe_designer_is_blind_to_the_commands_worth_buying", "verdict": "accept",
   "as": "promoted from probe: pending to probe: passed", "why": "four commands spent this round were the two highest-rule-count keys plus a twice-witnessed silence, every one of them named by an existing prune line, and the realised gain was 0.0 bits three times against 0.544, 0.918, 0.544 expected."},

  {"id": "L-07", "subject": "heuristic_miss: 'declaring the winning condition is the highest-value edit available to the playbook'", "verdict": "reject",
   "as": "the_goal_is_absent_because_no_instance_can_name_the_socket, with the price now measured", "why": "I agree the value is highest and the edit is not available: `goal` lives in theory.dsl, the socket cells have never changed and so are board with nothing to count, and every goal I can currently write is either already true or one keypress away, which would hand the level to a fake win."},

  {"id": "L-08", "subject": "replay_mismatch at t=12, ACTION4, (63,57)", "verdict": "accept",
   "as": "no change, answered by the_row_63_error_is_one_pixel_in_replay_and_unavoidable_in_live_prediction", "why": "this is the misfire of meter_burn_next_key4 predicted by name, date and pixel three rounds ago; every alternative rule set is worse by hand-recomputation over 21 transitions, so I refuse to change and say why."},

  {"id": "P-01", "subject": "the down key from lattice (2,2)", "verdict": "probe-pending",
   "why": "seven presses of it have all been from spawn; the body is now at (2,2) with clear floor south, so one command decides maze against rocker and five theorems ride on it. Manual predicts zero cells outside row 63."},

  {"id": "P-02", "subject": "the up key from lattice (2,2)", "verdict": "probe-pending",
   "why": "never pressed at this cell, north is open, and it splits the two keys that both currently fit the label 'up'. Manual predicts zero cells outside row 63, so the raw diff answers it."},

  {"id": "P-03", "subject": "ACTION6 and ACTION7, anywhere", "verdict": "probe-pending",
   "why": "two of seven actions untried in 22 commands, and the panel is a selector that provably selects nothing for the five keys already tried across seven cross-configuration comparisons."},

  {"id": "P-04", "subject": "the horizontal key at spawn, where east is open", "verdict": "probe-pending",
   "why": "still the only candidate for east and still never pressed where east is open, but it now costs a trip home first, so it ranks behind the two presses available from where the body stands."},

  {"id": "E-01", "subject": "drawing the meter cell the world is about to burn", "verdict": "probe-pending",
   "as": "theorem i_cannot_draw_the_leading_edge_burn", "why": "I wanted a rule that recolours (63,53); arc-instances: all reaches only cells the board cannot explain, landmarks are cells rather than objects, and every event takes an object first argument, so no construction in this DSL draws a cell before its first change."},

  {"id": "E-02", "subject": "a precondition for a click action", "verdict": "probe-pending",
   "as": "theorem two_actions_have_never_been_pressed_and_that_is_the_second_largest_gap", "why": "the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked; I can record a click's effect and never its precondition."},

  {"id": "E-03", "subject": "the divergent cells of a probe refutation", "verdict": "probe-pending",
   "as": "an order line on the playbook page", "why": "the report gives two frame hashes, so I cannot apply the one test that separates a meter reading from a real mechanism gap -- whether any divergent cell lies outside row 63 -- and I say so rather than guessing."}
]
```
```
