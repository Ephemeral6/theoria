# call-001-theorize-round1

model: `claude-opus-5` · 587049 ms · $1.487855 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 28599, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 28599, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 28599, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 28599, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 47235, "type": "message"}], "output_tokens": 47235, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 70,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4023,
 "distinct_states": 4,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 73,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 6,
 "steps": 6
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
9999999999999999999999999999999999999999999999999999999999999911
```

## Every command, and what changed

`t` indexes the state sequence. `frames` is how many grids one command returned -- more than one means the world took several internal steps for a single action.

- t0   RESET     frames=1   state=NOT_FINISHED (first frame)
- t1   ACTION1   frames=1   state=NOT_FINISHED no cells changed
- t2   ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-63, [5, 9] -> [1, 5, 9]
- t3   ACTION3   frames=1   state=NOT_FINISHED no cells changed
- t4   ACTION4   frames=1   state=NOT_FINISHED (63,62) 9->1
- t5   ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 5,
  "n_states": 6,
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
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj0",
    "transitions": 5
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
    "transitions": 5
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
   "recolor": 4,
   "vanish": 1
  },
  "n_frames": 6,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 6,
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
    "frames_present": 6,
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
    "frames_present": 6,
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
    "frames_present": 6,
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
    "frames_present": 1,
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
    "baseline_bits": 1976,
    "compression_ratio": 3.551619,
    "events": 8,
    "gain_bits": -5042,
    "ms": 12,
    "script_bits": 7018,
    "split_by_color": false,
    "tracks": 6
   },
   {
    "baseline_bits": 1976,
    "compression_ratio": 9.866397,
    "events": 19,
    "gain_bits": -17520,
    "ms": 19,
    "script_bits": 19496,
    "split_by_color": true,
    "tracks": 17
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 73,
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
  "cells_needing_an_owner": 70,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4023,
  "distinct_states": 4,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 73,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 6,
  "steps": 6
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 73,
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
  "cells_dynamic": 73,
  "cells_used": 73,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 3,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.008219,
   "difference_rank": 3,
   "features": 365,
   "space_dimension": 362,
   "transitions": 5,
   "verdict": "THIN: 5 transitions constrain rank 3 of 365 features, so the null space has dimension 362 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 365,
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
     "c2@38",
     "c5@38",
     "c9@38",
     "c0@39",
     "c1@39",
     "c2@39",
     "c5@39",
     "c9@39",
     "c0@40",
   
```

The full proposal stream is 368 rows in `candidates.jsonl`.

## The manual as it stands

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
  landmark spawn_center  # arc-cell: carried, coordinates stripped
  landmark socket_center  # arc-cell: carried, coordinates stripped
  landmark gate_center  # arc-cell: carried, coordinates stripped
  landmark knob_center  # arc-cell: carried, coordinates stripped
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

