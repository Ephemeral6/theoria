# Adversarial review — lens: the expression language and its evaluation (`recheck/expr.py`)

Brief: produce a forged certificate that `python -m recheck` **accepts** but that
is not a valid certificate for the rule set it is checked against. Secondary
target: any input that produces an unhandled traceback (exit 2 with a clean
message is fine; a traceback is not).

All runs below were executed from
`C:\Users\user\Desktop\theoria\.worktrees\e5-cert-recheck\engine-rig`.
Attack inputs are the `expr-A*.json` files beside this document. Nothing under
`recheck/` was modified.

## Version under test

`recheck/` is untracked and was being edited by another session while this
review ran, so results are pinned to file digests rather than to a commit.
Every verdict recorded below was re-run against this set:

| file | sha256 |
|---|---|
| `recheck/expr.py` | `68640d2005ad4ebcfcbb4ef2e3eb27ce127b5dde7c8d6c7ad746b0eb28a6e164` |
| `recheck/certificate.py` | `b3e80a405d4d7e3da5d162d1aed8008688ec1b812c6774206fd93db72d502953` |
| `recheck/verify.py` | `dd676d912e86f4b9d166fa1741b2f868c02c07c6f1d93f3c9c8cfb60ab1f7f56` |
| `recheck/ruleset.py` | `5badf446f63ac9287bbc1638784362467f9e279b82c9fb81bf20e52412a9d450` |

## Scoreboard

31 attacks run.

* **0** certificates were ACCEPTed with a claim that is false *of the rule set
  as written* by way of a mis-evaluated predicate. The certificate-side
  semantic attacks all held, for a structural reason argued in §5.
* **1 BROKEN — wrong ACCEPT.** `act` escapes the `allow_action=False` barrier
  through a `def`, which lets a rule set's **goal** read the action label. The
  goal then evaluates to a constant `False` and a universal invariant is
  ACCEPTed for a configuration that is solvable in two moves (§1).
* **5 BROKEN — unhandled traceback** (four distinct crash sites), all reachable
  from a certificate file alone (§2).
* **1 defect — false REJECT.** A certificate can use the rule set's `tables` but
  cannot call any of its `defs`, contrary to the code's own comment; the error
  message blames the recursion rule (§3).
* **1 defect — the report is not injective.** Two certificates that print the
  identical `predicate` line certify different theorems, and the text report
  never shows `n_satisfying` or the table contents (§4).

---

## 1. BROKEN (wrong ACCEPT) — `act` leaks past `allow_action=False` through a `def`

`expr.py` refuses `["act"]` outside a rule guard, in as many words:

```
"act is legal only inside a rule guard -- a certificate that mentions the
 action is describing the rules, not a set of states"
```

The check is `scope.allow_action`, decided **when the expression is compiled**.
`RuleSet._parse` compiles the rule set's `defs` in a scope with
`allow_action=True` (they must be usable in guards), and then hands the *already
compiled* closures to `state_scope`, which merely sets `allow_action=False`:

```python
self.scope = compile_macros(macros, base)          # base.allow_action = True
self.state_scope = Scope(..., macros=self.scope.macros, allow_action=False)
```

`goal` and `constraint` are compiled against `state_scope`. So a def body may
contain `["act"]`, and `goal` may call it. At evaluation `compile_predicate`
passes `action=None`, so `["=", ["act"], ["lit", "jump(0,1,2)"]]` is `None ==
"jump(0,1,2)"` → `False`, for every state. The goal becomes unsatisfiable and
the world becomes trivially "unsolvable" — and the second opinion agrees,
because BFS uses the same poisoned `goal`.

`peg4-1101` is the configuration the fixtures record as **solvable in 2 moves**.

Rule set (`expr-A09-act-in-goal.rules.json`, `peg4-1101.rules.json` verbatim
except for these two keys):

```json
"defs": [
  {"name": "peek", "params": [], "body": ["=", ["act"], ["lit", "jump(0,1,2)"]]}
],
"goal": ["call", "peek"]
```

Certificate (`expr-A09-universal.cert.json`) — the "claims everything" forgery
the catalogue already rejects on `goal_break`:

