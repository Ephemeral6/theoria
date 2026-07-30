# -*- coding: utf-8 -*-
"""哪些提交只存在于这一块磁盘上。

    python monitor/orphan_commits.py            # 普查，人读
    python monitor/orphan_commits.py --json <p> # 落盘，utf-8/LF

## 为什么需要它

`ci_merge` 枚举的是 `git branch -r --list origin/agent/*`，判祖先用的是
`origin/master`（`ci_merge.py:450` / `:454`）。**一条没推上去的分支对它不是红，
是不存在**——不是「合并失败」，而是从来没有进入过候选集合。板上、总线上、
`ops-status` 上都没有任何一处显示「有已完成的工作尚未推送」：心跳的 note 是
自报的散文，探针不读它。

Phase 4 的释出清单发布的是 master 上被跟踪的文件。**没推上去的工作在释出时
等于没做过**，而它在板上可能已经记为 done。

S35 的作者（我）在做那件活时自己走到了同一个位置：上一世死在对抗性复核与 push
之间，`agent/s28-no-third-value-in-the-monitor` 的两个提交因此在盘上待了一夜。

## 判据：两个条件的交集，两个都必要

**一、内容是新的**（patch-id，不是文件 diff）。三点 diff 会把「内容已由别的
分支落地」也算成未推送——那个数是虚高的。`git cherry origin/master <branch>`
逐提交比 patch-id：`+` 是上游没有等价物的，`-` 是有的。被 cherry-pick 过、
被 rebase 过、被另一条分支带上去的，都落在 `-` 里。

**二、这块盘之外没有拷贝**。`git rev-list --branches --not --remotes` 给出
「本地分支上、任何远端引用都到不了」的提交。**光有条件一不够**：一条推上去了
但还没被合并的分支，它的提交同样是 `+`，而那些提交已经在 origin 上、
`ci_merge` 看得见它们——那不是本探针要报的东西。

反过来光有条件二也不够：一条被 `ci_merge` 合并后**删掉了远端分支**的分支，
本地那几个提交从任何远端引用都到不了（合并进去的是 merge 而不是它们本身
——取决于合并方式），可它们的内容已经在 master 上。条件一把这一类滤掉。

所以只有**两个条件同时成立**的提交才是「只在这块盘上，且内容没有别处的拷贝」。

## 已知边界

远端引用是**上次 `git fetch` 时**的快照。判据只在读它的那一刻成立
（S35 为这句话付了两次账：一次是本地 master 落后 16 个提交，
一次是在过期快照上判断了「未发布」）。所以 `census()` 报出
`fetch_age_min`，而调用方可以要求它先 fetch。
"""

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: 上游锚点。`ci_merge` 用的就是这个，本探针必须用同一个，否则两边对
#: 「已经上去了吗」会给出两个答案——那正是 S35 修的那一族缺陷。
UPSTREAM = "origin/master"


