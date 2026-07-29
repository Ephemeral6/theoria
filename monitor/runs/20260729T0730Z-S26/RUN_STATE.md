# S26 — a gate that cannot close is a gate that gets stepped over

## Item 1 — the criterion now decides, and it is worth deciding on

`probe_a1_state` computed `bridge` and `consumed`, formatted both into its
`detail`, and returned `{"status": "partial"}` **unconditionally**. Every
possible tree produced the same verdict. Since `scan.build()` lets a probe beat
the hand-written status, `p1-a1` was nailed to `partial` permanently, and an
all-green Phase 1 was unreachable by construction — with `Theoria.md:305`
making all-green the precondition for spending game money and 0.31 of the
paper's weight (WP6 0.20 + WP7 0.06 + WP8 0.05) behind the door. It was stepped
over; that crossing is on record in the drift archive.

Tests first, as the ticket asked: four worlds, three verdicts, plus one
assertion that the verdict varies with the tree **at all**. That last is the one
that matters — the defect is invisible in any single-case test, and before the
fix all four worlds returned `partial`.

### The part the ticket did not ask for, and which mattered more

Making the evidence decide is only half a fix, because the criterion then has to
be worth deciding on. `consumed` was **the bare word "certificate" appearing in
any `.py`/`.lean` under `theory-compiler`** — which the Lean proofs satisfy in
prose (`/-- The certificate's pattern: at(b1,c11) -/`) and which run artefacts
under `runs/` satisfy from past runs. Turning that into a gate would have
replaced a door that never opens with one that opens on a word in a comment, and
the second is worse: it opens by accident, silently, with 0.31 behind it.

The handshake is now the schema id both sides stamp —
`engine-rig/interop/certificate_export.py:95` writes
`lp_potential/pagoda_certificate@1` and
`theory-compiler/src/theory_compiler/certificate.py:38` pins it to read the file
— or the interop directory path. `runs/` is excluded. Two tests hold the line: a
proof comment mentioning certificates must not open the gate, and neither must a
schema id inside a `runs/` artefact.

**The live verdict is now `green`, and it is true rather than unconditional.**
`theory-compiler/src/theory_compiler/certificate.py` really does consume the
export. The old code could never have said so. A test pins the real tree to
green, so a later tightening that stops matching reality fails loudly.

## Item 2 — the same family, swept

A fan-out over every verdict-producing function found the family is wider than
one probe: 14 flagged sites across 24 registered probes, in three shapes — a
hard-coded status no computed value can change; a status decided by some of the
computed evidence while the rest reaches only `detail`; and a status decided by
a condition that cannot be false in practice (`git()` returning `""` on failure
is a systemic source of the third — an empty result reads as "nothing wrong").

Two of them were structural rather than local, and those are fixed here.

**A partial-coverage probe could pass a whole item.** The combining rule was
"the probe wins unless the hand-written status is `risk`", applied with no trace
that it had fired. `p1-seal-test` is a conjunction — *no credential inside the
arm* **and** *egress bypassing the two proxies must fail* — hand-written
`partial`, with its own note saying the red-team surface is unverified. Its
probe `credential_hygiene` searches the tree for the key's value and **never
attempts an egress bypass**. It returns green. Green won. The board showed a
passing cell for a test nobody has ever run, and `p1_green` counted it.

The rule now: a probe may always **downgrade** — evidence of a problem is worth
acting on even from a check that does not cover everything — but may only
**upgrade** when it covers the whole item, declared per item as
`probe_scope: "partial"`, since only the item's author knows what the probe left
out. `p1-a0` is scoped the same way: it counts ten artefacts on disk and never
runs the pipeline, never checks `certify` passed, never checks the plan was SAT.
File presence can show something is missing; it cannot show A0 worked.

Every disagreement between hand and probe is now written to
`state.json.verdict_overrides` and printed. Previously an override left no trace
at all, so the two live swaps — `p1-a1` forced down, `p1-seal-test` forced up —
cancelled to the same total of 9 with nothing recording that either happened.

*Worth knowing before reading this probe's output:* `credential_hygiene`'s
verdict depends on which checkout it runs in. `.env` is gitignored, so in a
worktree the probe honestly reports `partial` ("cannot verify") and in the main
checkout it reports green. The merge robot runs gates inside temporary
worktrees. This was not changed here, but it means the probe answers a different
question depending on where it is asked.

## Item 3 — labelled honestly rather than probed

The ticket asks for all sixteen Phase 1 items attached to a probe. What the
survey found first is that **the sixteen are not Theoria.md's list**.
`Theoria.md:305` states nine clauses; `monitor/spec.py` expands them to sixteen
rows by folding in five items from the *construction* paragraph and splitting
A0/A1/A2 into three. That expansion is defensible, but **nothing in the repo
records the derivation**, and the headline denominator is therefore the length
of a Python list.

The numerator is worse: **eleven of the sixteen rows have no probe at all**, and
the nine greens are enumerated nowhere. Six of the eleven are asserted complete
in prose, and three of those are contradicted by other tables on the same
dashboard — `p1-engines` is green while `PARTNER_SYNC` states this machine has
no Fast Downward and only the BFS stub rung runs; `p1-proxy-model` is green
beside a documented 65-of-131 401 rate on `model_call`; `p1-runner` is green
with "待迁移" inside its own note.

Writing eleven probes is not one item's work, and several of them cannot be
honest offline (`p1-replay-audit` and `p1-same-shell` need a live run). So item 3
is delivered as **labelling, not silence**: every unprobed row now carries
`〔无探针：本项无任何机器检查，状态为人工断言〕`, and `p1_unprobed` is published
next to `p1_green` so "9/16" stops reading as sixteen checked things. A test
requires the two counts to partition the total, so a row cannot quietly become
unprobed without the number moving.

**This is a deliberate narrowing of the ticket and it should be read as one.**
Attaching real probes to the eleven — starting with `p1-access`, whose source
`arc-recon/ACCESS_CHECK.md` already has one status word per row and is the
cleanest candidate — is follow-up work, reported to the monitor.

## Item 4 — the negative sample

Both halves, per the ticket: a tree with both sides connected must report green,
and a tree with only one half must not. Both exist, plus the two criterion
tests, plus the varies-with-the-tree assertion. The green companions are not
decoration — a probe hardwired to `risk` satisfies every red assertion while
being exactly as useless, and the same trap applies to the reconcile rule, where
`return hand` would satisfy the half-coverage test and disable the probe layer
entirely. Both have companions that fail under that mutation.

## Verification

* `python -m pytest monitor/tests -q` → **all pass** (2 xfail, pre-existing).
* `bash monitor/verify.sh` → **GREEN**.
* `p1_green` 9/16, `p1_unprobed` **11**; `p1-seal-test` returns to `partial`,
  which is what its own note said all along.

## Not done, and reported rather than quietly dropped

1. The other 12 flagged sites from the sweep — the largest single win is the
   `git()` helper returning `""` on failure (`scan.py:84-85`), which makes
   `probe_append_only` and `probe_conflicts` read "nothing wrong" when git did
   not run. One fix repairs both.
2. Eleven Phase 1 rows still need real probes.
3. Whether the canonical checklist is Theoria.md's nine clauses or `spec.py`'s
   sixteen rows is an owner's ruling, not a probe's. The repo does not say, and
   the "16" has no written derivation.
