# call-002-theorize-round1

model: `claude-opus-5` · 846016 ms · $2.791139 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 96644, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 96644, "cache_read_input_tokens": 32579, "inference_geo": "not_available", "input_tokens": 4, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 64065, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 64065, "cache_read_input_tokens": 32579, "input_tokens": 2, "output_tokens": 7360, "type": "message"}], "output_tokens": 71360, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 73,
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
 "constant_cells": 3999,
 "distinct_states": 5,
 "dynamic_box": [
  29,
  10,
  54,
  63
 ],
 "dynamic_cells": 97,
 "max_frames_in_one_command": 2,
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
 53 222222222222222222222222222222222222222222222222222223
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

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 5,
  "n_states": 6,
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
   "recolor": 4,
   "vanish": 2
  },
  "n_frames": 6,
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
    "frames_present": 6,
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
   }
  ],
  "variants": [
   {
    "baseline_bits": 3475,
    "compression_ratio": 2.161727,
    "events": 8,
    "gain_bits": -4037,
    "ms": 4,
    "script_bits": 7512,
    "split_by_color": false,
    "tracks": 4
   },
   {
    "baseline_bits": 3475,
    "compression_ratio": 3.995396,
    "events": 61,
    "gain_bits": -10409,
    "ms": 15,
    "script_bits": 13884,
    "split_by_color": true,
    "tracks": 33
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
   "dynamic_cells": 97,
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
  "cells_needing_an_owner": 73,
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
  "constant_cells": 3999,
  "distinct_states": 5,
  "dynamic_box": [
   29,
   10,
   54,
   63
  ],
  "dynamic_cells": 97,
  "max_frames_in_one_command": 2,
  "shape": [
   64,
   64
  ],
  "states": 6,
  "steps": 6
 },
 "window": {
  "box": [
   29,
   10,
   54,
   63
  ],
  "covered": 1.0,
  "dynamic_cells": 97,
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
  "cells_dynamic": 97,
  "cells_used": 97,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c3",
   "c4",
   "c5",
   "c6"
  ],
  "difference_rank": 3,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.004418,
   "difference_rank": 3,
   "features": 679,
   "space_dimension": 676,
   "transitions": 5,
   "verdict": "THIN: 5 transitions constrain rank 3 of 679 features, so the null space has dimension 676 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 679,
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
     "c1@43",
     "c2@43",
     "c3@43",
   
```

The full proposal stream is 680 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- REWRITTEN FROM ZERO. World observed for 6 states / 5 transitions
# (RESET, then ACTION1 ACTION2 ACTION3 ACTION4 ACTION7, one press each).
#
# WHY THERE IS NOTHING LEFT OF THE PREVIOUS MANUAL
#
#   Two separate failures, and only one of them is a bug.
#
#   (1) THE SURPRISE THAT CALLED ME: `theory.dsl is non-empty but
#       generated/theory.py could not be loaded`. Nothing replayed, nothing
#       was checked, responsibility and ambiguity both reported empty. The
#       previous manual carried the line
#           landmark spawn_probe  # arc-cell: carried, coordinates stripped
#       and the grammar says in as many words that a landmark the level
#       cannot place is a HARD COMPILE ERROR. `carried, coordinates
#       stripped` is not `(row, col)`. Thirteen rules depended on that
#       landmark and the whole file died with it. THIS MANUAL DECLARES NO
#       LANDMARK AT ALL. Not as caution -- I have no rule that needs one,
#       and the cheapest way never to repeat that error is to have nothing
#       to get wrong.
#
#   (2) THE WORLD IS NOT THE SAME WORLD. The store says 6 states, 6 steps,
#       5 transitions, dynamic box rows 29-54 cols 10-63, 97 dynamic cells,
#       3999 constant, colours {0,1,2,3,4,5,6,8,9,14}, actions used
#       1,2,3,4,7. The previous manual described 34 states, a dynamic box
#       at rows 8-18 and row 63, 87 dynamic cells, 4009 constant, a five-key
#       alphabet with ACTION5 in it and ACTION7 never pressed, a 6-pixel
#       lattice, a comb, a socket at rows 50-54 cols 44-48. In the CURRENT
#       frame rows 50-54 cols 44-48 read plain 5,5,5,5 and 4 -- there is no
#       socket, no bracket, no colour-8 wire anywhere in the window, and
#       colour 14 exists here and existed nowhere there. Not one census
#       number matches. That manual is not stale, it is about somewhere
#       else, and AMENDING IT WOULD BE A LIE ABOUT WHAT I HAVE SEEN. Every
#       one of its thirty theorems is discarded together with its evidence
#       tags, because an ev: tag naming t29 in a world that has had five
#       transitions witnesses nothing.
#
#   WHAT I CARRY ACROSS IS METHOD AND NOT CONTENT: type by frame-0 colour,
#   check the census closes to the cell before believing a segmentation,
#   price the undrawable leading edge in advance, and never write a rule
#   for a transition whose pixels I have not been shown.
#
# WHAT THIS MANUAL CAN AND CANNOT DRAW, STATED BEFORE ANYONE REPLAYS IT
#
#   t3, t4, t5 are itemised cell by cell in the command log and this manual
#   reproduces all 25 of those recolours exactly. t1 and t2 are reported
#   ONLY as `96 cells changed, rows 30-41, cols 11-22` with a before/after
#   colour multiset -- no cell list, no per-cell colours. I therefore have
#   NO rule for ACTION1 and NO rule for ACTION2, my compiled step returns
#   identity for both, and replay WILL diverge by up to 96 cells at t1 and
#   again at t2. Expect replay 3/5. That is not a defect I can repair from
#   the evidence I was handed; it is repaired by pressing ACTION1 once and
#   reading the next full frame against this one. See
#   the_ninety_six_cell_hole_and_how_it_closes.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Ink1   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Ink2   { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Ink3   { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object Dark   { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Frame6 { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  object Field  { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Ground { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  Ink1   [segment: frame0_colour_1 ev: t3,t4,t5 compress: 9]
  Ink2   [segment: frame0_colour_2 ev: t3,t4,t5 compress: 10]
  Ink3   [segment: frame0_colour_3 ev: t1,t2 compress: 8]
  Dark   [segment: frame0_colour_0 ev: t1,t2 compress: 12]
  Frame6 [segment: frame0_colour_6 ev: t1,t2 compress: 22]
  Field  [segment: frame0_colour_4 ev: t1,t2 compress: 12]
  Ground [segment: frame0_colour_5 ev: t1,t2 compress: 24]

rules:
  rule key3_strip_blanks_ink1 forall ?p in Ink1 [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key3_strip_blanks_ink2 forall ?p in Ink2 [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key7_strip_blanks_ink1 forall ?p in Ink1 [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key7_strip_blanks_ink2 forall ?p in Ink2 [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key4_strip_restores_ink1 forall ?p in Ink1 [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_strip_restores_ink2 forall ?p in Ink2 [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_meter_burns_right_end forall ?p in Ink2 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

laws:
  invariant ink1_instances   count(Ink1) = 9      [status: counted]
  invariant ink2_instances   count(Ink2) = 10     [status: counted]
  invariant ink3_instances   count(Ink3) = 8      [status: counted]
  invariant dark_instances   count(Dark) = 12     [status: counted]
  invariant frame6_instances count(Frame6) = 22   [status: counted]
  invariant field_instances  count(Field) = 12    [status: counted]
  invariant ground_instances count(Ground) = 24   [status: counted]
  invariant board_cells      count(board) = 3999  [status: counted]

  theorem the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout "This is the load-bearing arithmetic of the whole manual and it closes with no slack, which is the only reason I trust a reconstruction built from bounding boxes. The diffs give a dynamic set of exactly two pieces: the 96 cells inside rows 30-41 x cols 11-22 that ACTION1 moved, and the single cell (53,63) that ACTION4 burned. 96 + 1 = 97 = dynamic_cells, and the 12 cells ACTION3 and ACTION7 touch lie inside the 12x12 box, so they add nothing. Now read the CURRENT frame inside that box and sort by colour. Colour 5 appears at rows 30-35 cols 11,12,15,16 and nowhere else in the box: 6 rows x 4 columns = 24 cells. 97 - 24 = 73 = cells_needing_an_owner EXACTLY, which is the store's own count of dynamic cells that are not background. That is not a coincidence I arranged; it is the store agreeing, from a number I did not compute, that my 24 background cells are the right 24. The remaining 73 sort as: 8 colour-3 (cols 13-14 at rows 30,31,34,35), 4 colour-2 (cols 13-14 at rows 32,33), 22 colour-6 and 12 colour-0 (the 6x6 token at rows 36-41 cols 11-16, whose border is 6 except that (38,16) reads 1 and (39,16) reads 2, whose interior is 0 except a 2x2 colour-6 core at rows 38-39 cols 13-14), 8 colour-1 and 4 colour-2 (the strip at rows 38-39 cols 17-22), 1 colour-1 at (38,16), 1 colour-2 at (39,16), 1 colour-2 at (53,63), and 12 colour-4 cells somewhere in rows 30-41 cols 17-22 that no diff itemises. 8+4+22+12+8+4+1+1+1+12 = 73. 4096 - 97 = 3999 = constant_cells. Three independent numbers from the store, all hit on the nose."
    [probe: passed]

  theorem the_twelve_unlocated_field_cells_are_real_and_i_do_not_need_their_addresses "The census above forces exactly 12 dynamic cells of frame-0 colour 4 into rows 30-41 cols 17-22, and no diff tells me which. This does not block the manual, because the arm locates instances BY COLOUR from the frames rather than from anything I write: `arc-instances: all` on Field seats one instance per colour-4 cell the board cannot explain, and the board explains every constant colour-4 cell in the huge field at cols 17-46 and in row 54. So Field gets those 12 and only those 12, wherever they are. What I lose is the ability to write a rule ABOUT them, which costs nothing today because the only transitions that move them are t1 and t2, for which I have no rule at all. My guess -- and I mark it a guess -- is rows 36-37 cols 17-22, i.e. the strip drawn two rows higher, because that is the one 2x6 block adjacent to the strip and because it would make ACTION1 a two-row shift of the strip rather than a repaint. If the next ACTION1 frame shows the strip at rows 36-37 the guess was right and the rule writes itself; if it shows something else I lose nothing but the guess."
    [depends: the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout  probe: pending]

  theorem action2_undoes_action1_and_the_store_proves_it_without_showing_me_a_pixel "distinct_states is 5 against 6 states, so among s0..s5 there is EXACTLY ONE coinciding pair. Enumerate the candidates. s2 -> s3 changed 12 cells, s3 -> s4 changed 13, s4 -> s5 changed 12, so s2,s3,s4,s5 are pairwise distinct except possibly s2 vs s5 -- and those differ at (53,63), 2 against 3, and at the strip, so no. s0 -> s1 and s1 -> s2 each changed 96 cells in the SAME box with the SAME colour multiset going in as coming out. The only pair left that can coincide is s0 and s2, so s0 = s2, and therefore ACTION2 EXACTLY UNDOES ACTION1 on this state. That is a real fact derived from one integer, and it is worth stating because it tells me the pair is a toggle or a two-way selector rather than a one-way commitment, so pressing ACTION1 to learn its pixels is REVERSIBLE and cannot strand me. It does NOT tell me what either key does, and I refuse to invent one: a 96-cell change whose colour multiset is preserved is equally consistent with a shift, a rotation, a swap of two sub-pictures, or a repaint, and I have seen zero of the pixels."
    [depends: the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout  probe: passed]

  theorem the_ninety_six_cell_hole_and_how_it_closes "The largest defect in this manual, named before certify names it. My compiled step is total, so where no rule fires it says `nothing happens` in the same voice it uses for things it has seen -- and for ACTION1 and ACTION2 it will say `nothing happens` while the world moves 96 cells. That silence is FORGED and it is the worst kind, because I know it is false rather than merely unwitnessed. I will not repair it by guessing, because a wrong 96-cell rule is worse than no rule: it would fire on future states, cascade into the strip rules, and it would be unfalsifiable-looking rather than obviously absent. THE REPAIR IS ONE COMMAND. The evidence brief hands me the full current frame every round, and the diff channel only itemises small changes -- 12 and 13 cells were itemised, 96 was summarised to a bounding box. So the pixels of ACTION1 are unreachable through the diff and reachable through the FRAME: press ACTION1, receive the resulting frame next round, subtract it from the frame I hold now, and the 96 cells are mine cell by cell. This is the single highest-value command on the board and the playbook ranks it first."
    [depends: action2_undoes_action1_and_the_store_proves_it_without_showing_me_a_pixel  probe: pending]

  theorem action3_and_action7_have_the_same_net_effect_and_action4_inverts_it "The three transitions I can actually see. t3 (ACTION3) recoloured all twelve cells of rows 38-39 cols 17-22 to colour 4. t5 (ACTION7) recoloured the same twelve cells to colour 4 again, from the same starting pattern, cell for cell identical to t3's list. t4 (ACTION4) recoloured those twelve back and burned one more cell. So on this state ACTION3 and ACTION7 are indistinguishable in net effect, 12/12 each, and ACTION4 is their inverse plus a side effect. The restored pattern is row 38 = 2,1,1,2,1,1 and row 39 = 1,1,2,1,1,2 across cols 17-22, which is a period-3 stripe: row 39 equals row 38 shifted one column left, so the 2s lie on a diagonal of slope one. This is why my two restore rules can be written without a single positional guard -- the arm types each instance by its FRAME-0 colour, so `recolour every Ink1 that currently reads 4 back to 1, and every Ink2 that currently reads 4 back to 2` reproduces the diagonal exactly, at no cost in rule length, and the pattern is carried by the type assignment rather than by anything I had to describe. That is the one place in this manual where a concept genuinely pays: two rules and no coordinates for twelve cells of structured pattern."
    [depends: the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout  probe: passed]

  theorem the_strip_guard_is_forced_and_i_checked_every_rival_instance "The blank rules must fire on the twelve strip cells and on NO other Ink1 or Ink2 instance, and the guard I use is `colored(above(above(?p)), 4)`. Here is the check, instance by instance, in the pre-blank state. Row-38 strip cells: two above is row 36 cols 17-22, which reads 4. Row-39 strip cells: two above is row 37 cols 17-22, which reads 4. Both pass. Now the rivals. (38,16) is Ink1: two above is (36,16), which reads 6 -- fails. (39,16) is Ink2: two above is (37,16), 6 -- fails. The four bar cells at rows 32-33 cols 13-14 are Ink2: two above is rows 30-31 cols 13-14, which read 3 -- fails. (53,63) is Ink2: two above is (51,63), which reads 5 -- fails. Every rival is excluded and every target is included, so coverage is 8/8 and 4/4 with no leakage. I considered and REJECTED the shorter guards: `colored(above(?p), 4)` catches only row 38 and needs a second rule for row 39, and `colored(below(?p), 4)` catches row 39 but ALSO catches (53,63), because row 54 is solid colour 4 from edge to edge -- that near miss is exactly the kind that would have cost a round, and it is why I checked all ten Ink2 instances rather than the obvious four."
    [depends: action3_and_action7_have_the_same_net_effect_and_action4_inverts_it  probe: passed]

  theorem the_seven_rules_cannot_clash_and_here_is_the_case_analysis "Constraint 5 demands exactly one successor per state and action, so pairwise exclusivity is checked rather than assumed. The seven rules partition first by action: {key3_strip_blanks_ink1, key3_strip_blanks_ink2} on key 3, {key7_strip_blanks_ink1, key7_strip_blanks_ink2} on key 7, {key4_strip_restores_ink1, key4_strip_restores_ink2, key4_meter_burns_right_end} on key 4. Across groups no clash is possible. Inside the key-3 and key-7 groups the two rules quantify over DISJOINT instance sets, Ink1 and Ink2, so no instance is ever claimed twice. Inside the key-4 group, key4_strip_restores_ink1 is over Ink1 and the other two are over Ink2; those two are separated by their colour test, `colored(?p, 4)` against `colored(?p, 2)`, which cannot both hold of one cell in one state. Zero clashes by construction, and no rule anywhere in this manual uses `not`, so there is no negation whose scope I could have got wrong."
    [depends: the_strip_guard_is_forced_and_i_checked_every_rival_instance  probe: passed]

  theorem the_row_53_burn_has_exactly_one_witness_and_three_live_readings "At t4, and only at t4, (53,63) went 2 to 3. Row 53 reads solid colour 2 from col 10 to col 62 with col 63 now 3, and it is the only row in the frame with that colouring, so I read it as a bar consumed one cell at a time from the right end -- but I have ONE burn in five transitions and I will not pretend that is a law. THREE READINGS ARE ALIVE. (A) The burn is keyed to ACTION4: my rule encodes this because it is the only reading that fires exactly once in the observed history and never elsewhere. (B) The burn is keyed to the RESTORE event rather than the key, so any action that repaints the strip burns. (C) The burn counts something the frame does not show -- a command counter, an attempt counter -- in which case no guard in this language can express it, exactly as the previous world's meter could not be expressed. Note what SEPARATES them cheaply: t2 was also an even-index command and did NOT burn, which kills plain index parity outright; and pressing ACTION4 now, when the strip is already blank so nothing is there to restore, splits (A) from (B) in a single press -- (A) predicts nothing, since (53,63) already reads 3 and my rule needs colour 2, while (B) predicts nothing either. The honest separator is ACTION4 pressed twice with a restore in between, which is two commands and not one, so I rank it below the ninety-six-cell hole."
    [depends: action3_and_action7_have_the_same_net_effect_and_action4_inverts_it  probe: pending]

  theorem the_next_burn_is_undrawable_and_i_price_it_now_rather_than_be_surprised "If row 53 really is a bar consumed from the right, the next cell to go is (53,62), and (53,62) HAS NEVER CHANGED. The arm seats instances only on cells the board cannot explain, a never-varying cell is precisely what the board explains, so (53,62) gets no instance, no object owns it, and NO RULE I CAN WRITE WILL DRAW ITS FIRST CHANGE. This is a property of the arm, not of my rules, and it is permanent for this level: every burn costs me exactly one wrong pixel on the transition where it happens and zero thereafter, because the cell becomes dynamic the moment it changes and my Ink2 type picks it up on the next instancing. I reject the two tempting repairs in advance. Declaring a second colour-2 type without arc-instances seats one instance at an unspecified cell that Ink2 may also claim, which is the double claim constraint 5 forbids. Declaring a landmark does not help, because every event in this language takes an object as its first argument and a landmark is a cell. So: when a refutation's divergence set is the single cell immediately left of the burned end of row 53, the manual is not implicated, and it must not be read as one."
    [depends: the_row_53_burn_has_exactly_one_witness_and_three_live_readings  probe: passed]

  theorem two_keys_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1, ACTION2, ACTION3, ACTION4, ACTION7 plus RESET; the alphabet is ACTION1..ACTION7. ACTION5 and ACTION6 are entirely unconstrained after six states, and in this action family one of the higher indices is normally a click carrying coordinates. That the world already answers to ACTION7 is itself informative -- the previous world in this series never used it and this one does, on its fifth command -- so nothing about which indices are `the movement keys` transfers. I cannot write a click rule: the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT and never its precondition. Until one of these keys is pressed my manual predicts silence for both, and that silence is unwitnessed -- a forged death certificate, not a finding."
    [probe: pending]

  theorem what_the_frame_shows_that_no_rule_of_mine_touches "Stated so that the parts of the picture I have not explained are visible rather than absent. FIRST, the 6x6 token at rows 36-41 cols 11-16: a colour-6 border, a colour-0 interior, a 2x2 colour-6 core at rows 38-39 cols 13-14, and two border cells that are NOT 6 -- (38,16) reads 1 and (39,16) reads 2, in the same two rows as the strip and immediately to its left. That alignment says the token and the strip are one widget read left to right, and the 1 and the 2 at col 16 look like the first two entries of the same sequence the strip continues; but they did not blank at t3, t5 or restore at t4, so whatever they are, they are not part of what ACTION3 and ACTION4 toggle. SECOND, the vertical bar at cols 13-14 rows 29-35: colour 3 except rows 32-33, which are colour 2. It sits directly above the token, two cells wide, with a two-row colour-2 marker a third of the way down -- the shape of a slider or a gauge. It is entirely inside the ACTION1 box, so ACTION1 or ACTION2 almost certainly moves that marker, and that is the single most likely meaning of the 96 cells. THIRD, the colour-14 block at rows 31-34 cols 42-45 and everything of colours 8 and 9 elsewhere in the frame: constant in all six frames, therefore board, therefore unowned and undrawable if they ever move. I name all three rather than model them."
    [depends: the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout  probe: pending]

  theorem the_goal_section_is_absent_on_purpose_and_it_costs_me_a_planner "There is no goal section, so is_goal compiles to False and no plan can terminate. I could have invented one and I decline, because a goal true in the wrong states is worse than no goal: it stops a planner at its first step and it is a claim about winning that six frames cannot support. Nothing in the history has shown a win, a score, or a state change other than NOT_FINISHED. The candidate predicates all fail on inspection. `count(Ink2, color = 3) = 1` is true right now, in a state that is plainly not a win. `count(Ink1, color = 4) = 8` is true in every blanked-strip state including the current one. There is no instance I could name for a positional goal because arc-instances: all yields Ink1_r38c18 and eight siblings rather than anything called Ink1. The price is explicit: nothing ranks one command above another except whether it is predicted to change pixels and what it would witness, so the playbook does the ranking and it does it on epistemic value, not on distance to a target."
    [depends: the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout  probe: passed]

  theorem the_cascade_channel_carries_one_bit_that_i_discard_by_construction "cascade_lengths are 1 and 2, and max_frames_in_one_command is 2. Four commands returned two frames -- t1, t2, t3, t4 -- and t5, the ACTION7, returned one. That is interesting precisely because t5's NET effect is identical to t3's, cell for cell: the same twelve cells to colour 4. So ACTION3 and ACTION7 differ in their animation and agree in their result, which is the only evidence I have that they are different commands at all rather than aliases. My semantics say cascade single_frame, which compares only the net, so I discard the intermediate frame of every two-frame command unread and my manual cannot distinguish ACTION3 from ACTION7 anywhere. I record this as a limitation of my own semantics rather than a fact about the world. LIVE PREDICTION, free to check: if ACTION7 is pressed again from a state with the strip showing, it should return ONE frame while ACTION3 returns two. If ACTION7 ever returns two, this is not a stable property of the key."
    [depends: action3_and_action7_have_the_same_net_effect_and_action4_inverts_it  probe: pending]

  theorem what_the_engines_gave_me_and_what_i_took "cegis_miner refused on all four tracks -- two for narrating vanish or recolor when it mines only move and none, two because the object is absent at frame 0 -- and its verdict, `the world does not narrate as one mover`, I ACCEPT as literally true here: nothing in six frames translates, everything recolours in place, and no object of mine has a pos that ever changes. That is a real finding and it is why this manual contains not one moved() event. mdl_segmenter reports NEGATIVE gain on both variants, -4037 bits with connected_components(4) and -10409 bits when split by colour, meaning its script costs more than writing the pixels out; by constraint 3 that segmentation has not earned its place and I take NO structure from it. Its four tracks are also unusable as they stand: obj0 and obj2 and obj3 are 13x36 blobs of 436-440 cells that have swallowed the whole colour-4 field along with everything embedded in it, and obj1 is a 2x54 strip present in all six frames, which is row 53 and row 54 fused. zero_space self-reports THIN in its own words -- 5 transitions constrain rank 3 of 679 features, null space dimension 676 -- and its single global law is a list of cells that is my dynamic set, so it corroborates the census and nothing else. Three engines, one accepted verdict, zero accepted structure."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body of this world, if it has one, is invisible to me; what I hold is a state where the strip at rows 38-39 cols 17-22 reads colour 4 and (53,63) reads colour 3. ACTION4: my manual predicts TWELVE cells, the strip restored to the 2,1,1,2,1,1 / 1,1,2,1,1,2 diagonal, and NO burn, because key4_meter_burns_right_end needs colour 2 at the right end and finds colour 3. If a burn happens anyway at (53,62) I cannot draw it and reading (C) of the burn theorem gains. ACTION3 and ACTION7: my manual predicts ZERO cells, since the strip is already 4 and both blank rules require colour 1 or 2. That silence is unwitnessed for both keys and I would believe it, but it buys almost nothing. ACTION1: my manual predicts ZERO cells and I KNOW that is false -- 96 cells will move and the resulting frame closes my largest hole. This is the press I want and the playbook says so. ACTION2: same 96 cells, but it returns to s0, a state I already hold, so it teaches strictly less than ACTION1. ACTION5 and ACTION6: my manual predicts zero cells with no witness whatever; either answer is new information and both are cheap. If ACTION1 is pressed and the frame comes back unchanged, then s5 is not s0-like in the way I assumed and this manual is wrong about more than its silences."
    [depends: the_ninety_six_cell_hole_and_how_it_closes, the_row_53_burn_has_exactly_one_witness_and_three_live_readings  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE SITUATION IN THREE LINES =========
# This is a NEW world, six states old. The previous manual described
# somewhere else entirely and also failed to compile, so nothing replayed
# and nothing was checked. Everything below is five transitions deep.
#
# ========= WHAT IS KNOWN =========
#   ACTION1 -> 96 cells in rows 30-41 cols 11-22. PIXELS NOT SHOWN.
#   ACTION2 -> exactly undoes ACTION1 (s0 = s2, forced by distinct_states=5).
#              PIXELS NOT SHOWN.
#   ACTION3 -> blanks the 12-cell strip at rows 38-39 cols 17-22 to colour 4.
#   ACTION7 -> the same 12 cells, same result, but in ONE frame not two.
#   ACTION4 -> restores the strip AND burned (53,63) from 2 to 3, once.
#   ACTION5, ACTION6 -> never pressed. Nothing is known about either.
#
# ========= WHAT THE MANUAL PREDICTS FROM HERE =========
#   Strip currently BLANK, (53,63) already burned to 3.
#     ACTION4 -> 12 cells (strip restored), no burn.
#     ACTION3, ACTION7 -> nothing, unwitnessed but believed.
#     ACTION1, ACTION2 -> nothing, AND THAT IS KNOWN TO BE FALSE.
#     ACTION5, ACTION6 -> nothing, with no witness of any kind.
#
# ========= THE ONE THING WORTH BUYING =========
# PRESS ACTION1.
#   The manual's largest defect is a forged silence over 96 cells, and it is
#   forged in the strongest sense: I know the world moves them and I have
#   never been shown which. The diff channel will not tell me -- it itemised
#   12 and 13 cells and summarised 96 to a bounding box -- but the FRAME
#   will, because every round hands me the current frame in full and I hold
#   this one. One press converts a 96-cell hole into a cell-by-cell diff.
#   It is also free of risk: ACTION2 provably restores the state exactly.
#   No other command on the board closes anything comparable.
#
# Ranked below it: ACTION5 or ACTION6, because two of seven keys have never
# been pressed and either answer -- motion or a witnessed silence -- is new.
# Ranked last: ACTION3 and ACTION7 from here, which my manual and the world
# probably agree do nothing, and re-pressing ACTION4 to chase the burn,
# which needs two commands to separate its readings and cannot be settled by
# one.
#
# The advertised price of ACTION1: my manual draws NONE of the 96 cells, so
# the refutation is guaranteed and it is 96 cells wide. That is priced here,
# in advance, and it must not be read as a defect discovered by certify.
#
# ------------------------------------------------------------------------
# STATE 5: strip blank; (53,63) burned; 97 dynamic cells all owned; 3999
# board. Seven rules, all of them witnessed, covering 25 of the 217 cell
# changes in history. The other 192 are t1 and t2 and I have not seen one
# of them.

order     buy_the_pixels_of_the_transition_i_have_never_been_shown        [proof: lean]
order     close_a_known_false_silence_before_testing_an_unwitnessed_one   [proof: lean]
order     press_a_key_that_has_never_been_pressed_before_repressing_one   [proof: lean]
order     prefer_a_reversible_probe_when_its_inverse_key_is_known         [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance              [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered   [proof: lean]
order     separate_two_live_readings_before_encoding_either_as_a_rule     [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it      [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead  [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead              [proof: lean]
prune     divergence_lies_only_on_the_burned_end_of_row_fiftythree => dead  [proof: lean]
prune     repeats_a_key_whose_effect_in_this_state_is_already_itemised => dead [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead   [proof: lean]
prune     needs_two_commands_when_a_one_command_probe_is_unspent => dead    [proof: lean]
prune     asserts_a_goal_no_frame_has_ever_shown => dead                    [proof: lean]
prune     carries_a_landmark_with_no_arc_cell_coordinate => dead            [proof: lean]

heuristic cells_the_manual_currently_draws_wrong_in_a_known_transition    [admissible: lean]
heuristic keys_whose_silence_here_rests_on_no_witness                     [admissible: lean]
heuristic keys_never_pressed_in_the_whole_history                         [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                    [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_row_fiftythree_edge        [admissible: lean]
heuristic frames_returned_per_command_as_a_free_side_channel              [admissible: lean]

prefer    the_key_whose_pixels_the_diff_channel_refused_to_itemise        [ev: 2/5 transitions]
prefer    a_probe_whose_result_arrives_as_a_full_frame_not_a_summary      [ev: 1/1 rounds]
prefer    an_unpressed_key_over_repeating_a_witnessed_effect              [ev: 2/7 keys]
prefer    a_probe_that_is_undone_by_a_key_already_known_to_undo_it        [ev: 1/1 pairs]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 3/5 diffs]
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
  "cap_reached": false,
  "clashes": [],
  "detail": "no (state, action) among 6 x 3 admitted two rules, and all 18 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 18,
  "pairs_nominal": 18,
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
=== THEORY (continued — the remainder of theory.dsl, appended to the block above) ===
```
                                                          do nothing while
the token is lifted. That prediction is almost certainly false: the obvious
generalisation is that these keys act on the strip wherever the strip is, and
it would be written as two Field rules with the same shape as the Ink1/Ink2
pair. I decline to write them because their coverage today is 0/0, and a rule
with no witness is exactly what constraint 2 forbids. One command settles it:
lift, then press ACTION3."
    [depends: every_rule_gates_itself_on_the_state_it_was_witnessed_in_and_no_landmark_was_needed  probe: pending]

  theorem the_row_53_burn_has_one_witness_and_three_live_readings "At t4 and only at t4, (53,63) went 2 to 3. Row 53 is a solid colour-2 bar from the left edge to col 62 with col 63 now 3, so I read it as a budget consumed one cell at a time from the right. One burn in five transitions is not a law. (A) The burn is keyed to ACTION4, which is what key4_burns_right_end encodes, being the only reading that fires exactly once in the observed history. (B) It is keyed to the restore EVENT rather than the key. (C) It counts something the frame does not show, in which case no guard here can express it. Cheap separators: t2 was also an even-indexed command and did not burn, which kills index parity; and from the current state ACTION4 restores the strip while (53,63) already reads 3, so (A) and (B) both predict no burn and a burn would be evidence for (C) directly."
    [depends: the_strip_rules_are_written_only_where_the_strip_has_been_seen  probe: pending]

  theorem the_next_burn_is_undrawable_and_i_price_it_now "If row 53 is consumed from the right, the next cell to go is (53,62), which has never changed. The arm seats instances only on cells the board cannot explain, and a never-varying cell is precisely what the board explains, so (53,62) has no instance and no rule of mine can draw its first change. This is a property of the arm, permanent for this level, and it costs exactly one wrong pixel on the transition where it happens and none afterwards, since the cell becomes dynamic and Ink2 picks it up. The two tempting repairs are both refused: a second colour-2 type without arc-instances lands one instance somewhere Ink2 may also claim, which is the double claim constraint 5 forbids, and a landmark cannot help because every event takes an object as its first argument. The same applies to the next rung of the rail at rows 24-29."
    [depends: the_row_53_burn_has_one_witness_and_three_live_readings  probe: passed]

  theorem two_keys_have_never_been_pressed "ACTION5 and ACTION6 are entirely unconstrained after six states; the alphabet is ACTION1..ACTION7 and this world already answers to ACTION7. My manual predicts silence for both and that silence rests on nothing whatever. I cannot write a click rule even if one of them is a click: the guard language admits act=key(6) but has nowhere to put two coordinates, so the rule would fire on every click anywhere and be silently wrong about which cell was hit. If a click drives this world I can record its effect and never its precondition."
    [probe: pending]

  theorem what_the_frame_shows_that_no_rule_of_mine_touches "Named so the unexplained parts are visible. FIRST, the colour-14 block at rows 31-34 cols 42-45, sitting inside the big colour-4 field that spans cols 17-46. It is constant in all six frames, therefore board, therefore undrawable if it ever moves. It is worth naming because the strip's lifted rows, 32-33, lie inside its row span 31-34: a 6-cell strip at cols 17-22 pointed along the same rows as a 4x4 block twenty columns to its right is the shape of a target and a thing aimed at it, and that is the only candidate for a winning condition this world has offered. SECOND, the two odd token-border cells (38,16)=1 and (39,16)=2, which ride with the token but neither blank at ACTION3 nor restore at ACTION4; they look like the first two entries of the sequence the strip continues, and they are not part of what those keys toggle. THIRD, everything of colours 8 and 9 outside the window, constant and unowned. I name all three rather than model them."
    [depends: the_refutation_was_the_probe_and_here_is_the_arithmetic_it_paid_for  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "No goal section, so is_goal compiles to False and no plan can terminate. Nothing in six frames has shown a win, a score, or a state other than NOT_FINISHED. The tempting predicate -- something about the strip reaching the colour-14 block -- cannot be written: the block is board, it has no instance, and arc-instances yields Field_r32c17 and eleven siblings rather than anything nameable. Inventing a goal true in the wrong states would stop a planner at its first step, which is worse than having none. The price is that nothing ranks one command above another except what it would witness, so the playbook ranks on epistemic value alone."
    [depends: what_the_frame_shows_that_no_rule_of_mine_touches  probe: passed]

  theorem what_the_engines_gave_me_and_what_i_took "cegis_miner refused all four tracks and its verdict, that the world does not narrate as one mover, I ACCEPT and then qualify: nothing translates in the sense the miner mines, but the widget does travel six rows, and it is invisible to a one-move-per-transition miner because 96 cells change at once and the DSL has no six-cell move. mdl_segmenter reports negative gain on both variants, -4037 and -10409 bits, so by constraint 3 its segmentation has not earned its place and I take no structure from it; its 13x36 blobs had swallowed the whole field. zero_space self-reports THIN in its own words, rank 3 of 679 features over 5 transitions, and its one global law is a list of cells identical to my dynamic set, so it corroborates the census and nothing else. Three engines, one accepted verdict, zero accepted structure. Every structural claim in this manual came from the certify divergence list and from counting."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. Current state: token at home, strip blank, (53,63) burned to 3. ACTION1 -- the widget lifts, 84 cells change rather than 96, because the twelve strip cells are already field colour and stay field colour at both ends of the swap; if 96 change I have misread the blank state. ACTION2 -- nothing, unwitnessed and probably false. ACTION3, ACTION7 -- nothing, since the strip is already blank; believed but worth almost nothing. ACTION4 -- twelve cells restored and NO burn, because key4_burns_right_end needs colour 2 at the right end and finds 3; a burn at (53,62) would be undrawable and would argue for reading (C). ACTION5, ACTION6 -- nothing, with no witness of any kind, and either answer is new. If replay now reports t1 and t2 exact, the block-swap reading and the slot-marker guess are both confirmed at 192 cells and this manual's only remaining holes are the unpressed keys and the untried rungs."
    [depends: which_of_the_ninety_six_i_have_actually_seen_and_which_i_reconstructed, the_four_cells_i_guessed_and_the_pattern_that_made_me_guess_them  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHAT CHANGED =========
# The 96-cell hole is CLOSED without spending a command. Certify's
# divergence list paired frame 0 with frame 1 for 24 cells, and the shift
# geometry plus the 96-count plus the census fixed the other 72. ACTION1
# lifts a 6x6 token plus its 2x6 strip by six rows; ACTION2 puts it back;
# the two are the same block swap and that is why s0 = s2.
#
# ========= WHY THE NEXT COMMAND IS NOT ACTION1 =========
# Replay re-runs t1 and t2 against the recorded frames every round. All 192
# reconstructed cells, including the four guessed slot cells, are adjudicated
# FOR FREE next round. Re-pressing ACTION1 would buy a transition I have
# already predicted in full. A command must buy something replay cannot.
#
# ========= WHAT REPLAY CANNOT BUY =========
#   ACTION5 and ACTION6: never pressed, two of seven keys, zero constraint.
#     Either answer is new: motion, or the first witnessed silence for them.
#   ACTION3 or ACTION4 from the LIFTED state: my manual predicts silence
#     there and says in the manual that it expects to be wrong. Costs two
#     commands (lift first), so it ranks below a one-command probe.
#   ACTION1 from the LIFTED state: tests whether key 1 is `up` or `swap this
#     pair`. Half-readable only -- a second rung at rows 24-29 is board and
#     undrawable -- and it costs a lift first.
#
# ========= STATE =========
# Token home (rows 36-41 x cols 11-16), strip blank, (53,63) burned to 3.
# 97 dynamic cells all owned, 3999 board, 33 rules covering 217 of the 217
# cell changes in history. Predicted for ACTION1 from here: 84 cells, not 96.

order     buy_what_replay_cannot_adjudicate_for_free                     [proof: lean]
order     press_a_key_that_has_never_been_pressed_before_repressing_one   [proof: lean]
order     prefer_a_one_command_probe_over_a_two_command_setup             [proof: lean]
order     close_a_known_false_silence_before_testing_an_unwitnessed_one   [proof: lean]
order     prefer_a_reversible_probe_when_its_inverse_key_is_known         [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     mine_a_divergence_list_for_paired_frames_before_calling_it_loss [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance              [proof: lean]
order     separate_two_live_readings_before_encoding_either_as_a_rule     [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it      [proof: lean]

prune     already_predicted_cell_by_cell_and_awaiting_free_replay => dead  [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead  [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead  [proof: lean]
prune     divergence_lies_only_on_a_cell_the_board_still_explains => dead   [proof: lean]
prune     repeats_a_key_whose_effect_in_this_state_is_already_itemised => dead [proof: lean]
prune     needs_two_commands_when_a_one_command_probe_is_unspent => dead    [proof: lean]
prune     asserts_a_goal_no_frame_has_ever_shown => dead                    [proof: lean]
prune     carries_a_landmark_with_no_arc_cell_coordinate => dead            [proof: lean]

heuristic keys_never_pressed_in_the_whole_history                         [admissible: lean]
heuristic keys_whose_silence_here_rests_on_no_witness                     [admissible: lean]
heuristic cells_the_manual_draws_from_geometry_rather_than_from_a_pixel   [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                    [admissible: lean]
heuristic rungs_of_the_rail_no_command_has_ever_reached                   [admissible: lean]
heuristic frames_returned_per_command_as_a_free_side_channel              [admissible: lean]

prefer    an_unpressed_key_over_repeating_a_witnessed_effect              [ev: 2/7 keys]
prefer    a_probe_whose_result_arrives_as_a_full_frame_not_a_summary      [ev: 2/2 rounds]
prefer    a_probe_that_is_undone_by_a_key_already_known_to_undo_it        [ev: 1/1 pairs]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 3/5 diffs]
prefer    testing_a_key_in_a_state_where_its_rule_has_never_fired         [ev: 3/5 transitions]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl obj0/obj2/obj3 (13x36, 436-440 cells)", "verdict": "reject",
   "as": null, "why": "both segmenter variants report negative gain (-4037 and -10409 bits), so by constraint 3 the segmentation costs more than the pixels it explains; the blobs have swallowed the entire colour-4 field along with the widget embedded in it."},
  {"id": "O-02", "subject": "mdl obj1 (2x54, present in all 6 frames)", "verdict": "reject",
   "as": null, "why": "it fuses row 53 (the colour-2 bar) with row 54 (solid field), two things with different behaviour: only one cell of row 53 has ever changed and no cell of row 54 ever has."},
  {"id": "O-03", "subject": "the seven frame0-colour types (Ink1,Ink2,Ink3,Dark,Frame6,Field,Ground)", "verdict": "accept",
   "as": "unchanged from the previous manual", "why": "their instance counts 9+10+8+12+22+12+24 sum to 97 = dynamic_cells, the 73 non-background of them equal cells_needing_an_owner, and certify reports 0 unexplained pixels in frame 0."},
  {"id": "O-04", "subject": "the widget: 6x6 token at cols 11-16 plus 2x6 strip at cols 17-22", "verdict": "accept",
   "as": "a shape spanning several types, not a new type", "why": "frame 1 rows 30-32 in the divergence list reproduce the current frame's rows 36-38 exactly; declaring it as one object is impossible since an instance is one cell, so it lives in the rules as a six-row block swap."},
  {"id": "O-05", "subject": "the rail at cols 13-14 with a 2x2 colour-2 slot marker", "verdict": "accept",
   "as": "Ink3 plus four Ink2 instances", "why": "rows 29-31 and 34-35 read 3, rows 32-33 read 2, which is one period of a period-6 pattern whose marker lands exactly where the token's 2x2 core lands when lifted."},
  {"id": "R-01", "subject": "cegis_miner tracks (all four)", "verdict": "reject",
   "as": null, "why": "the miner refused every track itself; its verdict that the world does not narrate as one mover is accepted, and the reason is now visible -- the mover travels six cells at once, which its one-move precondition cannot represent."},
  {"id": "R-02", "subject": "a1_ground_takes_body / _hollow / _ink1_edge, a1_rail_takes_*, a1_slot_takes_core, a1_field_takes_strip_*", "verdict": "accept",
   "why": "24 cells of the certify divergence list confirm these eight rules directly, 7+4+1+2+2+2+4+2, which is the whole printed sample and nothing else."},
  {"id": "R-03", "subject": "a1_ground_takes_ink2_edge and the nine a1_*_uncovers_* rules", "verdict": "accept",
   "why": "no printed pixel witnesses them; they are forced by the 96-cell count closing as 48 destination plus 48 source inside the log's own bounding box, and replay adjudicates all of them next round at zero command cost."},
  {"id": "R-04", "subject": "the eight a2_* rules", "verdict": "accept",
   "why": "s2 = s0 is forced by distinct_states=5 and independently confirmed by t3 changing cells at rows 38-39, which are strip cells only when the token is home; the swap is an involution so the same guard shape inverts."},
  {"id": "R-05", "subject": "key4_restores_strip_ink1/ink2, tightened with a sixth-above test", "verdict": "accept",
   "why": "the old form fires on any Ink1/Ink2 instance reading colour 4, which in the lifted state is the vacated strip seat, so it would have painted a phantom strip at rows 38-39; the added conjunct held at t4 and blocks the lifted state."},
  {"id": "R-06", "subject": "Field-typed rules for ACTION3/4/7 acting on the lifted strip", "verdict": "probe-pending",
   "why": "the obvious generalisation, coverage 0/0 today, refused under constraint 2; the probe is lift then press ACTION3, two commands, ranked below the unpressed keys."},
  {"id": "R-07", "subject": "an ACTION1 rule for a second rung at rows 24-29", "verdict": "reject",
   "why": "those cells are constant, the board explains them, no instance is seated there, and no rule could draw the widget arriving even if the rung exists."},
  {"id": "L-01", "subject": "zero_space global law (cell list plus support)", "verdict": "entailed",
   "why": "its cell list is exactly my 97 dynamic cells; the engine's own verdict is THIN, rank 3 of 679 features, so it corroborates the census and adds no structure."},
  {"id": "L-02", "subject": "the eight count invariants", "verdict": "accept",
   "why": "each is a direct count of dynamic cells of that frame-0 colour and the eight sum to 97 = dynamic_cells with 3999 board, though invariant bodies are raw text and no backend checks them."},
  {"id": "L-03", "subject": "prior theorem placing the 12 colour-4 cells at rows 36-37", "verdict": "reject",
   "why": "refuted: they are at rows 32-33 cols 17-22, the strip's lifted seat, as the divergence list shows colours 2,1,1,2,1,1 arriving there at t1."},
  {"id": "P-01", "subject": "ACTION5 or ACTION6", "verdict": "probe-pending",
   "why": "two of seven keys have never been pressed and constrain nothing; one command, and either motion or a first witnessed silence is new information."},
  {"id": "P-02", "subject": "the four guessed cells at rows 38-39 cols 13-14", "verdict": "probe-pending",
   "why": "settled by replay next round at no command cost; if wrong the repair is to read 3 instead of 2 in a1_body_uncovers_slot and a2_slot_returns."},
  {"id": "P-03", "subject": "the row-53 burn, readings A/B/C", "verdict": "probe-pending",
   "why": "one witness in five transitions; ACTION4 from here predicts a restore and no burn under both A and B, so a burn would argue for C and would land on (53,62), which is undrawable."},
  {"id": "E-01", "subject": "a six-cell move for the widget", "verdict": "probe-pending",
   "why": "wanted moved(token, up) six times or a jump to a computed cell; the event table moves one cell, jumps only to a declared landmark, and there is no object called the token since arc-instances yields 36 one-cell instances -- written instead as 26 per-cell recolour rules reading the cell six above or six below."},
  {"id": "E-02", "subject": "a goal naming the colour-14 block at rows 31-34 cols 42-45", "verdict": "reject",
   "why": "wanted a goal that the strip reaches it; the block is constant, hence board, hence has no instance to name, and no frame has shown a win -- so no goal section at all, and is_goal compiles to False."}
]
```
```
