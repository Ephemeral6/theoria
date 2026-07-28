"""Fail-closed guard over the local engine: `environment_files/` and the runners that fill it.

WHY THIS EXISTS. `ACCESS_CHECK.md` §8a.1 concluded, correctly, that caching ARC
data locally for our own analysis is *permitted* and needs no permission. That
sentence is about licensing. It says nothing about what lands in the cache, and
the other half of the same finding is in `browser-ops/TERMS.md` §4.2:

  * first run "download the game source", cached in `environment_files/`
    (docs.arcprize.org/arc-prize-2026);
  * `make list-games` -- "Print every game id available";
  * `make play-local` -- "Runs your agent against every game in the dataset";
  * the swarm runner's `--game` filter: "If not specified, the agent plays all
    available games" (docs.arcprize.org/swarms).

So the first thing anyone does after reading "permitted, no permission needed"
pulls all 25 games' SOURCE onto disk and, by default, plays all 25. By
INC-BA-001's own yardstick source ranks *worse* than trajectories: it hands over
the finished answer to the mechanics. Permission is not containment, and the
containment half has to be executable or it is a note somebody did not read.

WHAT IT REFUSES. The whitelist is positive and the default is deny, in the shape
`baseline-arms/SCHEMA_PATH_A.md` §3 settled on -- and for the reason it gives:
a negative list meets an unforeseen path shape and fails *open*, and failing
open here is not revocable.

  1. A game-playing or game-pulling command with no `--game` selector is
     refused as `deny_default_all`. Defaulting to every game is the documented
     upstream behaviour, so silence is the dangerous case, not the safe one.
  2. A selector token that is not exactly a development-pile full id or its
     4-character prefix is refused -- `deny_sealed` if it names one of the 21,
     `deny_unknown` otherwise. Sealed is tested FIRST, so a command naming both
     piles reads as sealed.
  3. `make list-games` and `make verify-local` are refused outright as
     `deny_unfiltered`: neither takes a filter. `list-games` enumerates all 25
     by design, and `verify-local` is documented as a "30-second smoke test on
     two games" without saying which two.
  4. Any command, trigger or not, that names a sealed game anywhere is refused.
     `arc.make("ls20")` is not a `make` target and has no `--game` flag.
  5. If `data/piles.json` is missing, unreadable, or no longer hashes to the
     value `CLAUDE.md` pins, EVERYTHING is refused. A guard that cannot read
     the cut does not know what it is guarding.

The prefix match is boundary-anchored on both sides, so `blobs/9ar25f0e/` does
not read as `ar25` -- the failure SCHEMA_PATH_A §3.1 found the hard way.

WHAT IT DOES NOT DO. It never opens, decodes, prints, or summarises a single
byte of anything under `environment_files/`. `scan` walks NAMES only. Downloading
is not reading: as long as no model has read those bytes the sealed discipline
holds, and a guard that quoted the file it was refusing would be the leak.

USAGE

    python local_engine_guard.py check -- make play-local           # exit 2
    python local_engine_guard.py check -- uv run main.py --agent=x  # exit 2
    python local_engine_guard.py check -- make play-local GAME=ar25 # exit 0
    python local_engine_guard.py run   -- <argv...>   # vet, then exec if allowed
    python local_engine_guard.py scan  <dir>          # names-only sweep of a cache
    python local_engine_guard.py selftest             # offline, no arguments

Exit codes follow the canary's convention so a scheduler can read them:
0 allowed / clean, 2 REFUSED on sealed-pile grounds, 1 the guard itself could
not run (which is also a refusal -- nothing was executed).

Offline by construction: stdlib only, no network, no API key, no import of any
client code.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
PILES_PATH = os.path.join(HERE, "data", "piles.json")

# The value CLAUDE.md pins. It is the hash of the document with its own "sha256"
# key removed (a file cannot contain its own hash), canonicalised the same way
# `baseline-arms/SCHEMA_PATH_A.md` §1.1 recomputed it.
DECLARED_CUT_SHA256 = (
    "3feca53e5ede695cfa46ae994cb95fd6b43abb9d97295e8c87e6302b41bbc19a"
)

# Verdicts. Exactly one is permissive, which is the point.
ALLOW = "allow"
DENY_SEALED = "deny_sealed"
DENY_UNKNOWN = "deny_unknown"
DENY_DEFAULT_ALL = "deny_default_all"
DENY_UNFILTERED = "deny_unfiltered"


class LocalEngineRefusal(Exception):
    """Refused: this would touch the sealed pile, or might, and we cannot tell."""


# --------------------------------------------------------------------------
# The cut. Fail-closed: any doubt about piles.json refuses everything.
# --------------------------------------------------------------------------


def cut_digest(doc: Dict[str, Any]) -> str:
    """The declared-hash recipe: drop the self-referential key, canonicalise, sha256."""
    body = {k: v for k, v in doc.items() if k != "sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_piles(path: Optional[str] = None) -> Dict[str, Any]:
    # Resolved at call time, not bound as a default: a default argument would
    # freeze the path at import and the guard would keep reading a cut that had
    # since been moved out from under it.
    path = path if path is not None else PILES_PATH
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except OSError as exc:
        raise LocalEngineRefusal(
            "cannot read the pile cut at %s (%s). Refusing every local-engine "
            "path: a guard that cannot read the cut does not know what it is "
            "guarding." % (path, exc)
        )
    except ValueError as exc:
        raise LocalEngineRefusal("the pile cut at %s is not valid JSON (%s)" % (path, exc))

    for key in ("dev_pile", "sealed_pile"):
        if not isinstance(doc.get(key), list) or not doc[key]:
            raise LocalEngineRefusal("the pile cut at %s has no usable %r" % (path, key))

    actual = cut_digest(doc)
    declared = doc.get("sha256")
    if actual != DECLARED_CUT_SHA256 or declared != DECLARED_CUT_SHA256:
        raise LocalEngineRefusal(
            "the pile cut no longer hashes to the value CLAUDE.md pins "
            "(recomputed %s, file declares %s, pinned %s). piles.json rule 3: "
            "any change after a game has been played invalidates the cut and is "
            "an incident. Refusing everything until a human adjudicates."
            % (actual[:16], str(declared)[:16], DECLARED_CUT_SHA256[:16])
        )
    return doc


def _prefix(game_id: str) -> str:
    return game_id.split("-")[0]


def piles_index(doc: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    doc = doc if doc is not None else load_piles()
    dev = list(doc["dev_pile"])
    sealed = list(doc["sealed_pile"])
    return {
        "dev": dev,
        "sealed": sealed,
        "dev_prefix": {_prefix(g): g for g in dev},
        "sealed_prefix": {_prefix(g): g for g in sealed},
    }


# --------------------------------------------------------------------------
# Name classification -- the only thing that ever looks at a game id.
# --------------------------------------------------------------------------

# Boundary-anchored on both sides. ARC ids are lowercase alphanumerics, so the
# guard against `blobs/9ar25f0e/` is "no alphanumeric may abut the prefix".
_BOUNDARY = "[0-9a-zA-Z]"


def names_game(text: str, game_id: str) -> bool:
    """Does `text` name this game, by full id or by its 4-character prefix?"""
    for token in (game_id, _prefix(game_id)):
        if re.search(r"(?<!%s)%s(?!%s)" % (_BOUNDARY, re.escape(token), _BOUNDARY), text):
            return True
    return False


def classify_name(text: str, idx: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
    """Classify an arbitrary string (a path, a CLI token). Sealed is tested first.

    Returns (verdict, detail). Naming nothing is `deny_unknown`, not `allow`:
    the whitelist is positive.
    """
    idx = idx if idx is not None else piles_index()
    for sealed in idx["sealed"]:
        if names_game(text, sealed):
            return DENY_SEALED, sealed
    hits = [g for g in idx["dev"] if names_game(text, g)]
    if hits:
        return ALLOW, ",".join(sorted(hits))
    return DENY_UNKNOWN, "names no game in the cut"


def classify_selector_token(token: str, idx: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
    """Classify one `--game=` token. Must be an exact dev id or its exact prefix.

    Deliberately stricter than `classify_name`: upstream treats the value as an
    ID *prefix*, so a loose token like `s` would filter to several games at once
    and five of those are sealed. Only the two exact forms are allowed through.
    """
    idx = idx if idx is not None else piles_index()
    tok = token.strip().strip("\"'").strip()
    if not tok:
        return DENY_UNKNOWN, "empty selector token"
    if tok in idx["sealed"] or tok in idx["sealed_prefix"]:
        return DENY_SEALED, idx["sealed_prefix"].get(tok, tok)
    if tok in idx["dev"]:
        return ALLOW, tok
    if tok in idx["dev_prefix"]:
        return ALLOW, idx["dev_prefix"][tok]
    return DENY_UNKNOWN, (
        "%r is neither a development-pile id nor its 4-character prefix; "
        "upstream reads it as an ID prefix, which may widen to sealed games" % tok
    )


# --------------------------------------------------------------------------
# Command classification.
# --------------------------------------------------------------------------

# Targets that take no filter at all, with the documented reason they are refused.
UNFILTERABLE_TARGETS = {
    "list-games": (
        "`make list-games` is documented as \"Print every game id available\" -- "
        "it enumerates all 25 by design and takes no filter. We already hold the "
        "ids in data/piles.json; read those instead."
    ),
    "verify-local": (
        "`make verify-local` is documented as a \"30-second smoke test on two "
        "games\" and the docs do not say which two. An unnamed pair cannot be "
        "checked against the cut."
    ),
}

# Commands that pull game source or play games. Matched on the whole command.
_TRIGGERS = (
    (r"(?<![0-9a-zA-Z])environment_files(?![0-9a-zA-Z])", "touches the environment_files/ cache"),
    (r"(?<![0-9a-zA-Z_-])make\s+play-local(?![0-9a-zA-Z])", "`make play-local` runs every game in the dataset"),
    (r"(?<![0-9a-zA-Z_-])make\s+play(?![0-9a-zA-Z_-])", "`make play` runs the local engine"),
    (r"(?<![0-9a-zA-Z_-])make\s+list-games(?![0-9a-zA-Z])", "`make list-games` enumerates every game"),
    (r"(?<![0-9a-zA-Z_-])make\s+verify-local(?![0-9a-zA-Z])", "`make verify-local` plays two unnamed games"),
    (r"main\.py\b[^\n]*--agent", "the swarm runner defaults to every available game"),
    (r"--agent[=\s][^\n]*main\.py", "the swarm runner defaults to every available game"),
    (r"(?<![0-9a-zA-Z_.])arc_agi(?![0-9a-zA-Z_])", "the local toolkit downloads game source on first use"),
    (r"(?<![0-9a-zA-Z_.])Arcade\s*\(", "the local toolkit downloads game source on first use"),
    (r"(?<![0-9a-zA-Z_.])arc\.make\s*\(", "arc.make() instantiates a game locally"),
    (r"(?<![0-9a-zA-Z_-])swarm[s]?(?![0-9a-zA-Z_-])", "the swarm runner defaults to every available game"),
)

# `--game`, `--games`, `-g`, and the Makefile-style `GAME=` / `GAMES=`.
_SELECTOR_INLINE = re.compile(
    r"(?:--games?|(?<![0-9a-zA-Z_-])-g|(?<![0-9a-zA-Z_])GAMES?)\s*=\s*([^\s]+)"
)
_SELECTOR_SPACED = re.compile(r"(?:--games?|(?<![0-9a-zA-Z_-])-g)\s+([^\s-][^\s]*)")


def _as_text(command: Sequence[str] | str) -> str:
    if isinstance(command, str):
        return command
    return " ".join(command)


def selector_tokens(text: str) -> List[str]:
    raw: List[str] = []
    for pattern in (_SELECTOR_INLINE, _SELECTOR_SPACED):
        for match in pattern.finditer(text):
            raw.append(match.group(1))
    tokens: List[str] = []
    for chunk in raw:
        for token in chunk.strip("\"'").split(","):
            token = token.strip().strip("\"'")
            if token:
                tokens.append(token)
    return tokens


def classify_command(
    command: Sequence[str] | str, idx: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Decide whether a command line may run. One permissive verdict, four refusals."""
    idx = idx if idx is not None else piles_index()
    text = _as_text(command)
    result: Dict[str, Any] = {
        "command": text,
        "verdict": ALLOW,
        "reasons": [],
        "triggers": [],
        "selector": [],
    }

    # Rule 4 first: naming a sealed game is fatal whatever the command is.
    for sealed in idx["sealed"]:
        if names_game(text, sealed):
            result["verdict"] = DENY_SEALED
            result["reasons"].append(
                "the command names sealed game %s. piles.json rule 1: the sealed "
                "pile is not played, inspected, or read about." % sealed
            )
            return result

    triggers = [why for pattern, why in _TRIGGERS if re.search(pattern, text)]
    # dedupe, order-stable
    result["triggers"] = list(dict.fromkeys(triggers))
    if not result["triggers"]:
        result["reasons"].append(
            "not a local-engine path; this guard has no opinion on it"
        )
        return result

    for target, why in UNFILTERABLE_TARGETS.items():
        if re.search(r"(?<![0-9a-zA-Z_-])make\s+%s(?![0-9a-zA-Z])" % re.escape(target), text):
            result["verdict"] = DENY_UNFILTERED
            result["reasons"].append(why)
            return result

    tokens = selector_tokens(text)
    result["selector"] = tokens
    if not tokens:
        result["verdict"] = DENY_DEFAULT_ALL
        result["reasons"].append(
            "no --game selector. Upstream documents the default as \"the agent "
            "plays all available games\" / \"every game in the dataset\", so an "
            "unfiltered run is a run over all 25 -- 21 of them sealed. Name the "
            "development-pile games explicitly: %s" % ", ".join(idx["dev"])
        )
        return result

    for token in tokens:
        verdict, detail = classify_selector_token(token, idx)
        if verdict != ALLOW:
            result["verdict"] = verdict
            result["reasons"].append("selector token %r: %s" % (token, detail))
            return result

    result["reasons"].append(
        "every selector token resolves inside the development pile: %s"
        % ", ".join(tokens)
    )
    return result


