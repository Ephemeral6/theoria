"""Generate `freeze/ENGINE_MANIFEST.md` — freeze-list item 5, 引擎清单与版本.

## Why this exists, and why it is a program

`Theoria.md:368`'s fifth item is **引擎清单与版本**.  Until this file there was
no engine manifest in the freeze kit at all: the roster lived as prose in
`engine-rig/STATUS.md`, the capability and boundary table lived in
`engine-rig/ENGINE_TABLE.md`, and nothing anywhere carried a version.  So the
one item whose name is literally "list *and versions*" had a list in two places
and versions in none.

It is a program for the same reason `build_manifest.py` is one, and that file's
docstring makes the argument in full: a hand-copied hash table in a freeze
manifest is a *false* statement about finished work, and false in the direction
of claiming more.  Nineteen of thirty-three hashes in an earlier hand-written
draft were wrong within a day.

The division of labour with `build_manifest.py` is deliberate.  That file pins
all thirteen items coarsely, one content-sha256 per path.  This one opens item 5
alone: per package, per file, the enum tag the package actually declares, the
tests that actually reference it, and the milestone tag that is supposed to
version it.  The two are joined by a cross-check — this file recomputes
`build_manifest.hash_path("engine-rig/engines")` and publishes it, so a drift
that one manifest sees and the other does not is impossible by construction.

## What is derived and what is judgement

Derived from git at HEAD, never typed: every sha1; the file lists; the `ENGINE`
and `PRODUCER` constants (parsed out of each `__init__.py`'s **blob**, not read
from an import); the version-string scan; which test files reference which
package; the `def test_` counts; the milestone-tag comparison; the census of the
committed candidate stream.

Judgement, held as literals below so it can be argued with: the one-line
statement of what each engine proposes or certifies, and each standing caveat.
`ENGINE_TABLE.md` sets the same precedent — its boundary prose lives in
`tools/engine_table.py`, not in the table it writes.

## Hash discipline — binding, from `MANIFEST_DRAFT.md` 哈希纪律

**Every hash here is a git tree/blob sha1 taken with `git rev-parse HEAD:<path>`.
No hash is taken from a worktree file.**  The repository root has no
`text`/`eol` `.gitattributes` rule, and the measured consequence is that
`CONTRACTS/dsl_grammar_v0.2.md` is CRLF in one checkout and LF in another — so a
worktree hash does not reproduce across checkouts, and the failure mode is the
worst available: `--verify` would go red on a tree that is in fact identical,
and whoever hit that would start regenerating the manifest to make it green.

`engine-rig/.gitattributes` pins LF, so this subtree happens to be safe from
that particular accident.  The rule is followed anyway: a manifest that is
correct because of a property of one subdirectory is correct by luck.

`git rev-parse HEAD:<path>` also reads **HEAD, not the worktree**, so these
hashes describe the commit even if the checkout is dirty.  That is a feature and
a trap, so the dirty state of `engine-rig/` is reported on stdout — not written
into the file, where it would make an unrelated edit look like hash drift.

## Usage

    python freeze/build_engine_manifest.py            # write freeze/ENGINE_MANIFEST.md
    python freeze/build_engine_manifest.py --verify    # exit 1 on drift, print every drifted row

`--verify` is what belongs in a gate.  It answers "does this manifest still
describe this tree", which is the only question the file is for.
"""

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "ENGINE_MANIFEST.md")

# Sibling reuse rather than a second copy of the same helpers.  `git()` and
# `hash_path()` are `build_manifest.py`'s; importing them is what makes the
# cross-check in section 6 a real join instead of two numbers that happen to
# look alike.
sys.path.insert(0, HERE)
from build_manifest import git, hash_path            # noqa: E402

ENGINES_DIR = "engine-rig/engines"

