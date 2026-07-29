# -*- coding: utf-8 -*-
"""账号池的阴性样本。

本仓的规矩：**每一道闸门都要有一个能让它变红的输入**，否则那道闸门只是装饰
（20 道闸门里 19 道从没被证明能变红）。轮换器尤其需要——它平时不动，
只在撞限那一刻动一次，而那一刻没人在看。
"""

from __future__ import annotations

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
for path in (HERE, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

import accounts                                                    # noqa: E402


@pytest.fixture
def pool(tmp_path, monkeypatch):
    """两个账号，都已登录、窗口都开着。"""
    cfg = tmp_path / "accounts.json"
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    cfg.write_text(json.dumps({"accounts": {
        "a": {"label": "acct-a", "config_dir": str(a)},
        "b": {"label": "acct-b", "config_dir": str(b)},
    }}), encoding="utf-8")
    monkeypatch.setattr(accounts, "CONFIG", str(cfg))
    monkeypatch.setattr(accounts, "STATE", str(tmp_path / "state.json"))
    monkeypatch.setattr(accounts, "LOG", str(tmp_path / "accounts.log"))
    monkeypatch.setattr(accounts, "login_state", lambda acct: "yes")
    return tmp_path


def test_a_limited_account_is_skipped_and_the_other_is_picked(pool):
    """阴性样本其一：关掉 a，下一次发车必须走 b。"""
    assert accounts.pick("RES-1") == "a"          # a 是研究员的主场
    accounts.mark_limited("a", "2099-01-01T00:00:00Z", "You've hit your session limit")
    assert accounts.window_state("a") == "limited"
    assert accounts.pick("RES-1") == "b"


def test_when_every_account_is_shut_nothing_is_picked(pool):
    """阴性样本其二：两个都关，**必须返回 None**，不许回落到某个默认账号。

    这一条是整套机制里最容易写错的地方——「一个都挑不出来」和「挑第一个」
    在代码里只差一行，而后者会把会话不断喂给一个已经关闭的窗口。
    """
    for acct in ("a", "b"):
        accounts.mark_limited(acct, "2099-01-01T00:00:00Z", "limit")
    assert accounts.pick("RES-1") is None
    assert accounts.pick("W-1") is None


def test_an_unknown_login_is_not_usable(pool, monkeypatch):
    """`unknown` 不是 `yes`。不确定的账号不发车。"""
    monkeypatch.setattr(accounts, "login_state",
                        lambda acct: "unknown" if acct == "a" else "yes")
    assert accounts.pick("RES-1") == "b"
    monkeypatch.setattr(accounts, "login_state", lambda acct: "unknown")
    assert accounts.pick("RES-1") is None


def test_an_unparsable_deadline_is_unknown_not_expired(pool):
    """解析不了的重开时刻是「未知」，不是「已经过去了」。

    反过来写会让一个坏掉的时间戳变成一张永久通行证。
    """
    st = accounts.load_state()
    st["a"] = {"limited_until": "not-a-timestamp"}
    accounts.save_state(st)
    assert accounts.window_state("a") == "unknown"
    assert accounts.pick("RES-1") == "b"


def test_a_corrupt_state_file_stops_dispatch_rather_than_opening_it(pool):
    """状态文件坏了，**谁也不发车**——而不是全都发车。"""
    open(accounts.STATE, "w", encoding="utf-8").write("{ this is not json")
    assert accounts.window_state("a") == "unknown"
    assert accounts.pick("RES-1") is None


def test_no_config_means_no_pool_not_a_default_account(pool, monkeypatch):
    monkeypatch.setattr(accounts, "CONFIG", str(pool / "does-not-exist.json"))
    assert accounts.load_config() == {}
    assert accounts.pick("RES-1") is None


def test_role_home_splits_workers_off_the_researchers_account(pool):
    """一个账号关了整条赛道不该跟着停，所以工人默认落在另一个账号上。"""
    assert accounts.pick("RES-3") == "a"
    assert accounts.pick("OPS-M") == "a"
    assert accounts.pick("W-1660") == "b"
