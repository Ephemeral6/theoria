# -*- coding: utf-8 -*-
"""S38: append-only 探针的实现与它自己写下的意图，只在 master 上一致。

`probe_append_only` 的注释写着判据：「once it is on the mainline it is frozen;
on a branch, fix it until it is right」，还点名 `6dec6f7` 不该计入。但实现从
**HEAD** 的第一父链求和删除行，而在分支上 HEAD 的第一父链就是这条分支自己的
提交——包括未发布的。于是作者每修正一次自己尚未发布的草稿段落，都被记成一次违反。

失败方向这次不是安静的（它是红的），但代价一样实：这个红**会自愈**（合并后
合并提交的 numstat 是净值，于是变绿），所以它教人忽略这条闸；而它把便宜的
错解摆在顺手的位置——去 `BASELINE` 加豁免行数，为一段从未发布的草稿
**永久放宽对已发布内容的守卫**。

实测（`runs/20260730T0410Z-S38/measure.json`，211 条本地分支）：旧判据红 26 条，
新判据红 1 条，25 条假红；而剩下那 1 条正是同一天由完全独立的路径（逐条读 diff
的人工裁决，S36）挑出来的同一条分支。

两个方向的负对照都在本文件里，第一个比第二个重要：
**净删除了已发布行的分支必须仍然红**，否则这次修复就是把闸门拆了。
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import scan                                                     # noqa: E402


def _run(*args, cwd):
    out = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    assert out.returncode == 0, "%s -> %s\n%s" % (args, out.returncode, out.stderr)
    return out.stdout


def _fleet_repo(tmp_path, published_lines):
    """一个带裸 origin 的仓，`PARTNER_SYNC.md` 已发布若干段落。"""
    bare, work = tmp_path / "origin.git", tmp_path / "work"
    _run("git", "init", "--bare", "-b", "master", str(bare), cwd=str(tmp_path))
    _run("git", "init", "-b", "master", str(work), cwd=str(tmp_path))
    w = str(work)
    for k, v in (("user.email", "t@e.com"), ("user.name", "t"),
                 ("commit.gpgsign", "false")):
        _run("git", "config", k, v, cwd=w)
    (work / "PARTNER_SYNC.md").write_text("\n".join(published_lines) + "\n",
                                          encoding="utf-8")
    # 另外三个被看着的文件也要建出来。不建的话「文件不存在」那一支先开火，
    # 判词仍是 risk 但**理由完全是另一件事**——本文件第三个用例第一版就那样
    # 「通过」了状态断言而卡在理由断言上。那一支本身是对的（S28：缺失单列），
    # 而这件事说明**一个只断言 status 的测试会把两种红混为一谈**。
    (work / "arc-recon" / "data").mkdir(parents=True)
    (work / "arc-recon" / "data" / "incidents.jsonl").write_text(
        "{}\n", encoding="utf-8")
    (work / "arc-recon" / "data" / "contamination_log.jsonl").write_text(
        "{}\n", encoding="utf-8")
    (work / "battery").mkdir()
    (work / "battery" / "PREDICTIONS.md").write_text("p\n", encoding="utf-8")
    _run("git", "add", "-A", cwd=w)
    _run("git", "commit", "-m", "published paragraphs", cwd=w)
    _run("git", "remote", "add", "origin", str(bare), cwd=w)
    _run("git", "push", "-u", "origin", "master", cwd=w)
    _run("git", "fetch", "origin", cwd=w)
    return w


def _probe_in(repo, monkeypatch):
    """在 `repo` 里跑这个探针。它按 `HERE` 定位仓库，所以两处都要指过去。"""
    monkeypatch.setattr(scan, "HERE", os.path.join(repo, "monitor"))
    monkeypatch.setattr(scan, "ROOT", repo)
    monkeypatch.setattr(scan, "rel", lambda *p: os.path.join(repo, *p))
    monkeypatch.setattr(scan, "exists",
                        lambda p: os.path.exists(os.path.join(repo, p)))
    monkeypatch.setattr(
        scan, "git_or_none",
        lambda *a: (lambda o: o.stdout if o.returncode == 0 else None)(
            subprocess.run(["git", "-C", repo] + list(a), capture_output=True,
                           text=True, encoding="utf-8", errors="replace")))
    return scan.probe_append_only()


def test_a_branch_that_deletes_published_lines_is_still_red(tmp_path,
                                                            monkeypatch):
    """**最重要的一个。** 这次修复不许把闸门拆了：一条净删除了**已发布**行的
    分支必须红，而且在它合并**之前**就红。"""
    w = _fleet_repo(tmp_path, ["## [t] one", "state: a", "## [t] two",
                               "state: b", "## [t] three", "state: c"])
    _run("git", "checkout", "-q", "-b", "agent/vandal", cwd=w)
    p = os.path.join(w, "PARTNER_SYNC.md")
    # 删掉一段**已发布**的段落。
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("## [t] one\nstate: a\n## [t] three\nstate: c\n")
    _run("git", "commit", "-am", "quietly drop a published paragraph", cwd=w)

    r = _probe_in(w, monkeypatch)
    assert r["status"] == "risk", r["detail"]
    assert "PARTNER_SYNC.md" in r["detail"]
    assert "本分支净删除 2 行" in r["detail"], r["detail"]


def test_a_branch_correcting_its_own_unpublished_paragraph_is_green(tmp_path,
                                                                    monkeypatch):
    """另一个方向，S35 的形状：作者在分支上加了一段，然后在后续提交里改它。
    那段从未发布，所以按规则不是违反——旧实现红，新实现绿。"""
    w = _fleet_repo(tmp_path, ["## [t] one", "state: a"])
    _run("git", "checkout", "-q", "-b", "agent/author", cwd=w)
    p = os.path.join(w, "PARTNER_SYNC.md")
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("## [t] mine\nstate: first draft\n")
    _run("git", "commit", "-am", "add my paragraph", cwd=w)
    # 现在改自己那一段三次，每次都是一次删除+一次新增。
    for n in ("second", "third", "final"):
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("## [t] one\nstate: a\n## [t] mine\nstate: %s\n" % n)
        _run("git", "commit", "-am", "correct my own draft (%s)" % n, cwd=w)

    # 旧判据会看到 3 行删除（分支自己第一父链求和）。
    old = _run("git", "log", "--first-parent", "--numstat", "--format=%h",
               "HEAD", "--", "PARTNER_SYNC.md", cwd=w)
    old_dels = sum(int(l.split("\t")[1]) for l in old.splitlines()
                   if len(l.split("\t")) == 3 and l.split("\t")[1].isdigit())
    assert old_dels == 3, ("fixture did not reproduce the false red: %d"
                           % old_dels)

    r = _probe_in(w, monkeypatch)
    assert r["status"] == "green", \
        ("an author correcting an unpublished draft was called a violation: %s"
         % r["detail"])


def test_the_stated_intent_and_the_code_agree_on_the_mainline_too(tmp_path,
                                                                  monkeypatch):
    """回归：修完之后 master 上的行为不许变。合并提交的 first-parent numstat
    是净变化，所以分支内的来回本来就不出现——这条钉住新锚点没有把
    「已发布的删除」这一半弄丢。"""
    w = _fleet_repo(tmp_path, ["## [t] one", "state: a", "note: keep me"])
    _run("git", "checkout", "-q", "-b", "agent/x", cwd=w)
    p = os.path.join(w, "PARTNER_SYNC.md")
    # **两行**，不是一行。`BASELINE["PARTNER_SYNC.md"] = 1` 是一次已裁决的
    # 主线自我订正，所以删一行等于豁免额、判词仍是 green——这个用例第一版就
    # 删了一行然后断言 risk，于是它测的是豁免额而不是「主线删除还算不算」。
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("## [t] one\nstate: CORRECTED ON THE MAINLINE\n")
    _run("git", "commit", "-am", "edit two published lines", cwd=w)
    _run("git", "checkout", "-q", "master", cwd=w)
    _run("git", "merge", "--no-ff", "-m", "merge the edit", "agent/x", cwd=w)
    _run("git", "push", "origin", "master", cwd=w)
    _run("git", "fetch", "origin", cwd=w)

    r = _probe_in(w, monkeypatch)
    assert r["status"] == "risk", \
        "a deletion that reached the mainline stopped counting: %s" % r["detail"]
    assert "已发布删除 2 行" in r["detail"], r["detail"]