```json
{
  "schema": "engine-rig/recheck/certificate-v1",
  "name": "A09-universal-invariant",
  "kind": "inductive_invariant",
  "claim": "unsolvable",
  "predicate": ["and"]
}
```

```
$ python -m recheck runs/.../attacks/expr-A09-act-in-goal.rules.json \
                    runs/.../attacks/expr-A09-universal.cert.json
ACCEPT       A09-universal-invariant
  rule set   peg4-1101-act-in-goal (16 states, 4 rules)
  claim      unsolvable
  predicate  true
  rules  effects_in_domain    ok
  rules  step_single_valued   ok
  cert   goal_break           ok
  cert   inv_closed           ok
  cert   inv_init             ok
  cert   predicate_wellformed ok
  second opinion: no goal state is reachable -- the claim is true of this rule set
  -> all three conditions hold over 16 states, and an independent search agrees
     the goal is unreachable
EXIT=0
```

The control — the *same* certificate against the unmodified `peg4-1101`:

```
$ python -m recheck --quiet recheck/cases/peg4-1101.rules.json .../expr-A09-universal.cert.json
control(honest goal) EXIT=1        # REJECT, goal_break, 2-action win found
$ python -m recheck --quiet .../expr-A09-act-in-goal.rules.json .../expr-A09-universal.cert.json
forged(act goal)     EXIT=0        # ACCEPT
```

**Verdict: BROKEN.** Same 16 states, same 4 rules, same init, same actions as
the `peg4-1101` fixture; only the goal is restated through a def, and the
rechecker certifies the solvable configuration as unsolvable, at exit 0.

Two things that make this worse than the catalogue's declared
`delete-the-rule` blind spot:

* the language *does* claim to make this impossible, and does block it when the
  `["act"]` is written inline — see A29 below, which is rejected cleanly;
* `render` prints the goal as `peek()` and `Verdict.report()` does not print the
  goal at all, so nothing on stdout hints that the goal reads the action.

Honest caveat: an attacker who can write the rule set could also just write a
contradictory goal directly, which no certificate checker can catch. What is
newly broken here is the specific `allow_action` barrier, which is not
transitive through `defs`. The suggested fix is to compile each def twice (once
with `allow_action=True` for guards/effects, once with `False` for
goal/constraint/certificates) or to record per-macro whether its body touched
`act` and refuse it in a state scope.

**The certificate side is *not* affected** — see A29:

```json
{"schema": "...certificate-v1", "name": "A29", "kind": "inductive_invariant",
 "claim": "unsolvable",
 "defs": [{"name": "peek", "params": [], "body": ["=", ["act"], ["lit", "jump(0,1,2)"]]}],
 "predicate": ["not", ["call", "peek"]]}
```
```
$ python -m recheck recheck/cases/peg4-0111.rules.json .../expr-A29-act-in-cert-def.cert.json
REJECT       A29
  cert   predicate_wellformed FAILED
  -> predicate: act is legal only inside a rule guard -- ...
EXIT=1
```
**held** — certificate defs are compiled with `allow_action=False`, correctly.
(That is only true today because of the separate bug in §3; if §3 is fixed by
letting certificates see the rule set's defs, the §1 leak becomes reachable from
a certificate too. Fix §1 before fixing §3.)

---

## 2. BROKEN — five inputs, four crash sites, all unhandled tracebacks

`__main__.main` only wraps the *load*, and only for
`(RuleSetError, CertificateError, ValueError, OSError)`. Everything else escapes
as a traceback with exit 1 — which a script reading exit codes will read as
`REJECT`, not as "the tool fell over".

### 2a. `render()` is called on an unvalidated predicate — `IndexError`

`recheck()` line 171 computes `certificate.summary()` *before* any of the
predicate's structure has been checked (`parse_certificate` only asserts the key
exists). `render` indexes `args` positionally with no arity guard.

