# S23-unreadable-is-not-clean · run state

Worker `W-1631`, branch `agent/s23-unreadable-is-not-clean`, base `29f41ea`.
Written as the work happened, not after it.

## Step 0 — the baseline, captured before a line was edited

`before/` holds three files. All three are green today, and that is the point of
capturing them: **the defect this item names is latent, not firing.** Nothing in
the tree is currently unreadable, so the gate's wrong answer is not visible in
any real run. Only a deliberate negative sample can show it.

| capture | result |
|---|---|
| `before/check_redlines.generate.txt` | exit 0. `2817 tracked file(s) scanned for the literal key`; `0 credential violation(s), 0 sealed-pile violation(s)`; "Both red lines clear." The credential half ran for real — `client.load_api_key` resolves the main checkout's `.env` from inside a worktree (`arc-recon/client.py:78`), so this is not a skipped check. |
| `before/check_redlines.verify.txt` | exit 0, credential half NOT APPLICABLE by design, sealed half identical. |
| `before/contamination.txt` | exit 0. piles.json sha256 MATCHES; three ledgers, 1231 + 560 + 1955 calls, sealed ADDRESSED: NONE; sealed pile 21 → claim set 19; **no NEEDS ADJUDICATION block printed**. |

So on this tree the two exit codes and the two printed tables agree. That is
luck, not design: the register happens to be clean and every tracked file happens
to decode. The item's claim is about what happens when they are not.

One thing the baseline already shows, which was not in the work order: the note
`2817 tracked file(s) scanned for sealed game ids` in `check_sealed` prints
`len(paths)` — the number of files it was *given*, not the number it *read*. The
credential half computes a real `scanned` counter; the sealed half does not. On
a tree with an unreadable file the two notes would disagree, and only one of them
would be true.