def assert_command_allowed(command: Sequence[str] | str) -> None:
    """Raise unless the command is filtered down to the development pile."""
    result = classify_command(command)
    if result["verdict"] != ALLOW:
        raise LocalEngineRefusal(
            "REFUSED (%s): %s\n  command: %s"
            % (result["verdict"], "; ".join(result["reasons"]), result["command"])
        )


def assert_local_pull_allowed(game_ids: Optional[Sequence[str]]) -> List[str]:
    """Programmatic entry point for anything that pulls game source.

    `None` or an empty sequence is the default-all case and is refused: callers
    that mean "all our games" must say which four.
    """
    idx = piles_index()
    if not game_ids:
        raise LocalEngineRefusal(
            "REFUSED (%s): a pull with no game list defaults to all 25. Name the "
            "development-pile games explicitly: %s"
            % (DENY_DEFAULT_ALL, ", ".join(idx["dev"]))
        )
    resolved: List[str] = []
    for token in game_ids:
        verdict, detail = classify_selector_token(token, idx)
        if verdict != ALLOW:
            raise LocalEngineRefusal("REFUSED (%s): %r -- %s" % (verdict, token, detail))
        resolved.append(detail)
    return resolved


# --------------------------------------------------------------------------
# Cache sweep -- names only, never contents.
# --------------------------------------------------------------------------


