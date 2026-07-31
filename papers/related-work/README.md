# papers/related-work — §7 的弹药

The citation library for `Theoria.md` §3.2 item 7 (the paper's Related Work
section) and its immediate downstream, `papers/phase1-workshop/sections/08_related.md`,
whose every citation is currently an unfilled `[bib: TODO]` marker.

This directory is **not** a paper. It is the evidence base a paper draws on: one
section per literature line, one BibTeX library, one prose draft, and the search
trail that produced them.

## Layout

| path | what it is |
|---|---|
| `RELATED.md` | prose draft, directly mergeable into the paper |
| `references.bib` | the verified BibTeX library |
| `UNVERIFIED.md` | entries that failed cross-verification — quarantined, never in `references.bib` |
| `lines/NN_<slug>.md` | one file per literature line: per-paper *what it did* + *our delta* |
| `lines/NN_<slug>.bib` | that line's BibTeX fragment, merged into `references.bib` |
| `SCHEMA_CITATION.md` | the special-cased attribution check (Zeng et al., not Feng et al.) |
| `AUDIT.md` | the adversarial 20% re-verification pass |
| `runs/<UTC>-p23/` | search trail: every query and what came back |

## The six lines

| # | line | `Theoria.md` §3.2 phrasing |
|---|---|---|
| 1 | world models, three waves | 世界模型三波谱系 |
| 2 | planning: unsolvability certificates and admissible heuristics | 规划领域的不可解证书与启发（势启发/operator-counting、LM-cut、PDB） |
| 3 | program synthesis: CEGIS and ILP | 程序综合（CEGIS）与 ILP |
| 4 | Petri invariants and model checking / IC3 | Petri 不变量与模型检查（IC3） |
| 5 | proof-carrying code | 证明携带代码（名字的谱系） |
| 6 | LLM + theorem proving | LLM+定理证明（可行性依据） |

## Red lines, binding on every file here

1. **A citation that could not be verified does not enter `references.bib`.**
   Fabricating a bibliographic record — an invented arXiv id, a guessed year, a
   venue that sounds right — is the least forgivable drift available in this
   repository, because it is invisible to every mechanical check the repo runs
   and it discredits every number next to it. When in doubt, quarantine in
   `UNVERIFIED.md` and say what could not be confirmed.
2. **Two independent sources per entry.** Title, year and venue must agree
   across both before the entry is admitted. The two sources are named per
   entry in the line file.
3. **The sealed pile is not touched, and this rule applies to searching.**
   `INC-BA-001` records nine sealed games whose mechanics leaked into a search
   subagent's context from a project homepage it had to open in order to judge
   whether opening it was safe. Therefore: **academic literature only.** No ARC
   game page, no walkthrough, no leaderboard write-up, no
   `schema-harness.github.io`, no `arc-agi-3` trace dataset. If a search result
   begins describing the mechanics of any specific game, stop reading, record
   that it happened, and do not transcribe it.
4. **No arXiv id is invented for a work that has none.** `Theoria.md` carries no
   bibliography at all, and `baseline-arms/SCHEMA_LOCATE.md` §2.1 already
   established that its central prior-work reference (Schema) has no paper and
   must be cited as `@misc`. That precedent is the house rule.
5. **Every claim of the form "X did Y" is one sentence and is checkable from the
   abstract.** We do not summarise papers we did not read.

## Provenance of the frame

* `Theoria.md` §3.1 (the three-wave table and 检验制度 thesis) and §3.2 item 7
  (the six lines, with the delta for line 2 already stated in the source).
* `papers/phase1-workshop/sections/08_related.md` — P-16's one-section version,
  which this library exists to arm. Its `[bib: TODO]` markers are the demand
  side.
* `baseline-arms/SCHEMA_LOCATE.md` §1.1 — the attribution correction.
* `baseline-arms/INCIDENTS.md` INC-BA-001 — why search itself is a hazard here.
