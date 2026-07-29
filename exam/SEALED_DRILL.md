# The sealed drill

The Phase 4 exam procedure — 出题 → 判卷 → 归档 — rehearsed end to end on worlds
that are not sealed games, with the sealed guardrail firing inside the rehearsal.

```bash
python -m exam.tools.sealed_drill        # exit 0 green, 1 red
python -m pytest exam/tests/test_sealed_drill.py -q
```

Zero API calls, zero network, zero contact with the sealed pile. The whole run
executes inside `exam.guard.no_network()`. It does handle sealed-pile ids — all
21, plus their short stems — but only ever as inputs it requires the guard to
refuse, read from `piles.json` at run time and redacted out of everything
written. No sealed id or stem appears in any of the 16 files a run produces, and
a test walks the whole tree to say so.

---

## 1. Why a drill, when `exam/` already rehearses Phase 4

`exam/README.md` is right that the operator library, the spec format, the leak
checks and the marker are all exercised. The gap is narrower and it is about
*which world*.

Every verdict item in the shipped paper is built on `a2`
(`exam/papers/verdict.py:80`) — a world its author designed and understood from
the first line. Phase 4's situation is the opposite one, and Theoria.md:372
states the deadlock it creates:

> 给封存局构造带依据的不可解变体，需要先懂那局的机制——但研究它就破了封存。
> 解法是顺序：主表数据先跑完；考卷子集 ⟨m⟩ 局在**主表跑完之后**才允许研究并构造变体。
> **冻结的是变体算子库与流程**，局内依据在主表之后现场构造。

Freezing a procedure is a claim that the procedure works. This drill is the last
place that claim can still be falsified, because of one asymmetry that never
comes back:

> On a sealed game, **"unsolvable by construction" is the only source of truth
> there is, and it can never be checked.** On a worldgen world it can — the
> world is small enough to enumerate.

So the drill states each variant's truth *by construction* first, in a
machine-checkable certificate, and only then asks an exhaustive oracle. A
disagreement between the two is the entire return on the exercise: a defect in
the procedure, caught on a world that costs nothing, instead of on a sealed game
where it would be invisible.

## 2. What is rehearsed, and with which shipped part

| Step | This drill | The shipped part it drives |
|---|---|---|
| 变体算子库调用 | 10 variants over 2 worlds, all five operators | `proxy.variants.Variant` validates every spec; `VariantRuntime` executes it |
| 构造性依据登记 | a justification per variant, refused under 40 chars by the frozen validator | `proxy/variants.py:69-73`; specs written and re-hashed from disk, two digests |
| 真值隔离 | sheet and key are two files; the class, the claim, the justification, the certificate and the witness are key-side only | `exam.model.Item.sheet_side` / `key_side`; `Paper.sheet()` structurally cannot emit a truth |
| 灵敏度与特异度标定 | five fakes, per-class table | `exam.grading.confusion_matrix.per_class_confusion` — the shipped function, unmodified |
| 封存护栏开火 | all 21 sealed ids **and** all 21 stems refused; all 4 dev ids refused; every worldgen world accepted | `exam.guard.assert_synthetic_world` → `battery.guard` |
| 归档 | `runs/<id>/MANIFEST.json` + `DRILL.json` + sheet + key + specs | the `runs/` provenance convention |

The wrapper (`exam/drill_wrapper.py`) adapts a worldgen `GridWorld` **up** to the
proxy's `{state, frame, score}` body protocol rather than reimplementing the
operator semantics, and composes `before`/`after` exactly as
`proxy/env_proxy.py:374-402` does. A rehearsal that reimplements the wrapper
rehearses the reimplementation and leaves the frozen artefact untested.

## 3. What the run says

```
sealed drill -- 10 variants over 2 worlds
  guard fired             yes
  construction vs oracle  10/10 agree
  certificates checked    5
  oracle      0.9500   sens 1.0    spec 1.0
  null        0.0000   sens None   spec None
  bluffer     0.3000   sens 1.0    spec 0.0
  contrarian  0.2000   sens 0.0    spec 1.0
  claim_only  0.5000   sens 1.0    spec 1.0
GREEN
```

