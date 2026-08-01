# call-005-theorize-round1

model: `claude-opus-5` · 807418 ms · $2.863988 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 111301, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 111301, "cache_read_input_tokens": 47236, "inference_geo": "not_available", "input_tokens": 4, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 64065, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 64065, "cache_read_input_tokens": 47236, "input_tokens": 2, "output_tokens": 3701, "type": "message"}], "output_tokens": 67701, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 76,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4017,
 "distinct_states": 16,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 79,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 18,
 "steps": 18
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
9999999999999999999999999999999999999999999999999999999911111111
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

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 17,
  "n_states": 18,
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
   "ValueError: object absent at frame 0; unsupported on this fixture"
  ],
  "tracks": [
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj0",
    "transitions": 17
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
    "transitions": 17
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
  "candidates": 12,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 7,
   "move": 14,
   "recolor": 22,
   "vanish": 7
  },
  "n_frames": 18,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 18,
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
    "frames_present": 18,
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
    "frames_present": 18,
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
    "frames_present": 18,
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
    "frames_present": 1,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj11"
   }
  ],
  "variants": [
   {
    "baseline_bits": 13592,
    "compression_ratio": 0.746763,
    "events": 50,
    "gain_bits": 3442,
    "ms": 71,
    "script_bits": 10150,
    "split_by_color": false,
    "tracks": 12
   },
   {
    "baseline_bits": 13592,
    "compression_ratio": 6.499853,
    "events": 115,
    "gain_bits": -74754,
    "ms": 73,
    "script_bits": 88346,
    "split_by_color": true,
    "tracks": 47
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 79,
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
  "cells_needing_an_owner": 76,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4017,
  "distinct_states": 16,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 79,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 18,
  "steps": 18
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 79,
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
  "cells_dynamic": 79,
  "cells_used": 79,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 9,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.022785,
   "difference_rank": 9,
   "features": 395,
   "space_dimension": 386,
   "transitions": 17,
   "verdict": "THIN: 17 transitions constrain rank 9 of 395 features, so the null space has dimension 386 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 395,
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

```

The full proposal stream is 1544 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 14 states / 13 transitions
#   RESET, A1 A2 A3 A4 A5 A2 A5 A2 A5 A2 A5 A2 A5.
# 77 cells have ever changed; this manual names and owns all 77.
#
# WHY THIS ROUND EXISTS: THE COMPILER REFUSED THE MANUAL.
#
#   No new transition arrived. The four probe_refutations (P-05..P-08) are the
#   four this manual already diagnosed and priced, on the same two actions, at
#   the same two information gains to six decimal places. Nothing empirical is
#   new. ONE THING IS NEW AND IT IS FATAL:
#
#     UnsupportedClause: count(Gate) -- this level declares no instance of
#     that type, so the count is 0 on every state and the clause decides
#     nothing.
#
#   Last round I wrote a goal over a type with ZERO instances ON PURPOSE and
#   argued in this very file that an unreachable goal is honest rather than
#   vacuous. It is neither. It does not compile, and a manual that does not
#   compile has no executable form -- so that one line cost the whole arm a
#   round of every downstream tier. Gate and the goal section are DELETED.
#   The law it taught is recorded as
#   the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught, and my
#   explicit refusal to replace it with an unsound goal is recorded as
#   no_goal_section_this_round_and_the_exact_reason.
#
#   THE STANDING DEFECT IS UNCHANGED AND STILL THE SHAPE OF EVERYTHING:
#     THE NEXT METER BURN ALWAYS LANDS ON A CELL THAT HAS NEVER CHANGED.
#     A never-changed cell is board. Board cells hold no instance. No event
#     in this language can recolour a cell with no instance. So the manual
#     CANNOT predict the next burn -- not now, not ever, at any length.
#   And the goal refusal is that same wall met from the other side: there I
#   could not PREDICT a cell that had never changed; here I cannot make a
#   GOAL out of one.
#
#   NO NEW RULE IS INSTALLED THIS ROUND. There is no new transition to
#   witness one. The only edit is the one the compiler demanded.
#   EXPECTED REPLAY: 13/13.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t13 compress: 41]
  Vacated [segment: dynamic_colour_5 ev: t2-t13 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13 compress: 3]

events:
  event recolored(o, c)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12 cov: 120/120]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12 cov: 120/120]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13 cov: 120/120]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13 cov: 120/120]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12 cov: 4/4]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13 cov: 24/24]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11 cov: 16/16]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11 cov: 16/16]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 41 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: inferred-from-replay]
  invariant board_cells count(board) = 4019 [status: counted]
  invariant meter_cells_burned_right_now count(Glyph9, color = 1) = 6 [status: state-dependent-not-an-invariant]

  theorem the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught "THE FINDING OF THIS ROUND. The compiler refused the entire manual over one clause, goal count(Gate, color = 5) = 23, saying: this level declares no instance of that type, so the count is 0 on every state and the clause decides nothing. I accept the refusal without argument and I record what it teaches, because it is a fact about this arm that no amount of frame-watching would have produced. A COUNT OVER A TYPE WITH ZERO INSTANCES IS NOT A FALSE PREDICATE. IT IS A REFUSED CLAUSE. My design was exactly the inverse of that: I chose colour 8 BECAUSE its instance set was empty today and could only become non-empty by the very event I wanted to name, and I wrote here in as many words that an unreachable goal is honest rather than vacuous. It is neither. It is uncompilable, and an uncompilable manual has no executable form, so plan, certify and probe all got nothing for a round. Gate is deleted from word_table, gate_instances is deleted from laws, and the goal section is gone. THE GENERAL FORM, which binds every desk that follows me here: THE GOAL LANGUAGE CAN ONLY SPEAK ABOUT CELLS THAT HAVE ALREADY CHANGED, because only those cells carry instances. That is the same wall as the burn frontier approached from the other side -- there I could not PREDICT a cell that had never changed, here I cannot make a GOAL out of one. One consequence I did not expect and now state plainly: declaring a type as insurance against a future colour change is not free, because the moment any clause counts it the manual stops compiling."
    [depends: i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem no_goal_section_this_round_and_the_exact_reason "heuristic_miss has fired three times and I am answering it with an explicit refusal rather than a fourth attempt, because the third attempt broke the compiler. Enumerate what the grammar lets a goal say: a count over a declared type, or an instance's pos equal to a landmark. Enumerate the types that actually carry instances: Glyph9, 41 cells, being the slot-1 ring, underline 1, the spawn ring and six burned meter cells; Vacated, 24 cells, the ring one lattice cell south; Spent, 9 cells, slot 2; Dark, 3 cells, underline 2. EVERY INSTANCE I HAVE IS IN THE PANEL, ON THE SPAWN RING, OR ON THE METER, and none of them is within forty rows of the socket. I tested the nearest plausible candidate honestly before rejecting it: count(Glyph9, color = 9) = 0 is false in all fourteen observed states, which makes it LOOK like a goal, and it becomes TRUE the moment the body steps one cell south while the panel sits in configuration B -- one press of ACTION2 from here, and not a win. A goal that halts a planner one move from spawn is strictly worse than no goal, because no goal makes plan return unsat while an unsound goal makes it return sat on garbage and commit act on it. The pos form fails for a different reason: this world never MOVES anything. Every rule in this manual is a recolour, no instance's pos has changed in fourteen states, and so X.pos = landmark is a constant for every X I can declare. THEREFORE THERE IS NO SOUND GOAL AVAILABLE TO ME AND I DECLINE TO INVENT ONE. What unlocks the goal line is an OBSERVATION, not an edit: the first pixel of the comb or of the socket bracket that changes colour turns those cells dynamic, seats instances on them, and makes a goal both writable and sound in the same instant. That is what the playbook is ranking for, and it is the honest reading of heuristic_miss -- the highest-value edit is not available until a command buys it."
    [depends: the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught, the_goal_i_still_cannot_write_is_the_real_one  probe: passed]

  theorem the_goal_i_still_cannot_write_is_the_real_one "The win is the body standing in lattice (8,7), rows 50-54 cols 44-48, its 24 ring pixels rendering 9 and its aperture showing the pip at (52,46). The exact reason it cannot be written is re-verified against the current frame. Those 24 cells are constant colour 5, so they are board and hold no instance; and colour 5 is already claimed by Vacated while the arm looks types up by colour alone, so a second colour-5 type would be indistinguishable from Vacated and would claim cells twice, which is the constraint-5 error. The goal I could write over Vacated once the socket goes dynamic -- count(Vacated, color = 9) = 24 -- is already true whenever the body stands in lattice (2,2), so it names two states and one of them is not a win. So the manual carries the true winning condition in prose, here and in the playbook, and carries NO goal line at all. That is a stated gap, not an evasion: the same observation that makes the socket dynamic is the observation that lets the next desk write the goal, and opening the comb is on the critical path to it under every reading I hold."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem the_burn_frontier_is_a_permanent_one_pixel_blind_spot "Row 63 is a 64-cell colour-9 bar that burns one cell at a time from the right. Six cells are burned: (63,63) at index 2, (63,62) at 4, (63,61) at 6, (63,60) at 8, (63,59) at 10, (63,58) at 12. The seventh burn will land on (63,57). (63,57) has never changed in fourteen frames, so it is board, so it holds no instance, so NO EVENT IN THIS LANGUAGE CAN TOUCH IT -- recolored takes an object as its first argument and there is no object there. Therefore my manual predicts, and must predict, that the seventh press of ACTION2 burns nothing. The world will burn (63,57) and the manual will be wrong by exactly one pixel. Then (63,57) becomes dynamic, the arm seats a Glyph9 on it, replay draws the burn retroactively, certify reports a perfect replay, and the eighth press repeats the cycle on (63,56). THAT IS WHY certify SAYS THE REPLAY IS EXACT WHILE THE PROBE DESK SAYS THE MANUAL WAS WRONG ON ACTION 2: they are asking about different times. Replay looks backwards through a census that already contains the burned cell; prediction looks forwards through one that cannot. I diagnosed the earlier pair of action-2 refutations as a missing rule, installed the rule, and was refuted twice more with nothing left to install -- so the missing-rule reading is REFUTED and this one replaces it. All six meter instances currently render 1, so meter_burn_key2_next has no grounding left and cannot fire again in this census. The manual's meter model is complete, correct on every transition it can see, and blind exactly one cell ahead, permanently."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_four_refutations_are_one_defect_and_i_am_not_installing_anything_for_them "P-05 and P-07 were action 2, P-06 and P-08 were action 5, and all four are the burn frontier and nothing else. On action 2 the divergence is the single unburnable frontier cell -- (63,59) at t10 and (63,58) at t12 -- because the 48 body pixels of a southward step all sit on the spawn ring and the lower ring, both fully instanced, and key2_body_leaves and key2_body_arrives draw them exactly, five times each. On action 5 the divergence is the same frontier cell carried forward: the 71 cells the diff reports at t11 and t13 are 48 body plus 23 panel and every one of them is fired by exactly one rule -- 24 by key5_body_clears, 24 by key5_body_respawns, and for the B-to-A direction 8 by key5_slot1_lights, 3 by key5_underline1_lights, 8 by key5_slot2_ring_resets, 1 by key5_slot2_centre_resets, 3 by key5_underline2_dims, which sums to 71 with nothing left over. I checked the arithmetic in both directions and it closes. So there is NO rule to add. I refuse to answer these four surprises with a rule, and I say so plainly rather than inventing one, because inventing one is how an earlier round spent four commands on text it had already written."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot, key5_slot1_lights  probe: passed]

  theorem the_identical_information_gains_prove_the_ranker_is_measuring_my_blind_spot "Read the four surprise payloads side by side. Action 2: information_gain_bits 5.087463 at P-05 and 5.087463 at P-07. Action 5: 3.5025 at P-06 and 3.5025 at P-08. Identical to six decimal places, across different world states, different meter counts, and opposite panel configurations. A quantity that measures the world does not repeat itself exactly; a quantity that measures the fixed structure of my own manual does. What these numbers measure is the constant gap between the manual and its ablations plus the constant one-pixel frontier miss -- a property of my bookkeeping, not of the world. Because the gap is constant and positive, ACTION2 scores as maximally informative on every future round, so the ranker buys it every round, so the arm runs this lap forever. THE LOOP IS NOT BAD LUCK AND IT IS NOT A TASTE THE PLAYBOOK CAN ARGUE WITH: it is a fixed point of the ranker created by an unfixable blind spot in the manual. The only honest lever I have is to state the artefact here and prune the cycle in the playbook. The dishonest lever -- writing an unwitnessed rule that makes ACTION3 predict 48 moving pixels so the ranker buys it -- I considered explicitly and REFUSE, because constraint 2 forbids a rule whose transitions I cannot name and because a manual that games its own ranker cannot be checked by anything. Note the advance prediction that cashed: I wrote last round that action 2 would come back at 5.087463 again, and P-07 is that number."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot, the_loop_ran_a_second_time_and_the_playbook_could_not_stop_it  probe: passed]

  theorem the_loop_ran_a_second_time_and_the_playbook_could_not_stop_it "Recorded as a process fact because a desk that hides this is useless. t10 A2, t11 A5, t12 A2, t13 A5. Body south, home, south, home. Panel B, A, B. Two meter cells burned. Zero new mechanism. The previous playbook ranked ACTION3 first in capital letters, listed A2 at spawn under WHAT NOT TO PRESS, and carried a hard prune against the cycle. None of that bound the ranker. So a prune in this playbook is a claim about what SHOULD be searched, not a filter that is enforced, and I will stop pretending otherwise: the prunes below are written for the reader and for whatever tier does respect them, and the argument that has to do the real work is the artefact argument above. The store's own numbers show the shape: 14 states, 12 distinct, and the only duplicates are the ancient sterile pair s1=s0 and s3=s2 -- every later state is nominally distinct ONLY because the meter keeps ticking, which is to say the arm is buying a new state label for one pixel a lap. Eight commands have gone this way. ACTION3 and ACTION4 have each been pressed exactly once, both at a cell where east and west were void, and the east key remains unnamed after thirteen transitions."
    [depends: the_action_map_after_thirteen_transitions  probe: passed]

  theorem certify_is_reporting_on_the_last_manual_that_compiled "Read the certify block carefully before trusting it. It says 9/9 transitions replay exactly, over 9 transitions, while this world has 13. Thirteen transitions exist and every one of t10 through t13 is covered by rules that carry those indices in their ev lists. So the 9 is not a claim about the manual in front of you: the compiler REFUSED this manual over the Gate goal, and a refused manual has no executable form to replay, so what certify measured is an earlier compiling snapshot. The responsibility figure of 0 unexplained cells and the ambiguity figure of 50 of 50 pairs adjudicated with no clashes are equally stale. I therefore claim NOTHING from certify this round and I record the expected number rather than a measured one: with the goal deleted and no other edit, this manual should compile and should replay 13/13. If it replays fewer, the first divergence is the thing to read, not this theorem."
    [depends: the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: pending]

  theorem dynamic_census "Exactly 77 cells have ever changed and every one has an owner. 23 are the panel: slot 1 at rows 1-3 cols 1-3 contributes its 8 ring pixels, its centre (2,2) rendering colour 0 in BOTH configurations and therefore board; underline 1 is row 5 cols 1-3, three cells; slot 2 at rows 1-3 cols 5-7 contributes all NINE cells, centre included, because (2,6) is 1 in configuration A and 0 in B; underline 2 is row 5 cols 5-7, three cells. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 6 are the burned right end of row 63, cols 58 through 63. 23+24+24+6 = 77 = dynamic_cells exactly, and 4096-77 = 4019 = constant_cells exactly. By frame-0 colour: 41 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 6 meter), 9 colour-1 (slot 2 solid in configuration A), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2 dark at frame 0). 41+9+24 = 74 = cells_needing_an_owner exactly."
    [probe: passed]

  theorem the_cascade_length_reads_the_panel_and_it_is_now_five_for_five "ACTION2 pressed with the panel in configuration A returns SEVEN internal frames: t2, t8, t12. Pressed in configuration B it returns NINE: t6, t10. Five presses, five correct, no counterexample, and the panel state before each press is determined by the alternation A5 drives -- A at t2, B at t6, A at t8, B at t10, A at t12. All five ACTION5 presses returned 9 frames regardless of configuration. THE NET DISPLACEMENT IS IDENTICAL IN ALL FIVE ACTION2 PRESSES -- 49 cells changed at t2, t6, t8, t10 and t12 alike, 24 out, 24 in, one burn, six rows south, one lattice cell -- so what the panel changes is the ANIMATION and not the distance, at least over open floor. My semantics say cascade single_frame, so I compare only the net and this costs me no replay accuracy; I record it as an observation my own semantics discard. Five witnesses is enough that I now treat the panel as functional rather than decorative, which is the premise of the mode reading below."
    [depends: key2_body_arrives  probe: passed]

  theorem the_panel_is_a_two_slot_mode_selector_and_the_mode_may_gate_terrain "The reading I hold, stated as a reading. Two 3x3 tokens sit side by side with a 3-cell underline beneath each. The underline of exactly one slot is lit colour 9 at any time and ACTION5 moves the light: configuration A lights underline 1, configuration B lights underline 2, and in thirteen transitions I have never seen both lit or neither. The token in the lit slot is drawn as a HOLLOW colour-9 ring with a dark centre -- which is the shape of the body itself, a rigid block of colour 9 with a one-pixel aperture. The token in the unlit slot is drawn otherwise: slot 1 unlit is a hollow colour-2 ring, slot 2 unlit is a SOLID colour-1 block with no aperture. So the panel says: two avatars exist, this is the one you are driving, and the other one has a different shape. Joined to the cascade finding at five for five -- 7 frames in mode A, 9 in mode B for the identical six-row move -- I read the two slots as two modes of travel. THE PAYOFF IF THIS IS RIGHT IS THE WHOLE LEVEL: the sole route south is blocked by the comb at lattice (6,2), 23 of whose 25 pixels render colour 8, and if the two modes differ in what terrain they may cross then the comb is a mode problem, not a switch problem. THE PROBE IS EXACT AND CHEAP ONCE THE BODY IS SOUTH: drive to lattice (5,2), press ACTION2 in mode A and then in mode B, and see whether either enters (6,2). I hold this at pending and note the competing reading honestly: 7 versus 9 frames could be nothing but two draw speeds."
    [depends: the_cascade_length_reads_the_panel_and_it_is_now_five_for_five, the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem action5_is_return_to_spawn_or_north_and_thirteen_transitions_cannot_split_them "ACTION5 has been pressed five times, at t5, t7, t9, t11 and t13, and every single one was pressed from lattice (2,2) with the body one cell south of spawn, and every single one put the body back at (1,2). Reading NORTH says ACTION5 steps one lattice cell up. Reading RETURN says ACTION5 sends the body home from wherever it is. The body has stood in exactly two lattice cells in fourteen states, and those two are adjacent, so the two readings have made identical predictions on every frame ever observed and will keep doing so unless the body gets two cells from home. A third reading is observationally identical too and I record it because it changes the strategy: ACTION5 SWAPS which of two avatars you drive, and the incoming avatar always starts at spawn. I tested that against t7 specifically, because it is the transition that could have refuted it: if the swap preserved each avatar's position, then at t7 the outgoing avatar sat at (2,2) and the incoming avatar would have been left at (2,2) by t5, so zero body cells should have changed and only 23 panel cells. 71 changed, and 71 changed again at t11. So swap-with-memory is REFUTED twice and swap-with-reset survives, indistinguishable from RETURN. THE SEPARATOR IS THREE COMMANDS: ACTION2, ACTION2, ACTION5, which puts the body at lattice (3,2) -- rows 20-24 are floor from col 13 to col 31, so (3,2) is enterable -- and then asks. If the body lands at (2,2), ACTION5 is north. If it lands at (1,2), ACTION5 is return, and every ACTION5 spent so far has been an undo. THE STAKES: under RETURN, the last EIGHT commands were a two-command loop that burned four meter cells and moved the body nowhere."
    [depends: key5_body_respawns, key5_body_clears  probe: pending]

  theorem the_meter_is_still_two_readings_and_thirteen_transitions_have_not_split_them "Six burns: (63,63) index 2 key 2, (63,62) index 4 key 4, (63,61) index 6 key 2, (63,60) index 8 key 2, (63,59) index 10 key 2, (63,58) index 12 key 2. Seven non-burns: index 1 key 1, 3 key 3, 5 key 5, 7 key 5, 9 key 5, 11 key 5, 13 key 5. READING A says a burn happens iff the key is 2 or 4. READING B says a burn happens iff the command index is even. EVERY BURN IS AT AN EVEN INDEX AND UNDER KEY 2 OR 4; EVERY NON-BURN IS AT AN ODD INDEX AND UNDER KEY 1, 3 OR 5. Thirteen transitions and the two readings have not diverged once, because the arm has pressed key 2 only at even indices and keys 1, 3, 5 only at odd ones. This is not thin evidence, it is evidence spent on the wrong question. I encode reading A because it is the only one this grammar can express, and I state that the next command index is 14, which is EVEN, so ANY press of key 1, 3 or 5 separates them: reading A predicts no burn, reading B predicts (63,57) turns 1. NOTE THE SECOND-ORDER TRAP: under reading B a burn at (63,57) is ALSO unpredictable by my manual for the frontier reason, so the separator must be read off the raw diff and not off a refutation flag. 58 unburned cells remain."
    [depends: meter_burn_key2_next, meter_burn_key4_next, the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: pending]

  theorem the_burn_rules_want_one_rule_and_the_grammar_forbids_it "meter_burn_key2_rightmost and meter_burn_key2_next are ONE law -- burn the leftmost burned-adjacent colour-9 cell of the bar, where the right board edge counts as burned -- split into two rules because the guard language has and and not but no or, and the two conditions (rightof(?p) = wall) and (colored(rightof(?p), 1)) cannot be joined. They are exclusive rather than merely different: where rightof(?p) is off-board there is no cell to render 1, so colored(off-board, 1) is false, and where rightof(?p) is a real cell it is not wall. So constraint 5 holds by construction and the cost is one duplicated line. meter_burn_key4_next has the same body as meter_burn_key2_next with a different key; the key-4 twin of the RIGHTMOST rule has no witness, cannot get one now that (63,63) is burned, and is therefore not written. Both surviving burn rules are now UNGROUNDABLE: all six meter instances render 1, no Glyph9 instance renders 9 with a right neighbour rendering 1, and none ever will again unless a future census extends the bar leftwards. They stay in the manual because they are what makes replay correct on t2 through t12; they will never fire again."
    [depends: meter_burn_key2_rightmost, meter_burn_key2_next  probe: passed]

  theorem dark_may_have_no_instances "The one arithmetic gap in the census and I will not hide it. cells_needing_an_owner is 74 while dynamic_cells is 77, and the difference is precisely the three colour-0 cells of underline 2. Colour 0 is the background, and the arm instances every cell of a declared colour the board cannot explain; whether a dynamic cell whose frame-0 colour is the background counts as explained is not something I can settle from the brief. The indirect evidence is strong: certify has reported an exact replay across transitions that include t5 and t9 with key5_underline2_lights carrying coverage -- if Dark seated no instances that rule could not fire and each of those transitions would be wrong by three cells. I hold this as a probe that has passed indirectly while keeping the theorem, because the reasoning is inference from a check rather than a reading of the arm, and because that check is now one round stale."
    [depends: dynamic_census, certify_is_reporting_on_the_last_manual_that_compiled  probe: passed]

  theorem the_spawn_probe_guard_is_carried_and_is_still_never_tested_negative "Thirteen panel rules carry colored(spawn_probe, 5), which reads cell (8,14) renders floor, which reads the body is not at home. In fourteen states that atom has FIVE positive witnesses -- t5, t7, t9, t11, t13, every one an ACTION5 pressed with the body away -- and ZERO negative witnesses, because ACTION5 has never once been pressed with the body at home. So the guard is doing no work I can demonstrate. Why keep it? Because it changes no prediction today and I can show that cell by cell: with the panel in configuration B, slot 1 renders 2, underline 1 renders 0, slot 2 renders 9, underline 2 renders 9, so the eight forward rules are blocked by their colour tests whatever the body does; and the five reverse rules would fire on those same colours, so with the body at home the guard is the ONLY thing blocking them. That is exactly the untested case. IF ACTION5 IS PRESSED AT SPAWN AND THE PANEL TOGGLES, THIS GUARD IS WRONG IN THIRTEEN RULES AT ONCE. The body is at spawn right now. That is a large, cheap, unclaimed bit."
    [depends: key5_slot1_lights, key5_slot1_dims  probe: pending]

  theorem the_action_map_after_thirteen_transitions "WITNESSED. ACTION2 is SOUTH: five times, t2, t6, t8, t10, t12, six rows south, one lattice cell, 48 cells each. ACTION5 puts the body at spawn from one cell south: five times, t5, t7, t9, t11, t13 -- see action5_is_return_to_spawn_or_north for why that is not the same as knowing it is north. NEGATIVE INFORMATION, read off the map rather than off a rule. At spawn, lattice (1,2), north is void (row 7 col 14 is 5 but row 6 is all 0, and rows 2-6 cols 14-18 are 0), west is void (cols 8-12 are 0), EAST is open floor (rows 8-12 cols 20-24 all render 5) and SOUTH is open. ACTION1 was pressed there at t1 and nothing changed, so ACTION1 IS NEITHER EAST NOR SOUTH. At lattice (2,2), rows 14-18, north was open and south was open (rows 20-24 cols 13-31 are floor) while east and west are void (rows 14-18 cols 20-24 and cols 8-12 are 0). ACTION3 at t3 and ACTION4 at t4 each moved nothing, so NEITHER IS NORTH AND NEITHER IS SOUTH. Combine: ACTION2 is south; ACTION1 is not east and not south; ACTION3 and ACTION4 are each west, or east-blocked-nowhere, and each is compatible with east because east has never been open under either. EAST IS ACTION3 OR ACTION4 and there is no third candidate. THIRTEEN COMMANDS SPENT AND NOT ONE HAS TESTED THE EAST KEY, at a cell where east is three unbroken lattice cells of floor."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the five keys at spawn, where the body now stands. key(2) moves 48 body cells and burns one meter cell it cannot draw: witnessed five times. key(1) inert: WITNESSED, t1, zero cells changed. key(3) inert at spawn: NO WITNESS -- pressed once, at t3, from one cell south, where east and west were both void. key(4) inert at spawn: NO WITNESS -- pressed once, at t4, from one cell south, where it burned a meter cell and moved nothing. key(5) inert at spawn: NO WITNESS AT ALL in fourteen states; ACTION5 has been pressed five times and every one was from one cell south. THREE OF FIVE SILENCES AT SPAWN ARE FORGED DEATH CERTIFICATES; two of the three are the east candidates and the third is the one that would refute thirteen rules' shared guard. This is the entire argument for the next command and against pressing ACTION2 or ACTION5 from the loop again."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_action_map_after_thirteen_transitions  probe: passed]

  theorem the_two_no_op_rules_fail_the_gain_test_and_i_say_so "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has exactly one witness, and each witnesses a transition on which zero cells changed. The manual would replay identically without them: constraint 3 is failed outright and I am not going to dress it up. The reason I keep them is smaller than the rule text: they put key(1) and key(3) into the manual's action alphabet, which is what certify's ambiguity check adjudicates over -- it reported 5 actions and 50 pairs, and without these two it would have reported 3. Deleting them removes information I can see for a saving, four lines, I cannot measure. They change no prediction, so keeping them cannot cost a pixel, and they are the two cheapest deletions in this manual if a later desk wants them gone. Gate was the third declaration that failed the gain test and I argued it bought a goal line; the compiler proved it bought nothing, so it is gone and these two stay."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "key2_body_leaves grounds on meter instances at row 63 whose sixth-below is row 69, and it must not fire there. It does not, because colored(off-board, k) is FALSE rather than an exception, and <cell> = wall is the sanctioned positive test. Every row and column discrimination in the eight forward panel rules is built from that one fact: the k-th above is off-board exactly when k exceeds the row, so panel row 1 is above-twice equals wall; row 3 is a colour test on above-twice, false for row 1 precisely because a colour test on an off-board cell is false; row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column -- col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice -- and those three are pairwise exclusive, which is what keeps constraint 5 satisfied on (2,5), (2,6) and (2,7). I checked the one case that looks dangerous: leftof-seven from col 5 is also off-board, so centre_darkens and row2_left_lights are separated NOT by that atom but by colored(leftof(?s), 1), which is false at col 5 because (2,4) is a separator rendering 0. It also protects meter_burn_key2_rightmost from meter_burn_key2_next. Not one rule uses not, deliberately."
    [depends: key5_slot2_centre_darkens, key2_body_leaves  probe: passed]

  theorem the_reverse_toggle_needs_only_a_colour_test_and_i_checked_every_clash "The five return rules are far shorter than the eight forward ones, because configuration B assigns a UNIQUE colour to each panel group within each declared type, which configuration A does not. In B, with the body away: Glyph9 renders 2 on slot 1 (8 cells) and 0 on underline 1 (3 cells) and 5 on the spawn ring and 9 or 1 on the meter; Spent renders 9 on the slot-2 ring (8 cells) and 0 on the slot-2 centre (1 cell); Dark renders 9 on underline 2 (3 cells). So a bare colour test names each group exactly. I re-audited constraint 5 pair by pair with the meter fully burned, which is the case that could newly clash: all six meter Glyph9 instances now render 1, and 1 is claimed by no key-5 rule at all, so the meter cannot be swept into a panel rule. Colour 2 is claimed only by key5_slot1_lights. Colour 0 on a Glyph9 is claimed only by key5_underline1_lights and no other Glyph9 ever renders 0. key5_slot2_ring_resets takes Spent at 9 while all four forward slot-2 rules take Spent at 1: disjoint. key5_slot2_centre_resets takes Spent at 0, claimed by nothing else. key5_underline2_dims takes Dark at 9 while key5_underline2_lights takes Dark at 0: disjoint. In configuration A none of the five can fire; in configuration B none of the eight forward rules can fire. The two directions are separated by the frame itself, which is why no phase counter is needed."
    [depends: key5_slot1_lights, key5_underline2_dims  probe: passed]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "cascade_lengths are 1, 7 and 9. Every no-op returned one frame; ACTION2 returned 7 or 9 depending on the panel; ACTION5 returned 9 every time. A move is animated one row per internal frame and the world reports the whole animation for a single action; cascade single_frame compares only the net, so up to eight intermediate frames per command are discarded unread, and I record that as a limitation of my own semantics rather than of the world. The refutation I keep, now with five witnesses: under a slide-until-blocked reading, ACTION2 at spawn would run the body south through rows 20-24 and 26-30 to the comb. It stopped after exactly six rows over open floor at t2, t6, t8, t10 and t12. ONE PRESS IS ONE LATTICE CELL, and every distance in the playbook rests on it."
    [depends: key2_body_arrives  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. Row 7 is floor cols 13-43. R=1 (rows 8-12) is floor from col 13 to col 43 except the knob block, so C=2,3,4,5 are open and C=6 holds the knob. R=2 (rows 14-18) is floor at cols 13-19 and 25-31 only, so C=2 and C=4. R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4. R=4 and R=5 are floor only at cols 13-19, so C=2. R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable. R=7 is C=2, plus a fragment of floor at row 48 cols 42-50 that is one row deep and cannot hold a body. R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in fourteen frames the body has occupied exactly TWO cells, (1,2) and (2,2)."
    [depends: the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed five times, t2, t6, t8, t10 and t12: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows and cols 49 and 43 are separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted in colour 9, with the west wall at col 43 left as FLOOR. Inside it, rows 50-54 cols 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, col 50 rows 49-56 is a one-cell strip of floor that leads nowhere. Overlay the body standing in lattice (8,7) -- 5x5, aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate: the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in fourteen frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally write a real goal line."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem pixel at (12,40), colour 8 filling col 40 from row 12 down to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18, which hold 23 colour-8 pixels and 2 colour-5 pixels at (39,14) and (41,14). It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in fourteen frames -- which is exactly why a type declared on colour 8 seats no instances and why the goal I tried to build on it did not compile. The first colour-8 pixel that changes turns this theorem into physics AND makes a goal line writable in the same instant."
    [depends: the_maze_is_a_six_pixel_lattice, the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell -- the eight knob pixels other than its centre (10,40), plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable in one of the two panel modes, and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Thirteen commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens, the_panel_is_a_two_slot_mode_selector_and_the_mode_may_gate_terrain  probe: pending]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because it is the permanent shape of every refutation this level will produce, and this round it bit twice: once as the burn frontier and once as the refused goal. To draw the next burn, or the first step onto fresh ground, or the socket, or to COUNT the comb, I would need an instance on a board cell. The arm offers exactly one lever, arc-instances: all, and its documented behaviour is to instance every cell of that colour THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance, and the compiler will not let a clause count a type whose instance set is empty. I considered and REJECT the two workarounds. First, a second declared type on colour 9 without arc-instances: the arm looks types up by colour and nothing else, so it is indistinguishable from Glyph9, its seat is unspecified, and any cell it landed on would be claimed twice. Second, dropping the board declaration so that every cell of every declared colour is instanced: that would in principle predict burns and fresh ground, and I traced it through the guards before rejecting it -- key2_body_leaves would then ground on the socket bracket at (49,49), whose sixth-below (55,49) renders 5, and would recolour a wall on every ACTION2. Every guard in this manual was written for a dynamic-only census and a full census would need all twenty-one rewritten in one round with no witnesses. So the manual heals ONE STEP BEHIND the world, permanently, and the correct way to read a refutation here is by its divergence set: where that set lies on cells that had never changed before the transition, the manual is not implicated."
    [depends: dynamic_census, the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_parity_and_cannot_say_or "Five expressive holes now. FIRST: there is no third outcome for a (state, action) pair -- not no change and not a named successor, but unobserved, the manual declines to predict. Rules produce events, absence of a rule produces identity, and the compiled step is total. So the three unwitnessed spawn silences are asserted in the same voice as the two witnessed ones, and the probe ranker cannot tell them apart. SECOND: if the meter runs on command parity, that law CANNOT be written here at any length, because the guard language reads pixels and the action name and there is no command counter and no phase pixel. THIRD: there is no or, which is why one burn law is two rules. FOURTH: THERE IS NO WAY TO SAY THAT A PIXEL WILL CHANGE WITHOUT NAMING AN OBJECT THAT OWNS IT, so a manual can never predict the frontier of its own knowledge. FIFTH, learned this round from the compiler: A GOAL CANNOT NAME A CELL THAT HAS NEVER CHANGED, for the same instancing reason, so the winning condition of this level is unwritable until the body or the gate first disturbs it. If a future desk gains one expressive extension, ask for instancing on constant cells first -- it repairs the fourth and fifth holes at once -- then a state counter, then or, then not."
    [depends: the_meter_is_still_two_readings_and_thirteen_transitions_have_not_split_them, the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1 through ACTION5 plus RESET; the alphabet is ACTION1 through ACTION7. Two commands are entirely unconstrained after fourteen states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels changing colour, and never its precondition. Recording that effect is also what would make a goal line writable, since it is the event that turns comb cells dynamic."
    [depends: no_goal_section_this_round_and_the_exact_reason  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on the split-by-colour variant, minus 55676 bits, and a small POSITIVE gain of 614 bits on the 10-track variant -- 614 bits over a 9720-bit baseline is a 6 percent saving, which I take as corroboration rather than structure. What I take is corroboration by frame index, independent of my rules. obj1: colour 1, nine cells, 3x3, present 5 of 14 frames -- slot 2 solid, alive in configuration A. obj5 colour 2 first frame 5, obj6 colour 1 first frame 7, obj7 colour 2 first frame 9, obj8 colour 1 first frame 11, obj9 colour 2 first frame 13: that is the panel alternating exactly on the odd indices where ACTION5 was pressed, five flips, an independent witness for both toggle directions. obj0: colour 9, eight cells, 3x3, present all 14 -- the lit token. obj4 is the whole 64-cell bar of which 6 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. cegis_miner refuses every track and its verdict, the world does not narrate as one mover, is true of the arm and false of the world -- there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours. zero_space self-reports THIN in its own words: 13 transitions constrain rank 7 of 385 features, null space dimension 378, nearly every vector in it a law true over these states and unfalsified rather than confirmed. Its single global law is my census and nothing more. Nothing in the candidate stream proposes anything about colour 8, which is consistent with colour 8 never having changed."
    [probe: passed]

  theorem a_declaration_is_only_as_true_as_the_arm_can_seat_it "Kept and extended, because it has now cost two rounds running. First it was a landmark whose arc-cell comment was missing, which is a hard compile error; spawn_probe at (8,14) was the repair and it held. This round it was a type the arm could seat nowhere. I flagged that risk in the very theorem that introduced Gate -- if the arm treats an empty instance set as an error rather than as an empty set, the goal line and the Gate line are the two lines to delete -- and that flag was right in substance and wrong in detail: the arm accepted the DECLARATION and refused the COUNT. Both lines are now deleted. The general rule I extract: before writing any clause, ask what the arm will seat for it, and if the answer is nothing, the clause is not conservative, it is fatal."
    [depends: the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The world has not advanced since the last round -- no transition was spent -- so this is the same prediction, restated, and it is now overdue. The body is at spawn, lattice (1,2). The panel is in configuration B. Six meter cells are burned, cols 58 through 63; 58 remain. The next command has index 14, which is EVEN. ACTION2 at spawn: 48 body pixels drawn correctly, ZERO meter pixels drawn, and the world burns (63,57) -- so the manual is refuted by exactly one cell, the information gain is reported as 5.087463 again, and NOTHING IS LEARNED. If that number comes back different, this theorem is wrong and the artefact reading is dead. ACTION5 at spawn: predicted identity by all thirteen guarded rules, and if the panel toggles instead then colored(spawn_probe, 5) is wrong in thirteen rules at once -- the largest single refutation available on this board. ACTION3 at spawn: predicted ZERO cells changed, with NO witness for that silence at this cell. If the body steps east, ACTION3 is east and I pay 48 pixels I have priced -- 24 arrival pixels on rows 8-12 cols 20-24, which have never changed and therefore hold no instance, and 24 departure pixels which do hold Glyph9 instances but which no witnessed east-leaves rule can fire on. If it does not step, ACTION4 is east by elimination. EITHER WAY, if (63,57) burns under key 3, reading A of the meter is dead and reading B is confirmed by the first discriminating transition in fourteen; if it does not burn, reading A survives its first real test. ACTION1 at spawn: predicted identity, witnessed at t1, buys nothing. ACTION6 or ACTION7: entirely unconstrained, and one of them may be the click that presses the knob and thereby writes my goal line for me."
    [depends: the_action_map_after_thirteen_transitions, the_meter_is_still_two_readings_and_thirteen_transitions_have_not_split_them, the_identical_information_gains_prove_the_ranker_is_measuring_my_blind_spot  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Fourteen states, thirteen transitions: RESET, A1 A2 A3 A4 A5 A2 A5 A2 A5
# A2 A5 A2 A5.
#   t1  A1 at spawn        -> nothing
#   t2  A2 at spawn        -> body one lattice cell SOUTH (48) + burn (63,63)
#   t3  A3 one cell south  -> nothing
#   t4  A4 one cell south  -> burn (63,62) and nothing else
#   t5  A5 one cell south  -> body to spawn (48) + panel A->B (23)
#   t6  A2 at spawn        -> body SOUTH (48) + burn (63,61), 9 frames
#   t7  A5 one cell south  -> body to spawn (48) + panel B->A (23)
#   t8  A2 at spawn        -> body SOUTH (48) + burn (63,60), 7 frames
#   t9  A5 one cell south  -> body to spawn (48) + panel A->B (23)
#   t10 A2 at spawn        -> body SOUTH (48) + burn (63,59), 9 frames
#   t11 A5 one cell south  -> body to spawn (48) + panel B->A (23)
#   t12 A2 at spawn        -> body SOUTH (48) + burn (63,58), 7 frames
#   t13 A5 one cell south  -> body to spawn (48) + panel A->B (23)
# Body is at spawn, lattice (1,2). Panel is configuration B. SIX meter cells
# burned, cols 58-63; 58 remain. Next command index is 14, EVEN.
#
# ========= WHAT ACTUALLY BROKE THIS ROUND: THE MANUAL DID NOT COMPILE =====
# No transition was spent. The four refutations are the four already priced.
# The one new fact is the compiler's:
#
#   UnsupportedClause: count(Gate) -- this level declares no instance of that
#   type, so the count is 0 on every state and the clause decides nothing.
#
# I had written a goal over a type with ZERO instances deliberately, arguing
# an unreachable goal is honest rather than vacuous. It is neither: it does
# not compile, and an uncompiled manual has no executable form, so plan,
# certify and probe all got nothing. Gate and the goal line are deleted.
#
# THE LAW THAT REPLACES THE MISTAKE, and it binds this playbook too:
#   A GOAL CAN ONLY NAME CELLS THAT HAVE ALREADY CHANGED, because only those
#   carry instances. It is the burn frontier from the other side.
#
# ========= heuristic_miss, ANSWERED WITH A REFUSAL AND A PRICE =========
# There is still no goal section, and this is the enumerated reason, not a
# shrug. A goal may say count(<type>) or <instance>.pos = <landmark>. The
# only types with instances are Glyph9 (panel slot 1, underline 1, the spawn
# ring, six burned meter cells), Vacated (the ring one cell south), Spent
# (slot 2) and Dark (underline 2). ALL OF THEM ARE PANEL, SPAWN RING OR
# METER. The nearest candidate, count(Glyph9, color = 9) = 0, is false in all
# fourteen states and would become TRUE one press of A2 from here, at a cell
# that is not a win -- a goal that halts a planner one move from spawn is
# worse than no goal, because unsat is honest and sat-on-garbage is not.
# The pos form is dead too: this world recolours, it never moves, so no
# instance's pos has ever changed.
#
#   SO THE GOAL IS BOUGHT WITH A COMMAND, NOT WRITTEN WITH AN EDIT.
#   The first pixel of the comb or of the socket bracket that changes colour
#   makes those cells dynamic, seats instances on them, and makes the goal
#   line both writable and sound in the same instant. Everything ranked below
#   is ranked by how close it gets to that pixel.
#
# THE WIN, carried in prose because the DSL cannot hold it:
#   WIN = the body stands in lattice (8,7), rows 50-54 cols 44-48, so its 24
#   ring pixels render 9 and its aperture shows the pip at (52,46). Drawn as
#   three colour-9 walls with the west side open: a socket cut to the body.
#   ROUTE = lattice column 2 is the only north-south corridor and the comb at
#   (6,2) blocks it, 23 of its 25 pixels colour 8. The comb is wired by one
#   connected colour-8 line to a 3x3 knob at (1,6), reachable eastward along
#   R=1 from spawn: (1,2) -> (1,3) -> (1,4) -> (1,5), three steps on open
#   floor, and (1,5) is separated from the knob's cell only by separator col
#   37, which is floor.
#
# ========= WHY THE ARM KEEPS BUYING THE SAME LAP =========
# The next meter burn always lands on a cell that has never changed, so no
# instance owns it, so no event can draw it. Every press of A2 refutes the
# manual by exactly one pixel; the refutation makes A2 look maximally
# informative; the ranker buys A2. It is a fixed point, not a taste.
# THE PROOF THAT THE BITS ARE FAKE IS IN THE PAYLOADS:
#   information_gain_bits = 5.087463 for action 2 at P-05 AND at P-07.
#   information_gain_bits = 3.5025   for action 5 at P-06 AND at P-08.
# Identical to six decimals across different states, different meter counts,
# opposite panel configurations. TREAT A REPEATED-IDENTICAL GAIN AS ZERO.
# I have NOT gamed the ranker back: the lever that would work is an
# unwitnessed rule making A3 predict 48 pixels, and constraint 2 forbids it.
#
# ========= THE ONE THING WORTH BUYING, AND IT PAYS THREE TIMES =========
# PRESS ACTION3 AT SPAWN.
#   1. THE EAST KEY, unanswered after thirteen commands and the only thing
#      between this arm and the knob. A2 is south (5 witnesses). A5 returns
#      to spawn (5 witnesses). A1 was pressed AT SPAWN with east OPEN and
#      moved nothing, so A1 is not east. EAST IS A3 OR A4, no third
#      candidate. A3 and A4 were each pressed once, both from lattice (2,2)
#      where east AND west are void, so neither press could answer anything.
#      If the body steps, A3 is east. If not, A4 is east by elimination.
#   2. THE METER. Six burns at even indices under keys 2,4,2,2,2,2; seven
#      non-burns at odd indices under keys 1,3,5,5,5,5,5. Reading A (key is 2
#      or 4) and reading B (index is even) agree on all thirteen. Index 14 is
#      EVEN and key 3 is neither 2 nor 4: A burns nothing, B burns (63,57).
#      READ IT OFF THE RAW DIFF, NOT OFF A REFUTATION FLAG -- under B the
#      burn is undrawable anyway, so a refutation fires either way.
#   3. A FORGED SILENCE. The manual predicts zero cells changed for A3 at
#      spawn and has no witness for it; three of the five spawn silences are
#      forged this way and A3 is one.
#   And the knob is four eastward lattice cells away, so the east key is the
#   first step of the only route to a goal line.
#
# ========= SECOND CHOICE: PRESS ACTION5 AT SPAWN =========
#   Thirteen rules share colored(spawn_probe, 5) -- the body is not at home.
#   Five positive witnesses, ZERO negatives, because A5 has never been
#   pressed with the body at home. The body is at home now. The manual
#   predicts identity. If the panel toggles anyway, thirteen rules are wrong
#   at once. Ranked second only because it does not touch the east key.
#
# ========= THIRD CHOICE: ACTION6 OR ACTION7 =========
#   Never pressed, entirely unconstrained. In this family one is usually a
#   click, and the knob is a 3x3 target the body appears unable to stand on.
#   My manual can record such a command's EFFECT and never its precondition
#   -- but the effect is exactly what makes the comb dynamic and the goal
#   writable, so the ceiling here is the level itself.
#
# ========= WHAT NOT TO PRESS, AND WHY IT WILL LOOK TEMPTING =========
#   A2 at spawn: it will score ~5.09 expected bits and buy NOTHING. The 48
#   body pixels are drawn correctly five times over; the only divergent cell
#   is (63,57), which no manual in this language can draw. Guaranteed
#   refutation, guaranteed wasted round, one more burned meter cell.
#   A5 from one cell south is pure loop; A5 from spawn is the exception and
#   is ranked second above.
#   A1 at spawn: witnessed inert at t1.
#   A4 at spawn: the same experiment as A3 with the labels swapped, but it
#   spends a meter cell under BOTH readings -- press it only if A3 is inert.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The next burn cell is undrawable: one pixel per press of A2 or A4,
#     forever. A refutation whose divergence set is exactly that cell
#     implicates nothing.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on rows 8-12 cols 20-24 which have never changed, and 24
#     departure pixels for which no east-leaves rule is witnessed. 24 for the
#     second step in the same direction, 0 after.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.
#
# ========= ONE CAUTION ABOUT CERTIFY =========
#   Its block says 9/9 over 9 transitions while the world has 13, and this
#   manual did not compile, so those numbers describe an earlier snapshot.
#   Do not read them as coverage of t10-t13.

order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     treat_a_repeated_identical_information_gain_as_zero_gain         [proof: lean]
order     discount_any_gain_that_comes_from_a_cell_with_no_instance        [proof: lean]
order     prefer_a_command_that_closes_three_open_questions_over_one       [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     break_a_repeating_command_cycle_before_optimising_within_it      [proof: lean]
order     test_a_shared_guard_where_it_has_never_been_false                [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one   [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation      [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal     [proof: lean]
order     spend_a_meter_cell_only_on_a_question_it_actually_closes         [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it   [proof: lean]

prune     goal_clause_over_a_type_with_zero_instances => dead                    [proof: lean]
prune     goal_that_becomes_true_at_a_state_that_is_not_a_win => dead            [proof: lean]
prune     divergence_lies_only_on_the_unburned_meter_frontier => dead            [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key => dead   [proof: lean]
prune     repeats_the_two_command_cycle_that_returns_the_body_to_spawn => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead        [proof: lean]
prune     no_rule_it_could_witness_can_still_ground_in_this_census => dead       [proof: lean]
prune     spends_a_meter_cell_and_closes_no_open_question => dead                [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead        [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                   [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead          [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead        [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead            [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                      [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead         [proof: lean]
prune     tests_a_direction_at_a_cell_where_that_direction_is_void => dead       [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead         [proof: lean]
prune     meter_exhausted and not goal => dead                                   [proof: lean]

heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic rules_sharing_a_guard_that_one_command_could_refute_together      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                   [admissible: lean]

prefer    a_command_that_would_turn_a_machinery_pixel_dynamic               [ev: 0/14 states]
prefer    a_key_that_names_a_direction_whichever_way_it_answers             [ev: 2/2 candidates]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index         [ev: 13/13 transitions tie]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed     [ev: 3/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on              [ev: 3/5 keys at spawn]
prefer    a_command_that_leaves_the_cycle_the_last_eight_commands_formed    [ev: 8/10 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 13/13 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                    [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered           [ev: 1/1 levels]
prefer    a_free_probe_over_one_that_costs_a_meter_cell                     [ev: 6/13 commands burned]
```

## Why you are being called: the surprises that fired

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "ee026f989fe57e88",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '30332fff54b4924c', the world answered '4dfbfe14d4e85299'

```json
{
 "action": 2,
 "expected_bits": 1.394848870026,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 5.087463,
 "manual_predicted": "30332fff54b4924c",
 "n_hypotheses": 34,
 "n_survivors": 1,
 "observed": "4dfbfe14d4e85299",
 "probe_id": "P-09",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'e66afa8078cb4fd2', the world answered 'd09fae77a1d46f2c'

```json
{
 "action": 5,
 "expected_bits": 2.2195282823,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 3.5025,
 "manual_predicted": "e66afa8078cb4fd2",
 "n_hypotheses": 34,
 "n_survivors": 3,
 "observed": "d09fae77a1d46f2c",
 "probe_id": "P-10",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '0c86941f09a0caaf', the world answered '44c44660a53cf5d4'

```json
{
 "action": 2,
 "expected_bits": 1.955012006402,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 5.087463,
 "manual_predicted": "0c86941f09a0caaf",
 "n_hypotheses": 34,
 "n_survivors": 1,
 "observed": "44c44660a53cf5d4",
 "probe_id": "P-11",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '06e79195f0adc15f', the world answered '3a11719074841328'

```json
{
 "action": 5,
 "expected_bits": 2.273661689922,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 3.5025,
 "manual_predicted": "06e79195f0adc15f",
 "n_hypotheses": 34,
 "n_survivors": 3,
 "observed": "3a11719074841328",
 "probe_id": "P-12",
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
 "first_divergence": null,
 "proof_layer_available": false,
 "replay": {
  "detail": "13/13 transitions replay exactly",
  "matched": 13,
  "ok": true,
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
```json
[
  {"id": "R-01", "subject": "colored(spawn_probe, 5) conjunct in 13 panel rules", "verdict": "reject",
   "as": "deleted from all thirteen key-5 panel rules",
   "why": "seven positive witnesses (t5,t7,t9,t11,t13,t15,t17) and zero negative witnesses, because key 5 has never been pressed with the body at home; an unwitnessed conjunct is an entry without evidence, so keeping it was the constraint-2 violation, and every observed key-5 press had it true so replay is unaffected"},

  {"id": "L-01", "subject": "information_gain_bits = log2(n_hypotheses / n_survivors)", "verdict": "accept",
   "as": "the_loop_is_a_theorem_of_my_own_manual_and_here_is_its_arithmetic",
   "why": "the payloads give n_hypotheses 34 with n_survivors 1 for key 2 and 3 for key 5; log2(34) = 5.087463 and log2(34/3) = 3.502500 are exactly the two reported numbers across all eight probes, so the gain measures my ablation count and not the world"},

  {"id": "L-02", "subject": "why the A2/A5 alternation is forced", "verdict": "accept",
   "as": "second half of the same theorem",
   "why": "at spawn only key 2 makes a rule fire, so only key 2 has ablation disagreement; at one cell south key 2 fires nothing because no Glyph9 renders 9 there and the destination lattice cell is board with no instance, so only key 5 does; the alternation is the unique argmax of any disagreement ranker reading this manual"},

  {"id": "L-03", "subject": "a probe tier ranking by ablation disagreement can never buy an unmodelled action", "verdict": "accept",
   "as": "general law stated inside the same theorem",
   "why": "every ablation of a manual silent on key k is also silent on key k, so k scores exactly zero expected bits, while constraint 2 forbids modelling a key with no witness; keys 3, 4, 6 and 7 are therefore permanently unbuyable by this tier"},

  {"id": "O-01", "subject": "two newly dynamic cells (63,57) and (63,56)", "verdict": "accept",
   "as": "two more Glyph9 instances, meter group now 8",
   "why": "dynamic_cells rose 77 to 79 and cells_needing_an_owner rose 74 to 76, exactly the two cells the diffs at t14 (cols 14-57) and t16 (cols 14-56) name, and the current row 63 shows cols 56-63 rendering 1"},

  {"id": "R-02", "subject": "meter_burn_key2_next", "verdict": "accept",
   "as": "ev extended to t6,t8,t10,t12,t14,t16 cov 6/6",
   "why": "last round it had no grounding left; the two frontier cells were instanced after they changed, so t14 and t16 now replay retroactively, which is the healing-one-step-behind prediction cashing"},

  {"id": "L-04", "subject": "the burn frontier is a permanent one-pixel blind spot", "verdict": "accept",
   "as": "the_burn_frontier_is_a_permanent_one_pixel_blind_spot, restated for (63,55)",
   "why": "confirmed twice more by bookkeeping rather than by argument: the census grew by exactly the two cells the manual could not draw, and (63,55) is board today for the same reason"},

  {"id": "P-01", "subject": "probe_refutation P-09 and P-11 (action 2)", "verdict": "reject",
   "why": "refusal to change: the divergence is the single unburnable frontier cell, (63,57) at t14 and (63,56) at t16; the 48 body pixels sit on the spawn ring and the lower ring, both fully instanced and drawn exactly by key2_body_leaves and key2_body_arrives seven times each, so there is no rule to install"},

  {"id": "P-02", "subject": "probe_refutation P-10 and P-12 (action 5)", "verdict": "reject",
   "why": "refusal to change: the 71 changed cells decompose as 24 by key5_body_clears, 24 by key5_body_respawns and 23 panel cells each fired by exactly one rule, summing with nothing left over, so the reported divergence must be the frontier cell carried forward through the predictor's own state rather than a missing rule"},

  {"id": "P-03", "subject": "heuristic_miss (no goal declared)", "verdict": "reject",
   "why": "third explicit refusal, with a new decisive limb: even a sound goal would not help, because the plan tier searches my compiled dynamics whose entire reachable set is two lattice cells crossed with two panel configurations, so a reachable goal commits A2 or A5 and an unreachable one returns unsat exactly as now; the bottleneck is the action map, not the goal"},

  {"id": "E-01", "subject": "the winning condition (24 ring pixels of rows 50-54 cols 44-48 rendering 9)", "verdict": "probe-pending",
   "why": "wanted a goal naming those cells; they have never changed, so they are board, carry no instance, and cannot appear in any count; wrote the condition as prose in the_socket_is_a_keyhole_and_names_the_winning_position and left the goal section absent"},

  {"id": "E-02", "subject": "a rigid 5x5 body translating six rows per action", "verdict": "reject",
   "as": "the_dsl_cannot_translate_a_body_of_extent",
   "why": "moved is one cell, jumped-over is two, jumped/teleported to a landmark collapses every grounded instance onto one cell, and cascade is fixed at single_frame, so no mover model can replay this world; the recolour model is the only one the grammar admits, which also kills the pos form of the goal permanently"},

  {"id": "E-03", "subject": "dropping the board declaration to instance constant cells", "verdict": "reject",
   "why": "traced concretely this round and it misfires: key2_body_leaves would ground on the socket wall pixel (50,49) whose sixth-below (56,49) renders 5, and key2_body_arrives would ground on floor pixel (55,43) whose sixth-above (49,43) renders 9, painting walls on every key 2; last round I justified this rejection with (55,49), which in fact renders 9, so the reason is corrected while the verdict stands"},

  {"id": "L-05", "subject": "cascade length reads the panel", "verdict": "accept",
   "as": "the_cascade_length_reads_the_panel_and_it_is_now_seven_for_seven",
   "why": "t14 in configuration B returned 9 frames and t16 in configuration A returned 7, matching the alternation key 5 drives, with net displacement identical in all seven key-2 presses"},

  {"id": "L-06", "subject": "meter reading A (key) versus reading B (parity)", "verdict": "probe-pending",
   "why": "four more transitions and still no separator, because key 2 was again pressed only at even indices and key 5 only at odd ones; that is now a direct consequence of the ranker loop rather than bad luck, and index 18 with key 1, 3 or 5 remains the separator"},

  {"id": "O-02", "subject": "mdl_segmenter obj10 (colour 1, first frame 15) and obj11 (colour 2, first frame 17)", "verdict": "entailed",
   "why": "they are the sixth and seventh panel flips at the odd indices where key 5 was pressed, which my toggle rules already predict; corroboration by frame index, no new structure"},

  {"id": "O-03", "subject": "mdl_segmenter obj3 (1006-cell colour-null blob)", "verdict": "reject",
   "why": "connected_components(4) merged the maze floor with the body ring, so the segmenter cannot see the mover at all; the absence is the finding and no track is adoptable from it"},

  {"id": "R-03", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "reject",
   "why": "true of the arm and false of the world; its own refusals say it mines only move and none while every transition here narrates recolor, and there is exactly one mover, a rigid 24-pixel ring the arm can only see as 24 simultaneous recolours"},

  {"id": "L-07", "subject": "zero_space global law", "verdict": "entailed",
   "why": "its single law is my dynamic census and nothing more, and it self-reports THIN at rank 9 of 395 features with a 386-dimensional null space, so nothing in it is adopted as a rule"},

  {"id": "P-04", "subject": "key 5 pressed at spawn", "verdict": "probe-pending",
   "why": "the manual now predicts exactly 23 panel cells change and zero body pixels move; if zero cells change, thirteen rules are wrong at once and the deleted conjunct gets the negative witness it never had, which is the largest single refutation available on this board and costs no meter cell"},

  {"id": "P-05", "subject": "key 3 pressed at spawn", "verdict": "probe-pending",
   "why": "still unbuyable by the probe tier (zero disagreement) but still the command that would close three questions: east is key 3 or key 4 with no third candidate, index 18 is even so key 3 separates the two meter readings, and its inertness at spawn has no witness"},

  {"id": "L-08", "subject": "certify's 13/13 over 14 states", "verdict": "reject",
   "as": "certify_is_one_round_stale_again",
   "why": "it reports 13 transitions and 70 adjudicated pairs (14 x 5) while the world has 17 transitions and 18 states, so it measured the previous manual against the previous history and says nothing about t14-t17 or about this round's edit; expected replay is stated as 17/17 rather than claimed"},

  {"id": "L-09", "subject": "the two no-op rules and the landmark spawn_probe", "verdict": "accept",
   "as": "kept, with the gain-test failure admitted",
   "why": "constraint 3 is failed outright: they recolour a pixel to the colour it already has; they are kept because they hold keys 1 and 3 in the action alphabet and because they are now the only references to spawn_probe, and deleting a landmark is the exact class of edit that cost a round once already"},

  {"id": "L-10", "subject": "dark_may_have_no_instances", "verdict": "probe-pending",
   "why": "cells_needing_an_owner 76 versus dynamic_cells 79 is exactly the three colour-0 underline-2 cells; the indirect evidence from exact replay on t5/t9/t13 is strong but is inference from a check rather than a reading of the arm"}
]
```
```
