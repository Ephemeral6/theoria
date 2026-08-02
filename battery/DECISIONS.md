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

---

## v1

### D-B-012 · The arm contrast is a separate artefact from process 1, on purpose

`Theoria.md` Phase 2 process 1 says validation uses the control arms only —
验证只用对照两臂，与 Theoria 无关，防止电池被设计成给自己脸上贴金. v1 finally
has Theoria-arm material, and the temptation is to fold it into
`discrimination.json` as "more data".

That would destroy the property the sentence exists to protect. A metric that
separates `bare_cc` from a Theoria arm has demonstrated nothing about its own
validity, and a battery that cited such a separation as validation would be
using its results to license its instruments.

So there are two files. `discrimination.json` is process 1 and stays
control-only. `arm_contrast.json` is a result, carries
`confounded_by_world: true` on every entry, and opens with a `status` field
saying in one sentence that nothing in it licenses a metric. `METRICS.md`'s
验证材料 column is fed from the first file and never the second.

### D-B-013 · Campaign labels come from two sources and one of them is derived

`baseline-arms/ledger.jsonl` holds the M4 pilot and the phase-3 variance
envelope with nothing on a row to distinguish them, and v0 pooled them. They
are not interchangeable: every envelope cell stops at exactly ten cumulative
failures because `bare_cc.py` breaks there, so the envelope runs are
right-censored by a harness rule rather than by the arm.

`out/campaign_cells.jsonl` carries an explicit `campaign` field and is used
verbatim. `out/pilot_*.json` carries no such field, so **membership in the file
is the label** — recorded as `m4-pilot`. That is a weaker fact than a field and
is flagged as derived rather than quietly equated with one. Seven runs appear in
neither index and are reported as `unlabelled`, not guessed at.

### D-B-014 · Calls and turns are different axes, and both are kept

`bare_cc` writes one `model_call` row per retry *attempt*. One pilot run bills
three attempts at a single step, with three different token counts and three
different prices — so the rows are not duplicates and dropping them would
understate real spend by a third on that step.

But the economy family's shape metrics are defined per *turn*, and a turn is a
decision. v0 had only the row axis, so a run whose model call failed twice
looked like a run that deliberated three times.

E1 therefore stays on the billing axis, because the money was really spent. E2
and E3 move to `Run.turn_costs()`, which groups calls onto the step they were
deciding. Total cost is identical under both; only its distribution changes.
This is the battery's local answer to `INPUT_FORMAT.md` gap 5 and does not close
it upstream.

### D-B-015 · A2's L6 verification replay is billed, against our own interest

A2's sixth beat (解出) re-executes the 18-action repaired plan against a freshly
initialised world to fill `plan_repaired.json`'s `world_reaches_goal`. Whether
that counts as a cost of the repair loop is genuinely arguable: the actions are
really executed, but one can call it a verification replay of a plan L1 already
paid for.

It decides K13, a metric this project registered a directional prediction about.
Unbilled the ratio is 30/183 = 0.164; billed it is 48/183 = 0.262. Both clear the
registered "< 0.3", and **the unbilled reading is the one that flatters the
prediction**.

Billed, for two reasons. 解出 is a beat of the loop by `Theoria.md`'s own
definition and K13 sums beat costs, so excluding the only beat that touches the
world after 戳探 would make the sum something other than what it claims. And
choosing between two defensible conventions by which one makes your own
pre-registration look better is precisely the failure this battery exists to
catch. The rejected reading stays in `Repair.notes` so the choice is arguable
rather than invisible.

### D-B-016 · a0-spike's concepts carry no compression account, and none is invented

`a0-spike/theory/theory.dsl` annotates both `Player` and `Box` with
`compress: -39`. Three separate reasons not to pass that through:

* **It is one global number written twice.** −39 = 373 − 412 is the whole-script
  delta quoted in that bundle's README; it is not a per-concept account, and a
  mean over it is n=1 duplicated.
* **The sign is inverted** relative to `Concept.compression_bits`, which
  documents "+ = the manual got shorter". Passing −39 straight through would
  report two concepts as *costing* 39 bits each and would manufacture the O-04
  negative-gain finding out of a bookkeeping convention.
