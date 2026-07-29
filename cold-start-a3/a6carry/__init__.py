"""A6 — the transfer protocol, in a form something online can call.

A3 showed that a domain travels between two levels of one hand-built world, by
hand, offline.  A6 turns that result into two artefacts an arm can use:

* **`pack`** — the carry package.  The two books, the theorem-grade entries
  lifted out of them, and a dependency fingerprint that is *compared*, not
  merely written.
* **`rebuild`** — the problem rebuilder.  A3's `a3pipeline/problem_frame.py`
  knows A3's colours, A3's two landmarks and A3's object names; this one is
  handed all three by the pack and knows nothing.

`protocol.carry` joins them and takes an `Executor` — so the same code path runs
against A3's world, against a `worldgen` world, and (the point) against whatever
`theoria-arm` plugs in.  Nothing in `protocol` imports a world.
"""
