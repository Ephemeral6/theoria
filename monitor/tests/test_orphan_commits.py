# -*- coding: utf-8 -*-
"""S36: 41 个提交只存在于这一块磁盘上，而板上没有任何一处显示这件事。

`ci_merge` 枚举 `origin/agent/*` 并拿 `origin/master` 判祖先
（`ci_merge.py:450` / `:454`）。**一条没推上去的分支对它不是红，是不存在。**
心跳的 note 是自报的散文，探针不读它；`done/` 里可能已经记着这件活。

这些测试建**真的** git 仓库（`git init` + 一个裸仓当 origin），因为要测的东西
就是 git 的可达性与 patch-id 语义。假造一层 git 的壳去测对 git 的判断，
测到的是那层壳。全部离线、零网络、零 API。

要求 4 说两个方向都要有：
* 当前这些提交存在时必须**红**（`test_a_repo_with_unpushed_work_is_red`）;
* 全部推送干净时必须**绿**（`test_a_repo_with_everything_pushed_is_green`）。
再加最要紧的第三个：**内容已在上游、只是 patch-id 不同**的分支不许算进去
（`test_content_already_upstream_does_not_count`）——那正是条目里写明
「不用文件 diff，用 patch-id」要防的虚高。
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import orphan_commits as oc                                     # noqa: E402


def _run(*args, cwd):
    out = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    assert out.returncode == 0, "%s -> %s\n%s" % (args, out.returncode,
                                                  out.stderr)
    return out.stdout


def _repo(tmp_path):
    """一个带裸 origin 的工作仓，master 已推送。"""
    bare = tmp_path / "origin.git"
    work = tmp_path / "work"
    _run("git", "init", "--bare", "-b", "master", str(bare), cwd=str(tmp_path))
    _run("git", "init", "-b", "master", str(work), cwd=str(tmp_path))
    w = str(work)
    for k, v in (("user.email", "t@example.com"), ("user.name", "t"),
                 ("commit.gpgsign", "false")):
        _run("git", "config", k, v, cwd=w)
    (work / "a.txt").write_text("one\n", encoding="utf-8")
    _run("git", "add", "a.txt", cwd=w)
    _run("git", "commit", "-m", "base", cwd=w)
    _run("git", "remote", "add", "origin", str(bare), cwd=w)
    _run("git", "push", "-u", "origin", "master", cwd=w)
    return w


def _commit(work, branch, fname, text, msg):
    _run("git", "checkout", "-q", "-B", branch, cwd=work)
    with open(os.path.join(work, fname), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(text)
    _run("git", "add", fname, cwd=work)
    _run("git", "commit", "-m", msg, cwd=work)
    return _run("git", "rev-parse", "HEAD", cwd=work).strip()


def test_a_repo_with_everything_pushed_is_green(tmp_path):
    """阴性对照，绿的那一侧。每条分支都有远端拷贝时，判词必须是 green ——
    否则这个探针只是在报「有分支」，那谁都会。"""
    w = _repo(tmp_path)
    _commit(w, "agent/x", "x.txt", "x\n", "x")
    _run("git", "push", "-u", "origin", "agent/x", cwd=w)
    _run("git", "checkout", "-q", "master", cwd=w)

    st = oc.status(repo=w, disp_path=os.path.join(w, "nope.json"))
    assert st["status"] == "green", st["detail"]
    assert st["census"]["orphan_commits"] == 0


def test_a_repo_with_unpushed_work_is_red(tmp_path):
    """阴性对照，红的那一侧。这是**当前这块盘的形状**：分支从未推送，
    提交内容上游没有。"""
    w = _repo(tmp_path)
    sha = _commit(w, "agent/lost", "lost.txt", "work nobody has\n", "real work")
    _run("git", "checkout", "-q", "master", cwd=w)

    st = oc.status(repo=w, disp_path=os.path.join(w, "nope.json"))
    assert st["status"] == "risk", st["detail"]
    assert st["census"]["orphan_commits"] == 1
    assert st["census"]["branches_at_risk"] == 1
    row = st["census"]["rows"][0]
    assert row["branch"] == "agent/lost"
    assert sha in row["commits"], "reported a count without the commit ids"
    assert "agent/lost" in st["census"]["unjudged"]


def test_content_already_upstream_does_not_count(tmp_path):
    """**要求 2 的判据，写成测试。** 一条分支的提交已经被别的路径带上了
    上游（cherry-pick / rebase / 另一条分支交付），patch-id 相同而 sha 不同。
    用三点 diff 数会把它算成未推送——条目说那个数是虚高的，这里钉住它。"""
    w = _repo(tmp_path)
    _commit(w, "agent/dup", "same.txt", "identical content\n", "the work")
    # 上游用**另一个 sha** 拿到同样的内容。中间那个提交是必要的：没有它，
    # cherry-pick 就是一次 fast-forward，sha 一模一样，这个测试于是什么也
    # 没测——本文件最后那句断言就是为抓这件事写的，而它确实抓到了一次。
    _run("git", "checkout", "-q", "master", cwd=w)
    _commit(w, "master", "unrelated.txt", "meanwhile\n", "unrelated")
    _run("git", "cherry-pick", "agent/dup", cwd=w)
    _run("git", "push", "origin", "master", cwd=w)

    st = oc.status(repo=w, disp_path=os.path.join(w, "nope.json"))
    assert st["status"] == "green", \
        ("content already upstream was counted as work at risk: %s"
         % st["detail"])
    # 而 sha 确实不同——否则这个测试什么也没测。
    tip = _run("git", "rev-parse", "agent/dup", cwd=w).strip()
    head = _run("git", "rev-parse", "master", cwd=w).strip()
    assert tip != head, "cherry-pick produced the same sha; test is vacuous"


def test_pushed_but_unmerged_is_not_at_risk(tmp_path):
    """第二个方向的混淆：推上去了、还没合并。那些提交在上游没有等价物
    （条件一成立），但 origin 上有拷贝（条件二不成立），`ci_merge` 看得见
    它们。只查 patch-id 的写法会把这一类也报成流失。"""
    w = _repo(tmp_path)
    _commit(w, "agent/waiting", "w.txt", "queued\n", "queued work")
    _run("git", "push", "-u", "origin", "agent/waiting", cwd=w)
    _run("git", "checkout", "-q", "master", cwd=w)

    st = oc.status(repo=w, disp_path=os.path.join(w, "nope.json"))
    assert st["status"] == "green", \
        "work that is on origin awaiting merge was called at risk: %s" % st["detail"]


def test_a_repo_without_an_upstream_is_missing_not_green(tmp_path):
    """第三个值。没有 `origin/master` 时判不了——而 `missing` 不是 `green`。
    把它写成绿就是给一块查不了的盘发健康证明，本仓库为这个形状付过账
    （S28/S30：`dels = 0` 被当成「append-only 规则完好」）。"""
    work = tmp_path / "solo"
    _run("git", "init", "-b", "master", str(work), cwd=str(tmp_path))
    w = str(work)
    for k, v in (("user.email", "t@e.com"), ("user.name", "t"),
                 ("commit.gpgsign", "false")):
        _run("git", "config", k, v, cwd=w)
    (work / "a.txt").write_text("one\n", encoding="utf-8")
    _run("git", "add", "a.txt", cwd=w)
    _run("git", "commit", "-m", "base", cwd=w)

    st = oc.status(repo=w, disp_path=os.path.join(w, "nope.json"))
    assert st["status"] == "missing", st["detail"]
    assert st["census"] is None
    assert "无法断言" in st["detail"]


def test_a_disposition_moves_a_branch_out_of_unjudged_but_not_to_green(tmp_path):
    """要求 3：这个状态要有名字和出口。判过之后它不再是「没人看过」，
    但**仍然不是绿**——工作确实还只在一块盘上。这两件事要分得开，
    否则一份裁决簿就变成了一块消音板。"""
    w = _repo(tmp_path)
    _commit(w, "agent/judged", "j.txt", "experiment\n", "an experiment")
    _run("git", "checkout", "-q", "master", cwd=w)
    disp = os.path.join(w, "disp.json")
    with open(disp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"branches": [{"branch": "agent/judged",
                                 "disposition": "abandoned",
                                 "why": "read the diff: a dead end",
                                 "by": "RES-4"}]}, fh)

    st = oc.status(repo=w, disp_path=disp)
    assert st["status"] == "partial", st["detail"]
    # 用的必须是渲染层认识的那个词。发明一个新值会让这一档从页面上消失
    # （`STATUS_ORDER` 遍历 + `STATUS_SCORE.get(s, 0)`），而那是安静的失败方向。
    import scan, spec
    assert st["status"] in scan.STATUS_ORDER
    assert st["status"] in spec.STATUS_SCORE
    assert st["census"]["unjudged"] == []
    assert st["status"] != "green", "a ruling silenced work that is still one copy"
    assert "已裁决" in st["detail"]


def test_a_push_ruling_stays_red_until_it_is_actually_pushed(tmp_path):
    """`push` 是判词里唯一**还没做完**的那个。判它 push 而没推，
    必须继续红：裁决不是动作。S35 的同一句话——印出来不算结掉。"""
    w = _repo(tmp_path)
    _commit(w, "agent/todo", "t.txt", "real\n", "real work")
    _run("git", "checkout", "-q", "master", cwd=w)
    disp = os.path.join(w, "disp.json")
    with open(disp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"branches": [{"branch": "agent/todo",
                                 "disposition": "push",
                                 "why": "undelivered work, owner is RES-4",
                                 "by": "RES-4"}]}, fh)

    st = oc.status(repo=w, disp_path=disp)
    assert st["status"] == "risk", st["detail"]
    assert st["census"]["awaiting_push"] == ["agent/todo"]

    # 推上去之后才绿。
    _run("git", "push", "-u", "origin", "agent/todo", cwd=w)
    assert oc.status(repo=w, disp_path=disp)["status"] == "green"


def test_an_unrecognised_disposition_does_not_count_as_judged(tmp_path):
    """fail-closed。判词打错了字不该把一条分支悄悄移出待办——
    本仓库正为这个形状开过事故单（INC-006a：`claim_set()` 认不出的值
    一律落进最干净的那一档，头条数字纹丝不动）。"""
    w = _repo(tmp_path)
    _commit(w, "agent/typo", "t.txt", "x\n", "x")
    _run("git", "checkout", "-q", "master", cwd=w)
    disp = os.path.join(w, "disp.json")
    for row in ({"branch": "agent/typo", "disposition": "abandonned",
                 "why": "typo in the verdict"},
                {"branch": "agent/typo", "disposition": "abandoned",
                 "why": "   "}):
        with open(disp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"branches": [row]}, fh)
        st = oc.status(repo=w, disp_path=disp)
        assert st["status"] == "risk", (row, st["detail"])
        assert "agent/typo" in st["census"]["unjudged"], row


def test_the_census_reports_how_stale_its_evidence_is(tmp_path):
    """远端引用是上次 fetch 的快照，判据只在读它的那一刻成立。
    S35 为这句话付了两次账（本地 master 落后 16 个提交；在过期快照上
    判断了「未发布」），所以时效性要跟着判据一起报出来。"""
    w = _repo(tmp_path)
    st = oc.status(repo=w, disp_path=os.path.join(w, "nope.json"))
    assert "fetch_age_min" in st["census"]
    assert st["census"]["fetch_age_min"] is not None
