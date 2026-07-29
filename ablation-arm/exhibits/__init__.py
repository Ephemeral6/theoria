"""The three calibration exhibits, one module each.

`DESIGN.md` §9 organises the arm's calibration by `Theoria.md:259`'s three
verdict classes, and each exhibit is a **testimony** rather than a test: it says
one specific thing about what the incision did, and it is allowed to say that
the design was wrong.

    E1  a true impossibility     -- verdict identical, reason evaporates
    E2  a false one              -- verdict differs, and nobody notices
    E3  the charitable variant   -- the reviewer's punch, answered

Every module exposes the same three names:

    EXHIBIT      the id, "E1" / "E2" / "E3"
    run()        -> a report dict, always including `holds` and `testimony`
    main()       print it

`holds` is deliberately not the same thing as "the run succeeded".  E3's
designed construction no longer exists in this repository, and the honest report
of that is `holds: False` with the measurements that show it — not a substitute
exhibit wearing E3's name.  `DESIGN.md` §10 pre-registered exactly this kind of
outcome as a falsifier, which is why it gets reported rather than worked around.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Tuple

MODULES: Tuple[str, ...] = (
    "exhibits.e1_a0",
    "exhibits.e2_a2",
    "exhibits.e3_charitable",
)


def run_all() -> Dict[str, Any]:
    reports = {}
    for name in MODULES:
        module = importlib.import_module(name)
        reports[module.EXHIBIT] = module.run()
    return {
        "exhibits": reports,
        "all_hold": all(r.get("holds") for r in reports.values()),
        "not_holding": sorted(k for k, r in reports.items() if not r.get("holds")),
    }
