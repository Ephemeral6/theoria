"""Everything about the fleet kernel that is not repository-agnostic.

The kernel is ~2100 lines and almost all of it is about coordination, not about
Theoria. What is project-specific turned out to be small and countable, and
this file is the whole of it. Each field below exists because a real line in
the kernel needed it -- nothing here is speculative configurability.

    from fleetkit.config import FleetConfig, load
    cfg = load()                 # reads fleet.toml, or the defaults below

## Why a config object rather than environment variables

The kernel is run from several places -- a scheduled task, a session's shell,
a test harness -- and an environment variable that one of those forgets to set
fails silently and in the reassuring direction: the default looks like an
answer. A missing key here raises where it is read.

## The one field that is not cosmetic

`task_prefix` is how a live worker is recognised on this machine
(`schtasks`/`tasklist` names are matched against it). Get it wrong and every
worker reads as dead, the board releases their claims, and the reflex layer
launches replacements on top of the ones still running. That exact failure --
under a different cause -- reported eight live workers as dead on 2026-07-28,
so this field is validated rather than defaulted.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

#: Where a project's own settings live, relative to the repo root.
CONFIG_NAME = "fleet.json"


class ConfigError(ValueError):
    """Raised where the value is read, not swallowed at import."""


class FleetConfig:
    """The project-specific half of the fleet kernel."""

    def __init__(self, root: str, **kw: Any):
        self.root = os.path.abspath(root)

        #: Prefix of the scheduled-task/process name a worker runs under. Must
        #: be non-empty and must not collide with another fleet on the same
        #: machine; liveness is decided by matching it.
        self.task_prefix: str = kw.get("task_prefix") or ""

        #: Directories a branch may touch. A branch touching anything else
        #: stops for a human -- the point is that an unrecognised path is a
        #: question, never a default-allow.
        self.territories: List[str] = list(kw.get("territories") or [])

        #: Root-level files no automatic merge may touch.
        self.protected_root: List[str] = list(
            kw.get("protected_root") or [".env", "LICENSE"])

        #: Lanes a standing agent can be restricted to. Empty means no lanes.
        self.lanes: List[str] = list(kw.get("lanes") or [])

        #: Board-id prefix -> human phrase, for rendering the dashboard.
        #: Purely cosmetic; a missing key renders the raw id.
        self.plain_item: Dict[str, str] = dict(kw.get("plain_item") or {})

        #: Optional dotted path to a callable returning a completion figure.
        #: The kernel never requires one -- a fleet with no progress model
        #: simply has no progress bar, which is better than a made-up one.
        self.progress_hook: Optional[str] = kw.get("progress_hook")

    # -- validation ---------------------------------------------------------

    def validate(self) -> None:
        """Raise on anything that would fail quietly later."""
        if not self.task_prefix:
            raise ConfigError(
                "task_prefix is empty. Worker liveness is decided by matching "
                "process names against it, so an empty prefix matches nothing "
                "and every worker reads as dead -- the board would release "
                "live claims and the reflex layer would launch duplicates.")
        if not self.territories:
            raise ConfigError(
                "territories is empty. The merge gate treats an unlisted "
                "directory as needing human judgment, so an empty list stops "
                "every branch. Name at least one.")
        dupes = sorted({t for t in self.territories
                        if self.territories.count(t) > 1})
        if dupes:
            raise ConfigError("territories repeats: %s" % ", ".join(dupes))
        for t in self.territories:
            if os.path.isabs(t) or ".." in t.split("/"):
                raise ConfigError(
                    "territory %r must be a plain directory name under the "
                    "repo root" % t)

    def as_dict(self) -> Dict[str, Any]:
        return {"task_prefix": self.task_prefix,
                "territories": self.territories,
                "protected_root": self.protected_root,
                "lanes": self.lanes,
                "plain_item": self.plain_item,
                "progress_hook": self.progress_hook}


def load(root: Optional[str] = None) -> FleetConfig:
    """Read `fleet.json` from `root`. Raises if it is absent or invalid.

    Absent is an error rather than a set of defaults on purpose: a fleet
    running on defaults it never chose is a fleet whose task_prefix probably
    belongs to somebody else.
    """
    root = os.path.abspath(root or os.getcwd())
    path = os.path.join(root, CONFIG_NAME)
    if not os.path.exists(path):
        raise ConfigError(
            "no %s at %s. Run `python -m fleetkit init` to write one."
            % (CONFIG_NAME, root))
    with open(path, encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ConfigError("%s is not valid JSON: %s" % (path, exc))
    cfg = FleetConfig(root, **data)
    cfg.validate()
    return cfg


def write_default(root: str, task_prefix: str,
                  territories: Optional[List[str]] = None) -> str:
    """Write a starter `fleet.json`. Returns the path."""
    cfg = FleetConfig(root, task_prefix=task_prefix,
                      territories=territories or ["src", "docs"])
    cfg.validate()
    path = os.path.join(root, CONFIG_NAME)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cfg.as_dict(), fh, indent=2, sort_keys=True,
                  ensure_ascii=False)
        fh.write("\n")
    return path


#: What Theoria itself uses, kept here as the worked example rather than as a
#: default. A second project copies this shape and changes every value.
THEORIA_EXAMPLE = {
    "task_prefix": "TheoriaAgent-",
    "territories": ["engine-rig", "theory-compiler", "proxy", "battery",
                    "cold-start-a0", "cold-start-a2", "cold-start-a3",
                    "a0-spike", "exam", "worldgen", "fuzzlab", "theoria-arm",
                    "ablation-arm", "arc-recon", "baseline-arms", "papers",
                    "figures", "release", "browser-ops", "monitor",
                    "CONTRACTS", "fleet-study", "fleetkit"],
    "protected_root": [".env", "Theoria.md", "CLAUDE.md", "LICENSE"],
    "lanes": ["campaign", "paper", "infra", "verify"],
    "plain_item": {"S": "基础设施", "V": "验证", "A": "战役", "P": "论文",
                   "E": "引擎", "C": "编译链"},
}