def git(*args, repo=None):
    out = subprocess.run(["git", "-C", repo or ROOT] + list(args),
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return out


def _lines(out):
    return [l for l in (out.stdout or "").splitlines() if l.strip()]


def fetch_age_min(repo=None):
    """距上次 `git fetch` 多少分钟。判据的时效性要跟着判据一起报出来。"""
    for name in ("FETCH_HEAD", os.path.join("refs", "remotes", "origin", "master")):
        p = os.path.join(repo or ROOT, ".git", name)
        if os.path.exists(p):
            return (time.time() - os.path.getmtime(p)) / 60.0
    return None


def disk_only_commits(repo=None):
    """本地分支上、任何远端引用都到不了的提交（条件二）。"""
    out = git("rev-list", "--branches", "--not", "--remotes", repo=repo)
    if out.returncode != 0:
        return None
    return set(_lines(out))


def census(repo=None, prefix="refs/heads/"):
    """每条本地分支有几个「只在这块盘上、且内容没有别处拷贝」的提交。

    返回 `None` 表示**问不出来**（没有 `origin/master`、git 报错）。
    这是刻意的第三个值：0 是「查过了，没有孤立提交」，`None` 是「查都没查成」。
    把后者写成 0 就是给一块查不了的盘发一张健康证明，而这个仓库为那个形状
    已经付过账（S28/S30：`dels = 0` 当成「append-only 规则完好」）。
    """
    if git("rev-parse", "--verify", "--quiet", UPSTREAM, repo=repo).returncode != 0:
        return None
    disk_only = disk_only_commits(repo=repo)
    if disk_only is None:
        return None
    refs = _lines(git("for-each-ref", "--format=%(refname:short)", prefix,
                      repo=repo))
    rows = []
    for b in refs:
        cherry = git("cherry", UPSTREAM, b, repo=repo)
        if cherry.returncode != 0:
            # 单条分支问不出来不该让整份普查变成 None——但它也不是 0。
            rows.append({"branch": b, "orphans": None, "commits": [],
                         "note": "git cherry failed"})
            continue
        novel = [l.split()[1] for l in _lines(cherry) if l.startswith("+")]
        stuck = [c for c in novel if c in disk_only]
        if stuck:
            rows.append({"branch": b, "orphans": len(stuck), "commits": stuck,
                         "novel_total": len(novel),
                         "on_a_remote": len(novel) - len(stuck)})
    rows.sort(key=lambda r: (-(r["orphans"] or 0), r["branch"]))
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "upstream": UPSTREAM,
        "fetch_age_min": fetch_age_min(repo=repo),
        "branches_at_risk": len(rows),
        "orphan_commits": sum(r["orphans"] or 0 for r in rows),
        "unreadable_branches": [r["branch"] for r in rows
                                if r["orphans"] is None],
        "rows": rows,
    }


#: 裁决簿。一条分支被读过、判过之后写在这里，**带理由带签名**。
#:
#: 为什么要有这个文件（要求 3：这个状态要有名字和出口）：光把 N 印出来，
#: 下一世看到的还是同一个 N，而它读不出「这 34 个里哪些已经有人看过了」。
#: S35 的教训一字不改地适用——**印出来不算结掉**，那件活当时已经被印了四次。
#:
#: 判词只有四个，刻意少：
#:   push          真活、没交付过，该推上去
#:   superseded    内容实际上已经在 origin/master 上，留着无害
#:   abandoned     没价值的实验
#:   deliberate-local  故意只留在本地（例如一次被放弃的历史重写留作物证）
#: `needs-owner` **不是**判词：它是「还没判」，所以它不进这个文件。
DISPOSITIONS = os.path.join(HERE, "orphan_dispositions.json")

#: 判词 → 这条分支还算不算「有工作正在流失」。
#: `push` 判完仍然算——判词不是动作，推上去才是。
STILL_AT_RISK = {"push": True, "superseded": False,
                 "abandoned": False, "deliberate-local": False}