#: The roster, keyed on the **package path**, in `engines/` listing order.
#:
#: Keyed on the path and not on the `ENGINE` constant, because two of these
#: eight packages declare another package's name (D-018) and a manifest keyed on
#: the enum would silently merge eight rows into six.  `enum_tag` and `producer`
#: are read out of the blob at generation time; they are NOT listed here, so
#: this table cannot disagree with the code about them.
#:
#: `milestone` is the tag `engine-rig/STATUS.md` names for the package.  It is
#: quoted from that file and then *checked*: the generator compares the tag's
#: tree against HEAD's, so a tag that no longer describes the code says so.
#:
#: `role` and `caveat` are judgements.  Every number in a caveat is quoted from
#: `engine-rig/ENGINE_TABLE.md`, which is generated, probe-backed and guarded by
#: `engine-rig/tests/test_engine_table.py` — so the numbers have an owner that
#: is not this file.
ROSTER = [
    {
        "pkg": "mdl_segmenter",
        "milestone": "engine-rig-m2-mdl",
        "role": "提出 object_hypothesis：轨迹 → 对象与事件，按比特计价，"
                "描述最短者胜。不证明任何东西。",
        "caveat":
            "**几何精确不等于对象正确。** 像素几何是精确的（506,302 格 0 错），"
            "但*分解*在 300 个世界里错了 127 个（最坏 4 个真实对象报 40 条轨迹），"
            "只有 173/300 逐帧与 ground truth 相符；"
            "`masks_partition_the_foreground` 在全部世界通过，因为"
            "「动体与障碍粘成一团」仍是一个合法划分。"
            "非均匀对象的逐格颜色根本不发布：18,118 格（3.5785 %）不可恢复。"
            "18 个发布字段里有 8 个没有任何不变量断言。",
    },
    {
        "pkg": "cegis_miner",
        "milestone": "engine-rig-m3-cegis",
        "role": "提出 rule_hypothesis：对精确账本做反例引导的带卫式规则合成，"
                "并给出证据尚不能分离的最小卫前沿。",
        "caveat":
            "**提升规则（lifted）是边界。** 149 条里 104 条带的卫是 "
            "`[\"act==?dir\"]`，**91/149 在承诺的移动并未发生的转移上开火**（342 行），"
            "**131/149** 发布的 `applicable` 不能由它自己的卫推出。"
            "`transitions_from_segmentation` 默认取 `tracks[0]`，于是 **72/193 个世界"
            "挖的是一块静止障碍**。4 个及以上文字的最小卫、以及除网格外的任何世界族，"
            "均 **边界未测**。20 个发布字段里 14 个没有不变量断言。",
    },
    {
        "pkg": "zero_space",
        "milestone": "engine-rig-m4-zerospace",
        "role": "提出 invariant：观测差分向量的 GF(2) 零空间 → 证据支持的线性守恒律，"
                "分为编码局部与世界层。",
        "caveat":
            "**只在它自己声明的量词下成立（D-003）。** 量词是「观测到的轨迹」；"
            "把它加强成「世界的全部合法转移」，**200 个世界里 13 个的 102 条律不再成立**。"
            "留出验证（E17）：信息量非零的那一刀（整条操作留出）下律成立率 **13.1 %**；"
            "同时报出的 **100.0 %** 是一个**被证明为空洞的对照**（转移级留出下 0/2160 行是新的）。"
            "`scope` 声称了一种它从未核验的来源：1271 条 `cell_local` 里 **329 条**"
            "支撑集是真子集，且其中 **0 条**落在本引擎自己的编码律张成里。"
            "11 个发布字段里 5 个没有不变量断言。",
    },
    {
        "pkg": "lp_potential",
        "milestone": "engine-rig-m5-lp",
        "role": "证明 invariant + heuristic：用有理数精确验证的线性 pagoda 证明目标不可达，"
                "同一组权重兼作可采纳启发。",
        "caveat":
            "**CLAUDE.md 的「sound but incomplete」两句都成立，但作为冻结条目它不完整——"
            "补齐的两条都会咬封存战役。**\n"
            "  1. **不完备是真的，且有量级。** `0111` 确实不可解而无线性 pagoda 证明它"
            "（D-014，用测试而不是注释断言）；E11 在 N=3000 上量到"
            "**639/2189 = 29.2 %** 的真不可达世界拿不到证书。"
            "流传的 **46.6 %** 是 N=500 下的*无证书率*，不是不完备率，高估约 2×。\n"
            "  2. **「sound」只在它被交付的移动表之上成立。** E17 每次留出一条 jump 几何："
            "回来的 1408 张证书里只有 **26.4 %** 在被留出的几何上仍满足 `inv_closed`，"
            "**58 张对完整移动集下的 BFS ground truth 是彻头彻尾的假**。"
            "最小见证可手算：`peg4`、目标 `0100`、起点 `0011`、留出 `jump(3,2,1)`——"
            "三个条件在有理数下全部精确为真，而 fixture 自己手验的表说该目标**可达**。"
            "发射门 `premises_against_graph` 拦不住：交给它一个「部分证据调用者真正持有」"
            "的图时，**1408 张全部发射，含那 58 张假证书**，每张都带着 `holds: true` 与 "
            "`sound_over_graph: true` 进入共享候选流。"
            "**臂按构造就是一个部分证据调用者。**\n"
            "  3. **第三条限定，写在代码里**（`potential.py:282-289`）："
            "`no_linear_pagoda` 是 `|w_i| <= bound` 盒子**之内**的不可行；"
            "`bound=10` 是求解器参数而非 pagoda 定义的一部分，E11 在 3000 个世界里"
            "找到 1 个 pagoda 落在盒外。另有 **638** 个世界的「不存在线性 pagoda」"
            "只是 HiGHS 返回的浮点不可行，**没有精确 Farkas 对偶**——那是求解器的说法，"
            "不是证明。\n"
            "  4. 可用之处也多半空洞：**65.1 %** 的可用状态 `h = 0`，"
            "**579/1550** 个世界里 `h` 在每个这样的状态上都是 0。锐度不被主张（D-008）。",
    },
    {
        "pkg": "fd_adapter",
        "milestone": "engine-rig-m6-fd",
        "role": "提出 plan：一个 `solve(domain, problem)` 接口覆盖三级规划器阶梯"
                "（自带 BFS / Fast Downward 最优 / LAMA 满意），"
                "并裁定「无计划」何时可以读作证明。",
        "caveat":
            "**三级阶梯是真的，回落是真的，但「静默回落」有条件，而「3 个测试跳过」已过期。**\n"
            "  1. 阶梯：`backends.py:33-36` `TIERS = (\"stub-bfs\", \"fd-optimal\", "
            "\"fd-satisficing\")`。真实构建：FD 24.06+ `7120aa01`，winlibs GCC 16.1.0，"
            "235 targets，无补丁。\n"
            "  2. **`.toolchain/` 按设计 gitignore**（`TOOLCHAIN_MANIFEST.md:290`），"
            "所以没有构建的机器上会回落到自带 BFS。**但回落只在调用者不指名档位时是静默的。**"
            "`choose_tier` 第 2 条（`backends.py:170-182`）在指名 FD 档而没有可达构建时"
            "**抛 `FastDownwardMissing`**，理由逐字写在 docstring 里："
            "「asking for a named planner and silently getting another one is how a "
            "benchmark lies」。静默回落是第 4 条（`:186-188`），即 `prefer=None`——"
            "而 `theoria-arm/inner/plan.py:112` 正是这样调的（本清单 待办 7-a）。"
            "还有一处**结构性**静默回落，第 3 条（`:184-185`）：带 `prune=` 或纯内存实例时"
            "强制 stub，**在有构建的机器上也一样**，fuzz 电池因此从未跑过任何 FD 档。\n"
            "  3. **「3 个测试跳过」是 P-13 时代的数字，已过期。** 本机实测（无 FD）："
            "**554 passed, 27 skipped**（581 收集）。27 跳过里 **15 条是 FD 的**，"
            "另 **12 条**是 `test_tool_failure_is_not_truth.py:349`，与 FD 无关。"
            "`STATUS.md:71-74` 记的 483/27 计数已过期且把「跳过全是 FD 的」写错了；"
            "`STATUS.md:384` 仍在引 P-13 的 252+3，那就是 CLAUDE.md「3」的来源。\n"
            "  4. **产物路径按设计钉死在 stub 上**（D-025，`__init__.py:36` "
            "`ARTIFACT_TIER = backends.STUB`），所以 `artifacts/candidates.jsonl` "
            "在有无规划器的机器上字节相同。**这也意味着提交流里没有一行来自真实 FD。**\n"
            "  5. 退出码分不开证明与放弃（D-024）：exit 12 是 `SEARCH_UNSOLVED_INCOMPLETE`，"
            "不是 11 `SEARCH_UNSOLVABLE`。跨赛道审计发现 `cold-start-a0` 曾"
            "仅凭异常字符串把 12 读成证明。",
    },
    {
        "pkg": "probe_frontier",
        "milestone": "engine-rig-m7-probe",
        "role": "提出 probe_design：选下一个实验——按预测观测切分存活假设，"
                "按单位成本信息增益排序动作。",
        "caveat":
            "**算术干净，边界全在退化与接缝上。** 0 个切分不符、0 个熵不符"
            "（最大偏差 1.11e-15）、4000 个世界 0 次真实换序。"
            "但零成本无用动作得分 `inf`、排第一，并让 `best_probe` 返回 `None`——"
            "**4000 个 fuzz 世界里 82 个因此丢掉一个可用的 1 比特实验**；"
            "同一个包里对「成本 0 的价值」有两个相反定义（`inf` 与 `0.0`）。"
            "裸 `Infinity`（不是合法 JSON）在 **1633/4000** 发射行里进入共享候选流，"
            "而冻结契约的校验器放行。"
            "规划器支撑的那条路径（`run_with_planner` / `ExecutableProbe`）"
            "**没有任何暴力对照——边界未测**，因为它需要真实 FD 构建。"
            "29 个发布字段里 19 个没有不变量断言。",
    },
    {
        "pkg": "deadlock_carver",
        "milestone": "engine-rig-m9-deadlock-ic3-probe",
        "role": "证明 invariant（+ plan 账）：条件式微型不可解定理 "
                "`pattern AND not-goal => dead`，由基化任务上的局部枚举加 h² 互斥证出；"
                "同一条定理既是候选也是规划器剪枝。",
        "caveat":
            "**真值干净，速度红利在真实规划器上不成立。** 被裁决的库存 "
            "**50 CONFIRMED / 0 refuted**（本引擎自己的数是 recheck 列的 **36/36**；"
            "那个 50 跨四条赛道八个生产者，不是本引擎的分数）。"
            "完备性被证据封顶：`MAX_PATTERN = 2` 就是 h² 互斥的宽度，"
            "`open4far` 的死状态覆盖 55.9 %，**44.1 % 死于没有 2 原子模式能陈述的理由**。"
            "**Theoria 1.9 的加速那一半没活过真实规划器**：`far6` 上对 blind 搜索 "
            "3070→2762（−10.0 %），对 `lmcut` **47→47**、对 `ipdb` **18→18**；"
            "M9 记的 `ringstuck` 44→22 是关于自带 BFS 的事实，真实 FD 两边都是 0→0。"
            "**边界未测**：所有定理都出自四个 sokoban 实例，换域后 `MAX_PATTERN = 2` "
            "买到或赔掉什么，没人测过。",
    },
    {
        "pkg": "ic3_pdr",
        "milestone": "engine-rig-m9-deadlock-ic3-probe",
        "role": "证明 invariant：LP 不可行处的后备归纳不变式，"
                "回答 lp_potential 的未了之事，报同样的三个条件。",
        "caveat":
            "**边界未测，整条。** 提交流里 **1** 张证书，在 **1** 个 16 状态 fixture 的"
            " **1** 个配置（`peg4` `0111`）上。没有状态空间阶梯、没有谓词数阶梯、"
            "没有超时、没有失败形态普查。**fuzz 电池里根本没有它的性质模块**——"
            "`fuzzlab/props/` 覆盖六个引擎而它不在其中，战役里 **0** 行属于它，"
            "所以 60 世界战役、64 个变异体、111 字段发布审计一条都碰不到它。"
            "**论文可以说 LP 的缺口在 `0111` 上被覆盖，不可以说它被覆盖。**"
            "未结工单：`monitor/board/items/E8-ic3-scale.md`——「只有一个点，画不出线」。",
    },
]

