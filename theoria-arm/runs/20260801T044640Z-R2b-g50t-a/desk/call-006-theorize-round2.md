# call-006-theorize-round2

model: `claude-opus-5` · 700562 ms · $2.012925 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 47369, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 47369, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 47369, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 47369, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 60173, "type": "message"}], "output_tokens": 60173, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
# theory.dsl -- world observed for 18 states / 17 transitions
#   RESET, A1 A2 A3 A4 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5.
# 79 cells have ever changed; this manual names and owns all 79.
#
# WHY THIS ROUND EXISTS, IN ORDER OF WHAT IT COST.
#
# 1. THE COMPILER GOT NO MANUAL AT ALL. Its complaint this round is not
#    semantic: "the reply carried no === THEORY === block; emit all three
#    blocks". That is my desk's own formatting failure and it cost a whole
#    round of every downstream tier for the SECOND round running -- last
#    round it was an uncompilable clause, this round it was an unemitted
#    block. Recorded as the_two_rounds_i_lost_were_both_lost_at_my_own_desk.
#    Nothing was installed, so certify's block below describes the 14-state
#    snapshot and not this world.
#
# 2. FOUR TRANSITIONS DID ARRIVE: t14 A2, t15 A5, t16 A2, t17 A5. Two more
#    laps of the same two-command loop. Two more meter cells burned, exactly
#    the two named in advance -- (63,57) at t14 and (63,56) at t16 -- and the
#    information gains came back at 5.087463 for action 2 (twice) and 3.5025
#    for action 5 (twice), to six decimals, for the fourth and fifth time.
#    THE ADVANCE PREDICTION CASHED IN FULL. The artefact reading is no longer
#    a reading.
#
# 3. NO NEW MECHANISM. Zero new rules are installed, because zero transitions
#    of a new kind arrived. Every edit below is a count: ev lists extended,
#    coverages recomputed, the census moved from 77 cells to 79.
#
# 4. ONE GENUINELY NEW FINDING, and it is the important one:
#    THE GOAL CLAUSE IS NOT THE BOTTLENECK. Even a compilable, reachable goal
#    would buy nothing, because MY TRANSITION MODEL CONTAINS NO MOVE THAT
#    LEAVES THE TWO-CELL LOOP. Every state my rules can reach is spawn or one
#    cell south. So `sat` could only ever be returned for a state inside the
#    loop, and committing inside the loop is the pathology itself. See
#    the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease.
#
# 5. AND ITS TWIN, ALSO NEW: MY MANUAL PREDICTS THAT ACTION2 PRESSED ONE CELL
#    SOUTH OF SPAWN DOES NOTHING. It is almost certainly wrong, the body has
#    stood on that cell seven times, and no one has ever tried. See
#    the_loudest_forged_silence_is_not_at_spawn.
#
# EXPECTED REPLAY: 17/17.

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
  Vacated [segment: dynamic_colour_5 ev: t2-t17 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13,t15,t17 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13,t15,t17 compress: 3]