def dispositions(path=None):
    try:
        raw = json.load(open(path or DISPOSITIONS, encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for row in raw.get("branches", []):
        # 判词必须认得出来。认不出的**不算判过**（fail-closed）——
        # 一个打错的判词不该把一条分支悄悄移出待办，那是本仓库
        # `claim_set()` 曾经犯过的错（INC-006a：认不出的一律进最强的桶）。
        if row.get("disposition") in STILL_AT_RISK and row.get("why", "").strip():
            out[row["branch"]] = row
    return out


def status(repo=None, disp_path=None):
    """探针判词。`scan.py` 用的就是这个。

    三个值，不是两个（本仓库反复付账的那条）：

    * `missing` —— **问不出来**。没有 `origin/master`、git 报错。这不是绿，
      也不是红：它是「本轮无法断言」，而把它写成绿就是给一块查不了的盘
      发健康证明。
    * `risk` —— 有孤立提交，**且至少一条分支还没被判过**，或判词是 `push`
      而它还没被推上去。这是要有人动手的那一档。
    * `green` —— 一个孤立提交都没有。**只有这一种情况是绿**（要求 1）。

    判过之后仍有孤立提交时，判词是 `partial`：不是绿（工作确实还只在一块盘上），
    但也不该和「没人看过」长得一样——那正是让 34 这个数字在页面上待了一夜
    而无人动手的原因。

    **用 `partial` 而不是新造一个 `note`。** 初版造了 `note`，而
    `scan.STATUS_ORDER = ["green","partial","risk","blocked","missing"]`
    与 `spec.STATUS_SCORE` 都不认识它：`STATUS_SCORE.get(s, 0)` 会把它算成
    0 分，而渲染那一段按 `STATUS_ORDER` 遍历，于是这一档**会从页面上消失**。
    一个探针发明一个渲染层不认识的值，正是本仓库反复付账的那一族
    （「第三个值」），而这次的失败方向是安静的那一侧。
    """
    c = census(repo=repo)
    if c is None:
        return {"status": "missing", "census": None,
                "detail": "问不出孤立提交（没有 %s，或 git 报错）；"
                          "本轮无法断言这块盘上没有只此一份的工作。" % UPSTREAM}
    judged = dispositions(disp_path)
    unjudged = [r["branch"] for r in c["rows"] if r["branch"] not in judged]
    to_push = [b for b, row in judged.items()
               if STILL_AT_RISK.get(row["disposition"])
               and any(r["branch"] == b for r in c["rows"])]
    c = dict(c, unjudged=unjudged, awaiting_push=sorted(to_push),
             judged=sorted(judged))
    if not c["orphan_commits"] and not c["unreadable_branches"]:
        return {"status": "green", "census": c,
                "detail": "没有只存在于本盘的提交（%d 条分支全部有远端拷贝或"
                          "内容已在 %s 上）。" % (len(judged), UPSTREAM)}
    if unjudged or to_push:
        return {"status": "risk", "census": c,
                "detail": "孤立提交 %d 个，分布在 %d 条分支上；"
                          "未裁决 %d 条（%s），已判 push 但还没推 %d 条（%s）。"
                          "对 ci_merge 而言这些工作不是红，是**不存在**。"
                          % (c["orphan_commits"], c["branches_at_risk"],
                             len(unjudged), "、".join(unjudged[:4]) or "无",
                             len(to_push), "、".join(to_push[:4]) or "无")}
    return {"status": "partial", "census": c,
            "detail": "孤立提交 %d 个，分布在 %d 条分支上，**每一条都已裁决**"
                      "（superseded/abandoned/deliberate-local），无人等着推。"
                      "仍然不是绿：工作确实只在这一块盘上。"
                      % (c["orphan_commits"], c["branches_at_risk"])}


def main():
    argv = sys.argv[1:]
    repo = None
    if argv and not argv[0].startswith("--"):
        repo = argv[0]
    c = census(repo=repo)
    if c is None:
        print("ORPHAN-CENSUS-UNREADABLE 问不出来（没有 %s，或 git 报错）。"
              "这**不是** 0。" % UPSTREAM)
        return 3
    if "--json" in argv:
        i = argv.index("--json") + 1
        path = argv[i] if i < len(argv) else ""
        if not path:
            print("usage: orphan_commits.py [<repo>] [--json <path>]")
            return 2
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(c, indent=2, ensure_ascii=False) + "\n")
        print("# JSON -> %s (utf-8, LF)" % path)
    age = c["fetch_age_min"]
    print("orphan commits: %d across %d branches  (upstream=%s, fetch %s)"
          % (c["orphan_commits"], c["branches_at_risk"], UPSTREAM,
             "age unknown" if age is None else "%.0f min ago" % age))
    for r in c["rows"]:
        print("  %-52s orphans=%s  (novel=%s, already on a remote=%s)"
              % (r["branch"], r["orphans"], r.get("novel_total"),
                 r.get("on_a_remote")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
