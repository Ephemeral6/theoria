# bus.jsonl — where the data lives, how it was counted

## Storage
`monitor/bus.py` writes four files per agent under `monitor/bus/<AGENT>/`:
`in.jsonl` (monitor writes, append-only, each row carries `seq`), `out.jsonl`
(the session writes; `kind` is `ack` with `ref=<seq>`, or `say`), `cursor.json`
(the session's `last_seq` + `read_at` — the bus's only delivery receipt), and
`URGENT` (a sentinel file whose mere existence is the interrupt channel).
Eight channels exist: `OPS-A`, `OPS-B`, `OPS-M`, `OPS-R`, `RES-1`…`RES-4`.
All 28 bus files are tracked in git. `bus.py` was not run: its console output is
mojibake here, so every row was read from the JSONL as UTF-8.

## Count
**111 messages**, window `2026-07-28T14:18:55Z` → `2026-07-28T23:39:50Z`:
27 monitor→agent (`in.jsonl`) + 84 agent→monitor (`out.jsonl`), of which 20 are
acks. Git history was replayed per file (`git show <sha>:<path>` at each of its
commits) to date every line: all eight `in.jsonl` and `out.jsonl` grow
monotonically, nothing was rotated, truncated or deleted, and the only bus paths
ever removed are the `URGENT` sentinels (removal is how they are consumed). Each
row cites its file plus the first commit that contained that line; all 41 shas
resolve to real commits and all 16 paths exist.

## True count vs the board's "28"
The "28 条总线消息" line entered the repo in commit `2e96b47`
(2026-07-28T15:19:18Z, the commit that created the S17 item). At that commit's
parent the bus held 27 messages in both directions; `2e96b47` itself appended two
more, ending at 29. So **28 was a live both-directions reading taken mid-write**,
at 15:19Z. It is not a wrong denominator — it is an 8-hour-stale snapshot, taken
about a fifth of the way into the bus's life. It is definitely *not* the
monitor→agent count, which was 14 at that moment and 27 at census time.

## Receipt claimed vs actually read
`cmd_read` advances the cursor to the file's **last** seq regardless of what the
reader consumed, so `cursor.json` proves delivery, never reading. 21 of 27
monitor→agent messages are cursor-claimed read; only 19 carry an explicit ack;
6 were never claimed at all. Three (`RES-1` #2/#3/#5, flagged
`receipt_disputed`) are the documented discrepancy: the cursor said read, and the
monitor recorded on the bus itself (`RES-1` #6) that a successor session had
inherited the cursor and skipped them. 6 messages are interrupts (`kind=urgent`);
**3 of them were never collected** — `RES-1/URGENT` (7), `RES-2/URGENT` (4),
`RES-4/URGENT` (4) are still on disk. The catalogued "reported receipted when
none had been read" fault was in the *probe*, not the bus: it shelled out to
`bus.py` and decoded GBK console output as UTF-8; `monitor/scan.py:634-638` now
reads the files directly and says so. `B-50` is a first-hand report that the
mojibake is live in the bus CLI. `B-23`/`B-24` are a byte-identical duplicate
send 9 seconds apart.

## Not the bus
`monitor/inbox/*.md` (43 files) is a separate append-only agent→monitor report
channel with no receipt, and `monitor/mailbox/` is the per-agent markdown mailbox
the bus replaced at 14:18:55Z. Neither is included here.

## Could not determine
- Agent→monitor rows have no receipt at all: `bus.py` never records the monitor
  reading `out.jsonl`, so `read_confirmed` is null for all 84.
- Per-message latency: `cursor.json` keeps only the latest `read_at`, so
  send→read delay is recoverable only for acked messages.
- Whether the six 14:18:55Z announcements were one broadcast: `bus.py` has no
  broadcast verb, so six identical-timestamp sends are indistinguishable from a
  loop over the agent list.
- Authorship within a channel: `out.jsonl` rows carry no session id, so a
  restarted `RES-1` cannot be told apart from its predecessor.