**10/10 constructive claims match the exhaustive oracle.** Every certificate
that was offered checks out mechanically, and every declared witness wins on
replay. The procedure, as frozen, produced correct truth on every variant it was
pointed at. That is the headline and it is a positive result — but see §4 and §5
for what it does and does not license.

**The two rates are genuinely separate numbers.** The bluffer (always
"unsolvable") lands at sensitivity 1.0 / specificity 0.0 and the contrarian
(always "solvable") at 0.0 / 1.0. A marker reporting one blended accuracy cannot
tell those two apart; this one puts them in opposite corners.

Per class (this is the `by_class` split, not the pooled `overall` pair the
console prints — both are in `DRILL.json`):

| class | n | positives | negatives | sensitivity | specificity |
|---|---|---|---|---|---|
| `small_unsolvable` | 6 | 6 | 0 | 1.000 (6/6) | — (empty denominator) |
| `solvable_hard` | 4 | 0 | 4 | — (empty denominator) | 1.000 (4/4) |

The dashes are the point: an empty denominator is reported as `None` with a
stated reason, never as `0.0`. A cell an arm was never tested on is empty, not
failed.

**`claim_only` scores exactly 0.5.** An arm with every claim right and no reason
at all banks precisely half. That is the split working: being right is worth
half, and being right *for a checkable reason* is what the other half buys.

**The pairs are the discriminating part of the paper.** Five of the ten items
exist only as the near-twin of another: `forbid DOWN` / `forbid UP`,
`remap DOWN→UP` / `remap LEFT→RIGHT`, `step_limit 9` / `step_limit 10`,
`cut both crossings` / `cut one crossing`. Each pair is the same operator on the
same board with opposite answers, so "the variant destroyed an action" and "the
variant imposed a budget" are not on their own reasons to answer unsolvable. An
arm reasoning from the operator's shape rather than the board gets exactly one of
each pair right, which is the bluffer's 0.30.

## 4. The finding: `win_tighten` degenerates on a scoreless game

This is what the drill was for.

`proxy.variants.LEGAL_OPERATORS` is the frozen wrapper-legal set, chosen because
those are the edits a proxy can make to *any* hosted game without touching
server-side dynamics. `win_tighten` is the one that tightens the win condition,
and the frozen validator admits exactly one form of it
(`proxy/variants.py:145-149`): `require.kind == "score_at_least"`.

A worldgen world keeps no score. Its recorded trace carries `{t, frame, action,
win}` and nothing else, so the body the wrapper sees has `score: None`. And
`proxy/variants.py:243-252` reads:

```python
for op in self._ops("win_tighten"):
    if body.get("state") == "WIN":
        needed = op["require"]["value"]
        have = body.get("score")
        if have is None or have < needed:
            body["state"] = "NOT_FINISHED"
```

`have is None` is treated identically to `have < needed`. So on a game that
reports no score, `win_tighten` does not tighten the win condition — **it
abolishes it**, at every requirement value, unconditionally. The variant is
unsolvable, but not because anything about the board is hard.

Three consequences, in decreasing order of how much they matter:

1. **The frozen library has one operator that is not game-agnostic.** Four of the
   five survived contact with a world they were not designed against; the fifth
   silently changed meaning. Whether a sealed ARC game reports a score is
   knowable without breaking the seal (it is a protocol question, not a mechanics
   question) and **should be checked before `win_tighten` is used on one**.
2. **The certificate grammar has no form for it.** `invariant`, `cut_set` and
   `counting` are all arguments about the board and the command alphabet; none of
   them can say "the win condition is unsatisfiable because the game reports no
   score". So ground truth itself cannot earn the reason half on this item, which
   is why the oracle's ceiling is 0.95 and not 1.0. The drill computes that
   ceiling rather than assuming 1.0, and names the capped item — otherwise a real
   property of the frozen library would have surfaced as a mysterious calibration
   failure.
3. **It is not a bug in `proxy/variants.py`.** Collapsing `None` into "below the
   requirement" is the conservative reading, and the alternative — treating a
   missing score as satisfying the requirement — would let a tightened variant be
   won by a game that never reports a score at all. The defect is that the
   collapse is silent. A `win_tighten` against a scoreless game should say so.

