"""OPS-M cycle 30: run monitor's gate per arm exactly as ci_merge.py does.

NOT gates.run() -- that helper never passes env despite its docstring, so it
gives a different verdict.  Replicated here from ci_merge.py:

    sh(args, cwd, timeout, extra_env):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        env.update(extra_env)
        subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout,
                       env=env)
    ...
    row = gate_for(wt, d)
    r = sh(row["cmd"], cwd=os.path.join(wt, d), timeout=1800,
           extra_env=gates.gate_env(wt))

usage: python opsm30_arms.py <outdir> <tag>...      (tag -> .worktrees/opsm30-<tag>)
"""
import json
import os
import subprocess
import sys

REPO = r"C:\Users\user\Desktop\theoria"


def one(wt, tag, outdir):
    assert os.path.isdir(os.path.join(wt, "monitor")), \
        "no monitor/ under %s -- path must exist before 'no verify script' " \
        "can mean anything" % wt
    sys.path.insert(0, os.path.join(wt, "monitor"))
    for mod in [m for m in list(sys.modules) if m == "gates"]:
        del sys.modules[mod]
    import gates                                                # noqa: E402
    sys.path.pop(0)

    row = gates.gate_for(wt, "monitor")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    env.update(gates.gate_env(wt))

    p = subprocess.run(row["cmd"], cwd=os.path.join(wt, "monitor"),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1800, env=env)
    out = (p.stdout or "") + (p.stderr or "")
    with open(os.path.join(outdir, tag + ".gate.txt"), "w",
              encoding="utf-8", errors="replace") as fh:
        fh.write("tag: %s\nworktree: %s\ncmd: %r\ncwd: %s\nrc: %d\n%s\n%s"
                 % (tag, wt, row["cmd"], os.path.join(wt, "monitor"),
                    p.returncode, "-" * 70, out))

    # The gate keeps only detail[-2000:] per stage, which can truncate the
    # failing-test list.  Same command its `_tests()` stage runs, same env,
    # plus -rf so every failing id is named.
    q = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p",
                        "no:cacheprovider", "-rf",
                        os.path.join(wt, "monitor", "tests")],
                       cwd=os.path.join(wt, "monitor"), capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       timeout=1800, env=env)
    qout = (q.stdout or "") + (q.stderr or "")
    with open(os.path.join(outdir, tag + ".pytest.txt"), "w",
              encoding="utf-8", errors="replace") as fh:
        fh.write("rc: %d\n%s\n%s" % (q.returncode, "-" * 70, qout))

    ids, seen = [], set()
    for ln in qout.splitlines():
        if ln.startswith(("FAILED ", "ERROR ")):
            tid = ln.split(None, 1)[1].split(" - ")[0].strip()
            if tid not in seen:
                seen.add(tid)
                ids.append(tid)
    stages = [ln.strip() for ln in out.splitlines() if ln.startswith("== ")]
    return {"tag": tag, "worktree": wt, "head": subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=wt, capture_output=True,
                text=True).stdout.strip(),
            "gate_kind": row["kind"], "gate_name": row["name"],
            "gate_rc": p.returncode, "pytest_rc": q.returncode,
            "failing_ids": ids, "gate_stages": stages}


if __name__ == "__main__":
    outdir = os.path.abspath(sys.argv[1])
    os.makedirs(outdir, exist_ok=True)
    res = []
    for tag in sys.argv[2:]:
        r = one(os.path.join(REPO, ".worktrees", "opsm32-" + tag), tag, outdir)
        res.append(r)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.stdout.flush()
    with open(os.path.join(outdir, "summary-c.json"), "w",
              encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)
