"""Is `audit.claim.relaxed_reachable_goal` really Fast Downward's relaxation?

The claim rests on a Python fixpoint standing in for FD's translator.  The audit
checked it on 16 states of one instance (`far4`).  This checks it where it is
more likely to break:

  `sokoban <level> <n>`  -- n states of a geometry that is *not* `far{N}`,
                           stratified so half are Python-relaxation-dead and
                           half are not, each rebuilt as a one-state problem
                           with `audit.claim._problem_with_initial` and handed
                           to the real planner.  Agreement is read off the
                           translator's own `No relaxed solution!` line.

  `noclear <level> <n>`  -- the same states in the `occupied` encoding
                           (`attacks/noclear.py`), where the "cell is free"
                           requirement is a *negative* precondition.  The Python
                           fixpoint ignores negative preconditions; FD's
                           translator compiles them away and does not.  If they
                           disagree anywhere, they disagree here.

    python -m attacks.fd_crosscheck sokoban ell 24
    python -m attacks.fd_crosscheck noclear far4 24
"""

import json
import os
import sys
from typing import Dict, List, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if RIG not in sys.path:
    sys.path.insert(0, RIG)

from audit.claim import _problem_with_initial, _translator_settled  # noqa: E402
from bench import fdrun                                             # noqa: E402
from engines.fd_adapter import backends                             # noqa: E402
from fixtures import sokoban                                        # noqa: E402

from attacks import noclear                                         # noqa: E402
from attacks.relaxation_sweep import analyse, far_level, named_levels  # noqa: E402

WORK = os.path.join(HERE, "crosscheck")


def level_by_name(name: str) -> sokoban.Level:
    if name.startswith("far"):
        return far_level(int(name[3:]))
    for lvl in named_levels():
        if lvl.name == name:
            return lvl
    raise SystemExit("unknown level %s" % name)


def executable() -> str:
    found = backends.find_fast_downward()
    if found is None:
        raise SystemExit("no Fast Downward; set FAST_DOWNWARD")
    return found


def stratified(entry: Dict[str, object], count: int) -> List[int]:
    """Three strata, the third of which is where a disagreement would live.

    * Python says relaxation-dead;
    * Python says relaxation-alive and the state really is alive;
    * Python says relaxation-alive but the state is **truly dead**.  If the
      Python fixpoint is weaker than FD's translator anywhere, it is here: these
      are exactly the states FD could settle before search and this module says
      it cannot.
    """
    relaxed = entry["_relaxation_dead"]
    total = len(entry["_states"])
    truly = entry.get("_truly_dead", set())
    dead = [i for i in range(total) if i in relaxed]
    gap = [i for i in range(total) if i not in relaxed and i in truly]
    alive = [i for i in range(total) if i not in relaxed and i not in truly]
    picked: List[int] = []
    shares = (count // 3, count // 3, count - 2 * (count // 3)) if gap else (
        count // 2, 0, count - count // 2)
    for pool, want in zip((dead, gap, alive), shares):
        if not pool or not want:
            continue
        step = max(1, len(pool) // want)
        picked.extend(pool[::step][:want])
    return sorted(set(picked))


def run(kind: str, level_name: str, count: int) -> Dict[str, object]:
    base = level_by_name(level_name)
    if kind == "noclear":
        level = noclear.as_nc(base)
        domain_path = noclear.write_domain(WORK)
    else:
        level = base
        domain_path = sokoban.DOMAIN_PATH

    entry = analyse(level, domain_path=domain_path, want_truly_dead=True)
    if "skipped" in entry:
        raise SystemExit("level too big: %s" % entry["skipped"])
    states = entry["_states"]
    relaxed = entry["_relaxation_dead"]
    problem = entry["_problem"]
    text = level.problem_text()

    fd = executable()
    work = os.path.join(WORK, "%s-%s" % (kind, level.name))
    logs = os.path.join(work, "logs")
    os.makedirs(logs, exist_ok=True)

    rows = []
    for i in stratified(entry, count):
        path = os.path.join(work, "%04d.pddl" % i)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(_problem_with_initial(text, problem, states[i]))
        log = os.path.join(logs, "%04d.log" % i)
        measured = fdrun.measure(fd, os.path.abspath(domain_path),
                                 os.path.abspath(path), tier=backends.FD_OPTIMAL,
                                 heuristic="lmcut", keep_log=log)
        fd_dead = bool(_translator_settled(log))
        rows.append({
            "state": i,
            "python_relaxation_dead": i in relaxed,
            "fd_translator_dead": fd_dead,
            "agree": (i in relaxed) == fd_dead,
            "fd_solved": measured.solved,
            "fd_proved_unsolvable": measured.proved_unsolvable,
            "fd_returncode": measured.returncode,
            "fd_error": (measured.error or "")[:120],
        })
        flag = "OK " if rows[-1]["agree"] else "DISAGREE"
        print("  %s state %-5d python_dead=%-5s fd_dead=%-5s solved=%s"
              % (flag, i, rows[-1]["python_relaxation_dead"], fd_dead,
                 measured.solved))

    out = {
        "kind": kind,
        "instance": level.name,
        "domain": os.path.basename(domain_path),
        "n_reachable": entry["n_reachable"],
        "n_python_relaxation_dead": entry["n_relaxation_dead"],
        "n_truly_dead": entry.get("n_truly_dead"),
        "n_theorem_dead": entry["n_theorem_dead"],
        "n_theorem_dead_outside_relaxation": entry["n_theorem_dead_outside_relaxation"],
        "n_checked": len(rows),
        "n_agree": sum(1 for r in rows if r["agree"]),
        "n_python_alive_fd_dead": sum(
            1 for r in rows if r["fd_translator_dead"] and not r["python_relaxation_dead"]),
        "n_python_dead_fd_alive": sum(
            1 for r in rows if r["python_relaxation_dead"] and not r["fd_translator_dead"]),
        "rows": rows,
    }
    print("%s/%s: %d/%d agree (python-alive-but-fd-dead %d, python-dead-but-fd-alive %d)"
          % (kind, level.name, out["n_agree"], out["n_checked"],
             out["n_python_alive_fd_dead"], out["n_python_dead_fd_alive"]))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: python -m attacks.fd_crosscheck {sokoban|noclear} "
                         "<level> [n]")
    kind_arg, name_arg = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    result = run(kind_arg, name_arg, n)
    path = os.path.join(HERE, "crosscheck_%s_%s.json" % (kind_arg, name_arg))
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("-> %s" % path)
