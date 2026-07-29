# Evidence for the intro/abstract rewrite — the five arms, and what benchmark this is

Prompt `P13-paper-intro-abstract`. Every fact below carries the repo-relative path
and the line or JSON field it was read from. Where an artefact does not settle
something, the entry says **not established** rather than inferring.

Read-only pass: no section file was edited.

---

## Part 1 — The five arms

### 1.1 Where the list actually lives

The enumeration exists in exactly one place in the repository, and it is a JSON
field, not prose:

`battery/artifacts/capability_spectrum.json`, field `provenance.arms`:

```json
["bare_cc", "schema_repro", "theoria_a0", "theoria_a0_spike", "theoria_a2"]
```

The same file's `runs` object holds 95 entries, each with an `arm` field, so the
per-arm counts are recoverable by counting `runs[*].arm`.

**No prose anywhere in the paper enumerates them.** `sections/07_battery.md:11`
says "95 runs across 5 arms"; line 32 says "two of the five arms live in
gitignored payloads" without naming which; §7.2 names `bare_cc` and
`schema_repro`; §7.10's table cell (line 429) mentions "A0, a0-spike and A2" in
passing. `sections/01_intro.md:113` says "95 runs, 5 arms, 4 development-pile
games". `sections/00_abstract.md:88` says "95 runs across five arms".
`papers/phase1-workshop/PROVENANCE.md:124` repeats "95 runs, 5 arms, 4 games".
The lay reviewer's finding is confirmed: a reader is never told what the five are.

### 1.2 The five arms

Counts computed from `battery/artifacts/capability_spectrum.json`, `runs[*].arm`.

| # | arm id (exact, as in the artefact) | what it is, in one clause | Theoria or control | runs |
|---|---|---|---|---|
| 1 | `bare_cc` | plain Claude Code playing ARC-AGI-3 development-pile games with no theory layer, no engines and no tools — it sees a frame, picks an action, sees the next frame | **control** | **80** |
| 2 | `schema_repro` | released trajectories from another team's Schema agent on the same four games, ingested from upstream files rather than re-run here | **control** | **8** |
| 3 | `theoria_a0` | the theory-compiler track's A0 cold start — two offline runs on self-built 9×9 worlds with published ground truth, one per world (A0 and A0′) | **Theoria** | **2** |
| 4 | `theoria_a0_spike` | the engine-rig track's independent A0 cold start on a self-built sokoban-2 world, the only bundle that was deliberately broken four times to see whether the manual notices | **Theoria** | **1** |
| 5 | `theoria_a2` | the A2 repair-loop bundle — four views of one self-built pushing world (sweep, holed play record, probed record, the 18-action refutation) | **Theoria** | **4** |

Supporting citations, arm by arm:

* **`bare_cc`** — `baseline-arms/harness/bare_cc.py:1-8` (module docstring): *"The
  bare-Claude-Code arm: no theory layer, no engines, no world model. Claude sees
  the frame, picks an action, sees the next frame. That is the whole loop. This
  is the column `Theoria.md` 1.12 calls '裸 Claude Code / 零分工'."* Three
  deliberate properties are load-bearing: the model runs in a neutral working
  directory outside the repository so it cannot read `Theoria.md` or the pile cut
  (`bare_cc.py:10-16`, D-009); tools are off; failures are recorded not smoothed.
  Ingested by `battery/adapters/ledger_jsonl.py`.
  Breakdown from `capability_spectrum.json`, `runs[*]`:
  games `ar25-0c556536` 21 / `g50t-5849a774` 19 / `sk48-d8078629` 22 /
  `tn36-ef4dde99` 18; models `claude-haiku-4-5-20251001` 70 / `claude-sonnet-5` 6
  / `claude-opus-5` 4; campaigns `S1 baseline-parity` 48 / unlabelled (`null`) 15
  / `m4-pilot` 14 / `phase3-variance-envelope` 3; `pile: "dev"` on all 80.