#: Companion files the item's landing spot depends on.  Pinned here so that
#: "item 5 = these bytes" is a closed statement.
COMPANIONS = [
    ("engine-rig/ENGINE_TABLE.md",
     "**名册与边界的现有权威**，`python -m tools.engine_table` 生成"
     "（`--check` 只核不写），由 `engine-rig/tests/test_engine_table.py`（9 条）"
     "盯住每个数字仍由其探针支撑；180 条事实带逐条来源表。"
     "它有八行、有「它解决什么」、有 fixture、有复核方式、有永不留空的边界列。"
     "**它没有：模块路径、哈希、版本串、测试条数、枚举标签、工具链身份。**"
     "所以钉住它是必要而不充分的——它是本条的「清单」那一半，不是「与版本」那一半。"),
    ("engine-rig/STATUS.md",
     "里程碑表（**九个**标签，不是八个）与测试套件计数。"
     "两处计数互相矛盾且都已过期，见 fd_adapter 的保留第 3 条。"),
    ("engine-rig/DECISIONS.md",
     "D-018（枚举撞名）、D-014（pagoda 不完备用测试断言）、D-025（产物钉在 stub）、"
     "D-024（退出码不是证明）、D-008（不主张锐度）的落点。"),
    ("engine-rig/common/candidates.py",
     "**冻结枚举 `ENGINES` 的唯一定义**（`:27-34`，恰好六个名字）与 `KINDS`。"),
    ("engine-rig/artifacts/candidates.jsonl",
     "提交的候选流，确定性模式（D-015），44 行，本清单第 4 节对它做普查。"),
    ("engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md",
     "外部工具链溯源：URL / 版本 / 大小 / sha256 / 构建命令 / 工具版本。"),
    ("engine-rig/bench/toolchain.py",
     "**工具链身份的可执行形态**：`EXPECTED`（`:42-47`）持有期望的 "
     "binary sha256 / FD commit / FD version，并在运行时从活体二进制重新导出比对，"
     "所以一份漂了的溯源文档会表现为 mismatch 而不是被当成仍然为真来引用。"),
]

#: The external toolchain's identity, as the tracked files state it.  Quoted
#: here and then *checked* against `bench/toolchain.py`'s blob, so this block
#: cannot drift away from the code that enforces it.
TOOLCHAIN_EXPECTED = {
    "binary_sha256":
        "645671ae40d825478a043a9f94c856dc6130a11c166b3393837c153c5020aee1",
    "fd_commit": "7120aa01704bfe8e3b9b92c062a4f775bc89c7bd",
    "fd_version": "Fast Downward 24.06+",
}

VERSION_PATTERN = (r"__version__|SCHEMA_VERSION|ENGINE_VERSION"
                   r"|VERSION[[:space:]]*=|version[[:space:]]*=")

BLOCK_BEGIN = "<!-- ENGINE-HASHES:BEGIN -->"
BLOCK_END = "<!-- ENGINE-HASHES:END -->"
GENERATED_FROM = "<!-- generated-from:"


# --------------------------------------------------------------------- git


def git_lines(*args):
    """`git` output as a list of lines; `[]` when the command finds nothing.

    `git grep` exits 1 for "no matches", which is not an error here, so the
    sibling's `git()` (which returns None on any non-zero exit) cannot be used
    for the scans.
    """
    result = subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
    if result.returncode not in (0, 1):
        raise RuntimeError("git %s failed: %s" % (" ".join(args), result.stderr))
    return [l for l in result.stdout.split("\n") if l]


def tree_sha1(rel, rev="HEAD"):
    """`git rev-parse <rev>:<path>` — the git object id, not a worktree hash.

    Returns None when the path does not exist at that revision, which is a
    finding rather than an error: an engine that is not in the commit cannot be
    frozen, and a milestone tag that predates a package says so this way.
    """
    return git("rev-parse", "%s:%s" % (rev, rel))


