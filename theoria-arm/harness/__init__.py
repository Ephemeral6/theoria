"""The Theoria arm's harness: the outer shell, shared with the other two arms.

`Theoria.md` 1.10(c) is explicit that the outer loop is *deliberately* not
changed between arms -- observe -> execute -> record against an append-only
ledger -- because otherwise the difference between arms cannot be attributed.
So nothing in this package makes a decision about the game. It opens sockets,
counts actions, and writes records. Every judgement lives in `inner/`.
"""
