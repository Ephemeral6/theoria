"""OPS-M cycle 32 / agent D: run one territory's gate in one worktree exactly as
ci_merge.py's try_merge() does, then re-run the suite with -rf so every failing
id is named (the gate truncates its own detail to the last 2000-3000 chars).

Faithfulness notes, all checked against monitor/ci_merge.py at cc7e414e:

  * discovery is ci_merge.gate_for -> TEST_CMDS (empty today) -> gates.gate_for
    of the *merged tree*, i.e. gate_for(wt, d).  For theoria-arm at cc7e414e
    that is kind="verify", name="verify.py" -- NOT a pytest gate.
  * env  = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
           then .update(gates.gate_env(wt))   [prepends wt to PYTHONPATH]
  * cwd  = <wt>/<dir>,  timeout 1800, encoding utf-8 errors replace.
  * gates.run() is deliberately NOT used: it calls gates.sh(), which passes no
    env at all, so it neither sets PYTHONUTF8 nor puts the root on PYTHONPATH.

usage: python agentD_arms.py <outdir> <wt-abspath> <dir> <tag>
"""
import json
import os
import subprocess
import sys


def load_gates(wt):
    mpath = os.path.join(wt, "monitor")
    assert os.path.isdir(mpath), "no monitor/ under %s" % wt
    sys.path.insert(0, mpath)
    for mod in [m for m in list(sys.modules) if m == "gates"]:
        del sys.modules[mod]
    import gates                                                  # noqa: E402
    sys.path.pop(0)
    return gates


def failing_ids(text):
    ids = []
    for ln in text.splitlines():
        if ln.startswith(("FAILED ", "ERROR ")):
            tid = ln.split(None, 1)[1].split(" - ")[0].strip()
            if tid not in ids:
                ids.append(tid)
    return ids


def main():
    outdir, wt, d, tag = (os.path.abspath(sys.argv[1]), sys.argv[2],
                          sys.argv[3], sys.argv[4])
    os.makedirs(outdir, exist_ok=True)
    gates = load_gates(wt)
    row = gates.gate_for(wt, d)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    env.update(gates.gate_env(wt))
    cwd = os.path.join(wt, d)

    rec = {"tag": tag, "worktree": wt, "dir": d,
           "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=wt,
                                  capture_output=True, text=True).stdout.strip(),
           "gate_kind": row["kind"], "gate_name": row["name"],
           "gate_cmd": row["cmd"], "cwd": cwd}

    if row["cmd"] is None:
        rec["gate_rc"] = None
        rec["note"] = "kind=none, nothing to run"
    else:
        p = subprocess.run(row["cmd"], cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800,
                           env=env)
        out = (p.stdout or "") + (p.stderr or "")
        with open(os.path.join(outdir, "%s.gate.txt" % tag), "w",
                  encoding="utf-8", errors="replace") as fh:
            fh.write("tag: %s\nwt: %s\ndir: %s\ncmd: %r\ncwd: %s\nrc: %d\n%s\n%s"
                     % (tag, wt, d, row["cmd"], cwd, p.returncode, "-" * 70, out))
        rec["gate_rc"] = p.returncode
        rec["gate_failing_ids"] = failing_ids(out)
        rec["gate_stages"] = [ln.strip() for ln in out.splitlines()
                              if ln.startswith("== ")][:80]

    tdir = os.path.join(cwd, "tests")
    if os.path.isdir(tdir):
        q = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p",
                            "no:cacheprovider", "-rf", tdir],
                           cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800,
                           env=env)
        qout = (q.stdout or "") + (q.stderr or "")
        with open(os.path.join(outdir, "%s.pytest.txt" % tag), "w",
                  encoding="utf-8", errors="replace") as fh:
            fh.write("rc: %d\n%s\n%s" % (q.returncode, "-" * 70, qout))
        rec["pytest_rc"] = q.returncode
        rec["pytest_failing_ids"] = failing_ids(qout)
        rec["pytest_tail"] = qout.strip().splitlines()[-1:] or []

    with open(os.path.join(outdir, "%s.json" % tag), "w",
              encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2, ensure_ascii=False)
    print(json.dumps(rec, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
