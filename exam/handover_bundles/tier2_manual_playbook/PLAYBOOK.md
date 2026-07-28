# The playbook for this world

The manual says what the world does. This says how to win in it, and — more
usefully — how to avoid work.

Nothing here is a solution to any particular board. The playbook deliberately
contains no board, no position and no sequence of actions: those are outputs of
planning, not contents of a book.

## What the conservation law is for

The manual records that the Box's row parity and its column parity never change.
That is a fact about the world; here is what to do with it.

**Decide before you search.** Compare the Box's row parity with the target's row
parity, and the Box's column parity with the target's column parity. If either
disagrees, the board is impossible — not "no plan was found", but *there is no
plan*, and the reason fits on one line. Searching such a board is wasted effort
in the best case and unbounded effort in the worst.

**Shrink the search when you do search.** Even when the parities agree, the law
says the Box can only ever stand on cells matching its own row parity and its
own column parity. Three quarters of the board is unreachable for the Box before
a single action is considered. Any search that expands nodes placing the Box on
those cells is expanding nodes that cannot exist.

**The certificate is the explanation.** When a board is refused, the refusal is
checkable by anyone with the manual: this parity, that parity, they differ, the
law forbids the crossing. That is a different kind of answer from "my search
finished and found nothing", and it is the answer this framework is for.

## Deadlocks

A deadlock is a situation that is not yet lost by the goal condition but from
which the goal can no longer be reached. They are the daily business of this
world, far more common than a whole board being impossible.

**The Box is frozen.** The Box moves only when the Player stands directly behind
it *and* the cell it would cross *and* the cell it would land on are both free.
If, in every one of the four directions, at least one of those three conditions
can never be met, the Box will never move again. If it is not already on the
target, the board is lost.

**The two-cell slide makes edges wider than they look.** Because the Box travels
two cells, it cannot be pushed toward a wall that sits one *or* two cells away
in that direction — one cell away blocks the crossing, two cells away blocks the
landing. A Box that would be pushable in an ordinary one-cell world can be
immovable here. Reason about the pair of cells, never about the next cell alone.

**The Player is not a wall but the Box is.** The Box blocks the Player's walking;
the Player blocks nothing. So the Player can always be routed anywhere the walls
allow, provided the route does not pass through the Box — which is exactly the
constraint that makes some pushes unreachable even when the Box could accept
them.

## Choosing an action

**Count pushes, then count walking.** Each push closes two cells of the gap
between the Box and the target along one axis. So the number of pushes still
needed is at least half the remaining row distance plus half the remaining
column distance. This is a lower bound and can be used to order candidates; it
is not proven admissible for the total number of actions, because the walking
between pushes is not counted.

**Plan the pushes, then plan the walking.** The Box's route is the hard part and
the Player's route is almost always the easy part: the Player is unobstructed
except by walls and by the Box itself. Work out which sequence of pushes brings
the Box to the target — respecting both parities and the deadlocks above — and
only then work out how to get the Player behind the Box each time.

**Getting behind the Box costs actions, and turning around costs the most.**
Pushing the Box in a direction requires the Player to be on the cell immediately
opposite that direction. Continuing a push in the direction already being pushed
is free — the Player is already in place, having followed the Box. Changing the
push direction means walking around the Box, and the Box is in the way while you
do it. A route that pushes along one axis and then the other is usually cheaper
than one that alternates.

**Only pushes are irreversible.** Walking can always be undone. A push may not
be: whether the Box can be pushed back depends on whether the Player can get to
the far side of it and on what is behind it there. Treat every push as a
commitment and check the deadlock conditions before making it, not after.

## Where this book came from, and what it does not have

Every claim above is derived from clauses of the manual, and the derivation is
short in each case. That is the pre-registered prediction of the layered
handover: a reader given only the manual should be able to reconstruct this
book, and should end up at the same place after paying the search cost this book
saves. If that turns out to be false, this book contains something the manual
does not, and finding out what would be the interesting result.

There is no empirical tier — no "this move ordering wins 7 times in 10" — because
no such measurement exists for this world. An entry of that kind without the
count behind it would be invented evidence.
