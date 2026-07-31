# call-009-theorize-round1

model: `claude-opus-5` · 469279 ms · $1.439363 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 41321, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 41321, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 41321, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 41321, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 39779, "type": "message"}], "output_tokens": 39779, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
  "ACTION7",
  "RESET"
 ],
 "background": 5,
 "cascade_lengths": [
  1,
  2
 ],
 "cells_needing_an_owner": 77,
 "colours_seen": [
  0,
  1,
  2,
  3,
  4,
  5,
  6,
  8,
  9,
  14
 ],
 "constant_cells": 3995,
 "distinct_states": 12,
 "dynamic_box": [
  29,
  10,
  54,
  63
 ],
 "dynamic_cells": 101,
 "max_frames_in_one_command": 2,
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

Only the cells that have EVER changed are shown (rows 29-10, cols 54-63); everything outside this box has held one colour for the whole history and is board by definition.

```
    111111111122222222223333333333444444444455555555556666
    012345678901234567890123456789012345678901234567890123
 29 555335544444444444444444444444444444455555555555555555
 30 555335544444444444444444444444444444455555555555555555
 31 55533554444444444444444444444444eeee455555555555555555
 32 55522554444444444444444444444444eeee455555555555555555
 33 55522554444444444444444444444444eeee455555555555555555
 34 55533554444444444444444444444444eeee455555555555555555
 35 555335544444444444444444444444444444455555555555555555
 36 566666644444444444444444444444444444455555555555555555
 37 560000644444444444444444444444444444455555555555555555
 38 560660144444444444444444444444444444455555555555555555
 39 560660244444444444444444444444444444455555555555555555
 40 560000644444444444444444444444444444455555555555555555
 41 566666644444444444444444444444444444455555555555555555
 42 555555555555555555555555555555555555555555555555555555
 43 555555555555555555555555555555555555555555555555555555
 44 555555555555555555555555555555555555555555555555555555
 45 555555555555555555555555555555555555555555555555555555
 46 555555555555555555555555555555555555555555555555555555
 47 555555555555555555555555555555555555555555555555555555
 48 555555555555555555555555555555555555555555555555555555
 49 555555555555555555555555555555555555555555555555555555
 50 555555555555555555555555555555555555555555555555555555
 51 555555555555555555555555555555555555555555555555555555
 52 555555555555555555555555555555555555555555555555555555
 53 222222222222222222222222222222222222222222222222233333
 54 444444444444444444444444444444444444444444444444444444
```

## Every command, and what changed

`t` indexes the state sequence. `frames` is how many grids one command returned -- more than one means the world took several internal steps for a single action.