def blob_text(rel, rev="HEAD"):
    out = subprocess.run(("git", "show", "%s:%s" % (rev, rel)), cwd=REPO,
                         capture_output=True)
    if out.returncode != 0:
        return None
    return out.stdout.decode("utf-8", "replace")


# ------------------------------------------------------------------ probes


CONST = {name: re.compile(r"^%s\s*=\s*[\"']([^\"']+)[\"']" % name, re.M)
         for name in ("ENGINE", "PRODUCER")}


def declared_constants(pkg):
    """`ENGINE` / `PRODUCER` as the package's own `__init__.py` blob declares them.

    Read out of the blob rather than imported.  Importing would run the package
    -- and `engines/*/__init__.py` imports numpy, scipy and the shared contract
    module -- so a manifest that imported to find a name would be unbuildable on
    a machine that cannot run the engines, which is precisely the machine most
    likely to be auditing the freeze.
    """
    rel = "%s/%s/__init__.py" % (ENGINES_DIR, pkg)
    text = blob_text(rel) or ""
    found = {}
    for name, pattern in CONST.items():
        match = pattern.search(text)
        found[name] = match.group(1) if match else None
        if match:
            line = text[:match.start()].count("\n") + 1
            found[name + "_line"] = line
    return found


def version_scan():
    """Every version-assignment-shaped line in `engine-rig`'s code, at HEAD.

    Scope is stated in the output because a null result is only as strong as its
    scope: all tracked `.py` / `.toml` / `.cfg` under `engine-rig/`.
    """
    hits = git_lines("grep", "-n", "-E", VERSION_PATTERN, "HEAD", "--",
                     "engine-rig/*.py", "engine-rig/*.toml", "engine-rig/*.cfg")
    files = len(git_lines("ls-files", "--", "engine-rig/*.py",
                          "engine-rig/*.toml", "engine-rig/*.cfg"))
    return [h[len("HEAD:"):] for h in hits], files


def def_test_count(rel):
    counted = git_lines("grep", "-c", "-E", "^def test_", "HEAD", "--", rel)
    return int(counted[0].rsplit(":", 1)[1]) if counted else 0


def tests_for(pkg):
    """The package's dedicated test file, and every other file that references it.

    The split is the whole point and the first cut of this function did not make
    it: "every test file that mentions `engines.mdl_segmenter`" is four files and
    70 `def test_`, because `test_cegis_miner.py` imports the segmenter to build
    its inputs.  Summing those would credit one engine with another engine's
    tests -- a manifest overstating its own coverage, which is the failure mode
    this whole kit exists to prevent.

    So: `tests/test_<pkg>.py` is the dedicated file and is the only thing
    counted.  Everything else is listed as a *reference* with its own count and
    is explicitly not attributed.  Both halves are derived from git, not curated.

    The count is `^def test_` over the blob, so it is reproducible from git on a
    machine that cannot run pytest.  It is NOT pytest's collected count --
    parametrisation makes those differ -- and section 5 says so and reports the
    measured totals separately.
    """
    dedicated_rel = "engine-rig/tests/test_%s.py" % pkg
    dedicated = ((dedicated_rel, def_test_count(dedicated_rel))
                 if tree_sha1(dedicated_rel) else None)

    pattern = r"engines\.%s|from engines import [A-Za-z_, ]*%s" % (pkg, pkg)
    files = git_lines("grep", "-l", "-E", pattern, "HEAD", "--",
                      "engine-rig/tests/*.py")
    others = []
    for entry in sorted(files):
        rel = entry[len("HEAD:"):]
        if dedicated is not None and rel == dedicated_rel:
            continue
        others.append((rel, def_test_count(rel)))
    return {"dedicated": dedicated, "references": others}


def stream_census():
    """`(engine, producer, kind) -> rows` over the committed candidate stream.

    From the blob, so this is a fact about the commit.  It is here because it is
    the only place the enum collision can be observed from the outside, and what
    it shows is that `payload.producer` -- D-018's whole answer to the collision
    -- is absent on most rows.
    """
    import json
    text = blob_text("engine-rig/artifacts/candidates.jsonl")
    if text is None:
        return None
    census = {}
    for line in text.split("\n"):
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row.get("engine"), (row.get("payload") or {}).get("producer"),
               row.get("kind"))
        census[key] = census.get(key, 0) + 1
    return census


def toolchain_check():
    """Does `bench/toolchain.py` still state the identity this manifest quotes?"""
    text = blob_text("engine-rig/bench/toolchain.py") or ""
    return {k: (v in text) for k, v in sorted(TOOLCHAIN_EXPECTED.items())}


# ------------------------------------------------------------------- build


def collect():
    """Everything derived, in one dict.  No I/O into the repo, no timestamps."""
    rows = []
    for entry in ROSTER:
        pkg = entry["pkg"]
        rel = "%s/%s" % (ENGINES_DIR, pkg)
        files = [p for p in git_lines("ls-files", "--", rel)]
        head = tree_sha1(rel)
        at_tag = tree_sha1(rel, entry["milestone"])
        rows.append({
            "pkg": pkg,
            "path": rel,
            "tree": head,
            "files": [(f, tree_sha1(f)) for f in sorted(files)],
            "milestone": entry["milestone"],
            "milestone_tree": at_tag,
            "milestone_pins": at_tag is not None and at_tag == head,
            "constants": declared_constants(pkg),
            "tests": tests_for(pkg),
            "role": entry["role"],
            "caveat": entry["caveat"],
        })

    enum_tags = {}
    for row in rows:
        enum_tags.setdefault(row["constants"]["ENGINE"], []).append(row["pkg"])

    versions, scanned = version_scan()
    kind, digest, count, source = hash_path(ENGINES_DIR)
    return {
        "rows": rows,
        "collisions": {tag: pkgs for tag, pkgs in sorted(enum_tags.items())
                       if len(pkgs) > 1},
        "version_hits": versions,
        "version_files_scanned": scanned,
        "companions": [(rel, tree_sha1(rel), note) for rel, note in COMPANIONS],
        "engines_tree": tree_sha1(ENGINES_DIR),
        "engines_content_sha256": digest,
        "engines_file_count": count,
        "engines_hashed_from": source,
        "census": stream_census(),
        "toolchain": toolchain_check(),
        "tags": sorted(t for t in git_lines("tag", "-l") if t.startswith("engine-rig-")),
    }


