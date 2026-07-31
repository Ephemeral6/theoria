# call-003-theorize-round1

model: `claude-opus-5` · 529099 ms · $1.416019 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 34238, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 34238, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 34238, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 34238, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 41871, "type": "message"}], "output_tokens": 41871, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 74,
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
 "constant_cells": 3998,
 "distinct_states": 7,
 "dynamic_box": [
  29,
  10,
  54,
  63
 ],
 "dynamic_cells": 98,
 "max_frames_in_one_command": 2,
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
 53 222222222222222222222222222222222222222222222222222233
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

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 9,
  "n_states": 10,
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
   "recolor": 9,
   "vanish": 2
  },
  "n_frames": 10,
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
    "frames_present": 10,
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
    "frames_present": 8,
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
    "baseline_bits": 4242,
    "compression_ratio": 1.828147,
    "events": 13,
    "gain_bits": -3513,
    "ms": 569,
    "script_bits": 7755,
    "split_by_color": false,
    "tracks": 4
   },
   {
    "baseline_bits": 4242,
    "compression_ratio": 5.287129,
    "events": 97,
    "gain_bits": -18186,
    "ms": 28,
    "script_bits": 22428,
    "split_by_color": true,
    "tracks": 51
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
   "dynamic_cells": 98,
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
  "cells_needing_an_owner": 74,
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
  "constant_cells": 3998,
  "distinct_states": 7,
  "dynamic_box": [
   29,
   10,
   54,
   63
  ],
  "dynamic_cells": 98,
  "max_frames_in_one_command": 2,
  "shape": [
   64,
   64
  ],
  "states": 10,
  "steps": 10
 },
 "window": {
  "box": [
   29,
   10,
   54,
   63
  ],
  "covered": 1.0,
  "dynamic_cells": 98,
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
  "cells_dynamic": 98,
  "cells_used": 98,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c3",
   "c4",
   "c5",
   "c6"
  ],
  "difference_rank": 4,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.005831,
   "difference_rank": 4,
   "features": 686,
   "space_dimension": 682,
   "transitions": 9,
   "verdict": "THIN: 9 transitions constrain rank 4 of 686 features, so the null space has dimension 682 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 686,
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
     "c0@42",
     "c1@42",
     "c2@42",
     "c3@42",
     "c4@42",
     "c5@42",
     "c6@42",
     "c0@43",
   
