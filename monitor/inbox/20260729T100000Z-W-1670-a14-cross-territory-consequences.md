# A14 · three things outside baseline-arms that A14 either touches or found

From W-1670, working `A14-campaign-json-untracked` on branch
`agent/a14-campaign-json-untracked`. A14 is a salvage ticket and stayed inside
its territory. These three need an owner elsewhere; **the first one is a
consequence of A14's own commit and is the one to act on.**

---

## 1. ACT: `figures/SOURCES.sha256` declares four files absent that A14 just made present

`figures/SOURCES.sha256:24-27` carries `ABSENT0000…` sentinels under
`[absent-optional]` for exactly these four:

```
baseline-arms/out/shards/ledger.ar25.jsonl
baseline-arms/out/shards/ledger.g50t.jsonl
baseline-arms/out/shards/ledger.sk48.jsonl
baseline-arms/out/shards/ledger.tn36.jsonl
```

They were never truly absent — they have been on disk in the main tree since
2026-07-28 07:25–10:59. The P4 and P8 figure builds ran inside `.worktrees/`
checkouts, where untracked payload does not exist, so the sentinel recorded
"absent from *this build's* cwd", not "absent from the project".

**A14 commits all four.** From now on they are present in every checkout, and
`figures/sources.py`'s own note says a dropped-in file "is picked up
automatically". So the next figure rebuild in a tree that has them may silently
change its inputs relative to the last published build.

Their digests (`a82d1f40… / 7fd8aa90… / 4ba20da9… / bacb484a…`) are already
pinned as *present* inputs by `battery/runs/20260728T061147Z-v3/MANIFEST.json:149-152`
and `battery/artifacts/capability_spectrum.json:809-813`, so two registries now
disagree about whether the same four files exist.

**A14 did not touch `figures/`.** This needs a `figures/` owner to decide
whether to re-pin the sentinels as real hashes and re-run, or to pin the figures
to the absent-input build. Either is defensible; leaving the disagreement is not.

---

## 2. FYI: the Phase 4 published-surface manifest is stale for one file

`release/MANIFEST.jsonl:148` pins `baseline-arms/out/campaign_cells.jsonl` as
`dd967e98…`, `size: 16014`. The file on disk and at HEAD is `ebe6396e…`,
26,765 bytes.

**This is growth, not rewriting.** Walking the history gives
2191 → 6776 → 11382 → **16014** → 20580 → 22130 → 25225 → **26765**,
monotonically increasing, exactly as the append-only rule requires
(`baseline-arms/DECISIONS.md:194`, `harness/ledger.py:156`). Nothing was
tampered with.

The problem is narrower and still worth fixing: **the manifest that defines what
Phase 4 publishes no longer describes what it would publish.**
`battery/runs/P-14/MANIFEST.json:33` separately pins the file's very first
2,191-byte version while claiming 31 runs, which looks like its own bug.

---

## 3. FYI: a CRLF trap of the same class as the one A14 hit, one layer out

Six **tracked** files are CRLF on disk but LF in git:

```
baseline-arms/out/pilot_{ar25-0c556536, g50t-5849a774, g50t_sonnet_rerun,
                         sk48-d8078629, sk48_sonnet_rerun, tn36-ef4dde99}.json
```

`git status` reports them clean, because `* text eol=lf` + `core.autocrlf=true`
makes git normalise on compare. But `figures/sources.py:722` and
`release/enumerate.py:109` both hash **raw bytes** — so re-running either in this
working tree emits the CRLF digests and produces a spurious manifest diff
against pins that were generated from an LF checkout.

Not a content problem: a fresh clone gets the LF form and every pin matches. It
is a property of *this machine's* working tree, and the fix is a `git checkout --`
re-materialisation. **A14 did not do it** — they are tracked files outside this
ticket's scope, and other sessions are live in this tree.

A14 hit the same class of bug on its own four files and closed it with an
`out/campaign/*.json -text` rule plus a test that compares the blob to the disk.
The same treatment would work here, and would be cheaper than remembering.

---

**A14 itself: zero API calls, zero dollars, zero sealed-pile contact.**
Details in `baseline-arms/runs/20260729T100000Z-a14/`.

---

## 4. DECIDE (added after adversarial review): is `origin` public? A14 commits 8 class-B files

`release/LICENCE_POSTURE.md` classifies material by ARC's ToS §2/§4. Run
through the repository's own content-based classifier
(`release/enumerate.py`), **8 of the 12 files A14 commits are class B,
"api-derived-compilation → NEEDS WRITTEN PERMISSION, default excluded"**:

```
out/shards/ledger.{ar25,g50t,sk48,tn36}.jsonl    B  (id + environment payload)
out/shards/probe_log.{ar25,g50t,sk48,tn36}.jsonl B  (X-API-Key transaction marker)
out/campaign/campaign_*.json                     C  (releasable-flagged)
```

`LICENCE_POSTURE.md` names `baseline-arms/out/shards/ledger.*.jsonl` in its
class-B examples verbatim.

**Why A14 committed them anyway**, on that file's own reasoning:

> Caching is separately and explicitly fine … **Holding is permitted;
> publishing is not.** These are two different questions and the release kit
> must not merge them.

Tracking is holding. The publication gate is an allow-list and it is automatic:
`release/enumerate.py --dry-run` classifies all eight as B **without anyone
adding them to a list**, and B is excluded by default. The precedent is settled
— `baseline-arms/ledger.jsonl` and the eleven `ledger.a7-*` / `probe_log.a7-*`
shards are class B, already tracked, already withheld by
`release/FRAME_HASHES.jsonl`. A14 enlarges an existing class-B surface (the
enumerator now reports B: 61 files / 95.16 MB); it does not open a new one.

**The one question A14 cannot answer.** If `origin`
(`github.com/Ephemeral6/theoria`) is a **public** remote, then pushing is
arguably the "republished, uploaded, posted, publicly displayed" that §2 names,
and holding-vs-publishing stops being the right frame. A14 made no network call
to check, because repository visibility is an ops/human decision rather than a
research one.

If the answer is "public", note that the line was crossed well before A14 by
the already-tracked class-B files listed above, and the remedy is a policy
decision about the whole surface — not something to pin on this branch.

**Also recorded for whoever owns the release surface:** A14's first draft
argued from "Phase 4 publishes every tracked file". That is the correct
worst-case rule for a *credential* and `CLAUDE.md` uses it that way, but it is
not how the release kit treats data — `BUNDLE.jsonl` is an allow-list with
class B and D excluded by default. The premise has been corrected in
`baseline-arms/runs/20260729T100000Z-a14/INVENTORY.md` §B′.
