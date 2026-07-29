"""Dump the SAS+ variable list a task translates to, so a pattern can be named
by meaning rather than by index and applied to two different tasks."""
import os, subprocess, sys, tempfile, json
import run as R


def translate(domain, problem):
    tmp = tempfile.mkdtemp(prefix="e7sas")
    cmd = [sys.executable, R.FD, "--translate", domain, problem]
    subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, check=True)
    with open(os.path.join(tmp, "output.sas"), encoding="utf-8") as fh:
        text = fh.read()
    return text


def variables(sas_text):
    lines = sas_text.splitlines()
    out, i = [], 0
    while i < len(lines):
        if lines[i] == "begin_variable":
            name = lines[i + 1]
            n = int(lines[i + 3])
            vals = lines[i + 4:i + 4 + n]
            out.append({"index": len(out), "name": name, "values": vals})
            i += 4 + n
        i += 1
    return out
