# V19-unverified-is-not-true — run state

**Cell** V19 · **lane** verify · **territory** `worldgen/`
**Branch** `agent/v19-unverified-is-not-true` · **base** `9348fa4`
**UTC** 2026-07-28T23:03:07Z

Provenance: `MANIFEST.json`. Per-file regeneration evidence: `FLIPS.md`.
Item 4's judgements: `OPTIMISTIC-DEFAULTS.md`. Adversarial review, verbatim:
`ADVERSARIAL-VERBATIM.md`. Raw console output: `evidence/`.

## The finding, restated

```python
"invariants_all_hold": all(i.get("holds", True) for i in invariants),
```

A prose-only invariant carries no `holds` key, so `.get`'s default reported it
as holding. `build.py` promoted that to `invariant_failures: []` in the
manifest, which is the list the build gate reads. Thirteen of thirty-five
shipped `ground_truth.json` files said `invariants_all_hold: true` while the
`GROUND_TRUTH.md` written from the same dict in the same function call printed
`prose only, unverified` about the same claim.

**The shape worth remembering.** The human-readable half was honest the whole
time. Only the machine-read half lied — and the machine is what adjudicates.
Any reviewer who audited the Markdown, which is the artefact designed to be
audited, would have seen the truth and had no reason to suspect the JSON.

## What was done

### 1. Three states replace the boolean

`core/truth.py` gains `INV_HOLDS` / `INV_VIOLATED` / `INV_UNVERIFIED`,
`classify_invariants()` and `all_invariants_hold()`. `invariants_all_hold` is
true only when the `violated` **and** `unverified` lists are both empty.
`ground_truth.json` publishes the whole partition as `invariant_status`, so a
consumer that genuinely wants "no violations" asks for it by name instead of
getting it by accident out of a boolean that claims to mean more.

The partition is **total, disjoint, and sinks to the bad news**: a row counts as
`holds` only when it says so three ways at once (`status == "holds"`,
`verified is True`, `holds is True`), counts as `violated` when it says so *or*
when it is verified and does not hold, and lands in `unverified` in every other
case — a missing status, an unrecognised one, a row from a pre-V19 writer, a
truthy-but-not-`True` value. `test_invariant_status.py` asserts the three lists
reconstruct the input on thirteen adversarial rows, because a three-way split
whose third class is bypassable is the two-way split wearing a third name.

`to_markdown` now prints the three counts and the resulting boolean at the head
of the section, so the two halves of the artefact state the same verdict in the
same place.

### 2. A separate gate, not a widened one

`build.py`'s `invariant_failures` **keeps its old meaning** — a violated
invariant. The one-character repair was to widen it to "anything that is not
`invariants_all_hold`", and that is a different bug: it makes an unexercised
claim indistinguishable from a broken world, and the work each calls for is not
the same. A new gate key `invariant_unverified` sits beside it with its own
sentence. Both block the build; neither is spoken of as the other.

### 3. The claims were verified rather than waived

The three-state alone turned the catalogue red on thirteen worlds
(`evidence/01`, exit 1) — the honest state, and unshippable. There were two ways
out and only one of them is honest: waive the gate for the three known claims
(the V19 disease relocated, wearing an allowlist), or exercise them.

All three are monotonicity properties — they relate two states, and
`check(world, state)` sees one. The mechanism modules said exactly that in their
own comments and were right; what was missing was a seam. `check_invariants`
grew `edge_check(world, prev, action, next)`, run over the whole reachable
graph, and `latch_monotone`, `collection_is_monotone` and
`tile_state_is_monotone` now use it. Two of the three verify **both** clauses of
their sentence rather than the easy first one, so the verdict is not cheaper
than the prose it summarises.

All thirteen came back `true` on measured transition counts (104 to 1744 each),
not on a default.

### 4. The sweep

Eight sites in `worldgen/` carry a default that could point at good news; four
are defects. `build.py`'s `gate_failures` read `totals.get(key, ())`, so a
manifest missing a gate key cleared that gate silently — the same shape, one
function from the original. `to_markdown`'s `corr.get("agrees", True)` rendered
an unmeasured rule correspondence as agreement. Full table and reasoning in
`OPTIMISTIC-DEFAULTS.md`.

## Negative controls

