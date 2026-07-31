# call-005-theorize-round1

model: `claude-opus-5` · 604437 ms · $1.630485 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 36600, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 36600, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 36600, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 36600, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 49485, "type": "message"}], "output_tokens": 49485, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
- t10  ACTION5   frames=1   state=NOT_FINISHED (63,59) 9->1
- t11  ACTION5   frames=1   state=NOT_FINISHED no cells changed
- t12  ACTION5   frames=1   state=NOT_FINISHED (63,58) 9->1
- t13  ACTION5   frames=1   state=NOT_FINISHED no cells changed

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
   "recolor": 12,
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
    "frames_present": 5,
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
    "baseline_bits": 5912,
    "compression_ratio": 1.372124,
    "events": 24,
    "gain_bits": -2200,
    "ms": 28,
    "script_bits": 8112,
    "split_by_color": false,
    "tracks": 8
   },
   {
    "baseline_bits": 5912,
    "compression_ratio": 7.317659,
    "events": 59,
    "gain_bits": -37350,
    "ms": 53,
    "script_bits": 43262,
    "split_by_color": true,
    "tracks": 31
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
     "c9@
```

The full proposal stream is 1140 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 10 states / 9 transitions
# (RESET + A1 A2 A3 A4 A5 A2 A5 A2 A5). 75 cells have ever changed; this
# manual names all 75 and now attempts to OWN all 75.
#
# WHAT HAPPENED THIS ROUND, IN ORDER OF WHAT IT COST ME:
#
#   1. THE WORLD ADVANCED BY FOUR COMMANDS AND THEY WERE THE FOUR I NEEDED.
#      t6 A2, t7 A5, t8 A2, t9 A5. Three of the five surprises are the same
#      surprise twice over: my ACTION5 rules only ran one way, and the world
#      runs ACTION5 BOTH ways.
#
#   2. MY PREDECESSOR'S BUDGET THEOREM IS DEAD. "Two tokens, one spent, one
#      remains, roughly 120 commands and one life" is REFUTED by t7: the
#      colour-1 solid block came BACK. The panel is a two-state toggle driven
#      by ACTION5, not a consumable. ACTION5 is therefore CHEAP, and every
#      ordering in the playbook that ranked branches by token cost was ranking
#      on a fiction. See the_panel_is_a_toggle_and_the_budget_theorem_is_dead.
#
#   3. I REVERSED THE STANDING REFUSAL ON THE METER AND I SAY WHY. Four
#      readings entered this round; the world killed one (phase-reset), and
#      arithmetic showed two others (frames-parity, command-parity) are the
#      SAME reading because every command returns an odd frame count. Two
#      survive, they are perfectly confounded -- and ONE OF THEM CANNOT BE
#      WRITTEN IN THIS LANGUAGE AT ALL. I wrote the writable one, on 4
#      witnesses, and I name the exact command that refutes it. See
#      the_meter_collapsed_to_two_readings_and_only_one_is_expressible.
#
#   4. I AM GAMBLING ON THREE PIXELS. (5,5),(5,6),(5,7) were declared
#      permanently unownable by two builds running. The arithmetic that
#      declared them unownable -- cells_needing_an_owner is 72, not 75 --
#      is exactly the arithmetic that says an arc-colour 0 object gets THREE
#      instances rather than three thousand. I declare `Dark` and guard its
#      two rules so that all three possible outcomes are safe. See
#      three_cells_i_am_gambling_can_be_owned_and_the_gamble_is_hedged.
#
#   5. THE PREVIOUS DESK EMITTED NO THEORY BLOCK AND THE MANUAL DID NOT
#      COMPILE. Nothing downstream ran. That is a process failure, not a
#      modelling one, and the only fix is the one I am applying: emit all
#      three blocks, every time.

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
  landmark spawn_center   # arc-cell: (10, 16)
  landmark knob_center    # arc-cell: (10, 40)
  landmark gate_center    # arc-cell: (40, 16)
  landmark socket_center  # arc-cell: (52, 46)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t9 compress: 39]
  Vacated [segment: dynamic_colour_5 ev: t2-t9 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t9 compress: 9]
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
    when act=key(5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7 cov: 8/8]
    when act=key(5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7 cov: 3/3]
    when act=key(5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7 cov: 8/8]
    when act=key(5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7 cov: 1/1]
    when act=key(5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_underline2_dims forall ?d in Dark [ev: t7 cov: 3/3]
    when act=key(5) and colored(?d, 9) and colored(above(above(?d)), 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 39 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: predicted_not_verified]
  invariant board_cells count(board) = 4021 [status: counted]

  theorem the_world_advanced_and_here_is_what_the_four_new_commands_bought "Unlike the last two rounds the store moved: 6 states became 10, 6 steps became 10, dynamic_cells 73 became 75, cells_needing_an_owner 70 became 72. The four new commands were ACTION2, ACTION5, ACTION2, ACTION5 at t6..t9, and their diffs are 49 / 71 / 49 / 71 cells. 49 = 24 body pixels leaving rows 8-12 plus 24 arriving at rows 14-18 plus one meter cell. 71 = 24 clearing rows 14-18 plus 24 respawning at rows 8-12 plus 23 panel cells, and NO meter cell. Every one of those numbers is what my movement rules already predicted; the entire cost of the round was the 23 panel cells and the 1 meter cell, and both are answered below with rules rather than with prose."
    [probe: passed]

  theorem the_panel_is_a_toggle_and_the_budget_theorem_is_dead "REFUTATION, stated first because it changes the playbook more than anything else here. The last manual read the panel as two lives: slot 1 hollow-9 in play, slot 2 solid-1 not yet issued, ACTION5 spends one, ONE TOKEN REMAINS. t7 killed it. The diff at t7 is [0,2,5,9] -> [0,1,5,9]: colour 2 vanished from the frame and colour 1 came BACK, and mdl_segmenter independently reports obj6, a 9-cell 3x3 colour-1 solid block, first seen at frame 7 and present for two frames -- the same shape as obj1, the colour-1 block of frames 0-4. t9 flipped it again. So the panel has exactly two configurations and ACTION5 swaps them. STATE A (frames 0-4, 7-8): slot 1 rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline row 5 cols 1-3 lit 9, slot 2 rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline row 5 cols 5-7 dark 0. STATE B (frames 5-6, 9, and now): slot 1 is a hollow colour-2 ring, underline 1 dark, slot 2 is a hollow colour-9 ring with its centre (2,6) dark, underline 2 lit 9. A consumable does not come back, so this is not lives; it is a two-phase indicator -- whose turn, which body, which mode -- and I do not yet know which. What it costs me to be wrong about the MEANING is nothing, because the ten rules below encode the SWAP and not the meaning. What it cost my predecessor to be wrong was the whole ordering of the search: every branch was ranked by a life it could not spend."
    [depends: key5_slot1_lights, key5_slot2_ring_resets  probe: passed]

  theorem the_meter_collapsed_to_two_readings_and_only_one_is_expressible "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right: (63,63) at t2, (63,62) at t4, (63,61) at t6, (63,60) at t8; no burn at t1, t3, t5, t7, t9. Four readings entered this round and here is the accounting. (c) PHASE-RESET-BY-RESPAWN, which predicted no burn at t6 because ACTION5 re-zeroed the phase, is REFUTED -- t6 burned. (a) FRAMES-PARITY and (b) COMMAND-PARITY are THE SAME READING and I should have seen it a round ago: every command this world has ever returned has an odd frame count (1, 7 or 9), so cumulative frames flip parity on every single command and 'cumulative frames odd' is identically 'command index even'. Cumulative frames stand at 1,2,9,10,11,20,29,38,45,54; the burns are at 9,11,29,45, all odd, all even-t. That leaves TWO live readings, 9/9 each: PARITY (burn on every second command) and ACTION-KEYED (burn iff the action is key 2 or key 4, equivalently iff the action number is even -- I cannot separate those two sub-readings either). They are perfectly confounded here because every ACTION2 landed on an even t and every ACTION5 on an odd t. Now the asymmetry that decides what I write: PARITY IS NOT EXPRESSIBLE IN THIS LANGUAGE. There is no command counter among the guards, and the meter's own drawn state does not carry the phase -- burned-count 2 occurs at t5 (no burn) and at t6 (burn), just as burned-count 0 occurred at t1 and t2 and burned-count 1 at t3 and t4. cegis_miner hit the same wall from its side: 'no literal separates transition 1 from the positives'. So my choice is not between two rules, it is between one rule and silence. Action-keying now has four positive witnesses (t2, t4, t6, t8) and five negatives, including ACTION5 pressed three times with no burn -- that is far more than the one-observation-per-action that made my predecessor refuse. I write it, I mark it as the most refutable thing in this manual, and I schedule its execution: any command that is not key 2 and not key 4, pressed at an EVEN command index, burns under parity and does not burn under action-keying. That is a free, one-bit, one-command experiment and the playbook puts it near the top."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_meter_rule_repairs_the_past_and_cannot_predict_the_future "An honest bound on what I just bought. The burn rules can only fire on cells that HAVE instances, and instances exist only for cells that have already changed, so the four burned cells (63,60)..(63,63) are drawable and (63,59) -- the next to burn -- is board and is not. On the observed transitions the rules should take replay from 1/9 towards 9/9, because at t2 (63,63) is an instance whose right neighbour is off-board, and at t4, t6, t8 the burning cell is an instance whose right neighbour already renders 1. On the NEXT command they draw nothing at all: whatever the meter does at t10 my manual leaves row 63 alone and the raw diff, not certify, is what tells me the answer. I state this so that nobody reads a rising replay score as predictive power it does not have."
    [depends: meter_burn_key2_rightmost, only_visited_cells_have_instances  probe: pending]

  theorem three_cells_i_am_gambling_can_be_owned_and_the_gamble_is_hedged "(5,5),(5,6),(5,7) -- underline 2 -- render 0 at frame 0 and 9 in state B. Two builds declared them permanently unownable on the grounds that an arc-colour 0 object would claim three thousand background cells. I think that is exactly backwards, and the evidence is the arm's own arithmetic: constant_cells 4021 + dynamic_cells 75 = 4096, while cells_needing_an_owner is 72 = 75 - 3. The arm already excludes background-coloured cells from the owner census, and it already instances only cells the BOARD CANNOT EXPLAIN -- and the board explains every constant background cell in this frame. So `object Dark # arc-colour: 0 arc-instances: all` should yield exactly three instances. I do not know that it does, so I hedged: both Dark rules carry positional guards that pin them to row 5 columns 5-7 by colour arithmetic alone -- lights requires the cell two above and the cell four above to render 1, which in state A is true only of (5,5),(5,6),(5,7), and dims requires the cell itself and the cell two above to render 9, which is true only of cells this manual has already lit. The three outcomes: THREE instances, and I gain 3 cells on every ACTION5 and the panel is complete; ZERO instances, and the two rules are dead text that draws nothing and costs nothing but their own lines, which I will then delete; THREE THOUSAND instances, and the guards keep every one of them inert except the three I want. No outcome draws a wrong pixel. This is the one place in the manual where I am testing the ARM rather than the world, and I say so."
    [depends: key5_underline2_lights, only_visited_cells_have_instances  probe: pending]

  theorem the_five_rule_decision_tree_i_previously_refused_and_now_buy "My predecessor wrote out, verbatim and correctly, the decision tree that draws slot 2's centre pixel (2,6) apart from its eight ring pixels, then refused it under rule 3: five rules to draw nine pixels is not shorter than nine pixels. That accounting was right for a ONE-OFF event and is wrong now that the panel is a recurrent toggle -- ACTION5 has been pressed three times in nine transitions and is now known to be free, so the tree is amortised over every future press, not over one. I bought it, and I re-derived it in a form that needs no `not` and no neighbour disjunction: row 1 is `above(above(?s)) = wall`; row 3 is `colored(above(above(?s)), 1)`, which is false for row 1 because off-board colour tests are false; row 2 is `above(above(above(?s))) = wall and colored(above(?s), 1)`, the second atom excluding row 1; and within row 2, column 5 is `leftof^6 = wall`, column 6 is `leftof^7 = wall and colored(leftof(?s), 1)`, column 7 is `colored(leftof(leftof(?s)), 1)`. The five guards are pairwise contradictory on at least one atom, checked cell by cell against the frame-0 panel, so rule 5 is satisfied by construction. The reverse direction costs only two rules, because in state B the nine cells render just 9 and 0 and all nine go to 1. Net: seven rules for slot 2, zero known-wrong pixels, where the last build had one rule and one deliberately wrong pixel."
    [depends: key5_slot2_centre_darkens, key5_slot2_ring_resets  probe: passed]

  theorem no_rule_in_this_manual_uses_negation_and_that_was_a_choice "Every row and column discrimination here could have been written with `not <cell> = wall`, which the grammar appears to allow and which would have been shorter. I refused it in every case and paid extra atoms instead, because the previous desk's manual never reached the compiler at all and I will not spend a round discovering that `not` before an equality atom is a parse error. Everything separating is therefore done with two facts I have already proven on this arm: k-th `above` is off-board exactly when k exceeds the row, and a colour test on an off-board cell returns false rather than raising. If a future desk wants the shorter forms, the place to try one is a single rule, not eighteen."
    [depends: off_board_cell_terms_evaluate_false_and_that_is_load_bearing  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth `below` is row 69. So `colored(<off-board>, k)` is false, not an exception, and `<cell> = wall` is the sanctioned positive test. Eleven of the twenty rules below rest on this."
    [depends: key2_body_leaves  probe: passed]

  theorem the_action_map_after_nine_transitions "PROVEN: ACTION2 is down, now three times over -- 24 pixels leave rows 8-12 and 24 arrive at rows 14-18 at t2, t6 and t8, identical to the pixel. ACTION5 returns the body to rows 8-12 from rows 14-18, three times. NEGATIVE INFORMATION, stated as negative: ACTION1 at spawn did not move a body that had open floor to its right and below it, so ACTION1 is not right and not down. ACTION3 at lattice (2,2) did not move a body that had open floor above and below it, so ACTION3 is neither up nor down; left and right are both void there, so ACTION3 is left, right, or inert. ACTION4 at the same cell did the same nothing -- but it BURNED THE METER, and under the action-keyed reading that makes ACTION4 a movement key whose move was blocked by void on both sides, hence left or right, while ACTION1 and ACTION3, which burned nothing, are not movement keys at all. THE PROBE THIS HANDS ME: from spawn, lattice (1,2), left is void and right (1,3) is open floor. Press ACTION4 there. If the body steps six pixels east, ACTION4 is right and it is the key that walks lattice row 1 toward the knob; if nothing moves, ACTION4 is left and no key I have found goes east. Either answer is worth more than anything else on the board, and it costs one meter tick under every surviving reading, which is why it is not also the meter probe."
    [depends: key2_body_leaves, the_meter_collapsed_to_two_readings_and_only_one_is_expressible  probe: pending]

  theorem action5_is_respawn_or_up_and_the_separator_is_now_cheap "Three ACTION5 presses, three returns from rows 14-18 to rows 8-12, and every one of them happened to be exactly one lattice cell below spawn, so 'respawn' and 'up' still fit identically. Two things changed. First, the panel toggles on ACTION5 and an up-key has no business toggling a panel, which tilts me towards respawn without deciding it. Second, and this is the operational change: the token budget was a fiction, so ACTION5 is FREE -- it does not even burn the meter, 3/3 -- and the separator has gone from last-resort to cheap. Press ACTION2 twice to reach lattice (3,2), rows 20-24, then press ACTION5: my rules predict the body reappears at rows 8-12, because key5_body_respawns can only ever light the original 24 spawn-ring instances, while the up-reading predicts rows 14-18. The manual announces its own refutation here with no extra machinery. There is a cheaper half-test available first: press ACTION5 while the body is ALREADY at spawn. My rules then predict the panel toggles and nothing else moves; if the panel does not toggle, the toggle is bound to body motion rather than to the key."
    [depends: key5_body_respawns, key5_body_clears  probe: pending]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me, for the two commands the playbook ranks highest. ACTION5 FROM SPAWN: I predict exactly 23 changed cells -- slot 1's eight ring pixels 2 to 9, underline 1's three 0 to 9, slot 2's eight ring pixels 9 to 1 and its centre 0 to 1, underline 2's three 9 to 0 -- and no change anywhere in rows 6-63. If the meter also burns at (63,59), parity beats action-keying and I will delete the three burn rules next round. If the body moves, ACTION5 is not respawn-in-place and I learn that instead. ACTION4 FROM SPAWN, if it is right: 24 pixels of rows 8-12 cols 14-18 go to 5, 24 pixels of rows 8-12 cols 20-24 go to 9, and one meter cell burns; my manual has no rule for ACTION4 except the burn, so I predict 48 wrong cells, and cols 20-24 carry no instances yet so I could not draw them even with the rule. 48 wrong cells is the correct price of the first step onto fresh ground and I will pay it. ANYTHING OTHER than 23-or-24 for the first and 0-or-49 for the second refutes my reading of the lattice or of the arm's instancing, and I would rather learn it from a counted diff."
    [depends: action5_is_respawn_or_up_and_the_separator_is_now_cheap, the_action_map_after_nine_transitions  probe: pending]

  theorem dynamic_census "Exactly 75 cells have ever changed and every one has an owner in this build. 23 are the panel: slot 1's eight ring pixels (9 in state A, 2 in B), underline 1's three (9 / 0), slot 2's nine (solid 1 in A; eight 9 plus centre 0 in B), underline 2's three (0 / 9). 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows down, rows 14-18 cols 14-18 minus its aperture (16,16). 4 are the right end of the row-63 bar, (63,60)..(63,63). 23+24+24+4 = 75. Frame-0 colours split them 39 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 4 meter), 9 colour-1 (slot 2), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 39+9+24 = 72 = cells_needing_an_owner exactly, and the 3 colour-0 cells are the difference between 75 and 72 -- which is the whole basis of the Dark gamble."
    [probe: passed]

  theorem only_visited_cells_have_instances "Re-verified on this build's numbers: constant 4021 + dynamic 75 = 4096, and 39+24+9 = 72 = cells_needing_an_owner. The arm instances exactly the cells that have already changed, typed by their frame-0 colour. Three consequences I keep paying for and keep accepting. The corridor ahead carries no instances, so the first step onto never-yet-changed ground costs 48 wrong cells and the round after that the same rule text draws them for free -- the manual heals one step behind the body. The next meter cell to burn cannot be drawn. And the body CHANGES TYPE as it walks: its pixels are Glyph9 at rows 8-12, Vacated at rows 14-18, and will be Vacated again at rows 20-24 because that floor renders 5 at frame 0."
    [depends: key2_body_arrives  probe: passed]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "A descent from rows 14-18 to rows 20-24 needs Vacated pixels going 9 to 5, which no rule of mine does -- key2_body_leaves is typed Glyph9 and only clears the spawn ring. The missing text, verbatim for whoever witnesses it: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. It is inert everywhere in the present frame and I am fairly sure it is true. It stays out because nothing witnesses it: the body has descended three times and every descent started at spawn. One press of ACTION2 from lattice (2,2) buys it. Note the contrast with the eighteen rules I DID write, each of which has a transition under it."
    [depends: key2_body_arrives  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; the rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read from this frame: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are open, C=6 holds the knob, C=7 is void; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2; R=8 is floor from col 13 to col 48. The separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6."
    [depends: key2_body_arrives  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed three times now: (16,16) stayed 5 at t2, t6 and t8 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- the pip at (52,46) and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket: top bar row 49, bottom bar row 55, right wall col 49, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in ten frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open: colour 8 leaves the comb along row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39 in a three-wide channel flanked by cols 39 and 41, and ends in the 3x3 colour-8 knob at rows 9-11 cols 39-41, inside lattice (1,6). Not one colour-8 pixel has moved in ten frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of the cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body enters a colour-8 cell my manual predicts it stays put and the world says otherwise, in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition."
    [probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and for a reason that got sharper this round. `Cart.pos = exit_cell` needs one named instance and arc-instances: all gives me Glyph9_r8c14 and thirty-eight siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells do become dynamic on first entry, but `count(Vacated, color = 9) = 24` would then be true of the body standing anywhere it has already been, which is not a win -- a goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in (8,7) once, the playbook steers by lattice distance to the knob."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter still scores NEGATIVE on both variants, -2214 and -36598 bits, so its segmentation loses to writing the pixels out and I owe it nothing structural. Its tracks are a useful audit: obj0 (colour 9, 8 cells, 3x3, present in all ten frames) is whichever slot currently holds the hollow-9 ring -- slot 1 in state A, slot 2 in state B, which is itself corroboration of the toggle; obj1 (colour 1, 9 cells, frames 0-4) and obj6 (colour 1, 9 cells, from frame 7) are slot 2 solid in state A before and after the round trip, and obj6 is the single most valuable number any engine produced this round because it is the refutation of the budget theorem; obj5 and obj7 (colour 2, from frames 5 and 9) are slot 1 dimmed; obj2 is an underline; obj4 is the whole row-63 bar of which four cells are dynamic; obj3 is a 1006-cell colour-null blob that swallowed the maze floor, a fair description of my board rather than an object. Every one is already inside Glyph9, Spent, Dark or board, and none gets a type of its own because a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 9 transitions constrain rank 5 of 375 features, null space dimension 370 -- and its one global law restates my census. cegis_miner's refusal remains the most useful sentence here: no track has exactly one move event per transition, 'the world does not narrate as one mover'. True of the arm, false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs me a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem the_instance_counts_are_build_relative_not_world_facts "The five invariants above are counted at THIS build. Glyph9 was 39, then 37, and is 39 again; board was 4021, then 4023, and is 4021 again -- the only thing that moved was meter cells entering and leaving the observation window. They will change again the moment the body steps onto fresh floor. I state them because they are the arithmetic that proves only_visited_cells_have_instances and the arithmetic behind the Dark gamble, and I say plainly that they describe what has been observed rather than laws of the world. No rule depends on them, and dark_instances is flagged predicted because nothing has verified it yet."
    [probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# WHAT CHANGED, AND IT IS THE BIGGEST CHANGE SINCE THIS FILE EXISTED:
#   (a) THE TOKEN BUDGET WAS A FICTION. The panel toggles back on the next
#       ACTION5, so respawn costs no life -- and it does not burn the meter
#       either, 3/3. Every line that ranked branches by token cost is gone.
#       ACTION5 is now the cheapest informative command on the board.
#   (b) THE METER HAS TWO LIVE READINGS, not four: parity of the command
#       index, and action-keyed on keys 2 and 4. They are separated by ONE
#       free command -- any non-2, non-4 key at an even command index.
#   (c) THE DIRECTION QUESTION IS NOW THE BLOCKING ONE. ACTION4 burned the
#       meter while doing nothing visible, which under the action-keyed
#       reading marks it a movement key; at lattice (2,2) both its candidate
#       directions were void, and at spawn exactly one of them is open. So
#       there is a cell where ACTION4's answer is unambiguous, and the body
#       is standing on it.
#   (d) The respawn-versus-up separator dropped from last-resort to cheap:
#       two descents put the body somewhere ACTION5's two readings disagree.
# No stored sequence anywhere: every line is a criterion on the current frame
# plus the manual's own open questions.

order     settle_the_blocking_question_before_the_merely_open_one       [proof: lean]
order     identify_a_direction_key_before_routing_with_it               [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open   [proof: lean]
order     free_probes_before_probes_that_spend_a_meter_tick             [proof: lean]
order     prefer_a_command_that_settles_two_open_questions_at_once      [proof: lean]
order     separate_two_readings_before_budgeting_against_either         [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it            [proof: lean]
order     reach_the_switch_before_testing_the_switch                    [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end              [proof: lean]
order     witness_a_rule_before_writing_it                              [proof: lean]

prune     destination_ring_pixels_are_not_all_floor => dead             [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead [proof: lean]
prune     meter_probe_using_a_key_that_burns_under_every_reading => dead [proof: lean]
prune     meter_probe_at_an_index_where_both_readings_agree => dead     [proof: lean]
prune     reset_that_returns_to_a_cell_this_branch_already_left => dead  [proof: lean]
prune     meter_exhausted and not goal => dead                          [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut           [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open          [admissible: lean]
heuristic live_readings_a_command_can_eliminate                         [admissible: lean]
heuristic open_questions_a_command_can_close                            [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time           [admissible: lean]
heuristic commands_remaining_at_one_burn_per_movement_key               [admissible: lean]
heuristic unexplained_cells_after_redraw                                [admissible: lean]

prefer    the_movement_key_whose_last_open_candidate_is_open_here       [ev: 3/3 no_ops]
prefer    a_command_whose_rival_readings_predict_different_pixels       [ev: 4/9 burns]
prefer    a_free_command_over_an_equally_informative_costly_one         [ev: 3/3 resets]
prefer    a_reset_pressed_where_its_two_readings_land_in_different_cells [ev: 3/3 resets]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule     [ev: 3/3 moves]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff              [ev: 9/9 diffs]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket          [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                 [ev: 2/7 keys]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered       [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                 [ev: 1/1 levels]
```

## Why you are being called: the surprises that fired

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '818eaaf57cafd7bb', the world answered '0c56717accb832fb'

```json
{
 "action": 5,
 "observed": "0c56717accb832fb",
 "predictions": {
  "inert": "15c2e5de8c8dc96b",
  "manual": "818eaaf57cafd7bb",
  "without_key2_body_arrives": "818eaaf57cafd7bb",
  "without_key2_body_leaves": "818eaaf57cafd7bb",
  "without_key5_body_clears": "818eaaf57cafd7bb",
  "without_key5_body_respawns": "818eaaf57cafd7bb",
  "without_key5_slot1_dims": "818eaaf57cafd7bb",
  "without_key5_slot1_lights": "15c2e5de8c8dc96b",
  "without_key5_slot2_centre_darkens": "818eaaf57cafd7bb",
  "without_key5_slot2_centre_resets": "15c2e5de8c8dc96b",
  "without_key5_slot2_ring_resets": "15c2e5de8c8dc96b",
  "without_key5_slot2_row1_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row2_left_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row2_right_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row3_lights": "818eaaf57cafd7bb",
  "without_key5_underline1_dims": "818eaaf57cafd7bb",
  "without_key5_underline1_lights": "15c2e5de8c8dc96b",
  "without_key5_underline2_dims": "15c2e5de8c8dc96b",
  "without_key5_underline2_lights": "818eaaf57cafd7bb",
  "without_meter_burn_key2_next": "818eaaf57cafd7bb",
  "without_meter_burn_key2_rightmost": "818eaaf57cafd7bb",
  "without_meter_burn_key4_next": "818eaaf57cafd7bb"
 },
 "probe_id": "P-05"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '15c2e5de8c8dc96b', the world answered '0c56717accb832fb'

```json
{
 "action": 5,
 "observed": "0c56717accb832fb",
 "predictions": {
  "inert": "818eaaf57cafd7bb",
  "manual": "15c2e5de8c8dc96b",
  "without_key2_body_arrives": "15c2e5de8c8dc96b",
  "without_key2_body_leaves": "15c2e5de8c8dc96b",
  "without_key5_body_clears": "15c2e5de8c8dc96b",
  "without_key5_body_respawns": "15c2e5de8c8dc96b",
  "without_key5_slot1_dims": "818eaaf57cafd7bb",
  "without_key5_slot1_lights": "15c2e5de8c8dc96b",
  "without_key5_slot2_centre_darkens": "818eaaf57cafd7bb",
  "without_key5_slot2_centre_resets": "15c2e5de8c8dc96b",
  "without_key5_slot2_ring_resets": "15c2e5de8c8dc96b",
  "without_key5_slot2_row1_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row2_left_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row2_right_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row3_lights": "818eaaf57cafd7bb",
  "without_key5_underline1_dims": "818eaaf57cafd7bb",
  "without_key5_underline1_lights": "15c2e5de8c8dc96b",
  "without_key5_underline2_dims": "15c2e5de8c8dc96b",
  "without_key5_underline2_lights": "818eaaf57cafd7bb",
  "without_meter_burn_key2_next": "15c2e5de8c8dc96b",
  "without_meter_burn_key2_rightmost": "15c2e5de8c8dc96b",
  "without_meter_burn_key4_next": "15c2e5de8c8dc96b"
 },
 "probe_id": "P-06"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '818eaaf57cafd7bb', the world answered '06e79195f0adc15f'

```json
{
 "action": 5,
 "observed": "06e79195f0adc15f",
 "predictions": {
  "inert": "15c2e5de8c8dc96b",
  "manual": "818eaaf57cafd7bb",
  "without_key2_body_arrives": "818eaaf57cafd7bb",
  "without_key2_body_leaves": "818eaaf57cafd7bb",
  "without_key5_body_clears": "818eaaf57cafd7bb",
  "without_key5_body_respawns": "818eaaf57cafd7bb",
  "without_key5_slot1_dims": "818eaaf57cafd7bb",
  "without_key5_slot1_lights": "15c2e5de8c8dc96b",
  "without_key5_slot2_centre_darkens": "818eaaf57cafd7bb",
  "without_key5_slot2_centre_resets": "15c2e5de8c8dc96b",
  "without_key5_slot2_ring_resets": "15c2e5de8c8dc96b",
  "without_key5_slot2_row1_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row2_left_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row2_right_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row3_lights": "818eaaf57cafd7bb",
  "without_key5_underline1_dims": "818eaaf57cafd7bb",
  "without_key5_underline1_lights": "15c2e5de8c8dc96b",
  "without_key5_underline2_dims": "15c2e5de8c8dc96b",
  "without_key5_underline2_lights": "818eaaf57cafd7bb",
  "without_meter_burn_key2_next": "818eaaf57cafd7bb",
  "without_meter_burn_key2_rightmost": "818eaaf57cafd7bb",
  "without_meter_burn_key4_next": "818eaaf57cafd7bb"
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
  "inert": "818eaaf57cafd7bb",
  "manual": "15c2e5de8c8dc96b",
  "without_key2_body_arrives": "15c2e5de8c8dc96b",
  "without_key2_body_leaves": "15c2e5de8c8dc96b",
  "without_key5_body_clears": "15c2e5de8c8dc96b",
  "without_key5_body_respawns": "15c2e5de8c8dc96b",
  "without_key5_slot1_dims": "818eaaf57cafd7bb",
  "without_key5_slot1_lights": "15c2e5de8c8dc96b",
  "without_key5_slot2_centre_darkens": "818eaaf57cafd7bb",
  "without_key5_slot2_centre_resets": "15c2e5de8c8dc96b",
  "without_key5_slot2_ring_resets": "15c2e5de8c8dc96b",
  "without_key5_slot2_row1_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row2_left_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row2_right_lights": "818eaaf57cafd7bb",
  "without_key5_slot2_row3_lights": "818eaaf57cafd7bb",
  "without_key5_underline1_dims": "818eaaf57cafd7bb",
  "without_key5_underline1_lights": "15c2e5de8c8dc96b",
  "without_key5_underline2_dims": "15c2e5de8c8dc96b",
  "without_key5_underline2_lights": "818eaaf57cafd7bb",
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
# (RESET + A1 A2 A3 A4 A5 A2 A5 A2 A5 A5 A5 A5 A5). 77 cells have ever
# changed; this manual names and owns all 77.
#
# WHAT THIS ROUND COST ME, IN ORDER:
#
#   1. FOUR REFUTATIONS, ALL THE SAME REFUTATION. P-05..P-08 are t10..t13,
#      four ACTION5 presses with the body ALREADY AT SPAWN. My thirteen panel
#      rules fired on act=key(5) unconditionally, so I predicted a 23-cell
#      panel toggle four times running. The world toggled nothing. The panel
#      toggles only when ACTION5 ACTUALLY DOES SOMETHING, and every panel rule
#      now carries the guard `colored(spawn_probe, 5)` -- "the body is away
#      from its start cell". That single atom answers all four surprises.
#
#   2. THE METER READING I WROTE LAST ROUND IS REFUTED AND THE SURVIVOR IS
#      INEXPRESSIBLE. I wrote action-keying (burn iff key 2 or key 4) and
#      named parity as its rival. t10 and t12 are ACTION5 presses that BURNED.
#      Parity is now 13/13 and action-keying is dead as an explanation. See
#      the_meter_is_command_parity_and_the_frame_cannot_carry_it.
#
#   3. THE WORLD IS NOT A FUNCTION OF THE DRAWN FRAME, AND I CAN PROVE IT.
#      t11 changed no cell, so the state entering t11 and the state entering
#      t12 are THE SAME GRID. Both commands were ACTION5. t11 did nothing;
#      t12 burned (63,58). Same state, same action, two successors. There is a
#      hidden bit and my manual, which reads only pixels, cannot hold it.
#
#   4. THE DARK GAMBLE PAID. Two builds called (5,5),(5,6),(5,7) permanently
#      unownable; I declared `object Dark # arc-colour: 0` and hedged it.
#      certify came back 9/9 replay and 0 unexplained cells, which is only
#      possible if Dark got exactly its three instances. Status upgraded from
#      predicted to proven, and the arithmetic 77 - 74 = 3 still holds.

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
  landmark spawn_probe   # arc-cell: (8, 14)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t13 compress: 41]
  Vacated [segment: dynamic_colour_5 ev: t2-t9  compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t9  compress: 9]
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

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

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

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_underline2_dims forall ?d in Dark [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) and colored(above(above(?d)), 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 41 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: proven_by_replay]
  invariant board_cells count(board) = 4019 [status: counted]

  theorem the_four_refutations_were_one_refutation_and_here_is_the_atom_that_answers_it "P-05 through P-08 are t10, t11, t12, t13: four consecutive ACTION5 presses with the body ALREADY at spawn. My manual predicted the 23-cell panel toggle every time and the world produced, in order, one meter cell, nothing, one meter cell, nothing. The diagnosis is exact and it is visible in the surprise report itself: at t10 the rival hash `without_key5_slot1_lights` equals `inert`, and so do `without_key5_slot2_ring_resets`, `without_key5_slot2_centre_resets` and `without_key5_underline1_lights` -- the panel rules were the ENTIRE difference between my prediction and doing nothing, and doing nothing was almost right. So: the panel toggle is not caused by the key, it is caused by ACTION5 HAVING AN EFFECT. Every one of the thirteen panel rules now carries `colored(spawn_probe, 5)`, where spawn_probe is (8,14), the top-left ring pixel of the start cell: it renders 9 while the body stands at spawn and 5 the moment the body is anywhere else. At t5, t7, t9 the body was one cell south and (8,14) rendered 5, so every rule still fires with its old coverage; at t10..t13 the body was home and (8,14) rendered 9, so all thirteen go silent. One positive atom, no negation, four surprises answered, zero coverage lost."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, key5_underline2_dims  probe: passed]

  theorem the_world_is_not_markov_in_the_drawn_frame "The single most important sentence in this manual, and it is a proof rather than a reading. t11 changed no cells at all. Therefore the grid entering t11 and the grid entering t12 are THE SAME GRID, pixel for pixel. Both commands were ACTION5. t11 produced no change; t12 burned (63,58). Same state, same action, two different successors. Constraint 5 asks my rules to be unambiguous and they are -- but the WORLD is not a function of what it draws. There is at least one bit of hidden state, it flips on every command, and no guard in this language can read it because no guard can read anything that is not a pixel. Everything I write about the meter from here is an approximation with a known error rate, and I would rather say that once, plainly, than keep discovering it. The same proof runs at t13 versus t10 in the other direction: t13 changed nothing from a state one burn further along."
    [depends: the_meter_is_command_parity_and_the_frame_cannot_carry_it  probe: passed]

  theorem the_meter_is_command_parity_and_the_frame_cannot_carry_it "Row 63 is a 64-cell colour-9 bar burning to 1 from the right end. Burns: (63,63) at t2, (63,62) at t4, (63,61) at t6, (63,60) at t8, (63,59) at t10, (63,58) at t12. No burn at t1, t3, t5, t7, t9, t11, t13. Read the index column: burn at every EVEN command, silence at every ODD one, 13/13, no exceptions. Last round I had two survivors and wrote the expressible one; this round the world executed the experiment for me four times over. ACTION-KEYING IS REFUTED: t10 and t12 are ACTION5 presses that burned, and t5, t7, t9 are ACTION5 presses that did not. No property of the drawn frame separates them -- t11 and t12 start from the identical grid. Not the meter count either: count 5 precedes both a burn (t12) and a silence (t11). PARITY IS THE LAW AND PARITY IS INEXPRESSIBLE, because the guard vocabulary has no command counter and the frame carries no phase. cegis_miner reached the same wall from its side and said so: 'no literal separates transition 1 from the positives'. So I am left with three rules that are perfect on their own guards -- every key-2 press has burned, 3/3, and the one key-4 press burned, 1/1 -- and are, I now believe, coincidences: every key-2 and key-4 press so far happened to land on an even index. I KEEP THEM, because they buy four exactly-replayed transitions and cost two, and because keeping them makes the manual announce its own refutation: press key 2 or key 4 at an ODD command index and my manual burns a cell the world will not. That is the cheapest experiment on the board and the playbook ranks it."
    [depends: meter_burn_key2_rightmost, meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_meter_is_a_budget_of_about_one_hundred_and_twenty_eight_commands "Sixty-four cells, one cell per two commands, so a full bar is 128 commands from RESET and 13 commands have consumed 6 cells. Two operational consequences, and the second kills a whole family of playbook lines. First: roughly 115 commands remain, which is generous but not unlimited, and the manual should stop pretending the meter is scenery. Second and more important: BECAUSE THE TICK IS PARITY, EVERY COMMAND COSTS EXACTLY HALF A CELL AND NO COMMAND IS FREE. My last playbook ranked probes by whether they burned -- 'free_probes_before_probes_that_spend_a_meter_tick', 'a_free_command_over_an_equally_informative_costly_one' -- and that ordering was ranking on a distinction that does not exist. Cost is uniform; only information differs; the ordering is now purely by information. I do not know what happens when the bar reaches zero and I have never seen a GAME_OVER, so 'meter_exhausted => dead' stays in the playbook as a conservative guess and is labelled as one."
    [depends: the_meter_is_command_parity_and_the_frame_cannot_carry_it  probe: pending]

  theorem the_action_map_after_thirteen_transitions "ACTION2 IS DOWN, 3/3, identical to the pixel at t2, t6, t8, and unaffected by the panel phase -- two of those presses were in phase A and one in phase B and all three moved 24 pixels six rows south. ACTION5 RETURNS THE BODY TO ITS START CELL, 3/3 from the cell directly below spawn, and IS A NO-OP AT SPAWN, 4/4 at t10..t13. The four new no-ops are the strongest thing this round bought me on the map. NEGATIVE INFORMATION, stated as negative: at spawn (lattice (1,2)) up is void and left is void, while down and right are open floor -- ACTION1 did nothing there, so ACTION1 IS NOT DOWN AND NOT RIGHT, leaving up, left, or inert. At lattice (2,2) up and down are open floor while left and right are both void -- ACTION3 and ACTION4 each did nothing there, so NEITHER IS UP AND NEITHER IS DOWN, leaving left, right, or inert. Fit those three exclusions together with ACTION2 = down and exactly one four-key assignment survives: ACTION1 = up, ACTION3 and ACTION4 = left and right in an order I do not know. That also settles what ACTION5 is not -- if ACTION1 is up then ACTION5 is not up, and its three ascents were return-to-start seen from a cell that happened to be one step from home, which is precisely what the four no-ops at home confirm."
    [depends: key2_body_leaves, key5_body_respawns  probe: pending]

  theorem the_east_key_is_the_blocking_question_and_spawn_is_the_cell_that_answers_it "Everything I want is east: the knob sits in lattice (1,6) and the only route to it runs along lattice row 1, which is open floor from column 13 to column 43. ACTION3 and ACTION4 are left and right in unknown order, and the only reason I do not know which is that both of them were pressed at lattice (2,2), where left and right are BOTH void -- a cell that could not distinguish them. The body is now standing at spawn, lattice (1,2), where left is void and right is open floor. Press either of them here and the answer is unambiguous in the raw diff: the body steps six columns east, or it does not. I ALSO PREDICT THE PRICE, so it cannot be mistaken for failure. Columns 20-24 of rows 8-12 have never changed, so they carry no instances and my manual cannot draw them under any rule; a successful eastward step therefore costs me 24 wrong pixels there plus 24 at columns 14-18 that no rule of mine clears, 48 in total, plus possibly one meter cell. 48 wrong cells is the correct price of the first step onto fresh ground and the round after, the same rule text draws it for free. What would refute my reading of the lattice is any other number."
    [depends: the_action_map_after_thirteen_transitions, only_visited_cells_have_instances  probe: pending]

  theorem the_one_command_that_settles_two_questions "Command index 14 is EVEN. Pressing ACTION3 there separates BOTH open questions at once and nothing else on the board does. On the meter: parity predicts a burn at (63,57), action-keying predicts silence because 3 is neither 2 nor 4, and my manual predicts silence -- so a one-pixel diff in row 63 refutes my own burn rules and a zero-pixel diff saves them. On the map: if ACTION3 is right the body steps east and I have found the key that walks lattice row 1; if it does not move, ACTION3 is left and ACTION4 is right by elimination. The four possible diffs are 0, 1, 48 and 49 cells and every one of them is a different pair of answers, which is exactly the shape of experiment I should be buying. Note what I deliberately did NOT choose: ACTION4 would burn under both meter readings and separate nothing, and ACTION1 at spawn is a pure parity test that tells me nothing about the map."
    [depends: the_east_key_is_the_blocking_question_and_spawn_is_the_cell_that_answers_it, the_meter_is_command_parity_and_the_frame_cannot_carry_it  probe: pending]

  theorem the_panel_is_a_two_phase_indicator_and_i_still_do_not_know_what_it_indicates "What is now PROVEN about it: it has exactly two configurations; ACTION5 swaps them; ACTION2 never touches them, 3/3; and ACTION5 swaps them only when it moves the body, 3 toggles for 3 effective presses and 0 toggles for 4 ineffective ones. STATE A (frames 0-4, 7-8): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. STATE B (frames 5-6, 9-13, and now): slot 1 is a hollow colour-2 ring, underline 1 dark; slot 2 is a hollow colour-9 ring with a dark centre, underline 2 lit 9. The lit underline follows the slot drawn in 9, so the underline reads as a selector and 9 reads as selected. What I DO NOT know is what is being selected -- two bodies, two modes, two carried items, or a reset counter shown mod two -- and I will not guess, because nothing downstream needs the meaning: the rules encode the SWAP and the swap is fully witnessed. The last manual read this panel as two lives and ranked every branch by a life that could not be spent; that is the failure mode I am refusing to repeat. One asymmetry worth recording for whoever gets more data: slot 1's idle form is a hollow 2-ring while slot 2's idle form is a SOLID 1-block, so the two slots hold different things, not two copies of one thing."
    [depends: key5_slot1_dims, key5_slot2_centre_darkens, the_four_refutations_were_one_refutation_and_here_is_the_atom_that_answers_it  probe: passed]

  theorem the_dark_gamble_paid_and_the_arithmetic_that_predicted_it_is_a_tool "Resolved, and I record the resolution because two previous builds got it wrong in the same direction. (5,5),(5,6),(5,7) render 0 at frame 0 and 9 in state B; both predecessors declared them permanently unownable on the grounds that an arc-colour 0 object would claim three thousand background cells. I declared `object Dark # arc-colour: 0 arc-instances: all` anyway, on the arm's own arithmetic -- constant 4019 plus dynamic 77 is 4096 while cells_needing_an_owner is 74, and 77 minus 74 is exactly 3 -- and hedged both Dark rules with positional guards so that zero, three or three thousand instances were all safe. certify answered: 9/9 replay and 0 unexplained cells, which is only possible if those three pixels were drawn correctly through the toggles at t5, t7 and t9. So the arm instances only cells the BOARD CANNOT EXPLAIN, background colour included, and the gap between dynamic_cells and cells_needing_an_owner is a reliable count of the background-coloured dynamic cells. That is now a tool: it will tell the next desk, before it declares anything, how many colour-0 instances it is about to get."
    [depends: key5_underline2_lights, key5_underline2_dims  probe: passed]

  theorem dynamic_census "Exactly 77 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels (9 in A, 2 in B), underline 1's three (9 / 0), slot 2's nine (solid 1 in A; eight 9 plus a dark centre in B), underline 2's three (0 / 9). 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 6 are the burned right end of row 63, (63,58) through (63,63) -- two more than last round, and those two are the entire growth of the census. 23+24+24+6 = 77. By frame-0 colour: 41 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 6 meter), 9 colour-1 (slot 2), 24 colour-5 (the lower ring, which is floor at frame 0), 3 colour-0 (underline 2). 41+24+9 = 74 = cells_needing_an_owner exactly, and the 3 colour-0 cells are the difference between 77 and 74."
    [probe: passed]

  theorem only_visited_cells_have_instances "Re-verified on this build: constant 4019 + dynamic 77 = 4096, and 41+24+9 = 74. The arm instances exactly the cells that have already changed, typed by their frame-0 colour. Three consequences I keep paying for and keep accepting. The corridor ahead carries no instances, so the first step onto never-yet-changed ground costs 48 wrong cells and the round after that the same rule text draws them for free -- the manual heals one step behind the body. The next meter cell to burn, (63,57), is board and cannot be drawn even if I knew it would burn, which is why the parity law would cost me a pixel at t14 whatever I wrote. And the body CHANGES TYPE as it walks: its pixels are Glyph9 at rows 8-12, Vacated at rows 14-18, and will be Vacated again at rows 20-24 and at columns 20-24, because all that floor renders 5 at frame 0."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem the_instance_counts_are_build_relative_not_world_facts "The five invariants above are counted at THIS build. Glyph9 has been 39, then 37, then 39, and is now 41; board has been 4021 and is now 4019. Nothing moved but meter cells entering the observation window, and they will move again the moment the body steps onto fresh floor. I state them because they are the arithmetic behind only_visited_cells_have_instances and behind the Dark resolution, and I say plainly that they describe what has been observed rather than laws of the world. No rule depends on them."
    [probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth `below` is row 69. So `colored(<off-board>, k)` is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen of the twenty rules above rest on this, and every row and column discrimination in the panel is built from it: the k-th `above` is off-board exactly when k exceeds the row, so row 1 is `above(above(?s)) = wall`, row 3 is `colored(above(above(?s)), 1)` which is false for row 1 because the colour test on an off-board cell is false, and row 2 is the conjunction of `above^3 = wall` with `colored(above(?s), 1)`. Not one rule uses `not`, deliberately: two rounds ago a manual failed to reach the compiler at all and I will not spend a round discovering whether `not` before an equality atom parses. If a future desk wants the shorter forms, try one rule, not twenty."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "A descent from rows 14-18 to rows 20-24 needs Vacated pixels going 9 to 5, which no rule of mine does -- key2_body_leaves is typed Glyph9 and only ever clears the spawn ring. The missing text, verbatim for whoever witnesses it: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. It is inert everywhere in the present frame and I am fairly sure it is true. It stays out because nothing witnesses it: the body has descended three times and every descent started at spawn. One ACTION2 from lattice (2,2) buys it. The same hole exists in the east-west direction and is worse, because there I do not even know the key: whatever the east key turns out to be, it will need a leaves-rule typed on whichever object owns the departing pixels and an arrives-rule typed on the destination, and neither can be written before the first eastward step is witnessed."
    [depends: key2_body_arrives  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read from this frame: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are open, C=6 holds the knob, C=7 is void; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2; R=8 is floor from col 13 to col 48. The separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); the body has occupied only (1,2) and (2,2) in fourteen frames."
    [depends: key2_body_arrives  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed three times: (16,16) stayed 5 at t2, t6 and t8 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket: top bar row 49, bottom bar row 55, right wall col 49, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in fourteen frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open: colour 8 leaves the comb along row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39 in a three-wide channel flanked by cols 39 and 41, and ends in the 3x3 colour-8 knob at rows 9-11 cols 39-41, inside lattice (1,6). Not one colour-8 pixel has moved in fourteen frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of the cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body enters a colour-8 cell my manual predicts it stays put and the world says otherwise, in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the five-key assignment I now believe -- 1 up, 2 down, 3 and 4 left and right, 5 return-to-start -- accounts for every key I have pressed, which makes 6 and 7 more likely to be a click and a spare than more directions."
    [depends: the_action_map_after_thirteen_transitions  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and arc-instances: all gives me Glyph9_r8c14 and forty siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells do become dynamic on first entry, but `count(Vacated, color = 9) = 24` would then be true of the body standing anywhere it has already been, which is not a win -- a goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in (8,7) once, the playbook steers by lattice distance."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter still scores NEGATIVE on both variants, -2200 and -37350 bits, so its segmentation loses to writing the pixels out and I owe it nothing structural. Its tracks remain a useful audit and one number in them is new: obj7, a colour-2 3x3 first seen at frame 9 and present for FIVE frames, which is slot 1 dimmed sitting still through t10..t13 -- independent corroboration, from an engine that knows nothing of my rules, that the panel did not toggle four times running. obj0 (colour 9, 8 cells, all 14 frames) is whichever slot currently holds the hollow-9 ring; obj1 and obj6 are slot 2 solid before and after the round trip; obj4 is the whole row-63 bar of which six cells are now dynamic; obj3 is a 1006-cell colour-null blob that swallowed the maze floor, a fair description of my board rather than an object. Every one is already inside Glyph9, Spent, Dark or board, and none gets a type of its own, because a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 13 transitions constrain rank 7 of 385 features, null space dimension 378, 'nearly every vector in it is a law that is true over these states and unfalsified rather than confirmed' -- and its one global law restates my census. cegis_miner's refusal is still the most useful sentence any engine has produced: 'the world does not narrate as one mover'. True of the arm, false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs me a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. ACTION3 FROM SPAWN AT COMMAND 14: my manual predicts ZERO changed cells. If exactly one cell changes and it is (63,57), parity is confirmed at 14/14 and my three burn rules are coincidence-fits that I will delete next round in favour of silence. If 48 or 49 cells change, ACTION3 is right, the body is at lattice (1,3), and I owe two new rules that the transition will witness. If zero cells change, ACTION3 is left AND action-keying survives, which would be the first evidence in two rounds that the meter is not parity. ACTION5 FROM SPAWN, if anyone presses it again: I now predict zero changed cells outside row 63, 4/4 witnessed, and I predict the meter burns on even indices only -- this is the prediction I got wrong four times running last round and the guard `colored(spawn_probe, 5)` is my whole answer to it. ANY panel change while the body is at spawn refutes that guard and means the toggle is bound to something I have not found."
    [depends: the_one_command_that_settles_two_questions, the_four_refutations_were_one_refutation_and_here_is_the_atom_that_answers_it  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# WHAT CHANGED THIS ROUND:
#   (a) COST IS NOW UNIFORM. The meter is command parity, 13/13, so every
#       command costs exactly half a cell and nothing is free. Every line
#       that ranked probes by whether they burned is DELETED -- it was
#       ranking on a distinction that does not exist. Rank by information.
#   (b) ACTION5 AT SPAWN IS A PROVEN NO-OP, 4/4, and still costs half a
#       cell. Pressing it at home is now pruned outright.
#   (c) THE EAST KEY IS THE ONLY BLOCKING QUESTION. ACTION3 and ACTION4 are
#       left and right in unknown order, and they were tested at the one
#       cell where both candidates were void. The body stands at spawn,
#       where left is void and right is open floor -- the cell that
#       separates them.
#   (d) ONE COMMAND SETTLES TWO QUESTIONS: an odd-numbered key pressed at an
#       even command index tests parity, and pressed at spawn it tests the
#       east key. Prefer commands whose four possible diffs are four
#       different pairs of answers.
# No stored sequence anywhere: every line is a criterion on the current
# frame plus the manual's own open questions.

order     settle_the_east_key_before_routing_toward_the_knob              [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open     [proof: lean]
order     prefer_a_command_that_settles_two_open_questions_at_once        [proof: lean]
order     test_a_law_with_a_key_its_rival_reading_says_is_silent          [proof: lean]
order     identify_a_direction_key_before_routing_with_it                 [proof: lean]
order     separate_two_readings_before_planning_against_either            [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it              [proof: lean]
order     reach_the_switch_before_testing_the_switch                      [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end                [proof: lean]
order     witness_a_rule_before_writing_it                                [proof: lean]
order     spend_commands_on_information_while_the_bar_is_still_long       [proof: lean]

prune     destination_ring_pixels_are_not_all_floor => dead               [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead  [proof: lean]
prune     return_to_start_pressed_while_already_at_start => dead          [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead   [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead [proof: lean]
prune     meter_exhausted and not goal => dead                            [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut             [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open            [admissible: lean]
heuristic live_readings_a_command_can_eliminate                           [admissible: lean]
heuristic open_questions_a_command_can_close                              [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time             [admissible: lean]
heuristic commands_remaining_at_one_burn_per_two_commands                 [admissible: lean]
heuristic unexplained_cells_after_redraw                                  [admissible: lean]

prefer    an_untested_direction_key_where_its_two_candidates_disagree     [ev: 4/4 no_ops]
prefer    a_command_whose_rival_readings_predict_different_pixels         [ev: 6/13 burns]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 13/13 diffs]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule       [ev: 3/3 moves]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket            [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered         [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                   [ev: 2/7 keys]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has              [ev: 2/11 cells]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter obj0 (colour 9, 8 cells, 3x3, present all 14 frames)", "verdict": "entailed",
   "why": "It is whichever panel slot currently draws the hollow-9 ring -- slot 1 in state A, slot 2 in state B -- so it is already covered by Glyph9 and Spent instances; giving it a type of its own would put two types on the same pixels and invite the double claim constraint 5 forbids."},

  {"id": "O-02", "subject": "mdl_segmenter obj7 (colour 2, 3x3, first_frame 9, present 5 frames)", "verdict": "accept",
   "as": "corroboration for the panel guard, not a new type",
   "why": "A colour-2 block persisting unchanged across frames 9,10,11,12,13 is exactly slot 1 sitting still through the four ACTION5 presses that my old rules said would toggle it -- an engine that knows nothing of my rules independently reporting the four surprises."},

  {"id": "O-03", "subject": "mdl_segmenter obj3 (1006 cells, colour null, 50x38)", "verdict": "reject",
   "why": "A colour-null blob that swallowed the whole maze floor is a description of my board, not an object; it has never changed in fourteen frames and declaring it would put an object over 1006 constant cells for zero compression."},

  {"id": "O-04", "subject": "object Dark, arc-colour 0, three cells at (5,5),(5,6),(5,7)", "verdict": "accept",
   "as": "Dark, upgraded from gamble to proven",
   "why": "certify returned 9/9 replay and 0 unexplained cells while key5_underline2_lights and key5_underline2_dims were the only rules drawing those three pixels through t5, t7, t9 -- impossible unless the arm gave Dark exactly three instances, as dynamic_cells 77 minus cells_needing_an_owner 74 predicted."},

  {"id": "O-05", "subject": "two new dynamic cells (63,58) and (63,59)", "verdict": "accept",
   "as": "Glyph9 instances, raising the count 39 -> 41",
   "why": "They render 9 at frame 0 and burned to 1 at t12 and t10, so the arm types them Glyph9; dynamic_cells rose 75 -> 77 and cells_needing_an_owner 72 -> 74, a delta of exactly two, which accounts for the entire growth of the census."},

  {"id": "R-01", "subject": "the thirteen panel rules, guard `colored(spawn_probe, 5)` added", "verdict": "accept",
   "why": "P-05..P-08 are four ACTION5 presses at spawn where my rules predicted a 23-cell toggle and the world produced none; (8,14) renders 9 when the body is home and 5 when it is away, so the atom silences all thirteen at t10-t13 while leaving their t5/t7/t9 coverage untouched."},

  {"id": "R-02", "subject": "meter_burn_key2_rightmost, meter_burn_key2_next, meter_burn_key4_next", "verdict": "probe-pending",
   "why": "Kept, but downgraded to coincidence-fits: every key-2 press burned (3/3) and the one key-4 press burned (1/1), yet t10 and t12 show ACTION5 burning too, so the real cause is command parity and these rules are right only because every key-2/key-4 press so far landed on an even index -- a key-2 press at an odd index refutes them in one cell."},

  {"id": "R-03", "subject": "a key-5 burn rule to capture t10 and t12", "verdict": "reject",
   "why": "The only available guard, body-at-spawn, fires at t10, t11, t12 and t13 and is right at exactly two of them, so it buys two transitions and loses two -- net zero replay for four extra atoms, which fails the no-entry-without-gain test."},

  {"id": "R-04", "subject": "cegis_miner (no track satisfies one-move-per-transition)", "verdict": "accept",
   "as": "a true statement about the arm, not about the world",
   "why": "There is one mover, a rigid 24-pixel ring, but the arm can only see 24 simultaneous recolours, which is why every direction costs me a leaves-rule plus an arrives-rule instead of one moved() event; its NoSeparatingGuard on transition 1 is the same wall I hit on parity."},

  {"id": "R-05", "subject": "key2_floor_leaves (descent from rows 14-18 to rows 20-24)", "verdict": "probe-pending",
   "why": "Written out verbatim in a theorem and kept out of the rules because nothing witnesses it -- all three descents started at spawn, so no transition shows a Vacated pixel going 9 to 5; one ACTION2 from lattice (2,2) buys it."},

  {"id": "L-01", "subject": "meter burns on even command indices, 13/13", "verdict": "accept",
   "as": "theorem the_meter_is_command_parity_and_the_frame_cannot_carry_it",
   "why": "Burns at t2,4,6,8,10,12 and silence at t1,3,5,7,9,11,13 with no exceptions; the rival action-keyed reading is refuted by t10 and t12, which are ACTION5 presses that burned while t5, t7, t9 did not."},

  {"id": "L-02", "subject": "the world is not a function of the drawn frame", "verdict": "accept",
   "as": "theorem the_world_is_not_markov_in_the_drawn_frame",
   "why": "t11 changed no cell, so the grids entering t11 and t12 are identical; both commands were ACTION5; t11 did nothing and t12 burned (63,58) -- one state, one action, two successors, which is a hidden bit no pixel guard can read."},

  {"id": "L-03", "subject": "the token-budget reading (panel = lives)", "verdict": "reject",
   "why": "Already refuted last round by the colour-1 block returning at t7, and now doubly dead: the panel did not move at all across four ACTION5 presses, so it is neither a consumable nor a per-press counter but a two-phase indicator swapped by effective returns only."},

  {"id": "L-04", "subject": "the action map ACTION1=up, ACTION2=down, {ACTION3,ACTION4}={left,right}, ACTION5=return-to-start", "verdict": "probe-pending",
   "why": "Forced by three exclusions plus one proof: ACTION2 is down 3/3; ACTION1 did nothing at spawn where down and right are open, so it is up or left; ACTION3 and ACTION4 did nothing at (2,2) where up and down are open, so both are horizontal -- and the four new no-ops at t10-t13 show ACTION5 is inert at home, which is return-to-start rather than up."},

  {"id": "P-01", "subject": "ACTION3 from spawn at command index 14", "verdict": "probe-pending",
   "why": "The only command whose four possible diffs -- 0, 1, 48, 49 cells -- are four different pairs of answers: row 63 alone separates parity from action-keying because 3 is neither 2 nor 4, and the 48 cells at rows 8-12 separate left from right because left is void at spawn and right is open floor."},

  {"id": "P-02", "subject": "ACTION4 as the east probe", "verdict": "reject",
   "why": "It burns under both surviving meter readings, so it separates nothing on the meter, and it answers the east question no better than ACTION3 does; it becomes the right command only if ACTION3 turns out to be left."},

  {"id": "P-03", "subject": "respawn-versus-up separator for ACTION5", "verdict": "probe-pending",
   "why": "The cheap version is now on the route rather than off it: step east to lattice (1,3), where up is void, then press ACTION5 -- return-to-start sends the body west to spawn, up sends it nowhere, and the two predictions differ by 48 cells."},

  {"id": "E-01", "subject": "command-index parity as a rule guard", "verdict": "reject",
   "why": "I wanted `when parity(command) = 0 ... then recolored(?p, 1)`; the guard vocabulary is exhaustive and has no counter, and the meter's own drawn state does not carry the phase since count 5 precedes both a burn (t12) and a silence (t11), so I wrote it as a theorem with 13/13 witnesses and left the manual unable to draw row 63 on odd-key presses."},

  {"id": "E-02", "subject": "a goal predicate for standing in the socket", "verdict": "reject",
   "why": "I wanted `goal Cart.pos = socket_cell`, but arc-instances: all gives me forty-one Glyph9 instances and no `Cart`, and the socket interior is board until first entry so count() has nothing to range over; a count-based stand-in would be true of the body standing anywhere it has already been, which would stop a planner at its first step."},

  {"id": "E-03", "subject": "a click rule for the knob", "verdict": "probe-pending",
   "why": "ACTION6 and ACTION7 have never been pressed and one is normally a click, but the guard language has nowhere to put coordinates, so any click rule would fire on every click anywhere; I can record a click's effect (comb pixels going 8 to 5) and never its precondition."}
]
```
```