`expr-A01-render-arity.cert.json`:
```json
{"schema": "engine-rig/recheck/certificate-v1", "name": "A01-render-arity",
 "kind": "inductive_invariant", "claim": "unsolvable", "predicate": ["lit"]}
```
```
$ python -m recheck recheck/cases/peg4-0111.rules.json .../expr-A01-render-arity.cert.json
Traceback (most recent call last):
  ...
  File ".../recheck/certificate.py", line 97, in rendering
    return render(self.predicate_src)
  File ".../recheck/expr.py", line 392, in render
    return repr(args[0])
IndexError: list index out of range
EXIT=1
```
**Verdict: BROKEN (crash).** The same hole exists for `["var"]`, `["table"]`,
`["not"]`, `["in", x]`, `["=", x]`.

### 2b. `render()` of a short `if` — `TypeError`

`expr-A02-render-if.cert.json`, predicate `["if", ["=", ["var","pos0"], ["lit",0]]]`:
```
  File ".../recheck/expr.py", line 414, in render
    return "(if %s then %s else %s)" % tuple(render(a) for a in args[:3])
TypeError: not enough arguments for format string
EXIT=1
```
**Verdict: BROKEN (crash).**

### 2c. `names_used()` / `render()` blow the stack — `RecursionError`

`expr-A03-deep-900.cert.json` — predicate is `["not",["not", ... ]]` nested 900
deep around `["=",["var","pos0"],["lit",0]]`:
```
  File ".../recheck/expr.py", line 380, in walk
    walk(child)
  [Previous line repeated 990 more times]
RecursionError: maximum recursion depth exceeded
EXIT=1
```
**Verdict: BROKEN (crash).** At depth 600 with `and` instead of `not`
(`expr-A22-andstack-600.cert.json`) the same crash lands in `render` line 404
instead. Depth 100/300/400/450 all produce clean REJECTs — the language has no
depth bound, so the failure is a stack overflow rather than a refusal.

### 2d. `json.loads` blows the stack inside `load_certificate` — `RecursionError`

`RecursionError` is a `RuntimeError`, so it slips past
`except (RuleSetError, CertificateError, ValueError, OSError)`.

`expr-A03-deep-5k.cert.json` (nesting 5000), `expr-A23-defstack-3000.cert.json`:
```
  File ".../recheck/certificate.py", line 203, in load_certificate
    spec = json.loads(payload.decode("utf-8"))
RecursionError: maximum recursion depth exceeded while decoding a JSON array
from a unicode string
EXIT=1
```
**Verdict: BROKEN (crash).** This one is a two-line fix — add `RecursionError`
(or `Exception`) to the load-time `except`.

### 2e. `compile_macros` blows the stack *inside* the try that exists to catch it

`certificate.compile` catches only `ExprError`, and `recheck` wraps it in
`except CertificateError`. A deeply nested **def body** never passes through
`names_used`/`render` (they walk `predicate_src` only), so it gets further than
2c before dying:

`expr-A23-defstack-1500.cert.json`:
```json
{"schema": "...certificate-v1", "name": "A23-defstack-1500",
 "kind": "inductive_invariant", "claim": "unsolvable",
 "defs": [{"name": "d", "params": [], "body": ["and",["and", ...1500 deep... ]]}],
 "predicate": ["call", "d"]}
```
```
  File ".../recheck/expr.py", line 327, in compile_macros
    compiled[name] = compile_expr(macro.body, body_scope)
  File ".../recheck/expr.py", line 229, in compile_expr
    parts = [compile_expr(arg, scope) for arg in args]
  [Previous line repeated 990 more times]
RecursionError: maximum recursion depth exceeded
EXIT=1
```
**Verdict: BROKEN (crash).** Depth 300/600/900 in a def body compile and
evaluate fine and REJECT cleanly, so this is purely the missing bound.

Note the interaction: `render`/`names_used` are the *shallowest* consumers, so
hiding the nesting in a `def` moves the crash to a deeper, less obviously
guarded site. A depth cap belongs in the parser, not in each consumer.

---

## 3. Defect (false REJECT) — a certificate can use the rule set's tables but not its defs

`ruleset.py` says, of `state_scope`:

```python
# Certificates read states only: no `act`, but the same tables and defs.
```

