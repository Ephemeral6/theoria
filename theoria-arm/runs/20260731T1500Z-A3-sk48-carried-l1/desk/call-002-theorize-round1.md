# call-002-theorize-round1

model: `claude-opus-5` · 475741 ms · $1.368456 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 34833, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 34833, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 34833, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 34833, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 39754, "type": "message"}], "output_tokens": 39754, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
# theory.dsl -- SEVENTH DRAFT.
#
# THE RECORD SHRANK, AND THAT IS THE WHOLE STORY OF THIS ROUND.
# The store now reads 6 states, 5 transitions, steps 6, dynamic_cells 97,
# cells_needing_an_owner 73. The draft I am replacing was written against 14
# states, 13 transitions, dynamic_cells 99, cells_needing_an_owner 75. The six
# states I am now given are cell-for-cell the first six of that longer record
# (RESET, swap up, swap back, blank, restore + one bar cell, blank), and the
# bar in the current frame has exactly one consumed cell instead of three.
# I cannot tell whether the episode was re-run from RESET or the record was
# truncated, and it does not matter for what I am allowed to write: the record
# is five transitions and I may cite nothing else.
#
# WHAT THAT COSTS ME, STATED BEFORE THE PLEASANT PARTS.
#  * key3_marches_the_meter_leftward is DELETED. Its only witness was t11 and
#    there is no t11. It never fires anywhere in this record, so deleting it
#    changes no replay score; keeping it would be a rule with coverage 0/0,
#    which constraint 2 forbids outright.
#  * The period-three extra-frame clock had three ticks and now has ONE. A
#    period and an offset fitted to one point is not a reading, it is a shrug.
#    Deflated accordingly.
#  * The refutation of the toll-on-the-restore-key reading rested on the third
#    tick arriving under ACTION3. That transition is gone, so the refutation is
#    gone with it and the toll reading is ALIVE AGAIN. I re-open it rather than
#    quietly keeping the conclusion I liked.
#  * The confirmation that the checker replays open-loop rested on the 9-vs-10
#    split over thirteen transitions. In THIS record open-loop and resyncing
#    both score 4 of 5, because my only error is at transition 0 and the world
#    returns to frame 0 at transition 1 where my silent manual already sits.
#    The two are indistinguishable here and I move that theorem back to pending.
#  * The 9-of-13 rule-search ledger is deleted, not demoted. It ranked rules
#    against transitions this record does not contain and I cannot re-check a
#    single line of it.
#
# 2. THE SURPRISE THAT FIRED IS THE ONE I PRE-REGISTERED, AND I REFUSE IT
#    AGAIN. replay_mismatch at t=0, ACTION1, 96 cells, first cell (30,11)
#    manual 5 world 6. Two measured blockers, both witnessed inside this very
#    brief: (a) (30,16), (31,16), (32,16), (33,16), (34,16) are all colour 5 in
#    frame 0 with above 5, below 5, left 5, right 4 -- one indistinguishable
#    guard reading -- and the world gives 6, 6, 1, 2, 6; constraint 5 forbids
#    the rule set that would be needed. (b) 24 of the 96 repainted cells are
#    background colour 5 in frame 0, carry no instance, and no recolored event
#    can name them. Silence costs exactly one transition of five. A partial
#    swap rule costs all five by desynchronising the replay.
#
# 3. WHAT THE SHORTER RECORD DID NOT COST. The frame-zero anatomy re-closes on
#    the new numbers without a single free parameter: the same six colour
#    classes give 22+12+8+9+10+12 = 73 = cells_needing_an_owner, and 73 + the
#    same 24 background cells of the swap footprint = 97 = dynamic_cells. The
#    only change is that the meter now contributes one Stud instead of three.
#    Responsibility stayed 0 unexplained of 4096. That is a real check passed,
#    not a coincidence rescued.
#
# 4. THIRTEEN LANDMARKS DELETED. Every one carried the comment
#    "arc-cell: carried, coordinates stripped", which is not the required
#    "arc-cell: (row, col)". Each of them therefore lands at (0,0). No rule in
#    this manual references any of them, so they were thirteen declarations
#    buying nothing and thirteen chances to drag a rule to the origin.
#
# 5. WHAT IS SHARP NOW. The manual says the bar NEVER MOVES AGAIN: the seed
#    rule needs a colour-2 Stud whose right neighbour is off-board, and after
#    t4 there is none. That is a deliberate under-claim and it will be wrong at
#    the next tick, whenever it comes. It is also the cleanest separator I
#    have: from the current blanked state, key(4) under my manual repaints
#    twelve strip cells and leaves the bar alone, while under the toll reading
#    it repaints thirteen. One press decides it.

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
  Casing [segment: colour_class_6 ev: t0-t5 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t5 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t5 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t5 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t5 compress: 10]
  Erased [segment: colour_class_4 ev: t0-t5 compress: 12]

events:
  event recolored(o, c)