def hash_rows(data):
    """The machine-readable pin list: `(kind, sha1, path)`, sorted by path.

    This block is what `--verify` compares row by row, so a drift report can
    name the file that moved instead of saying "the manifest changed".
    """
    rows = [("tree", data["engines_tree"], ENGINES_DIR)]
    for row in data["rows"]:
        rows.append(("tree", row["tree"], row["path"]))
        rows.extend(("blob", sha, path) for path, sha in row["files"])
    for rel, sha, _note in data["companions"]:
        rows.append(("blob" if not rel.endswith("/") else "tree", sha, rel))
    return sorted(rows, key=lambda r: (r[2], r[0]))


# ------------------------------------------------------------------ render


def render(data):
    L = []
    add = L.append

    add("# ENGINE_MANIFEST —— 冻结清单第 5 项：引擎清单与版本")
    add("")
    add("**生成物。不要手改。** "
        "由 `python freeze/build_engine_manifest.py` 写出；"
        "`--verify` 从 git 重算每一个哈希并逐行报漂移。")
    add("")
    add("`Theoria.md:368` 第 5 项逐字是「**引擎清单与版本**」。"
        "本文是那份清单。它的存在理由是 `MANIFEST_DRAFT.md` §5 的 ⛔："
        "在此之前，名册以散文形式存在于 `engine-rig/STATUS.md`，"
        "能力与边界表存在于 `engine-rig/ENGINE_TABLE.md`，"
        "而**版本一处都没有**。")
    add("")
    add("## 哈希纪律")
    add("")
    add("**本文全部哈希都是 `git rev-parse HEAD:<path>` 取的 git tree/blob sha1，"
        "没有一个取自工作树文件。** 理由是实测出来的，见 `MANIFEST_DRAFT.md`"
        "「哈希纪律」：仓库根没有 `text`/`eol` 规则，同一个文件在两个 checkout 里"
        "一个 CRLF 一个 LF，于是工作树哈希跨 checkout 不可复现——"
        "而失败模式是最坏的那种：`--verify` 会对一棵其实相同的树报红，"
        "撞上的人会去重生成清单把它弄绿。")
    add("")
    add("`engine-rig/.gitattributes` 恰好钉了 LF，所以本子树本不会栽在这上面。"
        "规则照样遵守：一份因为某个子目录的性质才正确的清单，是靠运气正确的。")
    add("")
    add("`git rev-parse HEAD:<path>` 读的是 **HEAD 而不是工作树**，"
        "所以即使 checkout 是脏的，这些哈希描述的仍是提交。"
        "这既是特性也是陷阱，因此 `engine-rig/` 的脏状态由生成器打在 stdout 上，"
        "**不写进本文**——写进来会让一次无关编辑看起来像哈希漂移。")
    add("")

    # ---------------------------------------------------------------- 0
    add("## 0. 覆盖表 —— 每个引擎的版本钉住了吗")
    add("")
    add("| # | 包 | 版本串 | 里程碑标签是否仍描述这些字节 | 结论 |")
    add("|---|---|---|---|---|")
    for i, row in enumerate(data["rows"], 1):
        pins = ("✅ 同" if row["milestone_pins"]
                else ("⛔ 不同" if row["milestone_tree"] else "⛔ 标签下无此路径"))
        add("| %d | `%s` | ⛔ 无 | %s (`%s`) | %s |"
            % (i, row["pkg"], pins, row["milestone"],
               "⛔ 未钉版" if not row["milestone_pins"] else "⚠ 仅标签，无版本串"))
    add("")
    pinned = sum(1 for r in data["rows"] if r["milestone_pins"])
    add("**八个包，零个版本串，%d/8 的里程碑标签仍与 HEAD 字节相同。**"
        % pinned)
    add("")
    add("扫描范围与结果，逐字：`git grep -E '%s' HEAD -- 'engine-rig/*.py' "
        "'engine-rig/*.toml' 'engine-rig/*.cfg'`，覆盖 **%d** 个受版本管理的文件，"
        "命中 **%d** 行："
        % (VERSION_PATTERN.replace("[[:space:]]", "\\s"),
           data["version_files_scanned"], len(data["version_hits"])))
    add("")
    for hit in data["version_hits"]:
        add("* `%s`" % hit)
    if not data["version_hits"]:
        add("* *（无）*")
    add("")
    add("命中的两行都是 Fast Downward 自己的版本管道，"
        "**不是任何引擎的版本**。`engine-rig/` 里没有 `pyproject.toml`。"
        "所以：")
    add("")
    add("> **⛔ 缺 5-b：八个引擎的版本串全部缺失，"
        "由 engine-rig 赛道在 `engine-rig/engines/<pkg>/__init__.py` 补"
        "（或在 `engine-rig/common/` 立一个单一来源）。**")
    add("")
    add("**这个 code 是故意重用的，不是新开一个缺口。** `MANIFEST_DRAFT.md` §5 已经"
        "declare 了 `⛔ 缺 5-b「引擎带名字，不带版本」`；本文是同一个缺口的**实测**"
        "（扫描范围、命中行、里程碑标签的反证），因此在这里是一处**引用**而不是"
        "第二次声明——`freeze/residuals.py` 拒绝同一个 code 被声明两次，"
        "而「它被修好了吗」有两个答案正是它要防的事。"
        "行首刻意留了 `> `，所以 `residuals.py` 的 `DECL`（要求行首 `**⛔`）不会"
        "把它读成声明，而 `ANY_MARK` 仍然能看见它还开着。")
    add("")
    add("在补上之前，本条唯一可引的版本把手是 **git tree sha1**（第 1 节）"
        "与**冻结提交本身**。里程碑标签**不是**把手："
        "上表 %d/8 的包在它自己的标签之后动过，"
        "所以「按 m8 冻结」或「按 m9 冻结」都盖不住 `engines/` 里的字节"
        "（`MANIFEST_DRAFT.md` 待办 5-d 的可执行形态）。"
        % (len(data["rows"]) - pinned))
    add("")

    # ---------------------------------------------------------------- 1
    add("## 1. 名册 —— 八个包，按包路径为键")
    add("")
    add("**键是包路径，不是 `ENGINE` 常量。** 理由见第 2 节："
        "两个包声明的是别人的名字，按枚举为键的清单会把八行静默并成六行。")
    add("")
    add("| # | 包路径（模块路径） | tree sha1 @HEAD | 文件 | 枚举标签 `ENGINE` | `PRODUCER` | 版本串 | 专属测试 |")
    add("|---|---|---|---|---|---|---|---|")
    for i, row in enumerate(data["rows"], 1):
        const = row["constants"]
        producer = ("`%s`" % const["PRODUCER"]) if const["PRODUCER"] else "*（未设）*"
        dedicated = row["tests"]["dedicated"]
        add("| %d | `%s` | `%s` | %d | `%s` | %s | ⛔ 无 | %s |"
            % (i, row["path"], row["tree"], len(row["files"]),
               const["ENGINE"], producer,
               ("`test_%s.py` %d 条" % (row["pkg"], dedicated[1]))
               if dedicated else "⛔ 无"))
    add("")
    add("`engines/` 整个目录树：`%s`（`engine-rig/engines`，%d 个受版本管理的文件）。"
        % (data["engines_tree"], data["engines_file_count"]))
    add("")
    add("「专属测试」只数 `engine-rig/tests/test_<pkg>.py` 里的 `^def test_`。"
        "第 3 节另列**引用**该引擎但属于别人的测试文件，**不计入**——"
        "按「提到它的文件」求和会让 `mdl_segmenter` 拿到 70 条（4 个文件），"
        "其中三份是别的引擎拿它当输入用的测试。"
        "一份高报自己覆盖率的清单，正是整套工具要防的那种假话。")
    add("")
    add("**推导规则与它的界限，写明以便反驳**：「引用」= blob 里出现 "
        "`engines.<pkg>` 或 `from engines import … <pkg>`，即**模块级引用**。"
        "只按名字提到它的测试**不算**——例如 `test_integration.py:137` 以 "
        "`by_producer[\"ic3_pdr\"]` 检查发射流、`test_engine_table.py:52-75` "
        "整段盯着 `ic3_pdr` 那一行，两者都不导入该模块，因此都不出现在它的引用表里。"
        "这是「谁 import 了它」的清单，不是「谁间接练到了它」的清单。")
    add("")
    add("逐文件 blob sha1 在第 10 节的机读块里，`--verify` 逐行核对。")
    add("")

    # ---------------------------------------------------------------- 2
    add("## 2. 枚举撞名 —— 为什么这份清单不能按 `ENGINE` 为键")
    add("")
    for tag, pkgs in sorted(data["collisions"].items()):
        add("* `ENGINE = \"%s\"` 由 **%d** 个包声明：%s。"
            % (tag, len(pkgs), "、".join("`%s`" % p for p in pkgs)))
    add("")
    add("逐字，从各自的 `__init__.py` blob 里读出来的（不是 import 出来的）：")
    add("")
    add("```")
    for row in data["rows"]:
        const = row["constants"]
        if const["PRODUCER"]:
            add("%s:%d  ENGINE   = \"%s\"   # the frozen enum; see D-018"
                % (row["path"] + "/__init__.py", const["ENGINE_line"],
                   const["ENGINE"]))
            add("%s:%d  PRODUCER = \"%s\""
                % (row["path"] + "/__init__.py", const["PRODUCER_line"],
                   const["PRODUCER"]))
    add("```")
    add("")
    add("冻结枚举 `ENGINES` 定义在 `engine-rig/common/candidates.py:27-34`，"
        "恰好六个名字。D-018 的裁定是：新引擎不改冻结契约，"
        "而是「emit under the enum member whose work it extends」，"
        "真实身份记在 `payload.producer`。")
    add("")
    add("**后果，对任何消费者都成立：「八个引擎、八个标签」读不出来。**"
        "按 `engine` 分行的直方图恒为六行——`run_all` 的 `by_engine` 就是这么写的，"
        "而且 D-018 把这一点列为优点。所以本清单按包路径为键，"
        "把枚举标签作为一个**可能撞名的独立列**。")
    add("")

    # ---------------------------------------------------------------- 3
    add("## 3. 每个引擎提出/证明什么，以及它的常设保留")
    add("")
    add("「提出/证明」一行是判断，与保留一起作为字面量存在生成器里，"
        "所以可以被争论。保留里的每个数字都引自 `engine-rig/ENGINE_TABLE.md`"
        "——那是生成的、探针支撑的、由 `engine-rig/tests/test_engine_table.py` 盯住的，"
        "于是这些数字有一个**不是本文**的主人。")
    add("")
    for i, row in enumerate(data["rows"], 1):
        const = row["constants"]
        add("### %d. `%s`  ·  枚举标签 `%s`%s"
            % (i, row["pkg"], const["ENGINE"],
               ("  ·  `PRODUCER = \"%s\"`" % const["PRODUCER"])
               if const["PRODUCER"] else ""))
        add("")
        add("* **提出/证明**：%s" % row["role"])
        add("* **tree sha1**：`%s`" % row["tree"])
        add("* **版本串**：⛔ 无。里程碑 `%s` 的树 %s HEAD。"
            % (row["milestone"],
               "**等于**" if row["milestone_pins"] else "**不等于**"))
        tests = row["tests"]
        dedicated = tests["dedicated"]
        if dedicated is None:
            add("* **专属测试文件**：⛔ `engine-rig/tests/test_%s.py` 不存在"
                % row["pkg"])
        else:
            add("* **专属测试文件**：`%s` — `^def test_` **%d** 条"
                % (dedicated[0], dedicated[1]))
        if tests["references"]:
            add("* **另有 %d 个测试文件引用它**（不计入上面的条数——"
                "它们是别的引擎的测试，把这个引擎当输入用）："
                % len(tests["references"]))
            for path, number in tests["references"]:
                add("  * `%s`（该文件自身 %d 条）" % (path, number))
        add("* **常设保留**：%s" % row["caveat"])
        add("")

    # ---------------------------------------------------------------- 4
    add("## 4. 提交候选流普查 —— 撞名的解法**没有写下来**")
    add("")
    census = data["census"]
    if census is None:
        add("⛔ `engine-rig/artifacts/candidates.jsonl` 在 HEAD 上不存在。")
    else:
        total = sum(census.values())
        without = sum(v for (_e, p, _k), v in census.items() if p is None)
        add("`engine-rig/artifacts/candidates.jsonl`，%d 行（确定性模式，D-015）："
            % total)
        add("")
        add("| `engine` | `payload.producer` | `kind` | 行数 |")
        add("|---|---|---|---|")
        for (engine, producer, kind), n in sorted(
                census.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]),
                                                str(kv[0][2]))):
            add("| `%s` | %s | `%s` | %d |"
                % (engine, "`%s`" % producer if producer else "*（缺）*", kind, n))
        add("")
        add("**%d/%d 行没有 `payload.producer`。** 只有那两个后来的包设了这个常量"
            "（`git grep -n '^PRODUCER' HEAD -- 'engine-rig/engines/*'` 恰好两行）。"
            % (without, total))
        add("")
        # D-018 的那句「`payload.producer` is never absent」是关于**两个新引擎的
        # 行**说的。所以要判它真假，得先把缺 producer 的行按 engine 分开，
        # 而不是拿总数 26/44 去对。分开算之后剩下的那条缺口更窄、也更该修：
        # 「缺失 ⇒ 枚举名即生产者」这条解析规则没写在任何文件里，
        # 于是一行缺 producer 的记录**在字节层面无法区分**是「六个冻结引擎之一
        # 发的」还是「某个新引擎忘了设 PRODUCER」。
        # （本段原先直接断言 D-018 为假；RES-1 复核后判为过头并改成这里的算法版，
        #  理由与 VARIANCE_BASIS.md §6 那次撤回相同——一份冻结文档里对某条裁定
        #  记录的错误指控，代价高于它本想修的那处遗漏。）
        frozen_enum = {"mdl_segmenter", "cegis_miner", "zero_space",
                       "lp_potential", "fd_adapter", "probe_frontier"}
        missing_under_enum = sum(
            v for (e, p, _k), v in census.items()
            if p is None and e in frozen_enum)
        named = sorted({p for (_e, p, _k) in census if p})
        named_rows = sum(v for (_e, p, _k), v in census.items() if p)
        add("**这 %d 行的 `engine` 全部是六个冻结引擎之一**（%d/%d 行如此），"
            "对它们来说枚举名本身就是生产者，字段缺失不是遗漏、是无话可说。"
            "带 producer 的 %d 行则全部出自后来的两个包（%s）。"
            "所以 D-018 那句「`payload.producer` is never absent」"
            "**在它所说的那批行上成立**，不必据此指控它。"
            % (without, missing_under_enum, without, named_rows,
               "、".join("`%s`" % p for p in named)))
        add("")
        add("**真正的缺口是解析规则没写下来。** 撞名可解——缺失 ⇒ 枚举名就是"
            "生产者——但这句话在任何文件里都找不到，"
            "于是**一行缺 producer 的记录在字节层面无法区分**"
            "「六个冻结引擎之一发的」与「某个新引擎忘了设 `PRODUCER`」；"
            "而 `by_engine` 与 `by_producer` 两个 histogram 会在新引擎的行上"
            "给出不同的答案。冻结前二选一："
            "把「缺失 ⇒ 自指」写成契约的一句话，或让六个冻结引擎也设 `PRODUCER`。")
        if missing_under_enum != without:
            add("")
            add("⛔ **%d 行缺 `payload.producer` 且其 `engine` 不在冻结枚举内**——"
                "这一条真的会让 D-018 的保证落空，必须在冻结前查清。"
                % (without - missing_under_enum))
    add("")

    # ---------------------------------------------------------------- 5
    add("## 5. 测试计数 —— 从 git 推导的与实测的，分开报")
    add("")
    add("第 3 节每个引擎的条数是 `^def test_` **对 blob 计数**，"
        "所以在一台跑不动 pytest 的机器上也能从 git 复现。"
        "**它不是 pytest 的收集数**（参数化会让两者不同），因此实测值单独报，"
        "并标明它是一次测量而不是一个哈希：")
    add("")
    add("| 量 | 值 | 条件 |")
    add("|---|---|---|")
    add("| 收集 | 581 | 本机，`python -m pytest --collect-only -q` |")
    add("| 通过 | 554 | 本机，**无** Fast Downward 构建 |")
    add("| 跳过 | 27 | 其中 15 条是 FD 的，12 条是 `test_tool_failure_is_not_truth.py:349` |")
    add("")
    add("留痕：`freeze/runs/20260729T2040Z-S4-freeze-complete/item05/pytest-no-fd.txt`。")
    add("")
    add("**三处已知过期的计数，都不要引：** `CLAUDE.md`「150 tests pass, 1 skipped」；"
        "`engine-rig/STATUS.md:71-74`「483 passed, 27 skipped … the skips are all FD's」"
        "（计数过期，且归因错误——12 条与 FD 无关）；"
        "`engine-rig/STATUS.md:384`「255 / 252+3」（P-13 时代）。")
    add("")

    # ---------------------------------------------------------------- 6
    add("## 6. 外部工具链 —— 身份钉在受版本管理的字节上，东西没有")
    add("")
    add("| 字段 | 值 | 由受版本管理的文件断言 |")
    add("|---|---|---|")
    for key in sorted(TOOLCHAIN_EXPECTED):
        add("| `%s` | `%s` | %s |"
            % (key, TOOLCHAIN_EXPECTED[key],
               "✅ `engine-rig/bench/toolchain.py`"
               if data["toolchain"][key] else "⛔ **不再出现在该文件里**"))
    add("")
    add("溯源：`engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`"
        "（URL / 版本 / 大小 / sha256 / 构建命令 / 实际用到的工具版本）。"
        "可执行形态：`engine-rig/bench/toolchain.py` 的 `EXPECTED`，"
        "它在运行时从活体二进制重新导出 `--version`、git revision 与 binary sha256 "
        "并比对，所以一份漂了的溯源文档会表现为 mismatch。")
    add("")
    add("**是否可从受版本管理的文件复现：期望可以，产物不可以。**"
        "`.toolchain/` 按设计 gitignore（约 1.6 GB），"
        "那个 280,538,976 字节的二进制不在仓库里，也不能由仓库重建。"
        "`bench/toolchain.py:8-16` 自己就这么写：「Every Fast Downward number in "
        "this run was produced by a binary that is not in the repository and "
        "cannot be reconstructed from it.」"
        "换来的不是可复现性而是**可反驳性**：重建出不同哈希，是一个可以被追问的问题。")
    add("")
    add("**因此，一条只写「fd-optimal」而不记录实际答题档位的冻结行，是一句假话。**"
        "阶梯有三级，`choose_tier` 第 4 条在 `prefer=None` 时按 `$FAST_DOWNWARD` "
        "是否可达在 `fd-optimal` 与 `stub-bfs` 之间切换，"
        "而 `theoria-arm/inner/plan.py:112` 就是不传 `prefer=` 的"
        "（`MANIFEST_DRAFT.md` 待办 7-a）。冻结行必须同时记："
        "(i) 请求的档位，(ii) 实际答题的档位，"
        "(iii) `bench/toolchain.py` 的 `matches_p13_manifest` 与 `available`。")
    add("")

    # ---------------------------------------------------------------- 7
    add("## 7. 伴生文件（本条的落点闭合到这些字节）")
    add("")
    add("| 路径 | blob sha1 @HEAD | 是什么 |")
    add("|---|---|---|")
    for rel, sha, note in data["companions"]:
        add("| `%s` | `%s` | %s |" % (rel, sha or "⛔ **不存在**", note))
    add("")
    add("里程碑标签，全部 %d 个 `engine-rig-*`：%s。"
        % (len(data["tags"]), "、".join("`%s`" % t for t in data["tags"])))
    add("")
    add("**九个，不是八个。** `CLAUDE.md` 说「all eight milestones」，"
        "而承载 `deadlock_carver` 与 `ic3_pdr` 的正是第九个 "
        "`engine-rig-m9-deadlock-ic3-probe`。")
    add("")

    # ---------------------------------------------------------------- 8
    add("## 8. 与 `freeze/MANIFEST.json` 的对接")
    add("")
    add("`build_manifest.py` 的第 5 项按内容 sha256 钉 `engine-rig/engines`；"
        "本文按 git tree sha1 钉同一个路径。两者用不同的算法，"
        "所以必须显式对接，否则一份漂了而另一份没看见。"
        "本行由本生成器调用 `build_manifest.hash_path` 重算，"
        "`--verify` 会连它一起核："
        "内容 sha256 = `%s`（%s，%d 个文件），git tree sha1 = `%s`。"
        % (data["engines_content_sha256"], data["engines_hashed_from"],
           data["engines_file_count"], data["engines_tree"]))
    add("")

    # ---------------------------------------------------------------- 9
    add("## 9. 本清单**没有**钉住什么")
    add("")
    add("* **版本串。** 八个全缺，见第 0 节的 ⛔ 5-b。")
    add("* **Fast Downward 二进制。** 只有身份，没有产物（第 6 节）。")
    add("* **Python 与库。** 全仓没有任何依赖锁"
        "（无 `requirements.txt` / `poetry.lock` / `uv.lock` / 环境导出），"
        "所以「全部哈希」对解释器与库不成立。这条与 `build_manifest.py` 的 X-2 同源。")
    add("* **fuzzlab 与 `runs/` 下的度量产物。** `ENGINE_TABLE.md` 的 180 条事实"
        "来自十个来源目录；本文钉的是那张表的 blob，不是它读的每一个产物。")
    add("* **`ic3_pdr` 的任何边界。** 不是本文的疏漏，是树上就没有（第 3.8 节）。")
    add("")

    # --------------------------------------------------------------- 10
    add("## 10. 机读钉住块")
    add("")
    add("`--verify` 逐行读这个块并与 git 重算的结果比对，"
        "所以漂移报告能点出**哪一个文件**动了，而不是只说「清单变了」。")
    add("")
    add(BLOCK_BEGIN)
    add("```")
    for kind, sha, path in hash_rows(data):
        add("%-4s %s  %s" % (kind, sha or "-" * 40, path))
    add("```")
    add(BLOCK_END)
    add("")
    add("---")
    add("")
    add("*生成：`freeze/build_engine_manifest.py`。工单 S4-freeze-complete 第 5 项，"
        "RES-1，2026-07-29。*")
    add("*基准：本文哈希取自生成时的 HEAD；冻结定稿时必须在真正的冻结提交上"
        "重跑 `--verify`，并把提交号回填到 `MANIFEST_DRAFT.md` 开头的 "
        "`⟨FREEZE_COMMIT⟩`。*")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ verify


