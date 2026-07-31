# -*- coding: utf-8 -*-
"""S38 要求 1：先量。有多少条本地分支会因为「作者修正自己尚未发布的段落」而红。

旧判据：`git log --first-parent --numstat <HEAD> -- <path>` 求和删除行。
在 master 上跑对，在分支上跑会把分支自己那些**未发布**的提交也算进去。

新判据（本条目要落的）：
* 已发布的删除 = 同一个求和，但锚在 `origin/master` 上（`ci_merge` 判祖先用的
  就是它），所以只数主线上真的发生过的删除；
* 分支自己的贡献 = `merge-base(origin/master, HEAD)..HEAD` 的净 diff。
  **必须用 merge-base 而不是两点 `origin/master..HEAD`**：分支基线落后时，
  两点 diff 会把「基线之后别人加的行」全部报成本分支删的
  （S35 实测：5 增 33 删，33 行一个字都不是我删的）。
"""
import os, subprocess, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PATH = "PARTNER_SYNC.md"
BASELINE = 1


def git(*a):
    return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def dels_first_parent(ref):
    out = git("log", "--first-parent", "--numstat", "--format=%h", ref, "--", PATH)
    n = 0
    for line in (out.stdout or "").splitlines():
        p = line.split("\t")
        if len(p) == 3 and p[1].isdigit():
            n += int(p[1])
    return n


def branch_own_dels(ref):
    mb = git("merge-base", "origin/master", ref).stdout.strip()
    if not mb:
        return None
    out = git("diff", "--numstat", "%s..%s" % (mb, ref), "--", PATH)
    for line in (out.stdout or "").splitlines():
        p = line.split("\t")
        if len(p) == 3 and p[1].isdigit():
            return int(p[1])
    return 0


def main():
    published = dels_first_parent("origin/master")
    branches = [l.strip() for l in git(
        "for-each-ref", "--format=%(refname:short)", "refs/heads/").stdout.splitlines()
        if l.strip()]
    rows = []
    for b in branches:
        old = dels_first_parent(b)
        own = branch_own_dels(b)
        rows.append({"branch": b, "old_criterion_dels": old,
                     "old_red": old > BASELINE,
                     "branch_own_dels": own,
                     "new_red": (published + (own or 0)) > BASELINE})
    false_reds = [r for r in rows if r["old_red"] and not r["new_red"]]
    out = {"path": PATH, "baseline": BASELINE,
           "published_dels_on_origin_master": published,
           "branches_examined": len(rows),
           "red_under_old_criterion": sum(1 for r in rows if r["old_red"]),
           "red_under_new_criterion": sum(1 for r in rows if r["new_red"]),
           "false_reds": [r["branch"] for r in false_reds],
           "rows": [r for r in rows if r["old_red"] or r["new_red"]]}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    p = os.path.join(os.path.dirname(__file__), "measure.json")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