# Seven rules. Six of them are the blank/restore pair for the two keys that
# blank and the one key that restores, and their coverage is now one witness
# each instead of five, because there is one witness each in this record. The
# seventh is the meter seed, which fires once and then can never fire again.
# The march rule that used to sit here is deleted: zero witnesses in this
# record, and a rule with no witness is not a rule.
#
# The four negative neighbour guards on the blank rules are what carves the
# twelve strip cells out of their colour classes: leftof-is-cavity excludes the
# two port cells (38,16) and (39,16); leftof-is-background and
# rightof-is-background exclude the four bar Studs at rows 32-33 cols 13-14;
# above-is-background excludes the meter Stud at (53,63), which is exactly why
# the t3 diff is twelve cells and not thirteen. Those guards are pixel-fitting
# in a costume and I say so in colour_classes_are_not_the_worlds_objects.

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

  rule key4_advances_the_meter_once forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall and colored(below(?p), 4) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 10 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 73 [status: proven]

  theorem the_record_now_holds_five_transitions_and_i_may_cite_nothing_else "the store reads 6 states and 5 transitions where my previous draft cited 14 and 13. The six states I am given are cell for cell the first six of that longer record, and the bar has one consumed cell where it had three. I cannot tell a re-run from a truncation and it changes nothing about what I may write. Four consequences, each paid: the march rule is deleted for want of a witness; the three-tick clock is down to one tick; the refutation of the toll-on-the-restore-key reading is withdrawn because it rested on a transition that is gone; and the 9-of-13 rule ledger is deleted rather than demoted, since not one of its lines can be re-checked here. What survives untouched is everything whose witness sits inside this brief: the frame-zero anatomy, the two swap blockers, the diagonal texture, and the six-row panel period, all of which the divergence report re-witnesses. A manual that loses evidence should get smaller, and this one did."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and (53,63) holds 2 rather than 3. The anatomy closes cell by cell on the new totals: 22 Casing as the 20-cell perimeter of rows 36-41 by cols 11-16 minus the two ports plus the 2x2 core at rows 38-39 cols 13-14; 12 Cavity as the 4x4 at rows 37-40 cols 12-15 minus that core; 8 Rail as the unselected slot bar at rows 30-31 and 34-35 by cols 13-14; 4 Stud as the same bar middle at rows 32-33; 8 Pip and 4 Stud in the strip; 1 Pip and 1 Stud in the two ports at (38,16) and (39,16); 12 Erased as lane A strip at rows 32-33 by cols 17-22; 1 Stud in the meter at (53,63). Totals 22+12+8+9+10+12 = 73 = cells_needing_an_owner. The 24 remaining dynamic cells are exactly the background cells of the unselected slot footprint, cols 11, 12, 15, 16 over rows 30-35, and 73+24 = 97 = dynamic_cells. The one difference from last draft is the meter contributing one Stud instead of three, and it is the only difference the shorter record demanded."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_the_arm_extends_it_as_cells_vary "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0. A cell constant across the whole record gets no instance, which is why the slots above row 29 are invisible to this manual and why 24 background cells of the swap are unreachable. A cell that varies gains one, and the meter is the clean demonstration read in both directions: with three bar cells consumed the store said 75 owners and 99 dynamic, with one consumed it says 73 and 97, and my declarations move by exactly the same two. This also fixes what the meter rules can reach -- (53,62) carries no instance in this record, so no rule of mine can ever repaint it, and that is a fact about the arm rather than about the world."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language can produce them. A guard sees a cell own colour and its four neighbour colours and nothing else -- no coordinate, no row band, no distance. The witness is measured inside this brief, not remembered: (30,16), (31,16), (32,16), (33,16) and (34,16) are all colour 5 in frame 0 with above 5, below 5, left 5, right 4, and the divergence report has the world make them 6, 6, 1, 2, 6 -- four distinct answers to one indistinguishable question. A second pair from the same report: (30,13) is colour 3 and becomes 6 while (32,13) is colour 2 in an equally uniform bar neighbourhood and also becomes 6, so colour does not decide it either. Constraint 5 forbids rules that both fire, so the swap does not go in the manual and the replay_mismatch at transition 0 is a cost I accept rather than a defect I can repair."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem the_swap_has_a_second_blocker_twenty_four_of_its_cells_have_no_instance "24 of the 96 cells the swap repaints are colour 5 in frame 0 -- the background cells of the unselected slot footprint at cols 11, 12, 15, 16 over rows 30 to 35, and the divergence report shows the world painting (30,11), (30,12), (30,15), (30,16), (31,11), (31,16), (32,11), (32,12), (32,15) among them. No declared object carries colour 5, so no instance exists there, so no recolored event can name them, and this blocker does not depend on what a guard can see. The only escape is declaring the background itself an object, which puts an instance on every unexplained colour-5 cell in a 4096-cell frame. Both blockers point the same way and they are independent, which is why I refuse this surprise twice with a clear conscience."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem silence_on_the_selector_costs_one_transition_of_five "my manual is silent on key(1) and key(2), so it draws frame 0 at transition 0 where the world draws the swapped panel: one transition lost, the one certify reports. Transition 1 then counts as a match because ACTION2 returns the world to frame 0 while my silent manual never left it, and transitions 2, 3 and 4 match because manual and world are back in step. That is 4 of 5, and it is the score certify returned. A partial or wrong swap rule would produce a frame equal to neither manual nor world at transition 0, would not be undone at transition 1, and would lose all five. The arithmetic is harsher than it was over thirteen transitions -- 20 percent of the record instead of 8 -- and it still comes out the same way."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem i_withdraw_the_claim_that_replay_is_confirmed_open_loop "I confirmed open-loop replay last round by pre-registering that a resyncing checker would return 10 of 13 and getting 9. That separation lived entirely in transitions 5 to 12, which this record does not contain. Here my only error is at transition 0 and the world hands the frame back at transition 1, so an open-loop checker and a resyncing checker both score 4 of 5 and nothing in this brief distinguishes them. I keep reading my coverage numbers as open-loop because that is the conservative reading and because it was measured once, but the status is pending, not passed. The separator is any transition on which my manual is wrong and the world does not immediately return to where my manual sits -- which is precisely what the next tick of the bar will provide, since my manual now says the bar never moves again."
    [depends: silence_on_the_selector_costs_one_transition_of_five  probe: pending]

  theorem the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified "row 53 reads colour 2 from column 10 to column 62 and colour 3 at column 63, and the whole of my evidence about how it moves is one transition: at t4 an ACTION4 press turned (53,63) from 2 to 3. One tick cannot identify a cadence. All four readings I have ever entertained are alive on this record -- a toll on the restore key, a toll on every key, a period in commands, a period in returned extra frames -- and I have no way to rank them. So the manual carries the seed rule, which fits the one thing about that tick I can express, that the cell with no right neighbour went first, and carries nothing about what happens next. The consequence is a deliberate under-claim: after t4 there is no colour-2 Stud whose right neighbour is off-board, so my manual says the bar never moves again and will be wrong at the next tick. I prefer to be wrong once, visibly, at a moment I have named, over inventing a cadence with a one-point fit."
    [depends: instance_anchoring_is_frame_zero_and_the_arm_extends_it_as_cells_vary  probe: passed]

  theorem the_seed_rule_is_a_one_shot_and_here_is_what_it_is_worth "key4_advances_the_meter_once has coverage 1/1 and by constraint 3 that looks like a rule spent on a single pixel. Its defence is smaller than it used to be and I state it at its true size: without it the current frame cannot be drawn at all, because (53,63) is colour 3 in every state from t4 onward and only this rule paints it. So it buys the last two transitions of the record rather than the three I once claimed for it. What it does not buy is understanding -- it is silent on why that tick fell on that press, and its guard rightof-is-wall makes it structurally unrepeatable, which is an honest way of saying that it explains a boundary and not a mechanism."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: passed]

  theorem i_deleted_the_march_rule_and_i_expect_to_regret_it_if_the_long_record_returns "the previous draft carried a rule marching the bar leftward on key(3), justified by a hand ledger scoring it 9 of 13 against 6 for silence. Every transition in that ledger except the first six is absent here, the rule fires nowhere in this record, and a rule with coverage 0/0 is exactly what constraint 2 forbids. So it is deleted, and my commitment flips: where the previous draft said the next key(3) press consumes a bar cell, this one says it does not. That is not a change of mind about the world, it is a change in what I am allowed to assert, and I flag it as the single most likely place this draft is wrong. If a longer record returns and the bar has moved on key(3) presses again, the rule comes straight back with its witnesses."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_extra_frame_clock_is_down_to_one_point "the reading was that a command advances a hidden clock by its frame count minus one and the bar loses a cell every third advance, and it was fitted to three ticks. This record has one tick. The count at the tick is four: t1, t2, t3, t4 each returned two frames, t5 returned one and did not advance it. Four advances and one tick determine neither a period nor an offset, so this is a shape without parameters now. It still makes the same qualitative prediction that ACTION7 is cheaper than the other keys, since it is the one command in six that returned a single frame, and that prediction is cheap to test by pressing ACTION7 again and reading the frame count alone. I record the clock here so that when ticks two and three arrive the fit can be re-made against the same numbers rather than re-invented."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_toll_on_the_restore_key_reading_is_alive_again "for two drafts I treated the reading -- one bar cell per key(4) press -- as refuted, on the strength of a tick that arrived under ACTION3 at t11. There is no t11 here. In this record ACTION4 was pressed exactly once and the bar moved exactly once, which is the toll reading fitting perfectly with one point. My manual does not implement it, because implementing it means guarding the next bar cell (53,62), which carries no instance and cannot be repainted by any rule of mine. So the reading is untestable by replay and testable in one press: from the current blanked state, key(4) restores twelve strip cells under my manual and thirteen cells including (53,62) under the toll reading. That is the cheapest open question in the game right now."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem i_do_not_know_which_way_the_bar_runs "one cell has gone from 2 to 3 at the right end of row 53. That is equally a resource being spent and a progress meter being filled, and colour 3 is also the colour an unselected slot shows on its rails, which argues weakly that 3 is a resting or completed state rather than a consumed one. Nothing in five transitions separates them, and they invert the sign of every ranking decision: under one reading a probe costs part of a budget, under the other it earns progress. Until something separates them the playbook may not rank on bar movement in either direction. The separator is cheap and will arrive on its own -- either the bar reaching column 10 ends the level, or NOT_FINISHED survives it."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_bar_is_between_fifty_three_and_sixty_three_cells_long "row 53 reads colour 2 over columns 10 to 62 and colour 3 at 63. I have never been shown columns 0 to 9 of that row, so 53 cells are measured unconverted and up to 63 exist if the bar reaches the left edge. Whatever the cadence turns out to be, the magnitude is what matters for ranking and it is safe in both directions: the budget is large compared with six actions, so probing is cheap now and will not stay cheap. I have deliberately stopped calling it a countdown."
    [depends: i_do_not_know_which_way_the_bar_runs  probe: pending]

  theorem the_strip_hides_and_shows_and_the_separator_is_still_one_action_away "key(3) blanked a shown strip at t3, key(7) blanked one at t5, key(4) restored a blanked one at t4, twelve cells and cell for cell identical each time, so the pattern lives somewhere the frame does not show. Both blank presses were made from a shown strip and the single restore press from a blanked one, so hide-and-show and toggle-and-toggle remain indistinguishable after five transitions exactly as they were after thirteen. The state now is blanked, and my manual commits to inert for a repeat of either blanking key: every strip cell is colour 4, so no blanking guard can fire, and no meter rule of mine can fire either. A restore of the strip under a blanking key refutes hide-and-show outright; nothing happening confirms it and also tells me what a null command does to the frame count."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_restore_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "key4_restores_the_strip_pips and _studs guard on colour 4 alone. That is correct on the one restore observed, because the press was made from a state where slot B was selected and the only colour-4 Pip and Stud instances in existence were the twelve blanked cells of lane B. It would be wrong the moment slot A is selected: lane A strip cells become texture while lane B strip cells become arena fill of colour 4, and a key(4) would then repaint an unselected lane. My manual never reaches that state, because it is silent on the selector, so this costs zero transitions today and certify cannot see it. It is written here because a searcher planning through a selector move would be misled by a rule that scores 12 of 12. The fix needs a guard that reads which slot is selected, and selection is exactly what the guard language cannot see."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have ever seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Witnesses inside this brief: frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, the same period-3 run offset by one column, and the divergence report gives all seven of lane A row 32 cols 16-22 as the world drew them at t1 -- 1 2 1 1 2 1 1 -- with rows 32 and 38 agreeing because they are six apart and 6 is divisible by 3. The two port cells fit the same formula, which is a small unforced success. So the two strips are two windows onto one diagonal texture, which is why a restore can rebuild twelve cells exactly. Untested prediction: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2. No rule needs this, since each instance already remembers its frame 0 colour, so by constraint 3 the concept buys understanding rather than symbols and I say so rather than smuggling it into the word table."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, twice now, twelve cells both times. (38,16)=1 and (39,16)=2 sit on the widget right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since leftof both is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The rival explanation is that col 16 is simply where the 6x6 widget ends and the survival is coincidence; two blanks do not separate them and neither did six."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied, so they are board. Colour 3 at cols 13-14 is what an unselected slot shows at its four outer rows, and the unselected slot at rows 30-35 shows 3 3 2 2 3 3 down those columns, so row 29 sits where the last row of a slot at rows 24-29 would sit. The period is measured inside this brief: the divergence report gives the world t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at the same columns read identically -- eighteen cells, six rows apart. Rows 42 onward are uniform background, so rows 36-41 is the bottom slot. I read key(1) as move selection up one slot and key(2) as down one. The probe has two halves and my manual is silent on both, so either press scores it for free: from the bottom slot the down key does nothing under the move reading and repaints 96 cells under a two-slot toggle, and from the upper slot the up key repaints rows 24-35 if a third slot exists."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_arena_is_lanes_and_the_badge_is_row_aligned_with_the_cavity "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47, and I have re-counted that against the current frame rather than assuming it. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45. Those are exactly the rows a selected slot 4x4 cavity occupies within its own six-row band -- the selected bottom slot cavity is rows 37-40 within band 36-41, and the badge is rows 31-34 within band 30-35. So the badge is a cavity-shaped, cavity-aligned object at the far right of the lane belonging to the slot at rows 30-35, and the bottom slot lane has nothing at cols 42-45. Either it is a target a lane must be made to match, or it marks which slot carries a task. Zero transitions bear on either, and slots above row 29 may carry badges I have never seen, since an unvarying badge is board by definition."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_meter_cadence_is_inexpressible_and_i_checked_for_a_latch "a guard reads a cell colour, its four neighbour colours, off-board, and the action name. A cadence needs a count and there is no count in the grammar. Before settling for silence I re-checked the one loophole: an object whose declared colour equals the background renders the same whether present or vanished, so present could in principle be an invisible bit. It cannot be used. The value grammar exposes only color as a field, so no guard can read present; and an object declared with arc-colour 5 would be instantiated on every background cell the board cannot explain, which is the 24 cells of the swap footprint, none of them where a latch would be wanted. So the cadence stays prose, and with the march rule gone the manual now carries no proxy for it at all, which is the smaller and more honest of the two failures available."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: passed]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot bar, a port, four strip cells and the meter cell -- four unrelated roles. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 73 cells that need an owner against 73 pixels written out, with 0 unexplained confirmed again this round. The cost is measured too: no rule can name the strip, so every blanking rule carves it out of its class with four negative neighbour guards, and the meter rule needs an off-board test to separate one Stud from the other nine. Those guards are pixel-fitting in a costume, they are correct on every instance in frame 0, and they are the price of a colour-first arm."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem thirteen_landmarks_deleted_because_none_of_them_had_coordinates "the previous draft declared thirteen landmarks each carrying the comment arc-cell colon carried, coordinates stripped, which is not the arc-cell (row, col) form the arm requires. Every one of them therefore resolves to (0,0). No rule in that draft or this one references a single landmark, so they bought nothing and risked dragging a future rule to the origin. They are gone. If I ever need a named cell -- the likeliest candidate is the next bar cell (53,62) once it varies and gains an instance -- I will declare exactly that one, with its coordinates in the comment where the grammar demands them."
    [probe: passed]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, which is rows 29-54 by cols 10-63. They are somewhere in the 3999 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is also where a title, target, score or instruction would live, and the most likely home of whatever finishing means. It is the largest thing I do not know, and it is also where the answer to i_do_not_know_which_way_the_bar_runs most plausibly sits."
    [depends: no_goal_section_on_purpose  probe: pending]

  theorem two_keys_have_never_been_pressed "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not. The case for pressing them is unchanged and the budget argument is unchanged in magnitude even though its sign is unknown: the bar is 53 cells or more from its end and six actions have been spent. If either key is a click carrying coordinates, this guard language cannot express it and the finding will be recorded as prose rather than as a rule. Each press also reads its own returned frame count, which is the only handle I have left on the clock."
    [depends: the_extra_frame_clock_is_down_to_one_point  probe: pending]

  theorem no_goal_section_on_purpose "all six states returned NOT_FINISHED and nothing in five transitions indicates what finishing means. The live candidates are that a lane texture must be brought to agree with the badge at its far end, that every slot in the column must be visited or solved, or that the objective lives in the rows I have never been shown. An absent goal compiles to is_goal implies False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. I will not write a goal on the strength of a badge I have never interacted with."
    [depends: i_do_not_know_which_way_the_bar_runs  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "I re-read the stream against the new, shorter numbers rather than assuming it repeated. mdl_segmenter returns negative gain on both variants, -4037 bits at 4 tracks and -10409 at 33, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator and not the world; its event tally of 4 recolors, 2 appears and 2 vanishes is however consistent with my reading that this world only ever recolours and that the appear/vanish pair is the swap seen as one blob. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition, and its own verdict says the world does not narrate as one mover, which agrees with my event vocabulary of recolored alone. zero_space calls its own evidence THIN in its own words -- 5 transitions constraining rank 3 of 679 features, null space of dimension 676 -- and its single global law spans 97 dynamic cells at once, which is what a 676-dimensional null space produces rather than what a conservation law looks like. What I took from the engines is the store arithmetic, dynamic_cells 97 and cells_needing_an_owner 73, and both closed against a reconstruction I built without them."
    [probe: pending]

  theorem what_this_draft_pre_registers "certify should return replay 4 of 5, first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) with manual 5 and world 6; responsibility 0 unexplained of 4096; unambiguous 0 clashes. That is the same score the previous draft got, because deleting the march rule removes a rule that never fired in this record, so this prediction tests the checker not at all and I say so instead of dressing it up. The informative pre-registrations are about the world and there are three, each decided by one press from the current blanked state. key(3) or key(7): my manual says the frame does not change at all, which refutes toggle-and-toggle if it holds and refutes my manual if the strip comes back. key(4): my manual says exactly twelve cells change and the bar does not move, while the toll reading says thirteen. ACTION7 again: my manual says nothing about frame count, and a second single-frame return would make ACTION7 the only key that does not advance the world clock."
    [depends: the_record_now_holds_five_transitions_and_i_may_cite_nothing_else  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- seventh draft. Rewritten because the evidence tags changed.
#
# THE RECORD SHRANK FROM 13 TRANSITIONS TO 5, so every entry whose evidence
# tag cited the longer record has been re-tagged or removed. Nothing here is a
# stored line of play; every entry is a ranking rule the searcher still has to
# evaluate against whatever state it is actually in.
#
# WHAT MOVED, AND WHY:
#
# 1. THE MARCH RULE IS GONE FROM THE MANUAL, so the prune that told a searcher
#    not to read it as a price per press is gone too -- there is nothing left
#    to misread. In its place: no plan may price a bar cell against any key at
#    all, because one tick cannot identify a cadence and all four readings are
#    open again.
#
# 2. THE TOLL-ON-THE-RESTORE-KEY READING CAME BACK FROM THE DEAD when its
#    refuting transition left the record. That makes the restore key, pressed
#    from the current blanked state, the cheapest live separator in the game:
#    twelve cells under my manual, thirteen under the toll reading. It is now
#    ranked directly behind the inert test.
#
# 3. I ADDED ONE PRUNE THAT IS ABOUT ME RATHER THAN THE WORLD: a plan that
#    cites a transition absent from the current record is dead. I was one
#    round away from ranking on a ledger I could no longer check.
#
# 4. STILL REMOVED, AND STAYING REMOVED: anything that ranks on the direction
#    of the bar. I cannot tell a budget being spent from progress being made,
#    and the two invert the sign of every such decision.

order   repress_a_blanking_key_in_the_blanked_state_to_test_the_inert_commitment  [proof: lean]
order   press_the_restoring_key_to_separate_the_toll_reading_from_the_rest  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_for_freedom_from_the_clock  [proof: lean]
order   settle_which_way_the_bar_runs_before_ranking_anything_on_it       [proof: lean]
order   press_the_two_never_pressed_keys_while_the_budget_is_still_long   [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule      [proof: lean]
order   make_some_cell_outside_the_observed_window_vary                   [proof: lean]
order   compare_a_lane_against_the_badge_at_its_own_far_end               [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known          [proof: lean]
order   read_every_bar_cell_that_changed_and_the_returned_frame_count_after_every_command  [proof: lean]

prefer  an_action_the_manual_has_pre_registered_a_frame_for               [ev: 4/5 transitions replay]
prefer  an_action_on_which_two_live_readings_predict_different_frames     [ev: 4 meter readings open]
prefer  an_action_that_answers_more_than_one_open_question_at_once        [ev: 1 press separates 2]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/5 commands returned one frame]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  a_slot_never_selected_over_one_already_drawn_twice                [ev: 2 slots seen of a column]
prefer  a_state_whose_lane_carries_the_badge_over_a_lane_without_one      [ev: 1/2 lanes carry a badge]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats        [ev: 97/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced           [ev: 0/5 transitions test it]

heuristic bar_cells_still_unconverted                                    [admissible: lean]
heuristic slots_in_the_column_never_yet_selected                         [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed                          [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                    [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                     [admissible: lean]
heuristic open_questions_no_single_command_can_yet_separate              [admissible: lean]

prune   plan_that_rests_on_the_bar_direction_being_known => dead          [proof: lean]
prune   plan_that_prices_a_bar_cell_against_any_particular_key => dead    [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_expects_the_manual_to_move_the_bar_a_second_time => dead  [proof: lean]
prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead     [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead       [proof: lean]
prune   plan_that_trusts_a_restore_rule_across_a_selector_move => dead    [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead       [proof: lean]
prune   repeat_of_a_key_already_witnessed_inert_in_this_exact_state => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead      [proof: lean]
prune   bar_consumed and not goal => dead                                [proof: lean]
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
=== THEORY ===
```
# theory.dsl -- EIGHTH DRAFT.
#
# 0. NOTHING NEW CAME IN. The store reads the same 6 states and 5 transitions
#    as the draft I am replacing: same actions, same dynamic_cells 97, same
#    cells_needing_an_owner 73, same current frame. No press was made between
#    drafts. So this round cannot be about new evidence, and any change I make
#    has to be paid for out of re-reading what I already had.
#
# 1. THE PRE-REGISTRATION WAS MET, CELL FOR CELL. Last draft predicted certify
#    would return replay 4/5, first divergence at transition 0 under ACTION1,
#    96 cells wrong, first cell (30,11) with manual 5 and world 6,
#    responsibility 0 unexplained of 4096, 0 clashes. Certify returned exactly
#    that, down to the cell. That is the one thing this round confirmed, and it
#    confirms my model of the CHECKER, not my model of the world. I say so.
#
# 2. THE SURPRISE IS THE SAME SURPRISE AND I REFUSE IT A THIRD TIME -- BUT ON
#    DIFFERENT GROUNDS, BECAUSE ONE OF MY TWO BLOCKERS TURNED OUT TO BE FALSE.
#    I had been saying the swap is blocked because (a) guards cannot tell the
#    96 cells apart and (b) 24 of them are background-coloured and carry no
#    instance. Blocker (b) is WRONG and I withdraw it: an object declared with
#    arc-colour 5 and arc-instances: all would be placed on exactly the colour-5
#    cells the board cannot explain, and those are exactly those 24 cells,
#    because 97 dynamic minus 73 owned is 24. The escape I said was ruinous is
#    in fact cheap and precise. It just does not help, for reasons (a) and (c).
#    In its place I put a blocker I had not written down before:
#    (c) MDL. Even granting every position-reading device I can imagine, the
#    swap comes out as roughly one rule per repainted cell, which is longer
#    than the 96 pixels it explains. Constraint 3 kills it independently of
#    constraint 5. Two blockers, both stated as measurements, both new-ish.
#
# 3. THE GUARDS GOT SHORTER AND THE MANUAL GOT MORE HONEST. The blanking rules
#    carried four negative neighbour guards each. Re-checking every one of the
#    9 Pip and 10 Stud instances against the frame I can reconstruct, three of
#    the four do nothing on the Pip rules and one of the four does nothing on
#    the Stud rules. Blanking now costs 1 guard for pips and 3 for studs
#    instead of 4 and 4, and the meter seed loses its redundant below-is-4 test.
#    Eight guard atoms deleted, same firing set on every instance in every state
#    my manual can reach, predicted replay unchanged at 4/5. This is the whole
#    of what a round with no new evidence is allowed to buy: a shorter manual
#    that says the same thing.
#
# 4. WHAT I CHECKED AND DID NOT TAKE. Declaring the background as an object
#    (rejected: zero gain, it explains no pixel that the board does not already
#    draw correctly). Declaring a second colour-2 type to reach the next bar
#    cell (rejected: the arm finds objects by colour and nothing else, so it
#    would duplicate the ten Studs). Nesting cell expressions -- above(above(?p))
#    -- which would give guards a two-cell reach and is the only thing that
#    could ever separate (32,16) from (33,16): the grammar calls its cell list
#    exhaustive and does not say whether the argument may itself be a cell
#    expression, so I will not gamble a parse error on it; it is written as a
#    probe instead.
#
# 5. WHAT IS STILL SHARP. The manual says the bar NEVER MOVES AGAIN, and it
#    says a repeat of either blanking key from the current blanked state
#    changes NOTHING. Both are deliberate under-claims and both are decided by
#    one press.

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
  Casing [segment: colour_class_6 ev: t0-t5 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t5 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t5 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t5 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t5 compress: 10]
  Erased [segment: colour_class_4 ev: t0-t5 compress: 12]

events:
  event recolored(o, c)

# Seven rules, and every guard atom in them is now load-bearing. I re-derived
# each one against all 19 Pip and Stud instances rather than inheriting it:
#
#  Pip blanking needs ONE guard. Only the port pip (38,16) must be spared, and
#  its left neighbour (38,15) is a colour-0 cavity cell. The three other guards
#  the previous draft carried -- left-is-5, right-is-5, above-is-5 -- exclude no
#  Pip whatsoever, because no Pip has a background neighbour on any of those
#  sides. They were decoration and they are gone.
#
#  Stud blanking needs THREE. The port stud (39,16) is spared by the same
#  left-is-cavity test. The four bar studs at rows 32-33 cols 13-14 form a 2x2
#  of colour 2, so each has a colour-2 cell to its left or its right; the meter
#  stud (53,63) has the colour-2 bar to its left. One pair of guards --
#  not-left-is-2 and not-right-is-2 -- therefore spares all five at once, where
#  the previous draft spent three guards doing it. The four strip studs are
#  flanked by colour-1 pips or by arena fill on both sides, so all four fire.
#
#  The meter seed needs ONE positional guard. Exactly one Stud in existence has
#  no right neighbour, so rightof-is-wall alone picks it out; the below-is-4
#  test the previous draft added was true of that cell and of nothing that
#  needed excluding.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_advances_the_meter_once forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 10 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 73 [status: proven]

  theorem the_last_drafts_pre_registration_was_met_exactly_and_no_new_evidence_arrived "the previous draft predicted replay 4 of 5, first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6, responsibility 0 unexplained of 4096, and 0 clashes over 18 adjudicated pairs. Certify returned all six numbers. The store is byte for byte what it was: 6 states, 5 transitions, 97 dynamic cells, 73 needing an owner, same current frame with one consumed bar cell. So no press was taken between drafts and this round has no new observation in it. What the match confirms is my model of the checker -- that it replays from frame 0, that silence draws the previous frame forward, that responsibility is scored on frame 0 -- and not one thing about the world. A draft written against an unchanged record may only get shorter or better argued, and I have tried to do both rather than manufacture a discovery."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and (53,63) holds 2 rather than 3. The anatomy closes cell by cell: 22 Casing as the 20-cell perimeter of rows 36-41 by cols 11-16 minus the two ports plus the 2x2 core at rows 38-39 cols 13-14; 12 Cavity as the 4x4 at rows 37-40 cols 12-15 minus that core; 8 Rail as the unselected slot bar at rows 30-31 and 34-35 by cols 13-14; 4 Stud as the same bar middle at rows 32-33; 8 Pip and 4 Stud in the strip; 1 Pip at (38,16) and 1 Stud at (39,16) in the ports; 12 Erased as the lane A strip at rows 32-33 by cols 17-22; 1 Stud in the meter at (53,63). Totals 22+12+8+9+10+12 = 73 = cells_needing_an_owner. The 24 remaining dynamic cells are exactly the background cells of the unselected slot footprint, cols 11, 12, 15, 16 over rows 30-35, and 73+24 = 97 = dynamic_cells. Responsibility came back 0 unexplained again, so this reconstruction has now been checked twice against the arm."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0. A cell constant across the whole record gets no instance, which is why the slots above row 29 are invisible to this manual and why the next bar cell (53,62) is unreachable: it has been colour 2 in all six states, so it is board, so no rule of mine can ever repaint it however I guard. A cell that varies gains one, and the meter demonstrated the arithmetic in both directions across the record change -- three bar cells consumed gave 75 owners and 99 dynamic, one consumed gives 73 and 97, and my declarations move by exactly the same two. This is a fact about the arm, not about the world, and it is the single largest constraint on what this manual can say."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language can produce them. A guard sees a cell's own colour, its four immediate neighbour colours, off-board, and the action name -- no coordinate, no row band, no distance. The witness is measured inside this brief: (30,16), (31,16), (32,16), (33,16) and (34,16) are all colour 5 in frame 0 with above 5, below 5, left 5, right 4 -- one indistinguishable guard reading -- and the divergence report has the world make them 6, 6, 1, 2, 6. Three distinct answers to one question. A second pair from the same report kills colour as a discriminator: (30,13) is colour 3 and becomes 6 while (32,13) is colour 2 in an equally uniform bar neighbourhood and also becomes 6. Constraint 5 forbids two rules that both fire, so the swap does not go in the manual, and the replay_mismatch at transition 0 is a cost I accept rather than a defect I can repair."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem i_withdraw_the_no_instance_blocker_because_a_colour_five_object_would_own_those_cells_exactly "for two drafts I gave a second reason the swap cannot be written: 24 of its 96 cells are background colour 5, carry no instance, and no recolored event can name them, and I called the only escape ruinous on the grounds that a colour-5 object would be instantiated on every background cell of a 4096-cell frame. That was wrong and the arithmetic in my own manual says so. The arm instantiates the cells of a declared colour THAT THE BOARD CANNOT EXPLAIN, and the colour-5 cells the board cannot explain number exactly 97 minus 73 = 24 -- precisely cols 11, 12, 15, 16 over rows 30-35, precisely the swap footprint, and not one cell more. So the escape is cheap and surgical, and I am withdrawing the blocker rather than keeping a conclusion whose reason has collapsed. I still do not declare the object, because it would explain no pixel the board does not already draw correctly and would enable no rule I can write, which is constraint 3 refusing it on its own terms. If a device ever appears that lets a guard read position, this declaration is the first thing to add."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_swap_also_fails_the_compression_test_and_that_blocker_needs_no_grammar_argument "suppose every expressibility obstacle vanished and I could read a cell's position freely. The swap would still not belong in the manual. It repaints 96 cells whose new colours follow no local law -- the widget is teleported six rows, which no event in the vocabulary does; moved is one cell, jumped-over is two, jumped-to-a-landmark needs a landmark and a rule per instance. The shortest form I can construct is on the order of one landmark and one rule per repainted cell, for both directions, which is longer than writing out the 96 pixels it explains. Constraint 3 refuses it independently of constraint 5, and unlike the guard argument this one does not depend on any reading of the grammar. Two independent refusals, and this is the reason I expect never to write the swap in this language rather than merely not to have written it yet."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem silence_on_the_selector_costs_one_transition_of_five "my manual is silent on key(1) and key(2), so it draws frame 0 at transition 0 where the world draws the swapped panel: one transition lost, the one certify reports. Transition 1 counts as a match because ACTION2 returns the world to frame 0 while my silent manual never left it, and transitions 2, 3 and 4 match because manual and world are back in step. That is 4 of 5, which is the score certify returned twice now. A partial or wrong swap rule would produce a frame equal to neither manual nor world at transition 0, would not be undone at transition 1, and would lose all five. Twenty percent of the record is a harsher price than the eight percent the longer record charged, and it still comes out the same way."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem the_blanking_guards_shrank_from_sixteen_atoms_to_eight_with_no_change_of_firing_set "the four blanking rules carried four negative neighbour guards each. I re-checked all 9 Pip and 10 Stud instances. Among Pips, only the port pip (38,16) must be spared and its left neighbour is a colour-0 cavity cell; no Pip anywhere has a background cell to its left, right or above, so three of the four guards excluded nothing and are deleted. Among Studs, the four bar studs form a 2x2 of colour 2 so each has a colour-2 horizontal neighbour, and the meter stud has the colour-2 bar to its left, so not-left-is-2 with not-right-is-2 spares all five where three separate guards did it before; the port stud still needs the cavity test. The meter seed loses its below-is-4 atom because exactly one Stud in existence has no right neighbour. Eight atoms deleted. The firing set is unchanged on every instance in every state this manual can reach -- 8 pips and 4 studs blank, 12 restore, 1 meter cell advances -- so the predicted replay stays 4 of 5 and this is a pure shortening."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem i_withdraw_the_claim_that_replay_is_confirmed_open_loop "I once confirmed open-loop replay by pre-registering that a resyncing checker would return 10 of 13 and getting 9. That separation lived in transitions this record does not contain. Here my only error is at transition 0 and the world hands the frame back at transition 1, so open-loop and resyncing both score 4 of 5 and nothing distinguishes them. I keep reading my coverage as open-loop because that is the conservative reading, but the status is pending. The separator is any transition on which my manual is wrong and the world does not immediately return to where my manual sits -- which the next tick of the bar will supply, since my manual now says the bar never moves again."
    [depends: silence_on_the_selector_costs_one_transition_of_five  probe: pending]

  theorem the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified "row 53 reads colour 2 from column 10 to column 62 and colour 3 at column 63, and the whole of my evidence about how it moves is one transition: at t4 an ACTION4 press turned (53,63) from 2 to 3. One tick cannot identify a cadence. All four readings remain alive -- a toll on the restore key, a toll on every key, a period in commands, a period in returned extra frames -- and I have no way to rank them. So the manual carries the seed rule, which fits the only expressible thing about that tick, that the cell with no right neighbour went first, and carries nothing about what happens next. The consequence is a deliberate under-claim: after t4 there is no colour-2 Stud whose right neighbour is off-board, so my manual says the bar never moves again and will be wrong at the next tick. I declare no landmark for (53,62) either, because a landmark is a cell and every event in the vocabulary takes an object."
    [depends: instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances  probe: passed]

  theorem the_seed_rule_is_a_one_shot_and_here_is_what_it_is_worth "key4_advances_the_meter_once has coverage 1/1 and by constraint 3 that looks like a rule spent on a single pixel. Its defence, at its true size: without it the current frame cannot be drawn at all, because (53,63) is colour 3 in every state from t4 onward and only this rule paints it. So it buys the last two transitions of the record. What it does not buy is understanding -- it is silent on why that tick fell on that press, and its rightof-is-wall guard makes it structurally unrepeatable, which is an honest way of saying it explains a boundary and not a mechanism."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: passed]

  theorem i_deleted_the_march_rule_and_i_flag_it_as_the_likeliest_error_in_this_draft "an earlier draft carried a rule marching the bar leftward on key(3), justified by a ledger scoring it 9 of 13 against 6 for silence over a record that no longer exists. It fires nowhere here, and a rule with coverage 0/0 is what constraint 2 forbids. So my commitment is flipped: the next key(3) press does not consume a bar cell. That is a change in what I am allowed to assert rather than a change of mind, and even if I wanted it back the arm forbids it, since (53,62) is board and carries no instance. If a longer record returns and the bar moves on key(3) presses, the rule comes back with its witnesses and with a colour-5 or landmark device to reach the cell."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_extra_frame_clock_is_down_to_one_point "the reading was that a command advances a hidden clock by its frame count minus one and the bar loses a cell every third advance, and it was once fitted to three ticks. This record has one. The advance count at the tick is four: t1 through t4 each returned two frames, t5 returned one and did not advance it. Four advances and one tick determine neither period nor offset, so this is a shape with no parameters left. It still makes one cheap qualitative prediction -- that ACTION7 is the only command so far that did not advance the world clock -- and that is testable by pressing ACTION7 and reading the frame count alone, with no cell comparison needed."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_toll_on_the_restore_key_reading_is_alive "in this record ACTION4 was pressed exactly once and the bar moved exactly once, which is the toll reading fitting perfectly with one point. My manual does not implement it, because implementing it means repainting (53,62), which is board and carries no instance. So the reading is untestable by replay and settled by one press: from the current blanked state, key(4) restores exactly twelve strip cells under my manual and thirteen cells including (53,62) under the toll reading. Cheapest open question in the game."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem i_do_not_know_which_way_the_bar_runs "one cell has gone from 2 to 3 at the right end of row 53. That is equally a resource being spent and a progress meter being filled, and colour 3 is also what an unselected slot shows on its rails, which argues weakly that 3 is a resting or completed state rather than a consumed one. Nothing in five transitions separates them, and they invert the sign of every ranking decision: under one reading a probe costs part of a budget, under the other it earns progress. Until something separates them the playbook may not rank on bar movement in either direction. The separator arrives on its own -- either the bar reaching column 10 ends the level, or NOT_FINISHED survives it."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_bar_is_between_fifty_three_and_sixty_three_cells_long "row 53 reads colour 2 over columns 10 to 62 and colour 3 at 63. I have never been shown columns 0 to 9 of that row, so 53 cells are measured unconverted and up to 63 exist if the bar reaches the left edge. Directly beneath it, row 54 reads colour 4 across the whole window and has never varied. Whatever the cadence turns out to be, the magnitude is safe in both directions: the bar is long compared with six actions, so probing is cheap now and will not stay cheap. I have stopped calling it a countdown."
    [depends: i_do_not_know_which_way_the_bar_runs  probe: pending]

  theorem the_strip_hides_and_shows_and_the_separator_is_still_one_action_away "key(3) blanked a shown strip at t3, key(7) blanked one at t5, key(4) restored a blanked one at t4, twelve cells and cell for cell identical each time, so the pattern lives somewhere the frame does not show. Both blank presses were made from a shown strip and the single restore from a blanked one, so hide-and-show and toggle-and-toggle are still indistinguishable. That key(3) and key(7) produced identical twelve-cell diffs is itself worth naming: they may be one function under two names, and no evidence separates them either. The state now is blanked and my manual commits to inert for a repeat of either blanking key -- every strip cell is colour 4, so no blanking guard can fire and no meter rule can fire. A restore under a blanking key refutes hide-and-show outright; nothing happening confirms it and also reads what a null command does to the frame count."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_restore_and_blank_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "the restore rules guard on colour 4 alone, and the blanking rules now guard on as few as one neighbour test. Both are correct on every press observed, because every press was made with the bottom slot selected, where the only colour-4 Pip and Stud instances in existence are the twelve blanked lane B cells. They would be wrong the moment slot A is selected: lane A strip cells become texture while lane B strip cells become arena fill of colour 4, and the instances do not move with the widget because I only ever recolour. My manual never reaches that state, being silent on the selector, so this costs zero transitions and certify cannot see it. It is written here because a searcher planning through a selector move would be misled by rules that score 12 of 12. The fix needs a guard that reads which slot is selected, and selection is exactly what the guard language cannot see."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have ever seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Twenty-one witnesses inside this brief. Frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, a period-3 run offset by one column; the divergence report gives lane A row 32 cols 16-22 as the world drew it at t1 -- 1 2 1 1 2 1 1 -- and rows 32 and 38 agree because 6 is divisible by 3. The two port cells fit the same formula, which is an unforced success. So the two strips are two windows onto one texture, which is why a restore can rebuild twelve cells exactly. Untested prediction: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2. No rule needs this, since each instance remembers its frame 0 colour, so by constraint 3 the concept buys understanding rather than symbols and stays out of the word table."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, twice now, twelve cells both times. (38,16)=1 and (39,16)=2 sit on the widget right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since the left neighbour of each is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The rival explanation is that col 16 is simply where the 6x6 widget ends and the survival is coincidence; two blanks do not separate them."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied, so they are board. Colour 3 at cols 13-14 is what an unselected slot shows at its four outer rows, and the unselected slot at rows 30-35 shows 3 3 2 2 3 3 down those columns, so row 29 sits where the last row of a slot at rows 24-29 would sit. The period is measured inside this brief: the divergence report gives the world's t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at those columns read identically -- eighteen cells, six rows apart. Rows 42 to 52 are uniform background, so rows 36-41 is the bottom slot. I read key(1) as moving selection up one slot and key(2) as down one. My manual is silent on both, so either press scores for free: from the bottom slot the down key does nothing under the move reading and repaints 96 cells under a two-slot toggle, and from the upper slot the up key repaints rows 24-35 if a third slot exists."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_badge_is_lane_aligned_but_it_is_not_the_same_shape_as_a_strip "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47, re-counted against the current frame. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45. Those are exactly the rows an upper-slot cavity occupies within its own six-row band, so the badge belongs to the lane of the slot at rows 30-35, and the bottom slot's lane has nothing at cols 42-45. But the strip is 2 rows by 6 cols and the badge is 4 rows by 4 cols of one uniform colour, so the tempting reading -- a target the lane texture must be made to match -- does not survive a shape comparison and I am downgrading it. The surviving readings are that it marks which slot carries a task, or that it is a destination something must reach. Zero transitions bear on either, and slots above row 29 may carry badges I have never seen, since an unvarying badge is board by definition."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_meter_cadence_is_inexpressible_and_i_rechecked_both_loopholes "a guard reads a cell colour, its four neighbour colours, off-board, and the action name. A cadence needs a count and there is no count in the grammar. Loophole one, an object whose declared colour equals the background used as an invisible latch bit: unusable, because the value grammar exposes only color as a field so no guard can read present, and the 24 colour-5 cells the arm would instantiate are all in the slot footprint, none of them where a latch would be wanted. Loophole two, a second object type declared at colour 2 to reach the next bar cell: unusable, because the arm finds objects by colour alone and would place a duplicate instance on all ten existing Studs. So the cadence stays prose, and with the march rule gone the manual carries no proxy for it at all, which is the smaller of the two available failures."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: passed]

  theorem nesting_a_cell_expression_is_the_one_device_that_could_break_the_swap_deadlock_and_i_have_not_tested_it "the grammar lists above, below, leftof and rightof as taking a cell, and lists cells exhaustively including those four forms, but does not say whether the argument may itself be one of them. If above(above(?p)) parses, guards gain a two-cell reach and the situation changes measurably: at depth two, (30,16) and (31,16) both see colour 3 two cells to their left while (32,16) and (33,16) see colour 2, which separates the pair that goes to 6 from the pair that goes to 1 and 2; at depth three below, (32,16) sees background and (33,16) sees casing, which separates the last two. So a position-reading device exists in principle. It does not change my verdict, because the compression blocker stands regardless and every such guard is pixel-fitting of the purest kind. I do not test it inside the manual because a parse error costs the whole round; it is a probe, and the cheapest form of the probe is a single throwaway rule with coverage 0/0 in a scratch manual, not this one."
    [depends: the_swap_also_fails_the_compression_test_and_that_blocker_needs_no_grammar_argument  probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot bar, a port, four strip cells and the meter cell -- four unrelated roles. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 73 cells that need an owner against 73 pixels written out, with 0 unexplained confirmed twice. The cost is measured too, and it got smaller this round: no rule can name the strip, so every blanking rule still carves it out of its colour class by neighbour tests, but the carving now costs eight guard atoms rather than sixteen, and the meter rule still needs an off-board test to separate one Stud from the other nine. Those guards remain pixel-fitting in a costume; there are simply fewer of them."
    [depends: the_blanking_guards_shrank_from_sixteen_atoms_to_eight_with_no_change_of_firing_set  probe: passed]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, which is rows 29-54 by cols 10-63. They live somewhere in the 3999 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is also where a title, target, score or instruction would live, and the most likely home of whatever finishing means. It is the largest thing I do not know, and the likeliest place the bar's direction is written down."
    [depends: no_goal_section_on_purpose  probe: pending]

  theorem two_keys_have_never_been_pressed "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not. The budget argument is unchanged in magnitude even though its sign is unknown: the bar is 53 cells or more from its end and six actions have been spent. If either key is a click carrying coordinates, this guard language cannot express it and the finding will be recorded as prose rather than as a rule. Each press also reads its own returned frame count, which is the only handle left on the clock."
    [depends: the_extra_frame_clock_is_down_to_one_point  probe: pending]

  theorem no_goal_section_on_purpose "all six states returned NOT_FINISHED and nothing in five transitions indicates what finishing means. The live candidates are that a lane must be brought into some relation with the badge at its far end, that every slot in the column must be visited or solved, or that the objective lives in the rows I have never been shown. An absent goal compiles to is_goal implies False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. I will not write a goal on the strength of a badge I have never interacted with, and this round's downgrade of the badge-matching reading makes me less willing, not more."
    [depends: i_do_not_know_which_way_the_bar_runs  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "mdl_segmenter returns negative gain on both variants, -4037 bits at 4 tracks and -10409 at 33, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator rather than the world; its tally of 4 recolors, 2 appears and 2 vanishes is nonetheless consistent with my reading that this world only ever recolours and that the appear/vanish pair is the swap seen as one blob. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition, and its own verdict says the world does not narrate as one mover, which agrees with my event vocabulary of recolored alone. zero_space calls its own evidence THIN in its own words -- 5 transitions constraining rank 3 of 679 features, null space of dimension 676 -- and its single global law spans 97 dynamic cells at once, which is what a 676-dimensional null space produces rather than what a conservation law looks like. What I took from the engines is the store arithmetic, dynamic_cells 97 and cells_needing_an_owner 73, and this round that arithmetic paid a second time by telling me exactly how many colour-5 instances a background object would get, which is what refuted my own second swap blocker."
    [probe: pending]

  theorem what_this_draft_pre_registers "certify should return replay 4 of 5, first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6; responsibility 0 unexplained of 4096; unambiguous 0 clashes. That is deliberately the same score as the previous draft, and it is now a real test rather than a formality: I deleted eight guard atoms, and if my re-derivation of the firing sets is wrong anywhere then t3, t4 or t5 will break and the score will fall to 3 or worse. Any drop below 4 is my error and localises immediately to the blanking or seed guards. The informative pre-registrations about the world are three, each decided by one press from the current blanked state. key(3) or key(7): my manual says the frame does not change at all, which refutes toggle-and-toggle if it holds and refutes my manual if the strip comes back. key(4): my manual says exactly twelve cells change and the bar does not move, while the toll reading says thirteen including (53,62). ACTION7 again: a second single-frame return would make it the only key that does not advance the world clock."
    [depends: the_blanking_guards_shrank_from_sixteen_atoms_to_eight_with_no_change_of_firing_set  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- eighth draft.
#
# NO NEW EVIDENCE ARRIVED THIS ROUND, so every evidence tag below still cites
# the same five transitions and I have not inflated one of them. Nothing here
# is a stored line of play; every entry is a ranking rule the searcher still
# has to evaluate against whatever state it is actually in.
#
# WHAT MOVED:
#
# 1. THE ORDER OF THE TOP THREE IS UNCHANGED AND I AM SAYING WHY RATHER THAN
#    RESTATING IT. Repressing a blanking key from the blanked state is first
#    because my manual pre-registers a completely null frame for it, which is
#    the strongest prediction I own and the cheapest to falsify. The restore
#    key is second because it separates twelve cells from thirteen. Retesting
#    the single-frame key is third because it costs a frame count and no cell
#    comparison at all.
#
# 2. ONE PRUNE WITHDRAWN. I had a prune saying no plan may rely on cells with
#    no instance. It was doing the work of a blanket ban when the truth is
#    narrower: a colour-5 object would own exactly the 24 swap-footprint cells
#    and nothing else, so the ban was overbroad. Replaced by the accurate one:
#    a plan may not rely on a cell that has never varied, because such a cell
#    is board and gets no instance whatever colour is declared.
#
# 3. ONE PRUNE ADDED ABOUT COST RATHER THAN EXPRESSIBILITY. A plan whose rule
#    set is longer than the pixels it draws is dead even if it replays, because
#    that is constraint 3 and it is the blocker that killed the swap for good.
#
# 4. STILL REMOVED, AND STAYING REMOVED: anything that ranks on the direction
#    of the bar. I cannot tell a budget being spent from progress being made,
#    and the two invert the sign of every such decision.

order   repress_a_blanking_key_in_the_blanked_state_to_test_the_inert_commitment  [proof: lean]
order   press_the_restoring_key_to_separate_the_toll_reading_from_the_rest  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_for_freedom_from_the_clock  [proof: lean]
order   test_whether_the_two_blanking_keys_are_one_function_under_two_names  [proof: lean]
order   settle_which_way_the_bar_runs_before_ranking_anything_on_it       [proof: lean]
order   press_the_two_never_pressed_keys_while_the_budget_is_still_long   [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule      [proof: lean]
order   make_some_cell_outside_the_observed_window_vary                   [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known          [proof: lean]
order   read_every_bar_cell_that_changed_and_the_returned_frame_count_after_every_command  [proof: lean]

prefer  an_action_the_manual_has_pre_registered_a_null_frame_for          [ev: 4/5 transitions replay]
prefer  an_action_on_which_two_live_readings_predict_different_frames     [ev: 4 meter readings open]
prefer  an_action_that_answers_more_than_one_open_question_at_once        [ev: 1 press separates 2]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/5 commands returned one frame]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  a_slot_never_selected_over_one_already_drawn_twice                [ev: 2 slots seen of a column]
prefer  a_state_whose_lane_carries_the_badge_over_a_lane_without_one      [ev: 1/2 lanes carry a badge]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats        [ev: 97/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced           [ev: 0/5 transitions test it]

heuristic bar_cells_still_unconverted                                    [admissible: lean]
heuristic slots_in_the_column_never_yet_selected                         [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed                          [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                    [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                     [admissible: lean]
heuristic open_questions_no_single_command_can_yet_separate              [admissible: lean]

prune   plan_that_rests_on_the_bar_direction_being_known => dead          [proof: lean]
prune   plan_that_prices_a_bar_cell_against_any_particular_key => dead    [proof: lean]
prune   plan_that_needs_a_cell_that_has_never_varied_to_change => dead    [proof: lean]
prune   plan_whose_rules_are_longer_than_the_pixels_they_draw => dead     [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_expects_the_manual_to_move_the_bar_a_second_time => dead  [proof: lean]
prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead     [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead       [proof: lean]
prune   plan_that_trusts_a_blank_or_restore_rule_across_a_selector_move => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead       [proof: lean]
prune   repeat_of_a_key_already_witnessed_inert_in_this_exact_state => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead      [proof: lean]
prune   bar_consumed and not goal => dead                                [proof: lean]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "colour class 6 (mdl_segmenter blob fragments)", "verdict": "accept",
   "as": "Casing", "why": "22 varying cells of colour 6 form the widget perimeter of rows 36-41 x cols 11-16 minus two ports plus the 2x2 core; declared arc-instances: all so each cell is its own instance."},
  {"id": "O-02", "subject": "colour class 0", "verdict": "accept",
   "as": "Cavity", "why": "12 varying cells, the 4x4 at rows 37-40 x cols 12-15 minus the core; its left-edge cells are what every blanking guard uses to spare the two port cells."},
  {"id": "O-03", "subject": "colour class 3", "verdict": "accept",
   "as": "Rail", "why": "8 varying cells at rows 30-31 and 34-35 x cols 13-14, the outer rows of the unselected slot; no rule names it, it exists to own pixels."},
  {"id": "O-04", "subject": "colour class 1", "verdict": "accept",
   "as": "Pip", "why": "9 varying cells: 8 strip cells plus the port pip at (38,16); the blanking rule fires on exactly the 8 and the port is spared by its colour-0 left neighbour."},
  {"id": "O-05", "subject": "colour class 2", "verdict": "accept",
   "as": "Stud", "why": "10 varying cells spanning four unrelated roles (4 bar, 1 port, 4 strip, 1 meter); the class is not a thing in the world and colour_classes_are_not_the_worlds_objects says so."},
  {"id": "O-06", "subject": "colour class 4", "verdict": "accept",
   "as": "Erased", "why": "12 varying cells at rows 32-33 x cols 17-22, the lane A strip footprint sitting at arena colour in frame 0."},
  {"id": "O-07", "subject": "a background object at colour 5 covering the 24 unowned dynamic cells", "verdict": "reject",
   "why": "checked and available -- 97 dynamic minus 73 owned is exactly the 24 swap-footprint cells, so the arm would place 24 instances and no more -- but it explains no pixel the board does not already draw correctly and enables no rule I can write, so constraint 3 refuses it; recorded in i_withdraw_the_no_instance_blocker."},
  {"id": "O-08", "subject": "a second colour-2 type to reach bar cell (53,62)", "verdict": "reject",
   "why": "the arm finds objects by colour alone, so a second colour-2 declaration duplicates instances on all ten existing Studs; and (53,62) has never varied so it is board and gets no instance under any declaration."},
  {"id": "O-09", "subject": "mdl_segmenter obj0/obj2/obj3 (440-cell, shape 13x36, colour null)", "verdict": "reject",
   "why": "connected_components(4) fused the panel with the arena across the port cells; both variants report negative gain (-4037 and -10409 bits), which is the engine refusing its own tracks."},
  {"id": "R-01", "subject": "key3_blanks_the_strip_pips", "verdict": "accept",
   "why": "8/8 at t3; guard set cut from four negative neighbour tests to one after checking all 9 Pip instances -- only the port pip needs sparing and only its colour-0 left neighbour does that work."},
  {"id": "R-02", "subject": "key3_blanks_the_strip_studs", "verdict": "accept",
   "why": "4/4 at t3; cut from four guards to three because the four bar studs form a 2x2 of colour 2 and the meter stud has the colour-2 bar to its left, so one pair of tests spares all five at once."},
  {"id": "R-03", "subject": "key7_blanks_the_strip_pips / _studs", "verdict": "accept",
   "why": "8/8 and 4/4 at t5, identical diff to t3; the grammar has no disjunction on act so the pair must be duplicated, and whether key(3) and key(7) are one function is left as a theorem."},
  {"id": "R-04", "subject": "key4_restores_the_strip_pips / _studs", "verdict": "accept",
   "why": "8/8 and 4/4 at t4; each instance remembers its frame-0 colour so the diagonal texture is rebuilt without any rule expressing it."},
  {"id": "R-05", "subject": "key4_advances_the_meter_once", "verdict": "accept",
   "why": "1/1 at t4; below-is-4 guard deleted as redundant since exactly one Stud in existence has no right neighbour. Without it the current frame cannot be drawn at all, which is its whole defence."},
  {"id": "R-06", "subject": "a rule set drawing the ACTION1/ACTION2 selector swap", "verdict": "reject",
   "why": "refused a third time on two independent grounds now: (30,16),(31,16),(32,16),(33,16),(34,16) present one identical guard reading and receive 6,6,1,2,6 (constraint 5), and any expressible form is about one rule per repainted cell, longer than the 96 pixels (constraint 3). The old no-instance ground is withdrawn as false."},
  {"id": "R-07", "subject": "a march rule stepping the bar leftward", "verdict": "reject",
   "why": "0 witnesses in this record, and (53,62) has never varied so it carries no instance and cannot be repainted by any rule however guarded. Flagged in i_deleted_the_march_rule as the likeliest error in the draft."},
  {"id": "R-08", "subject": "cegis_miner tracks obj0-obj3", "verdict": "reject",
   "why": "the engine refused all four itself; its precondition is one move event per transition and this world narrates as recolour only, which its own verdict states."},
  {"id": "L-01", "subject": "every_dynamic_cell_has_an_owner = 73", "verdict": "accept",
   "why": "22+12+8+9+10+12 reconstructed independently of the store and matching cells_needing_an_owner; responsibility returned 0 unexplained of 4096 for the second round running."},
  {"id": "L-02", "subject": "the last draft's pre-registration", "verdict": "entailed",
   "why": "certify returned all six predicted numbers exactly, which confirms my model of the checker and nothing about the world; recorded as such rather than as a discovery."},
  {"id": "L-03", "subject": "zero_space global law over 97 cells", "verdict": "reject",
   "why": "the engine's own adequacy verdict is THIN -- rank 3 of 679 features, null space dimension 676 -- so a law spanning every dynamic cell at once is an artefact of the null space, not a conservation."},
  {"id": "L-04", "subject": "open-loop replay confirmed", "verdict": "probe-pending",
   "why": "the 9-vs-10 separation that once confirmed it lived in transitions absent here; on this record open-loop and resyncing both score 4/5 and nothing distinguishes them."},
  {"id": "L-05", "subject": "the badge at rows 31-34 cols 42-45 as a pattern-matching target", "verdict": "reject",
   "why": "downgraded this round on a shape comparison I had not done: the strip is 2x6 of two colours, the badge is 4x4 of one colour 14, so they cannot be made to match. Its lane alignment with the upper slot survives."},
  {"id": "P-01", "subject": "repress a blanking key from the blanked state", "verdict": "probe-pending",
   "why": "manual pre-registers a completely null frame; a restored strip refutes hide-and-show and my manual at once, and nothing happening also reads what a null command does to the frame count."},
  {"id": "P-02", "subject": "press key(4) from the blanked state", "verdict": "probe-pending",
   "why": "twelve cells under my manual, thirteen including (53,62) under the toll reading -- the cheapest separator among the four live meter cadences."},
  {"id": "P-03", "subject": "press ACTION7 again and read the frame count only", "verdict": "probe-pending",
   "why": "a second single-frame return would make it the one key that does not advance the hidden clock; costs no cell comparison at all."},
  {"id": "P-04", "subject": "select slot A and read row 33 cols 17-22", "verdict": "probe-pending",
   "why": "the texture rule predicts 1 1 2 1 1 2 there, and that row has never been displayed in any state."},
  {"id": "E-01", "subject": "the 96-cell selector swap", "verdict": "probe-pending",
   "why": "wanted a rule that teleports a 6x6 widget six rows; the vocabulary offers moved (one cell), jumped-over (two cells), and jumped-to-landmark (one rule per instance). Wrote the_swap_also_fails_the_compression_test instead, which refuses it on cost rather than on grammar."},
  {"id": "E-02", "subject": "nested cell expressions such as above(above(?p))", "verdict": "probe-pending",
   "why": "wanted a two-cell guard reach, which measurably separates (30,16)/(31,16) from (32,16)/(33,16) at depth two and the last pair at depth three below. The grammar calls its cell list exhaustive without saying whether the argument may be a cell expression, so I wrote a theorem rather than risk a parse error that would cost the whole round."},
  {"id": "E-03", "subject": "the meter cadence", "verdict": "probe-pending",
   "why": "wanted a counter; the guard language has no count and no memory, and both loopholes are shut (present is not readable as a value, and a duplicate colour-2 type collides with the ten existing Studs). Wrote the_meter_cadence_is_inexpressible."},
  {"id": "E-04", "subject": "a guard reading which slot is selected", "verdict": "probe-pending",
   "why": "wanted it to make the blank and restore rules honest across a selector move; selection is global state and guards are local. Wrote the_restore_and_blank_rules_are_conditioned_on_a_selection so a planner is warned off rules that score 12/12."}
]
```
```