* **`schema_repro`** — `battery/adapters/schema_traces.py:1-12,71` (`ARM =
  "schema_repro"`): *"the control arm `Theoria.md` Phase 2 process 1 actually
  names… Source: `baseline-arms/schema_traces/`, two upstream collections
  (`claude_fable_opus/`, `gpt_5_6_sol/`) x the four development-pile games."*
  It is **not** a reproduction: `sections/07_battery.md:52-57` and
  `battery/DECISIONS.md` D-B-019 record that the Schema harness was never
  published, so the `⟨复现值⟩` cell in `Theoria.md` stays empty. Payload is
  gitignored (no upstream licence, D-B-020), so only aggregate statistics reach
  any artefact.
  Breakdown: 4 games × 2 collections; models `gpt-5.6-sol` 4 / `claude-fable-5` 2
  / `claude-opus-4-8` 2; `pile: "dev"` on all 8. Only the Claude-side collection
  records model calls at all (`sections/07_battery.md:78-84`).
* **`theoria_a0`** — `battery/adapters/a0.py:1-7` (docstring) and `a0.py:376`
  (`arm="theoria_a0"`). Runs `a0-base` (275 steps) and `a0-no-button` (111
  steps); both `game_id: null`, `pile: "synthetic"`, `model: null`,
  `model_calls: 0`, `intent: "explore"`, `source: "cold-start-a0"`. The adapter
  calls A0 *"the battery's richest fixture and its only one with a theory"*.
* **`theoria_a0_spike`** — `battery/adapters/a0_spike.py:1-8` and `a0_spike.py:339`
  (`arm="theoria_a0_spike"`). One run `a0-spike`, **`steps: 0`** (the bundle
  publishes no trace; the docstring refuses to execute another track's pipeline to
  manufacture one), `repairs: 4`, `pile: "synthetic"`, `model_calls: 0`.
* **`theoria_a2`** — `battery/adapters/a2.py:1-8,25-31` and `a2.py:771`
  (`arm="theoria_a2"`). Four runs: `a2-sweep` (247 steps, the control),
  `a2-play-record` (183, the exhibit), `a2-probed` (195, `repairs: 1`, the
  repair), `a2-refutation` (18, `intent: "solve"`, the 18-step solve). All
  `pile: "synthetic"`, `model_calls: 0`.

### 1.3 Totals check — the counts are right, the sentence around them is not

**Is it really 95 runs?** Yes. `capability_spectrum.json` `provenance.n_runs: 95`,
and `len(runs) == 95` independently. `battery/REPORT_V2.md:3` agrees.

**Is it really 5 arms?** Yes, in the sense of five distinct `arm` values.
`provenance.arms` has five entries; the `runs` object uses exactly those five.

**Do the per-arm counts sum to 95?** **Yes: 80 + 8 + 2 + 1 + 4 = 95.** No missing
runs, no double counting.

**But the compound sentence is wrong, and this is the number that matters for the
rewrite.** `sections/07_battery.md:11` and `sections/01_intro.md:113` both read
"95 runs … and 4 development-pile games" as a single scope statement. As a
conjunction over the run set it is **false**:

> **Only 88 of the 95 runs touch a development-pile game. The other 7 —
> `theoria_a0` 2, `theoria_a0_spike` 1, `theoria_a2` 4 — carry `game_id: null`
> and `pile: "synthetic"`, and were run on self-built worlds that are not
> ARC-AGI-3 games at all.**

Corroborated three ways, all in the artefacts:

* `capability_spectrum.json`, `runs[*].pile`: `"dev"` 88, `"synthetic"` 7.
* `battery/artifacts/discrimination_arms.json`, `control_runs: 88`;
  `arms_present: ["bare_cc", "schema_repro"]`. The specified gradient runs over
  88 runs, not 95.
* `battery/artifacts/arm_contrast.json`, `n_control_runs: 80`,
  `n_theoria_runs: 7`, `design: "unpaired; no game is shared between the arms"`.

