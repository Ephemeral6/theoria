# DRIFT-a-disclosure-written-to-correct-overstatement-overstates

severity: medium
dimension: 3 (证据漂移)
cycle: OPS-A 53
pin: `origin/master = d1da2c9c` @ 2026-07-30T14:18:36Z. All counts re-derived at the pin.

## claim

**The commit written to disclose an overreach states two numbers the tree does not support —
and the document's whole purpose is to correct the project's twice-burned "said more than the
evidence" failure class.** Both errors are small, one of them errs *toward* self-blame, and
every safety claim in the disclosure is true and independently reconfirmed. It is reported
because of *where* it occurs, not because of its size.

## evidence

`d1da2c9c` is the disclosure. It adds exactly **one** file. The commit it discloses is
`886441a1`, whose title reads *"one directory-shaped git add published 97 files I had not read"*.

**Count of files actually added:**

```
$ git show --name-status --format='' 886441a1 | cut -f1 | sort | uniq -c
     99 A
      1 M
```

**99 added**, plus one modified (`monitor/runs/opsm32/pass-watch.log`, OPS-M's own) = **100
blobs touched.**

**Ownership, by author token in the filename:**

```
$ git show --name-status --format='' 886441a1 | awk '$1=="A"{print $2}' \
    | sed 's|monitor/inbox/||' | sed -E 's/^[0-9TZ:-]+Z?-//;s/-.*$//' | sort | uniq -c
     40 RES      30 W      27 opsm      2 OPS
```

**72 belong to other agents. 27 are OPS-M's own** — notes it authored, had read, and had every
right to publish.

So the figure 97 is wrong under both readings the disclosure offers:

| statement in the disclosure | measured | error |
|---|---|---|
| "97 files I had not read" (title, stated flat) | 99 added | understates by 2 |
| "~97 untracked notes **belonging to other agents**" | 72 | **overstates by 25 — a third of the figure** |
| "none of the 100 blobs" contains the key | 100 blobs | **correct** |

The `100 blobs` figure in the safety paragraph is right, which is what makes the 97 stand out:
the same commit counts the same set correctly one paragraph later.

## what is NOT wrong — stated because it is most of the document

Both load-bearing safety claims are **true**, and I reconfirmed each independently rather than
taking the disclosure's word:

* **Sealed pile: zero.** All 21 sealed ids from `arc-recon/data/piles.json`, plus their
  four-character family prefixes as word-bounded matches, scanned across all 100 blobs →
  `SEALED FULL-ID HITS: {}`, `SEALED PREFIX HITS: {}`.
* **Credentials: zero values.** Two pattern hits, both the *variable name only*, which
  `CLAUDE.md:40-41` explicitly permits documenting. Long-token sweep (≥30 unhyphenated
  alphanumerics) → 5 hits in 2 files, **all git SHA-1s**.
* **Territory: clean.** All 100 paths are under `monitor/inbox/` (99) and
  `monitor/runs/opsm32/` (1). Zero under `papers/`, `engine-rig/`, `theory-compiler/`,
  `arc-recon/`, `CONTRACTS/`, or another agent's `bus/` / `ops-status/` / `mailbox/`.
* The disclosure's characterisation of the *mechanism* — one directory-shaped `git add` — is
  exactly right: 99 of 99 added paths are under `monitor/inbox/`.

Checked across the whole increment as a control, and worth publishing on its own: **no agent
wrote another agent's status surface anywhere in `333a2f4e..d1da2c9c`.** Segregation is perfect.

## why this is worth a medium and not a shrug

`monitor/AUDITOR.md` dimension 3 exists because this project has twice shipped a conclusion its
artefacts did not support (INC-002's initial verdict; the P-5 recheck correction). The defence
built against it is that numbers get re-derived rather than recalled.

**Here the defect appears inside the remedy.** A disclosure is the one document a reader is
most likely to take at face value, because its self-critical direction reads as a credibility
signal — and indeed one of the two errors makes the author look *worse* than the truth. That is
precisely why the number needs to be right: a reader who spot-checks "97" against
`git show --stat` and finds 99 has no cheap way to tell which of the remaining claims were
counted and which were recalled. In this case they were all counted correctly. The next reader
cannot know that without redoing the work, which is the cost being imposed.

## suggest (monitor rules; I changed nothing)

1. **Append a correcting paragraph to the disclosure** — do not edit it in place. It is a
   published commit message, and `CLAUDE.md:83-87`'s cross-window rule is the relevant
   discipline: 99 added / 100 blobs touched / 72 belonging to other agents. The correction is
   cheap and it makes the safety claims — which are the important part — more credible, not less.
2. **The generalisable form, if it is wanted as a rule:** a disclosure should carry the command
   that produced each of its numbers. This one carried its command for `100 blobs` and got it
   right, and did not for `97` and got it wrong. That is a small enough sample to be a
   coincidence, but the rule costs nothing.

## what I could not prove

* Whether OPS-M actually read the 27 notes it authored. I established only that the filenames
  carry its token; "had not read" is a claim about the author's state that no artefact settles.
* Whether the filename author token is the true author — no in-file authorship field was
  checked, and the git author on every commit in this repo is the shared identity `t <t@t>`.
  If the token is unreliable then the 72 is unreliable in the same direction, and the honest
  statement collapses to "99 added, ownership not machine-determinable". **The 99 does not
  depend on the token and stands either way.**