Recommendation, for whoever owns `proxy/`: make `win_tighten` distinguish
"absent" from "below", and refuse or warn on the first `WIN` it rewrites for
absence rather than for shortfall. Filed here rather than fixed: `proxy/` is not
this item's territory.

## 4b. The second finding: `observation_loss` cuts where the arm *rests*, not where it *goes*

`proxy/variants.py:_cells_hit` inspects `frames[-1]` — the last frame of the
response — and says why:

> The last frame is the observation the arm acts on; intermediate cascade frames
> are transient and declaring a loss on them would make the variant depend on
> animation timing.

That is a good reason, and it has a consequence nobody had written down: **a cell
the arm only passes through during a cascade is never observed, so a loss
declared on it never fires.** On any hosted game where an action triggers a
settling cascade, `observation_loss` is a loss-on-arrival, not a loss-on-contact.

It bit here. The `cut_set` certificate argues "every route crosses one of these
cells, and these cells are lethal, therefore no route survives". The first
version of the checker refused `portal` worlds — where the agent does not walk
cell by cell — but accepted `gravity` worlds. It should not have:
`GridWorld.step` runs `settle` to a fixpoint *before* rendering, so an agent that
gravity carries through a lethal cell comes to rest beyond it having never been
rendered on it. The board-level cut is then not a cut in the state space, and the
certificate would have been accepted while being wrong.

No variant in this drill runs on a gravity world, so no reported verdict was
affected. The checker now refuses `gravity` for `cut_set` as well, for this
reason rather than the portal one, and
`test_a_cut_set_is_refused_on_a_cascading_world` pins it.

**For Phase 4**: before using `observation_loss` to construct an unsolvable
variant of a sealed game, establish whether that game cascades. If it does, the
operator cuts a smaller set of cells than it appears to, and a separation
argument built on it is unsound.

## 4c. The third finding: `exam/verify.py` repairs the staleness it should report

Found by running the territory's own gate before delivering, which is the only
reason it was found at all — the gate exits 0.

The four committed papers under `exam/artifacts/papers/` carry
`rubric_digest e06bdf52…`. The registry's live digest is `63ce1eab…`. They have
not matched since **2026-07-29 04:23 +0800** (`18a39417`, the last commit to
touch a rubric module), and the papers were last written at
**2026-07-28 19:31 +0800** (`d43d8f60`) — nine hours earlier. `exam/grading/` is
byte-identical to this branch's base, so nothing local causes it.

Running `python -m exam.verify` **rewrites all eight artefacts and still exits
0**, because:

* `build_papers` writes sheets and keys unconditionally — a stale file on disk is
  simply overwritten, never compared;
* the determinism stage (`exam/verify.py:49-80`) builds **twice from scratch** and
  compares build A to build B. Both are fresh, so they agree, and the committed
  tree is never an operand.

So the digest that binds a paper to the code that marks it can drift arbitrarily
far from the code, and the gate whose job is to notice reports GREEN while
quietly fixing it on disk. A reviewer who runs `exam.verify` sees green *and* a
dirty working tree, and the dirty tree is the only signal.

The remedy already exists one directory over. `figures/verify.sh` gate 6 diffs
the **committed** tree against a fresh build, and its own comment says exactly
why: *"so a stale committed figure cannot hide behind a green determinism
check."* `exam/` has no equivalent gate. (This is the same defect shape as the
14 stale `figures/` rows in `release/MANIFEST.jsonl` found under V20 the same
day: a committed artefact whose declared digest no longer describes the code.)

**Not fixed here.** Regenerating four shipped papers and four truth files is a
change to the exam's published artefacts, well outside a rehearsal's scope, and
burying it in this diff would hide it. The eight files were restored with
`git checkout --` and this branch leaves them exactly as it found them. Filed as
its own item.

## 5. What this drill does **not** rehearse

Stated plainly, because a rehearsal that quietly omits a third of the exam reads
as covering all of it.