def scan_paths(names: Sequence[str], idx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Classify a list of path strings. Nothing is opened; this is a name sieve."""
    idx = idx if idx is not None else piles_index()
    entries = []
    counts = {ALLOW: 0, DENY_SEALED: 0, DENY_UNKNOWN: 0}
    for name in names:
        verdict, detail = classify_name(name, idx)
        counts[verdict] = counts.get(verdict, 0) + 1
        entries.append({"path": name, "verdict": verdict, "detail": detail})
    return {
        "entries": entries,
        "counts": counts,
        "clean": counts.get(DENY_SEALED, 0) == 0 and counts.get(DENY_UNKNOWN, 0) == 0,
    }


def scan_dir(root: str, idx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Sweep a cache directory by filename. Never reads a byte of any file."""
    names: List[str] = []
    if not os.path.isdir(root):
        return {"root": root, "exists": False, "entries": [], "counts": {}, "clean": True}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for filename in sorted(filenames):
            names.append(os.path.relpath(os.path.join(dirpath, filename), root).replace(os.sep, "/"))
    report = scan_paths(names, idx)
    report["root"] = root
    report["exists"] = True
    return report


# --------------------------------------------------------------------------
# Self-test. Runs offline, asserts the properties the guard is claimed to have.
# --------------------------------------------------------------------------


def selftest() -> List[str]:
    """Return a list of failures; empty means the guard holds its own claims."""
    failures: List[str] = []
    idx = piles_index()

    def expect(label: str, got: str, want: str) -> None:
        if got != want:
            failures.append("%s: got %s, want %s" % (label, got, want))

    # 1. Every sealed game, in every plausible shape, is refused.
    for sealed in idx["sealed"]:
        for template in (
            "make play-local GAME=%s",
            "uv run main.py --agent=random --game=%s",
            'python -c \'arc.make("%s")\'',
            "ls environment_files/%s",
        ):
            expect(
                "sealed %s" % sealed,
                classify_command(template % sealed)["verdict"],
                DENY_SEALED,
            )
            expect(
                "sealed prefix %s" % sealed,
                classify_command(template % _prefix(sealed))["verdict"],
                DENY_SEALED,
            )

    # 2. The development pile passes, full and prefix.
    for dev in idx["dev"]:
        expect("dev %s" % dev, classify_command("make play-local GAME=%s" % dev)["verdict"], ALLOW)
        expect(
            "dev prefix %s" % dev,
            classify_command("uv run main.py --agent=x --game=%s" % _prefix(dev))["verdict"],
            ALLOW,
        )

    # 3. Silence is refused.
    for bare in ("make play-local", "uv run main.py --agent=random", "make list-games"):
        got = classify_command(bare)["verdict"]
        if got == ALLOW:
            failures.append("unfiltered %r was allowed" % bare)

    # 4. Boundary anchoring: a prefix buried in a hash must not read as a game.
    if classify_name("blobs/9ar25f0e/data.bin", idx)[0] == ALLOW:
        failures.append("boundary anchoring failed: 9ar25f0e read as ar25")

    # 5. The two piles' prefixes are disjoint -- prefix matching is only safe if so.
    overlap = set(idx["dev_prefix"]) & set(idx["sealed_prefix"])
    if overlap:
        failures.append("dev and sealed prefixes overlap: %s" % sorted(overlap))
    for dp in idx["dev_prefix"]:
        for sp in idx["sealed_prefix"]:
            if dp.startswith(sp) or sp.startswith(dp):
                failures.append("prefix %r and %r are nested" % (dp, sp))

    # 6. Both piles named at once reads as sealed.
    expect(
        "mixed selector",
        classify_command("make play-local GAME=ar25,ls20")["verdict"],
        DENY_SEALED,
    )
    return failures


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

_USAGE = """usage:
  local_engine_guard.py check   [--json] -- <command argv...>
  local_engine_guard.py run     [--json] -- <command argv...>
  local_engine_guard.py scan    [--json] <directory>...
  local_engine_guard.py selftest [--json]

exit: 0 allowed/clean, 2 REFUSED, 1 the guard could not run"""


def _split_argv(argv: List[str]) -> Tuple[bool, List[str]]:
    as_json = "--json" in argv
    rest = [a for a in argv if a != "--json"]
    return as_json, rest


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(_USAGE)
        return 1
    mode, argv = argv[0], argv[1:]
    as_json, argv = _split_argv(argv)
    if argv and argv[0] == "--":
        argv = argv[1:]

    try:
        if mode == "selftest":
            failures = selftest()
            if as_json:
                print(json.dumps({"failures": failures, "ok": not failures}, indent=2))
            else:
                for line in failures:
                    print("FAIL " + line)
                print("selftest: %s" % ("green" if not failures else "%d FAILURES" % len(failures)))
            return 0 if not failures else 2

        if mode in ("check", "run"):
            if not argv:
                print(_USAGE)
                return 1
            result = classify_command(argv)
            if as_json:
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                print("%s: %s" % (result["verdict"].upper(), result["command"]))
                for reason in result["reasons"]:
                    print("  - " + reason)
            if result["verdict"] != ALLOW:
                if not as_json:
                    print(
                        "\nNothing was executed. Filter to the development pile "
                        "and try again."
                    )
                return 2
            if mode == "run":
                # stdout/stderr are inherited: the guard passes the child through
                # rather than reading it. It refuses content, it does not relay it.
                return subprocess.call(argv)
            return 0

        if mode == "scan":
            if not argv:
                print(_USAGE)
                return 1
            reports = [scan_dir(root) for root in argv]
            clean = all(r["clean"] for r in reports)
            if as_json:
                print(json.dumps(reports, indent=2, sort_keys=True))
            else:
                for report in reports:
                    if not report.get("exists"):
                        print("scan %s: absent -- nothing cached, nothing to refuse"
                              % report["root"])
                        continue
                    for entry in report["entries"]:
                        if entry["verdict"] != ALLOW:
                            print("%s  %s  (%s)"
                                  % (entry["verdict"], entry["path"], entry["detail"]))
                    print(
                        "scan %s: %d allow, %d sealed, %d unknown"
                        % (
                            report["root"],
                            report["counts"].get(ALLOW, 0),
                            report["counts"].get(DENY_SEALED, 0),
                            report["counts"].get(DENY_UNKNOWN, 0),
                        )
                    )
                if not clean:
                    print(
                        "\nREFUSED. Files naming sealed games are cached here. Nothing "
                        "was opened -- this is a name sieve. Do not read them; record "
                        "an incident and delete the cache."
                    )
            return 0 if clean else 2

        print(_USAGE)
        return 1

    except LocalEngineRefusal as exc:
        print("REFUSED: %s" % exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
