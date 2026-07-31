# P14 — where the section's evidence comes from, and what is missing

Written as the run opened, before any drafting. Incremental; appended as
verification lands.

## The constitutional hook

`Theoria.md:244`, mandatory constraint 6:

> | 6 | 全称断言必须带证明;裸 UNSAT 禁止 | 搜索说"无解"不算数,证书才算数 |

The census is not a hygiene sweep. It is a measurement of how often this
repository violated its own constraint 6 — and, more sharply, of the
*direction* in which it violated it.

## Primary source of the census — and its gap

The item names three reports at
`engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/SURVEY-*.md`.

**Those files do not exist.** Not on `master` (29f41ea), not on branch
`agent/e11-engine-crosscheck-deep`, and `git log --all --diff-filter=A
--name-only | grep -i survey` returns nothing. What that run directory
actually contains is `CROSSCHECK.md`, `ADVERSARIAL-cegis.md`,
`ADVERSARIAL-zero_space.md`, `MANIFEST.json` and six per-engine partials.

So the census survives in the repository only in **derived** form:

| what | where | status |
|---|---|---|
| the narrative report, with the 340 / 48 / 45 totals | `monitor/inbox/archive/20260729T063000Z-RES-3-the-pattern-you-named-appears-three-more-times.md` | committed |
| the census's own commit message | `cb4c526` | committed |
| five board items carrying the per-site evidence | `monitor/board/items/{C11,E14,E15,S23,V19}*.md` | committed |
| the per-site survey tables themselves | `SURVEY-solver-status.md`, `SURVEY-empty-as-negative.md` | **never committed** |

Consequence for the paper, decided before drafting: the four failure families
and their examples can be cited, because each has a committed board item and a
committed inbox report naming file and line. The **immune control** cannot be
cited at "about 45 sites" on that basis — that number's only witness is a file
that does not exist. Per the item's own rule (任何指不回去的删掉,不要软化措辞
留着) the choice is delete or re-derive. This run **re-derives** it: a fresh
read-only census of the same question, shipped in this run directory, so the
ratio the paper prints points at a file a reader can open.
