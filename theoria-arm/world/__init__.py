"""What the arm has seen, and how it is handed to the engines.

Nothing in this package decides anything about the world. It stores frames,
derives the things that are arithmetic rather than judgement (which cells ever
change, what the background colour is, what a transition was), and reshapes
them into the exact input each engine wants. Every naming, every acceptance,
every "this is a Door" is `inner/theorize.py`'s and is written into the books
by hand.
"""
