# call-001-theorize-round1

model: `claude-opus-5` · 537624 ms · $1.536699 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 40322, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40322, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 40322, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40322, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 44150, "type": "message"}], "output_tokens": 44150, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
# theory.dsl -- world observed for 34 states / 33 transitions
# (RESET + A1 A2 A3 A4 A5, then A2 A5 twelve times, then A5 A5 A5 A5).
# 87 cells have ever changed; this manual names and owns all 87.
#
# WHAT THIS ROUND COST AND WHAT IT BOUGHT
#
#   Last round I deleted `colored(spawn_probe, 5)` from thirteen panel rules
#   on a gain-test argument, and said in as many words: my manual now
#   predicts key(5) at spawn toggles 23 panel cells, no frame has ever
#   tested that, if it is wrong I pay 23 pixels and learn something worth
#   more than 23 pixels. THE WORLD ANSWERED. Four commands, all ACTION5,
#   all at spawn, indices 30-33. The panel did not move. Not one panel
#   pixel changed in four presses. THE CUT WAS WRONG AND IT IS REVERSED:
#   the guard is restored on all thirteen rules, and it now has what it
#   never had before -- FOUR NEGATIVE WITNESSES. 13 toggles with the body
#   away, 0 toggles with the body home. The atom is earned.
#
#   THE SAME FOUR COMMANDS SETTLED THE OTHER OPEN QUESTION, and settled it
#   the other way. Row 63 now reads 9 through col 47 and 1 from col 48:
#   SIXTEEN burns, two more than at state 29. Four presses of an ODD key,
#   at indices 30, 31, 32, 33, burned exactly twice -- at 30 and at 32.
#   Reading A (burns iff the key is 2 or 4) predicted ZERO burns and is
#   DEAD. Reading B (burns iff the command index is even) predicted exactly
#   two, in exactly those places, and is now 33/33 with a discriminating
#   set. The meter is a command counter and no key touches it.
#
#   AND THE FOUR COMMANDS PROVED THE THING I HAVE CARRIED AS A BELIEF SINCE
#   STATE 5. s30 and s31 are pixel-identical (distinct_states 30 against 34
#   states = four coincidences: s1=s0, s3=s2, s31=s30, s33=s32). From s30
#   the world was given ACTION5 and returned s31 = s30, identity. From s31,
#   the same pixels, the world was given ACTION5 AGAIN and returned s32,
#   one pixel burned. SAME STATE, SAME ACTION, DIFFERENT SUCCESSOR. This
#   world is NOT a function of the drawn frame, and constraint 5 obliges my
#   manual to be one. See the_world_is_not_a_function_of_the_drawn_frame.
#
#   THE BILL, STATED PLAINLY: replay can no longer be perfect. t31 and t33
#   replay exactly (identity). t30 and t32 each miss by ONE pixel, the
#   parity burn, which no guard in this language can express and which was
#   board at the instant it burned. Expect 31/33. That is the floor, not a
#   defect I can repair, and I would rather post it than hide it behind an
#   action-keyed burn rule that is now known to be a mis-attribution.

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
  landmark spawn_probe  # arc-cell: carried, coordinates stripped
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t33 compress: 51]
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
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23,t27 cov: 48/48]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23,t27 cov: 18/18]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23,t27 cov: 48/48]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23,t27 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11,t15,t19,t23,t27 cov: 18/18]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

goal:

