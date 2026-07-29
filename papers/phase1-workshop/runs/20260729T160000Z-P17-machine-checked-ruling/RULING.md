# P17 · Ruling on §5.2 item 3 — "The isomorphism is machine-checked, clause by clause"

RES-2, paper lane, 2026-07-29. Item: `monitor/board/claimed/P17-P17-machine-checked-ruling.RES-2.md`.

*Status: FINAL. Two fact-check rounds and a three-lens adversarial round are in.
The verdict below survived; one of the repairs made under it did not, and §6.1 is
rewritten rather than deleted — see §7.*

## 0 · What is being ruled on

`papers/phase1-workshop/sections/05_a2.md` §5.2, third numbered item:

> **The isomorphism is machine-checked, clause by clause:**

followed by a six-row table mapping clauses of `Theoria.md` §1.3's DC22 sentence
to a check and a result.

Two independent review rounds reached it and both declined to rule:

* **P12, hostile round** (`runs/20260728T173000Z-P12-paper-multi-review/review-d-hostile.md:152`,
  finding 1.7, verdict **LANDS**): *"The other side of your isomorphism is a
  paragraph you wrote in your own design document; a machine checked your world
  against your prose, which establishes that you built what you described."*
  Its glossary entry (ibid.:421) translates the sentence as *"a script compared
  an artefact to a string."*
* **P15** (`runs/20260729T111500Z-P15-capability-column/FINDINGS.md:41`): one row
  is a Lean proof, the rest are artefact comparisons; *"It is the strongest verb
  in the paper attached to a non-proof object. Outside this item and defensible
  as written; flagged so a later pass rules on it deliberately rather than
  inheriting it."*

This is that pass.

## 1 · The two objections are not the same objection

Separating them is most of the work, because a fix aimed at one leaves the other
standing.

**Objection A — strength.** "Machine-checked" is a term of art. This paper
spends §5.3 and §5.6 earning it in the strict sense: Lean 4.9.0, `decide` only,
no Mathlib, no `native_decide`, `#print axioms` returning `[]` and printed as
evidence. A reader who has just been taught that this project means *that* by
machine-checking will carry the standard forward two subsections. Under it, one
row of six qualifies. Loose use of the term is ordinarily a venial sin; in a
paper that also does the strict thing, it is a self-inflicted one, because the
paper itself has trained the reader to hear it strictly.

**Objection B — the relatum.** An isomorphism has two sides. This one's far side
is not DC22 — the pile cut forbids touching DC22, which is the whole reason the
substitution exists (§5.1, INC-004). The far side is a compressed Chinese
sentence in `Theoria.md` §1.3, written by this project. Checking a self-built
world against a self-written description establishes *fidelity of construction*:
we built what we said we would build. It is worth stating and worth checking. It
is not evidence about DC22, and the word "isomorphism" — a word that in
mathematics means structure-preserving correspondence between two given objects —
invites the reader to supply DC22 as the far side, which no row supplies.

Objection B survives every rewording of the adjective. That is what decides
between the options below.

## 2 · The owner's ruling already scoped this, and the sentence outran it

D-A2-001, quoted in §5.1 of the same section:

> A2 is fulfilled by a self-built world isomorphic to DC22's failure structure …
> **The isomorphism argument may cite only the structural description already
> printed in Theoria §1.3** — no upstream DC22 artifact is ever read.

So the authorising ruling itself says the far side is *the description*. §5.2's
sentence asserts the isomorphism flatly and attributes the check to a machine;
the ruling that permits the isomorphism at all had already restricted it to a
correspondence with prose. The paper claims more than its own warrant. This is
not a case of a claim that might or might not be defensible — the document that
authorises it states its scope, and the sentence is outside it.

## 3 · The three options, each argued

### Option 1 — keep it as written

**For.** Every row names the artefact it was decided by, so the literal content —
*checked by a machine rather than asserted by a human* — is true, row by row, and
that is not a small property; most isomorphism arguments in papers of this kind
are a paragraph of hand-waving. The claim has already survived two rounds of
review without being ruled false. Nothing in the table is fabricated.