The tables are inherited. The defs are not. `compile_macros` builds `body_scope`
with `macros=dict(compiled)` — the *locally* compiled ones only, never
`current.macros` — and then returns
`Scope(..., macros=compiled, macro_arity=arity, ...)`, discarding whatever the
enclosing scope had. So `certificate.compile`'s carefully assembled
`base = Scope(..., macros=dict(ruleset.state_scope.macros), ...)` is thrown away
one line later, whether or not the certificate declares any defs of its own.

`a2-world` declares `rendered/1` and `free/1`.

`expr-A08b-call-ruleset-def-direct.cert.json`, predicate `["call","free",["var","cart"]]`:
```
REJECT       A08b-call-ruleset-def-direct
  predicate  free(cart)
  cert   predicate_wellformed FAILED
  -> predicate: call: 'free' is not a declared def (defs may not recurse, and a
     def may only call one declared before it)
EXIT=1
```
`expr-A08-call-ruleset-def.cert.json` (cert def `mine(x) = free(x)`) fails the
same way. The control, `expr-A08c-uses-ruleset-table.cert.json` with predicate
`["=", ["table","board",["var","cart"]], ["lit",0]]`, gets
`predicate_wellformed ok` and a substantive REJECT on `goal_break` — so tables
*are* inherited.

**Verdict: held as a soundness matter, BROKEN as a correctness matter.** No
forgery comes out of it, but an honest `deadlock_carver` certificate that
phrases its region with the rule set's own `clear(x)` — the natural thing to
write for the sokoban levels — is refused, and the message sends the reader
looking for a recursion that is not there. Also note the shadow guard in
`certificate.compile` (`certificate defs %s shadow the rule set's`) is currently
unreachable-by-consequence: nothing could be shadowed, because nothing is
inherited.

---

## 4. Defect (auditability) — the rendered predicate is not injective, and `n_satisfying` is not printed

`table` renders as `name[args]`; the table's *contents* — including its
`default`, which can carry the entire region on its own — appear nowhere in
`Verdict.report()`. Neither does `stats.n_satisfying` (it is in `--json`, not on
stdout).

Three certificates for `sokoban-ringstuck`:

* `sokoban-ringstuck-dead-b1-11.cert.json` (genuine) — predicate `((b1 = '1,1'))`, `n_sat=11`
* `expr-A20-opaque-table-region.cert.json` — `["table","dead",["var","b1"]]`,
  `{"arity":1,"default":false,"entries":[["1,1",true]]}` → renders `dead[b1]`, `n_sat=11`
* `expr-A21b-same-rendering.cert.json` — identical predicate JSON, table
  `{"arity":1,"default":false,"entries":[["1,4",true]]}` → renders `dead[b1]`, `n_sat=11`

```
$ python -m recheck recheck/cases/sokoban-ringstuck.rules.json .../expr-A20-opaque-table-region.cert.json
ACCEPT       A20-opaque-table-region
  predicate  dead[b1]
  ... all conditions ok ...
EXIT=0
$ python -m recheck recheck/cases/sokoban-ringstuck.rules.json .../expr-A21b-same-rendering.cert.json
ACCEPT       A21b-same-rendering-other-theorem
  predicate  dead[b1]
  ... all conditions ok ...
EXIT=0
```

`expr-A21-default-carries-region.cert.json` makes the `default` point directly:
`"default": true` with fifteen `false` entries carves out the same region from
the other side, renders as the same three characters, and is ACCEPTed.

**Verdict: held (every one of these is a genuinely valid dead region), but the
report is uninformative.** Two ACCEPTs whose stdout differs only in the `name:`
line assert different theorems. Printing `stats.n_satisfying` in `report()`, and
rendering a table as `dead[b1] (1 entry, default False)`, would close it.

---

## 5. Why the semantic attacks all fail — and the ones I tried

The lens' suggested attacks (`bool`/`int` confusion, table `default` papering
over a key, `["in", ...]` with mixed types, `["if", ...]` returning a non-bool,
macro scoping) do land in the sense that the language *is* loosely typed. They
do not produce a wrong ACCEPT, and the reason is structural rather than lucky:

