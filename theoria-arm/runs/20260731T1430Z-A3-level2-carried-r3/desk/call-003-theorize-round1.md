# call-003-theorize-round1

model: `claude-opus-5` · 546430 ms · $1.569824 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 38041, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 38041, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 38041, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 38041, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 46440, "type": "message"}], "output_tokens": 46440, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 74,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4019,
 "distinct_states": 12,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 77,
 "max_frames_in_one_command": 9,
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
9999999999999999999999999999999999999999999999999999999999111111
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

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 13,
  "n_states": 14,
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
    "transitions": 13
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
    "transitions": 13
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
   "recolor": 16,
   "vanish": 5
  },
  "n_frames": 14,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 14,
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
    "frames_present": 14,
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
    "frames_present": 14,
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
    "frames_present": 14,
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
    "frames_present": 1,
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
    "baseline_bits": 9720,
    "compression_ratio": 0.936831,
    "events": 36,
    "gain_bits": 614,
    "ms": 34,
    "script_bits": 9106,
    "split_by_color": false,
    "tracks": 10
   },
   {
    "baseline_bits": 9720,
    "compression_ratio": 6.727984,
    "events": 83,
    "gain_bits": -55676,
    "ms": 56,
    "script_bits": 65396,
    "split_by_color": true,
    "tracks": 37
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 77,
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
  "cells_needing_an_owner": 74,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4019,
  "distinct_states": 12,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 77,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 14,
  "steps": 14
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 77,
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
  "cells_dynamic": 77,
  "cells_used": 77,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 7,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.018182,
   "difference_rank": 7,
   "features": 385,
   "space_dimension": 378,
   "transitions": 13,
   "verdict": "THIN: 13 transitions constrain rank 7 of 385 features, so the null space has dimension 378 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 385,
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
     "c5@16",
     "c9@16",
     "c0@17",
     "c1@17",
     "c2@17",
     "c5@1
```

The full proposal stream is 1142 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 10 states / 9 transitions
# (RESET + A1 A2 A3 A4 A5 A2 A5 A2 A5). 75 cells have ever changed; this
# manual names and owns all 75.
#
# WHAT THE FOUR REFUTATIONS COST AND WHAT THEY BOUGHT
#
#   The window grew from 6 states to 10 and the four new commands were
#   A2 A5 A2 A5 -- the body oscillating between lattice (1,2) and (2,2).
#   Four probe_refutations fired and ALL FOUR are the same two holes, both
#   of which the previous manual named in advance and priced in advance:
#
#   HOLE 1, 23 cells, transition t7. The panel has two configurations and
#   the previous window only ever witnessed the A->B half, so the five
#   B->A rules sat in `laws:` as preserved text. t7 is the first B->A
#   toggle. The manual, having no rule that fires on a B-coloured panel,
#   predicted no panel change at all and was wrong on exactly the 23 panel
#   cells -- the advertised price, to the cell. The five rules are now
#   witnessed and are back in `rules:`.
#
#   HOLE 2, 1 cell, transitions t6 and t8. `meter_burn_key2_next` had been
#   removed for want of a witness; t6 burned (63,61) and t8 burned (63,60).
#   Advertised price one wrong pixel per burn, paid twice, rule restored.
#
#   The four observed hashes are all distinct while the manual's two
#   predictions repeat (25cac.../9bb17...) because the manual was a 2-cycle
#   -- panel frozen in B, meter frozen at two burns -- while the world is
#   an open trajectory. That is the exact signature of a missing toggle
#   plus a missing counter, and nothing else needed diagnosing.
#
#   WHAT NOTHING FIXES: the NEXT burn is at (63,59), a cell that has never
#   changed and is therefore board, so no object owns it and no rule of
#   mine can draw it. Every burn costs one wrong pixel in the round it
#   happens and zero pixels forever after. See the_manual_heals_one_step_behind.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t9 compress: 39]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t8,t9 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8 cov: 72/72]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8 cov: 72/72]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8 cov: 2/2]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9 cov: 72/72]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9 cov: 72/72]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 16/16]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 39 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4021 [status: counted]

  theorem the_four_refutations_were_two_holes_and_both_were_advertised "P-01 and P-03 are ACTION2 presses, P-02 and P-04 ACTION5 presses, and the manual's predictions repeat (25cac.../9bb17...) while the world's four answers are all distinct. That pattern is the whole diagnosis: my compiled manual was a two-state cycle -- spawn and one-cell-south, panel frozen in configuration B because no rule of mine fires on B-coloured panel pixels, meter frozen at two burns because meter_burn_key2_next had been struck for want of a witness -- and the world is an open trajectory whose panel toggles B->A->B and whose bar burns twice more. Two holes, both named in the previous manual's own laws, both priced in advance: 23 cells for the missing B->A half and one pixel per unwitnessed burn. Both prices came in exactly. Repair: the five B->A rules move from prose back into `rules:` with t7 as their witness (8+3+8+1+3 = 23), and meter_burn_key2_next returns with t6,t8 as witnesses. Nothing else in the manual was implicated -- key2_body_leaves, key2_body_arrives, key5_body_clears and key5_body_respawns each gained two more full-coverage witnesses and not one contradiction. I record the shape of this because it is the CHEAP kind of failure: a manual that says in advance what it cannot draw and what that will cost is refuted at a price it already quoted, and the repair is a paste, not a rethink."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, meter_burn_key2_next  probe: passed]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over three toggles now, t5 t7 t9, 23 cells every time, and ACTION2 has never touched a panel pixel in three presses. CONFIGURATION A (states 0-4, 7, 8): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B (states 5, 6, 9, and the current frame): slot 1 is a hollow colour-2 ring with underline dark; slot 2 is a hollow colour-9 ring with a dark centre and its underline lit 9. mdl_segmenter, which knows nothing of my rules, corroborates this independently and adds a reading I had not seen: its obj0 is a colour-9 8-cell 3x3 present in ALL TEN frames and its obj2 a colour-9 1x3 present in all ten, and it narrates six MOVE events -- because the hollow 9 ring and the lit underline do not appear and vanish, they TRAVEL between slot 1 and slot 2, three toggles times two objects. So the panel is one marker with two seats, not two independent lamps, and colour 9 marks the occupied seat. What is still unknown is what the seats hold. I will not guess; nothing downstream needs it, because the rules encode the swap and the swap is fully witnessed in both directions. I cannot model it AS a moving marker: the arm gives one instance per cell and `moved(o, dir)` moves one cell, so an eight-pixel ring travelling four columns is not expressible as a move and the ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_still_cannot_test_it "Unchanged in kind, stronger in count: the guard `colored(spawn_probe, 5)` now has THREE positive witnesses (t5, t7, t9 -- body away, panel toggled) and STILL NO NEGATIVE ONE, because ACTION5 has never once been pressed with the body at home. Every ACTION5 in this window immediately followed an ACTION2, so 'ACTION5 was pressed' and 'the body was away from spawn' are the same event ten times over and no guard can be credited over the other. By the letter of no-entry-without-gain the atom is still unearned. I keep it because dropping it changes no replay and because the body is at spawn RIGHT NOW: with the guard, my manual predicts SILENCE for an ACTION5 pressed here; without it, it predicts a 23-cell toggle. Silence is the prediction I want on the record, and one press refutes it or confirms it outright."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots  probe: pending]

  theorem the_meter_question_after_nine_transitions_and_why_it_is_still_open "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right. Four burns: (63,63) at t2, (63,62) at t4, (63,61) at t6, (63,60) at t8. Five silences: t1, t3, t5, t7, t9. READING A, ACTION-KEYING -- burns iff the key is 2 or 4 -- scores 9/9 and is what the three burn rules encode. READING B, COMMAND PARITY -- burns iff the command index is even -- also scores 9/9. NINE TRANSITIONS CANNOT SEPARATE THEM, and now I know exactly why: every command so far has used a key whose parity equals its own index's parity (indices 2,4,6,8 used keys 2,4,2,2; indices 1,3,5,7,9 used keys 1,3,5,5,5). The two readings are numerically identical on that diagonal and differ nowhere else. THE SEPARATOR IS THEREFORE FREE AND NEEDS NO DEDICATED COMMAND: any press that breaks the alignment settles it -- key 2 or 4 at an odd index, or key 1, 3 or 5 at an even one. Next index is 10, EVEN. One new piece of evidence STRAINS reading A without refuting it: at t3 and t4 the body stood at lattice (2,2) with left and right BOTH void, so ACTION3 and ACTION4 were blocked identically -- and ACTION4 burned while ACTION3 did not. Under action-keying that means the cost is attached to the key and not to the attempt, with keys 2 and 4 charging and 1, 3 and 5 free; under parity it is one bit of clock and no special pleading. I encode A because it is the only one the guard language can say -- there is no command counter and no phase pixel, which is the same wall cegis_miner hit when it reported 'no literal separates transition 1 from the positives' -- and I expect B to win."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis "WITNESSED: ACTION2 IS DOWN, 3/3, six rows south, one lattice cell, at t2, t6, t8. ACTION5 returns the body from lattice (2,2) to (1,2), 3/3. NEGATIVE INFORMATION, and I state it as negative because that is all it is. At spawn (1,2) up and left are void while down and right are open floor, and ACTION1 did nothing -- so ACTION1 IS NEITHER DOWN NOR RIGHT. At (2,2) the body had just vacated rows 8-12 so UP WAS OPEN, and rows 20-24 cols 14-18 are floor so DOWN WAS OPEN, while left (cols 8-12) and right (cols 20-24) were both void; ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN. Fit those together and one assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else. It explains every no-op as a blocked move and it is the conventional mapping for this action family, which is a prior and not evidence. It has one cost, and I name it: under it, ACTION3 and ACTION4 were blocked in exactly the same way at the same cell and only one of them burned the meter, which is why I expect the parity reading of the bar. THE CHEAP TEST IS ONE PRESS: the body stands at spawn, where left is void and right is open floor, so ACTION4 pressed here either steps six columns east or does not, and either answer names the east key -- if ACTION4 does not move, ACTION3 is east by elimination, since ACTION1 is already excluded from east by t1."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_and_the_two_cell_experiment_that_names_it "Three readings survive all three ACTION5 presses because all three were made from exactly one cell south of spawn, where they are indistinguishable: UP (move one cell north), UNDO (revert the last move), RETURN (jump to spawn from anywhere). They separate the moment the body is TWO cells from spawn, and they separate differently depending on the axis. Two cells EAST at lattice (1,4): up is void there so UP predicts no move, UNDO predicts one cell west to (1,3), RETURN predicts spawn at (1,2) -- three different diffs, all legible in the raw pixel count. Two cells SOUTH at (3,2): UP and UNDO both predict (2,2) and only RETURN separates. So the eastward route answers this question for free and the southward route does not, which is one more reason to go east first. Note the coupling I cannot yet break: the panel toggles on every effective ACTION5, so whatever ACTION5 is, the panel is its counter or its selector, and if ACTION5 turns out to be UNDO then the panel is plausibly an undo-parity display -- a reading I record and do not act on."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "cascade_lengths are 1, 7 and 9. Every ACTION5 returned 9 frames; ACTION2 returned 7 frames at t2 and t8 and 9 frames at t6; every no-op returned 1. So a move is animated one row per internal frame, the world reports the whole animation for a single action, and `cascade single_frame` compares only the net effect -- which is identical for all three ACTION2 presses (48 body cells, rows 8-18, cols 14-18) regardless of whether the command took 7 frames or 9. TWO THINGS FOLLOW. First, a refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, three times. ONE PRESS IS ONE LATTICE CELL, 3/3, and every distance in the playbook rests on that. Second, an anomaly I will not over-read: the two 7-frame ACTION2 presses both had the panel in configuration A and the 9-frame one had it in B. Three samples, one clean correlation, zero effect on the net frame. It is not evidence of unobservable state -- it is evidence that the animation length is a function of something the panel also depends on -- and since the net effect is what I model, it costs me nothing either way."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_world_may_still_not_be_a_function_of_the_drawn_frame "Carried as a belief and NOT proven in this window. To prove it I need two pixel-identical states from which the SAME action produced different successors; I have no such pair. The near misses: states 2 and 3 are pixel-identical (ACTION3 changed nothing at t3) but were followed by different keys; t2 and t8 are the same key from the same lattice cell but from states differing in row 63. What keeps the belief alive is the parity reading of the meter, which if true IS one bit of hidden state that flips every command and that no guard in this language can read, because no guard can read anything that is not a pixel. Operationally it matters in exactly one way: if parity wins, every burn rule I can write is an approximation with a known error rate, and I would rather say that once than rediscover it."
    [depends: the_meter_question_after_nine_transitions_and_why_it_is_still_open  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4021 + dynamic 75 = 4096, and 39+24+9 = 72 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 75. Consequence, stated as a law of this manual rather than of this world: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. The bar makes this exact and unavoidable. meter_burn_key2_next now replays t6 and t8 perfectly, because by replay time (63,61) and (63,60) are dynamic and have instances; it will still miss the FIFTH burn at (63,59), because that cell is board today. Every burn therefore costs exactly one wrong pixel in the round it first happens and zero pixels forever after, and no rewriting of the rule fixes it -- only observation does. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable too until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, 24 if I already had the leaves rule, 0 for the second step. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 75 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three; slot 2's nine, centre included because (2,6) is 1 in A and 0 in B; underline 2's three. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 4 are the burned right end of row 63: (63,63), (63,62), (63,61), (63,60). 23+24+24+4 = 75 = dynamic_cells. By frame-0 colour: 39 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 4 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 39+9+24 = 72 = cells_needing_an_owner exactly. zero_space's cell list is the same 75 cells -- it lists (2,1) and (2,3) but not (2,2), (10,14),(10,15),(10,17),(10,18) but not (10,16), and all four burned bar cells -- and its single global law restates this census."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so that the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended three times and all three started at spawn, so no rule of mine turns Vacated pixels from 9 back to 5 on an ACTION2: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. One ACTION2 from lattice (2,2) buys it. (2) EAST-WEST MOTION. Whatever the east key turns out to be, it needs a pair: 'rule keyE_body_leaves forall ?p in Glyph9 when act=key(N) and colored(?p, 9) and colored(rightof(rightof(rightof(rightof(rightof(rightof(?p)))))), 5) then recolored(?p, 5)' and its arrives-twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) A FIFTH BURN AT A CELL THAT IS STILL BOARD, which is not a missing rule but a missing instance and cannot be written at all. I state the price of all three in advance so it cannot be mistaken for a surprise: the first eastward step costs 48 wrong cells plus one if the bar burns, the first second-descent costs 24, and every fresh burn costs 1."
    [depends: key2_body_arrives, the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth `below` is row 69. So `colored(<off-board>, k)` is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen of the twenty rules rest on this and every row and column discrimination in the panel is built from it: the k-th `above` is off-board exactly when k exceeds the row, so row 1 is `above(above(?s)) = wall`, row 3 is `colored(above(above(?s)), 1)` -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is `above^3 = wall` conjoined with `colored(above(?s), 1)`. The same trick separates slot 2's middle row by column: col 5 is `leftof^6 = wall`, col 6 is `leftof^7 = wall and colored(leftof(?s), 1)`, col 7 is `colored(leftof(leftof(?s)), 1)`, pairwise exclusive, which is why the ambiguity check reports 0 clashes. Not one rule uses `not`, deliberately. The eight A->B slot-2 and underline rules could collapse to two if I could write 'not all four neighbours are colour 1', and I decline to gamble a whole round's compile on discovering whether `not` before an equality atom parses. If a future desk wants the shorter form, try it on ONE rule, not on eight."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read from the current frame: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are open, C=6 holds the knob, C=7 is void; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2; R=8 is floor from col 13 to col 48, so C=2..7. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); in ten frames the body has occupied exactly two cells, (1,2) and (2,2), and it has been at spawn in six of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed three times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in ten frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open: colour 8 leaves the comb along row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41 with a stem pixel at (12,40), all inside lattice (1,6). Not one colour-8 pixel has moved in ten frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. Four lattice cells of eastward travel put the body at (1,5) and every one of those four steps is on floor that R=1 shows open."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after ten states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the standard mapping I now favour -- 1 up, 2 down, 3 left, 4 right, 5 undo-or-return -- accounts for every key I have pressed, which makes 6 and 7 more likely to be a click and a spare than more directions."
    [depends: the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and thirty-eight siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells do become dynamic on first entry, but `count(Vacated, color = 9) = 24` would then be true of the body standing anywhere it has already been, which is not a win -- a goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in lattice (8,7) once, the playbook steers by lattice distance, and `is_goal -> False` is the honest compilation."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -2214 and -36598 bits, so its segmentation still loses to writing the pixels out and I owe it nothing structural -- but its EIGHT tracks are the round's best independent corroboration. obj1 (colour 1, nine cells, first seen frame 0, present 5 frames) and obj6 (colour 1, nine cells, first seen frame 7, present 2 frames) are slot 2 solid in configurations A; obj5 (colour 2, first seen frame 5, present 2) and obj7 (colour 2, first seen frame 9, present 1) are slot 1 dimmed in configurations B. Read the frame indices off those four tracks and you get A at 0-4, B at 5-6, A at 7-8, B at 9 -- exactly the toggle sequence my three ACTION5 rules produce, derived by an engine that has never seen my rules. obj0 and obj2 persisting through all ten frames while the segmenter narrates six moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 4 cells are dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 9 transitions constrain rank 5 of 375 features, null space dimension 370, 'nearly every vector in it is a law that is true over these states and unfalsified rather than confirmed' -- and its single global law is my census. cegis_miner refuses on every track and its verdict, 'the world does not narrate as one mover', remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. ACTION4 FROM SPAWN, command index 10: if the standard mapping holds, the world changes 48 cells in rows 8-12 cols 14-24 and burns (63,59) for 49 total, and MY MANUAL DRAWS NONE OF THEM -- no east rules exist and (63,59) is board -- so I expect a 49-cell divergence and that is the advertised price of the first step onto fresh ground, not a failure of physics. If instead ZERO cells change, ACTION4 is not east, ACTION3 is east by elimination, and action-keying is refuted too, because index 10 is even and parity demanded a burn. If exactly ONE cell changes and it is (63,59), ACTION4 is not east and both meter readings survive. ACTION2 FROM SPAWN: 48 cells I draw correctly plus a burn at (63,59) I cannot draw -- exactly one wrong pixel, every time, forever, until that cell has burned once. ACTION5 FROM SPAWN: I predict ZERO changed cells anywhere, on the strength of the spawn_probe guard and nothing else; any panel toggle there refutes the guard outright and means the toggle is bound to the key and not to the return. ACTION1 OR ACTION3 FROM SPAWN at an even index: zero cells under my manual, one cell at (63,59) under parity -- the cheapest single-bit experiment on the board, and worth buying only when no map question is open."
    [depends: the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis, the_meter_question_after_nine_transitions_and_why_it_is_still_open  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept in compressed form because the lesson is structural and cost a full round. Thirteen panel rules once carried `colored(spawn_probe, 5)` while the landmark line read `# arc-cell: carried, coordinates stripped`, which is not a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The landmark now reads `# arc-cell: (8, 14)`, the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key5_slot1_dims  probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE OF PLAY (state 9): body home at lattice (1,2); panel in configuration
# B; four meter cells burned, (63,60)..(63,63); nine commands spent; the next
# command has index 10, which is EVEN.
#
# WHAT CHANGED THIS ROUND:
#  (a) THE FOUR REFUTATIONS COST WHAT THE MANUAL SAID THEY WOULD -- 23 cells
#      for the panel's unwitnessed half, one pixel per unwitnessed burn. No
#      line below caused them and none is retracted for them.
#  (b) THE REAL FAILURE IS NOT IN THE MANUAL, IT IS HERE. Nine commands have
#      been spent and the body has occupied exactly TWO lattice cells; six of
#      those commands were spent oscillating between them. An oscillation is
#      not a probe: the second ACTION2-then-ACTION5 pair bought two witnesses
#      the first pair had already bought, and the third bought none at all.
#      New prune, and it is the load-bearing line of this file: a command
#      that returns the body to a cell it has already occupied, from a cell
#      it has already occupied, with a key already witnessed there, is dead.
#  (c) ACTION4 NOW DOMINATES ACTION3 as the way to ask the east question.
#      At spawn, left is void and right is open floor. Either outcome of one
#      ACTION4 press names the east key -- it moves, or ACTION3 is east by
#      elimination, ACTION1 having been excluded from east at t1 -- and one
#      of the two outcomes also advances four cells' worth of route toward
#      the knob at lattice (1,6).
#  (d) THE METER SEPARATOR IS FREE AND NEEDS NO COMMAND OF ITS OWN. Every
#      command so far used a key whose parity matches its own index's parity,
#      which is exactly why nine transitions cannot separate action-keying
#      from command parity. Walking east breaks that alignment on the SECOND
#      step. Buying a dedicated parity probe now would pay a command for a
#      bit that arrives free.
#  (e) ONE PRESS IS ONE LATTICE CELL, 3/3. Every distance below is counted in
#      lattice cells, not pixels.
# No stored sequence anywhere: every line is a criterion on the current frame
# plus the manual's own open questions.

order     settle_the_east_key_before_routing_toward_the_knob                 [proof: lean]
order     prefer_the_probe_that_advances_over_the_probe_that_only_answers    [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open        [proof: lean]
order     take_a_separation_that_arrives_free_over_one_that_costs_a_command  [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it         [proof: lean]
order     identify_a_direction_key_before_routing_with_it                    [proof: lean]
order     separate_two_readings_before_planning_against_either               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                 [proof: lean]
order     reach_the_switch_before_testing_the_switch                         [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end                   [proof: lean]
order     witness_a_rule_before_writing_it                                   [proof: lean]
order     spend_commands_on_information_while_the_bar_is_still_long          [proof: lean]

prune     revisits_an_occupied_cell_by_an_already_witnessed_key => dead      [proof: lean]
prune     repeats_a_transition_whose_rule_already_has_full_coverage => dead  [proof: lean]
prune     dedicated_meter_probe_while_a_map_question_is_open => dead         [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead      [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead [proof: lean]
prune     guard_whose_landmark_carries_no_arc_cell_comment => dead           [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time                [admissible: lean]
heuristic unwitnessed_rules_this_command_would_witness                       [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]
heuristic unexplained_cells_after_redraw                                     [admissible: lean]

prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree        [ev: 3/5 no_ops]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule          [ev: 3/3 moves]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has                 [ev: 2/11 cells]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    a_key_whose_parity_differs_from_the_command_index                  [ev: 0/9 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 9/9 diffs]
prefer    distance_from_spawn_that_makes_up_undo_and_return_differ           [ev: 3/3 key5]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket               [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                      [ev: 2/7 keys]
```

## Why you are being called: the surprises that fired

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '287dc66cc4b95e77', the world answered '4922abb280cd8780'

```json
{
 "action": 2,
 "observed": "4922abb280cd8780",
 "predictions": {
  "inert": "15c2e5de8c8dc96b",
  "manual": "287dc66cc4b95e77",
  "without_key2_body_arrives": "15c2e5de8c8dc96b",
  "without_key2_body_leaves": "15c2e5de8c8dc96b",
  "without_key5_body_clears": "287dc66cc4b95e77",
  "without_key5_body_respawns": "287dc66cc4b95e77",
  "without_key5_slot1_dims": "287dc66cc4b95e77",
  "without_key5_slot1_lights": "287dc66cc4b95e77",
  "without_key5_slot2_centre_darkens": "287dc66cc4b95e77",
  "without_key5_slot2_centre_resets": "287dc66cc4b95e77",
  "without_key5_slot2_ring_resets": "287dc66cc4b95e77",
  "without_key5_slot2_row1_lights": "287dc66cc4b95e77",
  "without_key5_slot2_row2_left_lights": "287dc66cc4b95e77",
  "without_key5_slot2_row2_right_lights": "287dc66cc4b95e77",
  "without_key5_slot2_row3_lights": "287dc66cc4b95e77",
  "without_key5_underline1_dims": "287dc66cc4b95e77",
  "without_key5_underline1_lights": "287dc66cc4b95e77",
  "without_key5_underline2_dims": "287dc66cc4b95e77",
  "without_key5_underline2_lights": "287dc66cc4b95e77",
  "without_meter_burn_key2_next": "287dc66cc4b95e77",
  "without_meter_burn_key2_rightmost": "287dc66cc4b95e77",
  "without_meter_burn_key4_next": "287dc66cc4b95e77"
 },
 "probe_id": "P-05"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '818eaaf57cafd7bb', the world answered 'c65bd69c07fb3c77'

```json
{
 "action": 5,
 "observed": "c65bd69c07fb3c77",
 "predictions": {
  "inert": "287dc66cc4b95e77",
  "manual": "818eaaf57cafd7bb",
  "without_key2_body_arrives": "818eaaf57cafd7bb",
  "without_key2_body_leaves": "818eaaf57cafd7bb",
  "without_key5_body_clears": "287dc66cc4b95e77",
  "without_key5_body_respawns": "287dc66cc4b95e77",
  "without_key5_slot1_dims": "818eaaf57cafd7bb",
  "without_key5_slot1_lights": "287dc66cc4b95e77",
  "without_key5_slot2_centre_darkens": "818eaaf57cafd7bb",
  "without_key5_slot2_centre_resets": "287dc66cc4b95e77",
  "without_key5_slot2_ring_resets": "287dc66cc4b95e77",
  "without_key5_slot2_row1_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row2_left_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row2_right_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row3_lights": "818eaaf57cafd7bb",
  "without_key5_underline1_dims": "818eaaf57cafd7bb",
  "without_key5_underline1_lights": "287dc66cc4b95e77",
  "without_key5_underline2_dims": "287dc66cc4b95e77",
  "without_key5_underline2_lights": "818eaaf57cafd7bb",
  "without_meter_burn_key2_next": "818eaaf57cafd7bb",
  "without_meter_burn_key2_rightmost": "818eaaf57cafd7bb",
  "without_meter_burn_key4_next": "818eaaf57cafd7bb"
 },
 "probe_id": "P-06"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'b90a6233898771e2', the world answered '0c86941f09a0caaf'

```json
{
 "action": 2,
 "observed": "0c86941f09a0caaf",
 "predictions": {
  "inert": "818eaaf57cafd7bb",
  "manual": "b90a6233898771e2",
  "without_key2_body_arrives": "818eaaf57cafd7bb",
  "without_key2_body_leaves": "818eaaf57cafd7bb",
  "without_key5_body_clears": "b90a6233898771e2",
  "without_key5_body_respawns": "b90a6233898771e2",
  "without_key5_slot1_dims": "b90a6233898771e2",
  "without_key5_slot1_lights": "b90a6233898771e2",
  "without_key5_slot2_centre_darkens": "b90a6233898771e2",
  "without_key5_slot2_centre_resets": "b90a6233898771e2",
  "without_key5_slot2_ring_resets": "b90a6233898771e2",
  "without_key5_slot2_row1_lights": "b90a6233898771e2",
  "without_key5_slot2_row2_left_lights": "b90a6233898771e2",
  "without_key5_slot2_row2_right_lights": "b90a6233898771e2",
  "without_key5_slot2_row3_lights": "b90a6233898771e2",
  "without_key5_underline1_dims": "b90a6233898771e2",
  "without_key5_underline1_lights": "b90a6233898771e2",
  "without_key5_underline2_dims": "b90a6233898771e2",
  "without_key5_underline2_lights": "b90a6233898771e2",
  "without_meter_burn_key2_next": "b90a6233898771e2",
  "without_meter_burn_key2_rightmost": "b90a6233898771e2",
  "without_meter_burn_key4_next": "b90a6233898771e2"
 },
 "probe_id": "P-07"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '15c2e5de8c8dc96b', the world answered '06e79195f0adc15f'

```json
{
 "action": 5,
 "observed": "06e79195f0adc15f",
 "predictions": {
  "inert": "b90a6233898771e2",
  "manual": "15c2e5de8c8dc96b",
  "without_key2_body_arrives": "15c2e5de8c8dc96b",
  "without_key2_body_leaves": "15c2e5de8c8dc96b",
  "without_key5_body_clears": "b90a6233898771e2",
  "without_key5_body_respawns": "b90a6233898771e2",
  "without_key5_slot1_dims": "b90a6233898771e2",
  "without_key5_slot1_lights": "15c2e5de8c8dc96b",
  "without_key5_slot2_centre_darkens": "b90a6233898771e2",
  "without_key5_slot2_centre_resets": "15c2e5de8c8dc96b",
  "without_key5_slot2_ring_resets": "15c2e5de8c8dc96b",
  "without_key5_slot2_row1_lights": "b90a6233898771e2",
  "without_key5_slot2_row2_left_lights": "b90a6233898771e2",
  "without_key5_slot2_row2_right_lights": "b90a6233898771e2",
  "without_key5_slot2_row3_lights": "b90a6233898771e2",
  "without_key5_underline1_dims": "b90a6233898771e2",
  "without_key5_underline1_lights": "15c2e5de8c8dc96b",
  "without_key5_underline2_dims": "15c2e5de8c8dc96b",
  "without_key5_underline2_lights": "b90a6233898771e2",
  "without_meter_burn_key2_next": "15c2e5de8c8dc96b",
  "without_meter_burn_key2_rightmost": "15c2e5de8c8dc96b",
  "without_meter_burn_key4_next": "15c2e5de8c8dc96b"
 },
 "probe_id": "P-08"
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
  "detail": "9/9 transitions replay exactly",
  "matched": 9,
  "ok": true,
  "transitions": 9
 },
 "responsibility": {
  "cells_unexplained": 0,
  "detail": "every pixel of frame 0 belongs to the board or to an object",
  "ok": true,
  "total_cells": 4096
 },
 "unambiguous": {
  "actions": 3,
  "cap_reached": false,
  "clashes": [],
  "detail": "no (state, action) among 10 x 3 admitted two rules, and all 30 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 30,
  "pairs_nominal": 30,
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
# theory.dsl -- world observed for 14 states / 13 transitions
# (RESET + A1 A2 A3 A4 A5 A2 A5 A2 A5 A2 A5 A2 A5).
# 77 cells have ever changed; this manual names and owns all 77.
#
# WHAT THIS ROUND COST AND WHAT IT BOUGHT
#
#   Four commands were spent -- A2 A5 A2 A5 -- and they moved the body
#   between the same two lattice cells it was already oscillating between.
#   Four probe_refutations fired. THEY ARE ONE DEFECT, COUNTED FOUR TIMES,
#   AND THE DEFECT IS ONE PIXEL.
#
#   Read the `inert` fields of P-05..P-08 in order: 15c2e5..., 287dc6...,
#   818eaa..., b90a62... Each one is the PREVIOUS probe's `manual` value.
#   The harness rolls MY predicted frame forward; it does not resync to the
#   world. So at t10 the manual failed to burn (63,59) -- a cell that had
#   never changed, was therefore board, was owned by no object, and could
#   not be drawn by any rule I am able to write -- and that single wrong
#   pixel then travelled through t11, t12 (where a second undrawable burn
#   at (63,58) joined it) and t13. Four refutations, two pixels, zero
#   rules implicated. Every other rule in this manual took two more
#   full-coverage witnesses and not one contradiction.
#
#   The previous manual advertised this outcome by name and by price:
#   `the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows`
#   said the next burn was at (63,59), said it was board, said it would
#   cost exactly one wrong pixel, and said no rewriting fixes it. The
#   price came in exactly. The repair is arithmetic -- (63,59) and (63,58)
#   are dynamic now, Glyph9 goes 39 -> 41, and both transitions replay --
#   and the same bill will be presented again at (63,57).
#
#   THE STRUCTURAL CONSEQUENCE IS THE FINDING OF THIS ROUND, and it is
#   about the instrument rather than the world: every meter cell burns
#   exactly once, and at the moment it burns it is still board. So no
#   burn is ever predictable in advance by this manual, every ACTION2 or
#   ACTION4 press registers as a refutation whatever else it does, and the
#   refutation channel is SATURATED. A probe desk that ranks by
#   refutation-fired will keep choosing moves that teach nothing.
#   See the_meter_edge_saturates_the_refutation_channel.

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
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t8,t9,t10,t11,t12,t13 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12 cov: 120/120]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12 cov: 120/120]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12 cov: 4/4]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13 cov: 120/120]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13 cov: 120/120]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

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
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

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
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4019 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 6 [status: counted]

  theorem the_four_refutations_are_one_undrawable_pixel_rolled_forward "P-05 and P-07 are ACTION2, P-06 and P-08 ACTION5, and the diagnosis is arithmetic, not physics. Chain the inert fields: P-06 inert is P-05 manual, P-07 inert is P-06 manual, P-08 inert is P-07 manual. The harness rolls MY predicted frame forward and never resyncs to the world, so a divergence introduced once is carried until the run ends. The divergence was introduced at t10, where the world burned meter cell (63,59). At that moment (63,59) had never changed, was therefore board, was owned by no object, and no rule expressible in this DSL could draw it -- exactly as the previous manual stated in advance, at exactly the price it quoted. t12 added a second such pixel at (63,58). t11 and t13 introduced nothing of their own: their panel toggle is 23 cells and their body return is 48, and every one of those 71 cells was drawn correctly by rules that now carry five witnesses each. So the honest ledger for this round is TWO wrong pixels and FOUR refutation reports, and the ratio is a property of the instrument. Repair: (63,59) and (63,58) are dynamic now, Glyph9 rises 39 to 41, both transitions replay exactly, and the bill will be represented at (63,57)."
    [depends: meter_burn_key2_next, the_meter_edge_saturates_the_refutation_channel  probe: passed]

  theorem the_meter_edge_saturates_the_refutation_channel "Stated as a law of this manual rather than of this world, and it is the finding I most want on the record. Each of the 64 cells of the row-63 bar burns EXACTLY ONCE, from colour 9 to colour 1, advancing leftward. At the instant a cell burns it has never changed, so it is board, so no instance exists for it, so no rule of mine draws it. Therefore: (1) my three meter_burn rules have ZERO predictive value on the leading edge and full value on replay, which is not a contradiction but a division of labour I should not confuse with a rule that works; (2) EVERY press of a key that burns will be scored a refutation regardless of what else it teaches, so refutation-fired is no longer a signal that discriminates between commands; (3) the correct reading of a refutation is now its DIVERGENCE SET, not its hash, and where the divergence set is a subset of the bar's leading edge the manual is not implicated. Deleting the burn rules does not help -- the wrong-pixel count at the moment of the burn is identical -- and keeping them is strictly better because they make every past transition replay. I cannot repair this: `arc-instances: all` instances only cells the board cannot explain, and a cell that has never changed is exactly what the board explains."
    [depends: meter_burn_key2_next, the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows  probe: passed]

  theorem the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right. SIX burns now: (63,63) t2, (63,62) t4, (63,61) t6, (63,60) t8, (63,59) t10, (63,58) t12. Seven silences: t1, t3, t5, t7, t9, t11, t13. The current frame confirms it -- row 63 reads 9 through col 57 and 1 from col 58 to col 63. READING A, ACTION-KEYING: burns iff the key is 2 or 4. READING B, COMMAND PARITY: burns iff the command index is even. BOTH SCORE 13/13 AND NEITHER HAS GAINED A SINGLE BIT SINCE THE LAST ROUND, because the four new commands were key 2 at index 10, key 5 at 11, key 2 at 12, key 5 at 13 -- every one of them a key whose parity equals its index's parity, which is the diagonal on which the two readings are numerically identical. Thirteen commands, thirteen alignments, zero separation. THE SEPARATOR REMAINS FREE: any press whose key parity differs from its index parity settles it. The next index is 14, EVEN, so an odd key there (1, 3 or 5) separates in one command, and an even key there does not. I encode reading A because it is the only one the guard language can say -- there is no command counter and no phase pixel -- and I still expect B, because at t3 and t4 the body stood at lattice (2,2) with left and right both void, ACTION3 and ACTION4 were blocked identically, and only ACTION4 burned. Under A that is a cost attached to a key and not to an attempt; under B it is one bit of clock."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9. Sharpened to 5/5 this round and it is no longer a three-sample curiosity. ACTION2 returned SEVEN frames at t2, t8 and t12 and NINE frames at t6 and t10. The panel configuration in the state each press acted FROM: t2 from state 1 (A), t8 from state 7 (A), t12 from state 11 (A) -- seven frames; t6 from state 5 (B), t10 from state 9 (B) -- nine frames. Five for five, no exceptions: ACTION2 animates in 7 internal frames when the panel is in configuration A and 9 when it is in B. ACTION5 returned nine frames all five times regardless of configuration, and every no-op returned one. THE NET EFFECT IS IDENTICAL IN ALL FIVE ACTION2 PRESSES -- 48 body cells, rows 8-18, cols 14-18, plus one burn -- so this costs me nothing in replay and buys me nothing in prediction, and yet it is the only evidence I have that the panel does anything at all besides display. Six rows of travel at one row per frame is 7 frames with a terminal frame; the two extra frames under configuration B are two internal steps whose content I never see, because `cascade single_frame` compares only the net. I therefore record, as a limitation of my own semantics and not of the world: up to eight intermediate frames per command are discarded unread, and something distinguishable happens inside them. If the panel selects a mode, that mode's effect is either invisible in the net frame or has not yet had an occasion to show."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over FIVE toggles now -- t5, t7, t9, t11, t13 -- 23 cells every time, and ACTION2 has never touched a panel pixel in five presses. CONFIGURATION A (states 0-4, 7-8, 11-12): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B (states 5-6, 9-10, 13, and the current frame, which reads 222/2.2/222 at cols 1-3 and 999/9.9/999 at cols 5-7 with row 5 dark at 1-3 and lit at 5-7): slot 1 is a hollow colour-2 ring with underline dark; slot 2 is a hollow colour-9 ring with dark centre and underline lit. mdl_segmenter corroborates this independently and by frame index: its colour-1 nine-cell tracks are obj1 (frames 0-4), obj6 (7-8), obj8 (11-12) and its colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13) -- A,B,A,B,A,B read off an engine that has never seen my rules. Its obj0 (colour 9, eight cells, 3x3, present in all 14 frames) and obj2 (colour 9, 1x3, all 14) persist while it narrates ten MOVE events: the hollow ring and the lit underline do not appear and vanish, they TRAVEL between slot 1 and slot 2. So the panel is one marker with two seats and colour 9 marks the occupied seat. What the seats HOLD is still unknown and I will not guess. I cannot model it as a moving marker either: the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring travelling four columns is not expressible as a move, and ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_still_cannot_test_it "Unchanged in kind, stronger in count, and now the cheapest open question on the board. The guard `colored(spawn_probe, 5)` has FIVE positive witnesses (t5, t7, t9, t11, t13 -- body away, panel toggled) and STILL NO NEGATIVE ONE, because ACTION5 has never once been pressed with the body at home. Every ACTION5 in this window immediately followed an ACTION2, so ACTION5 was pressed and the body was away from spawn are the same event five times over and no guard can be credited over the other. By the letter of no-entry-without-gain the atom is still unearned. I keep it because dropping it changes no replay and because the body is at spawn RIGHT NOW: with the guard my manual predicts SILENCE for an ACTION5 pressed here, without it a 23-cell toggle. Silence is the prediction I want on the record. Note what one such press would settle at once: the guard, the meter parity (key 5 is odd, index 14 is even, so reading A predicts no burn and reading B predicts a burn at (63,57)), and the identity of ACTION5 (UNDO would return the body to (2,2) for 48 cells, while UP and RETURN both predict no motion from spawn). Three open questions, one command, and my manual's stake is a bare prediction of zero changed cells."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, what_action5_is_and_the_two_cell_experiment_that_names_it  probe: pending]

  theorem the_action_map_after_thirteen_transitions_and_the_standard_mapping_hypothesis "WITNESSED: ACTION2 IS DOWN, 5/5, six rows south, one lattice cell, at t2, t6, t8, t10, t12. ACTION5 returns the body from lattice (2,2) to (1,2), 5/5. NEGATIVE INFORMATION, and I state it as negative because that is all it is. At spawn (1,2) up and left are void while down and right are open floor, and ACTION1 did nothing at t1 -- so ACTION1 IS NEITHER DOWN NOR RIGHT. At (2,2) the body had just vacated rows 8-12 so UP WAS OPEN, and rows 20-24 cols 14-18 are floor so DOWN WAS OPEN, while left (cols 8-12) and right (cols 20-24) are void; ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else. It explains every no-op as a blocked move and it is the conventional mapping for this action family, which is a prior and not evidence. FOUR COMMANDS WERE SPENT THIS ROUND AND NOT ONE OF THEM TOUCHED THIS QUESTION -- the map is exactly as constrained as it was at state 9. THE CHEAP TEST IS STILL ONE PRESS: the body stands at spawn, where left is void and right is open floor, so ACTION4 pressed here either steps six columns east or does not, and either answer names the east key -- if ACTION4 does not move, ACTION3 is east by elimination, since ACTION1 is already excluded from east by t1."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_and_the_two_cell_experiment_that_names_it "Three readings survive all FIVE ACTION5 presses because all five were made from exactly one cell south of spawn, where they are indistinguishable: UP (move one cell north), UNDO (revert the last move), RETURN (jump to spawn from anywhere). They separate the moment the body is somewhere else, and they separate differently by axis. FROM SPAWN ITSELF, which is where the body is now: UP predicts no motion (north of spawn is void), RETURN predicts no motion (already home), UNDO predicts 48 cells back to (2,2) -- so one press here splits UNDO from the other two for free. Two cells EAST at lattice (1,4): UP no move, UNDO one cell west to (1,3), RETURN spawn at (1,2) -- three different diffs, all legible in the raw pixel count, which is the full separation. Two cells SOUTH at (3,2): UP and UNDO both predict (2,2) and only RETURN separates. So the eastward route answers this question completely and the southward route does not, which is one more reason to go east first. Note the coupling I cannot yet break: the panel toggles on every effective ACTION5, five for five, so whatever ACTION5 is, the panel is its counter or its selector -- and the 7-versus-9 cascade result says the panel's state is not merely cosmetic."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated one row per internal frame and the world reports the whole animation for a single action; `cascade single_frame` compares only the net effect, which is identical for all five ACTION2 presses (48 body cells, rows 8-18, cols 14-18) regardless of whether the command took 7 frames or 9. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, FIVE times. ONE PRESS IS ONE LATTICE CELL, 5/5, and every distance in the playbook rests on that."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_world_may_still_not_be_a_function_of_the_drawn_frame "Carried as a belief and NOT proven in this window. To prove it I need two pixel-identical states from which the SAME action produced different successors; I have no such pair, and distinct_states is 12 against 14 states, so two coincidences exist but neither is followed by the same key. What keeps the belief alive is the parity reading of the meter, which if true IS one bit of hidden state that flips every command and that no guard in this language can read, because no guard can read anything that is not a pixel. What now strengthens it is the cascade length: ACTION2 took 7 frames or 9 depending on a panel configuration that the net frame records but that my rules never consult, which is the same shape of dependence one step less hidden. Operationally it matters in exactly one way: if parity wins, every burn rule I can write is an approximation with a known error rate, and I would rather say that once than rediscover it."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4019 + dynamic 77 = 4096, and 41+24+9 = 74 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 77. Consequence: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This round is the second consecutive round in which that sentence, written in advance, was the entire content of every refutation. meter_burn_key2_next now replays t6, t8, t10 and t12 perfectly, because by replay time all four burned cells are dynamic; it will still miss the SEVENTH burn at (63,57), because that cell is board today. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable too until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, 24 if I already had the leaves rule, 0 for the second step. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 77 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three; slot 2's nine, centre included because (2,6) is 1 in A and 0 in B; underline 2's three. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 6 are the burned right end of row 63: cols 58 through 63. 23+24+24+6 = 77 = dynamic_cells. By frame-0 colour: 41 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 6 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 41+9+24 = 74 = cells_needing_an_owner exactly. zero_space's global-law cell list is the same 77 cells -- it lists (2,1) and (2,3) but not (2,2), (10,14),(10,15),(10,17),(10,18) but not (10,16), and all six burned bar cells -- and its single global law restates this census and nothing more."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so that the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended five times and all five started at spawn, so no rule of mine turns Vacated pixels from 9 back to 5 on an ACTION2: rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below-six(?v), 5) then recolored(?v, 5). One ACTION2 from lattice (2,2) buys it, and four commands this round each had the chance and none took it. (2) EAST-WEST MOTION. Whatever the east key turns out to be, it needs a pair: a leaves rule over Glyph9 guarded on colour 9 with rightof-six rendering 5, and its arrives twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) A SEVENTH BURN AT A CELL THAT IS STILL BOARD, which is not a missing rule but a missing instance and cannot be written at all. I state the price of all three in advance so it cannot be mistaken for a surprise: the first eastward step costs 48 wrong cells plus one if the bar burns, the first second-descent costs 24, and every fresh burn costs 1."
    [depends: key2_body_arrives, the_meter_edge_saturates_the_refutation_channel  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth below is row 69. So colored(off-board, k) is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen of the twenty rules rest on this and every row and column discrimination in the panel is built from it: the k-th above is off-board exactly when k exceeds the row, so row 1 is above-twice equals wall, row 3 is a colour test on above-twice -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column: col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice, pairwise exclusive, which is why the ambiguity check reports 0 clashes over 30 adjudicated pairs. Not one rule uses `not`, deliberately. The eight A-to-B slot-2 and underline rules could collapse to two if I could write that not all four neighbours are colour 1, and I decline to gamble a whole round's compile on discovering whether `not` before an equality atom parses. If a future desk wants the shorter form, try it on ONE rule, not on eight."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read from the CURRENT frame and unchanged: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open, C=6 holds the knob, C=7 does not exist (col 44 is void in this band); R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2, plus a fragment of floor at cols 42-50 in row 48 alone which cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); in fourteen frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it has been at spawn in eight of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed FIVE times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket, verified again against the current frame: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7) -- rows 50-54 cols 44-48, aperture at (52,46): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in fourteen frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and I have re-read every pixel of it in the current frame: colour 8 fills row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41 with a stem pixel at (12,40), all inside lattice (1,6). Not one colour-8 pixel has moved in fourteen frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. Four lattice cells of eastward travel put the body at (1,5) and every one of those four steps is on floor that R=1 shows open. Thirteen commands have been spent and none of them has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after fourteen states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the standard mapping I favour -- 1 up, 2 down, 3 left, 4 right, 5 undo-or-return -- accounts for every key pressed, which makes 6 and 7 more likely to be a click and a spare than more directions."
    [depends: the_action_map_after_thirteen_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and the reason has not weakened. Cart.pos = exit_cell needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and forty siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would be true of the body standing one cell south of spawn, which is not a win. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in lattice (8,7) once, the playbook steers by lattice distance, and is_goal -> False is the honest compilation."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter has crossed into POSITIVE gain for the first time, +614 bits at compression_ratio 0.937 on split_by_color=false, against -55676 bits when split by colour -- so its segmentation now just barely beats writing the pixels out, and I still owe it nothing structural. Its ten tracks remain the round's best independent corroboration and this round they corroborate the toggle by frame index: colour-1 nine-cell tracks obj1 (frames 0-4), obj6 (7-8), obj8 (11-12); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13). That is A,B,A,B,A,B derived by an engine that has never seen my rules. obj0 and obj2 persisting through all fourteen frames while the segmenter narrates ten moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 6 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 13 transitions constrain rank 7 of 385 features, null space dimension 378, nearly every vector in it is a law true over these states and unfalsified rather than confirmed -- and its single global law is my census. cegis_miner refuses on every track and its verdict, the world does not narrate as one mover, remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The next command has index 14, which is EVEN, and the body is at spawn with the panel in configuration B. ACTION4: if the standard mapping holds, the world changes 48 cells in rows 8-12 cols 14-24 and burns (63,57) for 49 total, and MY MANUAL DRAWS NONE OF THEM -- no east rules exist and (63,57) is board -- so I expect a 49-cell divergence, which is the advertised price of the first step onto fresh ground and not a failure of physics. If instead ZERO cells change, ACTION4 is not east, ACTION3 is east by elimination, AND BOTH METER READINGS DIE AT ONCE, because key 4 is even and index 14 is even and both demanded a burn. If exactly ONE cell changes and it is (63,57), ACTION4 is not east and both readings survive. ACTION5: I predict ZERO changed cells anywhere, on the strength of the spawn_probe guard and nothing else; a 23-cell panel toggle refutes the guard outright, a 48-cell move south says ACTION5 is UNDO, and a lone burn at (63,57) kills action-keying while leaving parity standing. ACTION2: 48 cells I draw correctly plus a burn at (63,57) I cannot draw -- exactly one wrong pixel, and nothing else learned, because key2_body_leaves and key2_body_arrives are at 120/120 and a sixth witness buys nothing. ACTION1 OR ACTION3 from spawn: zero cells under my manual, one cell at (63,57) under parity."
    [depends: the_action_map_after_thirteen_transitions_and_the_standard_mapping_hypothesis, the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept in compressed form because the lesson is structural and cost a full round. Thirteen panel rules once carried colored(spawn_probe, 5) while the landmark line read a prose placeholder instead of a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The landmark now reads (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key5_slot1_dims  probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE OF PLAY (state 13): body home at lattice (1,2); panel in
# configuration B; SIX meter cells burned, cols 58-63 of row 63; thirteen
# commands spent; the next command has index 14, which is EVEN.
#
# THE ONE NUMBER THAT MATTERS: thirteen commands spent, TWO lattice cells
# ever occupied, and the last eight commands were the same two keys
# alternating between the same two cells. The previous edition of this file
# already carried the prune that forbids exactly that, and four more such
# commands were bought anyway. So the prune was not the problem; the RANKING
# was. This edition names the reason and fixes the ranking.
#
# WHY THE RANKING FAILED: every ACTION2 press burns a meter cell, every burn
# lands on a cell that is board at the instant it burns, and no rule the
# manual can express draws it. So EVERY ACTION2 PRESS FIRES A REFUTATION no
# matter how little it teaches, and a desk that ranks by refutation-fired
# will keep buying the move that fires one. Four refutations this round,
# two wrong pixels, zero rules implicated, one whole round consumed. The
# refutation channel is saturated and must be read by its divergence SET,
# not by whether it fired. First two prunes below encode that.
#
# WHAT THE FOUR COMMANDS DID BUY, honestly: a fifth and sixth witness for
# rules already at full coverage (worth nothing), a fifth toggle of the
# panel (worth nothing), two more burns on the diagonal where the two meter
# readings agree (worth nothing), and ONE real finding -- ACTION2 animates
# in 7 frames under panel configuration A and 9 under B, 5/5, which is the
# only evidence that the panel is not purely cosmetic.
#
# WHAT TO BUY NEXT, and the reasoning, not the sequence:
#  (a) THE EAST KEY IS THE ONLY QUESTION WHOSE ANSWER MOVES THE BODY. At
#      spawn, west is void and east is open floor, so one press of the
#      right-hand candidate either steps a lattice cell east or names the
#      other candidate by elimination -- ACTION1 was already excluded from
#      east at t1. Either outcome is decisive and one outcome also spends
#      the first of the four steps that reach the knob at lattice (1,6).
#      Advertised cost: 49 divergent cells, all of them cells the manual
#      said in advance it cannot own. Do not read that as a refutation.
#  (b) A ZERO-CELL ANSWER TO (a) KILLS BOTH METER READINGS AT ONCE, because
#      index 14 is even and the key candidate is even, so action-keying and
#      command-parity both demand a burn. That is the one branch where the
#      cheap probe pays double.
#  (c) THE METER SEPARATOR IS STILL FREE AND STILL UNTAKEN. Thirteen
#      commands, thirteen times a key whose parity equalled its index's
#      parity, zero separation. Any odd key at index 14, or any even key at
#      index 15, breaks it. Walking east on two consecutive commands breaks
#      it on the second step at no cost, which is why no dedicated meter
#      probe is worth a command while the map is open.
#  (d) THE CHEAPEST TRIPLE ON THE BOARD IS THE RETURN KEY PRESSED AT HOME.
#      The body is at spawn for the first time with a free command: the
#      manual predicts total silence there, which tests the spawn guard
#      (five positives, zero negatives, five rounds running); the key is
#      odd and the index even, which separates the meter; and a 48-cell
#      move south would say the key is UNDO rather than UP or RETURN.
#      Three open questions, one press, zero route progress. Rank it second
#      to (a), and first if (a) turns out to leave the body where it stands.
#  (e) ONE PRESS IS ONE LATTICE CELL, 5/5. Every distance below is counted
#      in lattice cells, not pixels.
# No stored sequence anywhere: every line is a criterion on the current
# frame plus the manual's own open questions.

order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired    [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                 [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                 [proof: lean]
order     prefer_the_probe_that_advances_over_the_probe_that_only_answers    [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open        [proof: lean]
order     take_a_separation_that_arrives_free_over_one_that_costs_a_command  [proof: lean]
order     read_the_cascade_length_it_is_evidence_that_costs_no_pixel         [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it         [proof: lean]
order     identify_a_direction_key_before_routing_with_it                    [proof: lean]
order     separate_two_readings_before_planning_against_either               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                 [proof: lean]
order     reach_the_switch_before_testing_the_switch                         [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end                   [proof: lean]
order     witness_a_rule_before_writing_it                                   [proof: lean]
order     spend_commands_on_information_while_the_bar_is_still_long          [proof: lean]

prune     divergence_lies_only_on_the_meter_leading_edge => dead              [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead     [proof: lean]
prune     revisits_an_occupied_cell_by_an_already_witnessed_key => dead       [proof: lean]
prune     repeats_a_transition_whose_rule_already_has_full_coverage => dead   [proof: lean]
prune     dedicated_meter_probe_while_a_map_question_is_open => dead          [proof: lean]
prune     key_parity_equals_command_index_parity_when_bought_for_the_meter => dead [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                   [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead      [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead      [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead       [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead  [proof: lean]
prune     guard_whose_landmark_carries_no_arc_cell_comment => dead            [proof: lean]
prune     meter_exhausted and not goal => dead                                [proof: lean]

heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time                [admissible: lean]
heuristic unwitnessed_rules_this_command_would_witness                       [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                    [admissible: lean]

prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree        [ev: 5/7 no_ops]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule          [ev: 5/5 moves]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has                 [ev: 2/11 cells]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    a_key_whose_parity_differs_from_the_command_index                  [ev: 0/13 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 13/13 diffs]
prefer    a_press_at_home_that_splits_up_from_undo_from_return               [ev: 5/5 key5]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket               [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                      [ev: 2/7 keys]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "colour-9 dynamic cells (mdl obj0, obj2, obj4 in part)", "verdict": "accept", "as": "Glyph9 with arc-instances: all", "why": "the 41 cells that have ever changed and read colour 9 at frame 0 -- slot-1 ring 8, underline-1 3, spawn ring 24, burned meter 6 -- and zero_space's global-law cell list contains exactly these plus the other three types."},
  {"id": "O-02", "subject": "colour-5 dynamic cells", "verdict": "accept", "as": "Vacated with arc-instances: all", "why": "24 cells at rows 14-18 cols 14-18 minus aperture (16,16); they are floor at frame 0 and carry the body whenever it stands one lattice cell south of spawn."},
  {"id": "O-03", "subject": "mdl obj1/obj6/obj8 (colour 1, 9 cells, 3x3)", "verdict": "accept", "as": "Spent with arc-instances: all", "why": "three tracks at frames 0-4, 7-8, 11-12 are the same nine panel cells in configuration A; one type of nine instances covers all three appearances and their colour-2/colour-9 counterparts."},
  {"id": "O-04", "subject": "colour-0 dynamic cells (underline 2)", "verdict": "accept", "as": "Dark with arc-instances: all", "why": "3 cells at row 5 cols 5-7, dark in configuration A and lit 9 in B; they are the only dynamic cells whose frame-0 colour is the background."},
  {"id": "O-05", "subject": "mdl obj3 (colour null, 1006 cells, 50x38)", "verdict": "reject", "as": null, "why": "connected_components(4) merged the maze floor with the body ring because the ring is floor-adjacent; declaring it would put a second owner on cells Vacated and Glyph9 already own, which rule 5 forbids."},
  {"id": "O-06", "subject": "mdl obj5/obj7/obj9 (colour 2, 3x3) and obj4 (colour 9, 1x64)", "verdict": "entailed", "as": "Glyph9 instances", "why": "the colour-2 tracks are slot-1 ring cells rendering 2 in configuration B, and obj4 is the row-63 bar of which exactly 6 cells are dynamic; both are already instanced by O-01."},
  {"id": "R-01", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept", "as": "unchanged, ev extended to t2,t6,t8,t10,t12", "why": "two more presses at t10 and t12, 24 cells each, zero contradictions; coverage 120/120 and the pair is the only thing in the manual that moves the body south."},
  {"id": "R-02", "subject": "key5_body_clears / key5_body_respawns", "verdict": "accept", "as": "unchanged, ev extended to t5,t7,t9,t11,t13", "why": "t11 and t13 each returned 48 body cells exactly as predicted; 120/120."},
  {"id": "R-03", "subject": "meter_burn_key2_next", "verdict": "accept", "as": "unchanged, ev t6,t8,t10,t12 cov 4/4", "why": "(63,59) at t10 and (63,58) at t12 are dynamic now and replay under this rule; its live predictive value on a fresh cell is nil and the manual says so rather than hiding it."},
  {"id": "R-04", "subject": "the ten panel A-to-B rules and five B-to-A rules", "verdict": "accept", "as": "unchanged, coverage doubled", "why": "t13 gave the A-to-B set a third witness (24/24, 9/9, 9/9, 9/9, 3/3, 3/3, 3/3, 9/9) and t11 gave the B-to-A set a second (16/16, 6/6, 16/16, 2/2, 6/6); 23 cells per toggle, five toggles, no divergence."},
  {"id": "R-05", "subject": "key2_floor_leaves (second-descent rule)", "verdict": "probe-pending", "why": "the body has descended five times and all five started at spawn, so no transition witnesses a 9-to-5 clearing of the Vacated ring under ACTION2; the text is held in a theorem so the witnessing transition costs one paste."},
  {"id": "R-06", "subject": "an east/west movement pair", "verdict": "probe-pending", "why": "no key has been shown to move the body horizontally, and the destination pixels at rows 8-12 cols 20-24 are board, so even a correct rule would draw nothing on its first firing."},
  {"id": "L-01", "subject": "the four refutations P-05..P-08", "verdict": "accept", "as": "theorem the_four_refutations_are_one_undrawable_pixel_rolled_forward", "why": "each probe's inert hash equals the previous probe's manual hash, so the harness rolls my prediction forward; the only new error was the undrawable burn at (63,59) at t10 and (63,58) at t12, and every other cell in all four transitions was drawn correctly."},
  {"id": "L-02", "subject": "the meter's leading edge", "verdict": "accept", "as": "theorem the_meter_edge_saturates_the_refutation_channel", "why": "every bar cell burns exactly once and is board at that instant, so no burn is ever predictable, every burning press reports a refutation, and refutation-fired has stopped discriminating between candidate commands."},
  {"id": "L-03", "subject": "action-keying versus command parity for the meter", "verdict": "probe-pending", "why": "both readings score 13/13; the four new commands were key 2 at index 10, key 5 at 11, key 2 at 12, key 5 at 13, every one on the diagonal where the readings coincide, so not one bit was gained and the separator is still free at index 14 with any odd key."},
  {"id": "L-04", "subject": "ACTION2 cascade length versus panel configuration", "verdict": "accept", "as": "theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction", "why": "7 frames from states 1, 7, 11 (configuration A) and 9 frames from states 5, 9 (configuration B), 5/5 with the net effect identical every time -- the first evidence that the panel state has any consequence."},
  {"id": "L-05", "subject": "the spawn_probe guard", "verdict": "probe-pending", "why": "five positive witnesses and still zero negative ones, because every ACTION5 has followed an ACTION2; the body is at spawn now, so the manual's prediction of silence is on the record and one press settles it."},
  {"id": "L-06", "subject": "dynamic census", "verdict": "accept", "as": "invariants 41/24/9/3 and board 4019", "why": "23 panel + 24 spawn ring + 24 lower ring + 6 burned bar = 77 = dynamic_cells, and 41+9+24 = 74 = cells_needing_an_owner, matching zero_space's global-law cell list cell for cell."},
  {"id": "L-07", "subject": "zero_space evidence_adequacy", "verdict": "accept", "as": "quoted verbatim in what_the_engines_gave_me", "why": "it self-reports THIN -- rank 7 of 385 features over 13 transitions, null space 378 -- so its single global law is treated as my census restated and nothing is promoted from it."},
  {"id": "L-08", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "reject", "as": null, "why": "true of the arm, false of the world: the mover is a rigid 24-pixel ring and the arm can only see 24 simultaneous recolours, which is why movement costs a rule pair rather than one moved() event."},
  {"id": "L-09", "subject": "mdl_segmenter's first positive gain (+614 bits)", "verdict": "entailed", "as": "no structural change", "why": "a 6% compression edge over writing the pixels out does not buy a new type, but the frame indices of its colour-1 and colour-2 tracks independently reproduce the A,B,A,B,A,B toggle my five ACTION5 rules produce."},
  {"id": "L-10", "subject": "goal section", "verdict": "reject", "as": "no goal, is_goal -> False", "why": "the socket ring cells are frame-0 colour 5 and would type as Vacated, so any count() goal over them is also true of the body standing one cell south of spawn -- a goal true in the wrong states stops a planner at its first step."},
  {"id": "E-01", "subject": "owning a cell that has never changed", "verdict": "probe-pending", "why": "I wanted an instance on (63,57) so the seventh burn could be drawn when it happens; arc-instances: all instances only cells the board cannot explain, so I wrote theorem the_meter_edge_saturates_the_refutation_channel and priced the loss at one pixel per burn instead."},
  {"id": "E-02", "subject": "the discarded intermediate frames of a cascade", "verdict": "probe-pending", "why": "I wanted to say that ACTION2 takes two extra internal steps under panel configuration B; cascade single_frame compares only the net effect and there is no syntax for a multi-frame law, so I recorded the 5/5 correlation in theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction."},
  {"id": "E-03", "subject": "a click carrying coordinates", "verdict": "probe-pending", "why": "the knob at lattice (1,6) is a 3x3 target the body appears unable to stand on and a click is the shape of interaction that presses it; act=key(6) parses but has nowhere to put two coordinates, so the belief stays in theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click."},
  {"id": "P-01", "subject": "the right-hand direction candidate pressed from spawn", "verdict": "probe-pending", "why": "west is void and east is open floor there, so it either steps a lattice cell east or names the other candidate by elimination; if zero cells change, both meter readings die at once, since index 14 and the key are both even and both demanded a burn."},
  {"id": "P-02", "subject": "the return key pressed at home", "verdict": "probe-pending", "why": "the manual predicts total silence, so one press tests the spawn guard, separates action-keying from command parity (odd key at an even index), and splits UNDO from UP and RETURN -- three open questions, no route progress, ranked second."},
  {"id": "P-03", "subject": "another descend-and-return pair", "verdict": "reject", "as": "pruned as dead", "why": "every rule it would witness is already at full coverage, it revisits an occupied cell with an already-witnessed key, and its only refutation is the meter edge -- which is exactly the ranking error that consumed this round."}
]
```
```
