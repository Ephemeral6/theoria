"""`python -m fleetkit ...` -- the front door README.md and __init__.py document.

    python -m fleetkit init --prefix MyFleet-     # writes fleet.json
    python -m fleetkit board list
    python -m fleetkit board claim W-1
    python -m fleetkit bus say W-1 "..."

Until S42 this module did not exist, so the first command in both documents --
and the first thing anyone deploying the kit types -- died with
`No module named fleetkit.__main__`. `verify.py` did not notice because it
called `config.write_default()` directly: the gate was green on top of a front
door that had never opened. It now drives these verbs as subprocesses, which is
the only arrangement in which a broken entry point is visible to it.

`board` and `bus` delegate to the modules' own `main()`, so
`python -m fleetkit board list` and `python -m fleetkit.board list` are the same
command and neither can rot while the other works.
"""

import argparse
import os
import sys


def cmd_init(argv):
    """Write a starter `fleet.json` in `--root` (default: here)."""
    ap = argparse.ArgumentParser(
        prog="python -m fleetkit init",
        description="Write a starter fleet.json for a new repository.")
    ap.add_argument("--prefix", required=True,
                    help="scheduled-task/process name prefix a worker of this "
                         "fleet runs under. Liveness is decided by matching "
                         "it, so it must be unique on the machine.")
    ap.add_argument("--root", default=".",
                    help="repository root to write fleet.json into (default: "
                         "the current directory)")
    ap.add_argument("--territories", default="src,docs",
                    help="comma-separated directories a branch may touch")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing fleet.json")
    ns = ap.parse_args(argv)

    from fleetkit import config

    root = os.path.abspath(ns.root)
    path = os.path.join(root, config.CONFIG_NAME)
    if os.path.exists(path) and not ns.force:
        # 不静默覆盖：fleet.json 里的 task_prefix 是这支舰队的身份，覆盖掉它
        # 会让所有还在跑的工人一夜之间读成死的。
        print("INIT-REFUSED %s already exists. Pass --force to overwrite it "
              "-- but note that changing task_prefix makes every worker "
              "already running under the old one read as dead." % path)
        return 2
    territories = [t.strip() for t in ns.territories.split(",") if t.strip()]
    if not territories:
        # `config.write_default` reads an empty list as "give me the starter
        # default", which for a value the caller typed is a silent override.
        print("INIT-REFUSED --territories named none. The merge gate treats an "
              "unlisted directory as needing human judgment, so an empty list "
              "stops every branch. Name at least one.")
        return 2
    try:
        written = config.write_default(root, task_prefix=ns.prefix,
                                       territories=territories)
    except config.ConfigError as exc:
        print("INIT-REFUSED %s" % exc)
        return 2
    print("wrote %s" % written)
    print("task_prefix=%s territories=%s" % (ns.prefix, ",".join(territories)))
    return 0


def _delegate(module, argv):
    """Run a submodule's `main()` as if it had been invoked directly."""
    saved = sys.argv
    sys.argv = [module.__name__] + list(argv)
    try:
        return module.main()
    finally:
        sys.argv = saved


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    verb = argv[0] if argv else ""
    rest = argv[1:]

    if verb == "init":
        return cmd_init(rest)
    if verb == "board":
        from fleetkit import board
        return _delegate(board, rest)
    if verb == "bus":
        from fleetkit import bus
        return _delegate(bus, rest)

    if verb in ("", "-h", "--help", "help"):
        print(__doc__)
        return 0 if verb else 2
    print("unknown verb %r. Known verbs: init, board, bus." % verb)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
