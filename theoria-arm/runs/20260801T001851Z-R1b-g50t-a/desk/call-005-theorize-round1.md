# call-005-theorize-round1

model: `claude-opus-5` · 722188 ms · $1.961056 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 40658, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40658, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 40658, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40658, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 60981, "type": "message"}], "output_tokens": 60981, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "distinct_states": 13,
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
  "candidates": 10,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 5,
   "move": 10,
   "recolor": 18,
   "vanish": 5
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
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj9"
   }
  ],
  "variants": [
   {
    "baseline_bits": 9784,
    "compression_ratio": 0.935814,
    "events": 38,
    "gain_bits": 628,
    "ms": 54,
    "script_bits": 9156,
    "split_by_color": false,
    "tracks": 10
   },
   {
    "baseline_bits": 9784,
    "compression_ratio": 6.767375,
    "events": 91,
    "gain_bits": -56428,
    "ms": 67,
    "script_bits": 66212,
    "split_by_color": true,
    "tracks": 41
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
  "distinct_states": 13,
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
  "difference_rank": 10,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.025316,
   "difference_rank": 10,
   "features": 395,
   "space_dimension": 385,
   "transitions": 17,
   "verdict": "THIN: 17 transitions constrain rank 10 of 395 features, so the null space has dimension 385 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
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
     "c5@10",
     "c9@10",
     "c0@11",
     "c1@11",
     "c2@11",
     "c5@11",
     "c9@11",
     "c0@12",
     "c1@12",
     "c2@12",
     "c5@12",
     "c9@12",
     "c0@13",
     "c1@13",
     "c2@13",
     "c5@13",
     "c9@13",
     "c0@14",
     "c1@14",
     "c2@14",
     "c5@14",
     "c9@14",
     "c0@15",
     "c1@15",
     "c2@15",
     "c5@15",
     "c9@15",
     "c0@16",
     "c1@16",
     "c2@16",
     "c5
```

The full proposal stream is 1538 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 14 states / 13 transitions
# (RESET, then A1 A2 A3 A4 A5 A2 A5 A1 A3 A2 A5 A2 A4, one command each).
# 77 cells have ever changed; this manual names and owns all 77.
#
# ================= WHAT HAPPENED SINCE THE LAST MANUAL =================
#
# 1. FOUR NEW TRANSITIONS, AND NOT ONE OF THEM SHOWED ME A NEW MECHANISM.
#    t10 A2 = t2 repeated. t11 A5 = t5 repeated. t12 A2 = t6 repeated.
#    t13 A4 at lattice (2,2) = t4 repeated, minus the burn. I read the
#    CURRENT FRAME cell by cell against what my manual draws for state 13
#    and it agrees on every one of the 77 dynamic cells: panel in
#    configuration B exactly as described, body ring at rows 14-18 cols
#    14-18 with its aperture at (16,16), meter burned at row 63 cols
#    58-63 and nowhere else. A manual missing a 23-cell or 48-cell
#    mechanism could not land on the observed frame after thirteen
#    transitions. So the manual is not missing a mechanism.
#
# 2. THEN WHY DID THREE PROBES COME BACK VACUOUS? Because the frontier
#    CANNOT contain the world on an even-indexed command, and P-05, P-06
#    and P-07 were commands 10, 11 and 12. See
#    the_frontier_is_vacuous_by_construction_at_even_indices. In short:
#    the cell the meter is about to burn has never changed, so the arm
#    gives it no instance, so NEITHER the manual NOR any ablation of it
#    NOR `inert` can draw it -- every hypothesis is refuted by the same
#    one pixel and the realised gain is 0 bits by arithmetic, not by
#    ignorance. I am not given divergence sets, only hashes, so I mark
#    this reading probe: pending and name the observation that would
#    overturn it.
#
# 3. THE CLOCK IS NOW 6/6 AND 7/7 AND THE STORE CONFIRMED MY STATE MODEL
#    FROM A NUMBER I DID NOT FIT. My model says a state is (body in one
#    of two cells) x (panel A or B) x (burn count 0..6). It predicts that
#    s0=s1, s2=s3, s8=s9, s12=s13 and no other coincidence, hence
#    14 - 4 = 10 distinct states. The store reports distinct_states = 10.
#    See the_state_model_predicted_the_duplicate_count.
#
# 4. ACTION4 IS STILL UNTESTED WHERE EAST IS OPEN. t13 spent ACTION4 at
#    lattice (2,2), where east AND west are void -- the one cell where
#    its answer means nothing. Thirteen commands, two lattice cells
#    occupied out of eleven reachable. The playbook's whole first page is
#    about that and about the cheaper question underneath it: does
#    ACTION2 work from anywhere but spawn, or is this a two-cell shuttle?

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
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t10,t11,t12 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t11 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t11 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t10,t12 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t10,t12 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_edge_key2 forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_next_key2 forall ?p in Glyph9 [ev: t6,t10,t12 cov: 1/1]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key4 forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key1 forall ?p in Glyph9 [ev: t8 cov: 1/1]
    when act=key(1) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3,t9 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t11 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t11 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t11 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t11 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t11 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t11 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t11 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t11 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t11 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t11 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 41 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4019 [status: counted]
  invariant meter_burned_cells count(Glyph9, color = 1) = 6 [status: counted at state 13, monotone]

  theorem dynamic_census "Exactly 77 cells have ever changed and every one has an owner, two more than last round and both of them meter cells. 23 are the panel: slot 1's eight ring pixels at rows 1-3 cols 1-3, its centre (2,2) being colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in configuration A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 6 are the burned right end of row 63, cols 58 to 63, burned in order 63,62,61,60,59,58 at commands 2,4,6,8,10,12. 23+24+24+6 = 77 = dynamic_cells. By frame-0 colour: 41 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 6 meter), 9 colour-1 (slot 2, solid at frame 0), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 41+9+24 = 74 = cells_needing_an_owner EXACTLY, the store again declining to count background-coloured cells; Dark carries the remaining 3 anyway and replay proves the arm instances them. 4096-77 = 4019 = constant_cells exactly."
    [probe: passed]

  theorem the_state_model_predicted_the_duplicate_count "The strongest corroboration this round and it came from a number I did not fit. My manual says a state is exactly three things: which of two lattice cells the body occupies, which of two configurations the panel shows, and how many meter cells are burned. Writing them out for s0 to s13 -- burns floor(k/2), body spawn spawn (2,2) (2,2) (2,2) spawn (2,2) spawn spawn spawn (2,2) spawn (2,2) (2,2), panel A A A A A B B A A A A B B B -- exactly four pairs coincide: s0=s1, s2=s3, s8=s9 and s12=s13. That predicts 14 - 4 = 10 distinct states. The store reports distinct_states = 10. Any missing mechanism that varied a pixel anywhere in those fourteen frames would have broken a coincidence and pushed the count above 10; any spurious mechanism of mine would have pushed it the other way. This is why I do not believe the three vacuous probes indicate a missing mechanism."
    [depends: dynamic_census, the_meter_is_a_two_command_clock  probe: passed]

  theorem the_frontier_is_vacuous_by_construction_at_even_indices "My answer to P-05, P-06 and P-07, and it is a change of reading rather than a change of rules. All three report every hypothesis refuted, including `inert` and every ablation of the manual, and 0.0 bits realised. An ablation can only DELETE a rule, so the whole frontier is a lattice between the manual and `inert`; if the world does something NO rule of the manual can express, every member of that lattice dies together and the gain is 0 bits by arithmetic. There is exactly one such thing in this world and I named it two rounds ago: the meter's leading edge. The cell about to burn has never changed, so the arm gives it no instance, so no rule can recolour it. P-05 was command 10 (burn at 63,59), P-07 was command 12 (burn at 63,58) -- both even, both burning. P-06 was command 11, which does not burn, and my reading of it is that the frontier was built from a store that did not yet contain command 10's burn, so the predecessor the manual rolled forward from was already one pixel stale. WHAT WOULD OVERTURN THIS: a refutation report that carries a divergence SET rather than a hash, showing any cell outside row 63 cols 55-63. I am not given one, so I mark this pending and rest the claim on the census and on the state-model count instead: after thirteen transitions my manual lands on the observed frame at every one of the 77 dynamic cells, which no manual missing a 23-cell or 48-cell mechanism could do. CONSEQUENCE FOR THE ARM: half of all commands are even, and a probe designed at an even index has expected realised gain 0 whatever it expects on paper."
    [depends: i_cannot_draw_the_leading_edge_burn, the_meter_is_a_two_command_clock  probe: pending]

  theorem the_meter_is_a_two_command_clock "Now 6 out of 6 and 7 out of 7 and I consider it settled. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right. Burns occurred at commands 2, 4, 6, 8, 10 and 12 and at no other command; commands 1, 3, 5, 7, 9, 11 and 13 burned nothing. The key pressed is irrelevant: ACTION1 burned at 8 and did not at 1, ACTION4 burned at 4 and did not at 13, ACTION2 burned at every one of 2, 6, 10 and 12 which happen all to be even, ACTION3 and ACTION5 were only ever pressed at odd indices and never burned. Cols 58-63 are spent, 58 cells remain, so roughly 116 commands remain before the bar is out. The next command is index 14, which is EVEN, and it will burn (63,57) whatever is pressed."
    [depends: meter_burn_next_key1, meter_burn_next_key4  probe: passed]

  theorem the_burn_rules_are_deliberate_mis_attributions_and_one_of_them_is_about_to_break "Constraints 3 and 6, and this time with a dated failure attached. My four burn rules key on act=key(1), key(2) and key(4) because THE GUARD LANGUAGE HAS NO COMMAND COUNTER and no pixel records the parity. I checked whether the parity is recoverable from the frame and it is not: at the start of command k the burn count is floor((k-1)/2), so a frame showing b burns is the start of command 2b+1 (no burn) or 2b+2 (burn) with equal warrant, and b's own parity separates neither -- b takes every value 0..5 in both classes. THE DATED FAILURE. Right now no dynamic meter cell renders 9, so no burn rule can misfire and replay is clean at 13/13. The moment command 14 burns (63,57), that cell becomes dynamic and gets an instance, and REPLAYING t13 -- ACTION4 at an odd index -- will find (63,57) rendering 9 with a colour-1 right neighbour and fire meter_burn_next_key4, predicting a burn the world did not deliver. Exactly one wrong pixel at (63,57) on exactly transition t13, from the next even command onward. I considered guarding that rule on the panel configuration, which happens to separate t4 from t13, and rejected it: it is a fifth mis-attribution fitted to two points and it would break the first time key 4 is pressed in configuration A at an odd index. I considered deleting the rules and rejected that too: it costs six real pixels of replay now to save one later. I keep them and I date the failure instead of being surprised by it."
    [depends: the_meter_is_a_two_command_clock  probe: pending]

  theorem i_cannot_draw_the_leading_edge_burn "A law of this manual rather than of this world, now paid five times. The arm instances exactly the cells that have ALREADY changed, so the next cell to burn is board, has no instance, and NO RULE OF MINE CAN RECOLOUR IT. I checked whether any declaration escapes this: arc-instances: all covers only cells the board cannot explain, so it will not reach a static cell; a landmark can be named at (63,57) but landmarks are cells, not objects, and every event in the language takes an object as its first argument, so a landmark cannot be recoloured. There is no construction in this DSL that draws a cell before its first change. CONSEQUENCE FOR READING REFUTATIONS: a divergence set consisting only of the bar's leading edge does not implicate this manual and must not be allowed to consume a round -- it has now consumed three."
    [depends: the_meter_is_a_two_command_clock  probe: passed]

  theorem the_world_is_not_a_function_of_the_drawn_frame_and_one_command_would_prove_it "Nearly forced, and the proof is now one command away instead of two. s12 and s13 are PIXEL-IDENTICAL -- same body cell, same panel configuration B, same six burns -- which is not a guess but part of the arithmetic that makes distinct_states come out at 10. From s12 the world was given ACTION4 (command 13) and changed nothing. The body stands on s13 now. Give it ACTION4 again (command 14, even) and the clock says (63,57) burns: identical state, identical action, different successor, and hidden state is proven rather than argued. I RANK THIS LOW ANYWAY and say why: constraint 5 obliges my manual to be a function of the frame, so I already know I must be wrong about one member of that pair, that pixel is the leading edge I cannot draw in any case, and the finding changes no rule. It is a cheap proof of something I would not act on differently. I record it so that nobody can sell it to me later as a discovery."
    [depends: the_state_model_predicted_the_duplicate_count  probe: pending]

  theorem the_down_key_may_be_a_shuttle_and_one_press_settles_it "THE LARGEST UNEXAMINED ASSUMPTION IN THIS FILE, and thirteen commands have failed to touch it. ACTION2 has been pressed four times and every one was from spawn; ACTION5 has been pressed three times and every one was from lattice (2,2). Not once has ACTION2 been pressed from anywhere but spawn. So every observation is equally consistent with two readings. READING DOWN: ACTION2 moves the body one lattice cell south wherever it stands, ACTION5 moves it one north, and the maze theorem below is about a maze. READING SHUTTLE: ACTION2 means go to cell two and ACTION5 means go back to cell one, the world is a two-cell rocker, and the lattice, the comb and the socket are scenery. One press decides it: ACTION2 from where the body stands now. Lattice (3,2) is rows 20-24 cols 14-18, read floor in the current frame, and separator row 19 is floor across cols 13-31, so the destination ring is clear. WHAT MY MANUAL PREDICTS FOR THAT PRESS, so it can cost me: NOTHING except an undrawable burn. key2_body_leaves ranges over Glyph9 and the body currently stands on Vacated cells, so no rule of mine erases rows 14-18; key2_body_arrives ranges over Vacated and rows 20-24 are board with no instances. If the body moves I am wrong by 48 cells, 24 of which -- the departure at rows 14-18 -- I could have drawn with a rule and deliberately did not, because constraint 2 forbids a rule with no witness and this one has none. That is the price of the constraint and I pay it once, knowingly, rather than smuggling an unwitnessed rule into the manual."
    [depends: key2_body_leaves, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_action_map_after_thirteen_transitions "WITNESSED, with the negatives stated as negatives, and one negative wasted. ACTION2 CARRIES THE BODY SOUTH FROM SPAWN: t2, t6, t10, t12, the 5x5 ring from rows 8-12 to rows 14-18, four times, in both panel configurations. ACTION5 CARRIES IT BACK NORTH: t5, t7, t11, three times, each with a panel toggle. NEGATIVES. At spawn, north and west are void while south and east are open floor; ACTION1 did nothing there at t1 and t8, ACTION3 did nothing there at t9 -- so NEITHER ACTION1 NOR ACTION3 IS EAST. At (2,2) north and south are open while east and west are void; ACTION3 did nothing at t3 and ACTION4 did nothing at t4 and again at t13 -- so neither is up and neither is down, and both are consistent with being horizontal. Combine: ACTION3 is neither vertical nor east, which leaves west, and west is void at both cells it has been pressed from, explaining all three of its silences without inventing anything. ACTION4 IS STILL THE ONLY REMAINING CANDIDATE FOR EAST AND HAS STILL NEVER BEEN PRESSED WHERE EAST IS OPEN. t13 spent it at (2,2), the one cell where east and west are both void and its answer means nothing -- a command bought and thrown away. Cells where east is open: spawn (rows 8-12, cols 20-24 read floor) and lattice (3,2) (rows 20-24, cols 20-24 read floor). The residue: ACTION1 is consistent with up and so is ACTION5, and two up keys is a smell; one press of ACTION1 from (2,2) separates them."
    [depends: key2_body_arrives, key5_body_respawns  probe: pending]

  theorem action5_is_up_or_home_or_undo_and_a_third_cell_separates_them "Three witnesses now and all three moved the body from (2,2) to spawn, a move that up, return-home and undo-last-move predict identically, so this store still cannot separate them. The separator is unchanged and is a shape, not a route: stand two lattice steps from spawn and press ACTION5 once. Up predicts one step back; home predicts a jump of two cells; undo predicts one step back along the arrival direction, which differs from up as soon as the last step was horizontal. My rules encode none of the three -- key5_body_respawns is guarded on PIXELS, a Glyph9 cell rendering 5 whose neighbour above renders 5, so it is a spawn-ring refill rule and nothing more. As written it fires from ANY state where the spawn ring reads floor, so from a third cell my manual predicts the body is DRAWN AT SPAWN WITHOUT BEING ERASED where it stood: two bodies, 24 wrong pixels, priced here in advance."
    [depends: key5_body_respawns, the_action_map_after_thirteen_transitions  probe: pending]

  theorem the_spawn_probe_guard_is_still_the_untested_half_of_thirteen_rules "Every panel rule carries colored(spawn_probe, 5), which reads the body is not at home. All three witnesses had the body one cell south, so the guard has never been tested with the body home: ACTION5 has never been pressed at spawn in fourteen states. If the panel toggles anyway, thirteen rules are guarded on the wrong thing and my manual under-predicts 23 pixels on that command; if nothing happens, the guard survives and the manual is right that ACTION5 at spawn is inert. The asymmetry that makes this cheap is unchanged: my manual predicts ZERO cells for ACTION5 at spawn, so any change at all is legible in the raw diff."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: pending]

  theorem the_panel_is_a_two_slot_selector_toggled_by_action5 "Both directions witnessed, A to B at t5 and t11 and B to A at t7, and the current frame re-read pixel by pixel is configuration B. A: slot 1's ring reads 9 with underline 1 reading 9, slot 2 reads solid 1 with underline 2 reading 0. B: slot 1's ring reads 2 with underline 1 reading 0, slot 2 reads a ring of 9 with its centre hollowed to 0 and underline 2 reading 9. THE READING: two slots, an underline under each, and the underlined slot is also the one rendered in colour 9 -- a two-item selector whose cursor ACTION5 advances, wrapping after two. The two glyphs are a hollow 3x3 square and a solid 3x3 square; the body is a hollow ring and the knob at rows 9-11 cols 39-41 is a solid 3x3 block, which is a suggestive pairing and nothing more. WHAT I DO NOT CLAIM: what the selection selects. ACTION2 moved the body identically from configuration A at t2 and t10 and from configuration B at t6 and t12, and ACTION4 was inert in configuration A at t4 and in configuration B at t13, so the selector remaps neither -- four cross-configuration comparisons and not one difference. If the selection matters at all it matters to a key never pressed, which is ACTION6 or ACTION7."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, key5_underline2_dims  probe: passed]

  theorem the_goal_is_absent_because_no_instance_can_name_the_socket "I decline again to declare a goal, the argument is unchanged by four more transitions, and I restate the price. The winning position I believe in is lattice cell (8,7), rows 50-54 cols 44-48, whose 24 ring pixels read floor and whose centre (52,46) is a lone colour-9 pip inside a three-sided colour-9 bracket. Four forms of goal are available and every one is refuted. (1) Cart.pos = exit_cell needs ONE named instance; arc-instances: all gives me Glyph9_r8c14 and forty siblings and there is no instance called Glyph9, and a second colour-9 type would be indistinguishable to an arm that looks objects up by colour alone. (2) A count over the socket interior has nothing to range over: those cells have never changed, so they are board and carry no instances. (3) Counts over the four types I do have are all either true in some observed state -- count(Vacated, color = 9) = 0 holds in seven of fourteen, count(Glyph9, color = 5) = 24 holds in six -- or, like count(Spent, color = 0) = 9, false everywhere and meaningless, which is exactly the fake goal the rider warns is worse than none. (4) The goal cannot be conjunctive; the section takes one equation. THE PRICE: is_goal compiles to False, plan returns no_goal_declared, commit never runs, and all fourteen commands have been probes. THE OBSERVATION THAT ENDS THIS, restated sharply: a goal becomes writable the moment any pixel of the bracket rows 49-55 cols 43-49, or the pip (52,46), changes colour, because those cells become dynamic that instant and a count over them becomes both writable and false in every earlier state. Nothing the body has done in fourteen commands can cause that, because the body has not left a two-cell corridor. THAT is the reason there is no goal, and it is a reason about reach, not about vocabulary."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_down_key_may_be_a_shuttle_and_one_press_settles_it  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 ring with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2 plus a one-row fragment at row 48 cols 42-50 that cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in fourteen frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it stands at (2,2) now. THIS THEOREM IS HOSTAGE TO ONE PRESS: if ACTION2 does not carry the body from (2,2) to (3,2), there is no maze, only a rocker, and this theorem and the four below it are scenery."
    [depends: key2_body_arrives, the_down_key_may_be_a_shuttle_and_one_press_settles_it  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed seven times now: (16,16) stayed 5 at t2, t6, t10 and t12 while its 24 neighbours turned 9, and (10,16) did the same in reverse at t5, t7 and t11. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell again against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 50-54. Rows 49 and 55 are separator rows and cols 43 and 49 separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side left as floor. Inside it, rows 50-54 cols 44-48 are floor except the lone colour-9 pixel at the exact centre (52,46). Overlay the body standing there -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel. The bracket has not changed in fourteen frames, so it is board and no object owns it; the first time any of it changes, those cells become dynamic and the goal section can finally be written."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn under the DOWN reading and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem at col 40 running from row 12 to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18 with floor gaps only at (39,14) and (41,14). ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in fourteen frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Fourteen commands and TWO OF SEVEN ACTIONS HAVE NEVER BEEN TRIED ONCE. In this action family one of them is normally a click carrying coordinates, and that matters here for a specific reason: the knob is a 3x3 target the body appears unable to stand on, the panel is a two-item selector whose selection provably changes nothing about ACTION2 or ACTION4, and a selector that selects nothing for the five keys I have tried is a selector for a key I have not. I cannot write a click rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5 or panel pixels moving, and never its precondition. My manual predicts ZERO cells for both keys, so any change at all is legible, and certify adjudicates five actions rather than seven, which means those two columns of the transition table are unexamined rather than clean."
    [probe: pending]

  theorem the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_defect "Priced in advance so it cannot be sold to me as a surprise. The arm instances exactly the cells that have already changed, so any lattice cell the body has never entered is board and has NO instance. The first step into a new cell costs 24 undrawable arrival pixels no matter what rule I write, plus up to 24 departure pixels if no witnessed rule of mine erases the cell being left. Concretely for the press I am about to recommend, ACTION2 from (2,2): 24 arrival pixels at rows 20-24 cols 14-18 are undrawable, and 24 departure pixels at rows 14-18 are drawable only by a rule I am forbidden to write until it has a witness -- so 48 on the first step, 24 on the second, 0 thereafter. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated everywhere else -- because typing is by frame-0 colour and all that floor was 5. A manual that heals one step behind is the price of this arm, and those pixels are tuition, not damage. THE COROLLARY THE ARM MUST HEAR: a probe frontier evaluated on that command will be vacuous for the same reason the meter makes even commands vacuous, and its 0 bits must not be read as a refutation."
    [depends: the_maze_is_a_six_pixel_lattice, the_frontier_is_vacuous_by_construction_at_even_indices  probe: pending]

  theorem silence_is_a_prediction_and_three_of_my_seven_silences_here_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the seven actions at lattice (2,2), where the body stands. key(1): NO WITNESS HERE -- pressed only at spawn. key(2): NO WITNESS HERE, and this is the shuttle question. key(3): inert, WITNESSED at t3. key(4): inert, WITNESSED twice, t4 and t13. key(5): carries the body north, witnessed three times. key(6) and key(7): NO WITNESS ANYWHERE. So four of seven silences at this cell are forged death certificates and one of them, key(2), is the load-bearing assumption of five theorems. That is the largest block of unearned confidence in this file and the cheapest to fix: one press each."
    [depends: the_action_map_after_thirteen_transitions, the_down_key_may_be_a_shuttle_and_one_press_settles_it  probe: pending]

  theorem the_cascade_length_is_a_free_channel_and_it_keeps_paying "ACTION2 returned 7 frames from configuration A at t2 and t10, and 9 frames from configuration B at t6 and t12 -- four for four, the split I predicted two rounds ago now doubled. ACTION5 returned 9 frames all three times and every no-op returned 1. So the animation length is not a function of the key alone and the panel configuration is the one correlate with a witness. This is hidden state I discard by construction, since cascade single_frame compares only net effect, and it is the ONLY evidence I have that the panel configuration changes anything at all -- the net pixel effect of ACTION2 is identical in both configurations. It costs nothing in replay and buys nothing in prediction; I keep reading it because it is free, and because if the selector ever does something visible I expect the frame count to have warned me first."
    [depends: the_panel_is_a_two_slot_selector_toggled_by_action5  probe: passed]

  theorem the_no_op_rule_fails_the_gain_test_and_i_keep_it_for_a_narrow_reason "key3_inert_below_spawn recolours one pixel to the colour it already has, has two witnesses on transitions where zero cells changed, and replay is identical without it. It explains no pixel and lengthens the manual, so it fails constraint 3 and I say so rather than dressing it up. The reason I keep it: it is the ONLY occurrence of act=key(3) in the file, and deleting it narrows the action set certify adjudicates from five keys to four. Note what that reason implies about keys 6 and 7, which appear nowhere: certify's fifty adjudicated pairs cover five of seven columns, and the two missing columns are unexamined rather than clean."
    [depends: key3_inert_below_spawn, two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap  probe: passed]

  theorem the_rules_are_pairwise_exclusive_and_off_board_cell_terms_are_false "Constraint 5, re-checked by hand over all four instance types in both panel configurations after the meter grew by two cells. Under key(2): body_leaves needs below-six to render 5, which is off-board and therefore false for any row past 57, so it cannot fire on a meter cell; the two burn rules split on rightof = wall against a colour test on rightof, which cannot both hold. Under key(5) the type Glyph9 is split five ways by COLOUR FIRST -- 5 for respawns, 9 for the two dim rules, 2 for slot1_lights, 0 for underline1_lights -- and colours 2 and 0 occur on no other Glyph9 cell in any observed state, so the return half needs no geometry. The two colour-9 rules are then split by above-four: slot1_dims needs it to BE WALL, true only for rows 0-3; underline1_dims needs a COLOUR TEST on it, which is false off-board rather than raising, so it selects row 5 and excludes rows 0-3, and its above-six wall test excludes the meter at row 63. Spent splits by colour into 1 against 9 and 0; within colour 1 the geometry is row 1 by above-two wall, row 3 by a colour test on above-two, row 2 by above-three wall plus a colour test on above-one, and within row 2 col 5 by leftof-six wall, col 6 by leftof-seven wall plus a colour test on leftof-one, col 7 by a colour test on leftof-two. Dark splits by colour 0 against 9. Not one rule uses not, deliberately. Certify reports 0 clashes over 50 adjudicated pairs and 10 states."
    [depends: key2_body_leaves, key5_slot2_centre_darkens, key5_slot1_lights  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body is at lattice (2,2) rows 14-18, the panel is in configuration B, six meter cells are burned at row 63 cols 58-63, and the next command index is 14, which is EVEN, so under the clock it burns (63,57) whatever is pressed and I cannot draw that cell -- which also means whatever is pressed, the probe frontier will be vacuous and its 0 bits must be discounted. ACTION2, my first choice: my manual predicts ZERO cells and has NO WITNESS for that silence. If the body steps to (3,2) I pay 48 undrawable pixels already priced and the maze is real; if nothing moves, this world is a two-cell rocker and five theorems are scenery. Either answer is worth more than any other command on the board. ACTION4 here: predicted zero, witnessed zero twice already, and its only remaining value is the identical-state proof I have ranked low. ACTION5 here: 48 body cells and 23 panel cells I draw correctly, every rule already at full coverage, buying only a fourth cascade datum and a return to spawn. ACTION1 here: predicted zero, UNWITNESSED at this cell, and it separates ACTION1 from ACTION5 if it moves the body north. ACTION6 or ACTION7: predicted zero, never pressed anywhere, and the only keys that could plausibly give the selector something to select. THE SINGLE OBSERVATION THAT WOULD MOST CHANGE THIS FILE is unchanged and it is not a movement at all: any colour-8 pixel of the comb or the wire changing, because that turns the gate theorem into physics and puts the socket in reach."
    [depends: the_down_key_may_be_a_shuttle_and_one_press_settles_it, the_meter_is_a_two_command_clock  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on both variants, -1629 bits unsplit and -42062 split by colour, which is the segmenter saying its own script costs more than writing the pixels. I take its TRACK LIST and not its verdict, and this round the list dates my panel rules independently for a second time. obj0 (colour 9, eight cells, 3x3, all fourteen frames) and obj2 (colour 9, 1x3, all fourteen frames) are slot 1's ring and underline 1 persisting through all three toggles, so it does not see the panel as appearing and vanishing, which corroborates a marker with two seats rather than two objects. obj1 (colour 1, 3x3, frames 0-4) is slot 2 solid in configuration A; obj5 (colour 2, eight cells, first frame 5, present 2 frames) is slot 1 after the t5 dim, ending at t7; obj6 (colour 1, first frame 7, present 3 frames) is slot 2 solid again from t7 to t10; obj7 (colour 2, eight cells, FIRST FRAME 11, present 3 frames) is slot 1 dimmed again by t11 and still dim in the current frame. Four tracks whose birth and death frames are 5, 7, 7 and 11 -- exactly my three toggle transitions, from an engine that has never seen my rules. obj4 is the whole 64-cell row-63 bar, of which 6 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body: connected_components(4) cannot see the mover, because the mover is a ring adjacent to floor on every side, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 13 transitions constrain rank 7 of 385 features, null space dimension 378 -- and its one global law is my census cell for cell, 77 cells, a consistency check and not a discovery. cegis_miner refuses every track and its verdict, the world does not narrate as one mover, is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Fourteen states, thirteen transitions, and the manual lands on the
# current frame at every one of the 77 dynamic cells. Three probes came
# back vacuous and NONE of them found a missing mechanism; they found the
# meter's leading edge, which no hypothesis in the frontier can draw. The
# manual says why in the_frontier_is_vacuous_by_construction_at_even_
# indices, and the practical consequence belongs here: HALF OF ALL
# COMMANDS ARE EVEN AND EVERY ONE OF THEM WILL REPORT 0 BITS. Read the
# raw diff, which is given for every command regardless, and stop reading
# the frontier's bits as a verdict on the manual.
#
# ========= WHAT THIRTEEN COMMANDS BOUGHT, AND WHAT THEY DID NOT =========
# Bought: ACTION2 south from spawn (x4), ACTION5 north from (2,2) (x3),
# the two-command clock (6/6 and 7/7), the panel's two configurations in
# both directions, and a state model that predicted distinct_states = 10
# before the store said 10.
# Not bought: the body has occupied TWO lattice cells out of eleven, and
# it has occupied them since command 2. ACTION4 was finally pressed at
# t13 -- at (2,2), the one cell where east and west are both void, so its
# silence there means nothing. Two of seven actions have never been
# pressed at all.
#
# ========= THERE IS STILL NO GOAL, AND THE REASON IS REACH =========
# theorem the_goal_is_absent_because_no_instance_can_name_the_socket
# gives the argument and the price: is_goal is False, plan returns
# no_goal_declared, commit never runs, EVERY COMMAND THIS LEG IS A PROBE.
# The reason is not vocabulary and not shyness. A goal becomes writable
# the instant any pixel of the socket bracket (rows 49-55, cols 43-49) or
# its pip (52,46) changes colour, because those cells become dynamic that
# instant. Nothing the body can do inside a two-cell corridor causes
# that. So the goal is downstream of movement, and movement is downstream
# of one unasked question.
#
# ========= THE ONE THING WORTH BUYING =========
# ACTION2 FROM WHERE THE BODY STANDS NOW, lattice (2,2), rows 14-18.
# ACTION2 has been pressed four times and every one was from spawn.
# ACTION5 has been pressed three times and every one was from (2,2). So
# the entire movement record is consistent with a TWO-CELL ROCKER -- go
# to cell two, go back to cell one -- in which the lattice, the comb and
# the socket are scenery. One press decides it. Destination (3,2), rows
# 20-24 cols 14-18, reads floor in the current frame and separator row 19
# is floor across cols 13-31, so the ring is clear.
#   If the body moves: the maze is real, the body stands in a THIRD cell
#   for the first time, east is OPEN there (cols 20-24 read floor) so the
#   east key can finally be tested next command, and ACTION5 from a third
#   cell separates up from home from undo. One press, three questions.
#   If it does not move: this is a rocker, five theorems are scenery, and
#   that is a bigger finding bought for the same command.
# My manual predicts ZERO cells for this press and has no witness for
# that silence. The 48 pixels it will cost if the body moves are priced
# in the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_
# defect; they are tuition and they must not consume a round.
#
# SECOND: ACTION4 from any cell where east is open -- spawn or (3,2),
# never (2,2). It is the last candidate for east and its answer names a
# direction whichever way it falls.
# THIRD: ACTION6, then ACTION7. Never pressed, predicted zero, so any
# change is legible; and the panel is a selector that provably selects
# nothing for the five keys already tried.
# DO NOT BUY: ACTION4 at (2,2) again (witnessed inert twice); a fifth
# ACTION2 from spawn or a fourth ACTION5 from (2,2) (every rule already
# at full coverage); any probe ranked because a refutation fired on it.
#
# ------------------------------------------------------------------------
# STATE 13: body at lattice (2,2); panel configuration B; six meter cells
# burned (row 63, cols 58-63); next command index 14, which is EVEN and
# burns (63,57) whatever is pressed. s13 is pixel-identical to s12, from
# which ACTION4 changed nothing -- so ACTION4 now would prove hidden
# state, and the manual explains why that proof is not worth a command.

order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     treat_the_first_socket_pixel_that_moves_as_the_goal_writing_event [proof: lean]
order     settle_whether_down_works_off_the_spawn_ring_before_anything_else [proof: lean]
order     read_the_raw_diff_rather_than_the_frontier_bits_when_a_burn_is_due [proof: lean]
order     press_a_direction_key_only_where_that_direction_is_open           [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one           [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered     [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     spend_the_clock_on_unwitnessed_key_cell_pairs_not_on_repeats      [proof: lean]
order     try_an_action_never_pressed_before_repeating_a_settled_one        [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong    [proof: lean]

prune     divergence_lies_only_on_a_cell_that_has_never_changed => dead      [proof: lean]
prune     frontier_cannot_contain_the_world_so_its_bits_are_bookkeeping => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead    [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     repeats_a_key_cell_pair_whose_inertness_is_already_witnessed => dead [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     tests_a_direction_from_a_cell_where_that_direction_is_void => dead [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     probes_the_meter_parity_that_thirteen_transitions_settled => dead  [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic actions_never_pressed_anywhere_in_the_store                       [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic theorems_a_single_press_would_promote_or_demolish                 [admissible: lean]
heuristic rules_whose_shared_guard_a_single_command_would_falsify           [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                        [admissible: lean]

prefer    the_press_that_decides_whether_this_world_is_a_maze_or_a_rocker  [ev: 5/22 theorems hostage]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 4/7 keys at this cell]
prefer    stepping_into_a_lattice_cell_the_body_has_never_occupied         [ev: 2/11 cells visited]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 1/1 candidates left]
prefer    an_action_pressed_zero_times_over_one_pressed_four_times         [ev: 2/7 actions unpressed]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 13/13 diffs]
prefer    east_along_a_lattice_row_over_any_other_axis_once_south_is_known [ev: 1/1 levels]
prefer    a_press_at_a_third_cell_that_splits_up_from_home_from_undo       [ev: 3/3 key5_presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

## Why you are being called: the surprises that fired

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "3c8b3ee11d74edfd",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 24 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted 'e66afa8078cb4fd2' against the world's 'd09fae77a1d46f2c'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.918 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 5,
 "expected_bits": 0.918295834054,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "e66afa8078cb4fd2",
 "n_hypotheses": 24,
 "n_survivors": 0,
 "observed": "d09fae77a1d46f2c",
 "probe_id": "P-09",
 "vacuous_streak": 1
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 24 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '0c86941f09a0caaf' against the world's '72c21e35d4893016'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.544 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 2,
 "expected_bits": 0.5435644432,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "0c86941f09a0caaf",
 "n_hypotheses": 24,
 "n_survivors": 0,
 "observed": "72c21e35d4893016",
 "probe_id": "P-10",
 "vacuous_streak": 2
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 24 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '06e79195f0adc15f' against the world's '3a11719074841328'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.995 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 5,
 "expected_bits": 0.994984828186,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "06e79195f0adc15f",
 "n_hypotheses": 24,
 "n_survivors": 0,
 "observed": "3a11719074841328",
 "probe_id": "P-11",
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

## The manual has no goal section, and that has a price

This is not a complaint and not a request to invent one. It is a number you have not been shown.

The manual as it stands declares no `goal` clause. `is_goal` therefore compiles to `False` everywhere, so the planner cannot succeed on any input: every `plan` beat this leg has returned `no_goal_declared` without entering either rung of the ladder. So far that is 11 turn(s) and at least 15 action(s) spent with no target. The world has moved since the last time this was asked: 12 distinct states are now on record (the bar is 4 new ones).

Two answers are acceptable and one is not.

1. **A `goal` clause**, if the evidence now supports one. It must be false in the states you have already seen -- a goal satisfied by the current board stops the planner at the first node and is worse than no goal at all.
2. **A `theorem`** whose name says the goal is absent (it must contain both `goal` and one of absent, no_goal, unsigned, silence, not_signed, without_a_goal) and whose body gives the argument and the evidence that would settle it. Declining is a position; the record will carry it as one.

What is not acceptable is silence: a manual with neither a goal nor an argument about its absence leaves the arm exploring without knowing that it is exploring, which is the state this rider exists to end.


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
# (RESET, then A1 A2 A3 A4 A5 A2 A5 A1 A3 A2 A5 A2 A4 A5 A2 A5 A1).
# 79 cells have ever changed; this manual names and owns all 79.
#
# ================= WHAT HAPPENED SINCE THE LAST MANUAL =================
#
# 1. FOUR MORE COMMANDS AND NOT ONE NEW MECHANISM, BECAUSE ALL FOUR WERE
#    REPEATS OF WITNESSED KEY-CELL PAIRS. t14 A5 = t7 repeated (body
#    (2,2)->spawn, panel B->A). t15 A2 = t2 repeated (spawn->(2,2), the
#    FIFTH A2 from spawn, a press the playbook explicitly pruned).
#    t16 A5 = t5 repeated. t17 A1 at spawn = t1 repeated, the THIRD
#    witness of the same silence. The body is back at spawn, has still
#    occupied exactly TWO of eleven reachable lattice cells, and has
#    occupied them since command 2. I read the CURRENT FRAME cell by cell:
#    spawn ring rows 8-12 cols 14-18 reads 9 with its aperture (10,16)
#    reading 5; rows 14-18 read floor; panel is configuration B; row 63
#    cols 56-63 are burned. The manual draws exactly that.
#
# 2. THE DATED FAILURE ARRIVED ON SCHEDULE AND I AM PAYING IT. Last round
#    I wrote that the moment command 14 burned (63,57), replaying t13
#    would fire meter_burn_next_key4 on a cell that had just acquired an
#    instance and predict a burn the world did not deliver -- "exactly one
#    wrong pixel at (63,57) on exactly transition t13". Command 14 burned
#    (63,57). The same thing has now happened a second time at t15 with
#    key(2) and (63,56). Certify's next replay should read 13/17, not
#    17/17, with first_divergence at t13. See
#    the_burn_rules_are_deliberate_mis_attributions_and_the_dated_failure_arrived_on_schedule.
#
# 3. THE METER IS NOW PROVABLY NOT A FUNCTION OF THE DRAWN FRAME. 8 burns
#    at commands 2,4,6,8,10,12,14,16 and 9 silences at 1,3,5,7,9,11,13,15,
#    17: 8/8 and 9/9. Every key pressed at both parities now shows the
#    contradiction -- key1 burned at 8 and not at 1 or 17, key2 burned at
#    2,6,10,12 and not at 15, key4 burned at 4 and not at 13, key5 burned
#    at 14,16 and not at 5,7,11. And for five of the nine burn counts the
#    two commands sharing that count start from PIXEL-IDENTICAL frames.
#    See no_frame_function_can_predict_the_burn_and_five_identical_pairs_prove_it.
#
# 4. THE STATE MODEL PREDICTED distinct_states A SECOND TIME, FROM 18
#    STATES. Model: (body in one of two cells) x (panel A or B) x (burns
#    0..8). It says exactly five pairs coincide -- s0=s1, s2=s3, s8=s9,
#    s12=s13, s16=s17 -- hence 18-5 = 13. The store reports 13.
#
# 5. THE BODY IS AT SPAWN AND EAST IS OPEN THERE FOR THE FIRST TIME IN
#    EIGHTEEN STATES. ACTION4 is still the only candidate for east and has
#    still never been pressed where east is open; both its presses were at
#    (2,2) where east and west are void. Cols 20-24 of rows 8-12 read
#    floor right now. One press answers it.

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

  theorem dynamic_census "Exactly 79 cells have ever changed and every one has an owner, two more than last round and both of them meter cells. 23 are the panel: slot 1's eight ring pixels at rows 1-3 cols 1-3, its centre (2,2) being colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in configuration A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 8 are the burned right end of row 63, cols 56 to 63, burned in order 63,62,61,60,59,58,57,56 at commands 2,4,6,8,10,12,14,16. 23+24+24+8 = 79 = dynamic_cells. By frame-0 colour: 43 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 8 meter), 9 colour-1 (slot 2, solid at frame 0), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 43+9+24 = 76 = cells_needing_an_owner EXACTLY, the store again declining to count background-coloured cells; Dark carries the remaining 3 anyway and replay proves the arm instances them. 4096-79 = 4017 = constant_cells exactly. zero_space's single global law lists the same 79 cells, which is a consistency check on my arithmetic and not an independent discovery."
    [probe: passed]

  theorem the_state_model_predicted_the_duplicate_count "Corroborated a second time from a number I did not fit, now over 18 states instead of 14. My manual says a state is exactly three things: which of two lattice cells the body occupies, which of two configurations the panel shows, and how many meter cells are burned. Burns at s_k are floor(k/2). Body: spawn spawn (2,2) (2,2) (2,2) spawn (2,2) spawn spawn spawn (2,2) spawn (2,2) (2,2) spawn (2,2) spawn spawn. Panel: A A A A A B B A A A A B B B A A B B. Exactly five pairs coincide -- s0=s1, s2=s3, s8=s9, s12=s13, s16=s17 -- which predicts 18-5 = 13 distinct states. The store reports distinct_states = 13. Any mechanism I am missing that varied a pixel in those eighteen frames would have broken a coincidence and pushed the count above 13; any spurious mechanism would have pushed it below. Two independent hits (10 from 14 states, 13 from 18) is why I do not read the three vacuous probes as evidence of a missing mechanism."
    [depends: dynamic_census, the_meter_is_a_two_command_clock  probe: passed]

  theorem the_meter_is_a_two_command_clock "8 out of 8 and 9 out of 9 and I consider it closed. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right end. Burns occurred at commands 2,4,6,8,10,12,14,16 and at no other command; commands 1,3,5,7,9,11,13,15,17 burned nothing. The key pressed is irrelevant and every key pressed at both parities now says so in its own voice: ACTION1 burned at 8 and not at 1 or 17, ACTION2 burned at 2,6,10,12 and not at 15, ACTION4 burned at 4 and not at 13, ACTION5 burned at 14 and 16 and not at 5, 7 or 11. ACTION3 has only ever been pressed at odd indices. Cols 56-63 are spent, 56 cells remain, so roughly 112 commands remain before the bar is out. The next command is index 18, which is EVEN, and it will burn (63,55) whatever is pressed."
    [depends: meter_burn_next_key1, meter_burn_next_key4  probe: passed]

  theorem no_frame_function_can_predict_the_burn_and_five_identical_pairs_prove_it "The sharpest thing this round bought and it is a proof about my own form, not a guess. Group the eighteen commands by the burn count b visible at their start: exactly two commands share each b, the odd one k=2b+1 which does not burn and the even one k=2b+2 which does. For b = 0, 1, 4, 6 and 8 the two starting frames are PIXEL-IDENTICAL (s0=s1, s2=s3, s8=s9, s12=s13, s16=s17). So for five of the nine burn counts there is no function of the frame whatsoever -- not mine, not anyone's -- that can output burn for one and no-burn for the other. The world is driven by a command counter that is drawn nowhere. What is NOT yet proven is that the world fails to be a function of (frame, action): each of those five pairs was given two DIFFERENT keys, so a table that memorises the burn count per key survives the record. That table would need one clause per burn, would compress nothing, and would predict nothing about command 18, which is why I do not write it. CONSEQUENCE I ACCEPT: my manual is required by constraint 5 to be a function of (frame, action), so it is required to be wrong about this world's meter, and the only open question is where I choose to be wrong."
    [depends: the_meter_is_a_two_command_clock, the_state_model_predicted_the_duplicate_count  probe: passed]

  theorem the_burn_rules_are_deliberate_mis_attributions_and_the_dated_failure_arrived_on_schedule "Last round I dated this failure to the transition and to the pixel: 'the moment command 14 burns (63,57), REPLAYING t13 will fire meter_burn_next_key4 and predict a burn the world did not deliver -- exactly one wrong pixel at (63,57) on exactly transition t13'. Command 14 burned (63,57). The same mechanism then took a second scalp at t15, where key(2) from s14 finds the newly-instanced (63,56) rendering 9 with a colour-1 right neighbour. THE FULL LEDGER, computed by hand over all seventeen transitions with the current instance set (cells 56-63 instanced, 55 and left of it still board): correct at t1 t2 t3 t4 t5 t6 t7 t8 t9 t10 t11 t12 t17, wrong at t13 (misfire, key4), t14 (missed burn, key5 has no rule), t15 (misfire, key2), t16 (missed burn, key5). Thirteen of seventeen, four one-pixel divergences, all of them at (63,57) or (63,56). WHY I DO NOT DELETE THE RULES: deleting all four leaves eight real burns undrawn and replays 9/17. WHY I DO NOT ADD A KEY5 BURN RULE: it would fix t14 and t16 and break t5, t7 and t11, netting 12/17; see i_refused_a_witnessed_key5_burn_rule_and_here_is_the_arithmetic. WHY I DO NOT PATCH THE KEY4 RULE WITH A PANEL GUARD: the panel does separate t4 from t13 and would buy 14/17, and I refuse it because the same trick provably cannot save key(2) -- the burning s9 and the non-burning s14 are both (spawn, configuration A) and differ ONLY in the meter itself, so the meter would have to explain the meter. A patch that works on one key and is impossible on another is fitting, not physics. I keep 13/17, I name the four transitions, and I predict certify will report first_divergence at t13, cell (63,57)."
    [depends: no_frame_function_can_predict_the_burn_and_five_identical_pairs_prove_it  probe: pending]

  theorem i_refused_a_witnessed_key5_burn_rule_and_here_is_the_arithmetic "Constraint 2 says no entry without evidence; it does not say every witnessed pattern earns an entry. A rule 'when act=key(5) and colored(?p,9) and colored(rightof(?p),1) then recolored(?p,1)' now has two clean witnesses, t14 and t16. I refuse it. With the current instance set it would also fire at t5 (leading edge (63,61)), t7 ((63,60)) and t11 ((63,58)), where the world burned nothing: two transitions repaired, three broken, replay 12/17 instead of 13/17. This is the clearest single demonstration that the burn is not keyed on the key, and I record the refusal rather than the rule so that the next desk does not rediscover it as a gain."
    [depends: the_burn_rules_are_deliberate_mis_attributions_and_the_dated_failure_arrived_on_schedule  probe: passed]

  theorem every_command_from_here_refutes_the_manual_at_row_63_and_here_is_the_arithmetic "My answer to P-09, P-10 and P-11, and it corrects my own reading from last round. I said the frontier was vacuous at EVEN indices; P-10 was command 15, which is odd, so that reading was too narrow. The corrected reading covers all three and every future command. At an EVEN command the world burns the leading edge, which had never changed and therefore has no instance, so no rule of mine and no ablation of my manual and not `inert` can draw it -- P-09 (command 14, (63,57)) and P-11 (command 16, (63,56)) are exactly this, one pixel each. At an ODD command with key 1, 2 or 4 the leading edge HAS an instance by then and my burn rule fires on it, so the manual predicts a burn the world withholds -- P-10 (command 15, key 2, (63,56)) is exactly this, again one pixel. Since every hypothesis in the frontier is my manual or an ablation of it plus `inert`, and ablation can only DELETE rules, the whole lattice dies together on the even case and the realised gain is 0 bits by arithmetic rather than by ignorance. THE ODD CASE IS DIFFERENT AND I SAY SO: there an ablation that deletes the burn rule WOULD have survived, so P-10 should have reported one survivor, not zero. Two readings fit that: either the arm evaluated the frontier against a predecessor state one pixel stale, or the ablation set does not include the burn rules. WHAT DISCRIMINATES: certify's next replay. If it reports 13/17 with first_divergence at t13 then the instance set is recomputed from the whole store and my ledger above is exact; if it reports 17/17 then the arm replays with a per-transition instance set and the refutations are an artefact of stale predecessors. Either way, ONE PIXEL ON ROW 63 IS NOT A MISSING MECHANISM, and it has now consumed six rounds."
    [depends: i_cannot_draw_the_leading_edge_burn, the_burn_rules_are_deliberate_mis_attributions_and_the_dated_failure_arrived_on_schedule  probe: pending]

  theorem i_cannot_draw_the_leading_edge_burn "A law of this manual rather than of this world, now paid eight times. The arm instances exactly the cells that have ALREADY changed, so the next cell to burn is board, has no instance, and NO RULE OF MINE CAN RECOLOUR IT. I checked whether any declaration escapes this: arc-instances: all covers only cells the board cannot explain, so it never reaches a static cell; a landmark can be named at (63,55) but landmarks are cells, not objects, and every event in the language takes an object as its first argument, so a landmark cannot be recoloured. There is no construction in this DSL that draws a cell before its first change. CONSEQUENCE FOR READING REFUTATIONS: a divergence set consisting only of the bar's leading edge does not implicate this manual and must not consume a round."
    [depends: the_meter_is_a_two_command_clock  probe: passed]

  theorem the_probe_designer_is_blind_to_the_commands_worth_buying "The most useful thing I can tell the arm this round, and it is about the arm. Every hypothesis in the frontier is my manual or an ablation of it. Two ablations differ in their prediction ONLY on a command where some rule fires. So expected information gain is maximised exactly where my manual already fires most rules, and is exactly zero on every command my manual says nothing about. Look at what was bought: commands 14, 15 and 16 were ACTION5 at (2,2), ACTION2 at spawn and ACTION5 at (2,2) -- the three highest-rule-count commands on the board, each already at full coverage, two of them explicitly pruned by the playbook I wrote last round; command 17 was ACTION1 at spawn, a silence already witnessed twice. Meanwhile ACTION4 where east is open, ACTION6 and ACTION7 have expected gain 0.000 in that frontier by construction, and they are the only three commands that could tell me something I do not know. THE TRAP IS STRUCTURAL, NOT A BUG: a frontier built by deleting rules cannot represent 'a rule I am forbidden to write because it has no witness'. THE ONLY INSTRUMENT THAT WORKS ON THOSE COMMANDS IS THE RAW DIFF, which the arm is given for free on every command. My manual predicts ZERO changed cells for all three, so any non-empty diff outside row 63 is legible without any frontier at all. WHAT WOULD OVERTURN THIS: a fourth consecutive command chosen from the witnessed set would confirm it; a probe report showing non-zero expected bits for a command where no rule of mine fires would refute it."
    [depends: every_command_from_here_refutes_the_manual_at_row_63  probe: pending]

  theorem the_world_is_not_a_function_of_the_drawn_frame_and_one_repeat_would_prove_it "Now literally one command from a strict proof, and I still rank it low. s16 and s17 are PIXEL-IDENTICAL -- body at spawn, panel B, eight burns -- which is part of the arithmetic that makes distinct_states come out at 13. From s16 the world was given ACTION1 (command 17) and changed nothing. The body stands on s17 now. Give it ACTION1 again (command 18, even) and the clock says (63,55) burns: identical state, identical action, different successor, hidden state proven rather than argued. I RANK IT LOW AND SAY WHY: constraint 5 obliges my manual to be a function of the frame, so I already know I must be wrong about one member of that pair; the divergent pixel is the leading edge I cannot draw in any case; and the finding changes no rule and opens no cell. It is a cheap proof of something I would not act on differently, and I record it so nobody can sell it to me later as a discovery."
    [depends: no_frame_function_can_predict_the_burn_and_five_identical_pairs_prove_it  probe: pending]

  theorem the_down_key_may_be_a_shuttle_and_five_presses_have_all_been_from_spawn "STILL THE LARGEST UNEXAMINED ASSUMPTION IN THIS FILE after seventeen commands, and it got worse rather than better this round. ACTION2 has now been pressed FIVE times and every single one was from spawn; ACTION5 has been pressed FIVE times and every single one was from (2,2). Not once has either been pressed anywhere else. So every observation remains equally consistent with two readings. READING DOWN: ACTION2 moves the body one lattice cell south wherever it stands, ACTION5 one north, and the maze theorem is about a maze. READING SHUTTLE: ACTION2 means go to cell two and ACTION5 means go back to cell one, the world is a two-cell rocker, and the lattice, the comb and the socket are scenery. The press that decides it is ACTION2 from (2,2), which now costs TWO commands because the body was walked back to spawn: one ACTION2 to stand at (2,2), a second to ask the question. That is the price of the last four commands. Lattice (3,2) is rows 20-24 cols 14-18, read floor in the current frame, and separator row 19 is floor across cols 13-31, so the destination ring is clear. WHAT MY MANUAL PREDICTS FOR THE SECOND PRESS, so it can cost me: NOTHING except an undrawable burn -- key2_body_leaves ranges over Glyph9 and the body would stand on Vacated cells, key2_body_arrives ranges over Vacated and rows 20-24 are board with no instances. If the body moves I am wrong by 48 cells, 24 of which I could have written a rule for and deliberately did not, because constraint 2 forbids a rule with no witness."
    [depends: key2_body_leaves, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_action_map_after_seventeen_transitions "WITNESSED, with the negatives stated as negatives. ACTION2 CARRIES THE BODY SOUTH FROM SPAWN: t2, t6, t10, t12, t15, the 5x5 ring from rows 8-12 to rows 14-18, five times, in both panel configurations. ACTION5 CARRIES IT BACK NORTH: t5, t7, t11, t14, t16, five times, each with a panel toggle. NEGATIVES AT SPAWN, where north and west are void and south and east are open floor: ACTION1 did nothing at t1, t8 and t17, ACTION3 did nothing at t9 -- so NEITHER ACTION1 NOR ACTION3 IS EAST, and both are consistent with being north or west. NEGATIVES AT (2,2), where north and south are open and east and west are void: ACTION3 did nothing at t3, ACTION4 did nothing at t4 and t13 -- so neither is up and neither is down, and both are consistent with being horizontal. Combine: ACTION3 is neither vertical nor east, which leaves west, and west is void at both cells it has been pressed from, explaining all three of its silences without inventing anything. ACTION4 IS STILL THE ONLY REMAINING CANDIDATE FOR EAST AND HAS STILL NEVER BEEN PRESSED WHERE EAST IS OPEN -- and for the first time since command 2 the body stands where east IS open, rows 8-12 cols 20-24 reading floor in the current frame. The residue: ACTION1 is consistent with up and so is ACTION5, and two up keys is a smell; one press of ACTION1 from (2,2) separates them, and it has never been pressed there."
    [depends: key2_body_arrives, key5_body_respawns  probe: pending]

  theorem action5_is_up_or_home_or_undo_and_a_third_cell_separates_them "Five witnesses now and all five moved the body from (2,2) to spawn, a move that up, return-home and undo-last-move predict identically, so this store still cannot separate them. The separator is unchanged and is a shape, not a route: stand two lattice steps from spawn and press ACTION5 once. Up predicts one step back; home predicts a jump of two cells; undo predicts one step back along the arrival direction, which differs from up as soon as the last step was horizontal -- which is exactly what an east step would give me. My rules encode none of the three: key5_body_respawns is guarded on PIXELS, a Glyph9 cell rendering 5 whose neighbour above renders 5, so it is a spawn-ring refill rule and nothing more. As written it fires from ANY state where the spawn ring reads floor, so from a third cell my manual predicts the body is DRAWN AT SPAWN WITHOUT BEING ERASED where it stood: two bodies, 24 wrong pixels, priced here in advance."
    [depends: key5_body_respawns, the_action_map_after_seventeen_transitions  probe: pending]

  theorem the_spawn_probe_guard_is_now_one_press_from_being_tested "Thirteen rules carry colored(spawn_probe, 5), which reads 'the body is not at home'. All five ACTION5 witnesses had the body one cell south, so the guard has never been tested with the body home: ACTION5 has never been pressed at spawn in eighteen states. THE BODY IS AT SPAWN RIGHT NOW, so the test is one press and it is cheaper than it has ever been. My manual predicts ZERO changed cells for ACTION5 here -- the panel rules are gated off by the guard, key5_body_clears finds no Vacated cell rendering 9, key5_body_respawns finds no Glyph9 cell rendering 5 -- so any change at all is legible in the raw diff. If the panel toggles anyway, thirteen rules are guarded on the wrong thing and I under-predict 23 pixels; if the body jumps somewhere, ACTION5 is not 'up' at all. Both outcomes are worth more than a sixth repetition of the shuttle."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: pending]

  theorem the_panel_is_a_two_slot_selector_toggled_by_action5 "Both directions witnessed five times between them, A to B at t5, t11 and t16 and B to A at t7 and t14, and the current frame re-read pixel by pixel is configuration B. A: slot 1's ring reads 9 with underline 1 reading 9, slot 2 reads solid 1 with underline 2 reading 0. B: slot 1's ring reads 2 with underline 1 reading 0, slot 2 reads a ring of 9 with its centre hollowed to 0 and underline 2 reading 9. THE READING: two slots, an underline under each, and the underlined slot is also the one rendered in colour 9 -- a two-item selector whose cursor ACTION5 advances, wrapping after two. The two glyphs are a hollow 3x3 square and a solid 3x3 square; the body is a hollow ring and the knob at rows 9-11 cols 39-41 is a solid 3x3 block, which is a suggestive pairing and nothing more. WHAT I DO NOT CLAIM: what the selection selects. ACTION2 moved the body identically from configuration A at t2, t10 and t15 and from configuration B at t6 and t12, and ACTION4 was inert in configuration A at t4 and in configuration B at t13 -- five cross-configuration comparisons and not one difference in net effect. If the selection matters at all it matters to a key never pressed, which is ACTION6 or ACTION7."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, key5_underline2_dims  probe: passed]

  theorem the_goal_is_absent_because_no_instance_can_name_the_socket "I decline a goal clause for a fourth time, the rider's number is 11 turns and 15 actions with no target, and I accept that number as the price of this position rather than pretending it away. The winning position I believe in is lattice cell (8,7), rows 50-54 cols 44-48, whose 24 ring pixels read floor and whose centre (52,46) is a lone colour-9 pip inside a three-sided colour-9 bracket. Four forms of goal are available and every one is refuted. (1) `Cart.pos = exit_cell` needs ONE named instance; arc-instances: all gives me Glyph9_r8c14 and forty-two siblings and there is no instance called Glyph9, and a second colour-9 type would be indistinguishable to an arm that looks objects up by colour alone. (2) A count over the socket interior has nothing to range over: those cells have never changed, so they are board and carry no instances. (3) Counts over the four types I do have are all either true in some observed state -- count(Vacated, color = 9) = 0 holds in eleven of eighteen, count(Glyph9, color = 5) = 24 holds in seven -- or false everywhere and unreachable, like count(Spent, color = 0) = 9, which is exactly the fake goal the rider warns is worse than none. I also considered and rejected count(Glyph9, color = 1) = 64: it is false in every observed state and perfectly writable, and it says 'the clock has run out', so a planner given it would race to lose. (4) The goal cannot be conjunctive; the section takes one equation, and 'body away from spawn AND away from (2,2)' needs two. THE PRICE: is_goal compiles to False, plan returns no_goal_declared, commit never runs, and all eighteen commands have been probes. THE OBSERVATION THAT ENDS THIS: a goal becomes writable the moment any pixel of the bracket rows 49-55 cols 43-49, or the pip (52,46), or any colour-8 pixel of the comb, changes colour -- those cells become dynamic that instant, acquire instances, and a count over them becomes both writable and false in every earlier state. Nothing the body has done in eighteen commands can cause that, because it has not left a two-cell corridor. THE GOAL IS DOWNSTREAM OF REACH, REACH IS DOWNSTREAM OF THE EAST KEY, AND THE EAST KEY IS ONE PRESS AWAY."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_action_map_after_seventeen_transitions  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 ring with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2 plus a one-row fragment at row 48 cols 42-50 that cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in eighteen frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it stands at (1,2) now. THIS THEOREM IS HOSTAGE TO ONE PRESS: if the body cannot leave those two cells, there is no maze, only a rocker, and this theorem and the four below it are scenery."
    [depends: key2_body_arrives, the_down_key_may_be_a_shuttle_and_five_presses_have_all_been_from_spawn  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed ten times now: (16,16) stayed 5 at t2, t6, t10, t12 and t15 while its 24 neighbours turned 9, and (10,16) did the same in reverse at t5, t7, t11, t14 and t16. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_cannot_be_stood_on_and_that_is_why_the_east_walk_ends_in_a_bump "Read off the current frame and it changes what I expect the east key to be for. Lattice (1,6) is rows 8-12 cols 38-42; the knob is a solid 3x3 colour-8 block at rows 9-11 cols 39-41, which is precisely the centre 3x3 of that cell. A body is 5x5 minus its centre pixel, so eight of its 24 ring pixels would have to overlap colour 8: by the aperture reading, (1,6) is NOT enterable, and only its exact centre is free. The four cells (1,2) to (1,5) are clear floor. So if ACTION4 is east, the body can walk C=2,3,4,5 and then meet the knob head-on with nowhere to go. That is either a dead end or the intended interaction, and the two are distinguished by one pixel: any colour-8 pixel changing. I record this as the reason a bump is worth buying and not as a mechanism -- not one colour-8 pixel has moved in eighteen frames, so colour 8 is board and no object owns it."
    [depends: the_maze_is_a_six_pixel_lattice, the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell again against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 50-54. Rows 49 and 55 are separator rows and cols 43 and 49 separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side left as floor. Inside it, rows 50-54 cols 44-48 are floor except the lone colour-9 pixel at the exact centre (52,46). Overlay the body standing there -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel. The bracket has not changed in eighteen frames, so it is board and no object owns it; the first time any of it changes, those cells become dynamic and the goal section can finally be written."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn under the DOWN reading and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem at col 40 running from row 12 to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18 with floor gaps only at (39,14) and (41,14). ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. The first colour-8 pixel that changes turns this theorem into physics and hands me both a rule and a goal."
    [depends: the_maze_is_a_six_pixel_lattice, the_knob_cannot_be_stood_on_and_that_is_why_the_east_walk_ends_in_a_bump  probe: pending]

  theorem two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Eighteen commands and TWO OF SEVEN ACTIONS HAVE NEVER BEEN TRIED ONCE. In this action family one of them is normally a click carrying coordinates, and that matters here for a specific reason: the knob is a 3x3 target the body provably cannot stand on, the panel is a two-item selector whose selection provably changes nothing about ACTION2 or ACTION4, and a selector that selects nothing for the five keys I have tried is a selector for a key I have not. I cannot write a click rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5 or panel pixels moving, and never its precondition. My manual predicts ZERO cells for both keys, so any change is legible in the raw diff, and certify adjudicates five actions rather than seven, which means those two columns of the transition table are unexamined rather than clean."
    [probe: pending]

  theorem the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_defect "Priced in advance so it cannot be sold to me as a surprise, and now priced for the east step specifically. The arm instances exactly the cells that have already changed, so any lattice cell the body has never entered is board and has NO instance. An east step from spawn to (1,3) costs 24 undrawable arrival pixels at rows 8-12 cols 20-24, plus 24 departure pixels at the spawn ring which NO rule of mine erases -- key2_body_leaves is guarded on the pixel six rows BELOW rendering 5, which is a southward move and nothing else. So 48 wrong pixels on the first east step, 24 on the second, 0 thereafter. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12 cols 14-18, Vacated elsewhere -- because typing is by frame-0 colour and all that floor was 5. A manual that heals one step behind is the price of this arm, and those pixels are tuition, not damage. THE COROLLARY THE ARM MUST HEAR: the probe frontier evaluated on that command will be vacuous for the same reason row 63 makes every command vacuous, and its 0 bits must not be read as a refutation."
    [depends: the_maze_is_a_six_pixel_lattice, every_command_from_here_refutes_the_manual_at_row_63  probe: pending]

  theorem silence_is_a_prediction_and_four_of_seven_silences_at_spawn_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says 'I do not know', it says 'nothing happens', in the same voice it uses for things it has seen. Audit the seven actions at spawn, where the body stands. key(1): inert, WITNESSED three times, t1 t8 t17 -- settled and not worth a fourth. key(2): carries the body south, witnessed five times -- settled. key(3): inert, WITNESSED once at t9. key(4): NO WITNESS HERE, and this is the east question. key(5): NO WITNESS HERE, and this is the guard shared by thirteen rules. key(6) and key(7): NO WITNESS ANYWHERE. So four of seven silences at this cell are forged death certificates, and the two most valuable presses on the board are among them."
    [depends: the_action_map_after_seventeen_transitions, the_spawn_probe_guard_is_now_one_press_from_being_tested  probe: pending]

  theorem the_cascade_length_is_a_free_channel_and_it_keeps_paying "ACTION2 returned 7 frames from configuration A at t2, t10 and t15, and 9 frames from configuration B at t6 and t12 -- five for five on a split I predicted three rounds ago. ACTION5 returned 9 frames all five times, in both directions of the toggle, and every no-op returned 1. So the animation length is not a function of the key alone and the panel configuration is the one correlate with a witness. This is hidden state I discard by construction, since cascade single_frame compares only net effect, and it is the ONLY evidence I have that the panel configuration changes anything at all -- the net pixel effect of ACTION2 is identical in both configurations. It costs nothing in replay and buys nothing in prediction; I keep reading it because it is free, and because if the selector ever does something visible I expect the frame count to have warned me first."
    [depends: the_panel_is_a_two_slot_selector_toggled_by_action5  probe: passed]

  theorem the_no_op_rule_fails_the_gain_test_and_i_keep_it_for_a_narrow_reason "key3_inert_below_spawn recolours one pixel to the colour it already has, has two witnesses on transitions where zero cells changed, and replay is identical without it. It explains no pixel and lengthens the manual, so it fails constraint 3 and I say so rather than dressing it up. The reason I keep it: it is the ONLY occurrence of act=key(3) in the file, and deleting it narrows the action set certify adjudicates from five keys to four. Note what that reason implies about keys 6 and 7, which appear nowhere: certify's adjudicated pairs cover five of seven columns, and the two missing columns are unexamined rather than clean."
    [depends: key3_inert_below_spawn, two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap  probe: passed]

  theorem the_rules_are_pairwise_exclusive_and_off_board_cell_terms_are_false "Constraint 5, re-checked by hand over all four instance types in both panel configurations after the meter grew by two more cells. Under key(2): body_leaves needs below-six to render 5, which is off-board and therefore false for any row past 57, so it cannot fire on a meter cell; the two burn rules split on rightof = wall against a colour test on rightof, which cannot both hold. Under key(5) the type Glyph9 is split five ways by COLOUR FIRST -- 5 for respawns, 9 for the two dim rules, 2 for slot1_lights, 0 for underline1_lights -- and colours 2 and 0 occur on no other Glyph9 cell in any observed state, so the return half needs no geometry; no meter cell ever renders 5, so respawns cannot reach row 63. The two colour-9 rules are then split by above-four: slot1_dims needs it to BE WALL, true only for rows 0-3; underline1_dims needs a COLOUR TEST on it, which is false off-board rather than raising, so it selects row 5 and excludes rows 0-3, and its above-six wall test excludes the meter at row 63. Spent splits by colour into 1 against 9 and 0; within colour 1 the geometry is row 1 by above-two wall, row 3 by a colour test on above-two, row 2 by above-three wall plus a colour test on above-one, and within row 2 col 5 by leftof-six wall, col 6 by leftof-seven wall plus a colour test on leftof-one, col 7 by a colour test on leftof-two. Dark splits by colour 0 against 9. Not one rule uses `not`, deliberately. Certify reported 0 clashes over 70 adjudicated pairs."
    [depends: key2_body_leaves, key5_slot2_centre_darkens, key5_slot1_lights  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body is at spawn, rows 8-12 cols 14-18 rendering 9 with the aperture (10,16) rendering 5; the panel is in configuration B; eight meter cells are burned at row 63 cols 56-63; the next command index is 18, which is EVEN, so under the clock it burns (63,55) whatever is pressed and I cannot draw that cell. CERTIFY: I predict replay 13/17, divergences at t13, t14, t15 and t16, one pixel each, first_divergence at t13 cell (63,57); if it reports 17/17 my ledger is wrong about how instances are computed and every claim in every_command_from_here_refutes_the_manual_at_row_63 must be re-read. ACTION4 HERE, my first choice: my manual predicts ZERO cells and has NO WITNESS for that silence at this cell. If the body steps east to (1,3) I pay 48 undrawable pixels already priced, ACTION4 is east, the maze is real, and lattice row 1 opens toward the knob. If nothing moves, the last candidate for east among keys 1-5 is eliminated and east belongs to key 6, key 7 or to nothing. ACTION5 HERE: predicted zero, never pressed at spawn, and it tests the guard carried by thirteen rules. ACTION6 or ACTION7: predicted zero, never pressed anywhere, and the only keys that could give the selector something to select. ACTION1 HERE: predicted zero, witnessed zero three times, worth only the identical-state proof I have ranked low. ACTION2 HERE: predicted 48 cells I draw correctly plus an undrawable burn, every rule already at full coverage, and it buys nothing except standing on (2,2) so that the shuttle question can be asked next command. THE SINGLE OBSERVATION THAT WOULD MOST CHANGE THIS FILE is unchanged: any colour-8 pixel of the comb or the wire changing, because that turns the gate theorem into physics and makes the goal writable."
    [depends: the_action_map_after_seventeen_transitions, the_meter_is_a_two_command_clock  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter has FLIPPED SIGN: the ten-track unsplit variant now reports gain +628 bits where it reported -1629 last round, while split-by-colour stays catastrophic at -56428. I still take its TRACK LIST and not its verdict, and this round the list dates my panel rules a third time and independently. obj0 (colour 9, eight cells, 3x3, all eighteen frames) and obj2 (colour 9, 1x3, all eighteen frames) are slot 1's ring and underline 1 persisting through all five toggles, so it does not see the panel as appearing and vanishing, which corroborates a marker with two seats rather than two objects. The birth frames of the transient tracks are 5, 7, 11, 14 and 16: obj5 (colour 2, first frame 5), obj6 (colour 1, first frame 7), obj7 (colour 2, first frame 11), obj8 (colour 1, first frame 14), obj9 (colour 2, first frame 16). Those are EXACTLY my five toggle transitions, in order, from an engine that has never seen my rules -- and obj9, colour 2, present 2 frames, is slot 1 dimmed and still dim in the current frame, which is configuration B. obj4 is the whole 64-cell row-63 bar, of which 8 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body: connected_components(4) cannot see the mover, because the mover is a ring adjacent to floor on every side, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 17 transitions constrain rank 10 of 395 features, null space dimension 385 -- and its one global law is my census cell for cell, 79 cells including row 63 cols 56-63, a consistency check and not a discovery. cegis_miner refuses every track again and its verdict, 'the world does not narrate as one mover', is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= READ THIS FIRST: THE LAST FOUR COMMANDS BOUGHT NOTHING =========
# Commands 14-17 were ACTION5 at (2,2), ACTION2 at spawn, ACTION5 at
# (2,2), ACTION1 at spawn. Every one repeated a key-cell pair already at
# full coverage. Two of them were explicitly named in this file's DO NOT
# BUY list last round. Zero new mechanisms, zero new lattice cells, and
# the shuttle question that has been first on this page for three rounds
# is now MORE expensive than it was, because the body was walked back to
# spawn and reaching (2,2) costs a command before the question can even
# be asked.
#
# WHY THAT KEEPS HAPPENING, and it is not carelessness: the probe
# frontier is my manual plus ablations of it. Two ablations differ only
# where a rule FIRES. So expected-bits is maximised exactly on the
# commands my manual already explains, and is exactly 0.000 on every
# command it says nothing about -- which is every command worth buying.
# See theorem the_probe_designer_is_blind_to_the_commands_worth_buying.
# THE INSTRUMENT FOR THOSE COMMANDS IS THE RAW DIFF, which is given for
# free. My manual predicts ZERO changed cells for ACTION4 here, for
# ACTION5 here, for ACTION6 and for ACTION7, so ANY non-empty diff
# outside row 63 is a discovery and needs no frontier to read.
#
# ========= AND EVERY COMMAND FROM NOW ON WILL LOOK REFUTED =========
# Even command: the world burns the meter's leading edge, which has no
# instance yet, so nothing in the frontier can draw it -- one wrong pixel
# on row 63. Odd command with key 1, 2 or 4: my burn rule fires on the
# edge that has an instance by then, so I predict a burn that does not
# come -- one wrong pixel on row 63. That is arithmetic, not ignorance;
# the manual explains it and prices it. DISCOUNT ANY DIVERGENCE WHOSE
# CELLS ALL LIE IN ROW 63 AND READ THE REST OF THE DIFF.
#
# ========= THE ONE THING WORTH BUYING NOW =========
# THE UNTESTED HORIZONTAL KEY, ACTION4, FROM WHERE THE BODY STANDS.
# For the first time since command 2 the body is at spawn, and at spawn
# east is OPEN: rows 8-12 cols 20-24 read floor in the current frame.
# ACTION4 has been pressed twice and both times at (2,2), where east and
# west are both void and its silence means nothing. It is the last
# candidate for east among keys 1-5. One press, and it answers whichever
# way it falls:
#   If the body moves east: ACTION4 is east, the body stands in a THIRD
#   lattice cell for the first time, the maze is real and the rocker
#   reading dies, ACTION5 from that cell then separates up from home from
#   undo, and lattice row 1 runs C=2,3,4,5 to the knob at C=6.
#   If nothing moves: east belongs to key 6, key 7 or to nothing, and
#   four theorems about routes lose their footing. That is a bigger
#   finding for the same command.
# The 48 pixels a first east step would cost me are priced in advance in
# the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_defect.
# They are tuition. They must not consume a round.
#
# SECOND: ACTION5 AT SPAWN. Never pressed here in eighteen states. It is
# the untested half of the guard carried by thirteen rules, and my manual
# predicts ZERO cells for it, so the raw diff answers it outright.
# THIRD: ACTION6, then ACTION7. Never pressed anywhere in eighteen
# commands; the panel is a selector that provably selects nothing for the
# five keys already tried, so it selects for a key not yet tried.
# FOURTH: the shuttle question -- stand on (2,2), then ask the down key
# to move again. Two commands, and it decides whether five theorems are
# about a maze or about scenery.
# DO NOT BUY: the up-key at spawn (silence witnessed three times); a
# sixth down-press from spawn or a sixth up-press from (2,2) (every rule
# already at full coverage); the horizontal key at (2,2) again; any probe
# ranked because a refutation fired on it or because many rules fire.
#
# ========= THERE IS STILL NO GOAL, AND THE REASON IS REACH =========
# theorem the_goal_is_absent_because_no_instance_can_name_the_socket
# gives the argument and accepts the price: is_goal is False, plan
# returns no_goal_declared, commit never runs, EVERY COMMAND THIS LEG IS
# A PROBE. A goal becomes writable the instant any pixel of the socket
# bracket (rows 49-55, cols 43-49), its pip (52,46), or any colour-8 comb
# or wire pixel changes -- those cells become dynamic that instant and a
# count over them becomes writable and false in every earlier state.
# Nothing reachable from a two-cell corridor causes that. So: goal after
# reach, reach after the east key, east key after one press.
#
# ------------------------------------------------------------------------
# STATE 17: body at spawn, lattice (1,2), rows 8-12 cols 14-18; panel
# configuration B; eight meter cells burned (row 63, cols 56-63); 56
# unburned, so roughly 112 commands remain. Next command index 18, EVEN,
# and it burns (63,55) whatever is pressed. s17 is pixel-identical to
# s16, from which the up-key changed nothing -- so repeating that key now
# would prove hidden state, and the manual explains why that proof is not
# worth a command.

order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     rank_by_what_the_raw_diff_would_show_not_by_expected_frontier_bits [proof: lean]
order     buy_the_commands_the_frontier_scores_at_zero_because_it_is_blind_there [proof: lean]
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
heuristic lattice_cells_the_body_has_never_occupied                       [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut             [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open            [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                      [admissible: lean]

prefer    the_untested_horizontal_key_where_that_direction_is_finally_open [ev: 1/1 candidates left]
prefer    a_command_the_frontier_scores_at_zero_but_the_diff_can_read      [ev: 3/3 vacuous probes]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 4/7 keys at this cell]
prefer    stepping_into_a_lattice_cell_the_body_has_never_occupied         [ev: 2/11 cells visited]
prefer    the_press_that_decides_whether_this_world_is_a_maze_or_a_rocker  [ev: 5/23 theorems hostage]
prefer    an_action_pressed_zero_times_over_one_pressed_five_times         [ev: 2/7 actions unpressed]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 17/17 diffs]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 1/1 candidates left]
prefer    a_press_at_a_third_cell_that_splits_up_from_home_from_undo       [ev: 5/5 up_presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter obj0/obj2 (colour 9, 3x3 and 1x3, present all 18 frames)", "verdict": "entailed", "why": "these are slot 1's ring and underline 1, already owned by Glyph9 with arc-instances: all; the segmenter seeing them persist through all five toggles corroborates one marker with two seats rather than two objects, and a second type on the same pixels would invite the double claim rule 5 forbids."},
  {"id": "O-02", "subject": "mdl_segmenter obj5/obj6/obj7/obj8/obj9 (birth frames 5, 7, 11, 14, 16)", "verdict": "entailed", "why": "their birth frames are exactly my five ACTION5 toggle transitions t5,t7,t11,t14,t16, in order, from an engine that has never seen my rules -- independent dating of the panel rules, not new objects."},
  {"id": "O-03", "subject": "mdl_segmenter obj3 (colour null, 1006 cells) swallowing floor and body", "verdict": "reject", "as": "not an object", "why": "connected_components(4) merges the mover into the floor because the body is a ring adjacent to floor on every side; the absence of a mover track is the finding, and Vacated/Glyph9 already own every dynamic cell of that blob."},
  {"id": "O-04", "subject": "mdl_segmenter obj4 (colour 9, 1x64, row 63)", "verdict": "entailed", "why": "the meter bar; only its 8 burned cells are dynamic and Glyph9 already instances exactly those, which is why glyph9_instances went 41 -> 43."},
  {"id": "O-05", "subject": "mdl_segmenter positive gain (+628 bits, unsplit, 10 tracks)", "verdict": "reject", "as": "not a reason to re-segment", "why": "the sign flipped from -1629 to +628 with four more frames, but the chosen segmentation still cannot see the mover at all, so its compression number is not evidence about the vocabulary I need."},
  {"id": "O-06", "subject": "zero_space global law over 79 cells including row 63 cols 56-63", "verdict": "entailed", "as": "dynamic_census", "why": "cell for cell it is my census (23 panel + 24 + 24 rings + 8 meter); the engine self-reports THIN (rank 10 of 395), so this is a consistency check on my arithmetic and not a discovery."},
  {"id": "R-01", "subject": "meter_burn_next_key4 (misfire at t13, exactly as dated last round)", "verdict": "accept", "as": "kept, with the failure dated and paid", "why": "keeping the three burn rules replays 13/17; deleting all four leaves eight real burns undrawn and replays 9/17, so keeping is the cheaper wrong answer and I name both wrong transitions instead of hiding them."},
  {"id": "R-02", "subject": "meter_burn_next_key5 (witnessed at t14 and t16)", "verdict": "reject", "why": "it has two clean witnesses but would also fire at t5, t7 and t11 where nothing burned: two transitions repaired, three broken, 12/17 instead of 13/17 -- witnessed is not the same as earning its place."},
  {"id": "R-03", "subject": "patching meter_burn_next_key4 with a panel-configuration guard", "verdict": "reject", "why": "the panel does separate t4 from t13 and would buy 14/17, but the identical trick is provably impossible for key(2), whose burning s9 and non-burning s14 are both (spawn, configuration A) and differ only in the meter itself; a patch that works on one key and cannot exist on another is fitting, not physics."},
  {"id": "R-04", "subject": "column-pinned burn rules (one rule per burn, chaining rightof to wall)", "verdict": "reject", "why": "eight rules pinning eight columns would replay 17/17 and is pure memorisation -- zero compression by constraint 3, and it predicts no burn at all for command 18, which the clock says will burn (63,55)."},
  {"id": "R-05", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept", "as": "unchanged, ev extended to t15", "why": "t15 is t2 repeated exactly (48 cells, rows 8-18 cols 14-18, no burn since 15 is odd); both rules stay at 24/24 coverage."},
  {"id": "R-06", "subject": "the five ACTION5 panel rules for A->B and the five for B->A", "verdict": "accept", "as": "unchanged, ev extended to t16 and t14", "why": "t16 reproduced the A->B toggle and t14 the B->A toggle at full coverage; the colour sets in the diffs ([0,2,5,9]->[0,1,5,9] and back) match the manual's two configurations."},
  {"id": "R-07", "subject": "a departure rule for a body leaving a cell by any direction other than south", "verdict": "reject", "why": "no witness exists -- the body has never left a cell except southward or by the ACTION5 refill -- so constraint 2 forbids it; the 24 undrawn departure pixels of a first east step are priced in advance instead."},
  {"id": "L-01", "subject": "no_frame_function_can_predict_the_burn_and_five_identical_pairs_prove_it", "verdict": "accept", "why": "for burn counts 0, 1, 4, 6 and 8 the two commands sharing that count start from pixel-identical frames and differ in outcome, so no function of the frame can separate them -- this is read off the record, not conjectured."},
  {"id": "L-02", "subject": "the_meter_is_a_two_command_clock", "verdict": "accept", "as": "closed at 8/8 and 9/9", "why": "burns at commands 2,4,6,8,10,12,14,16 and silences at 1,3,5,7,9,11,13,15,17, with all four keys pressed at both parities now showing the contradiction in their own voice."},
  {"id": "L-03", "subject": "the_state_model_predicted_the_duplicate_count", "verdict": "accept", "as": "corroborated a second time", "why": "the model predicts exactly five coincident pairs among 18 states (s0=s1, s2=s3, s8=s9, s12=s13, s16=s17), hence 13 distinct states; the store reports 13, a number I did not fit."},
  {"id": "L-04", "subject": "the_frontier_is_vacuous_by_construction_at_even_indices (my own reading from last round)", "verdict": "reject", "as": "replaced by every_command_from_here_refutes_the_manual_at_row_63", "why": "P-10 was command 15, which is odd, so 'even indices' was too narrow; the corrected reading covers odd commands too, because my burn rules misfire on the leading edge once it acquires an instance."},
  {"id": "L-05", "subject": "the_probe_designer_is_blind_to_the_commands_worth_buying", "verdict": "probe-pending", "why": "a frontier of ablations can only distinguish hypotheses where some rule fires, so expected bits is 0 exactly on the commands my manual says nothing about; the last four commands were all high-rule-count repeats, two of them explicitly pruned -- a fourth consecutive such choice confirms it, a non-zero expected-bits report for a command where no rule fires refutes it."},
  {"id": "L-06", "subject": "the_goal_is_absent_because_no_instance_can_name_the_socket", "verdict": "accept", "as": "declined a fourth time, with the price accepted", "why": "no single named instance exists under arc-instances: all, the socket cells are board and carry no instances, every writable count over my four types is either true in some observed state or unreachable nonsense, and the section takes one equation so the two-part condition cannot be written; the goal is downstream of reach and reach is one press away."},
  {"id": "L-07", "subject": "goal count(Glyph9, color = 1) = 64 (the meter fully burned)", "verdict": "reject", "why": "it is writable and false in every observed state, and it means 'the clock has run out', so a planner given it would race to lose -- exactly the fake goal the rider warns is worse than none."},
  {"id": "L-08", "subject": "the_knob_cannot_be_stood_on_and_that_is_why_the_east_walk_ends_in_a_bump", "verdict": "accept", "why": "the knob is a solid 3x3 at rows 9-11 cols 39-41, which is precisely the centre 3x3 of lattice (1,6); a body is 5x5 minus its centre pixel, so eight of its cells would overlap colour 8 and the cell is not enterable under the aperture reading."},
  {"id": "P-01", "subject": "P-09 (command 14, ACTION5, 0.0 bits realised)", "verdict": "reject", "as": "not evidence of a missing mechanism", "why": "the one divergent pixel is the burn at (63,57), a cell that had never changed and therefore had no instance, so the manual, every ablation of it and `inert` all die together and the gain is 0 by arithmetic; the other 71 cells the manual drew correctly."},
  {"id": "P-02", "subject": "P-11 (command 16, ACTION5, 0.0 bits realised)", "verdict": "reject", "as": "same defect, same pixel class", "why": "identical to P-09 with the burn at (63,56); the 71 body-and-panel cells match the manual exactly, which is why distinct_states still lands on 13."},
  {"id": "P-03", "subject": "P-10 (command 15, ACTION2, odd index, 0.0 bits realised)", "verdict": "probe-pending", "why": "this one is NOT explained by the even-index reading: either the frontier was rolled forward from a predecessor one pixel stale, or the instance set is recomputed from the whole store so meter_burn_next_key2 misfired on (63,56); certify's next replay discriminates -- 13/17 with first_divergence at t13 means the misfire, 17/17 means the stale predecessor."},
  {"id": "P-04", "subject": "the next command", "verdict": "probe-pending", "as": "ACTION4 at spawn, where east is open for the first time since command 2", "why": "it is the last candidate for east among keys 1-5 and has only ever been pressed where east and west are void; my manual predicts zero cells and has no witness for that silence here, so either answer is legible in the raw diff and either answer settles a direction label."},
  {"id": "E-01", "subject": "the burn fires on every even-numbered command", "verdict": "probe-pending", "as": "written as theorems, not as a rule", "why": "the guard language has no command counter and no parity term, and I showed the parity is not recoverable from any pixel, so the true law is inexpressible; I wrote the_meter_is_a_two_command_clock plus no_frame_function_can_predict_the_burn and kept three deliberately mis-attributed action-keyed rules whose four failing transitions I name."},
  {"id": "E-02", "subject": "a goal meaning 'the body stands in the socket'", "verdict": "probe-pending", "as": "written as the_goal_is_absent_because_no_instance_can_name_the_socket", "why": "the goal forms need one named instance or a count over an instanced type; arc-instances: all leaves no instance called Glyph9 and the socket cells are board, so there is nothing to name and nothing to count until a socket or comb pixel first changes."},
  {"id": "E-03", "subject": "a click action carrying coordinates (keys 6 and 7)", "verdict": "probe-pending", "as": "written as two_actions_have_never_been_pressed", "why": "act=key(6) parses but there is nowhere to put a row and a column, so any click rule would fire on every click anywhere; I can record a click's effect and never its precondition, and both keys remain untried after eighteen commands."}
]
```
```