`battery/audit/contrast.py:29-30` states the split in the source: *"`bare_cc`
plays ARC games; the offline Theoria arms play self-built worlds. There is no
game to pair on."*

**A second structural point the "5 arms" phrasing hides.** The five are not five
peers. `arm_contrast.json` groups three of them under one key —
`theoria_arms: ["theoria_a0", "theoria_a0_spike", "theoria_a2"]` — against
`control_arm: "bare_cc"`. All three are offline self-built bundles with zero model
calls, and they are three *bundles from two tracks*, not three experimental
conditions. Read the other way: the battery has **2 control arms and 3 offline
Theoria bundles**, and `battery/audit/validation.py:41` encodes exactly that —
`CONTROL_ARMS = ("bare_cc", "schema_repro")`.

**Not established:** whether `theoria_a0` and `theoria_a0_spike` "should" be one
arm or two. They are two ids, two adapters (`battery/adapters/a0.py`,
`a0_spike.py`) and two tracks' cold starts; no artefact declares a merge.

**A run is not always an independent sample.** `battery/adapters/a2.py:25-40`:
the four A2 runs come from one bundle and their traces overlap byte-for-byte —
`history_trace[0..182]`, `probed_trace[0..182]` and `raw_trace[0..182]` are
identical — and every run records the overlap in `Run.notes["overlaps"]` "so a
de-redundancy pass cannot read four rows as four observations". The abstract
should not let "95 runs" read as 95 samples.

**Arithmetic reconciliation of the 80 `bare_cc` runs** (offered because
`battery/REPORT_V2.md` and the artefact use different labels):
v1 was 31 runs across 4 arms (`REPORT_V2.md:3`); 31 − 7 Theoria = 24 `bare_cc` at
v1; `REPORT_V2.md:250` reports "The S1 campaign, 56 more `bare_cc` runs";
24 + 56 = 80 ✓, and 31 + 56 + 8 (`schema_repro`) = 95 ✓. Of those 56, the
artefact labels 48 `S1 baseline-parity` (`REPORT_V2.md:251-253` explains that S1
writes `scenario` not `campaign`, so `load_campaigns()` had been dropping the
label). **Not established:** which specific 8 of the 15 `campaign: null` runs are
S1 shards — the arithmetic reconciles, no field says so.

### 1.4 The word "arm" is itself overloaded, and the rewrite will collide with it

None of these five is the framework's own arm. Four distinct senses of "arm" are
live in the paper and its design document:

| sense | where | what it means |
|---|---|---|
| battery arm | §7 (25 uses), §10 | one of the five data-source labels above |
| A3 experimental condition | §6 (16 uses), table at `sections/06_a3_transfer.md:24-31` | one of **cold start / transfer / blind control** |
| the live Theoria arm | §9 (29 uses), e.g. `sections/09_preflight.md:4,58,64` | the agent configuration in `theoria-arm/` that talks to the environment proxy |
| A0 vs A0′ | `sections/03_a0.md:145` "n = 1 per arm" | the two self-built world cold starts |

And the design document specifies a **three**-arm study, not a five-arm one:
`Theoria.md:406` — *"三臂实证:同壳对照 裸 agent / Schema / Theoria"* (bare agent /
Schema / Theoria), restated at `Theoria.md:280` (三臂共享同一外壳) and
`Theoria.md:292`. The battery's "5 arms" is a partition of *available trajectory
sources*, not of the design's arms.

Load-bearing consequence for the abstract: `sections/00_abstract.md:88` says
"95 runs across five arms" and `:114-118` says "No arm was run against a baseline
… **None is across the framework's own arms**". Both are true, but only because
"arm" changes meaning between the two sentences. The live Theoria arm's run (§9)
spent **zero billable actions** and is **not among the 95**.

---

## Part 2 — What benchmark this paper is about

### 2.1 The reviewer's finding, re-measured on the current build

`grep -n "ARC" papers/phase1-workshop/PAPER.md` returns **four** lines in the
whole assembled paper:

| PAPER.md | section source | what it says |
|---|---|---|
| 1993 | `sections/09_preflight.md:22` | inside a code fence: `arm -> env proxy -> key injection -> sealed-pile guard -> ARC -> ledger` |
| 2203 | `sections/10_limitations.md:56` | "The one thing recomputed over ARC trajectories is the battery (§7)" |
| 2235 | `sections/10_limitations.md:88` | "This paper makes no induction claim about any ARC game." |
| 2446 | `sections/11_related.md:43` | "ARC-AGI-3: an editable, executable world model checked by replaying the entire…" |

So **"ARC-AGI-3" appears exactly once in the paper**, in §11 Related Work, and
there it is an attribute of *Schema's* work, not a statement of this paper's own
environment. The first mention of "ARC" in reading order is inside a code fence
on ~page 20. The reviewer is right, and the confirming numbers are above. (Their
line 1918 differs from this build's 1993; the finding is unchanged.)

### 2.2 The environment, and its correct name

**Correct name: ARC-AGI-3.** `arc-recon/README.md:4` — *"the read-only instrument
used to survey the **ARC-AGI-3** API"*. Not "ARC" and not "ARC-AGI"; those are
different, earlier benchmarks.

**One-sentence description**, from `Theoria.md:9` (§1.0), which is the design
document's own framing:

> 一个 agent 面对一个从没见过的小世界:64×64 网格、16 色、确定性规则、规则隐藏。
> 它只能做两件事:行动,观察。
> — an agent faces a small world it has never seen: a 64×64 grid, 16 colours,
> deterministic rules, the rules hidden. It can do exactly two things: act, and
> observe.

**Access surface** — `arc-recon/README.md:50`: base URL `https://three.arcprize.org`,
auth header `X-API-Key`. (`browser-ops/TERMS.md:6` records that
`three.arcprize.org` now 301s to `https://arcprize.org/arc-agi/3`, with developer
docs at `https://docs.arcprize.org/`.)

**Public set size: 25 games.** `arc-recon/README.md:51` ("public set size: **25
games**") and `arc-recon/data/piles.json`, field `n_public: 25`.

### 2.3 The vocabulary a reader needs

All from `arc-recon/README.md` unless marked.

| term | what it is in ARC-AGI-3 | citation |
|---|---|---|
| **game** | one of the 25 titled entries returned by `GET /api/games`; per-game fields are `game_id`, `title`, `tags`, `baseline_actions`. Every `game_id` carries a version suffix that doubles as an environment-version fingerprint (e.g. `ar25-0c556536`) | `arc-recon/README.md:52,54` |
| tag families | `keyboard_click` 13, `click` 7, `keyboard` 4, untagged 1 | `arc-recon/README.md:53` |
| **level** | a real API concept, not an inference: the RESET/ACTION response carries `levels_completed` and `win_levels`, and `len(baseline_actions)` equals the level count (cross-checked: g50t `win_levels` 7 == 7 baseline-action entries). A game is a ladder of levels | `arc-recon/README.md:55,67` |
| **action** | `POST /api/cmd/RESET` opens or resets a session and returns a `guid`; gameplay actions are `ACTION1`…`ACTION6`, with `available_actions` declared per game (g50t: `[1,2,3,4,5]`, no ACTION6, matching its `keyboard` tag). ACTION6 is the click action and its coordinates go at the **top level** of the request, not inside `data` | `arc-recon/README.md:69,123,244` |
| **frame** | the response `frame` is a *list* of 64×64 grids (a render burst, not one tick per element); `step` is frozen as `S → A → frames[-1]` | `arc-recon/README.md:66`, `arc-recon/CASCADE_RULING.md` |
| **scorecard** | `POST /api/scorecard/open` returns a `card_id`; the card 404s until a game is played against it. Its `total_actions` counts **successful** actions only — failed 400s and retry amplification do not bill (19 samples, 3 model tiers, 4 games, 3 campaigns, no exception) | `arc-recon/README.md:56,57,181` |
| baseline actions | 17,135 across the public set | `arc-recon/README.md:55` |

The design document uses the same object model: `Theoria.md:286` — *"围绕官方 API
的对象模型:game / scorecard / 会话 / 动作→帧"* (game / scorecard / session /
action→frame).

### 2.4 The pile cut

`arc-recon/data/piles.json`, sha256 `3feca53e5ede695cfa46ae994cb95fd6b43abb9d97295e8c87e6302b41bbc19a`,
`cut_version: "v1"`, `seed: 8298874` (0x7EA17A), `method: "stratified by tag
family; quota {click: 1, keyboard: 1, keyboard_click: 2}; the untagged singleton
stays sealed; within a family, ids sorted lexicographically and drawn with
splitmix64(seed)"`.

**Development pile — 4 games** (`piles.json` `dev_pile`; table at
`arc-recon/README.md:509-514`):

| game_id | title | family | levels | baseline actions |
|---|---|---|---|---|
| `ar25-0c556536` | AR25 | keyboard_click | 8 | 748 |
| `g50t-5849a774` | G50T | keyboard | 7 | 879 |
| `sk48-d8078629` | SK48 | keyboard_click | 8 | 1070 |
| `tn36-ef4dde99` | TN36 | click | 7 | 317 |

**Sealed pile — 21 games** (`piles.json` `sealed_pile`, 21 entries;
`sealed_only_families: ["<untagged>"]`, so the sealed side keeps a mechanics
family the development pile never shows). Rules, verbatim from `piles.json`
`rules`: the sealed pile is not played, inspected or read about until
development-pile work is frozen; that includes upstream released artifacts
belonging to sealed games; any change to the file after a game has been played
invalidates the cut and must be recorded as an incident.

Reason for the cut, `arc-recon/README.md:519-521`: *"Phase 3 iterates until it
gets results; that is only honest if the confirmation runs on problems nobody has
seen. A game that has been played is burnt."*

**Contamination state.** `arc-recon/data/claim_set.json`: `sealed_pile_size: 21`,
`claim_set_size: 19`, `clean: 12`, `retained_with_sensitivity_analysis: 7`,
`quarantined: 2` (`ft09-0d8bbf25`, `ls20-9607627b`), `needs_adjudication: 0`.
12 + 7 = 19 = the claim set; 19 + 2 = 21 ✓. The `rule` field: a held-out claim may
name only games in `claim_set`, and statistics over it must be reported a second
time with the seven sensitivity games excluded, the weaker result governing.
`arc-recon/README.md:530-535`: the four development-pile games are
`trajectories_reviewed`; **no sealed game has been touched via the API**, checked
over the whole ledger rather than asserted.

`sections/07_battery.md:456-466` adds a caveat the rewrite should not repeat
wrongly: the digest `3feca53e…41bbc19a` is **not** the file's hash — it is taken
over the canonical JSON minus its own `sha256` field. The file itself hashes to
`d3140eff…` LF-normalised and `f2ef44d1…` on a Windows checkout.

---

## Part 3 — The word collision, mapped

### 3.1 The two things the paper calls a "game"

* **Sense A — a self-built deterministic world.** §3 (A0, A0′), §4 (A1, peg
  solitaire), §5 (A2), §6 (A3, levels L1/L2). Built by this project, ground truth
  known, no network, no API. `sections/03_a0.md:5`: *"A0 is a self-built world,
  not a benchmark task."* `sections/10_limitations.md:53-57`: *"Every world in
  §3–§5 was built by us; A1's is peg solitaire."*
* **Sense B — an ARC-AGI-3 game.** The four development-pile games the battery
  recomputes over (§7), the pile guard in §8, the live preflight in §9, the
  incidents in §10.

`Theoria.md:295` already draws the line in the design's own words: *"提示词的开发
迭代全部发生在**自建世界族**,ARC 开发堆只作验证"* — prompt iteration happens
entirely in the self-built world family, the ARC development pile is only for
validation.

### 3.2 Exactly where the two senses collide — it is small and asymmetric

**"game(s)" used in Sense A (self-built) — 3 occurrences, all §6/abstract:**

| file:line | text |
|---|---|
| `sections/00_abstract.md:98` | "A theory carried unchanged to a second level of the same **game**" |
| `sections/06_a3_transfer.md:10` | "A3 answers it for two levels of one **game**" |
| `sections/06_a3_transfer.md:163` | "**Levels, not games.** A3 says nothing about carrying a domain between **games** with different mechanics" |

A3's world is self-built: `cold-start-a3/a3world/a3_world.py`, cited at
`sections/06_a3_transfer.md:19`.

**"game(s)" used in Sense B (ARC-AGI-3) — everywhere else,** ~50 occurrences:
`00_abstract.md:95,115`; `01_intro.md:89,91,113,121,124`; `02_framework.md:111`;
`05_a2.md:27,43`; `07_battery.md` (22 occurrences, lines 11–440);
`08_exam.md:145`; `09_preflight.md:88,128,133,161`; `10_limitations.md` (17
occurrences, lines 34–209). One further use is the *verb*
(`07_battery.md:233` "harder to game"), a third and unrelated sense.

**"world" used in Sense B (an ARC-AGI-3 game) — 2 occurrences, both §7:**

| file:line | text |
|---|---|
| `sections/07_battery.md:50` | "pairing `bare_cc` against `schema_repro` **by game** … which controls for the **world**" |
| `sections/07_battery.md:99` | "'pairing by game, which controls for the **world**' is true of the column…" |

Both are inherited from the battery's own vocabulary, not invented by the paper —
`battery/audit/contrast.py:31` (*"Arm is confounded with **world**"*) and
`battery/artifacts/arm_contrast.json`, whose fields are `worlds_bare_cc`
(= the four ARC `game_id`s) and `worlds_theoria` (= `a0-spike`, `cold-start-a0`,
`cold-start-a2`). `battery/audit/contrast.py:79-80`:
`return sorted({r.game_id or r.source for r in runs})`. **In the artefacts,
"world" is the umbrella term covering both senses.** That is the one place a
`world = self-built only` convention will fight the repository.

Everywhere else, "world" in the paper is either Sense A (self-built) or the
uncountable theoretical use — "world model", "the world", "world theory" (§2, §11,
abstract title and opening). Those are not part of the collision: they are never
a countable noun.

### 3.3 A second collision the same rewrite will hit: "level"

`level` is a genuine ARC-AGI-3 API field (`levels_completed`, `win_levels`,
`arc-recon/README.md:67`), and §6 simultaneously uses "level" for L1/L2 of a
self-built 9×9 world (12 + 6 occurrences in `06_a3_transfer.md`).
`sections/03_a0.md:156` uses "the next development level" in a third, informal
sense.

The consequence is precisely the abstract sentence a reviewer will misread. Once
the abstract names ARC-AGI-3 (as the rewrite must),
`sections/00_abstract.md:98` — "A theory carried unchanged to a second level of
the same game" — will read as an ARC-AGI-3 result. It is not: A3 is a self-built
world with two hand-built levels, and §6 spends its whole limitation 1 saying so.

### 3.4 Candidate disambiguating vocabularies

**Option 1 (recommended core): `world` = self-built; `game` = ARC-AGI-3 only.**

* Total edits: **5**. Three Sense-A "game"s → "world"
  (`00_abstract.md:98`, `06_a3_transfer.md:10`, `06_a3_transfer.md:163`); two
  Sense-B "world"s → "game" (`07_battery.md:50,99`).
* Checked against existing usage: it is already the paper's dominant convention.
  `03_a0.md:5`, `05_a2.md:27` ("| the world | DC22, a sealed public **game** | a
  self-built 9×9 pushing **world** |" — the contrast table already uses exactly
  this pairing), `10_limitations.md:54`, `01_intro.md:12,88,97,120`,
  `00_abstract.md:57,62,66` all conform. It matches `Theoria.md:295`
  (自建世界族 vs ARC 开发堆) and the repo's own naming (`game_id`, `dev_pile`,
  "sealed game").
