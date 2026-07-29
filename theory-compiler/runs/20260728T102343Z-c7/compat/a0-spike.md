# C7 compat probe — does v0.3 regress `a0-spike/theory/theory.dsl`?

Run id `20260728T102343Z-c7`, branch `master` in worktree
`.worktrees/c7-dsl-v03-mentions`, base commit `f1346fb`. Nothing is committed on
this branch, so **baseline = `git show HEAD:./src/theory_compiler/...`**,
extracted verbatim into `baseline-spike/theory_compiler/` (22 files) and driven
through `sys.path` by the same probe script as the working tree.

Level: `theory-compiler/tests/fixtures/sokoban2_match_problem.json` (7x7, three
walls, Box (3,3), Player (3,5), target (3,1)).

Artifacts in this directory:

| file | what |
|---|---|
| `probe_compat.py` | per-stage compile, catches each stage separately |
| `dump_forms.py` | writes whichever forms succeed, for byte diffing |
| `baseline.a0.log` / `current.a0.log` | full tracebacks, a0 manual |
| `baseline.migrated.log` / `migrated.log` | full tracebacks, migrated fixture |
| `out-baseline-a0/` / `out-current-a0/` | the emitted forms |

`python -m pytest -q` in `theory-compiler`: **288 passed, 1 skipped** (17.6s).

---

## 1. `a0-spike/theory/theory.dsl` — baseline vs current

| stage | BASELINE (HEAD) | CURRENT (v0.3) |
|---|---|---|
| `parse_theory` | OK | OK |
| `build_ir` | OK, 3 warnings | OK, 3 warnings (different text) |
| `gen_python` | **raises** | **raises — same exception, same message** |
| `gen_pddl` | "OK" (1567 + 8771 chars) | "OK" — **byte-identical** |
| `gen_markdown` | OK (2335 chars) | OK — **byte-identical** |
| `gen_lean` | **raises** (via `_load_predictor`) | **raises — same exception, same message** |

`diff -r out-baseline-a0 out-current-a0` differs only in `warnings.txt` and in
the file paths / line numbers inside the two `.ERROR.txt` tracebacks.
`domain.pddl`, `problem.pddl` and `theory.md` are byte-for-byte equal.

### The exception, both versions, identical

```
theory_compiler.generators.gen_python.UnsupportedClause:
expected a direction from ['down', 'left', 'right', 'up'], got NameRef(name='dir')
```

```
generate_python  ->  _effect(rule, ctx)      (baseline L374 / current L448)
_effect          ->  _direction(a[1], ctx)   (baseline L213 / current L260)
_direction       ->  raise UnsupportedClause (baseline L253 / current L327)
```

`gen_lean` fails with the *same* exception object type and message, because
`gen_lean._load_predictor` (L101) execs `generate_python`'s output.

**This is not the error the claim predicts.** It is not `unknown event slid/2`.
It fires on the *first* rule, `walk`, whose event is `moved(Player, dir)` — a
default-table event — and it fires because `dir` is a free `NameRef`, never
bound by a `forall` and never a member of a declared `domain`. `push2` /
`slid/2` is never reached. The manual is outside the supported subset for a
reason that predates v0.3 entirely and that v0.3 does not touch.

### `conflict` does not raise either

Also not as the claim predicts: `conflict.claimed_objects` never raised "no
claim table". `build_ir` **survives** in both versions and emits a warning.

BASELINE `ir.warnings` (3):
1. `problem 'sokoban2-match' locates ['target'], which theory.dsl never declares as a landmark ... (E-04).`
2. `rule push2: rule 'push2' fires slid/2, which this checker has no claim table for. Add it to `CLAIMED_ARGS` ...`
3. `` `conflict exclusive` is not discharged by guard analysis for 2 rule pair(s): walk/blocked_box_crossing, walk/blocked_box_landing ... (ledger E-07).``

CURRENT `ir.warnings` (3):
1. (identical E-04 landmark warning)
2. `theory.dsl declares no `writes { ... }` for moved/2, stayed/1, so their write sets come from v0.3's default table ...`
3. `` rule push2: event slid/2 has no write set: it is not in v0.3's default table and its `events:` declaration carries no `writes { ... }` clause ... ``

The v0.3 FAIL-CLOSED rule for `slid/2` reaches this manual **as a warning, not
as an error** (`WriteSets.indices` raises `WritesError`, but `build_ir` /
`conflict` route it into `warnings`). The manual still never compiles, but it is
not v0.3 that stops it.

