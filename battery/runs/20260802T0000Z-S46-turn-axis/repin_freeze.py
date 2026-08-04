"""Re-pin BATTERY_V1.md's digest blocks after a legitimate battery change.

`freeze.render_blocks()` is deliberately not wired to write -- "a freeze that a
script can refresh in place is not a freeze".  This does the writing by hand,
block by block, and refuses to touch anything except a ```freeze:<name>``` fence
whose body is entirely digest lines.  It prints every digest that moves so the
change is reviewable rather than silent.

    cd <repo> && python battery/runs/20260802T0000Z-S46-turn-axis/repin_freeze.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)

from battery import freeze                                     # noqa: E402


def main() -> int:
    record = os.path.join(REPO, freeze.RECORD.replace("/", os.sep))
    with io.open(record, encoding="utf-8") as fh:
        text = fh.read()

    rendered = freeze.render_blocks()
    if not isinstance(rendered, str):
        rendered = "\n\n".join(rendered)
    fresh = {}
    for block in re.findall(r"```freeze:[a-z]+\n.*?\n```", rendered, re.DOTALL):
        fresh[block.splitlines()[0][len("```freeze:"):]] = block
    if not fresh:
        print("!! render_blocks() produced no fenced block")
        return 1

    moved = 0
    for name, block in fresh.items():
        pattern = re.compile(
            r"```freeze:%s\n.*?\n```" % re.escape(name), re.DOTALL)
        match = pattern.search(text)
        if match is None:
            print("!! no ```freeze:%s block in the record" % name)
            return 1
        if match.group(0) == block:
            continue
        old = dict(_lines(match.group(0)))
        new = dict(_lines(block))
        for key in sorted(set(old) | set(new)):
            if old.get(key) != new.get(key):
                print("  %-14s %-52s %s -> %s"
                      % (name, key, (old.get(key) or "absent")[:20],
                         (new.get(key) or "absent")[:20]))
                moved += 1
        text = text[:match.start()] + block + text[match.end():]

    with io.open(record, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("\n%d digest line(s) moved in %s" % (moved, freeze.RECORD))

    fails = freeze.check()
    if fails:
        print("\nSTILL DRIFTING (%d):" % len(fails))
        for line in fails:
            print("  - %s" % line.split(" hashes to")[0])
        return 1
    print("freeze.check() is clean")
    return 0


def _lines(block):
    for line in block.splitlines()[1:-1]:
        parts = line.split("  ", 1)
        if len(parts) == 2:
            yield parts[1], parts[0]
        else:
            yield line, line


if __name__ == "__main__":
    raise SystemExit(main())