* **Class (ii), large-space unsolvable, is absent.** Theoria.md:259 splits the
  verdict question into small-space unsolvable (exhaustion works), large-space
  unsolvable (only invariant reasoning works — "我们的主场") and solvable-but-hard.
  worldgen's largest world has 2654 reachable states, so nothing in the catalogue
  can stand in for a space exhaustive search cannot reach. Class (ii) is
  rehearsed **in procedure only, never in difficulty**. `DRILL.json` records this
  under `coverage.classes_absent` rather than leaving it to be inferred.
* **Truth-by-construction is validated on ten variants across two worlds**, not
  on the operator library's whole reachable space. "The procedure produced
  correct truth ten times" is not "the procedure cannot produce wrong truth".
* **The drill does not register a rubric.** `exam/grading/registry.py:33` is a
  frozen ordered tuple whose digest is stamped into four shipped papers;
  appending to it to score a rehearsal would move that digest underneath them. So
  the marking ladder is reimplemented and then pinned to the frozen one by
  `test_the_reason_vocabulary_matches_the_frozen_rubric`. The *statistics* half —
  the part V6 actually asks about — is the shipped `per_class_confusion`,
  unmodified.
* **The leak check is local.** `exam.leakage.check_paper` walks
  `exam/papers/__init__.py`'s `BUILDERS` and today refuses all twenty worldgen
  papers for a cause V7 filed and nobody has fixed (`heldout_worldgen` is not in
  `BUILDERS`). Borrowing that gate would make this drill red for somebody else's
  defect, so the probe half is reimplemented here. This is a known gap, not a
  clean bill.
* **The confusion table cannot tell reasoning from arithmetic on this paper.**
  The adversarial pass built an examinee that reads the operator shape and
  `board.start` / `board.goal` and **never touches `board.grid`**. From two
  coordinates it derives axis invariants and Manhattan counting bounds, and
  guesses an L-shaped route as a witness. It gets 10/10 claims and scores
  **0.80** — with sensitivity 1.0 and specificity 1.0, the same headline pair as
  ground truth.

  Its certificate work is arguably legitimate: a Manhattan bound genuinely does
  not need the walls, and refusing to pay for a correct argument because it was
  cheap would be the wrong lesson. What is not acceptable is the second half —
  on this paper a perfect per-class confusion table does not distinguish "modelled
  the world" from "read two integers off the sheet". Two cheaper channels were
  closed (item order, which alone answered 9 of 10; and a `cut_set` naming cells
  the variant never made lethal, which bought full marks); this one is reported
  rather than closed, because closing it means items whose answer turns on the
  walls, and that is a paper-design change rather than a rehearsal.

* **Solvability is always within one episode.** `RESET` is excluded from the
  command alphabet. It does refill a `step_limit` — but it also returns the agent
  to the start, so a budget shorter than the distance to the goal is not
  escapable by resetting. It is excluded because the verdict question asks about
  one episode, not because it would otherwise be a hole.

## 6. What the adversarial pass broke, and what it could not

Nine attack scripts, kept and re-runnable under
`runs/20260729T1030Z-V6-exam-on-sealed-dryrun/adversarial/`. One blocking
finding, five serious, five minor. All are fixed except the one recorded above
as a limitation.

**The blocking one is worth stating against this document's own claims**, because
it is the failure this file predicted and then committed. `drill_certificates.py`
argues: *"Two implementations of one grammar would drift, and the copy that drifts
is the one that accepts something it should not, so the key sets are imported from
that module rather than restated here."* The **key sets** were imported. The
**checks** were rewritten — and the rewrite dropped
`rubrics_verdict.py:521-525`, which requires every cut cell to be a hazard the
variant actually declares. So a `cut_set` naming any two separating cells was
accepted as a proof about a variant that had no `observation_loss` at all, and on
three of four probe cases it certified as unsolvable a world the drill's own
oracle wins in ten commands. It also bought full marks on the one item this
document says is unpayable to anyone, making the 0.95 ceiling not a ceiling.

The test meant to prevent exactly this — `test_the_reason_vocabulary_matches_the
_frozen_rubric` — compares five string literals and no semantics, so
`sealed_drill.py`'s claim that the two are "pinned together so they cannot drift
silently" was false. Both are fixed; the drift is now refused, with the frozen
rubric cited at the check site.