events:
  event recolored(o, c)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12,t14,t16 cov: 168/168]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12,t14,t16 cov: 168/168]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13,t15,t17 cov: 168/168]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13,t15,t17 cov: 168/168]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12,t14,t16 cov: 6/6]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17 cov: 32/32]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13,t17 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13,t17 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13,t17 cov: 4/4]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13,t17 cov: 4/4]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13,t17 cov: 4/4]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13,t17 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11,t15 cov: 24/24]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11,t15 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11,t15 cov: 24/24]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11,t15 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11,t15 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 43 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: inferred-from-replay]
  invariant board_cells count(board) = 4017 [status: counted]
  invariant meter_cells_burned_right_now count(Glyph9, color = 1) = 8 [status: state-dependent-not-an-invariant]

  theorem the_two_rounds_i_lost_were_both_lost_at_my_own_desk "Recorded first because it is the largest single cost in the log and neither loss was the world's doing. Round before last: a goal clause counting a type with zero instances, which the compiler refused, so nothing downstream ran. This round: the reply carried no === THEORY === block at all, so nothing was even offered to the compiler, and certify is still reporting 13/13 over 13 transitions while the world has 17. TWO ROUNDS, ZERO TRANSITIONS BOUGHT BY EITHER, AND BOTH SPENT ON THE FORM OF THE ANSWER RATHER THAN ITS CONTENT. The general rule, which binds every desk that stands here: THE MANUAL IS ONLY WORTH WHAT REACHES THE COMPILER. Emit all three blocks, every round, before worrying whether the content is good; a mediocre manual that compiles outperforms an excellent one that does not by an unbounded margin, because the mediocre one gets corrected by the next frame and the excellent one gets corrected by nothing. Every number certify reports this round is stale by one round and I claim nothing from it."
    [depends: a_declaration_is_only_as_true_as_the_arm_can_seat_it  probe: passed]

  theorem the_advance_prediction_cashed_and_the_artefact_is_now_established "Last round I wrote, before seeing the frames: the body is at spawn, the panel is in configuration B, the next burn lands on (63,57), pressing ACTION2 draws 48 body pixels correctly and zero meter pixels, the manual is refuted by exactly one cell, and the information gain is reported as 5.087463 again with nothing learned. FOUR TRANSITIONS LATER EVERY CLAUSE OF THAT IS TRUE. t14 burned (63,57) and t16 burned (63,56), exactly the two cells named in order; P-09 and P-11 both report action 2 at information_gain_bits 5.087463; P-10 and P-12 both report action 5 at 3.5025. That is five and five, to six decimals, across four different world states with four different meter counts and both panel configurations. A quantity that measures the world varies with the world. THE NUMBER IS MEASURING THE FIXED GEOMETRY OF MY OWN MANUAL AGAINST ITS OWN ABLATIONS PLUS A CONSTANT ONE-PIXEL MISS, and I now treat it as established rather than as a reading. The operational consequence is unchanged and now unarguable: A REPEATED-IDENTICAL INFORMATION GAIN IS ZERO INFORMATION. I again refuse the only lever that would move the number -- an unwitnessed rule making some other key predict 48 pixels -- because constraint 2 forbids it and because a manual that games its own ranker can be checked by nothing."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: passed]

  theorem the_five_refutations_are_one_defect_and_i_am_again_installing_nothing "P-09 and P-11 are action 2; P-10 and P-12 are action 5; heuristic_miss is the goal and is answered separately. The action-2 divergence is one cell each time and I can name it: t14 changed 49 cells over rows 8-63 cols 14-57, being 48 body pixels plus the burn at (63,57); t16 changed 49 over cols 14-56, being 48 body plus (63,56). All 48 body pixels sit on the spawn ring and the ring one lattice cell south, both fully instanced, and key2_body_leaves and key2_body_arrives draw them exactly, now seven times each. The unburned frontier cell was board at the moment of the press and held no instance, so no event in this language could touch it. The action-5 divergence contains no new cell at all: t15 and t17 each changed 71 cells over rows 1-18 cols 1-18, being 48 body plus 23 panel, and every one is fired by exactly one rule -- 24 by key5_body_clears, 24 by key5_body_respawns, and for the B-to-A direction 8 by key5_slot1_lights, 3 by key5_underline1_lights, 8 by key5_slot2_ring_resets, 1 by key5_slot2_centre_resets, 3 by key5_underline2_dims, which sums to 71 with nothing over. THERE IS NO RULE TO ADD FOR ANY OF THE FOUR. I refuse to answer them with a rule and say so plainly, because inventing one is how two earlier rounds were spent."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot, the_probe_tier_rolls_my_state_forward_and_never_resyncs  probe: passed]

  theorem the_probe_tier_rolls_my_state_forward_and_never_resyncs "NEW THIS ROUND, and it explains the one thing the previous desk waved at. Action 5 has no undrawable cell in it: at t15 and t17 the 71 changed cells are all instanced and all fired by exactly one rule, so if the probe predicted from the OBSERVED frame it would predict action 5 exactly and P-10 and P-12 would not exist. They do exist, twice, at an identical gain. THE LEADING READING IS THEREFORE THAT THE PROBE PREDICTS FROM THE MANUAL'S OWN ROLLED-FORWARD STATE, which already carries the burn the manual could not draw at the preceding action 2. If that is right, THE DEBT IS CUMULATIVE AND PERMANENT: once the manual misses one pixel it is behind for every subsequent action, so every future command looks refuted whatever it is, and no edit repairs it because the missed pixel is undrawable by construction. There is one mitigation and it is free: under reading A of the meter the debt only grows on keys 2 and 4, so ANY COMMAND THAT IS NOT KEY 2 OR KEY 4 ADDS NO NEW DEBT. Under reading B it grows on every even index regardless of key -- in which case a non-burning key at an even index is exactly the experiment that separates the two readings, so the same command is correct under both. I record the competing reading honestly: the hash might cover something beyond the frame, in which case the action-5 refutations mean something I have not found. The discriminating observation is a press of action 5 immediately after a press that burned nothing."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot, the_meter_is_still_two_readings_and_seventeen_transitions_have_not_split_them  probe: pending]

  theorem the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease "THE FINDING OF THIS ROUND, and it is my answer to heuristic_miss, which has now fired five times. The surprise says: declaring the winning condition is the highest-value edit available. I have tested that claim and it is FALSE ON THIS BOARD, for a reason that is arithmetic rather than taste. Suppose I could write a sound goal. The plan tier reaches it by searching MY compiled rules. Enumerate what my rules can do: key2_body_leaves and key2_body_arrives move the body from spawn to one cell south, key5_body_clears and key5_body_respawns move it back, the panel rules toggle 23 panel pixels, the burn rules are ungroundable. THAT IS THE WHOLE REACHABLE SET: TWO LATTICE CELLS AND TWO PANEL CONFIGURATIONS. So the only goals that could ever return sat are goals satisfied inside the loop, and committing inside the loop is precisely the pathology that has consumed twelve of seventeen commands. A goal that returns sat there is strictly worse than unsat, because unsat leaves the arm probing while sat-on-a-loop-state makes it commit and declare success one lattice cell from where it started. I checked the four candidates the grammar admits over the four types that carry instances. count(Glyph9, color = 5) = 24 means the body is off spawn: false now, true after one press, not a win. count(Vacated, color = 9) = 24 means the same thing from the other side. count(Glyph9, color = 1) = 64 exceeds the 43 instances that exist and can never be true. count(Spent) = 0 is constant-false because Spent always has 9 instances. THEREFORE I DECLINE THE GOAL SECTION FOR THE THIRD TIME AND I NAME WHAT WOULD END THE DECLINING: one observation in which the body occupies a THIRD lattice cell. That single observation seats instances on 24 cells that have never changed, extends the transition model past the loop, and is the same observation that eventually makes the socket writable. THE GOAL IS BOUGHT WITH A COMMAND. NO EDIT CAN SUBSTITUTE."
    [depends: the_goal_i_still_cannot_write_is_the_real_one, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_loudest_forged_silence_is_not_at_spawn "NEW, and it is the cheapest large error in this manual. Ask what my compiled rules predict for ACTION2 pressed with the body ONE CELL SOUTH of spawn, at lattice (2,2), a cell the body has now occupied seven times. key2_body_leaves grounds only on Glyph9 and requires colored(?p, 9): the spawn ring renders 5 when the body is away, the eight meter cells all render 1, slot 1 renders 2 or 9 with nothing but background six rows below it, so NO GLYPH9 INSTANCE SATISFIES IT. key2_body_arrives grounds only on Vacated and requires colored(?v, 5): the lower ring renders 9 when the body stands there, so NO VACATED INSTANCE SATISFIES IT EITHER. THE COMPILED STEP IS TOTAL, SO MY MANUAL ASSERTS THAT ACTION2 AT LATTICE (2,2) DOES NOTHING. That is almost certainly false: rows 20-24 are floor from column 13 to column 31, so lattice (3,2) is open, and one press of action 2 has moved the body exactly one lattice cell south on seven consecutive occasions over open floor. The manual is asserting a silence it has never witnessed, in the same voice it uses for the silence at t1 that it did witness, at the one cell where being wrong would be worth the most -- because the body landing in lattice (3,2) is the third lattice cell, which is the observation the whole manual is waiting on. Seventeen commands and no one has pressed action 2 twice in a row. I do NOT install a rule for this: the divergence would fall on rows 20-24 columns 14-18, twenty-four cells that have never changed and therefore hold no instance, so the rule could not fire even if I wrote it. The price is advertised, not hidden."
    [depends: the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease, silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged  probe: pending]

  theorem the_burn_frontier_is_a_permanent_one_pixel_blind_spot "Row 63 is a 64-cell colour-9 bar that burns one cell at a time from the right. EIGHT cells are burned and the current frame shows them: columns 56 through 63 render 1, columns 0 through 55 render 9. The order was (63,63) at index 2 under key 2, (63,62) at 4 under key 4, then (63,61), (63,60), (63,59), (63,58), (63,57), (63,56) at indices 6, 8, 10, 12, 14, 16, every one under key 2. The ninth burn will land on (63,55). (63,55) has never changed in eighteen frames, so it is board, so it holds no instance, so NO EVENT IN THIS LANGUAGE CAN TOUCH IT -- recolored takes an object as its first argument and there is no object there. Therefore my manual predicts, and must predict, that the ninth press of ACTION2 burns nothing, and the world will burn (63,55) and the manual will be wrong by exactly one pixel. Then (63,55) becomes dynamic, the arm seats a Glyph9 on it, replay draws the burn retroactively, certify reports a perfect replay, and the cycle repeats on (63,54). THAT IS WHY certify SAYS THE REPLAY IS EXACT WHILE THE PROBE DESK SAYS THE MANUAL WAS WRONG: they ask about different times. Replay looks backwards through a census that already contains the burned cell; prediction looks forwards through one that cannot. All eight meter instances currently render 1, so meter_burn_key2_next has no grounding left and can only ever fire in replay. 56 cells remain unburned."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_meter_is_still_two_readings_and_seventeen_transitions_have_not_split_them "Eight burns: indices 2, 4, 6, 8, 10, 12, 14, 16 under keys 2, 4, 2, 2, 2, 2, 2, 2. Nine non-burns: indices 1, 3, 5, 7, 9, 11, 13, 15, 17 under keys 1, 3, 5, 5, 5, 5, 5, 5, 5. READING A says a burn happens iff the key is 2 or 4. READING B says a burn happens iff the command index is even. EVERY BURN IS AT AN EVEN INDEX AND UNDER KEY 2 OR 4; EVERY NON-BURN IS AT AN ODD INDEX AND UNDER KEY 1, 3 OR 5. Seventeen transitions and the two readings have not diverged once, because the arm has pressed keys 2 and 4 only at even indices and keys 1, 3 and 5 only at odd ones. This is not thin evidence, it is evidence spent on the wrong question, and four more transitions have now been spent on it. I encode reading A because it is the only one this grammar can express. THE NEXT COMMAND INDEX IS 18, WHICH IS EVEN, so ANY press of key 1, 3 or 5 separates them: reading A predicts no burn, reading B predicts (63,55) turns 1. THE SECOND-ORDER TRAP IS UNCHANGED: under reading B that burn is also undrawable by my manual, so the answer must be read off the RAW DIFF and not off whether a refutation fired. Reading B additionally implies the debt in the_probe_tier_rolls_my_state_forward_and_never_resyncs grows no matter what the arm presses, which makes this the most load-bearing unanswered question in the manual."
    [depends: meter_burn_key2_next, meter_burn_key4_next, the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: pending]

  theorem no_goal_section_and_the_exact_enumerated_reason "Kept and shortened, because the argument that now does the work is the transition-model one above. A goal may say count over a declared type, optionally filtered by colour, or an instance's pos equal to a landmark. The types carrying instances are Glyph9 with 43 cells -- 8 slot-1 ring pixels, 3 underline-1 pixels, the 24 spawn-ring pixels, 8 burned meter cells -- Vacated with the 24 pixels of the ring one lattice cell south, Spent with the 9 pixels of slot 2, and Dark with the 3 pixels of underline 2. EVERY INSTANCE I HAVE IS IN THE PANEL, ON THE SPAWN RING, ON THE RING ONE CELL SOUTH, OR ON THE METER, and none is within thirty rows of the socket. The pos form is dead for a separate reason: this world never MOVES anything, every rule in this manual is a recolour, no instance's pos has changed in eighteen states, so X.pos = landmark is a constant for every X I can declare. What unlocks the goal line is an OBSERVATION and not an edit."
    [depends: the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease, the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: passed]

  theorem the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught "Kept because it is the reason a whole earlier round was lost and because it generalises. The compiler refused the entire manual over one clause, a count over a type with zero instances, saying: this level declares no instance of that type, so the count is 0 on every state and the clause decides nothing. A COUNT OVER A TYPE WITH ZERO INSTANCES IS NOT A FALSE PREDICATE, IT IS A REFUSED CLAUSE. The general form: THE GOAL LANGUAGE CAN ONLY SPEAK ABOUT CELLS THAT HAVE ALREADY CHANGED, because only those carry instances -- the same wall as the burn frontier met from the other side. One consequence I record afresh this round because I considered redoing it: declaring a colour-8 type as INSURANCE, so that the first comb pixel to change would already have an owner, is tempting and I REJECT it. The declaration alone was accepted last time and only the count was refused, so the insurance probably compiles -- but probably is the wrong word to bet a round on when the two costs are wildly asymmetric. If I am right, I save one round of a responsibility warning; if I am wrong, I lose an entire round of every tier, which has now happened twice. An unexplained pixel is a defect the next desk repairs in one round. An uncompilable manual is a round nobody gets back."
    [depends: a_declaration_is_only_as_true_as_the_arm_can_seat_it  probe: passed]

  theorem dynamic_census "Exactly 79 cells have ever changed and every one has an owner. 23 are the panel: slot 1 at rows 1-3 columns 1-3 contributes its 8 ring pixels, its centre (2,2) rendering colour 0 in BOTH configurations and therefore board; underline 1 is row 5 columns 1-3, three cells; slot 2 at rows 1-3 columns 5-7 contributes all NINE cells, centre included, because (2,6) renders 1 in configuration A and 0 in B; underline 2 is row 5 columns 5-7, three cells. 24 are the spawn ring, rows 8-12 columns 14-18 minus the aperture (10,16), which has never changed and is board. 24 are the same ring six rows south, rows 14-18 columns 14-18 minus its aperture (16,16). 8 are the burned right end of row 63, columns 56 through 63. 23+24+24+8 = 79 = dynamic_cells exactly, and 4096-79 = 4017 = constant_cells exactly. By frame-0 colour: 43 colour-9 being 8 slot-1 ring plus 3 underline-1 plus 24 spawn ring plus 8 meter, 9 colour-1 being slot 2 solid in configuration A, 24 colour-5 being the lower ring which was floor at frame 0, and 3 colour-0 being underline 2 dark at frame 0. 43+9+24 = 76 = cells_needing_an_owner exactly. Every one of these four sums moved by exactly the two meter cells burned this round and by nothing else."
    [probe: passed]

  theorem the_cascade_length_reads_the_panel_and_it_is_now_seven_for_seven "ACTION2 pressed with the panel in configuration A returns SEVEN internal frames: t2, t8, t12, t16. Pressed in configuration B it returns NINE: t6, t10, t14. Seven presses, seven correct, no counterexample, and the configuration before each press is fixed by the alternation ACTION5 drives -- A at t2, B at t6, A at t8, B at t10, A at t12, B at t14, A at t16. All seven ACTION5 presses returned 9 frames regardless of configuration. THE NET DISPLACEMENT IS IDENTICAL IN ALL SEVEN ACTION2 PRESSES -- 49 cells changed each time, 24 out, 24 in, one burn, six rows south, one lattice cell -- so what the panel changes is the ANIMATION and not the distance, at least over open floor. My semantics say cascade single_frame, so I compare only the net and this costs me no replay accuracy; I record it as an observation my own semantics discard."
    [depends: key2_body_arrives  probe: passed]

  theorem the_panel_is_a_two_slot_mode_selector_and_the_mode_may_gate_terrain "The reading I hold, stated as a reading, re-read against the current frame. Two 3x3 tokens sit side by side at rows 1-3 columns 1-3 and columns 5-7, with a 3-cell underline beneath each at row 5. The underline of exactly one slot is lit colour 9 at any time and ACTION5 moves the light: configuration A lights underline 1, configuration B lights underline 2, and in seventeen transitions I have never seen both lit or neither. Right now the frame shows slot 1 as a hollow colour-2 ring, underline 1 dark, slot 2 as a hollow colour-9 ring with a dark centre, underline 2 lit -- configuration B. The token in the LIT slot is always drawn as a HOLLOW colour-9 ring with a dark centre, which is the shape of the body itself, a rigid block with a one-pixel aperture. The token in the unlit slot differs by slot: slot 1 unlit is a hollow colour-2 ring, slot 2 unlit is a SOLID colour-1 block with no aperture. So the panel says two avatars exist, this is the one you are driving, and the other one has a different shape -- and a solid avatar with no aperture could not show the socket pip through itself. Joined to the cascade finding at seven for seven I read the two slots as two modes of travel. THE PAYOFF IF THIS IS RIGHT IS THE WHOLE LEVEL: the sole route south is blocked by the comb at lattice (6,2), 23 of whose 25 pixels render colour 8, and if the modes differ in what terrain they cross then the comb is a mode problem and not a switch problem. THE PROBE IS EXACT AND CHEAP ONCE THE BODY IS SOUTH. I hold it at pending and note the competing reading honestly: 7 versus 9 frames could be nothing but two draw speeds."
    [depends: the_cascade_length_reads_the_panel_and_it_is_now_seven_for_seven, the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem action5_is_return_to_spawn_or_north_and_seventeen_transitions_cannot_split_them "ACTION5 has now been pressed SEVEN times, at t5, t7, t9, t11, t13, t15 and t17, and every single one was pressed from lattice (2,2) with the body one cell south of spawn, and every single one put the body back at (1,2). Reading NORTH says ACTION5 steps one lattice cell up. Reading RETURN says ACTION5 sends the body home from wherever it is. The body has stood in exactly two lattice cells in eighteen states and those two are adjacent, so the readings have made identical predictions on every frame ever observed and will keep doing so unless the body gets two cells from home. A third reading is observationally identical and changes the strategy: ACTION5 SWAPS which of two avatars you drive and the incoming avatar always starts at spawn. I tested the memory-preserving version of that against t7 specifically, because it is the transition that could refute it: if the swap preserved each avatar's position then the incoming avatar would already have been at (2,2), zero body cells would have changed and only 23 panel cells would have moved. 71 changed, and 71 changed again at t11, t15 and t17. So swap-with-memory is REFUTED four times over and swap-with-reset survives, indistinguishable from RETURN. THE SEPARATOR NEEDS THE BODY TWO CELLS FROM HOME, which needs the third lattice cell, which is the same purchase the goal line needs. THE STAKES: under RETURN, twelve of the last sixteen commands were a two-command loop that burned seven meter cells and moved the body nowhere."
    [depends: key5_body_respawns, key5_body_clears, the_loudest_forged_silence_is_not_at_spawn  probe: pending]

  theorem the_loop_ran_two_more_times_and_the_playbook_could_not_stop_it "Recorded as a process fact because a desk that hides this is useless. t14 A2, t15 A5, t16 A2, t17 A5. Body south, home, south, home. Panel B, A, B, A... and back to B. Two meter cells burned. Zero new mechanism. The previous playbook ranked ACTION3 first in capital letters, listed ACTION2 at spawn under WHAT NOT TO PRESS, and carried a hard prune against the cycle by name. None of it bound the ranker, for the second round running. So a prune in this playbook is a claim about what SHOULD be searched and not a filter that is enforced, and I will keep saying so rather than pretending otherwise. THE MECHANISM OF THE LOOP IS NOW FULLY UNDERSTOOD AND IT IS STRUCTURAL, NOT A TASTE: with no goal the plan tier cannot return sat, so the arm falls through to the probe tier, so the ranker chooses; the ranker scores by information gain; the manual's undrawable frontier cell guarantees ACTION2 a large constant gain; so ACTION2 is chosen; so a cell burns; so the frontier moves; so the guarantee renews. That is a fixed point with a proof, and the only exits are a goal the manual cannot write or a ranker that discounts a repeated-identical gain. The store's own numbers show the shape: 18 states, 16 distinct, and the only duplicates are the ancient sterile pair at s1 and s3 -- every later state is nominally distinct ONLY because the meter keeps ticking, which is the arm buying a new state label for one pixel a lap. ACTION3 and ACTION4 have each been pressed exactly once, both at a cell where east and west were void, and the east key remains unnamed after seventeen transitions."
    [depends: the_advance_prediction_cashed_and_the_artefact_is_now_established, the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease  probe: passed]

  theorem the_goal_i_still_cannot_write_is_the_real_one "The win is the body standing in lattice (8,7), rows 50-54 columns 44-48, its 24 ring pixels rendering 9 and its aperture showing the pip at (52,46). Re-verified against the current frame. Those 24 cells render constant colour 5, so they are board and hold no instance; and colour 5 is already claimed by Vacated while the arm looks types up by colour alone, so a second colour-5 type would be indistinguishable from Vacated and would claim cells twice, which is the constraint-5 error. The goal I could write over Vacated once the socket goes dynamic, count(Vacated, color = 9) = 24, is already true whenever the body stands in lattice (2,2), so it names two states and one of them is not a win. So the manual carries the true winning condition in prose, here and in the playbook, and carries NO goal line at all. That is a stated gap and not an evasion."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem the_burn_rules_want_one_rule_and_the_grammar_forbids_it "meter_burn_key2_rightmost and meter_burn_key2_next are ONE law -- burn the leftmost burned-adjacent colour-9 cell of the bar, where the right board edge counts as burned -- split into two rules because the guard language has and and not but no or, and the two conditions rightof(?p) = wall and colored(rightof(?p), 1) cannot be joined. They are exclusive rather than merely different: where rightof(?p) is off-board there is no cell to render 1, so the colour test is false, and where rightof(?p) is a real cell it is not wall. So constraint 5 holds by construction and the cost is one duplicated line. meter_burn_key4_next has the same body as meter_burn_key2_next with a different key; the key-4 twin of the RIGHTMOST rule has no witness and can never get one now that (63,63) is burned, so it is not written. Both surviving burn rules are UNGROUNDABLE going forward: all eight meter instances render 1, no Glyph9 instance renders 9 with a right neighbour rendering 1, and none will unless a future census extends the bar leftwards. They stay because they are what makes replay correct on t2 through t16."
    [depends: meter_burn_key2_rightmost, meter_burn_key2_next  probe: passed]

  theorem dark_may_have_no_instances "The one arithmetic gap in the census and I will not hide it. cells_needing_an_owner is 76 while dynamic_cells is 79, and the difference is precisely the three colour-0 cells of underline 2. Colour 0 is the background, and the arm instances every cell of a declared colour the board cannot explain; whether a dynamic cell whose frame-0 colour is the background counts as explained is not something I can settle from the brief. The indirect evidence is strong: replay has been reported exact across transitions that include t5 and t9 with key5_underline2_lights carrying coverage, and if Dark seated no instances that rule could not fire and each of those transitions would be wrong by three cells. I hold this as a probe that has passed indirectly while keeping the theorem, because the reasoning is inference from a check rather than a reading of the arm, and because that check is now two rounds stale."
    [depends: dynamic_census, the_two_rounds_i_lost_were_both_lost_at_my_own_desk  probe: passed]

  theorem the_spawn_probe_guard_is_carried_and_is_still_never_tested_negative "Thirteen panel rules carry colored(spawn_probe, 5), which reads cell (8,14) renders floor, which reads the body is not at home. In eighteen states that atom has SEVEN positive witnesses -- t5, t7, t9, t11, t13, t15, t17, every one an ACTION5 pressed with the body away -- and ZERO negative witnesses, because ACTION5 has never once been pressed with the body at home. So the guard is doing no work I can demonstrate. Why keep it? Because it changes no prediction today and I can show that cell by cell: with the panel in configuration B, slot 1 renders 2, underline 1 renders 0, slot 2 renders 9 and underline 2 renders 9, so the eight forward rules are blocked by their colour tests whatever the body does; and the five reverse rules WOULD fire on exactly those colours, so with the body at home the guard is the ONLY thing blocking them. That is precisely the untested case, and the panel is in configuration B right now. IF ACTION5 IS PRESSED AT SPAWN AND THE PANEL TOGGLES, THIS GUARD IS WRONG IN THIRTEEN RULES AT ONCE. The body is at spawn right now. That is a large, free, unclaimed bit that has been available for four rounds."
    [depends: key5_slot1_lights, key5_slot1_dims  probe: pending]

  theorem the_action_map_after_seventeen_transitions "WITNESSED. ACTION2 is SOUTH: seven times, t2, t6, t8, t10, t12, t14, t16, six rows south, one lattice cell, 48 cells each. ACTION5 puts the body at spawn from one cell south: seven times, t5, t7, t9, t11, t13, t15, t17 -- see action5_is_return_to_spawn_or_north for why that is not the same as knowing it is north. NEGATIVE INFORMATION, read off the map rather than off a rule. At spawn, lattice (1,2), north is void because rows 2-6 columns 14-18 render 0, west is void because columns 8-12 render 0, EAST is open floor because rows 8-12 columns 20-24 all render 5, and SOUTH is open. ACTION1 was pressed there at t1 and nothing changed, so ACTION1 IS NEITHER EAST NOR SOUTH. At lattice (2,2), rows 14-18, north was open and south was open because rows 20-24 columns 13-31 are floor, while east and west are void because rows 14-18 columns 20-24 and columns 8-12 render 0. ACTION3 at t3 and ACTION4 at t4 each moved nothing, so NEITHER IS NORTH AND NEITHER IS SOUTH. Combine: ACTION2 is south; ACTION1 is not east and not south; ACTION3 and ACTION4 are each west, or east-blocked-nowhere, and each remains compatible with east because east has never been open under either. EAST IS ACTION3 OR ACTION4 AND THERE IS NO THIRD CANDIDATE. SEVENTEEN COMMANDS SPENT AND NOT ONE HAS TESTED THE EAST KEY, at a cell where east is four unbroken lattice cells of floor leading to the knob."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the five keys at spawn, where the body now stands. key(2) moves 48 body cells and burns one meter cell it cannot draw: witnessed seven times. key(1) inert: WITNESSED, t1, zero cells changed. key(3) inert at spawn: NO WITNESS -- pressed once, at t3, from one cell south, where east and west were both void. key(4) inert at spawn: NO WITNESS -- pressed once, at t4, from one cell south, where it burned a meter cell and moved nothing. key(5) inert at spawn: NO WITNESS AT ALL in eighteen states; all seven presses were from one cell south. THREE OF FIVE SILENCES AT SPAWN ARE FORGED DEATH CERTIFICATES; two of the three are the east candidates and the third is the one that would refute thirteen rules' shared guard. Add the fourth and largest, at the other cell, in the_loudest_forged_silence_is_not_at_spawn. This is the entire argument for the next command and against pressing ACTION2 or ACTION5 from the loop again."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_action_map_after_seventeen_transitions  probe: passed]

  theorem the_two_no_op_rules_fail_the_gain_test_and_i_say_so "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has exactly one witness, and each witnesses a transition on which zero cells changed. The manual would replay identically without them: constraint 3 is failed outright and I am not going to dress it up. The reason I keep them is smaller than the rule text: they put key(1) and key(3) into the manual's action alphabet, which is what certify's ambiguity check adjudicates over -- it reported 5 actions and 70 pairs, and without these two it would have reported 3. Deleting them removes information I can see for a saving I cannot measure. They change no prediction, so keeping them cannot cost a pixel, and they are the two cheapest deletions in this manual if a later desk wants them gone."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "key2_body_leaves grounds on meter instances at row 63 whose sixth-below is row 69, and it must not fire there. It does not, because a colour test on an off-board cell is FALSE rather than an exception, and <cell> = wall is the sanctioned positive test. Every row and column discrimination in the eight forward panel rules is built from that one fact: the k-th above is off-board exactly when k exceeds the row, so panel row 1 is above-twice equals wall; row 3 is a colour test on above-twice, false for row 1 precisely because a colour test on an off-board cell is false; row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column -- column 5 is leftof-six equals wall, column 6 is leftof-seven equals wall with a colour test on leftof-once, column 7 is a colour test on leftof-twice -- and those three are pairwise exclusive, which is what keeps constraint 5 satisfied on (2,5), (2,6) and (2,7). I re-checked the case that looks dangerous: leftof-seven from column 5 is also off-board, so centre_darkens and row2_left_lights are separated NOT by that atom but by colored(leftof(?s), 1), which is false at column 5 because (2,4) is a separator rendering 0. It also protects meter_burn_key2_rightmost from meter_burn_key2_next. Not one rule uses not, deliberately."
    [depends: key5_slot2_centre_darkens, key2_body_leaves  probe: passed]

  theorem the_reverse_toggle_needs_only_a_colour_test_and_i_checked_every_clash "The five return rules are far shorter than the eight forward ones, because configuration B assigns a UNIQUE colour to each panel group within each declared type, which configuration A does not. In B with the body away: Glyph9 renders 2 on slot 1, 8 cells, and 0 on underline 1, 3 cells, and 5 on the spawn ring and 1 on the meter; Spent renders 9 on the slot-2 ring, 8 cells, and 0 on the slot-2 centre, 1 cell; Dark renders 9 on underline 2, 3 cells. So a bare colour test names each group exactly. I re-audited constraint 5 pair by pair with EIGHT meter cells burned, which is the case that could newly clash: all eight meter Glyph9 instances render 1, and colour 1 is claimed by no key-5 rule at all, so the meter cannot be swept into a panel rule. Colour 2 is claimed only by key5_slot1_lights. Colour 0 on a Glyph9 is claimed only by key5_underline1_lights and no other Glyph9 ever renders 0. key5_slot2_ring_resets takes Spent at 9 while all four forward slot-2 rules take Spent at 1: disjoint. key5_slot2_centre_resets takes Spent at 0, claimed by nothing else. key5_underline2_dims takes Dark at 9 while key5_underline2_lights takes Dark at 0: disjoint. In configuration A none of the five can fire; in configuration B none of the eight forward rules can fire. The two directions are separated by the frame itself, which is why no phase counter is needed."
    [depends: key5_slot1_lights, key5_underline2_dims  probe: passed]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "cascade_lengths are 1, 7 and 9. Every no-op returned one frame; ACTION2 returned 7 or 9 depending on the panel; ACTION5 returned 9 every time. A move is animated one row per internal frame and the world reports the whole animation for a single action; cascade single_frame compares only the net, so up to eight intermediate frames per command are discarded unread, and I record that as a limitation of my own semantics rather than of the world. The refutation I keep, now with seven witnesses: under a slide-until-blocked reading, ACTION2 at spawn would run the body south through rows 20-24 and 26-30 to the comb. It stopped after exactly six rows over open floor at t2, t6, t8, t10, t12, t14 and t16. ONE PRESS IS ONE LATTICE CELL, and every distance in the playbook rests on it."
    [depends: key2_body_arrives  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2 through 6R+6 by columns 6C+2 through 6C+6; rows and columns congruent to 1 modulo 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. Row 7 is floor from column 13 to column 43. R=1, rows 8-12, is floor from column 13 to column 43 except the knob block, so C=2,3,4,5 are open and C=6 holds the knob. R=2, rows 14-18, is floor at columns 13-19 and 25-31 only, so C=2 and C=4. R=3, rows 20-24, is floor from column 13 to column 31, so C=2,3,4. R=4 and R=5 are floor only at columns 13-19, so C=2. R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable. R=7 is C=2, plus a fragment of floor at row 48 columns 42-50 that is one row deep and cannot hold a body. R=8, rows 50-54, is floor from column 13 to column 48, so C=2 through C=7 are open. Separator rows 7, 13, 19, 25, 31, 37, 43 and 49 are floor across column 2 and separator column 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in eighteen frames the body has occupied exactly TWO cells, (1,2) and (2,2)."
    [depends: the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed seven times, t2, t6, t8, t10, t12, t14 and t16: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 columns 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 columns 43-49, row 55 columns 43-49, column 49 rows 49-55. Rows 49 and 55 are separator rows and columns 49 and 43 are separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted in colour 9, with the west wall at column 43 left as FLOOR for rows 50-54. Inside it, rows 50-54 columns 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, column 50 rows 49-56 is a one-cell strip of floor that leads nowhere. Overlay the body standing in lattice (8,7), 5x5 with an aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate: the game is won when the 24 ring pixels of rows 50-54 columns 44-48 render 9. The bracket has never changed in eighteen frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally write a real goal line."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2), (1,3), (1,4), (1,5), (2,2), (2,4), (3,2), (3,3), (3,4), (4,2), (5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 columns 39-41, a stem pixel at (12,40), colour 8 filling column 40 from row 12 down to row 40, colour 8 filling row 40 from column 14 to column 40, and the comb teeth at rows 38-42 columns 14-18, which hold 23 colour-8 pixels and 2 colour-5 pixels at (39,14) and (41,14). It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Note also that the descending wire at column 40 is flanked by floor at columns 39 and 41 through the void rows, which is drawn deliberately and which I do not yet understand. Not one colour-8 pixel has moved in eighteen frames. The first colour-8 pixel that changes turns this theorem into physics AND makes a goal line writable in the same instant."
    [depends: the_maze_is_a_six_pixel_lattice, the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 columns 32-36, is fully open floor and is separated from the knob's cell (1,6) at columns 38-42 only by separator column 37, which renders floor through rows 8-12. Lattice (1,6) contains ten colour-8 pixels, nine of them non-centre pixels of that cell -- the eight knob pixels other than its centre (10,40), plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while colour 8 is solid. Either colour 8 is walkable in one of the two panel modes, and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Seventeen commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens, the_panel_is_a_two_slot_mode_selector_and_the_mode_may_gate_terrain  probe: pending]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because it is the permanent shape of every refutation this level will produce, and this round it bit three times: the burn frontier, the refused goal, and the twenty-four cells of lattice (3,2) that make the loudest forged silence undrawable. To draw the next burn, or the first step onto fresh ground, or the socket, or to COUNT the comb, I would need an instance on a board cell. The arm offers exactly one lever, arc-instances all, and its documented behaviour is to instance every cell of that colour THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance, and the compiler will not let a clause count a type whose instance set is empty. I considered and REJECT the two workarounds again. First, a second declared type on colour 9 without arc-instances: the arm looks types up by colour and nothing else, so it is indistinguishable from Glyph9, its seat is unspecified, and any cell it landed on would be claimed twice. Second, dropping the board declaration so that every cell of every declared colour is instanced: that would in principle predict burns and fresh ground, and I traced it through the guards before rejecting it -- key2_body_leaves would then ground on the socket bracket at (49,49), whose sixth-below (55,49) renders 5, and would recolour a wall on every ACTION2, and every guard in this manual was written for a dynamic-only census so a full census needs all twenty-two rules rewritten in one round with no witnesses. So the manual heals ONE STEP BEHIND the world, permanently, and the correct way to read a refutation here is by its divergence set: where that set lies on cells that had never changed before the transition, the manual is not implicated."
    [depends: dynamic_census, the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_parity_and_cannot_say_or "Five expressive holes, unchanged in substance and sharper in consequence. FIRST: there is no third outcome for a state-action pair -- not no change and not a named successor, but unobserved, the manual declines to predict. Rules produce events, absence of a rule produces identity, and the compiled step is total. So the three unwitnessed spawn silences and the one at lattice (2,2) are asserted in the same voice as the two witnessed ones, and the probe ranker cannot tell them apart. SECOND: if the meter runs on command parity, that law CANNOT be written here at any length, because the guard language reads pixels and the action name and there is no command counter and no phase pixel. THIRD: there is no or, which is why one burn law is two rules. FOURTH: THERE IS NO WAY TO SAY THAT A PIXEL WILL CHANGE WITHOUT NAMING AN OBJECT THAT OWNS IT, so a manual can never predict the frontier of its own knowledge. FIFTH: A GOAL CANNOT NAME A CELL THAT HAS NEVER CHANGED, for the same instancing reason, so the winning condition of this level is unwritable until the body or the gate first disturbs it. If a future desk gains one expressive extension, ask for instancing on constant cells first -- it repairs the fourth and fifth holes at once -- then a state counter, then or, then not."
    [depends: the_meter_is_still_two_readings_and_seventeen_transitions_have_not_split_them, the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1 through ACTION5 plus RESET; the alphabet is ACTION1 through ACTION7. Two commands are entirely unconstrained after eighteen states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels changing colour, and never its precondition. Recording that effect is also what would make a goal line writable, since it is the event that turns comb cells dynamic. I note the countervailing risk plainly: actions_used lists only the five that have been tried, so it is no evidence that 6 and 7 exist, and a press of a non-existent action may buy a wasted command."
    [depends: no_goal_section_and_the_exact_enumerated_reason  probe: pending]

  theorem a_declaration_is_only_as_true_as_the_arm_can_seat_it "Kept and extended, because it has now cost three rounds running in three different ways. First a landmark whose arc-cell comment was missing, which is a hard compile error; spawn_probe at (8,14) was the repair and it held. Then a type the arm could seat nowhere, where the arm accepted the DECLARATION and refused the COUNT. Then a reply that carried no theory block at all. THE GENERAL RULE, now stated to cover all three: before writing any clause, ask what the arm will seat for it, and if the answer is nothing, the clause is not conservative, it is fatal -- and before sending anything, ask whether the harness will read it at all, because a clause the harness never sees is not conservative either."
    [depends: the_two_rounds_i_lost_were_both_lost_at_my_own_desk  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on the split-by-colour variant, minus 74754 bits over 47 tracks, and a POSITIVE gain of 3442 bits on the 12-track variant against a 13592-bit baseline, a 25 percent saving, which I take as corroboration rather than as structure. What I take is corroboration by FRAME INDEX, independent of my rules. obj1: colour 1, nine cells, 3x3, present 5 of 18 frames -- slot 2 solid, alive in configuration A. obj5 colour 2 first frame 5, obj6 colour 1 first frame 7, obj7 colour 2 first frame 9, obj8 colour 1 first frame 11, obj9 colour 2 first frame 13, obj10 colour 1 first frame 15, obj11 colour 2 first frame 17: that is the panel alternating exactly on the odd indices where ACTION5 was pressed, SEVEN flips, an independent witness for both toggle directions and for the fact that the last two rounds bought nothing but more of the same. obj0: colour 9, eight cells, 3x3, present all 18 -- the lit token. obj4 is the whole 64-cell bar of which 8 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. cegis_miner refuses every track and its verdict, the world does not narrate as one mover, is true of the arm and false of the world -- there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours. zero_space self-reports THIN in its own words: 17 transitions constrain rank 9 of 395 features, null space dimension 386, nearly every vector in it a law true over these states and unfalsified rather than confirmed. Its single global law is my census and nothing more. Nothing in the candidate stream proposes anything about colour 8, which is consistent with colour 8 never having changed."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me, and the previous edition cashed in full. STATE: the body is at spawn, lattice (1,2). The panel is in configuration B -- slot 1 a hollow colour-2 ring, underline 1 dark, slot 2 a hollow colour-9 ring, underline 2 lit. EIGHT meter cells are burned, columns 56 through 63; 56 remain. The next command index is 18, which is EVEN. PREDICTIONS. ACTION2 at spawn: 48 body pixels drawn correctly, ZERO meter pixels drawn, the world burns (63,55), the manual is refuted by exactly one cell, the information gain comes back as 5.087463 and NOTHING IS LEARNED; if that number differs, the artefact reading is dead and I want to know. ACTION5 at spawn: predicted identity by all thirteen guarded rules, and if the panel toggles instead then colored(spawn_probe, 5) is wrong in thirteen rules at once, which is the largest single refutation available on this board and costs no meter cell. ACTION3 at spawn: predicted ZERO cells changed, with NO witness for that silence at this cell. If the body steps east I pay 48 pixels I have priced -- 24 arrival pixels on rows 8-12 columns 20-24 which have never changed and hold no instance, and 24 departure pixels which do hold Glyph9 instances but which no witnessed east-leaves rule can fire on. If it does not step, ACTION4 is east by elimination. EITHER WAY, since index 18 is even and key 3 is neither 2 nor 4: if (63,55) burns, reading A of the meter is DEAD and reading B is confirmed by the first discriminating transition in eighteen; if it does not burn, reading A survives its first real test. ACTION2 pressed one cell SOUTH of spawn: predicted identity, and I expect that to be WRONG by 48 pixels with the body landing in lattice (3,2) -- the third lattice cell ever occupied, which seats 24 new instances and extends the transition model past the loop for the first time. ACTION1 at spawn: predicted identity, witnessed at t1, buys nothing. ACTION6 or ACTION7: entirely unconstrained, and one of them may be the click that presses the knob and thereby writes my goal line for me, or may not exist at all."
    [depends: the_action_map_after_seventeen_transitions, the_meter_is_still_two_readings_and_seventeen_transitions_have_not_split_them, the_loudest_forged_silence_is_not_at_spawn  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Eighteen states, seventeen transitions:
#   RESET, A1 A2 A3 A4 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5.
#   t1  A1 at spawn        -> nothing
#   t2  A2 at spawn        -> body one lattice cell SOUTH (48) + burn (63,63)
#   t3  A3 one cell south  -> nothing (east and west both void there)
#   t4  A4 one cell south  -> burn (63,62) and nothing else
#   t5  A5 one cell south  -> body to spawn (48) + panel A->B (23)
#   t6..t17  the same two commands, six more times, alternating.
#   Burns since: (63,61) (63,60) (63,59) (63,58) (63,57) (63,56).
# BODY AT SPAWN, lattice (1,2). PANEL IN CONFIGURATION B. EIGHT meter cells
# burned, columns 56-63; 56 remain. Next command index is 18, EVEN.
#
# ========= WHAT HAPPENED THIS ROUND =========
# Two more laps. Two more burns, exactly the two the manual named in advance.
# Information gains came back at 5.087463 for action 2 (twice) and 3.5025 for
# action 5 (twice) -- to six decimals, for the fifth time, across different
# states, different meter counts and both panel configurations.
#   A REPEATED-IDENTICAL INFORMATION GAIN IS ZERO INFORMATION.
# And the reply carried no theory block, so nothing was installed and certify
# is reporting 13/13 over a 14-state snapshot of a world that has 18 states.
# Read none of certify's numbers as coverage of t14-t17.
#
# ========= heuristic_miss, ANSWERED PROPERLY THIS TIME =========
# The surprise says declaring the winning condition is the highest-value edit
# available. TESTED AND FALSE ON THIS BOARD, for an arithmetic reason:
#
#   THE PLAN TIER REACHES A GOAL BY SEARCHING MY COMPILED RULES, AND MY RULES
#   CAN ONLY REACH TWO LATTICE CELLS AND TWO PANEL CONFIGURATIONS.
#
# So the only goal that could ever return sat is one satisfied inside the very
# loop that has consumed twelve of seventeen commands, and sat-inside-the-loop
# is worse than unsat: unsat leaves the arm probing, sat makes it commit and
# declare success one lattice cell from spawn. I checked every candidate the
# grammar admits over the four types that carry instances and all four fail:
# count(Glyph9,color=5)=24 and count(Vacated,color=9)=24 both just mean "body
# is off spawn"; count(Glyph9,color=1)=64 exceeds the 43 instances that exist;
# count(Spent)=0 is constant-false.
#
#   THE GOAL IS NOT THE BOTTLENECK. THE MISSING TRANSITION IS.
#   ONE OBSERVATION FIXES BOTH: THE BODY IN A THIRD LATTICE CELL.
#   That seats instances on 24 cells that have never changed, extends the
#   transition model past the loop, and is the first step of the only route
#   to a writable goal. Everything below is ranked by proximity to it.
#
# THE WIN, carried in prose because the DSL cannot hold it:
#   WIN = the body stands in lattice (8,7), rows 50-54 columns 44-48, so its
#   24 ring pixels render 9 and its aperture shows the pip at (52,46). Drawn
#   as three colour-9 walls with the west side open: a socket cut to the body.
#   ROUTE = lattice column 2 is the only north-south corridor and the comb at
#   (6,2) blocks it, 23 of its 25 pixels colour 8. The comb is wired by one
#   connected colour-8 line to a 3x3 knob at lattice (1,6), reachable
#   eastward along R=1 from spawn through (1,3), (1,4), (1,5), all open floor,
#   and (1,5) is separated from the knob's cell only by separator column 37,
#   which is floor.
#
# ========= WHY THE ARM KEEPS BUYING THE SAME LAP, WITH THE PROOF =========
#   no goal -> plan cannot return sat -> the probe tier chooses
#   -> the ranker scores by information gain
#   -> the next burn always lands on a never-changed cell, which no manual in
#      this language can own, so action 2 is guaranteed a large CONSTANT gain
#   -> action 2 is bought -> a cell burns -> the frontier moves
#   -> the guarantee renews.
# That is a fixed point with a proof, not bad luck and not a taste a prune can
# argue with. I have NOT gamed the ranker back: the lever that would work is
# an unwitnessed rule making some other key predict 48 pixels, and constraint
# 2 forbids it.
#
# ========= NEW THIS ROUND: THE DEBT IS CUMULATIVE =========
# Action 5 has NO undrawable cell in it -- all 71 changed pixels at t15 and
# t17 are instanced and each is fired by exactly one rule -- yet action 5 was
# refuted twice. The reading that fits is that the probe predicts from the
# MANUAL'S OWN rolled-forward state, which already carries the burn it could
# not draw. If so the manual is behind forever once it misses one pixel, and
# EVERY command will look refuted whatever it is.
#   MITIGATION, and it is free: under reading A of the meter the debt only
#   grows on keys 2 and 4, so any command that is not key 2 or 4 adds none.
#   Under reading B it grows anyway -- and a non-burning key at an even index
#   is exactly the experiment that tells the readings apart. SAME COMMAND
#   EITHER WAY.
#
# ========= THE ONE THING WORTH BUYING, AND IT PAYS FOUR TIMES =========
# THE EAST KEY, TESTED AT SPAWN. ACTION3 first, ACTION4 only if 3 is inert.
#   1. IT NAMES A DIRECTION WHICHEVER WAY IT ANSWERS. A2 is south, seven
#      witnesses. A5 returns to spawn, seven witnesses. A1 was pressed AT
#      SPAWN with east OPEN and moved nothing, so A1 is not east. EAST IS A3
#      OR A4 and there is no third candidate. Both were pressed once, both
#      from one cell south where east AND west are void, so neither press
#      could answer anything.
#   2. IT SPLITS THE METER. Eight burns at even indices under keys 2 and 4;
#      nine non-burns at odd indices under keys 1, 3 and 5. Index 18 is EVEN
#      and key 3 is neither 2 nor 4: reading A predicts no burn, reading B
#      predicts (63,55) turns 1. READ IT OFF THE RAW DIFF, NOT OFF A
#      REFUTATION FLAG -- under B the burn is undrawable anyway.
#   3. IT KILLS A FORGED SILENCE. The manual predicts zero cells changed and
#      has no witness for it; three of five spawn silences are forged this way.
#   4. IT IS STEP ONE OF THE ONLY ROUTE TO THE KNOB, four lattice cells east
#      along a row that is open floor the whole way, and a third lattice cell
#      is what makes a goal writable at all.
#
# ========= SECOND: TEST THE SHARED GUARD WHERE IT HAS NEVER BEEN FALSE ====
#   Thirteen rules carry colored(spawn_probe, 5) -- the body is not at home.
#   Seven positive witnesses, ZERO negatives, because A5 has never been
#   pressed with the body at home. The body is at home now and the panel is in
#   configuration B, which is exactly the configuration in which the five
#   reverse rules would fire if the guard were not blocking them. The manual
#   predicts identity. If the panel toggles anyway, thirteen rules are wrong
#   at once. Free, and unclaimed for four rounds.
#
# ========= THIRD: THE FOURTH AND LARGEST FORGED SILENCE =========
#   The manual predicts that ACTION2 pressed ONE CELL SOUTH of spawn does
#   NOTHING -- because no Glyph9 renders 9 there and no Vacated renders 5.
#   That is almost certainly false: rows 20-24 are floor from column 13 to
#   column 31, and one press of A2 has moved the body exactly one lattice
#   cell south seven times running. The body has stood on that cell seven
#   times and nobody has ever tried it. It is the ONE command I can name that
#   is likely to put the body in a lattice cell it has never occupied, and it
#   is also the first half of the separator between "A5 is north" and "A5 is
#   return to spawn". It is ranked third only because it costs a meter cell
#   and needs the body moved south first.
#
# ========= FOURTH: ACTION6 OR ACTION7 =========
#   Never pressed, entirely unconstrained. In this family one is usually a
#   click, and the knob is a 3x3 target the body appears unable to stand on.
#   My manual can record such a command's EFFECT and never its precondition --
#   but the effect is exactly what makes the comb dynamic and the goal
#   writable. Countervailing risk stated honestly: actions_used lists only
#   what has been tried, so it is no evidence these exist.
#
# ========= WHAT NOT TO PRESS, AND WHY IT WILL LOOK TEMPTING =========
#   A2 at spawn: it will score 5.087463 expected bits and buy NOTHING. The 48
#   body pixels are drawn correctly seven times over; the only divergent cell
#   is (63,55), which no manual in this language can draw. Guaranteed
#   refutation, guaranteed wasted round, one more burned meter cell, and one
#   more unit of permanent prediction debt.
#   A5 from one cell south is pure loop; A5 from spawn is the exception and is
#   ranked second above.
#   A1 at spawn: witnessed inert at t1.
#   A4 at spawn: the same experiment as A3 with the labels swapped, but it
#   spends a meter cell under BOTH meter readings -- press it only if A3 is
#   inert.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The next burn cell is undrawable: one pixel per press of key 2 or 4,
#     forever. A refutation whose divergence set is exactly that cell
#     implicates nothing.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on cells that have never changed, and 24 departure pixels for
#     which no rule in that direction is witnessed. 24 for the second step in
#     the same direction, 0 after that.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.
#
# ========= A NOTE ON THIS DESK =========
#   Two rounds running were lost at my own desk -- one to an uncompilable
#   clause, one to a reply that omitted the theory block. A mediocre manual
#   that compiles beats an excellent one that does not by an unbounded margin.
#   Emit all three blocks first, then worry about the content.

order     settle_the_east_key_before_anything_else_at_this_cell             [proof: lean]
order     buy_a_third_lattice_cell_before_attempting_to_write_a_goal        [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language    [proof: lean]
order     treat_a_repeated_identical_information_gain_as_zero_gain          [proof: lean]
order     discount_any_gain_that_comes_from_a_cell_with_no_instance         [proof: lean]
order     prefer_a_command_that_closes_three_open_questions_over_one        [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     break_a_repeating_command_cycle_before_optimising_within_it       [proof: lean]
order     test_a_shared_guard_where_it_has_never_been_false                 [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation       [proof: lean]
order     prefer_a_key_that_adds_no_new_prediction_debt                     [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal      [proof: lean]
order     spend_a_meter_cell_only_on_a_question_it_actually_closes          [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     goal_clause_over_a_type_with_zero_instances => dead                    [proof: lean]
prune     goal_that_becomes_true_at_a_state_that_is_not_a_win => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_cells_already_visited => dead [proof: lean]
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

heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic rules_sharing_a_guard_that_one_command_could_refute_together      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic prediction_debt_a_command_would_add_to_the_rolled_forward_state   [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                   [admissible: lean]

prefer    a_command_that_would_put_the_body_in_a_lattice_cell_never_occupied [ev: 2/11 reachable cells seen]
prefer    a_command_that_would_turn_a_machinery_pixel_dynamic                [ev: 0/18 states]
prefer    a_key_that_names_a_direction_whichever_way_it_answers              [ev: 2/2 candidates]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index          [ev: 17/17 transitions tie]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed      [ev: 3/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on               [ev: 3/5 keys at spawn]
prefer    a_command_that_leaves_the_cycle_the_last_twelve_commands_formed    [ev: 12/16 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 17/17 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    a_free_probe_over_one_that_costs_a_meter_cell                      [ev: 8/17 commands burned]
```

=== LOG ===
```json
[
  {"id": "E-01", "subject": "the reply that carried no === THEORY === block", "verdict": "reject",
   "why": "This is my desk's own failure, not the DSL's: I wanted to install an updated manual and instead emitted a malformed reply, so nothing reached the compiler, nothing was installed, and certify is still reporting 13/13 over the 14-state snapshot while the world has 18 states. Recorded in the manual as the_two_rounds_i_lost_were_both_lost_at_my_own_desk; the operational rule I wrote instead is 'emit all three blocks first, then worry about content', carried into the playbook as order emit_every_required_block_before_polishing_any_of_them."},

  {"id": "O-01", "subject": "obj0/obj2/obj4 (colour 9 tracks)", "verdict": "accept",
   "as": "Glyph9, arc-instances all, now 43 instances",
   "why": "The census moved from 41 to 43 because (63,57) and (63,56) burned at t14 and t16 and are now dynamic; 8 slot-1 ring + 3 underline-1 + 24 spawn ring + 8 meter = 43, and 43 + 9 Spent + 24 Vacated = 76 = cells_needing_an_owner exactly."},

  {"id": "O-02", "subject": "the colour-5 dynamic cells one lattice cell south of spawn", "verdict": "accept",
   "as": "Vacated, 24 instances, unchanged",
   "why": "rows 14-18 cols 14-18 minus the aperture (16,16), which has never changed in 18 frames and is therefore board."},

  {"id": "O-03", "subject": "obj1/obj6/obj8/obj10 (colour 1, 3x3, first frames 0,7,11,15)", "verdict": "accept",
   "as": "Spent, 9 instances",
   "why": "The engine's own first-frame indices 7, 11, 15 are exactly the odd indices at which ACTION5 toggled the panel to configuration A, an independent witness for the reverse toggle that does not go through any of my rules."},

  {"id": "O-04", "subject": "obj5/obj7/obj9/obj11 (colour 2, 3x3, first frames 5,9,13,17)", "verdict": "entailed",
   "why": "Already owned as the unlit slot-1 ring inside Glyph9; the four first-frame indices 5, 9, 13, 17 are exactly the ACTION5 presses that produced configuration B, corroborating key5_slot1_dims at four witnesses rather than three."},

  {"id": "O-05", "subject": "obj3 (1006-cell colour-null blob)", "verdict": "reject",
   "why": "connected_components(4) merged the maze floor with the body ring because the body is floor-adjacent everywhere; accepting it would give one object that owns 1006 cells of which 950-odd never change, failing constraint 3 outright. Its ABSENCE of a mover track is the finding, not its presence."},

  {"id": "O-06", "subject": "a colour-8 type declared as responsibility insurance for the comb", "verdict": "reject",
   "why": "It would seat zero instances today, so it buys nothing measurable now and only pays if a comb pixel changes; the compiler has already refused this manual once over a zero-instance type, and losing a whole round to a compile refusal is far more expensive than one round of an unexplained-pixel warning, which the next desk repairs in one edit. Reasoning recorded in the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught."},

  {"id": "O-07", "subject": "a second colour-9 type to model the body as one moving object", "verdict": "reject",
   "why": "The arm looks types up by colour alone, so a second colour-9 type is indistinguishable from Glyph9, its seat is unspecified, and every cell it landed on would be claimed twice -- the constraint-5 error. This is why the world's one genuine mover is modelled as 48 recolours and why no pos-based goal exists."},

  {"id": "R-01", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept",
   "why": "Extended to t14 and t16, coverage 168/168 each (24 cells x 7 presses); the 48 body pixels of both new transitions are drawn exactly and the only divergent cell at t14 and t16 is the meter frontier."},

  {"id": "R-02", "subject": "key5_body_clears / key5_body_respawns", "verdict": "accept",
   "why": "Extended to t15 and t17, coverage 168/168 each; the 48 body pixels of both new ACTION5 transitions are drawn exactly."},

  {"id": "R-03", "subject": "the eight forward panel rules (A -> B)", "verdict": "accept",
   "why": "Extended to t17, so ev is t5,t9,t13,t17 and coverages rise to 32/32, 12/12, 12/12, 12/12, 4/4, 4/4, 4/4, 12/12 -- summing to the 23 panel cells exactly, matching the 71 = 48 + 23 reported at t17."},

  {"id": "R-04", "subject": "the five reverse panel rules (B -> A)", "verdict": "accept",
   "why": "Extended to t15, so ev is t7,t11,t15 and coverages rise to 24/24, 9/9, 24/24, 3/3, 9/9 -- again 23 cells exactly, matching t15."},

  {"id": "R-05", "subject": "meter_burn_key2_next", "verdict": "accept",
   "why": "Extended to t14 and t16 at 6/6: on replay (63,57) and (63,56) are dynamic and carry Glyph9 instances, so the rule draws both burns retroactively even though it could not predict either. Going forward it is ungroundable, since all eight meter instances now render 1."},

  {"id": "R-06", "subject": "a rule predicting the next meter burn", "verdict": "reject",
   "why": "The next burn lands on (63,55), which has never changed, so it is board, so it holds no instance, and recolored takes an object as its first argument. No rule of any length can fire there. Refusing to install one is the honest answer to P-09 and P-11."},

  {"id": "R-07", "subject": "a rule making ACTION2 move the body from lattice (2,2) to (3,2)", "verdict": "reject",
   "why": "It would have to recolour rows 20-24 cols 14-18, twenty-four cells that have never changed and hold no instance, so the rule could not fire even if written -- and there is no witness for the transition either, which constraint 2 forbids twice over. Carried instead as theorem the_loudest_forged_silence_is_not_at_spawn with the price advertised."},

  {"id": "R-08", "subject": "an unwitnessed rule making some quiet key predict 48 pixels, to move the ranker", "verdict": "reject",
   "why": "It is the one lever that would break the ACTION2 fixed point and it is exactly what constraint 2 forbids; a manual that games its own ranker can be checked by nothing. Refused for the second round running and stated in the manual rather than hidden."},

  {"id": "R-09", "subject": "key1_inert_at_spawn and key3_inert_below_spawn", "verdict": "accept",
   "why": "Both fail the gain test and I say so: each recolours a pixel to the colour it already has and replay is identical without them. Kept only because they put keys 1 and 3 into the alphabet the ambiguity check adjudicates over (5 actions, 70 pairs, no clashes), and they are the two cheapest deletions available."},

  {"id": "L-01", "subject": "dynamic_census", "verdict": "accept",
   "why": "Re-derived: 23 panel + 24 spawn ring + 24 lower ring + 8 meter = 79 = dynamic_cells, and 4096 - 79 = 4017 = constant_cells, both exact against the store; every sum moved by exactly the two cells burned this round."},

  {"id": "L-02", "subject": "the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease", "verdict": "accept",
   "why": "New and it is my answer to heuristic_miss: the plan tier reaches a goal by searching my compiled rules, my rules reach only two lattice cells and two panel configurations, so any goal that could return sat is satisfied inside the loop -- and sat-inside-the-loop is worse than unsat because it makes the arm commit and declare success one cell from spawn. I enumerated all four candidates the grammar admits over the four instanced types and each fails by name."},

  {"id": "L-03", "subject": "the goal section", "verdict": "reject",
   "why": "Third refusal, on a new and stronger ground than the previous two. No goal is emitted; the winning condition is carried in prose in the_socket_is_a_keyhole_and_names_the_winning_position and in the playbook header, and the exact observation that would make a sound goal writable is named."},

  {"id": "L-04", "subject": "the_advance_prediction_cashed_and_the_artefact_is_now_established", "verdict": "accept",
   "why": "Last round's written-in-advance prediction named (63,57) then (63,56), the panel configuration, the 48-correct-1-wrong divergence and the exact gains 5.087463 and 3.5025; P-09 through P-12 confirm every clause. Five identical readings across four states, two meter counts and both configurations promote the artefact from reading to fact."},

  {"id": "L-05", "subject": "the_probe_tier_rolls_my_state_forward_and_never_resyncs", "verdict": "probe-pending",
   "why": "New. Action 5's 71 changed cells at t15 and t17 are all instanced and each fired by exactly one rule, so a probe predicting from the observed frame could not have been refuted -- yet P-10 and P-12 exist. The leading reading is a rolled-forward predictor carrying the undrawable burn, which makes the debt cumulative and permanent; the discriminating observation is a press of ACTION5 immediately after a command that burned nothing, and I name the competing reading rather than asserting this one."},

  {"id": "L-06", "subject": "the_loudest_forged_silence_is_not_at_spawn", "verdict": "probe-pending",
   "why": "New. I traced both movement rules against the state one cell south of spawn: key2_body_leaves finds no Glyph9 rendering 9 and key2_body_arrives finds no Vacated rendering 5, so the total compiled step asserts ACTION2 there is inert. Rows 20-24 are floor from column 13 to column 31 and seven consecutive presses have moved the body one lattice cell south, so the assertion is almost certainly false at the one cell where being wrong is worth the most."},

  {"id": "L-07", "subject": "the_meter_is_still_two_readings_and_seventeen_transitions_have_not_split_them", "verdict": "probe-pending",
   "why": "Four more transitions spent without separating them, because keys 2 and 4 have still only ever been pressed at even indices and keys 1, 3 and 5 only at odd ones. Index 18 is even, so any press of key 1, 3 or 5 separates the readings -- and the answer must be read off the raw diff, since under the parity reading the burn is undrawable and a refutation fires either way."},

  {"id": "L-08", "subject": "the_spawn_probe_guard_is_carried_and_is_still_never_tested_negative", "verdict": "probe-pending",
   "why": "Seven positive witnesses and still zero negatives after four rounds; the body is at spawn and the panel is in configuration B, which is precisely the configuration in which the five reverse rules would fire but for this guard, so one free press of ACTION5 either confirms it or refutes thirteen rules at once."},

  {"id": "L-09", "subject": "action5_is_return_to_spawn_or_north", "verdict": "probe-pending",
   "why": "Seven presses, every one from the same cell, so the two readings still coincide on every frame ever observed; swap-with-memory is now refuted four times over by the 71-cell diffs at t7, t11, t15 and t17. The separator needs the body two cells from home, which is the same third-lattice-cell purchase the goal line needs."},

  {"id": "L-10", "subject": "the_cascade_length_reads_the_panel", "verdict": "accept",
   "why": "Now seven for seven: ACTION2 returned 7 frames in configuration A at t2, t8, t12, t16 and 9 frames in configuration B at t6, t10, t14, with identical 49-cell net displacement every time -- so the panel changes the animation, not the distance, over open floor."},

  {"id": "L-11", "subject": "invariant meter_cells_burned_right_now = 8", "verdict": "accept",
   "why": "Written as a state-dependent count and labelled as such in its status field rather than dressed as a conservation law; the current frame shows row 63 columns 56-63 rendering 1 and columns 0-55 rendering 9."},

  {"id": "L-12", "subject": "dark_may_have_no_instances", "verdict": "probe-pending",
   "why": "cells_needing_an_owner is 76 while dynamic_cells is 79 and the gap is exactly the three background-coloured underline-2 cells; the indirect evidence from exact replay is strong but is now two rounds stale, so I keep the theorem rather than promoting it."},

  {"id": "P-01", "subject": "P-09 and P-11 (action 2 refutations)", "verdict": "reject",
   "why": "No change made and the refusal is explicit. t14 changed 49 cells being 48 body plus the burn at (63,57), t16 changed 49 being 48 body plus (63,56); the 48 are drawn exactly by two rules with seven witnesses each, and the one divergent cell was board at the moment of the press. There is no rule to add."},

  {"id": "P-02", "subject": "P-10 and P-12 (action 5 refutations)", "verdict": "reject",
   "why": "No change made. The 71 changed cells at t15 and t17 decompose as 24 + 24 + 8 + 3 + 8 + 1 + 3 = 71 with nothing left over, every one fired by exactly one rule, so the divergence cannot lie in the ACTION5 model; it is the preceding ACTION2's undrawable burn carried forward, which is L-05."},

  {"id": "P-03", "subject": "heuristic_miss (no goal declared)", "verdict": "reject",
   "why": "Answered with an enumerated refusal rather than an invented goal, on the new ground in L-02: the bottleneck is the transition model, not the goal language, so no goal edit can help until one command puts the body in a third lattice cell. Both books now rank every option by proximity to that observation."},

  {"id": "P-04", "subject": "next command -- the east key at spawn", "verdict": "probe-pending",
   "why": "Ranked first because it pays four ways at once: it names a direction whichever way it answers (east is one of exactly two candidates and neither has been tested where east is open), it separates the two meter readings at an even index, it kills a forged silence, and if it moves the body it buys the third lattice cell that unblocks the goal line."},

  {"id": "E-02", "subject": "a click action's coordinates", "verdict": "reject",
   "why": "I wanted a guard naming the cell a click landed on, so the knob could be modelled; the grammar admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere. Written instead as theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click, which records that I could capture a click's effect and never its precondition."},

  {"id": "E-03", "subject": "a third outcome meaning 'unobserved, I decline to predict'", "verdict": "reject",
   "why": "I wanted to mark the four unwitnessed silences -- keys 3, 4 and 5 at spawn and key 2 one cell south -- as ignorance rather than as prediction, but the compiled step is total and absence of a rule compiles to identity. Written instead as theorem silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged plus L-06, and as a playbook order treating predicted inertness as ignorance unless a witness backs it."}
]
```
```