**Against.** True-if-parsed-carefully is the exact failure mode this paper's
§5.6 sets up a rule against: *any check it invites must survive being run*.
Objection A means a careful reader who runs the invited check finds one Lean
proof and five scripts; objection B means the invited check is against prose.
Two independent reviewers stopped at this sentence. A sentence that reliably
stops reviewers is not one to ship because it can be defended when challenged;
the reviewer who does not challenge it is the one being misled.

**Verdict on option 1: rejected.**

### Option 2 — qualify it

E.g. *"The isomorphism is mechanically checked, clause by clause — one clause by
Lean proof, the rest by artefact comparison."*

**For.** Cheap, preserves all content, defuses objection A cleanly, keeps the
table's rhetorical position as the third of three strengthening arguments.

**Against, and this is the decisive one.** It fixes the adjective and keeps the
noun. After the qualification, the sentence still asserts an *isomorphism*
established by *checking*, and objection B is untouched: the far side is still
this project's own paragraph, and a reader still supplies DC22 for it. Worse,
qualification is the move this repository has learnt to distrust — a softened
overclaim survives review, and survival is precisely the problem: it will be
inherited by the next draft with its qualification quietly load-bearing and
nobody's attention on it again. The two prior rounds already demonstrate the
mechanism: both saw it, both softened their own response to it ("defensible as
written"), and it shipped twice.

**Verdict on option 2: rejected.** Not because it is wrong, but because it is
the option that lets the sentence live.

### Option 3 — delete it

**For.** Removes both objections at a stroke. The strongest verb in the paper
stops being attached to a non-proof.

**Against, if applied to the whole item.** The table is the only place in the
paper where the substitution of §5.1 — the paper's single largest exposure — is
itemised and checked clause by clause. Delete it and the honest reader's
question, *"you swapped the world; show me the swap was faithful"*, has no
answer in the paper at all. It also deletes row 6, the one row that comes out
against the exhibit, and deleting the row that goes against you is the worst
possible deletion. §5.2's remaining two items (near-exhaustive-within-scope
history; history-as-prefix-of-sweep) would stand, but the section's third
strengthening argument would be gone with nothing in its place.

**Verdict on option 3: adopted for the claim, rejected for the evidence.**

## 4 · Ruling

**Delete the claim. Keep the ledger. Label every row.**

This is option 3 applied to the sentence and option 1 applied to the table. It
is deliberately *not* option 2: the word "machine-checked" does not survive
anywhere in this item, and neither does the flat assertion of an isomorphism.
Four changes:

1. **The claim sentence is deleted.** "The isomorphism is machine-checked,
   clause by clause" is removed, not softened. No proof-strength verb replaces
   it.
2. **The item is renamed for what the table is**: a clause-by-clause
   correspondence between the self-built world and `Theoria.md` §1.3's own
   *description*, with the far side named in the sentence itself so the reader
   cannot supply DC22 for it, and with the conclusion stated at the strength it
   supports — *the world was built to the description, and the correspondence
   was computed rather than asserted*.
3. **A `kind` column is added to the table**, valued `Lean` / `artefact` /
   `episode`, so the reader sees the 1-of-6 without inferring it. Fact-check
   round 1 settles the counts: **1 Lean** (row 5, and only its Lean half),
   **5 artefact-or-episode**, **0 refuted**
   (`FACTCHECK_rows.md`).
4. **Row 6's result cell is repaired** (see §5 below), and four row-level
   mismatches the fact-check turned up are repaired with it (§6). Adding a
   `kind` column while leaving those in place would *increase* the overclaim,
   not reduce it — a row labelled `Lean` whose other half is a BFS stub is a
   stronger misstatement than the same row unlabelled.

The word "isomorphism" is retained *only* where it names D-A2-001's construction
and is attributed to it, since that is the owner's ruling's own term; it is no
longer asserted as something a machine established.

## 5 · The adjacent defect this ruling found — row 6's `refuted`

Recorded here because it is not what the item asked about and is worse than what
the item asked about.

Row 6 reads:

| `Theoria.md` §1.3 | A2's check | result |
|---|---|---|
| "而这一关人类可解" | an 18-action episode ends with `win: true` | refuted |

