# call-001-theorize-round1

model: `claude-opus-5` · 1676135 ms · $5.498692 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 175077, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 175077, "cache_read_input_tokens": 60832, "inference_geo": "not_available", "input_tokens": 6, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 64065, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 64065, "cache_read_input_tokens": 57302, "input_tokens": 2, "output_tokens": 18992, "type": "message"}], "output_tokens": 146992, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
    "ms": 5,
    "script_bits": 7512,
    "split_by_color": false,
    "tracks": 4
   },
   {
    "baseline_bits": 3475,
    "compression_ratio": 3.995396,
    "events": 61,
    "gain_bits": -10409,
    "ms": 17,
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
# theory.dsl -- world observed for 26 states / 25 transitions
#   RESET, A1 A2 A3 A4 A5 then A2 A5 repeated eleven times.
# 83 cells have ever changed; this manual names and owns all 83.
#
# WHY THIS ROUND EXISTS, IN ORDER OF WHAT IT IS WORTH.
#
# 0. THE ADVANCE PREDICTION CASHED FOR THE THIRD ROUND RUNNING, INCLUDING THE
#    HEADLINE ONE THAT WAS ABOUT THE ARM AND NOT THE WORLD. I wrote: the next
#    command WILL BE ACTION2, because key 2 is the only key with a live rule at
#    spawn. t22 was ACTION2. I wrote: the world burns (63,53) and the manual is
#    refuted by exactly one cell. t22 burned (63,53); t24 burned (63,52). I
#    wrote: the realised gain comes back 5.087463 and nothing is learned. P-17
#    and P-19 report 5.087463; P-18 and P-20 report 3.5025. Eight and eight now.
#
# 1. THE FINDING OF THIS ROUND AND IT KILLS MY OWN PREVIOUS READING. Last round
#    I wrote that expected_bits MOVES with the state while realised gain does
#    not. FALSE. The four expected_bits this round are
#    1.394848870026, 2.2195282823, 1.955012006402, 2.273661689922 -- BIT FOR BIT
#    THE SAME FOUR NUMBERS, IN THE SAME ORDER, AS LAST ROUND'S FOUR PROBES.
#    The prior is PERIOD-4, and period 4 is exactly one full lap-pair. It is a
#    function of (key, panel configuration) and of NOTHING ELSE -- not of the
#    meter, which differs by two burned cells between the two rounds. See
#    the_expected_gain_is_period_four_and_therefore_also_measures_only_my_manual.
#
# 2. THE EDIT I HAVE REFUSED FOR FIVE ROUNDS AND AM MAKING NOW, WITH THE CHECK
#    THAT LICENSES IT. Thirteen panel rules carried colored(spawn_probe, 5).
#    That conjunct has ELEVEN positive witnesses and ZERO negative witnesses,
#    because ACTION5 has never once been pressed with the body at home. It is
#    not a law I observed; it is a description of where ACTION5 happened to be
#    pressed. Constraint 3 says a conjunct earns its place by explaining
#    something -- this one explains no pixel of any observed frame. I REMOVE IT
#    FROM ALL THIRTEEN RULES. Replay is provably unaffected (no observed A5
#    press had the body at home, so the conjunct was true wherever it was
#    evaluated) and I re-audited constraint 5 at all thirteen body-home states
#    in both panel configurations: forward and reverse rules stay separated by
#    colour alone, and no panel rule can reach a body, spawn-ring or meter
#    instance. See the_unwitnessed_guard_is_removed_and_this_is_not_gaming.
#
# 3. THE CONSEQUENCE I WANT ON THE RECORD BEFORE IT HAPPENS. That edit is the
#    first thing at this desk in five rounds that changes the RANKER's
#    arithmetic honestly. At spawn, TWO keys now have live rules -- key 2
#    (48 body pixels) and key 5 (23 panel pixels) -- so the ensemble can
#    disagree there for the first time, and the loop is no longer forced at the
#    spawn end. If ACTION5 at spawn toggles the panel I was right and I bought
#    it for nothing. If it changes nothing I am refuted by 23 cells and the
#    guard was real and goes straight back in. EITHER ANSWER IS INFORMATION;
#    THE SILENCE I WAS DEFENDING WAS NOT, AND COULD NEVER BE BOUGHT.
#
# 4. WHAT I STILL REFUSE. I do NOT write a rule for ACTION2 at lattice (2,2).
#    That has ZERO witnesses of any kind, and adding it would be the
#    fabrication constraint 2 exists to stop. Deleting an unwitnessed
#    RESTRICTION and inventing an unwitnessed RULE are opposite moves and I am
#    only making the first.
#
# 5. THE ONE MONOTONE QUANTITY. 12 cells burned, 52 remain. Eleven laps.
#
# EXPECTED REPLAY: 25/25.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t25 compress: 47]
  Vacated [segment: dynamic_colour_5 ev: t2-t25 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5-t25 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5-t25 compress: 3]

events:
  event recolored(o, c)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20,t22,t24 cov: 264/264]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20,t22,t24 cov: 264/264]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25 cov: 264/264]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25 cov: 264/264]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12,t14,t16,t18,t20,t22,t24 cov: 10/10]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25 cov: 48/48]
    when act=key(5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25 cov: 18/18]
    when act=key(5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25 cov: 18/18]
    when act=key(5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25 cov: 18/18]
    when act=key(5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25 cov: 6/6]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25 cov: 6/6]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25 cov: 6/6]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13,t17,t21,t25 cov: 18/18]
    when act=key(5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23 cov: 40/40]
    when act=key(5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23 cov: 15/15]
    when act=key(5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23 cov: 40/40]
    when act=key(5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23 cov: 5/5]
    when act=key(5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11,t15,t19,t23 cov: 15/15]
    when act=key(5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 47 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: inferred-from-replay]
  invariant board_cells count(board) = 4013 [status: counted]
  invariant meter_cells_burned_right_now count(Glyph9, color = 1) = 12 [status: state-dependent-not-an-invariant]

  theorem the_unwitnessed_guard_is_removed_and_this_is_not_gaming "THE EDIT OF THIS ROUND AND THE ONE THING AT THIS DESK THAT HAS EVER CHANGED THE RANKER HONESTLY. Thirteen panel rules carried colored(spawn_probe, 5), which reads: the body is not at home. That conjunct has ELEVEN positive witnesses and ZERO negative witnesses, and the zero is structural, not accidental -- every ACTION5 in twenty-six states was pressed from lattice (2,2), so the conjunct was TRUE BY CONSTRUCTION at every press. It is not an observed condition, it is a transcription of where the presses happened to occur. Constraint 3 asks what pixel it explains: NONE. So it goes. THE THREE CHECKS THAT LICENSE THE DELETION, each done cell by cell before writing it. REPLAY: no observed transition is affected, because the conjunct was true wherever it was evaluated and false nowhere, so the compiled step returns the same successor on all twenty-five transitions -- I expect 25/25 unchanged and I will be caught in one round if I am wrong. AMBIGUITY: the deletion newly grounds the thirteen rules at the thirteen body-home states, seven in configuration A and six in B. In A the eight forward rules fire on slot 1 at colour 9 rows 1-3, underline 1 at colour 9 row 5, slot 2 at colour 1, underline 2 at colour 0 -- 8+3+9+3 = 23 cells -- and all five reverse rules are dead because no Glyph9 renders 2 or 0, no Spent renders 9 or 0, no Dark renders 9. In B the five reverse rules fire on exactly those 23 cells and all eight forward rules are dead by the mirror argument. RESPONSIBILITY: no new cell is claimed; the same 23 panel instances are involved. THE THIRD CHECK THAT MATTERS MOST -- can a panel rule now reach the body, the spawn ring or the meter, which the guard was implicitly shielding? NO, and the reason is the off-board arithmetic, not the guard: key5_slot1_dims needs above-four to be wall, true only in rows 0-3; key5_underline1_dims needs above-six to be wall, true only in rows 0-5; the spawn ring is rows 8-12 and the meter is row 63. The reverse rules are colour-keyed and the spawn ring renders only 9 or 5 while the meter renders only 9 or 1, and no reverse rule claims 9-on-Glyph9 or 1-on-Glyph9. SO THE PREDICTION CHANGES AT EXACTLY ONE PLACE: ACTION5 AT SPAWN NOW TOGGLES THE PANEL AND MOVES NO BODY PIXEL. That is falsifiable in a single press and it costs no meter cell. I say the uncomfortable part plainly rather than burying it: I am aware this makes key 5 non-silent at spawn and therefore makes it purchasable by a ranker that could never buy it before. THE EDIT IS JUSTIFIED WITHOUT THAT EFFECT -- an unwitnessed conjunct fails constraint 3 on its own -- and the effect is a consequence, not the reason. The test of whether I am fooling myself is the opposite move, which I continue to refuse: I do NOT add a rule for ACTION2 at lattice (2,2), because that has no witness at all and would be manufacture rather than de-restriction."
    [depends: key5_slot1_lights, key5_slot1_dims, the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: pending]

  theorem the_expected_gain_is_period_four_and_therefore_also_measures_only_my_manual "I WAS WRONG LAST ROUND AND THE CORRECTION MATTERS. I wrote that expected_bits MOVES with the state while the realised gain is pinned, and I read the mismatch as the signature of an artefact. The mismatch does not exist. The four probes this round report expected_bits 1.394848870026 for action 2, 2.2195282823 for action 5, 1.955012006402 for action 2, 2.273661689922 for action 5 -- and those are, to the last digit, the same four numbers in the same order that P-13 through P-16 reported last round. THE PRIOR IS PERIODIC WITH PERIOD FOUR, and four commands is exactly one lap-pair. Line the probes up against the panel: action 2 pressed with the panel in configuration B scores 1.394848870026 at t18 and 1.394848870026 at t22; action 2 in configuration A scores 1.955012006402 at t20 and at t24; action 5 from B scores 2.2195282823 at t19 and t23; action 5 from A scores 2.273661689922 at t21 and t25. EXPECTED BITS IS A FUNCTION OF THE KEY AND THE PANEL CONFIGURATION AND OF NOTHING ELSE. In particular it does not see the meter, which burned two further cells between the two rounds, and it does not see the elapsed laps. Joined to the realised gains, which came back 5.087463 and 3.5025 for the eighth time each, the conclusion is stronger and simpler than the one I retract: BOTH THE PRIOR AND THE POSTERIOR ARE FUNCTIONS OF MY MANUAL'S FIXED GEOMETRY AGAINST ITS OWN ABLATIONS, EVALUATED AT ONE OF FOUR RECURRING CONFIGURATIONS. Nothing in either number is a measurement of the world. n_survivors corroborates and is likewise period-2: 1 for every action 2, 3 for every action 5. OPERATIONAL CONSEQUENCE: a gain that repeats is zero gain, and now a gain that CAN repeat is identifiable in advance from the panel alone."
    [depends: the_realised_gain_is_pinned_while_the_expected_gain_moves, the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: passed]

  theorem the_realised_gain_is_pinned_while_the_expected_gain_moves "SUPERSEDED BY the_expected_gain_is_period_four_and_therefore_also_measures_only_my_manual AND KEPT ONLY AS THE RECORD OF A CORRECTION. Its claim was that the prior varies with the state while the posterior collapse does not. Two further probes of each action showed the prior repeating bit for bit, so the premise was an artefact of my having seen only four samples of a period-four sequence. The conclusion it drew -- that these numbers measure my manual and not the world -- survives, and is now supported by a stronger argument than the one it used. I record the retraction rather than editing the earlier text away, because a desk that silently rewrites its own past readings cannot be audited."
    [depends: the_expected_gain_is_period_four_and_therefore_also_measures_only_my_manual  probe: passed]

  theorem the_ranker_can_only_buy_what_my_rules_already_fire_on "THE STANDING EXPLANATION OF ELEVEN IDENTICAL LAPS, AND THIS ROUND IT IS PARTLY DISARMED RATHER THAN MERELY DESCRIBED. The probe reports name their own hypothesis space: every hypothesis is the manual or an ablation of it, plus inert, 34 of them. An ablation DELETES rules. A deleted rule cannot fire, so an ablation predicts a SUBSET of the manual's changes and never a superset. Take any state-action pair on which the manual predicts identity: the manual changes nothing, every ablation therefore changes nothing, inert changes nothing, ALL 34 HYPOTHESES AGREE, and the expected gain is zero. A MANUAL CANNOT PROBE ITS OWN SILENCES. Applied to the board as it stood before this round's edit: at spawn only key 2 had a live rule, at lattice (2,2) only key 5 had one, so at each of the two reachable states exactly one action had nonzero expected bits and the cycle was forced -- twenty-one consecutive commands drawn from {A2, A5}, all predicted by the two-state cycle. THE PART THAT IS NEW. I looked again for a lever that was mine and found one, and it was not a rule to add but a guard to remove: see the_unwitnessed_guard_is_removed_and_this_is_not_gaming. AT SPAWN THERE ARE NOW TWO LIVE KEYS, so the ensemble can disagree at that state for the first time in twenty-six frames. This does not repeal the theorem -- at lattice (2,2) key 5 is still the only live key, and keys 1, 3, 4, 6, 7 are still silent everywhere and still unbuyable -- but it shows the general claim I made last round, that the manual can NEVER buy the experiment that would extend it, was too strong. THE CORRECT STATEMENT IS NARROWER: a manual cannot buy an experiment at a pair it calls silent, and the only silences it can honestly stop calling silent are the ones held there by an unwitnessed restriction rather than by an absence of evidence."
    [depends: the_unwitnessed_guard_is_removed_and_this_is_not_gaming, the_loudest_forged_silence_is_not_at_spawn  probe: pending]

  theorem the_playbook_and_the_ranker_are_exactly_anti_aligned "The corollary that explained five rounds of a playbook binding nothing, now amended by the same narrowing. My playbook ranks by keys whose inertness here rests on no witness -- that is, by actions the manual PREDICTS SILENT. The ranker scores expected bits, which is ZERO for exactly those actions. The two criteria were complements by construction, and every command the playbook put first was a command the ranker put last. WHAT CHANGED. Item 2 of the previous list, ACTION5 at spawn, has crossed the line: after the guard deletion my manual predicts it draws 23 panel pixels, so it is no longer one of my own silences and the ranker can price it above zero. The anti-alignment therefore holds for items 1, 3 and 4 -- the east key, ACTION2 at lattice (2,2), and ACTION6/ACTION7 -- and is broken for item 2. THE LESSON GENERALISES AND I STATE IT AS THE RULE FOR THIS DESK: the way to move a probe from the playbook into the ranker's reach is not to argue for it in prose, it is to find the unwitnessed conjunct that is holding the manual silent there and delete it. Where no such conjunct exists, the silence is real ignorance and prose is all I have."
    [depends: the_ranker_can_only_buy_what_my_rules_already_fire_on, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: pending]

  theorem the_loop_pins_key_to_parity_and_therefore_seals_the_meter "The loop pressed key 2 at every even command index and key 5 at every odd one, for twenty-one consecutive commands. Reading A of the meter says a burn happens iff the key is 2 or 4. Reading B says iff the index is even. On the loop, key-2-ness and even-ness are the same predicate, so the two readings agreed on EVERY command the ranker was capable of choosing: twenty-five transitions have produced twelve burns at indices 2,4,6,8,10,12,14,16,18,20,22,24 under keys 2,4,2,2,2,2,2,2,2,2,2,2 and thirteen non-burns at indices 1,3,5,7,9,11,13,15,17,19,21,23,25 under keys 1,3,5,5,5,5,5,5,5,5,5,5,5, with not one divergence. The separating observation is unchanged: ANY press of key 1, 3 or 5 at an EVEN index. IT IS NOW BUYABLE FOR THE FIRST TIME. The next index is 26, which is even, and after this round's guard deletion ACTION5 at spawn has a live rule, so a ranker that prefers it splits the two readings for free. Reading A predicts no burn and the twelve burned cells stay at columns 52 through 63; reading B predicts (63,51) turns colour 1. I encode reading A because it is the only one this grammar can express -- there is no command counter in the guard language -- and I will read the answer off the RAW DIFF, because under reading B the burn is undrawable by my manual anyway."
    [depends: meter_burn_key2_next, meter_burn_key4_next, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: pending]

  theorem the_meter_is_the_only_monotone_quantity_in_this_world "The only thing that makes the loop expensive. Body position cycles between two lattice cells. The panel cycles between two configurations. The state count says so: 26 states, 24 distinct, and the only two collisions are the ancient sterile pair at t0/t1 and the pair at t2/t3 -- every later state is nominally distinct ONLY because row 63 has one more cell burned. Twelve cells are burned, columns 52 through 63; FIFTY-TWO REMAIN. Eleven laps have cost eleven of them, so a lap costs one burn and two commands, and the loop can run about 104 more commands before row 63 is fully colour 1. What happens then is not in evidence and I will not guess. A quantity that only ever moves one way, in a world where everything else returns, is either a budget or a timer, and either way the arm has been spending it at one cell per two commands to learn nothing."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot, the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: pending]

  theorem the_advance_prediction_cashed_a_third_time_including_the_one_about_the_arm "Third consecutive round in which the written-in-advance prediction cashed in full, and this time the headline was a prediction about the ARM rather than the world, which is the harder kind. I wrote, before seeing the frames: the next command WILL BE ACTION2, because the body is at spawn and key 2 is the only key with a live rule there. It was. I wrote: 48 body pixels drawn correctly, zero meter pixels drawn, the world burns (63,53), the manual refuted by exactly one cell, the gain reported as 5.087463 again. t22 changed 49 cells over cols 14-53 -- 48 body plus the burn at (63,53) -- and t24 changed 49 over cols 14-52 with the burn at (63,52). P-17 and P-19 report 5.087463; P-18 and P-20 report 3.5025. I also wrote that the panel would be in configuration B with slot 1 a hollow colour-2 ring and underline 2 lit, and the current frame reads exactly that at rows 1-3 and row 5. THE ONE THING I PREDICTED THAT DID NOT COME TRUE IS THAT expected_bits WOULD KEEP MOVING; it repeated, and the retraction is in the_expected_gain_is_period_four_and_therefore_also_measures_only_my_manual. Writing predictions that can cost me is the only mechanism at this desk that has ever caught me, and this round it caught me once."
    [depends: the_expected_gain_is_period_four_and_therefore_also_measures_only_my_manual  probe: passed]

  theorem the_four_refutations_are_one_defect_and_i_am_again_installing_nothing "P-17 and P-19 are action 2; P-18 and P-20 are action 5; heuristic_miss is the goal and is answered separately. The action-2 divergence is one cell each time and I can name it: t22 changed 49 cells over rows 8-63 cols 14-53, being 48 body pixels plus the burn at (63,53); t24 changed 49 over cols 14-52, being 48 body plus (63,52). All 48 body pixels sit on the spawn ring and the ring one lattice cell south, both fully instanced, and key2_body_leaves and key2_body_arrives draw them exactly, now eleven times each. The unburned frontier cell was board at the moment of the press and held no instance, so no event in this language could touch it. The action-5 divergence contains no new cell at all: t23 and t25 each changed 71 cells over rows 1-18 cols 1-18, being 48 body plus 23 panel, and every one is fired by exactly one rule -- 24 by key5_body_clears, 24 by key5_body_respawns, and for the two panel directions either 8+3+3+3+1+1+1+3 forward or 8+3+8+1+3 reverse, each summing to 23 with nothing over. THERE IS NO RULE TO ADD FOR ANY OF THE FOUR, and the one edit I did make this round is a DELETION, not an answer to these. I refuse to answer a refutation with a rule when I cannot name the pixel the rule would draw, because inventing one is how two earlier rounds were spent."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot, the_probe_tier_rolls_my_state_forward_and_never_resyncs  probe: passed]

  theorem the_probe_tier_rolls_my_state_forward_and_never_resyncs "Action 5 has no undrawable cell in it: at t23 and t25 the 71 changed cells are all instanced and all fired by exactly one rule, so a probe predicting from the OBSERVED frame would predict action 5 exactly and P-18 and P-20 would not exist. They do exist, at an identical gain, for the fifth and sixth time. THE LEADING READING IS THEREFORE THAT THE PROBE PREDICTS FROM THE MANUAL'S OWN ROLLED-FORWARD STATE, which already carries the burn the manual could not draw at the preceding action 2. If that is right, THE DEBT IS CUMULATIVE AND PERMANENT: once the manual misses one pixel it is behind for every subsequent action, so every future command looks refuted whatever it is, and no edit repairs it because the missed pixel is undrawable by construction. n_survivors = 3 for action 5 against 1 for action 2 is consistent with this -- an ablation of my manual fits the rolled-forward observation better than my manual does, which is what a state offset looks like from the ensemble's side. The mitigation is unchanged and free: under reading A of the meter the debt only grows on keys 2 and 4. I record the competing reading honestly: the hash might cover something beyond the frame, in which case the action-5 refutations mean something I have not found. THE DISCRIMINATING OBSERVATION IS A PRESS OF ACTION 5 IMMEDIATELY AFTER A PRESS THAT BURNED NOTHING, and for the first time in five rounds that observation is purchasable, because ACTION5 at spawn is now a live rule and the press before it need not be a key 2."
    [depends: the_burn_frontier_is_a_permanent_one_pixel_blind_spot, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: pending]

  theorem the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease "My answer to heuristic_miss, which has now fired seven times, and it is unchanged because the arithmetic is unchanged. The surprise says declaring the winning condition is the highest-value edit available. TESTED AND FALSE ON THIS BOARD. Suppose I could write a sound goal. The plan tier reaches it by searching MY compiled rules. Enumerate what my rules can do: key2_body_leaves and key2_body_arrives move the body from spawn to one cell south, key5_body_clears and key5_body_respawns move it back, the panel rules toggle 23 panel pixels, the burn rules are ungroundable. THAT IS THE WHOLE REACHABLE SET: TWO LATTICE CELLS AND TWO PANEL CONFIGURATIONS. So the only goals that could ever return sat are goals satisfied inside the loop, and sat-inside-the-loop is strictly WORSE than unsat: unsat leaves the arm probing, while sat makes it commit and declare success one lattice cell from where it started. I re-checked every candidate the grammar admits over the four types that carry instances, with this round's counts. count(Glyph9, color = 5) = 24 means the body is off spawn: not a win. count(Vacated, color = 9) = 24 is the same thing from the other side. count(Dark, color = 9) = 3 means the panel is in configuration B: not a win. count(Glyph9, color = 1) = 64 exceeds the 47 instances that exist and can never be true; count(Glyph9, color = 1) = 47 would require the spawn ring and both panel groups to burn, which no rule can do. count(Spent) = 0 is constant-false because Spent always has 9 instances. THEREFORE I DECLINE THE GOAL SECTION FOR THE FIFTH TIME AND I NAME WHAT WOULD END THE DECLINING: one observation in which the body occupies a THIRD lattice cell. That single observation seats instances on 24 cells that have never changed, extends the transition model past the loop, and is the same observation that eventually makes the socket writable. THE GOAL IS BOUGHT WITH A COMMAND. NO EDIT CAN SUBSTITUTE."
    [depends: the_goal_i_still_cannot_write_is_the_real_one, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_loudest_forged_silence_is_not_at_spawn "The cheapest large error in this manual, and after this round's edit it is the LAST of the four forged silences still holding the loop shut. Ask what my compiled rules predict for ACTION2 pressed with the body ONE CELL SOUTH of spawn, at lattice (2,2), a cell the body has now occupied eleven times. key2_body_leaves grounds only on Glyph9 and requires colored(?p, 9): the spawn ring renders 5 when the body is away, the twelve burned meter cells render 1, slot 1 renders 2 or 9 with nothing but background six rows below it, so NO GLYPH9 INSTANCE SATISFIES IT. key2_body_arrives grounds only on Vacated and requires colored(?v, 5): the lower ring renders 9 when the body stands there, so NO VACATED INSTANCE SATISFIES IT EITHER. THE COMPILED STEP IS TOTAL, SO MY MANUAL ASSERTS THAT ACTION2 AT LATTICE (2,2) DOES NOTHING. That is almost certainly false: rows 20-24 are floor from column 13 to column 31, so lattice (3,2) is open, and one press of action 2 has moved the body exactly one lattice cell south on eleven consecutive occasions over open floor. I DO NOT INSTALL A RULE FOR IT, and this round I can sharpen why the two cases are different rather than just asserting it. The spawn-probe conjunct I deleted was a RESTRICTION on rules with eleven witnesses each, and deleting it removed a claim I could not support. A rule for action 2 at (2,2) would be a new claim with ZERO witnesses of any kind -- every key-2 press in the log was made from spawn -- and half its divergence would fall on rows 20-24 columns 14-18, twenty-four cells that have never changed and therefore hold no instance, so I could not even draw the half I believe in. DELETING AN UNWITNESSED CONJUNCT AND ADDING AN UNWITNESSED RULE ARE OPPOSITE MOVES AND ONLY ONE OF THEM IS HONEST. The price stays advertised."
    [depends: the_ranker_can_only_buy_what_my_rules_already_fire_on, silence_is_a_prediction_and_two_of_my_spawn_silences_are_still_forged  probe: pending]

  theorem the_burn_frontier_is_a_permanent_one_pixel_blind_spot "Row 63 is a 64-cell colour-9 bar that burns one cell at a time from the right. TWELVE cells are burned and the current frame shows them: columns 52 through 63 render 1, columns 0 through 51 render 9. The order was (63,63) at index 2 under key 2, (63,62) at 4 under key 4, then (63,61) through (63,52) at indices 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, every one under key 2. The thirteenth burn will land on (63,51). (63,51) has never changed in twenty-six frames, so it is board, so it holds no instance, so NO EVENT IN THIS LANGUAGE CAN TOUCH IT -- recolored takes an object as its first argument and there is no object there. Therefore my manual predicts, and must predict, that the next press of a burning key burns nothing, and the world will burn (63,51) and the manual will be wrong by exactly one pixel. Then (63,51) becomes dynamic, the arm seats a Glyph9 on it, replay draws the burn retroactively, certify reports a perfect replay, and the cycle repeats on (63,50). THAT IS WHY certify SAYS THE REPLAY IS EXACT WHILE THE PROBE DESK SAYS THE MANUAL WAS WRONG: they ask about different times. Replay looks backwards through a census that already contains the burned cell; prediction looks forwards through one that cannot. All twelve meter instances currently render 1, so meter_burn_key2_next and meter_burn_key4_next have no grounding left and can only ever fire in replay. 52 cells remain unburned."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem no_goal_section_and_the_exact_enumerated_reason "A goal may say count over a declared type, optionally filtered by colour, or an instance's pos equal to a landmark. The types carrying instances are Glyph9 with 47 cells -- 8 slot-1 ring pixels, 3 underline-1 pixels, the 24 spawn-ring pixels, 12 burned meter cells -- Vacated with the 24 pixels of the ring one lattice cell south, Spent with the 9 pixels of slot 2, and Dark with the 3 pixels of underline 2. EVERY INSTANCE I HAVE IS IN THE PANEL, ON THE SPAWN RING, ON THE RING ONE CELL SOUTH, OR ON THE METER, and none is within thirty rows of the socket. The pos form is dead for a separate reason: this world never MOVES anything, every rule in this manual is a recolour, no instance's pos has changed in twenty-six states, so X.pos = landmark is a constant for every X I can declare. What unlocks the goal line is an OBSERVATION and not an edit."
    [depends: the_missing_goal_is_a_symptom_and_the_missing_transition_is_the_disease, the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: passed]

  theorem the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught "Kept because it is the reason a whole earlier round was lost and because it generalises. The compiler refused the entire manual over one clause, a count over a type with zero instances, saying: this level declares no instance of that type, so the count is 0 on every state and the clause decides nothing. A COUNT OVER A TYPE WITH ZERO INSTANCES IS NOT A FALSE PREDICATE, IT IS A REFUSED CLAUSE. The general form: THE GOAL LANGUAGE CAN ONLY SPEAK ABOUT CELLS THAT HAVE ALREADY CHANGED, because only those carry instances -- the same wall as the burn frontier met from the other side. One consequence I reconsidered again this round and again REJECT: declaring a colour-8 type as INSURANCE, so that the first comb pixel to change would already have an owner. The declaration alone was accepted last time and only the count was refused, so it probably compiles -- but the arm would seat ZERO instances of it today, which is the exact configuration that killed a round before, and the two costs are wildly asymmetric. If I am right I save one round of a responsibility warning; if I am wrong I lose an entire round of every tier, which has now happened twice. An unexplained pixel is a defect the next desk repairs in one round. An uncompilable manual is a round nobody gets back."
    [depends: a_declaration_is_only_as_true_as_the_arm_can_seat_it  probe: passed]

  theorem dynamic_census "Exactly 83 cells have ever changed and every one has an owner. 23 are the panel: slot 1 at rows 1-3 columns 1-3 contributes its 8 ring pixels, its centre (2,2) rendering colour 0 in BOTH configurations and therefore board; underline 1 is row 5 columns 1-3, three cells; slot 2 at rows 1-3 columns 5-7 contributes all NINE cells, centre included, because (2,6) renders 1 in configuration A and 0 in B; underline 2 is row 5 columns 5-7, three cells. 24 are the spawn ring, rows 8-12 columns 14-18 minus the aperture (10,16), which has never changed and is board. 24 are the same ring six rows south, rows 14-18 columns 14-18 minus its aperture (16,16). 12 are the burned right end of row 63, columns 52 through 63. 23+24+24+12 = 83 = dynamic_cells exactly, and 4096-83 = 4013 = constant_cells exactly. By frame-0 colour: 47 colour-9 being 8 slot-1 ring plus 3 underline-1 plus 24 spawn ring plus 12 meter, 9 colour-1 being slot 2 solid in configuration A, 24 colour-5 being the lower ring which was floor at frame 0, and 3 colour-0 being underline 2 dark at frame 0. 47+9+24 = 80 = cells_needing_an_owner exactly. Every one of these four sums moved by exactly the two meter cells burned this round and by nothing else, for the third round running."
    [probe: passed]

  theorem the_cascade_length_reads_the_panel_and_it_is_now_eleven_for_eleven "ACTION2 pressed with the panel in configuration A returns SEVEN internal frames: t2, t8, t12, t16, t20, t24. Pressed in configuration B it returns NINE: t6, t10, t14, t18, t22. ELEVEN PRESSES, ELEVEN CORRECT, no counterexample, and the configuration before each press is fixed by the alternation ACTION5 drives -- A,B,A,B,A,B,A,B,A,B,A in press order. All eleven ACTION5 presses returned 9 frames regardless of configuration. THE NET DISPLACEMENT IS IDENTICAL IN ALL ELEVEN ACTION2 PRESSES -- 49 cells changed each time, 24 out, 24 in, one burn, six rows south, one lattice cell -- so what the panel changes is the ANIMATION and not the distance, at least over open floor. My semantics say cascade single_frame, so I compare only the net and this costs me no replay accuracy; I record it as an observation my own semantics discard. It is also the cleanest independent confirmation that the panel really is a two-state variable and not decoration, because the frame count reads it from outside my rule set entirely."
    [depends: key2_body_arrives  probe: passed]

  theorem the_panel_is_a_two_slot_mode_selector_and_the_mode_may_gate_terrain "The reading I hold, stated as a reading, re-read pixel by pixel against the current frame. Two 3x3 tokens sit at rows 1-3 columns 1-3 and columns 5-7, with a 3-cell underline beneath each at row 5. The underline of exactly one slot is lit colour 9 at any time and ACTION5 moves the light: configuration A lights underline 1, configuration B lights underline 2, and in twenty-five transitions I have never seen both lit or neither. Right now row 1 reads 222 at columns 1-3 and 999 at columns 5-7, row 2 reads 2,0,2 and 9,0,9, row 3 reads 222 and 999, row 5 reads 000 and 999 -- slot 1 a hollow colour-2 ring with underline 1 dark, slot 2 a hollow colour-9 ring with a dark centre and underline 2 lit. CONFIGURATION B. The token in the LIT slot is always drawn as a HOLLOW colour-9 ring with a dark centre, which is the shape of the body itself, a rigid block with a one-pixel aperture. The token in the unlit slot differs by slot: slot 1 unlit is a hollow colour-2 ring, slot 2 unlit is a SOLID colour-1 block with no aperture. So the panel says two avatars exist, this is the one you are driving, and the other one has a different shape -- and a solid avatar with no aperture could not show the socket pip through itself. Joined to the cascade finding at eleven for eleven I read the two slots as two modes of travel. THE PAYOFF IF THIS IS RIGHT IS THE WHOLE LEVEL: the sole route south is blocked by the comb at lattice (6,2), 23 of whose 25 pixels render colour 8, and if the modes differ in what terrain they cross then the comb is a mode problem and not a switch problem. THIS ROUND'S GUARD DELETION IS ALSO A TEST OF IT: under the mode reading the panel is a global selector and toggling it should not care where the body stands, which is exactly what my rules now predict."
    [depends: the_cascade_length_reads_the_panel_and_it_is_now_eleven_for_eleven, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: pending]

  theorem action5_is_return_to_spawn_or_north_and_twenty_five_transitions_cannot_split_them "ACTION5 has now been pressed ELEVEN times, at t5 through t25 odd, and every single one was pressed from lattice (2,2) with the body one cell south of spawn, and every single one put the body back at (1,2). Reading NORTH says ACTION5 steps one lattice cell up. Reading RETURN says ACTION5 sends the body home from wherever it is. The body has stood in exactly two lattice cells in twenty-six states and those two are adjacent, so the readings have made identical predictions on every frame ever observed. A third reading is observationally identical and changes the strategy: ACTION5 SWAPS which of two avatars you drive and the incoming avatar always starts at spawn. I tested the memory-preserving version of that against the transitions that could refute it: if the swap preserved each avatar's position then the incoming avatar would already have been at (2,2), zero body cells would have changed and only 23 panel cells would have moved. 71 changed at t7, t11, t15, t19, t23 and t25. So swap-with-memory is REFUTED six times over and swap-with-reset survives, indistinguishable from RETURN. THE SEPARATOR NEEDS THE BODY TWO CELLS FROM HOME, which needs the third lattice cell. But note a WEAKER separator that is now purchasable: pressing ACTION5 AT SPAWN. Under NORTH the body would try to step into rows 2-6 columns 14-18, which render 0 and are void, so nothing moves; under RETURN the body is already home and nothing moves; both agree on the body. They need not agree on the PANEL, and the panel is the part my rules now predict. Whatever happens there is the first new fact about ACTION5 in six rounds."
    [depends: key5_body_respawns, key5_body_clears, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: pending]

  theorem the_loop_ran_two_more_times_and_this_time_i_did_something_about_it "Recorded as a process fact because a desk that hides this is useless. t22 A2, t23 A5, t24 A2, t25 A5. Body south, home, south, home. Panel B, A, B, A. Two meter cells burned. Zero new mechanism from the world. THE MECHANISM OF THE LOOP WAS DERIVED LAST ROUND AND IS TWO INTERLOCKING FIXED POINTS. FIRST: with no goal the plan tier cannot return sat, so the probe tier chooses; the probe tier scores expected bits over the manual and its ablations; at spawn only key 2 had a live rule and at lattice (2,2) only key 5 had one, so at each of the two reachable states exactly one action had nonzero expected bits and the cycle was forced. SECOND, and reinforcing: the manual's undrawable frontier cell guarantees key 2 a large constant realised gain, so nothing about the outcome ever discourages the choice. WHAT IS DIFFERENT THIS ROUND IS THAT I STOPPED WRITING PRUNES ABOUT IT AND CHANGED THE MANUAL. The spawn end of the cycle is now open: two keys are live at spawn. I do not know that the ranker will take the new one, and I am predicting in advance that if it does not, the fault is not in the manual and I will say so rather than editing further. ACTION3 and ACTION4 have each been pressed exactly once, both at a cell where east and west were void, and the east key remains unnamed after twenty-five transitions."
    [depends: the_ranker_can_only_buy_what_my_rules_already_fire_on, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: passed]

  theorem the_goal_i_still_cannot_write_is_the_real_one "The win is the body standing in lattice (8,7), rows 50-54 columns 44-48, its 24 ring pixels rendering 9 and its aperture showing the pip at (52,46). Re-verified against the current frame. Those 24 cells render constant colour 5, so they are board and hold no instance; and colour 5 is already claimed by Vacated while the arm looks types up by colour alone, so a second colour-5 type would be indistinguishable from Vacated and would claim cells twice, which is the constraint-5 error. The goal I could write over Vacated once the socket goes dynamic, count(Vacated, color = 9) = 24, is already true whenever the body stands in lattice (2,2), so it names two states and one of them is not a win. So the manual carries the true winning condition in prose, here and in the playbook, and carries NO goal line at all. That is a stated gap and not an evasion."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem the_burn_rules_want_one_rule_and_the_grammar_forbids_it "meter_burn_key2_rightmost and meter_burn_key2_next are ONE law -- burn the leftmost burned-adjacent colour-9 cell of the bar, where the right board edge counts as burned -- split into two rules because the guard language has and and not but no or, and the two conditions rightof(?p) = wall and colored(rightof(?p), 1) cannot be joined. They are exclusive rather than merely different: where rightof(?p) is off-board there is no cell to render 1, so the colour test is false, and where rightof(?p) is a real cell it is not wall. So constraint 5 holds by construction and the cost is one duplicated line. meter_burn_key4_next has the same body as meter_burn_key2_next with a different key; the key-4 twin of the RIGHTMOST rule has no witness and can never get one now that (63,63) is burned, so it is not written. All three burn rules are UNGROUNDABLE going forward: all twelve meter instances render 1, no Glyph9 instance renders 9 with a right neighbour rendering 1, and none will unless a future census extends the bar leftwards. They stay because they are what makes replay correct on t2 through t24. Note the consequence for the ranker: an ungroundable rule contributes no expected bits, so KEY 4 IS A SILENT ACTION EVERYWHERE and is as unbuyable as keys 1 and 3."
    [depends: meter_burn_key2_rightmost, meter_burn_key2_next, the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: passed]

  theorem dark_may_have_no_instances "The one arithmetic gap in the census and I will not hide it. cells_needing_an_owner is 80 while dynamic_cells is 83, and the difference is precisely the three colour-0 cells of underline 2. Colour 0 is the background, and the arm instances every cell of a declared colour the board cannot explain; whether a dynamic cell whose frame-0 colour is the background counts as explained is not something I can settle from the brief. The indirect evidence is direct enough to satisfy me: certify reports replay 21/21 exact over transitions that include t5, t9, t13, t17 and t21, and key5_underline2_lights and key5_underline2_dims carry coverage on those; if Dark seated no instances those rules could not fire and each of those transitions would be wrong by three cells. I keep the theorem rather than promoting it to an invariant with status proven, because the reasoning is inference from a check rather than a reading of the arm."
    [depends: dynamic_census, the_two_rounds_i_lost_were_both_lost_at_my_own_desk  probe: passed]

  theorem silence_is_a_prediction_and_two_of_my_spawn_silences_are_still_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the five keys at spawn, where the body now stands, with this round's edit applied. key(2) moves 48 body cells and burns one meter cell it cannot draw: witnessed eleven times. key(5) NOW FIRES 23 PANEL CELLS AND NO BODY CELL -- that prediction is new this round, is a generalisation of eleven witnessed rule bodies with an unwitnessed conjunct removed, and is falsifiable in one press; it is no longer a silence at all. key(1) inert at spawn: WITNESSED, t1, zero cells changed. key(3) inert at spawn: NO WITNESS -- pressed once, at t3, from one cell south, where east and west were both void. key(4) inert at spawn: NO WITNESS -- pressed once, at t4, from one cell south, where it burned a meter cell and moved nothing. SO THE COUNT HAS GONE FROM THREE FORGED SILENCES AT SPAWN TO TWO, and the two remaining are exactly the two east candidates. The fourth and largest forgery, at the other cell, is in the_loudest_forged_silence_is_not_at_spawn and is unchanged. A forged silence is priced at zero by the ranker, so the manual's forgeries are self-protecting -- but the guard deletion shows that some of them are held in place by something I can honestly remove, and the discipline is to look for that conjunct before writing another paragraph of complaint."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: passed]

  theorem the_two_no_op_rules_fail_the_gain_test_and_i_say_so "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has exactly one witness, and each witnesses a transition on which zero cells changed. The manual would replay identically without them: constraint 3 is failed outright and I am not going to dress it up. The reason I keep them is smaller than the rule text: they put key(1) and key(3) into the manual's action alphabet, which is what certify's ambiguity check adjudicates over -- it reported 5 actions and 110 pairs, and without these two it would have reported 3. Deleting them removes information I can see for a saving I cannot measure. They change no prediction, so keeping them cannot cost a pixel, and they are the two cheapest deletions in this manual if a later desk wants them gone. I note one thing I checked and it did NOT save them: a rule that recolours a pixel to the colour it already has does not make its action non-silent for the ranker, because the successor state is identical, so these two rules do not buy key 1 or key 3 any expected bits. NOTE ALSO WHY THEIR spawn_probe GUARDS SURVIVED THIS ROUND'S DELETION: they are not part of the panel bundle, they change no prediction with or without the guard, and touching a rule that does nothing is churn."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "key2_body_leaves grounds on meter instances at row 63 whose sixth-below is row 69, and it must not fire there. It does not, because a colour test on an off-board cell is FALSE rather than an exception, and <cell> = wall is the sanctioned positive test. Every row and column discrimination in the eight forward panel rules is built from that one fact, AND AFTER THIS ROUND'S GUARD DELETION IT IS THE ONLY THING KEEPING THOSE RULES OFF THE SPAWN RING AND THE METER, so I re-derived it rather than trusting it. The k-th above is off-board exactly when k exceeds the row, so panel row 1 is above-twice equals wall; row 3 is a colour test on above-twice, false for row 1 precisely because a colour test on an off-board cell is false; row 2 is above-three equals wall conjoined with a colour test on above-once. key5_slot1_dims requires above-four equals wall, true only in rows 0 through 3, and the spawn ring is rows 8-12 and the meter is row 63, so neither can ground it however they are coloured. key5_underline1_dims requires above-six equals wall, true only in rows 0 through 5, and its above-four colour test is false for rows 1-3 because that cell is off-board -- which is what separates it from key5_slot1_dims. The same trick separates slot 2's middle row by column -- column 5 is leftof-six equals wall, column 6 is leftof-seven equals wall with a colour test on leftof-once, column 7 is a colour test on leftof-twice -- and those three are pairwise exclusive. leftof-seven from column 5 is also off-board, so centre_darkens and row2_left_lights are separated NOT by that atom but by colored(leftof(?s), 1), which is false at column 5 because (2,4) is a separator rendering 0. Not one rule uses not, deliberately."
    [depends: key5_slot2_centre_darkens, key2_body_leaves, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: passed]

  theorem the_reverse_toggle_needs_only_a_colour_test_and_i_reaudited_every_clash_without_the_guard "The five return rules are far shorter than the eight forward ones, because configuration B assigns a UNIQUE colour to each panel group within each declared type, which configuration A does not. In B: Glyph9 renders 2 on slot 1, 8 cells, and 0 on underline 1, 3 cells, and 9 or 5 on the spawn ring and 9 or 1 on the meter; Spent renders 9 on the slot-2 ring, 8 cells, and 0 on the slot-2 centre, 1 cell; Dark renders 9 on underline 2, 3 cells. So a bare colour test names each group exactly. THE AUDIT THAT MATTERED THIS ROUND is the one I could previously skip: with colored(spawn_probe, 5) gone, the reverse rules now ground at states where the body is AT HOME, which is thirteen of twenty-six states. Does the spawn ring at colour 9 collide with anything? key5_slot1_lights takes colour 2, key5_underline1_lights takes colour 0, and no reverse rule takes Glyph9 at 9, so no. Does the meter at colour 1 collide? No reverse rule takes Glyph9 at 1 and no forward rule does either. Does key5_body_respawns collide, which takes Glyph9 at colour 5 with the cell above at 5? Colour 5 is claimed by no panel rule in either direction, so no. Colour 2 is claimed only by key5_slot1_lights. Colour 0 on a Glyph9 is claimed only by key5_underline1_lights and no other Glyph9 ever renders 0. key5_slot2_ring_resets takes Spent at 9 while all four forward slot-2 rules take Spent at 1: disjoint. key5_slot2_centre_resets takes Spent at 0, claimed by nothing else. key5_underline2_dims takes Dark at 9 while key5_underline2_lights takes Dark at 0: disjoint. In configuration A none of the five can fire; in configuration B none of the eight forward rules can fire. The two directions are separated by the frame itself, which is why no phase counter is needed and why the deleted guard was never load-bearing."
    [depends: key5_slot1_lights, key5_underline2_dims, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "cascade_lengths are 1, 7 and 9. Every no-op returned one frame; ACTION2 returned 7 or 9 depending on the panel; ACTION5 returned 9 every time. A move is animated one row per internal frame and the world reports the whole animation for a single action; cascade single_frame compares only the net, so up to eight intermediate frames per command are discarded unread, and I record that as a limitation of my own semantics rather than of the world. The refutation I keep, now with eleven witnesses: under a slide-until-blocked reading, ACTION2 at spawn would run the body south through rows 20-24 and 26-30 to the comb. It stopped after exactly six rows over open floor on all eleven presses. ONE PRESS IS ONE LATTICE CELL, and every distance in the playbook rests on it."
    [depends: key2_body_arrives  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2 through 6R+6 by columns 6C+2 through 6C+6; rows and columns congruent to 1 modulo 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. Row 7 is floor from column 13 to column 43. R=1, rows 8-12, is floor from column 13 to column 43 except the knob block, so C=2,3,4,5 are open and C=6 holds the knob. R=2, rows 14-18, is floor at columns 13-19 and 25-31 only, so C=2 and C=4. R=3, rows 20-24, is floor from column 13 to column 31, so C=2,3,4. R=4 and R=5 are floor only at columns 13-19, so C=2. R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable. R=7 is C=2, plus a fragment of floor at row 48 columns 42-50 that is one row deep and cannot hold a body. R=8, rows 50-54, is floor from column 13 to column 48, so C=2 through C=7 are open. Separator rows 7, 13, 19, 25, 31, 37, 43 and 49 are floor across column 2 and separator column 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in twenty-six frames the body has occupied exactly TWO cells, (1,2) and (2,2)."
    [depends: the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed eleven times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 columns 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 columns 43-49, row 55 columns 43-49, column 49 rows 49-55. Rows 49 and 55 are separator rows and columns 49 and 43 are separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted in colour 9, with the west wall at column 43 left as FLOOR for rows 50-54. Inside it, rows 50-54 columns 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, column 50 rows 49-56 is a one-cell strip of floor that leads nowhere. Overlay the body standing in lattice (8,7), 5x5 with an aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate: the game is won when the 24 ring pixels of rows 50-54 columns 44-48 render 9. The bracket has never changed in twenty-six frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally write a real goal line."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2), (1,3), (1,4), (1,5), (2,2), (2,4), (3,2), (3,3), (3,4), (4,2), (5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 columns 39-41, a stem pixel at (12,40), colour 8 filling column 40 from row 12 down to row 40, colour 8 filling row 40 from column 14 to column 40, and the comb teeth at rows 38-42 columns 14-18, which hold 23 colour-8 pixels and 2 colour-5 pixels at (39,14) and (41,14). It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Note also that the descending wire at column 40 is flanked by floor at columns 39 and 41 through the void rows, which is drawn deliberately and which I do not yet understand. Not one colour-8 pixel has moved in twenty-six frames. The first colour-8 pixel that changes turns this theorem into physics AND makes a goal line writable in the same instant."
    [depends: the_maze_is_a_six_pixel_lattice, the_zero_instance_goal_was_refused_and_here_is_the_law_it_taught  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 columns 32-36, is fully open floor and is separated from the knob's cell (1,6) at columns 38-42 only by separator column 37, which renders floor through rows 8-12. Lattice (1,6) contains ten colour-8 pixels, nine of them non-centre pixels of that cell -- the eight knob pixels other than its centre (10,40), plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while colour 8 is solid. Either colour 8 is walkable in one of the two panel modes, and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Twenty-five commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens, the_panel_is_a_two_slot_mode_selector_and_the_mode_may_gate_terrain  probe: pending]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because it is the permanent shape of every refutation this level will produce, and this round it bit three times again: the burn frontier, the refused goal, and the twenty-four cells of lattice (3,2) that make the loudest forged silence undrawable. To draw the next burn, or the first step onto fresh ground, or the socket, or to COUNT the comb, I would need an instance on a board cell. The arm offers exactly one lever, arc-instances all, and its documented behaviour is to instance every cell of that colour THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance, and the compiler will not let a clause count a type whose instance set is empty. I considered and REJECT the two workarounds again. First, a second declared type on colour 9 without arc-instances: the arm looks types up by colour and nothing else, so it is indistinguishable from Glyph9, its seat is unspecified, and any cell it landed on would be claimed twice. Second, dropping the board declaration so that every cell of every declared colour is instanced: the arithmetic is fatal, because colour 0 covers roughly two thousand background cells and colour 5 roughly one thousand floor cells, so twenty-two rules would ground over some three thousand instances with constraint 5 needing a fresh pairwise audit against every one of them, in a single round, with no witnesses; and the concrete breakage is already known -- key2_body_leaves would ground on the socket bracket at (49,49), whose sixth-below (55,49) renders 5, and would recolour a wall on every ACTION2. So the manual heals ONE STEP BEHIND the world, permanently, and the correct way to read a refutation here is by its divergence set: where that set lies on cells that had never changed before the transition, the manual is not implicated."
    [depends: dynamic_census, the_burn_frontier_is_a_permanent_one_pixel_blind_spot  probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_parity_and_cannot_say_or "Five expressive holes, and the first remains the expensive one although this round found a partial way around it. FIRST: there is no third outcome for a state-action pair -- not no change and not a named successor, but unobserved, the manual declines to predict. Rules produce events, absence of a rule produces identity, and the compiled step is total. So the two remaining unwitnessed spawn silences and the one at lattice (2,2) are asserted in the same voice as the witnessed ones, AND THE PROBE RANKER PRICES BOTH VOICES AT ZERO. A manual that could say I DO NOT KNOW WHAT KEY 3 DOES HERE would be a manual whose ablations disagreed on key 3, and the ranker would buy the experiment immediately. THE PARTIAL WORKAROUND FOUND THIS ROUND, and its limits: where a silence is produced by an unwitnessed GUARD rather than by a missing rule, deleting the guard converts the silence into a falsifiable prediction and the ranker can see it. That worked for ACTION5 at spawn. It cannot work for keys 3, 4, 6 or 7, because there is no rule of theirs to un-guard. SECOND: if the meter runs on command parity, that law CANNOT be written here at any length, because the guard language reads pixels and the action name and there is no command counter and no phase pixel. THIRD: there is no or, which is why one burn law is two rules. FOURTH: THERE IS NO WAY TO SAY THAT A PIXEL WILL CHANGE WITHOUT NAMING AN OBJECT THAT OWNS IT, so a manual can never predict the frontier of its own knowledge. FIFTH: A GOAL CANNOT NAME A CELL THAT HAS NEVER CHANGED. Order of value to a future desk: an UNKNOWN outcome first, then instancing on constant cells, then a state counter, then or, then not."
    [depends: the_ranker_can_only_buy_what_my_rules_already_fire_on, the_loop_pins_key_to_parity_and_therefore_seals_the_meter  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1 through ACTION5 plus RESET; the alphabet is ACTION1 through ACTION7. Two commands are entirely unconstrained after twenty-six states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels changing colour, and never its precondition. Recording that effect is also what would make a goal line writable, since it is the event that turns comb cells dynamic. I note two countervailing risks plainly: actions_used lists only the five that have been tried, so it is no evidence that 6 and 7 exist; and since no rule of mine mentions them, my manual predicts identity for both, so the ranker prices them at zero and will not buy them either."
    [depends: no_goal_section_and_the_exact_enumerated_reason, the_ranker_can_only_buy_what_my_rules_already_fire_on  probe: pending]

  theorem the_two_rounds_i_lost_were_both_lost_at_my_own_desk "Two earlier rounds were lost at this desk: one to a goal clause counting a type with zero instances, which the compiler refused outright, and one to a reply that carried no theory block at all. The discipline that followed -- emit all three blocks first, worry about content second -- HELD for a third round. certify reports replay 21/21 exact, responsibility 0 of 4096 cells unexplained, ambiguity 0 clashes over 110 adjudicated pairs, no step crash, first_divergence null. THE GENERAL RULE STANDS: a mediocre manual that compiles outperforms an excellent one that does not by an unbounded margin, because the mediocre one gets corrected by the next frame and the excellent one gets corrected by nothing. certify's numbers describe a 22-state snapshot of a 26-state world -- the ordinary one-round lag, not a defect -- and I claim nothing from it about t22 through t25. I flag the one new risk I am taking this round: the guard deletion is the first edit in three rounds that changes what the compiled step does at any state, and although I checked replay and ambiguity by hand at every body-home state, a hand check is not certify."
    [depends: a_declaration_is_only_as_true_as_the_arm_can_seat_it, the_unwitnessed_guard_is_removed_and_this_is_not_gaming  probe: passed]

  theorem a_declaration_is_only_as_true_as_the_arm_can_seat_it "Kept because it cost three rounds in three different ways. First a landmark whose arc-cell comment was missing, which is a hard compile error; spawn_probe at (8,14) was the repair and it held. Then a type the arm could seat nowhere, where the arm accepted the DECLARATION and refused the COUNT. Then a reply that carried no theory block at all. THE GENERAL RULE, covering all three: before writing any clause, ask what the arm will seat for it, and if the answer is nothing, the clause is not conservative, it is fatal -- and before sending anything, ask whether the harness will read it at all. NOTE that spawn_probe is still declared and still used by the two no-op rules, so the landmark is not orphaned by this round's deletion."
    [depends: the_two_rounds_i_lost_were_both_lost_at_my_own_desk  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter now reports 16 tracks with a POSITIVE gain of 9098 bits against a 21336-bit baseline, a 43 percent saving, and NEGATIVE gain of 112910 bits on the 67-track split-by-colour variant. I take the positive variant as corroboration rather than as structure. What I take is corroboration by FRAME INDEX, independent of my rules. obj1: colour 1, nine cells, 3x3, present 5 of 26 frames -- slot 2 solid, alive in configuration A. obj5 colour 2 first frame 5, obj6 colour 1 first frame 7, obj7 colour 2 first frame 9, obj8 colour 1 first frame 11, obj9 colour 2 first frame 13, obj10 colour 1 first frame 15, obj11 colour 2 first frame 17, obj12 colour 1 first frame 19, obj13 colour 2 first frame 21, obj14 colour 1 first frame 23, obj15 colour 2 first frame 25: that is the panel alternating exactly on the odd indices where ACTION5 was pressed, ELEVEN flips, an independent witness for both toggle directions and for the fact that the last three rounds bought nothing but more of the same. obj0: colour 9, eight cells, 3x3, present all 26 -- the lit token. obj2: colour 9, three cells, 1x3 -- an underline. obj4 is the whole 64-cell bar of which 12 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. cegis_miner refuses every track and its verdict, the world does not narrate as one mover, is true of the arm and false of the world -- there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours. zero_space self-reports THIN in its own words: 25 transitions constrain rank 13 of 415 features, null space dimension 402, nearly every vector in it a law true over these states and unfalsified rather than confirmed. Its single global law is my census and nothing more. Nothing in the candidate stream proposes anything about colour 8, which is consistent with colour 8 never having changed."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me, and the previous three editions cashed in full except for one clause I had to retract. STATE: the body is at spawn, lattice (1,2). The panel is in configuration B -- slot 1 a hollow colour-2 ring, underline 1 dark, slot 2 a hollow colour-9 ring with dark centre, underline 2 lit. TWELVE meter cells are burned, columns 52 through 63; 52 remain. The next command index is 26, which is EVEN. THE HEADLINE PREDICTION IS AGAIN ABOUT THE ARM. Last round I predicted ACTION2 because it was the only live key at spawn; that is no longer true, so I predict instead THE NEXT COMMAND IS ACTION2 OR ACTION5 AND NOT ANY OTHER KEY, and I do NOT predict which of the two, because two hypotheses now disagree at this state and I have no model of how the ensemble weights 48 body pixels against 23 panel pixels. If the next command is ACTION1, ACTION3, ACTION4, ACTION6 or ACTION7 then something outside the ranker chose it and I want to know that. PER-ACTION PREDICTIONS. ACTION5 at spawn, THE ONE I MOST WANT: 23 panel pixels change, slot 1 turns from a colour-2 ring to a colour-9 ring, underline 1 lights, the slot-2 ring turns from 9 to 1 and its centre from 0 to 1, underline 2 goes dark, and NOT ONE BODY PIXEL MOVES because the spawn ring already renders 9 and the lower ring already renders 5. Under reading A of the meter no cell of row 63 burns. If instead nothing at all changes, the deleted guard was real, I am refuted by 23 cells, and it goes back into all thirteen rules next round. If the panel toggles AND (63,51) burns, reading B of the meter is right and reading A is dead. If the panel toggles and the body ALSO moves, ACTION5 is not a return and I learn what it is. FOUR DISTINCT OUTCOMES, ALL LEGIBLE IN THE RAW DIFF, AT ZERO METER COST UNDER READING A. ACTION2 at spawn: 48 body pixels drawn correctly, ZERO meter pixels drawn, the world burns (63,51), the manual refuted by exactly one cell, realised gain 5.087463 and NOTHING LEARNED; and because index 26 is even and the panel is B, I predict expected_bits comes back at 1.394848870026 exactly, which is the sharpest test of the period-four finding. ACTION3 at spawn: predicted ZERO cells changed, with NO witness for that silence at this cell; if the body steps east I pay 48 pixels I have priced. If it does not step, ACTION4 is east by elimination. ACTION2 pressed one cell SOUTH of spawn: predicted identity, and I expect that to be WRONG by 48 pixels with the body landing in lattice (3,2). ACTION1 at spawn: predicted identity, witnessed at t1. ACTION6 or ACTION7: entirely unconstrained."
    [depends: the_unwitnessed_guard_is_removed_and_this_is_not_gaming, the_expected_gain_is_period_four_and_therefore_also_measures_only_my_manual, the_loop_pins_key_to_parity_and_therefore_seals_the_meter  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Twenty-six states, twenty-five transitions:
#   RESET, A1 A2 A3 A4 A5, then A2 A5 eleven times.
# BODY AT SPAWN, lattice (1,2). PANEL IN CONFIGURATION B. TWELVE meter cells
# burned, columns 52-63; 52 remain. Next command index is 26, EVEN.
# certify last round: replay 21/21 exact, 0 cells unexplained, 0 clashes.
#
# ========= WHAT CHANGED AT THE THEORY DESK THIS ROUND =========
# For five rounds this book said the same thing: the ranker scores expected
# bits over {manual, ablations, inert}; an ablation only ever predicts FEWER
# changes; so on any pair where the manual predicts IDENTITY every hypothesis
# agrees and the gain is ZERO. A MANUAL CANNOT PROBE ITS OWN SILENCES. At
# spawn only key 2 was live; at (2,2) only key 5 was live; the eleven-lap loop
# was forced. And this book ranked precisely the silences, so it was the exact
# NEGATION of what the ranker would ever choose.
#
# I said the lever was not mine. THAT WAS TOO STRONG AND I FOUND ONE.
#
#   THIRTEEN PANEL RULES CARRIED colored(spawn_probe, 5) -- "body not at home".
#   ELEVEN positive witnesses. ZERO negative witnesses, and the zero is
#   STRUCTURAL: every ACTION5 in the log was pressed from lattice (2,2), so the
#   conjunct was true BY CONSTRUCTION at every press. It described where the
#   presses happened, not what the world does. It explains no pixel.
#   IT IS DELETED. Replay unaffected; ambiguity re-audited by hand at all
#   thirteen body-home states in both panel configurations; 0 new clashes.
#
# CONSEQUENCE: AT SPAWN, TWO KEYS ARE NOW LIVE.
#   key 2 -> 48 body pixels.   key 5 -> 23 panel pixels.
# The ensemble can disagree at this state for the first time in 26 frames.
#
# THE RULE THIS TAUGHT, AND IT IS THE ONLY GENERAL THING THIS BOOK HAS EVER
# LEARNED ABOUT ITSELF:
#   TO MOVE A PROBE FROM THIS BOOK INTO THE RANKER'S REACH, DO NOT ARGUE FOR
#   IT IN PROSE. FIND THE UNWITNESSED CONJUNCT HOLDING THE MANUAL SILENT
#   THERE AND DELETE IT. Where no such conjunct exists -- keys 3, 4, 6, 7 have
#   no rule to un-guard -- the silence is real ignorance and prose is all I
#   have.
#
# I DID NOT take the other lever, and the distinction is the whole of my
# honesty here: deleting an unwitnessed RESTRICTION on rules with eleven
# witnesses each is legitimate; adding an unwitnessed RULE (e.g. "A2 moves the
# body from lattice (2,2)", zero witnesses of any kind) is fabrication, and it
# stays refused for the sixth round.
#
# ========= THE PROBE THAT IS NOW BUYABLE, AND WHAT IT PAYS =========
# ACTION5 AT SPAWN. Four distinct outcomes, all legible in the RAW DIFF:
#   (a) 23 panel pixels change, no body pixel, no burn
#       -> the guard was fake, I was right, and thirteen rules generalise.
#   (b) nothing changes
#       -> the guard was real; I am refuted by 23 cells and put it back.
#   (c) panel toggles AND (63,51) burns
#       -> the meter runs on command PARITY, not on the key. Reading A dies.
#          This is the separator that six rounds of loop could never buy,
#          because the loop pinned key-2-ness and even-ness to the same
#          predicate. Index 26 is even. THIS IS THE WINDOW.
#   (d) panel toggles AND the body moves
#       -> ACTION5 is not "return to spawn"; the north/return/swap question
#          that eleven identical presses could not split is split.
# Under reading A it costs NO meter cell. There is no cheaper experiment on
# this board and there has not been one for six rounds.
#
# ========= heuristic_miss, ANSWERED FOR THE SEVENTH TIME =========
# Declaring a goal is NOT the highest-value edit, for an arithmetic reason:
#   THE PLAN TIER REACHES A GOAL BY SEARCHING MY COMPILED RULES, AND MY RULES
#   CAN ONLY REACH TWO LATTICE CELLS AND TWO PANEL CONFIGURATIONS.
# So the only goal that could return sat is one satisfied inside the loop, and
# sat-inside-the-loop is WORSE than unsat: unsat leaves the arm probing, sat
# makes it commit and declare success one lattice cell from spawn. Every
# candidate the grammar admits over the four instanced types, re-checked with
# this round's counts: count(Glyph9,color=5)=24 and count(Vacated,color=9)=24
# both mean only "body is off spawn"; count(Dark,color=9)=3 means only "panel
# is in configuration B"; count(Glyph9,color=1)=64 exceeds the 47 instances
# that exist and =47 is unreachable by any rule; count(Spent)=0 is
# constant-false.
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
# ========= THE PROBE NUMBERS ARE PERIOD-FOUR. I WAS WRONG LAST ROUND. =========
# I claimed expected_bits MOVES with the state while realised gain is pinned.
# It does not move. The four probes this round report 1.394848870026,
# 2.2195282823, 1.955012006402, 2.273661689922 -- BIT FOR BIT the same four
# numbers, in the same order, as last round's four. Aligned against the panel:
#   action 2 from config B -> 1.394848870026 (t18, t22)
#   action 5 from config B -> 2.2195282823   (t19, t23)
#   action 2 from config A -> 1.955012006402 (t20, t24)
#   action 5 from config A -> 2.273661689922 (t21, t25)
# EXPECTED BITS IS A FUNCTION OF (KEY, PANEL CONFIGURATION) AND NOTHING ELSE.
# It does not see the meter, which burned two more cells between the rounds.
# Both the prior and the posterior measure my manual's fixed geometry.
#   A GAIN THAT CAN BE PREDICTED FROM THE PANEL ALONE IS NOT A MEASUREMENT.
#
# ========= THE COST OF THE LOOP, IN THE ONLY CURRENCY THAT MOVES =========
# Row 63 is the ONLY monotone quantity. Body position cycles; the panel
# cycles; 26 states but only 24 distinct, and the two collisions are the
# ancient sterile pairs -- every later state is nominally new ONLY because one
# more meter cell burned. 12 gone, 52 left, one per lap, two commands per lap.
# About 104 commands of loop remain before row 63 is fully colour 1. What
# happens then is not in evidence and I will not guess.
#
# ========= THE RANKED LIST =========
# 1. ACTION5 AT SPAWN. Now priced above zero by the ranker's own arithmetic
#    (see above). Four outcomes, free under reading A, splits the meter at an
#    even index, splits north-vs-return, tests thirteen rules at once.
# 2. THE EAST KEY, TESTED AT SPAWN. ACTION3 first, ACTION4 only if 3 is inert.
#    A2 is south (11 witnesses). A1 was pressed AT SPAWN with east OPEN and
#    moved nothing, so A1 is not east. EAST IS A3 OR A4, no third candidate.
#    Both were pressed once, from one cell south where east AND west are void,
#    so neither press could answer anything. Step one of the only route to the
#    knob. STILL PRICED AT ZERO by the ranker; no conjunct exists to delete.
# 3. ACTION2 PRESSED ONE CELL SOUTH OF SPAWN. Manual predicts NOTHING -- no
#    Glyph9 renders 9 there, no Vacated renders 5 -- and that is almost
#    certainly false: rows 20-24 are floor from column 13 to 31 and one A2
#    press has moved the body one lattice cell south eleven times running.
#    The ONE command likely to put the body in a lattice cell never occupied.
#    I will not buy it with a fabricated rule.
# 4. ACTION6 OR ACTION7. Never pressed, entirely unconstrained. In this family
#    one is usually a click, and the knob is a 3x3 target the body appears
#    unable to stand on. My manual could record such a command's EFFECT and
#    never its precondition -- but the effect is what makes the comb dynamic
#    and the goal writable. Honest risk: actions_used lists only what has been
#    tried, so it is no evidence these exist.
#
# ========= WHAT NOT TO PRESS =========
#   A2 at spawn: buys the guaranteed constant. 48 body pixels drawn correctly
#   eleven times over; the only divergent cell is (63,51), which no manual in
#   this language can draw; gain returns 5.087463 for the ninth time and
#   expected_bits returns 1.394848870026 for the third. Guaranteed refutation,
#   guaranteed wasted round, one more burned meter cell.
#   A5 from one cell south is pure loop; A5 from spawn is item 1 above and is
#   a different experiment entirely.
#   A1 at spawn: witnessed inert at t1.
#   A4 at spawn: the same experiment as A3 with the labels swapped, but it
#   spends a meter cell under BOTH readings -- press it only if A3 is inert.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The next burn cell (63,51) is undrawable: one pixel per press of key 2
#     or 4, forever. A refutation whose divergence set is exactly that cell
#     implicates nothing.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on cells that have never changed, and 24 departure pixels for
#     which no rule in that direction is witnessed. 24 for the second step in
#     the same direction, 0 after that.
#   * NEW THIS ROUND, and it is mine: if ACTION5 at spawn changes nothing, I
#     am refuted by 23 panel cells and the spawn_probe guard goes back into
#     all thirteen rules. I priced that before pressing.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.

order     delete_an_unwitnessed_guard_before_complaining_that_a_probe_is_unbuyable [proof: lean]
order     distinguish_deleting_a_restriction_from_inventing_a_rule       [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition      [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     prefer_a_probe_with_four_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     split_the_meter_readings_at_an_even_index_while_a_window_exists [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell          [proof: lean]
order     buy_a_third_lattice_cell_before_attempting_to_write_a_goal     [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language [proof: lean]
order     treat_a_repeated_identical_information_gain_as_zero_gain       [proof: lean]
order     treat_a_gain_predictable_from_the_panel_alone_as_no_measurement [proof: lean]
order     discount_any_gain_that_comes_from_a_cell_with_no_instance      [proof: lean]
order     prefer_a_command_that_closes_three_open_questions_over_one     [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     break_a_repeating_command_cycle_before_optimising_within_it    [proof: lean]
order     test_a_shared_guard_where_it_has_never_been_false              [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance             [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation    [proof: lean]
order     prefer_a_key_that_adds_no_new_prediction_debt                  [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it             [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal   [proof: lean]
order     spend_a_meter_cell_only_on_a_question_it_actually_closes       [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it     [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it [proof: lean]
order     reaudit_ambiguity_by_hand_after_any_guard_deletion             [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them         [proof: lean]

prune     action_whose_expected_bits_are_zero_only_because_the_manual_is_silent => keep [proof: lean]
prune     rule_proposed_with_zero_witnesses_of_any_kind => dead                  [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead                    [proof: lean]
prune     goal_that_becomes_true_at_a_state_that_is_not_a_win => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_cells_already_visited => dead [proof: lean]
prune     divergence_lies_only_on_the_unburned_meter_frontier => dead            [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key => dead   [proof: lean]
prune     expected_bits_predictable_from_the_panel_configuration_alone => dead   [proof: lean]
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

heuristic guards_carried_with_no_negative_witness_anywhere_in_the_log       [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic actions_priced_at_zero_expected_bits_by_the_manuals_own_silence   [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
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

prefer    a_state_where_more_than_one_key_has_a_rule_that_can_fire           [ev: 13/26 states]
prefer    a_command_that_tests_a_guard_shared_by_thirteen_rules_at_once      [ev: 1/1 available]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index          [ev: 25/25 transitions tie]
prefer    a_command_that_would_put_the_body_in_a_lattice_cell_never_occupied [ev: 2/11 reachable cells seen]
prefer    a_command_that_would_turn_a_machinery_pixel_dynamic                [ev: 0/26 states]
prefer    a_key_that_names_a_direction_whichever_way_it_answers              [ev: 2/2 candidates]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed      [ev: 2/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on               [ev: 3/5 keys at spawn]
prefer    a_command_that_leaves_the_cycle_the_last_twenty_one_commands_formed [ev: 21/24 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 25/25 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    a_free_probe_over_one_that_costs_a_meter_cell                      [ev: 12/25 commands burned]
```

## Why you are being called: the surprises that fired

### render_mismatch (empirical family -> theory.dsl)

52 pixels of frame 0 belong to neither the board nor any declared object

```json
{
 "cells": [
  [
   30,
   13,
   5,
   3
  ],
  [
   30,
   14,
   5,
   3
  ],
  [
   31,
   13,
   5,
   3
  ],
  [
   31,
   14,
   5,
   3
  ],
  [
   32,
   13,
   5,
   2
  ],
  [
   32,
   14,
   5,
   2
  ],
  [
   32,
   17,
   5,
   4
  ],
  [
   32,
   18,
   5,
   4
  ],
  [
   32,
   19,
   5,
   4
  ],
  [
   32,
   20,
   5,
   4
  ],
  [
   32,
   21,
   5,
   4
  ],
  [
   32,
   22,
   5,
   4
  ],
  [
   33,
   13,
   5,
   2
  ],
  [
   33,
   14,
   5,
   2
  ],
  [
   33,
   17,
   5,
   4
  ],
  [
   33,
   18,
   5,
   4
  ],
  [
   33,
   19,
   5,
   4
  ],
  [
   33,
   20,
   5,
   4
  ],
  [
   33,
   21,
   5,
   4
  ],
  [
   33,
   22,
   5,
   4
  ],
  [
   34,
   13,
   5,
   3
  ],
  [
   34,
   14,
   5,
   3
  ],
  [
   35,
   13,
   5,
   3
  ],
  [
   35,
   14,
   5,
   3
  ]
 ],
 "count": 52
}
```

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
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    30,
    14
   ],
   "manual_says": 5,
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
   "manual_says": 5,
   "world_says": 0
  },
  {
   "cell": [
    31,
    14
   ],
   "manual_says": 5,
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
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    32,
    14
   ],
   "manual_says": 5,
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
   "manual_says": 5,
   "world_says": 2
  },
  {
   "cell": [
    32,
    18
   ],
   "manual_says": 5,
   "world_says": 1
  },
  {
   "cell": [
    32,
    19
   ],
   "manual_says": 5,
   "world_says": 1
  },
  {
   "cell": [
    32,
    20
   ],
   "manual_says": 5,
   "world_says": 2
  },
  {
   "cell": [
    32,
    21
   ],
   "manual_says": 5,
   "world_says": 1
  },
  {
   "cell": [
    32,
    22
   ],
   "manual_says": 5,
   "world_says": 1
  }
 ],
 "cells_wrong": 80,
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
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     30,
     14
    ],
    "manual_says": 5,
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
    "manual_says": 5,
    "world_says": 0
   },
   {
    "cell": [
     31,
     14
    ],
    "manual_says": 5,
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
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     32,
     14
    ],
    "manual_says": 5,
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
    "manual_says": 5,
    "world_says": 2
   },
   {
    "cell": [
     32,
     18
    ],
    "manual_says": 5,
    "world_says": 1
   },
   {
    "cell": [
     32,
     19
    ],
    "manual_says": 5,
    "world_says": 1
   },
   {
    "cell": [
     32,
     20
    ],
    "manual_says": 5,
    "world_says": 2
   },
   {
    "cell": [
     32,
     21
    ],
    "manual_says": 5,
    "world_says": 1
   },
   {
    "cell": [
     32,
     22
    ],
    "manual_says": 5,
    "world_says": 1
   }
  ],
  "cells_wrong": 80,
  "kind": "frame_mismatch",
  "t": 0
 },
 "proof_layer_available": false,
 "replay": {
  "detail": "0/5 transitions replay exactly",
  "matched": 0,
  "ok": false,
  "transitions": 5
 },
 "responsibility": {
  "cells_unexplained": 52,
  "detail": "52 pixels of frame 0 belong to neither the board nor any declared object",
  "ok": false,
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
# theory.dsl -- COMPLETE REWRITE. The manual I was handed described a
# DIFFERENT world (26 states, spawn ring rows 8-12, panel rows 1-5). certify:
# 0/5 replay, first divergence at t=0, 52 unexplained pixels of frame 0. Not
# one of its rules can ground here. I deleted it entire rather than patch it.
# Everything below comes from this log alone: RESET, A1, A2, A3, A4, A7.
#
# THE CENSUS I RECONSTRUCTED (the brief gives boxes and counts, not cell sets):
#   rows 30-35 x cols 11-16   36  top slot
#   rows 32-33 x cols 17-22   12  top readout
#   rows 36-41 x cols 11-16   36  bottom slot
#   rows 38-39 x cols 17-22   12  bottom readout
#   (53,63)                    1  meter tip
# FOUR NUMBERS I DID NOT CHOOSE LAND ON IT EXACTLY: 97 = dynamic_cells;
# 96 = the t1 and t2 diffs, box rows 30-41 cols 11-22; 97-24 background-
# coloured cells = 73 = cells_needing_an_owner; 4096-97 = 3999 = constant_cells.
#
# THE DEDUCTION EVERYTHING RESTS ON: states=6, distinct_states=5 => exactly one
# collision. S4/S5 carry (53,63)=3 and S0-S3 carry 2; S1 differs from S0 and S2
# by 96 each; S3 differs from S2 by 12 and from S1 by >=84. ONLY S0 = S2
# SURVIVES. So ACTION2 undid ACTION1, and THE CURRENT WIDGET IS THE FRAME-0
# WIDGET -- which is how I read frame 0's colours without being shown frame 0.
#
# THE READING: two 6x6 slots at cols 11-16 (rows 30-35, rows 36-41), each with
# a 6x2 readout at cols 17-22. W0 = bar on top (colour 3, core 2), hollow
# colour-6 box below, top readout blank, bottom readout patterned. ACTION1
# EXCHANGES the slots and the readouts; all 96 cells differ between the two
# configurations, which is why the diff says 96. ACTION2 exchanges back.
# ACTION3/ACTION7 blank the bottom readout; ACTION4 restores it AND advances
# the meter tip.
#
# EXPECTED REPLAY 5/5, with one named failure mode (Field seating, below).

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

  rule k1_frame_to_bar forall ?p in Frame [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_to_core forall ?p in Frame [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

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

  rule k2_frame_from_field forall ?p in Frame [ev: t2 cov: 14/14]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2 cov: 4/4]
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
  invariant field_instances count(Field) = 24 [status: counted-from-reconstructed-census]
  invariant barbody_instances count(BarBody) = 8 [status: counted-from-reconstructed-census]
  invariant barcore_instances count(BarCore) = 10 [status: counted-from-reconstructed-census]
  invariant blank_instances count(Blank) = 12 [status: counted-from-reconstructed-census]
  invariant frame_instances count(Frame) = 22 [status: counted-from-reconstructed-census]
  invariant hollow_instances count(Hollow) = 12 [status: counted-from-reconstructed-census]
  invariant dot_instances count(Dot) = 9 [status: counted-from-reconstructed-census]
  invariant board_cells count(board) = 3999 [status: matches constant_cells exactly]
  invariant meter_tip_now count(BarCore, color = 3) = 1 [status: state-dependent-not-an-invariant]

  theorem the_old_manual_is_discarded_entire "The manual I was handed is about another world: spawn ring rows 8-12, panel rows 1-5, 26 states, a 64-cell meter at row 63. This log has 6 states, dynamics confined to rows 30-41 cols 11-22 plus (53,63), and certify returns 0/5 replay with first divergence at t=0. No rule of it can ground here, so repair is meaningless and I deleted all of it. I kept two habits and no content: a manual that does not compile is worth less than a mediocre one that does, and a refutation is read by its divergence set."
    [probe: passed]

  theorem the_census_is_reconstructed_and_four_counts_confirm_it "The brief never hands me cell sets, so the five rectangles in the header are an inference. Four independent numbers land on them exactly: 36+12+36+12+1 = 97 = dynamic_cells; 36+12+36+12 = 96 = the cells changed at t1 and at t2 with bounding box rows 30-41 cols 11-22 as the diff reports; 97 minus the 24 cells of the top slot that render background 5 at frame 0 = 73 = cells_needing_an_owner; 4096-97 = 3999 = constant_cells. The render_mismatch listing corroborates where it is not truncated: it names (30,13),(30,14),(31,13),(31,14) as world 3, (32,13),(32,14),(33,13),(33,14) as world 2, and (32,17)-(33,22) as world 4 -- exactly the top slot's bar and the top readout, in exactly the colours the current frame shows. If any rectangle is wrong, replay breaks at t1 and I learn it in one round."
    [depends: the_old_manual_is_discarded_entire  probe: pending]

  theorem s0_equals_s2_and_that_is_what_lets_me_read_frame_zero "states = 6 and distinct_states = 5, so exactly one pair coincides. S4 and S5 carry (53,63)=3 while S0-S3 carry 2; S4 and S5 differ in 12 readout cells; S3 differs from S2 in 12 and from S1 in at least 84 since S1 and S2 differ in 96; S0 differs from S1 in 96. THE ONLY SURVIVOR IS S0 = S2. Two things follow. ACTION2 at t2 exactly undid ACTION1 at t1. And -- the part I cash -- the widget in the current frame IS the frame-0 widget, since t3, t4 and t5 touched only the bottom readout and the meter tip. Every source colour in every rule above is read off the picture in front of me, with the bottom readout back-corrected to the pattern ACTION3 erased. One deduction, no guess."
    [depends: the_census_is_reconstructed_and_four_counts_confirm_it  probe: passed]

  theorem the_widget_is_two_slots_and_action1_exchanges_them "Two 6x6 slots at cols 11-16, rows 30-35 and rows 36-41, each with a 6x2 readout at cols 17-22 (rows 32-33, rows 38-39). W0, which is frame 0 and is where I stand: the top slot is background with a two-column bar at cols 13-14 reading 3,3,2,2,3,3 down rows 30-35 and a blank readout; the bottom slot is a colour-6 box, colour-0 hollow, 2x2 colour-6 core at rows 38-39 cols 13-14, port pixels (38,16)=1 and (39,16)=2, and a patterned readout of eight 1s and four 2s with period 3 along each row and the rows offset by one column. ACTION1 exchanges them: (r,c) takes the colour of (r+6,c) for r in 30-35 and of (r-6,c) for r in 36-41. I checked all 96 cells and EVERY ONE differs between the configurations, which is exactly why the diff says 96 rather than fewer, and the exchange being an involution is exactly why S0 = S2. I hold this as a READING: a two-item list scrolled down then up is observationally identical over two transitions. The separator is a THIRD press of ACTION1 -- exchange returns to W1, scroll shows a third content."
    [depends: s0_equals_s2_and_that_is_what_lets_me_read_frame_zero  probe: pending]

  theorem the_swap_rules_are_thirty_six_and_constraint_three_is_failed "One law -- take the colour of the cell six away -- became 36 rules, and I will not dress that up. recolored(o, c) takes an INTEGER LITERAL, so a target colour cannot be read from a cell and must be named; the law splits into one rule per (source colour, target colour) pair, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I say so under constraint 3. I keep it because the alternative is 96 unexplained pixels twice over, and because these are one law under a grammar that cannot hold it. What buys some of it back is the TYPES: a type is a frame-0 colour, the frame-0 configuration is W0, so a rule's source colour selects its type for free, and the type separates top-half from bottom-half instances without a single row test. That is why not one rule in this file needs a deep nest of above() to say where it is."
    [depends: the_widget_is_two_slots_and_action1_exchanges_them  probe: passed]

  theorem barcore_is_four_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on four unrelated features: the 4-cell core of the bar (rows 32-33, cols 13-14), the lower port pixel (39,16), four dots of the bottom readout, and the meter tip (53,63). The arm looks types up by colour alone, so all ten are BarCore and no rule can tell the roles apart by type. I separate them by local geometry, every separator a cell I have actually read: the bar core has colour 3 two rows above, so k1_core_to_frame carries colored(above(above(?p)), 3); the readout dots have a colour-1 dot immediately left, so k1_core_to_blank, k3_core_blanks and k7_core_blanks carry colored(leftof(?s), 1); the port pixel has colour 0 left of it, so k1_core_to_field carries colored(leftof(?p), 0); the meter tip is the only instance with rightof off-board, so k4_meter_advances carries rightof(?s) = wall and every other BarCore rule fails a positive guard on it. I checked the four rules that can ground on colour 2 in one transition against all ten instances one at a time. NO RULE IN THIS FILE USES not: every exclusion is a positive colour test."
    [depends: the_swap_rules_are_thirty_six_and_constraint_three_is_failed  probe: pending]

  theorem the_twenty_four_field_cells_are_the_seating_i_am_betting_on "The named way this manual can fail replay. Twenty-four dynamic cells -- rows 30-35, cols 11, 12, 15, 16 -- render colour 5 at frame 0, and colour 5 is the BACKGROUND. The arm instances every cell of a declared colour the board cannot explain, and these cells vary, so they should seat. But cells_needing_an_owner is 73 rather than 97 and the 24 missing are exactly these, which shows something in the pipeline treats a background-coloured dynamic cell as needing nobody. IF FIELD SEATS NOTHING the fourteen Field rules never fire and replay is wrong by exactly those 24 cells at t1 and again at t2, and by nothing else. I take the bet because the alternative leaves 24 cells ownerless by construction, and because the failure is diagnosable at a glance."
    [depends: the_census_is_reconstructed_and_four_counts_confirm_it  probe: pending]

  theorem action1_here_should_move_seventy_two_cells_not_ninety_six "I stand in W0 but ACTION7 blanked the bottom readout at t5, so BOTH readouts render 4. Under the exchange reading, swapping two identical blank strips changes nothing, so ACTION1 now should move the 66 slot cells plus (32,13),(32,14),(33,13),(33,14) to colour 6, (39,16) to 5 and (38,16) to 5 -- 72 cells -- and no readout cell and no meter cell. My rules predict exactly that and not by arrangement: the readout rules are guarded on the pattern colours and simply do not ground when it is absent. 96 changed cells refutes the claim that a readout travels with its slot. 72 plus a cell of row 53 says the meter is not tied to ACTION4. Three outcomes, all legible in the raw diff."
    [depends: the_widget_is_two_slots_and_action1_exchanges_them  probe: pending]

  theorem the_readout_toggles_and_action3_and_action7_are_not_the_same_action "Twelve cells at rows 38-39 cols 17-22 have shown exactly two configurations in six states: BLANK (all 4) and PATTERN (eight 1s, four 2s). ACTION3 set BLANK at t3, ACTION4 set PATTERN at t4, ACTION7 set BLANK at t5. The pattern returns to the same twelve colours it had, which is why k4_dot_lights and k4_core_lights can be bare colour rules: an instance's TYPE is its frame-0 colour and therefore already records which cell gets a 1 and which a 2. WHAT I CANNOT CLOSE: ACTION3 and ACTION7 have identical net effects and I have written them as two rules with identical bodies, which is the shape of a claim that they are one key. THEY ARE NOT -- ACTION3 returned two internal frames and ACTION7 returned one. My own semantics say cascade single_frame, so my compiler discards the only evidence that separates them, and I record that here rather than pretend it is not in the log."
    [depends: the_census_is_reconstructed_and_four_counts_confirm_it  probe: passed]

  theorem the_meter_has_one_witness_and_its_next_cell_is_undrawable "Row 53 is a colour-2 bar across the frame; (53,63) turned 3 at t4 under ACTION4 and is the only cell of row 53 that has ever changed. I encode ACTION4-advances-it because that is the only reading this guard language can express and it has one witness. THREE READINGS FIT ONE WITNESS: that key 4 advances it, that lighting the readout advances it, that command index or parity advances it. There is no command counter in the guard language, so the third cannot be written at any length. THE STRUCTURAL PART: the next cell is (53,62), which has never changed, so it is board, so no instance sits on it, so no event here can touch it -- recolored takes an object and there is no object there. MY MANUAL MUST PREDICT THE SECOND ADVANCE NEVER HAPPENS and must be wrong by exactly one pixel every time the meter moves, until a later census heals one step behind. A divergence set of one cell in row 53 implicates nothing in this file."
    [depends: barcore_is_four_unrelated_things_and_the_arm_sees_only_colour  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where no rule fires I say NOTHING HAPPENS in the same voice I use for what I watched. Audit at the current state, W0 with both readouts blank. ACTION1: 72 cells, generalised from t1 and falsifiable at once -- not a silence. ACTION3 and ACTION7: predicted silent HERE because the pattern they erase is already gone; that silence is entailed by witnessed rules, not forged. ACTION4: predicted to light 12 readout cells and move no meter cell, the second half being the blind spot above rather than knowledge. ACTION2: PREDICTED SILENT ON ZERO WITNESSES -- every ACTION2 in the log was pressed in W1, never in W0 -- and that forgery covers 18 rules. ACTION5 and ACTION6: PREDICTED SILENT AND NEVER PRESSED IN ANY STATE. A probe ranker scoring expected bits over my manual and its ablations prices a predicted identity at zero, because every ablation agrees with a rule that does not fire, SO THE ACTIONS I MOST NEED ARE THE ONES IT CAN NEVER BUY. Saying so in prose is the only lever this desk has, and I would rather name the lever than pretend the silence is a finding."
    [depends: action1_here_should_move_seventy_two_cells_not_ninety_six, the_meter_has_one_witness_and_its_next_cell_is_undrawable  probe: pending]

  theorem no_goal_section_and_the_reason_is_arithmetic "The pos form is dead outright: nothing in this world moves, every rule here is a recolour, and no instance's pos changes in six states. That leaves counts over seven types whose members are one 12x12 widget plus one meter cell, and every count I can write names a CONFIGURATION rather than a victory. count(Frame, color = 5) = 14 says only the box is in the top slot. count(Dot, color = 4) = 8 says only the readout is blank. count(BarCore, color = 3) = 1 says the meter advanced once and IS TRUE RIGHT NOW, four commands after RESET, so declaring it would make the plan tier commit and report success at a state I have no reason to call a win. I cannot count the meter past one, because (53,62) and its 62 neighbours have never changed and hold no instance: THE GOAL LANGUAGE CAN ONLY SPEAK ABOUT CELLS THAT HAVE ALREADY MOVED. So there is no goal section. What ends that is an observation, not an edit -- a second cell of row 53, or any cell outside rows 30-41 and row 53 changing at all."
    [depends: the_meter_has_one_witness_and_its_next_cell_is_undrawable  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3999 constant cells, not just naming them board. A colour-4 panel fills about rows 29-41 from col 17 to col 46, carrying a 4x4 block of colour 14 at rows 31-34 cols 42-45 -- the only colour-14 anywhere and the only structure on the panel's right. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them from it. Row 29 shows the same 5,5,3,3,5,5 signature as the top slot but has NEVER changed, so the bar looks seven rows tall while only six of it is alive; I do not know whether row 29 is a static cap or a row the exchange refuses to move, and the exchange reading predicts it will look wrong on screen in W1. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the meter, row 54 a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports BOTH variants at negative gain -- minus 4037 bits on four tracks, minus 10409 on 33 -- so by its own measure it compressed nothing, and I take none of its structure. Its tracks are unusable individually: obj0, obj2 and obj3 are 436-to-440-cell blobs of shape 13x36 that swallow the colour-4 panel together with the widget; obj1 is a 108-cell 2x54 strip that is rows 53 and 54 read as one thing. What I DO take is a frame-index witness independent of my rules: obj0 present only at frame 0, obj2 first at frame 1, obj3 first at frame 2 and then present for four frames -- the widget redrawn at t1 and again at t2 and standing still after, exactly two 96-cell transitions and no third, which is the same shape as my S0 = S2 deduction arrived at from a different direction. cegis_miner refuses all four tracks and its verdict, that the world does not narrate as one mover, is TRUE and is the strongest negative result here: nothing in this world moves, everything recolours. zero_space self-reports THIN in its own words -- 5 transitions constraining rank 3 of 679 features, null space dimension 676 -- and its one global law is my census with the meter tip appended; I take the corroboration and reject the law as unfalsified rather than confirmed, which is what its own report says."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me. STATE: W0, both readouts blank colour 4, (53,63) rendering 3. ACTION1: exactly 72 cells change, no readout cell, no row-53 cell; 96 refutes the claim that readouts travel with slots. ACTION2: I predict NOTHING CHANGES on zero witnesses and I EXPECT TO BE WRONG -- if it exchanges, 18 rules generalise for free and my largest forgery closes in one press. ACTION3, ACTION7: nothing changes, and this one I believe. ACTION4: the 12 bottom readout cells take their frame-0 arrangement of 1s and 2s and NO cell of row 53 moves; if (53,62) turns 3 then ACTION4 advances the meter unconditionally, my rule is right in spirit and undrawable in fact, and the divergence set is one cell that implicates nothing. ACTION5, ACTION6: unconstrained, never pressed in six states, and I predict only that whichever of them is pressed produces the largest single addition to this manual available. If the next command is ACTION1, ACTION3 or ACTION7 I will have learned least, because those three are what the manual already speaks about."
    [depends: action1_here_should_move_seventy_two_cells_not_ninety_six, the_silences_i_assert_and_which_of_them_are_forged  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: six states, five transitions (RESET, A1, A2, A3, A4, A7). Widget in
# configuration W0 -- colour-3 bar in the TOP slot, hollow colour-6 box in the
# BOTTOM slot. BOTH readouts blank (colour 4). (53,63) advanced to 3 at t4.
# 97 cells have ever changed and all 97 are owned by the seven declared types.
#
# THE MANUAL WAS REPLACED, NOT PATCHED. The book I was handed described a
# different world; certify gave it 0/5 replay and a divergence at t=0. Gone.
#
# THE DEDUCTION EVERYTHING RESTS ON: states=6, distinct_states=5 forces
# S0 = S2. So ACTION2 undid ACTION1 and the CURRENT widget is the FRAME-0
# widget -- which is how frame 0 was read without being shown.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in any state. Zero constraint.
#   * ACTION2 in W0: never pressed. My manual says "nothing happens" on zero
#     witnesses. Largest forged silence in the file; it covers 18 rules.
#   * Whether ACTION4 advances the meter always, or only when it lights the
#     readout, or whether the meter runs on the command index. One witness
#     cannot split three readings, and the index reading is inexpressible.
#   * ACTION3 vs ACTION7: identical net effect, 2 frames vs 1. Not the same
#     action inside; cascade single_frame throws away the only evidence.
#   * The win condition. Nothing countable separates a win from here.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * (53,62) is board, holds no instance, is UNDRAWABLE. Every meter advance
#     after the first costs exactly one pixel of accuracy, permanently.
#   * The 24 background-coloured Field cells may not be seated. If not, t1 and
#     t2 each diverge by exactly those 24 and no rule of mine is wrong.
#   * ACTION1 now is predicted at 72 cells, NOT 96, because swapping two
#     identical blank readouts changes nothing. That is a prediction.
#
# THE RANKED LIST
# 1. ACTION5 or ACTION6. Never pressed in six states. Any outcome is the
#    largest single addition available -- including "nothing", which would be
#    the first WITNESSED inertness in this world. The ranker prices these at
#    zero because my manual is silent on them; that is a fact about my manual.
# 2. ACTION2, HERE, IN W0. Tests a zero-witness silence covering 18 rules. If
#    it exchanges, the toggle is key-symmetric and 18 rules generalise free.
# 3. ACTION4 A SECOND TIME, once the readout is lit. The only way to split
#    "key 4 advances the meter" from "lighting the readout advances it".
#    Costs a meter cell; read the answer off the RAW DIFF, since the
#    divergence lands on (53,62) which I cannot draw either way.
# 4. ACTION1, HERE. Fully predicted at 72 cells. Cheap confirmation of the
#    exchange reading. Buy only if the ranker refuses everything above.
#
# WHAT NOT TO PRESS
#   ACTION3 or ACTION7 here: the pattern they erase is already erased, my
#   manual predicts identity AND I believe it. Confirmed silence, no witness.
#   Anything chosen because my manual predicts the most pixels for it: that
#   number measures my coverage, not the world's information.

order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition         [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation       [proof: lean]
order     confirm_a_reconstructed_census_before_trusting_a_rule_built_on_it [proof: lean]
order     replace_a_manual_about_another_world_rather_than_patching_it      [proof: lean]
order     derive_a_state_collision_from_counts_before_guessing_a_frame      [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     prefer_a_positive_colour_test_over_a_negated_wall_test            [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it    [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language    [proof: lean]
order     spend_a_monotone_counter_only_on_a_question_it_actually_closes    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead               [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead     [proof: lean]
prune     divergence_lies_only_on_the_unadvanced_meter_frontier => dead     [proof: lean]
prune     divergence_is_exactly_the_twenty_four_background_coloured_cells => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     advances_the_meter_and_closes_no_open_question => dead            [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                   [admissible: lean]

prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 1/5 pressed keys]
prefer    a_command_that_tests_eighteen_rules_at_once                       [ev: 1/1 available]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 1/6 states]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 5/5 diffs]
prefer    a_free_probe_over_one_that_advances_the_meter                     [ev: 1/5 commands advanced it]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 2/6 states are W1 or W0-with-pattern]
```

=== LOG ===
```json
[
  {"id": "O-00", "subject": "the entire inherited manual", "verdict": "reject",
   "why": "certify gives it 0/5 replay, first divergence at t=0, 52 unexplained frame-0 pixels; it names a spawn ring at rows 8-12 and a meter at row 63 while every dynamic cell in this log lies in rows 30-41 cols 11-22 plus (53,63). It describes another world, so it is deleted rather than repaired."},

  {"id": "O-01", "subject": "dynamic-cell census (97 cells in five rectangles)", "verdict": "accept",
   "as": "the five rectangles named in the header", "why": "36+12+36+12+1 = 97 = dynamic_cells; the first four sum to 96 with bounding box rows 30-41 cols 11-22, matching both the t1 and t2 diffs; 97 minus 24 background-coloured cells = 73 = cells_needing_an_owner; 4096-97 = 3999 = constant_cells. Four counts I did not choose."},

  {"id": "O-02", "subject": "obj1 (mdl track, colour null, 2x54, present all 6 frames)", "verdict": "reject",
   "why": "it is rows 53 and 54 merged into one component; only (53,63) has ever changed, so 107 of its 108 cells are board and the track carries no dynamics."},

  {"id": "O-03", "subject": "obj0 / obj2 / obj3 (13x36 blobs, ~440 cells)", "verdict": "reject",
   "as": "not an object", "why": "connected_components(4) merged the colour-4 panel with the readouts cut into its edge; the tracks are 4.5x larger than the whole dynamic set and mdl_segmenter reports both variants at NEGATIVE gain (-4037, -10409), i.e. no compression by its own measure."},

  {"id": "O-04", "subject": "obj0/obj2/obj3 first-frame indices (0, 1, 2 then present 4 frames)", "verdict": "accept",
   "as": "corroboration only", "why": "an index witness independent of my rules that the widget was redrawn at t1 and at t2 and stood still after -- the same shape as the S0=S2 deduction, reached from a different direction."},

  {"id": "O-05", "subject": "Field (colour 5, 24 cells)", "verdict": "accept",
   "as": "Field", "why": "rows 30-35 cols 11,12,15,16 vary but render the background at frame 0; they are exactly the 97-73 gap in cells_needing_an_owner, and without them the exchange has 24 undrawable cells."},

  {"id": "O-06", "subject": "BarBody (3), BarCore (2), Blank (4), Frame (6), Hollow (0), Dot (1)", "verdict": "accept",
   "as": "six types, one per frame-0 colour", "why": "8+10+12+22+12+9 = 73 = cells_needing_an_owner exactly; together with Field they cover all 97 dynamic cells, so responsibility is total by construction."},

  {"id": "R-01", "subject": "the 18 key(1) exchange rules", "verdict": "accept",
   "why": "each fires on a disjoint cell set summing to 24+8+9+12+22+12+9 = 96, exactly the cells t1 changed; source colours are the frame-0 colours, which is legitimate because S0=S2 makes the current frame the frame-0 frame."},

  {"id": "R-02", "subject": "the 18 key(2) exchange rules", "verdict": "accept",
   "why": "mirror of R-01 with guards on the W1 renderings; they sum to 96 and are silent in W0 because every source colour they require is one no instance shows there."},

  {"id": "R-03", "subject": "k3_dot_blanks / k3_core_blanks (12 cells)", "verdict": "accept",
   "why": "the t3 diff is exactly 8 colour-1 and 4 colour-2 cells going to 4; the above-six-is-4 guard excludes the port pixel (38,16), whose above-six renders 5."},

  {"id": "R-04", "subject": "k4_dot_lights / k4_core_lights / k4_meter_advances (13 cells)", "verdict": "accept",
   "why": "the t4 diff is 12 readout cells plus (53,63); which cell takes 1 and which takes 2 is recorded by the instance's TYPE, so no geometry is needed, and the meter rule is the only one with rightof off-board."},

  {"id": "R-05", "subject": "k7_dot_blanks / k7_core_blanks", "verdict": "accept",
   "why": "identical bodies to R-03 under key 7, witnessed at t5. Recorded with the caveat in L-05: identical net effect but 1 frame against ACTION3's 2, so they are not the same thing inside."},

  {"id": "R-06", "subject": "a rule for ACTION2 in W0", "verdict": "reject",
   "why": "zero witnesses of any kind -- every ACTION2 in the log was pressed in W1. Writing it would be manufacture; my manual predicts identity there and I have named that as a forgery instead."},

  {"id": "R-07", "subject": "a rule for ACTION1 in W1", "verdict": "reject",
   "why": "same reason as R-06 with the configurations swapped."},

  {"id": "R-08", "subject": "a rule advancing the meter past (53,63)", "verdict": "reject",
   "why": "(53,62) has never changed, so it is board, so no instance sits on it, so recolored has no first argument to take. Structurally unwritable, not merely unwitnessed."},

  {"id": "R-09", "subject": "cegis_miner's four tracks", "verdict": "reject",
   "why": "it refuses all four and its verdict -- the world does not narrate as one mover -- is TRUE: nothing here moves, everything recolours, and a miner restricted to move/none has nothing to say."},

  {"id": "L-01", "subject": "S0 = S2", "verdict": "accept",
   "why": "states=6 with distinct_states=5 forces one collision; the meter tip separates S4/S5 from S0-S3 and the 96-cell diffs separate S1 from both neighbours, leaving S0=S2 as the only survivor. This is what makes frame 0 readable."},

  {"id": "L-02", "subject": "the exchange reading of ACTION1", "verdict": "probe-pending",
   "why": "it explains all 96 cells and explains why the count is 96 rather than fewer, but a two-item list scrolled down then up is observationally identical over two transitions. The separator is a third press of ACTION1."},

  {"id": "L-03", "subject": "zero_space's single global law", "verdict": "entailed",
   "why": "it is my census with the meter tip appended, and zero_space self-reports THIN -- rank 3 of 679 features, null space 676 -- so it is unfalsified rather than confirmed. I take the corroboration and no more."},

  {"id": "L-04", "subject": "Field seating on background-coloured dynamic cells", "verdict": "probe-pending",
   "why": "the arm's documented rule says these seat; the brief's own cells_needing_an_owner=73 suggests some part of the pipeline disagrees. If they do not seat, t1 and t2 each diverge by exactly those 24 cells and no rule is wrong."},

  {"id": "L-05", "subject": "ACTION3 and ACTION7 being one action", "verdict": "reject",
   "why": "identical net effect but 2 frames against 1. My cascade single_frame semantics discard the only evidence separating them, so I wrote two rules and recorded the discrepancy rather than merging them."},

  {"id": "L-06", "subject": "a goal section", "verdict": "reject",
   "why": "every count the grammar admits names a configuration, not a win; count(BarCore, color=3)=1 is TRUE RIGHT NOW, which would make the plan tier declare success four commands after RESET. The meter cannot be counted past one because its other 63 cells hold no instance."},

  {"id": "P-01", "subject": "ACTION5 or ACTION6", "verdict": "probe-pending",
   "why": "never pressed in any state; zero prior, so any outcome including a witnessed 'nothing' is the largest single addition available. Ranked first, with the honest note that the ranker prices it at zero precisely because my manual is silent on it."},

  {"id": "P-02", "subject": "ACTION2 pressed here, in W0", "verdict": "probe-pending",
   "why": "tests an 18-rule silence that rests on no witness; if it exchanges, those 18 rules generalise to both keys for free."},

  {"id": "P-03", "subject": "ACTION1 pressed here", "verdict": "probe-pending",
   "why": "my manual predicts exactly 72 cells, not 96, because both readouts are blank and swapping two identical blanks changes nothing. 96 refutes the claim that a readout travels with its slot."},

  {"id": "P-04", "subject": "ACTION4 twice in succession", "verdict": "probe-pending",
   "why": "the only way to split 'key 4 advances the meter' from 'lighting the readout advances it'. Costs a meter cell and its answer must be read off the raw diff, since (53,62) is undrawable under either reading."},

  {"id": "E-01", "subject": "the meter running on command index or parity",
   "verdict": "probe-pending",
   "why": "I wanted a guard on the command counter. The guard language reads pixels and the action name only, and there is no phase pixel anywhere in the frame, so this reading cannot be written at any length. I recorded it as one of three live readings in the_meter_has_one_witness_and_its_next_cell_is_undrawable instead."},

  {"id": "E-02", "subject": "'?p takes the colour of the cell six away'",
   "verdict": "probe-pending",
   "why": "I wanted one rule per direction. recolored(o, c) demands an integer literal, so the target cannot be read from a cell; the law split into 36 rules. I said plainly in the_swap_rules_are_thirty_six_and_constraint_three_is_failed that this fails the gain test and why I keep it anyway."},

  {"id": "E-03", "subject": "an UNKNOWN outcome for an unwitnessed state-action pair",
   "verdict": "probe-pending",
   "why": "I wanted to say 'I do not know what ACTION5 does'. The compiled step is total: no rule means identity, in the same voice as a witnessed silence, and a ranker scoring ablations prices both at zero. I wrote the audit in the_silences_i_assert_and_which_of_them_are_forged instead, naming which three silences are forged."}
]
```
```