* **It is stale.** `a0_report.json`'s `perceive` block says 602 vs 712 bits, a
  delta of −110 over five levels.

Negating fixes only the second; recomputing fixes only the third; neither splits
the number between the two concepts. So `compression_bits` is `None` and K6, K7
and K14 report `insufficient-data` on that arm with a stated reason. A fabricated
per-concept account would have been indistinguishable from a real one in the
artefacts.

### D-B-017 · `parse_dsl` reads bracket continuation lines

Every theorem in the repository writes its annotation on the line after the
clause:

    theorem unsolvable_mismatch "..."
      [depends: push2  probe: passed]

A line-by-line reader therefore reported `proven=False` and
`probe_pending=False` for exactly the clauses carrying a proof or a pending
probe, silently and on all three arms. A clause is now its own line plus any
following bracket-only lines; anything else — a blank line, a `when` body, a
section header — ends it, so an annotation further down cannot be misattributed.

No metric currently reads either flag, so no published number moved. That is
why it survived v0 undetected, and it is the argument for the machine-readable
manifest `INPUT_FORMAT.md` has been asking the theory-compiler track for.

### D-B-018 · The concurrent S1 campaign is read-excluded, and says so in the artefact

`baseline-arms/out/shards/` holds a third campaign that another session was
writing *during* this recompute — untracked, tens of megabytes, mtimes moving
between one run and the next. It is the same game and model as the envelope and
would roughly double the `bare_cc` sample.

Not ingested. Untracked live input cannot be byte-reproduced by a reader, and
folding an unmerged in-flight campaign into a published number is the kind of
thing that is discovered later rather than declared now. `run_battery` carries
an `EXCLUDED_SOURCES` list into `capability_spectrum.json`'s provenance, so
"not ingested" is a recorded decision with a reason attached rather than an
omission someone has to notice.

### D-B-019 · "No Schema arm" was two different facts, and v1 reported the wrong one

`REPORT_V1.md` leads with *the Schema arm does not exist*, and lists the
missing CC vs Schema gradient as gap number one. That was already false when it
was written. `baseline-arms/SCHEMA_PATH_A.md` landed at commit `63ef0bf`
(2026-07-28T02:53Z) and battery v1 at `e82558b` (09:04Z) — six hours later, on
the same day, in the same tree.

The conflation is worth naming precisely, because both halves are real and only
one of them was a gap:

| question | status |
|---|---|
| can we *run* Schema and get our own reproduction score? | **no**, and probably never — the harness was never released |
| do we have Schema-side *trajectories* on the development pile? | **yes**, since 02:53Z that day |

`SCHEMA_PATH_A.md` §6 draws exactly this line and says of the second row:
*Phase 2 指标电池要的 Schema 侧材料 ✅ 本轮解决*. Process 1 needs trajectories,
not a reproduction score — it asks whether a metric separates two arms, and for
that the upstream ledger is sufficient material. v1 read "no Schema arm" off
`SCHEMA_LOCATE.md`, which is about the harness, and never revisited it.

So `discriminate_arms()` is the primary pass from v2 on, and the model ladder
drops to secondary. The ladder is not deleted: it holds the harness fixed,
which the cross-arm pass cannot, so the two passes fail in different directions
and disagreement between them is information.

`⟨复现值⟩` in `Theoria.md:271` stays empty. Nothing here fills it, and this
decision does not license anyone to.

### D-B-020 · Only derived statistics from the upstream payload, never the payload

Upstream declares no licence (`SCHEMA_LOCATE.md` §2.3), which is why
`baseline-arms/.gitignore` excludes the 87.7 MB payload and tracks only
`MANIFEST.json`. `Theoria.md` Phase 4 publishes every tracked file, so anything
the battery commits about this material is effectively republished.

The rule this track adopts: **the battery commits effect sizes, correlations
and per-metric verdicts; it never commits a frame, an action sequence, a
transcript, a prompt, or any per-step record derived from one.** A Cliff's
delta over four games is a statistic about our instrument, not a redistribution
of somebody's dataset; a state-key digest column would be closer to the line
and is not written to any artefact.