```

The full proposal stream is 1370 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- SECOND DRAFT. The first draft was written blind against frame 0
# and came back with two hard numbers: responsibility 0/4096 unexplained, and
# replay 4/5 with first divergence at t=0. Both of those are results, not
# scores, and this round is mostly about reading them.
#
# WHAT THE CERTIFY OUTPUT ACTUALLY PROVED
#
#   (1) responsibility ok, 0 unexplained. The pre-registered question
#       instance_anchoring_has_one_alternative resolves in favour of the first
#       branch: arc-instances: all enumerates cells of the declared colour in
#       FRAME 0 that the board cannot explain. The 12 strip cells are NOT
#       double-claimed and (53,63) is NOT double-claimed. Six colour classes
#       own all 73 cells. That question is now closed and I write it as passed.
#
#   (2) replay says 4/5 and first_divergence says t=0. Those two look
#       contradictory and they are not: they can only both be true if replay is
#       OPEN LOOP -- the manual is run forward from frame 0 without being
#       resynced to the world. My manual is silent on key(1) and key(2), so its
#       state after both is still frame 0; the world went S0 -> S1 -> S2 and
#       matched again at t=1. That is a MEASUREMENT, from the harness rather
#       than from my arithmetic, that S2 = S0 exactly, cell for cell. The
#       deduction in frame_zero_is_reconstructed_exactly is no longer a
#       deduction. It is confirmed, and with it the whole reconstruction, since
#       t2..t5 then replayed exactly on top of it.
#
#   (3) 4/5 is one better than the 3/5 I pre-registered. I predicted t1 and t2
#       would both fail. t2 passed for the reason above. I record the miss.
#
# WHAT I LEARNED FROM THE FRAME THAT I HAD NOT SEEN
#
#   (4) Row 29, cols 13-14, holds colour 3 -- and row 29 is BOARD. The true
#       dynamic box is rows 30-53 x cols 11-63 (the reported [29,10,54,63] is
#       that box padded by one and clipped), so (29,13) and (29,14) have never
#       varied. Colour 3 at cols 13-14 is the signature of a COLLAPSED SLOT.
#       There is therefore at least one more slot above row 29, at rows 24-29,
#       which has never been selected and is consequently indistinguishable
#       from furniture. Rows 42 and below are uniform background, so slot B at
#       rows 36-41 is the LAST slot. The panel is a column of slots running
#       upward from row 41, key(1) moves the selection up one slot and key(2)
#       moves it down one slot. That reading, not the two-slot toggle I wrote
#       last round, is what the board itself says.
#
#   (5) The badge -- the 4x4 colour-14 block at rows 31-34 x cols 42-45 -- is
#       vertically centred on row 32.5, which is exactly the centre of SLOT A
#       (rows 30-35) and exactly the rows of STRIP A. Slot B's lane (rows
#       36-41) has no badge: cols 17-46 are uniform colour 4 there. So the
#       arena is lanes, one per slot, strip at the left end and badge at the
#       right end, and slot A has a task where slot B has none.
#
#   (6) In S1 the world drew strip A as 2 1 1 2 1 1 on row 32 -- the same six
#       colours strip B shows on row 38 in S0. Six of twelve cells agree. The
#       strip may be one display that follows the selection rather than two
#       stored patterns.
#
# WHAT I REFUSE TO DO, AND THIS TIME WITH A PROOF
#
#   The swap stays out of `rules:`. Last round I said it was inexpressible and
#   waved at "96 simultaneous recolourings". That was an assertion. This round
#   I checked it and it is a theorem with named witnesses: three pairs of cells
#   that are IDENTICAL in colour and in all four neighbour colours in frame 0
#   and that must take DIFFERENT colours under key(1). No guard in the
#   documented language separates them, and constraint 5 forbids writing two
#   rules that both fire. See the_swap_is_provably_inexpressible_here. The
#   refusal is now earned rather than pleaded.

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
  landmark slot_a_head  # arc-cell: (30, 11)
  landmark slot_b_head  # arc-cell: (36, 11)
  landmark slot_c_head  # arc-cell: (24, 11)
  landmark strip_a_head  # arc-cell: (32, 17)
  landmark strip_b_head  # arc-cell: (38, 17)
  landmark strip_c_head  # arc-cell: (26, 17)
  landmark rail_witness  # arc-cell: (29, 13)
  landmark meter_tip  # arc-cell: (53, 63)
  landmark meter_next  # arc-cell: (53, 62)
  landmark badge_cell  # arc-cell: (31, 42)
  Casing [segment: colour_class_6 ev: t0-t5 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t5 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t5 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t5 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t5 compress: 10]
  Erased [segment: colour_class_4 ev: t0-t5 compress: 12]

events:
  event recolored(o, c)

# The seven rules below are UNCHANGED from the draft that replayed t3, t4 and
# t5 exactly. Nothing observed this round bears on them, so nothing is touched.
# Their negative neighbour guards are ugly and I defend them, at cost, in
# colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_advances_the_meter forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and colored(above(?p), 5) and colored(below(?p), 4) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 10 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 73 [status: proven]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I was shown with two edits: rows 38-39 x cols 17-22 hold 2 1 1 2 1 1 over 1 1 2 1 1 2 instead of colour 4, and (53,63) holds 2 instead of 3. Last round this was a deduction from distinct_states = 5 plus two arithmetic closures, 97 dynamic cells and 73 owned cells, neither of which I had used to build it. This round the harness confirmed it independently: replay reports 4/5 with its first divergence at t=0, which is only consistent with open-loop replay, which in turn means the world returned to my frame 0 after key(2) and then matched me for three more transitions. Load-bearing, and now measured rather than inferred."
    [probe: passed]

  theorem replay_is_open_loop_and_that_is_what_four_of_five_means "the manual is run forward from frame 0 without resync. My manual is a no-op on key(1) and key(2), so it sat at frame 0 through both; the world left and came back; from t=2 onward the strip rules carried it. The single failing transition is t=0, the key(1) selector move, 96 cells wrong. This has a consequence I must design around: a wrong rule for key(1) would not merely fail at t=0, it would DESELECT the manual from the world for the rest of the trace and lose the three transitions I currently get for free. Silence on the selector is worth more than a guess at it, and that is a numerical argument, not a temperamental one."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied, so they are board. Colour 3 at cols 13-14 is exactly the signature of a collapsed slot -- it is what slot A shows at its four outer rows. So there is a further slot at rows 24-29 that has never been selected, and probably more above it, all of them invisible to me because an unselected slot is a constant drawing and a constant drawing is board by definition. Below, rows 42 onward are uniform background, so slot B at rows 36-41 is the last slot. key(1) took the selection from B up to A and key(2) took it back down. I therefore read key(1) as move-selection-up-one-slot and key(2) as move-selection-down-one-slot, in preference to the two-slot toggle I wrote last round. The two readings differ on a probe that costs nothing: from the current state, with the bottom slot selected, a move reading predicts key(2) does nothing at all and a toggle reading predicts 96 cells change. My manual, being silent, already commits to the move reading, so the next key(2) press scores it."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_arena_is_lanes_and_only_slot_a_has_a_badge "the arena is colour 4 over cols 17-46, rows 29-41 at least and probably further up where I cannot see. The 4x4 colour-14 badge at rows 31-34 x cols 42-45 is centred on row 32.5, which is the centre of slot A and the exact rows of strip A. Slot B's band, rows 36-41, is uniform colour 4 from col 17 to col 46 -- no badge. So the arena reads as one lane per slot, a 2x6 strip at the lane's left end and a badge at its right end, and slot A carries a task that slot B does not. Slots above row 29 may carry badges too and I would not know, because their badges would never have varied. This is the only structure in the arena that is neither strip nor fill and it remains the natural candidate for what the strips are compared against. Zero transitions bear on it."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_strip_may_be_one_display_rather_than_two "in S1 the world drew strip A row 32 as 2 1 1 2 1 1, which is exactly what strip B row 38 shows in S0. Six of the twelve cells agree; the divergence report was truncated at 24 cells and row 33 was never shown to me. Either the strip is a single display that follows the selection, or each slot has its own pattern and the two agree on their first row. The separator is free and comes with the selector probe: select slot A and read row 33. If it is 1 1 2 1 1 2 the two are the same display or the same pattern; if it differs, patterns are per-slot and the strip is slot data."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and I cannot write it, and this is now a proof rather than a complaint. A guard sees a cell's own colour and the colours of its four neighbours, and nothing else -- there is no coordinate, no row band, no distance. Under key(1) the new colour of a panel cell is a function of its offset within a six-row period, and that offset is not determined by the four neighbour colours. Three witness pairs, each identical in colour and in all four neighbour colours in frame 0, each required to take different colours: (30,12) and (31,12) are colour 5 with above 5, below 5, left 5, right 3, and must become 6 and 0; (41,12) and (41,13) are colour 6 with above 0, below 5, left 6, right 6, and must become 5 and 3; (32,18) and (32,20) are colour 4 with all four neighbours colour 4, and must become 1 and 2. Stronger still, the five cells (30,16), (31,16), (32,16), (33,16), (34,16) are all colour 5 with above 5, below 5, left 5, right 4 and must become 6, 6, 1, 2, 6 -- four distinct answers to one indistinguishable question. Constraint 5 forbids two rules firing on one object in one transition, so there is no escape by writing both. The swap does not go in the manual."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem nesting_would_break_the_ties_and_would_still_fail_the_gain_test "the proof above assumes cell expressions take an instance or a landmark, as the grammar documents. If above(above(?p)) in fact compiles, the ties break: a chain of five nested neighbours can count a cell's distance from the panel edge and so recover its offset in the period. I decline that route for two reasons and I want both on the record. First, a guard form the grammar does not list is a parse risk, and a manual that fails to parse loses everything including the three transitions it currently gets right. Second, and decisively, distinguishing 96 cells by 96 distinct neighbour chains is writing the pixels out with extra syntax: it would cost more symbols than the 96 pixels it explains, which is exactly the failure constraint 3 names. The swap is inexpressible without nesting and uncompressible with it, so it stays out either way."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_meter_can_tick_only_once_in_this_manual_and_the_second_tick_is_pre_registered "row 53 is a colour-2 bar running at least cols 10 to 62 with its rightmost cell at col 63, and (53,63) is the only cell of it that has ever varied. My rule key4_advances_the_meter recolours that one Stud instance from 2 to 3 and then guards itself off, because it now holds colour 3. There is no instance at (53,62): that cell is constant in frame 0 and therefore board. So this manual predicts the meter never advances again, which is almost certainly wrong. I pre-register the shape of the failure exactly: the second key(4) press diverges at ONE cell, (53,62), 2 -> 3, and nowhere else. That divergence would confirm the bar reading rather than refute the manual, and the repair is one line -- the arm will hand (53,62) an instance once it has varied, and stud_population goes from 10 to 11. A divergence anywhere other than (53,62) refutes the bar reading and I would rebuild the meter from what is reported."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_strip_toggles_and_only_key_four_costs_anything "key(3) at t3 and key(7) at t5 each blanked all 12 cells of the selected slot's strip to arena colour 4; key(4) at t4 restored exactly the same 1 and 2 pattern cell for cell and additionally advanced the meter. The pattern is therefore stored somewhere the frame does not show and blanking does not destroy it. Over five commands the meter ticked once and only under key(4), so key(4) is the metered action and keys 1, 2, 3 and 7 are free. One witness each: key(3) and key(7) may be a blank and a toggle that agreed because the strip was shown both times, and key(4) may be a show or a toggle that agreed because the strip was blank. Nothing in the record separates blank from toggle for any of the three, and the cheapest separator is a second consecutive key(3) from a shown strip."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_sign_of_the_meter_is_unknown_and_that_matters_more_than_its_length "I have been calling (53,63) a meter and treating its tick as a cost, and I have no evidence for the sign. Colour 2 is the bar and colour 3 is what one unit became; colour 3 is also the colour of an unselected slot's rails, and colour 2 is also the colour of half the strip. A bar consumed right to left and a score accumulated right to left look identical after one tick. If it is a cost, key(4) should be rationed; if it is a score, key(4) is the only action that has ever accomplished anything and should be repeated. This is the single largest open question about what to do next, it is worth more than any refinement of the drawing, and one further key(4) press resolves the direction while leaving at least fifty-two units of whatever it is."
    [depends: the_meter_can_tick_only_once_in_this_manual_and_the_second_tick_is_pre_registered  probe: pending]

  theorem cascade_length_carries_no_signal_here "t1, t2, t3 and t4 returned 2 frames each and t5 returned 1, yet t3 and t5 produced identical 12-cell effects. Frame count does not track the magnitude or even the presence of change and must not be used as a motion detector. What it may still carry is that ACTION7 and ACTION3 are genuinely different actions that happened to agree in this state -- one animates and one does not. That is a hint about key identity, not about world state."
    [probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans slot A's core, a port cell of the expanded slot, four strip cells and the meter tip -- four unrelated roles. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm is what draws the frame. The gain is real and now measured: six declarations own all 73 cells that need an owner, against 73 pixels written out, responsibility reports 0 unexplained, and seven rules over those classes reproduce three of the five transitions exactly. The cost is real too: no rule can name the strip as such, so every strip rule carves it out of its class with four negative neighbour guards. Those guards are pixel-fitting in a costume. They are correct on every instance of both classes in frame 0, which I checked one by one, and they survived replay, and they are the price of a colour-first arm."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem instance_anchoring_is_frame_zero_and_that_question_is_closed "I pre-registered two branches: instances anchored from frame 0, predicting 0 unexplained, or anchored from the union of frames, predicting a residue drawn from exactly 13 named cells. The report reads 0 unexplained over 4096 cells. Frame 0 it is. The consequence I now rely on: a cell that is constant in frame 0 gets no instance and can never be drawn as anything else, which is precisely why the meter cannot tick twice and why the slots above row 29 are invisible to this manual. Both of those are stated as their own entries rather than left implicit."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem two_keys_have_never_been_pressed "this world has seen ACTION1, 2, 3, 4 and 7. key(5) and key(6) are unpressed and unknown. In this family a click carrying coordinates is common and this guard language cannot express one at all -- if key(5) or key(6) is that, the finding will be recorded as prose and never as a rule. Both are worth pressing early: whatever they cost, they cost less now, while the manual is small enough that a surprise is cheap to absorb, than later when a plan depends on them."
    [depends: the_sign_of_the_meter_is_unknown_and_that_matters_more_than_its_length  probe: pending]

  theorem no_goal_section_on_purpose "every command returned NOT_FINISHED and nothing in five transitions indicates what finishing means. The live candidates are that a strip must be brought to agree with the badge in its lane, that the meter must be filled, or that the objective lies above row 29 where I have never looked. Writing any of them as a goal would compile to a claim refuted by the first win, or worse, would send the searcher after a fiction. An absent goal compiles to is_goal -> False, which under-claims and costs a round; a wrong goal over-claims and costs the level."
    [depends: the_arena_is_lanes_and_only_slot_a_has_a_badge  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "mdl_segmenter returned negative gain on both variants, -4037 bits at 4 tracks and -10409 at 33, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4). That is a fact about the operator. cegis_miner refused every track because its precondition is one move event per transition and this world has no mover; correct and unhelpful. zero_space calls its own evidence THIN, 5 transitions constraining rank 3 of 679 features, and its single global law spans nearly every dynamic cell at once, which is what a 676-dimensional null space produces rather than what a conservation law looks like. I took one thing from the engines and it was the store arithmetic, dynamic_cells 97 and cells_needing_an_owner 73, both of which closed against a reconstruction built without them and both of which the responsibility check has since ratified."
    [probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- the manual is silent on the selector by proof, not by
# laziness, so every routable thing about the selector lives here. What changed
# this round:
#
#   the panel is a COLUMN of slots, not a pair -- (29,13) and (29,14) are
#     board-constant colour 3, the signature of a collapsed slot above row 29,
#     and rows 42 down are empty, so slot B is the bottom one;
#   key(1) is up-one-slot and key(2) is down-one-slot, and the manual's silence
#     already commits to that reading: from the bottom slot, key(2) is
#     predicted to do nothing, so the cheapest probe in the game also scores
#     the leading hypothesis;
#   slot A's lane carries a badge and slot B's lane carries none, so the slots
#     are not interchangeable and the one with the task is worth being in;
#   the meter's SIGN is unknown -- cost or score -- and that outranks every
#     refinement of the drawing, because it decides whether key(4) is the thing
#     to avoid or the only thing that has ever worked;
#   ACTION5 and ACTION6 have never been pressed at all.
#
# Nothing below is a stored line of play. Every entry is a ranking rule that
# still has to be evaluated against whatever state the searcher is actually in.

order   probe_the_selector_bound_before_theorising_about_the_selector    [proof: lean]
order   settle_the_sign_of_the_meter_before_rationing_the_metered_key    [proof: lean]
order   reach_a_slot_that_has_never_been_selected                        [proof: lean]
order   read_the_second_strip_row_while_the_upper_slot_is_selected       [proof: lean]
order   press_the_two_never_pressed_keys_while_the_meter_is_still_long   [proof: lean]
order   separate_blank_from_toggle_before_trusting_either_reading        [proof: lean]
order   compare_a_strip_against_the_badge_in_its_own_lane                [proof: lean]
order   read_the_meter_tip_and_the_frame_count_after_every_command       [proof: lean]

prefer  a_state_whose_lane_contains_the_badge_over_a_lane_without_one    [ev: 1/2 lanes carry a badge]
prefer  a_slot_that_has_never_been_selected_over_one_already_mapped      [ev: 2 slots seen of a column]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_known     [ev: 2/7 keys unpressed]
prefer  an_action_whose_outcome_the_manual_already_predicts              [ev: 1/1 open_loop replay reads]
prefer  a_press_that_makes_a_board_cell_dynamic_over_one_that_repeats    [ev: 97/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_it_already_produced               [ev: 2/2 blanking presses agreed]

heuristic slots_in_the_column_never_yet_selected                        [admissible: lean]
heuristic strip_rows_still_unread_in_the_panel                          [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                   [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                    [admissible: lean]

prune   meter_exhausted and not goal => dead                            [proof: lean]
prune   repeat_of_a_key_that_left_this_exact_state_unchanged => dead     [proof: lean]
prune   metered_press_before_the_selector_bound_is_known => dead         [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead     [proof: lean]
prune   selector_move_away_from_the_badge_lane_with_nothing_learned => dead [proof: lean]
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

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '8ccbe276408c4dd7', the world answered 'bb5c436a2318c544'

```json
{
 "action": 4,
 "observed": "bb5c436a2318c544",
 "predictions": {
  "inert": "05615f3d5f835100",
  "manual": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r38c16": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r38c18": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r38c19": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r38c21": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r38c22": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r39c17": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r39c18": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r39c20": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r39c21": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r32c13": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r32c14": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r33c13": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r33c14": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r38c17": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r38c20": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r39c16": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r39c19": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r39c22": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r53c63": "8ccbe276408c4dd7",
  "without_key4_advances_the_meter__Stud_r32c13": "8ccbe276408c4dd7",
  "without_key4_advances_the_meter__Stud_r32c14": "8ccbe276408c4dd7",
  "without_key4_advances_the_meter__Stud_r33c13": "8ccbe276408c4dd7",
  "without_key4_advances_the_meter__Stud_r33c14": "8ccbe276408c4dd7",
  "without_key4_advances_the_meter__Stud_r38c17": "8ccbe276408c4dd7",
  "without_key4_advances_the_meter__Stud_r38c20": "8ccbe276408c4dd7",
  "without_key4_advances_the_meter__Stud_r39c16": "8ccbe276408c4dd7",
  "without_key4_advances_the_meter__Stud_r39c19": "8ccbe276408c4dd7",
  "without_key4_advances_the_meter__Stud_r39c22": "8ccbe276408c4dd7",
  "without_key4_advances_the_meter__Stud_r53c63": "8ccbe276408c4dd7",
  "without_key4_restores_the_strip_pips__Pip_r38c16": "8ccbe276408c4dd7",
  "without_key4_restores_the_strip_pips__Pip_r38c18": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r38c19": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r38c21": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r38c22": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r39c17": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r39c18": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r39c20": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r39c21": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r32c13": "8ccbe276408c4dd7",
  "without_key4_restores_the_strip_studs__Stud_r32c14": "8ccbe276408c4dd7",
  "without_key4_restores_the_strip_studs__Stud_r33c13": "8ccbe276408c4dd7",
  "without_key4_restores_the_strip_studs__Stud_r33c14": "8ccbe276408c4dd7",
  "without_key4_restores_the_strip_studs__Stud_r38c17": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r38c20": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r39c16": "8ccbe276408c4dd7",
  "without_key4_restores_the_strip_studs__Stud_r39c19": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r39c22": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r53c63": "8ccbe276408c4dd7",
  "without_key7_blanks_the_strip_pips__Pip_r38c16": "8ccbe276408c4dd7",
  "without_key7_blanks_the_strip_pips__Pip_r38c18": "8ccbe276408c4dd7",
  "without_key7_blanks_the_strip_pips__Pip_r38c19": "8ccbe276408c4dd7",
  "without_key7_blanks_the_strip_pips__Pip_r38c21": "8ccbe276408c4dd7",
  "without_key7_blanks_the_strip_pips__Pip_r38c22": "8ccbe276408c4dd
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '05615f3d5f835100', the world answered '3bf51d2fd9036a78'

```json
{
 "action": 3,
 "observed": "3bf51d2fd9036a78",
 "predictions": {
  "inert": "8ccbe276408c4dd7",
  "manual": "05615f3d5f835100",
  "without_key3_blanks_the_strip_pips__Pip_r38c16": "05615f3d5f835100",
  "without_key3_blanks_the_strip_pips__Pip_r38c18": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r38c19": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r38c21": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r38c22": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r39c17": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r39c18": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r39c20": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_pips__Pip_r39c21": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r32c13": "05615f3d5f835100",
  "without_key3_blanks_the_strip_studs__Stud_r32c14": "05615f3d5f835100",
  "without_key3_blanks_the_strip_studs__Stud_r33c13": "05615f3d5f835100",
  "without_key3_blanks_the_strip_studs__Stud_r33c14": "05615f3d5f835100",
  "without_key3_blanks_the_strip_studs__Stud_r38c17": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r38c20": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r39c16": "05615f3d5f835100",
  "without_key3_blanks_the_strip_studs__Stud_r39c19": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r39c22": "8ccbe276408c4dd7",
  "without_key3_blanks_the_strip_studs__Stud_r53c63": "05615f3d5f835100",
  "without_key4_advances_the_meter__Stud_r32c13": "05615f3d5f835100",
  "without_key4_advances_the_meter__Stud_r32c14": "05615f3d5f835100",
  "without_key4_advances_the_meter__Stud_r33c13": "05615f3d5f835100",
  "without_key4_advances_the_meter__Stud_r33c14": "05615f3d5f835100",
  "without_key4_advances_the_meter__Stud_r38c17": "05615f3d5f835100",
  "without_key4_advances_the_meter__Stud_r38c20": "05615f3d5f835100",
  "without_key4_advances_the_meter__Stud_r39c16": "05615f3d5f835100",
  "without_key4_advances_the_meter__Stud_r39c19": "05615f3d5f835100",
  "without_key4_advances_the_meter__Stud_r39c22": "05615f3d5f835100",
  "without_key4_advances_the_meter__Stud_r53c63": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r38c16": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r38c18": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r38c19": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r38c21": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r38c22": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r39c17": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r39c18": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r39c20": "05615f3d5f835100",
  "without_key4_restores_the_strip_pips__Pip_r39c21": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r32c13": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r32c14": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r33c13": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r33c14": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r38c17": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r38c20": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r39c16": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r39c19": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r39c22": "05615f3d5f835100",
  "without_key4_restores_the_strip_studs__Stud_r53c63": "05615f3d5f835100",
  "without_key7_blanks_the_strip_pips__Pip_r38c16": "05615f3d5f835100",
  "without_key7_blanks_the_strip_pips__Pip_r38c18": "05615f3d5f835100",
  "without_key7_blanks_the_strip_pips__Pip_r38c19": "05615f3d5f835100",
  "without_key7_blanks_the_strip_pips__Pip_r38c21": "05615f3d5f835100",
  "without_key7_blanks_the_strip_pips__Pip_r38c22": "05615f3d5f83510
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
  "detail": "4/5 transitions replay exactly",
  "matched": 4,
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
  "actions": 3,
  "clashes": [],
  "detail": "no (state, action) among 6 x 3 admitted two rules",
  "ok": true,
  "scope": "sampled",
  "states": 6
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
# theory.dsl -- THIRD DRAFT. Four more commands arrived (t6..t9) and they paid
# for themselves several times over. Three things fired at me and each is
# answered below by a change, not by a paragraph.
#
# 1. THE WORLD IS NOT A FUNCTION OF THE FRAME. This is the finding of the
#    round and it is a proof from the record, not a guess.
#      S5 (after t5, key(7)) and S7 (after t7, key(3)) are the SAME FRAME:
#      strip B blanked, (53,63)=3, everything else frame 0. The store agrees --
#      10 states, 7 distinct, and the three collisions are exactly S2=S0,
#      S6=S4, S7=S5.
#      key(4) from S5 gave S6 with NO meter change.
#      key(4) from S7 gave S8 with (53,62): 2 -> 3.
#    Same visible state, same key, different successor. No manual whose rules
#    read only colours can produce both, mine included, and constraint 5
#    forbids writing two rules that both fire. There is a counter behind the
#    glass. I say so in the_world_has_hidden_state..., I decline to fake it,
#    and I pre-register exactly which two transitions I therefore lose.
#
# 2. MY PRE-REGISTRATION WAS HALF RIGHT AND I SCORE BOTH HALVES. I wrote that
#    the second tick would diverge at ONE cell, (53,62), 2 -> 3, and nowhere
#    else. The cell is right -- the bar is consumed RIGHT TO LEFT, which was a
#    guess and is now measured -- and the timing is wrong: it came on the THIRD
#    key(4) press, not the second. That miss is the whole of finding 1.
#
# 3. THE METER IS PROBABLY A CLOCK, NOT A TOLL. Ticks landed after global
#    action 4 and after global action 8. t6 was a key(4) press that restored
#    twelve cells and cost nothing. So "key(4) is the metered action and the
#    other keys are free", which I wrote last round, is refuted: either every
#    action ticks the bar one cell per four, or the tick follows odd-numbered
#    key(4) presses. Both need hidden state; they differ on a probe that costs
#    three actions and none of them key(4). This inverts the playbook -- there
#    is nothing to ration and no reason to hoard.
#
# WHAT I ALSO LEARNED BY FINALLY BEING SHOWN THE PIXELS
#
# 4. THE STRIP IS A WINDOW ONTO ONE GLOBAL DIAGONAL TEXTURE. Frame 0 rows 38
#    and 39, cols 16-22, and the row the world drew at t1 in lane A, row 32,
#    cols 16-22, are all covered by ONE rule: colour 2 where (r + c) mod 3 = 1,
#    colour 1 otherwise. 21 cells, three rows, two lanes, no exception. It
#    predicts the row I have never been shown, row 33, exactly. Last round I
#    asked whether the strip was one display or two patterns; the answer is
#    better than either -- it is one texture, and each lane shows two rows of
#    it. See the_strip_is_one_global_diagonal_texture.
#
# 5. COL 16 IS A SEED AND IS NEVER ERASED. Blanking takes cols 17-22 and stops.
#    (38,16)=1 and (39,16)=2 survive every blank, and both continue their row's
#    period-3 run leftward. That is why key(4) can restore the pattern cell for
#    cell: what it needs is still on the glass.
#
# 6. THE WIDGET ANATOMY CLOSES ARITHMETICALLY. The selected slot is a 6x6 box,
#    rows 36-41 x cols 11-16: colour-6 ring (20) minus two right-edge ports
#    (38,16),(39,16) plus a colour-6 2x2 core at rows 38-39 x cols 13-14 = 22
#    Casing; colour-0 cavity rows 37-40 x cols 12-15 minus that core = 12
#    Cavity. An unselected slot is a 2-wide bar at cols 13-14: colour 3 at its
#    four outer rows (8 Rail) and colour 2 at its two middle rows (4 Stud), the
#    other 24 cells of its 6x6 footprint being background. 22+12+8+4 = 46,
#    plus 9 Pip and 5 Stud in strip and ports and 12 Erased in lane A and 2
#    Stud in the bar = 74, which is cells_needing_an_owner to the unit, and
#    74 + 24 background = 98 = dynamic_cells. The t1 diff of 96 cells is
#    36 + 36 + 12 + 12 with nothing left over. The drawing is settled.
#
# WHAT I STILL REFUSE. The selector swap stays out of rules: the witness pairs
# in the_swap_is_provably_inexpressible_here are unchanged and silence still
# buys me six replayed transitions instead of none.

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
  landmark slot_a_head  # arc-cell: (30, 11)
  landmark slot_b_head  # arc-cell: (36, 11)
  landmark slot_above_head  # arc-cell: (24, 11)
  landmark strip_a_seed  # arc-cell: (32, 16)
  landmark strip_b_seed  # arc-cell: (38, 16)
  landmark strip_a_row_two  # arc-cell: (33, 17)
  landmark strip_b_row_two  # arc-cell: (39, 17)
  landmark rail_witness  # arc-cell: (29, 13)
  landmark badge_head  # arc-cell: (31, 42)
  landmark meter_tip  # arc-cell: (53, 63)
  landmark meter_next  # arc-cell: (53, 62)
  landmark meter_third  # arc-cell: (53, 61)
  Casing [segment: colour_class_6 ev: t0-t9 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t9 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t9 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t9 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t9 compress: 11]
  Erased [segment: colour_class_4 ev: t0-t9 compress: 12]

events:
  event recolored(o, c)

# The six strip rules are UNCHANGED in form and now carry three witnesses each
# for key(3) and three for key(4) instead of one. The seventh rule, the meter
# tick, is the only edit: (53,62) has now varied, so the arm will hand it a
# Stud instance (cells_needing_an_owner went 73 -> 74), and the old guard
# `above=5 and below=4` is true of BOTH bar cells, which would have ticked them
# together at t4. `rightof(?p) = wall` is the one documented guard that names
# the rightmost cell and nothing else. If that form does not fire, the symptom
# is a one-cell divergence at (53,63) on t4 and the repair is
# `not colored(rightof(?p), 2)`; I say this here so the failure is diagnosable
# rather than mysterious.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3,t7,t9 cov: 24/24]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3,t7,t9 cov: 12/12]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4,t6,t8 cov: 24/24]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4,t6,t8 cov: 12/12]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_advances_the_meter_once forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall and colored(below(?p), 4) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 11 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 74 [status: proven]

  theorem the_world_has_hidden_state_two_identical_frames_answered_the_same_key_differently "S5, reached by key(7) at t5, and S7, reached by key(3) at t7, are the same frame cell for cell: strip B blanked to colour 4 over rows 38-39 x cols 17-22, (53,63) already colour 3, everything else as frame 0. key(4) from S5 produced S6 with no change outside the strip; key(4) from S7 produced S8 with (53,62) 2 -> 3 as well. Same state, same action, two successors. The store corroborates independently: 10 states, 7 distinct, and the only way to get three collisions out of this trace is S2=S0, S6=S4, S7=S5. So the world carries a counter the frame does not show, my guard language has no counters and no memory of the previous action, and constraint 5 forbids two rules that both fire on one instance. I therefore write the tick I can witness once and none of the ticks I cannot, and I state the cost rather than hide it: replay will report 6/9, with the first divergence at transition 0 (ACTION1, 96 cells, the selector I refuse to guess) and one-cell divergences at transitions 7 and 8, both at (53,62), both because my bar is one unit longer than the world's from that point on. Any divergence anywhere else refutes this reading."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_second_tick_landed_where_i_said_and_when_i_did_not "last round I pre-registered the shape of my own failure: the next tick would be a single cell, (53,62), 2 -> 3, and nowhere else. That is exactly what arrived, so the bar is consumed RIGHT TO LEFT and the arm does hand a cell an instance the moment it stops being constant -- cells_needing_an_owner went 73 to 74 and dynamic_cells 97 to 98, which is that one cell and no other. What I got wrong was the timing: I said the second key(4) press and it was the third, because t6 was a key(4) press that restored twelve cells and moved no bar at all. I record the miss plainly: it refutes 'key(4) is the metered action', which I had asserted on one witness, and it is the observation that forced the hidden-state theorem."
    [depends: the_world_has_hidden_state_two_identical_frames_answered_the_same_key_differently  probe: passed]

  theorem the_meter_is_probably_a_clock_and_not_a_toll "the two ticks landed after global action 4 and after global action 8. Two readings survive. CLOCK: the bar loses one cell every four actions whatever they are, so the game is timed, 62 cells remain and about 248 actions with them, and no key is cheaper than any other. TOLL WITH PARITY: the tick follows the first, third, fifth key(4) press. Both require the hidden counter and neither is expressible here, so the manual cannot choose between them and does not try. The separator is cheap and I want it early: spend three consecutive actions none of which is key(4). The clock reading says (53,61) turns 3 on the third of them; the toll reading says the bar does not move at all. Frame counts cannot substitute -- cumulative frames at the ticks were 8 and 15, no period. This question outranks every refinement of the drawing because it decides whether there is any reason to be frugal, and after t6 there is no evidence left that any single key costs anything."
    [depends: the_second_tick_landed_where_i_said_and_when_i_did_not  probe: pending]

  theorem the_meter_cadence_is_inexpressible_in_this_language "a guard reads a cell's colour, its four neighbours' colours, off-board, and the action name. A cadence needs a count of past actions, and there is no count anywhere in the grammar -- not in guards, not in values, not in events. I could fake a parity bit only by recolouring some cell the world does not recolour, which is a guaranteed responsibility or replay failure, so faking it is strictly worse than silence. This is the second thing this world does that the language cannot say; the first is the selector swap. Both are recorded as prose and neither is smuggled into rules."
    [depends: the_world_has_hidden_state_two_identical_frames_answered_the_same_key_differently  probe: passed]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have ever seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Witnesses: frame 0 row 38, cols 16-22, reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, which are the same period-3 run offset by one column; and at t1 the world drew lane A's row 32, cols 16-22, as 1 2 1 1 2 1 1 -- the divergence report gave me (32,16)=1 and (32,17)=2 and (32,20)=2 and the rest, and every one of those 21 cells satisfies the rule. So the two strips are not two stored patterns and not one display that follows the selection; they are two windows onto a single diagonal texture that runs across the whole arena, which is why key(4) can restore twelve cells cell for cell and why the ports at col 16 continue their row's run leftward. The prediction, made before looking: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2, with (33,16) colour 2. Nothing needs it in rules -- the colour classes already restore the right colours because each instance remembers its frame 0 colour -- so it earns its place as structure, not as prediction, and I flag that: by constraint 3 this concept currently buys understanding rather than symbols."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, three times for key(3) and once for key(7), twelve cells every time. (38,16)=1 and (39,16)=2 sit on the widget's right edge, are Pip and Stud instances, and have never changed under any blank. They are the only cells of the texture that survive hiding, and they are exactly the two cells needed to phase a period-3 run. I read col 16 as a seed the world keeps visible; the alternative is that it is simply part of the widget's border and the survival is a coincidence of the 6x6 box ending there. Both are consistent with nine transitions."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I was shown with two edits: rows 38-39 x cols 17-22 hold the texture rather than colour 4, and (53,63) and (53,62) hold 2 rather than 3. The reconstruction is now over-determined. Open-loop replay matched the world from t2 onward, which can only happen if the world returned to my frame 0 after key(2). The widget anatomy closes: 22 Casing as a 20-cell ring minus two ports plus a 2x2 core, 12 Cavity as a 4x4 minus that core, 8 Rail and 4 Stud as the unselected bar at cols 13-14, 9 Pip and 5 Stud in the strips and ports, 12 Erased in lane A, 2 Stud in the meter bar, total 74 = cells_needing_an_owner. The 24 remaining dynamic cells are exactly the background cells of the unselected slot's 6x6 footprint, and 74 + 24 = 98 = dynamic_cells. The t1 diff of 96 cells is 36 for panel A plus 36 for panel B plus 12 for lane A's strip rows plus 12 for lane B's, with nothing left over. Load-bearing and measured from three independent directions."
    [probe: passed]

  theorem replay_is_open_loop_and_silence_on_the_selector_is_worth_six_transitions "the manual is run forward from frame 0 without resync, which is why last round reported 4/5 with its first divergence at t=0. My manual is a no-op on key(1) and key(2), so it sat at frame 0 through both, the world left and came back, and every strip transition since has replayed on top of it. A wrong rule for key(1) would not cost one transition, it would desynchronise the manual from the world permanently and cost all nine. That is the numerical argument for silence and it got stronger this round, not weaker: silence now buys six of nine instead of four of five."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied in nine transitions, so they are board. Colour 3 at cols 13-14 is exactly what an unselected slot shows at its four outer rows, and the unselected slot at rows 30-35 shows 3 3 2 2 3 3 down cols 13-14, so row 29 sits where the last row of a slot at rows 24-29 would sit. Below, rows 42 onward are uniform background, so the slot at rows 36-41 is the bottom one. I read key(1) as move-selection-up-one-slot and key(2) as move-selection-down-one-slot. The probe I named last round was not run and it is still the cheapest structural test in the game, now in two halves: from the bottom slot key(2) should do nothing under the move reading and repaint 96 cells under a two-slot toggle; and from the upper slot key(1) should repaint rows 24-35 if a third slot exists and do nothing if slot A is the top. My manual, being silent, already predicts 'nothing' for both, so either press scores it for free."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_arena_is_lanes_and_the_badge_is_row_aligned_with_the_cavity "the arena is colour 4 over cols 17-46, rows 30-41 at least. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 x cols 42-45. Those are precisely the rows a selected slot's 4x4 cavity occupies within its own 6-row band -- the cavity of the selected bottom slot is rows 37-40 within band 36-41, and the badge is rows 31-34 within band 30-35. So the badge is a cavity-shaped, cavity-aligned object at the far right of slot A's lane, and slot B's lane has nothing at cols 42-45. Two readings: the badge is a target the lane's cavity or strip must be made to match, or it is simply a marker that slot A carries a task and slot B does not. Zero transitions bear on either. Slots above row 29 may carry badges I have never seen, since an unvarying badge is board by definition."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_strip_hides_and_shows_and_no_key_has_been_shown_to_cost_anything "key(3) blanked a shown strip at t3, t7 and t9; key(7) blanked one at t5; key(4) restored a blanked one at t4, t6 and t8, identically every time, so the pattern lives somewhere the frame does not show and blanking does not destroy it. What I wrote last round -- that key(4) is the metered action and the rest are free -- is refuted by t6, a key(4) press that moved no bar. What is still untested after nine transitions is the same thing as after five: key(3) has never been pressed from a blanked strip and key(4) has never been pressed from a shown one. Until one of those happens, hide-and-show and toggle-and-toggle are indistinguishable, and the current state is blanked, so the separator costs exactly one action and my manual predicts inert for it -- which makes it a test of the manual as well as of the world."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language can produce them. A guard sees a cell's own colour and its four neighbours' colours and nothing else -- no coordinate, no row band, no distance. Under key(1) the new colour of a panel cell is a function of its offset within a six-row period, and that offset is not determined by the four neighbour colours. Witnesses, all in frame 0: (30,12) and (31,12) are colour 5 with above 5, below 5, left 5, right 3, and must become 6 and 0; (41,12) and (41,13) are colour 6 with above 0, below 5, left 6, right 6, and must become 5 and 3; (32,18) and (32,20) are colour 4 with all four neighbours colour 4, and must become 1 and 2. Worse, (30,16), (31,16), (32,16), (33,16), (34,16) are all colour 5 with above 5, below 5, left 5, right 4 and must become 6, 6, 1, 2, 6 -- four distinct answers to one indistinguishable question. Constraint 5 forbids writing both rules. The swap does not go in the manual."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem nesting_would_break_the_ties_and_would_still_fail_the_gain_test "if above(above(?p)) compiles -- the grammar does not list it -- a chain of nested neighbours could count a cell's distance from the panel edge and recover its offset in the period. I decline that route twice over. A guard form the grammar does not document is a parse risk, and a manual that fails to parse loses all six transitions it currently replays. And distinguishing 96 cells by 96 neighbour chains costs more symbols than the 96 pixels it explains, which is exactly the failure constraint 3 names. Inexpressible without nesting, uncompressible with it."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, which is rows 29-54 x cols 10-63. They are therefore somewhere in the 3998 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility is safe; but it is also where any title, target display, score or instruction would live, and it is the most likely home of whatever finishing means. I mention it because it is the largest thing I do not know, and because the only way to see it is to make a cell of it change, which is another argument for pressing the selector past the slots I have already mapped."
    [depends: no_goal_section_on_purpose  probe: pending]

  theorem cascade_length_carries_no_signal_here "t1 through t4 and t6 through t9 each returned 2 frames and t5 returned 1, yet t5 (key(7)) and t7 (key(3)) produced identical 12-cell effects, and t6 (key(4), 2 frames) and t8 (key(4), 2 frames) produced different effects. Frame count tracks neither the magnitude nor the presence nor the identity of change and must not be used as a motion detector. The one thing it may still carry is that ACTION7 is a different key from ACTION3 that happened to agree in this state."
    [probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot's middle rows, a port, four strip cells and two cells of the meter bar -- four unrelated roles. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm is what draws the frame. The gain is measured: six declarations own all 74 cells that need an owner against 74 pixels written out, responsibility reports 0 unexplained, and seven rules over those classes reproduce six of nine transitions. The cost is measured too: no rule can name the strip, so every strip rule carves it out of its class with four negative neighbour guards, and the meter rule now needs an off-board test to separate two cells of the same class two columns apart. Those guards are pixel-fitting in a costume; they are correct on every instance of both classes in frame 0, they have survived three blanks and three restores, and they are the price of a colour-first arm."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem instance_anchoring_is_frame_zero_and_the_arm_extends_it_as_cells_vary "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0. Two consequences, both now confirmed rather than assumed. A cell constant in frame 0 gets no instance, which is why the slots above row 29 are invisible to this manual and why it cannot draw the selector. And a cell that later varies stops being board and gains one: (53,62) was constant through t7 and owned by nothing, then varied at t8, and cells_needing_an_owner went from 73 to 74 with dynamic_cells 97 to 98. I have raised stud_population to 11 accordingly, and that new instance forced the meter rule's guard to be rewritten, since the old one was true of both bar cells and would have ticked them together at t4."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem two_keys_have_never_been_pressed "this world has seen ACTION1, 2, 3, 4 and 7. key(5) and key(6) are unpressed and unknown, and the case for pressing them just got much stronger: t6 showed that a key press can accomplish twelve cells of change and move the bar not at all, so the cost of an experiment is at worst one quarter of a bar cell out of sixty-two remaining. If either is a click carrying coordinates, this guard language cannot express it at all and the finding will be recorded as prose. Pressing them also doubles as the meter probe, since neither is key(4)."
    [depends: the_meter_is_probably_a_clock_and_not_a_toll  probe: pending]

  theorem no_goal_section_on_purpose "all ten states returned NOT_FINISHED and nothing in nine transitions indicates what finishing means. The live candidates are that a lane's texture must be brought to agree with the badge at its far end, that every slot in the column must be visited or solved, or that the objective is in the rows I have never been shown. An absent goal compiles to is_goal -> False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level."
    [depends: the_arena_is_lanes_and_the_badge_is_row_aligned_with_the_cavity  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "mdl_segmenter returned negative gain on both variants, -3513 bits at 4 tracks and -18186 at 51, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), which is a fact about the operator and not about the world. cegis_miner refused all four tracks because its precondition is exactly one move event per transition and this world has no mover; correct and unhelpful, and its refusal messages naming 'vanish' and 'recolor' agree with my event vocabulary. zero_space calls its own evidence THIN in its own words -- 9 transitions constraining rank 4 of 686 features, null space of dimension 682 -- and its single global law spans nearly every dynamic cell at once, which is what a 682-dimensional null space produces rather than what a conservation law looks like; notably its cell list includes both (53,62) and (53,63), so even its one law is really the observation that those two cells changed. What I took from the engines is the store arithmetic, dynamic_cells 98 and cells_needing_an_owner 74, and both closed against a reconstruction built without them."
    [probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- rewritten around the finding that inverted last round's
# economics. What changed:
#
#   THE TOLL READING IS DEAD. t6 was a key(4) press that restored twelve cells
#     and moved the bar not one unit. So key(4) is not "the metered action" and
#     there is nothing to ration. Every prune that rationed it is gone, and I
#     say so rather than quietly dropping it.
#   THE BAR IS PROBABLY A CLOCK, one cell per four actions, consumed right to
#     left, 62 cells and roughly 248 actions left. If that is right, delay is
#     the only thing that costs, and an action that learns nothing is the
#     expensive move.
#   TWO IDENTICAL FRAMES ANSWERED THE SAME KEY DIFFERENTLY (S5 and S7 under
#     key(4)). Any search that treats the frame as the state is unsound here,
#     and that is now a prune rather than a caveat.
#   THE STRIP IS ONE GLOBAL DIAGONAL TEXTURE, colour 2 where (r+c) mod 3 = 1.
#     It predicts the unseen row 33 exactly, so selecting the upper slot is now
#     a scored experiment and not just sightseeing.
#   THE CURRENT STATE IS BLANKED, which makes the blank-versus-toggle
#     separator available for one action, with the manual predicting inert.
#
# Nothing below is a stored line of play. Every entry is a ranking rule that
# still has to be evaluated against whatever state the searcher is in.

order   separate_hiding_from_toggling_by_repressing_the_hiding_key_in_the_hidden_state  [proof: lean]
order   settle_whether_the_bar_is_a_clock_by_spending_actions_that_are_not_the_restore_key  [proof: lean]
order   press_the_two_never_pressed_keys_while_the_bar_is_still_long      [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule      [proof: lean]
order   make_some_cell_outside_the_observed_window_vary                   [proof: lean]
order   compare_a_lane_against_the_badge_at_its_own_far_end               [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known          [proof: lean]
order   read_both_bar_cells_and_the_frame_count_after_every_command       [proof: lean]

prefer  an_action_on_which_two_live_readings_predict_different_frames     [ev: 4 rival pairs open]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  a_slot_never_selected_over_one_already_drawn_twice                [ev: 2 slots seen of a column]
prefer  a_state_whose_lane_carries_the_badge_over_a_lane_without_one      [ev: 1/2 lanes carry a badge]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats        [ev: 98/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced           [ev: 0/9 transitions test it]
prefer  an_action_whose_outcome_the_manual_commits_to_by_a_rule           [ev: 6/9 transitions replay]

heuristic slots_in_the_column_never_yet_selected                          [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed                           [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                     [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                      [admissible: lean]
heuristic cells_of_the_bar_still_unconsumed                               [admissible: lean]

prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead      [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead        [proof: lean]
prune   repeat_of_a_key_already_witnessed_inert_in_this_exact_state => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead       [proof: lean]
prune   bar_consumed and not goal => dead                                  [proof: lean]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter obj0/obj2/obj3 (13x36 blobs, colour null, 436-440 cells)", "verdict": "reject",
   "why": "connected_components(4) fuses the panel widget with the whole colour-4 arena into one 440-cell blob and reports gain_bits -3513 and -18186 on the two variants; a track that is negative-gain and colour-null tells me about the operator, not the world, and it cannot be located by the colour-keyed arm."},
  {"id": "O-02", "subject": "mdl_segmenter obj1 (2x54, present in all 10 frames)", "verdict": "entailed",
   "why": "rows 53-54 x cols 10-63 is the meter bar plus the floor row, which my Stud instances at (53,63) and (53,62) plus board already cover; the track adds no cell I do not own."},
  {"id": "O-03", "subject": "colour class 2 gains a member at (53,62)", "verdict": "accept", "as": "Stud",
   "why": "the cell varied at t8 for the first time, so it stopped being board, and the store moved cells_needing_an_owner 73 -> 74 and dynamic_cells 97 -> 98 in exactly that one step; stud_population and the ownership invariant are raised to 11 and 74."},
  {"id": "O-04", "subject": "the 4x4 colour-14 badge at rows 31-34 x cols 42-45", "verdict": "reject",
   "why": "it has never varied, so the board already draws it correctly; declaring an object for it would create instances competing with a board cell for pixels that responsibility currently reports as 0 unexplained. Kept as landmark badge_head and as prose in the_arena_is_lanes_and_the_badge_is_row_aligned_with_the_cavity."},
  {"id": "R-01", "subject": "cegis_miner, all four tracks refused", "verdict": "reject",
   "why": "its precondition is exactly one move event per transition and this world narrates as recolour only; its own refusal strings name 'vanish' and 'recolor', which agrees with my events section but yields no rule."},
  {"id": "R-02", "subject": "key4_advances_the_meter, old guard above=5 and below=4", "verdict": "reject",
   "why": "with (53,62) now an instance that guard is true of both bar cells, so it would tick them together at t4 where the world ticked only (53,63); replaced rather than kept."},
  {"id": "R-03", "subject": "key4_advances_the_meter_once with rightof(?p) = wall", "verdict": "accept",
   "why": "(53,63) is the only Stud in frame 0 whose right neighbour is off-board, so the rule fires exactly once, on the only tick I can witness; `<cell> = wall` is the documented off-board test and if it fails to fire the symptom is a one-cell divergence at (53,63) on t4 with the repair named in the manual."},
  {"id": "R-04", "subject": "a rule ticking (53,62) on a later key(4)", "verdict": "reject",
   "why": "S5 and S7 are the same frame and key(4) ticked from one and not the other, so any such rule fires at t6 where the world did not and is then guarded off before t8 where it did; it would lose two transitions to save none."},
  {"id": "R-05", "subject": "key3/key7 blank and key4 restore rules", "verdict": "accept",
   "why": "unchanged in form and now witnessed three times each for key(3) and key(4) instead of once; the negative neighbour guards still exclude (38,16), (39,16), the four bar-slot Studs and both meter cells, checked instance by instance against frame 0."},
  {"id": "R-06", "subject": "a rule for the selector, ACTION1/ACTION2", "verdict": "reject",
   "why": "the witness pairs in the_swap_is_provably_inexpressible_here are indistinguishable to every guard the language has, and open-loop replay means a wrong selector rule desynchronises the manual permanently -- silence currently buys six of nine transitions."},
  {"id": "L-01", "subject": "the world is a function of the visible frame", "verdict": "reject",
   "why": "S5 and S7 are identical cell for cell and key(4) sent them to different successors; the store's 7 distinct states out of 10 corroborates exactly the three collisions this implies."},
  {"id": "L-02", "subject": "zero_space global law over 98 cells", "verdict": "reject",
   "why": "the engine itself grades its evidence THIN -- 9 transitions constrain rank 4 of 686 features, leaving a 682-dimensional null space -- and the law's support is nearly every dynamic cell at once, which is the signature of an underdetermined system rather than a conservation."},
  {"id": "L-03", "subject": "the strip texture, colour 2 iff (row + col) mod 3 = 1", "verdict": "accept",
   "why": "21 cells across three rows and two lanes satisfy it without exception, including (32,16)=1 and (32,17)=2 and (32,20)=2 handed to me by the t1 divergence report; recorded as a theorem because no rule needs it, which I flag as a constraint-3 shortfall rather than hide."},
  {"id": "L-04", "subject": "key(4) is the metered action and the other keys are free", "verdict": "reject",
   "why": "t6 was a key(4) press with no bar movement at all; the belief rested on a single witness and is withdrawn, taking the playbook prune that rationed key(4) with it."},
  {"id": "E-01", "subject": "the meter cadence", "verdict": "probe-pending",
   "why": "I wanted a counter -- tick every fourth action, or every other press of one key -- and the grammar has no counter in guards, values or events, and a faked parity cell would be a guaranteed replay failure; written as the_meter_cadence_is_inexpressible_in_this_language plus a pre-registered replay of 6/9 with one-cell divergences at transitions 7 and 8, both at (53,62)."},
  {"id": "E-02", "subject": "the selector swap", "verdict": "reject",
   "why": "unchanged from last round and still proven: four distinct required outcomes for five cells that are identical in colour and in all four neighbours; written as prose, not as rules."},
  {"id": "P-01", "subject": "repress the hiding key from the hidden state", "verdict": "probe-pending",
   "why": "the strip is blanked now, so one action separates hide-and-show from toggle-and-toggle, and my manual predicts inert for it -- the same press scores the world and the manual."},
  {"id": "P-02", "subject": "three consecutive actions none of which is key(4)", "verdict": "probe-pending",
   "why": "the clock reading turns (53,61) to colour 3 on the third of them and the toll reading leaves the bar alone; using the two never-pressed keys as two of the three settles E-01's rival and two_keys_have_never_been_pressed at once."},
  {"id": "P-03", "subject": "push the selector past the slots already drawn", "verdict": "probe-pending",
   "why": "a repaint of rows 24-35 confirms the column continues above row 29 and would be the first variation ever seen outside rows 30-53; no repaint at the top bounds the panel at two slots and refutes the collapsed-slot reading of (29,13) and (29,14)."},
  {"id": "P-04", "subject": "read row 33 of lane A while the upper slot is selected", "verdict": "probe-pending",
   "why": "the texture rule predicts 1 1 2 1 1 2 at cols 17-22 and colour 2 at (33,16); it is the only prediction I have that names cells I have never been shown."}
]
```
```
