"""ADVERSARIAL PROBE -- temporary, to be deleted. Redacts sealed ids in ALL output.

Never executes any command. Only calls classify_command().
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import local_engine_guard as G

IDX = G.piles_index()
SEALED = IDX["sealed"]
DEV = IDX["dev"]
# a stable, arbitrary sealed pick -- never printed
S_FULL = SEALED[0]
S_PRE = G._prefix(S_FULL)
D_FULL = DEV[0]          # ar25-0c556536
D_PRE = G._prefix(D_FULL)


def red(s):
    """Redact every sealed full id and prefix from a string."""
    out = str(s)
    for g in SEALED:
        out = out.replace(g, "<SEALED-ID>").replace(g.upper(), "<SEALED-ID>")
        p = G._prefix(g)
        out = out.replace(p, "<SP>").replace(p.upper(), "<SP>")
    return out


def show(label, command):
    r = G.classify_command(command)
    reason = r["reasons"][0] if r["reasons"] else ""
    print("%-46s %-16s | %s" % (label, r["verdict"], red(reason)[:88]))
    return r["verdict"]


if __name__ == "__main__":
    print("dev pick: %s (prefix %s)   sealed pick: <SEALED-ID> (<SP>)" % (D_FULL, D_PRE))
    print("sealed count %d, dev count %d" % (len(SEALED), len(DEV)))