`verify.recheck` evaluates the predicate **exactly once per state** into a
single `satisfies` list, and then derives `region`, `closed_bad`, `goal_bad`,
and the BFS `sources` from that one list. There is no second evaluator to
disagree with the first. So whatever weird thing `["in", ["var","pos0"], [true]]`
means, the three conditions are checked against *that* meaning, and an ACCEPT is
a true statement about the set the predicate actually denotes. Type confusion
buys a misleading *report*, not a false theorem.

Nor can the disagreement be manufactured between the conditions and the second
opinion: for `inductive_invariant` the BFS starts from `init` and never consults
the predicate; for `dead_region` it starts from the same `region` list. And
`states()` is a fresh `itertools.product` over the declared domains each time it
is called, in a fixed order, so the index spaces cannot drift. Domains reject
duplicates via `set()`, which also rejects the `[0, false]` / `[1, true]`
collision that would otherwise let two distinct declared values share one index.

Individual attempts:

| # | attack | rule set | result | verdict |
|---|---|---|---|---|
| A04 | table with no `default`, key missing for half the product: `{"t":{"arity":1,"entries":[[0,true]]}}`, predicate `["table","t",["var","pos0"]]` | peg4-0111 | REJECT, `predicate_wellformed`, witness `{pos0=1,...}: table t has no entry for (1,) and no default` | **held** — evaluated state by state inside a `try`, so the raise becomes a named rejection, not a pass and not a traceback |
| A05 | `["if", ["=",["var","pos0"],["lit",0]], ["lit",true], ["lit",7]]` — non-boolean on some states only | peg4-0111 | REJECT, `predicate returned 7, not a boolean` | **held** |
| A06 | `["in", ["var","posN"], [true]]` ×4 against an **integer** domain `[0,1]` | peg4-0111 | ACCEPT, `n_sat=1` | **held** — `1 in {True}` is true, so the region is `{1111}`, which really is closed (no jump fires) and really is not the goal. Valid theorem, misleading rendering `pos0 in {True}` |
| A07 | the genuine `peg4-0111` invariant rewritten entirely with `["lit", true/false]` against the integer domain | peg4-0111 | ACCEPT, `n_sat=8` | **held** — denotes exactly the same 8 states as the shipped certificate; report reads `(pos1 = False)` about a `{0,1}` variable |
| A11 | table keyed by booleans, looked up with ints: `{"t":{"arity":1,"entries":[[false,"a"],[true,"b"]]}}`, predicate `["=",["table","t",["var","pos1"]],["table","t",["var","pos2"]]]` | peg4-0111 | ACCEPT, `n_sat=8` | **held** — `(1,)` hits the `(True,)` entry; the predicate is exactly `pos1 = pos2`, the true invariant |
| A12 | `["in", ["var","pos0"], [1, true]]` | peg4-0111 | REJECT, `in: duplicate member in the literal list` | **held** — the `len(set(members))` guard catches the `1`/`True` collision |
| A10 | table that is nothing but `{"arity":1,"entries":[],"default":true}` | peg4-0111 | REJECT, `goal_break` | **held** — a default-only table is just the universal invariant |
| A10b | same with `"default": false`, `dead_region` | peg4-0111 | REJECT, `region_nonempty` | **held** |
| A13 | macro parameter named `pos0`, i.e. shadowing a declared variable: `f(pos0) = ["=",["param","pos0"],["var","pos0"]]`, and `g(pos0) = f(?pos0)` | peg4-0111 | REJECT on the merits (`inv_init`, `inv_closed`) with `predicate_wellformed ok` | **held** — `["param","x"]` and `["var","x"]` are separate namespaces; the actual is evaluated in the caller's scope and passed by value, no capture |
| A14 | certificate table named `nb`, shadowing the rule set's | a2-world | REJECT, `certificate tables ['nb'] shadow the rule set's` | **held** |
| A25 | self-recursive def `r(x) = r(?x)` | peg4-0111 | REJECT, `'r' is not a declared def` | **held** — declaration order really does make recursion unnameable |
| A26 | `"defs"` as a JSON object instead of a list | peg4-0111 | exit **2**, `could not load: certificate: defs must be a list` | **held**, clean |
| A27 | `["param","x"]` at the top level of a predicate | peg4-0111 | REJECT, `param: 'x' is not a parameter here` | **held** |
| A28 | 2 keys given to an arity-1 table | peg4-0111 | REJECT, `table t has arity 1, given 2 keys` | **held** |
| A30 | key expression whose *type* varies by state: `["table","t",["if",["=",["var","pos0"],["lit",1]],["lit",true],["lit","y"]]]` with `{"entries":[[true,true],["x",true]],"default":false}` — one branch hits an entry, the other silently takes the default | peg4-1101 | REJECT, `region_closed`, and the second opinion reports the 2-action win | **held** — the default did paper over the missing `"y"` key, and the closure check caught the region anyway |
| A15 | `dead_region` = the all-empty peg board, on the **solvable** peg4-1101 | peg4-1101 | ACCEPT, `n_sat=1` | **held** — `0000` fires no rule and is not the goal, so it is a true (if vacuous, being unreachable) conditional-unsolvability theorem. Worth noting that `region_nonempty` does not require the region to be *reachable*, so "true but about states the world never enters" is an accepted shape |
| A18 | universal `dead_region` (`["and"]`) on the solvable peg4-1101 | peg4-1101 | REJECT, `goal_break`, second opinion finds the win | **held** |
| A20/A21/A21b | opaque table regions, §4 | sokoban-ringstuck | ACCEPT ×3 | **held** (valid), report defect |
| A09b | rule set def whose body is bare `["act"]`, used as the goal | peg4-1101 | REJECT, `rules_evaluate FAILED — goal: predicate returned None, not a boolean` | **held** — the leak of §1 only bites when the `act` is buried under a comparison |

`INCONSISTENT` (conditions green + goal reachable, the verdict reserved for "this
file has a bug") was never produced. I do not believe it is reachable through
the expression language, for the single-evaluation argument above.

---

## Note on a live edit (not one of my inputs)

Between 22:36 and roughly 22:50 local, `recheck/ruleset.py` was in a broken
intermediate state — `Obligations` had lost its `assignment = dict(enumerate(state))`
initialiser while `assignment[index] = value` remained, so *every* invocation,
including `python -m recheck recheck/cases/peg4-0111.rules.json
recheck/cases/peg4-0111-ic3.cert.json`, died with:

```
  File ".../recheck/ruleset.py", line 427, in obligations
    assignment[index] = value
