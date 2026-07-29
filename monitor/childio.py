"""How to decode a child process, when the right answer depends on the child.

Every `subprocess.run(..., text=True)` in this directory decodes with the host
locale, which here is cp936. That is wrong for some children and right for
others, and the two failure modes point in opposite directions -- which is
exactly why the sweep this module exists for was *not* done as a single
find-and-replace.

## Two families

**UTF-8 children.** Python (`sys.executable`, pytest, `board.py`) and git.
Python here is configured to emit UTF-8; git stores paths and messages as
UTF-8. Decoding their output as cp936 either mojibakes it or raises
`UnicodeDecodeError` *inside* `subprocess.run` -- and a checker that dies while
decoding its child is a checker that did not check. That is the mismatch that
reported eight live workers as dead on 2026-07-28.

**Console children.** `tasklist` and `schtasks` are Windows built-ins and emit
the *console code page*, which on this box is cp936. Forcing UTF-8 on them
would corrupt their output -- and `tasklist` is what worker-liveness is read
from, so a careless "fix everything to UTF-8" would recreate the original
incident from the other side. Anyone sweeping this file should read that
sentence twice.

## The one rule both families share

`errors="replace"`. Whatever the encoding, decoding must not be able to raise:
the check has to reach its verdict even if a byte is unexpected. A mangled
character in a log is a cosmetic problem; an exception thrown while reading a
child is a check that silently did not happen.

`_CONSOLE` is resolved once at import rather than per call, so a test can
monkeypatch it, and so the value cannot change halfway through a scan.
"""

import locale
import subprocess

#: What Windows console tools emit on this host.
_CONSOLE = locale.getpreferredencoding(False) or "utf-8"


def run_utf8(args, **kwargs):
    """Run a child that emits UTF-8: Python, pytest, git, this repo's own tools."""
    kwargs.setdefault("capture_output", True)
    return subprocess.run(args, text=True, encoding="utf-8",
                          errors="replace", **kwargs)


def run_console(args, **kwargs):
    """Run a Windows console built-in: `tasklist`, `schtasks`.

    Decoded with the console code page, NOT utf-8. Getting this backwards is
    how liveness detection breaks, and it breaks quietly and in the reassuring
    direction -- a process that is running reads as gone.
    """
    kwargs.setdefault("capture_output", True)
    return subprocess.run(args, text=True, encoding=_CONSOLE,
                          errors="replace", **kwargs)
