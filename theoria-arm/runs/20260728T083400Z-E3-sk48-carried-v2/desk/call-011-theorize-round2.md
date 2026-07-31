# call-011-theorize-round2

model: `claude-opus-5` · 4005 ms · $0.000000 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 0, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "inference_geo": "", "input_tokens": 0, "iterations": [], "output_tokens": 0, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
    "ms": 15,
    "script_bits": 8248,
    "split_by_color": false,
    "tracks": 4
   },
   {
    "baseline_bits": 5791,
    "compression_ratio": 6.883094,
    "events": 173,
    "gain_bits": -34069,
    "ms": 90,
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
# theory.dsl -- SIXTH DRAFT.
#
# NO NEW TRANSITIONS ARRIVED THIS ROUND. The store still reads 14 states, 13
# transitions, dynamic_cells 99, cells_needing_an_owner 75. What arrived is a
# CERTIFY REPORT, and it is the second consecutive round in which this manual
# named its own failure set in advance and the checker reproduced it exactly.
# That is the only new evidence, and it constrains exactly one thing: the
# checker. So exactly one theorem changes status, one rule-search is written
# down that was previously only asserted, and two honest gaps are opened that
# I had papered over. No rule changes, because nothing happened that could
# license a rule change, and I say so rather than fidgeting.
#
# 1. THE ONE SURPRISE THAT FIRED IS THE ONE I PRE-REGISTERED. replay_mismatch
#    at t=0, ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6. I
#    REFUSE TO CHANGE THE MANUAL FOR IT, and the refusal is not stubbornness,
#    it is two independent measured blockers:
#      (a) five cells -- (30,16), (31,16), (32,16), (33,16), (34,16) -- are
#          colour 5 in frame 0 with above 5, below 5, left 5, right 4, an
#          identical guard reading, and the world gives them 6, 6, 1, 2, 6.
#          Four distinct answers to one indistinguishable question. Constraint
#          5 forbids the rule set that would be needed.
#      (b) 24 of the 96 repainted cells are background colour 5 in frame 0, so
#          no declared object has an instance there and no recolored event can
#          name them.
#    Silence on the selector costs exactly ONE transition of thirteen, because
#    ACTION2 at t2 put the world back where my silent manual already was. Any
#    partial swap rule costs all thirteen by desynchronising an open-loop
#    replay. The arithmetic is unchanged and the surprise does not touch it.
#
# 2. PRE-REGISTRATION MET, SECOND TIME, AND IT SETTLES THE CHECKER. I wrote:
#    replay 9 of 13, first divergence transition 0 under ACTION1 with 96 cells,
#    responsibility 0 of 4096, unambiguous 0 clashes; and I wrote that a return
#    of 10 of 13 would mean the checker resyncs between transitions and would
#    refute my open-loop theorem. Certify returned 9 of 13, transition 0,
#    ACTION1, 96 cells, 0 unexplained, 0 clashes. Open-loop replay is now
#    confirmed rather than assumed, and every coverage figure in this manual is
#    to be read as open-loop. replay_is_open_loop... moves to probe: passed.
#
# 3. I NOW WRITE DOWN THE RULE SEARCH INSTEAD OF ASSERTING ITS RESULT. Last
#    round I claimed the eager march was the best available meter rule. This
#    round I traced the four alternatives by hand against all thirteen
#    transitions and none beats it. The ledger is in
#    nine_of_thirteen_is_the_ceiling_of_this_guard_language. If a searcher can
#    beat 9/13 without a counter in the grammar, that theorem is the thing to
#    refute.
#
# 4. TWO GAPS I HAD PAPERED OVER, OPENED ON PURPOSE.
#    (a) I do not know which way the bar runs. I have been writing deadline. A
#        cell going 2 -> 3 right-to-left is equally a progress meter filling.
#        Nothing in thirteen transitions separates them and the playbook was
#        quietly assuming one. That assumption is removed from the playbook and
#        the ambiguity is now a theorem.
#    (b) the restore rules fire on any Pip or Stud instance that is colour 4,
#        and in a slot-A-selected state that would restore the WRONG lane. My
#        manual never enters such a state, so open-loop replay never exposes
#        it, but a searcher planning through a selector move would be misled.
#        Named, not hidden.
#
# 5. WHAT IS STILL SHARP. The extra-frame clock stands at twelve advances and
#    predicts that the NEXT two-frame command consumes (53,60), while this
#    manual predicts it cannot, because (53,60) has never varied and carries no
#    instance. One action separates them and the state is blanked, so the same
#    action also separates hide-and-show from toggle-and-toggle and scores my
#    committed prediction of inert. Three questions, one command.

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
  landmark meter_fourth  # arc-cell: (53, 60)
  Casing [segment: colour_class_6 ev: t0-t13 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t13 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t13 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t13 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t13 compress: 12]
  Erased [segment: colour_class_4 ev: t0-t13 compress: 12]

events:
  event recolored(o, c)

# All eight rules are byte-for-byte last round's. No transition arrived that
# could move them, and a rule edited without evidence is a rule I would have to
# un-edit. What changed is that rule eight's status is now the conclusion of a
# written search rather than an assertion, and rule seven's one-shot coverage
# now carries an explicit defence: it is worth three transitions, not one,
# because nothing else can seed the march.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3,t7,t9,t11,t13 cov: 40/40]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3,t7,t9,t11,t13 cov: 20/20]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4,t6,t8,t10,t12 cov: 40/40]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4,t6,t8,t10,t12 cov: 20/20]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_advances_the_meter_once forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall and colored(below(?p), 4) then recolored(?p, 3)

  rule key3_marches_the_meter_leftward forall ?p in Stud [ev: t11 cov: 1/3]
    when act=key(3) and colored(?p, 2) and colored(above(?p), 5) and colored(below(?p), 4) and not rightof(?p) = wall and colored(rightof(?p), 3) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 12 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 75 [status: proven]

  theorem the_pre_registration_has_now_been_met_twice_and_the_checker_is_open_loop "two rounds running I wrote the failure set before the checker ran and the checker returned it. This round: predicted replay 9 of 13, first divergence transition 0 under ACTION1 with 96 cells wrong, responsibility 0 unexplained of 4096, unambiguous 0 clashes. Certify returned exactly that. The load-bearing half is the negative one: I named 10 of 13 as the outcome that would prove the checker resyncs between transitions, and 10 did not come back. So replay is open-loop, confirmed rather than assumed, and every coverage number here is an open-loop number. The honest deflation is that this draft changes no rule, so its replay prediction is the same 9 of 13 and predicts nothing new about the checker. The informative pre-registration has moved off the checker and onto the world: the next two-frame command either consumes (53,60) or it does not, and this manual says it cannot."
    [depends: replay_is_open_loop_and_silence_on_the_selector_is_still_the_cheap_error  probe: passed]

  theorem nine_of_thirteen_is_the_ceiling_of_this_guard_language "last round I asserted the eager march was the best meter rule available. This round I traced the alternatives by hand over all thirteen transitions and wrote the numbers down. Silence on the meter after the seed: matches 1,2,3,4,5,6 then diverges from transition 7 to the end, 6 of 13. March on key(3), the rule I keep: wrong at 0, 6, 8, 9, so 9 of 13. March on key(4) instead: wrong at 0, 5, 6, 9, also 9 of 13, and it is the worse of the two because its single witness is a key whose meter role I have already refuted. March on both keys: consumes three cells by t8 while the world has consumed two, wrong at 0, 5, 6, 7, 8, 9, so 7 of 13. Nested march requiring two consumed cells to the right: never fires at all once the manual has missed (53,62), so 6 of 13. Four alternatives, none better, and the reason is the same in every case -- the cadence is a count and the grammar has no counter. This is a hand search over the rules I could think to write, not a proof of optimality, and it is exactly the claim a searcher should try to break."
    [depends: i_reverse_my_preference_for_understatement_and_here_is_the_ledger  probe: passed]

  theorem the_seed_rule_is_a_one_shot_that_is_worth_three_transitions "key4_advances_the_meter_once has coverage 1/1 and fires exactly once in the whole history, which by constraint 3 looks like a rule spent to explain one pixel and therefore a loss. It is not, and here is why. The march rule requires a colour-3 neighbour to its right, and (53,63) has no right neighbour at all -- rightof is wall -- so no march rule can ever consume the first cell. Delete the seed and the meter never starts, the march never finds a colour-3 anchor, and the manual falls from 9 of 13 to 6 of 13. The rule buys three transitions, not one. What it does not buy is understanding: it fits the ONE thing about the first tick I can express, that the rightmost bar cell went first, and it is silent about why that tick fell on a key(4) press when the third tick fell on a key(3) press."
    [depends: nine_of_thirteen_is_the_ceiling_of_this_guard_language  probe: passed]

  theorem i_do_not_know_which_way_the_bar_runs "I have been writing deadline for four drafts and I have no evidence for it. What is measured is that row 53 holds colour 2 from column 10 to column 60 and colour 3 from 61 to 63, and that the boundary moved left three times, one cell each. That is equally a resource being spent and a progress meter being filled, and colour 3 is also the colour an unselected slot shows on its rails, which argues weakly that 3 is a resting or completed state rather than a consumed one. Nothing in thirteen transitions separates the two readings, and they invert the sign of every ranking decision: under the deadline reading a probe costs a third of a bar cell, under the progress reading the same probe earns it. Until something separates them the playbook may not rank on bar movement in either direction, and I have removed the entries that did. The separator is cheap and will arrive on its own -- either the bar reaching column 10 ends the level, or NOT_FINISHED survives it."
    [depends: the_tick_is_not_bound_to_the_restore_key_and_two_readings_are_dead  probe: pending]

  theorem the_restore_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "key4_restores_the_strip_pips and _studs guard on colour 4 alone and nothing else. That is correct on every transition observed, because every key(4) press was made from a state where slot B was selected and the only colour-4 Pip and Stud instances in existence were the six-by-two blanked cells of lane B. It would be wrong the moment slot A is selected: lane B's strip cells become arena fill of colour 4 while their Pip and Stud instances persist, so a key(4) would repaint lane B's texture into an unselected lane. My manual never reaches that state, because it is silent on the selector and open-loop replay therefore never leaves slot B, so this costs zero transitions today and certify cannot see it. It is written here because a searcher that plans through a selector move would be misled by a rule that scores 40/40. The fix needs a guard that reads which slot is selected, and selection is exactly the thing the guard language cannot see."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_tick_is_not_bound_to_the_restore_key_and_two_readings_are_dead "at t11 ACTION3 turned (53,61) from 2 to 3. The first two ticks, at t4 and t8, were ACTION4. So the meter is not a toll on the restore key, and the parity reading I carried for two drafts -- tick on the first, third, fifth key(4) -- is refuted outright, because the third tick was not a key(4) press at all. The period-4 clock is refuted too: ticks fell after global actions 4, 8 and 11, gaps of four and then three. Both readings were named in advance as the two survivors and both are gone in one transition, which is the whole value of having written them down. What survives is the shape: consumption is one cell at a time, strictly right to left, monotone, and indifferent to which key was pressed."
    [depends: the_world_has_hidden_state_and_there_are_now_two_witnesses_on_two_keys  probe: passed]

  theorem the_clock_ticks_in_extra_frames_not_in_actions "count the commands that returned two frames rather than the commands. t1,t2,t3,t4 make four and the meter ticks; t5 returned one frame and the count stays at four; t6,t7,t8 make seven and it ticks; t9,t10,t11 make ten and it ticks. Period three, hit exactly three times out of three, where the action count gives the irregular 4,8,11 and the cumulative frame count gives the irregular 8,15,21. The reading is that a command advances the world's clock by its frame count minus one, and the meter loses a cell every third advance. Honesty about strength: three ticks against a period and an offset is two parameters fitted to three points, so this is one degree of confirmation, not a law. Its virtue is that it is sharp right now -- t12 and t13 were both two-frame commands so the count stands at twelve, and the next two-frame command should consume (53,60), while my manual predicts no consumption there because (53,60) has never varied and carries no instance. One action separates them."
    [depends: the_tick_is_not_bound_to_the_restore_key_and_two_readings_are_dead  probe: pending]

  theorem i_retract_that_cascade_length_carries_no_signal "two drafts ago I wrote that frame count tracks neither the magnitude nor the identity of change and must not be used as a motion detector. The first half stands: t5 with one frame and t7 with two produced identical twelve-cell effects, so a single frame does not mean nothing happened. The second half was too strong. Exactly one command in thirteen returned a single frame, and it is exactly the command the meter clock skipped. If that holds, frame count is the world's own step counter and ACTION7 is a key that acts without spending a step -- a free action, which would be worth more than any other fact I could learn here. The rival explanation is that the single frame at t5 was an artifact of the harness and the coincidence with the clock gap is luck. Repressing ACTION7 settles it, since a second single-frame return under a key that changes cells is not luck twice."
    [depends: the_clock_ticks_in_extra_frames_not_in_actions  probe: pending]

  theorem i_reverse_my_preference_for_understatement_and_here_is_the_ledger "two drafts ago I wrote that between two manuals that replay equally I keep the one whose error is a missing event. That preference was conditioned on equality and the condition failed. Traced by hand over all thirteen transitions: a manual silent on the second and third ticks matches 1,2,3,4,5,6 and then diverges at (53,62) from transition 7 to the end, six of thirteen; the eager march matches nine of thirteen, because its divergences close when the world catches up. The reason is structural rather than lucky: consumption is monotone and right-to-left, so consuming early is an error in timing alone, never in which cell or in what order, and timing errors in a monotone process heal. Certify has now scored this manual at 9 of 13 with an open-loop checker, so the nine is measured and not my arithmetic. I record the price: the rule invents ticks at t7 and t9, which is why its coverage reads 1/3 and not 1/1."
    [depends: the_tick_is_not_bound_to_the_restore_key_and_two_readings_are_dead  probe: passed]

  theorem the_march_rule_stops_for_a_reason_i_do_not_trust "key3_marches_the_meter_leftward stops at column 61 and that is why it matches transitions 10, 11 and 12 instead of running away. It stops because (53,60) has never varied, so the arm creates no Stud instance there and no rule can recolour it. That is a fact about instance anchoring, not about the world. The moment the world consumes (53,60), the arm will place an instance there on the next build and this rule will run one cell ahead again before healing again. So the rule's good score is partly a boundary effect, and a searcher must read it as a proxy for a cadence the language cannot count, not as the claim that pressing key(3) costs a bar cell -- over the observed trace key(3) was pressed five times and the bar lost three cells in total, two of them on other keys."
    [depends: i_reverse_my_preference_for_understatement_and_here_is_the_ledger  probe: pending]

  theorem the_world_has_hidden_state_and_there_are_now_two_witnesses_on_two_keys "first witness: S5 reached by key(7) at t5 and S7 reached by key(3) at t7 are the same frame cell for cell, and key(4) from S5 moved no bar while key(4) from S7 consumed (53,62). Second witness, on a different key: S8, reached by the restore at t8, and S10, reached by the restore at t10, are also identical -- strip shown, (53,63) and (53,62) consumed, (53,61) still colour 2 -- and key(3) from S8 only blanked the strip while key(3) from S10 blanked it and consumed (53,61). Same state, same action, two successors, twice, under two different keys. The store corroborates without being asked: fourteen states and nine distinct requires exactly five collisions, and the only assignment available is S2=S0, S6=S4, S7=S5, S10=S8, S13=S11. My guard language has no counter and no memory of the previous action, so I write the ticks I can witness and pay for the ones I cannot."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_meter_cadence_is_inexpressible_and_i_checked_for_a_latch "a guard reads a cell's colour, its four neighbours' colours, off-board, and the action name. A cadence needs a count and there is no count in the grammar. Before settling for a proxy I checked the one loophole I could see: an object whose declared colour equals the background renders the same whether present or vanished, so present could in principle be an invisible bit. It cannot be used. The value grammar exposes only color as a field, so no guard can read present; and an object declared with arc-colour 5 would be instantiated on every background cell the board cannot explain, which is the twenty-four cells of the swap footprint, one instance each and none of them where a latch would be wanted. So the cadence stays prose and the manual carries a proxy that is honest about being one."
    [depends: the_clock_ticks_in_extra_frames_not_in_actions  probe: passed]

  theorem the_bar_is_between_fifty_one_and_sixty_one_cells_from_its_end "row 53 reads colour 2 over columns 10 to 60 and colour 3 over 61 to 63. I have never been shown columns 0 to 9 of that row, so 51 cells are measured unconverted and up to 61 exist if the bar reaches the left edge. At one cell per three clock advances that is 153 to 183 advances, and at two frames per ordinary command roughly the same number of actions. I have deliberately stopped calling this a countdown, because I do not know the sign -- see i_do_not_know_which_way_the_bar_runs. What is safe in either reading is the magnitude: the budget is large compared with thirteen actions, so probing is cheap now and will not stay cheap."
    [depends: i_do_not_know_which_way_the_bar_runs  probe: pending]

  theorem replay_is_open_loop_and_silence_on_the_selector_is_still_the_cheap_error "the manual is run forward from frame 0 without resync, and this is now confirmed and not assumed: I pre-registered 10 of 13 as the score a resyncing checker would produce and certify returned 9. Transition 1 counts as a match only because the world returned to frame 0 under key(2) while my silent manual had never left it. Silence on key(1) and key(2) therefore costs exactly one transition out of thirteen. A wrong or partial swap rule would produce a frame equal to neither manual nor world, desynchronise permanently and cost all thirteen. That arithmetic has not changed and the new certify does not touch it, since no selector key has been pressed since t2."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and (53,63), (53,62) and (53,61) hold 2 rather than 3. The anatomy closes cell by cell: 22 Casing as a 20-cell ring minus two ports plus a 2x2 core at rows 38-39 cols 13-14, 12 Cavity as a 4x4 at rows 37-40 cols 12-15 minus that core, 8 Rail as the unselected slot's bar at rows 30-31 and 34-35 by cols 13-14, 4 Stud as the same bar's middle at rows 32-33, 9 Pip and 5 Stud in the strip and the two ports, 12 Erased in lane A at rows 32-33 by cols 17-22, 3 Stud in the meter bar, total 75 = cells_needing_an_owner. The 24 remaining dynamic cells are exactly the background cells of the unselected slot's 6x6 footprint, cols 11, 12, 15, 16 over six rows, and 75 + 24 = 99 = dynamic_cells. The t1 diff of 96 is 36 for panel A, 36 for panel B, 12 for lane A's strip rows and 12 for lane B's, with nothing left over."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_the_arm_extends_it_as_cells_vary "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0. A cell constant in frame 0 gets no instance, which is why the slots above row 29 are invisible to this manual and why 24 background cells of the swap are unreachable. A cell that later varies stops being board and gains one: this has now happened twice and both times the store moved as predicted, (53,62) at t8 taking cells_needing_an_owner from 73 to 74, and (53,61) at t11 taking it from 74 to 75 with dynamic_cells 98 to 99. stud_population is 12 accordingly. This is also the mechanism behind the march rule's boundary and the reason its score is not fully mine."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_strip_hides_and_shows_and_the_separator_is_still_one_action_away "key(3) blanked a shown strip at t3, t7, t9, t11 and t13; key(7) blanked one at t5; key(4) restored a blanked one at t4, t6, t8, t10 and t12, twelve cells and cell-for-cell identical every time, so the pattern lives somewhere the frame does not show. All six blank presses were made from a shown strip and all five restore presses from a blanked one, so after thirteen actions hide-and-show and toggle-and-toggle remain indistinguishable. The state now is blanked. My manual commits to inert for a repeat of the hiding key: every strip cell is colour 4 so no blanking rule can fire, and the march rule finds no colour-2 Stud with a consumed right neighbour because (53,60) carries no instance. A restore of the strip refutes hide-and-show; a consumption of (53,60) refutes my manual and confirms the extra-frame clock; nothing happening confirms both."
    [depends: the_clock_ticks_in_extra_frames_not_in_actions  probe: pending]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language can produce them. A guard sees a cell's own colour and its four neighbours' colours and nothing else -- no coordinate, no row band, no distance. The witness is measured, not reconstructed: (30,12) and (31,12) are both colour 5 in frame 0 with above 5, below 5, left 5, right 3, and the world makes them 6 and 0. (32,13) and (32,14) are colour 2 with left and right in the same bar and become 6, while (30,13) and (30,14) are colour 3 in an identical local neighbourhood and also become 6. And (30,16), (31,16), (32,16), (33,16), (34,16) are all colour 5 with above 5, below 5, left 5, right 4 and must become 6, 6, 1, 2, 6 -- four distinct answers to one indistinguishable question. Constraint 5 forbids rules that both fire, so the swap does not go in the manual, and the replay_mismatch at transition 0 is a cost I accept rather than a defect I can repair."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem the_swap_has_a_second_blocker_twenty_four_of_its_cells_have_no_instance "24 of the 96 cells the swap repaints are colour 5 in frame 0 -- the background cells of the unselected slot's footprint at cols 11, 12, 15, 16 over rows 30 to 35. No declared object carries colour 5, so no instance exists there, so no recolored event can name them, and this blocker does not depend on what a guard can see. The only escape is declaring the background itself an object, which puts an instance on every unexplained colour-5 cell and makes the manual responsible for arguing about the arena's filler. Both blockers point the same way."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem nesting_would_not_rescue_the_meter_either "if rightof(rightof(?p)) parses -- the grammar does not document nesting -- I could write a meter rule that requires two consumed cells to the right, which fires on (53,61) and never on (53,62), and so invents nothing. I traced it: it scores 6 of 13, no better than silence, because the manual's own state lags. Having missed (53,62) it can never see two consumed cells and the rule never fires at all. Nesting is a parse risk that buys nothing here, and for the swap it would cost 96 neighbour chains to explain 96 pixels, which is exactly the failure constraint 3 names."
    [depends: nine_of_thirteen_is_the_ceiling_of_this_guard_language  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have ever seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Witnesses: frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, the same period-3 run offset by one column; and the divergence report gives all seven of row 32 cols 16-22 as the world drew them at t1 -- 1 2 1 1 2 1 1 -- with rows 32 and 38 agreeing because they are six apart. So the two strips are two windows onto one diagonal texture, which is why the restore can rebuild twelve cells exactly. Untested prediction, unchanged: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2 with (33,16) colour 2. No rule needs it, since each instance already remembers its frame 0 colour, so by constraint 3 this concept buys understanding rather than symbols and I say so."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, six times now, twelve cells every time. (38,16)=1 and (39,16)=2 sit on the widget's right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since leftof both is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The alternative is that col 16 is simply where the 6x6 box ends and the survival is coincidence; thirteen transitions do not separate them."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied, so they are board. Colour 3 at cols 13-14 is what an unselected slot shows at its four outer rows, and the unselected slot at rows 30-35 shows 3 3 2 2 3 3 down those columns, so row 29 sits where the last row of a slot at rows 24-29 would sit. The period is measured: the divergence report gives the world's t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at the same columns read identically. Eighteen cells, six rows apart. Rows 42 onward are uniform background, so rows 36-41 is the bottom slot. I read key(1) as move selection up one slot and key(2) as down one. The probe is still the cheapest structural test in the game and it has two halves: from the bottom slot the down key should do nothing under the move reading and repaint 96 cells under a two-slot toggle, and from the upper slot the up key should repaint rows 24-35 if a third slot exists. My manual is silent on both, so either press scores it for free."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_arena_is_lanes_and_the_badge_is_row_aligned_with_the_cavity "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45, confirmed again in the current frame. Those are exactly the rows a selected slot's 4x4 cavity occupies within its own 6-row band -- the selected bottom slot's cavity is rows 37-40 within band 36-41, and the badge is rows 31-34 within band 30-35. So the badge is a cavity-shaped, cavity-aligned object at the far right of slot A's lane, and slot B's lane has nothing at cols 42-45. Either it is a target the lane must be made to match, or it marks which slot carries a task. Zero transitions bear on either, and slots above row 29 may carry badges I have never seen, since an unvarying badge is board by definition."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, which is rows 29-54 by cols 10-63. They are somewhere in the 3997 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is also where a title, target, score or instruction would live, and the most likely home of whatever finishing means. It is the largest thing I do not know, and it is also where the answer to i_do_not_know_which_way_the_bar_runs most plausibly sits."
    [depends: no_goal_section_on_purpose  probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot's bar, a port, four strip cells and three cells of the meter -- four unrelated roles, and the meter role needs two rules of its own. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 75 cells that need an owner against 75 pixels written out, with 0 unexplained confirmed twice by certify. The cost is measured too: no rule can name the strip, so every strip rule carves it out of its class with four negative neighbour guards, and both meter rules need an off-board or above-is-background test to separate cells of the same class. Those guards are pixel-fitting in a costume, they are correct on every instance in frame 0, and they are the price of a colour-first arm."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem two_keys_have_never_been_pressed "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not. The case for pressing them is stronger than last round, because t6, t10 and t12 were restore presses that moved no bar and the extra-frame clock says the cost of any single command is one third of one bar cell out of fifty-one or more. If either is a click carrying coordinates, this guard language cannot express it and the finding will be recorded as prose. Each press also reads its own frame count, which is now the clock probe, and a press that changes nothing at all still discriminates one frame from two."
    [depends: i_retract_that_cascade_length_carries_no_signal  probe: pending]

  theorem no_goal_section_on_purpose "all fourteen states returned NOT_FINISHED and nothing in thirteen transitions indicates what finishing means. The live candidates are that a lane's texture must be brought to agree with the badge at its far end, that every slot in the column must be visited or solved, or that the objective lives in the rows I have never been shown. An absent goal compiles to is_goal -> False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. I previously wrote here that the bar running out is a deadline; I withdraw that sentence, because I cannot tell a deadline from a progress meter, and the playbook now ranks on neither."
    [depends: i_do_not_know_which_way_the_bar_runs  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "the proposal stream is materially unchanged and I re-read it rather than assuming. mdl_segmenter returns negative gain on both variants, -2989 bits at 4 tracks and -25963 at 69, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator and not the world; its event tally of 14 recolors, 2 appears and 2 vanishes is however consistent with my reading that this world only ever recolours and that the two appear/vanish pairs are the swap seen as a blob. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition and this world has no mover; its own verdict says the world does not narrate as one mover, which agrees with my event vocabulary. zero_space calls its own evidence THIN in its own words -- 13 transitions constraining rank 5 of 693 features, null space of dimension 688 -- and its single global law spans nearly every dynamic cell at once, which is what a 688-dimensional null space produces rather than what a conservation law looks like. What I took from the engines is the store arithmetic, dynamic_cells 99 and cells_needing_an_owner 75, and both closed against a reconstruction built without them."
    [probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- sixth draft. Small changes, each forced.
#
# NOTHING NEW HAPPENED IN THE WORLD THIS ROUND. No transition arrived, so no
# ranking entry may move on evidence about the world. Two things did move.
#
# 1. THE CHECKER IS SETTLED. I pre-registered that a 10-of-13 return would mean
#    the checker resyncs; it returned 9. Replay is open-loop, confirmed. The
#    prefer-entry that ranks pre-registered actions keeps its 9/13 evidence tag
#    and that tag is now a measurement rather than my own arithmetic.
#
# 2. I REMOVED AN ASSUMPTION I HAD NO RIGHT TO. Every previous draft ranked as
#    if the bar were a countdown. I cannot tell a countdown from a progress
#    meter: three cells went 2 -> 3 from the right edge leftward and that is
#    all. Under one reading a probe costs a third of a cell; under the other it
#    earns one. So the two entries that ranked on bar movement are gone and a
#    prune replaces them. Every remaining entry is sign-independent, and the
#    one surviving bar entry -- the deadline prune -- is safe in both readings,
#    because a progress bar that fills would presumably not leave us NOT_GOAL.
#
# THE NEXT COMMAND IS STILL THE SAME COMMAND, AND IT IS STILL WORTH THREE
# ANSWERS. The state is blanked. Pressing the hiding key from here separates
# hide-and-show from toggle-and-toggle, tests the extra-frame clock (the count
# stands at twelve, so a two-frame return should consume (53,60) while my
# manual says it cannot), and scores my manual's committed prediction of inert.
# Immediately after it, repressing the key that once returned a single frame
# tests whether that key is free of the world's clock.
#
# Nothing below is a stored line of play. Every entry is a ranking rule that
# still has to be evaluated against whatever state the searcher is in.

order   separate_hiding_from_toggling_by_repressing_the_hiding_key_in_the_hidden_state  [proof: lean]
order   settle_the_extra_frame_clock_on_the_next_command_before_the_count_drifts  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_for_freedom_from_the_clock  [proof: lean]
order   settle_which_way_the_bar_runs_before_ranking_anything_on_it       [proof: lean]
order   press_the_two_never_pressed_keys_while_the_budget_is_still_long   [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule      [proof: lean]
order   make_some_cell_outside_the_observed_window_vary                   [proof: lean]
order   compare_a_lane_against_the_badge_at_its_own_far_end               [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known          [proof: lean]
order   read_every_bar_cell_that_changed_and_the_returned_frame_count_after_every_command  [proof: lean]

prefer  an_action_the_manual_has_pre_registered_a_frame_for               [ev: 9/13 transitions replay]
prefer  an_action_on_which_two_live_readings_predict_different_frames     [ev: 3 rival pairs open]
prefer  an_action_that_answers_more_than_one_open_question_at_once        [ev: 1 press separates 3]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/13 commands returned one frame]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  a_slot_never_selected_over_one_already_drawn_twice                [ev: 2 slots seen of a column]
prefer  a_state_whose_lane_carries_the_badge_over_a_lane_without_one      [ev: 1/2 lanes carry a badge]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats        [ev: 99/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced           [ev: 0/13 transitions test it]

heuristic advances_of_the_extra_frame_clock_still_available               [admissible: lean]
heuristic slots_in_the_column_never_yet_selected                         [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed                          [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                    [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                     [admissible: lean]
heuristic open_questions_no_single_command_can_yet_separate              [admissible: lean]

prune   plan_that_rests_on_the_bar_direction_being_known => dead          [proof: lean]
prune   plan_that_treats_one_particular_key_as_the_metered_one => dead    [proof: lean]
prune   plan_that_reads_the_march_rule_as_a_price_per_press => dead       [proof: lean]
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
  "detail": "no Lean form was generated",
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
  "detail": "9/17 transitions replay exactly",
  "matched": 9,
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
  "clashes": [],
  "detail": "no (state, action) among 18 x 3 admitted two rules",
  "ok": true,
  "scope": "sampled",
  "states": 18
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
You've hit your session limit · resets 8:20pm (Asia/Shanghai)
```