`SCHEMA_PATH_A.md` §7.1 flags that citing specific numbers may still need a
licence judgement. That judgement is not this track's to make and is not made
here — it is escalated in `PARTNER_SYNC.md`, and until it comes back the
artefacts stay at the aggregate-statistic level described above.

### D-B-021 · The S1 shard exclusion is lifted, because its premise expired

D-B-018 excluded `baseline-arms/out/shards/` for a stated reason: *untracked,
actively appended during this recompute*. That was true when it was written and
is not true now. The shards carry a terminal `status`, none carries the
in-flight `live_episode` key, no producer process is running, every file's last
line parses, and their `run_id` set is **disjoint** from `ledger.jsonl` — so
ingesting them duplicates nothing.

Ingested: 56 further `bare_cc` runs. They are written by the same
`harness/ledger.py` writers as the merged ledger, so the schema is identical by
construction rather than by luck.

One clause of D-B-018 still bites and is not waved away: these files are
**untracked**, so nothing pins them for a reader except the sha256 list in the
run manifest. That is weaker than a tracked input and is recorded as such.

A second thing this turned up. S1 labels itself with a **differently named
field in a directory `load_campaigns()` did not read** — `scenario` in
`out/campaign/campaign_<stem>.json`, against `campaign` in
`out/campaign_cells.jsonl`. Nothing errored; 48 runs simply came out
`unlabelled`. That is D-B-013's failure mode exactly, one campaign later, which
suggests the real fix is upstream: a `campaign` field on the ledger row itself,
which remains this track's one standing request.

### D-B-022 · The gaming register had to become executable, because prose cannot be wrong

`Theoria.md` process 4 demotes a metric that is gameable, accidental and
undefended. Through v1 those were three hand-written booleans, and `tier_of()`
demoted metrics on their strength. The suite checked that a register entry
*existed* — `test_every_registered_metric_has_a_gaming_entry` — and never that
it was true. So a wrong `defended: True` kept a gameable metric in the main
table, and 117 passing tests could not tell anyone.

`battery/audit/exploits/` is the register made falsifiable: an actual `Run` per
metric that scores at or near the best value while possessing none of the
capability, with `succeeded` read from `evaluate()` rather than asserted. Where
a demonstration exists, its fields decide the tier. **17 of 38 entries were
contradicted and 13 metrics demoted**, four of them contradicting a
`defended: True` that had never been checked.

The prose entry is kept beside the demonstration rather than corrected in
place. A register that gets quietly edited to agree with its own audit has
learned nothing; the disagreement is the finding.

`accidental` stays a judgement — "would a real arm do this without trying" is
not decidable from a `Run` — but it is now required to be argued from a named
file in this repository, and every exploit's docstring names the one it argues
from.

**One inconsistency is left standing.** Three independent audits produced these
demonstrations and they did not agree on whether a `neutral` direction is
itself a defence, so some diagnostics fell to `reference` and some did not. The
artefact marks neutral tiers advisory and explains that *direction*, not tier,
excludes a diagnostic from an ordering. Normalising the disagreement would have
concealed that a hand-set boolean is still doing work here.

### D-B-023 · The blinding source is a pinned sha, because a moving ref is a silent blinding failure

`make_blind.py` built the attackers' trees from a hardcoded absolute path into
`.worktrees/v9-battery-gaming-audit`. The obvious complaint is that the path is
machine-local and the worktree is one cleanup from gone. The real one is that a
worktree has a HEAD and a HEAD moves.

Blinding happened at `9892d23c` — prereg, poverty certificate and blinding, all
in one commit, before any attack. The branch then ran on to `0d586b6f`, and
`520dc5dd` in between added the three defences the attacks had just provoked.
Rebuilding from the path today produces 5 of the 10 files it reads differing
from what the
attackers saw, and puts `unsound(` — recorded in `BLINDING.md` §3 item 8 as a
**zero-hit** term — into the blind 13 times. Nothing about that failure is
visible from outside: the tree builds, the attacks run, a verdict comes out.

So the source is `BLIND_REF`, a full 40-character sha. **Not a branch name**: a
branch name is more readable and would have reproduced exactly the same drift
one indirection later, which is the mistake worth naming. Files are read with
`git cat-file blob`, not `git show`, so smudge and eol filters cannot make the
bytes depend on the machine's `core.autocrlf` either.

