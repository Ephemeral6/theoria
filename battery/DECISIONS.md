# DECISIONS — battery track

Design calls and the reasons for them. A decision without its reason is a
decision that will be re-litigated.

---

### D-B-001 · The guardrail verifies the cut, not just the id

`piles.json` publishes a `sha256` over the canonical JSON of itself with that
field removed. `guard.py` recomputes it on every load and raises on mismatch.

An id-only guard answers "is this game sealed *according to the current file*",
which is the wrong question if the file can change. The pile cut is the
evidence that Phase 4 ran on unseen problems; a battery that recomputed
metrics under a silently edited cut would destroy that evidence and leave no
trace. Every artefact carries the verified digest, so a reader can tell which
cut produced a number.

Matching is loose where looseness is safe and strict where it is not: sealed
ids match by full id, by de-suffixed short id and case-insensitively (the live
API accepts short ids, as `baseline-arms` established, so a full-id-only guard
is a sieve), and an id belonging to *neither* pile is refused as well. An
unregistered game is not a safe game, it is an unaudited one.

### D-B-002 · The no-progress streak is normalised by run length

`Theoria.md` writes "无进展最长连击" as a raw count. The runs available differ
in length by a factor of twenty — one pilot run is a single step, another is
275. A raw streak would rank a long run above a short one for no reason but
its length. Reported as a fraction of the run; the raw count travels in the
support field.

### D-B-003 · Metrics never see raw records

Adapters normalise into `model.py` and metrics read that alone. Three
consequences were worth the indirection:

* the same definition applies to a self-built world and a live ARC ledger with
  no branch inside the metric;
* `state_key` is an opaque digest, so a metric physically cannot learn a game's
  mechanics — relevant given that a battery is cheap to point at anything;
* when `proxy/LEDGER_FORMAT.md` lands, only one adapter changes.

### D-B-004 · The discriminative gradient is a substitute, and a weaker one

`Theoria.md` process 1 specifies CC vs Schema. **There is no Schema arm.**
`baseline-arms/SCHEMA_LOCATE.md` establishes the official harness was never
released and records the decision not to fake it with a re-implementation.

v0 substitutes the model ladder inside `bare_cc` — haiku-4.5 < sonnet-5 <
opus-5, same harness, same prompts, same games. Two properties of the
specified gradient survive: the ordering is fixed independently of this
battery, and it contains no Theoria arm, so the battery cannot be tuned into
flattering the framework it exists to test.

What does **not** survive is the size of the gap. CC vs Schema is a difference
of *kind* — no world model against a fitted one. Haiku against Opus is a
difference of degree within one kind. A metric that fails to separate the
model ladder might still separate CC from Schema, so a `no-effect` verdict here
is much weaker evidence against a metric than the process intends. The verdicts
say `underpowered` where that is the honest word, and this substitution is the
first thing to revisit if a Schema-shaped arm ever exists.

### D-B-005 · `not-applicable` and `insufficient-data` are different, and neither is zero

A run with no model calls has no cost curve; a run with three turns has no
front-load index. Both are reported with a reason string, never as `0.0` or
`None` without explanation. A battery that reports zero for "no data" is a
battery that will eventually be believed — and the first time that happens will
be in a table nobody re-derives.

### D-B-006 · Tier is decided by code

`gaming_audit` demotes a metric mechanically: *accidental and not defended →
reference*. The alternative — deciding tiers while writing the report — puts
the demotion decision downstream of seeing which metrics flattered the
framework. `defended` means the battery implements the defence, not that a
defence is imaginable; "pair by game and it goes away" is not a defence until
something pairs by game. That rule cost E2 and E3 a real code change (the
eight-turn floor) rather than a paragraph.

### D-B-007 · Statistics are hand-rolled

Cliff's delta, the exact sign test, Spearman and the polynomial fits are all
written out in `audit/stats.py` and `metrics/__init__.py` rather than taken
from scipy. Artefacts must be byte-reproducible, and a BLAS-backed routine is
not a promise anyone can keep across platforms. The samples are tiny enough
that the arithmetic is trivial, so determinism costs almost nothing here.

Non-parametric throughout: with four games per arm there is no distributional
assumption anyone could defend, and `Theoria.md` Phase 4 already fixes the
confirmatory tests as the sign test and Wilcoxon.

### D-B-008 · The determinism test runs against a synthetic fixture

`baseline-arms/ledger.jsonl` grew by twenty rows during this session — another
track is actively appending to it. A determinism test pinned to the live file
would fail for reasons that have nothing to do with the battery. The fixture
is generated by a seeded, byte-stable script, contains only development-pile
ids, and deliberately encodes a known capability gradient so the discrimination
machinery is tested against an answer we planted.

The live recompute records input digests instead, so a changed number can
always be traced to a changed input.

### D-B-009 · Path-efficiency metrics refuse coverage walks

Found by running the battery: A0's trace scores 22.9× its optimal plan length,
which reads as catastrophic planning and is nothing of the kind — the trace is
a deliberate walk over the reachable state space, not an attempt to win.
`Run.intent` now declares this and `P4` refuses anything but a solve attempt.

Worth recording as a general shape: **a metric that is silently meaningful on
the wrong kind of input is more dangerous than one that is missing**, because
it produces a number, and numbers get tabulated.

### D-B-010 · `METRICS.md` is generated

The metric reference is rendered from the registry by `python -m battery.docs`,
and a test fails if the committed file drifts. A hand-written reference for
twenty-eight metrics goes stale on the second change; this one cannot.

### D-B-011 · CLAUDE.md's description of the pile hash is ambiguous, and it cost time

`CLAUDE.md` says `arc-recon/data/piles.json` has "sha256 `3feca53e…41bbc19a`".
Hashing the file gives `d3140eff…`. The published digest is over the canonical
JSON of the payload *minus* its own `sha256` field — which is the only scheme
that can work for a self-describing file, but the phrasing reads as a file
hash. The cut itself is intact and has never been modified since its first
commit; only the description is misleading. Not fixed here, because
`arc-recon/` is shared ground and this track does not own it; recorded so the
next reader spends a minute rather than twenty.
