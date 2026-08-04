# call-004-theorize-round1

model: `claude-opus-5` · 846241 ms · $2.818145 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 100252, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 100252, "cache_read_input_tokens": 36187, "inference_geo": "not_available", "input_tokens": 4, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 64065, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 64065, "cache_read_input_tokens": 36187, "input_tokens": 2, "output_tokens": 6818, "type": "message"}], "output_tokens": 70818, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 30 566666644444444444444444444444444444455555555555555555
 31 56000064444444444444444444444444eeee455555555555555555
 32 56066014444444444444444444444444eeee455555555555555555
 33 56066024444444444444444444444444eeee455555555555555555
 34 56000064444444444444444444444444eeee455555555555555555
 35 566666644444444444444444444444444444455555555555555555
 36 555335544444444444444444444444444444455555555555555555
 37 555335544444444444444444444444444444455555555555555555
 38 555225544444444444444444444444444444455555555555555555
 39 555225544444444444444444444444444444455555555555555555
 40 555555544444444444444444444444444444455555555555555555
 41 555555544444444444444444444444444444455555555555555555
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
- t6   ACTION1   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t7   ACTION2   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t8   ACTION1   frames=2   state=NOT_FINISHED 73 cells changed, rows 30-53, cols 11-62, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
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
   "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 3 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
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
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
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
  "background": 5,
  "candidates": 7,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 5,
   "recolor": 5,
   "vanish": 5
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
    "frames_present": 4,
    "n_cells": 440,
    "shape": [
     13,
     36
    ],
    "track_id": "obj3"
   },
   {
    "color": null,
    "first_frame": 6,
    "frames_present": 1,
    "n_cells": 436,
    "shape": [
     13,
     36
    ],
    "track_id": "obj4"
   },
   {
    "color": null,
    "first_frame": 7,
    "frames_present": 1,
    "n_cells": 440,
    "shape": [
     13,
     36
    ],
    "track_id": "obj5"
   },
   {
    "color": null,
    "first_frame": 8,
    "frames_present": 2,
    "n_cells": 436,
    "shape": [
     13,
     36
    ],
    "track_id": "obj6"
   }
  ],
  "variants": [
   {
    "baseline_bits": 6762,
    "compression_ratio": 2.11328,
    "events": 15,
    "gain_bits": -7528,
    "ms": 99,
    "script_bits": 14290,
    "split_by_color": false,
    "tracks": 7
   },
   {
    "baseline_bits": 6762,
    "compression_ratio": 2.17835,
    "events": 92,
    "gain_bits": -7968,
    "ms": 42,
    "script_bits": 14730,
    "split_by_color": true,
    "tracks": 38
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
  "difference_rank": 5,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.007289,
   "difference_rank": 5,
   "features": 686,
   "space_dimension": 681,
   "transitions": 9,
   "verdict": "THIN: 9 transitions constrain rank 5 of 686 features, so the null space has dimension 681 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
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
     "c0@32"
```

The full proposal stream is 1372 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- second edition. The first edition of THIS world's manual
# replayed 4/5 with a divergence of exactly four cells at t=0:
#   (40,13) (40,14) (41,13) (41,14)   manual says 3, world says 5.
# That is 92 of 96 cells of the ACTION1 transition correct and four wrong, and
# the four are not scattered: they are the BOTTOM TWO ROWS of the bar's landing
# site in the bottom slot, at the bar's own two columns. Everything else in the
# file is untouched by this refutation and stays.
#
# WHAT THE FOUR CELLS MEAN. My reading was "the two 6x6 slots exchange images,
# (r,c) takes the colour of (r+-6,c)". Under it the bar copies down as
# 3,3,2,2,3,3 into rows 36-41. THE WORLD COPIED ONLY 3,3,2,2 INTO ROWS 36-39
# AND LEFT ROWS 40-41 BACKGROUND. The bar is six rows tall in the top slot
# (seven on screen, counting the never-changing cap at row 29) and FOUR rows
# tall in the bottom slot. The exchange is exact everywhere else, including the
# box travelling up entire and the two port pixels (38,16)=1 and (39,16)=2
# landing at (32,16) and (33,16).
#
# THE FIX IS FOUR RULES WHERE THERE WERE TWO. I need to separate the two
# destination cells that copy the bar from the two that clear, and the two are
# MIRROR IMAGES in the box: (37,13) and (40,13) have identical 4-neighbourhoods
# (6 above, 6 below, 0 left, 0 right). The nearest cell that tells them apart is
# TWO up: above(above((37,13))) = (35,13) = 3, above(above((40,13))) = (38,13)
# = 6. Same for the border pair: above^2 of (36,13) is 3, of (41,13) is 6. So
# every one of the four new rules carries colored(above(above(?p)), <3|6>) and
# the split is exact, 2/2 and 2/2. I SAY PLAINLY WHAT THAT GUARD IS: a proxy
# for a row test I cannot write, fitted to one transition. It is not a law
# about neighbours; it is the cheapest expressible separator of two cells I
# have watched behave differently. See the_truncation theorem.
#
# THE CENSUS (unchanged, and now confirmed rather than reconstructed):
#   rows 30-35 x cols 11-16   36  top slot
#   rows 32-33 x cols 17-22   12  top readout
#   rows 36-41 x cols 11-16   36  bottom slot
#   rows 38-39 x cols 17-22   12  bottom readout
#   (53,63)                    1  meter tip
# 97 = dynamic_cells, 96 = the t1/t2 diffs, 4096-97 = 3999 = constant_cells,
# and certify now reports cells_unexplained = 0 over the whole 64x64 frame.
#
# EXPECTED REPLAY 5/5.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Field    { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object BarBody  { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object BarCore  { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Blank    { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Frame    { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  object Hollow   { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Dot      { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  Field   [segment: dynamic_colour_5 ev: t0-t5 compress: 24]
  BarBody [segment: dynamic_colour_3 ev: t0-t5 compress: 8]
  BarCore [segment: dynamic_colour_2 ev: t0-t5 compress: 10]
  Blank   [segment: dynamic_colour_4 ev: t0-t5 compress: 12]
  Frame   [segment: dynamic_colour_6 ev: t0-t5 compress: 22]
  Hollow  [segment: dynamic_colour_0 ev: t0-t5 compress: 12]
  Dot     [segment: dynamic_colour_1 ev: t0-t5 compress: 9]

events:
  event recolored(o, c)

rules:
  rule k1_field_to_frame forall ?p in Field [ev: t1 cov: 14/14]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_field_to_hollow forall ?p in Field [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_field_to_dot forall ?p in Field [ev: t1 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_field_to_core forall ?p in Field [ev: t1 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_bar_to_frame forall ?p in BarBody [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_bar_to_hollow forall ?p in BarBody [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_core_to_frame forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(above(above(?p)), 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_blank_to_dot forall ?p in Blank [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_blank_to_core forall ?p in Blank [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_frame_to_field forall ?p in Frame [ev: t1 cov: 14/14]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_frame_to_bar forall ?p in Frame [ev: t1 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_clears forall ?p in Frame [ev: t1 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_frame_to_core forall ?p in Frame [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_hollow_clears forall ?p in Hollow [ev: t1 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_dot_to_field forall ?p in Dot [ev: t1 cov: 1/1]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_dot_to_blank forall ?p in Dot [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k1_core_to_field forall ?p in BarCore [ev: t1 cov: 1/1]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_core_to_blank forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k2_field_from_frame forall ?p in Field [ev: t2 cov: 14/14]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_hollow forall ?p in Field [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_dot forall ?p in Field [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_core forall ?p in Field [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_bar_from_frame forall ?p in BarBody [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_from_hollow forall ?p in BarBody [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_core_from_frame forall ?p in BarCore [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k2_blank_from_dot forall ?p in Blank [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_blank_from_core forall ?p in Blank [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_frame_from_field forall ?p in Frame [ev: t2 cov: 16/16]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2 cov: 10/10]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_dot_from_field forall ?p in Dot [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_dot_from_blank forall ?p in Dot [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_core_from_field forall ?p in BarCore [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k2_core_from_blank forall ?p in BarCore [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k3_dot_blanks forall ?s in Dot [ev: t3 cov: 8/8]
    when act=key(3) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k3_core_blanks forall ?s in BarCore [ev: t3 cov: 4/4]
    when act=key(3) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k4_dot_lights forall ?s in Dot [ev: t4 cov: 8/8]
    when act=key(4) and colored(?s, 4) then recolored(?s, 1)

  rule k4_core_lights forall ?s in BarCore [ev: t4 cov: 4/4]
    when act=key(4) and colored(?s, 4) then recolored(?s, 2)

  rule k4_meter_advances forall ?s in BarCore [ev: t4 cov: 1/1]
    when act=key(4) and colored(?s, 2) and rightof(?s) = wall then recolored(?s, 3)

  rule k7_dot_blanks forall ?s in Dot [ev: t5 cov: 8/8]
    when act=key(7) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k7_core_blanks forall ?s in BarCore [ev: t5 cov: 4/4]
    when act=key(7) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

laws:
  invariant field_instances count(Field) = 24 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant barbody_instances count(BarBody) = 8 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant barcore_instances count(BarCore) = 10 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant blank_instances count(Blank) = 12 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant frame_instances count(Frame) = 22 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant hollow_instances count(Hollow) = 12 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant dot_instances count(Dot) = 9 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant board_cells count(board) = 3999 [status: matches constant_cells exactly]
  invariant meter_tip_now count(BarCore, color = 3) = 1 [status: state-dependent-not-an-invariant]

  theorem the_old_manual_is_discarded_entire "The manual I was first handed is about another world: spawn ring rows 8-12, panel rows 1-5, 26 states, a 64-cell meter at row 63. This log has 6 states, dynamics confined to rows 30-41 cols 11-22 plus (53,63), and certify returned 0/5 replay with first divergence at t=0. No rule of it could ground here, so repair was meaningless and I deleted all of it. That decision is now paid for: the replacement replays 4/5 and its single divergence is four cells wide."
    [probe: passed]

  theorem the_census_is_confirmed "The five rectangles in the header were an inference from counts, since the brief hands me boxes and totals rather than cell sets. They are now confirmed from two directions. certify: responsibility reports cells_unexplained = 0 over all 4096 cells, so every pixel of frame 0 is board or belongs to a declared instance, which no wrong census survives. And replay: 92 of the 96 cells of the ACTION1 transition are reproduced exactly by rules whose guards read cells six rows away, which is impossible if the slot rectangles were misplaced by even one row. The four failures are a fact about the BAR, not about the rectangles."
    [depends: the_old_manual_is_discarded_entire  probe: passed]

  theorem s0_equals_s2_and_that_is_what_lets_me_read_frame_zero "states = 6 and distinct_states = 5, so exactly one pair coincides. S4 and S5 carry (53,63)=3 while S0-S3 carry 2; S4 and S5 differ in 12 readout cells; S3 differs from S2 in 12 and from S1 in at least 84 since S1 and S2 differ in 96; S0 differs from S1 in 96. THE ONLY SURVIVOR IS S0 = S2. Two things follow. ACTION2 at t2 exactly undid ACTION1 at t1, so whatever ACTION1 does to the bar is REVERSIBLE and the bar comes back six rows tall. And the widget in the current frame IS the frame-0 widget, since t3, t4 and t5 touched only the bottom readout and the meter tip -- which is how every source colour in this file was read off the picture in front of me without ever being shown frame 0."
    [depends: the_census_is_confirmed  probe: passed]

  theorem the_truncation_is_the_only_thing_i_got_wrong_and_i_have_fitted_it_not_explained_it "THE REFUTATION, stated exactly. Under ACTION1 the bar's image lands in the bottom slot as 3,3 / 3,3 / 2,2 / 2,2 at rows 36-39 and rows 40-41 cols 13-14 go BACKGROUND, where I predicted 3,3 / 3,3. The bar is six rows in the top slot (30-35, seven on screen counting the never-changing cap at row 29) and four rows in the bottom. THE FIX IS A FIT. (37,13) and (40,13) have identical four-neighbourhoods -- 6 above, 6 below, 0 left, 0 right -- because the box is mirror-symmetric, so no local test separates them; the nearest asymmetry is two rows up, where (35,13)=3 and (38,13)=6, and that is the guard I wrote. It separates all four pairs exactly, 2/2 and 2/2, and it is a proxy for a row test the guard language does not have. I am claiming a fitted separator, not a neighbour law, and I would rather say so than let colored(above(above(?p)), 3) read as physics."
    [depends: s0_equals_s2_and_that_is_what_lets_me_read_frame_zero  probe: passed]

  theorem two_readings_of_the_widget_and_the_truncation_now_favours_the_second "READING A, exchange: two 6x6 slots trade images, and the bar simply RENDERS shorter in the lower slot. READING B, scroll: this is a list of at least three items scrolled by 6 rows, ACTION1 brings the box up to the top slot and a THIRD item -- which happens to look like 3,3,2,2 -- into the bottom, and ACTION2 scrolls back. Both explain every cell of t1 and t2 identically, because from S0 the two are the same map. The truncation is what tilts me: under A I must carry a slot-dependent rendering law with one witness and no mechanism; under B the four-row thing is just a different item and nothing needs explaining. I DO NOT DECIDE, because deciding costs nothing today and the probe is one command: A says a second consecutive ACTION1 returns W0 exactly, B says it produces a configuration never seen. My compiled rules implement neither reading in W1 -- they are colour lookups keyed on W0 colours and they fire on nothing there -- so the manual currently predicts SILENCE for ACTION1 in W1 and I expect that to be refuted."
    [depends: the_truncation_is_the_only_thing_i_got_wrong_and_i_have_fitted_it_not_explained_it  probe: pending]

  theorem the_swap_rules_are_thirty_eight_and_constraint_three_is_failed "One law -- take the colour of the cell six away -- became 36 rules, and the truncation made it 38, and I will not dress that up. recolored(o, c) takes an INTEGER LITERAL, so a target colour cannot be read from a cell and must be named; the law splits into one rule per (source colour, target colour) pair, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I say so under constraint 3. I keep it because the alternative is 96 unexplained pixels twice over. What buys some of it back is the TYPES: a type is a frame-0 colour, the frame-0 configuration is W0, so a rule's source colour selects its type for free and separates top-half from bottom-half instances without a single row test -- which is why only the two truncation rules in this file need a nest of above() to say where they are."
    [depends: two_readings_of_the_widget_and_the_truncation_now_favours_the_second  probe: passed]

  theorem barcore_is_four_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on four unrelated features: the 4-cell core of the bar (rows 32-33, cols 13-14), the lower port pixel (39,16), four dots of the bottom readout, and the meter tip (53,63). The arm looks types up by colour alone, so all ten are BarCore and no rule can tell the roles apart by type. I separate them by local geometry, every separator a cell I have read: the bar core has colour 3 two rows above; the readout dots have a colour-1 dot immediately left; the port pixel has colour 0 left of it; the meter tip is the only instance whose rightof is off-board. This is no longer a bet -- five transitions replayed with these separators in place, including t4 where the meter rule fired on exactly one of the ten instances and the readout rules on four others in the same step, and certify found no ambiguous pair in 30. NO RULE IN THIS FILE USES not: every exclusion is a positive colour test."
    [depends: the_swap_rules_are_thirty_eight_and_constraint_three_is_failed  probe: passed]

  theorem the_twenty_four_background_coloured_cells_do_seat "The named way this manual could have failed, now settled. Twenty-four dynamic cells -- rows 30-35, cols 11, 12, 15, 16 -- render colour 5 at frame 0, and 5 is the BACKGROUND; cells_needing_an_owner is 73 rather than 97, which is exactly those 24 short, and I read that as the pipeline not requiring an owner for a background-coloured cell. It does not follow that the arm refuses to SEAT one, and it does not: the fourteen Field rules fired at t1 and the divergence set contains none of those 24 cells. Declaring the background colour as an object type is legal and it works."
    [depends: the_census_is_confirmed  probe: passed]

  theorem action1_here_moves_seventy_two_cells_and_four_of_them_have_new_colours "I stand in W0 with BOTH readouts blank, since ACTION7 erased the bottom one at t5. Swapping two identical blank strips changes nothing, so ACTION1 now should move the 72 slot cells and NOT ONE readout cell and NOT the meter. The count is unchanged by this edition's fix -- the four truncation cells change either way -- but their TARGET colours are new: (40,13),(40,14) go 0 to 5 and (41,13),(41,14) go 6 to 5, where the last edition said 3. That is a sharp, cheap check on the fix, legible in the raw diff without any replay machinery. 96 changed cells would refute the claim that a blank readout travels invisibly; 3 at any of those four cells would say the truncation is not a property of the destination at all."
    [depends: the_truncation_is_the_only_thing_i_got_wrong_and_i_have_fitted_it_not_explained_it  probe: pending]

  theorem the_readout_toggles_and_action3_and_action7_are_not_the_same_action "Twelve cells at rows 38-39 cols 17-22 have shown exactly two configurations in six states: BLANK (all 4) and PATTERN (eight 1s, four 2s, period 3 along each row, the rows offset by one column). ACTION3 set BLANK at t3, ACTION4 set PATTERN at t4, ACTION7 set BLANK at t5, and all three transitions replay exactly. The pattern returns to the same twelve colours it had, which is why k4_dot_lights and k4_core_lights can be bare colour rules: an instance's TYPE is its frame-0 colour and therefore already records which cell gets a 1 and which a 2. WHAT I CANNOT CLOSE: ACTION3 and ACTION7 have identical net effects and I have written them as two rules with identical bodies, which is the shape of a claim that they are one key. THEY ARE NOT -- ACTION3 returned two internal frames and ACTION7 returned one. My own semantics say cascade single_frame, so my compiler discards the only evidence that separates them, and I record that here rather than pretend it is not in the log."
    [depends: the_census_is_confirmed  probe: passed]

  theorem the_meter_has_one_witness_and_its_next_cell_is_undrawable "Row 53 is a colour-2 bar across the frame; (53,63) turned 3 at t4 under ACTION4 and is the only cell of row 53 that has ever changed. I encode ACTION4-advances-it because that is the only reading this guard language can express and it has one witness. THREE READINGS FIT ONE WITNESS: that key 4 advances it, that lighting the readout advances it, that command index or parity advances it. There is no command counter in the guard language, so the third cannot be written at any length. THE STRUCTURAL PART: the next cell is (53,62), which has never changed, so it is board, so no instance sits on it, so no event here can touch it -- recolored takes an object and there is no object there. MY MANUAL MUST PREDICT THE SECOND ADVANCE NEVER HAPPENS and must be wrong by exactly one pixel every time the meter moves, until a later census heals one step behind. A divergence set of one cell in row 53 implicates nothing else in this file."
    [depends: barcore_is_four_unrelated_things_and_the_arm_sees_only_colour  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where no rule fires I say NOTHING HAPPENS in the same voice I use for what I watched. Audit at the current state, W0 with both readouts blank. ACTION1: 72 cells, witnessed and falsifiable at once -- not a silence. ACTION3 and ACTION7: predicted silent HERE because the pattern they erase is already gone; that silence is entailed by witnessed rules, not forged. ACTION4: predicted to light 12 readout cells and move no meter cell, the second half being the blind spot above. ACTION2 IN W0: PREDICTED SILENT ON ZERO WITNESSES -- every ACTION2 in the log was pressed in W1 -- and that forgery covers 18 rules. ACTION1 IN W1: PREDICTED SILENT ON ZERO WITNESSES, and this is now my LARGEST forgery, because it is exactly the probe that would decide exchange against scroll and my rules are colour lookups that ground on nothing there. ACTION5 and ACTION6: predicted silent and never pressed in any state. A probe ranker scoring expected bits over my manual and its ablations prices a predicted identity at zero, because every ablation agrees with a rule that does not fire, SO THE ACTIONS I MOST NEED ARE THE ONES IT CAN NEVER BUY. Saying so in prose is the only lever this desk has."
    [depends: action1_here_moves_seventy_two_cells_and_four_of_them_have_new_colours, the_meter_has_one_witness_and_its_next_cell_is_undrawable  probe: pending]

  theorem no_goal_section_and_the_reason_is_arithmetic "The pos form is dead outright: nothing in this world moves, every rule here is a recolour, and no instance's pos changes in six states -- cegis_miner's refusal of all four tracks says the same thing from outside. That leaves counts over seven types whose members are one 12x12 widget plus one meter cell, and every count I can write names a CONFIGURATION rather than a victory. count(Frame, color = 5) = 14 says only that the box is in the top slot. count(Dot, color = 4) = 8 says only that the readout is blank. count(BarCore, color = 3) = 1 says the meter advanced once and IS TRUE RIGHT NOW, four commands after RESET, so declaring it would make the plan tier report success at a state I have no reason to call a win. I cannot count the meter past one, because (53,62) and its 62 neighbours have never changed and hold no instance: THE GOAL LANGUAGE CAN ONLY SPEAK ABOUT CELLS THAT HAVE ALREADY MOVED. So there is no goal section. What ends that is an observation, not an edit -- a second cell of row 53, or any cell outside rows 30-41 and row 53 changing at all."
    [depends: the_meter_has_one_witness_and_its_next_cell_is_undrawable  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3999 constant cells, not just naming them board, and certify now agrees that they are all accounted for. A colour-4 panel fills rows 29-41 from col 17 to col 46, carrying a 4x4 block of colour 14 at rows 31-34 cols 42-45 -- the only colour-14 anywhere and the only structure on the panel's right. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them from it. Row 29 shows 5,5,3,3,5,5 at cols 11-16, the same signature as the top slot, and has NEVER changed: the bar reads seven rows tall on screen while only six of it is alive, and that static cap is now load-bearing evidence, because the thing that lands in the bottom slot is four rows and the thing that leaves the top is six or seven depending on whether you count it. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the meter, row 54 a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports BOTH variants at negative gain -- minus 4037 bits on four tracks, minus 10409 on 33 -- so by its own measure it compressed nothing, and I take none of its structure: obj0, obj2 and obj3 are 436-to-440-cell blobs of shape 13x36 that swallow the colour-4 panel together with the widget, and obj1 is rows 53 and 54 read as one 2x54 strip. What I DO take is a frame-index witness independent of my rules: obj0 present only at frame 0, obj2 first at frame 1, obj3 first at frame 2 and present for four frames -- the widget redrawn at t1 and again at t2 and standing still after, exactly two 96-cell transitions and no third, which is my S0 = S2 deduction arrived at from another direction. Note also that obj2 has 436 cells where obj0 and obj3 have 440: the frame-1 blob is FOUR CELLS SMALLER, and those four cells are the truncation this edition fixes. The engine had the answer in a field I did not read last round. cegis_miner refuses all four tracks and its verdict, that the world does not narrate as one mover, is TRUE and is the strongest negative result here. zero_space self-reports THIN in its own words -- 5 transitions constraining rank 3 of 679 features, null space dimension 676 -- and its one global law is my census with the meter tip appended; I take the corroboration and reject the law as unfalsified rather than confirmed, which is what its own report says."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me. STATE: W0, both readouts blank colour 4, (53,63) rendering 3. ACTION1: exactly 72 cells change, no readout cell, no row-53 cell, and (40,13),(40,14),(41,13),(41,14) all become 5. ACTION1 TWICE: my manual predicts the second press changes NOTHING, and I expect to be wrong; if it restores W0 the exchange reading wins and 18 rules generalise by symmetry, if it shows a configuration I have never seen the scroll reading wins and the bar and the four-row glyph are different items. ACTION2 HERE: predicted silent on zero witnesses, and I expect to be wrong for the same reason. ACTION3, ACTION7: nothing changes, and this one I believe. ACTION4: the 12 bottom readout cells take their frame-0 arrangement of 1s and 2s and NO cell of row 53 moves; if (53,62) turns 3 then ACTION4 advances the meter unconditionally, my rule is right in spirit and undrawable in fact, and the divergence set is one cell that implicates nothing. ACTION5, ACTION6: never pressed in six states, and I predict only that whichever is pressed produces the largest single addition to this manual available. If the next command is ACTION3 or ACTION7 I will have learned least."
    [depends: action1_here_moves_seventy_two_cells_and_four_of_them_have_new_colours, the_silences_i_assert_and_which_of_them_are_forged  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: six states, five transitions (RESET, A1, A2, A3, A4, A7). Widget in
# configuration W0 -- colour-3 bar in the TOP slot, hollow colour-6 box in the
# BOTTOM slot. BOTH readouts blank (colour 4). (53,63) advanced to 3 at t4.
# 97 cells have ever changed; certify reports 0 unexplained pixels in 4096.
#
# WHAT CHANGED THIS ROUND. Replay was 4/5, diverging at t=0 on exactly four
# cells: (40,13) (40,14) (41,13) (41,14), the bottom two rows of the bar's
# landing site. The bar is six rows tall on top and FOUR rows tall on the
# bottom. Two rules became four; nothing else moved. The separator I used --
# the colour two rows above -- is a FIT, not a law, and the manual says so.
#
# THE STRUCTURAL QUESTION THAT IS NOW OPEN AND WAS NOT BEFORE
#   Reading A, exchange: two slots trade images and the bar renders shorter
#     below. Reading B, scroll: a list of >=3 items scrolls by 6 and the
#     four-row glyph is a THIRD ITEM, not the bar.
#   From W0 the two are the same map, so nothing observed splits them. A
#   SECOND CONSECUTIVE ACTION1 splits them in one command: A returns W0,
#   B shows a configuration never seen. My rules fire on nothing in W1, so
#   they predict silence there -- the largest forged silence in the file.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in any state. Zero constraint.
#   * ACTION1 in W1, ACTION2 in W0: never pressed, silence forged, 18 rules
#     and one structural reading riding on each.
#   * Whether ACTION4 advances the meter always, or only when it lights the
#     readout, or whether the meter runs on the command index. One witness
#     cannot split three readings and the index reading is inexpressible.
#   * ACTION3 vs ACTION7: identical net effect, 2 frames vs 1. Not the same
#     action inside; cascade single_frame throws away the only evidence.
#   * The win condition. Nothing countable separates a win from here.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * (53,62) is board, holds no instance, is UNDRAWABLE. Every meter advance
#     after the first costs exactly one pixel of accuracy, permanently.
#   * ACTION1 here is predicted at 72 cells, NOT 96, and the four truncation
#     cells are predicted to become 5, not 3. That is the fix on trial.
#   * ACTION1 in W1 and ACTION2 in W0 are predicted silent with no witness.
#     A refutation there is a purchase, not a defect.
#
# THE RANKED LIST
# 1. ACTION5 or ACTION6. Never pressed in six states. Any outcome is the
#    largest single addition available -- including "nothing", which would be
#    the first WITNESSED inertness in this world. The ranker prices these at
#    zero because my manual is silent on them; that is a fact about my manual.
# 2. ACTION1, then ACTION1 AGAIN. The first press is cheap confirmation of the
#    truncation fix and is fully predicted; the second is the only command
#    that splits exchange from scroll and it tests an 18-rule forged silence
#    at the same time. Two commands, two distinct purchases, no waste.
# 3. ACTION2, HERE, IN W0. Tests a zero-witness silence covering 18 rules. If
#    it exchanges, the toggle is key-symmetric and 18 rules generalise free.
# 4. ACTION4 A SECOND TIME, once the readout is lit. The only way to split
#    "key 4 advances the meter" from "lighting the readout advances it".
#    Costs a meter cell; read the answer off the RAW DIFF, since the
#    divergence lands on (53,62) which I cannot draw either way.
#
# WHAT NOT TO PRESS
#   ACTION3 or ACTION7 here: the pattern they erase is already erased, my
#   manual predicts identity AND I believe it. Confirmed silence, no witness.
#   Anything chosen because my manual predicts the most pixels for it: that
#   number measures my coverage, not the world's information.

order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition         [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     spend_one_predicted_command_to_reach_a_state_that_splits_two_readings [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation       [proof: lean]
order     fit_a_separator_to_a_refuted_cell_and_declare_the_fit_as_a_fit    [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     search_the_engine_report_for_a_count_that_matches_the_divergence  [proof: lean]
order     prefer_a_positive_colour_test_over_a_negated_wall_test            [proof: lean]
order     replace_a_manual_about_another_world_rather_than_patching_it      [proof: lean]
order     patch_a_manual_whose_divergence_is_four_cells_rather_than_replacing_it [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language    [proof: lean]
order     spend_a_monotone_counter_only_on_a_question_it_actually_closes    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead               [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead     [proof: lean]
prune     divergence_lies_only_on_the_unadvanced_meter_frontier => dead     [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key_in_this_configuration => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     advances_the_meter_and_closes_no_open_question => dead            [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic fitted_guards_a_command_could_convert_into_witnessed_ones         [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                   [admissible: lean]

prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 2/5 pressed keys]
prefer    a_command_that_decides_between_two_named_readings                 [ev: 1/1 available]
prefer    a_command_that_tests_eighteen_rules_at_once                       [ev: 2/2 available]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 1/6 states]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 5/5 diffs]
prefer    a_free_probe_over_one_that_advances_the_meter                     [ev: 1/5 commands advanced it]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 2/6 states are W1 or W0-with-pattern]
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
    34,
    13
   ],
   "manual_says": 0,
   "world_says": 3
  },
  {
   "cell": [
    34,
    14
   ],
   "manual_says": 0,
   "world_says": 3
  },
  {
   "cell": [
    35,
    13
   ],
   "manual_says": 6,
   "world_says": 3
  },
  {
   "cell": [
    35,
    14
   ],
   "manual_says": 6,
   "world_says": 3
  }
 ],
 "cells_wrong": 4,
 "kind": "frame_mismatch",
 "t": 1
}
```

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "d285637413abf223",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 57 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted 'fc2f046441e6c00d' against the world's 'a2785e8b6038ce0d'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 1.907 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 1,
 "expected_bits": 1.907136069469,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "fc2f046441e6c00d",
 "n_hypotheses": 57,
 "n_survivors": 0,
 "observed": "a2785e8b6038ce0d",
 "probe_id": "P-01",
 "vacuous_streak": 1
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 57 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '7f63731228e1e9ee' against the world's '05615f3d5f835100'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 1.830 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 2,
 "expected_bits": 1.829889174569,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "7f63731228e1e9ee",
 "n_hypotheses": 57,
 "n_survivors": 0,
 "observed": "05615f3d5f835100",
 "probe_id": "P-02",
 "vacuous_streak": 2
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 57 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '4670d1018e63606a' against the world's '19dfac07f1519c71'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 1.798 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 1,
 "expected_bits": 1.798345181232,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "4670d1018e63606a",
 "n_hypotheses": 57,
 "n_survivors": 0,
 "observed": "19dfac07f1519c71",
 "probe_id": "P-03",
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
 "first_divergence": {
  "arc_action": "ACTION2",
  "cells": [
   {
    "cell": [
     34,
     13
    ],
    "manual_says": 0,
    "world_says": 3
   },
   {
    "cell": [
     34,
     14
    ],
    "manual_says": 0,
    "world_says": 3
   },
   {
    "cell": [
     35,
     13
    ],
    "manual_says": 6,
    "world_says": 3
   },
   {
    "cell": [
     35,
     14
    ],
    "manual_says": 6,
    "world_says": 3
   }
  ],
  "cells_wrong": 4,
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
predicted silent, and whichever is pressed will produce the largest single addition to this manual available. THE METER: no tick at action 10 or 11, and a tick at (53,61) on action 12. If the meter moves on action 10 the period-4 reading is dead in one command."
    [depends: the_silences_i_assert_and_which_of_them_are_forged, there_is_still_no_goal_and_here_is_the_arithmetic  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: ten states, nine transitions. Widget in W1 -- hollow colour-6 box in
# the TOP slot, four-row bar glyph in the BOTTOM slot. BOTH readouts blank.
# Meter: (53,63) advanced at action 4, (53,62) at action 8, both now 3.
# 98 cells have ever changed; responsibility reports 0 unexplained in 4096.
#
# WHAT CHANGED THIS ROUND
#   The four-cell divergence was in ACTION2, not ACTION1. The slot does not
#   exchange pixels, it is SET: key(1) sets W1, key(2) sets W0. That made the
#   key(2) half of the manual nine rules instead of eighteen and fixed all four
#   cells with no separator. One bug at t2 corrupted the reconstructed state and
#   caused all three vacuous probes at t6, t7, t8 -- 0.0 bits realised against
#   5.5 expected. The truncation separators are re-anchored on row 42, which is
#   permanent background, precisely so a future state error cannot flip them.
#   ACTION1 did NOT stop advancing the meter: ACTION4 advanced it at action 4,
#   ACTION1 at action 8, and ACTION1 at action 6 did not. The meter runs on a
#   command counter and no guard over the frame can see it.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in ten states. Zero constraint.
#   * ACTION1 in W1: never pressed. Twenty rules and the structural reading of
#     the slot ride on a silence with no witness. WE ARE STANDING IN W1.
#   * ACTION2 in W0: never pressed; predicted identity on zero witnesses.
#   * The readout exchange with a LIT source: half witnessed, and I disbelieve
#     my own prediction there. One command from here.
#   * The win condition. All seven distinct states so far are NOT_FINISHED.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * Replay is expected 8/9. The one failure is t8, one cell, (53,62).
#   * Every meter tick costs exactly one pixel, permanently, because the tip's
#     next cell is board until the transition that moves it.
#   * Next tick predicted at action 12, on (53,61). No tick at action 10 or 11.
#
# THE GOAL, AND WHY I AM STILL REFUSING TO WRITE ONE
#   The heuristic_miss is correct on its facts: with no goal section is_goal is
#   False everywhere, plan never returns sat, commit never runs, and every
#   action is a probe. I decline anyway, and the reason is arithmetic, not
#   taste. The goal language reaches only declared instances, which are exactly
#   the 98 cells that have ever varied. Those cells have shown SEVEN distinct
#   configurations and the world returned NOT_FINISHED for all seven. So every
#   goal I could write today is either false at a board I have already lost in,
#   or is a configuration I have never seen and have no evidence names a win.
#   A wrong goal does not merely fail; it makes the plan tier report success and
#   spend the action budget defending it. The refusal is temporary and it has a
#   named exit: item 3 below manufactures a configuration no state has shown,
#   and if any state ever returns something other than NOT_FINISHED the goal
#   line gets written in that same round.
#
# THE RANKED LIST
# 1. ACTION1, NOW. We are in W1 for the first time with a free command. One
#    press splits three readings that no observation has ever separated --
#    toggle (returns W0), list (a third configuration), clamped selector
#    (genuine inertness) -- and tests the largest forged silence in the file,
#    twenty rules, at the same time. It was ranked second last round only
#    because reaching W1 cost a command. It does not now.
# 2. ACTION5 or ACTION6. Never pressed in ten states. Any outcome is the
#    largest single addition available, including "nothing", which would be a
#    witnessed inertness. Ranked below item 1 only because item 1 is free,
#    decisive between three named readings, and expires when we leave W1.
# 3. ACTION4, then ACTION1, then ACTION4. Manufactures BOTH READOUTS LIT, a
#    configuration no state has shown, which is the only win candidate I have
#    and simultaneously closes the half-witnessed readout exchange. Costs three
#    actions and crosses the action-12 meter tick, which is itself a prediction
#    being read for free.
# 4. ACTION2 from W0. Tests a zero-witness prediction of identity. Cheap, but
#    it buys less than item 1 buys and item 1 must come first anyway.
#
# WHAT NOT TO PRESS
#   ACTION3 or ACTION7 here: t9 already showed the entailed silence. Repeating
#   it is the cheapest way to learn nothing.
#   Anything chosen because the manual predicts the most pixels for it: that
#   number measures my coverage, not the world's information.

order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     take_a_decisive_probe_that_expires_when_the_state_changes_first   [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     manufacture_a_configuration_no_state_has_shown_before_guessing_a_goal [proof: lean]
order     refuse_a_goal_that_is_false_at_an_already_visited_losing_state    [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     anchor_a_fitted_separator_on_a_cell_the_transition_cannot_rewrite [proof: lean]
order     trace_every_vacuous_probe_back_to_the_earliest_wrong_transition   [proof: lean]
order     fix_the_reverse_direction_whenever_the_forward_one_needed_a_fit   [proof: lean]
order     collapse_rules_whose_target_equals_the_instance_type_colour       [proof: lean]
order     declare_a_mechanism_refuted_by_a_state_pair_no_guard_can_separate [proof: lean]
order     keep_an_admitted_fit_over_a_silent_hole_and_name_it_as_a_fit      [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation       [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     search_the_engine_report_for_a_count_that_matches_the_divergence  [proof: lean]
order     patch_a_manual_whose_divergence_is_four_cells_rather_than_replacing_it [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     separator_that_reads_a_cell_the_same_transition_rewrites => dead  [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead               [proof: lean]
prune     goal_true_at_any_state_the_world_returned_not_finished => dead    [proof: lean]
prune     goal_satisfiable_without_leaving_the_seven_observed_states => dead [proof: lean]
prune     divergence_lies_only_on_the_unadvanced_meter_frontier => dead     [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key_in_this_configuration => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     rule_keyed_on_a_counter_the_guard_language_cannot_express => dead [proof: lean]
prune     leaves_the_configuration_that_a_decisive_probe_requires => dead   [proof: lean]

heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic readout_configurations_never_yet_observed                         [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic fitted_guards_a_command_could_convert_into_witnessed_ones         [admissible: lean]
heuristic actions_remaining_before_the_next_predicted_meter_tick            [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                   [admissible: lean]

prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 2/5 pressed keys]
prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_command_that_decides_between_three_named_readings               [ev: 1/1 available]
prefer    a_command_that_tests_twenty_rules_at_once                         [ev: 1/1 available]
prefer    a_probe_available_only_from_the_configuration_now_showing         [ev: 1/10 states are W1_with_a_free_command]
prefer    a_sequence_that_produces_a_readout_state_never_observed           [ev: 0/10 states have both readouts lit]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 9/9 diffs]
prefer    a_free_probe_over_one_that_advances_the_meter                     [ev: 2/9 commands advanced it]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "seven colour types over the 98 dynamic cells", "verdict": "accept",
   "as": "Field/BarBody/BarCore/Blank/Frame/Hollow/Dot",
   "why": "their censuses sum to 98 = dynamic_cells, 4096-98 = 3998 = constant_cells, and 98 minus the 24 background-coloured cells = 74 = cells_needing_an_owner, three independent numbers from the brief that no wrong partition satisfies."},
  {"id": "O-02", "subject": "(53,62) newly dynamic at t8", "verdict": "accept",
   "as": "an eleventh BarCore instance",
   "why": "the t8 diff spans cols 11-62 where t1 and t6 spanned 11-22, dynamic_cells rose 97 to 98, and the current frame shows row 53 ending 3,3; its frame-0 colour is 2 so the arm can only seat it as BarCore."},
  {"id": "O-03", "subject": "mdl_segmenter obj0..obj6", "verdict": "reject",
   "why": "both variants report negative gain (-7528 and -7968 bits) so the engine compressed nothing by its own measure, and its 13x36 blobs merge the static colour-4 panel with the widget."},
  {"id": "O-04", "subject": "mdl_segmenter cell counts 440/436/440", "verdict": "accept",
   "as": "external corroboration of the four-cell truncation",
   "why": "the frame-1 blob is exactly four cells smaller than the frame-0 and frame-2 blobs, which is the bar's missing bottom two rows arrived at without any of my rules."},
  {"id": "R-01", "subject": "k2 slot rules, unguarded restore to type colour", "verdict": "accept",
   "why": "an instance's type is its frame-0 colour and frame 0 is W0, so 'key(2) sets W0' is one line per type; it fixes all four divergent cells at t2, replays t7's 72-cell diff, and replaces eighteen rules with nine."},
  {"id": "R-02", "subject": "k2_bar_from_frame and k2_bar_from_hollow", "verdict": "reject",
   "why": "they were the divergence: they demand colour 3 six rows below, which is background for (34,13),(34,14),(35,13),(35,14), so they could never restore the bar's bottom two rows."},
  {"id": "R-03", "subject": "truncation separators re-anchored on row 42", "verdict": "accept",
   "why": "the old above(above(...)) separators read cells the same transition rewrites, which is why a four-cell error at t2 turned into three vacuous probes; row 42 is background in all ten states and splits both pairs 2/2 exactly."},
  {"id": "R-04", "subject": "meter_tip_advance_fitted (was k4_meter_advances)", "verdict": "probe-pending",
   "why": "ACTION1 advanced (53,62) at t8 from a frame identical to t6's, which advanced nothing, so key(4) is not the cause; kept because it is correct at t4, is now permanently dead, and deleting it would cost two replay transitions instead of one."},
  {"id": "R-05", "subject": "key(2) rules carrying a LIT readout upward", "verdict": "probe-pending",
   "why": "key(2) has only ever been pressed with the bottom readout blank, so the rules exist only as a theorem; I disbelieve my own predicted identity there and one command closes it."},
  {"id": "R-06", "subject": "cegis_miner's refusal of all seven tracks", "verdict": "accept",
   "as": "a negative result",
   "why": "no instance's pos changes in ten states; every rule in this world is a recolour, which is why no goal of the form pos = landmark is writable at any length."},
  {"id": "L-01", "subject": "meter ticks on action 4 and action 8, period 4", "verdict": "probe-pending",
   "why": "two witnesses fit period 4 and predict no tick at action 10 or 11 and a tick at (53,61) on action 12; row 53 being 64 cells wide reads as a budget of about 256 actions."},
  {"id": "L-02", "subject": "zero_space's single global law", "verdict": "reject",
   "why": "its own evidence_adequacy says THIN -- 9 transitions constrain rank 5 of 686 features, null space 681 -- so the law is unfalsified rather than confirmed; I take only its cell list, which corroborates the census including (53,62)."},
  {"id": "L-03", "subject": "the slot exchanges pixels", "verdict": "reject",
   "why": "ACTION2 produced 3,3,3,3 at rows 34-35 out of an image holding 0,0 and 6,6 with background six rows below; no copy of any offset does that, so key(1) and key(2) SET configurations rather than trading them."},
  {"id": "P-01", "subject": "ACTION1 from W1, now", "verdict": "probe-pending",
   "why": "three legible outcomes -- W0, a third configuration, or genuine inertness -- separating toggle, list and clamped selector, while testing a twenty-rule silence with no witness; it is free and it expires the moment we leave W1."},
  {"id": "P-02", "subject": "ACTION5 or ACTION6", "verdict": "probe-pending",
   "why": "never pressed in ten states, so any outcome including inertness is the largest single addition available; ranked below P-01 only because P-01 is state-bound and P-02 is not."},
  {"id": "P-03", "subject": "ACTION4, ACTION1, ACTION4 to light both readouts", "verdict": "probe-pending",
   "why": "produces a configuration none of the seven distinct states has shown, which is the only win candidate I have, and closes the half-witnessed readout exchange on the way."},
  {"id": "E-01", "subject": "a command counter in a guard", "verdict": "reject",
   "why": "t6 and t8 are the same action from frames identical in all 4096 cells with opposite meter outcomes, so the driver is outside the frame; I wanted 'when command_index mod 4 = 0' and wrote the_meter_is_a_command_counter theorem plus a one-pixel price instead."},
  {"id": "E-02", "subject": "a goal section", "verdict": "reject",
   "why": "the goal language reaches only the 98 varying cells, those have shown seven configurations and the world called all seven NOT_FINISHED, so every writable goal is either false at a lost board or is unevidenced; refusal is recorded in there_is_still_no_goal_and_here_is_the_arithmetic with a named exit condition."},
  {"id": "E-03", "subject": "a row test to separate mirror-image cells", "verdict": "reject",
   "why": "the guard language has no coordinate predicate, so (36,13) and (41,13) with identical four-neighbourhoods needed a fitted geometric separator; I wrote colored(below(?p), 0) against colored(below(?p), 5) anchored on permanent-background row 42 and declared it a fit, not a law."}
]
```
```