## The playbook as it stands

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
  "detail": "1/5 transitions replay exactly",
  "matched": 1,
  "ok": false,
  "transitions": 5
 },
 "responsibility": {
  "cells_unexplained": 0,
  "detail": "every pixel of frame 0 belongs to the board or to an object",
  "ok": true,
  "total_cells": 4096
 },
 "unambiguous": {
  "actions": 2,
  "cap_reached": false,
  "clashes": [],
  "detail": "no (state, action) among 6 x 2 admitted two rules, and all 12 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 12,
  "pairs_nominal": 12,
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
=== THEORY ===
```
# theory.dsl -- world re-observed for 6 states / 5 transitions (RESET +
# ACTION1..ACTION5). 73 cells have ever changed; this manual names all 73 and
# owns the 70 that any colour-keyed object can own.
#
# WHAT CHANGED THIS ROUND, AND IT IS MOSTLY THE INSTRUMENT, NOT THE WORLD:
#
#   1. THE OBSERVATION WINDOW SHRANK. The manual I inherited was written from
#      10 states (t0..t9). The store now reports states=6, steps=6,
#      dynamic_cells=73, cells_needing_an_owner=70. Those are exactly the
#      first six states of the same run: same spawn, same descent at t2, same
#      respawn at t5, and the meter bar has lost two cells instead of four. So
#      four transitions I once observed are no longer in the window and cannot
#      be re-checked by certify. Every count in this manual is re-derived from
#      the six frames I can see; every claim that rests on a transition I can
#      no longer see is labelled as such, in the theorem that uses it.
#      See the_window_shrank_and_two_of_my_theorems_now_rest_on_memory.
#
#   2. THE SURPRISE IS THE ONE CELL I DECLARED UNPREDICTABLE. replay diverges
#      at t=1, ACTION2, cells_wrong = 1, cell (63,63), manual 9 world 1. That
#      is the meter, and it is the only divergence: the 48 body pixels of the
#      descent are drawn right. The manual's physics is intact.
#
#   3. AND THE SHRUNK WINDOW HANDS ME A CHEAP LIE. In these five transitions
#      each action appears exactly once, so "the bar burns iff the action is
#      ACTION2 or ACTION4" fits 5/5, is writable in this grammar, and would
#      lift replay from 1/5 to 4/5. I refuse it, I show the arithmetic of what
#      I am refusing, and I convert the refusal into a scheduled test that the
#      very next command settles. See
#      the_meter_is_a_hidden_parity_and_the_short_window_tempts_me_to_lie.
#
#   4. I READ THE SOCKET AND IT IS A KEYHOLE. Rows 49-55, cols 43-49 are a 7x7
#      colour-9 bracket, open on the left, with ONE colour-9 pip at (52,46).
#      The body is a 5x5 ring with a one-pixel hole at its centre. Stand the
#      body in lattice (8,7) -- rows 50-54, cols 44-48 -- and its hole lands
#      exactly on (52,46). The pip is what shows through the hole. That is the
#      winning position, named to the pixel, and it is still not writable as a
#      `goal:` for reasons I give in the_goal_section_is_absent_on_purpose.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark spawn_center   # arc-cell: (10, 16)
  landmark knob_center    # arc-cell: (10, 40)
  landmark gate_center    # arc-cell: (40, 16)
  landmark socket_center  # arc-cell: (52, 46)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t5 compress: 37]
  Vacated [segment: dynamic_colour_5 ev: t2,t5 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t5 compress: 9]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

laws:
  invariant nine_count_this_build count(Glyph9) = 37 [status: counted]
  invariant five_count_this_build count(Vacated) = 24 [status: counted]
  invariant one_count_this_build count(Spent) = 9 [status: counted]
  invariant board_static_this_build count(board) = 4023 [status: counted]

  theorem the_descent_replays_to_the_pixel_and_that_is_the_whole_physics_bill "certify's first divergence is t=1, ACTION2, cells_wrong 1, cell (63,63), manual 9 world 1. Nothing else. The descent moves 49 cells and 48 of them are the body; all 48 are drawn correctly by two rules whose whole content is a distance-six recolour pair. So: a rigid 24-pixel mover on this arm is correctly encoded as source-cells-recolour-to-floor plus destination-cells-recolour-to-body, `colored(?p, 9)` reads the CURRENTLY RENDERED colour and not the frame-0 colour that typed the instance, and both guards are inert on the panel, on the meter and on every floor cell the body is not standing on -- I re-checked each class by hand against this frame. This part of the manual is finished and I changed not one character of it."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem the_window_shrank_and_two_of_my_theorems_now_rest_on_memory "The store reports 6 states where the manual I inherited worked from 10, and the six are the same six: RESET, a no-op, the descent, two no-ops, the respawn. Consequences I must state plainly. (a) Every count is re-derived here from the six visible frames: 23 panel cells + 24 spawn-ring cells + 24 lower-ring cells + 2 meter cells = 73 = dynamic_cells, and 73 - 3 background-at-frame-0 cells = 70 = cells_needing_an_owner. (b) The key2 pair is now witnessed by ONE descent, not two, so its coverage tags read 24/24 at t2 and not 48/48; the rule text did not need to change, which is itself the evidence that the second descent was not carrying it. (c) Two things I believe are now UNCHECKABLE by certify because the transitions that witness them are outside the window: that ACTION1 burned the meter at the old t6 and ACTION3 burned it at the old t8, and that ACTION2 at the old t7 and ACTION4 at the old t9 did NOT burn. I carry those as recorded observation, not as anything this round can re-derive, and I name exactly where they are load-bearing rather than letting them hide."
    [probe: passed]

  theorem replay_accumulates_and_the_count_now_proves_it_one_against_two "certify says 1/5. Count what my manual predicts under the rival reading, where replay re-seeds from the world frame before each command: t1 is a world no-op and no rule of mine fires, so it matches; t3 is a world no-op and no rule fires, so it matches; t2, t4 and t5 all miss (meter, meter, panel). That is 2, and 2 is not 1. Under accumulation: t1 matches, t2 diverges at (63,63), and from then on my carried state differs from the world's at that cell forever, so t3, t4, t5 all miss whatever else I get right. That is exactly 1. So replay carries its own state forward and never re-seeds -- last round the same argument gave 4-against-1 on nine transitions and this round it gives 2-against-1 on five, from an independent count. Operationally: while the meter burns unpredicted, `matched` cannot exceed 1 and `first_divergence` cannot move past t=1, no matter how much of the manual is right. I score myself on the responsibility check (0 unexplained) and on reading the command diffs by hand."
    [probe: passed]

  theorem the_meter_is_a_hidden_parity_and_the_short_window_tempts_me_to_lie "Row 63 is a 64-cell colour-9 bar losing its rightmost live cell to colour 1, right to left. In this window: burn at t2 (63,63), burn at t4 (63,62), no burn at t1, t3, t5. HERE IS THE TEMPTATION, priced honestly. In five transitions each of ACTION1..ACTION5 occurs exactly once, so 'burns iff act is key(2) or key(4)' fits 5/5, and it is writable: `when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)` picks (63,63) and only it, and `when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)` picks (63,62) and only it, neither clashing with key2_body_leaves because that rule's below-six guard is off-board at row 63. Writing them takes replay from 1/5 to 4/5, since t5 would still lose 23 panel cells. I REFUSE, for two reasons and I want both on the record. First, one observation per action is not evidence for a law keyed on the action when a one-parameter clock explains the same pixels: cumulative frames returned, counting the reset frame, are 2, 9, 10, 11, 20 at the ends of t1..t5, and the bar burns exactly on the odd ones -- 9 and 11 burn, 2, 10 and 20 do not, 5 for 5, with no free parameter. Second, my own manual records a longer window in which ACTION2 did not burn and ACTION1 did, which kills action-keying outright; that record is now unverifiable here, which is precisely why I refuse to let a 4/5 score buy me a rule I have written down as refuted. And no drawn cell can carry the clock: the count of already-burned cells is 0 at t1 (no burn) and 0 at t2 (burn), 1 at t3 (no burn) and 1 at t4 (burn), so the meter's own visible state does not separate its own behaviour. cegis_miner hit the same wall from the other side -- 'no literal separates transition 1 from the positives'."
    [probe: passed]

  theorem the_next_command_settles_the_meter_and_i_am_writing_the_prediction_down_first "Cumulative frames now stand at 20, which is even, and every command this world has ever returned has had an odd frame count -- 1, 7 or 9. So the next command, whatever it is, lands on an odd cumulative count and BOTH parity readings (frames-odd, or command-index-even, which agree on t6) predict the bar burns its next cell, (63,61), 9 to 1. Action-keying predicts a burn only if that command is ACTION2 or ACTION4. Therefore ANY command other than those two is a free, decisive separator, and the cost is one meter tick out of the roughly 62 the bar still holds. If the next non-key-2, non-key-4 command burns (63,61), action-keying is dead and my refusal above was right. If it does NOT burn, the parity reading is dead, my recorded memory of the longer window is wrong, and the very next desk must write the two burn rules quoted above verbatim. That is what makes the refusal a test rather than an omission."
    [depends: the_meter_is_a_hidden_parity_and_the_short_window_tempts_me_to_lie  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice_and_i_re_read_every_span_this_round "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; the separator strips are the rows and cols congruent to 1 mod 6. Colour 5 is floor, colour 0 is void, colour 8 is the machine, and the body is a rigid 5x5 block of colour 9 with a one-cell floor hole at its centre, so a cell is enterable only if all 25 of its pixels render floor. Re-read from the current frame, span by span: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are enterable, C=6 holds the knob and C=7 is void; R=2 (rows 14-18) is floor only at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4; R=4 and R=5 (rows 26-36) are floor only at cols 13-19, so C=2; R=6 (rows 38-42) is the comb, and its only floor pixels are (39,14) and (41,14), so nothing is enterable there; R=7 (rows 44-48) is floor cols 13-19, so C=2; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2 through C=7 including the socket interior. Separator rows 7, 13, 19, 25, 31, 37, 43, 49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb and row R=1 is continuous from C=2 to C=6. That is the whole map, and it costs no concept beyond the lattice."
    [depends: key2_body_arrives  probe: pending]

  theorem the_socket_is_a_keyhole_and_the_pip_names_the_winning_position "New this round, and it is the best-paying pixel-reading I have done. Rows 49-55, cols 43-49 form a 7x7 colour-9 bracket: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 49-55, and the left side col 43 rows 50-54 is FLOOR, i.e. the bracket is open on the left. Inside it, one lone colour-9 pixel at (52,46) and nothing else. Now overlay the body: it is 5x5 with its hole at its own centre, and lattice (8,7) is rows 50-54 cols 44-48, whose centre is exactly (52,46). So a body standing in (8,7) has the bracket flush against it on three sides and the pip showing through its hole. This is a socket and a plug, drawn to the pixel, and it tells me the winning position without my having to guess a goal predicate: the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in six frames, so it is board today and no object of mine owns it; the first time the body enters, those pixels become dynamic and the manual can finally speak about them."
    [depends: the_maze_is_a_six_pixel_lattice_and_i_re_read_every_span_this_round  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood the map from spawn (1,2) and the body reaches exactly eleven cells: (1,2), (1,3), (1,4), (1,5), (2,2), (2,4), (3,2), (3,3), (3,4), (4,2), (5,2). The socket interior (8,7) is not among them, and neither is anything in R=7 or R=8, because every route south crosses (6,2) and (6,2) renders colour 8 on 23 of its 25 pixels. So the comb is not an obstacle to route around; it is the door, and this game cannot be won without opening it. The wiring is drawn in the open: colour 8 leaves the comb along row 40, runs right from col 14 to col 40, climbs col 40 through rows 13 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41, which sits inside lattice (1,6). Not one colour-8 pixel has moved in six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule to write."
    [depends: the_maze_is_a_six_pixel_lattice_and_i_re_read_every_span_this_round  probe: pending]

  theorem the_knob_is_the_only_thing_the_body_can_touch_and_i_do_not_know_how_it_is_pressed "Of the eleven reachable cells, ten are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from (1,6) only by separator col 37, which is floor. So the knob is the single interactive object within reach and pressing it is the only lever I can see. The geometry argues against the obvious reading: (1,6) contains ten colour-8 pixels -- nine knob and one cable at (12,40) -- while the body's hole is one pixel, so entering it would mean the body overlapping colour 8. Either 8 is walkable and key2_body_arrives, which demands the destination render 5, is wrong at the knob and at the comb; or the knob answers to proximity from (1,5); or it answers to an action I have never pressed. All three are cheap to tell apart and my rules make the first self-announcing: if the body enters a colour-8 cell, my manual predicts it stays put and the world will say otherwise, in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem the_action_map_after_five_transitions "Proven: ACTION2 is down, 24 pixels leaving rows 8-12 and 24 arriving at rows 14-18 at t2. Everything else is negative information and I will not overstate it. ACTION1 was a no-op at t1 from spawn (1,2), where up is void and left is void but RIGHT, (1,3), is open floor and DOWN, (2,2), is open floor -- so ACTION1 is neither right nor down, leaving up, left, or inert. ACTION3 and ACTION4 were no-ops at t3 and t4 from (2,2), where left and right are both void but UP, (1,2), was open floor at the time and DOWN, (3,2), is open floor -- so NEITHER ACTION3 NOR ACTION4 IS UP OR DOWN, leaving left, right, or inert. That last fact is what makes the cheapest probe in the game available from where the body stands right now: at spawn, up and left are void, down is excluded for ACTION3 and ACTION4 by the paragraph above, so RIGHT IS THE ONLY CANDIDATE DIRECTION EITHER OF THEM COULD EXPRESS. Press one at spawn and the outcome is unambiguous -- a six-pixel step east identifies the key that walks the body along R=1 toward the knob, and no movement retires that key to left-or-inert. The same command doubles as the meter separator of the previous theorem. ACTION5 is respawn and up remains unassigned among ACTION1, ACTION6, ACTION7."
    [depends: key2_body_leaves  probe: pending]

  theorem what_i_predict_for_that_probe_before_i_see_it "Written in advance so it can cost me. If the next command is ACTION3 or ACTION4 from spawn and it does NOT move the body, my manual predicts the frame is unchanged and the world will change one cell, (63,61), and replay will disagree with me on that one cell and no other. If it DOES move the body east, my manual has no right-hand rule and cols 20-24 have never been dynamic so they carry no instances: I predict 48 wrong cells, 24 at rows 8-12 cols 14-18 where I keep drawing a body that has left and 24 at rows 8-12 cols 20-24 where I cannot draw the body that arrived, plus the meter cell. Anything OTHER than 1 or 49 wrong cells refutes something I currently believe -- most likely my reading of the lattice or of which cells the arm has instanced -- and I would rather learn that from a counted diff than from a vague sense that the manual is drifting."
    [depends: the_action_map_after_five_transitions, only_visited_cells_have_instances  probe: pending]

  theorem two_actions_have_never_been_pressed "The store's actions_used is ACTION1..ACTION5 and RESET; this world's alphabet is ACTION1..ACTION7. So two commands exist that no observation constrains at all, and in this family one of them is normally a click carrying coordinates. That matters here specifically: the knob is a 3x3 target the body may be geometrically unable to stand on, and a click is exactly the shape of interaction that would press it. I cannot write such a rule. The guard language admits `act=key(6)` but has nowhere to put the two coordinates a click carries, so a click rule would be silently wrong about WHICH cell was clicked and would fire on every click anywhere. If a click drives this world, my manual can record its EFFECT -- comb pixels going 8 to 5 -- and never its precondition. I record the limit now rather than discovering it under pressure."
    [probe: pending]

  theorem the_panel_is_two_tokens_and_one_is_already_spent "Rows 1-3 cols 1-3 and rows 1-3 cols 5-7 are two 3x3 icons, each with a 1x3 underline at row 5. Frames 0 through 4: slot 1 is a hollow colour-9 ring with its underline lit colour 9, slot 2 is a solid colour-1 block with its underline dark. From frame 5: slot 1 is a hollow colour-2 ring with its underline dark, slot 2 is a hollow colour-9 ring with its underline lit. The icons are miniatures of the body -- a hollow square with a one-pixel hole -- so I read them as bodies: two tokens, the lit hollow 9 is the one in play, and colour 2 marks a token consumed. The only command that has ever touched the panel is ACTION5, and ACTION5 is respawn, so respawn spends a token and ONE TOKEN REMAINS. This, not the meter, is the binding budget: roughly 120 commands and one life. Every branch that can end in a respawn ranks below every branch that cannot."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem only_visited_cells_have_instances "Settled by arithmetic, and the shrunk window re-confirms it with different numbers, which is the strongest form of the check. The arm builds one instance per cell of the declared colour THAT THE BOARD CANNOT EXPLAIN, and board is the set of never-varying cells: constant_cells 4023 plus dynamic_cells 73 is 4096, and cells_needing_an_owner is 70, which is my 73 minus the three cells that render background at frame 0 and which no colour-keyed object can claim. 37 + 24 + 9 = 70 exactly. Last round the same identity held at 4021, 75, 72 and 39 + 24 + 9. So the instance set IS the set of cells that have already changed, and the corridor ahead carries no instances however much floor it shows. The consequence I have now priced twice: the first step into never-yet-changed ground costs 48 wrong cells, and the round after, those cells are dynamic, instances exist, and key2_body_arrives draws them with no change to its text. The manual heals itself one step behind the body, and I take the step anyway."
    [depends: key2_body_arrives  probe: passed]

  theorem the_instance_counts_are_build_relative_not_world_facts "The four invariants above are counted at THIS build and were different at the last one -- 39, 24, 9, 4021 then, 37, 24, 9, 4023 now, and the only thing that moved was two meter cells falling out of the observation window. They will change again the moment the body steps onto fresh floor. I state them because they are the arithmetic that proves only_visited_cells_have_instances, and I say here plainly that they are properties of what has been observed rather than laws of the world. No rule depends on them."
    [probe: passed]

  theorem dynamic_census "Exactly 73 cells have ever changed. 23 are the status panel: slot 1's eight ring pixels going 9 to 2, its three underline pixels going 9 to 0, slot 2's nine block pixels of which eight go 1 to 9 and the centre (2,6) goes 1 to 0, and its three underline pixels going 0 to 9. 24 are the spawn ring, rows 8-12 cols 14-18 minus the hole (10,16), which never changes and is therefore board. 24 are the same shape six rows down, rows 14-18 cols 14-18 minus its hole (16,16). 2 are the right end of the row-63 bar, (63,62) and (63,63). 23+24+24+2 = 73 and nothing is left over. zero_space independently lists 73 cells_used and its cell list ends with exactly those two meter cells. At frame 0 they split as 37 colour-9, 9 colour-1, 24 colour-5 and 3 background; 37+9+24 = 70 = cells_needing_an_owner, and the responsibility check reports 0 unexplained."
    [probe: passed]

  theorem three_cells_no_object_can_ever_own "(5,5), (5,6), (5,7) render background at frame 0 and colour 9 from frame 5, so no colour-keyed object owns them and none can: an arc-colour 0 object would claim three thousand background cells. Any future panel rule therefore has a floor of 3 wrong cells. This is exactly the gap between 73 dynamic cells and 70 cells_needing_an_owner, and it is structural, not an oversight."
    [probe: passed]

  theorem the_panel_debt_i_am_choosing_to_carry "I write no panel rule and every ACTION5 costs me 23 wrong cells. The reason is rules 3 and 5, not laziness: (1,2) and (5,2) have byte-identical four-neighbourhoods, so no guard in this language separates slot 1's ring from its underline, and separating slot 2's ring from its dark centre needs a disjunction the grammar does not have. The honest encoding would be four rules that all fire on the same corner cell -- exactly the ambiguity rule 5 forbids. 23 wrong cells on a command I intend to press at most once more is the cheaper error, and since replay accumulates it is currently free in the score."
    [probe: pending]

  theorem key5_is_respawn_and_i_have_written_it_as_respawn "key5_body_clears and key5_body_respawns say: on ACTION5 every floor pixel rendering body-colour returns to floor and the spawn ring lights up. That fits t5 exactly, 24/24 on each half, and I re-checked key5_body_respawns for spurious grounding against this frame -- the meter Glyph9 cells render 9 or 1 and never 5, and the panel Glyph9 cells rendered 9 before t5 and render 2 or 0 after, so neither can satisfy colored(?p, 5). The rival reading, 'ACTION5 is up', fits t5 equally well because the body happened to be exactly one lattice cell below spawn, and it is not idle since up is still unassigned. I keep respawn because ACTION5 alone has ever touched the panel and the panel reads as tokens. Separator: press ACTION5 from a cell that is NOT one lattice cell below spawn. It costs the last token, so it waits behind every other probe in the game, including the two keys never pressed."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "There is no goal: section, so is_goal is False, and that is deliberate even though I can now name the winning position to the pixel. `Cart.pos = exit_cell` needs one named instance, and arc-instances: all gives me Glyph9_r8c14 and 36 siblings instead of a Cart. The socket interior, rows 50-54 cols 44-48, has never changed, so it is board, has no instances, and there is literally nothing there for a count() to range over. `count(Vacated, color = 9) = 24` is true of the body standing on any already-visited floor, which is not a win and would stop a planner at the first step it takes. A goal true in the wrong states is worse than no goal at all. The manual can state its goal only after the body has once stood in (8,7) and those 24 pixels have become dynamic; until then the playbook steers by lattice distance to the knob, which is where the game actually is."
    [depends: the_socket_is_a_keyhole_and_the_pip_names_the_winning_position  probe: pending]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "The arm types a cell by its frame-0 colour, so the body changes type as it walks: at rows 8-12 its pixels are Glyph9, at rows 14-18 they are Vacated. The next descent, from (2,2) to (3,2), needs Vacated pixels going 9 to 5 at rows 14-18 and pixels going 5 to 9 at rows 20-24 -- the second is key2_body_arrives, already written and already witnessed, which will ground at rows 20-24 the moment they are dynamic. Only the clearing half is missing, verbatim for the next desk: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. I have checked it for spurious grounding and it is inert everywhere in this frame, because no Vacated instance renders 9 unless the body stands on it. I still refuse to write it: rule 2 is not negotiable and one descent buys it. Last round the second descent was in the window and I still did not write it; the window has since shrunk and taken that descent with it, which is exactly the kind of thing that makes writing unwitnessed rules expensive."
    [depends: key2_body_arrives  probe: pending]

  theorem nested_cell_terms_parse "Settled by the compiler three rounds running: below(below(...)) six deep parses and grounds, one line of guard draws 24 pixels, and the fallback I once dreaded -- one landmark per lattice cell, which is coordinates in disguise -- is off the table permanently. The four landmarks this manual does declare now carry real arc-cell comments (10,16), (10,40), (40,16), (52,46) instead of the stripped placeholders the previous build shipped, which were silently landing every one of them at (0,0). No rule referenced them, so nothing was drawn wrong; it was a latent trap and it is closed."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem the_meter_rules_i_withdrew "An older build of this manual carried meter_burn_key2 and meter_burn_key4 on one observation each. Both were refuted, and meter_burn_key4's guard would additionally have invented a fifth burn. The lesson is the load-bearing one this round, because the shrunk window offers me those exact two rules again at a 4/5 replay score: one observation per action is not evidence for a rule keyed on the action when a hidden clock explains the same pixels with no free parameter. It is also why key2_floor_leaves stays out of the rules section despite my being fairly sure it is true."
    [probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -5042 and -17520 bits, so its own segmentation loses to writing the pixels out and I owe it nothing structural. Its tracks are nonetheless a useful audit: obj0 (colour 9, 8 cells, 3x3) is panel slot 1, obj1 (colour 1, 9 cells, present 5 frames) is panel slot 2 before the recolour, obj2 (colour 9, 1x3) is an underline, obj4 (colour 9, 1x64) is the whole row-63 bar of which only two cells are dynamic, obj5 (colour 2, first_frame 5) is slot 1 after the recolour, and obj3 is a 1006-cell colour-null blob that swallowed the maze floor -- a fair description of my board, not an object. Every one of them is already inside Glyph9, Spent or board, and obj5 gets no type of its own because a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 5 transitions constrain rank 3 of 365 features, null space dimension 362 -- and its single global law restates my 73-cell census, which I take as corroboration of the census and nothing more. cegis_miner's refusal remains the most useful sentence any engine has produced here: 'no track satisfies the precondition of exactly one move event per transition; the world does not narrate as one mover.' True of the ARM, false of the world. The world has exactly one mover, a rigid 24-pixel ring; the arm can only see 24 simultaneous recolours, which is why my movement law needs a pair of rules per direction instead of one moved() event."
    [probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
# What changed this round and why the ordering changed with it:
#   (a) One command now settles TWO open questions at once. At spawn, up and
#       left are void and down is excluded for ACTION3 and ACTION4 by the
#       t3/t4 no-ops, so right is the only direction either could express --
#       and simultaneously, cumulative frames stand at even, so both parity
#       readings of the meter predict a burn at (63,61) while action-keying
#       predicts none. Any non-key-2, non-key-4 command tests both. Take it.
#   (b) The winning position is now named to the pixel -- lattice (8,7), the
#       body's hole over the pip at (52,46) -- but the comb still shuts the
#       only route to it, so distance-to-the-knob is still the live heuristic
#       and distance-to-the-socket is still dead weight.
#   (c) The binding budget is tokens, not the meter: one token remains, the
#       bar still holds about 62 cells, so roughly 120 commands and one life.
#   (d) replay accumulates and one unpredicted meter cell pins it at 1/5, so
#       "wrong cells in replay" is not a currency I can spend down. Probes are
#       chosen by what the raw frame diff will say, not by what certify will.
# No stored sequence anywhere: every line is a criterion on the current frame
# plus the manual's own open questions.

order     prefer_a_command_that_settles_two_open_questions_at_once     [proof: lean]
order     probe_the_meter_by_piggybacking_it_on_a_direction_probe      [proof: lean]
order     identify_a_direction_key_before_routing_with_it              [proof: lean]
order     probe_from_a_cell_where_one_candidate_direction_is_open      [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it           [proof: lean]
order     reach_the_switch_before_testing_the_switch                   [proof: lean]
order     free_probes_before_token_costing_probes                      [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end             [proof: lean]
order     witness_a_rule_before_writing_it                             [proof: lean]

prune     destination_lattice_cell_is_not_wholly_floor => dead         [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead [proof: lean]
prune     meter_probe_using_a_key_that_burns_under_every_reading => dead [proof: lean]
prune     respawn_while_a_legal_move_exists => dead                    [proof: lean]
prune     respawn_when_no_token_remains and not goal => dead           [proof: lean]
prune     meter_exhausted and not goal => dead                         [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut          [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open         [admissible: lean]
heuristic commands_remaining_at_one_burn_per_two_commands              [admissible: lean]
heuristic open_questions_a_command_can_close                           [admissible: lean]
heuristic unexplained_cells_after_redraw                               [admissible: lean]

prefer    an_unassigned_key_where_right_is_its_only_open_candidate     [ev: 3/3 no_ops]
prefer    a_command_whose_two_rival_readings_predict_different_pixels  [ev: 2/2 meter]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule    [ev: 1/1 moves]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff             [ev: 1/1 levels]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket         [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                [ev: 2/5 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered      [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                [ev: 1/1 levels]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter obj0/obj2/obj4 (colour 9 fragments)", "verdict": "entailed", "as": "Glyph9", "why": "all three are colour-9 cells already inside the arc-colour-9 type with arc-instances: all (panel ring, underline, row-63 bar), so they add no cell my declarations do not already own."},
  {"id": "O-02", "subject": "mdl_segmenter obj1 (colour 1, 9 cells, present 5 frames)", "verdict": "entailed", "as": "Spent", "why": "it is panel slot 2 before the t5 recolour; nine colour-1 cells at frame 0 is exactly count(Spent) = 9."},
  {"id": "O-03", "subject": "mdl_segmenter obj5 (colour 2, first_frame 5)", "verdict": "reject", "why": "those eight pixels are panel slot 1 after a recolour and are already Glyph9 instances; a second type over the same cells is the double claim constraint 5 forbids."},
  {"id": "O-04", "subject": "mdl_segmenter obj3 (colour null, 1006 cells)", "verdict": "reject", "why": "a blob that swallowed the maze floor is a description of my board, not an object; declaring it would put a thousand never-varying cells under a rule."},
  {"id": "O-05", "subject": "landmarks spawn/knob/gate/socket", "verdict": "accept", "why": "re-declared with real arc-cell comments (10,16), (10,40), (40,16), (52,46); the inherited build shipped stripped placeholders that silently placed all four at (0,0)."},
  {"id": "R-01", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept", "why": "retagged to [ev: t2 cov: 24/24] each since the second descent left the observation window; certify's only divergence at t=1 is the meter cell, so all 48 body pixels of the descent are drawn correctly."},
  {"id": "R-02", "subject": "key5_body_clears / key5_body_respawns", "verdict": "accept", "why": "24/24 on each half at t5, and I re-checked both guards against this frame for spurious grounding on the meter cells (render 9 or 1, never 5) and the panel cells (render 9 before t5, 2 or 0 after)."},
  {"id": "R-03", "subject": "meter_burn_key2 and meter_burn_key4, action-keyed, rightof(?p) = wall and colored(rightof(?p), 1)", "verdict": "reject", "why": "they fit this five-transition window 5/5 and would lift replay from 1/5 to 4/5, but each rests on one observation per action, the frames-parity reading fits the same pixels with no free parameter, and my own manual records a longer window in which ACTION2 did not burn and ACTION1 did; I will not buy a score with a rule I have written down as refuted."},
  {"id": "R-04", "subject": "key2_floor_leaves (Vacated 9 to 5 on descent)", "verdict": "probe-pending", "why": "still unwitnessed in this window and quoted verbatim in the manual for the desk that sees the next descent; last round's second descent has since fallen out of the window, which is the concrete cost of writing unwitnessed rules."},
  {"id": "R-05", "subject": "any right/left/up movement rule", "verdict": "probe-pending", "why": "no lateral or upward move has ever been observed, so there is nothing to witness a rule with; the manual predicts 48 wrong cells on the first such move and heals one step behind the body."},
  {"id": "L-01", "subject": "cegis_miner verdict, 'the world does not narrate as one mover'", "verdict": "accept", "why": "true of the arm, not of the world: one rigid 24-pixel ring shows up as 24 simultaneous recolours, which is why my movement law needs a rule pair per direction rather than one moved() event."},
  {"id": "L-02", "subject": "zero_space global law and THIN self-report (rank 3 of 365, 5 transitions)", "verdict": "entailed", "why": "its 73-cell support restates my census cell for cell, including (63,62) and (63,63), and it says itself that its laws are correlations awaiting a breaking transition."},
  {"id": "L-03", "subject": "instance census 37/9/24, board 4023, dynamic 73", "verdict": "accept", "why": "re-derived from the six visible frames as 23 panel + 24 spawn ring + 24 lower ring + 2 meter, and 73 minus the 3 background-at-frame-0 cells equals cells_needing_an_owner = 70 = 37 + 9 + 24."},
  {"id": "L-04", "subject": "the socket is a keyhole: bracket rows 49-55 cols 43-49, pip (52,46)", "verdict": "probe-pending", "why": "the pip sits exactly where the body's one-pixel hole lands if the body stands in lattice (8,7) rows 50-54 cols 44-48; geometry only, untestable until the body gets there, and it needs the comb open first."},
  {"id": "L-05", "subject": "replay accumulates rather than re-seeding", "verdict": "accept", "why": "re-seeding predicts 2 matches (the two world no-ops), accumulation predicts exactly 1, and certify reports 1; the same argument gave 4-against-1 on the longer window."},
  {"id": "P-01", "subject": "press ACTION3 (or ACTION4) from spawn", "verdict": "probe-pending", "why": "right is the only candidate direction either key can still express from spawn, and the same command separates the meter parity from action-keying because cumulative frames are even, so both readings disagree about (63,61); prediction written into the manual as 1 wrong cell if it is inert and 49 if it steps east."},
  {"id": "P-02", "subject": "bump right from (1,5) into the colour-8 knob cell", "verdict": "probe-pending", "why": "the knob is the only interactive thing inside the eleven reachable cells; my rules demand a floor destination, so if the body enters colour 8 the manual announces its own error in one command."},
  {"id": "P-03", "subject": "press ACTION5 from a cell that is not one lattice cell below spawn", "verdict": "probe-pending", "why": "the only separator between 'ACTION5 is respawn' and 'ACTION5 is up', but it spends the last token, so it ranks below every free probe including the two never-pressed keys."},
  {"id": "E-01", "subject": "the meter clock", "verdict": "probe-pending", "why": "wanted a guard on a hidden parity bit or on cumulative frame count; the guard language reads only drawn cells and the current action, and the meter's own drawn state takes both values on both outcomes, so I wrote a theorem plus a next-command prediction instead of a rule."},
  {"id": "E-02", "subject": "a click action's coordinates", "verdict": "probe-pending", "why": "wanted act=click(row, col) for a knob the body may be unable to stand on; the grammar admits only act=key(n), so a click rule would fire regardless of where the click landed and I wrote two_actions_have_never_been_pressed instead."},
  {"id": "E-03", "subject": "the goal predicate", "verdict": "probe-pending", "why": "wanted 'the 24 pixels of rows 50-54 cols 44-48 render 9'; those cells are still board with no instances, and count(Vacated, color = 9) = 24 is true of the body standing almost anywhere, so the manual ships with no goal: section rather than a goal true in the wrong states."},
  {"id": "E-04", "subject": "the panel rules", "verdict": "reject", "why": "wanted a disjunctive guard to separate slot 1's ring from its underline, whose four-neighbourhoods are byte-identical; the grammar has no disjunction and the honest encoding would be four rules clashing on one corner cell, so I carry 23 wrong cells per ACTION5 and say so."}
]
```
```