- t0   RESET     frames=1   state=NOT_FINISHED (first frame)
- t1   ACTION1   frames=2   state=NOT_FINISHED 96 cells changed, rows 30-41, cols 11-22, [0, 1, 2, 3, 4, 5, 6] -> [0, 1, 2, 3, 4, 5, 6]
- t2   ACTION2   frames=2   state=NOT_FINISHED 96 cells changed, rows 30-41, cols 11-22, [0, 1, 2, 3, 4, 5, 6] -> [0, 1, 2, 3, 4, 5, 6]
- t3   ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t4   ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2; (53,63) 2->3
- t5   ACTION7   frames=1   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t6   ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2
- t7   ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t8   ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2; (53,62) 2->3
- t9   ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t10  ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2
- t11  ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4; (53,61) 2->3
- t12  ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2
- t13  ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t14  ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2; (53,60) 2->3
- t15  ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t16  ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2
- t17  ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4; (53,59) 2->3

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 17,
  "n_states": 18,
  "refusals": [
   "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 3 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture"
  ],
  "tracks": [
   {
    "ms": 0,
    "refused": "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj0"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 3 narrates ['recolor']; only move/none are mined on this fixture",
    "track_id": "obj1"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj2"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj3"
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
  "background": 5,
  "candidates": 4,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 2,
   "recolor": 20,
   "vanish": 2
  },
  "n_frames": 18,
  "tracks": [
   {
    "color": null,
    "first_frame": 0,
    "frames_present": 1,
    "n_cells": 440,
    "shape": [
     13,
     36
    ],
    "track_id": "obj0"
   },
   {
    "color": null,
    "first_frame": 0,
    "frames_present": 18,
    "n_cells": 108,
    "shape": [
     2,
     54
    ],
    "track_id": "obj1"
   },
   {
    "color": null,
    "first_frame": 1,
    "frames_present": 1,
    "n_cells": 436,
    "shape": [
     13,
     36
    ],
    "track_id": "obj2"
   },
   {
    "color": null,
    "first_frame": 2,
    "frames_present": 16,
    "n_cells": 440,
    "shape": [
     13,
     36
    ],
    "track_id": "obj3"
   }
  ],
  "variants": [
   {
    "baseline_bits": 5791,
    "compression_ratio": 1.424279,
    "events": 24,
    "gain_bits": -2457,
    "ms": 14,
    "script_bits": 8248,
    "split_by_color": false,
    "tracks": 4
   },
   {
    "baseline_bits": 5791,
    "compression_ratio": 6.883094,
    "events": 173,
    "gain_bits": -34069,
    "ms": 50,
    "script_bits": 39860,
    "split_by_color": true,
    "tracks": 89
   }
  ],
  "window": {
   "box": [
    29,
    10,
    54,
    63
   ],
   "covered": 1.0,
   "dynamic_cells": 101,
   "frame_cells": 4096,
   "full_frame": false,
   "reason": "frame is 4096 cells (> 1200), arena is 1404",
   "window_cells": 1404
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
   "ACTION7",
   "RESET"
  ],
  "background": 5,
  "cascade_lengths": [
   1,
   2
  ],
  "cells_needing_an_owner": 77,
  "colours_seen": [
   0,
   1,
   2,
   3,
   4,
   5,
   6,
   8,
   9,
   14
  ],
  "constant_cells": 3995,
  "distinct_states": 12,
  "dynamic_box": [
   29,
   10,
   54,
   63
  ],
  "dynamic_cells": 101,
  "max_frames_in_one_command": 2,
  "shape": [
   64,
   64
  ],
  "states": 18,
  "steps": 18
 },
 "window": {
  "box": [
   29,
   10,
   54,
   63
  ],
  "covered": 1.0,
  "dynamic_cells": 101,
  "frame_cells": 4096,
  "full_frame": false,
  "reason": "frame is 4096 cells (> 1200), arena is 1404",
  "window_cells": 1404
 },
 "zero_space": {
  "cap": 240,
  "cells": [
   [
    30,
    11
   ],
   [
    30,
    12
   ],
   [
    30,
    13
   ],
   [
    30,
    14
   ],
   [
    30,
    15
   ],
   [
    30,
    16
   ],
   [
    31,
    11
   ],
   [
    31,
    12
   ],
   [
    31,
    13
   ],
   [
    31,
    14
   ],
   [
    31,
    15
   ],
   [
    31,
    16
   ],
   [
    32,
    11
   ],
   [
    32,
    12
   ],
   [
    32,
    13
   ],
   [
    32,
    14
   ],
   [
    32,
    15
   ],
   [
    32,
    16
   ],
   [
    32,
    17
   ],
   [
    32,
    18
   ],
   [
    32,
    19
   ],
   [
    32,
    20
   ],
   [
    32,
    21
   ],
   [
    32,
    22
   ],
   [
    33,
    11
   ],
   [
    33,
    12
   ],
   [
    33,
    13
   ],
   [
    33,
    14
   ],
   [
    33,
    15
   ],
   [
    33,
    16
   ],
   [
    33,
    17
   ],
   [
    33,
    18
   ],
   [
    33,
    19
   ],
   [
    33,
    20
   ],
   [
    33,
    21
   ],
   [
    33,
    22
   ],
   [
    34,
    11
   ],
   [
    34,
    12
   ],
   [
    34,
    13
   ],
   [
    34,
    14
   ],
   [
    34,
    15
   ],
   [
    34,
    16
   ],
   [
    35,
    11
   ],
   [
    35,
    12
   ],
   [
    35,
    13
   ],
   [
    35,
    14
   ],
   [
    35,
    15
   ],
   [
    35,
    16
   ],
   [
    36,
    11
   ],
   [
    36,
    12
   ],
   [
    36,
    13
   ],
   [
    36,
    14
   ],
   [
    36,
    15
   ],
   [
    36,
    16
   ],
   [
    37,
    11
   ],
   [
    37,
    12
   ],
   [
    37,
    13
   ],
   [
    37,
    14
   ],
   [
    37,
    15
   ],
   [
    37,
    16
   ],
   [
    38,
    11
   ],
   [
    38,
    12
   ],
   [
    38,
    13
   ],
   [
    38,
    14
   ]
  ],
  "cells_dynamic": 101,
  "cells_used": 101,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c3",
   "c4",
   "c5",
   "c6"
  ],
  "difference_rank": 7,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.009901,
   "difference_rank": 7,
   "features": 707,
   "space_dimension": 700,
   "transitions": 17,
   "verdict": "THIN: 17 transitions constrain rank 7 of 707 features, so the null space has dimension 700 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 707,
  "global_laws": [
   {
    "cells": [
     [
      30,
      11
     ],
     [
      30,
      12
     ],
     [
      30,
      13
     ],
     [
      30,
      14
     ],
     [
      30,
      15
     ],
     [
      30,
      16
     ],
     [
      31,
      11
     ],
     [
      31,
      12
     ],
     [
      31,
      13
     ],
     [
      31,
      14
     ],
     [
      31,
      15
     ],
     [
      31,
      16
     ],
     [
      32,
      11
     ],
     [
      32,
      12
     ],
     [
      32,
      13
     ],
     [
      32,
      14
     ],
     [
      32,
      15
     ],
     [
      32,
      16
     ],
     [
      32,
      17
     ],
     [
      32,
      18
     ],
     [
      32,
      19
     ],
     [
      32,
      20
     ],
     [
      32,
      21
     ],
     [
      32,
      22
     ],
     [
      33,
      11
     ],
     [
      33,
      12
     ],
     [
      33,
      13
     ],
     [
      33,
      14
     ],
     [
      33,
      15
     ],
     [
      33,
      16
     ],
     [
      33,
      17
     ],
     [
      33,
      18
     ],
     [
      33,
      19
     ],
     [
      33,
      20
     ],
     [
      33,
      21
     ],
     [
      33,
      22
     ],
     [
      34,
      11
     ],
     [
      34,
      12
     ],
     [
      34,
      13
     ],
     [
      34,
      14
     ],
     [
      34,
      15
     ],
     [
      34,
      16
     ],
     [
      35,
      11
     ],
     [
      35,
      12
     ],
     [
      35,
      13
     ],
     [
      35,
      14
     ],
     [
      35,
      15
     ],
     [
      35,
      16
     ],
     [
      36,
      11
     ],
     [
      36,
      12
     ],
     [
      36,
      13
     ],
     [
      36,
      14
     ],
     [
      36,
      15
     ],
     [
      36,
      16
     ],
     [
      37,
      11
     ],
     [
      37,
      12
     ],
     [
      37,
      13
     ],
     [
      37,
      14
     ],
     [
      37,
      15
     ],
     [
      37,
      16
     ],
     [
      38,
      11
     ],
     [
      38,
      12
     ],
     [
      38,
      13
     ],
     [
      38,
      14
     ],
     [
      38,
      15
     ],
     [
      38,
      16
     ],
     [
      38,
      17
     ],
     [
      38,
      18
     ],
     [
      38,
      19
     ],
     [
      38,
      20
     ],
     [
      38,
      21
     ],
     [
      38,
      22
     ],
     [
      39,
      11
     ],
     [
      39,
      12
     ],
     [
      39,
      13
     ],
     [
      39,
      14
     ],
     [
      39,
      15
     ],
     [
      39,
      16
     ],
     [
      39,
      17
     ],
     [
      39,
      18
     ],
     [
      39,
      19
     ],
     [
      39,
      20
     ],
     [
      39,
      21
     ],
     [
      39,
      22
     ],
     [
      40,
      11
     ],
     [
      40,
      12
     ],
     [
      40,
      13
     ],
     [
      40,
      14
     ],
     [
      40,
      15
     ],
     [
      40,
      16
     ],
     [
      41,
      11
     ],
     [
      41,
      12
     ],
     [
      41,
      13
     ],
     [
      41,
      14
     ],
     [
      41,
      15
     ],
     [
      41,
      16
     ],
     [
      53,
      59
     ],
     [
      53,
      60
     ],
     [
      53,
      61
     ],
     [
      53,
      62
     ],
     [
      53,
      63
     ]
    ],
    "support": [
     "c0@0",
     "c1@0",
     "c2@0",
     "c3@0",
     "c4@0",
     "c5@0",
     "c6@0",
     "c0@1",
     "c1@1",
     "c2@1",
     "c3@1",
     "c4@1",
     "c5@1",
     "c6@1",
     "c0@2",
     "c1@2",
     "c2@2",
     "c3@2",
     "c4@2",
     "c5@2",
     "c6@2",
     "c0@3",
     "c1@3",
     "c2@3",
     "c3@3",
     "c4@3",
     "c5@3",
     "c6@3",
     "c0@4",
     "c1@4",
     "c2@4",
     "c3@4",
     "c4@4",
     "c5@4",
     "c6@4",
     "c0@5",
     "c1@5",
     "c2@5",
     "c3@5",
     "c4@5",
     "c5@5",
     "c6@5",
     "c0@6",
     "c1@6",
     "c2@6",
     "c3@6",
     "c4@6",
     "c5@6",
     "c6@6",
     "c0@7",
     "c1@7",
     "c2@7",
     "c3@7",
     "c4@7",
     "c5@7",
     "c6@7",
     "c0@8",
     "c1@8",
     "c2@8",
     "c3@8",
     "c4@8",
     "c5@8",
     "c6@8",
     "c0@9",
     "c1@9",
     "c2@9",
     "c3@9",
     "c4@9",
     "c5@9",
     "c6@9",
     "c0@10",
     "c1@10",
     "c2@10",
     "c3@10",
     "c4@10",
     "c5@10",
     "c6@10",
     "c0@11",
     "c1@11",
     "c2@11",
     "c3@11",
     "c4@11",
     "c5@11",
     "c6@11",
     "c0@12",
     "c1@12",
     "c2@12",
     "c3@12",
     "c4@12",
     "c5@12",
     "c6@12",
     "c0@13",
     "c1@13",
     "c2@13",
     "c3@13",
     "c4@13",
     "c5@13",
     "c6@13",
     "c0@14",
     "c1@14",
     "c2@14",
     "c3@14",
     "c4@14",
     "c5@14",
     "c6@14",
     "c0@15",
     "c1@15",
     "c2@15",
     "c3@15",
     "c4@15",
     "c5@15",
     "c6@15",
     "c0@16",
     "c1@16",
     "c2@16",
     "c3@16",
     "c4@16",
     "c5@16",
     "c6@16",
     "c0@17",
     "c1@17",
     "c2@17",
     "c3@17",
     "c4@17",
     "c5@17",
     "c6@17",
     "c0@18",
     "c1@18",
     "c2@18",
     "c3@18",
     "c4@18",
     "c5@18",
     "c6@18",
     "c0@19",
     "c1@19",
     "c2@19",
     "c3@19",
     "c4@19",
     "c5@19",
     "c6@19",
     "c0@20",
     "c1@20",
     "c2@20",
     "c3@20",
     "c4@20",
     "c5@20",
     "c6@20",
     "c0@21",
     "c1@21",
     "c2@21",
     "c3@21",
     "c4@21",
     "c5@21",
     "c6@21",
     "c0@22",
     "c1@22",
     "c2@22",
     "c3@22",
     "c4@22",
     "c5@22",
     "c6@22",
     "c0@23",
     "c1@23",
     "c2@23",
     "c3@23",
     "c4@23",
     "c5@23",
     "c6@23",
     "c0@24",
     "c1@24",
     "c2@24",
     "c3@24",
     "c4@24",
     "c5@24",
     "c6@24",
     "c0@25",
     "c1@25",
     "c2@25",
     "c3@25",
     "c4@25",
     "c5@25",
     "c6@25",
     "c0@26",
     "c1@26",
     "c2@26",
     "c3@26",
     "c4@26",
     "c5@26",
     "c6@26",
     "c0@27",
     "c1@27",
     "c2@27",
     "c3@27",
     "c4@27",
     "c5@27",
     "c6@27",
     "c0@28",
     "c1@28",
     "c2@28",
     "c3@28",
     "c4@28",
     "c5@28",
     "c6@28",
     "c0@29",
     "c1@29",
     "c2@29",
     "c3@29",
     "c4@29",
     "c5@29",
     "c6@29",
     "c0@30",
     "c1@30",
     "c2@30",
     "c3@30",
     "c4@30",
     "c5@30",
     "c6@30",
     "c0@31",
     "c1@31",
     "c2@31",
     "c3@31",
     "c4@31",
     "c5@31",
     "c6@31",
     "c0@32",
     "c1@32",
     "c2@32",
     "c3@32",
     "c4@32",
     "c5@32",
     "c6@32",
     "c0@33",
     "c1@33",
     "c2@33",
     "c3@33",
     "c4@33",
     "c5@33",
     "c6@33",
     "c0@34",
     "c1@34",
     "c2@34",
     "c3@34",
     "c4@34",
     "c5@34",
     "c6@34",
     "c0@35",
     "c1@35",
     "c2@35",
     "c3@35",
     "c4@35",
     "c5@35",
     "c6@35",
     "c0@36",
     "c1@36",
     "c2@36",
     "c3@36",
     "c4@36",
     "c5@36",
     "c6@36",
     "c0@37",
     "c1@37",
     "c2@37",
     "c3@37",
     "c4@37",
     "c5@37",
     "c6@37",
     "c0@38",
     "c1@38",
     "c2@38",
     "c3@38",
     "c4@38",
     "c5@38",
     "c6@38",
     "c0@39",
     "c1@39",
     "c2@39",
     "c3@39",
     "c4@39",
     "c5@39",
     "c6@39",
     "c0@40",
     "c1@40",
     "c2@40",
     "c3@40",
     "c4@40",
     "c5@40",
     "c6@40",
     "c0@41",
     "c1@41",
     "c2@41",
     "c3@41",
     "c4@41",
     "c5@41",
     "c6@41",
  
```

The full proposal stream is 2774 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- FOURTEENTH DRAFT.
#
# 0. FOUR COMMANDS WERE FINALLY PRESSED AND THEY PAID FOR THEMSELVES.
#    The store moved for the first time in three rounds: steps 14 -> 18,
#    states 14 -> 18, distinct_states 9 -> 12, dynamic_cells 99 -> 101,
#    cells_needing_an_owner 75 -> 77, constant_cells 3997 -> 3995. The new
#    commands are t14 ACTION4, t15 ACTION3, t16 ACTION4, t17 ACTION3, and the
#    meter converted twice more: (53,60) at t14 and (53,59) at t17.
#
# 1. ONE READING OF THE CADENCE DIED AND I NAME THE PRESS THAT KILLED IT.
#    Reading F -- internal-frame totals crossing a multiple of seven --
#    required the fourth tick at t15, because the running total goes 25 to 27
#    at t14 and only crosses 28 at t15. The world ticked at t14. F is dead.
#    Readings D and E both went 5 for 5. A fourth reading I had never written
#    down, E'' (count EVERY strip-affecting press including the ACTION7), is
#    also dead: its tick ordinals are 2, 6, 9, 12, 15 and 2 is not congruent
#    to 6 modulo three. So both survivors agree that the ACTION7 at t5 does
#    not count, and they disagree only about WHY.
#
# 2. THE FOUR PROBE REFUTATIONS ARE ONE DEFECT AND THE HASHES DECODE THE
#    WORLD. P-09 to P-12 are all the frontier blindness, and the four distinct
#    hashes they name let me read the world's state space off the record; that
#    decoding is the round's real gain and it is written out in full below.
#
# 3. WHAT I EXPECT TO LOSE. The march now has instances at (53,59) and
#    (53,60) that it did not have last round, so on replay it runs FOUR
#    commands ahead of the world instead of one, and I pre-register replay
#    falling from 9/13 to 7/17. I keep it anyway and I say exactly what for.
#
# 4. THE BAR LOOKS MORE LIKE A CLOCK THAN A SCORE NOW, AND THAT IS AN UPDATE
#    ABOUT THE PLAYBOOK RATHER THAN A GOAL. Fourteen work presses accomplished
#    nothing whatever -- the strip was toggled back to where it started every
#    time -- and the meter advanced five times regardless. Meters that advance
#    for no achievement are clocks. Still not enough to sign a goal.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Casing { pos: Coord, color: Int }  # arc-colour: 6  arc-instances: all
  object Cavity { pos: Coord, color: Int }  # arc-colour: 0  arc-instances: all
  object Rail { pos: Coord, color: Int }  # arc-colour: 3  arc-instances: all
  object Pip { pos: Coord, color: Int }  # arc-colour: 1  arc-instances: all
  object Stud { pos: Coord, color: Int }  # arc-colour: 2  arc-instances: all
  object Erased { pos: Coord, color: Int }  # arc-colour: 4  arc-instances: all
  Casing [segment: colour_class_6 ev: t0-t17 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t17 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t17 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t17 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t17 compress: 14]
  Erased [segment: colour_class_4 ev: t0-t17 compress: 12]

events:
  event recolored(o, c)

# Eight rules. Six are the strip toggle: seven ACTION3 blanks, one ACTION7
# blank, seven ACTION4 restores, 12 cells every time, 192 cell-recolourings,
# every one correct. One is the seed. One is the march.
#
# The Stud type now has FOURTEEN instances, two more than last round, because
# (53,59) and (53,60) varied for the first time this round and the arm gives
# an instance to every cell of a declared colour that the board cannot
# explain. They are: (32,13) (32,14) (33,13) (33,14) in the unselected slot
# bar, (38,17) (38,20) (39,19) (39,22) in the strip, (39,16) in the lower
# port, and (53,59) (53,60) (53,61) (53,62) (53,63) in the meter.
#
# THE MARCH'S ev TAG STILL CITES THE WORLD'S CONVERSIONS, NOT ITS OWN
# FIRINGS. The world converted (53,62) at t8, (53,61) at t11, (53,60) at t14
# and (53,59) at t17: four conversions, and the march is the only rule that
# accounts for any of them. It FIRES at t7, t9, t11 and t13. Citing the
# firings would hide a four-command phase error inside a tag; the error is
# written out at full length in the_march_now_leads_by_four_commands theorem.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3,t7,t9,t11,t13,t15,t17 cov: 56/56]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3,t7,t9,t11,t13,t15,t17 cov: 28/28]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4,t6,t8,t10,t12,t14,t16 cov: 56/56]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4,t6,t8,t10,t12,t14,t16 cov: 28/28]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_seeds_the_meter_at_the_right_edge forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

  rule key3_marches_the_meter_leftward forall ?p in Stud [ev: t8,t11,t14,t17 cov: 4/4]
    when act=key(3) and colored(?p, 2) and colored(rightof(?p), 3) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 14 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 77 [status: proven]

  theorem the_four_probe_hashes_decode_the_entire_state_space_and_that_is_this_rounds_real_gain "P-09 through P-12 are four refutations of the same defect, and taken together they hand me something no single frame does: the world's state lattice, read off four sixteen-hex-digit strings. Assign them by which press they follow. 1317da5b367d300a is the manual's answer to ACTION4 and the manual's starting point before ACTION3, so it is a strip-SHOWN state; b278887e087d3593 is the mirror, a strip-BLANKED state; and both of them carry the manual's bar, converted through (53,61) only. The world's answers are 3281b51b4c1aa929 after ACTION4 at BOTH t14 and t16 -- the same hash twice, which is the world telling me s14 and s16 are the identical frame -- and d2c8aa05e38a2da7 after ACTION3 at t15 against febfe034e90989ad after ACTION3 at t17, two different hashes because the world converted (53,59) in between. So a state of this world is a PRODUCT: strip in shown-or-blanked, times bar length, times which slot the selector holds. I can now check that against the store without a single new press. Enumerate: s0, s1 the swapped slot, s3 blanked with no bar, s4 shown with one, s5 blanked with one, s8 shown with two, s9 blanked with two, s11 blanked with three, s12 shown with three, s14 shown with four, s15 blanked with four, s17 blanked with five. Twelve, and distinct_states is 12. The collapses are s2=s0, s6=s4, s7=s5, s10=s8, s13=s11, s16=s14 -- six of them, and 18 minus 6 is 12. The lattice closes exactly. The consequence I care about most is in the next theorem: this product has no room in it for winning."
    [depends: the_world_is_not_a_function_of_the_visible_frame_and_it_is_now_witnessed_under_both_keys  probe: passed]

  theorem the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending "eighteen states, every one NOT_FINISHED, and the previous theorem shows why that is not bad luck. Keys 1, 2, 3, 4 and 7 move the world only within a product of three coordinates: the strip is shown or blanked, the selector is in one of two slots, and the meter has converted k cells. The first two are involutions -- I have toggled them eleven and two times respectively and always landed back where I started -- and the third is monotone and moves on a schedule no key controls. So the only thing eighteen commands have actually ACHIEVED is spending meter. If the ending lives anywhere it lives outside this product, which means it needs either a key I have never pressed or a state of the panel I have never built. That is an argument from the shape of the reachable set rather than from any single frame, and it is the reason the playbook now ranks the two unpressed keys ahead of everything else, including the cadence question I have been chasing for five drafts. I state the weakness plainly: the argument assumes the product is complete, and it is complete only over the eighteen states I have, which is exactly the kind of assumption a new key exists to break."
    [depends: the_four_probe_hashes_decode_the_entire_state_space_and_that_is_this_rounds_real_gain  probe: pending]

  theorem reading_F_is_dead_and_the_press_that_killed_it_was_t14 "reading F said the meter ticks on the command during which the running total of internal frames crosses a multiple of seven. It was 3 of 3 when I wrote it and I gave it equal standing with D and E, deliberately, because three ticks cannot pin a counter. Four commands later it is refuted and the refutation is arithmetic I pre-registered. Totals after each command: 2, 4, 6, 8, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33. Seven is crossed during t4, fourteen during t8, twenty-one is reached at t11 -- three ticks, three crossings. Twenty-eight is crossed during t15, because t14 takes the total from 25 only to 27. The world ticked at t14 and did not tick at t15. F predicted the wrong command and dies on it. I also killed a reading I had never bothered to write down, E'' -- count every press that touches the strip, INCLUDING the ACTION7 at t5. Its tick ordinals are 2, 6, 9, 12, 15, and 2 against 6 is a gap of four where every later gap is three. So the exclusion of t5 is not optional under any surviving reading: whatever the counter counts, it did not count that command."
    [depends: a_third_cadence_reading_fits_and_my_previous_draft_was_wrong_to_say_none_did  probe: passed]

  theorem readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them "ticks fell at commands 4, 8, 11, 14 and 17 of seventeen. Reading D counts commands that returned TWO frames and ticks on every third: the two-frame ordinals of the ticking commands are 4, 7, 10, 13 and 16, an exact arithmetic progression of step three with no false positive among the eleven commands that did not tick. Reading E counts presses of ACTION3 or ACTION4 only and ticks on every third starting at the second: the work-press ordinals of the ticking commands are 2, 5, 8, 11 and 14, again exact, again no false positive. Five for five each. They cannot be separated by any run of ACTION3 and ACTION4, because over such a run every command is both a two-frame command and a work press and the two counters advance in lockstep -- which is precisely what the last fourteen commands were, and precisely why fourteen commands of evidence bought no discrimination. A command that is two-frame but NOT a strip key separates them in one press. Concretely, from the present position of 16 two-frame commands and 14 work presses: press ACTION1, then ACTION2, then any strip key. D counts all three, reaches two-frame ordinal 19, and ticks on the strip key; E counts only the strip key, reaches work ordinal 15, and does not tick. One bit, three presses, and the pair of selector presses returns the frame to where it started so the strip key is pressed at home."
    [depends: reading_F_is_dead_and_the_press_that_killed_it_was_t14  probe: pending]

  theorem the_meter_advances_for_no_achievement_and_that_tilts_it_toward_clock "for five drafts I have refused to say whether colour 3 on the bar means consumed or filled, on the ground that the two invert every ranking and I could not tell them apart. This round tilts it, and I want to record the tilt without overstating it. Fourteen work presses have now been spent, and what they accomplished is nothing: the strip was blanked and restored and blanked and restored, and it stands blanked now exactly as it stood at t3. Not one of the eighteen states does anything a designer would call progress. The meter advanced five times through all of it, on a schedule keyed to the number of presses rather than to their content, and it advanced under ACTION4 three times and under ACTION3 twice, so it is not paying out for a particular deed. A quantity that increases at a fixed rate regardless of what you do is a clock; a quantity that increases when you achieve something is a score, and I have achieved nothing. That is real evidence and it is still not proof: a designer may well have written a progress meter that also credits mere activity, and I have never seen the left end of row 53 nor any label for it. What changes is the playbook, not the goal section. If this is a clock then a press spent producing a state I have already seen is a press spent for nothing, and the toggle loop I have been running is the most expensive thing in the record."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: pending]

  theorem the_march_now_leads_by_four_commands_and_i_keep_it_for_the_present_state_alone "last round the march lagged the world and I priced it at three replay transitions. The arm has since given it instances at (53,59) and (53,60), and a rule I did not edit changed behaviour again -- the second time level data has moved a rule under me. Trace it exactly. The seed paints (53,63) at t4, correctly. The march then fires at t7, t9, t11 and t13, painting (53,62), (53,61), (53,60) and (53,59), while the world converts those same four cells at t8, t11, t14 and t17. The lead grows one command per conversion: one at t7, two at t9, three at t11, four at t13. Under open-loop replay errors compound, so transitions t7 and t9 through t16 all diverge and only t17 recovers, and I pre-register replay at 7 of 17 rather than the 9 of 13 certify last returned. What I get for it is the present state: the manual's bar stands at (53,63) through (53,59) converted and the world's bar stands at exactly the same five cells, so the manual reconstructs the CURRENT frame cell for cell and every probe I launch from here starts from truth. Dropping the march scores 6 of 17 and leaves the manual four cells wrong right now. I take the exactness. And I name the price honestly: the exactness is luck, not design -- the march ran out of instances at (53,58) at the same moment the world caught up -- and the very next conversion will restore the lead and destroy it."
    [depends: the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied  probe: passed]

  theorem the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied "this was prose last round and is now witnessed four times, by P-09 through P-12. The arm instantiates only cells the board cannot explain, and the board is the cells that never vary, so at prediction time (53,60) and (53,59) were board, no rule of mine could name them, and the manual's answer to ACTION4 at t14 and to ACTION3 at t17 was necessarily a frame with those cells unconverted. Both refutations are exactly that and nothing else: 1317da5b367d300a against 3281b51b4c1aa929 is one bar cell, b278887e087d3593 against febfe034e90989ad is one bar cell. What I got wrong last round was the SIZE of the defect, and I correct it here. I wrote that the lag was permanent but bounded at one cell. It is bounded at one cell only when the frontier converts before another conversion is due; across a stretch where the world ticks twice and the store is not refreshed in between, the manual falls two cells behind, and it will fall k behind across k ticks. The bound is on the store's staleness, not on the world. The mechanism is unchanged and is not a bug I can fix from inside the manual: each cell the world converts hands the arm one more instance and hands me one more cell of reach, always one conversion after I needed it."
    [depends: instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances  probe: passed]

  theorem replay_is_open_loop_and_the_probe_stream_re_confirmed_it_this_round "settled two drafts ago by a four-way table and re-confirmed here for free, which is the kind of corroboration I trust because I did not go looking for it. Read the probe stream in sequence. P-09's inert hash is b278887e087d3593; P-10's inert hash is 1317da5b367d300a, which is exactly the hash P-09's MANUAL prediction named, not the hash the world answered. The probe harness carried my prediction forward as its own next state and never once resynced to the world. Same again at P-11 and P-12. So the checker replays the manual against itself, a guard on an off-board cell reads false rather than matching, and my errors compound rather than being wiped -- which is the whole explanation of why a four-command lead shows up as ten consecutive wrong transitions that close in one."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_first_divergence_is_the_selector_swap_and_i_refuse_to_change_the_manual_for_it "the surprise that called me back is the replay mismatch at transition 0: ACTION1, 96 cells, first cell (30,11) manual 5 world 6. I have predicted this surprise, cell for cell, for five drafts running, and I answer it with a refusal rather than an edit for the sixth round. The refusal rests on two independent grounds already proven and re-checked against the divergence report certify returned again this round. Ground one, constraint 5: the report contains five cells, (30,16) (31,16) (32,16) (33,16) (34,16), that are colour 5 in frame 0 with above 5, below 5, left 5, right 4 -- one indistinguishable guard reading -- and the world sends them to 6, 6, 1, 2, 6. No guard in this language separates them, so any rule set producing the swap contains two rules that both fire, which is forbidden. Ground two, constraint 3: the shortest expressible form is of order one landmark and one rule per repainted cell in each direction, longer than the 96 pixels it draws. A surprise the manual predicted in advance, whose cause the manual has proven inexpressible twice over, is the price of a language rather than a defect in the theory, and the price is one transition in seventeen."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem no_goal_is_signed_and_that_is_deliberate "all eighteen states returned NOT_FINISHED and nothing in seventeen transitions indicates what finishing means. An absent goal compiles to is_goal implies False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. The bar is still the only monotone quantity in the record and still the most tempting goal, and this round moved my belief about it -- the meter advanced five times while nothing whatever was achieved, which is what a clock does -- but moved it toward BUDGET, which is the reading under which making the bar full is the opposite of winning. So the tilt is an argument against signing the tempting goal, not for it. The live candidates are unchanged: that a lane must be brought into some relation with the badge at its far end, that every slot in the column must be visited or solved, or that the objective lives in the twenty-nine rows I have never been shown. There is no goal section, and this theorem is where the silence is recorded."
    [depends: the_meter_advances_for_no_achievement_and_that_tilts_it_toward_clock  probe: pending]

  theorem the_march_and_the_blanking_rule_cannot_both_fire_and_the_argument_survives_two_new_meter_studs "both are guarded on act=key(3) and colored(?p,2), so constraint 5 needs the remaining guards disjoint on every instance in every state, and the Stud type just grew from twelve instances to fourteen. I re-ran the argument on the two new ones rather than assuming it carried. The blanking guard needs the left neighbour to be neither 0 nor 2; a meter stud's left neighbour is 2 whenever the stud itself is still 2, because the bar converts strictly right to left and no state in the record has a colour-3 cell immediately left of a colour-2 one. That covers (53,59) and (53,60) exactly as it covered (53,61). The march needs the right neighbour to be 3, which fails for every strip stud (right neighbours are only ever 1, 2 or 4), for both unselected-bar studs (2 or 5), for the port stud (1 or 4), and for (53,63) whose right neighbour is off-board and therefore reads false under every guard. Certify adjudicated 42 pairs last round with zero clashes; the same enumeration now covers 18 states by 3 actions, 54 pairs, and I pre-register zero clashes again. The latent risk is unchanged and I restate it because it is the one thing that would break this: a state with a colour-3 cell immediately left of a colour-2 bar cell admits both rules on that cell. The monotone right-to-left order forbids it, and that order is now witnessed five times rather than three -- witnessed, not proven."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: passed]

  theorem the_world_is_not_a_function_of_the_visible_frame_and_it_is_now_witnessed_under_both_keys "witnessed twice, once for each strip key, which removes the chance that it was an artefact of ACTION4. Witness one: s5 and s7 are the same 4096 cells, ACTION4 from s5 restored twelve cells, ACTION4 from s7 restored twelve cells and ticked (53,62). Witness two: s8 and s10 are the same 4096 cells and ACTION3 from s8 blanked twelve cells while ACTION3 from s10 blanked twelve and ticked (53,61). This round adds a third of the same shape: s14 and s16 are the same frame -- the world said so itself by answering the identical hash 3281b51b4c1aa929 to ACTION4 at both t14 and t16 -- and ACTION3 from s15 did not tick while ACTION3 from s17's predecessor did. So the world carries at least one bit no guard of mine can read, constraint 5 forbids me writing both successors of an identical frame, and any planner treating a frame as a state is planning in the wrong space. This holds whichever of D and E is right, which is why it survived F's death untouched."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and (53,59) through (53,63) all hold 2 rather than 3. The anatomy closes cell by cell: 22 Casing as the perimeter of rows 36-41 by cols 11-16 minus the two ports plus the 2x2 core at rows 38-39 cols 13-14; 12 Cavity as the 4x4 at rows 37-40 cols 12-15 minus that core; 8 Rail at rows 30-31 and 34-35 by cols 13-14; 4 Stud at rows 32-33 by cols 13-14; 8 Pip and 4 Stud in the lane B strip; 1 Pip at (38,16) and 1 Stud at (39,16) in the ports; 12 Erased as the lane A strip at rows 32-33 cols 17-22; 5 Stud in the meter, two more than last round. 22+12+8+9+14+12 = 77 = cells_needing_an_owner. The 24 remaining dynamic cells are the background of the unselected slot footprint, cols 11, 12, 15, 16 over rows 30-35, and 77+24 = 101 = dynamic_cells, and 4096-101 = 3995 = constant_cells. The dynamic set closes independently: the selector swap repaints 96 cells and the meter has ticked five times, and 96+5 = 101. Certify has returned 0 unexplained of 4096 on this reconstruction every round it has run and must do so again."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0; a cell constant across the whole record gets none. The arithmetic has been demonstrated five times now: 73 owners at 97 dynamic, 74 at 98, 75 at 99, and this round 77 at 101, the difference each time exactly the bar cells that converted and my Stud declaration moving by exactly the same number. Twice it has done something sharper than bookkeeping. The instance at (53,61) once changed the behaviour of a rule I did not edit; this round the instances at (53,59) and (53,60) did it again and in the same direction, turning a march that lagged into a march that leads by four. Level data is not inert with respect to the manual, and I will not again assume a rule's replay is stable across a store update -- this is the second time I have written that sentence and the first time it cost me a pre-registered number."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_bar_runs_leftward_and_the_budget_is_measurable "five cells have converted, (53,63) then (53,62) then (53,61) then (53,60) then (53,59), so right-to-left is witnessed five times with no exception. Row 53 reads colour 2 from column 10 to column 58 in the window I am given and I have never been shown columns 0 to 9 of that row, so at least 49 and at most 59 cells remain. Seventeen commands bought five ticks; both surviving readings put the rate at one tick per three counted commands, so of order 150 to 180 commands remain. Probing is cheap and the cheapness is a measured quantity -- but see the clock theorem, because if this is a budget then cheap is not the same as free, and the fourteen presses that produced no new state were the expensive kind."
    [depends: the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied  probe: passed]

  theorem a_repeat_of_a_blanking_key_has_still_never_been_tried_and_no_longer_separates_the_cadence "key(3) blanked a shown strip at t3, t7, t9, t11, t13, t15 and t17, key(7) blanked one at t5, key(4) restored a blanked one at t4, t6, t8, t10, t12, t14 and t16 -- fifteen presses, every blank from a shown strip and every restore from a blanked one, twelve cells and cell for cell identical every time. Hide-and-show and toggle-and-toggle remain indistinguishable and this probe is still the only thing that separates them. What has CHANGED is its price in cadence information, and I record the loss rather than quietly leaving the old justification standing: last round I sold this press partly on separating F from D and E on the tick, and F is dead. From the present position both survivors say a single extra strip press does not tick -- D reaches two-frame ordinal 17, E reaches work ordinal 15, neither a tick point -- so the press now buys structure and inertness, not cadence. My manual commits to complete inertness: every strip cell is colour 4, no blanking guard can fire, and the march cannot fire because (53,58) has never varied and has no instance. If the strip returns, hide-and-show is dead. If anything moves at all, my inertness claim is dead. Both are worth having and neither is worth the first slot any more."
    [depends: readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them  probe: pending]

  theorem the_cadence_is_inexpressible_and_the_period_three_finding_makes_that_sharper_rather_than_softer "a guard reads a cell colour, its four neighbour colours, off-board, and the action name. Both surviving readings need a counter modulo three, and the grammar has no counter and no latch. Five ticks at an exact period of three is now the best-established quantitative fact in the record and it is exactly the fact I cannot write down. I re-examined one loophole with the new data, because a three-cycle is the shape a colour cycle could carry: paint the frontier cell through two intermediate colours and let the third press finish it at 3. It fails on the frame rather than on the grammar. Every cell of this world is drawn and compared, so an intermediate colour is a visibly wrong cell for two presses out of every three, which trades the march's wrong cell for a differently wrong cell at no gain -- and there is no cell anywhere in the frame whose colour the record leaves free to use as scratch. The other three loopholes stay shut as before: an object at the background colour exposes no readable field, a second type at colour 2 duplicates all fourteen Studs because the arm finds objects by colour alone, and a landmark can be read but never painted. The hidden bit stays prose."
    [depends: readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them  probe: passed]

  theorem the_landmark_and_teleport_device_would_reach_the_next_bar_cell_and_i_refuse_it "the one device in the grammar that touches a cell no object occupies is the landmark, so I priced it properly rather than asserting the frontier was unreachable. A landmark bar_frontier at arc-cell (53,58) is legal and can be READ by a guard. It cannot be PAINTED: the event table dispatches recolored on an object name, and the only events taking a landmark are jumped and teleported, which MOVE an object to that cell. So the sole way to colour (53,58) is to teleport a Stud into it, and that is where the device fails on the world rather than on the grammar. Teleporting the (53,59) Stud vacates (53,59), which the world converted at t17 and which must stay colour 3 -- I would gain the frontier and destroy the cell behind it, turning the bar's converted prefix into a single travelling cell and contradicting five witnessed conversions that all persisted. Teleporting a strip Stud instead breaks a toggle that is 192 for 192. Beyond that, no transition in seventeen witnesses any position change at all: my entire event vocabulary is recolored, and cegis_miner independently refuses every track on the ground that the world does not narrate as one mover."
    [depends: the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied  probe: passed]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language produces them. A guard sees a cell's own colour, its four neighbour colours, off-board, and the action name -- no coordinate, no row band, no distance. The witness is inside the divergence report certify returned again this round: (30,16), (31,16), (32,16), (33,16) and (34,16) are all colour 5 in frame 0 with above 5, below 5, left 5, right 4, one indistinguishable guard reading, and the world makes them 6, 6, 1, 2, 6. Three answers to one question. A second pair kills colour as a discriminator: (30,13) is colour 3 and becomes 6 while (32,13) is colour 2 in an equally uniform bar neighbourhood and also becomes 6. Constraint 5 forbids two rules that both fire, so the swap does not go in the manual."
    [depends: the_panel_is_a_column_of_slots  probe: passed]

  theorem the_swap_also_fails_the_compression_test "grant every expressibility obstacle removed and free reading of position. The swap still does not belong. It repaints 96 cells whose new colours follow no local law, because the widget is teleported six rows and no event in the vocabulary does that -- moved is one cell, jumped-over is two, jumped-to-a-landmark needs a landmark and a rule per instance. The shortest form I can construct is of order one landmark and one rule per repainted cell in both directions, longer than the 96 pixels it explains. Constraint 3 refuses it independently of constraint 5. Two independent refusals, which is why I expect never to write the swap rather than merely not to have written it yet."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem a_background_object_would_own_exactly_the_swap_footprint_and_i_still_do_not_declare_it "an object declared at arc-colour 5 with arc-instances all would be placed on the colour-5 cells the board cannot explain, and those number exactly 101 minus 77 = 24: cols 11, 12, 15, 16 over rows 30-35, the unselected slot footprint, not one cell more, and the count survived the store growing by two because both new cells were colour 2. The declaration is cheap and surgical. I still do not declare it, because it would explain no pixel the board does not already draw correctly and would enable no rule I can write, which is constraint 3 refusing it on its own terms."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_restore_and_blank_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "the restore rules guard on colour 4 alone and the blanking rules on one to three neighbour tests. Both are correct on all fifteen blank-or-restore presses, because every press was made with the bottom slot selected, where the only colour-4 Pip and Stud instances in existence are the twelve blanked lane B cells. They would be wrong the moment slot A is selected: lane A strip cells become texture while lane B strip cells become arena fill of colour 4, and the instances do not move with the widget because I only ever recolour. My manual never reaches that state, being silent on the selector, so this costs zero transitions and certify cannot see it. It is written here because a searcher planning through a selector move would be misled by rules scoring 192 of 192 -- and because the excursion the playbook now ranks second walks straight into it. The mitigation is a condition on the probe, not avoidance of it: press no strip key while the upper slot is selected. An out-and-back pair of selector presses satisfies that by construction, which is why the order names the pair rather than the single press."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, a period-3 run offset by one column; the divergence report gives lane A row 32 cols 16-22 as the world drew it at t1, 1 2 1 1 2 1 1, and rows 32 and 38 agree because 6 divides by 3. The two port cells fit the same formula, which is an unforced success. So the two strips are two windows onto one texture, which is why a restore rebuilds twelve cells exactly and why seven restores rebuilt them identically. Untested prediction: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2. No rule needs this, since each instance remembers its frame 0 colour, so the concept buys understanding rather than symbols and stays out of the word table."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, eight times now, twelve cells every time. (38,16)=1 and (39,16)=2 sit on the widget right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since the left neighbour of each is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The rival explanation is that col 16 is where the 6x6 widget ends and the survival is coincidence; eight blanks do not separate them."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots "the divergence report gives the world's t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at those columns read identically -- eighteen cells, six rows apart. Rows 42 to 52 are uniform background, so rows 36-41 is the bottom slot and rows 30-35 the one above it. ACTION1 moved selection from the bottom slot to the upper one and ACTION2 moved it back, one witness each for up and down, no wrap needed. Whether a third slot exists above is untested: (29,13) and (29,14) hold colour 3 and never vary, which is what a slot at rows 24-29 would show on its bottom rail, but board cells prove nothing about slots never selected."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_badge_is_lane_aligned_and_the_matching_reading_stays_downgraded "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45. Those are exactly the rows an upper-slot cavity occupies within its six-row band, so the badge belongs to the lane of the slot at rows 30-35, and the bottom slot's lane has nothing at cols 42-45. The tempting reading is that it is a target the lane texture must be made to match, but the strip is 2 by 6 and the badge is 4 by 4 of one uniform colour, so shape refutes it. The surviving readings are that it marks which slot carries the task, that it is a destination, or that it is a picture of a completed cavity, the widget cavity being also 4x4 with a 2x2 core removed. Seventeen transitions and none of them bear on any of the three; colour 14 appears nowhere else in the frame. This is the strongest single hint that the ending lives outside the product of states my pressed keys generate."
    [depends: the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending  probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone now spans the unselected slot bar, a port, four strip cells and five meter cells -- four unrelated roles in one type, and the count grows every time the bar converts, which is the clearest possible sign that the type is an artefact of the arm rather than a thing in the world. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 77 cells that need an owner against 77 pixels written out, with 0 unexplained confirmed every round it has been checked. The cost is measured too: no rule can name the strip, so every blanking rule carves it out of its colour class by neighbour tests, and the march is kept off nine other Studs by a right-neighbour test that is a fact about the bar's geometry rather than about the meter. Those guards are pixel-fitting in a costume, and the march is the worst offender because its guard is an accident of what has already ticked."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, rows 29-54 by cols 10-63. They live in the 3995 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is where a title, target, score or instruction would live, and the likeliest home of whatever finishing means and of whether the bar is a budget or a score. Seventeen commands have not made one cell of it vary, which is mild evidence that it is decoration, but only mild, since fourteen of the seventeen were the same two keys and the two keys generate a closed space."
    [depends: the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending  probe: pending]

  theorem two_keys_have_never_been_pressed_and_they_are_now_the_first_thing_to_press "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not, after eighteen commands. They have sat at rank four in the playbook for five drafts and I am moving them to rank one, and the reason is not impatience. It is the closure argument: the five pressed keys move the world only inside a product of strip state, selector slot and meter length, all eighteen states are in that product, and nothing in that product has ever returned anything but NOT_FINISHED. An unpressed key is the only cheap thing that can leave it. Of order 150 to 180 commands of bar remain so two presses are affordable, and each press also reads its own returned frame count, which reading D turns into a direct measurement of the counter -- a non-strip two-frame press is exactly the thing that separates D from E, so if either key returns two frames it does the cadence work as a side effect. If either is a click carrying coordinates, this guard language cannot express it and the finding is recorded as prose rather than as a rule."
    [depends: the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "the store moved so the engines moved, and they moved the way a store update moves them rather than the way a discovery does. mdl_segmenter still returns negative gain on both variants, now -2457 bits at 4 tracks and -34069 at 89, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator rather than the world. Its obj1 is 108 cells of shape 2 by 54 present in all eighteen frames, which is rows 53 and 54 clipped to the window, the meter bar and the fill row beneath it, fused because colour 2 and colour 4 touch vertically and background 5 does not separate them; it corroborates that the bar is one object continuing left of column 10 where I have never seen it. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition, and its verdict that the world does not narrate as one mover agrees with my event vocabulary of recolored alone and is the outside evidence I leaned on when refusing the teleport device. zero_space calls its own evidence THIN in its own words -- 17 transitions constraining rank 7 of 707 features, null space of dimension 700 -- and its single global law spans 101 dynamic cells at once, which is what a 700-dimensional null space produces rather than what a conservation law looks like. Its cell list, ninety-six slot cells plus the five meter cells (53,59) through (53,63), is exactly my dynamic set and is the one thing in the stream I use. Four extra transitions moved zero_space's rank from 5 to 7 and its verdict not at all."
    [probe: pending]

  theorem what_this_draft_pre_registers "certify first, and I pre-register a WORSE number than last round on purpose, because the store grew under a rule I did not edit. Replay 7 of 17, matching at t2, t3, t4, t5, t6, t8 and t17 and diverging everywhere else; first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6; responsibility 0 unexplained of 4096; unambiguous 0 clashes over 18 states by 3 actions, 54 pairs, 54 nominal, 0 step crashes. If replay comes back at 9 or 6 rather than 7 my trace of the march's lead is wrong and I want the trace corrected before anything else. Now the world. Present position: 33 internal frames spent, 16 two-frame commands, 14 work presses, bar converted through (53,59), strip blanked, selector home. Probe one, key(5) then key(6): anything at all is new, the returned frame count is read regardless, and if either returns two frames it also separates D from E on the following strip press. Probe two, ACTION1 then ACTION2 then a strip key: D ticks (53,58) on the strip key, E does not; the pair returns the frame to its start and no strip key is pressed while the upper slot is selected. Probe three, repeat ACTION3 from the blanked state: my manual says not one cell changes and both surviving readings say no tick; if the strip returns, hide-and-show is dead. Probe four, three consecutive work presses with nothing between: both D and E say the third of them converts (53,58), which my manual cannot draw and will get wrong -- that is the pre-registered cost of the frontier blindness and I state it before paying it."
    [depends: readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- fourteenth draft.
#
# WHAT MOVED, AND WHY.
#
# 1. THE TOP OF THE ORDER CHANGED FOR THE FIRST TIME IN FIVE DRAFTS, AND NOT
#    OUT OF BOREDOM. Four commands were finally pressed and what they taught
#    me was structural: the five keys I have pressed move the world only
#    inside a product of three coordinates -- strip shown or blanked, selector
#    in one of two slots, meter length k. All eighteen states are in that
#    product, the world's own hashes confirm it (s14 and s16 answered the
#    identical hash), and every one of them returned NOT_FINISHED. A closed
#    space that has never contained the ending cannot be explored into
#    containing it. So the two keys never pressed go first.
#
# 2. THE CADENCE QUESTION SHRANK BY ONE READING AND GOT ONE CLEAN PRESS.
#    Reading F is dead -- it required the tick at t15, the world ticked at
#    t14. D and E are both 5 for 5 and are provably inseparable by any run of
#    strip keys, because over such a run the two counters advance in lockstep.
#    That is why fourteen presses bought no discrimination and why one
#    selector excursion buys all of it. The excursion moves up to second.
#
# 3. THE REPEAT-BLANK PROBE LOST HALF ITS VALUE AND I DEMOTE IT RATHER THAN
#    RE-ARGUING FOR IT. It used to separate F from D and E on the tick; F is
#    gone, and both survivors now agree that one extra strip press does not
#    tick. It still separates hide-and-show from toggle-and-toggle, which
#    nothing else does, so it stays third rather than falling off.
#
# 4. NEW PRUNE, AND IT IS THE MOST EXPENSIVE THING I HAVE LEARNED. Fourteen
#    work presses accomplished nothing and the meter advanced five times
#    regardless. A quantity that rises at a fixed rate whatever you do is a
#    clock. That is not proof and there is still no goal section, but it flips
#    the price of a press that produces a state I have already seen from free
#    to costly, and the toggle loop I ran for four rounds was the worst
#    offender in the record.
#
# 5. STILL NO PLAN HERE. These are orders of interrogation.

order   press_the_two_never_pressed_keys_before_anything_else  [proof: lean]
order   take_the_selector_excursion_as_a_pair_then_one_strip_key_to_split_D_from_E  [proof: lean]
order   repeat_a_blanking_key_in_the_blanked_state_to_kill_hide_or_toggle  [proof: lean]
order   read_the_returned_frame_count_of_every_command_since_one_reading_counts_it  [proof: lean]
order   prefer_a_press_that_leaves_the_reachable_product_over_one_that_moves_inside_it  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_since_a_reading_rests_on_it  [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   look_at_the_badge_lane_while_its_own_slot_is_the_selected_one  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule  [proof: lean]
order   make_some_cell_outside_the_observed_window_vary  [proof: lean]
order   vary_the_order_of_the_two_blanking_keys_across_a_restore  [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known  [proof: lean]
order   read_every_bar_cell_after_every_command  [proof: lean]

prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  an_action_that_can_leave_the_closed_product_of_states_already_enumerated  [ev: 12/12 states in the product]
prefer  an_action_the_two_surviving_counter_readings_give_different_answers_for  [ev: 2 readings, each 5/5 on 5 ticks]
prefer  a_non_strip_two_frame_press_since_only_that_advances_the_readings_differently  [ev: 14/14 work presses moved both alike]
prefer  an_action_that_answers_more_than_one_open_question_at_once  [ev: 1 press separates 3]
prefer  an_action_the_manual_has_pre_registered_a_null_frame_for  [ev: 0/17 transitions tested it]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/17 commands returned one frame]
prefer  a_slot_never_selected_over_one_already_drawn_twice  [ev: 2 slots seen of a column]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats  [ev: 101/4096 cells ever varied]
prefer  a_probe_launched_from_a_state_the_manual_reconstructs_exactly  [ev: 4096/4096 cells right now]
prefer  an_excursion_that_returns_the_frame_to_where_it_started  [ev: 1/17 commands undid another]

heuristic state_classes_outside_the_enumerated_product  [admissible: lean]
heuristic keys_never_pressed  [admissible: lean]
heuristic counter_readings_still_alive  [admissible: lean]
heuristic presses_needed_to_separate_the_surviving_counter_readings  [admissible: lean]
heuristic bar_cells_still_unconverted  [admissible: lean]
heuristic slots_in_the_column_never_yet_selected  [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed  [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed  [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness  [admissible: lean]

prune   plan_that_spends_a_work_press_and_returns_a_state_already_enumerated => dead  [proof: lean]
prune   plan_that_expects_a_run_of_strip_keys_to_separate_the_two_readings => dead  [proof: lean]
prune   plan_that_treats_the_internal_frame_total_reading_as_still_alive => dead  [proof: lean]
prune   plan_that_counts_the_lone_one_frame_command_toward_the_cadence => dead  [proof: lean]
prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead  [proof: lean]
prune   plan_that_assumes_the_checker_resyncs_the_manual_between_transitions => dead  [proof: lean]
prune   plan_that_assumes_a_rule_replays_the_same_after_the_store_grows => dead  [proof: lean]
prune   plan_that_ties_the_bar_tick_to_one_particular_key => dead  [proof: lean]
prune   plan_that_prices_a_bar_cell_at_one_per_restore_press => dead  [proof: lean]
prune   plan_that_counts_the_bar_on_raw_command_number_alone => dead  [proof: lean]
prune   plan_that_asks_the_manual_to_tick_a_bar_cell_never_yet_witnessed => dead  [proof: lean]
prune   plan_that_needs_a_cell_that_has_never_varied_to_change => dead  [proof: lean]
prune   plan_that_teleports_an_object_out_of_a_cell_the_bar_has_converted => dead  [proof: lean]
prune   plan_that_rests_on_the_bar_meaning_being_known => dead  [proof: lean]
prune   plan_that_spends_the_manuals_present_exactness_and_returns_no_new_frame => dead  [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead  [proof: lean]
prune   plan_that_presses_a_strip_key_while_the_upper_slot_is_selected => dead  [proof: lean]
prune   plan_that_treats_the_two_blanking_keys_as_interchangeable => dead  [proof: lean]
prune   plan_whose_rules_are_longer_than_the_pixels_they_draw => dead  [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_spends_a_round_on_a_manual_that_does_not_compile => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead  [proof: lean]
prune   bar_consumed and not goal => dead  [proof: lean]
```

## Why you are being called: the surprises that fired

### replay_mismatch (empirical family -> theory.dsl)

replay diverges at t=0 (frame_mismatch)

```json
{
 "arc_action": "ACTION1",
 "cells": [
  {
   "cell": [
    30,
    11
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    30,
    12
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    30,
    13
   ],
   "manual_says": 3,
   "world_says": 6
  },
  {
   "cell": [
    30,
    14
   ],
   "manual_says": 3,
   "world_says": 6
  },
  {
   "cell": [
    30,
    15
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    30,
    16
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    31,
    11
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    31,
    12
   ],
   "manual_says": 5,
   "world_says": 0
  },
  {
   "cell": [
    31,
    13
   ],
   "manual_says": 3,
   "world_says": 0
  },
  {
   "cell": [
    31,
    14
   ],
   "manual_says": 3,
   "world_says": 0
  },
  {
   "cell": [
    31,
    15
   ],
   "manual_says": 5,
   "world_says": 0
  },
  {
   "cell": [
    31,
    16
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    32,
    11
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    32,
    12
   ],
   "manual_says": 5,
   "world_says": 0
  },
  {
   "cell": [
    32,
    13
   ],
   "manual_says": 2,
   "world_says": 6
  },
  {
   "cell": [
    32,
    14
   ],
   "manual_says": 2,
   "world_says": 6
  },
  {
   "cell": [
    32,
    15
   ],
   "manual_says": 5,
   "world_says": 0
  },
  {
   "cell": [
    32,
    16
   ],
   "manual_says": 5,
   "world_says": 1
  },
  {
   "cell": [
    32,
    17
   ],
   "manual_says": 4,
   "world_says": 2
  },
  {
   "cell": [
    32,
    18
   ],
   "manual_says": 4,
   "world_says": 1
  },
  {
   "cell": [
    32,
    19
   ],
   "manual_says": 4,
   "world_says": 1
  },
  {
   "cell": [
    32,
    20
   ],
   "manual_says": 4,
   "world_says": 2
  },
  {
   "cell": [
    32,
    21
   ],
   "manual_says": 4,
   "world_says": 1
  },
  {
   "cell": [
    32,
    22
   ],
   "manual_says": 4,
   "world_says": 1
  }
 ],
 "cells_wrong": 96,
 "kind": "frame_mismatch",
 "t": 0
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
  "arc_action": "ACTION1",
  "cells": [
   {
    "cell": [
     30,
     11
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     30,
     12
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     30,
     13
    ],
    "manual_says": 3,
    "world_says": 6
   },
   {
    "cell": [
     30,
     14
    ],
    "manual_says": 3,
    "world_says": 6
   },
   {
    "cell": [
     30,
     15
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     30,
     16
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     31,
     11
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     31,
     12
    ],
    "manual_says": 5,
    "world_says": 0
   },
   {
    "cell": [
     31,
     13
    ],
    "manual_says": 3,
    "world_says": 0
   },
   {
    "cell": [
     31,
     14
    ],
    "manual_says": 3,
    "world_says": 0
   },
   {
    "cell": [
     31,
     15
    ],
    "manual_says": 5,
    "world_says": 0
   },
   {
    "cell": [
     31,
     16
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     32,
     11
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     32,
     12
    ],
    "manual_says": 5,
    "world_says": 0
   },
   {
    "cell": [
     32,
     13
    ],
    "manual_says": 2,
    "world_says": 6
   },
   {
    "cell": [
     32,
     14
    ],
    "manual_says": 2,
    "world_says": 6
   },
   {
    "cell": [
     32,
     15
    ],
    "manual_says": 5,
    "world_says": 0
   },
   {
    "cell": [
     32,
     16
    ],
    "manual_says": 5,
    "world_says": 1
   },
   {
    "cell": [
     32,
     17
    ],
    "manual_says": 4,
    "world_says": 2
   },
   {
    "cell": [
     32,
     18
    ],
    "manual_says": 4,
    "world_says": 1
   },
   {
    "cell": [
     32,
     19
    ],
    "manual_says": 4,
    "world_says": 1
   },
   {
    "cell": [
     32,
     20
    ],
    "manual_says": 4,
    "world_says": 2
   },
   {
    "cell": [
     32,
     21
    ],
    "manual_says": 4,
    "world_says": 1
   },
   {
    "cell": [
     32,
     22
    ],
    "manual_says": 4,
    "world_says": 1
   }
  ],
  "cells_wrong": 96,
  "kind": "frame_mismatch",
  "t": 0
 },
 "proof_layer_available": false,
 "replay": {
  "detail": "7/17 transitions replay exactly",
  "matched": 7,
  "ok": false,
  "transitions": 17
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
  "detail": "no (state, action) among 18 x 3 admitted two rules, and all 54 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 54,
  "pairs_nominal": 54,
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
# theory.dsl -- FIFTEENTH DRAFT.
#
# 0. NO COMMAND WAS PRESSED THIS ROUND. The store is byte-identical to last
#    round's: steps 18, states 18, distinct_states 12, dynamic_cells 101,
#    cells_needing_an_owner 77, constant_cells 3995, same 17 diffs. So this
#    draft has no new world evidence at all. It has exactly one new source of
#    evidence, certify, and I say up front what that can and cannot buy.
#
# 1. WHAT IT BOUGHT: THE PRE-REGISTRATION CAME BACK FOUR FOR FOUR, EXACT.
#    Last draft pre-registered replay 7/17 (a WORSE number than the 9/13 it
#    was replacing), first divergence at transition 0 under ACTION1 with 96
#    cells wrong and first cell (30,11) manual 5 world 6, responsibility 0
#    unexplained of 4096, and unambiguous 0 clashes over 18 states x 3
#    actions = 54 pairs, 54 nominal, 0 step crashes. Certify returned every
#    one of those, to the digit. A manual that predicts its own score,
#    including its own regression, is a self-model rather than a flattering
#    one, and that is this round's whole gain.
#
# 2. WHAT IT CANNOT BUY: A THEORY OF THE WORLD. Certify replays the manual
#    against a record it has already seen. Four rounds of prose on a static
#    record have now returned diminishing evidence, and the binding
#    constraint is not the quality of this manual but the absence of a
#    nineteenth state. The playbook is rewritten around that.
#
# 3. TWO REAL SHARPENINGS, BOTH DERIVED FROM THE RECORD I ALREADY HAVE.
#    (a) A landmark makes ANY cell readable by a guard, so the cadence
#    obstacle is not that the grammar cannot read a counter -- it is that no
#    cell of the frame carries one. I checked all 4096. Every dynamic cell is
#    period two or monotone; there is no period-three quantity anywhere to
#    read. That is a stronger and checkable form of a claim I had been making
#    loosely for five drafts.
#    (b) Reading D has a twin, D' ("count every command that is not
#    ACTION7"), which is identical to D on all seventeen commands. I had been
#    treating D as one reading. The excursion probe still splits {D,D'} from
#    E, and a key(5)/key(6) press that returns one frame splits D from D'.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Casing { pos: Coord, color: Int }  # arc-colour: 6  arc-instances: all
  object Cavity { pos: Coord, color: Int }  # arc-colour: 0  arc-instances: all
  object Rail { pos: Coord, color: Int }  # arc-colour: 3  arc-instances: all
  object Pip { pos: Coord, color: Int }  # arc-colour: 1  arc-instances: all
  object Stud { pos: Coord, color: Int }  # arc-colour: 2  arc-instances: all
  object Erased { pos: Coord, color: Int }  # arc-colour: 4  arc-instances: all
  Casing [segment: colour_class_6 ev: t0-t17 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t17 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t17 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t17 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t17 compress: 14]
  Erased [segment: colour_class_4 ev: t0-t17 compress: 12]

events:
  event recolored(o, c)

# Eight rules, unchanged, because no transition arrived that could touch
# them. Six are the strip toggle: seven ACTION3 blanks, one ACTION7 blank,
# seven ACTION4 restores, 12 cells every time, 192 cell-recolourings, every
# one correct. One is the seed. One is the march.
#
# THE MARCH'S ev TAG CITES THE WORLD'S CONVERSIONS, NOT ITS OWN FIRINGS. The
# world converted (53,62) at t8, (53,61) at t11, (53,60) at t14 and (53,59)
# at t17; the march is the only rule accounting for any of them, and it FIRES
# at t7, t9, t11 and t13. Citing the firings would hide a four-command phase
# error inside a tag. The error is written out at full length in
# the_march_leads_by_four_commands_and_the_seven_of_seventeen_was_exact, and
# certify has now priced it at precisely the ten transitions I said it would.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3,t7,t9,t11,t13,t15,t17 cov: 56/56]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3,t7,t9,t11,t13,t15,t17 cov: 28/28]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4,t6,t8,t10,t12,t14,t16 cov: 56/56]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4,t6,t8,t10,t12,t14,t16 cov: 28/28]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_seeds_the_meter_at_the_right_edge forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

  rule key3_marches_the_meter_leftward forall ?p in Stud [ev: t8,t11,t14,t17 cov: 4/4]
    when act=key(3) and colored(?p, 2) and colored(rightof(?p), 3) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 14 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 77 [status: proven]

  theorem certify_confirmed_every_pre_registered_number_and_that_is_this_rounds_only_evidence "last draft closed with four numbers written down before they could be measured, and certify returned all four exactly. Replay 7 of 17 -- pre-registered 7, and pre-registered DOWNWARD from the 9 of 13 the previous certify had returned, because the store had grown two Stud instances under a rule I did not edit. First divergence transition 0, ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6 -- identical to the report I predicted, cell for cell. Responsibility 0 unexplained of 4096. Unambiguous 0 clashes, 54 pairs checked of 54 nominal, 0 step crashes, exactly the 18 x 3 enumeration I said it would be. I claimed that if replay came back at 9 or 6 rather than 7 then my trace of the march's four-command lead was wrong; it came back at 7, so the trace stands, and I record the trace as confirmed rather than merely consistent: the manual is wrong at t1 and at t7 and at t9 through t16, and right at t2, t3, t4, t5, t6, t8 and t17. That is a defect I can compute, which is a different thing from a defect I can only regret. It is also the entire content of this round, and the next theorem says why."
    [depends: the_march_leads_by_four_commands_and_the_seven_of_seventeen_was_exact  probe: passed]

  theorem no_command_was_pressed_this_round_and_that_is_now_the_binding_constraint "the store is identical to last round's in every field: 18 steps, 18 states, 12 distinct, 101 dynamic cells, 77 owners, 3995 constant, the same seventeen diffs. Four probes were pre-registered and none was executed. So this draft is written on exactly the evidence the last one had, and I will not pretend otherwise by dressing re-derivation up as discovery: the two sharpenings below are things I could have derived last round and did not, not things the world told me. The honest consequence is a claim about where the value now sits. Certify measures the manual against a record it has already seen, and the manual now scores 0 unexplained, 0 clashes, and a replay whose every miss it predicts in advance. There is nothing left for certify to teach me. The eighteen states occupy a product of three coordinates that every one of them returns NOT_FINISHED from. One press of an unpressed key is worth more than any number of further drafts, and the playbook is reordered so that its first line is a press rather than an analysis."
    [depends: the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending  probe: passed]

  theorem the_four_probe_hashes_decode_the_entire_state_space "four refutations, P-09 through P-12, of one defect, and together they hand me the state lattice off four sixteen-hex-digit strings. 1317da5b367d300a is the manual's answer to ACTION4 and its starting point before ACTION3, a strip-SHOWN state; b278887e087d3593 is the mirror, strip-BLANKED; both carry the manual's bar. The world answered 3281b51b4c1aa929 to ACTION4 at BOTH t14 and t16 -- the same hash twice, the world itself saying s14 and s16 are the identical frame -- and d2c8aa05e38a2da7 to ACTION3 at t15 against febfe034e90989ad at t17, two hashes because (53,59) converted in between. So a state is a PRODUCT: strip shown-or-blanked, times bar length, times which slot the selector holds. Enumerate against the store without a press: s0, s1 swapped, s3 blanked-no-bar, s4 shown-one, s5 blanked-one, s8 shown-two, s9 blanked-two, s11 blanked-three, s12 shown-three, s14 shown-four, s15 blanked-four, s17 blanked-five. Twelve, and distinct_states is 12. The collapses are s2=s0, s6=s4, s7=s5, s10=s8, s13=s11, s16=s14 -- six, and 18 minus 6 is 12. The lattice closes exactly, and the consequence I care about is that this product has no room in it for winning."
    [depends: the_world_is_not_a_function_of_the_visible_frame  probe: passed]

  theorem the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending "eighteen states, every one NOT_FINISHED, and the lattice shows that is not bad luck. Keys 1, 2, 3, 4 and 7 move the world only within a product of three coordinates: strip shown or blanked, selector in one of two slots, meter converted to k. The first two are involutions -- toggled eleven and two times, always landing back where they started -- and the third is monotone and moves on a schedule no key controls. So eighteen commands have ACHIEVED only the spending of meter. If the ending lives anywhere it lives outside this product, which needs either a key never pressed or a panel state never built. The weakness I state plainly: the product is complete only over the eighteen states I have, which is exactly the kind of assumption a new key exists to break."
    [depends: the_four_probe_hashes_decode_the_entire_state_space  probe: pending]

  theorem reading_F_is_dead_and_the_press_that_killed_it_was_t14 "F said the meter ticks on the command during which the running total of internal frames crosses a multiple of seven. It was 3 of 3 when written and given equal standing with D and E deliberately, because three ticks cannot pin a counter. Totals after each command: 2, 4, 6, 8, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33. Seven is crossed during t4, fourteen during t8, twenty-one reached at t11. Twenty-eight is crossed during t15, because t14 takes the total from 25 only to 27. The world ticked at t14 and not at t15. F predicted the wrong command and dies on it. A reading I had never bothered to write down, E'' (count every strip-affecting press INCLUDING the ACTION7 at t5), dies with it: its tick ordinals are 2, 6, 9, 12, 15, and 2 against 6 is a gap of four where every later gap is three. The exclusion of t5 is therefore not optional under any surviving reading."
    [depends: readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them  probe: passed]

  theorem readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them "ticks fell at commands 4, 8, 11, 14 and 17 of seventeen. Reading D counts commands that returned TWO frames and ticks on every third: the two-frame ordinals of the ticking commands are 4, 7, 10, 13, 16, an exact progression of step three with no false positive among the eleven non-ticking commands. Reading E counts presses of ACTION3 or ACTION4 only and ticks on every third from the second: work-press ordinals 2, 5, 8, 11, 14, again exact, again no false positive. They cannot be separated by any run of strip keys, because over such a run every command is both a two-frame command and a work press and the counters advance in lockstep -- which is what the last fourteen commands were, and why fourteen commands of evidence bought no discrimination. From the present position of 16 two-frame commands and 14 work presses: press ACTION1, then ACTION2, then any strip key. D reaches two-frame ordinal 19 and ticks on the strip key; E reaches work ordinal 15 and does not. One bit, three presses, and the selector pair returns the frame home so the strip key is pressed with the bottom slot selected."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: pending]

  theorem reading_D_has_a_twin_this_record_cannot_separate_and_the_same_press_buys_both_bits "I have been writing D as one reading and it is two. D is 'count commands returning two frames'. D-prime is 'count every command that is not ACTION7'. On this record they are the same function, because the ACTION7 at t5 is the only command that returned one frame -- one coincidence doing the work of two hypotheses, which is exactly the situation that produced reading F and then killed it. I record the twin now rather than after it costs me a probe. Nothing in the seventeen commands separates them, and they agree on the selector excursion (ACTION1 and ACTION2 are both non-ACTION7 and both two-frame), so that probe still buys the D-versus-E bit it claims. What separates D from D-prime is a command that is neither ACTION7 nor two-frame -- that is, an unpressed key that returns a single frame. So if key(5) or key(6) comes back with frames=1, the following strip press separates the twins for free: D does not count the single-frame press and does not tick, D-prime counts it and does tick. The playbook's first probe therefore buys a cadence bit as a side effect of buying a structural one, which is why it stays first even on cadence grounds."
    [depends: readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them  probe: pending]

  theorem the_meter_advances_for_no_achievement_and_that_tilts_it_toward_clock "for six drafts I have refused to say whether colour 3 on the bar means consumed or filled, because the two invert every ranking. The tilt, recorded without overstatement: fourteen work presses accomplished nothing -- the strip was blanked and restored and blanked and restored and stands blanked now exactly as at t3 -- and the meter advanced five times through all of it, on a schedule keyed to the number of presses rather than their content, three times under ACTION4 and twice under ACTION3, so it is not paying out for a deed. A quantity that rises at a fixed rate whatever you do is a clock; a quantity that rises when you achieve something is a score, and I have achieved nothing. Still not proof: a designer may credit mere activity, and I have never seen the left end of row 53 nor any label for it. What changes is the playbook, not the goal section. If this is a clock then a press producing a state I have already seen is a press spent for nothing, and the toggle loop is the most expensive thing in the record."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: pending]

  theorem the_march_leads_by_four_commands_and_the_seven_of_seventeen_was_exact "the seed paints (53,63) at t4, correctly. The march then fires at t7, t9, t11 and t13, painting (53,62), (53,61), (53,60) and (53,59), while the world converts those same four cells at t8, t11, t14 and t17. The lead grows one command per conversion. Under open-loop replay errors compound, so t7 and t9 through t16 diverge and only t17 recovers, giving 7 of 17 matching at t2, t3, t4, t5, t6, t8 and t17 -- pre-registered, and returned by certify to the digit. What I get for the ten wrong transitions is the present state: the manual's bar stands at (53,63) through (53,59) converted and so does the world's, so the manual reconstructs the CURRENT frame cell for cell and every probe launched from here starts from truth. Dropping the march scores 6 of 17 -- t2 through t7 -- and leaves the manual four cells wrong right now. I take the exactness, and I name its price honestly: the exactness is luck, not design. The march ran out of instances at (53,58) at the same moment the world caught up, and the very next conversion restores the lead and destroys it. Pre-registered for the next round: if any command is pressed and the world ticks, replay drops and the manual's present frame goes one cell wrong again; if commands are pressed without a tick, replay stays 7 of the new total."
    [depends: the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied  probe: passed]

  theorem the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied "witnessed four times, by P-09 through P-12. The arm instantiates only cells the board cannot explain, and the board is the cells that never vary, so at prediction time (53,60) and (53,59) were board, no rule of mine could name them, and the manual's answer to ACTION4 at t14 and ACTION3 at t17 was necessarily a frame with those cells unconverted. Both refutations are exactly one bar cell: 1317da5b367d300a against 3281b51b4c1aa929, b278887e087d3593 against febfe034e90989ad. The bound is on the store's staleness, not on the world: across a stretch where the world ticks k times without a store refresh, the manual falls k cells behind. The mechanism is not a bug I can fix from inside the manual -- each cell the world converts hands the arm one more instance and hands me one more cell of reach, always one conversion after I needed it."
    [depends: instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances  probe: passed]

  theorem replay_is_open_loop "settled by a four-way table two drafts ago and re-confirmed by the probe stream. P-09's inert hash is b278887e087d3593; P-10's inert hash is 1317da5b367d300a, which is exactly the hash P-09's MANUAL prediction named, not the hash the world answered. The harness carries my prediction forward as its own next state and never resyncs. Same at P-11 and P-12. So the checker replays the manual against itself, a guard on an off-board cell reads false rather than matching, and errors compound rather than being wiped -- which is the whole explanation of why a four-command lead shows up as ten consecutive wrong transitions that close in one, and why certify's 7 was computable in advance."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_first_divergence_is_the_selector_swap_and_i_refuse_to_change_the_manual_for_it "the surprise that called me back is the replay mismatch at transition 0: ACTION1, 96 cells, first cell (30,11) manual 5 world 6. This is the seventh consecutive round in which I have predicted this surprise cell for cell, and the seventh in which I answer it with a refusal rather than an edit. Two independent grounds, both re-checked against the report certify returned again. Ground one, constraint 5: the report contains five cells, (30,16) (31,16) (32,16) (33,16) (34,16), that are colour 5 in frame 0 with above 5, below 5, left 5, right 4 -- one indistinguishable local guard reading -- and the world sends them to 6, 6, 1, 2, 6. Ground two, constraint 3: the shortest expressible form is of order one landmark and one rule per repainted cell in each direction, longer than the 96 pixels it draws. I add the exact price this round, because it is smaller than it looks: the swap costs ONE transition of seventeen, not two, and t2 matches. The reason is that the manual's no-op composed with itself equals the world's swap composed with itself -- ACTION2 undoes ACTION1, so the excursion returns both models to the same frame. A defect that self-cancels over an out-and-back is the cheapest kind there is, and it is another reason the excursion probe is safe to run."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem no_goal_is_signed_and_that_is_deliberate "all eighteen states returned NOT_FINISHED and nothing in seventeen transitions indicates what finishing means. An absent goal compiles to is_goal implies False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. The bar is the only monotone quantity and the most tempting goal, and the evidence has moved toward BUDGET, the reading under which filling the bar is the opposite of winning -- so the tilt argues against signing the tempting goal, not for it. Live candidates unchanged: that a lane must be brought into some relation with the badge at its far end, that every slot in the column must be visited or solved, or that the objective lives in the twenty-nine rows I have never been shown. There is no goal section, and this theorem is where the silence is recorded."
    [depends: the_meter_advances_for_no_achievement_and_that_tilts_it_toward_clock  probe: pending]

  theorem the_march_and_the_blanking_rule_cannot_both_fire "both are guarded on act=key(3) and colored(?p,2), so constraint 5 needs the remaining guards disjoint on every instance in every state. The blanking guard needs the left neighbour neither 0 nor 2; a meter stud's left neighbour is 2 whenever the stud itself is still 2, because the bar converts strictly right to left and no state in the record has a colour-3 cell immediately left of a colour-2 one. The march needs the right neighbour to be 3, which fails for every strip stud (right neighbours only ever 1, 2 or 4), for both unselected-bar studs (2 or 5), for the port stud (1 or 4), and for (53,63) whose right neighbour is off-board and reads false under every guard. Certify adjudicated all 54 pairs over 18 states by 3 actions with zero clashes, as pre-registered. The latent risk is unchanged: a state with a colour-3 cell immediately left of a colour-2 bar cell admits both rules on that cell. The monotone right-to-left order forbids it, and that order is witnessed five times -- witnessed, not proven."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: passed]

  theorem the_world_is_not_a_function_of_the_visible_frame "witnessed three times and under both strip keys, which removes the chance that it was an artefact of ACTION4. s5 and s7 are the same 4096 cells; ACTION4 from s5 restored twelve cells, ACTION4 from s7 restored twelve and ticked (53,62). s8 and s10 are the same cells; ACTION3 from s8 blanked twelve, ACTION3 from s10 blanked twelve and ticked (53,61). s14 and s16 are the same frame -- the world said so itself by answering the identical hash 3281b51b4c1aa929 to ACTION4 at both -- and the ACTION3 after one did not tick while the ACTION3 after the other did. So the world carries at least one bit no guard of mine can read, constraint 5 forbids me writing both successors of an identical frame, and any planner treating a frame as a state is planning in the wrong space. This holds whichever of D, D-prime and E is right, which is why it survived F's death untouched."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and (53,59) through (53,63) all hold 2 rather than 3. The anatomy closes cell by cell: 22 Casing as the perimeter of rows 36-41 by cols 11-16 minus the two ports plus the 2x2 core at rows 38-39 cols 13-14; 12 Cavity as the 4x4 at rows 37-40 cols 12-15 minus that core; 8 Rail at rows 30-31 and 34-35 by cols 13-14; 4 Stud at rows 32-33 by cols 13-14; 8 Pip and 4 Stud in the lane B strip; 1 Pip at (38,16) and 1 Stud at (39,16) in the ports; 12 Erased as the lane A strip at rows 32-33 cols 17-22; 5 Stud in the meter. 22+12+8+9+14+12 = 77 = cells_needing_an_owner. The 24 remaining dynamic cells are the background of the unselected slot footprint, cols 11, 12, 15, 16 over rows 30-35, and 77+24 = 101 = dynamic_cells, and 4096-101 = 3995 = constant_cells. The dynamic set closes independently: the swap repaints 96 cells and the meter has ticked five times, and 96+5 = 101. Certify returned 0 unexplained of 4096 again this round, as pre-registered."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0; a cell constant across the whole record gets none. The arithmetic has held five times: 73 owners at 97 dynamic, 74 at 98, 75 at 99, 77 at 101, the difference each time exactly the bar cells that converted and my Stud declaration moving by the same number. Twice it has done something sharper than bookkeeping: the instance at (53,61) once changed the behaviour of a rule I did not edit, and the instances at (53,59) and (53,60) did it again in the same direction, turning a march that lagged into one that leads by four. Level data is not inert with respect to the manual. This round the store did not move, and neither did any rule's behaviour -- which is the control case for that claim and the reason the pre-registered 7 was computable at all."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_bar_runs_leftward_and_the_budget_is_measurable "five cells have converted, (53,63) then (53,62) then (53,61) then (53,60) then (53,59), so right-to-left is witnessed five times with no exception. Row 53 reads colour 2 from column 10 to column 58 in the window I am given and I have never been shown columns 0 to 9 of that row, so at least 49 and at most 59 cells remain. Seventeen commands bought five ticks; every surviving reading puts the rate at one tick per three counted commands, so of order 150 to 180 commands remain. Probing is cheap and the cheapness is measured -- but see the clock theorem, because if this is a budget then cheap is not free, and the fourteen presses that produced no new state were the expensive kind."
    [depends: the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied  probe: passed]

  theorem a_repeat_of_a_blanking_key_has_still_never_been_tried "key(3) blanked a shown strip at t3, t7, t9, t11, t13, t15 and t17, key(7) blanked one at t5, key(4) restored a blanked one at t4, t6, t8, t10, t12, t14 and t16 -- fifteen presses, every blank from a shown strip and every restore from a blanked one, twelve cells and cell for cell identical every time. Hide-and-show and toggle-and-toggle remain indistinguishable and this probe is the only thing that separates them. Its cadence value is gone with F, and I record the loss rather than leaving the old justification standing: from the present position every surviving reading says one extra strip press does not tick, since D reaches two-frame ordinal 17 and E reaches work ordinal 15, neither a tick point. My manual commits to complete inertness -- every strip cell is colour 4, no blanking guard can fire, and the march cannot fire because (53,58) has never varied and has no instance. If the strip returns, hide-and-show is dead. If anything moves at all, my inertness claim is dead. Both are worth having and neither is worth the first slot."
    [depends: readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them  probe: pending]

  theorem the_cadence_is_inexpressible_and_no_cell_of_the_frame_cycles_with_period_three "I have said for five drafts that the grammar has no counter, and that was the weaker half of the truth. The stronger half, derived this round and checkable against the record I already have: a landmark makes ANY cell of the frame readable by a guard, since a landmark name is a legal cell and colored(<cell>, <int>) is a legal guard. So reading is not the obstacle. The obstacle is that nothing in the frame carries a period-three quantity, and I checked all 4096 cells. 3995 are constant by definition and carry nothing. Of the 101 that vary, 96 are the selector-swap footprint, whose colour is a function of which slot is selected and whether the selected lane's strip is blanked -- two involutions, period two. The other 5 are meter cells, monotone, and their count does not change between ticks, so reading them tells me only what has already happened. Period two and monotone compose to period two; there is no period-three signal anywhere to read, and there is no spare cell to write one into, because every cell of the frame is drawn and compared and an intermediate scratch colour is a visibly wrong cell for two presses in three. The other loopholes stay shut as before: an object at the background colour exposes no readable field, and a second type at colour 2 duplicates all fourteen Studs because the arm finds objects by colour alone. Five ticks at an exact period of three is the best-established quantitative fact in the record and it is exactly the fact I cannot write down. The hidden bit stays prose."
    [depends: readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them  probe: passed]

  theorem the_landmark_and_teleport_device_would_reach_the_next_bar_cell_and_i_refuse_it "the one device in the grammar that touches a cell no object occupies is the landmark, so I priced it rather than asserting the frontier unreachable. A landmark bar_frontier at arc-cell (53,58) is legal and can be READ. It cannot be PAINTED: recolored dispatches on an object name, and the only events taking a landmark are jumped and teleported, which MOVE an object there. So the sole way to colour (53,58) is to teleport a Stud into it, which vacates the source. Teleporting the (53,59) Stud destroys a cell the world converted at t17 and which must stay colour 3, turning the bar's converted prefix into a single travelling cell and contradicting five witnessed conversions that all persisted. Teleporting a strip Stud instead breaks a toggle that is 192 for 192. Beyond that, no transition in seventeen witnesses any position change at all: my entire event vocabulary is recolored, and cegis_miner independently refuses every track on the ground that the world does not narrate as one mover."
    [depends: the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied  probe: passed]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of LOCAL rules produces them. A local guard sees a cell's own colour, its four neighbour colours, off-board, and the action name -- no coordinate, no row band, no distance. The witness is inside the divergence report certify returned again this round: (30,16), (31,16), (32,16), (33,16) and (34,16) are all colour 5 in frame 0 with above 5, below 5, left 5, right 4, one indistinguishable reading, and the world makes them 6, 6, 1, 2, 6. Three answers to one question. A second pair kills colour as a discriminator: (30,13) is colour 3 and becomes 6 while (32,13) is colour 2 in an equally uniform bar neighbourhood and also becomes 6. Constraint 5 forbids two rules that both fire. I now state the boundary of this claim precisely, because the landmark device shows it is not the whole space: a landmark IS a coordinate, so a guard of the form <instance> = <landmark> would pin identity and evade constraint 5 entirely, if it compiles at all. That escape exists and I close it in the next theorem on cost rather than pretending it does not. The two grounds together partition the space of rule sets: local ones die on constraint 5, coordinate-pinned ones die on constraint 3."
    [depends: the_panel_is_a_column_of_slots  probe: passed]

  theorem the_swap_also_fails_the_compression_test "grant every expressibility obstacle removed and free reading of position via landmarks. The swap still does not belong. It repaints 96 cells whose new colours follow no local law, because the widget is teleported six rows and no event in the vocabulary does that -- moved is one cell, jumped-over is two, jumped-to-a-landmark needs a landmark and a rule per instance. The shortest form I can construct is of order 96 landmarks and one rule per repainted cell in each direction, some 190 rules and 96 landmarks to draw 96 pixels. Constraint 3 refuses it independently of constraint 5, and refuses the coordinate-pinning escape at the same time and for the same reason. Two independent refusals covering the whole space, which is why I expect never to write the swap rather than merely not to have written it yet."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem a_background_object_would_own_exactly_the_swap_footprint_and_i_still_do_not_declare_it "an object at arc-colour 5 with arc-instances all would be placed on the colour-5 cells the board cannot explain, and those number exactly 101 minus 77 = 24: cols 11, 12, 15, 16 over rows 30-35, the unselected slot footprint, not one cell more, and the count survived the store growing by two because both new cells were colour 2. The declaration is cheap and surgical. I still do not declare it, because it would explain no pixel the board does not already draw correctly and would enable no rule I can write, which is constraint 3 refusing it on its own terms."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_restore_and_blank_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "the restore rules guard on colour 4 alone and the blanking rules on one to three neighbour tests. Both are correct on all fifteen blank-or-restore presses, because every press was made with the bottom slot selected, where the only colour-4 Pip and Stud instances in existence are the twelve blanked lane B cells. They would be wrong the moment slot A is selected: lane A strip cells become texture while lane B strip cells become arena fill of colour 4, and the instances do not move with the widget because I only ever recolour. My manual never reaches that state, being silent on the selector, so this costs zero transitions and certify cannot see it. It is written here because a searcher planning through a selector move would be misled by rules scoring 192 of 192 -- and because the excursion the playbook ranks second walks straight past it. The mitigation is a condition on the probe, not avoidance of it: press no strip key while the upper slot is selected. An out-and-back pair satisfies that by construction, which is why the order names the pair rather than the single press."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, a period-3 run offset by one column; the divergence report gives lane A row 32 cols 16-22 as the world drew it at t1, 1 2 1 1 2 1 1, and rows 32 and 38 agree because 6 divides by 3. The two port cells fit the same formula, which is an unforced success. So the two strips are two windows onto one texture, which is why a restore rebuilds twelve cells exactly and why seven restores rebuilt them identically. Untested prediction: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2. No rule needs this, since each instance remembers its frame 0 colour, so the concept buys understanding rather than symbols and stays out of the word table. Note that this period-3 texture is spatial, not temporal, and cannot be read as a clock: it never changes."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, eight times now, twelve cells every time. (38,16)=1 and (39,16)=2 sit on the widget right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since the left neighbour of each is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The rival explanation is that col 16 is where the 6x6 widget ends and the survival is coincidence; eight blanks do not separate them."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots "the divergence report gives the world's t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at those columns read identically -- eighteen cells, six rows apart. Rows 42 to 52 are uniform background, so rows 36-41 is the bottom slot and rows 30-35 the one above it. ACTION1 moved selection from the bottom slot to the upper one and ACTION2 moved it back, one witness each for up and down, no wrap needed. Whether a third slot exists above is untested: (29,13) and (29,14) hold colour 3 and never vary, which is what a slot at rows 24-29 would show on its bottom rail, but board cells prove nothing about slots never selected."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_badge_is_lane_aligned_and_the_matching_reading_stays_downgraded "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45. Those are exactly the rows an upper-slot cavity occupies within its six-row band, so the badge belongs to the lane of the slot at rows 30-35, and the bottom slot's lane has nothing at cols 42-45. The tempting reading is that it is a target the lane texture must be made to match, but the strip is 2 by 6 and the badge is 4 by 4 of one uniform colour, so shape refutes it. The surviving readings are that it marks which slot carries the task, that it is a destination, or that it is a picture of a completed cavity, the widget cavity being also 4x4 with a 2x2 core removed. Seventeen transitions and none bear on any of the three; colour 14 appears nowhere else in the frame. This is the strongest single hint that the ending lives outside the product of states my pressed keys generate."
    [depends: the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending  probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot bar, a port, four strip cells and five meter cells -- four unrelated roles in one type, and the count grows every time the bar converts, which is the clearest sign that the type is an artefact of the arm rather than a thing in the world. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 77 cells that need an owner against 77 pixels written out, with 0 unexplained confirmed every round it has been checked. The cost is measured too: no rule can name the strip, so every blanking rule carves it out of its colour class by neighbour tests, and the march is kept off nine other Studs by a right-neighbour test that is a fact about the bar's geometry rather than about the meter. Those guards are pixel-fitting in a costume, and the march is the worst offender because its guard is an accident of what has already ticked."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, rows 29-54 by cols 10-63. They live in the 3995 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is where a title, target, score or instruction would live, and the likeliest home of whatever finishing means and of whether the bar is a budget or a score. Seventeen commands have not made one cell of it vary, which is mild evidence that it is decoration, but only mild, since fourteen of the seventeen were the same two keys and those keys generate a closed space."
    [depends: the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending  probe: pending]

  theorem two_keys_have_never_been_pressed_and_they_are_the_first_thing_to_press "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not, after eighteen commands and two rounds in which they sat at the top of the order unexecuted. The reason is not impatience. It is closure: the five pressed keys move the world only inside a product of strip state, selector slot and meter length, all eighteen states are in that product, and nothing in that product has ever returned anything but NOT_FINISHED. An unpressed key is the only cheap thing that can leave it. Of order 150 to 180 commands of bar remain so two presses are affordable, and each press reads its own returned frame count, which under reading D is a direct measurement of the counter: a non-strip press separates D from E on the following strip key, and a SINGLE-FRAME press separates D from its twin D-prime. So one press answers a structural question and up to two cadence questions at once. If either key is a click carrying coordinates, this guard language cannot express it and the finding is recorded as prose rather than as a rule."
    [depends: the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "the store did not move, so the engines returned what they returned last round, and I re-read them rather than re-quoting them. mdl_segmenter still reports negative gain on both variants, -2457 bits at 4 tracks and -34069 at 89, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator rather than the world. Its obj1 is 108 cells of shape 2 by 54 present in all eighteen frames: rows 53 and 54 clipped to the window, the meter bar and the fill row beneath it, fused because colour 2 and colour 4 touch vertically and background 5 does not separate them. That corroborates one thing I use, that the bar is one object continuing left of column 10 where I have never seen it. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition, and its verdict that the world does not narrate as one mover agrees with my event vocabulary of recolored alone and is the outside evidence I leaned on when refusing the teleport device. zero_space calls its own evidence THIN in its own words -- 17 transitions constraining rank 7 of 707 features, null space of dimension 700 -- and its single global law spans 101 dynamic cells at once, which is what a 700-dimensional null space produces rather than what a conservation law looks like. Its cell list, ninety-six slot cells plus (53,59) through (53,63), is exactly my dynamic set and is the one thing in the stream I use."
    [probe: pending]

  theorem what_this_draft_pre_registers "certify first, and the numbers are unchanged because nothing that could change them changed: replay 7 of 17, matching at t2, t3, t4, t5, t6, t8 and t17, diverging elsewhere; first divergence transition 0 under ACTION1, 96 cells, first cell (30,11) manual 5 world 6; responsibility 0 unexplained of 4096; unambiguous 0 clashes over 18 states by 3 actions, 54 pairs, 54 nominal, 0 step crashes. If any of those four moves without a command having been pressed, something in the arm has changed under me and that is the first thing to chase. Now the world. Present position: 33 internal frames spent, 16 two-frame commands, 14 work presses, bar converted through (53,59), strip blanked, selector home, and no probe from the last draft executed. Probe one, key(5) then key(6): anything at all is new; read the returned frame count of each; if either returns TWO frames the following strip press separates D from E, and if either returns ONE frame the following strip press separates D from D-prime. Probe two, ACTION1 then ACTION2 then a strip key: D ticks (53,58) on the strip key, E does not; the pair returns the frame to its start and no strip key is pressed while the upper slot is selected. Probe three, repeat ACTION3 from the blanked state: my manual says not one cell changes and every surviving reading says no tick; if the strip returns, hide-and-show is dead. Probe four, three consecutive work presses with nothing between: every surviving reading says the third converts (53,58), which my manual cannot draw and will get wrong -- the pre-registered cost of frontier blindness, stated before it is paid."
    [depends: two_keys_have_never_been_pressed_and_they_are_the_first_thing_to_press  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- fifteenth draft.
#
# WHAT MOVED, AND WHY.
#
# 1. THE ONLY REAL CHANGE IS A PRUNE AGAINST MY OWN LAST ROUND. Zero commands
#    were pressed between the fourteenth draft and this one. The store is
#    byte-identical, certify returned exactly the four numbers I pre-registered,
#    and the manual learned nothing about the world because there was nothing
#    new to learn from. A round that produces a draft and no press is a round
#    spent measuring the manual against a record it has already fitted. That
#    is now a dead plan, written first and pruned explicitly.
#
# 2. THE TOP OF THE ORDER IS UNCHANGED AND IS RESTATED RATHER THAN RE-ARGUED.
#    The five pressed keys move the world only inside a product of three
#    coordinates -- strip shown or blanked, selector slot, meter length. All
#    eighteen states lie in it, the world's own hashes confirm the lattice
#    closes at twelve distinct states, and every one returns NOT_FINISHED. The
#    two never-pressed keys are the only cheap thing that can leave it. They
#    have been rank one for two rounds and have not been pressed.
#
# 3. ONE READING SPLIT INTO TWO AND THE FIRST PROBE GOT MORE VALUABLE, NOT
#    LESS. Reading D ("count two-frame commands") has a twin D-prime ("count
#    every command that is not ACTION7") which this record cannot separate
#    from it. A key(5)/key(6) press separates D from E if it returns two
#    frames and D from D-prime if it returns one. Either way the frame count
#    of that press is information, so read it before anything else.
#
# 4. THE CADENCE IS NOT MERELY UNWRITTEN, IT IS UNWRITEABLE, AND THAT IS NOW
#    A PRUNE. A landmark makes any cell readable, so reading was never the
#    obstacle; the obstacle is that no cell of the frame carries a
#    period-three quantity. All 4096 checked: 3995 constant, 96 period two, 5
#    monotone. Any plan that hopes to find the tick counter in the frame is
#    dead.
#
# 5. STILL NO PLAN HERE, AND STILL NO GOAL. These are orders of interrogation.

order   press_the_two_never_pressed_keys_before_anything_else  [proof: lean]
order   press_at_least_one_command_before_writing_another_draft  [proof: lean]
order   read_the_returned_frame_count_of_every_command_since_two_readings_count_it  [proof: lean]
order   take_the_selector_excursion_as_a_pair_then_one_strip_key_to_split_D_from_E  [proof: lean]
order   repeat_a_blanking_key_in_the_blanked_state_to_kill_hide_or_toggle  [proof: lean]
order   prefer_a_press_that_leaves_the_reachable_product_over_one_that_moves_inside_it  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_since_two_readings_rest_on_it  [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   look_at_the_badge_lane_while_its_own_slot_is_the_selected_one  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule  [proof: lean]
order   make_some_cell_outside_the_observed_window_vary  [proof: lean]
order   vary_the_order_of_the_two_blanking_keys_across_a_restore  [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known  [proof: lean]
order   read_every_bar_cell_after_every_command  [proof: lean]

prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  an_action_that_can_leave_the_closed_product_of_states_already_enumerated  [ev: 12/12 states in the product]
prefer  a_command_pressed_now_over_an_argument_written_now  [ev: 0/1 rounds with a press]
prefer  an_action_the_surviving_counter_readings_give_different_answers_for  [ev: 3 readings, each 5/5 on 5 ticks]
prefer  a_non_strip_press_since_only_that_advances_the_readings_differently  [ev: 14/14 work presses moved both alike]
prefer  a_press_whose_returned_frame_count_would_split_D_from_its_twin  [ev: 1/17 commands returned one frame]
prefer  an_action_that_answers_more_than_one_open_question_at_once  [ev: 1 press separates 3]
prefer  an_action_the_manual_has_pre_registered_a_null_frame_for  [ev: 0/17 transitions tested it]
prefer  a_slot_never_selected_over_one_already_drawn_twice  [ev: 2 slots seen of a column]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats  [ev: 101/4096 cells ever varied]
prefer  a_probe_launched_from_a_state_the_manual_reconstructs_exactly  [ev: 4096/4096 cells right now]
prefer  an_excursion_that_returns_the_frame_to_where_it_started  [ev: 1/17 commands undid another]

heuristic state_classes_outside_the_enumerated_product  [admissible: lean]
heuristic keys_never_pressed  [admissible: lean]
heuristic counter_readings_still_alive  [admissible: lean]
heuristic presses_needed_to_separate_the_surviving_counter_readings  [admissible: lean]
heuristic rounds_since_the_store_last_grew  [admissible: lean]
heuristic bar_cells_still_unconverted  [admissible: lean]
heuristic slots_in_the_column_never_yet_selected  [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed  [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed  [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness  [admissible: lean]

prune   plan_that_produces_a_draft_and_presses_no_command => dead  [proof: lean]
prune   plan_that_expects_certify_to_teach_something_about_the_world => dead  [proof: lean]
prune   plan_that_looks_for_the_tick_counter_inside_the_frame => dead  [proof: lean]
prune   plan_that_treats_the_two_frame_reading_as_a_single_hypothesis => dead  [proof: lean]
prune   plan_that_spends_a_work_press_and_returns_a_state_already_enumerated => dead  [proof: lean]
prune   plan_that_expects_a_run_of_strip_keys_to_separate_the_readings => dead  [proof: lean]
prune   plan_that_treats_the_internal_frame_total_reading_as_still_alive => dead  [proof: lean]
prune   plan_that_counts_the_lone_one_frame_command_toward_the_cadence => dead  [proof: lean]
prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead  [proof: lean]
prune   plan_that_assumes_the_checker_resyncs_the_manual_between_transitions => dead  [proof: lean]
prune   plan_that_assumes_a_rule_replays_the_same_after_the_store_grows => dead  [proof: lean]
prune   plan_that_ties_the_bar_tick_to_one_particular_key => dead  [proof: lean]
prune   plan_that_prices_a_bar_cell_at_one_per_restore_press => dead  [proof: lean]
prune   plan_that_counts_the_bar_on_raw_command_number_alone => dead  [proof: lean]
prune   plan_that_asks_the_manual_to_tick_a_bar_cell_never_yet_witnessed => dead  [proof: lean]
prune   plan_that_needs_a_cell_that_has_never_varied_to_change => dead  [proof: lean]
prune   plan_that_teleports_an_object_out_of_a_cell_the_bar_has_converted => dead  [proof: lean]
prune   plan_that_rests_on_the_bar_meaning_being_known => dead  [proof: lean]
prune   plan_that_spends_the_manuals_present_exactness_and_returns_no_new_frame => dead  [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead  [proof: lean]
prune   plan_that_presses_a_strip_key_while_the_upper_slot_is_selected => dead  [proof: lean]
prune   plan_that_treats_the_two_blanking_keys_as_interchangeable => dead  [proof: lean]
prune   plan_whose_rules_are_longer_than_the_pixels_they_draw => dead  [proof: lean]
prune   plan_that_pins_a_cell_identity_with_one_landmark_per_pixel => dead  [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_spends_a_round_on_a_manual_that_does_not_compile => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead  [proof: lean]
prune   bar_consumed and not goal => dead  [proof: lean]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "colour classes 6/0/3/1/2/4 as Casing/Cavity/Rail/Pip/Stud/Erased, arc-instances all", "verdict": "accept", "as": "unchanged from draft 14", "why": "six declarations own all 77 cells that need an owner and certify returned responsibility 0 unexplained of 4096 again, exactly as pre-registered; the store did not move so no declaration could need to."},
  {"id": "O-02", "subject": "mdl_segmenter obj0 / obj2 / obj3 (440-cell blobs, shape 13x36, colour null)", "verdict": "reject", "why": "connected_components(4) fuses the panel with the arena because both touch through non-background colours; the tracks are a fact about the operator, and the variant reports negative gain (-2457 bits) so the engine refutes itself on constraint 3."},
  {"id": "O-03", "subject": "mdl_segmenter obj1 (108 cells, shape 2x54, present in all 18 frames)", "verdict": "reject", "as": "used as corroboration only", "why": "it is rows 53-54 clipped to the window, the bar fused with the fill row beneath it; I do not declare it, but it independently supports the bar being one object continuing left of column 10 where I have never been shown."},
  {"id": "O-04", "subject": "a background object at arc-colour 5 owning the 24-cell swap footprint", "verdict": "reject", "why": "it would own cols 11,12,15,16 over rows 30-35 exactly, but explains no pixel the board does not already draw correctly and enables no rule I can write -- constraint 3, and the refusal is recorded as a theorem rather than dropped."},
  {"id": "R-01", "subject": "cegis_miner, all four tracks", "verdict": "entailed", "why": "it refuses every track on the precondition of exactly one move event per transition, and its verdict that the world does not narrate as one mover is exactly my event vocabulary of recolored alone; I use it as outside evidence against the teleport device."},
  {"id": "R-02", "subject": "the six strip-toggle rules (key3/key7 blank, key4 restore)", "verdict": "accept", "why": "192 of 192 cell-recolourings correct across fifteen presses, and certify's 54-pair adjudication found no state and action where two of them fire."},
  {"id": "R-03", "subject": "key4_seeds_the_meter_at_the_right_edge", "verdict": "accept", "why": "1/1, the only rule that can name (53,63) and the only way the manual reaches the bar at all."},
  {"id": "R-04", "subject": "key3_marches_the_meter_leftward", "verdict": "accept", "as": "kept with its defect priced", "why": "it accounts for all four conversions but fires four commands early, and certify returned the pre-registered 7/17 with the pre-registered matching set t2,t3,t4,t5,t6,t8,t17 -- dropping it scores 6/17 and leaves the present frame four cells wrong, so I keep the present-state exactness and name the phase error in a theorem."},
  {"id": "R-05", "subject": "any rule set drawing the ACTION1 selector swap", "verdict": "reject", "why": "seventh refusal; local rule sets die on constraint 5 (five cells with an identical guard reading go to three different colours) and coordinate-pinned ones die on constraint 3 (96 landmarks and ~190 rules to draw 96 pixels), and those two grounds now partition the whole space rather than overlapping."},
  {"id": "L-01", "subject": "zero_space global law spanning 101 cells", "verdict": "reject", "why": "the engine calls its own evidence THIN in its own words -- 17 transitions constraining rank 7 of 707 features, null space dimension 700 -- and a law spanning every dynamic cell at once is what such a null space emits, not a conservation law; only its cell list is used, and only because it equals my dynamic set."},
  {"id": "L-02", "subject": "certify_confirmed_every_pre_registered_number", "verdict": "accept", "as": "theorem [probe: passed]", "why": "replay 7/17, first divergence identical cell for cell, responsibility 0/4096, unambiguous 0 clashes over 54 of 54 pairs -- all four written down before measurement, including a deliberate regression from 9/13, so the manual is now a self-model that predicts its own score."},
  {"id": "L-03", "subject": "reading D has a twin D-prime (count every command that is not ACTION7)", "verdict": "probe-pending", "why": "identical to D on all seventeen commands because the ACTION7 at t5 is the only single-frame command; one coincidence carrying two hypotheses is what produced and then killed reading F, so it is recorded now, and a single-frame press of an unpressed key separates them."},
  {"id": "L-04", "subject": "no cell of the frame cycles with period three", "verdict": "accept", "as": "strengthened theorem [probe: passed]", "why": "checked over all 4096 cells: 3995 constant, 96 governed by two involutions (slot, strip) and so period two, 5 monotone; since a landmark makes any cell readable, this converts 'the grammar has no counter' into the stronger checkable claim that the frame carries no counter to read."},
  {"id": "L-05", "subject": "no goal section", "verdict": "accept", "as": "silence recorded in a theorem", "why": "eighteen states, all NOT_FINISHED, and the evidence about the bar has tilted toward budget, under which filling it is the opposite of winning -- so the tempting goal is less signable than a round ago, not more."},
  {"id": "P-01", "subject": "press key(5) then key(6)", "verdict": "probe-pending", "why": "the only cheap action that can leave the closed product of twelve states; it also reads its own frame count, which splits D from E if two frames and D from D-prime if one. Ranked first for a third round and unexecuted for a second."},
  {"id": "P-02", "subject": "ACTION1, ACTION2, then one strip key", "verdict": "probe-pending", "why": "D reaches two-frame ordinal 19 and ticks (53,58); E reaches work ordinal 15 and does not. The pair returns the frame home, so no strip key is pressed while the upper slot is selected, which is the one condition the blank/restore rules require."},
  {"id": "P-03", "subject": "repeat ACTION3 from the blanked state", "verdict": "probe-pending", "why": "the only thing that separates hide-and-show from toggle-and-toggle; my manual commits to a completely null frame, so any movement at all refutes something."},
  {"id": "P-04", "subject": "three consecutive work presses with nothing between", "verdict": "probe-pending", "why": "every surviving reading says the third converts (53,58), which the manual cannot draw because that cell has never varied and has no instance -- the cost is pre-registered before it is paid."},
  {"id": "P-05", "subject": "the four probes pre-registered last round", "verdict": "probe-pending", "why": "none was executed; the store is byte-identical to last round's, so the entire probe queue carries forward unchanged and the playbook now prunes any plan that produces a draft without pressing a command."},
  {"id": "E-01", "subject": "the 96-cell selector swap", "verdict": "reject", "as": "theorem pair, inexpressible then uncompressible", "why": "wanted one rule moving the widget six rows; wrote two theorems instead, because moved is one cell, jumped-over is two, and jumped-to-a-landmark needs a landmark and a rule per instance."},
  {"id": "E-02", "subject": "the tick counter modulo three", "verdict": "reject", "as": "theorem the_cadence_is_inexpressible...", "why": "wanted a latch or counter guard; the grammar has none, and this round I closed the landmark loophole too by checking that no cell of the frame carries a period-three quantity and no cell is free to be used as scratch."},
  {"id": "E-03", "subject": "painting the bar frontier at (53,58)", "verdict": "reject", "as": "theorem the_landmark_and_teleport_device...", "why": "wanted recolored on a landmark; the event table dispatches recolored on an object name only, and teleporting a Stud into (53,58) vacates a cell the world has already converted."},
  {"id": "E-04", "subject": "a click action carrying coordinates, if key(5) or key(6) is one", "verdict": "probe-pending", "as": "prose in two_keys_have_never_been_pressed...", "why": "the guard language cannot express coordinates on an action, so the finding would be recorded as prose rather than as a rule, exactly as the instructions require."}
]
```
```