* Known cost, must be handled explicitly: it contradicts
  `battery/artifacts/arm_contrast.json`'s `worlds_bare_cc` field and
  `battery/audit/contrast.py:31`. If §7 quotes those field names it should quote
  them as field names in backticks and add half a sentence — "the artefact calls
  both kinds of arena a *world*" — rather than silently rewriting the artefact's
  vocabulary. `07_battery.md:99` is already a *quotation* of §7.2's own earlier
  sentence, so fixing line 50 fixes line 99 mechanically.
* It leaves "world model" / "the world" untouched, because those are never
  countable.

**Option 2 (recommended addition): qualify on first use per section — "ARC-AGI-3
game" / "development-pile game".**

* Same five edits as Option 1, plus the qualifier at the first Sense-B use in each
  section. Costs about six words per section.
* Already partly in place: "development-pile games" appears at
  `01_intro.md:113`, `07_battery.md:11,52`, `09_preflight.md:88`,
  `10_limitations.md:34,94`. Adopting it as the rule makes ~12 existing phrases
  the standard rather than the exception, and it is the only change that helps a
  lay reader who has not yet reached §11.

**Option 3 (rejected): `world` = self-built; `task` = the ARC-AGI-3 item.**

* Rejected on grep evidence. "task" occurs 3 times in the whole paper
  (`03_a0.md:1` region, `11_related.md:2` occurrences), and one of them —
  `03_a0.md:5`, *"A0 is a self-built world, **not a benchmark task**"* — would
  invert meaning under the new convention. Upstream calls them games everywhere
  (`GET /api/games`, `game_id`, `piles.json` `dev_pile`/`sealed_pile`,
  `contamination_log.jsonl`), so the paper would be the only document in the
  chain using "task", and every quoted artefact field would disagree with the
  surrounding prose. It also collides with ARC-AGI-1/2, where "task" means a
  static input/output grid pair — the exact confusion the paper is trying to avoid.