Every failure raises `BlindingError` and exits 2 — unresolvable ref, missing
file at the ref, not inside a git work tree. There is no fallback to the working
tree and no default directory, on the principle that an audit which blinds
badly and still reports is worse than one that does not run: the second stops,
the first publishes.

Two things keep the pin honest. `BLIND_REF` must equal the `prereg_commit` the
V9 run manifest recorded, checked by test, so the constant and the provenance
record cannot drift apart. And `audit/v9/BLIND_DIGESTS.json` records the twelve
sha256s of the blinded tree — no manifest had ever recorded a digest of it, so
until now "re-run the blinding and compare" had nothing to compare against.

The comparison that replaced it is two-sided, because a one-sided one is
passable by an empty tree. The blind must contain no post-attack vocabulary
(the negative control, `BLINDING.md` §3.8) **and** must still contain the one
registered leak — K2's `thin()` string carrying `39960` and "3 adversarial
gaps" (`BLINDING.md` §3.7). A rebuild missing the known leak is not the tree
the attackers saw either.


### D-B-024 · An axis that cannot be rebuilt is a measurement that was not taken

`Run.turn_costs()` used to fill a missing `Call.turn` in with the call's
position in the list, and put that position into the same bucket dictionary as
the real labels.  Two defects in one line.  The loud one: a *partly* labelled
record summed the unlabelled call at position 7 into the bucket of the call
genuinely labelled `turn=7`.  The quiet one, and the worse one: a *wholly*
unlabelled record was renumbered `0..n-1` and scored, so a record that could not
answer the question answered it anyway.

`freeze` found it, ruled on it in `STATS_RULES.md` §3.0.2 step 4, registered it
as `RESIDUALS.json` `E2-AXIS`, and sent it here rather than editing our code.
S46 is the answer.

**The decision that needed arguing is not "refuse the partly labelled record"
— that is the ticket — it is "refuse the wholly unlabelled one too."**  This
module's own header used to declare one-call-per-turn as E2's axis, on the
authority of `INPUT_FORMAT.md` gap 5: the ledger carries no turn index, so
call order is the substitute.  Refusing the unlabelled record withdraws that
substitute, and costs any future source that stops stamping turns its E2 and E3
readings outright.  It is still right, because the substitute was never applied
*instead of* the labels — it was applied *alongside* them, in one key space,
and a substitute that cannot be told apart from the real axis in the published
number is not a substitute but a fabrication.  The header now says so, and gap 5
is visible as an absence instead of being papered over by one.

Two things make this a repair rather than a change of口径, and both were
measured before anything was edited rather than argued afterwards:

* **Every priced call in every loadable ledger already carries a `step_idx`**,
  so the fallback was reachable but never load-bearing.  4028 metric cells were
  compared against master one by one: **none moved.**
* **`v9_demotions()` recomputes against the live metric**, so a gate that made
  a V9 attack stop landing would *promote* a metric, which `PREREG_V9.md` R1
  forbids outright.  Measured: 38 demotions before, 38 after, zero tier moves.
  The V9 mutants and the exploit fixtures that meant "one call per turn" were
  re-expressed to say it (`turn=i`) rather than to infer it from the fallback;
  their registered verdicts and every asserted number are unchanged.

The refusal is split so the reason stays useful: `partial` is `unsound` (the
record claims an axis and does not supply one, and `incoherent record:` is the
grep handle for that), `absent` is `thin` (nothing contradicts itself; the axis
was simply never written down).  No fourth status was invented — `Value`'s three
are a contract the artefacts are written against.

The gate sits **after** the price check and **before** `total <= 0` and
`MIN_TURNS_FOR_SHAPE`, because those two are computed from the empty list and
would otherwise report "total cost is zero" about a leg that spent real money.
That is not hypothetical: `20260731T231654Z-R1-sk48-b` bills three calls for
$7.6085275 with no turn label on any of them, and E1 states the money in the
same artefact where E2 would have stated a zero.  **A false reason is worse
than a refusal, because it reads as a finding.**
