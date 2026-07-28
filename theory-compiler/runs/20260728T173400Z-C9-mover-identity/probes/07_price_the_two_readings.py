"""Probe 07 -- why the matcher prefers the wrong reading, in bits.

At the frame where the agent steps onto a token the bipartite matcher has two
explanations available and it picks by cost:

  A (chosen)  the token *recolours in place* to the agent's colour,
              and the agent *vanishes*.
  B (true)    the agent *moves* one cell onto the token,
              and the token *vanishes*.

Both explain exactly the same changed pixels.  This prints what each costs under
`engine-rig`'s published cost model, so the choice is a number rather than a
suspicion.

Read-only.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "engine-rig"))

from engines.mdl_segmenter.costs import CostModel  # noqa: E402

# t2-lock-fragile's object layer is 7 rows x 9 cols, 5 tracks.
cost = CostModel(7, 9, max_objects=5)

recolor_1cell = cost.recolor_bits(1)
vanish = cost.vanish_bits()
move_1step = cost.move_bits(1, 0)

print("b_evtype=%d b_objid=%d b_color=%d b_pos=%d"
      % (cost.b_evtype, cost.b_objid, cost.b_color, cost.b_pos))
print()
print("A  recolor(1 cell) + vanish = %2d + %2d = %2d bits   <- the matcher's choice"
      % (recolor_1cell, vanish, recolor_1cell + vanish))
print("B  move(1 step)    + vanish = %2d + %2d = %2d bits   <- what actually happened"
      % (move_1step, vanish, move_1step + vanish))
print()
print("delta per swap: %+d bits" % ((move_1step + vanish) - (recolor_1cell + vanish)))
print()
print("A one-cell recolour costs b_evtype+b_objid+1*b_color = %d." % recolor_1cell)
print("A one-cell move costs b_evtype+b_objid+offset(1)+offset(0) = %d." % move_1step)
print("So on any world where the mover steps ONTO a stationary object of a")
print("different colour, 'the stationary one changed colour and the mover died'")
print("is strictly cheaper than 'the mover moved'.  The assignment is per")
print("transition and independent, so this is the global optimum of the")
print("published objective, not a search failure.")
print()
for d in (1, 2, 3, 4, 8):
    print("   move of %d cells costs %d bits (recolour stays %d)"
          % (d, cost.move_bits(d, 0), recolor_1cell))
