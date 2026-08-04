# call-004-theorize-round2

model: `claude-opus-5` · 805632 ms · $2.890231 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 111536, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 111536, "cache_read_input_tokens": 47471, "inference_geo": "not_available", "input_tokens": 4, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 64065, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 64065, "cache_read_input_tokens": 47471, "input_tokens": 2, "output_tokens": 4646, "type": "message"}], "output_tokens": 68646, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 73,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4020,
 "distinct_states": 9,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 76,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 11,
 "steps": 11
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
9999999999999999999999999999999999999999999999999999999999911111
```

## Every command, and what changed

`t` indexes the state sequence. `frames` is how many grids one command returned -- more than one means the world took several internal steps for a single action.

- t0   RESET     frames=1   state=NOT_FINISHED (first frame)
- t1   ACTION1   frames=1   state=NOT_FINISHED no cells changed
- t2   ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-63, [5, 9] -> [1, 5, 9]
- t3   ACTION3   frames=1   state=NOT_FINISHED no cells changed
- t4   ACTION4   frames=1   state=NOT_FINISHED (63,62) 9->1
- t5   ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t6   ACTION5   frames=1   state=NOT_FINISHED (63,61) 9->1
- t7   ACTION2   frames=9   state=NOT_FINISHED 48 cells changed, rows 8-18, cols 14-18, [5, 9] -> [5, 9]
- t8   ACTION5   frames=9   state=NOT_FINISHED 72 cells changed, rows 1-63, cols 1-60, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t9   ACTION2   frames=7   state=NOT_FINISHED 48 cells changed, rows 8-18, cols 14-18, [5, 9] -> [5, 9]
- t10  ACTION5   frames=9   state=NOT_FINISHED 72 cells changed, rows 1-63, cols 1-59, [0, 1, 5, 9] -> [0, 1, 2, 5, 9]

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 10,
  "n_states": 11,
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
    "transitions": 10
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
    "transitions": 10
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
   "recolor": 11,
   "vanish": 3
  },
  "n_frames": 11,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 11,
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
    "frames_present": 11,
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
    "frames_present": 11,
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
    "frames_present": 11,
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
    "frames_present": 3,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj5"
   },
   {
    "color": 1,
    "first_frame": 8,
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
    "first_frame": 10,
    "frames_present": 1,
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
    "baseline_bits": 5872,
    "compression_ratio": 1.375851,
    "events": 23,
    "gain_bits": -2207,
    "ms": 26,
    "script_bits": 8079,
    "split_by_color": false,
    "tracks": 8
   },
   {
    "baseline_bits": 5872,
    "compression_ratio": 7.296662,
    "events": 55,
    "gain_bits": -36974,
    "ms": 44,
    "script_bits": 42846,
    "split_by_color": true,
    "tracks": 29
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 76,
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
  "cells_needing_an_owner": 73,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4020,
  "distinct_states": 9,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 76,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 11,
  "steps": 11
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 76,
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
  "cells_dynamic": 76,
  "cells_used": 76,
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
   "constrained_fraction": 0.018421,
   "difference_rank": 7,
   "features": 380,
   "space_dimension": 373,
   "transitions": 10,
   "verdict": "THIN: 10 transitions constrain rank 7 of 380 features, so the null space has dimension 373 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 380,
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
     "c9@27",
     "c0@28",
     "c1@28",
 
```

The full proposal stream is 1126 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 7 states / 6 transitions.
#   t0 RESET, t1 A1, t2 A2, t3 A3, t4 A4, t5 A5, t6 A5.
# 74 cells have ever changed; this manual names and owns all 74.
#
# THE LOG RESTARTED. Last round's brief carried 26 states and twelve burned
# meter cells. This brief carries SEVEN states and three. Same level -- knob at
# rows 9-11 cols 39-41, comb at rows 38-42 cols 14-18, socket at rows 49-55
# cols 43-49, all re-read pixel by pixel below -- but the episode is new and
# the meter is refilled. I re-cite every rule against the six transitions that
# actually exist, and where a rule's only witnesses are pre-RESET I say so in
# the ev field instead of pretending otherwise.
#
# 1. I WAS REFUTED AND THE EDIT IS REVERTED. Last round I deleted
#    colored(spawn_probe, 5) -- "the body is not at home" -- from thirteen
#    panel rules, on the ground that it had eleven positive witnesses and zero
#    negative ones and therefore explained no pixel. I wrote, in advance and in
#    both books, exactly what would refute me: ACTION5 pressed at spawn
#    changing nothing. t6 IS THAT PRESS. It changed ONE cell, (63,61), and not
#    one of the 23 panel cells. THE GUARD IS REAL AND IT IS BACK IN ALL
#    THIRTEEN RULES. It now has a negative witness and is no longer a
#    transcription of where presses happened to occur.
#    I do not regret the experiment. A conjunct with no negative witness is a
#    hypothesis; the deletion was the cheapest way to test it; it cost one
#    command and returned a decisive answer in one press. The procedure was
#    right and the belief was wrong, which is the good case.
#
# 2. THE BIGGER PRIZE, BOUGHT BY THE SAME PRESS. t6 is ACTION5 and it BURNED A
#    METER CELL. Reading A -- "a burn happens iff the key is 2 or 4" -- is
#    DEAD. Reading B survives untouched: burns at indices 2, 4, 6 (all even),
#    no burn at 1, 3, 5 (all odd), and pre-RESET the same pattern held for 25
#    transitions. THE METER IS A TWO-COMMAND TIMER, NOT A COST OF PARTICULAR
#    KEYS. Six rounds of loop could never split these two because the loop
#    pinned key-2-ness and even-ness to the same predicate; one press of key 5
#    at an even index split them. This is the first fact about this world that
#    the last thirty commands could not have told me.
#    CONSEQUENCE FOR EVERY PLAN: no command is free. Every command costs half a
#    meter cell whatever it does. 61 cells remain, so about 122 commands.
#
# 3. THE PRICE OF (2). The timer is command PARITY and this grammar has no
#    command counter and no phase pixel, so I CANNOT WRITE IT. What I write
#    instead is meter_burn_key5_at_home, a position guard that fits t5 and t6
#    and replays them exactly, and which I state here to be a PROXY for a law I
#    cannot express. It is witnessed and it is not the law. See
#    the_meter_is_a_two_command_timer_and_the_guard_language_cannot_say_so.
#
# 4. THE LOOP IS FORCED AGAIN AND I AM NOT GOING TO FORGE A WAY OUT. With the
#    guard restored, at spawn only key 2 has a live rule and at lattice (2,2)
#    only key 5 does. That is the same fixed point as before. Last round I
#    found a lever; it turned out to be a real law and pushing it was refuted.
#    I have looked for another and there is none: keys 3, 4, 6, 7 have no rule
#    to un-guard, and inventing one has zero witnesses of any kind.
#
# EXPECTED REPLAY: 6/6.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t6 compress: 38]
  Vacated [segment: dynamic_colour_5 ev: t2-t6 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5-t6 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5-t6 compress: 3]