The clause says *this level is human-solvable*. The check is an 18-action
episode that wins. So the clause is **confirmed** — as strongly as any row in
the table. What is *refuted* is the manual's `unsolvable` theorem, which is the
whole point of the exhibit. The cell names the object of the refutation nowhere,
and it sits in a column called **result**, under five cells that all read as
pass-indicators (`1/1`, `184/184, 0 anomalies`, `green`). A reader scanning the
column sees five passes and one failure.

That the misreading actually happens is not a hypothesis. **The board item that
commissioned this ruling makes it**, in its own statement of the facts:

> 其余几行是**制品比对**…还有一行是被一次 episode **反驳**的
> ("…and one row was refuted by an episode")

The row was not refuted by the episode; the theorem was, and the row passed.
The item's author is the paper's most careful available reader, reading with the
table in front of them and this exact sentence under examination, and they read
the column the wrong way. My own first reading of the item made the same
mistake. That is the strongest evidence a table cell can generate against
itself.

`cold-start-a2/artifacts/refutation.json` says which object it means, in a field
the table does not quote:

> `"verdict": "REFUTED — the episode ends on the goal cell with win=true, so the
> machine-checked, axiom-free theorem `unsolvable` is false of the world."`

The fix is to say what was refuted, in the cell. §5.5's beat table already does
this correctly for the same event (`18 actions, win on frame 18`, under the
claim *"the theorem is false"*); the two tables should not disagree about an
event they both report.

**So the table contains no refuted clause at all.** All six clauses of §1.3 are
confirmed — which, once said plainly, is a *stronger* result than the table
currently appears to report, and it is being lost to a one-word cell.

## 6 · Four row-level mismatches, repaired with the labels

Turned up by fact-check round 1 (`FACTCHECK_rows.md`) while classifying the
rows. None was in the item's scope; all four are in the ruling's, because a
`kind` column is a promise that each row means what it says.

