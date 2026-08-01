# call-002-theorize-round1

model: `claude-opus-5` · 801189 ms · $2.715763 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 101680, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 101680, "cache_read_input_tokens": 37615, "inference_geo": "not_available", "input_tokens": 4, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 64065, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 64065, "cache_read_input_tokens": 37615, "input_tokens": 2, "output_tokens": 2102, "type": "message"}], "output_tokens": 66102, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 72,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4021,
 "distinct_states": 7,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 75,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 10,
 "steps": 10
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
9999999999999999999999999999999999999999999999999999999999991111
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

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 9,
  "n_states": 10,
  "refusals": [
   "ValueError: transition 4 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
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
    "transitions": 9
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
    "transitions": 9
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
  "candidates": 7,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 2,
   "move": 4,
   "recolor": 8,
   "vanish": 2
  },
  "n_frames": 10,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 10,
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
    "frames_present": 10,
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
    "frames_present": 10,
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
    "frames_present": 10,
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
    "frames_present": 3,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj6"
   }
  ],
  "variants": [
   {
    "baseline_bits": 3944,
    "compression_ratio": 1.918611,
    "events": 16,
    "gain_bits": -3623,
    "ms": 20,
    "script_bits": 7567,
    "split_by_color": false,
    "tracks": 7
   },
   {
    "baseline_bits": 3944,
    "compression_ratio": 7.956643,
    "events": 39,
    "gain_bits": -27437,
    "ms": 35,
    "script_bits": 31381,
    "split_by_color": true,
    "tracks": 24
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 75,
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
  "cells_needing_an_owner": 72,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4021,
  "distinct_states": 7,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 75,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 10,
  "steps": 10
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 75,
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
  "cells_dynamic": 75,
  "cells_used": 75,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 5,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.013333,
   "difference_rank": 5,
   "features": 375,
   "space_dimension": 370,
   "transitions": 9,
   "verdict": "THIN: 9 transitions constrain rank 5 of 375 features, so the null space has dimension 370 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 375,
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
     "c5@17",
     "c9@17",
     "c0@18",
     "c1@18",
     "c2@18",
     "c5@18",
     "c9@18",
     "c0@19",
     "c1@19",
     "c2@19",
     "c5@19",
     "c9@19",
     "c0@20",
     "c1@20",
     "c2@20",
     "c5@20",
     "c9@20",
     "c0@21",
     "c1@21",
     "c2@21",
     "c5@21",
     "c9@21",
     "c0@22",
     "c1@22",
     "c2@22",
     "c5@22",
     "c9@22",
     "c0@23",
     "c1@23",
     "c2@23",
     "c5@23",
     "c9@23",
     "c0@24",
     "c1@24",
     "c2@24",
     "c5@24",
     "c9@24",
     "c0@25",
     "c1@25",
     "c2@25",
     "c5@25",
     "c9@25",
     "c0@26",
     "c1@26",
     "c2@26",
     "c5@26",
     "c9@26",
     "c0@27",
     "c1@27",
     "c2@27",
     "c5@27",
     "c9@27",
     "c0@28",
     "c1@28",
     "c2@28",
     "c5@28",
     "c9@28",
     "c0@29",
     "c1@29",
     "c2@29",
     "c5@29",
     "c9@29",
     "c0@30",
     "c1@30",
     "c2@30",
     "c5@30",
     "c9@30",
     "c0@31",
     "c1@31",
     "c2@31",
     "c5@31",
     "c9@31",
     "c0@32",
     "c1@32",
     "c2@32",
     "c5@32",
     "c9@32",
     "c0@33",
     "c1@33",
     "c2@33",
     "c5@33",
     "c9@33",
     
```

The full proposal stream is 749 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 6 states / 5 transitions
# (RESET, then ACTION1 ACTION2 ACTION3 ACTION4 ACTION5, indices t1..t5).
# 73 cells have ever changed; this manual names and owns all 73.
#
# WHY THIS ROUND EXISTS AND WHAT IT REPAIRS
#
#   The only surprise that fired is replay_mismatch with the reason
#   "theory.dsl is non-empty but generated/theory.py could not be loaded".
#   certify returned an EMPTY replay dict, an EMPTY responsibility dict and
#   unambiguous: null. Nothing ran. That is not a wrong manual, it is a
#   manual that does not compile, and there is exactly one line in the
#   previous text that the grammar calls a HARD compile error:
#
#       landmark spawn_probe  # arc-cell: carried, coordinates stripped
#
#   The spec is explicit: every landmark line MUST carry a trailing
#   # arc-cell: (row, col) comment, and a landmark the level cannot place
#   is a hard compile error. The previous manual even contained a theorem
#   named a_landmark_is_only_as_true_as_the_comment_beside_it which SAYS
#   the landmark reads (8, 14) -- while the landmark line itself said
#   prose. The prose was carried forward and the coordinate was not.
#   FIXED: the line now reads # arc-cell: (8, 14). Second parse risk
#   removed: the empty `goal:` section is gone entirely, since a manual
#   with no goal section at all is legal and an empty one is a guess.
#
#   THE OBSERVATION RECORD HAS BEEN ROLLED BACK AND I HAVE REWRITTEN THE
#   WHOLE MANUAL TO IT. The store now reports 6 states, 5 transitions, 73
#   dynamic cells, 4023 constant cells, 2 burned meter cells. The previous
#   manual was written against 34 states, 87 dynamic cells, 16 burned meter
#   cells. 87 - 73 = 14 and 16 - 2 = 14: this record is a strict PREFIX of
#   that history, cut at state 5. So every `ev:` and every `cov:` in the
#   old text cited transitions this desk cannot see. All of them are
#   rewritten to what the record actually contains, and every rule whose
#   only witnesses lay past t5 has been REMOVED from rules: and parked in
#   laws: with its text intact. See the_record_is_a_prefix and
#   the_rules_i_have_no_witness_for_in_this_record.
#
#   WHAT THAT BUYS: this manual should replay 5/5 exactly. t1 and t3 are
#   no-ops it draws as no-ops, t2 is 49 cells it draws as 49, t4 is 1 cell
#   it draws as 1, t5 is 71 cells it draws as 71. There is no priced-in
#   miss anywhere in this record. The old manual advertised 31/33; this one
#   advertises 5/5 and will be caught out at once if that is wrong.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t5 compress: 37]
  Vacated [segment: dynamic_colour_5 ev: t2,t5 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

laws:
  invariant glyph9_instances count(Glyph9) = 37 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4023 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 2 [status: counted]

  theorem why_theory_py_did_not_exist "The whole of this round's surprise. certify returned replay {}, responsibility {} and unambiguous null -- not a divergence, an absence. theory.dsl was non-empty and generated/theory.py could not be loaded, so the manual had no executable form and NOTHING downstream had a predictor. Exactly one line in the previous text is a documented HARD compile error: landmark spawn_probe carrying the comment arc-cell: carried, coordinates stripped, where the grammar demands arc-cell: (row, col) and calls a landmark the level cannot place a hard error. The manual even contained a theorem asserting the landmark reads (8, 14) -- the belief survived the rewrite and the coordinate did not. The line now reads arc-cell: (8, 14), which is the top-left pixel of the spawn ring, rendering 9 while the body is home and 5 the moment it is anywhere else. Second parse hazard removed at the same time: the previous manual carried a `goal:` header with an empty body, and the spec sanctions NO goal section rather than an empty one. THE LESSON THAT GENERALISES: a compile failure is invisible to every other check in this rig. Responsibility, ambiguity and step-crash counts all reported cleanly in earlier rounds while thirteen rules pointed at (0,0); this time not even those ran. Before believing any certify number, check that certify had something to run."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: pending]

  theorem the_record_is_a_prefix_and_every_count_is_restated "The store I am given reports 6 states, 5 transitions, dynamic_cells 73, cells_needing_an_owner 70, constant_cells 4023, two burned meter cells. The manual I inherited was written against 34 states, 87 dynamic cells and 16 burned meter cells. The difference is 14 in both places, which is exactly the number of extra meter cells that had burned, so THIS RECORD IS A STRICT PREFIX OF THAT HISTORY, cut at state 5, and the current frame is that history's state 5. I have rewritten every ev: and every cov: to the transitions I can actually see, and I have deleted from rules: every rule whose only witnesses lay past t5. WHAT I AM GIVING UP AND SAYING SO: the inherited text reports things I now cannot re-derive -- thirteen descents, thirteen panel toggles, four presses of ACTION5 at spawn that witnessed its silence, and a discriminating experiment at indices 30 to 33 that killed the action-keyed reading of the meter. I do not treat my own prior prose as evidence in a book whose first rule is that every entry carries the transitions that witness it. I carry those claims as named beliefs below, flagged as unwitnessed HERE, and I let this record decide them again. Where the prefix and the prior text disagree about what to write, the prefix wins."
    [depends: dynamic_census  probe: passed]

  theorem the_rules_i_have_no_witness_for_in_this_record "Six rules were removed from rules: this round because their witnesses lie past t5. Their text is kept verbatim so the transition that witnesses one costs a paste and not a rediscovery, and their absence is PRICED so it cannot be read as a surprise. (1) THE PANEL TOGGLING BACK, five rules: key5_slot1_lights over Glyph9 when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9); key5_underline1_lights over Glyph9 with colored(?p, 0) and above-six equals wall then recolored(?p, 9); key5_slot2_ring_resets over Spent with colored(?s, 9) then recolored(?s, 1); key5_slot2_centre_resets over Spent with colored(?s, 0) then recolored(?s, 1); key5_underline2_dims over Dark with colored(?d, 9) then recolored(?d, 0). The panel is now in configuration B and no rule of mine fires on it, so MY MANUAL PREDICTS THE PANEL IS FROZEN. If the next effective ACTION5 toggles it back I am wrong by exactly 23 pixels, and that is the cost of obeying rule 2 rather than my own memory. (2) THE SECOND METER BURN UNDER KEY 2: meter_burn_key2_next over Glyph9 when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1). Only the rightmost cell has ever burned under key 2 in this record. If ACTION2 is pressed again my manual burns nothing and is wrong by one pixel. Both prices are stated before the press, not after."
    [depends: key5_slot1_dims, meter_burn_key2_rightmost  probe: pending]

  theorem the_two_meter_readings_are_not_separated_here_and_the_next_command_separates_them "Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right; it reads 9 through col 61 and 1 at cols 62 and 63, TWO burns in five commands. The burns were at t2 (ACTION2) and t4 (ACTION4) and at no other index. READING A: the bar burns iff the key is 2 or 4. READING B: the bar burns iff the command index is even. Over t1 to t5 the two are numerically IDENTICAL -- every even index carried an even key -- so this record cannot tell them apart, and I say that rather than pretend my rules settle it. My two burn rules encode reading A, for the only reason available inside this grammar: reading B cannot be written here at all, because the guard language reads pixels and the action name and there is no command counter. THE SEPARATOR IS FREE AND IT IS THE NEXT COMMAND. The next index is 6, EVEN. An ODD key at an even index splits them: reading A predicts no burn, reading B predicts (63,61) goes to 1. ACTION3 and ACTION4 are the two keys I want to press anyway for the direction question, and ACTION3 is odd, so ONE PRESS OF ACTION3 BUYS BOTH ANSWERS. The inherited text says this experiment was run at indices 30 to 33 and reading B won; I do not hold that as evidence, but I do note that if reading B is right my burn rules are a mis-attribution that happens to draw every burn in this record, and I would keep them anyway as the shortest expressible shadow of the true law."
    [depends: meter_burn_key2_rightmost, meter_burn_key4_next  probe: pending]

  theorem the_action_map_after_five_transitions "WITNESSED: ACTION2 IS DOWN. t2 moved the body six rows south, from lattice (1,2) to (2,2), one lattice cell, 1/1. ACTION5 carried it back north from (2,2) to (1,2), 1/1. Everything else is NEGATIVE information and I state it as negative. AT SPAWN (1,2) the open neighbours are DOWN and RIGHT only -- lattice (0,2) at rows 2-6 cols 14-18 is void and lattice (1,1) at cols 8-12 is void, while (1,3) at cols 20-24 and (2,2) at rows 14-18 are floor. ACTION1 was pressed there and moved nothing, so ACTION1 IS NEITHER DOWN NOR RIGHT. AT (2,2) the open neighbours are UP and DOWN only -- (2,1) and (2,3) are void, while (1,2) had just been vacated and (3,2) at rows 20-24 is floor. ACTION3 was pressed there and moved nothing; ACTION4 was pressed there and moved nothing but a meter cell. SO NEITHER ACTION3 NOR ACTION4 IS UP OR DOWN, and if either is a direction key at all it is HORIZONTAL. That is the sharpest thing this record says: the east key, if it exists, is ACTION3 or ACTION4, and one press from spawn -- where east is three lattice cells of unbroken floor -- names it whichever way it answers. ACTION5 is up, or return-to-start, or undo; all three agree on the only press ever made. The conventional mapping for this action family agrees with left/right for 3 and 4, which is a prior and not evidence."
    [depends: key2_body_arrives, key5_body_respawns, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem silence_is_a_prediction_and_three_of_my_five_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the five keys AT SPAWN, which is where the body stands. key(2): moves 48 body cells and burns one meter cell, WITNESSED at t2. key(1): inert, WITNESSED at t1, zero cells. key(3), key(4), key(5): my manual predicts ZERO CELLS AND HAS NO WITNESS FOR ANY OF THEM AT THIS CELL -- 3 and 4 were pressed only from one cell south, and 5 was pressed only from one cell south. THREE FORGED DEATH CERTIFICATES out of five, and two of them are attached to the keys that the elimination argument says must be horizontal. This is the cheapest unclaimed information on the board and it is claimed by pressing a key, not by writing a rule."
    [depends: the_action_map_after_five_transitions, key1_inert_at_spawn  probe: pending]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "Twenty-three cells in the top-left corner, in two 3x3 seats with a 1x3 underline beneath each, and ONE toggle witnessed, at t5, all 23 cells at once. CONFIGURATION A, states 0 to 4: slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B, state 5 and the current frame: slot 1 a hollow colour-2 ring with dark underline, slot 2 a hollow colour-9 ring with dark centre and lit underline. Slot 1's centre (2,2) is colour 0 in BOTH configurations, which is why it is board and not an instance; slot 2's centre (2,6) is 1 in A and 0 in B, which is why it is. mdl_segmenter corroborates by frame index without having seen my rules: obj0 is a colour-9 eight-cell 3x3 present in all six frames, obj1 a colour-1 nine-cell 3x3 present in frames 0-4 only, obj5 a colour-2 eight-cell 3x3 first seen at frame 5, obj2 a colour-9 1x3 present in all six. The hollow ring and the lit underline do not appear and vanish, they TRAVEL between the two seats: one marker, two seats, colour 9 marks the occupied seat. WHAT THE SEATS HOLD IS UNKNOWN AND I WILL NOT GUESS. I cannot model the marker as a mover either -- the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring crossing four columns is not a move, and eight recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot2_row1_lights  probe: passed]

  theorem the_panel_guard_is_a_correlation_in_this_record "All eight panel rules carry colored(spawn_probe, 5), which reads cell (8,14) renders floor, which reads the body is not at spawn. In this record there is exactly ONE panel toggle and it happened on the one ACTION5 ever pressed, from lattice (2,2). So `key(5) was pressed` and `the body is away from spawn` are the SAME single event here and the conjunct has no discriminating witness -- by rule 3 it explains no pixel this record can show me. I keep it, and I name the reason rather than dress it up: without it my manual predicts that ACTION5 at spawn, which is where the body stands right now, repaints 23 panel cells, and I have no evidence for that either. The inherited text records that exact deletion being made, being answered by four presses of ACTION5 at spawn with the panel unmoved, and being reversed. I cannot cite those four presses. I can note that the cheap version of the same experiment is available: press ACTION5 at spawn once. Panel still means the guard is earned; panel moves means eight rules are guarded on the wrong thing. A second confound is worth naming before it costs me: the single positive had the body at ONE cell, (2,2), so a guard reading `the body is at (2,2)` fits identically and differs only at a third lattice cell the body has never occupied."
    [depends: key5_slot1_dims, the_panel_is_a_marker_that_alternates_between_two_slots  probe: pending]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9. ACTION2 from configuration A returned SEVEN frames at t2. ACTION5 returned NINE at t5. All three no-ops returned one. My semantics say cascade single_frame, so only the net change is compared and up to eight intermediate frames per command are discarded unread -- I record that as a limitation of my own manual, not of the world. The channel is free and it is the only hint that the panel does anything besides display: the inherited text claims ACTION2 takes seven frames from configuration A and NINE from configuration B, 13/13. That is a LIVE PREDICTION here and it costs nothing to collect, because the panel is now in configuration B and the frame count is printed in every diff. If the next ACTION2 returns nine frames the claim survives; if it returns seven, the panel is cosmetic after all."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: pending]

  theorem dynamic_census "Exactly 73 cells have ever changed and every one has an owner. 23 ARE THE PANEL: slot 1's eight ring pixels at rows 1-3 cols 1-3 excluding centre (2,2) which is colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in A and 0 in B; underline 2's three at row 5 cols 5-7. 24 ARE THE SPAWN RING, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 ARE THE SAME RING SIX ROWS SOUTH, rows 14-18 cols 14-18 minus its aperture (16,16). 2 ARE THE BURNED RIGHT END OF ROW 63, cols 62 and 63. 23+24+24+2 = 73 = dynamic_cells, and it agrees cell for cell with zero_space's enumerated support. BY FRAME-0 COLOUR: 37 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 2 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 37+9+24 = 70 = cells_needing_an_owner exactly, and 4096-73 = 4023 = constant_cells exactly."
    [probe: passed]

  theorem the_dark_type_may_receive_no_instances_and_i_would_rather_be_told "A risk in my own declarations, named in advance. cells_needing_an_owner is 70 while dynamic_cells is 73, and the three missing cells are exactly the three whose frame-0 colour is 0, the background: underline 2 at row 5 cols 5-7. That gap is consistent with the arm treating background-coloured cells as board-explained and refusing to instance them. If so, `object Dark ... arc-colour: 0 arc-instances: all` yields ZERO instances, key5_underline2_lights grounds on nothing, and three pixels of t5 come back unexplained in the responsibility report. I declare Dark anyway, because the alternative is to leave three pixels of an observed change with no owner at all, and because a responsibility report naming those three cells tells me the arm's rule in one round. If they come back unexplained the repair is not another type on colour 0 -- two types on one colour are indistinguishable to an arm that looks objects up by colour and nothing else -- it is to accept the three cells as board and delete the rule."
    [depends: dynamic_census, key5_underline2_lights  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_first_step_east_is_where_it_will_show "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4023 + dynamic 73 = 4096. A cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This prices the first eastward step exactly. Lattice (1,3) is rows 8-12 cols 20-24; not one of those 25 cells has ever changed, so 24 arrival pixels are undrawable NO MATTER WHAT RULE I WRITE. The 24 departure pixels at the spawn ring are instances, but no east-leaves rule exists and none can be written before an east press witnesses one. So the first step east costs 48 wrong pixels, plus one more at (63,61) if the meter turns out to be command parity. THE SECOND step east costs 24, the third costs 0. I state this now so that a refutation whose divergence set is exactly rows 8-12 cols 20-24 is read as the advertised price of new ground and not as a defect in the rules. One further consequence worth knowing before it confuses someone: THE BODY CHANGES TYPE AS IT WALKS. Typing is by frame-0 colour, the body was colour 9 at rows 8-12 and floor was colour 5 everywhere else, so the same physical mover is Glyph9 at spawn and Vacated one cell south."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because the same repair will tempt the next desk. To draw the meter's leading edge before it burns I would need an instance on a board cell. arc-instances: all instances every cell of that colour THE BOARD CANNOT EXPLAIN, and a never-varying cell is precisely what the board explains, so it gets none. The tempting workaround is a second declared type on colour 9 without arc-instances, hoping the arm seats one instance somewhere useful; I reject it, because the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, its seat is unspecified, and any cell it landed on would be claimed twice -- the rule-5 error the grammar warns about in as many words. A landmark cannot help either: landmarks are cells and every event in this language takes an object as its first argument. The hole is a property of the arm and it is permanent for this level."
    [depends: dynamic_census  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "key2_body_leaves grounds on meter instances at row 63 whose sixth-below is row 69, and the inherited certify runs reported zero step crashes, so colored(off-board, k) is FALSE rather than an exception, and `<cell> = wall` is the sanctioned positive test. Eight panel rules rest on this and every row and column discrimination in the panel is built from it. The k-th above is off-board exactly when k exceeds the row: row 1 is above-twice equals wall; row 3 is a colour test on above-twice, false for row 1 precisely because a colour test on an off-board cell is false; row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row BY COLUMN: col 5 is leftof-six equals wall; col 6 is leftof-seven equals wall with a colour test on leftof-once; col 7 is a colour test on leftof-twice. The three are pairwise exclusive, which is why no ambiguity clash has ever been reported on them. Not one rule in this manual uses `not`, deliberately. THIS CLAIM IS NOW UNVERIFIED, because certify could not load a predictor this round, so it must be re-confirmed by the first run that actually executes."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated over several internal frames and the world reports the whole animation for a single action. The refutation that matters: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor. ONE PRESS IS ONE LATTICE CELL, 1/1 in this record, and every distance in the playbook rests on it. With one witness this is the weakest load-bearing claim in the manual and the second ACTION2 press confirms or destroys it for free."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read pixel by pixel out of the CURRENT frame. R=1, rows 8-12, is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; C=7 does not exist in that band, cols 44 onward being void. R=2, rows 14-18, is floor at cols 13-19 and 25-31 only, so C=2 and C=4. R=3, rows 20-24, is floor cols 13-31, so C=2,3,4. R=4 and R=5, rows 26-30 and 32-36, are floor only at cols 13-19, so C=2. R=6, rows 38-42, is the comb: 23 of the 25 pixels at cols 14-18 render colour 8 and only (39,14) and (41,14) are floor, so nothing there is enterable. R=7, rows 44-48, is C=2, plus a fragment of floor at row 48 cols 42-50 that is one row deep and cannot hold a 5x5 body. R=8, rows 50-54, is floor from col 13 to col 48, so C=2 through C=7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across lattice column 2 and separator col 37 is floor across R=1, so LATTICE COLUMN 2 IS CONTINUOUS FROM R=1 TO R=8 APART FROM THE COMB, and LATTICE ROW 1 IS CONTINUOUS FROM C=2 TO C=6. Spawn is (1,2); in six frames the body has occupied exactly TWO cells, (1,2) and (2,2)."
    [depends: key2_body_arrives  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything. key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor -- so the centre is never repainted. Witnessed at t2: (16,16) stayed 5 while all 24 of its neighbours turned 9, and it is absent from the dynamic-cell census for exactly that reason. This matters because it is the only reading under which the winning cell is enterable at all: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell against the current frame. A colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows and cols 43 and 49 are separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west wall at col 43 left as FLOOR. Inside it, rows 50-54 cols 44-48 are floor except one colour-9 pixel at the exact centre (52,46). Outside it, col 50 rows 49-56 is a one-cell strip of floor leading nowhere. Overlay the body standing in (8,7) -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my inventing a goal predicate: the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in six frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem pixel at (12,40), colour 8 filling col 40 from row 12 down to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18. It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell -- the eight knob pixels other than its centre, plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: drive the body into a colour-8 cell and my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Five commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1 through ACTION5 plus RESET; the alphabet is ACTION1 through ACTION7. Two commands are entirely unconstrained, and in this family one is normally a click carrying coordinates. That matters here, because the knob is a 3x3 target the body appears unable to stand on and a click is the shape of interaction that presses it. I CANNOT WRITE SUCH A RULE: the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT -- comb pixels going 8 to 5 -- and never its precondition. With no witness for key(6) or key(7), no rule may name them, so they sit outside this manual's alphabet."
    [probe: pending]

  theorem the_goal_section_is_absent_on_purpose "There is no goal: section, which compiles is_goal to False, and I would rather have no goal than a goal true in the wrong states, because the latter stops a planner at its first step. Every candidate fails on this arm. `Cart.pos = exit_cell` needs one named instance and arc-instances: all gives me Glyph9_r8c14 and thirty-six siblings, none of them the body as such. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but their frame-0 colour is 5 so they would type as Vacated, indistinguishable from the 24 Vacated cells at rows 14-18 -- and count(Vacated, color = 9) = 24 is exactly the state of the body standing one cell south of spawn, which is not a win. count(Glyph9, color = 5) = 24 is true of every state in which the body is anywhere but home. A Wire type on colour 8 would have zero instances because every colour-8 cell is constant, so count(Wire) = 0 would be true at RESET. I name the price plainly: no plan terminates, and nothing ranks one command above another except what the playbook says."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter chose connected_components(4) with split_by_color false and reports NEGATIVE gain on both variants, -5042 bits at 6 tracks and -17520 at 17, so on this record its own script is longer than writing the pixels out and I owe it nothing structural. Its tracks still corroborate the panel by frame index, and that is what I took: obj0 colour-9 eight cells 3x3 across all six frames, obj1 colour-1 nine cells present frames 0-4, obj5 colour-2 eight cells first seen at frame 5, obj2 colour-9 1x3 across all six -- the ring and the underline travelling between two seats rather than appearing and vanishing. obj4 is the whole 64-cell bar of which 2 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. cegis_miner refuses on every track -- four refusals naming recolor and vanish narrations and one absent object -- and its verdict, the world does not narrate as one mover, is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours. zero_space self-reports THIN in its own words -- 5 transitions constrain rank 3 of 365 features, null space dimension 362, nearly every vector in it a law true over these states and unfalsified rather than confirmed -- and its single global law enumerates exactly my 73 dynamic cells, which is the census and nothing more."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body is at spawn, the panel is in configuration B, two meter cells are burned, the next command index is 6. ACTION3 AT SPAWN, which is what the playbook asks for: my manual predicts ZERO cells changed and has no witness for that at this cell. If the body steps east I am wrong by 48 pixels, ACTION3 IS EAST and the map closes; if only (63,61) burns I am wrong by one pixel, the meter is command parity rather than key-driven, and ACTION4 is east by elimination; if nothing at all changes then ACTION3 is not a direction key here, ACTION4 is east by elimination, and the key-driven meter reading survives. THREE OUTCOMES AND ALL THREE ARE INFORMATIVE, which is the property I am buying. ACTION4 at spawn: the same experiment with the labels swapped, except that a burn there is uninformative about the meter because 4 is an even key. ACTION2 at spawn: 48 body cells I draw correctly, plus one burn I do NOT draw since meter_burn_key2_next is out of the manual -- one wrong pixel, one free datum in the cascade length, and no new witness. ACTION5 at spawn: my manual predicts nothing and has no witness; if the panel moves, eight rules are guarded on the wrong atom and I want to know. ACTION1 at spawn: witnessed silence, nothing bought, the only strictly worthless press on the board."
    [depends: the_two_meter_readings_are_not_separated_here_and_the_next_command_separates_them, silence_is_a_prediction_and_three_of_my_five_spawn_silences_are_forged  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHERE THE ROUND ACTUALLY WENT =========
# No command was adjudicated this round. certify returned an EMPTY replay,
# an EMPTY responsibility map and unambiguous null, because theory.py was
# never generated: the manual did not compile. One landmark line carried
# prose where the grammar demands a coordinate. Nothing else could run.
# The manual is repaired and rewritten against the observation record as it
# now stands -- 6 states, 5 transitions -- and it should replay 5/5 with no
# priced-in miss. THE FIRST THING TO CHECK NEXT ROUND IS THAT CERTIFY HAD
# SOMETHING TO RUN. A compile failure is invisible to every other check.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   Body at lattice (1,2), spawn. Panel in configuration B. Two meter cells
#   burned, cols 62-63 of row 63. Next command index is 6.
#
#   At spawn:  key(2) -> 48 body cells south, WITNESSED at t2
#              key(1) -> nothing, WITNESSED at t1
#              key(3), key(4), key(5) -> nothing, NO WITNESS AT THIS CELL
#
#   Open neighbours of spawn are DOWN and RIGHT only; up and left are void.
#   ACTION1 was pressed here and moved nothing, so it is neither.
#   At (2,2) the open neighbours were UP and DOWN only; ACTION3 and ACTION4
#   were each pressed there and moved nothing, so NEITHER IS VERTICAL.
#   If either is a direction key at all, IT IS HORIZONTAL.
#
# ========= THE ONE THING WORTH BUYING, AND IT PAYS TWICE =========
# PRESS ACTION3 FROM SPAWN.
#   (1) It settles the east key. Body steps -> ACTION3 is east and the map
#       closes. Body still -> ACTION4 is east by elimination. Either answer
#       names it, and east of spawn is three lattice cells of unbroken
#       floor while west is void, so the test is free at this cell.
#   (2) It separates the two meter readings AT NO EXTRA COST. Both readings
#       fit t1-t5 identically because every even index carried an even key.
#       Index 6 is EVEN and key 3 is ODD: key-driven predicts no burn,
#       command-parity predicts (63,61) burns. No other single command
#       splits them.
#   (3) It converts one of three forged silences at spawn into a witness.
#   ACTION4 is the same probe minus benefit (2), so it is the fallback and
#   not the choice.
#
# THE ADVERTISED PRICE OF A STEP ONTO FRESH GROUND: 48 pixels the manual
# cannot draw. Rows 8-12 cols 20-24 have never changed, so they are board
# and no rule may draw their first change; the 24 departure pixels need an
# east-leaves rule that cannot be written before an east press witnesses
# one. 24 pixels for the second step, 0 for the third. A refutation whose
# divergence set is exactly that block is the price, not a defect.
#
# TWO PRICES ALREADY POSTED, so neither can be read as a surprise:
#   - the panel toggle-back rules are OUT of the manual for want of a
#     witness in this record, so the next effective ACTION5 costs 23 pixels
#     if the panel does toggle back.
#   - meter_burn_key2_next is OUT for the same reason, so a second ACTION2
#     costs one pixel.
#
# ------------------------------------------------------------------------
# THE MAP, FOR WHEN THE DIRECTION KEYS ARE NAMED. Eleven lattice cells are
# reachable and the body has stood in two. Every route south crosses (6,2),
# 23 of whose 25 pixels are colour 8; lattice column 2 is the only
# north-south corridor, so the comb is the door and not an obstacle. The
# comb is the near end of ONE connected colour-8 wire whose far end is a
# 3x3 knob beside lattice (1,5), three steps east along lattice row 1. The
# socket at (8,7) is drawn as three colour-9 walls with a pip at its exact
# centre -- a keyhole shaped for a body with an aperture -- and it is south
# of the comb. So: open the gate before planning anything south of it, and
# the gate is reached by going EAST, which is the key nobody has pressed.

order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_probe_that_answers_two_open_questions_in_one_press      [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     confirm_the_manual_compiled_before_trusting_any_certify_number   [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     collect_the_free_cascade_length_whenever_a_command_is_spent      [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     even_key_pressed_only_to_separate_the_two_meter_readings => dead   [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_single_command_can_close                         [admissible: lean]
heuristic readings_still_live_that_this_command_would_eliminate             [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                        [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 3/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    an_odd_key_while_the_command_index_is_even                       [ev: 0/5 commands so far]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 3/5 keys at spawn]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 5/5 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
prefer    a_press_at_a_third_lattice_cell_that_splits_up_from_return       [ev: 1/1 key5_presses]
```

## Why you are being called: the surprises that fired

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "e28df7de3e0bd1cd",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 18 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '25cac958273811a3' against the world's 'af3bb95d3135e37c'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.650 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 2,
 "expected_bits": 0.650022421648,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "25cac958273811a3",
 "n_hypotheses": 18,
 "n_survivors": 0,
 "observed": "af3bb95d3135e37c",
 "probe_id": "P-01",
 "vacuous_streak": 1
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 18 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '9bb17844cc3a57c9' against the world's '0e1cd0b30fbb12b3'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.650 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 5,
 "expected_bits": 0.650022421648,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "9bb17844cc3a57c9",
 "n_hypotheses": 18,
 "n_survivors": 0,
 "observed": "0e1cd0b30fbb12b3",
 "probe_id": "P-02",
 "vacuous_streak": 2
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
  "detail": "5/5 transitions replay exactly",
  "matched": 5,
  "ok": true,
  "transitions": 5
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
  "detail": "no (state, action) among 6 x 5 admitted two rules, and all 30 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 30,
  "pairs_nominal": 30,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 6,
  "states_reconstructed": 6,
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
  {"id": "L-07", "subject": "the heuristic_miss demand for a goal", "verdict": "reject",
   "as": "no_goal_is_writable_on_this_arm_and_i_refuse_to_invent_one", "why": "the winning cell, lattice (8,7) at rows 50-54 cols 44-48, has not changed in ten frames, so it is board, has no instances and count() cannot range over it; every writable alternative is true in non-winning states, and count(Vacated, color = 9) = 24 in particular holds both at the socket and one cell south of spawn where the body has already stood four times."},
  {"id": "L-08", "subject": "a Gate type on colour 8 as a future subgoal carrier", "verdict": "probe-pending",
   "why": "every colour-8 pixel is constant so the type would have zero instances today and count(Gate) = 0 would be true at RESET; the first comb pixel that changes makes it instanceable and makes the first honest subgoal writable."},
  {"id": "L-09", "subject": "off-board cell terms evaluate false", "verdict": "accept",
   "as": "off_board_cell_terms_evaluate_false_and_that_is_load_bearing", "why": "certify ran this time, reported zero step crashes over 30 adjudicated pairs and replayed 5/5 exactly, which is only possible if colored(off-board, k) is false rather than an exception -- thirteen panel rules and meter_burn_key1_edge's t1 silence depend on it."},
  {"id": "L-10", "subject": "the census", "verdict": "accept",
   "as": "dynamic_census", "why": "23 panel + 24 spawn ring + 24 lower ring + 4 burned meter = 75 = dynamic_cells, 4096 - 75 = 4021 = constant_cells, and 75 - 3 background-coloured = 72 = cells_needing_an_owner, which pins the arm's accounting convention."},
  {"id": "L-11", "subject": "zero_space's single global law", "verdict": "entailed",
   "why": "it enumerates exactly the 75 cells of my census and nothing more; its own verdict is THIN -- 9 transitions constrain rank 5 of 375 features -- so it confirms the ownership list and asserts no dynamics."},
  {"id": "L-12", "subject": "cegis_miner's verdict that the world does not narrate as one mover", "verdict": "reject",
   "why": "true of the arm, false of the world: there is one mover, a rigid 24-pixel ring, and an arm that instances one object per cell can only ever see 24 simultaneous recolours, which is why the miner refuses on recolor and vanish narrations."},
  {"id": "P-01", "subject": "ACTION4 from spawn at index 10", "verdict": "probe-pending",
   "why": "the sole surviving candidate for east; the manual predicts exactly one changed cell, (63,59) burning, so a step east shows up as a clean 48-pixel divergence confined to rows 8-12 cols 14-24, and no step east means no key among the five moves the body horizontally at all."},
  {"id": "P-02", "subject": "ACTION5 from spawn at an odd index", "verdict": "probe-pending",
   "why": "separates north from undo-the-last-move, which have never been distinguished, and simultaneously tests whether the colored(spawn_probe, 5) guard on thirteen panel rules is earned; odd index so the parity burn does not sit inside the divergence set."},
  {"id": "P-03", "subject": "ACTION1 or ACTION3 from spawn", "verdict": "reject",
   "why": "inertness at this cell is already witnessed -- ACTION1 at t1 and t8, ACTION3 at t9 -- so neither creates a witness, and at an even index ACTION3 additionally costs one undrawn meter pixel."},
  {"id": "E-01", "subject": "the true meter law", "verdict": "probe-pending",
   "why": "I wanted `when index_is_even then recolored(leading_edge, 1)`. The guard language reads pixels, the action name and off-board tests, and no cell in the frame tracks command parity -- the panel toggles on ACTION5, not on parity. I wrote three leading-edge rules keyed to actions 1, 2 and 4 instead: the largest fragment with zero false positives in this record, labelled a shadow in the manual, with the exact failure predicted (one wrong pixel the first time key 1, 2 or 4 lands on an odd index; one missing pixel the first time key 3 or 5 lands on an even one)."},
  {"id": "E-02", "subject": "the winning condition", "verdict": "probe-pending",
   "why": "I wanted `goal ring_of(lattice_8_7) = colour 9`. There is no goal form over a coordinate region, no single named instance for the body under arc-instances: all, and the socket cells are constant so they have no instances to count. I wrote no goal: section at all and put the winning position in the manual as the_socket_is_a_keyhole_and_names_the_winning_position, with the two conditions that would make a goal writable stated in no_goal_is_writable_on_this_arm."},
  {"id": "E-03", "subject": "a rule for the knob", "verdict": "probe-pending",
   "why": "I wanted a click rule naming the knob's 3x3 target at rows 9-11 cols 39-41. act=key(6) parses but the guard language has nowhere to put two coordinates, so the rule would fire on every click anywhere and be silently wrong about which cell was clicked. I wrote two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click instead, which records that I can capture a click's effect and never its precondition."},
  {"id": "E-04", "subject": "one type per physical body", "verdict": "probe-pending",
   "why": "I wanted the mover to be one object that keeps its identity as it walks. The arm types cells by their frame-0 colour, so the same 24-pixel ring is Glyph9 at spawn and Vacated one cell south, and every movement law has to be written twice, once per type. Recorded in the_manual_heals_one_step_behind."}
]
```
```