events:
  event recolored(o, c)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: pre_reset cov: 10/10]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key5_at_home forall ?p in Glyph9 [ev: t6 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 9) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

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

  rule key5_slot1_lights forall ?p in Glyph9 [ev: pre_reset cov: 40/40]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: pre_reset cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: pre_reset cov: 40/40]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: pre_reset cov: 5/5]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: pre_reset cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 38 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: inferred-from-replay]
  invariant board_cells count(board) = 4022 [status: counted]
  invariant meter_cells_burned_right_now count(Glyph9, color = 1) = 3 [status: state-dependent-not-an-invariant]

  theorem the_guard_i_deleted_was_real_and_t6_is_the_witness "THE REFUTATION OF THIS ROUND, AND IT IS MINE. Last round I removed colored(spawn_probe, 5) from thirteen panel rules, arguing that a conjunct with eleven positive witnesses and zero negative witnesses explains no pixel and therefore fails constraint 3. I wrote the refutation condition in advance, in both books: if ACTION5 at spawn changes nothing, the guard was real, I am refuted by 23 cells, and it goes back. t6 IS EXACTLY THAT PRESS -- ACTION5, body at home, panel in configuration B -- AND IT CHANGED ONE CELL, (63,61), WHICH IS NOT A PANEL CELL. My edited manual predicted 23 panel pixels; the world moved none of them. THE GUARD IS RESTORED IN ALL THIRTEEN RULES and now carries one negative witness, which is what it never had. WHAT I TAKE FROM THIS, STATED SO A LATER DESK DOES NOT OVERCORRECT: an unwitnessed conjunct is a HYPOTHESIS, not a fabrication, and deleting it is a legitimate and cheap EXPERIMENT -- but it is an experiment, so it must be priced as one and reverted the moment it loses. It lost in a single press and it bought two facts for that press: the guard is a law, and the meter is not keyed to key 2. That is a good trade and I would make it again. What I will NOT now conclude is that every unwitnessed conjunct is real; I conclude only that this one is."
    [depends: key5_slot1_dims, key5_slot2_ring_resets  probe: passed]

  theorem the_meter_is_a_two_command_timer_and_the_guard_language_cannot_say_so "THE FINDING OF THIS ROUND AND THE FIRST NEW FACT ABOUT THE WORLD IN SIX ROUNDS. Two readings of row 63 have been live since the beginning. READING A: a burn happens iff the key is 2 or 4. READING B: iff the command index is even. Every earlier command was drawn from a loop that pressed key 2 at even indices and key 5 at odd ones, so the two predicates were the SAME predicate and 25 transitions could not separate them. t6 SEPARATES THEM: it is ACTION5, index 6, and it burned (63,61). READING A IS DEAD. Reading B is 6/6 in this episode -- burns at 2, 4, 6 under keys 2, 4, 5; no burn at 1, 3, 5 under keys 1, 3, 5 -- and 25/25 pre-RESET. THE METER IS A TIMER THAT SPENDS ONE CELL EVERY TWO COMMANDS REGARDLESS OF WHAT THE COMMAND IS. THE PRICE: I cannot write it. The guard language reads pixels and the action name; there is no command counter and no pixel whose value tracks parity -- I checked the panel, which flips only on some ACTION5 presses, and the body position, which correlates with neither. What I write instead is meter_burn_key5_at_home, whose guard colored(spawn_probe, 9) separates t6 from t5 by BODY POSITION because that is the only expressible thing that separates them. I DECLARE IT A PROXY. It replays t5 and t6 exactly and it is not the law. Its falsifier is any press of key 5 at spawn at an ODD index: the proxy says burn, the timer says no burn. That falsifier is available at index 7, right now. Note also that the proxy costs me nothing forward, because all three meter instances render 1 and (63,60) is a board cell holding no instance, so no burn rule can ground until the world burns it first."
    [depends: meter_burn_key5_at_home, the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: passed]

  theorem no_command_is_free_any_more_and_that_reprices_every_plan "The direct corollary of the timer, and it overturns a line that stood in the playbook for five rounds. Under reading A, ACTION5, ACTION1 and ACTION3 were free and only keys 2 and 4 spent the budget, so the playbook ranked a free probe above a paid one. UNDER THE TIMER EVERY COMMAND COSTS HALF A METER CELL, INCLUDING THE ONES THAT CHANGE NOTHING AT ALL. t1 and t3 changed nothing and still consumed half a cell each. So the only ranking criterion left is information per command, and a command that returns a known answer is now strictly a loss rather than a wash. 3 cells are burned, 61 remain, which is about 122 commands before row 63 is fully colour 1. What happens at exhaustion is not in evidence and I will not guess."
    [depends: the_meter_is_a_two_command_timer_and_the_guard_language_cannot_say_so  probe: passed]

  theorem the_episode_restarted_and_reset_refills_the_meter "Recorded because it changes what a RESET is worth. The previous brief carried 26 states and twelve burned meter cells; this brief carries 7 states and three, and the frame layout is identical pixel for pixel -- the knob at rows 9-11 columns 39-41, the stem and wire on column 40, the comb at rows 38-42 columns 14-18, the socket bracket at rows 49-55 columns 43-49 with the pip at (52,46). So the level did not change; the episode did. TWO CONSEQUENCES. FIRST, RESET REFILLS THE TIMER: everything the old episode spent came back. Since the old episode had reached exactly two lattice cells in 25 commands, a RESET costs almost nothing here and buys back a large budget -- that is a real option and I record it rather than assuming resets are pure loss. SECOND, MY EVIDENCE BASE IS SIX TRANSITIONS, NOT TWENTY-FIVE. I have re-cited every rule against t1 through t6. Five reverse panel rules have NO witness in this episode -- the panel has flipped once, A to B, and never back -- so they carry ev: pre_reset, meaning I saw them five times in a log that is no longer in the brief. I keep them because they are replay-safe here (they cannot ground on any of these six transitions) and because withdrawing a rule I watched fire five times would be a worse error than citing where I watched it. One press of ACTION5 from lattice (2,2) re-witnesses all five."
    [depends: the_guard_i_deleted_was_real_and_t6_is_the_witness  probe: pending]

  theorem dynamic_census "Exactly 74 cells have ever changed in this episode and every one has an owner. 23 are the panel: slot 1 at rows 1-3 columns 1-3 gives its 8 ring pixels, its centre (2,2) rendering colour 0 in BOTH configurations and therefore board; underline 1 is row 5 columns 1-3; slot 2 at rows 1-3 columns 5-7 gives all NINE cells, centre included, because (2,6) renders 1 in configuration A and 0 in B; underline 2 is row 5 columns 5-7. 24 are the spawn ring, rows 8-12 columns 14-18 minus the aperture (10,16), which has never changed. 24 are the same ring six rows south, rows 14-18 columns 14-18 minus its aperture (16,16). 3 are the burned right end of row 63, columns 61 through 63. 23+24+24+3 = 74 = dynamic_cells exactly, and 4096-74 = 4022 = constant_cells exactly, and zero_space's single global law lists precisely these cells and nothing more. By frame-0 colour: 38 colour-9 being 8 slot-1 ring plus 3 underline-1 plus 24 spawn ring plus 3 meter, 9 colour-1 being slot 2 solid in configuration A, 24 colour-5 being the lower ring which was floor at frame 0, and 3 colour-0 being underline 2 dark at frame 0. 38+9+24 = 71 = cells_needing_an_owner exactly."
    [probe: passed]

  theorem dark_may_have_no_instances "The one arithmetic gap in the census and I will not hide it. cells_needing_an_owner is 71 while dynamic_cells is 74, and the difference is precisely the three colour-0 cells of underline 2. Colour 0 is the background, and whether a dynamic cell whose frame-0 colour is the background gets seated is not something the brief settles. The indirect evidence satisfies me: t5 changed 71 cells, of which three are underline 2 going 0 to 9, and key5_underline2_lights is the only rule that draws them; if Dark seated no instances, t5 would replay wrong by three cells. certify last round reported the replay exact over a window containing t5."
    [depends: dynamic_census  probe: passed]

  theorem the_loop_is_forced_again_and_i_have_no_honest_lever "The mechanism, restated with the guard back in. The probe tier scores expected bits over the manual and its ablations plus inert; an ablation DELETES rules, so it predicts a subset of the manual's changes and never a superset; therefore on any state-action pair where the manual predicts IDENTITY all 34 hypotheses agree and the expected gain is zero. A MANUAL CANNOT PROBE ITS OWN SILENCES. Audit the current state, body at spawn, panel B: key 2 fires key2_body_leaves and key2_body_arrives, 48 pixels, LIVE. key 5 fires nothing -- the panel rules are guarded off by spawn_probe, key5_body_clears needs a Vacated at 9 and the lower ring renders 5, key5_body_respawns needs a Glyph9 at 5 and none renders 5, and meter_burn_key5_at_home needs a Glyph9 at 9 with a right neighbour at 1, which (63,60) cannot supply because it is board. Keys 1, 3, 4, 6, 7 fire nothing. SO KEY 2 IS AGAIN THE ONLY LIVE KEY AT SPAWN, and at lattice (2,2) key 5 is again the only live key, and the two-command cycle is again forced. Last round I found a lever and it was a real law, so pushing it lost. I have looked for another and there is none: keys 3, 4, 6 and 7 have no rule to un-guard, and the only remaining guarded silence, key3_inert_below_spawn's spawn_probe conjunct, guards a rule that recolours a pixel to the colour it already has, so removing it changes no successor and buys no expected bits. I state plainly that I cannot break this from my desk with an honest edit."
    [depends: the_guard_i_deleted_was_real_and_t6_is_the_witness, silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged  probe: pending]

  theorem the_burn_frontier_is_a_permanent_one_pixel_blind_spot "Row 63 is a 64-cell colour-9 bar that burns one cell at a time from the right. THREE cells are burned in this episode -- (63,63) at index 2, (63,62) at 4, (63,61) at 6 -- and the current frame shows columns 61-63 rendering 1 and 0-60 rendering 9. The fourth burn will land on (63,60). (63,60) has never changed in seven frames, so it is board, so it holds no instance, so NO EVENT IN THIS LANGUAGE CAN TOUCH IT -- recolored takes an object as its first argument and there is no object there. Therefore my manual predicts, and must predict, that the next burn does not happen, and the world will burn it and the manual will be wrong by exactly one pixel; then (63,60) becomes dynamic, the arm seats a Glyph9 on it, replay draws the burn retroactively, and the cycle repeats on (63,59). THAT IS WHY certify SAYS THE REPLAY IS EXACT WHILE THE PROBE DESK SAYS THE MANUAL WAS WRONG: replay looks backwards through a census that already contains the burned cell, prediction looks forwards through one that cannot. All four burn rules are ungroundable right now for exactly this reason."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "The permanent shape of every refutation this level produces, and it bit three times again this round: the burn frontier, the refused goal, and the 24 cells of lattice (3,2) that make the loudest forged silence undrawable. To draw the next burn, or the first step onto fresh ground, or the socket, or to COUNT the comb, I would need an instance on a board cell. The arm offers one lever, arc-instances all, and its documented behaviour is to instance every cell of that colour THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains. I re-reject the two workarounds. A second declared type on colour 9 without arc-instances is indistinguishable from Glyph9, because the arm looks types up by colour alone, and any cell it landed on would be claimed twice. Dropping the board declaration instances roughly two thousand colour-0 cells and one thousand colour-5 cells, needs a fresh pairwise ambiguity audit against all of them in one round, and breaks concretely: key2_body_leaves would ground on the socket bracket at (49,49), whose sixth-below (55,49) renders 5, and would recolour a wall on every ACTION2. SO THE MANUAL HEALS ONE STEP BEHIND THE WORLD, PERMANENTLY, and the correct way to read a refutation here is by its divergence set: where that set lies on cells that had never changed before the transition, the manual is not implicated."
    [depends: dynamic_census, the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: passed]

  theorem the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease "My answer to heuristic_miss, which has now fired eight times, re-checked against this episode's counts rather than repeated. The surprise says declaring the winning condition is the highest-value edit available. IT IS NOT, FOR AN ARITHMETIC REASON. The plan tier reaches a goal by searching MY compiled rules. Enumerate what they can do: key2_body_leaves and key2_body_arrives move the body from spawn to one lattice cell south, key5_body_clears and key5_body_respawns move it back, the panel rules toggle 23 panel pixels, the four burn rules are ungroundable. THAT IS THE ENTIRE REACHABLE SET: TWO LATTICE CELLS BY TWO PANEL CONFIGURATIONS, FOUR STATES. So the only goal that could ever return sat is one satisfied inside that set, and sat-inside-the-loop is strictly WORSE than unsat -- unsat leaves the arm probing, sat makes it commit and declare success one lattice cell from where it started. Every candidate the grammar admits, re-checked: count(Glyph9, color = 5) = 24 and count(Vacated, color = 9) = 24 both say only that the body is off spawn; count(Dark, color = 9) = 3 says only that the panel is in configuration B; count(Glyph9, color = 1) = 64 exceeds the 38 instances that exist and can never be true; count(Glyph9, color = 1) = 38 would require the spawn ring and both panel groups to burn, which no rule can do; count(Spent) = 0 is constant-false because Spent always has 9 instances. THEREFORE I DECLINE THE GOAL SECTION AGAIN AND I NAME WHAT WOULD END THE DECLINING: one observation in which the body occupies a THIRD lattice cell. That seats instances on 24 cells that have never changed, extends the transition model past the loop, and is the same observation that eventually makes the socket writable. THE GOAL IS BOUGHT WITH A COMMAND; NO EDIT CAN SUBSTITUTE."
    [depends: the_goal_i_still_cannot_write_is_the_real_one, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_goal_i_still_cannot_write_is_the_real_one "The win is the body standing in lattice (8,7), rows 50-54 columns 44-48, its 24 ring pixels rendering 9 and its aperture showing the pip at (52,46). Re-verified against the current frame. Those 24 cells render constant colour 5, so they are board and hold no instance; and colour 5 is already claimed by Vacated while the arm looks types up by colour alone, so a second colour-5 type would be indistinguishable from Vacated and would claim cells twice, which is the constraint-5 error. The goal I could write over Vacated once the socket goes dynamic, count(Vacated, color = 9) = 24, is already true whenever the body stands in lattice (2,2), so it names two states and one of them is not a win. So the manual carries the true winning condition in prose, here and in the playbook, and carries NO goal line at all. That is a stated gap, not an evasion."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 columns 43-49, row 55 columns 43-49, column 49 rows 49-55. Rows 49 and 55 are separator rows and columns 43 and 49 are separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side at column 43 left as FLOOR for rows 50-54. Inside it, rows 50-54 columns 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, column 50 rows 49-56 is a one-cell strip of floor leading nowhere. Overlay the body standing in lattice (8,7), a 5x5 ring with an aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate: the game is won when the 24 ring pixels of rows 50-54 columns 44-48 render 9. The bracket has never changed, so it is board and no object owns it; the first time the body enters, those 24 cells become dynamic and a real goal line becomes writable."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2), (1,3), (1,4), (1,5), (2,2), (2,4), (3,2), (3,3), (3,4), (4,2), (5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 columns 39-41, a stem pixel at (12,40), colour 8 filling column 40 from row 12 down to row 40, colour 8 filling row 40 from column 14 to column 40, and the comb teeth at rows 38-42 columns 14-18 holding 23 colour-8 pixels with floor at (39,14) and (41,14). It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has changed in seven frames, and nothing in the candidate stream proposes anything about colour 8. The first colour-8 pixel that changes turns this theorem into physics AND makes a goal line writable in the same instant."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 columns 32-36, is fully open floor and is separated from the knob's cell (1,6) at columns 38-42 only by separator column 37, which renders floor through rows 8-12. Lattice (1,6) contains ten colour-8 pixels, nine of them non-centre pixels of that cell, so even under the aperture rule the body cannot stand there while colour 8 is solid. Either colour 8 is walkable in one of the two panel modes, and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Thirty-one commands have been spent across two episodes and none has taken step one, because the east key is unnamed and unbuyable."
    [depends: the_socket_is_unreachable_until_the_comb_opens, the_panel_is_a_two_slot_mode_selector_and_the_mode_may_gate_terrain  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2 through 6R+6 by columns 6C+2 through 6C+6; rows and columns congruent to 1 modulo 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read from the CURRENT frame. Row 7 is floor from column 13 to column 43. R=1, rows 8-12, is floor from column 13 to column 43 except the knob block, so C=2,3,4,5 are open and C=6 holds the knob. R=2, rows 14-18, is floor at columns 13-19 and 25-31 only, so C=2 and C=4. R=3, rows 20-24, is floor from column 13 to column 31, so C=2,3,4. R=4 and R=5 are floor only at columns 13-19, so C=2. R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable. R=7 is C=2, plus a one-row fragment of floor at row 48 columns 42-50 that cannot hold a body. R=8, rows 50-54, is floor from column 13 to column 48, so C=2 through C=7 are open. Separator rows 7, 13, 19, 25, 31, 37, 43 and 49 are floor across column 2 and separator column 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in seven frames the body has occupied exactly TWO cells, (1,2) and (2,2)."
    [depends: the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed at t2: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) has all 24 ring pixels rendering floor and its centre (52,46) rendering colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "cascade_lengths are 1, 7 and 9. Every no-op and every pure burn returned one frame; ACTION2 at t2 returned 7 with the panel in configuration A; ACTION5 at t5 returned 9. Pre-RESET the rule held eleven times for eleven: ACTION2 from configuration A returns 7 frames, from B returns 9, and ACTION5 returns 9 always, while the NET displacement is identical in every case. So the panel changes the ANIMATION, not the distance. A move is animated one row per internal frame and the world reports the whole animation for one action; my semantics say cascade single_frame, so I compare only the net and discard up to eight intermediate frames per command, which I record as a limitation of my own semantics and not of the world. THE REFUTATION I KEEP: under a slide-until-blocked reading, ACTION2 at spawn would run the body south to the comb. It stopped after exactly six rows over open floor, at t2 and at eleven pre-RESET presses. ONE PRESS IS ONE LATTICE CELL, and every distance in the playbook rests on it."
    [depends: key2_body_arrives  probe: passed]

  theorem the_panel_is_a_two_slot_mode_selector_and_the_mode_may_gate_terrain "The reading I hold, stated as a reading, re-read pixel by pixel against the current frame. Two 3x3 tokens sit at rows 1-3 columns 1-3 and columns 5-7, with a 3-cell underline beneath each at row 5. The underline of exactly one slot is lit colour 9 at any time and ACTION5 moves the light, but ONLY when pressed with the body away from spawn -- that is this round's correction and it is what t6 taught. Configuration A lights underline 1, B lights underline 2, and neither both nor neither has ever been seen. Right now row 1 reads 222 at columns 1-3 and 999 at columns 5-7, row 2 reads 2,0,2 and 9,0,9, row 3 reads 222 and 999, row 5 reads 000 and 999: slot 1 a hollow colour-2 ring with underline 1 dark, slot 2 a hollow colour-9 ring with a dark centre and underline 2 lit. CONFIGURATION B. The token in the LIT slot is always a HOLLOW colour-9 ring with a dark centre, which is the shape of the body itself. The token in the unlit slot differs by slot: slot 1 unlit is a hollow colour-2 ring, slot 2 unlit is a SOLID colour-1 block with no aperture. So the panel says two avatars exist, this is the one you drive, and the other has a different shape -- and a solid avatar with no aperture could not show the socket pip through itself. mdl_segmenter corroborates from outside my rule set: its obj0 is a colour-9 8-cell 3x3 present in all seven frames and its obj2 is a colour-9 1x3 present in all seven, and its event table narrates two MOVES at frame 5, which is the segmenter reading the flip as the lit ring TRAVELLING from slot 1 to slot 2. THE PAYOFF IF THIS IS RIGHT IS THE WHOLE LEVEL: the sole route south is blocked by the comb, 23 of whose 25 pixels render colour 8, and if the modes differ in what terrain they cross then the comb is a mode problem and not a switch problem."
    [depends: the_cascade_is_animation_and_one_press_is_one_lattice_cell, the_guard_i_deleted_was_real_and_t6_is_the_witness  probe: pending]

  theorem action5_is_return_to_spawn_and_it_is_also_the_panel_key_only_when_away "ACTION5 has been pressed twice in this episode. t5, from lattice (2,2): the body returned to spawn and the panel flipped, 71 cells. t6, from spawn: NOTHING moved except one meter cell. Reading NORTH says ACTION5 steps one lattice cell up; reading RETURN says it sends the body home from wherever it is. t6 does not split them -- under NORTH the body would try to step into rows 2-6 columns 14-18, which render 0 and are void, so nothing moves either way -- but t6 DOES establish the new and unobvious fact that the PANEL is inert too when the body is already home. Under a pure mode-selector reading I expected the panel to toggle wherever the body stood; it does not, so the panel flip is bound to the body's return and not to the keypress. A third reading remains alive: ACTION5 swaps which of two avatars you drive and the incoming one always starts at spawn. Its memory-preserving variant is refuted -- if the swap preserved each avatar's position the incoming avatar would already be at (2,2), zero body cells would change and only 23 panel cells would move, whereas 71 changed at t5. The separator between NORTH and RETURN still needs the body two lattice cells from home, which needs the third lattice cell."
    [depends: key5_body_respawns, the_guard_i_deleted_was_real_and_t6_is_the_witness  probe: passed]

  theorem silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for what it has seen. Audit the five tried keys at spawn, where the body stands now. key(2): 48 body pixels, WITNESSED at t2. key(5): predicted identity, WITNESSED at t6 -- this is the one that changed this round and it is now the strongest silence I own, because it was bought with a press. key(1): predicted inert, WITNESSED at t1. key(3): predicted inert, NO WITNESS -- pressed once, at t3, from one lattice cell south, where east and west are both void. key(4): predicted inert, NO WITNESS -- pressed once, at t4, from one cell south, where it burned a meter cell and moved nothing. key(6), key(7): never pressed anywhere. SO THREE SPAWN SILENCES ARE FORGED, being keys 3, 4 and the untried pair. A forged silence is priced at zero expected bits by the ranker, so it is self-protecting, and unlike last round there is no guard to delete that would expose it -- keys 3, 4, 6 and 7 have no rule of their own to un-guard. The fourth and largest forgery is at the other cell and is in the_loudest_forged_silence_is_not_at_spawn."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_loop_is_forced_again_and_i_have_no_honest_lever  probe: passed]

  theorem the_loudest_forged_silence_is_not_at_spawn "The cheapest large error in this manual, unchanged by this round's reversion. Ask what my rules predict for ACTION2 pressed with the body ONE CELL SOUTH of spawn, at lattice (2,2). key2_body_leaves grounds only on Glyph9 and needs colour 9: the spawn ring renders 5 when the body is away, the three burned meter cells render 1, slot 1 renders 2 or 9 with nothing but background six rows below it, so NO GLYPH9 SATISFIES IT. key2_body_arrives grounds only on Vacated and needs colour 5: the lower ring renders 9 when the body stands there, so NO VACATED SATISFIES IT. THE COMPILED STEP IS TOTAL, SO MY MANUAL ASSERTS THAT ACTION2 AT LATTICE (2,2) DOES NOTHING. That is almost certainly false: rows 20-24 are floor from column 13 to column 31, so lattice (3,2) is open, and one press of ACTION2 has moved the body exactly one lattice cell south on twelve occasions across two episodes. I DO NOT INSTALL A RULE FOR IT. Such a rule would have ZERO witnesses of any kind -- every key-2 press ever logged was made from spawn -- and half its divergence would fall on rows 20-24 columns 14-18, twenty-four cells that have never changed and hold no instance, so I could not draw the half I believe in even if I wrote it. Deleting an unwitnessed CONJUNCT is an experiment; adding an unwitnessed RULE is manufacture. I made the first last round and lost it honestly; I still refuse the second."
    [depends: the_loop_is_forced_again_and_i_have_no_honest_lever, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "key2_body_leaves grounds on meter instances at row 63 whose sixth-below is row 69, and it must not fire there. It does not, because a colour test on an off-board cell is FALSE rather than an exception, and <cell> = wall is the sanctioned positive test. Every row and column discrimination in the eight forward panel rules is built from that one fact. The k-th above is off-board exactly when k exceeds the row, so panel row 1 is above-twice equals wall; row 3 is a colour test on above-twice, false for row 1 precisely because a colour test on an off-board cell is false; row 2 is above-three equals wall conjoined with a colour test on above-once. key5_slot1_dims needs above-four equals wall, true only in rows 0-3, so the spawn ring at rows 8-12 and the meter at row 63 can never ground it however they are coloured; key5_underline1_dims needs above-six equals wall AND a colour test on above-four, which is false for rows 1-3 because that cell is off-board, so it grounds only at row 5. The same trick separates slot 2's middle row by column: column 5 is leftof-six equals wall, column 6 is leftof-seven equals wall with a colour test on leftof-once, column 7 is a colour test on leftof-twice, and those three are pairwise exclusive. leftof-seven from column 5 is also off-board, so centre_darkens and row2_left_lights are separated NOT by that atom but by colored(leftof(?s), 1), which is false at column 5 because (2,4) is a separator rendering 0. Not one rule uses not, deliberately."
    [depends: key5_slot2_centre_darkens, key2_body_leaves  probe: passed]

  theorem the_two_directions_of_the_panel_are_separated_by_colour_alone "The five reverse rules are far shorter than the eight forward ones because configuration B assigns a UNIQUE colour to each panel group within each declared type, which configuration A does not. In B: Glyph9 renders 2 on slot 1 and 0 on underline 1, while the spawn ring renders 9 or 5 and the meter renders 9 or 1; Spent renders 9 on the slot-2 ring and 0 on its centre; Dark renders 9 on underline 2. So a bare colour test names each group exactly. THE AMBIGUITY AUDIT, redone with the spawn_probe guard restored and therefore easier than last round's: in configuration A none of the five reverse rules can fire, because no Glyph9 renders 2 or 0, no Spent renders 9 or 0 and no Dark renders 9; in configuration B none of the eight forward rules can fire, by the mirror argument. Across types: key5_body_respawns takes Glyph9 at 5, claimed by no panel rule; key5_body_clears takes Vacated at 9, and no panel rule grounds on Vacated at all; meter_burn_key5_at_home takes Glyph9 at 9 with a right neighbour at 1 and additionally requires spawn_probe at 9, which is the exact negation of the panel guard, so it is exclusive with all thirteen by that atom alone."
    [depends: key5_slot1_lights, key5_underline2_dims, the_guard_i_deleted_was_real_and_t6_is_the_witness  probe: passed]

  theorem the_burn_rules_want_one_rule_and_the_grammar_forbids_it "meter_burn_key2_rightmost and meter_burn_key2_next are ONE law -- burn the leftmost burned-adjacent colour-9 cell of the bar, where the right board edge counts as burned -- split into two rules because the guard language has and and not but no or, and rightof(?p) = wall cannot be joined to colored(rightof(?p), 1). They are exclusive rather than merely different: where rightof(?p) is off-board there is no cell to render 1, and where it is a real cell it is not wall. meter_burn_key4_next and meter_burn_key5_at_home repeat the same body under other keys, which is the second and larger duplication the missing or forces on me, and which the missing command counter forces on top of that: under the timer these four rules are ONE law with no key in it at all. The key-4 and key-5 twins of the RIGHTMOST form have no witness and can never get one now that (63,63) is burned, so they are not written. All four burn rules are ungroundable going forward, since all three meter instances render 1 and (63,60) is board; they stay because they are what makes replay correct at t2, t4 and t6."
    [depends: meter_burn_key2_rightmost, meter_burn_key5_at_home, the_meter_is_a_two_command_timer_and_the_guard_language_cannot_say_so  probe: passed]

  theorem the_two_no_op_rules_fail_the_gain_test_and_i_say_so "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has exactly one witness, and each witnesses a transition on which zero cells changed. The manual would replay identically without them: constraint 3 is failed outright and I am not dressing it up. The reason I keep them is smaller than the rule text: they put key(1) and key(3) into the manual's action alphabet, which is what certify's ambiguity check adjudicates over -- it reported 5 actions and 30 pairs, and without these two it would have reported 3. They change no prediction, so keeping them cannot cost a pixel, and they are the two cheapest deletions here if a later desk wants them gone. I checked and it did NOT save them: a rule that recolours a pixel to the colour it already has leaves the successor state identical, so it buys key 1 and key 3 no expected bits."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_parity_and_cannot_say_or "Five expressive holes, and this round the SECOND one became the expensive one. FIRST: there is no third outcome for a state-action pair -- not no change and not a named successor, but unobserved, the manual declines to predict. So the three forged spawn silences are asserted in the same voice as the witnessed ones, AND THE RANKER PRICES BOTH VOICES AT ZERO. A manual that could say I DO NOT KNOW WHAT KEY 3 DOES HERE would be a manual whose ablations disagreed on key 3, and the ranker would buy the experiment immediately. SECOND, AND NOW DEMONSTRATED RATHER THAN FEARED: the meter runs on command parity and THAT LAW CANNOT BE WRITTEN HERE AT ANY LENGTH, because the guard language reads pixels and the action name, there is no command counter, and no pixel in this world tracks parity -- I checked the panel, which flips only on some ACTION5 presses, and the body position, which correlates with neither. I wrote a position proxy instead and labelled it. THIRD: there is no or, which is why one burn law is four rules. FOURTH: there is no way to say a pixel will change without naming an object that owns it, so a manual can never predict the frontier of its own knowledge. FIFTH: a goal cannot name a cell that has never changed. Order of value to a future desk: an UNKNOWN outcome first, then instancing on constant cells, then a state counter, then or, then not."
    [depends: the_meter_is_a_two_command_timer_and_the_guard_language_cannot_say_so, the_loop_is_forced_again_and_i_have_no_honest_lever  probe: passed]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1 through ACTION5 plus RESET; the alphabet is ACTION1 through ACTION7. Two commands are entirely unconstrained after two episodes, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels changing colour, and never its precondition. Two countervailing risks, plainly: actions_used lists only what has been tried, so it is no evidence that 6 and 7 exist; and since no rule mentions them my manual predicts identity for both, so the ranker prices them at zero and will not buy them either."
    [depends: the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports 6 tracks under connected_components(4) with a NEGATIVE gain of 5035 bits, and 19 tracks with negative gain of 17896 under split-by-colour; on a seven-frame log neither variant pays for itself, so I take corroboration by frame index and nothing structural. obj1: colour 1, nine cells, 3x3, present frames 0-4 -- slot 2 solid, alive in configuration A and dead from frame 5, which dates the single panel flip to t5 and confirms it did NOT flip back at t6. obj5: colour 2, eight cells, 3x3, FIRST FRAME 5, present 2 frames -- slot 1 turning into its unlit ring at exactly the same transition. obj0 and obj2 are colour-9 groups present in all seven frames, eight cells and three cells, and the engine's event table narrates two MOVES at that transition: the segmenter, which knows nothing of my rules, reads the flip as the lit ring and its underline TRAVELLING from slot 1 to slot 2, which is independent support for the mode-selector reading. obj4 is the whole 64-cell bar of which 3 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover, because the mover is a ring of floor-adjacent pixels that merges with the floor, AND THAT ABSENCE IS THE FINDING. cegis_miner refuses every track -- transition 4 narrates vanish, transition 1 narrates recolor, object absent at frame 0 -- and its verdict that the world does not narrate as one mover is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the miner can only see 24 simultaneous recolours. zero_space self-reports THIN in its own words: 6 transitions constrain rank 4 of 370 features, null space dimension 366, nearly every vector in it a law true over these states and unfalsified rather than confirmed. Its one global law lists exactly my 74 dynamic cells."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me; the previous four editions cashed except for one clause I retracted and one edit the world refuted, which is the whole point of writing them. STATE: body at spawn, lattice (1,2); panel in configuration B; THREE meter cells burned, columns 61-63, 61 remain. THE NEXT COMMAND INDEX IS 7, WHICH IS ODD. HEADLINE: THE NEXT COMMAND WILL BE ACTION2, because with the guard restored key 2 is again the only key at spawn on which any rule of mine can fire, so it is the only action with nonzero expected bits. If it is anything else, something outside the ranker chose it and I want to know that. PER-ACTION PREDICTIONS. ACTION2 at spawn: 48 body pixels change, 24 spawn-ring cells 9 to 5 and 24 lower-ring cells 5 to 9, AND (63,60) DOES NOT BURN, because index 7 is odd. THIS IS THE SHARP ONE: my manual cannot draw a burn there either way, so if the raw diff shows 48 cells I am exactly right for the first time on a key-2 press and the timer is confirmed at an odd index; if it shows 49 with (63,60) burned, THE TIMER READING IS DEAD, the burn is keyed to the action after all, and meter_burn_key2_next was right all along. Either way the answer is legible in the raw diff and costs nothing extra, because under the timer every command costs the same half cell. ACTION5 at spawn: predicted total identity, including no burn at odd index. If (63,60) burns, my position proxy meter_burn_key5_at_home is the right shape and the timer is wrong. If the panel toggles, the guard I just restored is wrong twice over and I will have to explain t6 some other way. ACTION3 or ACTION4 at spawn: predicted identity, NO witness for either silence at this cell; if the body steps east I pay 48 pixels I have priced in advance, and I learn the east key, which is the only thing on this board that leads anywhere. ACTION1 at spawn: predicted identity, witnessed at t1. ACTION2 at lattice (2,2): predicted identity, and I expect that to be WRONG by 48 pixels with the body landing in lattice (3,2). ACTION6 or ACTION7: entirely unconstrained."
    [depends: the_meter_is_a_two_command_timer_and_the_guard_language_cannot_say_so, the_loop_is_forced_again_and_i_have_no_honest_lever, the_guard_i_deleted_was_real_and_t6_is_the_witness  probe: pending]

  theorem the_two_rounds_i_lost_were_both_lost_at_my_own_desk "Two earlier rounds were lost here: one to a goal clause counting a type with zero instances, which the compiler refused outright, and one to a reply that carried no theory block. AND IT HAPPENED AGAIN LAST ROUND -- the compiler reports the reply carried no === THEORY === block, so the manual shown to me is the one from two rounds ago and the whole round was spent on nothing. THAT IS THREE ROUNDS LOST TO FORMAT, MORE THAN I HAVE LOST TO ANY WRONG BELIEF. THE DISCIPLINE, RESTATED AND THIS TIME FIRST: emit all three blocks, in order, whole, before polishing any of them. A mediocre manual that compiles outperforms an excellent one that does not by an unbounded margin, because the mediocre one is corrected by the next frame and the excellent one is corrected by nothing. certify on the shown manual reports replay 5/5 exact, responsibility 0 of 4096 unexplained, ambiguity 0 clashes over 30 adjudicated pairs, no step crash, first_divergence null -- over a six-state window, one behind the world as usual, so it says nothing about t6, which is precisely the transition that refuted me."
    [depends: a_declaration_is_only_as_true_as_the_arm_can_seat_it  probe: passed]

  theorem a_declaration_is_only_as_true_as_the_arm_can_seat_it "Kept because it cost three rounds in three different ways. First a landmark whose arc-cell comment was missing, which is a hard compile error; spawn_probe at (8,14) was the repair and it held, and I have rewritten the coordinate explicitly this round rather than trusting a stripped comment, because the entire panel rule set now depends on that landmark resolving to the top-left cell of the spawn ring -- it renders 9 when the body is home and 5 when it is away, which is the whole content of the restored guard. Second, a type the arm could seat nowhere, where the arm accepted the DECLARATION and refused the COUNT. Third, a reply the harness could not read. THE GENERAL RULE covering all three: before writing any clause, ask what the arm will seat for it, and if the answer is nothing, the clause is not conservative, it is fatal; and before sending anything, ask whether the harness will read it at all."
    [depends: the_two_rounds_i_lost_were_both_lost_at_my_own_desk  probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# THE EPISODE RESTARTED. Seven states, six transitions:
#   RESET, A1, A2, A3, A4, A5, A5.
# BODY AT SPAWN, lattice (1,2). PANEL IN CONFIGURATION B. THREE meter cells
# burned, columns 61-63; 61 remain. NEXT COMMAND INDEX IS 7, WHICH IS ODD.
# Same level as the 26-state episode -- same knob, comb, socket, pixel for
# pixel -- but the log and the meter both restarted.
#
# ========= I WAS REFUTED, AND IT PAID =========
# Last round I deleted colored(spawn_probe,5) -- "body not at home" -- from
# thirteen panel rules, and I wrote the falsifier in advance in this book:
#   "(b) nothing changes -> the guard was real; I am refuted by 23 cells and
#    put it back."
# t6 IS THAT PRESS. ACTION5 at spawn changed ONE cell and it was not a panel
# cell. THE GUARD IS RESTORED. I am not sorry I spent the command: an
# unwitnessed conjunct is a HYPOTHESIS, deleting it was the cheapest possible
# test, and one press settled it. The procedure was right; the belief was
# wrong. That is the good case, and the general rule survives with a rider:
#   DELETING AN UNWITNESSED CONJUNCT IS AN EXPERIMENT, NOT A CORRECTION.
#   PRICE IT AS ONE AND REVERT IT THE MOMENT IT LOSES.
#
# ========= AND THE SAME PRESS BOUGHT THE BIG ONE =========
# t6 IS ACTION5 AND IT BURNED A METER CELL.
#   READING A -- "burn iff the key is 2 or 4" -- IS DEAD.
#   READING B -- "burn iff the command index is even" -- is 6/6 here and was
#   25/25 before the reset. THE METER IS A TWO-COMMAND TIMER.
# Six rounds of loop could never split these, because the loop pinned
# key-2-ness and even-ness to the same predicate. One press of key 5 at an
# even index split them. This is the first new fact about the world in six
# rounds and it came from the probe this book ranked first.
#
# ========= WHAT THE TIMER DOES TO EVERY RANKING =========
# THERE IS NO FREE PROBE ANY MORE. Every command costs half a meter cell,
# including the ones that change nothing -- t1 and t3 changed nothing and
# were charged. The line "prefer a free probe over one that costs a meter
# cell" is DELETED from this book; it was true only under a reading the world
# has now killed. The only criterion left is INFORMATION PER COMMAND, and a
# command whose answer is already known is now a strict loss, not a wash.
# 61 cells remain = about 122 commands. RESET refills them (12 burned cells
# came back at the restart), so a reset is cheap on this board -- it costs
# only position, and position has never been more than two lattice cells.
#
# ========= THE LOOP IS FORCED AGAIN AND I SAY SO =========
# With the guard back: at spawn only key 2 has a live rule; at lattice (2,2)
# only key 5 does. The ranker scores expected bits over {manual, ablations,
# inert}; an ablation only ever predicts FEWER changes; so wherever the manual
# predicts IDENTITY every hypothesis agrees and the gain is ZERO. The
# two-command cycle is therefore forced exactly as before.
# I looked for a second lever. THERE IS NONE I CAN TAKE HONESTLY: keys 3, 4,
# 6 and 7 have no rule to un-guard, and the one remaining guarded silence
# (key3's spawn_probe conjunct) guards a rule that recolours a pixel to the
# colour it already has, so removing it changes no successor and buys no bits.
# I am not going to invent a rule to break the loop. I said last round that
# adding an unwitnessed RULE is fabrication; the fact that my legitimate
# deletion lost does not make the fabrication legitimate.
#
# ========= BUT THE FORCED COMMAND IS INFORMATIVE THIS TIME =========
# INDEX 7 IS ODD. Under the timer NOTHING burns next, whatever is pressed.
# Under any surviving key-based reading, ACTION2 burns (63,60).
# So the command the ranker will take anyway -- ACTION2 at spawn -- is for
# once a real experiment, readable in the raw diff:
#   48 cells changed -> timer confirmed at an odd index.
#   49 cells changed with (63,60) burned -> timer dead, burn is keyed.
# That is the first time in six rounds that the forced move is worth its cost.
#
# ========= heuristic_miss, ANSWERED FOR THE EIGHTH TIME =========
# Declaring a goal is NOT the highest-value edit, for an arithmetic reason:
#   THE PLAN TIER REACHES A GOAL BY SEARCHING MY COMPILED RULES, AND MY RULES
#   REACH EXACTLY FOUR STATES: TWO LATTICE CELLS BY TWO PANEL CONFIGURATIONS.
# So the only goal that could return sat is one satisfied inside the loop, and
# sat-inside-the-loop is WORSE than unsat: unsat leaves the arm probing, sat
# makes it commit and declare success one lattice cell from spawn. Re-checked
# with this episode's counts: count(Glyph9,color=5)=24 and
# count(Vacated,color=9)=24 both mean only "body is off spawn";
# count(Dark,color=9)=3 means only "panel is in configuration B";
# count(Glyph9,color=1)=64 exceeds the 38 instances that exist and =38 is
# unreachable by any rule; count(Spent)=0 is constant-false.
#   THE GOAL IS NOT THE BOTTLENECK. THE MISSING TRANSITION IS.
#   ONE OBSERVATION FIXES BOTH: THE BODY IN A THIRD LATTICE CELL.
#
# THE WIN, carried in prose because the DSL cannot hold it:
#   WIN = the body stands in lattice (8,7), rows 50-54 columns 44-48, so its
#   24 ring pixels render 9 and its aperture shows the pip at (52,46). Drawn
#   as three colour-9 walls with the west side open: a socket cut to the body.
#   ROUTE = lattice column 2 is the only north-south corridor and the comb at
#   (6,2) blocks it, 23 of its 25 pixels colour 8. The comb is wired by one
#   connected colour-8 line to a 3x3 knob at lattice (1,6), reachable
#   eastward along R=1 from spawn through (1,3), (1,4), (1,5), all open floor.
#   THE EAST KEY IS STILL UNNAMED AFTER THIRTY-ONE COMMANDS.
#
# ========= THE RANKED LIST =========
# 1. ACTION3 AT SPAWN. The east key, tested where east is OPEN. A2 is south
#    (12 witnesses). A1 was pressed AT SPAWN with east open and moved nothing,
#    so A1 is not east. EAST IS A3 OR A4, no third candidate. Both were
#    pressed exactly once, from one cell south where east AND west are void,
#    so neither press could answer anything. This is step one of the only
#    route to the only switch on the board. STILL PRICED AT ZERO by the
#    ranker, and there is no conjunct to delete that would change that; I say
#    so rather than pretending otherwise.
# 2. ACTION2 AT SPAWN. Forced by the ranker, and this time worth it: at an ODD
#    index it splits the timer reading from every key-based reading, in the
#    raw diff, at the same half-cell every command costs.
# 3. ACTION2 PRESSED ONE CELL SOUTH OF SPAWN. Manual predicts NOTHING -- no
#    Glyph9 renders 9 there, no Vacated renders 5 -- and that is almost
#    certainly false: rows 20-24 are floor from column 13 to 31 and one A2
#    press has moved the body one lattice cell south twelve times running.
#    The one command likeliest to seat the body in a cell never occupied,
#    which is the observation that makes a goal writable. Not buyable with a
#    fabricated rule.
# 4. ACTION5 AT SPAWN AT AN ODD INDEX. Splits my written proxy guard
#    (position) from the timer (parity): the proxy says (63,60) burns, the
#    timer says nothing does. Cheap, but it settles bookkeeping rather than
#    the level.
# 5. ACTION6 OR ACTION7. Never pressed, entirely unconstrained. In this family
#    one is usually a click, and the knob is a 3x3 target the body appears
#    unable to stand on. My manual could record such a command's EFFECT and
#    never its precondition -- but the effect is what turns comb pixels
#    dynamic and makes a goal line writable. Honest risk: actions_used lists
#    only what has been tried, so it is no evidence these exist.
#
# ========= WHAT NOT TO PRESS =========
#   A5 from one cell south: pure loop. It re-witnesses the five reverse panel
#   rules, which is worth something, and nothing else.
#   A1 at spawn: witnessed inert at t1.
#   A4 at spawn: the same experiment as A3 with the labels swapped; press it
#   only if A3 is inert. It no longer costs more than A3 -- under the timer
#   nothing costs more than anything.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The next burn cell (63,60) is undrawable: no instance sits on a cell
#     that has never changed. A refutation whose divergence set is exactly
#     that cell implicates nothing.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on cells that have never changed, and 24 departure pixels for
#     which no rule in that direction is witnessed. 24 for the second step in
#     the same direction, 0 after that.
#   * The five reverse panel rules have NO witness in this episode and carry
#     pre-reset evidence. If the panel fails to flip back on the next ACTION5
#     from lattice (2,2), that is 23 cells against me and they come out.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.

order     revert_an_edit_in_the_round_the_world_refutes_it                  [proof: lean]
order     treat_deleting_an_unwitnessed_conjunct_as_an_experiment_to_price  [proof: lean]
order     distinguish_deleting_a_restriction_from_inventing_a_rule          [proof: lean]
order     rank_by_information_per_command_now_that_no_command_is_free       [proof: lean]
order     read_the_burn_answer_off_the_raw_diff_not_off_a_refutation        [proof: lean]
order     confirm_a_timer_reading_at_an_odd_index_while_the_window_is_open  [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition         [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
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
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     recite_every_rule_against_the_log_that_actually_exists            [proof: lean]
order     label_a_proxy_guard_as_a_proxy_wherever_the_true_law_is_unsayable [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal      [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it    [proof: lean]
order     reaudit_ambiguity_by_hand_after_any_guard_restoration             [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     action_whose_expected_bits_are_zero_only_because_the_manual_is_silent => keep [proof: lean]
prune     rule_proposed_with_zero_witnesses_of_any_kind => dead                  [proof: lean]
prune     guard_conjunct_the_world_has_since_witnessed_negatively => keep        [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead                    [proof: lean]
prune     goal_that_becomes_true_at_a_state_that_is_not_a_win => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_cells_already_visited => dead [proof: lean]
prune     divergence_lies_only_on_the_unburned_meter_frontier => dead            [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead          [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key => dead   [proof: lean]
prune     ranking_that_still_assumes_a_key_free_of_meter_cost => dead            [proof: lean]
prune     repeats_the_two_command_cycle_that_returns_the_body_to_spawn => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead        [proof: lean]
prune     no_rule_it_could_witness_can_still_ground_in_this_census => dead       [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead        [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                   [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead        [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead            [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                      [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead         [proof: lean]
prune     tests_a_direction_at_a_cell_where_that_direction_is_void => dead       [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead         [proof: lean]
prune     meter_exhausted and not goal => dead                                   [proof: lean]

heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic actions_priced_at_zero_expected_bits_by_the_manuals_own_silence   [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic rules_carrying_only_pre_reset_evidence_a_command_would_rewitness  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic meter_cells_remaining_as_a_uniform_budget_on_every_command        [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]

prefer    a_command_that_splits_the_timer_reading_from_a_key_based_one     [ev: 1/6 transitions split them]
prefer    a_command_at_an_odd_index_while_the_timer_reading_is_testable    [ev: 3/3 odd indices agree]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 2/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 2/5 keys at spawn]
prefer    a_command_that_would_put_the_body_in_a_lattice_cell_never_occupied [ev: 2/11 reachable cells seen]
prefer    a_command_that_would_turn_a_machinery_pixel_dynamic              [ev: 0/7 states]
prefer    a_command_that_leaves_the_cycle_the_manual_forces                [ev: 2/6 transitions]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 6/6 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
prefer    a_reset_over_a_stall_once_the_timer_is_nearly_spent              [ev: 1/1 resets refilled it]
```

## Why you are being called: the surprises that fired

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "b7779e7e6980c183",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '0e1cd0b30fbb12b3', the world answered '818eaaf57cafd7bb'

```json
{
 "action": 5,
 "expected_bits": 1.57235988258,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 5.129283,
 "manual_predicted": "0e1cd0b30fbb12b3",
 "n_hypotheses": 35,
 "n_survivors": 1,
 "observed": "818eaaf57cafd7bb",
 "probe_id": "P-03",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '14be221d9f8c0a5b', the world answered 'b90a6233898771e2'

```json
{
 "action": 2,
 "expected_bits": 1.918649927902,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 3.544321,
 "manual_predicted": "14be221d9f8c0a5b",
 "n_hypotheses": 35,
 "n_survivors": 3,
 "observed": "b90a6233898771e2",
 "probe_id": "P-04",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '2a3bc6a0d9bbddb4', the world answered '0c56717accb832fb'

```json
{
 "action": 5,
 "expected_bits": 2.247383253569,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 5.129283,
 "manual_predicted": "2a3bc6a0d9bbddb4",
 "n_hypotheses": 35,
 "n_survivors": 1,
 "observed": "0c56717accb832fb",
 "probe_id": "P-05",
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
  "detail": "6/6 transitions replay exactly",
  "matched": 6,
  "ok": true,
  "transitions": 6
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
  "detail": "no (state, action) among 7 x 5 admitted two rules, and all 35 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 35,
  "pairs_nominal": 35,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 7,
  "states_reconstructed": 7,
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
 2/11 reachable cells seen]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 2/5 keys at spawn]
prefer    a_command_that_leaves_the_cycle_the_manual_forces                [ev: 4/10 transitions]
prefer    a_command_that_would_turn_a_machinery_pixel_dynamic              [ev: 0/11 states]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 10/10 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    south_again_from_the_cell_already_reached_over_returning_home    [ev: 5/5 southward presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
prefer    a_reset_over_a_stall_once_the_timer_is_nearly_spent              [ev: 1/1 resets refilled it]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter obj0/obj2 (colour 9, 3x3 and 1x3, present all 11 frames)", "verdict": "accept",
   "as": "part of Glyph9 (arc-instances: all)", "why": "the engine tracks the lit slot token and its underline as single objects present in every frame while my census shows those cells recolouring between slots, so I seat them as per-cell Glyph9 instances and take the engine's travel reading only as corroboration for the mode-selector theorem."},

  {"id": "O-02", "subject": "mdl_segmenter obj1/obj6 (colour 1, nine cells, frames 0-4 and 8-9)", "verdict": "accept",
   "as": "Spent (arc-instances: all)", "why": "two tracks of the same nine cells with a gap at frames 5-7 and 10 is exactly configuration A holding and B intervening; it dates the flips to t5, t8 and t10 independently of my rules."},

  {"id": "O-03", "subject": "mdl_segmenter obj5/obj7 (colour 2, eight cells, first frames 5 and 10)", "verdict": "entailed",
   "as": "Glyph9 slot-1 ring in configuration B", "why": "colour 2 exists only in configuration B and only on slot 1; the two first-frame indices 5 and 10 match my flip history cell for cell, so it adds no new object, only a date check."},

  {"id": "O-04", "subject": "mdl_segmenter obj3 (colour null, 1006 cells, 50x38)", "verdict": "reject",
   "as": null, "why": "connected_components(4) merged the maze floor with the body ring because the ring is floor-adjacent; accepting it would give one instance for a thousand cells and lose the mover entirely — the absence of a mover track is the finding, not the track."},

  {"id": "O-05", "subject": "mdl_segmenter obj4 (colour 9, 64 cells, row 63)", "verdict": "entailed",
   "as": "5 Glyph9 instances plus 59 board cells", "why": "only columns 59-63 have ever varied; the other 59 cells are constant and belong to the board, so seating the whole bar would claim 59 cells no evidence touches."},

  {"id": "R-01", "subject": "meter_burn_key2_next", "verdict": "reject",
   "why": "t7 and t9 are ACTION2 at odd indices and neither burned; once (63,60) and (63,59) were seated the rule became groundable and fired on both, which is exactly probe P-04's one-pixel divergence — two negative witnesses, deleted."},

  {"id": "R-02", "subject": "meter_burn_key2_rightmost, meter_burn_key4_next, meter_burn_key5_at_home", "verdict": "accept",
   "why": "each fits exactly one logged burn (t2, t4, t6) with no negative witness and each is ungroundable in every state the loop can reach, so they cost no forward prediction; they are labelled proxies for the parity law in the timer theorem, with their falsifier written down."},

  {"id": "R-03", "subject": "a rule for ACTION5 burns with the body away (would cover P-03 and P-05)", "verdict": "reject",
   "why": "any such rule also grounds at t5, which is ACTION5 from the same cell at an odd index and did not burn; the repair is refuted by an existing transition before it is written, so the two divergences stand as declared permanent gaps."},

  {"id": "R-04", "subject": "key2_body_leaves, key2_body_arrives", "verdict": "accept",
   "why": "72/72 across t2, t7 and t9 — three presses, each moving 24 spawn-ring cells 9 to 5 and 24 lower-ring cells 5 to 9, with the aperture (16,16) untouched every time."},

  {"id": "R-05", "subject": "key5_body_clears, key5_body_respawns", "verdict": "accept",
   "why": "72/72 across t5, t8 and t10; all three presses were made from lattice (2,2) so they still do not separate 'north' from 'return to spawn'."},

  {"id": "R-06", "subject": "the five reverse panel rules (slot1_lights, underline1_lights, ring_resets, centre_resets, underline2_dims)", "verdict": "accept",
   "why": "they carried pre_reset evidence last round; t8 is an in-episode B-to-A flip that witnesses all five, so the ev fields now cite t8 and nothing in this manual rests on a log the brief no longer carries."},

  {"id": "R-07", "subject": "the eight forward panel rules", "verdict": "accept",
   "why": "t5 and t10 are both A-to-B flips, doubling every coverage count; the row and column discriminations are re-audited pairwise in off_board_cell_terms_evaluate_false."},

  {"id": "R-08", "subject": "key1_inert_at_spawn, key3_inert_below_spawn", "verdict": "accept",
   "why": "both fail the gain test outright — each recolours a pixel to the colour it already has — and I say so in the manual; they are kept only to hold keys 1 and 3 in the alphabet certify adjudicates over, and they are the two cheapest deletions here."},

  {"id": "R-09", "subject": "a rule for ACTION2 pressed at lattice (2,2)", "verdict": "reject",
   "why": "zero witnesses of any kind — every key-2 press ever logged was made from spawn — and half its divergence would fall on rows 20-24 columns 14-18, which have never changed and hold no instance; the forged silence is left standing and named instead."},

  {"id": "L-01", "subject": "the meter burns iff the command index is even", "verdict": "accept",
   "why": "10/10 in this episode (burns at 2,4,6,8,10; none at 1,3,5,7,9) and it survives every predicate the guard language can write — body position fails on t5 versus t10, panel fails on t2 versus t9, burn count fails because each count appears once before a burn and once before a non-burn."},

  {"id": "L-02", "subject": "one press is one lattice cell, and the panel changes only the animation", "verdict": "accept",
   "why": "ACTION2 returned 7 frames in configuration A (t2, t9) and 9 in B (t7), and all three changed the identical 48 cells in rows 8-18 — net displacement constant across frame counts, 5/5 with the ACTION5 presses."},

  {"id": "L-03", "subject": "the panel flips only when ACTION5 is pressed with the body away from spawn", "verdict": "accept",
   "why": "three positive witnesses (t5, t8, t10, all from lattice (2,2)) and one negative (t6, ACTION5 at spawn, which moved one meter cell and no panel cell); mdl_segmenter's track first-frames date the same three flips."},

  {"id": "L-04", "subject": "census: 76 dynamic cells, 40 Glyph9 / 24 Vacated / 9 Spent / 3 Dark, 4020 board", "verdict": "accept",
   "why": "23 panel plus 24 spawn ring plus 24 lower ring plus 5 meter equals dynamic_cells exactly, 40+9+24 equals cells_needing_an_owner exactly, and zero_space's single global law lists these cells including the two burned this round."},

  {"id": "L-05", "subject": "zero_space's global conservation law", "verdict": "probe-pending",
   "why": "the engine self-reports THIN — 10 transitions constrain rank 7 of 380 features, null space 373 — so I take its cell list as a census check and none of its vectors as physics."},

  {"id": "L-06", "subject": "cegis_miner's verdict that the world does not narrate as one mover", "verdict": "reject",
   "why": "true of the arm, false of the world: there is one mover, a rigid 24-pixel ring, and the miner can only see 24 simultaneous recolours, which is why it refuses every track."},

  {"id": "P-01", "subject": "ACTION2 at lattice (2,2)", "verdict": "probe-pending",
   "why": "never pressed in 41 commands though the body has stood there five times; my manual predicts identity and I expect 48 pixels with the body landing in lattice (3,2) — the one command that breaks the cycle, seats instances on fresh ground, makes a goal writable and splits ACTION5-north from ACTION5-return."},

  {"id": "P-02", "subject": "ACTION3 then ACTION4 at spawn", "verdict": "probe-pending",
   "why": "east is A3 or A4 with no third candidate (A1 was witnessed inert at spawn with east open, A2 is south); both were pressed only from a cell where east and west are void, so neither press could answer anything."},

  {"id": "P-03", "subject": "ACTION5 at spawn at an odd index", "verdict": "reject",
   "why": "this was ranked fourth last round to split the position proxy from parity; parity has now won ten times and the manual predicts identity here, so the press returns nothing and is a strict loss under the timer."},

  {"id": "P-04", "subject": "ACTION6 or ACTION7", "verdict": "probe-pending",
   "why": "never pressed; if one is a click it is the shape of interaction that presses a 3x3 knob the body cannot stand on, and my manual could record its effect even though it can never express its precondition."},

  {"id": "E-01", "subject": "the parity law of the meter", "verdict": "reject",
   "why": "I wanted 'burn one cell every second command'. The guard language reads pixels and the action name; there is no command counter and no pixel tracks parity (every cascade length observed is odd, so cumulative frames give no independent handle). I wrote three narrow single-witness proxies instead and declared them proxies."},

  {"id": "E-02", "subject": "the winning condition", "verdict": "reject",
   "why": "I wanted 'the 24 ring pixels of rows 50-54 columns 44-48 render 9'. Those cells are constant, so they are board and hold no instance, and a goal cannot name a cell that has never changed. I wrote no goal section and carried the win in prose."},

  {"id": "E-03", "subject": "the conjunctive proxy goal", "verdict": "probe-pending",
   "why": "count(Glyph9, color = 5) = 24 with count(Vacated, color = 5) = 24 is unsatisfiable inside the four-state loop and true at the win. I did not write it because I cannot verify that two goal lines conjoin, and if the compiler takes the last alone it is TRUE at spawn and the arm commits immediately. It goes in the moment either the semantics are confirmed or the body reaches a third cell."},

  {"id": "E-04", "subject": "an UNKNOWN successor", "verdict": "reject",
   "why": "the compiled step is total, so 'no rule fires' is asserted as 'nothing happens' in the same voice as a witnessed no-op; three spawn silences (keys 3, 4 and the untried pair) are forged and the ranker prices them at zero, which is why the loop is self-protecting."},

  {"id": "E-05", "subject": "the next burn at (63,58)", "verdict": "reject",
   "why": "recolored takes an object as its first argument and (63,58) has never changed, so it is board and holds no instance; the manual must predict no burn, will be wrong by one pixel, and will only be able to draw it retroactively — advertised here so that divergence implicates nothing."}
]
```
```