**Option 4 (for "level", pairs with Option 1): keep "level" for ARC-AGI-3 and
write A3's two arenas as "L1/L2" or "the two levels of one self-built world".**

* §6 already writes `L1` and `L2` as the primary handles
  (`06_a3_transfer.md:19,21,34,80,101`), so the section needs at most a first-use
  gloss. The one sentence that must change is `00_abstract.md:98`.

**Recommendation: Option 1 + Option 2 + Option 4, together.** Option 1 fixes the
five hard collisions, Option 2 makes the fix legible to a reader who does not yet
know what ARC-AGI-3 is, Option 4 stops the abstract's item (6) from being read as
a benchmark result. Additionally: never write the battery's "5 arms" without
either the qualifier "battery arm" or the arm ids, because §6, §9 and
`Theoria.md`'s 三臂 all use "arm" for something else (§1.4 above).

---

## Not established

* Whether `theoria_a0` and `theoria_a0_spike` are intended as one arm or two. Two
  ids, two adapters, two tracks; no artefact rules on it.
* Which 8 of the 15 `campaign: null` `bare_cc` runs are S1 shards. The totals
  reconcile arithmetically (24 + 56 = 80); no field records the split.
* Any per-arm run count stated in prose. `battery/REPORT_V2.md` gives the Schema
  arm as 8 runs (line 45) and the S1 addition as 56 (line 250); the other four
  counts exist only as `runs[*].arm` in `capability_spectrum.json`.
* Whether a single-word replacement for Sense-B "game" exists that upstream would
  also accept. Nothing in `arc-recon/`, `browser-ops/TERMS.md` or
  `docs.arcprize.org` excerpts uses anything but "game".
