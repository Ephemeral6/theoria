# call-007-theorize-round1

model: `claude-opus-5` · 689519 ms · $2.089105 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 50825, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 50825, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 50825, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 50825, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 61744, "type": "message"}], "output_tokens": 61744, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 78,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4015,
 "distinct_states": 20,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 81,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 22,
 "steps": 22
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
9999999999999999999999999999999999999999999999999999991111111111
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
- t18  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-55, [5, 9] -> [1, 5, 9]
- t19  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t20  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-54, [5, 9] -> [1, 5, 9]
- t21  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 21,
  "n_states": 22,
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
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture"
  ],
  "tracks": [
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 0,
    "ms": 1,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj0",
    "transitions": 21
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
    "transitions": 21
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
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj12"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj13"
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
  "candidates": 14,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 9,
   "move": 18,
   "recolor": 28,
   "vanish": 9
  },
  "n_frames": 22,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 22,
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
    "frames_present": 22,
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
    "frames_present": 22,
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
    "frames_present": 22,
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
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj11"
   },
   {
    "color": 1,
    "first_frame": 19,
    "frames_present": 2,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj12"
   },
   {
    "color": 2,
    "first_frame": 21,
    "frames_present": 1,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj13"
   }
  ],
  "variants": [
   {
    "baseline_bits": 17464,
    "compression_ratio": 0.640976,
    "events": 64,
    "gain_bits": 6270,
    "ms": 50,
    "script_bits": 11194,
    "split_by_color": false,
    "tracks": 14
   },
   {
    "baseline_bits": 17464,
    "compression_ratio": 6.372881,
    "events": 147,
    "gain_bits": -93832,
    "ms": 106,
    "script_bits": 111296,
    "split_by_color": true,
    "tracks": 57
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 81,
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
  "cells_needing_an_owner": 78,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4015,
  "distinct_states": 20,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 81,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 22,
  "steps": 22
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 81,
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
  "cells_dynamic": 81,
  "cells_used": 81,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 11,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.02716,
   "difference_rank": 11,
   "features": 405,
   "space_dimension": 394,
   "transitions": 21,
   "verdict": "THIN: 21 transitions constrain rank 11 of 405 features, so the null space has dimension 394 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 405,
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
     
```

The full proposal stream is 1956 rows in `candidates.jsonl`.

## The manual as it stands

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

## The playbook as it stands

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

## Why you are being called: the surprises that fired

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "15bde6867a07a78f",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'e260ba2228378b61', the world answered '8a0fb5148b5adfb0'

```json
{
 "action": 2,
 "expected_bits": 1.394848870026,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 5.087463,
 "manual_predicted": "e260ba2228378b61",
 "n_hypotheses": 34,
 "n_survivors": 1,
 "observed": "8a0fb5148b5adfb0",
 "probe_id": "P-13",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '01006a6a9e21beca', the world answered '2bdbfae66570eec5'

```json
{
 "action": 5,
 "expected_bits": 2.2195282823,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 3.5025,
 "manual_predicted": "01006a6a9e21beca",
 "n_hypotheses": 34,
 "n_survivors": 3,
 "observed": "2bdbfae66570eec5",
 "probe_id": "P-14",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '44c44660a53cf5d4', the world answered '0db510635e263539'

```json
{
 "action": 2,
 "expected_bits": 1.955012006402,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 5.087463,
 "manual_predicted": "44c44660a53cf5d4",
 "n_hypotheses": 34,
 "n_survivors": 1,
 "observed": "0db510635e263539",
 "probe_id": "P-15",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '3a11719074841328', the world answered '4c57486b12b722d4'

```json
{
 "action": 5,
 "expected_bits": 2.273661689922,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 3.5025,
 "manual_predicted": "3a11719074841328",
 "n_hypotheses": 34,
 "n_survivors": 3,
 "observed": "4c57486b12b722d4",
 "probe_id": "P-16",
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
  "detail": "17/17 transitions replay exactly",
  "matched": 17,
  "ok": true,
  "transitions": 17
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
  "detail": "no (state, action) among 18 x 5 admitted two rules, and all 90 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 90,
  "pairs_nominal": 90,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 18,
  "states_reconstructed": 18,
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
# theory.dsl -- world observed for 22 states / 21 transitions
#   RESET, A1 A2 A3 A4 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5.
# 81 cells have ever changed; this manual names and owns all 81.
#
# WHY THIS ROUND EXISTS, IN ORDER OF WHAT IT IS WORTH.
#
# 0. THE MANUAL REACHED THE COMPILER AND PASSED EVERYTHING. certify reports
#    replay 17/17 exact, responsibility 0 cells unexplained of 4096, ambiguity
#    0 clashes over 90 adjudicated pairs, no step crash. The two-round
#    formatting bleed is closed. The remaining loss is NOT at my desk, and
#    that changes what this round is allowed to blame.
#
# 1. FOUR TRANSITIONS ARRIVED AND THEY WERE THE SAME LAP AGAIN: t18 A2,
#    t19 A5, t20 A2, t21 A5. Burns at (63,55) and (63,54), the exact two cells
#    named in advance, in order. Gains 5.087463 for action 2 twice and 3.5025
#    for action 5 twice. THE ADVANCE PREDICTION CASHED IN FULL FOR THE SECOND
#    ROUND RUNNING. Zero new mechanism. Every rule edit below is a count.
#
# 2. THE FINDING OF THIS ROUND, AND IT IS THE REAL EXPLANATION OF NINE
#    IDENTICAL LAPS. The probe ranker scores expected bits over {this manual,
#    its ablations, inert}. An ablation removes rules, so it can only ever
#    predict FEWER changes, never more. Therefore for any state-action pair on
#    which THIS MANUAL PREDICTS IDENTITY, every ablation predicts identity and
#    `inert` predicts identity: all 34 hypotheses agree and the expected gain
#    is zero. A MANUAL CANNOT PROBE ITS OWN SILENCES. And at spawn exactly one
#    key has a live rule (key 2); at lattice (2,2) exactly one key has a live
#    rule (key 5). The nine-lap loop is not the meter's doing and not bad
#    luck -- IT IS THE RANKER FOLLOWING THE ONLY NON-SILENT ACTION AT EACH OF
#    THE TWO STATES MY RULES CAN REACH. See
#    the_ranker_can_only_buy_what_my_rules_already_fire_on, and its twin
#    the_playbook_and_the_ranker_are_exactly_anti_aligned: every probe my
#    playbook ranks is a probe the ranker scores at zero, by construction.
#
# 3. A SECOND CONSEQUENCE, WHICH SEALS THE OPEN QUESTION I HAVE BEEN CHASING
#    FOR FIVE ROUNDS: the loop presses key 2 at even indices and key 5 at odd
#    ones. Reading A (burn iff key 2 or 4) and reading B (burn iff even index)
#    therefore agree on EVERY command the ranker is capable of choosing. The
#    meter confound is self-sustaining and will never break from inside the
#    loop. See the_loop_pins_key_to_parity_and_therefore_seals_the_meter.
#
# 4. SHARPER EVIDENCE FOR THE GAIN ARTEFACT. The four probes this round report
#    expected_bits 1.394849, 2.219528, 1.955012, 2.273662 -- all different,
#    including the two action-2 probes -- while realised information_gain came
#    back 5.087463, 3.5025, 5.087463, 3.5025. A PRIOR THAT MOVES AND A
#    POSTERIOR COLLAPSE THAT DOES NOT IS EXACTLY WHAT "THE NUMBER MEASURES MY
#    MANUAL'S FIXED GEOMETRY" PREDICTS.
#
# 5. THE ONE MONOTONE QUANTITY. Everything in this world cycles except row 63.
#    10 cells burned, 54 remain. Nine laps cost seven of them.
#
# EXPECTED REPLAY: 21/21.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t21 compress: 45]
  Vacated [segment: dynamic_colour_5 ev: t2-t21 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21 compress: 3]

events:
  event recolored(o, c)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20 cov: 216/216]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20 cov: 216/216]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21 cov: 216/216]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21 cov: 216/216]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12,t14,t16,t18,t20 cov: 8/8]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21 cov: 40/40]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21 cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21 cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21 cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21 cov: 5/5]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21 cov: 5/5]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13,t17,t21 cov: 5/5]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13,t17,t21 cov: 15/15]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19 cov: 32/32]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11,t15,t19 cov: 32/32]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11,t15,t19 cov: 4/4]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11,t15,t19 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 45 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: inferred-from-replay]
  invariant board_cells count(board) = 4015 [status: counted]
  invariant meter_cells_burned_right_now count(Glyph9, color = 1) = 10 [status: state-dependent-not-an-invariant]

  theorem the_ranker_can_only_buy_what_my_rules_already_fire_on "THE FINDING OF THIS ROUND AND THE FIRST COMPLETE EXPLANATION OF NINE IDENTICAL LAPS. The probe reports name their own hypothesis space: every hypothesis is the manual or an ablation of it, plus inert, 34 of them. An ablation DELETES rules. A deleted rule cannot fire, so an ablation predicts a SUBSET of the manual's changes and never a superset. Now take any state-action pair on which the manual predicts identity. The manual changes nothing; every ablation therefore changes nothing; inert changes nothing. ALL 34 HYPOTHESES AGREE, THE EXPECTED GAIN IS ZERO, AND THE ACTION CANNOT BE RANKED ABOVE ANY ACTION WITH A LIVE RULE. So: A MANUAL CANNOT PROBE ITS OWN SILENCES. Apply it to this board. At spawn, key 2 fires 48 body pixels; key 5 fires nothing, because no Vacated renders 9 and no Glyph9 renders 5; keys 1, 3, 4 fire nothing. EXACTLY ONE LIVE KEY. At lattice (2,2), key 5 fires 71 pixels; key 2 fires nothing, because no Glyph9 renders 9 with floor six rows below and no Vacated renders 5; keys 1, 3, 4 fire nothing. EXACTLY ONE LIVE KEY. The loop is therefore not a preference the ranker has and not the meter's doing -- IT IS THE ONLY PATH THROUGH THE STATE SPACE ON WHICH ANY HYPOTHESIS DISAGREES WITH ANY OTHER. Seventeen consecutive commands, t5 through t21, are drawn from {A2, A5} and the two-state cycle predicts each one. I record the honest consequence rather than dressing it: CONSTRAINT 2 AND THIS RANKER TOGETHER GUARANTEE THAT THE MANUAL CAN NEVER BUY THE EXPERIMENT THAT WOULD EXTEND IT, WHENEVER THE EXTENSION LIES AT A PAIR THE MANUAL CURRENTLY CALLS SILENT. The lever that would break it is not mine: either a ranker that scores an UNWITNESSED silence above a witnessed noise, or a plan tier with a goal, or an arm that overrides. I refuse the lever that IS mine -- writing an unwitnessed rule so that key 2 predicts something at lattice (2,2) -- because that is exactly the fabrication constraint 2 exists to stop, and a manual that games its own ranker can be checked by nothing."
    [depends: the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease, the_loudest_forged_silence_is_not_at_spawn  probe: pending]

  theorem the_playbook_and_the_ranker_are_exactly_anti_aligned "The corollary, and it explains five rounds of a playbook that never bound anything. My playbook ranks by keys_whose_inertness_here_rests_on_no_witness -- that is, by actions the manual PREDICTS SILENT. The ranker scores expected bits, which is ZERO for exactly those actions. THE TWO CRITERIA ARE NOT MERELY DIFFERENT, THEY ARE COMPLEMENTS: every command my playbook puts first is a command the ranker puts last, by construction and not by accident. Check it on this frame. First-ranked A3 at spawn: manual predicts identity, expected bits zero. Second-ranked A5 at spawn: manual predicts identity, expected bits zero. Third-ranked A2 at lattice (2,2): manual predicts identity, expected bits zero. Fourth-ranked A6 or A7: no rule mentions them, identity, zero. And the command the playbook explicitly lists under WHAT NOT TO PRESS, A2 at spawn, is the unique action with a live rule at the state the arm is in. I am not going to keep writing prunes as though they were filters. THE PLAYBOOK IS A CLAIM ABOUT WHAT SHOULD BE SEARCHED, AND ON THIS BOARD IT IS THE EXACT NEGATION OF WHAT IS SEARCHED. Saying that once, clearly, is worth more than another twenty prune lines."
    [depends: the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: pending]

  theorem the_loop_pins_key_to_parity_and_therefore_seals_the_meter "The second corollary, and it retires a question I have carried for five rounds as though a command would eventually settle it. The loop is: body at spawn on even command indices, key 2 the only live key there; body at lattice (2,2) on odd indices, key 5 the only live key there. So the ranker presses key 2 at every even index and key 5 at every odd index, FOREVER. Reading A of the meter says a burn happens iff the key is 2 or 4. Reading B says iff the index is even. On the loop, key-2-ness and even-ness are the same predicate. THE TWO READINGS AGREE ON EVERY COMMAND THE RANKER IS CAPABLE OF CHOOSING, so the confound is not thin evidence waiting to thicken -- IT IS SELF-SUSTAINING, and twenty-one transitions have produced ten burns at indices 2,4,6,8,10,12,14,16,18,20 under keys 2,4,2,2,2,2,2,2,2,2 and eleven non-burns at indices 1,3,5,7,9,11,13,15,17,19,21 under keys 1,3,5,5,5,5,5,5,5,5,5 with not one divergence. The separating observation is unchanged and now provably unbuyable from inside the loop: ANY press of key 1, 3 or 5 at an even index. I encode reading A because it is the only one this grammar can express, and I read the answer off the RAW DIFF if it ever comes, because under reading B the burn is undrawable by my manual anyway."
    [depends: the_ranker_can_only_buy_what_my_rules_already_fire_on, meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_realised_gain_is_pinned_while_the_expected_gain_moves "NEW AND SHARPER THAN LAST ROUND'S VERSION. The four probes report expected_bits 1.394848870026 (action 2), 2.2195282823 (action 5), 1.955012006402 (action 2), 2.273661689922 (action 5) -- FOUR DIFFERENT NUMBERS, and crucially the TWO ACTION-2 PROBES DIFFER FROM EACH OTHER by more than half a bit. The realised information_gain came back 5.087463, 3.5025, 5.087463, 3.5025, to six decimals, for the seventh time each. A PRIOR THAT MOVES WITH THE STATE AND A POSTERIOR COLLAPSE THAT DOES NOT IS PRECISELY THE SIGNATURE OF A QUANTITY THAT IS MEASURING THE FIXED GEOMETRY OF MY MANUAL AGAINST ITS OWN ABLATIONS PLUS A CONSTANT ONE-PIXEL MISS, rather than measuring the world. n_survivors corroborates: action 2 leaves exactly 1 survivor every time, action 5 leaves exactly 3, in every state and both panel configurations. I note one thing I cannot explain and do not pretend to: 34 hypotheses over 22 rules is not one ablation per rule, so I do not know how the ensemble is built, and I say so rather than inventing an account of it. OPERATIONAL CONSEQUENCE, UNCHANGED AND NOW UNARGUABLE: A REPEATED-IDENTICAL INFORMATION GAIN IS ZERO INFORMATION."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: passed]

  theorem the_meter_is_the_only_monotone_quantity_in_this_world "Worth stating plainly because it is the only thing that makes the loop expensive. Body position cycles between two lattice cells. The panel cycles between two configurations. The state count says so: 22 states, 20 distinct, and the only two collisions are the ancient sterile pair at t0/t1 and t2/t3 -- every later state is nominally distinct ONLY because row 63 has one more cell burned. Ten cells are burned, columns 54 through 63; FIFTY-FOUR REMAIN. Nine laps cost seven of them, so a lap costs one burn and two commands, and the loop can run about 108 more commands before row 63 is fully colour 1. What happens then is not in evidence and I will not guess. But a quantity that only ever moves one way, in a world where everything else returns, is either a budget or a timer, and either way the arm is spending it at one cell per two commands to learn nothing. That is the honest price of the fixed point above."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot, the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: pending]

  theorem the_two_rounds_i_lost_were_both_lost_at_my_own_desk "STATUS CHANGED THIS ROUND AND THE CHANGE IS GOOD NEWS. Two earlier rounds were lost at this desk: one to a goal clause counting a type with zero instances, which the compiler refused outright, and one to a reply that carried no theory block at all. The discipline that followed -- emit all three blocks first, worry about content second -- HELD. certify now reports replay 17/17 exact, responsibility 0 of 4096 cells unexplained, ambiguity 0 clashes over 90 adjudicated pairs, no step crash, first_divergence null. The manual compiles, installs, and draws every pixel of every frame it was shown. THE GENERAL RULE STANDS AND IS NOW CONFIRMED RATHER THAN MERELY ARGUED: a mediocre manual that compiles outperforms an excellent one that does not by an unbounded margin, because the mediocre one gets corrected by the next frame and the excellent one gets corrected by nothing. certify's numbers describe an 18-state snapshot of a 22-state world -- that is the ordinary one-round lag and not a defect, and I claim nothing from it about t18 through t21."
    [depends: a_declaration_is_only_as_true_as_the_arm_can_seat_it  probe: passed]

  theorem the_advance_prediction_cashed_and_the_artefact_is_now_established "Second consecutive round in which the written-in-advance prediction cashed in full. I wrote, before seeing the frames: the body is at spawn, the panel is in configuration B, the next burn lands on (63,55), pressing ACTION2 draws 48 body pixels correctly and zero meter pixels, the manual is refuted by exactly one cell, the gain is reported as 5.087463 again with nothing learned. t18 burned (63,55) and t20 burned (63,54), the two cells named in order; P-13 and P-15 report action 2 at 5.087463; P-14 and P-16 report action 5 at 3.5025. Seven and seven now, to six decimals, across nine world states with nine different meter counts and both panel configurations. A quantity that measured the world would vary with the world."
    [depends: the_realised_gain_is_pinned_while_the_expected_gain_moves  probe: passed]

  theorem the_four_refutations_are_one_defect_and_i_am_again_installing_nothing "P-13 and P-15 are action 2; P-14 and P-16 are action 5; heuristic_miss is the goal and is answered separately. The action-2 divergence is one cell each time and I can name it: t18 changed 49 cells over rows 8-63 cols 14-55, being 48 body pixels plus the burn at (63,55); t20 changed 49 over cols 14-54, being 48 body plus (63,54). All 48 body pixels sit on the spawn ring and the ring one lattice cell south, both fully instanced, and key2_body_leaves and key2_body_arrives draw them exactly, now nine times each. The unburned frontier cell was board at the moment of the press and held no instance, so no event in this language could touch it. The action-5 divergence contains no new cell at all: t19 and t21 each changed 71 cells over rows 1-18 cols 1-18, being 48 body plus 23 panel, and every one is fired by exactly one rule -- 24 by key5_body_clears, 24 by key5_body_respawns, and for the two panel directions either 8+3+3+3+1+1+1+3 forward or 8+3+8+1+3 reverse, each summing to 23 with nothing over. THERE IS NO RULE TO ADD FOR ANY OF THE FOUR. I refuse to answer them with a rule and say so plainly, because inventing one is how two earlier rounds were spent."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot, the_probe_tier_rolls_my_state_forward_and_never_resyncs  probe: passed]

  theorem the_probe_tier_rolls_my_state_forward_and_never_resyncs "Action 5 has no undrawable cell in it: at t19 and t21 the 71 changed cells are all instanced and all fired by exactly one rule, so a probe predicting from the OBSERVED frame would predict action 5 exactly and P-14 and P-16 would not exist. They do exist, at an identical gain, for the fourth and fifth time. THE LEADING READING IS THEREFORE THAT THE PROBE PREDICTS FROM THE MANUAL'S OWN ROLLED-FORWARD STATE, which already carries the burn the manual could not draw at the preceding action 2. If that is right, THE DEBT IS CUMULATIVE AND PERMANENT: once the manual misses one pixel it is behind for every subsequent action, so every future command looks refuted whatever it is, and no edit repairs it because the missed pixel is undrawable by construction. n_survivors = 3 for action 5 against 1 for action 2 is consistent with this -- an ablation of my manual fits the rolled-forward observation better than my manual does, which is what a state offset looks like from the ensemble's side. The mitigation is unchanged and free: under reading A of the meter the debt only grows on keys 2 and 4. I record the competing reading honestly: the hash might cover something beyond the frame, in which case the action-5 refutations mean something I have not found. The discriminating observation is a press of action 5 immediately after a press that burned nothing -- and the_loop_pins_key_to_parity_and_therefore_seals_the_meter now says the ranker will never buy it."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot, the_loop_pins_key_to_parity_and_therefore_seals_the_meter  probe: pending]

  theorem the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease "My answer to heuristic_miss, which has now fired six times, and it is unchanged because the arithmetic is unchanged. The surprise says declaring the winning condition is the highest-value edit available. TESTED AND FALSE ON THIS BOARD. Suppose I could write a sound goal. The plan tier reaches it by searching MY compiled rules. Enumerate what my rules can do: key2_body_leaves and key2_body_arrives move the body from spawn to one cell south, key5_body_clears and key5_body_respawns move it back, the panel rules toggle 23 panel pixels, the burn rules are ungroundable. THAT IS THE WHOLE REACHABLE SET: TWO LATTICE CELLS AND TWO PANEL CONFIGURATIONS. So the only goals that could ever return sat are goals satisfied inside the loop, and sat-inside-the-loop is strictly WORSE than unsat: unsat leaves the arm probing, while sat makes it commit and declare success one lattice cell from where it started. I re-checked the four candidates the grammar admits over the four types that carry instances. count(Glyph9, color = 5) = 24 means the body is off spawn: not a win. count(Vacated, color = 9) = 24 is the same thing from the other side. count(Glyph9, color = 1) = 64 exceeds the 45 instances that exist and can never be true. count(Spent) = 0 is constant-false because Spent always has 9 instances. THEREFORE I DECLINE THE GOAL SECTION FOR THE FOURTH TIME AND I NAME WHAT WOULD END THE DECLINING: one observation in which the body occupies a THIRD lattice cell. That single observation seats instances on 24 cells that have never changed, extends the transition model past the loop, and is the same observation that eventually makes the socket writable. THE GOAL IS BOUGHT WITH A COMMAND. NO EDIT CAN SUBSTITUTE -- and this round I can say something stronger and worse about which command, in the_ranker_can_only_buy_what_my_rules_already_fire_on."
    [depends: the_goal_i_still_cannot_write_is_the_real_one, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_loudest_forged_silence_is_not_at_spawn "The cheapest large error in this manual, and this round it is promoted from a curiosity to the hinge of the whole fixed point. Ask what my compiled rules predict for ACTION2 pressed with the body ONE CELL SOUTH of spawn, at lattice (2,2), a cell the body has now occupied nine times. key2_body_leaves grounds only on Glyph9 and requires colored(?p, 9): the spawn ring renders 5 when the body is away, the ten meter cells all render 1, slot 1 renders 2 or 9 with nothing but background six rows below it, so NO GLYPH9 INSTANCE SATISFIES IT. key2_body_arrives grounds only on Vacated and requires colored(?v, 5): the lower ring renders 9 when the body stands there, so NO VACATED INSTANCE SATISFIES IT EITHER. THE COMPILED STEP IS TOTAL, SO MY MANUAL ASSERTS THAT ACTION2 AT LATTICE (2,2) DOES NOTHING. That is almost certainly false: rows 20-24 are floor from column 13 to column 31, so lattice (3,2) is open, and one press of action 2 has moved the body exactly one lattice cell south on nine consecutive occasions over open floor. AND BECAUSE MY MANUAL ASSERTS THAT SILENCE, THE RANKER SCORES THE COMMAND AT ZERO AND WILL NEVER BUY IT -- so the silence is not merely untested, it is UNTESTABLE FROM INSIDE, and it is precisely what forces key 5 at every odd index and closes the cycle. Twenty-one commands and no one has pressed action 2 twice in a row. I do NOT install a rule for it. The rule would be over Vacated at colour 9 with floor six rows below, it has ZERO witnesses because every key-2 press in the log was made from spawn, and half its divergence would fall on rows 20-24 columns 14-18, twenty-four cells that have never changed and therefore hold no instance. The price is advertised, not hidden, and constraint 2 is the reason it stays advertised rather than paid."
    [depends: the_ranker_can_only_buy_what_my_rules_already_fire_on, silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged  probe: pending]

  theorem the_burn_frontier_is_a_permanent_one_pixel_blind_spot "Row 63 is a 64-cell colour-9 bar that burns one cell at a time from the right. TEN cells are burned and the current frame shows them: columns 54 through 63 render 1, columns 0 through 53 render 9. The order was (63,63) at index 2 under key 2, (63,62) at 4 under key 4, then (63,61), (63,60), (63,59), (63,58), (63,57), (63,56), (63,55), (63,54) at indices 6, 8, 10, 12, 14, 16, 18, 20, every one under key 2. The eleventh burn will land on (63,53). (63,53) has never changed in twenty-two frames, so it is board, so it holds no instance, so NO EVENT IN THIS LANGUAGE CAN TOUCH IT -- recolored takes an object as its first argument and there is no object there. Therefore my manual predicts, and must predict, that the eleventh press of ACTION2 burns nothing, and the world will burn (63,53) and the manual will be wrong by exactly one pixel. Then (63,53) becomes dynamic, the arm seats a Glyph9 on it, replay draws the burn retroactively, certify reports a perfect replay, and the cycle repeats on (63,52). THAT IS WHY certify SAYS THE REPLAY IS EXACT WHILE THE PROBE DESK SAYS THE MANUAL WAS WRONG: they ask about different times. Replay looks backwards through a census that already contains the burned cell; prediction looks forwards through one that cannot. All ten meter instances currently render 1, so meter_burn_key2_next and meter_burn_key4_next have no grounding left and can only ever fire in replay. 54 cells remain unburned."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem no_goal_section_and_the_exact_enumerated_reason "A goal may say count over a declared type, optionally filtered by colour, or an instance's pos equal to a landmark. The types carrying instances are Glyph9 with 45 cells -- 8 slot-1 ring pixels, 3 underline-1 pixels, the 24 spawn-ring pixels, 10 burned meter cells -- Vacated with the 24 pixels of the ring one lattice cell south, Spent with the 9 pixels of slot 2, and Dark with the 3 pixels of underline 2. EVERY INSTANCE I HAVE IS IN THE PANEL, ON THE SPAWN RING, ON THE RING ONE CELL SOUTH, OR ON THE METER, and none is within thirty rows of the socket. The pos form is dead for a separate reason: this world never MOVES anything, every rule in this manual is a recolour, no instance's pos has changed in twenty-two states, so X.pos = landmark is a constant for every X I can declare. What unlocks the goal line is an OBSERVATION and not an edit."
    [depends: the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease, the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: passed]

  theorem the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught "Kept because it is the reason a whole earlier round was lost and because it generalises. The compiler refused the entire manual over one clause, a count over a type with zero instances, saying: this level declares no instance of that type, so the count is 0 on every state and the clause decides nothing. A COUNT OVER A TYPE WITH ZERO INSTANCES IS NOT A FALSE PREDICATE, IT IS A REFUSED CLAUSE. The general form: THE GOAL LANGUAGE CAN ONLY SPEAK ABOUT CELLS THAT HAVE ALREADY CHANGED, because only those carry instances -- the same wall as the burn frontier met from the other side. One consequence I reconsidered again this round and again REJECT: declaring a colour-8 type as INSURANCE, so that the first comb pixel to change would already have an owner. The declaration alone was accepted last time and only the count was refused, so it probably compiles -- but the arm would seat ZERO instances of it today, which is the exact configuration that killed a round before, and the two costs are wildly asymmetric. If I am right I save one round of a responsibility warning; if I am wrong I lose an entire round of every tier, which has now happened twice. An unexplained pixel is a defect the next desk repairs in one round. An uncompilable manual is a round nobody gets back."
    [depends: a_declaration_is_only_as_true_as_the_arm_can_seat_it  probe: passed]

  theorem dynamic_census "Exactly 81 cells have ever changed and every one has an owner. 23 are the panel: slot 1 at rows 1-3 columns 1-3 contributes its 8 ring pixels, its centre (2,2) rendering colour 0 in BOTH configurations and therefore board; underline 1 is row 5 columns 1-3, three cells; slot 2 at rows 1-3 columns 5-7 contributes all NINE cells, centre included, because (2,6) renders 1 in configuration A and 0 in B; underline 2 is row 5 columns 5-7, three cells. 24 are the spawn ring, rows 8-12 columns 14-18 minus the aperture (10,16), which has never changed and is board. 24 are the same ring six rows south, rows 14-18 columns 14-18 minus its aperture (16,16). 10 are the burned right end of row 63, columns 54 through 63. 23+24+24+10 = 81 = dynamic_cells exactly, and 4096-81 = 4015 = constant_cells exactly. By frame-0 colour: 45 colour-9 being 8 slot-1 ring plus 3 underline-1 plus 24 spawn ring plus 10 meter, 9 colour-1 being slot 2 solid in configuration A, 24 colour-5 being the lower ring which was floor at frame 0, and 3 colour-0 being underline 2 dark at frame 0. 45+9+24 = 78 = cells_needing_an_owner exactly. Every one of these four sums moved by exactly the two meter cells burned this round and by nothing else."
    [probe: passed]

  theorem the_cascade_length_reads_the_panel_and_it_is_now_nine_for_nine "ACTION2 pressed with the panel in configuration A returns SEVEN internal frames: t2, t8, t12, t16, t20. Pressed in configuration B it returns NINE: t6, t10, t14, t18. NINE PRESSES, NINE CORRECT, no counterexample, and the configuration before each press is fixed by the alternation ACTION5 drives -- A,B,A,B,A,B,A,B,A in press order. All nine ACTION5 presses returned 9 frames regardless of configuration. THE NET DISPLACEMENT IS IDENTICAL IN ALL NINE ACTION2 PRESSES -- 49 cells changed each time, 24 out, 24 in, one burn, six rows south, one lattice cell -- so what the panel changes is the ANIMATION and not the distance, at least over open floor. My semantics say cascade single_frame, so I compare only the net and this costs me no replay accuracy; I record it as an observation my own semantics discard."
    [depends: key2_body_arrives  probe: passed]

  theorem the_panel_is_a_two_slot_mode_selector_and_the_mode_may_gate_terrain "The reading I hold, stated as a reading, re-read pixel by pixel against the current frame. Two 3x3 tokens sit at rows 1-3 columns 1-3 and columns 5-7, with a 3-cell underline beneath each at row 5. The underline of exactly one slot is lit colour 9 at any time and ACTION5 moves the light: configuration A lights underline 1, configuration B lights underline 2, and in twenty-one transitions I have never seen both lit or neither. Right now row 1 reads 222 at columns 1-3 and 999 at columns 5-7, row 2 reads 2,0,2 and 9,0,9, row 3 reads 222 and 999, row 5 reads 000 and 999 -- slot 1 a hollow colour-2 ring with underline 1 dark, slot 2 a hollow colour-9 ring with a dark centre and underline 2 lit. CONFIGURATION B. The token in the LIT slot is always drawn as a HOLLOW colour-9 ring with a dark centre, which is the shape of the body itself, a rigid block with a one-pixel aperture. The token in the unlit slot differs by slot: slot 1 unlit is a hollow colour-2 ring, slot 2 unlit is a SOLID colour-1 block with no aperture. So the panel says two avatars exist, this is the one you are driving, and the other one has a different shape -- and a solid avatar with no aperture could not show the socket pip through itself. Joined to the cascade finding at nine for nine I read the two slots as two modes of travel. THE PAYOFF IF THIS IS RIGHT IS THE WHOLE LEVEL: the sole route south is blocked by the comb at lattice (6,2), 23 of whose 25 pixels render colour 8, and if the modes differ in what terrain they cross then the comb is a mode problem and not a switch problem. I hold it at pending and note the competing reading honestly: 7 versus 9 frames could be nothing but two draw speeds."
    [depends: the_cascade_length_reads_the_panel_and_it_is_now_nine_for_nine, the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem action5_is_return_to_spawn_or_north_and_twenty_one_transitions_cannot_split_them "ACTION5 has now been pressed NINE times, at t5, t7, t9, t11, t13, t15, t17, t19 and t21, and every single one was pressed from lattice (2,2) with the body one cell south of spawn, and every single one put the body back at (1,2). Reading NORTH says ACTION5 steps one lattice cell up. Reading RETURN says ACTION5 sends the body home from wherever it is. The body has stood in exactly two lattice cells in twenty-two states and those two are adjacent, so the readings have made identical predictions on every frame ever observed. A third reading is observationally identical and changes the strategy: ACTION5 SWAPS which of two avatars you drive and the incoming avatar always starts at spawn. I tested the memory-preserving version of that against the transitions that could refute it: if the swap preserved each avatar's position then the incoming avatar would already have been at (2,2), zero body cells would have changed and only 23 panel cells would have moved. 71 changed at t7, t11, t15, t19 and t21. So swap-with-memory is REFUTED five times over and swap-with-reset survives, indistinguishable from RETURN. THE SEPARATOR NEEDS THE BODY TWO CELLS FROM HOME, which needs the third lattice cell, which needs a command the ranker cannot buy. THE STAKES: eighteen of the last twenty commands were a two-command loop that burned nine meter cells and moved the body nowhere."
    [depends: key5_body_respawns, key5_body_clears, the_loudest_forged_silence_is_not_at_spawn  probe: pending]

  theorem the_loop_ran_two_more_times_and_i_now_know_exactly_why "Recorded as a process fact because a desk that hides this is useless, and this round it stops being a lament and becomes a derivation. t18 A2, t19 A5, t20 A2, t21 A5. Body south, home, south, home. Panel B, A, B, A. Two meter cells burned. Zero new mechanism. The previous playbook ranked ACTION3 first in capital letters, listed ACTION2 at spawn under WHAT NOT TO PRESS, and carried a hard prune against the cycle by name; none of it bound the ranker, for the third round running. THE MECHANISM IS NOW FULLY DERIVED AND IT IS TWO INTERLOCKING FIXED POINTS. FIRST: with no goal the plan tier cannot return sat, so the probe tier chooses; the probe tier scores expected bits over the manual and its ablations; at spawn only key 2 has a live rule and at lattice (2,2) only key 5 has one, so at each of the two reachable states exactly one action has nonzero expected bits and the cycle is forced. SECOND, and reinforcing: the manual's undrawable frontier cell guarantees key 2 a large constant realised gain, so nothing about the outcome ever discourages the choice. Neither loop is a taste a prune can argue with. Seventeen consecutive commands from {A2, A5}. ACTION3 and ACTION4 have each been pressed exactly once, both at a cell where east and west were void, and the east key remains unnamed after twenty-one transitions."
    [depends: the_ranker_can_only_buy_what_my_rules_already_fire_on, the_playbook_and_the_ranker_are_exactly_anti_aligned  probe: passed]

  theorem the_goal_i_still_cannot_write_is_the_real_one "The win is the body standing in lattice (8,7), rows 50-54 columns 44-48, its 24 ring pixels rendering 9 and its aperture showing the pip at (52,46). Re-verified against the current frame. Those 24 cells render constant colour 5, so they are board and hold no instance; and colour 5 is already claimed by Vacated while the arm looks types up by colour alone, so a second colour-5 type would be indistinguishable from Vacated and would claim cells twice, which is the constraint-5 error. The goal I could write over Vacated once the socket goes dynamic, count(Vacated, color = 9) = 24, is already true whenever the body stands in lattice (2,2), so it names two states and one of them is not a win. So the manual carries the true winning condition in prose, here and in the playbook, and carries NO goal line at all. That is a stated gap and not an evasion."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem the_burn_rules_want_one_rule_and_the_grammar_forbids_it "meter_burn_key2_rightmost and meter_burn_key2_next are ONE law -- burn the leftmost burned-adjacent colour-9 cell of the bar, where the right board edge counts as burned -- split into two rules because the guard language has and and not but no or, and the two conditions rightof(?p) = wall and colored(rightof(?p), 1) cannot be joined. They are exclusive rather than merely different: where rightof(?p) is off-board there is no cell to render 1, so the colour test is false, and where rightof(?p) is a real cell it is not wall. So constraint 5 holds by construction and the cost is one duplicated line. meter_burn_key4_next has the same body as meter_burn_key2_next with a different key; the key-4 twin of the RIGHTMOST rule has no witness and can never get one now that (63,63) is burned, so it is not written. All three burn rules are UNGROUNDABLE going forward: all ten meter instances render 1, no Glyph9 instance renders 9 with a right neighbour rendering 1, and none will unless a future census extends the bar leftwards. They stay because they are what makes replay correct on t2 through t20. Note the consequence for the ranker: an ungroundable rule contributes no expected bits, so KEY 4 IS NOW A SILENT ACTION EVERYWHERE and is as unbuyable as keys 1 and 3."
    [depends: meter_burn_key2_rightmost, meter_burn_key2_next, the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: passed]

  theorem dark_may_have_no_instances "The one arithmetic gap in the census and I will not hide it. cells_needing_an_owner is 78 while dynamic_cells is 81, and the difference is precisely the three colour-0 cells of underline 2. Colour 0 is the background, and the arm instances every cell of a declared colour the board cannot explain; whether a dynamic cell whose frame-0 colour is the background counts as explained is not something I can settle from the brief. The indirect evidence is now direct enough to satisfy me: certify reports replay 17/17 exact over transitions that include t5, t9, t13 and t17, and key5_underline2_lights and key5_underline2_dims carry coverage on those; if Dark seated no instances those rules could not fire and each of those transitions would be wrong by three cells. I keep the theorem rather than promoting it to an invariant with status proven, because the reasoning is inference from a check rather than a reading of the arm."
    [depends: dynamic_census, the_two_rounds_i_lost_were_both_lost_at_my_own_desk  probe: passed]

  theorem the_spawn_probe_guard_is_carried_and_is_still_never_tested_negative "Thirteen panel rules carry colored(spawn_probe, 5), which reads cell (8,14) renders floor, which reads the body is not at home. In twenty-two states that atom has NINE positive witnesses -- t5, t7, t9, t11, t13, t15, t17, t19, t21, every one an ACTION5 pressed with the body away -- and ZERO negative witnesses, because ACTION5 has never once been pressed with the body at home. So the guard is doing no work I can demonstrate. Why keep it? Because it changes no prediction today and I can show that cell by cell: with the panel in configuration B, slot 1 renders 2, underline 1 renders 0, slot 2 renders 9 and underline 2 renders 9, so the eight forward rules are blocked by their colour tests whatever the body does; and the five reverse rules WOULD fire on exactly those colours, so with the body at home the guard is the ONLY thing blocking them. That is precisely the untested case, and the panel is in configuration B right now with the body at spawn. IF ACTION5 IS PRESSED AT SPAWN AND THE PANEL TOGGLES, THIS GUARD IS WRONG IN THIRTEEN RULES AT ONCE. It is the largest single refutation available on this board and it costs no meter cell -- and it has been unclaimed for five rounds for the reason now derived: because the guard blocks everything, my manual predicts identity for A5 at spawn, so the ranker scores the experiment at zero. THE MOST INFORMATIVE COMMAND ON THE BOARD IS THE ONE MY OWN MANUAL PRICES AT NOTHING."
    [depends: key5_slot1_lights, key5_slot1_dims, the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: pending]

  theorem the_action_map_after_twenty_one_transitions "WITNESSED. ACTION2 is SOUTH: nine times, t2, t6, t8, t10, t12, t14, t16, t18, t20, six rows south, one lattice cell, 48 cells each. ACTION5 puts the body at spawn from one cell south: nine times, t5 through t21 odd -- see action5_is_return_to_spawn_or_north for why that is not the same as knowing it is north. NEGATIVE INFORMATION, read off the map rather than off a rule. At spawn, lattice (1,2), north is void because rows 2-6 columns 14-18 render 0, west is void because columns 8-12 render 0, EAST is open floor because row 8 renders 5 from column 19 to column 43 and rows 9-12 render 5 from column 19 to column 38, and SOUTH is open. ACTION1 was pressed there at t1 and nothing changed, so ACTION1 IS NEITHER EAST NOR SOUTH. At lattice (2,2), rows 14-18, north was open and south was open because rows 20-24 columns 13-31 are floor, while east and west are void because rows 14-18 columns 20-24 and columns 8-12 render 0. ACTION3 at t3 and ACTION4 at t4 each moved nothing, so NEITHER IS NORTH AND NEITHER IS SOUTH. Combine: ACTION2 is south; ACTION1 is not east and not south; ACTION3 and ACTION4 are each west, or east-blocked-nowhere, and each remains compatible with east because east has never been open under either. EAST IS ACTION3 OR ACTION4 AND THERE IS NO THIRD CANDIDATE. TWENTY-ONE COMMANDS SPENT AND NOT ONE HAS TESTED THE EAST KEY, at a cell where east is four unbroken lattice cells of floor leading to the knob."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the five keys at spawn, where the body now stands. key(2) moves 48 body cells and burns one meter cell it cannot draw: witnessed nine times. key(1) inert: WITNESSED, t1, zero cells changed. key(3) inert at spawn: NO WITNESS -- pressed once, at t3, from one cell south, where east and west were both void. key(4) inert at spawn: NO WITNESS -- pressed once, at t4, from one cell south, where it burned a meter cell and moved nothing. key(5) inert at spawn: NO WITNESS AT ALL in twenty-two states; all nine presses were from one cell south. THREE OF FIVE SILENCES AT SPAWN ARE FORGED DEATH CERTIFICATES; two of the three are the east candidates and the third is the one that would refute thirteen rules' shared guard. Add the fourth and largest, at the other cell, in the_loudest_forged_silence_is_not_at_spawn. THE NEW AND BITTER PART: a forged silence is exactly what the ranker prices at zero, so the manual's forgeries are self-protecting. This is the entire argument for the next command and against pressing ACTION2 or ACTION5 from the loop again, and it is also the argument that no argument of mine will be heard."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: passed]

  theorem the_two_no_op_rules_fail_the_gain_test_and_i_say_so "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has exactly one witness, and each witnesses a transition on which zero cells changed. The manual would replay identically without them: constraint 3 is failed outright and I am not going to dress it up. The reason I keep them is smaller than the rule text: they put key(1) and key(3) into the manual's action alphabet, which is what certify's ambiguity check adjudicates over -- it reported 5 actions and 90 pairs, and without these two it would have reported 3. Deleting them removes information I can see for a saving I cannot measure. They change no prediction, so keeping them cannot cost a pixel, and they are the two cheapest deletions in this manual if a later desk wants them gone. I note one thing I checked and it did NOT save them: a rule that recolours a pixel to the colour it already has does not make its action non-silent for the ranker, because the successor state is identical, so these two rules do not buy key 1 or key 3 any expected bits."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "key2_body_leaves grounds on meter instances at row 63 whose sixth-below is row 69, and it must not fire there. It does not, because a colour test on an off-board cell is FALSE rather than an exception, and <cell> = wall is the sanctioned positive test. Every row and column discrimination in the eight forward panel rules is built from that one fact: the k-th above is off-board exactly when k exceeds the row, so panel row 1 is above-twice equals wall; row 3 is a colour test on above-twice, false for row 1 precisely because a colour test on an off-board cell is false; row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column -- column 5 is leftof-six equals wall, column 6 is leftof-seven equals wall with a colour test on leftof-once, column 7 is a colour test on leftof-twice -- and those three are pairwise exclusive, which is what keeps constraint 5 satisfied on (2,5), (2,6) and (2,7). I re-checked the case that looks dangerous: leftof-seven from column 5 is also off-board, so centre_darkens and row2_left_lights are separated NOT by that atom but by colored(leftof(?s), 1), which is false at column 5 because (2,4) is a separator rendering 0. It also protects meter_burn_key2_rightmost from meter_burn_key2_next. Not one rule uses not, deliberately. certify reports 0 clashes over 90 adjudicated pairs, which is the check this theorem exists to survive."
    [depends: key5_slot2_centre_darkens, key2_body_leaves  probe: passed]

  theorem the_reverse_toggle_needs_only_a_colour_test_and_i_checked_every_clash "The five return rules are far shorter than the eight forward ones, because configuration B assigns a UNIQUE colour to each panel group within each declared type, which configuration A does not. In B with the body away: Glyph9 renders 2 on slot 1, 8 cells, and 0 on underline 1, 3 cells, and 5 on the spawn ring and 1 on the meter; Spent renders 9 on the slot-2 ring, 8 cells, and 0 on the slot-2 centre, 1 cell; Dark renders 9 on underline 2, 3 cells. So a bare colour test names each group exactly. I re-audited constraint 5 pair by pair with TEN meter cells burned, which is the case that could newly clash: all ten meter Glyph9 instances render 1, and colour 1 is claimed by no key-5 rule at all, so the meter cannot be swept into a panel rule. Colour 2 is claimed only by key5_slot1_lights. Colour 0 on a Glyph9 is claimed only by key5_underline1_lights and no other Glyph9 ever renders 0. key5_slot2_ring_resets takes Spent at 9 while all four forward slot-2 rules take Spent at 1: disjoint. key5_slot2_centre_resets takes Spent at 0, claimed by nothing else. key5_underline2_dims takes Dark at 9 while key5_underline2_lights takes Dark at 0: disjoint. In configuration A none of the five can fire; in configuration B none of the eight forward rules can fire. The two directions are separated by the frame itself, which is why no phase counter is needed."
    [depends: key5_slot1_lights, key5_underline2_dims  probe: passed]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "cascade_lengths are 1, 7 and 9. Every no-op returned one frame; ACTION2 returned 7 or 9 depending on the panel; ACTION5 returned 9 every time. A move is animated one row per internal frame and the world reports the whole animation for a single action; cascade single_frame compares only the net, so up to eight intermediate frames per command are discarded unread, and I record that as a limitation of my own semantics rather than of the world. The refutation I keep, now with nine witnesses: under a slide-until-blocked reading, ACTION2 at spawn would run the body south through rows 20-24 and 26-30 to the comb. It stopped after exactly six rows over open floor at t2, t6, t8, t10, t12, t14, t16, t18 and t20. ONE PRESS IS ONE LATTICE CELL, and every distance in the playbook rests on it."
    [depends: key2_body_arrives  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2 through 6R+6 by columns 6C+2 through 6C+6; rows and columns congruent to 1 modulo 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. Row 7 is floor from column 13 to column 43. R=1, rows 8-12, is floor from column 13 to column 43 except the knob block, so C=2,3,4,5 are open and C=6 holds the knob. R=2, rows 14-18, is floor at columns 13-19 and 25-31 only, so C=2 and C=4. R=3, rows 20-24, is floor from column 13 to column 31, so C=2,3,4. R=4 and R=5 are floor only at columns 13-19, so C=2. R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable. R=7 is C=2, plus a fragment of floor at row 48 columns 42-50 that is one row deep and cannot hold a body. R=8, rows 50-54, is floor from column 13 to column 48, so C=2 through C=7 are open. Separator rows 7, 13, 19, 25, 31, 37, 43 and 49 are floor across column 2 and separator column 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in twenty-two frames the body has occupied exactly TWO cells, (1,2) and (2,2)."
    [depends: the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed nine times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 columns 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 columns 43-49, row 55 columns 43-49, column 49 rows 49-55. Rows 49 and 55 are separator rows and columns 49 and 43 are separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted in colour 9, with the west wall at column 43 left as FLOOR for rows 50-54. Inside it, rows 50-54 columns 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, column 50 rows 49-56 is a one-cell strip of floor that leads nowhere. Overlay the body standing in lattice (8,7), 5x5 with an aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate: the game is won when the 24 ring pixels of rows 50-54 columns 44-48 render 9. The bracket has never changed in twenty-two frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally write a real goal line."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2), (1,3), (1,4), (1,5), (2,2), (2,4), (3,2), (3,3), (3,4), (4,2), (5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 columns 39-41, a stem pixel at (12,40), colour 8 filling column 40 from row 12 down to row 40, colour 8 filling row 40 from column 14 to column 40, and the comb teeth at rows 38-42 columns 14-18, which hold 23 colour-8 pixels and 2 colour-5 pixels at (39,14) and (41,14). It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Note also that the descending wire at column 40 is flanked by floor at columns 39 and 41 through the void rows, which is drawn deliberately and which I do not yet understand. Not one colour-8 pixel has moved in twenty-two frames. The first colour-8 pixel that changes turns this theorem into physics AND makes a goal line writable in the same instant."
    [depends: the_maze_is_a_six_pixel_lattice, the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 columns 32-36, is fully open floor and is separated from the knob's cell (1,6) at columns 38-42 only by separator column 37, which renders floor through rows 8-12. Lattice (1,6) contains ten colour-8 pixels, nine of them non-centre pixels of that cell -- the eight knob pixels other than its centre (10,40), plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while colour 8 is solid. Either colour 8 is walkable in one of the two panel modes, and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Twenty-one commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens, the_panel_is_a_two_slot_mode_selector_and_the_mode_may_gate_terrain  probe: pending]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because it is the permanent shape of every refutation this level will produce, and this round it bit three times again: the burn frontier, the refused goal, and the twenty-four cells of lattice (3,2) that make the loudest forged silence undrawable. To draw the next burn, or the first step onto fresh ground, or the socket, or to COUNT the comb, I would need an instance on a board cell. The arm offers exactly one lever, arc-instances all, and its documented behaviour is to instance every cell of that colour THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance, and the compiler will not let a clause count a type whose instance set is empty. I considered and REJECT the two workarounds again, and this round I costed the second properly. First, a second declared type on colour 9 without arc-instances: the arm looks types up by colour and nothing else, so it is indistinguishable from Glyph9, its seat is unspecified, and any cell it landed on would be claimed twice. Second, dropping the board declaration so that every cell of every declared colour is instanced: the arithmetic is fatal, because colour 0 covers roughly two thousand background cells and colour 5 roughly one thousand floor cells, so twenty-two rules would ground over some three thousand instances with constraint 5 needing a fresh pairwise audit against every one of them, in a single round, with no witnesses; and the concrete breakage is already known -- key2_body_leaves would ground on the socket bracket at (49,49), whose sixth-below (55,49) renders 5, and would recolour a wall on every ACTION2. So the manual heals ONE STEP BEHIND the world, permanently, and the correct way to read a refutation here is by its divergence set: where that set lies on cells that had never changed before the transition, the manual is not implicated."
    [depends: dynamic_census, the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_parity_and_cannot_say_or "Five expressive holes, and this round the first one turns out to be the expensive one. FIRST: there is no third outcome for a state-action pair -- not no change and not a named successor, but unobserved, the manual declines to predict. Rules produce events, absence of a rule produces identity, and the compiled step is total. So the three unwitnessed spawn silences and the one at lattice (2,2) are asserted in the same voice as the two witnessed ones, AND THE PROBE RANKER PRICES BOTH VOICES AT ZERO, which is the whole content of the_ranker_can_only_buy_what_my_rules_already_fire_on. A manual that could say I DO NOT KNOW WHAT KEY 3 DOES HERE would be a manual whose ablations disagreed on key 3, and the ranker would buy the experiment immediately. THIS IS NOW THE SINGLE MOST VALUABLE EXTENSION THE LANGUAGE COULD RECEIVE, ahead of instancing on constant cells. SECOND: if the meter runs on command parity, that law CANNOT be written here at any length, because the guard language reads pixels and the action name and there is no command counter and no phase pixel. THIRD: there is no or, which is why one burn law is two rules. FOURTH: THERE IS NO WAY TO SAY THAT A PIXEL WILL CHANGE WITHOUT NAMING AN OBJECT THAT OWNS IT, so a manual can never predict the frontier of its own knowledge. FIFTH: A GOAL CANNOT NAME A CELL THAT HAS NEVER CHANGED, so the winning condition of this level is unwritable until the body or the gate first disturbs it. Order of value to a future desk: an UNKNOWN outcome first, then instancing on constant cells, then a state counter, then or, then not."
    [depends: the_ranker_can_only_buy_what_my_rules_already_fire_on, the_loop_pins_key_to_parity_and_therefore_seals_the_meter  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1 through ACTION5 plus RESET; the alphabet is ACTION1 through ACTION7. Two commands are entirely unconstrained after twenty-two states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels changing colour, and never its precondition. Recording that effect is also what would make a goal line writable, since it is the event that turns comb cells dynamic. I note two countervailing risks plainly: actions_used lists only the five that have been tried, so it is no evidence that 6 and 7 exist; and since no rule of mine mentions them, my manual predicts identity for both, so the ranker prices them at zero and will not buy them either."
    [depends: no_goal_section_and_the_exact_enumerated_reason, the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: pending]

  theorem a_declaration_is_only_as_true_as_the_arm_can_seat_it "Kept because it cost three rounds in three different ways and because the discipline it produced held this round. First a landmark whose arc-cell comment was missing, which is a hard compile error; spawn_probe at (8,14) was the repair and it held. Then a type the arm could seat nowhere, where the arm accepted the DECLARATION and refused the COUNT. Then a reply that carried no theory block at all. THE GENERAL RULE, covering all three: before writing any clause, ask what the arm will seat for it, and if the answer is nothing, the clause is not conservative, it is fatal -- and before sending anything, ask whether the harness will read it at all, because a clause the harness never sees is not conservative either. certify's clean sheet this round is what the rule buys."
    [depends: the_two_rounds_i_lost_were_both_lost_at_my_own_desk  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter now reports 14 tracks with a POSITIVE gain of 6270 bits against a 17464-bit baseline, a 36 percent saving, and NEGATIVE gain of 93832 bits on the 57-track split-by-colour variant. I take the positive variant as corroboration rather than as structure. What I take is corroboration by FRAME INDEX, independent of my rules. obj1: colour 1, nine cells, 3x3, present 5 of 22 frames -- slot 2 solid, alive in configuration A. obj5 colour 2 first frame 5, obj6 colour 1 first frame 7, obj7 colour 2 first frame 9, obj8 colour 1 first frame 11, obj9 colour 2 first frame 13, obj10 colour 1 first frame 15, obj11 colour 2 first frame 17, obj12 colour 1 first frame 19, obj13 colour 2 first frame 21: that is the panel alternating exactly on the odd indices where ACTION5 was pressed, NINE flips, an independent witness for both toggle directions and for the fact that the last two rounds bought nothing but more of the same. obj0: colour 9, eight cells, 3x3, present all 22 -- the lit token. obj2: colour 9, three cells, 1x3 -- an underline. obj4 is the whole 64-cell bar of which 10 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. cegis_miner refuses every track and its verdict, the world does not narrate as one mover, is true of the arm and false of the world -- there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours. zero_space self-reports THIN in its own words: 21 transitions constrain rank 11 of 405 features, null space dimension 394, nearly every vector in it a law true over these states and unfalsified rather than confirmed. Its single global law is my census and nothing more. Nothing in the candidate stream proposes anything about colour 8, which is consistent with colour 8 never having changed."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me, and the previous two editions cashed in full. STATE: the body is at spawn, lattice (1,2). The panel is in configuration B -- slot 1 a hollow colour-2 ring, underline 1 dark, slot 2 a hollow colour-9 ring with dark centre, underline 2 lit. TEN meter cells are burned, columns 54 through 63; 54 remain. The next command index is 22, which is EVEN. THE HEADLINE PREDICTION IS ABOUT THE ARM AND NOT THE WORLD, AND IT IS THE ONE I MOST WANT TESTED: THE NEXT COMMAND WILL BE ACTION2, because the body is at spawn and key 2 is the only key with a live rule there, so every other key scores zero expected bits over an ensemble of ablations that all predict identity. If the next command is anything other than ACTION2, the_ranker_can_only_buy_what_my_rules_already_fire_on is wrong and I want to know that more than I want any pixel. PER-ACTION PREDICTIONS. ACTION2 at spawn: 48 body pixels drawn correctly, ZERO meter pixels drawn, the world burns (63,53), the manual is refuted by exactly one cell, the realised gain comes back 5.087463 and NOTHING IS LEARNED; if that number differs, the artefact reading is dead. ACTION5 at spawn: predicted identity by all thirteen guarded rules, and if the panel toggles instead then colored(spawn_probe, 5) is wrong in thirteen rules at once -- the largest single refutation available on this board, costing no meter cell. ACTION3 at spawn: predicted ZERO cells changed, with NO witness for that silence at this cell; if the body steps east I pay 48 pixels I have priced -- 24 arrival pixels on rows 8-12 columns 20-24 which have never changed and hold no instance, and 24 departure pixels which do hold Glyph9 instances but which no witnessed east-leaves rule can fire on. If it does not step, ACTION4 is east by elimination. ACTION2 pressed one cell SOUTH of spawn: predicted identity, and I expect that to be WRONG by 48 pixels with the body landing in lattice (3,2) -- the third lattice cell ever occupied, which seats 24 new instances and extends the transition model past the loop for the first time. ACTION1 at spawn: predicted identity, witnessed at t1, buys nothing. ACTION6 or ACTION7: entirely unconstrained, and one may be the click that presses the knob and thereby writes my goal line for me, or may not exist at all. METER: index 22 is even, so any press of key 1, 3 or 5 separates readings A and B -- reading A predicts no burn, reading B predicts (63,53) turns 1 -- and I predict that no such press will be made, because the loop pins key to parity."
    [depends: the_ranker_can_only_buy_what_my_rules_already_fire_on, the_loop_pins_key_to_parity_and_therefore_seals_the_meter, the_loudest_forged_silence_is_not_at_spawn  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Twenty-two states, twenty-one transitions:
#   RESET, A1 A2 A3 A4 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5.
#   t1  A1 at spawn        -> nothing
#   t2  A2 at spawn        -> body one lattice cell SOUTH (48) + burn (63,63)
#   t3  A3 one cell south  -> nothing (east and west both void there)
#   t4  A4 one cell south  -> burn (63,62) and nothing else
#   t5  A5 one cell south  -> body to spawn (48) + panel A->B (23)
#   t6..t21  the same two commands, EIGHT more times, alternating.
#   Burns since: (63,61) (63,60) (63,59) (63,58) (63,57) (63,56) (63,55) (63,54)
# BODY AT SPAWN, lattice (1,2). PANEL IN CONFIGURATION B. TEN meter cells
# burned, columns 54-63; 54 remain. Next command index is 22, EVEN.
# certify this round: replay 17/17 exact, 0 cells unexplained, 0 clashes.
# THE MANUAL IS SOUND. THE PROBLEM IS NOT THE MANUAL'S ACCURACY.
#
# ========= THE FINDING THAT CHANGES WHAT THIS BOOK IS FOR =========
# The probe ranker scores expected bits over {manual, ablations, inert}.
# An ablation DELETES rules, so it predicts a SUBSET of the manual's changes.
# Therefore on any pair where the manual predicts IDENTITY, all 34 hypotheses
# agree and the expected gain is ZERO.
#
#   A MANUAL CANNOT PROBE ITS OWN SILENCES.
#
# At spawn, exactly one key has a live rule: key 2.
# At lattice (2,2), exactly one key has a live rule: key 5.
# So the nine-lap loop is not a taste, not the meter, and not bad luck --
# IT IS THE RANKER FOLLOWING THE ONLY NON-SILENT ACTION AT EACH OF THE TWO
# STATES MY RULES CAN REACH. Seventeen consecutive commands from {A2, A5}.
#
# AND THE COROLLARY THAT INDICTS THIS BOOK:
#   THE PLAYBOOK AND THE RANKER ARE EXACTLY ANTI-ALIGNED.
#   I rank by "keys whose inertness rests on no witness" -- i.e. by actions
#   the manual predicts SILENT. The ranker prices exactly those at zero.
#   Every command ranked below is a command the ranker ranks last, by
#   construction. Five rounds of prunes have bound nothing and this is why.
#
# I am NOT going to fix this by writing an unwitnessed rule so that some other
# key predicts pixels. That is the fabrication constraint 2 exists to stop and
# a manual that games its own ranker can be checked by nothing. The lever is
# not mine. It belongs to whoever can (a) score an UNWITNESSED silence above a
# witnessed noise, or (b) hand the plan tier a goal, or (c) override the arm.
# The list below is written FOR THAT READER.
#
# ========= A SECOND CORROLARY: THE METER QUESTION IS SEALED =========
# The loop presses key 2 at every EVEN index and key 5 at every ODD index.
# Reading A (burn iff key 2 or 4) and reading B (burn iff even index) are the
# same predicate on the loop. Ten burns, eleven non-burns, zero divergence,
# and NO COMMAND THE RANKER CAN CHOOSE WILL EVER SPLIT THEM. I stop treating
# this as evidence that will thicken with time.
#
# ========= heuristic_miss, ANSWERED FOR THE SIXTH TIME =========
# Declaring a goal is NOT the highest-value edit, for an arithmetic reason:
#   THE PLAN TIER REACHES A GOAL BY SEARCHING MY COMPILED RULES, AND MY RULES
#   CAN ONLY REACH TWO LATTICE CELLS AND TWO PANEL CONFIGURATIONS.
# So the only goal that could return sat is one satisfied inside the loop, and
# sat-inside-the-loop is WORSE than unsat: unsat leaves the arm probing, sat
# makes it commit and declare success one lattice cell from spawn. All four
# candidates the grammar admits over the four instanced types fail:
# count(Glyph9,color=5)=24 and count(Vacated,color=9)=24 both mean only "body
# is off spawn"; count(Glyph9,color=1)=64 exceeds the 45 instances that exist;
# count(Spent)=0 is constant-false.
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
#
# ========= THE COST OF THE LOOP, IN THE ONLY CURRENCY THAT MOVES =========
# Row 63 is the ONLY monotone quantity in this world. Body position cycles;
# the panel cycles; 22 states but only 20 distinct, and the two collisions are
# the ancient sterile pair -- every later state is nominally new ONLY because
# one more meter cell burned. 10 gone, 54 left, one per lap, two commands per
# lap. About 108 commands of loop remain before row 63 is fully colour 1.
# What happens then is not in evidence and I will not guess.
#
# ========= THE RANKED LIST, FOR A READER WHO CAN ACT ON IT =========
# Every item here is priced at ZERO expected bits by the current ranker. That
# is the point: they are the four places the manual is most likely wrong.
#
# 1. THE EAST KEY, TESTED AT SPAWN. ACTION3 first, ACTION4 only if 3 is inert.
#    - Names a direction whichever way it answers. A2 is south (9 witnesses).
#      A1 was pressed AT SPAWN with east OPEN and moved nothing, so A1 is not
#      east. EAST IS A3 OR A4 and there is no third candidate. Both were
#      pressed once, from one cell south where east AND west are void, so
#      neither press could answer anything.
#    - Splits the meter at an even index -- the only kind of command that can.
#      READ IT OFF THE RAW DIFF, NOT OFF A REFUTATION FLAG.
#    - Kills a forged silence: three of five spawn silences have no witness.
#    - Is step one of the only route to the knob, four lattice cells east
#      along a row that is open floor the whole way.
#
# 2. ACTION5 AT SPAWN. Thirteen rules share colored(spawn_probe,5): NINE
#    positive witnesses, ZERO negative, because A5 has never been pressed with
#    the body at home. The body is at home NOW and the panel is in
#    configuration B -- exactly the configuration in which the five reverse
#    rules would fire if the guard were not blocking them. Manual predicts
#    identity. If the panel toggles anyway, THIRTEEN RULES ARE WRONG AT ONCE,
#    and it costs no meter cell. Unclaimed for five rounds.
#
# 3. ACTION2 PRESSED ONE CELL SOUTH OF SPAWN. The manual predicts NOTHING
#    happens -- no Glyph9 renders 9 there, no Vacated renders 5 -- and that is
#    almost certainly false: rows 20-24 are floor from column 13 to column 31
#    and one A2 press has moved the body one lattice cell south nine times
#    running. The body has stood on that cell nine times and nobody has tried.
#    THIS IS THE SILENCE THAT CLOSES THE CYCLE: because the manual asserts it,
#    the ranker prices it at zero, so key 5 is forced at every odd index.
#    It is the ONE command likely to put the body in a lattice cell never
#    occupied, and it is half the separator between "A5 is north" and "A5 is
#    return to spawn".
#
# 4. ACTION6 OR ACTION7. Never pressed, entirely unconstrained. In this family
#    one is usually a click, and the knob is a 3x3 target the body appears
#    unable to stand on. My manual could record such a command's EFFECT and
#    never its precondition -- but the effect is what makes the comb dynamic
#    and the goal writable. Honest risk: actions_used lists only what has been
#    tried, so it is no evidence these exist.
#
# ========= WHAT NOT TO PRESS, AND WHY IT WILL BE PRESSED ANYWAY =========
#   A2 at spawn: it will score the guaranteed constant and buy NOTHING. The 48
#   body pixels are drawn correctly nine times over; the only divergent cell
#   is (63,53), which no manual in this language can draw. Guaranteed
#   refutation, guaranteed wasted round, one more burned meter cell.
#   I PREDICT IT WILL BE THE NEXT COMMAND ANYWAY, and I have written that
#   prediction into the manual so it can cost me.
#   A5 from one cell south is pure loop; A5 from spawn is item 2 above.
#   A1 at spawn: witnessed inert at t1.
#   A4 at spawn: the same experiment as A3 with the labels swapped, but it
#   spends a meter cell under BOTH readings -- press it only if A3 is inert.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The next burn cell (63,53) is undrawable: one pixel per press of key 2
#     or 4, forever. A refutation whose divergence set is exactly that cell
#     implicates nothing.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on cells that have never changed, and 24 departure pixels for
#     which no rule in that direction is witnessed. 24 for the second step in
#     the same direction, 0 after that.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.
#
# ========= A NOTE ON THIS DESK =========
#   The emit-all-three-blocks discipline held and certify came back clean on
#   every check. The remaining loss is no longer at my desk, and I have
#   stopped writing prunes as though they were filters. This book is now
#   addressed to whoever holds the ranker.

order     score_an_unwitnessed_silence_above_a_witnessed_repetition        [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     buy_a_third_lattice_cell_before_attempting_to_write_a_goal       [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language   [proof: lean]
order     treat_a_repeated_identical_information_gain_as_zero_gain         [proof: lean]
order     trust_a_realised_gain_less_when_the_expected_gain_moved_and_it_did_not [proof: lean]
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
order     prefer_a_key_that_adds_no_new_prediction_debt                    [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal     [proof: lean]
order     spend_a_meter_cell_only_on_a_question_it_actually_closes         [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it   [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them           [proof: lean]

prune     action_whose_expected_bits_are_zero_only_because_the_manual_is_silent => keep [proof: lean]
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

heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic actions_priced_at_zero_expected_bits_by_the_manuals_own_silence   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic rules_sharing_a_guard_that_one_command_could_refute_together      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic prediction_debt_a_command_would_add_to_the_rolled_forward_state   [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                   [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]

prefer    a_state_where_more_than_one_key_has_a_rule_that_can_fire           [ev: 0/22 states]
prefer    a_command_that_would_put_the_body_in_a_lattice_cell_never_occupied [ev: 2/11 reachable cells seen]
prefer    a_command_that_would_turn_a_machinery_pixel_dynamic                [ev: 0/22 states]
prefer    a_key_that_names_a_direction_whichever_way_it_answers              [ev: 2/2 candidates]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index          [ev: 21/21 transitions tie]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed      [ev: 3/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on               [ev: 3/5 keys at spawn]
prefer    a_command_that_leaves_the_cycle_the_last_seventeen_commands_formed [ev: 17/20 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 21/21 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    a_free_probe_over_one_that_costs_a_meter_cell                      [ev: 10/21 commands burned]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl obj0 (colour 9, 8 cells, 3x3, present 22/22)", "verdict": "entailed",
   "as": "the 8 ring pixels of panel slot 1, already owned by Glyph9",
   "why": "an 8-cell 3x3 present in every frame is a hollow token; my census already assigns rows 1-3 cols 1-3 minus centre (2,2) to Glyph9, and (2,2) renders 0 in both configurations so it is board -- which is exactly why the engine counts 8 and not 9."},

  {"id": "O-02", "subject": "mdl obj1 (colour 1, 9 cells, 3x3, present 5/22)", "verdict": "entailed",
   "as": "panel slot 2 solid, already owned by Spent",
   "why": "9 cells not 8 means the centre is included, which is the census claim that (2,6) renders 1 in configuration A and 0 in B; present in 5 of 22 frames matches configuration A holding at frames 0-4 and after each odd-index A5 flip back."},

  {"id": "O-03", "subject": "mdl obj2 (colour 9, 3 cells, 1x3, present 22/22)", "verdict": "entailed",
   "as": "a panel underline, already owned by Glyph9 or Dark",
   "why": "exactly one underline is lit at any time and the engine tracks the lit one continuously; 3 cells 1x3 is row 5 columns 1-3 or 5-7, both already in the census."},

  {"id": "O-04", "subject": "mdl obj3 (colour null, 1006 cells, 50x38, present 22/22)", "verdict": "reject",
   "why": "connected_components(4) merged the maze floor with the body ring, because the body is floor-adjacent on every side; a 1006-cell blob that contains both the mover and the terrain explains nothing and its absence of a mover is the finding, not the track."},

  {"id": "O-05", "subject": "mdl obj4 (colour 9, 64 cells, 1x64, present 22/22)", "verdict": "accept",
   "as": "row 63 in full, of which only the 10 burned cells (cols 54-63) are seated as Glyph9 instances",
   "why": "the engine sees the whole bar because it segments frame 0; the arm can only instance the 10 cells that have varied, and that gap is the permanent one-pixel blind spot recorded in the_burn_frontier_is_a_permanent_one_pixel_blind_spot."},

  {"id": "O-06", "subject": "mdl obj12 (colour 1, first frame 19) and obj13 (colour 2, first frame 21)", "verdict": "entailed",
   "as": "two further panel flips, no new object",
   "why": "the first-frame indices of obj5,6,7,8,9,10,11,12,13 are 5,7,9,11,13,15,17,19,21 -- exactly the odd indices where ACTION5 was pressed, an independent frame-index witness for nine toggles and for zero new mechanism."},

  {"id": "O-07", "subject": "any object on colour 8 (comb, wire, knob)", "verdict": "reject",
   "why": "no colour-8 pixel has changed in 22 frames, so the arm would seat zero instances and a count over the type would be refused outright -- the failure that cost a whole round already; declared only in prose, in the_socket_is_unreachable_until_the_comb_opens."},

  {"id": "R-01", "subject": "cegis_miner tracks obj0..obj13", "verdict": "reject",
   "why": "every track was refused or hit NoSeparatingGuard; the engine's own verdict is that the world does not narrate as one mover, which is true of the segmenter and false of the world -- there is one mover and the arm can only see 24 simultaneous recolours."},

  {"id": "R-02", "subject": "key2_body_leaves_south -- a rule over Vacated at colour 9 with floor six rows below, which would make ACTION2 non-silent at lattice (2,2)", "verdict": "reject",
   "why": "ZERO witnesses: all nine key-2 presses were made from spawn, where Vacated renders 5, so cov would be 0/0 and constraint 2 forbids it; half its divergence would also land on rows 20-24 cols 14-18, which hold no instance. It would break the ranker's fixed point, and that is precisely why writing it would be gaming my own scorer."},

  {"id": "R-03", "subject": "all 22 installed rules", "verdict": "accept",
   "why": "no new mechanism arrived; ev lists extended by t18,t20 (key 2) and t19,t21 (key 5), coverages recomputed to 216/216 on the four body rules, 40/15/15/15/5/5/5/15 forward panel and 32/12/32/4/12 reverse panel, 8/8 on meter_burn_key2_next. certify replayed the previous edition 17/17 with 0 unexplained and 0 clashes."},

  {"id": "L-01", "subject": "the_ranker_can_only_buy_what_my_rules_already_fire_on", "verdict": "accept",
   "why": "derived, not observed: the probe report names its own hypothesis space as {manual, ablations, inert}; an ablation deletes rules so it predicts a subset of changes; therefore on any identity-predicting pair all 34 hypotheses agree and expected bits are zero. At spawn only key 2 fires, at lattice (2,2) only key 5 fires -- which reproduces the exact 17-command cycle t5-t21."},

  {"id": "L-02", "subject": "the_playbook_and_the_ranker_are_exactly_anti_aligned", "verdict": "accept",
   "why": "corollary of L-01 checked against my own top four recommendations: A3 at spawn, A5 at spawn, A2 at lattice (2,2), and A6/A7 all predict identity under this manual and are therefore priced at zero, while the one command the playbook forbids is the unique live action at the current state."},

  {"id": "L-03", "subject": "the_loop_pins_key_to_parity_and_therefore_seals_the_meter", "verdict": "accept",
   "why": "the loop puts the body at spawn on even indices and at (2,2) on odd ones, so the ranker presses key 2 at every even index and key 5 at every odd one; reading A (key-based) and reading B (parity-based) are the same predicate on that trajectory, which is why 10 burns and 11 non-burns have produced zero divergence."},

  {"id": "L-04", "subject": "the_realised_gain_is_pinned_while_the_expected_gain_moves", "verdict": "accept",
   "why": "expected_bits this round were 1.394849, 2.219528, 1.955012, 2.273662 -- all four different, including the two action-2 probes -- while realised gain was 5.087463, 3.5025, 5.087463, 3.5025 to six decimals, and n_survivors was 1 for every action 2 and 3 for every action 5."},

  {"id": "L-05", "subject": "the_meter_is_the_only_monotone_quantity_in_this_world", "verdict": "accept",
   "why": "22 states but only 20 distinct, and the two collisions are t0/t1 and t2/t3; every later state is nominally new only because one more cell of row 63 burned. 10 burned, 54 remain, one per lap, two commands per lap."},

  {"id": "L-06", "subject": "dynamic_census updated to 81 cells", "verdict": "accept",
   "why": "23 panel + 24 spawn ring + 24 lower ring + 10 meter = 81 = dynamic_cells; 4096 - 81 = 4015 = constant_cells; 45 Glyph9 + 24 Vacated + 9 Spent = 78 = cells_needing_an_owner. All four sums moved by exactly the two cells burned this round."},

  {"id": "L-07", "subject": "zero_space global law and its own THIN verdict", "verdict": "reject",
   "why": "the engine reports 21 transitions constraining rank 11 of 405 features, null space dimension 394, and says in its own words that nearly every vector in it is unfalsified rather than confirmed; its single global law enumerates my census cells and adds nothing to it."},

  {"id": "L-08", "subject": "a goal section", "verdict": "reject",
   "why": "declined for the fourth time. The plan tier searches my compiled rules, whose reachable set is two lattice cells and two panel configurations, so any satisfiable goal is satisfied inside the loop and sat-inside-the-loop is worse than unsat. All four grammar-admissible candidates were enumerated and each is either not-a-win, impossible, or constant-false. The winning condition is carried in prose in the_goal_i_still_cannot_write_is_the_real_one."},

  {"id": "P-01", "subject": "ACTION3 at spawn", "verdict": "probe-pending",
   "why": "names east or eliminates it, kills a forged silence with no witness, and splits the meter readings at an even index. Manual predicts zero cells changed. Priced at zero expected bits by the current ranker, which is the whole of L-02."},

  {"id": "P-02", "subject": "ACTION5 at spawn", "verdict": "probe-pending",
   "why": "thirteen rules share colored(spawn_probe, 5) with nine positive witnesses and zero negative; the body is at home now and the panel is in configuration B, the exact configuration where the five reverse rules would fire if the guard were not blocking. If the panel toggles, thirteen rules fail at once, at no meter cost."},

  {"id": "P-03", "subject": "ACTION2 pressed one cell south of spawn", "verdict": "probe-pending",
   "why": "manual asserts identity with no witness; nine consecutive presses have moved the body one lattice cell south over open floor and rows 20-24 are floor from column 13 to 31. It is the likeliest source of a third lattice cell, and its own asserted silence is what forces key 5 at every odd index."},

  {"id": "P-04", "subject": "the next command will be ACTION2", "verdict": "probe-pending",
   "why": "written in advance so it can cost me: L-01 predicts the ranker has no alternative at spawn. If the next command is anything else, L-01 is refuted and I want that more than any pixel."},

  {"id": "P-05", "subject": "ACTION6 or ACTION7", "verdict": "probe-pending",
   "why": "never pressed and entirely unconstrained; one may be the click that presses the knob and thereby makes comb cells dynamic and a goal writable. Honest counter: actions_used is evidence of what was tried, not of what exists, and no rule of mine mentions them, so the ranker prices them at zero too."},

  {"id": "E-01", "subject": "an UNKNOWN outcome for a state-action pair", "verdict": "probe-pending",
   "why": "wanted: a way to say the manual declines to predict key 3 here. The compiled step is total, so absence of a rule renders as 'nothing happens' in the same voice as a witnessed no-op -- and every ablation agrees, so the ranker prices the experiment at zero. Wrote instead: silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged plus the_ranker_can_only_buy_what_my_rules_already_fire_on. This is now the single most valuable extension the language could receive."},

  {"id": "E-02", "subject": "a goal or a rule naming a cell that has never changed", "verdict": "probe-pending",
   "why": "wanted: predict the burn at (63,53), or name the socket's 24 ring pixels at rows 50-54 cols 44-48. arc-instances all seats nothing on cells the board explains, and a count over a zero-instance type is a refused clause, not a false one. Wrote instead: i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed, and I costed and rejected dropping the board declaration (roughly 3000 instances, 22 rules needing a fresh pairwise constraint-5 audit in one round)."},

  {"id": "E-03", "subject": "a burn law conditioned on command parity", "verdict": "probe-pending",
   "why": "wanted: 'burn iff the command index is even'. The guard language reads pixels and the action name; there is no command counter and no phase pixel. Wrote instead reading A as three rules and carried reading B in the_loop_pins_key_to_parity_and_therefore_seals_the_meter, which now argues the two can never be separated from inside the loop."},

  {"id": "E-04", "subject": "a click action carrying coordinates", "verdict": "probe-pending",
   "why": "wanted: a rule for pressing the 3x3 knob at rows 9-11 cols 39-41. act=key(6) compiles but there is nowhere to put two coordinates, so such a rule would fire on every click anywhere. Wrote instead: two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click."},

  {"id": "E-05", "subject": "one burn law instead of two rules", "verdict": "entailed",
   "why": "wanted: 'burn the leftmost burned-adjacent colour-9 cell, where the right board edge counts as burned'. The guard language has no or, so rightof(?p) = wall and colored(rightof(?p), 1) cannot be joined. Wrote two exclusive rules; the exclusivity is proven in off_board_cell_terms_evaluate_false_and_that_is_load_bearing and certify reports 0 clashes."}
]
```
```
