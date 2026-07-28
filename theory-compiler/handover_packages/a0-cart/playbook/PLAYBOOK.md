# The playbook for this world

The manual says what the world does. This says how to win in it — and, more usefully, how to avoid work.

Nothing here is a solution to any board. The playbook's grammar has four sentence forms — ordering, pruning, heuristics, preferences — and no form for a sequence of actions. A solution is a planner's output, not a book's content.

Every entry is written in the manual's vocabulary and answers to the manual, not to the world: change the clause an entry rests on and the entry is void.

## Heuristic

An estimate of how much work is left, used to steer the search. `admissible` says whether it is proved never to over-estimate; `none` means it is not, so it may mislead.

- `heuristic w_room(Cart)` — admissible: none

## Ordering

Do this before that. An ordering changes how fast an answer is found and never which answers are correct.

- `order press_before_door` — proof: lean

## Pruning

A search node matching this is dead: nothing reachable from it wins. Cutting it changes nothing about which boards are winnable — it only stops work that could not have paid.

- `prune w_room(Cart) > 0 and no_button => dead` — proof: lean

## What is not in here

This playbook has no entry of these forms: Preference.

A `prefer` entry must carry a win rate or a node count, because the grammar requires one. An empty empirical tier means nobody measured, not that nothing works.

`playbook/PLAYBOOK.dsl` is the source these sentences were read from, comments and all.