### The one real behavioural change v0.3 makes here

Baseline warning 3 — `conflict exclusive` undischarged for
`walk/blocked_box_crossing` and `walk/blocked_box_landing` — is **gone** under
current. `conflict exclusive` is now reported as fully discharged for this
manual.

Cause: `writes.py` `DEFAULT_WRITE_SETS[("stayed", 1)] = ()`, whereas v0.2's
`conflict.CLAIMED_ARGS` had `stayed` claiming its argument (stated in
`writes.py`'s own docstring, L52-58). A rule that writes nothing cannot be the
second writer of an object, so the two `blocked_box_*` pairs drop out of the
obligation. This narrows what the compiler asserts about the a0 manual. It is
not a regression — no error appears that did not appear before — but it is the
only place the two versions disagree about this manual beyond warning wording.

### Neither version produced a working predictor — and the two "successes" are false

`gen_python` raised in both, so no predictor exists in either, so `exec` was
never reached, so **no v0.2 predictor for this manual was lost**.

The two forms that *do* "succeed" do not produce usable artifacts, in either
version. `out-current-a0/domain.pddl` (= `out-baseline-a0/domain.pddl`):

```
(:action walk
  :parameters (?player - player ?dir - object ?player-pos - cell)
  :precondition (and (at ?player ?player-pos))
  :effect (and (not (at ?player ?player-pos)) (at ?player ?dest) ...))
```

`?dest` is unbound — not a parameter — so the domain is not valid PDDL. Every
`free(...)` and `Box.pos = ahead(...)` guard was silently dropped; `push2`,
`blocked_wall`, `blocked_box_crossing`, `blocked_box_landing` all compile to
`:effect (and (and))`, i.e. no-ops; the Box appears nowhere. This is silent
approximation, and it is equally silent before and after v0.3.

---

## 2. VERDICT

**The claim is VERIFIED. v0.3 does not regress `a0-spike/theory/theory.dsl`.**

The baseline chain did **not** compile this manual to a working predictor.
`gen_python` and `gen_lean` refused it under HEAD and refuse it under v0.3 with
the *same* exception type and the *same* message; `gen_pddl` and `gen_markdown`
emit byte-identical output before and after. There is no form that worked before
and fails now.

**But the claim's stated reasons are both wrong**, and they matter because they
point at the wrong risk:

* The refusal is `UnsupportedClause: expected a direction from [...], got
  NameRef(name='dir')` at rule `walk` — **not** `unknown event slid/2`. The
  manual's free `dir` variable, not `slid`, is what stops it, and v0.3 does not
  change *which* error it gets: it is bit-for-bit the same error.
* `conflict.claimed_objects` never raised "no claim table"; it warned, and
  `build_ir` succeeded, in both versions.

So the accurate statement is stronger than the claim: v0.3 changes **nothing**
about this manual's compilation outcome. It changes three warning strings and
removes one undischarged-`conflict` warning (via `stayed/1 -> ()`).

---

## 3. `tests/fixtures/sokoban2_theory.dsl` (the v0.3 migration), current code

| form | result |
|---|---|
| `parse_theory` | OK |
| `build_ir` | OK, 2 warnings |
| `gen_python` | **OK** (18298 chars) |
| exec the predictor | **OK** — `step`, `simulate`, `is_goal`, `initial_state`, `render`, `fired`, `RULES`, `SEMANTICS` all present |
| `gen_pddl` | **RAISES** |
| `gen_markdown` | OK (3125 chars) |
| `gen_lean` | **OK** (39667 chars) |

The PDDL failure:

```
theory_compiler.generators.gen_python.UnsupportedClause:
free(Box) names its cell through an object, which excludes that object from its
own occupancy test (v0.3, X-5). This STRIPS encoding holds `free` as a property
of a cell and has no way to say `free except for Box`. Refusing rather than
dropping the precondition.
  gen_pddl.py:54 generate_pddl -> :94 _gen_domain -> :176 _rule_to_action
  -> :221 _guard_to_pddl -> :253 _extract_pred_pddl
```

This is a deliberate fail-closed refusal added by v0.3 (`gen_pddl.py` L239-257).
Note the asymmetry it creates: the **unrepaired** a0 manual still gets a silent,
invalid PDDL domain out of this backend, while the **repaired** one is refused —
because the a0 manual's guards are discarded before reaching the new check.

`build_ir` warnings for the migration (2):
1. `` theory.dsl declares no `writes { ... }` for moved/2, so their write sets come from v0.3's default table ... ``
2. `` `conflict exclusive` is not discharged by guard analysis for 4 rule pair(s): walk_up/push2_up, walk_down/push2_down, walk_left/push2_left (and 1 more) ... (ledger E-07).``

The second is worth flagging: the migration's own header comment argues the
`free(Box.pos)` clauses are needed so `blocked_box_on_wall` does not overlap and
"`conflict exclusive` stops being dischargeable". Guard analysis still leaves
four `walk_*/push2_*` pairs undischarged, which the a0 manual's own
`semantics:` comment claims is settled by the syntactic route
(`free(c)` implies `c != Box.pos`, THEORIZE_LOG T-11c). The checker does not
implement that route.

Ground truth: `python tools/probe_mentions.py` passes 7/7, including
`sokoban2 declared all 0 / 47040 (expected 0)` and
`sokoban2 first_argument off_wall 376 / 39960 (expected 376)`.

### Baseline on the migrated fixture (for completeness)

Baseline **parses it without complaint** — its event regex is
`re.match(r'(\w+)\(([^)]*)\)', part)`, a prefix match, so `writes {o, p}` is
**silently discarded**, and `slid(o, p, dir)` is read as a plain 3-ary event.
`build_ir` then emits 5 warnings and `gen_python` raises
`UnsupportedClause: not a cell expression: FuncCall(name='ahead', args=[...])`
(baseline `gen_python.py:111`). v0.3's parser turns an unreadable alternative
into a `ParseError` instead.

---

## 4. Semantic diff: `a0-spike/theory/theory.dsl` -> `sokoban2_theory.dsl`

The two repairs named in the brief are present and are as described:

* **X-1** `slid(o, dir)` -> `slid(o, p, dir) writes {o, p}`; `push2`'s event
  becomes `slid(Box, Player, ?d)`.
* **X-5** `free(Box.pos)` added to `push2`, `blocked_box_crossing`,
  `blocked_box_landing`; new rule `blocked_box_on_wall`.

**Everything else the migration changed, that the brief does not list:**

1. **`domain direction { up, down, left, right }` added to `word_table`.** New
   declaration, no counterpart in the original.
2. **`landmark target` added to `word_table`.** New declaration. It silences the
   E-04 warning that both versions raise against the original. Not mentioned in
   the migration's own header comment either.
3. **Every one of the five original rules gains `forall ?d in direction`, and
   every `dir` becomes `?d`.** This is the largest change in the file. It is
   what makes `gen_python` work at all — it is the direct fix for the *actual*
   baseline failure (`NameRef(name='dir')`), and it is unrelated to X-1 and X-5.
   The migration's header calls it E-02; the brief's "two intended repairs"
   framing does not cover it. Downstream: five rules become twenty grounded
   rules (`walk_up` ... `blocked_box_landing_right`).
4. **`stayed(o)` -> `stayed(o) writes {}`.** Extensionally equal to the v0.3
   default table, but *not* equal to v0.2's `conflict.CLAIMED_ARGS`, which had
   `stayed` claiming its argument. This narrows the `conflict exclusive`
   obligation. (Same change also lands on the unmigrated a0 manual — see §1.)
5. **`blocked_box_on_wall` carries no `[ev: ... cov: ...]` annotation**, while
   all five inherited rules do. The new rule has no recorded evidence in the
   manual.
6. **Stale provenance on changed rules.** `push2 [ev: t3,t9,t27 cov: 267/267]`,
   `blocked_box_crossing [cov: 24/24]` and `blocked_box_landing [cov: 28/28]`
   keep their original coverage tags although their guards gained a conjunct.
   Likewise `theorem unsolvable_mismatch [depends: push2 probe: passed]` keeps
   `probe: passed` although `push2` changed.
7. **The `semantics:` rationale comments were replaced.** Values are unchanged
   (`frame persist`, `conflict exclusive`, `cascade single_frame`) — no semantic
   difference — but the original's recorded refutation counts (38712/39960 for
   `frame`, the 47040-pair scan for `conflict`, 22582/39960 for `cascade`) do
   not survive into the copy. The `events:` comment recording that `stayed` was
   forced by `certify` is also dropped.
8. `goal:` and `laws:` are semantically identical; only law comments were
   translated from Chinese to English.

Item 3 is the one to act on: the migration is presented as two repairs, but it
is three changes, and the third is the only one that has any bearing on whether
the manual compiles.