NameError: name 'assignment' is not defined
```

That is not attributable to any input of mine; it is recorded only because it
invalidated one batch of runs, all of which were repeated afterwards against
`ruleset.py` = `5badf446…`. Whoever owns that edit should confirm the local
`assignment` map was meant to be deleted outright rather than half-deleted —
`git status` shows `recheck/` is still untracked, so there is no history to
recover the intent from.

## Recommended fixes, in the order I would take them

1. **§1** — do not reuse guard-scope macros in `state_scope`. Either compile each
   def twice, or tag a `Macro` with `reads_action` at compile time and refuse it
   where `allow_action` is false. This is the only wrong-ACCEPT found.
2. **§2d** — add `RecursionError` to the `except` in `__main__.main`. One line.
3. **§2a/2b** — validate the predicate's shape before rendering it, or give
   `render` an arity guard and a fallback to `repr(node)`. `recheck()` currently
   renders an unvalidated blob at line 171.
4. **§2c/2e** — bound expression depth in `compile_expr`/`parse_macros` (a
   constant like 64 is far above anything an engine emits) and make
   `names_used`/`render` iterative. A depth cap is the honest counterpart of the
   `MAX_STATES` cap already in `ruleset.py`.
5. **§3** — make `compile_macros` seed `compiled` from `scope.macros` (which also
   makes the existing shadow guard meaningful). Do this *after* fix 1.
6. **§4** — print `stats.n_satisfying` in `report()`, and render tables with
   their entry count and default.