Both required samples run the **real command line** in a package-copy sandbox
(`tests/invariant_sandbox.py`, built on V16's precedent) and assert the
**process exit code** and **which gate line the build printed** — not a helper's
return value. Raw output: `evidence/05-negative-controls-raw.txt`.

| injection | weakening | exit | gate that fired |
|---|---|---|---|
| — | — | **0** | none (clean control) |
| `prose_only` | — | **1** | `invariant_unverified` |
| `prose_only_explicit_none` | — | **1** | `invariant_unverified` |
| `violated_state` | — | **1** | `invariant_failures` |
| `violated_edge` | — | **1** | `invariant_failures` |
| `holds_state` | — | **0** | none |
| `holds_edge` | — | **0** | none |
| `prose_only` | `pre_v19` | **0** | none — **the defect, reproduced** |
| `prose_only_explicit_none` | `pre_v19` | **0** | none |
| `violated_state` | `pre_v19` | **1** | `invariant_failures` |
| `prose_only` | `boolean_default` | **1** | `invariant_unverified` |
| `prose_only` | `unverified_sinks_to_holds` | **0** | none |
| `prose_only` | `drop_unverified_gate` | **0** | none |

Four things this table is arranged to prove, beyond "the gate is red":

* **(a) is caught as unverified and (b) as violated**, and the tests assert the
  *absence* of the other gate key in each case. A repair that answered
  "unverified is not true" by refusing everything would pass an exit-code-only
  test and fail here.
* **`holds_state` / `holds_edge` are green.** Without them every red above could
  be a build that is red for its own reasons, and the new `edge_check` seam
  could be one that is red on everything — as useless as one green on
  everything.
* **`pre_v19` puts the boolean back and the defect returns**, which is the
  demonstration the work order asks for in as many words.
* **`unverified_sinks_to_holds` reproduces the bug while leaving all three class
  names in the schema.** That is the failure a three-way split invites: a third
  class that exists in the JSON and is unreachable in the code.

### One unflattering result, kept

`boolean_default` reverts **only** `all_invariants_hold` and the build stays
**red**. So the honest conjunction is *not* what stops the defect at the gate —
the separate `GATES` key is. Anyone who repairs only `truth.py` next time will
believe they have fixed this and will have fixed the reporting alone. Pinned as
`test_the_boolean_alone_is_not_what_catches_it`.

## Measurements

| | before | after |
|---|---|---|
| `pytest worldgen -q` | 432 passed, 13 skipped | **512 passed, 13 skipped** |
| `python -m worldgen.build` | exit 0 | exit **0** |
| `python -m worldgen.build --check` | — | exit **0**, byte-identical across interpreters |
| `python -m worldgen.verify` | — | exit **0**, `green` |
| `ground_truth.json` with a `holds`-less invariant | 13 of 35 | **0 of 35** |
| worlds asserting an unexercised claim | 13 | **0** |

`verify` reports its two standing pre-registered QC misses (`RUN_STATE.md`
§gaps). They are unchanged by this cell and do not gate.

## Encountered, recorded, not fixed

`python -m worldgen.verify` rewrote eighteen committed artefacts under
`out/qc/` and left one untracked file — the side effect cell V12 measured and
registered. QC reads only `raw_trace.jsonl` (`qc/run_qc.py:81,170`) and V19
modified no trace, spec, coverage or reversibility file, so none of it is
attributable here. Reverted so this branch carries only its own change;
`evidence/08-qc-side-effect-not-ours.txt` has the diffstat and the attribution
argument. Not ours to fix.

## Deferred, with the reason

`mutate.py`'s `claims_now_false` counts violations only, so a mutation that
turns a verified invariant into an *unverified* one is invisible to it. Closing
that means a `claims_now_unverified` sibling in `MUTATIONS.json`, and
`claims_now_false` is read by name from `exam/grading/rubrics_adaptation.py` and
`exam/papers/adaptation.py` — another track's territory. Recorded at the call
site and in `OPTIMISTIC-DEFAULTS.md` §4 rather than done unilaterally.

## Downstream compatibility

`INDEX.json` and `MUTATIONS.json` changed **additively only** (41 and 31
inserted lines, zero deletions). `claims_now_false` is byte-identical for all
fifteen mutants. No key was removed or re-signed.
