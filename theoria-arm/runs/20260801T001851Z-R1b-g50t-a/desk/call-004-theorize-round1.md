# call-004-theorize-round1

model: `claude-opus-5` · 755423 ms · $1.961036 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 38245, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 38245, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 38245, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 38245, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 62014, "type": "message"}], "output_tokens": 62014, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "distinct_states": 10,
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
- t8   ACTION1   frames=1   state=NOT_FINISHED (63,60) 9->1
- t9   ACTION3   frames=1   state=NOT_FINISHED no cells changed
- t10  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-59, [5, 9] -> [1, 5, 9]
- t11  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t12  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-58, [5, 9] -> [1, 5, 9]
- t13  ACTION4   frames=1   state=NOT_FINISHED no cells changed

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
  "candidates": 8,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 3,
   "move": 6,
   "recolor": 13,
   "vanish": 3
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
   }
  ],
  "variants": [
   {
    "baseline_bits": 6680,
    "compression_ratio": 1.243862,
    "events": 25,
    "gain_bits": -1629,
    "ms": 30,
    "script_bits": 8309,
    "split_by_color": false,
    "tracks": 8
   },
   {
    "baseline_bits": 6680,
    "compression_ratio": 7.296707,
    "events": 63,
    "gain_bits": -42062,
    "ms": 51,
    "script_bits": 48742,
    "split_by_color": true,
    "tracks": 32
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
  "distinct_states": 10,
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
     "c9
```

The full proposal stream is 1139 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 10 states / 9 transitions
# (RESET, then A1 A2 A3 A4 A5 A2 A5 A1 A3, one command each).
# 75 cells have ever changed; this manual names and owns all 75.
#
# ================= WHAT HAPPENED SINCE THE LAST MANUAL =================
#
# 0. MY LAST REPLY WAS NOT REFUSED BY THE GRAMMAR. The refusal reads
#    `the reply carried no === THEORY === block; emit all three blocks`.
#    That is a harness-level formatting failure on my side, not a parse
#    error: the manual that WAS compiled replayed 5/5 with 0 unexplained
#    cells and 0 clashes. Three blocks are emitted this time.
#
# 1. FOUR NEW TRANSITIONS ARRIVED AND TWO OF THEM REFUTED ME OUTRIGHT.
#    t6 A2: 49 cells, rows 8-63 cols 14-61 -- the 48 body cells I draw
#           correctly, plus a meter burn at (63,61) I could not draw.
#    t7 A5: 71 cells, rows 1-18 -- the 48 body cells I draw correctly,
#           plus THE PANEL TOGGLING BACK, 23 cells I had no rule for.
#    t8 A1: 1 cell, (63,60) 9->1. A METER BURN UNDER ACTION1.
#    t9 A3: 0 cells, at spawn.
#    Both probe_refutations are answered by construction, not by excuse:
#    the 23 return-half panel cells now have five rules (t7 witnesses
#    them), and the two new meter cells are now dynamic, so instances
#    exist and rules can finally draw them. I expect 9/9 replay.
#
# 2. ACTION1 BURNED A METER CELL AT t8 AND DID NOT AT t1. That single
#    fact kills reading A of the meter (burns follow keys 2 and 4) and
#    confirms reading B EXACTLY: burns happen on EVEN command indices,
#    4/4 of them, and never on odd, 5/5. See the_meter_is_a_two_command
#    _clock. The guard language cannot count commands, so my burn rules
#    are knowingly mis-attributed to keys; they replay all four burns and
#    predict nothing, and I say so rather than dressing them up.
#
# 3. ACTION3 IS INERT AT SPAWN (t9), WHERE EAST IS OPEN. With ACTION1
#    inert at spawn twice (t1, t8), ACTION2 down and ACTION5 up-or-home,
#    ACTION4 IS THE LAST CANDIDATE FOR EAST and is the only key never
#    pressed from the cell the body stands on. That is the whole of the
#    playbook's first line.

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
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6 cov: 48/48]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6 cov: 48/48]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_edge_key2 forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_next_key2 forall ?p in Glyph9 [ev: t6 cov: 1/1]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key4 forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key1 forall ?p in Glyph9 [ev: t8 cov: 1/1]
    when act=key(1) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3,t9 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7 cov: 48/48]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7 cov: 48/48]
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
  invariant glyph9_instances count(Glyph9) = 39 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4021 [status: counted]

  theorem dynamic_census "Exactly 75 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels at rows 1-3 cols 1-3, its centre (2,2) being colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in configuration A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 4 are the burned right end of row 63, cols 60 to 63 -- two more than last round, at (63,61) under t6 and (63,60) under t8. 23+24+24+4 = 75 = dynamic_cells. By frame-0 colour: 39 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 4 meter), 9 colour-1 (slot 2, solid at frame 0), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 39+9+24 = 72 = cells_needing_an_owner EXACTLY, which is the store telling me again that it does not count background-coloured cells as needing an owner; Dark carries the remaining 3 anyway and t5 and t7 both prove the arm does instance them, because key5_underline2_lights and key5_underline2_dims are the only rules that can touch row 5 cols 5-7 and last round's replay was exact. 4096-75 = 4021 = constant_cells exactly."
    [probe: passed]

  theorem the_dark_type_is_honoured_after_all "Last round I flagged Dark, declared on the background colour, as the one declaration I was not sure the arm would instance, and named the exact price: three pixels at row 5 cols 5-7 missing from t5. Replay came back 5/5 with zero unexplained cells, so the arm does instance background-coloured cells that vary. The doubt is discharged and I record the discharge rather than quietly deleting the doubt."
    [depends: key5_underline2_lights, dynamic_census  probe: passed]

  theorem the_goal_is_absent_because_no_instance_can_name_the_socket "I decline to declare a goal and here is the argument, with the price. The winning position I believe in is lattice cell (8,7), rows 50-54 cols 44-48, whose 24 ring pixels are floor and whose centre (52,46) is a colour-9 pip inside a three-sided colour-9 bracket -- a plug and a socket drawn to the pixel. Four forms of goal are available and every one of them is refuted. (1) Cart.pos = exit_cell needs ONE named instance; arc-instances: all gives me Glyph9_r8c14 and thirty-eight siblings and there is no instance called Glyph9, and a second colour-9 type would be indistinguishable to an arm that looks objects up by colour alone, which is the constraint-5 double claim. (2) count over the socket interior has nothing to range over: those cells have never changed, so they are board and carry no instances. (3) count(Vacated, color = 9) = 24 is TRUE of the body standing one cell south of spawn, a state I have already seen four times; when the body first enters any new floor cell those 24 cells also become Vacated and the count still reads 24, so no threshold on it ever names the socket. (4) count(Glyph9, color = 9) = 11 is false in all ten observed states and is therefore admissible by the letter of the rider -- and it is satisfied by pressing ACTION2 once from where the body stands right now, because it means nothing more than the body is off spawn in panel configuration A with all four instanced meter cells burned. A goal that a planner satisfies with its first move is worse than no goal, and the rider says so. THE PRICE I AM PAYING: is_goal compiles to False, plan returns no_goal_declared, commit never runs, and every command remains a probe -- one turn and nine actions so far. THE OBSERVATION THAT ENDS THIS: the first frame in which any pixel of the bracket rows 49-55 cols 43-49, or the pip (52,46), changes colour. Those cells become dynamic that instant, get instances, and a count over them becomes writable and false everywhere before it. Until then I am exploring, and the playbook now says out loud that I am exploring."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem the_meter_is_a_two_command_clock "SETTLED, and it was settled by ACTION1. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right. Four cells are burned and the command indices are 2, 4, 6, 8 -- every even index, no odd index, 4 out of 4 and 5 out of 5. Reading A of last round (burns follow keys 2 and 4) predicted no burn at t8 under ACTION1 and no burn at t2 versus t1 distinction; t8 burned (63,60) under ACTION1 and t1 under the same key at the same cell burned nothing. READING A IS DEAD. The meter is a clock that ticks once every two commands, and it does not care which key. Consequences I accept: 60 cells remain, so about 120 commands remain before the bar is spent, which is a budget and not an emergency; and the next command, index 10, is EVEN and will burn (63,59)."
    [depends: meter_burn_next_key1  probe: passed]

  theorem the_burn_rules_are_deliberate_mis_attributions_kept_only_for_replay "Constraint 3 and constraint 6 both apply and I would rather be caught saying this than caught implying otherwise. My four burn rules are keyed on act=key(1), key(2) and key(4) because THE GUARD LANGUAGE HAS NO COMMAND COUNTER and no pixel of the frame records the parity, so the true law cannot be written here at all. They replay all four burns exactly -- t2 by rightof = wall, t4, t6 and t8 by a colour-1 right neighbour -- and that is the whole of their value. They are wrong about the mechanism, and they were saved from being caught by an accident I want on the record: the only odd-index press of a key they name was ACTION1 at index 1, when nothing was yet burned, so no cell had a colour-1 right neighbour and the rule correctly did not fire. THE TIME BOMB, NAMED IN ADVANCE: once (63,59) burns and becomes dynamic, an instance exists for it, and the first ODD-index press of key 1, 2 or 4 after that moment will make my manual predict a burn the world will not deliver -- exactly one wrong pixel, at the bar's leading edge, and it is my mis-attribution and not a new mechanism."
    [depends: the_meter_is_a_two_command_clock  probe: pending]

  theorem i_cannot_draw_the_leading_edge_burn "A law of this manual rather than of this world, and it has now been paid twice. The arm instances exactly the cells that have ALREADY changed, so the next cell to burn is board, has no instance, and NO RULE OF MINE CAN RECOLOUR IT. That is precisely why probe P-01 refuted the manual at t6: I drew the 48 body cells correctly and missed (63,61), which was board at the time. It is now dynamic, so t6 replays whole. The same will happen at index 10 with (63,59). CONSEQUENCE FOR READING REFUTATIONS: a divergence set consisting only of the bar's leading edge does not implicate this manual and must not be allowed to consume a round. A divergence set containing anything else does."
    [depends: the_meter_is_a_two_command_clock  probe: passed]

  theorem the_world_is_probably_not_a_function_of_the_drawn_frame "Now nearly forced rather than merely possible. The bar shows floor(index/2) burned cells, so a frame with b burns is consistent with index 2b and with index 2b+1, and those two differ in whether the NEXT command burns. Concretely: s0 and s1 are pixel-identical (ACTION1 at t1 changed nothing) and both show zero burns, yet the command taken from s1 burned and the command taken from s0 did not; s2 and s3 are pixel-identical and both show one burn, and the command from s3 burned while the command from s2 did not. WHAT STOPS THIS BEING A PROOF is that in each pair the two commands were different keys, so a frame-function that distinguishes keys is not yet contradicted. THE DIRECT WITNESS COSTS TWO COMMANDS: press the same inert key twice in a row from the current cell -- ACTION3 twice, say -- and the pixel-identical predecessor states will have received identical actions with different successors, one burning and one not. Constraint 5 obliges my manual to be a function of the frame, so it will be wrong about one member of that pair by exactly one pixel, and that pixel is the leading edge I cannot draw anyway. I record the prediction and rank the experiment low precisely because its cost and its lesson are already priced."
    [depends: the_meter_is_a_two_command_clock  probe: pending]

  theorem the_panel_is_a_two_slot_selector_toggled_by_action5 "BOTH DIRECTIONS ARE NOW WITNESSED and this is the round's largest repair. t5 turned 23 panel cells from configuration A to B while the body returned north; t7 turned the same 23 back from B to A, again while the body returned north. A: slot 1's ring reads 9 with underline 1 reading 9, slot 2 reads solid 1 with underline 2 reading 0. B: slot 1's ring reads 2 with underline 1 reading 0, slot 2 reads a ring of 9 with its centre hollowed to 0 and underline 2 reading 9. The current frame is A, re-read pixel by pixel. THE READING: two slots, an underline under each, and the underlined slot is also the one rendered in colour 9 -- a two-item selector whose cursor ACTION5 advances, wrapping after two. The unselected slot reverts to its own colour, 2 for slot 1 and 1 for slot 2, and slot 2's centre fills in when it is unselected, so the two glyphs are a hollow square and a solid square, the hollow one being the shape of the body itself. WHAT I DO NOT CLAIM: what the selection selects. ACTION2 moved the body down identically from configuration A at t2 and from configuration B at t6, so the selector does NOT remap ACTION2, which is the only cross-configuration comparison this store contains. Return-half rules were absent last round and I named their price as exactly 23 pixels on the first effective ACTION5 from configuration B; that bill arrived at t7 as probe P-02 and it is now paid with five rules, key5_slot1_lights, key5_underline1_lights, key5_slot2_ring_resets, key5_slot2_centre_resets and key5_underline2_dims, each guarded by colour alone because colours 2, 0 and 9 occur nowhere else in their types."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, key5_underline2_dims  probe: passed]

  theorem the_spawn_probe_guard_is_the_untested_half_of_thirteen_rules "Every panel rule carries colored(spawn_probe, 5), which reads the body is not at home. Both witnesses had the body one cell south, so the guard has never been tested with the body home: ACTION5 has never been pressed at spawn in this store. If the panel toggles anyway, thirteen rules are guarded on the wrong thing and my manual under-predicts 23 pixels on that command; if nothing happens, the guard survives and the manual is right that ACTION5 at spawn is inert. Either way the answer arrives in one press and it is the second-ranked probe. Note the asymmetry that makes this cheap: my manual currently predicts ZERO cells for ACTION5 at spawn, so any change at all is legible."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: pending]

  theorem the_action_map_after_nine_transitions "WITNESSED, with the negatives stated as negatives. ACTION2 IS DOWN: t2 and t6, the 5x5 body block from rows 8-12 to rows 14-18, exactly six rows, one lattice cell, twice. ACTION5 CARRIES THE BODY NORTH: t5 and t7, the reverse, twice, each time with the panel toggle. NEGATIVES. At spawn (1,2) north and west are void while south and east are open floor; ACTION1 did nothing there at t1 AND at t8, and ACTION3 did nothing there at t9 -- so NEITHER ACTION1 NOR ACTION3 IS EAST and neither is south. At (2,2) north and south are open while east and west are void; ACTION3 at t3 and ACTION4 at t4 each did nothing -- so neither is up and neither is down. Combine: ACTION3 is neither vertical nor east, which leaves west, and west is void at both cells it was pressed from, which explains all three of its silences without inventing anything. ACTION4 IS THE ONLY REMAINING CANDIDATE FOR EAST AND HAS NEVER BEEN PRESSED WHERE EAST IS OPEN. If ACTION4 also does nothing at spawn then NO KEY IS EAST, movement in this world is vertical only, and the map theorem below is wrong about what a lattice is -- that is a big finding cheaply bought, which is why the probe is ranked first whichever way it answers. The residue I cannot resolve: ACTION1 is consistent with up, and so is ACTION5, and two up keys is a smell. ACTION1 has only ever been pressed at spawn where up is void, so one press of ACTION1 from (2,2) separates them."
    [depends: key2_body_arrives, key5_body_respawns  probe: pending]

  theorem action5_is_up_or_home_or_undo_and_two_presses_separate_them "Both ACTION5 witnesses moved the body from (2,2) to (1,2), a move that up, return-home and undo-last-move all predict identically, so this store cannot separate them and I will not pretend it can. The separator is cheap and I write it as a shape, not as a route: reach any cell TWO lattice steps from spawn and press ACTION5 once. Up predicts one step back; home predicts a jump of two cells, 48 pixels I cannot draw; undo predicts one step back along the arrival direction, which differs from up as soon as the last step was horizontal. My rules encode neither reading -- key5_body_respawns is guarded on PIXELS, a Glyph9 cell rendering 5 whose neighbour above renders 5, so it is a spawn-ring refill rule and nothing more. As written it fires from ANY state where the spawn ring reads floor, so from a third cell my manual predicts the body is DRAWN AT SPAWN WITHOUT BEING ERASED where it stood: two bodies, 24 wrong pixels, priced here in advance so it cannot be sold to me later as a new mechanism."
    [depends: key5_body_respawns, the_action_map_after_nine_transitions  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2 plus a one-row fragment at row 48 cols 42-50 that cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in ten frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it is at spawn now. THIS THEOREM IS HOSTAGE TO THE EAST PROBE: if ACTION4 does not move the body east from spawn, then no horizontal move exists, the lattice is a column and not a grid, and the reachability argument below collapses to a line."
    [depends: key2_body_arrives, the_action_map_after_nine_transitions  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed four times now: (16,16) stayed 5 at t2 and t6 while its 24 neighbours turned 9, and (10,16) did the same in reverse at t5 and t7. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows, cols 43 and 49 separator columns -- so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side left as floor. Inside it, rows 50-54 cols 44-48 are floor except the lone colour-9 pixel at the exact centre (52,46). Overlay the body standing there -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel. The bracket has never changed, so it is board and no object owns it; the first time any of it changes, those cells become dynamic and the goal section can finally be written."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem at (12,40), colour 8 filling col 40 from row 12 to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18 with floor gaps only at (39,14) and (41,14). ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in ten frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_interactive_thing_within_reach "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains nine colour-8 ring pixels, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: drive the body into a colour-8 cell and my manual predicts it stays put, and the world contradicts that in one command if 8 is walkable. C=2 to C=5 is three lattice cells of eastward travel and C=2 to C=6 is four. Ten commands spent and none has taken step one, because the east key is still unnamed."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained, and in this action family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition."
    [probe: pending]

  theorem the_first_step_east_costs_forty_eight_pixels_and_that_is_not_a_defect "Priced in advance so it cannot be sold to me as a surprise. The arm instances exactly the cells that have already changed, so rows 8-12 cols 20-24 -- lattice (1,3), the first cell east of spawn -- are board and have NO instance. When the body first steps there, 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels at rows 8-12 cols 14-18 are undrawable too until an east-leaves rule is witnessed, because no rule of mine turns spawn-ring Glyph9 cells from 9 to 5 on any key but 2. 48 wrong cells for the first step onto fresh ground, plus one for the leading-edge burn at index 10, then 24 for the second step, then 0. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated everywhere else -- because typing is by frame-0 colour and all that floor was 5. A manual that heals one step behind is the price of this arm, and the pixels it costs are the tuition, not the damage."
    [depends: the_maze_is_a_six_pixel_lattice, i_cannot_draw_the_leading_edge_burn  probe: pending]

  theorem silence_is_a_prediction_and_two_of_my_five_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the five keys at the cell the body stands on. key(1): inert, WITNESSED twice, t1 and t8, apart from the t8 burn. key(2): moves 48 body cells, witnessed twice, both rules at full coverage. key(3): inert, WITNESSED once, t9. key(4): NO WITNESS AT THIS CELL -- pressed once ever, from one cell south, where east and west are void. key(5): NO WITNESS AT THIS CELL -- never pressed at spawn at all. So two of five silences at spawn are forged death certificates, down from three, and one of the two is the last surviving candidate for east. That is the largest remaining block of unearned confidence in this file and it is the cheapest to fix: one press each."
    [depends: the_action_map_after_nine_transitions, the_spawn_probe_guard_is_the_untested_half_of_thirteen_rules  probe: pending]

  theorem the_cascade_length_is_a_free_channel_and_it_just_paid_out "Last round I predicted, free to check in the raw diff, that the next ACTION2 taken from configuration B would return 7 frames if the cascade count belongs to the key and 9 if it belongs to the panel. It returned NINE. So the count is not a function of the key alone: ACTION2 gave 7 frames from configuration A at t2 and 9 from configuration B at t6, while ACTION5 gave 9 both times and every no-op gave 1. Something outside the key -- the panel configuration is the candidate with a witness -- lengthens the animation. This is hidden state I discard by construction, since cascade single_frame compares only net effect, and it corroborates the_world_is_probably_not_a_function_of_the_drawn_frame from a second direction. It costs nothing in replay and buys nothing in prediction; I keep reading it because it is free."
    [depends: the_panel_is_a_two_slot_selector_toggled_by_action5  probe: passed]

  theorem the_no_op_rule_fails_the_gain_test_and_i_keep_it_for_a_narrow_reason "key3_inert_below_spawn recolours one pixel to the colour it already has, has two witnesses on transitions where zero cells changed, and replay is identical without it. It explains no pixel and lengthens the manual, so it fails constraint 3 and I say so rather than dressing it up. The reason I keep it: it is the ONLY occurrence of act=key(3) in the file, and deleting it narrows the action set certify adjudicates from five keys to four. Its counterpart key1_inert_at_spawn is DELETED this round, because meter_burn_next_key1 now mentions key(1) with a real witness at t8 and does real work, so the placeholder is redundant on both counts."
    [depends: key3_inert_below_spawn, meter_burn_next_key1  probe: passed]

  theorem the_rules_are_pairwise_exclusive_and_off_board_cell_terms_are_false "Constraint 5, checked by hand over all four instance types in both panel configurations. Under key(2): body_leaves needs below-six to render 5, off-board for any row past 57, so it cannot fire on a meter cell; the two burn rules split on rightof = wall against a colour test on rightof, which cannot both hold. Under key(5) the type Glyph9 is split five ways by COLOUR FIRST -- 5 for respawns, 9 for the two dim rules, 2 for slot1_lights, 0 for underline1_lights -- and colours 2 and 0 occur on no other Glyph9 cell in any observed state, so the return half needs no geometry at all. The two colour-9 rules are then split by above-four: slot1_dims needs it to BE WALL, true only for rows 0-3; underline1_dims needs a COLOUR TEST on it, which is false off-board rather than raising, so it selects row 5 and excludes rows 0-3, and its above-six wall test excludes the meter at row 63. Spent splits by colour into 1 (the five configuration-A rules) against 9 and 0 (the two configuration-B rules); within colour 1 the geometry is row 1 by above-two wall, row 3 by a colour test on above-two, row 2 by above-three wall plus a colour test on above-one, and within row 2 col 5 by leftof-six wall, col 6 by leftof-seven wall plus a colour test on leftof-one, col 7 by a colour test on leftof-two -- each pair separated by the same off-board-is-false trick, which is the load-bearing fact of this whole file. Dark splits by colour 0 against 9. Not one rule uses not, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens, key5_slot1_lights  probe: pending]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body is at spawn, the panel is in configuration A, four meter cells are burned at row 63 cols 60-63, and the next command index is 10, which is EVEN, so under the clock it burns (63,59) whatever is pressed and I cannot draw that cell. ACTION4 at spawn, my first choice: my manual predicts ZERO cells and has NO WITNESS for that silence. If the body steps east I pay 48 undrawable pixels already priced, and EAST IS ACTION4; if nothing moves beyond the burn, NO KEY IS EAST and the lattice is a column, which rewrites four theorems. ACTION5 at spawn, my second choice: my manual predicts ZERO cells; a panel toggle refutes the spawn_probe guard on thirteen rules, a body jump refutes the up reading of ACTION5, and nothing at all confirms both. ACTION1 at spawn: 0 cells plus a burn I cannot draw, one witnessed silence repeated, nothing bought. ACTION2 at spawn: 48 body cells I draw correctly plus the undrawable burn, and both its rules are already at full coverage, so it buys only the cascade datum. ACTION3 at spawn: 0 cells, witnessed at t9, nothing bought. THE SINGLE OBSERVATION THAT WOULD MOST CHANGE THIS FILE: any panel pixel moving on a command taken while the body is HOME, because that falsifies the guard on thirteen rules at once."
    [depends: the_action_map_after_nine_transitions, the_meter_is_a_two_command_clock  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on both variants, -3623 bits unsplit and -27437 split by colour, which is the segmenter saying its own script costs more than writing the pixels. I take its TRACK LIST and not its verdict. obj0 (colour 9, eight cells, 3x3, all ten frames) and obj2 (colour 9, 1x3, all ten frames) are slot 1's ring and underline 1 persisting through both toggles, so it does not see the panel as appearing and vanishing, which corroborates a marker with two seats rather than two objects. obj1 (colour 1, nine cells, 3x3, frames 0-4) is slot 2 solid in configuration A; obj5 (colour 2, eight cells, FIRST FRAME 5, present 2 frames) is slot 1 after the dim, and its appearance at frame 5 and disappearance by frame 7 is exactly key5_slot1_dims followed by key5_slot1_lights, dated independently by an engine that has never seen my rules; obj6 (colour 1, nine cells, FIRST FRAME 7, present 3 frames) is slot 2 solid again after the return. THAT IS THE ROUND'S CORROBORATION AND IT ARRIVED FROM OUTSIDE. obj4 is the whole 64-cell row-63 bar, of which 4 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body: connected_components(4) cannot see the mover, because the mover is a ring adjacent to floor on every side, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 9 transitions constrain rank 5 of 375 features, null space dimension 370 -- and its one global law is my census cell for cell, 75 cells, which is a consistency check and not a discovery. cegis_miner refuses every track and its verdict, the world does not narrate as one mover, is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Ten states, nine transitions. The manual compiles and replayed 5/5 last
# round with zero unexplained cells; the two refutations that brought me
# back are both repaired IN THE MANUAL, not here: the 23 panel cells of
# t7 now have five return rules, and the two new meter cells are dynamic
# so their burns can finally be drawn. I expect 9/9 this round, and if it
# is not 9/9 the defect is mine and legible.
#
# ========= THERE IS STILL NO GOAL, AND I HAVE SAID WHY IN THE MANUAL =========
# theorem the_goal_is_absent_because_no_instance_can_name_the_socket gives
# the argument and the price: is_goal is False, plan returns
# no_goal_declared, commit never runs, and EVERY COMMAND THIS LEG IS A
# PROBE. That is now a stated position rather than a silence, and the
# ranking below is a ranking of expected information, which is the only
# currency available while the goal section is empty. The observation
# that ends it: the first colour change anywhere in the socket bracket,
# rows 49-55 cols 43-49, or its pip at (52,46).
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   Body at spawn, lattice (1,2). North and west void, south and east open.
#   Panel in configuration A. Meter: 4 cells burned, cols 60-63 of row 63.
#   At spawn:  key(2) -> 48 body cells, both rules already at full coverage
#              key(1) -> nothing, WITNESSED twice, t1 and t8
#              key(3) -> nothing, WITNESSED once, t9
#              key(4) -> UNWITNESSED HERE, and the last candidate for east
#              key(5) -> UNWITNESSED HERE, and the only test of the guard
#                        colored(spawn_probe, 5) that thirteen rules share
#   The meter is a clock, one cell per two commands, 60 cells left. Index
#   10 is EVEN and burns (63,59) whatever is pressed; that cell is board,
#   has no instance, and no rule of mine can draw it. Discount it.
#
# ========= THE ONE THING WORTH BUYING =========
# ACTION4 AT SPAWN. It is the only key never pressed from this cell whose
# answer names a direction either way. ACTION2 is down; ACTION5 carries
# the body north; ACTION1 was inert here twice and ACTION3 once, with
# east open the whole time, so neither is east; ACTION3 and ACTION4 were
# both inert one cell south where east and west are void, which is what
# the horizontal pair would do there. So east is ACTION4 or east does not
# exist. A step east means the road to the knob is open and costs 48
# undrawable pixels I have priced in the manual. No step means NO KEY IS
# EAST, movement is vertical only, and four theorems get rewritten -- a
# bigger finding than the step, bought for the same one command.
#
# SECOND: ACTION5 AT SPAWN. My manual predicts zero cells. A panel toggle
# there falsifies the spawn_probe guard on thirteen rules at once, which
# is the single observation that would most change the file; a body jump
# falsifies the up reading of ACTION5; nothing at all confirms both.
#
# ------------------------------------------------------------------------
# STATE 9: body home at lattice (1,2); panel configuration A; four meter
# cells burned; next command index 10. Eleven lattice cells reachable and
# the body has stood in two. Three steps east along lattice row 1 reach
# the cell beside the knob; the knob is the far end of one connected
# colour-8 wire whose near end is the comb; the comb gates every route to
# the socket at (8,7).

order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     treat_the_first_socket_pixel_that_moves_as_the_goal_writing_event [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one          [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     spend_the_clock_on_unwitnessed_key_cell_pairs_not_on_repeats     [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong   [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     probes_the_meter_parity_that_nine_transitions_already_settled => dead [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic rules_whose_shared_guard_a_single_command_would_falsify           [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                        [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 2/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 1/1 candidates left]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 2/5 keys at spawn]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 9/9 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    a_press_at_a_third_cell_that_splits_up_from_home_from_undo       [ev: 2/2 key5_presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

## Why you are being called: the surprises that fired

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "e59713974b62ec16",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 24 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted 'b90a6233898771e2' against the world's '882c12b1cc465224'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.544 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 2,
 "expected_bits": 0.5435644432,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "b90a6233898771e2",
 "n_hypotheses": 24,
 "n_survivors": 0,
 "observed": "882c12b1cc465224",
 "probe_id": "P-05",
 "vacuous_streak": 1
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 24 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '15c2e5de8c8dc96b' against the world's '0c56717accb832fb'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.995 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 5,
 "expected_bits": 0.994984828186,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "15c2e5de8c8dc96b",
 "n_hypotheses": 24,
 "n_survivors": 0,
 "observed": "0c56717accb832fb",
 "probe_id": "P-06",
 "vacuous_streak": 2
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 24 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '287dc66cc4b95e77' against the world's '30332fff54b4924c'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.544 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 2,
 "expected_bits": 0.5435644432,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "287dc66cc4b95e77",
 "n_hypotheses": 24,
 "n_survivors": 0,
 "observed": "30332fff54b4924c",
 "probe_id": "P-07",
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
  "actions": 5,
  "cap_reached": false,
  "clashes": [],
  "detail": "no (state, action) among 10 x 5 admitted two rules, and all 50 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 50,
  "pairs_nominal": 50,
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

## The manual has no goal section, and that has a price

This is not a complaint and not a request to invent one. It is a number you have not been shown.

The manual as it stands declares no `goal` clause. `is_goal` therefore compiles to `False` everywhere, so the planner cannot succeed on any input: every `plan` beat this leg has returned `no_goal_declared` without entering either rung of the ladder. So far that is 6 turn(s) and at least 10 action(s) spent with no target. The world has moved since the last time this was asked: 8 distinct states are now on record (the bar is 4 new ones).

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

=== PLAYBOOK ===
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

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl obj0, obj2 (colour 9, 3x3 and 1x3, present all 14 frames)", "verdict": "entailed",
   "as": "Glyph9 instances at rows 1-3 cols 1-3 and row 5 cols 1-3",
   "why": "the segmenter keeps them alive across all three toggles rather than killing and rebirthing them, which is what a marker with two seats looks like and not what two objects look like; no new type is warranted."},

  {"id": "O-02", "subject": "mdl obj7 (colour 2, eight cells, first_frame 11, present 3 frames)", "verdict": "entailed",
   "as": "slot 1 dimmed by key5_slot1_dims at t11",
   "why": "its birth frame is exactly my third toggle transition and it is still alive in the current frame, which is an independent dating of key5_slot1_dims by an engine that has never seen my rules; obj5's window 5-7 dates the first toggle pair the same way."},

  {"id": "O-03", "subject": "mdl obj3 (1006 cells, colour null, shape 50x38)", "verdict": "reject",
   "why": "connected_components(4) merged the maze floor with the mover because the body is a ring adjacent to floor on every side; accepting it would put 1006 cells under one type that moves as 24, and the merge itself is the finding, recorded in what_the_engines_gave_me."},

  {"id": "O-04", "subject": "mdl obj4 (colour 9, 1x64, row 63)", "verdict": "entailed",
   "as": "the meter bar, of which cols 58-63 are dynamic Glyph9 instances",
   "why": "the other 58 cells have never changed, so the arm gives them no instances and they remain board; the count 6 matches dynamic_cells 77 minus the 71 panel-and-ring cells exactly."},

  {"id": "R-01", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept",
   "why": "t10 and t12 are the third and fourth witnesses, 24/24 cells each, in both panel configurations; coverage lines updated and nothing about the rules changed."},

  {"id": "R-02", "subject": "a generalised down-move over Vacated (body leaves rows 14-18 on key 2)", "verdict": "probe-pending",
   "why": "I believe it and I refuse to write it: constraint 2 forbids a rule with no witnessing transition, and ACTION2 has never once been pressed from anywhere but spawn. It is carried as the_down_key_may_be_a_shuttle_and_one_press_settles_it with the exact 48-pixel price of being right and the exact five theorems that die if it is wrong."},

  {"id": "R-03", "subject": "meter_burn_next_key4", "verdict": "accept",
   "why": "kept with a dated failure attached: t13 (ACTION4, odd index, no burn) will start mispredicting one pixel at (63,57) the moment command 14 makes that cell dynamic. I checked the two escapes -- a panel-configuration guard separates t4 from t13 but is a two-point curve fit that would break on the first odd key-4 press in configuration A, and deletion costs six real replayed pixels now to save one later. Named rather than patched."},

  {"id": "R-04", "subject": "key5 panel rules (all 13)", "verdict": "accept",
   "why": "t11 gives every A-to-B rule a second witness with identical cell counts; the B-to-A half still rests on t7 alone and the shared colored(spawn_probe, 5) guard still has zero tests with the body home."},

  {"id": "L-01", "subject": "the_meter_is_a_two_command_clock", "verdict": "accept",
   "why": "burns at commands 2,4,6,8,10,12 and nowhere else -- 6/6 even and 7/7 odd, across four different keys, with ACTION4 burning at 4 and silent at 13 as the cleanest single pair."},

  {"id": "L-02", "subject": "the_state_model_predicted_the_duplicate_count", "verdict": "accept",
   "why": "my three-component state model forces s0=s1, s2=s3, s8=s9, s12=s13 and no other coincidence, hence 10 distinct states out of 14; the store reports distinct_states = 10, a number I did not fit and could not have hit while missing a mechanism."},

  {"id": "L-03", "subject": "the_world_is_not_a_function_of_the_drawn_frame", "verdict": "probe-pending",
   "why": "s12 and s13 are pixel-identical and ACTION4 from s12 changed nothing, so ACTION4 now (command 14, even) must burn and would prove hidden state in one command. Ranked LOW on purpose: constraint 5 already forces my manual to be wrong about one member of that pair, and the pixel in question is the leading edge I cannot draw regardless."},

  {"id": "L-04", "subject": "the_goal_is_absent_because_no_instance_can_name_the_socket", "verdict": "accept",
   "why": "restated and sharpened rather than repeated: I enumerated the four writable forms again against 14 states and every one is either true in an observed state or arbitrary, and the real obstacle is named as REACH -- the socket cells are board because the body has not left a two-cell corridor since command 2. This is the rider's option 2, and the playbook now says the goal is downstream of the ACTION2 probe."},

  {"id": "P-01", "subject": "probe_refutation P-05, P-06, P-07 (three vacuous frontiers, 0.0 bits each)", "verdict": "probe-pending",
   "why": "answered by a change of reading, not a change of rules: every hypothesis in the frontier is the manual or an ablation of it, so all of them die together whenever the world touches a cell no rule can express, and the meter's leading edge is exactly that cell on every even command. P-05 and P-07 were commands 10 and 12, both burning. P-06 was command 11, which does not burn, and I attribute it to a predecessor already one pixel stale from P-05. I mark this pending because I am given hashes and not divergence sets; the census and the distinct-state count are what actually carry the claim that no mechanism is missing."},

  {"id": "P-02", "subject": "the next command", "verdict": "probe-pending",
   "why": "ACTION2 from lattice (2,2). It is the only unpressed key-cell pair whose answer is decisive either way: a step to (3,2) makes the maze real, puts the body in a third cell for the first time in twelve commands, and opens the east test next; no step makes this a two-cell rocker and demolishes five theorems. My manual predicts zero cells and has no witness for that silence."},

  {"id": "P-03", "subject": "ACTION4 where east is open", "verdict": "probe-pending",
   "why": "still unbought after fourteen commands. t13 spent ACTION4 at (2,2), where east and west are both void, so its silence there carries no information about direction; the pairs that matter are ACTION4 at spawn or at (3,2)."},

  {"id": "P-04", "subject": "ACTION6 and ACTION7", "verdict": "probe-pending",
   "why": "two of seven actions have never been pressed once. The panel is a selector whose selection provably changes nothing for ACTION2 (four cross-configuration witnesses) or ACTION4 (two), so if it selects anything it selects for a key not yet tried."},

  {"id": "E-01", "subject": "command-index parity, which the meter actually depends on", "verdict": "probe-pending",
   "why": "wanted a guard like act_index mod 2 = 0. The guard language has no counter and I proved the parity is not recoverable from the frame either: burn count b at the start of command k is floor((k-1)/2), so b is identical for the burning and non-burning member of every pair, and b's own parity separates neither. Wrote four key-attributed burn rules that replay all six burns and predict nothing, plus a theorem saying so and dating their first failure."},

  {"id": "E-02", "subject": "drawing the meter cell that is about to burn", "verdict": "reject",
   "why": "wanted any construction that gives an instance to a cell before its first change. arc-instances: all covers only cells the board cannot explain, and a landmark is a cell rather than an object so no event can recolour it. There is no such construction; recorded in i_cannot_draw_the_leading_edge_burn and it is the whole cause of the three vacuous probes."},

  {"id": "E-03", "subject": "a goal naming lattice cell (8,7)", "verdict": "reject",
   "why": "wanted goal Body.pos = socket_cell. arc-instances: all yields forty-one Glyph9 instances and no instance called Glyph9; a second colour-9 type is indistinguishable to an arm that looks objects up by colour alone; and the socket cells are board with nothing to count. Wrote the rider's theorem instead, with the exact observation (any pixel of rows 49-55 cols 43-49, or (52,46), changing) that makes a goal writable."},

  {"id": "E-04", "subject": "a click action's coordinates", "verdict": "probe-pending",
   "why": "wanted act=click(row, col). The language admits act=key(6) but has nowhere to put two coordinates, so any click rule would fire on every click anywhere. Carried as two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap: I can record a click's effect and never its precondition."}
]
```
```
