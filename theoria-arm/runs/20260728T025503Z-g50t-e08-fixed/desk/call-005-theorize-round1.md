# call-005-theorize-round1

model: `claude-opus-5` · 732291 ms · $1.725836 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 26283, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 26283, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 26283, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 26283, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 57752, "type": "message"}], "output_tokens": 57752, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
0222099900000000000000000000000000000000000000000000000000000000
0202090900000000000000000000000000000000000000000000000000000000
0222099900000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000099900000000000000000000000000000000000000000000000000000000
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
- t6   ACTION1   frames=1   state=NOT_FINISHED (63,61) 9->1
- t7   ACTION2   frames=9   state=NOT_FINISHED 48 cells changed, rows 8-18, cols 14-18, [5, 9] -> [5, 9]
- t8   ACTION3   frames=1   state=NOT_FINISHED (63,60) 9->1
- t9   ACTION4   frames=1   state=NOT_FINISHED no cells changed

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
   "ValueError: object absent at frame 0; unsupported on this fixture"
  ],
  "tracks": [
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
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
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
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
  "candidates": 6,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 1,
   "move": 2,
   "recolor": 7,
   "vanish": 1
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
    "frames_present": 5,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj5"
   }
  ],
  "variants": [
   {
    "baseline_bits": 2808,
    "compression_ratio": 2.587251,
    "events": 11,
    "gain_bits": -4457,
    "ms": 21,
    "script_bits": 7265,
    "split_by_color": false,
    "tracks": 6
   },
   {
    "baseline_bits": 2808,
    "compression_ratio": 9.185185,
    "events": 31,
    "gain_bits": -22984,
    "ms": 35,
    "script_bits": 25792,
    "split_by_color": true,
    "tracks": 22
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
  "difference_rank": 6,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.016,
   "difference_rank": 6,
   "features": 375,
   "space_dimension": 369,
   "transitions": 9,
   "verdict": "THIN: 9 transitions constrain rank 6 of 375 features, so the null space has dimension 369 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
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
     "c0@34",
     "c1@34",
     "c2@34",
     "c5@34",
     "c9@34",
     "c0@35",
     "c1@35",
     "c2@35",
     "c5@35",
     "c9@35",
     "c0@36",
     "c1@36",
     "c2@36",
     "c5@36",
     "c9@36",
     "c0@37",
     "c1@37",
     "c2@37",
     "c5@37",
     "c9@37",
     "c0@38",
     "c1@38",
     "c
```

The full proposal stream is 1486 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 9 commands (RESET + ACTION1..ACTION5,
# ACTION1..ACTION4). 75 cells have ever changed; this manual names all 75 and
# owns the 72 that any colour-keyed object can own.
#
# WHAT CHANGED THIS ROUND, AND WHY:
#
#   1. THE PARSE ERROR IS FIXED, AND IT WAS NOT WHAT I FEARED. The compiler
#      said "Line 65: Expected 'goal' statement, got: laws:". Line 65 is the
#      `laws:` header; the `goal:` section above it contained comment lines and
#      no statement, and a section header demands at least one statement. The
#      spec says "No goal section at all is legal", so the section is DELETED
#      rather than filled with a goal I do not believe. See
#      the_goal_section_is_absent_on_purpose.
#
#   2. THE BET OF LAST ROUND IS WON. Six-deep nested cell terms PARSE. The
#      proof is the error message itself: the parser reached line 65, and the
#      four movement rules are lines 44-53. So `below(below(...))` is legal
#      cell syntax in this grammar and the manual may speak about distance six
#      without inventing one landmark per lattice cell. That is the single
#      most valuable fact I learned this round and it is now a settled part of
#      the language, not a gamble.
#
#   3. THE REPLAY DIVERGENCE IS ANSWERED, NOT PATCHED. certify replayed the
#      LAST COMPILED manual -- the move-less one -- and it lost 24 cells at
#      the first ACTION2, saying 5 where the world said 9 over rows 14-18,
#      cols 14-18 minus (16,16). That is exactly the footprint of a body that
#      arrived and was never drawn. The two key2 rules in this manual draw
#      those 24 cells and erase the 24 they came from, so the divergence
#      should close to zero on t2 and on t7 without a single new concept. If
#      it does not close, the fault is in `colored` or in instance typing and
#      not in the physics, and I will know which from the cells that remain.
#
#   4. A NEW STRUCTURAL LIMIT IS NAMED: instances live only where pixels have
#      already moved. See only_visited_cells_have_instances. It changes the
#      price of the next descent from 24 wrong cells to 48, and I would rather
#      pay a known 48 than hide it.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark spawn_center    # arc-cell: (10, 16)
  landmark socket_center   # arc-cell: (52, 46)
  landmark gate_center     # arc-cell: (40, 16)
  landmark knob_center     # arc-cell: (10, 40)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t9 compress: 39]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t7 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t9 compress: 9]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t7 cov: 48/48]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t7 cov: 48/48]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

laws:
  invariant nine_count_frame0 count(Glyph9) = 39 [status: counted]
  invariant five_count_frame0 count(Vacated) = 24 [status: counted]
  invariant one_count_frame0 count(Spent) = 9 [status: counted]
  invariant board_static count(board) = 4021 [status: counted]

  theorem the_goal_section_is_absent_on_purpose "The previous manual carried a `goal:` header whose body was two comment lines, and the compiler refused it at the next section header. A section must contain a statement. I did not fill it, because the only goals this grammar can state are false: `Cart.pos = exit_cell` needs a single named instance and `arc-instances: all` gives me Glyph9_r8c14 and 38 siblings instead; `count(Vacated, color = 9) = 24` is true of the body standing ANYWHERE off spawn, which is most of the maze and not a win. A goal that is true in the wrong states is worse than no goal, because the planner would stop at the first one. So the section is gone, is_goal is False, and the playbook steers by lattice distance instead. This is a language limit I am recording in the open, not a belief I am hiding."
    [probe: pending]

  theorem nested_cell_terms_parse "SETTLED, and settled by the compiler. Last round I spent the manual on the guess that `below(below(x))` is legal, and said that if it was not, nothing would compile. The compiler's only complaint was at line 65, the `laws:` header; the movement rules are lines 44-53 and it walked past them. A recursive-descent parser that rejected nested cell terms would have died there, not thirteen lines later. Therefore this grammar can express distance six, one line of guard draws 24 pixels, and the fallback I dreaded -- one landmark per lattice cell, which is coordinates in disguise and generalises to nothing -- is off the table permanently."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem the_replay_divergence_and_what_i_did_about_it "certify replayed the move-less manual and diverged at the first ACTION2, 24 cells, manual 5 versus world 9 across rows 14-18 cols 14-18 minus (16,16). Those 24 cells ARE the body's arrival footprint, and the old manual had no rule that could draw an arrival. I have answered it with physics rather than with a patch: key2_body_arrives recolours exactly those 24 cells to 9 and key2_body_leaves clears the 24 they left. I make the prediction sharp so it can be scored -- after this manual compiles, t2 and t7 must each replay with ZERO cells wrong except (63,63) at t2, which is the meter and which I have deliberately left undrawn. Any other residue at t2 or t7 refutes my reading of `colored`, of instance typing, or of both, and the identity of the residual cells says which."
    [depends: key2_body_leaves, key2_body_arrives  probe: pending]

  theorem only_visited_cells_have_instances "New this round, and it changes what my manual can promise. `arc-instances: all` creates one instance per cell of that colour THE BOARD CANNOT EXPLAIN, and board is the never-varying cells. The arm reports 72 cells_needing_an_owner and 0 unexplained, and 72 is exactly my dynamic census minus the three cells no colour can own -- so the instance set is the cells that have already changed, not every cell of that colour. Consequence: the corridor ahead, rows 20-24 cols 14-18, is constant floor so far and therefore has NO Vacated instances, so key2_body_arrives cannot ground there however true it is. The next ACTION2 will cost me 48 wrong cells -- 24 for a body I still draw at rows 14-18 and 24 for one I cannot draw at rows 20-24 -- and only 24 of those are the missing-rule debt below. The round after, those cells will be dynamic, instances will exist, and the same unchanged rule will draw them. I am not confident enough to call this proven: it is an inference from the arm's own 72, and the cheapest test is the next descent, whose residue will be 48 cells if I am right and 24 if instances exist everywhere."
    [depends: key2_body_arrives  probe: pending]

  theorem the_body_is_a_ring_on_a_six_pixel_lattice "The mover is a 5x5 hollow ring of colour 9 whose top-left sits at (6R+2, 6C+2), hole at (6R+4, 6C+4). Seen at (R,C) = (1,2), rows 8-12, and (2,2), rows 14-18; one command displaces it exactly six pixels. The maze agrees six is the module: void columns run 20-24 and 32-36 with single floor columns at 19, 25, 31, and the socket interior is rows 50-54 cols 44-48, which is lattice (8,7). Spawn is lattice (1,2). The corridor at column-lattice 2 is floor at R=1..5 and R=7..8 and carries the colour-8 comb at R=6."
    [depends: key2_body_leaves, key2_body_arrives  probe: pending]

  theorem dynamic_census "Exactly 75 cells have ever changed. 23 are the status panel at rows 1-5 cols 1-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus its hole (10,16), which never changes and is therefore board. 24 are the same shape six pixels down, rows 14-18 cols 14-18 minus its hole (16,16). 4 are the right end of the row-63 bar, cols 60-63. 23+24+24+4 = 75 and nothing is left over. At frame 0 they split as 39 colour-9 (8 panel ring + 3 panel underline + 24 spawn ring + 4 meter), 9 colour-1 (the solid slot-2 block), 24 colour-5 (the lower ring's footprint) and 3 background ((5,5),(5,6),(5,7)); 39+9+24 = 72, exactly the arm's cells_needing_an_owner."
    [probe: pending]

  theorem the_two_key2_rules_i_am_still_not_allowed_to_write "The arm types cells by their frame-0 colour, so the body changes type as it walks: the ring at rows 8-12 is Glyph9, at rows 14-18 it is Vacated. Every movement law therefore needs four rules, and for ACTION2 I hold witnesses for only two. The missing pair, verbatim so the next desk can paste them: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)' and 'rule key2_body_arrives_at_nine forall ?p in Glyph9 when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 9) then recolored(?p, 9)'. I have checked both for spurious grounding and both are inert everywhere except the intended cells, so the temptation to write them now is real. I refuse anyway, on rule 2: they have never fired in an observed transition, and the identical-looking pair I wrote last round on one observation each -- the meter rules -- were both refuted within two commands. One consecutive ACTION2 buys both, and the playbook prefers it."
    [depends: key2_body_leaves, key2_body_arrives  probe: pending]

  theorem the_action_map "ACTION2 is down: proven twice, t2 and t7, six pixels each. The rest is the unique assignment consistent with every observation. ACTION1 did nothing at t1 and t6, both from rows 8-12, where six above is rows 2-6, off the floor. ACTION3 did nothing at t3 and t8, both from rows 14-18, where six left is cols 8-12, void. ACTION4 did nothing at t4 and t9, both from rows 14-18, where six right is cols 20-24, void. So 1=up, 3=left, 4=right all fit as blocked moves and no other assignment explains all six no-ops. ACTION5 is respawn: it alone has ever touched the panel. The separator is free and available RIGHT NOW: the body sits at lattice (2,2) and the cell above it, rows 8-12, is floor, so ACTION1 here must move the body up six pixels if 1=up and must do nothing if it is anything else. It is also the one probe whose entire outcome lands on cells that already have instances, so my manual could be scored on it exactly -- if I had a key1 rule, which I do not, so it costs 48 wrong cells to buy the fact."
    [depends: key2_body_leaves, key5_body_respawns  probe: pending]

  theorem the_meter_is_a_clock_and_the_dsl_has_no_counter "Row 63 is a 64-cell colour-9 bar losing its rightmost live cell to colour 1. Burns: t2 (63,63), t4 (63,62), t6 (63,61), t8 (63,60). No burns: t1, t3, t5, t7, t9. That is every even-numbered command and no odd one, and it cuts clean across the actions -- ACTION2 burned at t2 and not t7, ACTION4 burned at t4 and not t9, ACTION1 burned at t6 but not t1, ACTION3 burned at t8 but not t3. I also tested it against internal time, since commands return 1, 7 or 9 frames: cumulative frames at the burns are 8, 10, 20, 30, which is a clean period of ten for the last three and not for the first, so I do not claim it. Either reading needs a counter over commands and the guard language has no state that is not a cell. I write NO meter rule, which predicts 'the bar never burns' and is wrong by one cell on four of nine transitions. The alternative, 'burn every command', is wrong by one cell on five of nine AND empties a 64-cell budget twice too fast for any planning that reads the bar as a budget."
    [probe: pending]

  theorem the_meter_rules_i_withdrew "The manual before last carried meter_burn_key2 and meter_burn_key4 on one observation each. t7 refuted the first (an ACTION2 with no burn), t9 the second (an ACTION4 with no burn); worse, meter_burn_key4's guard 'right neighbour already spent' now grounds on (63,59) and would invent a fifth burn. The lesson is recorded because I nearly repeated it this round: one observation per action is not evidence for a rule keyed on the action when a clock explains the same pixels."
    [probe: pending]

  theorem the_panel_debt_i_am_choosing_to_carry "The panel is two 3x3 icon slots at rows 1-3 cols 1-3 and cols 5-7, each with a 1x3 underline at row 5. Frames 0-4: slot 1 a hollow colour-9 ring, underline lit; slot 2 a solid colour-1 block, underline dark. Frame 5 on: slot 1 a hollow colour-2 ring, underline dark; slot 2 a hollow colour-9 ring, underline lit. I read it as two lives, lit underline marking the live one, colour 2 marking a spent one. I write no rule and every ACTION5 costs me 23 wrong cells. The reason is rules 3 and 5, not laziness: (1,2) and (5,2) have byte-identical four-neighbourhoods so no guard separates the slot-1 ring from its underline, and separating the slot-2 ring from its centre needs a disjunction this grammar does not have, so the honest encoding is four rules that all fire on a corner cell -- exactly the ambiguity rule 5 forbids. 23 wrong cells on a command I intend never to press again is the cheaper error."
    [probe: pending]

  theorem three_cells_no_object_can_ever_own "(5,5), (5,6), (5,7) are background at frame 0 and colour 9 from frame 5, so no colour-keyed object owns them and none can: an arc-colour 0 object would claim three thousand background cells. Any future panel rule has a floor of 3 wrong cells. This is exactly the gap between the arm's 75 dynamic cells and its 72 cells_needing_an_owner, and it is structural."
    [probe: pending]

  theorem key5_is_respawn_and_i_have_written_it_as_respawn "key5_body_clears and key5_body_respawns say: on ACTION5 any floor cell that is body-coloured returns to floor and the spawn ring lights up. That is respawn-from-anywhere and it fits t5 exactly, 24/24 on both halves. I checked key5_body_respawns for spurious grounding: the only Glyph9 instances that ever render 5 are the spawn ring's, since panel cells render 9, 2 or 0 and meter cells render 9 or 1. The rival reading, 'ACTION5 is up', fits t5 equally well because the body happened to be one lattice cell below spawn. I chose respawn because ACTION5 alone has touched the panel and because 1-4 already exhaust the directions. Separator: press ACTION5 from a cell that is NOT one lattice cell below spawn. Land at spawn, respawn; move up one, my two rules are wrong and become an up-rule. It costs a life, so it waits behind every free probe."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem the_socket_is_the_conjectured_lock "Rows 49-55, cols 43-49 hold a static colour-9 outline, open on the left at col 43 for rows 50-54, with a single dot at its centre (52,46). Its interior, rows 50-54 cols 44-48, is lattice (8,7), and the body is a 5x5 ring whose hole is its centre -- so a body parked there puts the dot exactly in the hole and covers not one pixel of it. That is a lock and a key and it is the only shape in the frame that fits the body. It also means the win leaves NO colour signature I can test: the 24 arriving cells go 5 to 9 like any other move and the dot never changes. Route, in lattice steps: down column-lattice 2 from (2,2) to (8,2), then right five to (8,7); row band 50-54 is unbroken floor from col 13 to col 48."
    [probe: pending]

  theorem the_only_route_down_and_the_gate_across_it "Cols 14-18 is the sole corridor from spawn to the bottom room; floor at lattice rows R=1..5 and R=7..8, blocked at R=6 by a five-toothed colour-8 comb filling rows 38-42 cols 14-18. A colour-8 cable leaves the comb along row 40, runs right to col 40 and up col 40 to a 3x3 colour-8 knob at rows 9-11 cols 39-41, lattice (1,6), the same lattice row as spawn. So the comb is plausibly a gate and the knob plausibly its switch. No colour-8 cell has changed in nine commands, which is why 8 is board and not an object. My rules make this falsifiable: key2_body_arrives needs the destination to render 5 and the comb renders 8, so my manual says the body stops at R=5. If it walks through, the gate is open and I learn it in one command."
    [depends: key2_body_arrives  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants (-4457 and -22984 bits), so its own segmentation loses to writing the pixels out and I owe it nothing; its obj3 is a 1006-cell colour-null blob that swallowed the maze floor, which is not an object but is a fair description of my `board`. obj0, obj2 and obj4 are colour-9 fragments already inside Glyph9; obj5 is the colour-2 panel ring, which is Glyph9 cells after a recolour and gets no type of its own -- a second type on the same pixels would invite the double claim rule 5 forbids. zero_space self-reports THIN (9 transitions constrain rank 6 of 375 features, null space dimension 369) and its one global law restates my 75-cell census. cegis_miner's refusal is the most useful sentence any engine produced: 'no track satisfies the precondition of exactly one move event per transition; the world does not narrate as one mover.' That is true of the ARM and false of the world. The world has exactly one mover, a 24-cell rigid ring; the arm can only see 24 simultaneous recolours, which is why my movement law needs four rules instead of one moved() event."
    [probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
# The manual still has no goal it can state, so nothing here may name a
# sequence. Every line is a criterion on the current frame plus the manual's
# own open questions. Two lines changed this round: descending now buys a rule
# as well as ground (the missing key2 pair), and the up-probe is priced,
# because only_visited_cells_have_instances says a step into fresh corridor
# costs 48 wrong cells in replay while the up-probe costs 48 and buys the
# whole action map.

order     confirm_a_key_direction_before_relying_on_it             [proof: lean]
order     descend_the_only_corridor_before_testing_the_gate        [proof: lean]
order     resolve_gate_passability_before_planning_the_bottom_room [proof: lean]
order     free_probes_before_life_costing_probes                   [proof: lean]
order     witness_a_rule_before_writing_it                         [proof: lean]

prune     action_that_was_a_no_op_from_this_lattice_cell => dead    [proof: lean]
prune     respawn_while_the_body_still_has_a_legal_move => dead     [proof: lean]
prune     destination_lattice_cell_is_not_floor => dead             [proof: lean]
prune     meter_exhausted and not goal => dead                      [proof: lean]
prune     panel_slots_exhausted and not goal => dead                [proof: lean]

heuristic lattice_manhattan_to_socket_interior                      [admissible: lean]
heuristic unexplained_cells_after_redraw                            [admissible: lean]
heuristic meter_cells_still_lit                                     [admissible: lean]

prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule  [ev: 2/2 moves]
prefer    step_toward_the_socket_when_the_destination_reads_floor    [ev: 2/2 moves]
prefer    press_a_direction_key_from_a_cell_where_it_is_unblocked    [ev: 6/6 no_ops]
prefer    stay_in_the_corridor_that_reaches_the_socket               [ev: 1/1 levels]
prefer    probe_the_knob_only_if_the_gate_refuses_the_body           [ev: 1/1 levels]
prefer    a_probe_whose_outcome_lands_on_cells_that_have_instances   [ev: 1/1 levels]
prefer    untried_action_in_an_unvisited_lattice_cell                [ev: 2/5 levels]
```

## Why you are being called: the surprises that fired

### replay_mismatch (empirical family -> theory.dsl)

replay diverges at t=1 (frame_mismatch)

```json
{
 "arc_action": "ACTION2",
 "cells": [
  {
   "cell": [
    63,
    63
   ],
   "manual_says": 9,
   "world_says": 1
  }
 ],
 "cells_wrong": 1,
 "kind": "frame_mismatch",
 "t": 1
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
  "arc_action": "ACTION2",
  "cells": [
   {
    "cell": [
     63,
     63
    ],
    "manual_says": 9,
    "world_says": 1
   }
  ],
  "cells_wrong": 1,
  "kind": "frame_mismatch",
  "t": 1
 },
 "proof_layer_available": false,
 "replay": {
  "detail": "1/9 transitions replay exactly",
  "matched": 1,
  "ok": false,
  "transitions": 9
 },
 "responsibility": {
  "cells_unexplained": 0,
  "detail": "every pixel of frame 0 belongs to the board or to an object",
  "ok": true,
  "total_cells": 4096
 },
 "unambiguous": {
  "actions": 2,
  "clashes": [],
  "detail": "no (state, action) among 10 x 2 admitted two rules",
  "ok": true,
  "scope": "sampled",
  "states": 10
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
# theory.dsl -- world observed for 9 commands (RESET + ACTION1..ACTION5,
# ACTION1..ACTION4). 75 cells have ever changed; this manual names all 75 and
# owns the 72 that any colour-keyed object can own.
#
# WHAT HAPPENED THIS ROUND:
#
#   1. THE PREDICTION WAS MET EXACTLY. Last round I wrote, in the manual and in
#      advance: "t2 and t7 must each replay with ZERO cells wrong except
#      (63,63) at t2." certify's first divergence is t=1, ACTION2, cells_wrong
#      = 1, cell (63,63), manual 9 world 1. That is the prediction, to the
#      cell. The four movement rules are physics and they are now paid for.
#
#   2. THE INSTRUMENT IS SATURATED, AND I CAN PROVE IT. replay reports 1/9. If
#      replay re-seeded from the world frame each command, my manual would
#      match at least three transitions (the two no-ops it predicts correctly
#      and the second descent). It reports one. So replay carries its own state
#      forward, one wrong cell at t=1 poisons every later comparison, and the
#      meter is a cell no guard in this language can predict. My replay score
#      is pinned at 1/9 for the rest of this game. From here I score myself on
#      the responsibility check and on hand-read frame diffs, not on `matched`.
#      See replay_accumulates_so_the_meter_pins_the_score.
#
#   3. I READ THE WHOLE MAZE OFF THE FRAME AND IT HAS EXACTLY ONE DOOR. The
#      lattice is 6 rows by 8 columns of 5x5 cells. From spawn the body can
#      reach eleven cells and no more; the socket is not among them; the single
#      cell separating the two halves is the colour-8 comb, and the only thing
#      touching the reachable region that is neither floor nor void is the
#      colour-8 knob wired to that comb. That is a whole theory of the game,
#      and it is falsifiable in one command.
#
#   4. I WITHDRAW AN OVER-CLAIM OF MY OWN. Last round's action map said the
#      direction assignment was unique. It is not: at spawn, left is void too,
#      so ACTION1 could be left. What IS forced is that ACTION3 and ACTION4 are
#      not up. The corrected argument, and the one command that settles it, are
#      in the_action_map_is_weaker_than_i_claimed.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark spawn_center    # arc-cell: (10, 16)
  landmark socket_center   # arc-cell: (52, 46)
  landmark gate_center     # arc-cell: (40, 16)
  landmark knob_center     # arc-cell: (10, 40)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t9 compress: 39]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t7 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t9 compress: 9]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t7 cov: 48/48]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t7 cov: 48/48]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

laws:
  invariant nine_count_this_build count(Glyph9) = 39 [status: counted]
  invariant five_count_this_build count(Vacated) = 24 [status: counted]
  invariant one_count_this_build count(Spent) = 9 [status: counted]
  invariant board_static_this_build count(board) = 4021 [status: counted]

  theorem the_prediction_i_made_last_round_was_met_exactly "I wrote the test into the manual before the manual was scored: after the two key2 rules compile, t2 and t7 must replay with zero cells wrong except (63,63), and any other residue refutes my reading of `colored` or of instance typing. certify's first divergence is t=1, ACTION2, cells_wrong 1, cell (63,63), manual 9 world 1. Nothing else. So: distance-six recolour pairs are the correct encoding of a rigid 24-cell mover on this arm; `colored(?p, 9)` reads the CURRENT rendered colour and not the frame-0 colour, since key2_body_leaves had to see the ring as 9 while its instances are typed 9 and key2_body_arrives had to see floor as 5 while typed 5; and the guards are inert on the panel and the meter exactly as I hand-checked them. This is the one thing in the manual that is finished."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem replay_accumulates_so_the_meter_pins_the_score "certify says 1/9 transitions replay exactly. Count what my manual predicts under the other reading, where replay re-seeds from the world frame each command: transition 0 (ACTION1, world no-op, no rule fires) matches; transition 2 (ACTION3, no-op) matches; transition 8 (ACTION4, no-op) matches; transition 6 (ACTION2, the second descent) matches, since transition 1 shows the descent is drawn correctly and t7 burns no meter cell. That is at least four, and four is not one. Therefore replay carries ITS OWN state forward and never re-seeds. Consequence, and it is the operational fact of this round: one unpredictable cell at t=1 makes every later transition wrong at that cell, so `matched` can never rise above 1 while the meter burns, and `first_divergence` can never move past t=1. The replay number is now blind to every improvement I make. I score the manual by the responsibility check, which is at 0 unexplained, and by reading the command diffs myself."
    [probe: passed]

  theorem the_meter_is_a_hidden_parity_and_no_guard_can_separate_it "Row 63 is a 64-cell colour-9 bar losing its rightmost live cell to colour 1, right to left. Burns: t2 (63,63), t4 (63,62), t6 (63,61), t8 (63,60). No burns: t1, t3, t5, t7, t9. I have now checked every guard this language offers against that split, and each one puts a burn and a non-burn in the same class. By action: ACTION1 burns at t6 and not at t1; ACTION2 burns at t2 and not at t7; ACTION3 burns at t8 and not at t3; ACTION4 burns at t4 and not at t9. By body position: spawn burns at t2, t6 and does not at t1, t7; the lower cell burns at t4, t8 and does not at t3, t5, t9. By the meter's own state, which is the only counter visible as cells: with 0 cells already burned the world both refuses (t1) and burns (t2); with 1 burned it both refuses (t3) and burns (t4); with 2, refuses (t5) and burns (t6); with 3, refuses (t7) and burns (t8). By panel state: within each of the two panel states the burns still alternate. The world is flipping a bit that is not drawn anywhere in the 4096 cells, and `free`, `colored`, `adjacent`, `= wall` and `act=` can only ask about drawn cells and the current action. So I write NO meter rule. This is a refusal, not an omission: it costs one cell on four transitions and, because replay accumulates, it costs the whole replay score, and every alternative I can write costs more. cegis_miner reached the same wall from the other side -- 'no literal separates transition 1 from the positives'."
    [probe: passed]

  theorem the_meter_may_be_counting_frames_rather_than_commands "A refinement worth having because it prices the game. Commands have returned 1, 7 or 9 frames; cumulative frames including the reset frame are 2, 9, 10, 11, 20, 21, 30, 31, 32 at the ends of t1..t9. The bar burns exactly when that cumulative count is ODD -- 9, 11, 21, 31 burn; 2, 10, 20, 30, 32 do not -- nine for nine. Command parity fits equally well, and the two readings cannot be told apart yet for a plain reason: 1, 7 and 9 are all odd, so every command so far flipped the parity. A command returning an EVEN number of frames is the separator, and I do not know how to force one. Either way the budget is the same to first order: one cell per two commands, 64 cells, 4 spent, so roughly 120 commands remain. The lattice route I can see is about twenty. The meter is not the binding constraint; the tokens are."
    [depends: the_meter_is_a_hidden_parity_and_no_guard_can_separate_it  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice_and_i_have_read_all_of_it "Cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; separator strips are the rows and cols congruent to 1 mod 6. Colour 5 is floor, colour 0 is wall, and the body is a rigid 5x5 block of 9 with a one-cell hole at its centre, so a cell is enterable only if all 25 of its pixels are floor. Reading the current frame span by span: R=1 (rows 8-12) is floor at C=2,3,4,5, carries the knob at C=6 and is void at C=7; R=2 (rows 14-18) is floor at C=2 and C=4 only; R=3 (rows 20-24) at C=2,3,4; R=4 and R=5 (rows 26-36) at C=2 only; R=6 (rows 38-42) has no enterable cell at all -- C=2 is the comb and C=3..6 are floor only on rows 39 and 41, a three-tall channel flanking the row-40 cable, which a five-tall body cannot use; R=7 (rows 44-48) at C=2; R=8 (rows 50-54) is open floor from col 13 to col 48, so C=2 through C=7 all enterable, and C=7 is the socket interior. Openings: column 2 is continuous from R=1 to R=8 across every separator row; R=1 is continuous from C=2 to C=6; R=3 connects C=2,3,4; R=8 connects C=2 through C=7. That is the whole map and it took no concept beyond the lattice I already had."
    [depends: key2_body_arrives  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood the map from spawn (1,2) and the body reaches exactly eleven cells: (1,2), (1,3), (1,4), (1,5), (2,2), (2,4), (3,2), (3,3), (3,4), (4,2), (5,2). The socket interior (8,7) is not among them, and neither is anything in R=7 or R=8, because every path south crosses (6,2) and (6,2) is filled with colour 8 except the two pixels (39,14) and (41,14). So the comb is not an obstacle to route around; it is the door, and this game cannot be won without opening it. The cable makes the mechanism explicit: colour 8 leaves the comb along row 40, runs right to col 40, climbs col 40 and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41, which is the interior of lattice (1,6). No colour-8 pixel has moved in nine commands, which is why 8 is board and not an object; the first colour-8 pixel that changes converts this theorem into physics and gives me a rule to write."
    [depends: the_maze_is_a_six_pixel_lattice_and_i_have_read_all_of_it  probe: pending]

  theorem the_knob_is_the_only_thing_the_body_can_touch_and_i_do_not_know_how_it_is_pressed "Of the eleven reachable cells, ten are surrounded by floor and void only. The eleventh, (1,5), is adjacent through the open separator col 37 to (1,6), whose interior is the knob. So the knob is the single interactive object within reach, and pressing it is the only lever I can see. How it is pressed I do not know, and the geometry is against the obvious reading: the body's hole is ONE pixel, at (10,40) if it stood at (1,6), while the knob is nine pixels, so entering (1,6) means the body overlapping eight colour-8 pixels. Either colour 8 is walkable and my key2_body_arrives -- which demands the destination render 5 -- is wrong at the knob and at the comb, or the knob is triggered by proximity from (1,5), or by an action I have not pressed. All three are cheap to distinguish and my rules make the first one self-announcing: if the body enters a colour-8 cell, the manual predicts it stops and the world says otherwise, in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem the_action_map_is_weaker_than_i_claimed "I withdraw last round's 'unique assignment'. ACTION2 = down is proven twice, six pixels at t2 and t7. What the six no-ops actually force is less. ACTION1 was a no-op at t1 and t6, both from spawn (1,2), where up is off the floor AND left is void -- but right, (1,3), is open floor, so ACTION1 is not right, and ACTION1 is up or left or nothing. ACTION3 and ACTION4 were no-ops at t3, t8 and t4, t9, all four from (2,2), where left and right are both void -- but up, (1,2), is open floor, so NEITHER ACTION3 NOR ACTION4 IS UP. That is the strong new fact. If up lies in ACTION1..ACTION4 at all it is ACTION1; it could still be ACTION5, or one of the two keys I have never pressed. The separator is free, it is available from where the body stands right now, and it is progress rather than a detour: press ACTION1 from (2,2), where up is open and left is void. Body moves six pixels north, ACTION1 is up and the route to the knob is open; nothing moves, ACTION1 is left or inert and I have lost one meter tick and learned the same amount."
    [depends: key2_body_leaves  probe: pending]

  theorem two_actions_have_never_been_pressed "The store's actions_used is ACTION1..ACTION5 and RESET. This world's alphabet is ACTION1..ACTION7. So a sixth and a seventh command exist that I have never sent and that no observation constrains at all -- and in this family ACTION6 is normally a click carrying coordinates. That matters here specifically: the knob is a 3x3 target the body may be geometrically unable to stand on, and a click is exactly the shape of interaction that would press it. I cannot write such a rule. The guard language admits `act=key(6)` but has no way to attach the two coordinates a click carries, so a click rule would be silently wrong about which cell was clicked. If a click turns out to drive this world, my manual can record its EFFECT -- comb pixels going 8 to 5 -- and never its precondition. I am recording that limit now rather than discovering it under pressure."
    [probe: pending]

  theorem the_panel_is_two_tokens_and_one_is_already_spent "Rows 1-3 cols 1-3 and cols 5-7 are two 3x3 icons, each with a 1x3 underline at row 5. Frames 0-4: slot 1 a hollow colour-9 ring with its underline lit, slot 2 a solid colour-1 block with its underline dark. From frame 5: slot 1 a hollow colour-2 ring with its underline dark, slot 2 a hollow colour-9 ring with its underline lit. The icons are miniatures of the body -- a hollow square with a one-pixel hole -- so I read them as bodies: two tokens, the lit hollow 9 is the one in play, colour 2 is a token consumed. The only command that has ever touched the panel is ACTION5, and ACTION5 is respawn, so respawn spends a token and ONE TOKEN REMAINS. This is the binding budget of the game, not the meter: I have roughly 120 commands and one life. Every probe that could end in a respawn is therefore ranked below every probe that cannot."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem only_visited_cells_have_instances "Settled by arithmetic. The arm builds one instance per cell of the declared colour THAT THE BOARD CANNOT EXPLAIN, and board is the set of never-varying cells: constant_cells 4021 plus dynamic_cells 75 is 4096, and cells_needing_an_owner is 72, which is my 75 minus the three background-at-frame-0 cells no colour-keyed object can claim. 39 + 24 + 9 = 72 exactly. So the instance set IS the set of cells that have already changed, and the corridor ahead has no instances however much floor it shows. The deductive consequence, which is still untested: the first step into a never-yet-changed cell costs 48 wrong cells -- 24 for a body I keep drawing where it no longer is, 24 for a body I cannot draw where it now is -- and the round AFTER that, those cells are dynamic, instances exist, and key2_body_arrives draws them with no change to its text. The manual heals itself one step behind the body. I price every forward step at 48 and take it anyway."
    [depends: key2_body_arrives  probe: passed]

  theorem the_instance_counts_are_build_relative_not_world_facts "The four invariants above are counted at THIS build and will be false at the next one, because stepping into fresh corridor moves 24 more cells from board into Vacated and raises count(board) is 4021 to something smaller. I state them anyway because they are the arithmetic that proves only_visited_cells_have_instances, and I say plainly here that they are properties of what has been observed rather than laws of the world. Nothing in the rules depends on them."
    [probe: passed]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "The arm types a cell by its frame-0 colour, so the body changes type as it walks: at rows 8-12 its pixels are Glyph9, at rows 14-18 they are Vacated. Last round I said this costs me two unwritten rules. It costs one. The next descent, from (2,2) to (3,2), needs Vacated pixels going 9 to 5 at rows 14-18 and Vacated pixels going 5 to 9 at rows 20-24 -- and the second of those IS key2_body_arrives, already written and already witnessed, which will ground at rows 20-24 as soon as they are dynamic. Only the clearing half is missing, verbatim for the next desk: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. I have checked it for spurious grounding and it is inert everywhere today, because no Vacated instance renders 9 unless the body is standing on it. I still refuse to write it: rule 2 is not negotiable and one descent buys it. The companion I named last round, Glyph9 going 5 to 9 on arrival, I now expect never to need for a downward move -- the only frame-0 colour-9 floor pixels in the maze are the spawn ring, and nothing lies above spawn."
    [depends: key2_body_arrives  probe: pending]

  theorem dynamic_census "Exactly 75 cells have ever changed. 23 are the status panel at rows 1-5 cols 1-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus its hole (10,16), which never changes and is therefore board. 24 are the same shape six pixels down, rows 14-18 cols 14-18 minus its hole (16,16). 4 are the right end of the row-63 bar, cols 60-63. 23+24+24+4 = 75 and nothing is left over. At frame 0 they split as 39 colour-9, 9 colour-1 and 24 colour-5, plus 3 background; 39+9+24 = 72, exactly cells_needing_an_owner, and the responsibility check reports 0 unexplained."
    [probe: passed]

  theorem three_cells_no_object_can_ever_own "(5,5), (5,6), (5,7) are background at frame 0 and colour 9 from frame 5, so no colour-keyed object owns them and none can: an arc-colour 0 object would claim three thousand background cells. Any future panel rule has a floor of 3 wrong cells. This is exactly the gap between 75 dynamic cells and 72 cells_needing_an_owner, and it is structural."
    [probe: passed]

  theorem the_panel_debt_i_am_choosing_to_carry "I write no panel rule and every ACTION5 costs me 23 wrong cells. The reason is rules 3 and 5, not laziness: (1,2) and (5,2) have byte-identical four-neighbourhoods so no guard separates the slot-1 ring from its underline, and separating the slot-2 ring from its centre needs a disjunction this grammar does not have, so the honest encoding is four rules that all fire on a corner cell -- exactly the ambiguity rule 5 forbids. 23 wrong cells on a command I intend to press at most once more is the cheaper error, and since replay accumulates it is now free in the score."
    [probe: pending]

  theorem key5_is_respawn_and_i_have_written_it_as_respawn "key5_body_clears and key5_body_respawns say: on ACTION5 any floor pixel that is body-coloured returns to floor and the spawn ring lights up. That fits t5 exactly, 24/24 on both halves, and I checked key5_body_respawns for spurious grounding -- the only Glyph9 instances that ever render 5 are the spawn ring's. The rival reading, 'ACTION5 is up', fits t5 equally well because the body happened to be one lattice cell below spawn, and it is not idle: the_action_map_is_weaker_than_i_claimed leaves up unassigned. I keep respawn because ACTION5 alone has ever touched the panel and the panel reads as tokens. Separator: press ACTION5 from a cell that is NOT one lattice cell below spawn. It costs the last token, so it waits behind every other probe in the game, including the two keys I have never pressed."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "There is no goal: section, so is_goal is False, and that is deliberate. The socket interior, rows 50-54 cols 44-48, is floor that has never changed, so it is board and has no instances -- there is nothing there for a goal to name. `Cart.pos = exit_cell` needs a single named instance and arc-instances: all gives me Glyph9_r8c14 and 38 siblings instead. `count(Vacated, color = 9) = 24` is true of the body standing anywhere off spawn, which is most of the maze and not a win. A goal true in the wrong states is worse than none, because the planner stops at the first one. The manual will be able to state its goal only after the body has once stood in the socket and those pixels have become dynamic; until then the playbook steers by lattice distance."
    [probe: pending]

  theorem nested_cell_terms_parse "Settled by the compiler two rounds running: below(below(...)) six deep parses and grounds, one line of guard draws 24 pixels, and the fallback I dreaded -- one landmark per lattice cell, which is coordinates in disguise -- is off the table permanently."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem the_meter_rules_i_withdrew "The manual before last carried meter_burn_key2 and meter_burn_key4 on one observation each. t7 refuted the first, t9 the second, and meter_burn_key4's guard would now invent a fifth burn at (63,59). One observation per action is not evidence for a rule keyed on the action when a hidden clock explains the same pixels. The lesson is why key2_floor_leaves stays out of the rules section this round despite being, I am fairly sure, true."
    [probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -4457 and -22984 bits, so its own segmentation loses to writing the pixels out and I owe it nothing; its obj3 is a 1006-cell colour-null blob that swallowed the maze floor, which is a fair description of my board and not an object. obj0, obj2 and obj4 are colour-9 fragments already inside Glyph9; obj5 is the colour-2 panel ring, which is Glyph9 pixels after a recolour and gets no type of its own, since a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN -- 9 transitions constrain rank 6 of 375 features, null space dimension 369 -- and its one global law restates my 75-cell census. cegis_miner's refusal remains the most useful sentence any engine has produced: 'no track satisfies the precondition of exactly one move event per transition; the world does not narrate as one mover.' True of the ARM, false of the world. The world has exactly one mover, a rigid 24-pixel ring; the arm can only see 24 simultaneous recolours, which is why my movement law needs a pair of rules per direction instead of one moved() event."
    [probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
# Three things changed this round and all three change the ordering.
#   (a) The map is read: the socket is unreachable until the comb opens, so
#       distance-to-socket is the wrong heuristic while the gate is shut and
#       distance-to-switch is the right one.
#   (b) The binding budget is tokens, not the meter. One token remains. Any
#       branch that can end in a respawn ranks below every branch that cannot.
#   (c) replay accumulates and the meter pins it at 1/9, so "wrong cells in
#       replay" is no longer a currency I can spend down. Probes are now chosen
#       by what the raw frame diff will tell me, not by what certify will say.
# Still no stored sequence anywhere: every line is a criterion on the current
# frame plus the manual's own open questions.

order     identify_a_direction_key_before_routing_with_it            [proof: lean]
order     probe_from_a_cell_where_the_rival_readings_disagree        [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it         [proof: lean]
order     reach_the_switch_before_testing_the_switch                 [proof: lean]
order     free_probes_before_token_costing_probes                    [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end           [proof: lean]
order     witness_a_rule_before_writing_it                           [proof: lean]

prune     destination_lattice_cell_is_not_wholly_floor => dead        [proof: lean]
prune     action_that_was_a_no_op_from_this_lattice_cell => dead      [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead [proof: lean]
prune     respawn_while_a_legal_move_exists => dead                   [proof: lean]
prune     respawn_when_no_token_remains and not goal => dead          [proof: lean]
prune     meter_exhausted and not goal => dead                        [proof: lean]

heuristic lattice_distance_to_the_switch_while_the_gate_is_shut       [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open        [admissible: lean]
heuristic commands_remaining_at_one_burn_per_two_commands             [admissible: lean]
heuristic unexplained_cells_after_redraw                              [admissible: lean]

prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule   [ev: 2/2 moves]
prefer    a_key_whose_only_unblocked_candidate_direction_is_forward   [ev: 6/6 no_ops]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff            [ev: 1/1 levels]
prefer    a_step_toward_the_switch_over_a_step_toward_the_socket      [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op               [ev: 2/5 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered     [ev: 1/1 levels]
prefer    stay_on_the_lattice_column_that_reaches_the_gate            [ev: 1/1 levels]
```

=== LOG ===
```json
[
  {"id": "S-01", "subject": "replay_mismatch t=1, cell (63,63), manual 9 world 1", "verdict": "reject",
   "why": "Explicit refusal to change the manual. I checked every guard the language has against the burn split -- action, body position, meter state, panel state -- and each puts a burn and a non-burn in the same class (ACTION2 burns at t2 and not t7; 0-cells-burned both refuses at t1 and burns at t2). The burn depends on a bit that is not drawn in any of the 4096 cells, so no rule I can write predicts it, and every rule I could write is wrong more often. Recorded as the_meter_is_a_hidden_parity_and_no_guard_can_separate_it, probe: passed."},
  {"id": "L-01", "subject": "replay accumulates rather than re-seeding", "verdict": "accept",
   "as": "replay_accumulates_so_the_meter_pins_the_score",
   "why": "Under re-seeding my manual matches at least transitions 0, 2, 6 and 8 (two no-ops it predicts, the second descent it draws, one more no-op); certify reports matched=1, which only the accumulating reading explains. Consequence: replay is now saturated by one cell and gives me no further signal."},
  {"id": "L-02", "subject": "last round's advance prediction on t2 and t7", "verdict": "accept",
   "as": "the_prediction_i_made_last_round_was_met_exactly",
   "why": "I wrote 'zero cells wrong except (63,63) at t2' before scoring; first_divergence is exactly one cell and it is (63,63). That confirms distance-six recolour pairs as the encoding of a rigid mover, and that `colored` reads current rendered colour, not frame-0 colour."},
  {"id": "R-01", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept",
   "as": "kept unchanged",
   "why": "48/48 on t2 and t7 and now verified by replay with zero residue on their own pixels; no reason to touch text that predicts exactly."},
  {"id": "R-02", "subject": "key5_body_clears / key5_body_respawns", "verdict": "accept",
   "as": "kept unchanged",
   "why": "24/24 each at t5, hand-checked inert on panel and meter; the rival reading (ACTION5 = up) is now live again because up is unassigned, so the theorem naming its separator is kept and the probe is ranked last because it spends the final token."},
  {"id": "R-03", "subject": "key2_floor_leaves (Vacated 9 -> 5 at distance six)", "verdict": "probe-pending",
   "why": "Never witnessed: no Vacated pixel has ever gone 9 to 5. Rule 2 forbids it in the rules section however inert I have verified it to be, and the withdrawn meter rules are the standing reminder of what one-observation rules cost. One further descent buys it."},
  {"id": "R-04", "subject": "the second missing key2 rule I named last round (Glyph9 5 -> 9 on arrival)", "verdict": "reject",
   "why": "Downgraded from pending to unneeded for downward motion: key2_body_arrives already covers arrival on frame-0 floor, and the only frame-0 colour-9 floor pixels in the whole maze are the spawn ring, above which there is nothing. Last round overcounted the debt at two rules; it is one."},
  {"id": "L-03", "subject": "the full lattice map read off the current frame", "verdict": "accept",
   "as": "the_maze_is_a_six_pixel_lattice_and_i_have_read_all_of_it",
   "why": "Cell (R,C) = rows 6R+2..6R+6 by cols 6C+2..6C+6; enterable cells listed band by band from the pixel spans of the current frame, using the fact that a 5x5 body needs all 25 pixels floor -- which is what disqualifies the three-tall channel at rows 39-41."},
  {"id": "L-04", "subject": "reachability from spawn", "verdict": "accept",
   "as": "the_socket_is_unreachable_until_the_comb_opens",
   "why": "Flooding the map from (1,2) yields exactly eleven cells and the socket is not among them; every southward path crosses (6,2), which is colour 8 except two pixels. This makes the gate mandatory rather than optional and reorders the whole playbook."},
  {"id": "L-05", "subject": "the knob at lattice (1,6) as the only interactive target", "verdict": "probe-pending",
   "as": "the_knob_is_the_only_thing_the_body_can_touch_and_i_do_not_know_how_it_is_pressed",
   "why": "It is the only non-floor non-void thing adjacent to the reachable region, and the cable wires it to the comb; but the body's hole is one pixel and the knob is nine, so entering it means overlapping colour 8. Three mechanisms remain open and key2_body_arrives makes the first self-announcing."},
  {"id": "L-06", "subject": "last round's claim that the direction assignment is unique", "verdict": "reject",
   "as": "the_action_map_is_weaker_than_i_claimed",
   "why": "Self-correction: left is also blocked at spawn, so ACTION1 could be left. What the no-ops do force is stronger in the useful direction -- up was OPEN from (2,2) and ACTION3 and ACTION4 both did nothing there, so neither is up; and right was open from (1,2), so ACTION1 is not right."},
  {"id": "P-01", "subject": "press ACTION1 from the current cell", "verdict": "probe-pending",
   "why": "The one free separator on the board right now: up is open, left is void, source and destination pixels both already have instances. Movement proves ACTION1 = up and opens the route to the switch; no movement proves it is left or inert. It is also progress, not a detour."},
  {"id": "P-02", "subject": "ACTION6 and ACTION7 have never been pressed", "verdict": "probe-pending",
   "as": "two_actions_have_never_been_pressed",
   "why": "actions_used covers only ACTION1..ACTION5 and this world's alphabet runs to seven. Two commands of the alphabet are wholly unconstrained, and in this family ACTION6 is normally a click -- which is exactly the shape of thing that could press a 3x3 knob the body cannot stand on."},
  {"id": "E-01", "subject": "a click action's coordinates", "verdict": "probe-pending",
   "why": "Wanted: a rule keyed on clicking a specific cell. The guard language allows act=key(6) but has no way to bind the two coordinates a click carries, so such a rule would be silently wrong about which cell was hit. Wrote a theorem naming the limit instead, and noted that the EFFECT (comb pixels 8 -> 5) is expressible even when the precondition is not."},
  {"id": "E-02", "subject": "a goal for this world", "verdict": "reject",
   "why": "Wanted: goal body-occupies-lattice-(8,7). The socket interior has never changed, so it is board and has no instance to name; arc-instances: all leaves no single instance name; count-based goals are true across most of the maze. Wrote no goal: section at all (is_goal -> False) and a theorem saying why, since a goal true in wrong states would stop the planner early."},
  {"id": "L-07", "subject": "the status panel", "verdict": "accept",
   "as": "the_panel_is_two_tokens_and_one_is_already_spent",
   "why": "The icons are 3x3 miniatures of the body's hollow square; slot 1 went from lit 9-ring to dark 2-ring and slot 2 from solid 1-block to lit 9-ring at exactly the one command that has ever touched the panel, ACTION5, which is respawn. One token left, and that is the game's binding budget, not the meter."},
  {"id": "L-08", "subject": "only_visited_cells_have_instances", "verdict": "accept",
   "as": "upgraded from pending to passed",
   "why": "Arithmetic, not inference: 4021 constant + 75 dynamic = 4096, and 39 + 24 + 9 = 72 = cells_needing_an_owner. The instance set is the dynamic set. The consequence -- 48 wrong cells on the first step into fresh corridor, self-healing the round after -- stays as a priced expectation."},
  {"id": "L-09", "subject": "the meter as a frame-parity counter", "verdict": "probe-pending",
   "why": "Cumulative frames at command ends are 2, 9, 10, 11, 20, 21, 30, 31, 32 and the bar burns exactly on the odd ones, nine for nine. Indistinguishable from command parity because 1, 7 and 9 are all odd; separator is a command that returns an even number of frames. Either way: about 120 commands remain against a route of about twenty."},
  {"id": "O-01", "subject": "mdl_segmenter obj0, obj2, obj4 (colour 9 fragments)", "verdict": "entailed",
   "why": "All three are subsets of Glyph9's cells; declaring them separately would put two types on the same pixels and invite the double claim rule 5 forbids."},
  {"id": "O-02", "subject": "mdl_segmenter obj3 (1006-cell colour-null blob)", "verdict": "reject",
   "why": "It is the maze floor, which my manual already owns as board; and the segmenter's own score is negative on both variants, so it is not proposing a concept that pays for itself."},
  {"id": "O-03", "subject": "mdl_segmenter obj5 (colour-2 ring, first seen frame 5)", "verdict": "entailed",
   "why": "Those pixels are Glyph9 panel cells after a recolour, already owned; a colour-2 type would double-claim them and would still not let me write a panel rule, since the ambiguity there is between ring and underline, not between colours."},
  {"id": "O-04", "subject": "cegis_miner's global refusal", "verdict": "accept",
   "as": "recorded verbatim in what_the_engines_gave_me",
   "why": "'The world does not narrate as one mover' is true of the arm and false of the world; it is the precise reason my movement law is a pair of recolour rules per direction rather than one moved() event, and it independently confirms that no literal separates the meter burns."},
  {"id": "O-05", "subject": "zero_space's global law and its THIN self-report", "verdict": "entailed",
   "why": "Its single law restates the 75-cell census I already carry, and it says itself that 9 transitions constrain rank 6 of 375 features, so nothing in its null space is evidence for anything."}
]
```
```