laws:
  invariant glyph9_instances count(Glyph9) = 51 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4009 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 16 [status: counted]

  theorem the_cut_is_reversed_and_the_guard_is_now_earned "THE ROUND'S FIRST STRUCTURAL CHANGE AND IT IS AN UNDO OF MINE. Last round I deleted colored(spawn_probe, 5) from thirteen panel rules, on the argument that its thirteen positive witnesses were confounded -- every ACTION5 in history had followed an ACTION2, so `key(5) was pressed` and `the body is away` were the same thirteen events, and constraint 3 says a conjunct with no discriminating negative explains no pixel. THE ARGUMENT WAS SOUND AND THE CONCLUSION WAS FALSE, and the difference between those two sentences is the whole value of this round. The manual then predicted 23 panel cells for key(5) at spawn; the world was asked four times and answered zero panel cells four times. THE ATOM NOW HAS FOUR NEGATIVE WITNESSES -- t30, t31, t32, t33, all ACTION5, all with the body home at spawn, all with the panel unmoved in configuration B, confirmed cell by cell in the current frame which still reads 222/2.2/222 at cols 1-3 and 999/9.9/999 at cols 5-7 with row 5 dark at 1-3 and lit at 5-7. So the guard is restored on all thirteen rules and it is no longer a correlation: 13/13 toggles with the body away, 0/4 with the body home. WHAT I WOULD DO AGAIN: buy a negative witness by removing an unearned guard, because an unwitnessed silence is invisible and an unwitnessed prediction of change is answered in one press. WHAT I WOULD DO DIFFERENTLY: the answer arrived on the FIRST press and the next three bought nothing new about the panel -- they were paid for by the meter, which is the only reason this round was not a waste."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_meter_is_command_parity_and_no_key_touches_it "SETTLED, and settled against the reading my rules encode. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right; the current frame reads 9 through col 47 and 1 from col 48 to col 63, SIXTEEN burns after thirty-three commands. Burns occurred at command indices 2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32 -- every even index, sixteen of them, no odd index ever. READING A said burns iff the key is 2 or 4. READING B said burns iff the index is even. For twenty-nine commands the two were numerically identical because every command was an even key at an even index or an odd key at an odd index; I said the separator was one odd key at an even index and cost one command. THIS ROUND SPENT FOUR ODD KEYS AT INDICES 30-33 AND READING A PREDICTED ZERO BURNS. Two burns happened, at 30 and 32, exactly where B says. READING A IS DEAD. The meter counts commands, not keys, and it does not care which key. CONSEQUENCE FOR MY THREE BURN RULES: their attribution is now KNOWN FALSE. I keep them anyway and say why -- they are the shortest expressible shadow of the true law, they draw 14 of the 16 burns on replay, and every alternative is worse. A key(5) burn rule would fire at t31 and t33 where nothing burned; an action-free burn rule would fire at every odd index from t5 on and lose seventeen transitions. Fourteen right, two structurally unreachable, and no better option inside this grammar."
    [depends: meter_burn_key2_next, meter_burn_key4_next, the_world_is_not_a_function_of_the_drawn_frame  probe: passed]

  theorem the_world_is_not_a_function_of_the_drawn_frame "PROVEN THIS ROUND, after carrying it as a belief since state 5. The proof needs two pixel-identical states from which the SAME action produced different successors, and the store hands me the pair: distinct_states is 30 against 34 states, so there are exactly four coincidences, and they are s1=s0, s3=s2, s31=s30, s33=s32. The first two are the old sterile pair -- different keys were pressed from each, so they test nothing. THE LAST TWO ARE NOT. Refutations P-25 and P-26 report the SAME observed hash 132f0bf441d96376, and P-27 and P-28 the same 121cbbc9c93803ed: so s31 = s30 and s33 = s32 to the pixel. Now read the transitions. t31 acted on s30 with ACTION5 and returned s31, which equals s30 -- identity. t32 acted on s31, THE SAME PIXELS, with ACTION5 AGAIN, and returned s32, which differs by one burned bar cell. Same state, same action, two different successors. The hidden bit is the command counter the meter reads and no guard in this language can. WHAT IT COSTS ME IS EXACT AND UNAVOIDABLE: constraint 5 obliges my manual to be a function of the frame, so my manual must be wrong about at least one member of every such pair, and it is wrong about t30 and t32 by exactly one pixel each. Expect replay 31/33 and do not read those two as repairable."
    [depends: the_meter_is_command_parity_and_no_key_touches_it  probe: passed]

  theorem the_four_refutations_are_one_experiment_and_it_paid_for_itself "P-25 through P-28 are four reports of ONE experiment: ACTION5 pressed four times at spawn. Their arithmetic is worth reading because it is how I reconstructed the round. The manual prediction of P-25 is the inert field of P-26 and vice versa -- that is the harness rolling my predicted frame forward without resyncing, so my toggled panel became my next starting point and toggled back, the same closed 2-cycle as the last five rounds. What is NEW is the observed column: P-25 and P-26 observed the same hash, P-27 and P-28 observed the same hash. The world's successors were change, no-change, change, no-change, and the changes are one pixel each at indices 30 and 32. THREE THINGS FELL OUT OF FOUR COMMANDS: the panel guard is earned (four negatives), the meter is command parity (reading A refuted), and the world is not a function of the frame (a pixel-identical pair with the same key and different successors). Compare the six rounds before it: twenty-four refutations, every divergence set a subset of the meter's leading edge, ZERO rules contradicted, nothing learned. A prediction the world can answer is worth more than a prediction that is safe, and this is the evidence for that claim rather than the slogan."
    [depends: the_cut_is_reversed_and_the_guard_is_now_earned, the_meter_is_command_parity_and_no_key_touches_it  probe: passed]

  theorem silence_is_a_prediction_and_exactly_two_of_my_spawn_silences_are_still_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says `I do not know`, it says `nothing happens`, in the same voice it uses for things it has seen. Audit the five keys at spawn after this round. key(1) inert: WITNESSED, t1, zero cells. key(2) moves 48 body cells: witnessed thirteen times. key(5) inert: WITNESSED FOUR TIMES, t30-t33, which is the round's gain -- it was an unwitnessed prediction of change last round and it is now a witnessed silence. key(3) inert: NO WITNESS at spawn, pressed once ever, at t3, from one cell south. key(4) inert: NO WITNESS at spawn, pressed once ever, at t4, from one cell south. TWO OF FIVE SILENCES AT SPAWN ARE FORGED DEATH CERTIFICATES and the elimination is now tight enough to say more: ACTION2 is down, ACTION1 is not east (t1, spawn, east open, nothing moved), ACTION5 is not east (t30-t33, spawn, east open, nothing moved). So EAST IS ACTION3 OR ACTION4, one of my two forged silences is FALSE, and one press of either settles which -- if it steps it is east, if it does not the other is east by elimination. That is the cheapest unclaimed bit on the board."
    [depends: the_action_map_after_thirtythree_transitions, the_cut_is_reversed_and_the_guard_is_now_earned  probe: pending]

  theorem the_action_map_after_thirtythree_transitions "WITNESSED: ACTION2 IS DOWN, 13/13, six rows south, one lattice cell. ACTION5 returns the body from lattice (2,2) to (1,2), 13/13, and does NOTHING at spawn, 4/4. NEGATIVE INFORMATION, stated as negative. At spawn (1,2) up and left are void while down and right are open floor; ACTION1 did nothing there at t1, so ACTION1 IS NEITHER DOWN NOR RIGHT; ACTION5 did nothing there four times, so ACTION5 IS NEITHER DOWN NOR RIGHT either. At (2,2) up was open (the body had just vacated rows 8-12) and down was open (rows 20-24 are floor) while left and right were void; ACTION3 and ACTION4 each did nothing there, so NEITHER IS UP AND NEITHER IS DOWN. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else -- and the something-else is now constrained too, see what_action5_is. The conventional mapping for this action family agrees, which is a prior and not evidence. THIRTY-THREE COMMANDS AND NOT ONE HAS TESTED THE EAST KEY. The test is one press from where the body stands."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_after_four_presses_at_home "Three readings survived thirteen presses because all thirteen were made from one cell south of spawn, where UP, UNDO and RETURN are indistinguishable. This round pressed it FOUR TIMES AT SPAWN and the body did not move a pixel. UP predicts exactly that -- north of spawn is void, the move is blocked. RETURN predicts exactly that -- the body is already home. UNDO in its plain form is REFUTED: t29 was an effective ACTION5 that carried the body home, so an undo at t30 would have carried it back south, and it did not. UNDO survives only in a stack variant where no-ops are not pushed and t29 emptied the stack; I record that variant rather than pretend it is dead, but I no longer rank it. THE SEPARATOR IS NOW CHEAP AND NAMED: press ACTION5 from any cell that is neither spawn nor one south with open floor above it. From lattice (1,3), one step east, UP is void so UP predicts nothing while RETURN predicts a 48-pixel jump west to spawn. That is one more reason the east key is the next thing to buy. The coupling I still cannot break is the panel's: it toggles on every effective ACTION5 and on no ineffective one, so it is a counter of ACTION5's successes, and the 7-versus-9 cascade split says its state is not merely cosmetic."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_cut_is_reversed_and_the_guard_is_now_earned  probe: pending]

  theorem the_panel_guard_is_earned_but_its_extrapolation_is_not "The restored guard reads colored(spawn_probe, 5), which is `cell (8,14) renders floor`, which is `the body is not at spawn`. Every one of the thirteen positives had the body at ONE specific cell, lattice (2,2), and every one of the four negatives had it at spawn. So a guard reading `the body is at (2,2)` -- a second landmark at (14,14) tested for colour 9 -- fits the same 13 positives and the same 4 negatives EXACTLY as well. The two guards differ only at cells the body has never occupied: from a third cell, spawn_probe says the panel toggles and a south_probe would say it does not. I choose spawn_probe because it is the guard that already replayed twenty-five transitions and because the panel reads as a counter of effective ACTION5s rather than of one location, but I am naming the confound BEFORE it costs me, unlike last round. THE PROBE: get the body to any third lattice cell and press ACTION5. Panel toggles, spawn_probe wins; panel still, the guard is really about (2,2) and thirteen rules need a different landmark."
    [depends: key5_slot1_dims, the_cut_is_reversed_and_the_guard_is_now_earned  probe: pending]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over THIRTEEN toggles -- every odd index t5 through t29 -- 23 cells every time; ACTION2 has never touched a panel pixel in thirteen presses; and ACTION5 AT HOME has never touched one in four presses. CONFIGURATION A: slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B, which states 29 through 33 and the current frame all show: slot 1 a hollow colour-2 ring with dark underline, slot 2 a hollow colour-9 ring with dark centre and lit underline. mdl_segmenter corroborates by frame index and has never seen my rules: colour-1 nine-cell tracks obj1 (0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16), obj12 (19-20), obj14 (23-24), obj16 (27-28); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17-18), obj13 (21-22), obj15 (25-26), obj17 (29 onward, and note it is the ONLY colour-2 track to run past two frames -- five frames, 29 through 33, which is the panel standing still for this round's four commands). Its obj0 (colour 9, eight cells, 3x3, all 34 frames) and obj2 (colour 9, 1x3, all 34) persist while it narrates 26 MOVE events: the hollow ring and the lit underline do not appear and vanish, they TRAVEL between the two slots. One marker, two seats, colour 9 marks the occupied seat. What the seats HOLD is still unknown and I will not guess. I cannot model it as a mover either: the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring travelling four columns is not a move, and ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9. ACTION2 returned SEVEN frames from configuration A (t2, t8, t12, t16, t20, t24, t28) and NINE from configuration B (t6, t10, t14, t18, t22, t26), 13/13 with no exception. ACTION5 returned nine frames on all thirteen effective presses; every no-op returned one. THE NET EFFECT IS IDENTICAL IN ALL THIRTEEN ACTION2 PRESSES, so this costs nothing in replay and buys nothing in prediction, and it remains the only evidence that the panel does anything besides display. I record it as a limitation of my own semantics: cascade single_frame compares only the net, so up to eight intermediate frames per command are discarded unread. LIVE PREDICTION, now that the panel is confirmed stuck in configuration B: the next ACTION2 from spawn must take NINE internal frames. Seven would mean the panel's effect on the animation is not what I think, and it would cost me nothing to find out because the diff is free."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_meter_edge_saturates_the_refutation_channel_and_parity_makes_it_worse "A law of this manual rather than of this world, and now the most expensive fact on the board. Each of the 64 cells of the row-63 bar burns EXACTLY ONCE, advancing leftward. At the instant a cell burns it has never changed, so it is board, so no instance exists for it, so NO RULE OF MINE CAN DRAW IT. Therefore my burn rules have zero predictive value on the leading edge and full value on replay -- a division of labour, not a contradiction. WHAT PARITY ADDS: before this round I could tell myself that only keys 2 and 4 burned, so a refutation on key 5 meant something. Now I know EVERY EVEN-INDEX COMMAND BURNS, whatever the key, so every even-index command is scored a refutation before it is even chosen, and refutation-fired carries ZERO information at even indices. The next index is 34, EVEN: whatever I press, (63,47) burns, I cannot draw it, and I am refuted by exactly one pixel. Read refutations by their DIVERGENCE SET; where that set is a subset of the bar's leading edge, the manual is not implicated. All twenty-eight refutations across seven rounds have been exactly that."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_meter_is_a_budget_and_it_is_now_priced_correctly "Sixteen of sixty-four bar cells consumed after thirty-three commands. Under the settled parity reading the bar buys 48 more burns and therefore about 96 MORE COMMANDS, since every second one burns. I do not know that exhaustion ends the game -- no frame has shown it -- but 96 commands against a route I can see costing about nineteen steps plus interactions plus identification probes is not the binding constraint. The route: spawn (1,2) east three cells to (1,5) beside the knob, an unknown number of interactions there, three cells back west, seven cells south down lattice column 2 to (8,2), five cells east to the socket at (8,7). THE BINDING CONSTRAINT IS THIRTY-THREE COMMANDS SPENT AND THE BODY HAVING OCCUPIED TWO LATTICE CELLS. Note that parity makes waste cheaper than I feared and repetition no cheaper: a wasted command still costs half a bar cell."
    [depends: the_meter_is_command_parity_and_no_key_touches_it, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_two_no_op_rules_still_fail_the_gain_test_and_i_keep_them_for_a_weaker_reason "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has one witness on a transition where zero cells changed, and the manual would replay identically without them. They were bought to test the alphabet hypothesis, which is refuted, so THAT reason is gone. The reason I keep them is weaker and I will not dress it up: deleting them narrows certify's adjudicated action set from five keys to three, removing information I can see for a benefit -- two lines -- I cannot measure. This round supplies a second, better reason: my one deletion of an unearned thing was reversed by the world four commands later. Conservatism about deletions is not a virtue in general, but it is the correct posture toward deletions that change NO prediction, and these two change none. They remain declared failures of the gain test and the two cheapest deletions in this manual."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_key_alphabet_hypothesis_is_refuted  probe: passed]

  theorem the_key_alphabet_hypothesis_is_refuted "Kept compressed, because it is settled. I once hypothesised that the command chooser derives its candidate keys from the act=key(n) literals in my rules, and that this was why round after round bought A2 A5. I paid two witnessed no-op rules to widen the alphabet. THE INSTRUMENT MOVED AS PREDICTED -- certify went from 3 actions and 54 pairs to 5 actions and now 150 pairs, 0 clashes, 0 step crashes -- and THE COMMANDS DID NOT MOVE. Alphabet width is not sufficient. What DID move the commands is now known: last round I gave key(5) at spawn a predicted 23-cell change and the chooser pressed key(5) four times. THE CHOOSER FOLLOWS THE MANUAL'S PREDICTED CHANGE. That is a lever and it is also a trap, because the honest manual after this round predicts change for exactly one key at spawn again."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_parity "Two expressive holes, and this round they interlock. FIRST: there is no third outcome for a (state, action) pair -- not `no change` and not a named successor, but `unobserved, the manual declines to predict`. Rules produce events, absence of a rule produces identity, and the compiled step is total. The one lever the grammar offers is deleting an unearned guard, which converts an unwitnessed silence into an unwitnessed PREDICTION OF CHANGE, testable in one press; I used it, it was answered, and the answer was no -- which is exactly what the lever is for. SECOND: the true meter law is `burns iff the command index is even`, and the guard language reads pixels and the action name and nothing else. There is no command counter, no phase pixel, and the frame provably does not determine the parity, since s30 and s31 are identical and only one of them was followed by a burn. So the parity law CANNOT be written here at all, at any length. If a future desk gains one expressive extension, ask for a state counter before asking for `not`."
    [depends: the_world_is_not_a_function_of_the_drawn_frame, the_cut_is_reversed_and_the_guard_is_now_earned  probe: passed]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4009 + dynamic 87 = 4096, and 51+24+9 = 84 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 87. Consequence: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This is the seventh consecutive round in which that sentence, written in advance, was the entire content of every refutation. The two cells burned this round, (63,49) and (63,48), are dynamic NOW, which is why Glyph9 went 49 to 51 and the burned count 14 to 16 -- but they were board when they burned, so t30 and t32 are one wrong pixel each even after the repair, and this time the repair does not even restore replay, because no rule of mine burns on key 5. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, plus one for the parity burn if the index is even, 24 for the second step, 0 thereafter. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 87 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 16 are the burned right end of row 63: cols 48 through 63, two more than last round. 23+24+24+16 = 87 = dynamic_cells. By frame-0 colour: 51 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 16 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 51+9+24 = 84 = cells_needing_an_owner exactly, and 4096-87 = 4009 = constant_cells exactly."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended thirteen times and all thirteen started at spawn, so no rule turns Vacated pixels from 9 back to 5 on an ACTION2: rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below-six(?v), 5) then recolored(?v, 5). One ACTION2 from lattice (2,2) buys it. (2) EAST-WEST MOTION. Whatever the east key is, it needs a pair: a leaves rule over Glyph9 guarded on colour 9 with rightof-six rendering 5, and its arrives twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) THE PARITY BURN, which is not a missing rule but an inexpressible one, and which will cost exactly one pixel on every even-index command for the rest of the game. I state all three prices in advance so none can be mistaken for a surprise."
    [depends: key2_body_arrives, the_meter_edge_saturates_the_refutation_channel_and_parity_makes_it_worse  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all 150 adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth below is row 69. So colored(off-board, k) is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen rules rest on this and every row and column discrimination in the panel is built from it: the k-th above is off-board exactly when k exceeds the row, so row 1 is above-twice equals wall, row 3 is a colour test on above-twice -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column: col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice, pairwise exclusive, which is why the ambiguity check reports 0 clashes. Restoring the spawn_probe conjunct only tightens this: it narrows all thirteen panel rules by the same atom, so no pair that was exclusive before can clash now. Not one rule uses `not`, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated one row per internal frame and the world reports the whole animation for a single action; cascade single_frame compares only the net, which is identical for all thirteen ACTION2 presses (48 body cells, rows 8-18, cols 14-18) whether the command took 7 frames or 9. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, THIRTEEN times. ONE PRESS IS ONE LATTICE CELL, 13/13, and every distance in the playbook rests on that."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame and unchanged: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open, C=6 holds the knob, C=7 does not exist in this band; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2, plus a fragment of floor at row 48 cols 42-50 that is one row deep and cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in thirty-four frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it has been at spawn in twenty of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed THIRTEEN times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows, col 49 and col 43 are separator columns -- so what is drawn is the north, south and east walls of lattice cell (8,7), painted in colour 9, with the west wall at col 43 left as FLOOR. Inside it, rows 50-54 cols 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, col 50 rows 49-56 is a one-cell strip of floor that leads nowhere. Overlay the body standing in lattice (8,7) -- 5x5, aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in thirty-four frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem pixel at (12,40), colour 8 filling col 40 from row 12 down to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18. It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in thirty-four frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell -- the eight knob pixels other than its centre, plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Thirty-three commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after thirty-four states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. I have no witness for key(6) or key(7), so no rule can name them, so they sit outside the manual's alphabet -- which I once thought decisive and now know is not sufficient, since keys 1 and 3 are inside the alphabet and were still never chosen."
    [depends: the_key_alphabet_hypothesis_is_refuted  probe: pending]

  theorem the_goal_section_is_empty_on_purpose "Still empty, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and fifty siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would be true of the body standing one cell south of spawn, which is not a win. The alternatives fail too: count(Glyph9, color = 5) = 24 is true of every state where the body is anywhere but home, and a Wire type on colour 8 would have zero instances because every colour-8 cell is constant, so count(Wire) = 0 would be true at RESET. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. I name the price plainly: is_goal compiles to False, no plan terminates, and nothing ranks one command above another except whether the command is predicted to change pixels -- which, with the guard restored, admits exactly ONE key at spawn again, and that key is the one that has been pressed thirteen times."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_key_alphabet_hypothesis_is_refuted  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The next command has index 34, EVEN, so (63,47) BURNS WHATEVER I PRESS and I cannot draw it: every option below carries exactly one guaranteed wrong pixel and refutation-fired therefore carries zero information this turn. The body is at spawn, the panel is in configuration B, sixteen meter cells are burned. ACTION3 at spawn: my manual predicts ZERO cells and has NO WITNESS for that, so this is the press I want -- 48 undrawable cells plus the burn means ACTION3 IS EAST and the map is closed; 1 cell, the burn alone, means ACTION3 is not east and therefore ACTION4 IS EAST by elimination, since ACTION1 and ACTION5 are both excluded from east at this very cell. Either answer names the east key. ACTION4 at spawn: the same experiment with the labels swapped. ACTION1 at spawn: 1 cell, key1_inert_at_spawn firing as a no-op, the silence I already have a witness for, nothing bought. ACTION5 at spawn: 1 cell, now WITNESSED four times, nothing bought. ACTION2 at spawn: 48 body cells I draw correctly plus the burn -- one wrong pixel and nothing learned, because key2_body_leaves and key2_body_arrives are at 312/312, except for one free datum, the cascade must be NINE frames from configuration B. If ACTION5 is pressed at spawn a fifth time and the panel moves, this manual is wrong twice over and I would want to know that more than anything else on this list."
    [depends: the_meter_is_command_parity_and_no_key_touches_it, silence_is_a_prediction_and_exactly_two_of_my_spawn_silences_are_still_forged  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept compressed because the lesson is structural and cost a full round. Thirteen panel rules once carried colored(spawn_probe, 5) while the landmark line read a prose placeholder instead of a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The coda, now complete: that same atom was deleted last round for failing the gain test and is restored this round with four negative witnesses. It has been wrong by pointing nowhere, wrong by being absent, and is now right for a reason I can state. The landmark reads (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because a future desk will be tempted by the same repair I have now rejected five times. To draw the leading-edge burn I would need an instance on a board cell. The arm offers exactly one lever, arc-instances: all, and its documented behaviour is to instance every cell OF THAT COLOUR THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance. The tempting workaround is a second declared type on colour 9 without arc-instances, hoping the arm seats one instance somewhere useful. I reject it: the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, the seat is unspecified, and any cell it landed on would be claimed twice, which is the constraint-5 error the grammar warns about in as many words. A landmark cannot help either, because landmarks are cells and every event in the language takes an object as its first argument. So the hole is a property of the arm, it is permanent for this level, and with parity confirmed it now costs one pixel on EVERY second command rather than only on key 2 and key 4."
    [depends: the_meter_edge_saturates_the_refutation_channel_and_parity_makes_it_worse  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter keeps a positive gain of +11940 bits at compression_ratio 0.527 on split_by_color=false, against -132740 bits when split by colour; its segmentation beats writing the pixels out and I still owe it nothing structural. Its eighteen tracks corroborate the panel by frame index and one of them corroborates THIS ROUND specifically: obj17, colour 2, first_frame 29, frames_present 5 -- the only colour-2 track longer than two frames, which is the panel standing still through t30-t33 exactly as the restored guard requires. obj0 and obj2 persisting through all 34 frames while the segmenter narrates 26 moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 16 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 33 transitions constrain rank 17 of 435 features, null space dimension 418, nearly every vector in it a law true over these states and unfalsified rather than confirmed -- and its single global law is my census. cegis_miner refuses on every track and its verdict, `the world does not narrate as one mover`, remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHAT THE LAST FOUR COMMANDS SETTLED =========
# Four presses of ACTION5 at spawn, indices 30-33. The panel did not move.
# Two bar cells burned, at indices 30 and 32.
#
#   1. THE CUT IS REVERSED. `colored(spawn_probe, 5)` is back on thirteen
#      panel rules and it now has FOUR NEGATIVE WITNESSES: 13/13 toggles
#      with the body away, 0/4 with the body home. ACTION5 at spawn is a
#      witnessed no-op.
#   2. THE METER IS COMMAND PARITY. Four ODD keys at indices 30-33 burned
#      exactly twice, at the two EVEN indices. The action-keyed reading
#      predicted zero burns and is dead. 33/33 for parity, with a
#      discriminating set at last. No key touches the meter.
#   3. THE WORLD IS NOT A FUNCTION OF THE DRAWN FRAME -- PROVEN. s30 and
#      s31 are pixel-identical; ACTION5 from s30 returned identity and
#      ACTION5 from s31 burned a cell. Same pixels, same key, two
#      successors.
#
# The wrong prediction was worth more than six safe rounds. But only the
# FIRST of the four presses answered it; presses two, three and four were
# the harness re-choosing the same key against a rolled-forward frame, and
# they were paid for by the meter alone. Buying a negative witness is right;
# buying it four times is not.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   At spawn (where the body IS):  key(2) -> 48 body cells
#                                  keys 1, 5 -> nothing, WITNESSED
#                                  keys 3, 4 -> nothing, NO WITNESS
#   Index 34 is EVEN, so (63,47) burns under every key and I cannot draw it:
#   one guaranteed wrong pixel this turn whatever is pressed, and
#   refutation-fired carries ZERO information at an even index.
#
# ========= THE ONE THING WORTH BUYING =========
# EAST IS ACTION3 OR ACTION4 AND ONE PRESS SETTLES IT.
#   ACTION2 is down (13/13). ACTION1 is not east -- pressed at spawn at t1
#   with east open, nothing moved. ACTION5 is not east -- pressed at spawn
#   four times this round with east open, nothing moved. Two candidates
#   remain and the body is standing where the test is free: east of spawn is
#   three lattice cells of unbroken floor, west is void.
#   Press ACTION3 (or ACTION4): if the body steps, that key is EAST and the
#   map is closed; if it does not, the OTHER is east by elimination. Both
#   outcomes name the east key. No other command on the board names anything.
#
# The advertised price of the step onto fresh ground: 48 pixels my manual
# cannot draw, because rows 8-12 cols 20-24 have never changed and are board.
# That is a refutation I have priced in advance and it must not be read as a
# defect. 24 pixels for the second step, 0 for the third.
#
# ------------------------------------------------------------------------
# STATE 33: body home at lattice (1,2); panel configuration B; SIXTEEN meter
# cells burned, cols 48-63 of row 63; next command index 34, EVEN. Eleven
# lattice cells reachable, the body has stood in TWO in thirty-four states.
# Three steps east along lattice row 1 reach the cell beside the knob; the
# knob is the far end of one connected colour-8 wire whose near end is the
# comb; the comb gates every route to the socket at (8,7). Under parity the
# bar buys about 96 more commands against a route of about nineteen steps:
# the budget is not binding, repetition is.

order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     buy_the_probe_that_closes_a_question_no_other_command_can_close  [proof: lean]
order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     ignore_refutation_pressure_entirely_when_the_index_is_even       [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     ranked_only_to_separate_the_two_meter_readings => dead             [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic live_readings_a_command_can_eliminate                             [admissible: lean]
heuristic commands_remaining_under_the_confirmed_parity_budget              [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 2/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 0/33 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 33/33 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_witnessed_no_op                [ev: 2/7 keys]
prefer    a_press_at_a_third_cell_that_splits_up_from_return               [ev: 4/4 key5_at_home]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

## Why you are being called: the surprises that fired

### replay_mismatch (empirical family -> theory.dsl)

the manual has no executable form: theory.py has not been generated

```json
{
 "beat": "certify",
 "carried": true,
 "level": 1,
 "why": "theory.dsl is non-empty but generated/theory.py could not be loaded, so nothing can replay it"
}
```


## What certify said about the manual you have now

```json
{
 "expensive": {
  "available": false,
  "detail": "no Lean form was generated",
  "ok": false,
  "state_estimate": null
 },
 "first_divergence": null,
 "proof_layer_available": false,
 "replay": {},
 "responsibility": {},
 "unambiguous": null
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
# theory.dsl -- world observed for 6 states / 5 transitions
# (RESET, then ACTION1 ACTION2 ACTION3 ACTION4 ACTION5, one command each).
# 73 cells have ever changed; this manual names and owns all 73.
#
# ================= READ THIS BEFORE THE RULES =================
#
# 1. THE MANUAL I INHERITED DID NOT COMPILE, SO NOTHING WAS CHECKED.
#    certify reports no replay, no responsibility, no ambiguity verdict:
#    theory.dsl was non-empty and generated/theory.py could not be loaded.
#    The grammar names exactly one HARD compile error and the file had it:
#        landmark spawn_probe  # arc-cell: carried, coordinates stripped
#    "carried, coordinates stripped" is not (row, col). A landmark the
#    level cannot place kills the file. It now reads # arc-cell: (8, 14).
#    I also removed the bare `goal:` header with no indented body as the
#    second suspect -- a section with an empty body is not a documented
#    legal form, "no goal section at all" is. Everything below is downstream
#    of that repair, and the repair is the round's whole deliverable: a
#    manual that cannot be run is a manual with no evidence at all.
#
# 2. THE STORE HOLDS SIX STATES. THE MANUAL I INHERITED CLAIMED THIRTY-FOUR.
#    That is not a difference of opinion, it is a contradiction with the
#    frame in front of me. The old manual asserted SIXTEEN burned meter
#    cells, 87 dynamic cells, 51 Glyph9 instances, thirteen ACTION2 presses.
#    The current frame's row 63 reads 9 through col 61 and 1 at cols 62-63:
#    TWO burns. The store reads dynamic_cells 73, constant_cells 4023,
#    cells_needing_an_owner 70, states 6, steps 6. Every one of those
#    numbers matches the six-state history and refutes the thirty-four-state
#    history. Either the episode was restarted and the store rewound, or
#    that narrative was never in this store. I cannot tell which, and it
#    does not change what I am allowed to write: CONSTRAINT 2 BINDS ME TO
#    THE TRANSITIONS THIS STORE ACTUALLY HOLDS. Every `ev:` tag below cites
#    only t1-t5. Every count below is recomputed from this frame.
#    The inherited beliefs I cannot witness are not deleted -- they are
#    demoted to `theorem ... [probe: pending]`, which is what that keyword
#    is for, and each names the pixels it will cost if it is right and I
#    left it out.
#
# 3. WHAT SIX TRANSITIONS ACTUALLY BOUGHT, AND IT IS NOT NOTHING.
#    t1 A1 at spawn: 0 cells. t2 A2: 48 body cells six rows south + 1 burn.
#    t3 A3 one south: 0 cells. t4 A4 one south: 1 cell, a burn, body still.
#    t5 A5 one south: 48 body cells back north + 23 panel cells.
#    Every one of the 73 dynamic cells is touched by that history except the
#    burn edge, and the manual below replays all five transitions to the
#    pixel except nothing -- I expect 5/5, and if it is not 5/5 the defect
#    is mine and legible.

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

  theorem the_compile_error_was_one_comment_and_it_cost_the_whole_round "The single most useful sentence I can leave behind. The inherited manual declared `landmark spawn_probe  # arc-cell: carried, coordinates stripped`. The grammar says in as many words that every landmark line MUST carry a trailing `# arc-cell: (row, col)` and that a landmark the level cannot place is a HARD compile error. So theory.py was never generated, and every downstream verdict came back empty: replay {}, responsibility {}, unambiguous null, first_divergence null. NOTHING IN THAT MANUAL WAS EVER CHECKED, including the thirteen panel rules its prose spends four paragraphs defending. Note the failure mode: a manual that does not compile produces no divergence and therefore looks exactly like a manual with no defects. The lesson generalises past this bug -- an empty certify block is the loudest possible signal and must be read as `nothing is known` rather than `nothing is wrong`. The repair is (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. I also dropped the bare `goal:` header with no indented body, since `no goal section at all is legal` is documented and `a section with an empty body` is not."
    [depends: key5_slot1_dims  probe: pending]

  theorem the_store_holds_six_states_and_every_tag_in_this_file_cites_one_of_them "The inherited manual narrated thirty-three transitions and the store hands me five. This is not a disagreement I can split. Its claims are refuted by the frame on my desk: it says SIXTEEN meter cells burned and row 63 shows TWO, at cols 62 and 63; it says 87 dynamic cells and the store says 73; it says 51 Glyph9 instances and the census below counts 37; it says the body has been driven south thirteen times and the store records ONE ACTION2. Every number in the store -- constant_cells 4023, cells_needing_an_owner 70, distinct_states 4, states 6, cascade_lengths [1,7,9] -- fits the six-state history exactly. So either the episode restarted and the store rewound, or that narrative never described this store; I cannot distinguish those from here and I do not need to, because constraint 2 binds me to witnessed transitions either way. WHAT I DID WITH THE INHERITED BELIEFS: kept every one that this frame independently confirms (the map, the lattice, the socket, the aperture -- all readings of pixels I can re-read now), demoted every one whose only support was t6-t33 to `probe: pending`, and priced each demotion. WHAT I REFUSE TO DO: re-cite t30-t33. A tag that names a transition the store does not hold is worse than no tag, because it cannot be checked and it looks checked."
    [depends: dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 73 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels at rows 1-3 cols 1-3, its centre (2,2) being colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 before t5 and 0 after; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 2 are the burned right end of row 63, cols 62 and 63. 23+24+24+2 = 73 = dynamic_cells. By frame-0 colour: 37 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 2 meter), 9 colour-1 (slot 2, solid at frame 0), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 37+9+24 = 70 = cells_needing_an_owner EXACTLY, which is the store telling me it does not count background-coloured cells as needing an owner; the 3 colour-0 cells are the difference between 70 and 73 and Dark is declared to carry them anyway. 4096-73 = 4023 = constant_cells exactly."
    [probe: passed]

  theorem the_dark_type_is_the_one_declaration_i_am_not_sure_the_arm_honours "Dark is declared on colour 0, which is the background. The arm instances every cell of a declared colour THE BOARD CANNOT EXPLAIN, and (5,5),(5,6),(5,7) do vary, so they should be instanced; but the store's own arithmetic excludes them from cells_needing_an_owner, so the arm may treat background-coloured cells as board unconditionally. IF IT DOES, key5_underline2_lights never fires and t5 replays three pixels short, at row 5 cols 5-7, and the divergence set will say so precisely. There is no alternative declaration -- those three cells are colour 0 at frame 0 and colour 9 after t5, and typing is by frame-0 colour -- so the choice is Dark or three permanently unexplained pixels. I take Dark and name the exact three cells to look for in the first divergence report."
    [depends: key5_underline2_lights, dynamic_census  probe: pending]

  theorem the_action_map_after_five_transitions "WITNESSED HERE, not inherited. ACTION2 IS DOWN: t2, the 5x5 body block moved from rows 8-12 to rows 14-18, exactly six rows, one lattice cell, over floor that continues further south -- so one press is one lattice cell and not a slide. ACTION5 CARRIES THE BODY BACK NORTH: t5, rows 14-18 to rows 8-12. NEGATIVE INFORMATION, stated as negative. At spawn (1,2) north and west are void, south and east are open floor; ACTION1 did nothing at t1, so ACTION1 IS NEITHER DOWN NOR EAST. At lattice (2,2) north was open (the body had just vacated rows 8-12) and south was open (rows 20-24 are floor at cols 13-31) while east and west were void (cols 8-12 and 20-24 are 0 at those rows); ACTION3 and ACTION4 each did nothing there, so NEITHER IS UP AND NEITHER IS DOWN, and their inertness is fully explained if they are the horizontal pair. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 and ACTION4 the two horizontals in some order, ACTION5 up-or-return. EAST IS ACTION3 OR ACTION4 AND NOTHING IN THIS STORE SAYS WHICH. The body stands at spawn where east is three lattice cells of unbroken floor: one press names the key whichever way it answers, because a step means that key is east and no step means the other one is."
    [depends: key2_body_arrives, key5_body_respawns, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem key5_is_written_as_spawn_refills_and_that_is_a_return_reading_i_did_not_choose "Worth stating because it is a prediction I will be held to. key5_body_respawns is guarded on PIXELS -- a Glyph9 cell rendering 5 whose neighbour above renders 5 -- and not on where the body is. Its one witness had the body one cell south, where UP and RETURN are indistinguishable. But as written it fires from ANY state in which the spawn ring reads floor. So my manual predicts that after a first eastward step, ACTION5 redraws the body at spawn WITHOUT erasing it from its new cell, because the cells it would have to erase are at rows 8-12 cols 20-24, which have never changed, are board, and have no instance. TWO BODIES, 24 wrong pixels, and I am naming it now so it cannot be sold to me later as a surprise. The honest content is: this rule is a spawn-ring refill rule, its RETURN flavour is an artefact of guarding on pixels, and the first ACTION5 pressed from a third lattice cell separates UP from RETURN in one command -- UP predicts nothing at all from any cell whose north is void, RETURN predicts a 48-pixel jump."
    [depends: key5_body_respawns, the_action_map_after_five_transitions  probe: pending]

  theorem the_panel_toggles_with_the_body_away_and_the_return_half_is_unwitnessed_here "t5 turned 23 panel cells over, all at once, while the body returned home: slot 1's eight ring pixels 9 to 2, underline 1's three 9 to 0, slot 2's nine 1 to 9 except its centre (2,6) 1 to 0, underline 2's three 0 to 9. The current frame still shows that configuration -- call it B -- at rows 1-3 and row 5, cols 1-3 and 5-7, and I have re-read every pixel of it. ONE WITNESS, and the guard colored(spawn_probe, 5) means `the body is not at spawn`, which was true at the start of t5 and is the only discriminator I have; ACTION2 at t2 touched no panel pixel with the same guard true, which is one negative for `any key toggles it`. WHAT I DO NOT HAVE IN THIS STORE IS THE RETURN HALF. Nothing here witnesses B going back to A, so under constraint 2 the six rules that would do it are NOT in the manual, and I write them out here so that the transition which witnesses them costs one paste: key5_slot1_lights over Glyph9 on colour 2 to 9; key5_underline1_lights over Glyph9 on colour 0 with above-six equal wall to 9; key5_slot2_ring_resets over Spent on colour 9 to 1; key5_slot2_centre_resets over Spent on colour 0 to 1; key5_underline2_dims over Dark on colour 9 to 0; all five guarded by act=key(5) and colored(spawn_probe, 5). THE PRICE OF LEAVING THEM OUT IS EXACTLY 23 PIXELS on the first effective ACTION5 taken from configuration B, and it buys the certainty that no rule in this file rests on a transition the store does not hold."
    [depends: key5_slot1_dims, key5_slot2_centre_darkens  probe: pending]

  theorem the_meter_is_a_leftward_bar_and_two_readings_still_fit_it "Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right. Two cells are burned: (63,63) at command index 2 under ACTION2, (63,62) at index 4 under ACTION4. READING A: a burn happens when the key is 2 or 4. READING B: a burn happens when the command index is even. BOTH FIT ALL FIVE TRANSITIONS PERFECTLY, because indices 1, 3, 5 carried odd keys and indices 2, 4 carried even ones -- this store contains no separator and I will not pretend otherwise. My two burn rules encode reading A because reading B cannot be written in this grammar at all: the guard language reads pixels and the action name, there is no command counter, and no pixel of the frame records the parity. THE SEPARATOR IS ONE COMMAND AND IT IS FREE: press an ODD key at the next index, which is 6 and therefore even. If (63,61) burns, reading A is dead and my two burn rules are known mis-attributions kept only for replay. If nothing burns, reading A survives another round. Note that ACTION3 is an odd key and is also the east probe -- one press answers two questions, which is why the playbook ranks it first."
    [depends: meter_burn_key2_rightmost, meter_burn_key4_next  probe: pending]

  theorem i_cannot_draw_the_leading_edge_burn_whichever_reading_wins "A law of this manual rather than of this world. The arm instances exactly the cells that have ALREADY changed, so the next cell to burn, (63,61), is board right now, has no instance, and NO RULE OF MINE CAN RECOLOUR IT. My burn rules therefore have zero predictive value at the leading edge and full value on replay, which is a division of labour and not a contradiction: t2 and t4 replay to the pixel because (63,63) and (63,62) are dynamic NOW. The tempting repair -- a second declared type on colour 9 without arc-instances, hoping the arm seats an instance somewhere useful -- I reject: the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, its seat is unspecified, and any cell it landed on would be claimed twice, which is exactly the constraint-5 error the grammar warns about. CONSEQUENCE FOR READING REFUTATIONS: a divergence set consisting only of the bar's leading edge does not implicate this manual. A divergence set containing anything else does."
    [depends: the_meter_is_a_leftward_bar_and_two_readings_still_fit_it  probe: passed]

  theorem the_world_may_not_be_a_function_of_the_drawn_frame_and_this_store_cannot_tell "distinct_states is 4 against 6 states, so there are exactly two pixel-coincidences: s1 = s0 (ACTION1 changed nothing) and s3 = s2 (ACTION3 changed nothing). To show the world is not a function of the frame I would need a pixel-identical pair from which THE SAME action produced different successors. My two pairs are sterile: from s0 the world was given ACTION1 and from s1 it was given ACTION2, and from s2 it was given ACTION3 and from s3 ACTION4. Different keys, so nothing is tested. If reading B of the meter is true then such a pair MUST exist -- press any key twice in a row from a state where it does nothing, and the even press burns while the odd press does not -- and constraint 5 obliges my manual to be a function of the frame, so it would be wrong about one member of every such pair by exactly one pixel. I record the prediction rather than the conclusion: THE CHEAPEST WAY TO PRODUCE THAT PAIR IS TWO CONSECUTIVE PRESSES OF A KEY THAT IS INERT WHERE THE BODY STANDS, and it is the same experiment as the meter separator."
    [depends: the_meter_is_a_leftward_bar_and_two_readings_still_fit_it  probe: pending]

  theorem silence_is_a_prediction_and_three_of_my_five_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says `I do not know`, it says `nothing happens`, in the same voice it uses for things it has seen. Audit the five keys at spawn, where the body stands now. key(1) inert: WITNESSED, t1, zero cells. key(2) moves 48 body cells: witnessed once, t2. key(3), key(4), key(5) at spawn: NO WITNESS -- key(3) and key(4) were each pressed once ever, both from one cell south, and key(5) has never been pressed at spawn in this store at all. THREE OF FIVE SILENCES AT SPAWN ARE FORGED DEATH CERTIFICATES. Two of them are the east key by the elimination above, so at least one of those three silences is FALSE, and the manual is currently claiming with a straight face that four of the five keys do nothing here. That is the largest single block of unearned confidence in this file and it is also the cheapest to fix: one press."
    [depends: the_action_map_after_five_transitions, key1_inert_at_spawn  probe: pending]

  theorem the_two_no_op_rules_fail_the_gain_test_and_i_keep_them_for_a_narrow_reason "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has one witness on a transition where zero cells changed, and replay is identical without them. They explain no pixel and they lengthen the manual, so they fail constraint 3 and I say so rather than dressing them up. The reason I keep them: they are the only occurrences of act=key(1) and act=key(3) in the file, and deleting them narrows the action set certify adjudicates from five keys to three. Since the next command I want is ACTION3, removing the only rule that mentions ACTION3 is a way to make my own probe unchooseable. They are declared failures of the gain test and the two cheapest deletions here the moment the east key is named."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem i_deleted_the_key2_leading_edge_burn_rule_and_here_is_why "The inherited manual carried `meter_burn_key2_next`, firing on a Glyph9 whose right neighbour reads 1. In this store it has NO witness -- t2's burn was the rightmost cell, guarded by rightof equals wall, and t4's was under key(4). It also cannot pay its way going forward: the only cell it could ever recolour next is (63,61), which is board and has no instance, so the rule would fire on nothing. Zero witnesses, zero pixels explained, zero pixels predictable: it fails constraints 2 and 3 simultaneously and it is gone. meter_burn_key4_next survives only because t4 witnesses it exactly and it replays that transition to the pixel."
    [depends: meter_burn_key4_next, i_cannot_draw_the_leading_edge_burn_whichever_reading_wins  probe: passed]

  theorem the_rules_are_pairwise_exclusive_and_off_board_cell_terms_are_false "Constraint 5 checked by hand, since certify has never had an executable form to check it with. Under key(2): body_leaves needs below-six to render 5, which is off-board for any row past 57, so it cannot fire on either meter cell; the rightmost-burn rule needs rightof equal wall, true only at col 63, where no other Glyph9 instance sits. Under key(5): body_respawns needs colour 5 while both panel-dim rules need colour 9. slot1_dims needs above-four equal wall (rows 0-3); underline1_dims needs a COLOUR TEST on above-four, which is false for rows 0-3 precisely because a colour test on an off-board cell evaluates false rather than raising -- that is the load-bearing fact, and it is the same trick that separates slot 2 by row (row 1 is above-two equals wall, row 3 is a colour test on above-two, row 2 is above-three equals wall with a colour test on above-one) and by column (col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-one, col 7 is a colour test on leftof-two). Pairwise exclusive in every combination I can construct on the observed states. Not one rule uses `not`, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame, which is the only authority I have: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2 plus a one-row fragment at row 48 cols 42-50 that cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in six frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it is at spawn now."
    [depends: key2_body_arrives, the_action_map_after_five_transitions  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed at t2: (16,16) stayed 5 while its 24 neighbours turned 9, and again at t5 in reverse with (10,16). This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows, cols 43 and 49 separator columns -- so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side left as floor. Inside it, rows 50-54 cols 44-48 are floor except the lone colour-9 pixel at the exact centre (52,46). Overlay the body standing there -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate: the game is plausibly won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed, so it is board and no object owns it; the first time the body enters, those 24 cells become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem at (12,40), colour 8 filling col 40 from row 12 to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18. ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_interactive_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: drive the body into a colour-8 cell and my manual predicts it stays put, and the world contradicts that in one command if 8 is walkable. C=2 to C=5 is three lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Six commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained, and in this action family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition."
    [probe: pending]

  theorem the_first_step_east_costs_forty_eight_pixels_and_that_is_not_a_defect "Priced in advance so it cannot be sold to me as a surprise. The arm instances exactly the cells that have already changed, so rows 8-12 cols 20-24 -- lattice (1,3), the first cell east of spawn -- are board and have NO instance. When the body first steps there, 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels at rows 8-12 cols 14-18 are undrawable too until an east-leaves rule is witnessed, because no rule of mine turns spawn-ring Glyph9 cells from 9 to 5 on any key but 2. 48 wrong cells for the first step onto fresh ground, plus one for the burn if reading B is right, then 24 for the second step, then 0. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5. A manual that heals one step behind is the price of this arm, and the pixels it costs are the tuition, not the damage."
    [depends: the_maze_is_a_six_pixel_lattice, i_cannot_draw_the_leading_edge_burn_whichever_reading_wins  probe: pending]

  theorem the_goal_section_is_empty_on_purpose "`Cart.pos = exit_cell` needs one named instance and arc-instances: all gives me Glyph9_r8c14 and thirty-six siblings; there is no instance called Glyph9. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) never becomes dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated, indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would also be true of the body standing one cell south of spawn, which is not a win. count(Glyph9, color = 5) = 24 is true of every state where the body is anywhere but home. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. THE PRICE, PLAINLY: is_goal compiles to False, no plan terminates, and nothing ranks one command above another except whether the manual predicts pixels to move -- which at spawn today is exactly one key, ACTION2, the one key here whose rules are already at full coverage. The playbook exists to fight that gradient."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: passed]

  theorem the_cascade_length_is_a_free_channel_i_discard_by_construction "cascade_lengths are 1, 7 and 9. ACTION2 returned SEVEN frames at t2; ACTION5 returned NINE at t5; every command that changed nothing returned one. With one witness each I cannot tell whether the count belongs to the key or to the panel configuration -- both were in configuration A at the start. The net effect is what my semantics compares, so this costs nothing in replay and buys nothing in prediction, and I record it as a limitation of my own choice of `cascade single_frame`: up to eight intermediate frames per command are discarded unread. LIVE PREDICTION, free to check in the raw diff: the next ACTION2, taken from configuration B, is 7 frames if the count belongs to the key and 9 if it belongs to the panel."
    [depends: key2_body_arrives  probe: pending]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body is at spawn, the panel is in configuration B, two meter cells are burned, the next command index is 6 and it is EVEN. ACTION3 at spawn: my manual predicts ZERO cells and has NO WITNESS for that. If the body steps east, ACTION3 IS EAST and I pay 48 undrawable pixels I have already priced; if nothing moves, ACTION4 IS EAST by elimination since ACTION1 was inert here with east open. Either answer names the key. Independently, ACTION3 is an ODD key at an EVEN index, so (63,61) burning separates the two meter readings and (63,61) staying 9 separates them the other way -- one press, two questions, and both answers legible in the raw diff. ACTION4 at spawn: the same experiment with the labels swapped. ACTION5 at spawn: my manual predicts zero cells and has no witness; a step or a jump would refute the UP reading loudly, so it is the second-best press. ACTION1 at spawn: 1 cell, an identity recolour, the one silence I already have a witness for, nothing bought. ACTION2 at spawn: 48 body cells I draw correctly plus a burn I cannot draw -- one wrong pixel, nothing learned, since both its rules are already at full coverage, except the free cascade datum. IF THE PANEL MOVES ON ANY COMMAND TAKEN AT SPAWN, the guard colored(spawn_probe, 5) is wrong and thirteen rules need rewriting; that is the single observation that would most change this file."
    [depends: the_action_map_after_five_transitions, the_meter_is_a_leftward_bar_and_two_readings_still_fit_it  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on both variants -- -5042 bits with connected_components(4) unsplit, -17520 split by colour -- which is the segmenter saying its own script costs more than writing the pixels. I take its TRACK LIST and not its verdict. obj0 (colour 9, eight cells, 3x3, all six frames) and obj2 (colour 9, 1x3, all six frames) are slot 1's ring and underline 1 persisting while it narrates 2 moves and 4 recolours: it does not see the panel as appearing and vanishing, which corroborates a marker with two seats. obj1 (colour 1, nine cells, 3x3, frames 0-4) is slot 2 solid, and obj5 (colour 2, eight cells, 3x3, FIRST FRAME 5) is slot 1 after the dim -- the appear event at frame 5 is exactly key5_slot1_dims and its frame index is independent corroboration, since the segmenter has never seen my rules. obj4 is the whole 64-cell row-63 bar, of which 2 cells are dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body: connected_components(4) cannot see the mover at all, because the mover is a ring adjacent to floor on every side, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 5 transitions constrain rank 3 of 365 features, null space dimension 362 -- and its one global law is my census cell for cell. cegis_miner refuses every track and its verdict, `the world does not narrate as one mover`, is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# The manual did not compile last round, so nothing has ever been checked:
# certify's replay, responsibility and ambiguity blocks are all empty. The
# landmark comment is repaired and the first thing this round must produce
# is an EXECUTABLE manual and a real divergence report. Until that exists,
# every ranking below is a ranking of expected information, not of proof.
#
# The store holds SIX states. The inherited manual claimed thirty-four and
# the current frame refutes it (two burned meter cells, not sixteen). All
# rules now cite t1-t5 only; the beliefs that cannot be witnessed here are
# demoted to pending theorems with their prices named.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   Body at spawn, lattice (1,2). North and west void, south and east open.
#   At spawn:  key(2) -> 48 body cells, both its rules already full
#              key(1) -> nothing, WITNESSED at t1
#              key(3), key(4), key(5) -> nothing, NO WITNESS, and at least
#              one of those three silences is FALSE because east is 3 or 4.
#   Next command index is 6, EVEN: under the parity reading of the meter it
#   burns (63,61) whatever is pressed, and I cannot draw that cell.
#
# ========= THE ONE THING WORTH BUYING =========
# ONE ODD, UNTESTED KEY AT THIS CELL ANSWERS TWO QUESTIONS AT ONCE.
#   (a) DIRECTION. ACTION2 is down. ACTION1 was inert at spawn with east
#       open, so ACTION1 is not east. ACTION3 and ACTION4 were each inert
#       one cell south, where east and west are both void -- which is
#       exactly what the horizontal pair would do there. So east is ACTION3
#       or ACTION4, and pressing either names the key whichever way it
#       answers: a step means that key is east, no step means the other one
#       is east by elimination.
#   (b) THE METER. Reading A says burns follow keys 2 and 4; reading B says
#       burns follow even command indices. Both fit all five transitions
#       because every even index so far carried an even key. An ODD key at
#       the EVEN index 6 splits them in one press, and ACTION3 is odd.
#
# The advertised price of the step onto fresh ground: 48 pixels the manual
# cannot draw, because rows 8-12 cols 20-24 have never changed and are
# board, plus the departure ring which has no east-leaves rule yet. That is
# a refutation priced in advance and it must not be read as a defect.
# 24 pixels for the second step east, 0 for the third.
#
# ------------------------------------------------------------------------
# STATE 5: body home at lattice (1,2); panel in configuration B; TWO meter
# cells burned, cols 62-63 of row 63; next command index 6. Eleven lattice
# cells reachable; the body has stood in two of them. Three steps east
# along lattice row 1 reach the cell beside the knob; the knob is the far
# end of one connected colour-8 wire whose near end is the comb; the comb
# gates every route to the socket at (8,7).

order     make_the_manual_executable_before_trusting_any_other_verdict     [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong   [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one          [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                      [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                        [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 3/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    an_odd_key_at_an_even_index_while_the_meter_readings_are_tied    [ev: 0/5 commands so far]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 3/5 keys at spawn]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 5/5 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    a_press_at_a_third_cell_that_splits_up_from_return               [ev: 1/1 key5_presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

=== LOG ===
```json
[
  {"id": "E-01", "subject": "landmark spawn_probe # arc-cell: carried, coordinates stripped", "verdict": "reject",
   "why": "This is why certify returned empty replay/responsibility/ambiguity blocks: the grammar states a landmark without a real (row, col) comment is a HARD compile error, so theory.py was never generated and nothing in the inherited manual was ever checked; replaced with # arc-cell: (8, 14), the spawn-ring corner that reads 9 when the body is home and 5 otherwise."},

  {"id": "E-02", "subject": "empty `goal:` section header", "verdict": "reject",
   "why": "A section header with no indented body is not a documented legal form while 'no goal section at all' explicitly is, so it was the second compile suspect and is removed; the reason the goal stays unwritten is in the_goal_section_is_empty_on_purpose."},

  {"id": "E-03", "subject": "meter law 'burns iff the command index is even'", "verdict": "probe-pending",
   "why": "I wanted a guard on a command counter; the guard language reads pixels and the action name only and no pixel records the parity, so I wrote two key-triggered burn rules that fit t2 and t4 exactly and recorded both readings, with their one-command separator, in the_meter_is_a_leftward_bar_and_two_readings_still_fit_it."},

  {"id": "E-04", "subject": "click action carrying coordinates", "verdict": "probe-pending",
   "why": "ACTION6/ACTION7 are unpressed and one is normally a click; act=key(6) parses but has nowhere to put two coordinates, so a click rule would fire on every click anywhere, and the belief is carried as two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click instead."},

  {"id": "S-01", "subject": "store says 6 states / 5 transitions; inherited manual says 34 / 33", "verdict": "accept",
   "why": "The current frame settles it against the manual: row 63 shows two burned cells (cols 62-63) not sixteen, and the store's 73 dynamic / 4023 constant / 70 needing an owner all match the six-state history exactly, so every ev: tag was rewritten to t1-t5 and every unwitnessable inherited claim was demoted to a pending theorem."},

  {"id": "O-01", "subject": "mdl_segmenter obj0/obj2 (colour 9, 3x3 and 1x3, all 6 frames)", "verdict": "accept",
   "as": "Glyph9 (arc-instances: all)", "why": "These are slot 1's ring and underline 1; one declared type on colour 9 with per-cell instances covers them plus the spawn ring and the two burned meter cells, 37 instances, and the segmenter's persistence of both tracks across all six frames is what says the panel recolours rather than appears."},

  {"id": "O-02", "subject": "the 24 changed cells at rows 14-18 cols 14-18 (floor at frame 0)", "verdict": "accept",
   "as": "Vacated (arc-instances: all)", "why": "They are colour 5 at frame 0 and 9 after t2, so typing-by-frame-0-colour forces a separate type from Glyph9; 24 instances, exactly the lower ring minus its aperture (16,16), which never changes."},

  {"id": "O-03", "subject": "mdl_segmenter obj1 (colour 1, 9 cells, 3x3, frames 0-4)", "verdict": "accept",
   "as": "Spent (arc-instances: all)", "why": "Slot 2 solid at frame 0 including its centre (2,6), which goes to 0 at t5 while the other eight go to 9 — nine instances, and the track ending at frame 4 is the segmenter dating the toggle to t5 independently of my rules."},

  {"id": "O-04", "subject": "the 3 changed cells at row 5 cols 5-7 (background colour at frame 0)", "verdict": "accept",
   "as": "Dark (arc-instances: all)", "why": "They are colour 0 at frame 0 and 9 after t5, so no other type can carry them; accepted with a stated risk, since cells_needing_an_owner is 70 = 73 minus exactly these three, which may mean the arm refuses to instance background-coloured cells — see the_dark_type_is_the_one_declaration_i_am_not_sure_the_arm_honours."},

  {"id": "O-05", "subject": "mdl_segmenter obj5 (colour 2, 8 cells, 3x3, first_frame 5)", "verdict": "entailed",
   "why": "This is slot 1 after key5_slot1_dims recolours its eight ring pixels 9 to 2; giving it a type of its own would claim the same pixels twice, which rule 5 forbids, and its first_frame of 5 is corroboration rather than a new object."},

  {"id": "O-06", "subject": "mdl_segmenter obj4 (colour 9, 64 cells, 1x64)", "verdict": "entailed",
   "why": "The row-63 bar, of which only the two burned cells have ever changed; the other 62 are constant and therefore board, and no declaration can give them instances — which is the whole content of i_cannot_draw_the_leading_edge_burn_whichever_reading_wins."},

  {"id": "O-07", "subject": "mdl_segmenter obj3 (colour null, 1006 cells, 50x38)", "verdict": "reject",
   "why": "connected_components(4) merged the maze floor with the body ring because the mover is floor-adjacent on every side; the blob is an artefact of the operator, and its inability to isolate the mover is the finding, not a candidate object."},

  {"id": "O-08", "subject": "mdl_segmenter's own gain figures (-5042 and -17520 bits)", "verdict": "reject",
   "why": "Both variants report negative gain, i.e. the segmenter says its script costs more than the pixels; I take its track list and frame indices as corroboration and decline its verdict, and I say so rather than quoting a positive number it did not produce."},

  {"id": "R-01", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept",
   "why": "t2 is one witness at 24/24 each: 24 spawn-ring cells 9→5 whose sixth-below renders floor, 24 lower-ring cells 5→9 whose sixth-above renders 9, and the aperture cells (10,16)/(16,16) are excluded automatically because they never changed and have no instance."},

  {"id": "R-02", "subject": "key5_body_clears / key5_body_respawns", "verdict": "accept",
   "why": "t5 reverses t2 at 24/24 each; but respawns is guarded on spawn-ring pixels rather than on where the body is, which bakes in a RETURN-flavoured prediction I did not choose and have flagged in key5_is_written_as_spawn_refills_and_that_is_a_return_reading_i_did_not_choose."},

  {"id": "R-03", "subject": "the seven key(5) panel rules (slot1_dims, underline1_dims, four slot2 rules, underline2_lights)", "verdict": "accept",
   "why": "Together they draw exactly the 23 panel cells of t5 with no overlap, discriminating row and column by off-board tests whose exclusivity I checked pair by pair; the guard colored(spawn_probe, 5) has one positive (t5, body away) and one negative (t2, body away but key 2 touched no panel pixel), which is thin and said to be thin."},

  {"id": "R-04", "subject": "the six configuration-B-to-A panel rules (slot1_lights, underline1_lights, ring_resets, centre_resets, underline2_dims)", "verdict": "probe-pending",
   "why": "No transition in this store witnesses the return half of the toggle, so under constraint 2 they cannot be rules; their full text sits in the_panel_toggles_with_the_body_away_and_the_return_half_is_unwitnessed_here with the price named — 23 pixels on the first effective ACTION5 taken from configuration B."},

  {"id": "R-05", "subject": "meter_burn_key2_rightmost / meter_burn_key4_next", "verdict": "accept",
   "why": "t2 burned (63,63), the only Glyph9 instance with rightof = wall, and t4 burned (63,62), the only one whose right neighbour reads 1; both replay to the pixel, and both encode reading A only because reading B is inexpressible, not because reading A is established."},

  {"id": "R-06", "subject": "meter_burn_key2_next (inherited)", "verdict": "reject",
   "why": "Zero witnesses in this store — t2's burn was the rightmost cell and t4's was under key(4) — and zero possible future firings, since the only cell it could recolour next is (63,61), which is board and has no instance; it fails constraints 2 and 3 at the same time."},

  {"id": "R-07", "subject": "key1_inert_at_spawn / key3_inert_below_spawn", "verdict": "accept",
   "why": "Each grounds to exactly one instance in its witnessing state and recolours it to the colour it already has, so both fail the gain test and I say so; they are kept solely because they are the only mentions of key(1) and key(3) in the file, and deleting the key(3) mention would make the probe I most want unadjudicable."},

  {"id": "R-08", "subject": "cegis_miner's verdict 'the world does not narrate as one mover'", "verdict": "reject",
   "why": "True of the arm and false of the world: there is one rigid 24-pixel mover, but per-cell instancing turns each of its steps into 48 simultaneous recolours, which is precisely the shape the miner's precondition (exactly one move event per transition) refuses."},

  {"id": "L-01", "subject": "instance and board counts (37/24/9/3, board 4023, burned 2)", "verdict": "accept",
   "why": "Recomputed from this frame and cross-checked against the store three ways: 23+24+24+2 = 73 dynamic, 37+9+24 = 70 cells_needing_an_owner, 4096-73 = 4023 constant_cells."},

  {"id": "L-02", "subject": "'the world is not a function of the drawn frame' (inherited, claimed proven)", "verdict": "probe-pending",
   "why": "The proof needed a pixel-identical pair with the same action and different successors; this store's only two coincidences are s1=s0 and s3=s2, and different keys were pressed from each, so both are sterile and the claim is downgraded with the experiment that would establish it written out."},

  {"id": "L-03", "subject": "zero_space's single global law and its THIN self-report", "verdict": "entailed",
   "why": "Its law is my census cell for cell, and it says itself that 5 transitions constrain rank 3 of 365 features, leaving a 362-dimensional null space of unfalsified correlations — so it adds nothing and warns against being read as adding anything."},

  {"id": "P-01", "subject": "press ACTION3 from spawn", "verdict": "probe-pending",
   "why": "The only command that closes two questions at once: it names the east key whichever way it answers (a step means ACTION3 is east, no step means ACTION4 is east by elimination, since ACTION1 was inert here with east open), and being an odd key at even index 6 it separates the two meter readings by whether (63,61) burns."},

  {"id": "P-02", "subject": "press ACTION5 at spawn", "verdict": "probe-pending",
   "why": "Second-best: my manual predicts zero cells here and has no witness for that in this store, and because key5_body_respawns is guarded on pixels rather than position, any movement at all would immediately separate the UP and RETURN readings."},

  {"id": "P-03", "subject": "press ACTION2 at spawn again", "verdict": "reject",
   "why": "Both its rules are already at full coverage, it costs a burn I cannot draw, and it returns the body to the one other cell it has ever occupied; the only thing it buys is the free cascade-length datum, which does not justify the command."}
]
```
```