def parse_block(text):
    """The on-disk pin list, as `path -> (kind, sha1)`."""
    start = text.find(BLOCK_BEGIN)
    end = text.find(BLOCK_END)
    if start < 0 or end < 0:
        return None
    body = text[start + len(BLOCK_BEGIN):end]
    found = {}
    for line in body.split("\n"):
        line = line.strip()
        if not line or line.startswith("```"):
            continue
        parts = line.split()
        if len(parts) != 3:
            return None
        kind, sha, path = parts
        found[path] = (kind, sha)
    return found


def strip_volatile(text):
    """Drop the one line that is allowed to move without being drift."""
    return "\n".join(l for l in text.split("\n")
                     if not l.startswith(GENERATED_FROM))


def verify():
    if not os.path.exists(OUT):
        print("freeze/ENGINE_MANIFEST.md does not exist; run without --verify")
        return 1

    data = collect()
    expected = {path: (kind, sha) for kind, sha, path in hash_rows(data)}
    with open(OUT, "r", encoding="utf-8") as handle:
        on_disk = handle.read()

    found = parse_block(on_disk)
    if found is None:
        print("DRIFT: the ENGINE-HASHES block is missing or malformed.")
        print("       every hash in this manifest is therefore unchecked.")
        return 1

    drifted = []
    for path in sorted(set(expected) | set(found)):
        want = expected.get(path)
        have = found.get(path)
        if want == have:
            continue
        if want is None:
            drifted.append("  EXTRA    %s\n             pinned  %s %s\n"
                           "             at HEAD not in the tree at all"
                           % (path, have[0], have[1]))
        elif have is None:
            drifted.append("  MISSING  %s\n             pinned  nothing\n"
                           "             at HEAD %s %s"
                           % (path, want[0], want[1]))
        else:
            drifted.append("  DRIFTED  %s\n             pinned  %s %s\n"
                           "             at HEAD %s %s"
                           % (path, have[0], have[1], want[0], want[1]))

    rendered_differs = strip_volatile(render(data)) != strip_volatile(on_disk)

    if drifted:
        print("DRIFT: freeze/ENGINE_MANIFEST.md no longer describes this tree.")
        print("       %d row(s) disagree:" % len(drifted))
        for line in drifted:
            print(line)
        print("       regenerate it and read the diff before freezing.")
        return 1

    if rendered_differs:
        print("DRIFT: every pinned hash matches, but the rendered manifest does "
              "not.")
        print("       something outside the hash block moved -- a derived count, "
              "a constant,")
        print("       a caveat, or a hand edit to a generated file. Regenerate "
              "and diff.")
        return 1

    print("freeze/ENGINE_MANIFEST.md still describes this tree "
          "(%d pinned rows, %d packages, %d/%d milestone tags still pin their "
          "own bytes, 0 engine version strings)"
          % (len(expected), len(data["rows"]),
             sum(1 for r in data["rows"] if r["milestone_pins"]),
             len(data["rows"])))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true",
                        help="exit 1 if ENGINE_MANIFEST.md no longer describes "
                             "the tree; print every drifted row")
    args = parser.parse_args()

    if args.verify:
        return verify()

    data = collect()
    text = render(data)
    commit = git("rev-parse", "HEAD")
    header = "%s %s -->\n" % (GENERATED_FROM, commit)
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(header + text)

    print("wrote freeze/ENGINE_MANIFEST.md")
    print("  8 packages, %d pinned rows, %d version string(s) found"
          % (len(hash_rows(data)), len(data["version_hits"])))
    pinned = sum(1 for r in data["rows"] if r["milestone_pins"])
    print("  %d/8 milestone tags still describe HEAD's bytes" % pinned)
    dirty = git("status", "--porcelain", "--", "engine-rig")
    if dirty:
        print("  WARNING: engine-rig/ is dirty -- these hashes describe HEAD, "
              "not what you are looking at:")
        for line in dirty.split("\n"):
            print("    %s" % line)
    else:
        print("  engine-rig/ is clean, so HEAD is what is on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