1. **Row 5's plan half is real evidence, and an earlier version of this ruling
   said the opposite.** *Rewritten after the adversarial round; the original text
   is quoted and answered in §7, because a ruling that got a fact wrong should
   show the fact it got wrong.* The cell reads *"plan UNSAT + Lean `unsolvable`,
   axioms `[]`"* against the clause 完备**搜索**. Two things are true of the plan
   leg and neither demotes it. It runs the bundled BFS stub
   (`cold-start-a2/a2pipeline/plan.py:70`, `prefer="stub"`), and
   `cold-start-a2/A2_REPORT.md:277-279` discloses that in the same breath as its
   consequence: *"Optimal for unit costs, so `SAT`/`UNSAT` and plan length are
   sound here."* And §5.8's **D-A2-006** — the PDDL backend that cannot ground a
   teleport — was **worked around inside A2 before any A2 plan was run**
   (`cold-start-a2/a2pipeline/compile_a2.py:121,171`, `pddl_addressable`, which is
   D-A2-006's own **Call**). With the workaround the planner discriminates
   exactly on the hole: `plan_generated.json` and `plan_repaired.json` are both
   **SAT in 18** on manuals containing the teleport rule, `plan_holed.json` is
   **UNSAT**. The cell now says the proof carries the row and the plan
   corroborates it.

2. **Row 3 cites two fields that do not exist.** `184/184` is not a ratio
   `certify_cheap` computes (it records `frames: 184`, `transitions: 183`,
   `pixels_checked: 14904`, `pixels_unexplained: 0`), and there is no
   `anomalies` key under `certify_cheap` — the only `anomalies` integer in that
   file is `44`, under `certify_cheap_vs_full_sweep`. Both of the row's
   statements are *true*; neither is at the cited path, so the invited check
   fails on being run, which §5.6's own rule forbids.
3. **Rows 2 and 4 are labelled `(compressed)` and are verbatim.**
   缺的那条传送规则从未触发 and 模型重放 175/175 全对 are both exact substrings of
   `Theoria.md:36`. The label understates the fidelity of the very rows it
   appears on, and it is the source report's tag left behind after the paper
   restored the full wording.
4. **Row 1's "the only proposal" is unscoped.** It is the only jump proposal
   **in the sweep stream**; the history stream proposes none
   (`engines_diff.json:103`, `rules_with_a_jump_effect: []`) — which is row 4's
   whole content. Unscoped, rows 1 and 4 read as contradicting each other.

## 7 · What the adversarial round overturned, and how

Three adversaries ran against the *applied text* rather than the draft: one
trying to overturn the verdict, one re-running every citation in the rewritten
item, one sweeping the rest of the paper for damage. All three independently
landed on the same blocker, and they were right.

**The overturned claim.** §6.1 of this ruling, and the paragraph it put into
§5.2, said:

> §5.8's D-A2-006 records that the PDDL backend cannot ground a teleport at all —
> that planner returns UNSAT on a manual *containing* the rule too, so a verdict
> which comes out UNSAT either way is no evidence about the hole.

Every clause after the dash is false of the pipeline that produced A2's
artefacts. `plan_generated.json` and `plan_repaired.json` are SAT in 18 on
manuals that contain the teleport rule; only the holed manual is UNSAT.

**How it happened, exactly.** Fact-check round 1 sourced the qualification from
§5.8's prose and never opened `compile_a2.py` or `plan_repaired.json`. §5.8
quotes D-A2-006's *Finding* and omits its *Call*, so the paper reports a defect
that was fixed as though it were live. I read the paper's account of an artefact
instead of the artefact, in a ruling whose entire argument is that a claim must
be checked against the thing it is about. **That is the same error as the one
being ruled on, one level up**: §5.2 said "machine-checked" of something a script
had compared, and this ruling said "no evidence" of something it had not run.

**What it cost, and what caught it.** The demotion contradicted three passages of
the same section (§5.2's own gate table, §5.3's block quote of the source report
calling the planner right, §5.5's beat table recording SAT in 18) and the
abstract, which cites the planner's UNSAT as one of three gates. `verify_paper.py`
was **green 6/6 across the whole episode** — before the error, with the error, and
after the repair. Its checks establish that a citation resolves and that a
number-bearing block has one; none of the six opens the artefact and compares the
value. **A green gate was not evidence here, and only an adversary reading the
artefacts was.**

**What survived.** The verdict itself — delete the claim, keep the ledger, label
every row — was attacked on its merits and stood: the option-2 rejection is the
commissioning item's own stated policy, one row of six is Lean, and two
independent prior rounds stopping at the sentence is real signal. Row 6's repair
stood; an adversary tried to defend the original bare "refuted" and could not.
Row 3's repair, the `(compressed)` repair and the board's task 3 all stood.

**What else the round found, and where it went.** Fixed in place: the row-5
citation pointed at the `.lean` file for an axiom list that only exists in
`exhibit_report.json`; row 6 quoted a `win` key that file does not have
(`final_win` / `win_frames` are the real ones); row 5's Chinese clause used
`'` where `Theoria.md` uses `"`, so the one row labelled `Lean` was the one row
whose quotation was not exact; §5.6 said "fourteen of the 52 are the weight
table" — fourteen *entries*, twenty-eight *lines*; "every clause of §1.3's DC22
sentence" was a universal over a paragraph the table does not exhaust, and the
clauses span two sentences; the item still contained the word "machine-checked"
and sent the reader to §5.3 and §5.6 for a term neither uses; the definition it
gave for that term — a kernel proof with an empty axiom list — is the exact
reading §6.6 keeps a vacuous artefact in the tree to forbid; and D-A2-001 was
paraphrased as scoping the *far side* when it scopes the *citations*, a
paraphrase the block quote nine lines above it contradicts. Recorded rather than
repaired, because repairing them honestly needs a measurement or an audit edit:
**C14** (row 4's clause and its check are not the same proposition), **C15**
(row 1's citation trail dead-ends in a stream a later stage overwrote), **B6**
(`CITECHECK.md`'s class-D count now includes two findings the text has fixed).
**C12** was widened: its own quotation of the §4 heading is inexact, §11 carries
the phrasing a third time, and the real defect there is a conjunction §4 itself
retracts.