Fixed as a result: the cut-cell hazard check (blocking); the reason ceiling,
which follows from it; item order, which alone answered 9 of 10 items; the guard
sweep, which probed 1 of 21 sealed ids and passed a guard that let the other
twenty and all four dev games through; hostile submissions, which raised
`AttributeError` / `KeyError` out of the marker instead of scoring — one
malformed answer aborted everybody's marks, and there was no witness cap where
the frozen rubric has `MAX_WITNESS = 5000`; the side conditions keying on
`spec.families`, a self-declaration, rather than the mechanisms `GridWorld` binds;
a doctored cut, which killed the run with a traceback before any verdict was
written; two wrong file:line citations in modules whose whole point is
provenance; and the sheet's provenance block, which published all four dev-pile
ids.

**What it tried hard and could not break**, recorded because a claim that
survives real effort is worth more than one nobody attacked: the oracle is
exhaustive and the counter folding is exact — an independent decider sharing no
code with `solve()`, replaying every sequence from t=0 with the full runtime
state as its visited key, found **0 disagreements over 33 cases × 4 counter
caps**, including multiple simultaneous `step_limit`s, `limit: 0`, losses on the
start and goal cells, and `win_tighten` at `value: 0`; `OracleTruncated` fires
strictly before a wrong answer can be returned, on both sides; RESET is genuinely
not a hole; no sealed id or stem reaches any of the 16 files the run writes; every
reported number recomputes exactly from `DRILL.json` and `truth.json`; and
`apply_command` matches `env_proxy.py:373-406` line by line.

## 7. Three defects the drill found in itself

Recorded because the next person will make the same ones.

1. **The guard's own evidence leaked a sealed id.** `SealedPileError`'s message
   quotes the id it refused, so recording the refusal verbatim wrote a sealed
   game's name into a tracked artefact — the exact leak the guard exists to
   prevent, arriving through the door marked "evidence". Caught by
   `test_no_sealed_id_is_written_into_the_run`; the id is now redacted from the
   recorded detail. **Anything that records a refusal must redact what it
   refused.**
2. **The spec path made the truth file depend on where the run was written.**
   `spec_file` was recorded relative to the repo, so a run written outside the
   repo (which the determinism check does) embedded `..\..\..\Temp\...` in a
   byte-reproducible artefact. Caught by `test_the_run_is_byte_reproducible`; the
   path is now relative to the run. `exam/runs/p15-rehearsal-01/MANIFEST.json`
   still carries the same defect in its `report_path` entries.
3. **The composed search did not terminate.** `VariantRuntime.commands`
   increments on every forwarded command whether or not a `step_limit` was
   declared, so carrying it raw into the node key made every revisit of a world
   state a fresh node — an unbounded graph over a world with three reachable
   cells. The counter is now folded, exactly rather than approximately.

## 8. The Phase 4 checklist this leaves behind

When a sealed game is finally opened and its ⟨m⟩ exam variants are constructed,
the procedure below is the one that has been exercised:

1. Load the cut and let it verify its own digest (`guard.load_piles()`); refuse to
   proceed on `CutIntegrityError`.
2. Assert the target id is one you are allowed to study *at this point in the
   ordering* — the main table must already have run.
3. Check whether the game reports a score **before** reaching for `win_tighten`
   (§4).
4. Write the justification first, from the construction, and let
   `proxy.variants.Variant` refuse it if it is too thin to be one.
5. Emit the spec, re-load it from disk, and hash both the object and the file
   bytes. What is hashed must be what is on disk.
6. Split sheet from key. The class, the claim, the justification, the certificate
   and the witness are key-side. `points` is equal on every item, because it
   rides on the sheet.
7. Calibrate before marking anything real, and check the two single-answer fakes
   land in opposite corners. If they do not, the marker is blending the rates.
8. Report sensitivity and specificity per class, with coverage beside each. An
   empty denominator is `None` and says why.
9. Archive: manifest with `prompt_id`, `branch`, `base_commit`, `utc`, and a
   digest of every artefact.
10. Record what was *not* covered, in the artefact, not in a memory.

Provenance for this run: `exam/runs/20260729T1030Z-V6-exam-on-sealed-dryrun/`.
