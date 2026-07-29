# Known traps

Every entry cost a real outage on 2026-07-27/28. None of them announced
itself — that is what they have in common and why they are worth a file.
They are listed with the symptom first, because the symptom is what you will
actually be looking at.

---

## 1. `schtasks` and `tasklist` emit the console code page, not UTF-8

**Symptom:** every worker reads as dead. The board releases live claims, the
reflex layer launches replacements on top of sessions that are still running.

Windows console built-ins emit the console code page — cp936 on a zh-CN box.
Worker liveness is decided by matching process names in that output, and the
first version matched a UTF-8 pattern against it. **Eight live workers were
reported dead.**

The trap when you go to fix it is that the correct answer is *not* "decode
everything as UTF-8". Python children and git emit UTF-8; `schtasks` and
`tasklist` do not, and forcing UTF-8 on those recreates the same incident from
the other side. `fleetkit/board.py` decodes with
`locale.getpreferredencoding(False)` and says why on the line above.

## 2. Never decode a child with the host locale by default

**Symptom:** a check dies mid-run with `UnicodeDecodeError`, or its output is
mojibake, and nothing downstream reports that the check did not happen.

`subprocess.run(..., text=True)` uses the host locale. For a UTF-8 child on a
cp936 box that either mangles the text or raises *inside* `subprocess.run` — and
a checker that dies while decoding its child is a checker that did not check.

Whatever encoding you choose, pass `errors="replace"`. A mangled character in a
log is cosmetic; an exception thrown while reading a child is a check that
silently did not run.

## 3. A gate must not write into the tree it is checking

**Symptom:** a territory's own read-only test goes red for reasons unrelated to
the branch, or two gates that pass alone fail when run in sequence.

The first completion gate written here dropped files into the directory it was
gating and turned that arm's read-only test red — the gate broke the thing it
was guarding. Send output to `tempfile.mkdtemp()` and remove it in a `finally`.

Corollary worth knowing: a gate that regenerates a *tracked* artefact is telling
you something different — the committed artefact no longer matches what the code
produces. That is a real finding, but it belongs to the territory, not to
whichever branch happens to be merging.

## 4. Snapshot comparison is a false positive generator under concurrency

**Symptom:** a read-only check reports that another track's files changed, and
it is right, and it does not matter.

Hash-the-tree-before-and-after works only when nothing else is running. With
several sessions live, someone else's commit lands mid-check. Either scope the
comparison to paths you own, or report it as amber and name concurrency as a
possible cause — never as a hard red, because a check that is flaky for a
reason unrelated to its subject gets switched off within a day.

## 5. `schtasks /TR` truncates at 261 characters

**Symptom:** a scheduled task registers successfully and then does nothing, or
runs a command that is missing its tail.

The task action is silently cut. Keep `/TR` to a short launcher script and put
the real arguments inside it.

## 6. The `claude` `.cmd` shim eats multi-line UTF-8 argv

**Symptom:** a worker starts with an empty or truncated prompt, runs, and exits
0 having done nothing. The exit code is the trap: it looks like success.

Pass the prompt on **stdin**, never as an argument.

The general lesson, which is why this file exists: **judge a worker by its
artefacts, not by its exit code.** Every failure above returns 0 somewhere.

---

## The shape they share

All six fail *quietly*, and all six fail in the direction that looks fine:
dead-but-reported-alive, unchecked-but-reported-green, empty-but-reported-done.
When adding a check to a fleet built on this kit, the question worth asking is
not "does it pass?" but **"can I make it fail on purpose?"** A probe that has
never been shown the failure it exists to catch has only been observed not to
complain.
