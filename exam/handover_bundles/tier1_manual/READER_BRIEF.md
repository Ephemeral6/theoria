# Reader brief — tier1_manual

## Who you are

You are a fresh reader. You have never seen this world, you have no record of
anyone playing it, no source code beyond this bundle, and no earlier
conversation about it. Everything you are entitled to use is in this bundle and
on the question sheet you were handed with it. If something is not in one of
those two places, you do not know it — say `abstain` rather than guess it.

## What you have been given

You have been given **the manual only**. There is no playbook in this bundle and there is not supposed to be one: this tier measures what a description of the world alone is worth. If you want a strategy, you will have to derive it.

Files in this bundle:

- `MANUAL.dsl` — the manual, in the form its author wrote it
- `MANUAL.md` — the same manual rendered into English, mechanically

## What to do

Read the bundle. Then answer every item on the question sheet. The sheet is a
JSON document; each item has an `item_id`, a `kind`, and whatever board
geometry and situation that item needs.

## How the sheet describes a board

An item that needs a board carries a `level` block giving the board's `height`,
its `width`, the list of `walls` and the `target` cell, and a `board` field
holding the same thing drawn as rows of characters. The lists are authoritative;
the drawing is there to be read at a glance.

P=Player  B=Box  #=wall  T=target cell  .=empty. Row 0 is the top row, column 0 the left column. If two of these share a cell the earlier letter is drawn, so the target is still the cell named in `target` even when it is not visible.

An item that needs a situation carries a `state` block with the Player's cell
and the Box's cell. Take the situation from `state`, not from any earlier item:
each item stands alone.

## How to write your answers

Produce **one JSON object**. Its keys are the `item_id` values from the sheet —
every one of them, none omitted, none invented. Its values are answer strings in
the grammars below. Nothing else: no commentary, no reasoning, no extra keys.

    {
      "<item_id>": "<answer string>",
      ...
    }

### `kind` = `step_semantics`

    player=(row,col); box=(row,col); rule=<name>

Exactly three fields. Separate them with semicolons. The order does not matter.
Case does not matter for the field names. `row` and `col` are integers.
`<name>` must be one of:

  - `walk`
  - `push2`
  - `blocked_wall`
  - `blocked_box_crossing`
  - `blocked_box_landing`

`player` is where the Player stands after the action, `box` is where the Box
stands after the action, and `rule` is the rule that accounts for what happened.
If nothing moved, `player` and `box` are where they already were.

### `kind` = `name_class`

One word, exactly one of:

  - `level_data`
  - `world_law`

Answer `level_data` if the item's name is something each individual board
supplies. Answer `world_law` if it is something the world fixes once and for
all, the same on every board.

### `kind` = `optimal_action`

One word, exactly one of:

  - `UP`
  - `DOWN`
  - `LEFT`
  - `RIGHT`

Name an action that begins a shortest sequence of actions ending with the Box on
the target cell. If several actions begin some shortest sequence, any of them is
accepted; you do not need to find them all.

### Any item

Instead of an answer you may write:

    abstain

An abstention scores nothing and is recorded as an abstention. A guess that
turns out wrong is recorded as a wrong answer. If you cannot work an item out
from this bundle, abstaining is the honest response and it is treated as one.

### Format example

This example uses an item id that is not on your sheet and a situation that
cannot occur; it shows the shape and nothing else.

    {
      "example-item-id-not-on-your-sheet": "player=(9,9); box=(9,9); rule=walk",
      "another-example-id": "world_law",
      "a-third-example-id": "abstain"
    }

## How you will be marked

By a fixed rule, published before your answers existed, applied mechanically. An
answer outside the grammars above scores zero and the parse failure is recorded;
it is not interpreted charitably. A step-semantics answer must have all three
fields right — two out of three scores zero.
